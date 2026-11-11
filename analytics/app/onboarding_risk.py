"""PHANTOM — New Customer Onboarding Risk Assessment Engine (Stage 1).

Evaluates linkage and consistency signals before customer has transaction history.
Implements ONB_001 to ONB_007 with privacy-safe salted hashing (no raw PII stored/logged).
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import date, datetime
from typing import Any

SALT = os.getenv("PHANTOM_HASH_SALT", "PHANTOM_DEFAULT_SALT_2026").encode("utf-8")

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwawaymail.com", "yopmail.com", "sharklasers.com", "trashmail.com",
}

HIGH_RISK_COUNTRIES = {"KP", "IR", "SY", "MM", "CU"}  # Placeholder FATF-style risk list
HIGH_RISK_ACCOUNT_TYPES = {"CRYPTO_WALLET": 10.0, "ESCROW": 5.0}


def salted_hash(value: str) -> str:
    """Deterministic salted SHA-256 for privacy-preserving attribute matching."""
    if not value:
        return ""
    h = hashlib.sha256(SALT)
    h.update(value.strip().lower().encode("utf-8"))
    return h.hexdigest()


def mask_string(val: str, prefix_len: int = 2, suffix_len: int = 2) -> str:
    """Mask sensitive string, showing only minimal prefix and suffix."""
    if not val:
        return ""
    val = val.strip()
    if len(val) <= prefix_len + suffix_len:
        return "*" * len(val)
    return f"{val[:prefix_len]}***{val[-suffix_len:]}"


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return mask_string(email)
    user, domain = email.strip().split("@", 1)
    masked_user = f"{user[0]}***" if len(user) > 1 else "*"
    return f"{masked_user}@{domain}"


def mask_phone(phone: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if len(cleaned) < 6:
        return "***"
    return f"{cleaned[:5]}***{cleaned[-2:]}"


class OnboardingRiskEngine:
    """Evaluates onboarding risk checks (ONB_001 to ONB_007)."""

    def __init__(self, existing_attributes: list[dict[str, Any]] | None = None, existing_customers: list[dict[str, Any]] | None = None, clusters: list[dict[str, Any]] | None = None) -> None:
        self.attributes = existing_attributes or []
        self.customers = existing_customers or []
        self.clusters = clusters or []

        # Index attributes by (type, hash) -> list of records
        self._attr_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for a in self.attributes:
            key = (str(a.get("attribute_type", "")), str(a.get("attribute_hash", "")))
            if key not in self._attr_index:
                self._attr_index[key] = []
            self._attr_index[key].append(a)

        # Index customers by identity_hash
        self._cust_by_hash: dict[str, list[dict[str, Any]]] = {}
        for c in self.customers:
            h = str(c.get("identity_hash", ""))
            if h:
                if h not in self._cust_by_hash:
                    self._cust_by_hash[h] = []
                self._cust_by_hash[h].append(c)

    def assess_customer(
        self,
        customer_data: dict[str, Any],
        accounts: list[dict[str, Any]],
        identity_attributes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Perform pre-onboarding risk scoring and return explainable decision."""
        checks: list[dict[str, Any]] = []
        matched_entities: list[dict[str, Any]] = []
        total_score = 0.0

        # Check ONB_001: Shared device / IP collision
        c1, matches1 = self._check_onb_001(identity_attributes)
        checks.append(c1)
        matched_entities.extend(matches1)
        total_score += c1["score"]

        # Check ONB_002: Linked to flagged entities (HIGH / CRITICAL)
        c2, matches2 = self._check_onb_002(identity_attributes)
        checks.append(c2)
        matched_entities.extend(matches2)
        total_score += c2["score"]

        # Check ONB_003: Duplicate / near-duplicate identity
        c3, matches3 = self._check_onb_003(customer_data)
        checks.append(c3)
        matched_entities.extend(matches3)
        total_score += c3["score"]

        # Check ONB_004: Cluster membership
        c4 = self._check_onb_004(identity_attributes, matched_entities)
        checks.append(c4)
        total_score += c4["score"]

        # Check ONB_005: High-risk country or account type
        c5 = self._check_onb_005(customer_data, accounts)
        checks.append(c5)
        total_score += c5["score"]

        # Check ONB_006: Data quality & consistency
        c6 = self._check_onb_006(customer_data)
        checks.append(c6)
        total_score += c6["score"]

        # Check ONB_007: Income vs expected activity (initial check)
        c7 = self._check_onb_007(customer_data)
        checks.append(c7)
        total_score += c7["score"]

        final_score = round(min(100.0, total_score), 2)
        decision = self._classify_decision(final_score)
        risk_level = self._classify_risk_level(final_score)

        return {
            "onboarding_score": final_score,
            "risk_level": risk_level,
            "decision": decision,
            "checks": checks,
            "matched_entities": matched_entities,
            "assessed_at": datetime.utcnow().isoformat() + "Z",
        }

    # ── Check Implementations ──────────────────────────────────────────

    def _check_onb_001(self, new_attrs: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """ONB_001 — Shared device / IP with existing accounts (max 30 pts)."""
        max_score = 30.0
        matches = []
        weight = 0.0

        for attr in new_attrs:
            atype = attr.get("attribute_type", "")
            ahash = attr.get("attribute_hash", "")
            if atype in ("DEVICE", "IP") and (atype, ahash) in self._attr_index:
                hits = self._attr_index[(atype, ahash)]
                for hit in hits:
                    matches.append({
                        "attribute_type": atype,
                        "attribute_value_masked": hit.get("attribute_value_masked", "***"),
                        "matched_customer_id": hit.get("customer_id"),
                        "source": "EXISTING_NETWORK",
                    })
                # Check if matched entity is HIGH/CRITICAL
                has_high_risk = any(
                    h.get("risk_level") in ("HIGH", "CRITICAL") or float(h.get("risk_score", 0)) >= 60.0
                    for h in hits
                )
                weight += 30.0 if has_high_risk else 15.0

        score = min(max_score, weight)
        reason = f"{len(matches)} shared hardware/network collision(s) detected" if matches else "No shared device/IP collision"
        return {
            "rule_id": "ONB_001",
            "name": "Shared Device / IP with Existing Accounts",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"match_count": len(matches)},
        }, matches

    def _check_onb_002(self, new_attrs: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """ONB_002 — Linked to flagged or investigated entities (max 30 pts)."""
        max_score = 30.0
        matches = []

        for attr in new_attrs:
            atype = attr.get("attribute_type", "")
            ahash = attr.get("attribute_hash", "")
            if (atype, ahash) in self._attr_index:
                hits = self._attr_index[(atype, ahash)]
                flagged_hits = [
                    h for h in hits
                    if h.get("risk_level") in ("HIGH", "CRITICAL") or float(h.get("risk_score", 0)) >= 60.0
                ]
                for fh in flagged_hits:
                    matches.append({
                        "attribute_type": atype,
                        "matched_customer_id": fh.get("customer_id"),
                        "risk_level": fh.get("risk_level", "HIGH"),
                    })

        score = max_score if matches else 0.0
        reason = f"Identity matches {len(matches)} previously flagged high-risk entities" if matches else "No link to flagged entities"
        return {
            "rule_id": "ONB_002",
            "name": "Linked to Flagged / Investigated Entities",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"flagged_links": len(matches)},
        }, matches

    def _check_onb_003(self, customer_data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """ONB_003 — Duplicate or near-duplicate identity (max 20 pts)."""
        max_score = 20.0
        id_hash = customer_data.get("identity_hash", "")
        name = customer_data.get("full_name", "").strip().lower()

        matches = []
        if id_hash and id_hash in self._cust_by_hash:
            for hit in self._cust_by_hash[id_hash]:
                matches.append({
                    "matched_customer_id": hit.get("id"),
                    "customer_reference": hit.get("customer_reference"),
                    "match_type": "EXACT_HASH",
                })

        score = max_score if matches else 0.0
        reason = f"Duplicate identity match found ({len(matches)} existing record)" if matches else "Identity is unique"
        return {
            "rule_id": "ONB_003",
            "name": "Duplicate / Near-Duplicate Identity",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"matches": matches},
        }, matches

    def _check_onb_004(self, new_attrs: list[dict[str, Any]], matched_entities: list[dict[str, Any]]) -> dict[str, Any]:
        """ONB_004 — Cluster membership (max 15 pts)."""
        max_score = 15.0
        hit_cust_ids = {m.get("matched_customer_id") for m in matched_entities if m.get("matched_customer_id")}

        cluster_hits = []
        for cl in self.clusters:
            c_members = cl.get("entity_ids", [])
            if isinstance(c_members, str):
                import json
                try:
                    c_members = json.loads(c_members)
                except Exception:
                    c_members = []
            if any(cid in hit_cust_ids for cid in c_members):
                cluster_hits.append(cl.get("cluster_name", "Unknown Cluster"))

        score = max_score if cluster_hits else 0.0
        reason = f"Associated with {len(cluster_hits)} active network cluster(s)" if cluster_hits else "No known cluster associations"
        return {
            "rule_id": "ONB_004",
            "name": "Cluster Membership Link",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"clusters": cluster_hits},
        }

    def _check_onb_005(self, customer_data: dict[str, Any], accounts: list[dict[str, Any]]) -> dict[str, Any]:
        """ONB_005 — High-risk country or account type (max 10 pts)."""
        max_score = 10.0
        score = 0.0
        factors = []

        country = customer_data.get("country", "").upper()
        if country in HIGH_RISK_COUNTRIES:
            score += 10.0
            factors.append(f"High-risk jurisdiction ({country})")

        for acc in accounts:
            atype = acc.get("account_type", "").upper()
            if atype in HIGH_RISK_ACCOUNT_TYPES:
                pts = HIGH_RISK_ACCOUNT_TYPES[atype]
                score += pts
                factors.append(f"High-risk account type ({atype}: +{pts}pts)")

        score = min(max_score, score)
        reason = "; ".join(factors) if factors else "Standard jurisdiction and account types"
        return {
            "rule_id": "ONB_005",
            "name": "High-Risk Country or Account Type",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"factors": factors},
        }

    def _check_onb_006(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """ONB_006 — Data quality and consistency (max 10 pts)."""
        max_score = 10.0
        score = 0.0
        issues = []

        raw_email = customer_data.get("_raw_email", "")
        if raw_email and "@" in raw_email:
            domain = raw_email.split("@")[1].lower()
            if domain in DISPOSABLE_EMAIL_DOMAINS:
                score += 5.0
                issues.append(f"Disposable email domain detected ({domain})")

        dob_str = customer_data.get("date_of_birth")
        if dob_str:
            try:
                dob = date.fromisoformat(str(dob_str))
                age = (date.today() - dob).days // 365
                if age < 18:
                    score += 10.0
                    issues.append(f"Applicant is under legal age (Age: {age})")
                elif age > 110:
                    score += 5.0
                    issues.append(f"Implausible age ({age})")
            except Exception:
                issues.append("Invalid date of birth format")

        score = min(max_score, score)
        reason = "; ".join(issues) if issues else "Data passed standard quality checks"
        return {
            "rule_id": "ONB_006",
            "name": "Data Quality and Consistency",
            "score": score,
            "max_score": max_score,
            "reason": reason,
            "evidence": {"issues": issues},
        }

    def _check_onb_007(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """ONB_007 — Income vs expected activity baseline (max 10 pts)."""
        max_score = 10.0
        income = float(customer_data.get("declared_monthly_income") or 0.0)
        ctype = customer_data.get("customer_type", "INDIVIDUAL").upper()

        score = 0.0
        notes = "Income baseline registered"
        if income > 0 and income < 1000 and ctype == "BUSINESS":
            score = 10.0
            notes = "Business income declaration suspiciously low"

        return {
            "rule_id": "ONB_007",
            "name": "Income vs Expected Activity",
            "score": score,
            "max_score": max_score,
            "reason": notes,
            "evidence": {"declared_income": income, "customer_type": ctype},
        }

    @staticmethod
    def _classify_decision(score: float) -> str:
        if score < 30.0:
            return "APPROVE"
        if score < 60.0:
            return "ENHANCED_DUE_DILIGENCE"
        if score < 80.0:
            return "MANUAL_REVIEW"
        return "ESCALATE"

    @staticmethod
    def _classify_risk_level(score: float) -> str:
        if score < 30.0:
            return "LOW"
        if score < 60.0:
            return "MEDIUM"
        if score < 80.0:
            return "HIGH"
        return "CRITICAL"

