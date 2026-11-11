// Supabase Edge Function: ingest-transactions
// Validates CSV / JSON transaction imports and persists to PostgreSQL via Supabase client.
import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const VALID_TYPES = new Set(["WIRE", "UPI", "NEFT", "RTGS", "INTERNAL_TRANSFER", "ATM"]);

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const body = await req.json();
    const rows: Record<string, unknown>[] = Array.isArray(body.transactions) ? body.transactions : [];

    const errors: string[] = [];
    const validRows: Record<string, unknown>[] = [];
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      const amount = Number(r.amount);
      const txType = String(r.transaction_type ?? "WIRE");
      if (!r.transaction_reference || !r.sender_account_id || !r.receiver_account_id) {
        errors.push(`Row ${i}: missing required account or reference field`);
        continue;
      }
      if (!Number.isFinite(amount) || amount <= 0) {
        errors.push(`Row ${i}: amount must be > 0`);
        continue;
      }
      if (!VALID_TYPES.has(txType)) {
        errors.push(`Row ${i}: invalid transaction_type ${txType}`);
        continue;
      }
      validRows.push({
        transaction_reference: r.transaction_reference,
        sender_account_id: r.sender_account_id,
        receiver_account_id: r.receiver_account_id,
        amount,
        currency: r.currency ?? "INR",
        transaction_type: txType,
        transaction_timestamp: r.transaction_timestamp ?? new Date().toISOString(),
        status: r.status ?? "COMPLETED",
      });
    }

    if (supabaseUrl && serviceKey && validRows.length > 0) {
      const client = createClient(supabaseUrl, serviceKey);
      const { error } = await client
        .from("transactions")
        .upsert(validRows, { onConflict: "transaction_reference" });
      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
    }

    return new Response(
      JSON.stringify({
        accepted: validRows.length,
        rejected: errors.length,
        errors,
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : "Ingest error" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
