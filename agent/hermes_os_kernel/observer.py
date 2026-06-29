"""Observer component for Hermes OS Kernel Phase 0."""

from __future__ import annotations

import json
import subprocess
import urllib.request
from typing import Any, Callable

from .contracts import Objective, Snapshot, SourceRef

KnowledgeFn = Callable[[str, Any], dict[str, Any]]


class Observer:
    """Read-only state collector.

    Public contract: ``observer.snapshot(objective)``.
    The default implementation only uses read-only probes: Knowledge Fabric,
    local HTTP health endpoints, and optional ``docker ps`` inventory.
    """

    def __init__(self, knowledge_fn: KnowledgeFn | None = None, timeout_seconds: float = 2.0) -> None:
        self.knowledge_fn = knowledge_fn
        self.timeout_seconds = timeout_seconds

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

        observations["james_health"] = self._james_health()
        sources.append(SourceRef("James local health endpoints", "http", "read_only", 0.85))

        docker = self._docker_inventory()
        if docker is not None:
            observations["docker_inventory"] = docker
            sources.append(SourceRef("docker ps", "container_inventory", "read_only", 0.8))

        status = "ok" if _all_required_health_ok(observations["james_health"]) else "degraded"
        return Snapshot(
            objective=objective,
            status=status,
            observations=observations,
            sources=tuple(sources),
            confidence=0.82 if status == "ok" else 0.68,
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


def _all_required_health_ok(health: dict[str, Any]) -> bool:
    required = ("core", "adapter", "worker", "atendimento")
    return all(bool(health.get(name, {}).get("ok")) for name in required)
