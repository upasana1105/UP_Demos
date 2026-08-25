#!/usr/bin/env python3
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

"""Example 3: Cryptographic Identity, HMAC Signing & Database Tamper Detection.

Demonstrates how agent decisions are HMAC-signed with monotonic nonces and Merkle hashes,
and how mathematical discrepancy detection catches unauthorized database modifications.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from zero_trust.crypto_guard import (
    GENESIS_HASH,
    LedgerIntegrityAuditor,
    sign_transaction,
    verify_transaction_signature,
)


def run_example():
    print("=" * 70)
    print("EXAMPLE 3: Cryptographic Identity & Tamper-Evident Ledger")
    print("=" * 70)

    # 1. Sign Claim Decision #1
    claim_1 = {
        "claim_id": 101,
        "total_amount": 750.00,
        "decision": "Approved",
        "severity": "Simple",
        "status": "Assessed",
    }
    signed_block_1 = sign_transaction(
        payload=claim_1,
        nonce=1,
        agent_id="ProcessorAgent",
        prev_hash=GENESIS_HASH,
    )

    print("\n[Step 1] Cryptographically Signing Claim #101 Approval:")
    print(f"  - Nonce         : #{signed_block_1['nonce']}")
    print(f"  - Payload Hash  : {signed_block_1['payload_hash']}")
    print(f"  - HMAC Signature: {signed_block_1['signature']}")
    print(f"  - Block Chain   : {signed_block_1['chain_hash']}")

    is_valid, _ = verify_transaction_signature(signed_block_1)
    print(f"  - Signature Check: {'✅ Valid' if is_valid else '❌ Invalid'}")

    # 2. Sign Claim Decision #2 (Chained to Block #1)
    claim_2 = {
        "claim_id": 102,
        "total_amount": 3200.00,
        "decision": "Review Required",
        "severity": "Complex",
        "status": "Review Required",
    }
    signed_block_2 = sign_transaction(
        payload=claim_2,
        nonce=2,
        agent_id="ProcessorAgent",
        prev_hash=signed_block_1["chain_hash"],
    )

    print("\n[Step 2] Cryptographically Signing Claim #102 Approval (Chained):")
    print(f"  - Nonce         : #{signed_block_2['nonce']}")
    print(f"  - Prev Block    : {signed_block_2['prev_hash']}")
    print(f"  - HMAC Signature: {signed_block_2['signature']}")
    print(f"  - Block Chain   : {signed_block_2['chain_hash']}")

    # 3. Simulate an Out-of-Band Database Tamper Attack
    print("\n" + "-" * 70)
    print("[Step 3] Attack Simulation: Rogue DB Modification")
    print("A rogue database admin updates Claim #101 in SQLite: total_amount: $750.00 -> $12,500.00")

    db_state = [
        {"id": 101, "claim_id": 101, "total_amount": 12500.00, "decision": "Approved", "status": "Assessed"},
        {"id": 102, "claim_id": 102, "total_amount": 3200.00, "decision": "Review Required", "status": "Review Required"},
    ]

    # Run Auditor
    audit_report = LedgerIntegrityAuditor.audit_database_records(db_state, [signed_block_1, signed_block_2])

    print("\nAudit Verification Result:")
    print(f"  - Overall Healthy: {audit_report['healthy']}")
    print(f"  - Verified Count : {audit_report['total_verified']}")
    print(f"  - Tampered Count : {audit_report['tampered_count']}")

    if not audit_report["healthy"]:
        print("  - Tampered Alert Details:")
        for t in audit_report["tampered_records"]:
            print(f"    ⚠️ Claim #{t['claim_id']}: Discrepancies -> {t['discrepancies']}")
            print(f"       Expected Hash: {t['signed_hash']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_example()
