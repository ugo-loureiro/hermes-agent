"""Hermes Knowledge Fabric bridge and legacy compatibility adapters.

This module is the enforcement boundary for knowledge reads. Hermes runtime code
must not query Holographic/fact-store/session-history/canonical indexes directly;
read access is routed through Knowledge Fabric's public APIs:

    search(), lookup(), entity(), reason(), explain()

Legacy tool names (session_search, fact_store read actions) can keep their
schemas for compatibility, but their read paths should call this module.
"""

from __future__ import annotations

import json
import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

_READ_FACT_ACTIONS = {"search", "probe", "related", "reason", "contradict", "list"}


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home())
    except Exception:
        return Path.home() / ".hermes"


def _ensure_knowledge_fabric_importable() -> None:
    candidates = [str(_hermes_home().parent), str(Path.home() / ".hermes")]
    for candidate in candidates:
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def _load_config() -> Dict[str, Any]:
    home = _hermes_home()
    cfg_path = home / "knowledge_fabric" / "config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            logger.debug("Failed to read Knowledge Fabric config", exc_info=True)
            cfg = {}
    else:
        cfg = {}

    cfg.setdefault("version", "knowledge-fabric/runtime-bridge")
    cfg.setdefault("read_only", True)
    cfg.setdefault(
        "provider_priority",
        ["canonical_relations", "canonical_entities", "holographic", "project_memory_index", "session_search"],
    )
    cfg.setdefault("cache", {"enabled": True, "ttl_seconds": 300, "mode": "memory_only"})
    cfg.setdefault("audit", {})
    cfg["audit"].setdefault("enabled", True)
    cfg["audit"].setdefault("path", str(home / "knowledge_fabric" / "audit" / "query_audit.jsonl"))
    cfg.setdefault("limits", {"default": 10, "provider_limit": 20})
    cfg.setdefault("paths", {})
    # Profile-safe live paths. Canonical artifacts remain explicit config entries.
    cfg["paths"]["memory_store_db"] = str(home / "memory_store.db")
    cfg["paths"]["state_db"] = str(home / "state.db")
    return cfg


@lru_cache(maxsize=1)
def _fabric():
    _ensure_knowledge_fabric_importable()
    from knowledge_fabric.api.fabric import KnowledgeFabric

    return KnowledgeFabric(_load_config())


def reset_knowledge_fabric_cache() -> None:
    """Clear the bridge-level singleton. Used by tests and config reloads."""

    _fabric.cache_clear()


def knowledge_call(method: str, query: Any | None = None, *, limit: int | None = None) -> Dict[str, Any]:
    """Call one public Knowledge Fabric API and return a plain dict."""

    fabric = _fabric()
    method = (method or "search").strip().lower()
    if method not in {"search", "lookup", "entity", "reason", "explain"}:
        method = "search"

    if method == "explain":
        return fabric.explain(str(query or ""))

    fn = getattr(fabric, method)
    if method == "reason" and isinstance(query, (list, tuple)):
        response = fn([str(x) for x in query], limit=limit)
    else:
        response = fn(str(query or ""), limit=limit)
    data = response.to_dict()
    data["knowledge_fabric_enforced"] = True
    return data


def _result_to_fact_like(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = item.get("metadata") or {}
    fact_id = metadata.get("fact_id")
    if fact_id is None:
        source = str(item.get("source_id") or "")
        if source.startswith("fact:"):
            try:
                fact_id = int(source.split(":", 1)[1])
            except Exception:
                fact_id = source
    return {
        "fact_id": fact_id,
        "content": item.get("content", ""),
        "category": item.get("category") or "general",
        "tags": metadata.get("tags", ""),
        "trust_score": item.get("confidence"),
        "provider": item.get("provider"),
        "source_id": item.get("source_id"),
        "aggregate_score": item.get("aggregate_score"),
        "justification": item.get("justification", ""),
        "metadata": metadata,
    }


def fact_store_read_adapter(args: Dict[str, Any]) -> str:
    """Compatibility adapter for legacy fact_store read actions.

    Write actions are intentionally not handled here; explicit writes remain a
    separate memory persistence path, not a knowledge read path.
    """

    action = str(args.get("action") or "search").lower()
    limit = int(args.get("limit", 10) or 10)

    if action == "probe" or action == "related":
        data = knowledge_call("entity", args.get("entity") or args.get("query") or "", limit=limit)
    elif action == "reason":
        data = knowledge_call("reason", args.get("entities") or args.get("query") or "", limit=limit)
    elif action == "contradict":
        data = knowledge_call("search", args.get("query") or "conflict contradiction", limit=limit)
        return json.dumps(
            {
                "results": [_result_to_fact_like(r) for r in data.get("results", [])],
                "conflicts": data.get("conflicts", []),
                "count": len(data.get("results", [])),
                "knowledge_fabric_enforced": True,
                "explanation_id": data.get("explanation_id"),
            },
            ensure_ascii=False,
        )
    elif action == "list":
        # Fabric intentionally exposes retrieval, not raw provider enumeration.
        # Use a broad lookup to preserve a usable compatibility result without
        # reintroducing direct provider reads.
        data = knowledge_call("lookup", args.get("query") or args.get("category") or "Hermes James Ugo", limit=limit)
    else:
        data = knowledge_call("search", args.get("query") or args.get("content") or "", limit=limit)

    results = [_result_to_fact_like(r) for r in data.get("results", [])]
    return json.dumps(
        {
            "results": results,
            "count": len(results),
            "knowledge_fabric_enforced": True,
            "providers_used": data.get("providers_used", []),
            "confidence": data.get("confidence"),
            "explanation_id": data.get("explanation_id"),
            "answer": data.get("answer"),
        },
        ensure_ascii=False,
    )


def _result_to_session_like(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = item.get("metadata") or {}
    return {
        "session_id": metadata.get("session_id") or item.get("source_id"),
        "title": item.get("title", "Knowledge Fabric result"),
        "when": item.get("timestamp"),
        "source": item.get("provider"),
        "snippet": item.get("content", "")[:800],
        "match_message_id": metadata.get("message_id"),
        "messages": [],
        "bookend_start": [],
        "bookend_end": [],
        "knowledge_result": item,
    }


def session_search_adapter(args: Dict[str, Any]) -> str:
    """Compatibility adapter for legacy session_search calls via Fabric."""

    limit = int(args.get("limit", 3) or 3)
    if args.get("session_id") and args.get("around_message_id"):
        query = f"session {args.get('session_id')} message {args.get('around_message_id')}"
        data = knowledge_call("lookup", query, limit=limit)
        mode = "scroll_adapter"
    elif args.get("session_id"):
        query = f"session {args.get('session_id')}"
        data = knowledge_call("lookup", query, limit=limit)
        mode = "read_adapter"
    elif args.get("query"):
        data = knowledge_call("search", args.get("query"), limit=limit)
        mode = "discovery_adapter"
    else:
        data = knowledge_call("lookup", "recent sessions Hermes", limit=limit)
        mode = "browse_adapter"

    results = [_result_to_session_like(r) for r in data.get("results", [])]
    return json.dumps(
        {
            "success": True,
            "mode": mode,
            "results": results,
            "count": len(results),
            "knowledge_fabric_enforced": True,
            "providers_used": data.get("providers_used", []),
            "confidence": data.get("confidence"),
            "explanation_id": data.get("explanation_id"),
            "answer": data.get("answer"),
            "compatibility_note": "Legacy session_search schema is served through Knowledge Fabric; raw DB bookends/windows are provider-internal.",
        },
        ensure_ascii=False,
    )


def assert_no_legacy_knowledge_read(action: str) -> None:
    if action in _READ_FACT_ACTIONS:
        raise RuntimeError(f"Legacy knowledge read action {action!r} must go through Knowledge Fabric")
