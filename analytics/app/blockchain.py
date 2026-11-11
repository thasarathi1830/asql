"""PHANTOM Analytics — Blockchain integrity (canonical JSON + SHA-256)."""

import hashlib
import json
from typing import Any

# Fields that are volatile / system-generated and must be stripped before hashing.
_VOLATILE_FIELDS = frozenset({
    "blockchain_hash",
    "blockchain_tx_id",
    "verification_status",
    "created_at",
})


def canonical_json(record: dict[str, Any]) -> str:
    """Return a deterministic JSON string for *record*.

    * Strips volatile fields listed in ``_VOLATILE_FIELDS``.
    * Sorts keys recursively.
    * Serialises with ``ensure_ascii=False`` for UTF-8 transparency and
      no trailing whitespace.
    """
    cleaned = {k: v for k, v in record.items() if k not in _VOLATILE_FIELDS}
    return json.dumps(cleaned, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_hash(record: dict[str, Any]) -> str:
    """Compute a ``0x``-prefixed SHA-256 hex digest of *record*'s canonical form."""
    payload = canonical_json(record).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"0x{digest}"


def verify_record(record: dict[str, Any], expected_hash: str) -> bool:
    """Return ``True`` when the hash of *record* matches *expected_hash*.

    The comparison is case-insensitive and tolerates the ``0x`` prefix
    being present or absent on either side.
    """
    actual = compute_hash(record)
    # Normalise both to lowercase without prefix for comparison.
    def _strip(h: str) -> str:
        return h.lower().removeprefix("0x")

    return _strip(actual) == _strip(expected_hash)
