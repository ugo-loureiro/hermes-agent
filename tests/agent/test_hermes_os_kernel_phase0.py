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
    build_module_dashboard,
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
    assert review.status in {"on_track", "attention"}
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
    assert payload["approval_required"] in {True, False}
    assert payload["real_side_effects_executed"] is False


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


def test_module_dashboard_maps_full_james_registry_and_policy():
    dashboard = build_module_dashboard(FakeJamesAdapter().collect(), StubObserver()._docker_inventory())
    assert dashboard["benchmark"]["module_count"] >= 26
    assert dashboard["benchmark"]["max_autonomy_without_ugo"] == "R1"
    assert dashboard["benchmark"]["real_side_effects_allowed"] is False
    first = dashboard["modules"][0]
    for field in (
        "name",
        "manager",
        "health",
        "status",
        "risk",
        "confidence",
        "dependencies",
        "watchers_related",
        "workers_related",
        "capabilities_related",
        "gates_active",
        "autonomy_max_allowed",
        "observations",
        "metrics",
        "policy",
    ):
        assert field in first
    assert first["policy"]["max_allowed_without_ugo"] == "R1"


def test_observer_snapshot_exposes_global_and_individual_module_state():
    snapshot = StubObserver(knowledge_fn=fake_knowledge).snapshot(Objective("estado por módulo"))
    modules = snapshot.observations["module_supervision"]
    assert modules["benchmark"]["module_count"] >= 26
    assert "global_state" in snapshot.observations
    assert snapshot.observations["global_state"]["read_only"] is True
    assert modules["executive_summary"]


def test_supervisor_answers_attention_healthy_wait_and_approval_without_llm():
    snapshot = StubObserver(knowledge_fn=fake_knowledge).snapshot(Objective("priorizar módulos"))
    review = Supervisor().review(snapshot.objective, snapshot)
    joined = "\n".join(review.findings + review.recommendations)
    assert "Attention now:" in joined
    assert "Can wait:" in joined
    assert "R2+ module actions require explicit Ugo approval" in joined


def test_planner_generates_module_separated_dry_run_steps():
    snapshot = StubObserver(knowledge_fn=fake_knowledge).snapshot(Objective("planejar por módulo"))
    review = Supervisor().review(snapshot.objective, snapshot)
    plan = Planner().plan(snapshot.objective, snapshot, review)
    module_steps = [step for step in plan.steps if step.step_id.startswith("module-plan-")]
    assert module_steps
    assert all(step.proposed_action["type"] == "module_plan_dry_run" for step in module_steps)
    assert all(step.proposed_action["side_effects"] is False for step in module_steps)


def test_executor_dry_run_lists_tool_api_mcp_kanban_and_simulated_action():
    snapshot = StubObserver(knowledge_fn=fake_knowledge).snapshot(Objective("executar simulado por módulo"))
    review = Supervisor().review(snapshot.objective, snapshot)
    plan = Planner().plan(snapshot.objective, snapshot, review)
    dry_run = Executor().dry_run(plan)
    module_actions = [action for action in dry_run.actions if action.step_id.startswith("module-plan-")]
    assert module_actions
    for action in module_actions:
        assert set(["tool", "api", "mcp", "kanban", "simulated_action"]).issubset(action.payload_shape)
        assert action.access == "simulated"
        assert action.policy.requires_ugo_approval in {True, False}
        assert action.payload_shape["real_execution"] is False


def test_ten_supervision_scenarios_remain_readonly(tmp_path):
    objectives = [
        "estado geral do James",
        "estado por módulo",
        "módulos críticos",
        "módulos degradados",
        "watchers com problema",
        "workers com problema",
        "containers com problema",
        "filas crescendo",
        "dependências ausentes",
        "ações que exigem aprovação",
    ]
    for idx, text in enumerate(objectives):
        result = run_demo_cycle(objective_text=text, audit_path=tmp_path / f"scenario-{idx}.json")
        assert result["dry_run"]["real_side_effects_executed"] is False
        assert result["snapshot"]["observations"]["module_supervision"]["benchmark"]["module_count"] >= 26
        assert result["snapshot"]["observations"]["global_state"]["max_autonomy_without_ugo"] == "R1"
