"""PHANTOM Analytics — FastAPI routers: analytics endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..anomaly_detection import AnomalyEngine
from ..blockchain import compute_hash, verify_record
from ..config import ANALYTICS_API_KEY
from ..graph_analysis import TransactionGraphEngine
from ..network_analysis import analyze_network
from ..risk_engine import RiskScoringEngine
from ..structuring_engine import StructuringEngine


async def verify_api_key(x_internal_api_key: str | None = Header(default=None)) -> str:
    """Validate internal API key between edge functions / clients and analytics service."""
    if not x_internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-API-Key header",
        )
    if x_internal_api_key != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Internal-API-Key",
        )
    return x_internal_api_key


router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(verify_api_key)],
)


# ── Pydantic v2 models ───────────────────────────────────────────────

class TransactionIn(BaseModel):
    transaction_id: str = ""
    sender_account_id: str
    receiver_account_id: str
    amount: float = Field(..., gt=0)
    transaction_date: str = ""
    transaction_timestamp: str = ""
    transaction_type: str = "RTGS"


class RiskScoreRequest(BaseModel):
    account_id: str
    transactions: list[TransactionIn]
    identity_attrs: list[dict[str, Any]] = Field(default_factory=list)
    counterparty_flags: dict[str, bool] = Field(default_factory=dict)
    velocity_spikes: list[dict[str, Any]] = Field(default_factory=list)
    profile: str = "default"


class RiskScoreResponse(BaseModel):
    account_id: str
    risk_score: float
    risk_level: str
    factors: list[dict[str, Any]]
    explanation: str


class BatchScoreRequest(BaseModel):
    account_ids: list[str]
    transactions: list[TransactionIn]
    identity_attrs_by_account: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    counterparty_flags: dict[str, bool] = Field(default_factory=dict)
    profile: str = "default"


class CycleRequest(BaseModel):
    transactions: list[TransactionIn]
    max_length: int = Field(default=5, ge=2, le=8)
    time_window_hours: int = Field(default=72, ge=1)


class StructuringRequest(BaseModel):
    account_id: str
    transactions: list[TransactionIn]
    threshold_min: float = 80_000
    threshold_max: float = 99_999
    window_hours: int = 24
    min_tx_count: int = 3


class RapidPassthroughRequest(BaseModel):
    account_id: str
    transactions: list[TransactionIn]
    max_delay_hours: int = 2
    retain_ratio_max: float = 0.10


class CentralityRequest(BaseModel):
    transactions: list[TransactionIn]


class BlockchainVerifyRequest(BaseModel):
    record: dict[str, Any]
    expected_hash: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/risk-score", response_model=RiskScoreResponse)
async def risk_score(req: RiskScoreRequest):
    txs = [t.model_dump() for t in req.transactions]
    engine = TransactionGraphEngine()
    engine.load_transactions(txs)
    scorer = RiskScoringEngine(profile=req.profile)
    result = scorer.score_account(
        account_id=req.account_id,
        transactions=txs,
        identity_attrs=req.identity_attrs or None,
        graph_engine=engine,
        counterparty_flags=req.counterparty_flags or None,
        velocity_spikes=req.velocity_spikes or None,
    )
    return RiskScoreResponse(**result)


@router.post("/score-batch")
async def score_batch(req: BatchScoreRequest):
    txs = [t.model_dump() for t in req.transactions]
    scorer = RiskScoringEngine(profile=req.profile)
    results = scorer.score_batch(
        account_ids=req.account_ids,
        transactions=txs,
        identity_attrs_by_account=req.identity_attrs_by_account or None,
        counterparty_flags=req.counterparty_flags or None,
    )
    return {"count": len(results), "scores": results}


@router.post("/detect-cycles")
@router.post("/cycles")
async def detect_cycles(req: CycleRequest):
    txs = [t.model_dump() for t in req.transactions]
    engine = TransactionGraphEngine()
    engine.load_transactions(txs)
    cycles = engine.detect_cycles(max_length=req.max_length, time_window_hours=req.time_window_hours)
    return {"cycles": cycles}


@router.post("/detect-structuring")
async def detect_structuring(req: StructuringRequest):
    txs = [t.model_dump() for t in req.transactions]
    patterns = StructuringEngine.detect_structuring_patterns(
        txs, req.account_id, req.threshold_min, req.threshold_max,
        req.window_hours, req.min_tx_count,
    )
    return {"patterns": patterns}


@router.post("/detect-rapid-passthrough")
async def detect_rapid_passthrough(req: RapidPassthroughRequest):
    txs = [t.model_dump() for t in req.transactions]
    events = AnomalyEngine.detect_rapid_pass_through(
        txs, req.account_id, req.max_delay_hours, req.retain_ratio_max,
    )
    return {"events": events}


@router.post("/centrality")
async def centrality(req: CentralityRequest):
    txs = [t.model_dump() for t in req.transactions]
    engine = TransactionGraphEngine()
    engine.load_transactions(txs)
    return {"centralities": engine.calculate_centralities()}


@router.post("/clusters")
async def clusters(req: CentralityRequest):
    txs = [t.model_dump() for t in req.transactions]
    return analyze_network(txs)


@router.post("/verify-blockchain")
@router.post("/verify-record")
async def verify_blockchain(req: BlockchainVerifyRequest):
    h = compute_hash(req.record)
    if req.expected_hash:
        valid = verify_record(req.record, req.expected_hash)
        return {
            "hash": h,
            "expected_hash": req.expected_hash,
            "valid": valid,
            "status": "VERIFIED" if valid else "TAMPERED",
        }
    return {"hash": h, "status": "HASHED"}
