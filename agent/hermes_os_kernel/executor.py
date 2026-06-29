"""Dry-run Executor for Hermes OS Kernel Phase 0."""

from __future__ import annotations

from .contracts import DryRunAction, DryRunResult, Plan
from .policy import Policy


class Executor:
    """Maps intended calls but never performs mutative execution in Phase 0."""

    def __init__(self, policy: Policy | None = None) -> None:
        self.policy = policy or Policy()

    def dry_run(self, plan: Plan) -> DryRunResult:
        actions: list[DryRunAction] = []
        for step in plan.steps:
            proposed = dict(step.proposed_action)
            proposed.setdefault("risk_level", step.risk_level)
            policy = self.policy.check(proposed)
            actions.append(
                DryRunAction(
                    step_id=step.step_id,
                    would_call=_would_call_for_component(step.component),
                    access="read_only" if proposed.get("type") in {"observe", "review", "audit"} else "simulated",
                    policy=policy,
                    payload_shape={"objective": "str", "step_id": step.step_id, "approval_ref": "optional[str]"},
                )
            )
        return DryRunResult(objective=plan.objective, actions=tuple(actions), real_side_effects_executed=False, confidence=0.91)


def _would_call_for_component(component: str) -> str:
    if component == "Observer":
        return "observer.snapshot() -> Knowledge Fabric + James read-only health/MCP"
    if component == "Supervisor":
        return "supervisor.review(snapshot)"
    if component == "Executor":
        return "executor.dry_run(plan) only; no mutative tool call"
    if "Learner" in component or "Audit" in component:
        return "learner.reflect() + audit.record() without automatic memory writes"
    return "component contract call"
