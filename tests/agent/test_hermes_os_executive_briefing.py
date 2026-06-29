from agent.hermes_os_kernel import BRIEFING_SECTIONS, ExecutiveBriefingEngine, build_module_dashboard


def _base_observations():
    james_operational = {
        "readonly": True,
        "real_side_effects_executed": False,
        "operational_view": {"kanban": {"ok": True, "task_count": 15}},
        "mcp": {
            "james_core_status": {"component": "core", "ok": True},
            "james_adapter_status": {"component": "adapter", "ok": True},
            "james_atendimento_status": {"component": "atendimento", "ok": True},
            "james_employee_telegram_status": {"component": "employee_telegram", "ok": True},
            "james_campaign_center_status": {"component": "campaign_center", "ok": True},
        },
    }
    docker = {
        "available": True,
        "containers": [
            {"name": "james-core-api", "status": "Up (healthy)"},
            {"name": "james-campaign-engine", "status": "Exited"},
            {"name": "james-atendimento-worker-baileys", "status": "Exited"},
        ],
    }
    dashboard = build_module_dashboard(james_operational, docker)
    return {
        "read_only": True,
        "knowledge_fabric": {"knowledge_fabric_enforced": True, "confidence": 0.88},
        "james_operational": james_operational,
        "docker_inventory": docker,
        "module_supervision": dashboard,
        "global_state": {"overall": dashboard["overall_state"], "read_only": True},
    }


def _brief(observations, review=None):
    return ExecutiveBriefingEngine().generate(observations, review=review).as_dict()


def _assert_briefing_contract(briefing):
    for section in BRIEFING_SECTIONS:
        assert section in briefing
    assert briefing["scheduled"] is False
    assert briefing["notification_sent"] is False
    assert briefing["real_side_effects_executed"] is False
    assert briefing["memory_written"] is False
    assert briefing["mutative_calls_made"] is False
    for recommendation in briefing["recommendations"]:
        for field in ("origin", "confidence", "available_capability", "policy_r0_r5", "approval_required"):
            assert recommendation[field] not in (None, "")


def test_daily_briefing_has_all_required_sections_and_evidence_only():
    briefing = _brief(_base_observations(), {"status": "attention", "confidence": 0.83})
    _assert_briefing_contract(briefing)
    assert briefing["evidence_used"]
    assert briefing["general_state"]["read_only"] is True
    assert briefing["general_state"]["real_side_effects_allowed"] is False


def test_daily_briefing_no_evidence_creates_no_false_opportunities():
    briefing = _brief({"read_only": True, "module_supervision": {"modules": [], "degraded_modules": [], "containers_with_problem": [], "workers_with_problem": [], "watchers_with_problem": []}})
    _assert_briefing_contract(briefing)
    assert briefing["opportunities_detected"] == ()
    assert briefing["capability_gaps"] == ()
    assert "Sem evidência suficiente" in briefing["executive_summary"]


def test_daily_briefing_seasonal_licensing_scenario():
    observations = _base_observations()
    observations["seasonal_licensing"] = {"active": True, "month": 1, "evidence": "calendar_window", "confidence": 0.82}
    briefing = _brief(observations)
    _assert_briefing_contract(briefing)
    assert any(item["opportunity_type"] == "seasonal_campaign" for item in briefing["opportunities_detected"])


def test_daily_briefing_module_degraded_scenario():
    briefing = _brief(_base_observations())
    _assert_briefing_contract(briefing)
    assert briefing["modules_needing_attention"]
    assert any(item["opportunity_type"] == "module_degraded" for item in briefing["opportunities_detected"])


def test_daily_briefing_queue_gap_scenario():
    observations = _base_observations()
    observations["queues"] = {"orphan_queue": {"growing": True, "depth": 42, "module": "unknown_queue_module", "confidence": 0.8}}
    briefing = _brief(observations)
    _assert_briefing_contract(briefing)
    assert any(gap["missing_capability"] == "queue.depth.read" for gap in briefing["capability_gaps"])
    assert any(action["execution"] == "not_executable_gap" for action in briefing["actions_requiring_approval"])


def test_daily_briefing_worker_stopped_scenario_requires_approval():
    briefing = _brief(_base_observations())
    _assert_briefing_contract(briefing)
    worker = [item for item in briefing["opportunities_detected"] if item["opportunity_type"] == "worker_stopped"]
    assert worker
    assert worker[0]["approval_required"] is True


def test_daily_briefing_container_degraded_scenario_requires_approval():
    briefing = _brief(_base_observations())
    _assert_briefing_contract(briefing)
    container = [item for item in briefing["opportunities_detected"] if item["opportunity_type"] == "container_degraded"]
    assert container
    assert any(action["approval_required"] is True for action in briefing["actions_requiring_approval"])


def test_daily_briefing_financial_existing_data_scenario():
    observations = _base_observations()
    observations["financial_existing_data"] = {"detected": True, "source": "existing_vehicle_debt_flags", "impact": "Serviço potencial", "confidence": 0.79}
    briefing = _brief(observations)
    _assert_briefing_contract(briefing)
    financial = [item for item in briefing["opportunities_detected"] if item["opportunity_type"] == "financial_existing_data"]
    assert financial
    assert financial[0]["policy_r0_r5"] == "R5"


def test_daily_briefing_documentation_outdated_scenario():
    observations = _base_observations()
    observations["documentation"] = {"outdated": True, "component": "runbook", "confidence": 0.75}
    briefing = _brief(observations)
    _assert_briefing_contract(briefing)
    assert any(item["opportunity_type"] == "documentation_outdated" for item in briefing["opportunities_detected"])


def test_daily_briefing_technical_backlog_scenario():
    observations = _base_observations()
    observations["technical_backlog"] = {"items": ["T1", "T2"], "confidence": 0.76}
    briefing = _brief(observations)
    _assert_briefing_contract(briefing)
    assert any(item["opportunity_type"] == "technical_backlog" for item in briefing["opportunities_detected"])


def test_daily_briefing_markdown_model_is_renderable():
    briefing_obj = ExecutiveBriefingEngine().generate(_base_observations())
    markdown = briefing_obj.to_markdown()
    assert "## 1. Resumo Executivo" in markdown
    assert "## 13. Evidências utilizadas" in markdown
    assert "Executive Daily Briefing" in markdown
