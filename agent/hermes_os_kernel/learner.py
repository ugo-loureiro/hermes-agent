"""Learner component for Hermes OS Kernel Phase 0."""

from __future__ import annotations

from .contracts import DryRunResult, Objective, Reflection, Review


class Learner:
    """Recommends learnings but never writes memory automatically in Phase 0."""

    def reflect(self, objective: Objective, review: Review, dry_run: DryRunResult) -> Reflection:
        learnings = [
            "Hermes OS should treat James as governed ERP/modular OS, not as a single agent.",
            "Read-only observation and dry-run execution can produce useful audit evidence without changing James.",
        ]
        if review.status != "on_track":
            learnings.append("Supervisor attention states should create recommendations, not direct execution, until an approval gate is opened.")
        recommended_memories = [
            "Hermes OS Phase 0 kernel contracts validated with read-only James health objective."
        ]
        recommended_skills = [
            "Create/extend a Hermes OS operations skill after repeated Phase 0 cycles reveal stable procedures."
        ]
        return Reflection(
            objective=objective,
            learnings=tuple(learnings),
            recommended_memories=tuple(recommended_memories),
            recommended_skills=tuple(recommended_skills),
            writes_applied=False,
            confidence=0.86 if dry_run.real_side_effects_executed is False else 0.2,
        )
