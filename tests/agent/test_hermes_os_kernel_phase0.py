import json

from agent.hermes_os_kernel import (
    Audit,
    Executor,
    JamesReadOnlyAdapter,
    Learner,
    Objective,
    Observer,
    Planner,
    Policy,
    Supervisor,
    autonomy_entry,
    autonomy_matrix_as_dicts,
    resolve_kanban_target,
)
from agent.hermes_os_kernel.demo import run_demo_cycle
from agent.hermes_os_kernel.james_readonly import READONLY_TOOL_NAMES, mutative_markers_in_source


def fake_knowledge(method, query):
    return {
        "knowledge_fabric_enforced": True,
        "confidence": 0.88,
        "providers_used": ["test_provider"],
        "results": [{"content": f"context for {query}", "provider": "test_provider"}],
        "explanation_id": "exp-test",
    }


class FakeJamesAdapter:
    def collect(self, *, kanban_limit=20):
        return {
            "readonly": True,
            "real_side_effects_executed": False,
            "mcp_tools_expected": list(READONLY_TOOL_NAMES),
            "mcp_tools_available": list(READONLY_TOOL_NAMES),
            "mcp": {name: {"readonly": True, "ok": True} for name in READONLY_TOOL_NAMES},
            "registries": {
                "workers": {"readonly": True, "ok": True, "summary": {"worker_mentions": 3}},
                "watchers": {"readonly": True, "ok": True, "summary": {"watcher_mentions": 4}},
                "capabilities": {"readonly": True, "ok": True, "summary": {"capability_mentions": 8, "gate_mentions": 5}},
            },
            "operational_view": {
                "overall_health": "ok",
                "unhealthy_components": [],
                "containers": {"count": 11},
                "modules": {"count": 12},
                "workers": {"readonly": True, "ok": True},
                "watchers": {"readonly": True, "ok": True},
                "capabilities": {"readonly": True, "ok": True},
                "atendimento": {"readonly": True, "ok": True},
                "campaigns": {"readonly": True, "ok": True},
                "employee_telegram": {"readonly": True, "ok": True},
                "kanban": {"ok": True, "task_count": 2},
                "risks_gates": {"gate_markers": 5, "side_effect_markers": 2, "phase1_execution_allowed": False},
                "pending_detected": [],
            },
            "adapter_errors": {},
            "mutative_methods_allowed": [],
        }


class StubObserver(Observer):
    def __init__(self, **kwargs):
        super().__init__(james_adapter=FakeJamesAdapter(), **kwargs)

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


def test_phase1_cycle_contracts_are_read_only(tmp_path):
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
    record = audit.record(plan=plan, review=review, dry_run=dry_run, reflection=reflection, snapshot=snapshot, path=audit_path)

    assert snapshot.observations["read_only"] is True
    assert snapshot.observations["knowledge_fabric"]["knowledge_fabric_enforced"] is True
    assert snapshot.observations["james_operational"]["operational_view"]["overall_health"] == "ok"
    assert review.status == "on_track"
    assert len(plan.steps) >= 5
    assert dry_run.real_side_effects_executed is False
    assert all(action.access in {"read_only", "simulated"} for action in dry_run.actions)
    assert reflection.writes_applied is False
    assert record.snapshot is snapshot
    assert record.real_side_effects_executed is False
    assert audit_path.exists()
    payload = json.loads(audit_path.read_text())
    assert payload["audit_schema"] == "hermes_os_kernel_phase0/v1"
    assert payload["snapshot"]["observations"]["james_operational"]["real_side_effects_executed"] is False
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


def test_james_readonly_adapter_declares_expected_tools_and_no_mutative_allowlist():
    adapter = JamesReadOnlyAdapter(server=None, prefer_mcp_stdio=False)
    payload = adapter.collect()
    assert payload["readonly"] is True
    assert payload["real_side_effects_executed"] is False
    assert payload["mcp_tools_expected"] == list(READONLY_TOOL_NAMES)
    assert payload["mutative_methods_allowed"] == []
    assert payload["kanban_target"]["board_slug"] == "james-despachante"


def test_kanban_target_prefers_active_james_board():
    target = resolve_kanban_target()
    assert target["board_slug"] == "james-despachante"
    assert target["db_path"].endswith("/kanban/boards/james-despachante/kanban.db")


def test_no_mutative_markers_in_readonly_tool_names():
    joined = " ".join(READONLY_TOOL_NAMES)
    assert mutative_markers_in_source(joined) == []


def test_demo_cycle_can_run_with_monkeypatched_observer(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.hermes_os_kernel.demo.knowledge_call", lambda method, query, limit=5: fake_knowledge(method, query))
    monkeypatch.setattr("agent.hermes_os_kernel.observer.JamesReadOnlyAdapter", lambda: FakeJamesAdapter())
    monkeypatch.setattr("agent.hermes_os_kernel.observer.Observer._james_health", lambda self: StubObserver()._james_health())
    monkeypatch.setattr("agent.hermes_os_kernel.observer.Observer._docker_inventory", lambda self: StubObserver()._docker_inventory())
    result = run_demo_cycle(audit_path=tmp_path / "demo-audit.json")
    assert result["dry_run"]["real_side_effects_executed"] is False
    assert result["audit"]["objective"] == "avaliar saúde operacional atual do James"
    assert result["audit"]["snapshot"]["observations"]["james_operational"]["readonly"] is True
    assert result["reflection"]["writes_applied"] is False
