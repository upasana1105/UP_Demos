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

"""Zero-Trust Architecture for Autonomous Google ADK Agents."""

from zero_trust.crypto_guard import (
    GENESIS_HASH,
    LedgerIntegrityAuditor,
    compute_hash,
    generate_hmac_signature,
    sign_transaction,
    verify_transaction_signature,
)
from zero_trust.sandbox import (
    ASTSecurityInspector,
    SandboxResult,
    execute_sandboxed,
    inspect_code_safety,
    sandboxed_repair_cost_calculator,
)
from zero_trust.semantic_gateway import (
    AgentDecisionPolicyGuard,
    InspectionResult,
    PolicyAction,
    PromptFirewall,
    enforce_decision_policy,
    screen_claim_request,
)
from zero_trust.adk_interceptor import (
    ZeroTrustSecurityManager,
    generate_repair_cost_sandboxed,
    security_manager,
)

__all__ = [
    "compute_hash",
    "generate_hmac_signature",
    "sign_transaction",
    "verify_transaction_signature",
    "LedgerIntegrityAuditor",
    "GENESIS_HASH",
    "ASTSecurityInspector",
    "SandboxResult",
    "execute_sandboxed",
    "inspect_code_safety",
    "sandboxed_repair_cost_calculator",
    "PromptFirewall",
    "AgentDecisionPolicyGuard",
    "InspectionResult",
    "PolicyAction",
    "screen_claim_request",
    "enforce_decision_policy",
    "ZeroTrustSecurityManager",
    "generate_repair_cost_sandboxed",
    "security_manager",
]
