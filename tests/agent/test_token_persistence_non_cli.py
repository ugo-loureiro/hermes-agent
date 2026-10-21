from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch
import json
import sys

from run_agent import AIAgent

def _mock_response(*, usage: dict, content: str = "done"):
    msg = SimpleNamespace(content=content, tool_calls=None)
    choice = SimpleNamespace(message=msg, finish_reason="stop")
    return SimpleNamespace(
        choices=[choice],
        model="test/model",
        usage=SimpleNamespace(**usage),
    )

def _make_agent(session_db, *, platform: str):
    with (
        patch("model_tools.get_tool_definitions", return_value=[]),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            session_db=session_db,
            session_id=f"{platform}-session",
            platform=platform,
        )
    agent.client = MagicMock()
    agent.client.chat.completions.create.return_value = _mock_response(
        usage={
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        }
    )
    return agent

def test_run_conversation_persists_tokens_for_telegram_sessions():
    session_db = MagicMock()
    agent = _make_agent(session_db, platform="telegram")

    result = agent.run_conversation("hello")

    assert result["final_response"] == "done"
    # Per-call deltas are enqueued for the SessionDB background writer
    # (queue_token_counts) rather than written inline on the turn thread.
    session_db.queue_token_counts.assert_called_once()
    assert session_db.queue_token_counts.call_args.args[0] == "telegram-session"

def test_session_search_runtime_routes_through_knowledge_fabric(monkeypatch):
    captured = []

    def fake_session_search_adapter(args):
        captured.append(dict(args))
        return json.dumps({"success": True, "results": [], "knowledge_fabric_enforced": True})

    import agent.knowledge_fabric_bridge as bridge
    from agent.tool_executor import _ToolCallRef, _resolve_sequential_dispatch

    monkeypatch.setattr(bridge, "session_search_adapter", fake_session_search_adapter)

    agent = _make_agent(None, platform="acp")
    args = {"query": "Hermes", "detail": "full"}
    concurrent_result = json.loads(agent._invoke_tool("session_search", args, "task-id"))
    sequential_dispatch = _resolve_sequential_dispatch(
        agent, _ToolCallRef("session_search", args, "task-id", "tool-call-id", []), [],
    )
    sequential_result = json.loads(sequential_dispatch.execute(args))

    assert concurrent_result["success"] is True
    assert sequential_result["success"] is True
    assert concurrent_result["knowledge_fabric_enforced"] is True
    assert sequential_result["knowledge_fabric_enforced"] is True
    assert captured == [args, args]
    assert agent._session_db is None
