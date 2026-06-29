"""Planner component for Hermes OS Kernel Phase 0."""

from __future__ import annotations

from .contracts import Objective, Plan, PlanStep, Review, Snapshot, SourceRef


class Planner:
    """Turns Ugo objectives into plans without execution."""

    def plan(self, objective: Objective, snapshot: Snapshot | None = None, review: Review | None = None) -> Plan:
        sources: list[SourceRef] = []
        if snapshot:
            sources.extend(snapshot.sources)
        if not sources:
            sources.append(SourceRef("Planner input", "objective", "local_artifact", 0.7))

        steps = (
            PlanStep(
                step_id="observe-current-state",
                component="Observer",
                description="Collect James health, container inventory, queues/status artifacts and Knowledge Fabric context using read-only channels.",
                risk_level="R0",
                success_criteria=("No side effects", "Snapshot includes source list and confidence"),
                proposed_action={"type": "observe", "target": "james_readonly", "side_effects": False},
            ),
            PlanStep(
                step_id="review-state-vs-objective",
                component="Supervisor",
                description="Compare current state with objective success criteria and classify risk/blockers.",
                dependencies=("observe-current-state",),
                risk_level="R0",
                success_criteria=("Findings are evidence-backed",),
                proposed_action={"type": "review", "target": "hermes_os", "side_effects": False},
            ),
            PlanStep(
                step_id="simulate-next-actions",
                component="Executor",
                description="Map tools/APIs/MCP calls that would be used, but keep them simulated or read-only.",
                dependencies=("review-state-vs-objective",),
                risk_level="R1",
                success_criteria=("Mutative actions remain dry-run only", "Policy decision attached to every action"),
                proposed_action={"type": "dry_run", "target": "james_tools", "side_effects": False},
            ),
            PlanStep(
                step_id="reflect-and-document",
                component="Learner/Audit",
                description="Recommend learnings/memory/skills and record an audit trail without applying memory writes automatically.",
                dependencies=("simulate-next-actions",),
                risk_level="R0",
                success_criteria=("Audit record contains objective, sources, plan, risk, confidence and approval need",),
                proposed_action={"type": "audit", "target": "hermes_os", "side_effects": False},
            ),
        )
        risks = [
            "Phase 0 must not mutate James runtime, Copilot, providers, configs, channels or financial systems.",
            "Health/status endpoints without auth provide partial visibility only.",
        ]
        if review and review.status in {"attention", "blocked"}:
            risks.append("Supervisor found attention/blocker state; execution must stay dry-run until Ugo approves scoped remediation.")
        return Plan(objective=objective, steps=steps, risks=tuple(risks), sources=tuple(sources), confidence=0.84)
