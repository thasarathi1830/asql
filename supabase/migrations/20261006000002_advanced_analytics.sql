-- ============================================================================
-- PHANTOM — Advanced Analytics Migration
-- 8 PL/pgSQL Functions + 1 View + DML Audit Trigger
-- Uses: Recursive CTEs, Window Functions (LAG, LEAD, SUM OVER, COUNT OVER),
--       Self-Joins, Sliding Windows
-- ============================================================================

-- ============================================================================
-- FUNCTION A: find_transaction_paths()
-- Multi-hop transaction path discovery using Recursive CTE (BFS-style)
-- ============================================================================
CREATE OR REPLACE FUNCTION find_transaction_paths(
    p_start_account_id UUID,
    p_max_depth INT DEFAULT 4
)
RETURNS TABLE (
    source_account_id   UUID,
    destination_account_id UUID,
    path_nodes          UUID[],
    depth               INT,
    cumulative_amount   NUMERIC(15,2),
    transaction_ids     UUID[]
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE paths AS (
        -- Base case: all transactions from the starting account
        SELECT
            t.sender_account_id     AS source_id,
            t.receiver_account_id   AS current_node,
            ARRAY[t.sender_account_id, t.receiver_account_id] AS path_nodes,
            1                       AS depth,
            t.amount                AS cumulative_amount,
            ARRAY[t.id]             AS transaction_ids,
            t.transaction_timestamp AS last_timestamp
        FROM transactions t
        WHERE t.sender_account_id = p_start_account_id
          AND t.status IN ('COMPLETED', 'FLAGGED')

        UNION ALL

        -- Recursive case: extend paths by one hop
        SELECT
            p.source_id,
            t.receiver_account_id,
            p.path_nodes || t.receiver_account_id,
            p.depth + 1,
            p.cumulative_amount + t.amount,
            p.transaction_ids || t.id,
            t.transaction_timestamp
        FROM paths p
        JOIN transactions t ON t.sender_account_id = p.current_node
        WHERE p.depth < p_max_depth
          AND NOT (t.receiver_account_id = ANY(p.path_nodes))  -- Cycle prevention
          AND t.status IN ('COMPLETED', 'FLAGGED')
          AND t.transaction_timestamp >= p.last_timestamp      -- Chronological ordering
    )
    SELECT
        paths.source_id         AS source_account_id,
        paths.current_node      AS destination_account_id,
        paths.path_nodes,
        paths.depth,
        paths.cumulative_amount,
        paths.transaction_ids
    FROM paths
    ORDER BY paths.depth, paths.cumulative_amount DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION B: detect_transaction_cycles()
-- Circular money flow detection (A -> B -> C -> A)
-- Uses Recursive CTE that closes when current_node = origin
-- ============================================================================
CREATE OR REPLACE FUNCTION detect_transaction_cycles(
    p_lookback_days INT DEFAULT 30,
    p_min_amount NUMERIC DEFAULT 50000
)
RETURNS TABLE (
    cycle_signature TEXT,
    cycle_length    INT,
    accounts        UUID[],
    total_volume    NUMERIC(15,2),
    start_time      TIMESTAMPTZ,
    end_time        TIMESTAMPTZ,
    time_window_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE cycle_paths AS (
        -- Base case: start from each account with recent large transactions
        SELECT
            t.sender_account_id     AS origin,
            t.receiver_account_id   AS current_node,
            ARRAY[t.sender_account_id, t.receiver_account_id] AS path_nodes,
            1                       AS depth,
            t.amount                AS total_volume,
            t.transaction_timestamp AS start_ts,
            t.transaction_timestamp AS last_ts,
            FALSE                   AS cycle_closed
        FROM transactions t
        WHERE t.transaction_timestamp >= NOW() - (p_lookback_days || ' days')::INTERVAL
          AND t.amount >= p_min_amount
          AND t.status IN ('COMPLETED', 'FLAGGED')

        UNION ALL

        -- Recursive case: expand or close the cycle
        SELECT
            cp.origin,
            t.receiver_account_id,
            cp.path_nodes || t.receiver_account_id,
            cp.depth + 1,
            cp.total_volume + t.amount,
            cp.start_ts,
            t.transaction_timestamp,
            (t.receiver_account_id = cp.origin) AS cycle_closed
        FROM cycle_paths cp
        JOIN transactions t ON t.sender_account_id = cp.current_node
        WHERE cp.depth < 5                                          -- Max 5-hop depth
          AND NOT cp.cycle_closed                                   -- Don't expand closed cycles
          AND t.transaction_timestamp >= cp.start_ts                -- Chronological
          AND t.transaction_timestamp <= cp.start_ts + INTERVAL '72 hours'  -- 72-hour window
          AND t.amount >= p_min_amount
          AND t.status IN ('COMPLETED', 'FLAGGED')
          AND (
              t.receiver_account_id = cp.origin                     -- Closing the cycle
              OR NOT (t.receiver_account_id = ANY(cp.path_nodes))   -- Or new node
          )
    )
    SELECT
        array_to_string(cp2.path_nodes::TEXT[], ' -> ') AS cycle_signature,
        cp2.depth                                       AS cycle_length,
        cp2.path_nodes                                  AS accounts,
        cp2.total_volume,
        cp2.start_ts                                    AS start_time,
        cp2.last_ts                                     AS end_time,
        ROUND(EXTRACT(EPOCH FROM (cp2.last_ts - cp2.start_ts)) / 3600.0, 2) AS time_window_hours
    FROM cycle_paths cp2
    WHERE cp2.cycle_closed = TRUE
    ORDER BY cp2.total_volume DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION C: calculate_transaction_velocity()
-- Transaction velocity & burst anomaly detection using Window Functions
-- Uses: LAG(), SUM() OVER, COUNT() OVER, AVG() OVER
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_transaction_velocity(
    p_account_id UUID,
    p_window_hours INT DEFAULT 24
)
RETURNS TABLE (
    transaction_id          UUID,
    transaction_reference   VARCHAR(64),
    amount                  NUMERIC(15,2),
    transaction_timestamp   TIMESTAMPTZ,
    prev_amount             NUMERIC(15,2),
    prev_timestamp          TIMESTAMPTZ,
    time_gap_minutes        NUMERIC,
    rolling_sum             NUMERIC(15,2),
    rolling_count           BIGINT,
    rolling_avg             NUMERIC(15,2),
    is_velocity_spike       BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH velocity AS (
        SELECT
            t.id,
            t.transaction_reference,
            t.amount,
            t.transaction_timestamp,
            LAG(t.amount) OVER w_time           AS prev_amount,
            LAG(t.transaction_timestamp) OVER w_time AS prev_timestamp,
            SUM(t.amount) OVER w_range          AS rolling_sum,
            COUNT(*) OVER w_range               AS rolling_count,
            AVG(t.amount) OVER w_range          AS rolling_avg
        FROM transactions t
        WHERE (t.sender_account_id = p_account_id OR t.receiver_account_id = p_account_id)
          AND t.status IN ('COMPLETED', 'FLAGGED')
        WINDOW
            w_time AS (ORDER BY t.transaction_timestamp),
            w_range AS (
                ORDER BY t.transaction_timestamp
                RANGE BETWEEN (p_window_hours || ' hours')::INTERVAL PRECEDING AND CURRENT ROW
            )
    )
    SELECT
        v.id                    AS transaction_id,
        v.transaction_reference,
        v.amount,
        v.transaction_timestamp,
        v.prev_amount,
        v.prev_timestamp,
        CASE
            WHEN v.prev_timestamp IS NOT NULL
            THEN ROUND(EXTRACT(EPOCH FROM (v.transaction_timestamp - v.prev_timestamp)) / 60.0, 2)
            ELSE NULL
        END                     AS time_gap_minutes,
        v.rolling_sum,
        v.rolling_count,
        ROUND(v.rolling_avg, 2) AS rolling_avg,
        -- Spike: rolling count > 4x typical or amount > 3x rolling average
        (v.rolling_count > 4 OR (v.rolling_avg > 0 AND v.amount > v.rolling_avg * 3))
                                AS is_velocity_spike
    FROM velocity v
    ORDER BY v.transaction_timestamp DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION D: detect_structuring()
-- Smurfing pattern detection (transactions just below reporting threshold)
-- Uses: Window function aggregation within sliding time windows
-- ============================================================================
CREATE OR REPLACE FUNCTION detect_structuring(
    p_threshold_min NUMERIC DEFAULT 80000,
    p_threshold_max NUMERIC DEFAULT 99999,
    p_window_hours INT DEFAULT 24,
    p_min_tx_count INT DEFAULT 3
)
RETURNS TABLE (
    account_id          UUID,
    account_number      VARCHAR(64),
    window_start        TIMESTAMPTZ,
    window_end          TIMESTAMPTZ,
    tx_count            BIGINT,
    total_structured    NUMERIC(15,2),
    avg_amount          NUMERIC(15,2),
    min_amount          NUMERIC(15,2),
    max_amount          NUMERIC(15,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH structured_tx AS (
        SELECT
            t.sender_account_id,
            t.amount,
            t.transaction_timestamp,
            -- Sliding window aggregates
            COUNT(*) OVER w_window      AS window_tx_count,
            SUM(t.amount) OVER w_window AS window_total,
            AVG(t.amount) OVER w_window AS window_avg,
            MIN(t.amount) OVER w_window AS window_min,
            MAX(t.amount) OVER w_window AS window_max,
            MIN(t.transaction_timestamp) OVER w_window AS window_start,
            MAX(t.transaction_timestamp) OVER w_window AS window_end
        FROM transactions t
        WHERE t.amount BETWEEN p_threshold_min AND p_threshold_max
          AND t.status IN ('COMPLETED', 'FLAGGED')
        WINDOW w_window AS (
            PARTITION BY t.sender_account_id
            ORDER BY t.transaction_timestamp
            RANGE BETWEEN (p_window_hours || ' hours')::INTERVAL PRECEDING AND CURRENT ROW
        )
    )
    SELECT DISTINCT
        st.sender_account_id   AS account_id,
        a.account_number_masked AS account_number,
        st.window_start,
        st.window_end,
        st.window_tx_count     AS tx_count,
        st.window_total        AS total_structured,
        ROUND(st.window_avg, 2) AS avg_amount,
        st.window_min          AS min_amount,
        st.window_max          AS max_amount
    FROM structured_tx st
    JOIN accounts a ON a.id = st.sender_account_id
    WHERE st.window_tx_count >= p_min_tx_count
    ORDER BY st.window_total DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION E: detect_rapid_pass_through()
-- Mule account detection via rapid inflow -> outflow matching (self-join)
-- ============================================================================
CREATE OR REPLACE FUNCTION detect_rapid_pass_through(
    p_max_delay_hours INT DEFAULT 2,
    p_retain_ratio_max NUMERIC DEFAULT 0.10
)
RETURNS TABLE (
    mule_account_id     UUID,
    mule_account_number VARCHAR(64),
    inbound_tx_id       UUID,
    inbound_amount      NUMERIC(15,2),
    inbound_time        TIMESTAMPTZ,
    outbound_tx_id      UUID,
    outbound_amount     NUMERIC(15,2),
    outbound_time       TIMESTAMPTZ,
    delay_minutes       NUMERIC,
    retained_ratio      NUMERIC(5,4),
    source_account_id   UUID,
    destination_account_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t_in.receiver_account_id    AS mule_account_id,
        a.account_number_masked     AS mule_account_number,
        t_in.id                     AS inbound_tx_id,
        t_in.amount                 AS inbound_amount,
        t_in.transaction_timestamp  AS inbound_time,
        t_out.id                    AS outbound_tx_id,
        t_out.amount                AS outbound_amount,
        t_out.transaction_timestamp AS outbound_time,
        ROUND(EXTRACT(EPOCH FROM (t_out.transaction_timestamp - t_in.transaction_timestamp)) / 60.0, 2)
                                    AS delay_minutes,
        ROUND(1.0 - (t_out.amount / NULLIF(t_in.amount, 0)), 4)
                                    AS retained_ratio,
        t_in.sender_account_id      AS source_account_id,
        t_out.receiver_account_id   AS destination_account_id
    FROM transactions t_in
    -- Self-join: match inflows to subsequent outflows from the same account
    JOIN transactions t_out
        ON t_out.sender_account_id = t_in.receiver_account_id
        AND t_out.transaction_timestamp > t_in.transaction_timestamp
        AND t_out.transaction_timestamp <= t_in.transaction_timestamp + (p_max_delay_hours || ' hours')::INTERVAL
    JOIN accounts a ON a.id = t_in.receiver_account_id
    WHERE t_in.status IN ('COMPLETED', 'FLAGGED')
      AND t_out.status IN ('COMPLETED', 'FLAGGED')
      -- Retained ratio <= threshold (i.e., funds are mostly passed through)
      AND (1.0 - (t_out.amount / NULLIF(t_in.amount, 0))) <= p_retain_ratio_max
      -- Outflow must be a significant portion of inflow
      AND t_out.amount >= t_in.amount * (1.0 - p_retain_ratio_max)
    ORDER BY delay_minutes ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION F: detect_dormant_activation()
-- Dormant account burst activation detection
-- Uses: LAG() window function to compute gap between consecutive transactions
-- ============================================================================
CREATE OR REPLACE FUNCTION detect_dormant_activation(
    p_dormant_days INT DEFAULT 60,
    p_min_burst_amount NUMERIC DEFAULT 100000
)
RETURNS TABLE (
    account_id          UUID,
    account_number      VARCHAR(64),
    dormant_gap_days    NUMERIC,
    burst_tx_id         UUID,
    burst_amount        NUMERIC(15,2),
    burst_timestamp     TIMESTAMPTZ,
    prev_timestamp      TIMESTAMPTZ,
    bank_code           VARCHAR(32)
) AS $$
BEGIN
    RETURN QUERY
    WITH tx_with_gaps AS (
        SELECT
            t.sender_account_id,
            t.id AS tx_id,
            t.amount,
            t.transaction_timestamp,
            LAG(t.transaction_timestamp) OVER (
                PARTITION BY t.sender_account_id
                ORDER BY t.transaction_timestamp
            ) AS prev_tx_timestamp
        FROM transactions t
        WHERE t.status IN ('COMPLETED', 'FLAGGED')
    )
    SELECT
        g.sender_account_id        AS account_id,
        a.account_number_masked    AS account_number,
        ROUND(EXTRACT(EPOCH FROM (g.transaction_timestamp - g.prev_tx_timestamp)) / 86400.0, 1)
                                   AS dormant_gap_days,
        g.tx_id                    AS burst_tx_id,
        g.amount                   AS burst_amount,
        g.transaction_timestamp    AS burst_timestamp,
        g.prev_tx_timestamp        AS prev_timestamp,
        a.bank_code
    FROM tx_with_gaps g
    JOIN accounts a ON a.id = g.sender_account_id
    WHERE g.prev_tx_timestamp IS NOT NULL
      AND EXTRACT(EPOCH FROM (g.transaction_timestamp - g.prev_tx_timestamp)) / 86400.0 >= p_dormant_days
      AND g.amount >= p_min_burst_amount
    ORDER BY dormant_gap_days DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION G: calculate_counterparty_metrics()
-- In/out volume analysis and counterparty frequency metrics
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_counterparty_metrics(
    p_account_id UUID
)
RETURNS TABLE (
    counterparty_id         UUID,
    counterparty_number     VARCHAR(64),
    total_sent              NUMERIC(15,2),
    total_received          NUMERIC(15,2),
    sent_count              BIGINT,
    received_count          BIGINT,
    net_flow                NUMERIC(15,2),
    in_out_ratio            NUMERIC(10,4),
    first_transaction       TIMESTAMPTZ,
    last_transaction        TIMESTAMPTZ,
    unique_counterparties   BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH outflows AS (
        SELECT
            t.receiver_account_id AS counterparty,
            SUM(t.amount)         AS total_sent,
            COUNT(*)              AS sent_count,
            MIN(t.transaction_timestamp) AS first_out,
            MAX(t.transaction_timestamp) AS last_out
        FROM transactions t
        WHERE t.sender_account_id = p_account_id
          AND t.status IN ('COMPLETED', 'FLAGGED')
        GROUP BY t.receiver_account_id
    ),
    inflows AS (
        SELECT
            t.sender_account_id   AS counterparty,
            SUM(t.amount)         AS total_received,
            COUNT(*)              AS received_count,
            MIN(t.transaction_timestamp) AS first_in,
            MAX(t.transaction_timestamp) AS last_in
        FROM transactions t
        WHERE t.receiver_account_id = p_account_id
          AND t.status IN ('COMPLETED', 'FLAGGED')
        GROUP BY t.sender_account_id
    ),
    combined AS (
        SELECT
            COALESCE(o.counterparty, i.counterparty) AS counterparty_id,
            COALESCE(o.total_sent, 0)                AS total_sent,
            COALESCE(i.total_received, 0)            AS total_received,
            COALESCE(o.sent_count, 0)                AS sent_count,
            COALESCE(i.received_count, 0)            AS received_count,
            LEAST(COALESCE(o.first_out, i.first_in), COALESCE(i.first_in, o.first_out)) AS first_tx,
            GREATEST(COALESCE(o.last_out, i.last_in), COALESCE(i.last_in, o.last_out))  AS last_tx
        FROM outflows o
        FULL OUTER JOIN inflows i ON o.counterparty = i.counterparty
    )
    SELECT
        c.counterparty_id,
        a.account_number_masked         AS counterparty_number,
        c.total_sent,
        c.total_received,
        c.sent_count,
        c.received_count,
        (c.total_received - c.total_sent) AS net_flow,
        CASE
            WHEN c.total_sent > 0
            THEN ROUND(c.total_received / c.total_sent, 4)
            ELSE 0
        END                             AS in_out_ratio,
        c.first_tx                      AS first_transaction,
        c.last_tx                       AS last_transaction,
        COUNT(*) OVER ()                AS unique_counterparties
    FROM combined c
    LEFT JOIN accounts a ON a.id = c.counterparty_id
    ORDER BY (c.total_sent + c.total_received) DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- VIEW H: view_shared_identity_clusters
-- Identity attribute collision detection across customers
-- Uses self-join on identity_attributes by attribute_hash and attribute_type
-- with customer_a < customer_b deduplication
-- ============================================================================
CREATE OR REPLACE VIEW view_shared_identity_clusters AS
SELECT
    ia1.customer_id         AS customer_a_id,
    c1.name                 AS customer_a_name,
    c1.customer_reference   AS customer_a_ref,
    ia2.customer_id         AS customer_b_id,
    c2.name                 AS customer_b_name,
    c2.customer_reference   AS customer_b_ref,
    ia1.attribute_type      AS shared_attribute_type,
    ia1.attribute_hash      AS shared_attribute_hash,
    ia1.attribute_value_masked AS attribute_value,
    GREATEST(ia1.confidence, ia2.confidence) AS confidence
FROM identity_attributes ia1
JOIN identity_attributes ia2
    ON ia1.attribute_hash = ia2.attribute_hash
    AND ia1.attribute_type = ia2.attribute_type
    AND ia1.customer_id < ia2.customer_id   -- Deduplication: customer_a < customer_b
JOIN customers c1 ON c1.id = ia1.customer_id
JOIN customers c2 ON c2.id = ia2.customer_id;


-- ============================================================================
-- FUNCTION H (8th PL/pgSQL Function): calculate_account_centrality_metrics()
-- Structural hub & degree centrality helper in PostgreSQL
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_account_centrality_metrics(
    p_min_degree INT DEFAULT 1
)
RETURNS TABLE (
    account_id          UUID,
    account_number      VARCHAR(64),
    in_degree           BIGINT,
    out_degree          BIGINT,
    total_degree        BIGINT,
    total_volume        NUMERIC(15,2),
    is_structural_hub   BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH out_stats AS (
        SELECT
            t.sender_account_id AS acc_id,
            COUNT(DISTINCT t.receiver_account_id) AS out_deg,
            COALESCE(SUM(t.amount), 0) AS out_vol
        FROM transactions t
        WHERE t.status IN ('COMPLETED', 'FLAGGED')
        GROUP BY t.sender_account_id
    ),
    in_stats AS (
        SELECT
            t.receiver_account_id AS acc_id,
            COUNT(DISTINCT t.sender_account_id) AS in_deg,
            COALESCE(SUM(t.amount), 0) AS in_vol
        FROM transactions t
        WHERE t.status IN ('COMPLETED', 'FLAGGED')
        GROUP BY t.receiver_account_id
    )
    SELECT
        a.id AS account_id,
        a.account_number_masked AS account_number,
        COALESCE(i.in_deg, 0) AS in_degree,
        COALESCE(o.out_deg, 0) AS out_degree,
        (COALESCE(i.in_deg, 0) + COALESCE(o.out_deg, 0)) AS total_degree,
        (COALESCE(i.in_vol, 0) + COALESCE(o.out_vol, 0))::NUMERIC(15,2) AS total_volume,
        ((COALESCE(i.in_deg, 0) + COALESCE(o.out_deg, 0)) >= 10
         OR (COALESCE(i.in_deg, 0) >= 5 AND COALESCE(o.out_deg, 0) >= 5)) AS is_structural_hub
    FROM accounts a
    LEFT JOIN out_stats o ON o.acc_id = a.id
    LEFT JOIN in_stats i ON i.acc_id = a.id
    WHERE (COALESCE(i.in_deg, 0) + COALESCE(o.out_deg, 0)) >= p_min_degree
    ORDER BY total_degree DESC, total_volume DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- DML TRIGGER: log_record_audit_trigger()
-- Automated append-only differential audit stream for key tables
-- ============================================================================
CREATE OR REPLACE FUNCTION log_record_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_entity_id UUID;
    v_details JSONB;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        v_entity_id := OLD.id;
        v_details := jsonb_build_object('operation', TG_OP, 'table', TG_TABLE_NAME, 'old_data', to_jsonb(OLD));
    ELSIF (TG_OP = 'UPDATE') THEN
        v_entity_id := NEW.id;
        v_details := jsonb_build_object('operation', TG_OP, 'table', TG_TABLE_NAME, 'old_data', to_jsonb(OLD), 'new_data', to_jsonb(NEW));
    ELSE
        v_entity_id := NEW.id;
        v_details := jsonb_build_object('operation', TG_OP, 'table', TG_TABLE_NAME, 'new_data', to_jsonb(NEW));
    END IF;

    INSERT INTO audit_logs (action, entity_type, entity_id, details)
    VALUES (TG_OP || '_' || UPPER(TG_TABLE_NAME), UPPER(TG_TABLE_NAME), v_entity_id, v_details);

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
