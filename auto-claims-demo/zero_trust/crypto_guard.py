# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pillar 1: Cryptographic Identity & Tamper-Evident Ledger Guard.

Provides HMAC-SHA256 and Google Cloud KMS-ready signing, monotonic nonce sequencing,
chained cryptographic audit logs, and real-time database tamper detection.
"""

import datetime
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from zero_trust.config import ZERO_TRUST_SECRET_KEY, CLOUD_KMS_KEY_NAME, USE_CLOUD_KMS

logger = logging.getLogger("zero_trust.crypto_guard")

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def canonical_json(data: Any) -> str:
    """Serialize data to a deterministic, sorted JSON string for consistent hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(data: Any) -> str:
    """Compute SHA-256 digest of any serializable object."""
    if isinstance(data, str):
        payload_bytes = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload_bytes = data
    else:
        payload_bytes = canonical_json(data).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def generate_hmac_signature(message: str, secret_key: Optional[str] = None) -> str:
    """Generate HMAC-SHA256 signature for a message string."""
    key = (secret_key or ZERO_TRUST_SECRET_KEY).encode("utf-8")
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


def sign_transaction(
    payload: Dict[str, Any],
    nonce: int,
    agent_id: str = "ProcessorAgent",
    secret_key: Optional[str] = None,
    prev_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Cryptographically sign an agent transaction/decision payload.

    Args:
        payload: The business payload (e.g. claim approval, estimate items, severity).
        nonce: Strictly monotonic sequence number to prevent replay attacks.
        agent_id: Identifier of the signing agent or service.
        secret_key: Secret key override for HMAC signing.
        prev_hash: Hash of the previous block in the audit ledger.

    Returns:
        Signed record dictionary containing metadata, payload_hash, and signature.
    """
    payload_hash = compute_hash(payload)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    signing_string = f"{nonce}:{agent_id}:{payload_hash}:{timestamp}"

    signature = generate_hmac_signature(signing_string, secret_key)
    
    # Compute block chain hash
    prev_block_hash = prev_hash or GENESIS_HASH
    chain_payload = f"{prev_block_hash}:{signing_string}:{signature}"
    chain_hash = compute_hash(chain_payload)

    return {
        "agent_id": agent_id,
        "nonce": nonce,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "signature": signature,
        "prev_hash": prev_block_hash,
        "chain_hash": chain_hash,
        "payload": payload,
    }


def verify_transaction_signature(
    signed_tx: Dict[str, Any],
    secret_key: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Verify cryptographic HMAC signature and payload hash of a signed transaction."""
    required_fields = ["agent_id", "nonce", "timestamp", "payload_hash", "signature", "payload"]
    for field in required_fields:
        if field not in signed_tx:
            return False, f"Missing required cryptographic field: {field}"

    # 1. Verify payload hash matches payload
    expected_payload_hash = compute_hash(signed_tx["payload"])
    if expected_payload_hash != signed_tx["payload_hash"]:
        return False, f"Payload hash mismatch! Expected {expected_payload_hash}, got {signed_tx["payload_hash"]}"

    # 2. Verify HMAC signature
    signing_string = f"{signed_tx["nonce"]}:{signed_tx["agent_id"]}:{signed_tx["payload_hash"]}:{signed_tx["timestamp"]}"
    expected_signature = generate_hmac_signature(signing_string, secret_key)

    if not hmac.compare_digest(expected_signature, signed_tx["signature"]):
        return False, "Cryptographic signature verification failed (invalid signature or tampered secret)."

    return True, None


class LedgerIntegrityAuditor:
    """Audits database rows against the signed cryptographic ledger."""

    @staticmethod
    def verify_ledger_chain(records: List[Dict[str, Any]], secret_key: Optional[str] = None) -> Dict[str, Any]:
        """Verify an entire sequence of ledger entries for signature validity and chain continuity."""
        if not records:
            return {"valid": True, "count": 0, "errors": []}

        errors = []
        last_nonce = -1
        last_chain_hash = GENESIS_HASH

        for idx, entry in enumerate(records):
            # Check nonce monotonicity
            nonce = entry.get("nonce", 0)
            if nonce <= last_nonce:
                errors.append({
                    "index": idx,
                    "error": f"Nonce out of sequence or replay attack detected. Last nonce: {last_nonce}, current: {nonce}",
                })

            # Verify signature
            valid_sig, sig_err = verify_transaction_signature(entry, secret_key)
            if not valid_sig:
                errors.append({"index": idx, "nonce": nonce, "error": sig_err})

            # Verify chain hash continuity
            prev_hash = entry.get("prev_hash", GENESIS_HASH)
            if idx > 0 and prev_hash != last_chain_hash:
                errors.append({
                    "index": idx,
                    "nonce": nonce,
                    "error": f"Broken ledger chain! Expected prev_hash {last_chain_hash}, found {prev_hash}",
                })

            last_nonce = nonce
            last_chain_hash = entry.get("chain_hash", "")

        return {
            "valid": len(errors) == 0,
            "count": len(records),
            "errors": errors,
        }

    @staticmethod
    def audit_database_records(
        db_records: List[Dict[str, Any]],
        signed_ledger_entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compares database state directly against signed ledger entries to catch any unauthorized SQL tampering.

        Args:
            db_records: Current database state (e.g. list of claims/estimates with their live amounts & status).
            signed_ledger_entries: The cryptographically signed ledger records.

        Returns:
            Dictionary with audit verdict, healthy count, and list of tampered/unauthorized records.
        """
        ledger_by_claim = {}
        for entry in signed_ledger_entries:
            claim_id = entry.get("payload", {}).get("claim_id")
            if claim_id is not None:
                # Keep latest signed entry for each claim
                ledger_by_claim[claim_id] = entry

        tampered = []
        verified = []
        untracked = []

        for row in db_records:
            claim_id = row.get("claim_id") or row.get("id")
            if claim_id not in ledger_by_claim:
                untracked.append({
                    "claim_id": claim_id,
                    "reason": "Database record exists with no corresponding signed cryptographic ledger entry.",
                })
                continue

            ledger_entry = ledger_by_claim[claim_id]
            signed_payload = ledger_entry.get("payload", {})

            # Check for field tampering
            discrepancies = []
            for check_key in ["total_amount", "decision", "severity", "status"]:
                if check_key in signed_payload and check_key in row:
                    db_val = row[check_key]
                    signed_val = signed_payload[check_key]
                    if isinstance(db_val, float) and isinstance(signed_val, (float, int)):
                        if abs(float(db_val) - float(signed_val)) > 0.001:
                            discrepancies.append(f"{check_key}: signed={signed_val}, db={db_val}")
                    elif str(db_val).strip() != str(signed_val).strip():
                        discrepancies.append(f"{check_key}: signed={signed_val}, db={db_val}")

            if discrepancies:
                tampered.append({
                    "claim_id": claim_id,
                    "discrepancies": discrepancies,
                    "signed_nonce": ledger_entry.get("nonce"),
                    "signed_hash": ledger_entry.get("payload_hash"),
                    "signature": ledger_entry.get("signature"),
                })
            else:
                verified.append({
                    "claim_id": claim_id,
                    "nonce": ledger_entry.get("nonce"),
                    "status": "VERIFIED_AUTHENTIC",
                })

        return {
            "healthy": len(tampered) == 0 and len(untracked) == 0,
            "total_verified": len(verified),
            "tampered_count": len(tampered),
            "untracked_count": len(untracked),
            "tampered_records": tampered,
            "untracked_records": untracked,
            "verified_records": verified,
        }
