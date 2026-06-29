"""Knowledge Fabric tool.

The public read-only knowledge tool. Legacy knowledge tool names may remain for
compatibility, but runtime reads should route through this tool/bridge.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agent.knowledge_fabric_bridge import knowledge_call
from tools.registry import registry, tool_error

KNOWLEDGE_SCHEMA = {
    "name": "knowledge",
    "description": (
        "Official read-only knowledge gateway for Hermes. Use this instead of "
        "direct Holographic/fact_store/session_search/canonical/project-memory access. "
        "Actions map to Knowledge Fabric APIs: search, lookup, entity, reason, explain."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "lookup", "entity", "reason", "explain"],
                "description": "Knowledge Fabric API to call.",
            },
            "query": {"type": "string", "description": "Query/entity/explanation id."},
            "entities": {"type": "array", "items": {"type": "string"}, "description": "Entities for reason()."},
            "limit": {"type": "integer", "description": "Maximum results."},
        },
        "required": ["action"],
    },
}


def _handle_knowledge(args: Dict[str, Any], **_: Any) -> str:
    try:
        action = str(args.get("action") or "search").lower()
        query: Any = args.get("entities") if action == "reason" and args.get("entities") else args.get("query", "")
        return json.dumps(knowledge_call(action, query, limit=args.get("limit")), ensure_ascii=False)
    except Exception as exc:
        return tool_error(f"Knowledge Fabric unavailable: {exc}")


def _check_knowledge_requirements() -> bool:
    try:
        # Import through the bridge, which resolves profile-safe paths.
        knowledge_call("search", "Hermes", limit=1)
        return True
    except Exception:
        return False


registry.register(
    name="knowledge",
    toolset="knowledge",
    schema=KNOWLEDGE_SCHEMA,
    handler=_handle_knowledge,
    check_fn=_check_knowledge_requirements,
    emoji="🧠",
)
