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

"""Pillar 3: Semantic Gateway & Policy Firewall.

Enforces prompt injection/jailbreak screening, financial spend ceilings ($2,500 auto-approval cap),
damage severity coherence, and deterministic unit-test guards against rogue agent decisions.
"""

import enum
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from zero_trust.config import (
    COMPLEX_DAMAGE_AUTO_APPROVE_ALLOWED,
    MAX_AUTONOMOUS_APPROVAL_LIMIT,
)

logger = logging.getLogger("zero_trust.semantic_gateway")


class PolicyAction(str, enum.Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    QUARANTINE_FOR_REVIEW = "QUARANTINE_FOR_REVIEW"


@dataclass
class InspectionResult:
    action: PolicyAction
    passed: bool
    risk_score: float
    violations: List[str] = field(default_factory=list)
    reasoning: str = ""
    remediated_decision: Optional[str] = None


class PromptFirewall:
    """Detects and neutralizes adversarial prompt injection, jailbreaks, and fraud attempts."""

    INJECTION_PATTERNS = [
        (
            re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules|guidelines)", re.IGNORECASE),
            "Instruction override / jailbreak attempt detected.",
        ),
        (
            re.compile(r"disregard\s+(all\s+)?(safety|security|adjuster|policy)\s+(directives|rules|checks)", re.IGNORECASE),
            "Safety directive bypass attempt detected.",
        ),
        (
            re.compile(r"(override|change|set)\s+(severity|damage)\s+to\s+('|\")?simple('|\")?", re.IGNORECASE),
            "Adversarial severity manipulation detected.",
        ),
        (
            re.compile(r"(approve|payout|refund)\s+(claim\s+)?(immediately|without|regardless|auto)", re.IGNORECASE),
            "Forced claim approval bypass detected.",
        ),
        (
            re.compile(r"(issue|payout|transfer|send)\s+(a\s+)?(refund|claim|payment)\s+of\s+\$?\d{4,}", re.IGNORECASE),
            "Unauthorized high-value transaction injection detected.",
        ),
        (
            re.compile(r"(print|show|dump|reveal|leak|exfiltrate)\s+(the\s+)?(system\s+prompt|environment|api[_\s]key|secret)", re.IGNORECASE),
            "Credential / System prompt exfiltration probe detected.",
        ),
        (
            re.compile(r"(os\.environ|environ\.get|subprocess|exec\(|eval\()", re.IGNORECASE),
            "Code injection / environment variable extraction pattern detected.",
        ),
        (
            re.compile(r"you\s+are\s+now\s+(in|acting\s+as)\s+(developer|maintenance|unrestricted|god)\s+mode", re.IGNORECASE),
            "Persona switching / privilege escalation attempt detected.",
        ),
    ]

    @classmethod
    def inspect(cls, user_text: str) -> InspectionResult:
        if not user_text:
            return InspectionResult(action=PolicyAction.ALLOW, passed=True, risk_score=0.0)

        violations = []
        for pattern, desc in cls.INJECTION_PATTERNS:
            if pattern.search(user_text):
                violations.append(desc)

        if violations:
            risk = min(1.0, 0.4 + (0.3 * len(violations)))
            return InspectionResult(
                action=PolicyAction.BLOCK,
                passed=False,
                risk_score=risk,
                violations=violations,
                reasoning=f"Semantic Gateway Firewall Blocked Input: {'; '.join(violations)}",
            )

        return InspectionResult(
            action=PolicyAction.ALLOW,
            passed=True,
            risk_score=0.0,
            reasoning="Prompt passed all semantic security filters.",
        )


class AgentDecisionPolicyGuard:
    """Enforces deterministic business invariants, financial ceilings, and arithmetic integrity."""

    @staticmethod
    def validate(
        agent_output: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> InspectionResult:
        context = context or {}
        violations = []
        decision = agent_output.get("decision", "")
        estimate = agent_output.get("estimate", {}) or {}
        total_cost = float(estimate.get("total_cost", 0.0) or 0.0)
        severity = str(context.get("severity") or agent_output.get("severity") or "").lower()

        # 1. Financial Auto-Approval Ceiling Check
        if decision.lower() == "approved" and total_cost > MAX_AUTONOMOUS_APPROVAL_LIMIT:
            violations.append(
                f"Financial Ceiling Violation: Approved amount (${total_cost:,.2f}) exceeds autonomous limit (${MAX_AUTONOMOUS_APPROVAL_LIMIT:,.2f})."
            )

        # 2. Damage Severity vs Decision Coherence
        if "complex" in severity and decision.lower() == "approved":
            if not COMPLEX_DAMAGE_AUTO_APPROVE_ALLOWED:
                violations.append(
                    "Severity Coherence Violation: Claims with 'Complex' damage cannot be autonomously 'Approved' and mandate 'Review Required'."
                )

        # 3. Arithmetic Integrity Check
        items = estimate.get("items", [])
        total_labor = float(estimate.get("total_labor", 0.0) or 0.0)
        total_parts = float(estimate.get("total_parts", 0.0) or 0.0)
        expected_total = round(total_labor + total_parts, 2)

        if abs(total_cost - expected_total) > 0.01:
            violations.append(
                f"Arithmetic Discrepancy: total_cost (${total_cost}) != total_labor (${total_labor}) + total_parts (${total_parts})"
            )

        if violations:
            # Downgrade decision to Review Required
            return InspectionResult(
                action=PolicyAction.QUARANTINE_FOR_REVIEW,
                passed=False,
                risk_score=0.85,
                violations=violations,
                reasoning="; ".join(violations),
                remediated_decision="Review Required",
            )

        return InspectionResult(
            action=PolicyAction.ALLOW,
            passed=True,
            risk_score=0.0,
            reasoning="Agent decision complies with all zero-trust business policies.",
        )


def screen_claim_request(description: str, notes: str = "") -> InspectionResult:
    """Convenience helper to screen incoming claim user inputs."""
    combined = f"{description}\n{notes}".strip()
    return PromptFirewall.inspect(combined)


def enforce_decision_policy(
    agent_output: Dict[str, Any],
    severity: str = "",
    claim_id: Optional[int] = None,
) -> Tuple[Dict[str, Any], InspectionResult]:
    """Inspects and enforces security policies on agent output, automatically remediating if necessary."""
    inspection = AgentDecisionPolicyGuard.validate(
        agent_output, context={"severity": severity, "claim_id": claim_id}
    )
    
    final_output = dict(agent_output)
    if not inspection.passed and inspection.remediated_decision:
        final_output["original_decision"] = final_output.get("decision")
        final_output["decision"] = inspection.remediated_decision
        final_output["policy_enforcement"] = {
            "remediated": True,
            "violations": inspection.violations,
            "reasoning": inspection.reasoning,
        }
    else:
        final_output["policy_enforcement"] = {
            "remediated": False,
            "violations": [],
            "reasoning": "Compliant",
        }

    return final_output, inspection
