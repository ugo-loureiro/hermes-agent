"""Dry-run Executor for Hermes OS Kernel."""

from __future__ import annotations

from .contracts import DryRunAction, DryRunResult, Plan
from .james_readonly import READONLY_TOOL_NAMES
from .policy import Policy


class Executor:
    """Maps intended calls but never performs mutative execution."""

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
                    would_call=_would_call_for_step(step.component, proposed.get("target", "")),
                    access="read_only" if proposed.get("type") in {"observe", "review", "audit"} else "simulated",
                    policy=policy,
                    payload_shape={
                        "objective": "str",
                        "step_id": step.step_id,
                        "approval_ref": "optional[str]",
                        "real_execution": False,
                    },
                )
            )
        return DryRunResult(objective=plan.objective, actions=tuple(actions), real_side_effects_executed=False, confidence=0.92)


def _would_call_for_step(component: str, target: str) -> str:
    if component == "Observer":
        return "observer.snapshot() -> Knowledge Fabric + JamesReadOnlyAdapter.collect() using " + ", ".join(READONLY_TOOL_NAMES)
    if component == "Supervisor":
        return "supervisor.review(snapshot) -> no James mutation"
    if component == "Planner":
        return f"planner scopes read-only follow-up for {target}; no execution"
    if component == "Executor":
        return "executor.dry_run(plan) only; mutative tools remain listed, not invoked"
    if "Learner" in component or "Audit" in component:
        return "learner.reflect() + audit.record(snapshot=...) without automatic memory writes"
    return "component contract call"
