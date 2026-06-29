"""Read-only adapter for James operational surfaces.

This module is intentionally conservative: it calls only James MCP read-only
functions, localhost GET/status probes implemented by that MCP package, and
read-only local registry files. It never sends POST/PUT/PATCH/DELETE requests,
never starts/restarts containers, and never writes to James.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

JAMES_REPO = Path("/home/ugo/ops/james-2")
REGISTRY_DIR = JAMES_REPO / "docs/james-organization/registries"

READONLY_TOOL_NAMES = (
    "james_health_summary",
    "james_container_status",
    "james_core_status",
    "james_adapter_status",
    "james_atendimento_status",
    "james_employee_telegram_status",
    "james_campaign_center_status",
    "james_kanban_snapshot_readonly",
    "james_runtime_inventory",
    "james_modules_registry_readonly",
)

OPTIONAL_REGISTRY_FILES = {
    "workers": REGISTRY_DIR / "james_workers_registry.yaml",
    "watchers": REGISTRY_DIR / "james_watchers_registry.yaml",
    "capabilities": REGISTRY_DIR / "james_capabilities_registry.yaml",
}

SENSITIVE_TEXT_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "dsn",
)

MUTATIVE_MARKERS = (
    "send",
    "post",
    "put",
    "patch",
    "delete",
    "restart",
    "rebuild",
    "up -d",
    "compose up",
    "docker start",
    "docker stop",
    "pix",
    "santander",
    "whatsapp",
)


def _safe_import_server() -> Any | None:
    if not JAMES_REPO.exists():
        return None
    repo_text = str(JAMES_REPO)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)
    try:
        from packages.james_mcp_readonly import server  # type: ignore[import-not-found]

        return server
    except Exception:
        return None


class JamesReadOnlyAdapter:
    """Collects James state through read-only surfaces only."""

    def __init__(self, server: Any | None = None, repo_root: Path = JAMES_REPO) -> None:
        self.repo_root = repo_root
        self.server = server if server is not None else _safe_import_server()
        self.transport = "james_python_mcp_functions" if self.server is not None else "local_readonly_fallback"

    def available_tools(self) -> tuple[str, ...]:
        if self.server is None:
            return READONLY_TOOL_NAMES
        return tuple(name for name in READONLY_TOOL_NAMES if callable(getattr(self.server, name, None)))

    def collect(self, *, kanban_limit: int = 20) -> dict[str, Any]:
        """Return a consolidated read-only operational snapshot of James."""

        tools: dict[str, Any] = {}
        errors: dict[str, str] = {}
        for name in READONLY_TOOL_NAMES:
            if name == "james_kanban_snapshot_readonly":
                payload = self._call_tool(name, limit=kanban_limit)
            else:
                payload = self._call_tool(name)
            if isinstance(payload, dict) and payload.get("adapter_error"):
                errors[name] = str(payload.get("adapter_error"))
            tools[name] = _sanitize(payload)

        registries = self._read_optional_registries()
        consolidated = _consolidate(tools, registries)
        return {
            "readonly": True,
            "real_side_effects_executed": False,
            "repo_root": str(self.repo_root),
            "mcp_transport": self.transport,
            "mcp_tools_expected": list(READONLY_TOOL_NAMES),
            "mcp_tools_available": list(self.available_tools()),
            "mcp": tools,
            "registries": registries,
            "operational_view": consolidated,
            "adapter_errors": errors,
            "mutative_methods_allowed": [],
        }

    def _call_tool(self, name: str, **kwargs: Any) -> dict[str, Any]:
        if self.server is None:
            return _fallback_tool(name, self.repo_root, **kwargs)
        tool: Callable[..., Any] | None = getattr(self.server, name, None)
        if tool is None:
            return {"readonly": True, "ok": False, "adapter_error": "readonly_tool_unavailable"}
        try:
            payload = tool(**kwargs) if kwargs else tool()
        except Exception as exc:
            return {"readonly": True, "ok": False, "adapter_error": type(exc).__name__}
        if isinstance(payload, dict):
            return payload
        return {"readonly": True, "ok": True, "payload": payload}

    def _read_optional_registries(self) -> dict[str, Any]:
        registries: dict[str, Any] = {}
        for key, path in OPTIONAL_REGISTRY_FILES.items():
            registries[key] = _read_registry_summary(path)
        return registries


def _fallback_tool(name: str, repo_root: Path, **kwargs: Any) -> dict[str, Any]:
    endpoints = {
        "james_core_status": ("core", "http://127.0.0.1:18080/health"),
        "james_adapter_status": ("adapter", "http://127.0.0.1:18083/health"),
        "james_atendimento_status": ("atendimento", "http://127.0.0.1:18086/atendimento/status"),
        "james_employee_telegram_status": ("employee_telegram", "http://127.0.0.1:18088/health"),
        "james_campaign_center_status": ("campaign_center", "http://127.0.0.1:18087/health"),
    }
    if name in endpoints:
        component, url = endpoints[name]
        return {"component": component, **_fallback_http_get(url)}
    if name == "james_health_summary":
        components = {key.replace("james_", "").replace("_status", ""): _fallback_tool(key, repo_root) for key in endpoints}
        return {
            "readonly": True,
            "external_side_effects": False,
            "summary": {key: value.get("ok") for key, value in components.items()},
            "components": components,
            "fallback": True,
        }
    if name == "james_container_status":
        expected = [
            "james-adapter-api",
            "james-core-api",
            "james-employee-telegram-gateway",
            "james-atendimento-api",
            "james-atendimento-cockpit",
            "james-ingestion",
            "james-enrichment",
            "james-messaging-gateway",
            "james-campaign-engine",
            "james-billing-pix",
            "james-ops",
        ]
        return {
            "readonly": True,
            "external_side_effects": False,
            "check_mode": "declared_inventory_only_no_process_spawn",
            "containers": [{"name": item, "runtime_state": "not_checked"} for item in expected],
            "fallback": True,
        }
    if name == "james_runtime_inventory":
        artifacts = {
            "docker_compose": repo_root / "infra/docker/docker-compose.yml",
            "core_api": repo_root / "packages/james_core_api/server.py",
            "adapter_api": repo_root / "packages/james_adapter/server.py",
            "atendimento_api": repo_root / "packages/james_atendimento/server.py",
            "employee_telegram": repo_root / "packages/james_employee_telegram/server.py",
            "campaign_center_ui": repo_root / "apps/james-campaign-center/index.html",
        }
        return {
            "readonly": True,
            "external_side_effects": False,
            "mutative_methods_allowed": [],
            "repo_root": str(repo_root),
            "artifacts": {key: str(path) for key, path in artifacts.items() if path.exists()},
            "fallback": True,
        }
    if name == "james_kanban_snapshot_readonly":
        return _fallback_kanban(kwargs.get("limit", 20))
    if name == "james_modules_registry_readonly":
        return _fallback_modules_registry(repo_root)
    return {"readonly": True, "ok": False, "adapter_error": "fallback_tool_unknown"}


def _fallback_http_get(url: str, timeout: float = 2.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - localhost read-only probe
            raw = response.read(65536).decode("utf-8", errors="replace")
            try:
                payload: Any = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError:
                payload = raw.strip()[:500]
            return {
                "readonly": True,
                "external_side_effects": False,
                "ok": 200 <= int(response.status) < 300,
                "method": "GET",
                "url": url,
                "status_code": int(response.status),
                "payload": _sanitize(payload),
                "fallback": True,
            }
    except Exception as exc:
        return {"readonly": True, "external_side_effects": False, "ok": False, "method": "GET", "url": url, "error": type(exc).__name__, "fallback": True}


def _fallback_kanban(limit: int = 20) -> dict[str, Any]:
    path = Path("/home/ugo/.hermes/kanban.db")
    uri = f"file:{path}?mode=ro"
    if not path.exists():
        return {"readonly": True, "ok": False, "sqlite_uri": uri, "error": "kanban_db_missing", "tasks": [], "fallback": True}
    safe_limit = max(1, min(int(limit), 100))
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, title, status, assignee, tenant, priority FROM tasks WHERE tenant = ? ORDER BY priority DESC, id ASC LIMIT ?",
            ("james-despachante", safe_limit),
        ).fetchall()
    except sqlite3.Error as exc:
        return {"readonly": True, "ok": False, "sqlite_uri": uri, "error": type(exc).__name__, "tasks": [], "fallback": True}
    finally:
        try:
            conn.close()  # type: ignore[name-defined]
        except Exception:
            pass
    return {"readonly": True, "ok": True, "sqlite_uri": uri, "tasks": [dict(row) for row in rows], "fallback": True}


def _fallback_modules_registry(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs/james-organization/registries/james_modules_registry.yaml"
    summary = _read_registry_summary(path)
    modules = _extract_yaml_items(path, root_key="modules")
    return {
        "readonly": True,
        "external_side_effects": False,
        "mutative_methods_allowed": [],
        "ok": bool(summary.get("ok")),
        "source": {"kind": "canonical", "path": str(path)},
        "counts": {"modules": len(modules), "filtered": len(modules)},
        "modules": modules,
        "fallback": True,
    }


def _extract_yaml_items(path: Path, root_key: str) -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore[import-not-found]

        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(loaded, dict) or not isinstance(loaded.get(root_key), list):
        return []
    items = []
    for raw in loaded[root_key]:
        if not isinstance(raw, dict):
            continue
        items.append(
            _sanitize(
                {
                    "module": raw.get("module") or raw.get("module_id") or "",
                    "type": raw.get("type") or [],
                    "path_repo": raw.get("path_repo") or raw.get("repo_paths") or [],
                    "process_container": raw.get("process_container") or raw.get("containers") or [],
                    "gates": raw.get("gates") or [],
                    "possible_side_effects": raw.get("possible_side_effects") or [],
                    "health_status_endpoint": raw.get("health_status_endpoint") or raw.get("endpoints") or {},
                }
            )
        )
    return items


def _read_registry_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"readonly": True, "ok": False, "path": str(path), "error": "registry_missing"}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"readonly": True, "ok": False, "path": str(path), "error": type(exc).__name__}
    return {
        "readonly": True,
        "ok": True,
        "path": str(path),
        "bytes": len(text.encode("utf-8")),
        "line_count": text.count("\n") + 1,
        "summary": _registry_text_summary(text),
    }


def _registry_text_summary(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines()]
    item_lines = [line for line in lines if line.startswith("-") or line.startswith("  -")]
    watcher_mentions = sum(1 for line in lines if "watcher" in line.lower())
    worker_mentions = sum(1 for line in lines if "worker" in line.lower())
    capability_mentions = sum(1 for line in lines if "capability" in line.lower() or "capability_id" in line.lower())
    gate_mentions = sum(1 for line in lines if "gate" in line.lower() or "approval_required" in line.lower())
    return {
        "item_like_lines": len(item_lines),
        "watcher_mentions": watcher_mentions,
        "worker_mentions": worker_mentions,
        "capability_mentions": capability_mentions,
        "gate_mentions": gate_mentions,
    }


def _consolidate(tools: dict[str, Any], registries: dict[str, Any]) -> dict[str, Any]:
    health = tools.get("james_health_summary", {}) if isinstance(tools.get("james_health_summary"), dict) else {}
    summary = health.get("summary", {}) if isinstance(health.get("summary"), dict) else {}
    modules = tools.get("james_modules_registry_readonly", {})
    kanban = tools.get("james_kanban_snapshot_readonly", {})
    containers = tools.get("james_container_status", {})

    unhealthy = sorted(name for name, ok in summary.items() if ok is not True)
    module_count = _dig_count(modules, "modules")
    task_count = len(kanban.get("tasks", []) or []) if isinstance(kanban, dict) else 0
    container_count = len(containers.get("containers", []) or []) if isinstance(containers, dict) else 0
    registry_ok = {name: bool(data.get("ok")) for name, data in registries.items() if isinstance(data, dict)}

    gates = _gate_summary(modules, registries)
    pending = []
    if unhealthy:
        pending.append("health_degraded:" + ",".join(unhealthy))
    if not registry_ok.get("workers", False):
        pending.append("workers_registry_unavailable")
    if not registry_ok.get("watchers", False):
        pending.append("watchers_registry_unavailable")
    if not registry_ok.get("capabilities", False):
        pending.append("capabilities_registry_unavailable")

    return {
        "overall_health": "ok" if not unhealthy else "degraded",
        "unhealthy_components": unhealthy,
        "containers": {"count": container_count, "source": "james_container_status"},
        "modules": {"count": module_count, "source": "james_modules_registry_readonly"},
        "workers": registries.get("workers", {}),
        "watchers": registries.get("watchers", {}),
        "capabilities": registries.get("capabilities", {}),
        "atendimento": tools.get("james_atendimento_status", {}),
        "campaigns": tools.get("james_campaign_center_status", {}),
        "employee_telegram": tools.get("james_employee_telegram_status", {}),
        "kanban": {"ok": kanban.get("ok") if isinstance(kanban, dict) else False, "task_count": task_count},
        "risks_gates": gates,
        "pending_detected": pending,
    }


def _dig_count(payload: Any, key: str) -> int:
    if not isinstance(payload, dict):
        return 0
    counts = payload.get("counts")
    if isinstance(counts, dict) and isinstance(counts.get(key), int):
        return int(counts[key])
    value = payload.get(key)
    if isinstance(value, list):
        return len(value)
    return 0


def _gate_summary(modules: Any, registries: dict[str, Any]) -> dict[str, Any]:
    gate_markers = 0
    side_effect_markers = 0
    if isinstance(modules, dict):
        module_list = modules.get("modules") or []
        for module in module_list if isinstance(module_list, list) else []:
            text = json.dumps(module, ensure_ascii=False).lower()
            gate_markers += text.count("gate") + text.count("approval")
            side_effect_markers += text.count("side_effect") + text.count("whatsapp") + text.count("pix") + text.count("santander")
    for data in registries.values():
        if isinstance(data, dict):
            summary = data.get("summary", {})
            if isinstance(summary, dict):
                gate_markers += int(summary.get("gate_mentions", 0) or 0)
    return {
        "gate_markers": gate_markers,
        "side_effect_markers": side_effect_markers,
        "sensitive_domains_preserved": ["WhatsApp", "Telegram real", "PIX/Santander", "HOST", "providers/auth"],
        "phase1_execution_allowed": False,
    }


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if any(marker in key_text.lower() for marker in SENSITIVE_TEXT_MARKERS):
                continue
            result[key_text] = _sanitize(child)
        return result
    if isinstance(value, list):
        return [_sanitize(child) for child in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS):
            return "[redacted]"
        return value[:500]
    return value


def mutative_markers_in_source(source: str) -> list[str]:
    lowered = source.lower()
    return [marker for marker in MUTATIVE_MARKERS if marker in lowered]
