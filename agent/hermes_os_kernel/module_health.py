"""Module-level supervision model for Hermes OS Kernel.

The model is read-only and descriptive. It computes operational supervision
signals from James' MCP/registry snapshots and optional Docker inventory, but it
never calls James mutative APIs and never changes autonomy gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .contracts import RiskLevel
from .james_readonly import JAMES_REPO, OPTIONAL_REGISTRY_FILES

MODULE_REGISTRY_PATH = JAMES_REPO / "docs/james-organization/registries/james_modules_registry.yaml"


@dataclass(frozen=True)
class ModuleAutonomyPolicy:
    """R0-R5 policy summary for one James module."""

    r0_observe: tuple[str, ...]
    r1_plan: tuple[str, ...]
    r2_requires_ugo: tuple[str, ...]
    r3_forbidden: tuple[str, ...]
    r4_external_blocked: tuple[str, ...]
    r5_real_effects_forbidden: tuple[str, ...]
    max_allowed_without_ugo: RiskLevel = "R1"


@dataclass(frozen=True)
class ModuleHealth:
    name: str
    manager: str
    health: str
    status: str
    risk: RiskLevel
    confidence: float
    dependencies: tuple[str, ...]
    watchers_related: tuple[str, ...]
    workers_related: tuple[str, ...]
    capabilities_related: tuple[str, ...]
    gates_active: tuple[str, ...]
    autonomy_max_allowed: RiskLevel
    observations: tuple[str, ...]
    metrics: dict[str, Any] = field(default_factory=dict)
    policy: ModuleAutonomyPolicy | None = None


@dataclass(frozen=True)
class ModuleDashboard:
    overall_state: str
    modules: tuple[ModuleHealth, ...]
    critical_modules: tuple[str, ...]
    degraded_modules: tuple[str, ...]
    healthy_modules: tuple[str, ...]
    watchers_with_problem: tuple[str, ...]
    workers_with_problem: tuple[str, ...]
    containers_with_problem: tuple[str, ...]
    queues_growing: tuple[str, ...]
    missing_dependencies: tuple[str, ...]
    attention_now: tuple[str, ...]
    can_wait: tuple[str, ...]
    requires_approval: tuple[str, ...]
    executive_summary: str
    benchmark: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_module_dashboard(james_operational: dict[str, Any], docker_inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    modules_raw = _module_registry_from_payload(james_operational) or _module_registry_from_yaml(MODULE_REGISTRY_PATH)
    workers_raw = _registry_items(OPTIONAL_REGISTRY_FILES["workers"], "workers")
    watchers_raw = _registry_items(OPTIONAL_REGISTRY_FILES["watchers"], "watchers")
    capabilities_raw = _registry_items(OPTIONAL_REGISTRY_FILES["capabilities"], "capabilities")
    docker_by_name = _docker_by_name(docker_inventory)
    health_by_component = _health_by_component(james_operational)

    module_models: list[ModuleHealth] = []
    for module in modules_raw:
        name = str(module.get("module") or module.get("module_id") or "unknown")
        manager = str(module.get("manager") or module.get("manager_owner") or "unknown")
        declared_containers = tuple(str(item) for item in (module.get("containers") or module.get("process_container") or []) if item)
        watchers = tuple(str(item) for item in module.get("watchers") or [])
        capabilities = tuple(str(item) for item in module.get("capabilities") or [])
        dependencies = tuple(str(item) for item in module.get("dependencies") or [])
        gates = tuple(str(item) for item in module.get("gates") or [])
        risk = _normalize_risk(str(module.get("risk_default") or "R1"))
        workers = _workers_for_module(name, declared_containers, workers_raw)
        related_watchers = _watchers_for_module(watchers, manager, watchers_raw)
        related_capabilities = _capabilities_for_module(capabilities, manager, capabilities_raw)

        metrics = _metrics_for_module(name, declared_containers, workers, related_watchers, related_capabilities, docker_by_name, health_by_component)
        health, status, confidence, observations = _classify_module(module, metrics, gates, risk)
        policy = module_policy(name=name, risk=risk, gates=gates, capabilities=related_capabilities)

        module_models.append(
            ModuleHealth(
                name=name,
                manager=manager,
                health=health,
                status=status,
                risk=risk,
                confidence=confidence,
                dependencies=dependencies,
                watchers_related=tuple(sorted(set(watchers + related_watchers))),
                workers_related=tuple(sorted(set(workers))),
                capabilities_related=tuple(sorted(set(capabilities + related_capabilities))),
                gates_active=gates,
                autonomy_max_allowed=policy.max_allowed_without_ugo,
                observations=tuple(observations),
                metrics=metrics,
                policy=policy,
            )
        )

    dashboard = _dashboard(module_models)
    return dashboard.as_dict()


def module_policy(*, name: str, risk: RiskLevel, gates: tuple[str, ...], capabilities: tuple[str, ...]) -> ModuleAutonomyPolicy:
    safe_capabilities = tuple(cap for cap in capabilities if cap.endswith(".read") or ".status." in cap or "status.read" in cap)
    observe = safe_capabilities or (f"{name}.registry.read", f"{name}.health.read")
    plan = (f"{name}.plan.dry_run", f"{name}.risk.review", f"{name}.kanban.scope_readonly")
    r2 = (f"{name}.local_code_or_config_change_with_ugo_approval", f"{name}.runtime_recovery_handoff_only")
    r3 = (f"{name}.runtime_restart_or_rebuild_without_approval", f"{name}.db_migration_or_state_change")
    r4 = (f"{name}.external_provider_or_HOST_call", f"{name}.real_channel_interaction")
    r5 = (f"{name}.customer_contact_or_financial_effect", f"{name}.WhatsApp/Telegram/Pix/Santander real execution")
    if gates:
        r3 = r3 + tuple(f"gate_preserved:{gate}" for gate in gates[:6])
    max_allowed: RiskLevel = "R1"
    return ModuleAutonomyPolicy(
        r0_observe=observe,
        r1_plan=plan,
        r2_requires_ugo=r2,
        r3_forbidden=r3,
        r4_external_blocked=r4,
        r5_real_effects_forbidden=r5,
        max_allowed_without_ugo=max_allowed,
    )


def _module_registry_from_payload(james_operational: dict[str, Any]) -> list[dict[str, Any]]:
    payload = (((james_operational.get("mcp") or {}).get("james_modules_registry_readonly") or {}).get("modules") or [])
    modules = [item for item in payload if isinstance(item, dict)]
    # The MCP contract may return a compact module list for transport economy.
    # Phase 1.2 needs the full supervision model, so prefer the YAML registry
    # unless MCP exposes rich manager/risk metadata for every module.
    if modules and all("manager" in item and "risk_default" in item for item in modules):
        return modules
    return []


def _module_registry_from_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    modules = data.get("modules", []) if isinstance(data, dict) else []
    return [item for item in modules if isinstance(item, dict)]


def _registry_items(path: Path, key: str) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = data.get(key, []) if isinstance(data, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _docker_by_name(docker_inventory: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(docker_inventory, dict):
        return {}
    return {str(item.get("name")): item for item in docker_inventory.get("containers", []) if isinstance(item, dict)}


def _health_by_component(james_operational: dict[str, Any]) -> dict[str, Any]:
    mcp = james_operational.get("mcp") or {}
    health: dict[str, Any] = {}
    for key in (
        "james_core_status",
        "james_adapter_status",
        "james_atendimento_status",
        "james_employee_telegram_status",
        "james_campaign_center_status",
    ):
        payload = mcp.get(key)
        if isinstance(payload, dict):
            component = str(payload.get("component") or key.removeprefix("james_").removesuffix("_status"))
            health[component] = payload
    return health


def _workers_for_module(name: str, containers: tuple[str, ...], workers_raw: list[dict[str, Any]]) -> tuple[str, ...]:
    result = []
    lowered_name = name.lower()
    for worker in workers_raw:
        worker_id = str(worker.get("worker_id") or "")
        worker_containers = tuple(str(item) for item in worker.get("containers") or [])
        if lowered_name in worker_id.lower() or set(containers) & set(worker_containers):
            result.append(worker_id)
    return tuple(result)


def _watchers_for_module(watchers: tuple[str, ...], manager: str, watchers_raw: list[dict[str, Any]]) -> tuple[str, ...]:
    result = []
    for watcher in watchers_raw:
        watcher_id = str(watcher.get("watcher_id") or "")
        if watcher_id in watchers or str(watcher.get("manager")) == manager:
            result.append(watcher_id)
    return tuple(result)


def _capabilities_for_module(capabilities: tuple[str, ...], manager: str, capabilities_raw: list[dict[str, Any]]) -> tuple[str, ...]:
    result = []
    for capability in capabilities_raw:
        capability_id = str(capability.get("capability_id") or "")
        if capability_id in capabilities or str(capability.get("manager")) == manager:
            result.append(capability_id)
    return tuple(result)


def _metrics_for_module(
    name: str,
    containers: tuple[str, ...],
    workers: tuple[str, ...],
    watchers: tuple[str, ...],
    capabilities: tuple[str, ...],
    docker_by_name: dict[str, dict[str, Any]],
    health_by_component: dict[str, Any],
) -> dict[str, Any]:
    matched = [docker_by_name.get(container) for container in containers if docker_by_name.get(container)]
    containers_problem = [container for container in containers if container in docker_by_name and "healthy" not in str(docker_by_name[container].get("status", "")).lower() and "up" not in str(docker_by_name[container].get("status", "")).lower()]
    component_key = _component_key(name)
    component_health = health_by_component.get(component_key)
    availability = 1.0
    if containers:
        availability = len(matched) / max(1, len(containers))
    if component_health and component_health.get("ok") is False:
        availability = min(availability, 0.5)
    return {
        "availability": round(availability, 2),
        "health_ok": None if component_health is None else bool(component_health.get("ok")),
        "containers_declared": len(containers),
        "containers_observed": len(matched),
        "containers_problem": containers_problem,
        "workers_active": len(workers),
        "watchers_active": len(watchers),
        "queues": "not_observed_readonly_contract_missing",
        "known_errors": [] if not containers_problem else containers_problem,
        "blockers": [],
        "risk_markers": [],
        "capabilities_count": len(capabilities),
    }


def _classify_module(module: dict[str, Any], metrics: dict[str, Any], gates: tuple[str, ...], risk: RiskLevel) -> tuple[str, str, float, list[str]]:
    observations: list[str] = []
    if metrics["availability"] < 1.0:
        observations.append("declared_container_not_observed")
    if metrics["health_ok"] is False:
        observations.append("health_endpoint_unhealthy")
    if gates:
        observations.append(f"gates_active={len(gates)}")
    if risk in {"R4", "R5"}:
        observations.append("sensitive_high_risk_boundary")
    if not observations:
        observations.append("read_only_evidence_coherent")
    if metrics["health_ok"] is False or metrics["availability"] == 0 and metrics["containers_declared"]:
        return "degraded", "attention", 0.72, observations
    if risk == "R5":
        return "guarded", "approval_required", 0.84, observations
    if risk == "R4":
        return "guarded", "watch", 0.84, observations
    return "healthy", "ok", 0.88, observations


def _dashboard(modules: list[ModuleHealth]) -> ModuleDashboard:
    critical = tuple(m.name for m in modules if m.risk == "R5" or m.status == "approval_required")
    degraded = tuple(m.name for m in modules if m.health == "degraded")
    healthy = tuple(m.name for m in modules if m.health == "healthy")
    containers_problem = tuple(sorted({c for m in modules for c in m.metrics.get("containers_problem", [])}))
    watchers_problem = tuple(m.name for m in modules if m.metrics.get("watchers_active", 0) == 0 and m.risk in {"R3", "R4", "R5"})
    workers_problem = tuple(m.name for m in modules if m.metrics.get("workers_active", 0) == 0 and "worker" in m.name.lower())
    missing_dependencies = tuple(sorted({dep for m in modules for dep in m.dependencies if dep.lower().startswith(("host_", "santander", "telegram_"))}))
    attention = tuple(dict.fromkeys(degraded + critical + watchers_problem + workers_problem))[:12]
    can_wait = tuple(m.name for m in modules if m.name not in attention and m.health in {"healthy", "guarded"})[:12]
    requires_approval = tuple(m.name for m in modules if m.risk in {"R2", "R3", "R4", "R5"})
    overall = "degraded" if degraded else "guarded" if critical else "ok"
    benchmark = {
        "module_count": len(modules),
        "healthy_count": len(healthy),
        "degraded_count": len(degraded),
        "critical_count": len(critical),
        "containers_problem_count": len(containers_problem),
        "max_autonomy_without_ugo": "R1",
        "real_side_effects_allowed": False,
    }
    summary = (
        f"James supervision: {len(modules)} modules mapped; {len(healthy)} healthy; "
        f"{len(degraded)} degraded; {len(critical)} critical/guarded high-risk; max autonomy remains R1 dry-run."
    )
    return ModuleDashboard(
        overall_state=overall,
        modules=tuple(modules),
        critical_modules=critical,
        degraded_modules=degraded,
        healthy_modules=healthy,
        watchers_with_problem=watchers_problem,
        workers_with_problem=workers_problem,
        containers_with_problem=containers_problem,
        queues_growing=(),
        missing_dependencies=missing_dependencies,
        attention_now=attention,
        can_wait=can_wait,
        requires_approval=requires_approval,
        executive_summary=summary,
        benchmark=benchmark,
    )


def _normalize_risk(value: str) -> RiskLevel:
    for level in ("R5", "R4", "R3", "R2", "R1", "R0"):
        if level in value.upper():
            return level  # type: ignore[return-value]
    return "R1"


def _component_key(name: str) -> str:
    mapping = {
        "core": "core",
        "adapter_api_host_boundary": "adapter",
        "atendimento": "atendimento",
        "atendimento_api": "atendimento",
        "employee_telegram": "employee_telegram",
        "employee_telegram_gateway": "employee_telegram",
        "campaign": "campaign_center",
        "campaign_center": "campaign_center",
    }
    return mapping.get(name, name)
