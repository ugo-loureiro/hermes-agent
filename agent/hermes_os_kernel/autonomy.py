"""Preliminary autonomy matrix for Hermes OS Kernel.

The matrix is descriptive in Phase 0: it informs Policy/Audit decisions and
human review, but it does not grant execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .contracts import RiskLevel


@dataclass(frozen=True)
class AutonomyMatrixEntry:
    level: RiskLevel
    name: str
    allowed_without_ugo: tuple[str, ...]
    requires_ugo: tuple[str, ...]
    forbidden_in_phase0: tuple[str, ...]
    evidence_required: tuple[str, ...]


AUTONOMY_MATRIX: tuple[AutonomyMatrixEntry, ...] = (
    AutonomyMatrixEntry(
        level="R0",
        name="read-only observation",
        allowed_without_ugo=("Knowledge Fabric query", "local health GET", "docker ps inventory", "docs/registry reads"),
        requires_ugo=(),
        forbidden_in_phase0=(),
        evidence_required=("source list", "timestamp", "confidence", "no side effects flag"),
    ),
    AutonomyMatrixEntry(
        level="R1",
        name="dry-run planning and simulation",
        allowed_without_ugo=("planner output", "supervisor recommendation", "executor dry-run map", "audit record write"),
        requires_ugo=("turning dry-run into execution",),
        forbidden_in_phase0=("mutating James runtime",),
        evidence_required=("plan", "risk", "policy decision", "approval need"),
    ),
    AutonomyMatrixEntry(
        level="R2",
        name="assisted local change",
        allowed_without_ugo=(),
        requires_ugo=("repo edits beyond planning", "Kanban state changes", "service-specific diagnostics with side-effect risk"),
        forbidden_in_phase0=("runtime change", "config flip", "service restart"),
        evidence_required=("approval_ref", "diff", "tests", "rollback note"),
    ),
    AutonomyMatrixEntry(
        level="R3",
        name="controlled runtime operation",
        allowed_without_ugo=(),
        requires_ugo=("rebuild", "restart", "compose up", "database migration", "gateway operation"),
        forbidden_in_phase0=("all R3 execution",),
        evidence_required=("approval_ref", "backup", "pre/post health", "rollback plan"),
    ),
    AutonomyMatrixEntry(
        level="R4",
        name="external integration or customer-adjacent action",
        allowed_without_ugo=(),
        requires_ugo=("HOST/API-interna assisted lookup", "Telegram real test", "WhatsApp allowlist pilot"),
        forbidden_in_phase0=("all R4 execution", "customer contact"),
        evidence_required=("approval_ref", "scope", "allowlist", "rate/window", "sanitized evidence"),
    ),
    AutonomyMatrixEntry(
        level="R5",
        name="financial/production real side effect",
        allowed_without_ugo=(),
        requires_ugo=("PIX/Santander", "WhatsApp customer send", "HOST mutation", "provider/auth/token changes"),
        forbidden_in_phase0=("all R5 execution", "secret changes", "payments", "customer campaigns"),
        evidence_required=("fresh approval_ref", "idempotency", "audit trail", "rollback/recovery plan", "post-action proof"),
    ),
)


def autonomy_matrix_as_dicts() -> list[dict[str, object]]:
    return [asdict(entry) for entry in AUTONOMY_MATRIX]


def autonomy_entry(level: RiskLevel) -> AutonomyMatrixEntry:
    for entry in AUTONOMY_MATRIX:
        if entry.level == level:
            return entry
    raise KeyError(level)
