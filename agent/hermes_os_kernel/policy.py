"""Policy/Gates for Hermes OS Kernel Phase 0.

The policy layer is conservative by construction. Phase 0 allows read-only and
simulated actions only; sensitive areas stay gated even in dry-run metadata.
"""

from __future__ import annotations

from typing import Any

from .contracts import PolicyDecision, RiskLevel

SENSITIVE_TARGET_MARKERS = (
    "whatsapp",
    "telegram_real",
    "pix",
    "santander",
    "host",
    "api-interna",
    "cloudflare",
    "nginx",
    "sqlserver",
    "customer_contact",
    "real_side_effect",
)

MUTATIVE_ACTION_MARKERS = (
    "send",
    "post_real",
    "restart",
    "rebuild",
    "deploy",
    "write",
    "update",
    "delete",
    "migrate",
    "charge",
    "cancel",
    "flip_flag",
)


def _risk_rank(risk_level: RiskLevel) -> int:
    return int(risk_level[1]) if risk_level.startswith("R") and risk_level[1:].isdigit() else 5


class Policy:
    """Autonomy gatekeeper for Hermes OS.

    Public contract: ``policy.check(action)`` where action is a mapping with
    type/target/risk_level/side_effects/approval_ref fields.
    """

    def check(self, action: dict[str, Any]) -> PolicyDecision:
        action_type = str(action.get("type", "read")).lower()
        target = str(action.get("target", "")).lower()
        risk_level = str(action.get("risk_level", "R0")).upper()
        if risk_level not in {"R0", "R1", "R2", "R3", "R4", "R5"}:
            risk_level = "R5"
        side_effects = bool(action.get("side_effects", False))
        approval_ref = action.get("approval_ref")

        gates: list[str] = []
        reasons: list[str] = []
        requires_approval = False

        if any(marker in target for marker in SENSITIVE_TARGET_MARKERS):
            requires_approval = True
            gates.append("sensitive_target")
            reasons.append("target touches sensitive boundary/channel")

        if any(marker in action_type for marker in MUTATIVE_ACTION_MARKERS) or side_effects:
            requires_approval = True
            gates.append("mutative_or_side_effecting_action")
            reasons.append("action is mutative or may cause real side effects")

        if _risk_rank(risk_level) >= 2:
            requires_approval = True
            gates.append("risk_r2_or_above")
            reasons.append("risk level requires Ugo approval")

        phase0_allows = action_type in {"read", "observe", "plan", "review", "simulate", "dry_run", "reflect", "audit"}
        allowed = phase0_allows and not side_effects
        if requires_approval and not approval_ref:
            allowed = False
            reasons.append("approval_ref absent")
        if approval_ref and phase0_allows and not side_effects:
            # Approval can document a dry-run, but Phase 0 still does not execute mutations.
            allowed = True

        if not reasons:
            reasons.append("read-only or simulated Phase 0 action")
        return PolicyDecision(
            allowed=allowed,
            requires_ugo_approval=requires_approval,
            risk_level=risk_level,  # type: ignore[arg-type]
            reasons=tuple(reasons),
            gates=tuple(gates),
        )
