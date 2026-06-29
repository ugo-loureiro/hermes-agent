import json

from agent.hermes_os_kernel import (
    Audit,
    Executor,
    Learner,
    Objective,
    Observer,
    Planner,
    Policy,
    Supervisor,
    autonomy_entry,
    autonomy_matrix_as_dicts,
)
from agent.hermes_os_kernel.demo import run_demo_cycle


def fake_knowledge(method, query):
    return {
        "knowledge_fabric_enforced": True,
        "confidence": 0.88,
        "providers_used": ["test_provider"],
        "results": [{"content": f"context for {query}", "provider": "test_provider"}],
        "explanation_id": "exp-test",
    }


class StubObserver(Observer):
    def _james_health(self):
        return {
            "core": {"ok": True, "status": 200, "body": "ok"},
            "adapter": {"ok": True, "status": 200, "body": "ok"},
            "worker": {"ok": True, "status": 200, "body": "ok"},
            "atendimento": {"ok": True, "status": 200, "body": "ok"},
            "employee_telegram": {"ok": True, "status": 200, "body": "ok"},
        }

    def _docker_inventory(self):
        return {"available": True, "count": 2, "containers": [{"name": "james-core-api", "status": "Up"}]}


def test_phase0_cycle_contracts_are_read_only(tmp_path):
    objective = Objective("avaliar saúde operacional atual do James")
    observer = StubObserver(knowledge_fn=fake_knowledge)
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
    audit_path = tmp_path / "audit.json"
    record = audit.record(plan=plan, review=review, dry_run=dry_run, reflection=reflection, path=audit_path)

    assert snapshot.observations["read_only"] is True
    assert snapshot.observations["knowledge_fabric"]["knowledge_fabric_enforced"] is True
    assert review.status == "on_track"
    assert len(plan.steps) == 4
    assert dry_run.real_side_effects_executed is False
    assert all(action.access in {"read_only", "simulated"} for action in dry_run.actions)
    assert reflection.writes_applied is False
    assert record.real_side_effects_executed is False
    assert audit_path.exists()
    payload = json.loads(audit_path.read_text())
    assert payload["audit_schema"] == "hermes_os_kernel_phase0/v1"
    assert payload["approval_required"] is False


def test_policy_preserves_sensitive_gates():
    decision = Policy().check(
        {
            "type": "send",
            "target": "whatsapp_customer_contact",
            "risk_level": "R5",
            "side_effects": True,
        }
    )
    assert decision.allowed is False
    assert decision.requires_ugo_approval is True
    assert "sensitive_target" in decision.gates
    assert "mutative_or_side_effecting_action" in decision.gates


def test_autonomy_matrix_has_all_levels_and_phase0_blocks_r5():
    matrix = autonomy_matrix_as_dicts()
    assert [entry["level"] for entry in matrix] == ["R0", "R1", "R2", "R3", "R4", "R5"]
    assert autonomy_entry("R0").allowed_without_ugo
    assert "all R5 execution" in autonomy_entry("R5").forbidden_in_phase0


def test_demo_cycle_can_run_with_monkeypatched_observer(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.hermes_os_kernel.demo.knowledge_call", lambda method, query, limit=5: fake_knowledge(method, query))
    monkeypatch.setattr("agent.hermes_os_kernel.observer.Observer._james_health", lambda self: StubObserver()._james_health())
    monkeypatch.setattr("agent.hermes_os_kernel.observer.Observer._docker_inventory", lambda self: StubObserver()._docker_inventory())
    result = run_demo_cycle(audit_path=tmp_path / "demo-audit.json")
    assert result["dry_run"]["real_side_effects_executed"] is False
    assert result["audit"]["objective"] == "avaliar saúde operacional atual do James"
    assert result["reflection"]["writes_applied"] is False
