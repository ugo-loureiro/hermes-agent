"""Read-only demonstration cycle for Hermes OS Kernel Phase 0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent.knowledge_fabric_bridge import knowledge_call

from .audit import Audit
from .contracts import Objective, to_plain
from .executor import Executor
from .learner import Learner
from .observer import Observer
from .planner import Planner
from .supervisor import Supervisor

DEFAULT_OBJECTIVE = "avaliar saúde operacional atual do James"


def run_demo_cycle(objective_text: str = DEFAULT_OBJECTIVE, *, audit_path: str | Path | None = None) -> dict[str, Any]:
    """Run Observer → Supervisor → Planner → Executor dry-run → Learner → Audit.

    Only read-only probes and simulation are performed. Mutative actions are not
    invoked and the audit record sets ``real_side_effects_executed=false``.
    """

    objective = Objective(
        text=objective_text,
        autonomy_level="read_only",
        success_criteria=(
            "James observed through read-only sources",
            "Executor remains dry-run",
            "Audit record includes approval/risk/confidence",
        ),
    )
    observer = Observer(knowledge_fn=lambda method, query: knowledge_call(method, query, limit=5))
    supervisor = Supervisor()
    planner = Planner()
    executor = Executor()
    learner = Learner()
    audit = Audit()

    snapshot = observer.snapshot(objective)
    review = supervisor.review(objective, snapshot)
    plan = planner.plan(objective, snapshot, review)
    dry_run = executor.dry_run(plan)
    reflection = learner.reflect(objective, review, dry_run)
    record = audit.record(plan=plan, review=review, dry_run=dry_run, reflection=reflection, snapshot=snapshot, path=audit_path)

    return {
        "objective": objective.text,
        "snapshot": to_plain(snapshot),
        "review": to_plain(review),
        "plan": to_plain(plan),
        "dry_run": to_plain(dry_run),
        "reflection": to_plain(reflection),
        "audit": to_plain(record),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes OS Kernel Phase 0 read-only demo")
    parser.add_argument("--objective", default=DEFAULT_OBJECTIVE)
    parser.add_argument("--audit-path", default="")
    args = parser.parse_args()
    result = run_demo_cycle(args.objective, audit_path=args.audit_path or None)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
