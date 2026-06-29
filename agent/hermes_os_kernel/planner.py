"""Planner component for Hermes OS Kernel."""

from __future__ import annotations

from .contracts import Objective, Plan, PlanStep, Review, Snapshot, SourceRef


class Planner:
    """Turns Ugo objectives and read-only findings into non-executing plans."""

    def plan(self, objective: Objective, snapshot: Snapshot | None = None, review: Review | None = None) -> Plan:
        sources: list[SourceRef] = []
        if snapshot:
            sources.extend(snapshot.sources)
        if not sources:
            sources.append(SourceRef("Planner input", "objective", "local_artifact", 0.7))

        steps: list[PlanStep] = [
            PlanStep(
                step_id="observe-james-readonly-surfaces",
                component="Observer",
                description="Collect Knowledge Fabric context plus James MCP read-only, local health/status, registries, Kanban and runtime inventory.",
                risk_level="R0",
                success_criteria=("No side effects", "Snapshot includes operational_view and source list"),
                proposed_action={"type": "observe", "target": "james_readonly_surfaces", "side_effects": False},
            ),
            PlanStep(
                step_id="review-operational-consistency",
                component="Supervisor",
                description="Classify health, blockers, inconsistencies, risks/gates, pending items and evidence confidence.",
                dependencies=("observe-james-readonly-surfaces",),
                risk_level="R0",
                success_criteria=("Findings are backed by snapshot evidence",),
                proposed_action={"type": "review", "target": "hermes_os_supervisor", "side_effects": False},
            ),
        ]

        for idx, finding in enumerate(_actionable_findings(review), start=1):
            steps.append(
                PlanStep(
                    step_id=f"scope-readonly-followup-{idx}",
                    component="Planner",
                    description=f"Scope a read-only follow-up for finding: {finding}",
                    dependencies=("review-operational-consistency",),
                    risk_level="R1",
                    success_criteria=("Follow-up remains read-only", "Any R2+ action is left as recommendation only"),
                    proposed_action={"type": "dry_run_scope", "target": "james_followup", "side_effects": False, "finding": finding},
                )
            )

        steps.extend(
            [
                PlanStep(
                    step_id="simulate-approved-tool-map",
                    component="Executor",
                    description="List MCP/tools/APIs that would be used if Ugo later approved remediation, without invoking mutative calls.",
                    dependencies=(steps[-1].step_id,),
                    risk_level="R1",
                    success_criteria=("Mutative actions remain dry-run only", "Policy decision attached to every action"),
                    proposed_action={"type": "dry_run", "target": "james_tools", "side_effects": False},
                ),
                PlanStep(
                    step_id="reflect-and-audit-cycle",
                    component="Learner/Audit",
                    description="Recommend learnings and record objective, sources, snapshot, review, plan, dry-run, risk, confidence and approval need.",
                    dependencies=("simulate-approved-tool-map",),
                    risk_level="R0",
                    success_criteria=("Audit record is complete", "Learner does not write memory automatically"),
                    proposed_action={"type": "audit", "target": "hermes_os", "side_effects": False},
                ),
            ]
        )

        risks = [
            "Phase 1 must not mutate James runtime, Copilot, providers, configs, channels or financial systems.",
            "MCP read-only functions may be import-level surfaces rather than a live MCP transport in this session.",
            "Health/status and Kanban read-only snapshots provide operational visibility, not permission to execute.",
        ]
        if review and review.status in {"attention", "blocked"}:
            risks.append("Supervisor found attention/blocker state; all remediation remains recommendation/dry-run until Ugo approves a scoped mission.")
        return Plan(objective=objective, steps=tuple(steps), risks=tuple(risks), sources=tuple(sources), confidence=0.86)


def _actionable_findings(review: Review | None) -> list[str]:
    if review is None:
        return ["no_review_available"]
    selected = [finding for finding in review.findings if "Pending detected" in finding or "unreachable" in finding or "errors" in finding]
    return selected[:4] or ["no_blocker_detected"]
