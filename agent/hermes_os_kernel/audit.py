"""Audit/Evaluation component for Hermes OS Kernel Phase 0."""

from __future__ import annotations

import json
from pathlib import Path

from typing import cast

from .contracts import AuditRecord, DryRunResult, Plan, Reflection, Review, RiskLevel, Snapshot, SourceRef, to_plain, utc_now_iso


class Audit:
    """Creates an audit trail for every Hermes OS decision."""

    def record(
        self,
        *,
        plan: Plan,
        review: Review,
        dry_run: DryRunResult,
        reflection: Reflection,
        snapshot: Snapshot | None = None,
        path: str | Path | None = None,
    ) -> AuditRecord:
        all_sources: list[SourceRef] = []
        all_sources.extend(plan.sources)
        if snapshot:
            all_sources.extend(snapshot.sources)
        action_proposed = "; ".join(action.would_call for action in dry_run.actions)
        approval_required = any(action.policy.requires_ugo_approval for action in dry_run.actions)
        risk = _max_risk([review.risk_level, *(action.policy.risk_level for action in dry_run.actions)])
        record = AuditRecord(
            objective=plan.objective.text,
            sources_consulted=tuple(_dedupe_sources(all_sources)),
            snapshot=snapshot,
            plan=plan,
            review=review,
            dry_run=dry_run,
            reflection=reflection,
            risk=cast(RiskLevel, risk),
            confidence=round(min(plan.confidence, review.confidence, dry_run.confidence, reflection.confidence), 3),
            action_proposed=action_proposed,
            approval_required=approval_required,
            reason="Phase 0 audit record: read-only observation, plan/review, dry-run execution map, learner recommendations.",
            real_side_effects_executed=dry_run.real_side_effects_executed,
        )
        if path:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = to_plain(record)
            payload["audit_schema"] = "hermes_os_kernel_phase0/v1"
            payload["written_at"] = utc_now_iso()
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record


def _dedupe_sources(sources: list[SourceRef]) -> list[SourceRef]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SourceRef] = []
    for source in sources:
        key = (source.name, source.kind)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped


def _max_risk(values: list[str]) -> str:
    ranked = sorted(values, key=lambda value: int(value[1]) if value.startswith("R") and value[1:].isdigit() else 5)
    return ranked[-1] if ranked else "R0"
