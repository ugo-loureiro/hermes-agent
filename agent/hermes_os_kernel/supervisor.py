"""Supervisor component for Hermes OS Kernel."""

from __future__ import annotations

from typing import Any, cast

from .contracts import Objective, Review, RiskLevel, Snapshot


class Supervisor:
    """Compares objective vs observed state and emits evidence-backed review."""

    def review(self, objective: Objective, snapshot: Snapshot) -> Review:
        findings: list[str] = [f"Snapshot status: {snapshot.status}"]
        recommendations: list[str] = []
        risk_level: RiskLevel = "R0"
        status = "on_track"

        operational = snapshot.observations.get("james_operational", {})
        view = operational.get("operational_view", {}) if isinstance(operational, dict) else {}
        adapter_errors = operational.get("adapter_errors", {}) if isinstance(operational, dict) else {}

        if view:
            findings.extend(_findings_from_operational_view(view))
            pending = view.get("pending_detected") or []
            unhealthy = view.get("unhealthy_components") or []
            if pending or unhealthy:
                status = "attention"
                risk_level = "R1"
                recommendations.append("Keep all execution blocked; use read-only MCP/Kanban evidence to scope remediation.")
            else:
                recommendations.append("James operational read-only view is coherent; continue with dry-run planning only.")

        if adapter_errors:
            status = "attention"
            risk_level = "R1"
            findings.append("Read-only adapter errors: " + ", ".join(sorted(adapter_errors)))
            recommendations.append("Confirm James MCP read-only package/path before relying on full operational view.")

        james_health = snapshot.observations.get("james_health", {})
        failed = [name for name, data in james_health.items() if isinstance(data, dict) and not data.get("ok")]
        if failed:
            status = "attention"
            risk_level = "R1"
            findings.append("Compatibility health probe unreachable: " + ", ".join(sorted(failed)))
        elif james_health:
            findings.append("Compatibility health probe responded OK for required local endpoints.")

        docker_inventory = snapshot.observations.get("docker_inventory") or {}
        if isinstance(docker_inventory, dict) and docker_inventory.get("available"):
            findings.append(f"Docker read-only inventory found {docker_inventory.get('count', 0)} James/Evolution containers.")
        elif docker_inventory:
            findings.append("Docker inventory unavailable or failed; MCP/runtime inventory remains primary evidence.")

        modules = snapshot.observations.get("module_supervision") or {}
        if isinstance(modules, dict):
            findings.extend(_findings_from_module_dashboard(modules))
            if modules.get("degraded_modules"):
                status = "attention"
                risk_level = "R1"
                recommendations.append("Prioritize degraded modules with read-only evidence; remediation remains dry-run or approval-gated.")
            if modules.get("requires_approval"):
                recommendations.append("R2+ module actions require explicit Ugo approval; current maximum remains R1 planning/dry-run.")
            attention = modules.get("attention_now") or []
            if attention:
                recommendations.append("Attention now: " + ", ".join(str(item) for item in attention[:8]))
            can_wait = modules.get("can_wait") or []
            if can_wait:
                recommendations.append("Can wait: " + ", ".join(str(item) for item in can_wait[:8]))

        if not recommendations:
            recommendations.append("Proceed with read-only planning and dry-run mapping; no runtime action authorized.")

        return Review(
            objective=objective,
            status=cast(Any, status),
            findings=tuple(findings),
            recommendations=tuple(recommendations),
            risk_level=risk_level,
            confidence=min(0.92, snapshot.confidence + 0.04),
        )


def _findings_from_module_dashboard(modules: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    benchmark = modules.get("benchmark") or {}
    findings.append(
        "Module dashboard: "
        f"{benchmark.get('module_count', 0)} modules; "
        f"healthy={benchmark.get('healthy_count', 0)}; "
        f"degraded={benchmark.get('degraded_count', 0)}; "
        f"critical={benchmark.get('critical_count', 0)}."
    )
    findings.append(str(modules.get("executive_summary") or "Module supervision summary unavailable."))
    if modules.get("containers_with_problem"):
        findings.append("Containers with problem: " + ", ".join(str(item) for item in modules["containers_with_problem"][:8]))
    if modules.get("watchers_with_problem"):
        findings.append("Watchers/modules needing watcher attention: " + ", ".join(str(item) for item in modules["watchers_with_problem"][:8]))
    if modules.get("workers_with_problem"):
        findings.append("Workers needing attention: " + ", ".join(str(item) for item in modules["workers_with_problem"][:8]))
    if modules.get("missing_dependencies"):
        findings.append("External/boundary dependencies declared: " + ", ".join(str(item) for item in modules["missing_dependencies"][:8]))
    return findings


def _findings_from_operational_view(view: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    findings.append(f"Operational health: {view.get('overall_health', 'unknown')}.")
    findings.append(f"Modules observed via registry: {view.get('modules', {}).get('count', 0)}.")
    findings.append(f"Containers declared/observed: {view.get('containers', {}).get('count', 0)}.")
    findings.append(f"Kanban read-only task count: {view.get('kanban', {}).get('task_count', 0)}.")
    risks_gates = view.get("risks_gates", {})
    if isinstance(risks_gates, dict):
        findings.append(
            "Gate markers: "
            f"{risks_gates.get('gate_markers', 0)}; side-effect markers: {risks_gates.get('side_effect_markers', 0)}."
        )
    pending = view.get("pending_detected") or []
    if pending:
        findings.append("Pending detected: " + ", ".join(str(item) for item in pending))
    return findings
