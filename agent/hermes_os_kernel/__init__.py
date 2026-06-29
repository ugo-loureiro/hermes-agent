"""Hermes OS Kernel Phase 0.

Initial reversible foundation for governing James through read-only observation,
planning, supervision, dry-run execution, learning recommendations, policy gates
and audit trails. This package is not wired into Hermes runtime dispatch yet.
"""

from .audit import Audit
from .autonomy import AUTONOMY_MATRIX, AutonomyMatrixEntry, autonomy_entry, autonomy_matrix_as_dicts
from .contracts import AuditRecord, DryRunResult, Objective, Plan, PolicyDecision, Reflection, Review, Snapshot
from .executor import Executor
from .james_readonly import JamesReadOnlyAdapter, discover_kanban_targets, resolve_kanban_target
from .learner import Learner
from .observer import Observer
from .planner import Planner
from .policy import Policy
from .supervisor import Supervisor

__all__ = [
    "Audit",
    "AUTONOMY_MATRIX",
    "AuditRecord",
    "AutonomyMatrixEntry",
    "DryRunResult",
    "Executor",
    "JamesReadOnlyAdapter",
    "Learner",
    "Objective",
    "Observer",
    "Plan",
    "Planner",
    "Policy",
    "PolicyDecision",
    "Reflection",
    "Review",
    "Snapshot",
    "Supervisor",
    "autonomy_entry",
    "autonomy_matrix_as_dicts",
    "discover_kanban_targets",
    "resolve_kanban_target",
]
