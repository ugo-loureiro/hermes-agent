"""Observer component for Hermes OS Kernel.

Phase 1 keeps the Observer strictly read-only while broadening visibility from
basic health probes to James MCP read-only tools, registries, Kanban snapshots,
workers/watchers/capabilities, and runtime inventory.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from typing import Any, Callable, cast

from .contracts import Objective, Snapshot, SourceRef
from .james_readonly import JamesReadOnlyAdapter

KnowledgeFn = Callable[[str, Any], dict[str, Any]]


class Observer:
    """Read-only state collector.

    Public contract: ``observer.snapshot(objective)``.
    The default implementation only uses read-only probes: Knowledge Fabric,
    James MCP read-only tools, local HTTP health endpoints, registries, Kanban
    read-only snapshots, and optional ``docker ps`` inventory.
    """

    def __init__(
        self,
        knowledge_fn: KnowledgeFn | None = None,
        timeout_seconds: float = 2.0,
        james_adapter: Any | None = None,
    ) -> None:
        self.knowledge_fn = knowledge_fn
        self.timeout_seconds = timeout_seconds
        self.james_adapter = james_adapter or JamesReadOnlyAdapter()

    def snapshot(self, objective: Objective) -> Snapshot:
        sources: list[SourceRef] = []
        observations: dict[str, Any] = {
            "objective": objective.text,
            "read_only": True,
            "real_side_effects_executed": False,
        }

        if self.knowledge_fn:
            try:
                knowledge = self.knowledge_fn("search", objective.text)
                observations["knowledge_fabric"] = _compact_knowledge(knowledge)
                sources.append(SourceRef("Knowledge Fabric", "knowledge", "read_only", 0.9, {"method": "search"}))
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                observations["knowledge_fabric_error"] = type(exc).__name__
                sources.append(SourceRef("Knowledge Fabric", "knowledge", "read_only", 0.4, {"error": type(exc).__name__}))

        james_operational = self.james_adapter.collect(kanban_limit=20)
        observations["james_operational"] = james_operational
        sources.extend(
            (
                SourceRef("James MCP read-only", "mcp", "read_only", 0.88, {"tools": james_operational.get("mcp_tools_available", [])}),
                SourceRef("James local health/status endpoints", "http", "read_only", 0.85),
                SourceRef("James registries", "registry", "read_only", 0.84),
                SourceRef("James Kanban read-only", "kanban", "read_only", 0.8),
            )
        )

        # Keep the older direct probes as a secondary compatibility source while
        # MCP read-only is being adopted. Both are read-only and local only.
        observations["james_health"] = self._james_health()
        sources.append(SourceRef("Hermes direct James health compatibility probe", "http", "read_only", 0.75))

        docker = self._docker_inventory()
        if docker is not None:
            observations["docker_inventory"] = docker
            sources.append(SourceRef("docker ps", "container_inventory", "read_only", 0.8))

        status = _overall_status(observations)
        return Snapshot(
            objective=objective,
            status=cast(Any, status),
            observations=observations,
            sources=tuple(sources),
            confidence=0.86 if status == "ok" else 0.72 if status == "degraded" else 0.6,
        )

    def _james_health(self) -> dict[str, Any]:
        endpoints = {
            "core": "http://127.0.0.1:18080/health",
            "adapter": "http://127.0.0.1:18083/health",
            "worker": "http://127.0.0.1:18084/health",
            "atendimento": "http://127.0.0.1:18086/health",
            "employee_telegram": "http://127.0.0.1:18088/health",
        }
        result: dict[str, Any] = {}
        for name, url in endpoints.items():
            result[name] = _http_text(url, self.timeout_seconds)
        return result

    def _docker_inventory(self) -> dict[str, Any] | None:
        try:
            proc = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            return None
        if proc.returncode != 0:
            return {"available": False, "error": "docker_ps_failed"}
        containers = []
        for line in proc.stdout.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = item.get("Names", "")
            if "james" in name.lower() or "evolution" in name.lower():
                containers.append({"name": name, "status": item.get("Status", ""), "state": item.get("State", "")})
        return {"available": True, "containers": containers, "count": len(containers)}


def _http_text(url: str, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - localhost read-only probe
            body = response.read(200).decode("utf-8", errors="replace").strip()
            return {"ok": 200 <= response.status < 300, "status": response.status, "body": body[:40]}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def _compact_knowledge(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_fabric_enforced": data.get("knowledge_fabric_enforced"),
        "confidence": data.get("confidence"),
        "providers_used": data.get("providers_used", []),
        "result_count": len(data.get("results", []) or []),
        "explanation_id": data.get("explanation_id"),
    }


def _overall_status(observations: dict[str, Any]) -> str:
    operational = observations.get("james_operational", {})
    view = operational.get("operational_view", {}) if isinstance(operational, dict) else {}
    if view.get("overall_health") == "degraded":
        return "degraded"
    if operational.get("adapter_errors"):
        return "degraded"
    health = observations.get("james_health", {})
    required = ("core", "adapter", "atendimento")
    if all(bool(health.get(name, {}).get("ok")) for name in required):
        return "ok"
    if view:
        return "ok" if not view.get("pending_detected") else "degraded"
    return "unknown"
