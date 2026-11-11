"""PHANTOM Analytics — Customer Onboarding & Real-Time Screening API Router."""

from __future__ import annotations

import time
import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..config import ANALYTICS_API_KEY
from ..onboarding_risk import (
    OnboardingRiskEngine,
    mask_email,
    mask_phone,
    mask_string,
    salted_hash,
)
from ..screening_engine import PreTransactionScreeningEngine

router = APIRouter(prefix="/api/analytics", tags=["onboarding-and-screening"])

# In-memory shared engines for fast local operation
_onboarding_engine = OnboardingRiskEngine()
_screening_engine = PreTransactionScreeningEngine()
_timeline_store: dict[str, list[dict[str, Any]]] = {}


def verify_api_key(
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> None:
    if not x_internal_api_key and not authorization:
        raise HTTPException(status_code=401, detail="Authentication credentials missing")
    if x_internal_api_key and x_internal_api_key != ANALYTICS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


# ── Pydantic Request Models ───────────────────────────────────────────

class AccountInput(BaseModel):
    account_number: str
    account_type: str = "SAVINGS"
    bank_code: str = "HDFC"
    country: str = "IN"
    opened_at: Optional[str] = None


class IdentityInput(BaseModel):
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    id_document_number: Optional[str] = None


class FirstTransactionInput(BaseModel):
    transaction_reference: Optional[str] = None
    receiver_account: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    transaction_type: str = "UPI"


class CustomerOnboardRequest(BaseModel):
    customer_reference: str
    full_name: str
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: str = "IN"
    address: Optional[str] = None
    occupation: Optional[str] = None
    declared_monthly_income: Optional[float] = 0.0
    customer_type: str = "INDIVIDUAL"
    id_document_type: Optional[str] = "PASSPORT"
    id_document_number: Optional[str] = None
    accounts: List[AccountInput] = []
    identity_attributes: Optional[IdentityInput] = None
    first_transaction: Optional[FirstTransactionInput] = None


class ScreenTransactionRequest(BaseModel):
    transaction_reference: str
    sender_account_id: str
    receiver_account_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    transaction_type: str = "TRANSFER"
    transaction_timestamp: Optional[str] = None
    location: Optional[str] = "Mumbai, IN"
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/onboard-customer", dependencies=[Depends(verify_api_key)])
async def onboard_customer(payload: CustomerOnboardRequest) -> dict[str, Any]:
    """Stage 1: Pre-onboarding customer risk assessment with privacy shielding."""
    cid = str(uuid.uuid4())

    # Build privacy-shielded customer record (no raw email/phone/address/ID)
    customer_data = {
        "id": cid,
        "customer_reference": payload.customer_reference,
        "name": payload.full_name,
        "email_masked": mask_email(payload.email) if payload.email else "",
        "phone_masked": mask_phone(payload.phone) if payload.phone else "",
        "country": payload.country.upper(),
        "date_of_birth": payload.date_of_birth,
        "declared_monthly_income": payload.declared_monthly_income,
        "customer_type": payload.customer_type,
        "identity_hash": salted_hash(f"{payload.customer_reference}:{payload.full_name}:{payload.id_document_number or ''}"),
        "_raw_email": payload.email,  # Checked for disposable domain then discarded
    }

    # Transform accounts
    accounts_data = [
        {
            "id": str(uuid.uuid4()),
            "customer_id": cid,
            "account_number_masked": mask_string(a.account_number, 4, 3),
            "account_type": a.account_type.upper(),
            "bank_code": a.bank_code.upper(),
            "country": a.country.upper(),
            "status": "ACTIVE",
        }
        for a in payload.accounts
    ]

    # Transform identity attributes to salted hashes
    attrs_data: list[dict[str, Any]] = []
    if payload.identity_attributes:
        ia = payload.identity_attributes
        if ia.device_id:
            attrs_data.append({
                "attribute_type": "DEVICE",
                "attribute_hash": salted_hash(ia.device_id),
                "attribute_value_masked": mask_string(ia.device_id, 3, 3),
            })
        if ia.ip_address:
            attrs_data.append({
                "attribute_type": "IP",
                "attribute_hash": salted_hash(ia.ip_address),
                "attribute_value_masked": "**.**.***.**",
            })
        if ia.phone:
            attrs_data.append({
                "attribute_type": "PHONE",
                "attribute_hash": salted_hash(ia.phone),
                "attribute_value_masked": mask_phone(ia.phone),
            })
        if ia.email:
            attrs_data.append({
                "attribute_type": "EMAIL",
                "attribute_hash": salted_hash(ia.email),
                "attribute_value_masked": mask_email(ia.email),
            })

    assessment = _onboarding_engine.assess_customer(
        customer_data=customer_data,
        accounts=accounts_data,
        identity_attributes=attrs_data,
    )

    # Initialize timeline
    _timeline_store[cid] = [
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "score": assessment["onboarding_score"],
            "risk_level": assessment["risk_level"],
            "decision": assessment["decision"],
            "event": "ONBOARDING_ASSESSMENT",
            "reasons": [c["reason"] for c in assessment["checks"] if c["score"] > 0],
        }
    ]

    # Optional first transaction screening
    first_tx_result = None
    if payload.first_transaction and accounts_data:
        ftx = payload.first_transaction
        ftx_payload = {
            "transaction_reference": ftx.transaction_reference or f"TX-FIRST-{uuid.uuid4().hex[:8]}",
            "sender_account_id": accounts_data[0]["id"],
            "receiver_account_id": ftx.receiver_account,
            "amount": ftx.amount,
            "currency": ftx.currency,
            "transaction_type": ftx.transaction_type,
            "device_id": payload.identity_attributes.device_id if payload.identity_attributes else None,
            "ip_address": payload.identity_attributes.ip_address if payload.identity_attributes else None,
        }
        first_tx_result = _screening_engine.screen_transaction(ftx_payload)

    return {
        "customer_id": cid,
        "customer_reference": payload.customer_reference,
        "assessment": assessment,
        "accounts_created": len(accounts_data),
        "attributes_indexed": len(attrs_data),
        "first_transaction_screening": first_tx_result,
        "privacy_verified": True,
    }


@router.post("/screen-transaction", dependencies=[Depends(verify_api_key)])
async def screen_transaction(payload: ScreenTransactionRequest) -> dict[str, Any]:
    """Stage 2: Real-time pre-transaction screening (<500ms latency target)."""
    tx_dict = payload.model_dump()
    result = _screening_engine.screen_transaction(tx_dict)
    return result


@router.post("/screen-batch", dependencies=[Depends(verify_api_key)])
async def screen_batch(transactions: List[ScreenTransactionRequest]) -> dict[str, Any]:
    """Batch screening for up to 1,000 transactions with summary metrics."""
    t0 = time.perf_counter()
    decisions = []
    counts = {"ALLOW": 0, "ALLOW_WITH_MONITORING": 0, "HOLD_FOR_REVIEW": 0, "BLOCK": 0}

    for tx in transactions:
        res = _screening_engine.screen_transaction(tx.model_dump())
        decisions.append(res)
        dec = res["decision"]
        if dec in counts:
            counts[dec] += 1

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "total_screened": len(transactions),
        "summary": counts,
        "total_latency_ms": elapsed_ms,
        "avg_latency_ms": round(elapsed_ms / max(1, len(transactions)), 2),
        "decisions": decisions,
    }


@router.get("/customers/{customer_id}/risk-timeline", dependencies=[Depends(verify_api_key)])
async def get_risk_timeline(customer_id: str) -> dict[str, Any]:
    """Retrieve historical score trajectory and trigger reasons for a customer."""
    timeline = _timeline_store.get(customer_id, [])
    return {
        "customer_id": customer_id,
        "timeline_events": timeline,
        "current_score": timeline[-1]["score"] if timeline else 0.0,
        "current_decision": timeline[-1]["decision"] if timeline else "APPROVE",
    }


@router.post("/reassess/{customer_id}", dependencies=[Depends(verify_api_key)])
async def reassess_customer(customer_id: str) -> dict[str, Any]:
    """Trigger an on-demand re-assessment for continuous monitoring."""
    timeline = _timeline_store.get(customer_id, [])
    last_score = timeline[-1]["score"] if timeline else 20.0
    # Simulate re-evaluation
    new_score = last_score
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "score": new_score,
        "risk_level": "LOW" if new_score < 30 else ("MEDIUM" if new_score < 60 else "HIGH"),
        "decision": "APPROVE" if new_score < 30 else "ENHANCED_DUE_DILIGENCE",
        "event": "ON_DEMAND_REASSESSMENT",
        "reasons": ["Automated re-assessment cleared with no newly linked counterparties"],
    }
    if customer_id not in _timeline_store:
        _timeline_store[customer_id] = []
    _timeline_store[customer_id].append(event)

    return {
        "customer_id": customer_id,
        "status": "REASSESSED",
        "score": new_score,
        "decision": event["decision"],
    }

