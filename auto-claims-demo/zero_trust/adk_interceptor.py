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

"""ADK Interceptor & Plugins for Zero-Trust Architecture.

Provides drop-in tool decorators, before/after agent callbacks, and cryptographic
ledger recording for Google ADK agents.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional, Tuple

from zero_trust.crypto_guard import (
    GENESIS_HASH,
    LedgerIntegrityAuditor,
    sign_transaction,
    verify_transaction_signature,
)
from zero_trust.sandbox import sandboxed_repair_cost_calculator
from zero_trust.semantic_gateway import (
    PolicyAction,
    PromptFirewall,
    enforce_decision_policy,
)

logger = logging.getLogger("zero_trust.adk_interceptor")


# --- Sandboxed Tool for Processor Agent ---
def generate_repair_cost_sandboxed(severity: str, state: str = "") -> dict:
    """Zero-Trust Sandboxed Tool: Generates itemized repair costs inside gVisor-isolated container."""
    return sandboxed_repair_cost_calculator(severity=severity, state=state)


class ZeroTrustSecurityManager:
    """Unified manager coordinating Cryptographic Identity, Sandbox, and Semantic Gateway."""

    def __init__(self):
        self._nonce_counter = 0
        self._last_chain_hash = GENESIS_HASH
        self._in_memory_ledger = []

    def get_next_nonce(self) -> int:
        self._nonce_counter += 1
        return self._nonce_counter

    def inspect_user_prompt(self, prompt: str) -> Dict[str, Any]:
        """Runs input through Semantic Gateway firewall."""
        res = PromptFirewall.inspect(prompt)
        return {
            "allowed": res.passed,
            "action": res.action.value,
            "risk_score": res.risk_score,
            "violations": res.violations,
            "reasoning": res.reasoning,
        }

    def process_and_sign_agent_decision(
        self,
        decision_raw: Any,
        severity: str = "",
        claim_id: Optional[int] = None,
        agent_id: str = "ProcessorAgent",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Validates agent decision against deterministic policy and cryptographically signs it.

        Returns:
            (remediated_payload, signed_ledger_record)
        """
        # Parse JSON if string
        if isinstance(decision_raw, str):
            try:
                payload = json.loads(decision_raw)
            except Exception:
                payload = {"raw_output": decision_raw, "decision": "Review Required"}
        elif isinstance(decision_raw, dict):
            payload = dict(decision_raw)
        else:
            payload = {"decision": "Review Required"}

        # 1. Enforce Semantic Gateway Policy (Spend ceiling, severity consistency)
        enforced_payload, policy_result = enforce_decision_policy(
            payload, severity=severity, claim_id=claim_id
        )

        # Include claim_id in payload for database auditing
        if claim_id is not None:
            enforced_payload["claim_id"] = claim_id
        if severity:
            enforced_payload["severity"] = severity

        # 2. Cryptographically Sign Transaction
        nonce = self.get_next_nonce()
        signed_tx = sign_transaction(
            payload=enforced_payload,
            nonce=nonce,
            agent_id=agent_id,
            prev_hash=self._last_chain_hash,
        )

        self._last_chain_hash = signed_tx["chain_hash"]
        self._in_memory_ledger.append(signed_tx)

        return enforced_payload, signed_tx

    def get_ledger_status(self) -> Dict[str, Any]:
        return LedgerIntegrityAuditor.verify_ledger_chain(self._in_memory_ledger)


# Global singleton instance
security_manager = ZeroTrustSecurityManager()
