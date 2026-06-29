"""Contracts for Hermes OS Kernel Phase 0.

Phase 0 is intentionally read-only + planning/dry-run. These dataclasses are
plain value objects so the kernel can be tested without mutating James runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal

RiskLevel = Literal["R0", "R1", "R2", "R3", "R4", "R5"]
AutonomyLevel = Literal["read_only", "dry_run", "assisted", "approved_execution"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: to_plain(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class SourceRef:
    name: str
    kind: str
    access: Literal["read_only", "simulated", "local_artifact"]
    confidence: float = 0.7
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Objective:
    text: str
    requested_by: str = "Ugo"
    autonomy_level: AutonomyLevel = "read_only"
    success_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    component: str
    description: str
    dependencies: tuple[str, ...] = ()
    risk_level: RiskLevel = "R0"
    success_criteria: tuple[str, ...] = ()
    proposed_action: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    objective: Objective
    steps: tuple[PlanStep, ...]
    risks: tuple[str, ...]
    sources: tuple[SourceRef, ...]
    confidence: float
    generated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Snapshot:
    objective: Objective
    status: Literal["ok", "degraded", "blocked", "unknown"]
    observations: dict[str, Any]
    sources: tuple[SourceRef, ...]
    confidence: float
    collected_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Review:
    objective: Objective
    status: Literal["on_track", "attention", "blocked", "unknown"]
    findings: tuple[str, ...]
    recommendations: tuple[str, ...]
    risk_level: RiskLevel
    confidence: float
    reviewed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_ugo_approval: bool
    risk_level: RiskLevel
    reasons: tuple[str, ...]
    gates: tuple[str, ...]
    confidence: float = 0.9


@dataclass(frozen=True)
class DryRunAction:
    step_id: str
    would_call: str
    access: Literal["read_only", "simulated"]
    policy: PolicyDecision
    payload_shape: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DryRunResult:
    objective: Objective
    actions: tuple[DryRunAction, ...]
    real_side_effects_executed: bool
    confidence: float
    generated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Reflection:
    objective: Objective
    learnings: tuple[str, ...]
    recommended_memories: tuple[str, ...]
    recommended_skills: tuple[str, ...]
    writes_applied: bool
    confidence: float
    reflected_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AuditRecord:
    objective: str
    sources_consulted: tuple[SourceRef, ...]
    snapshot: Snapshot | None
    plan: Plan
    review: Review
    dry_run: DryRunResult
    reflection: Reflection
    risk: RiskLevel
    confidence: float
    action_proposed: str
    approval_required: bool
    reason: str
    real_side_effects_executed: bool = False
    recorded_at: str = field(default_factory=utc_now_iso)
