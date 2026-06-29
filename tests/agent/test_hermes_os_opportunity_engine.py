from agent.hermes_os_kernel import OpportunityEngine, build_module_dashboard


def _base_observations():
    james_operational = {
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
    return {"module_supervision": dashboard, "read_only": True}


def _detect(observations):
    return OpportunityEngine().detect(observations).as_dict()


def test_opportunity_engine_detects_seasonal_licensing_without_execution():
    observations = _base_observations()
    observations["seasonal_licensing"] = {"active": True, "month": 1, "evidence": "calendar_window", "confidence": 0.82}
    report = _detect(observations)
    seasonal = [o for o in report["opportunities"] if o["opportunity_type"] == "seasonal_campaign"]
    assert seasonal
    assert seasonal[0]["origin"] == "seasonal_licensing"
    assert seasonal[0]["execution_tool_available"] is True
    assert seasonal[0]["approval_required"] is True
    assert report["real_side_effects_executed"] is False
    assert report["priority_assigned"] is False
    assert report["decision_made"] is False


def test_opportunity_engine_detects_degraded_module_from_evidence():
    observations = _base_observations()
    report = _detect(observations)
    degraded = [o for o in report["opportunities"] if o["opportunity_type"] == "module_degraded"]
    assert degraded
    assert all(o["evidence"] for o in degraded)
    assert all(o["available_capability"] for o in degraded)
    assert all(o["policy_r0_r5"] for o in degraded)


def test_opportunity_engine_turns_queue_growth_without_capability_into_gap():
    observations = _base_observations()
    observations["queues"] = {
        "orphan_queue": {"growing": True, "depth": 42, "module": "unknown_queue_module", "confidence": 0.8}
    }
    report = _detect(observations)
    assert not [o for o in report["opportunities"] if o["opportunity_type"] == "queue_growth"]
    gaps = [g for g in report["capability_gaps"] if g["missing_capability"] == "queue.depth.read"]
    assert gaps
    assert gaps[0]["origin"] == "queues"


def test_opportunity_engine_detects_worker_stopped_and_container_degraded():
    observations = _base_observations()
    report = _detect(observations)
    worker = [o for o in report["opportunities"] if o["opportunity_type"] == "worker_stopped"]
    container = [o for o in report["opportunities"] if o["opportunity_type"] == "container_degraded"]
    assert worker
    assert container
    assert all(o["approval_required"] is True for o in worker + container)
    assert all("restart" in o["recommended_action"].lower() or "diagnóstico" in o["recommended_action"].lower() or "recuperação" in o["recommended_action"].lower() for o in worker + container)


def test_opportunity_engine_detects_available_campaign_and_financial_existing_data():
    observations = _base_observations()
    observations["financial_existing_data"] = {
        "detected": True,
        "source": "existing_vehicle_debt_flags",
        "impact": "Cobrança/serviço potencial a partir de dado existente.",
        "confidence": 0.79,
    }
    report = _detect(observations)
    financial = [o for o in report["opportunities"] if o["opportunity_type"] == "financial_existing_data"]
    assert financial
    assert financial[0]["policy_r0_r5"] == "R5"
    assert financial[0]["approval_required"] is True
    assert "não criar PIX" in financial[0]["recommended_action"]


def test_opportunity_engine_no_evidence_creates_no_opportunities():
    report = _detect({"module_supervision": {"modules": [], "degraded_modules": [], "containers_with_problem": [], "workers_with_problem": [], "watchers_with_problem": []}})
    assert report["opportunities"] == ()
    assert report["capability_gaps"] == ()
    assert report["real_side_effects_executed"] is False


def test_opportunity_engine_requires_complete_evidence_or_gap():
    observations = _base_observations()
    observations["queues"] = {"jobs": {"growing": True, "depth": 5, "module": "worker_jobs"}}
    report = _detect(observations)
    assert report["capability_gaps"] or [o for o in report["opportunities"] if o["opportunity_type"] == "queue_growth"]
    for opportunity in report["opportunities"]:
        for field in (
            "title",
            "summary",
            "origin",
            "evidence",
            "impact",
            "urgency",
            "effort",
            "risk",
            "confidence",
            "available_capability",
            "policy_r0_r5",
            "recommended_action",
            "observed_component",
        ):
            assert opportunity[field] not in (None, "", {}, ())
