"""Batched child-process notices follow the owning profile and session boundary."""

import asyncio

import pytest

from tests.gateway.test_child_notice_profile_admission import (
    OWNERS,
    _build_rig,
    _for_each_leg,
    _transfer_to_parent,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("surface_a", [True, False])
@pytest.mark.parametrize("owner", OWNERS)
@pytest.mark.parametrize("path", [
    "batch_child_first", "batch_foreground_first", "batch_boundary_first", "batch_boundary_last",
])
async def test_batched_completions_follow_the_owning_profile(
    monkeypatch, tmp_path, request, surface_a, owner, path, private_db_probe_cleanup,
):
    from gateway.run import _async_profile_runtime_scope

    rig = _build_rig(monkeypatch, tmp_path, request, surface_a, "all")
    runner = rig.runner

    async def consume(leg):
        runner._completion_notification_batch_window = 0.01
        if owner == "live_handoff":
            _transfer_to_parent(rig, leg)
        leg.proc.output_buffer = "PROCESS_RESULT"
        evt = runner._build_process_completion_event(leg.watcher, leg.proc, leg.proc.id)
        companion = {**evt, "session_id": f"companion-{leg.name}-{leg.index}",
                     "owner_task_id": "parent-owner", "output": "COMPANION_RESULT"}
        boundary = path in {"batch_boundary_first", "batch_boundary_last"}
        if boundary:
            async with _async_profile_runtime_scope(rig.homes[leg.name]):
                stale = f"stale-{leg.name}-{leg.index}"
                leg.db.create_session(stale, source="telegram")
                leg.db.end_session(stale, end_reason="session_reset")
            companion["parent_session_id"] = stale
        pair = [("PROCESS_RESULT", evt), ("COMPANION_RESULT", companion)]
        if path in {"batch_foreground_first", "batch_boundary_first"}:
            pair.reverse()
        outcomes = await asyncio.gather(*(
            runner._enqueue_process_completion_notification(text, event)
            for text, event in pair
        ))
        assert outcomes[pair.index(("PROCESS_RESULT", evt))] is (True if leg.surfaced else None)
        assert outcomes[pair.index(("COMPANION_RESULT", companion))] is (None if boundary else True)
        texts = "\n".join(event.text for event, _sid, _home in rig.admitted)
        assert ("PROCESS_RESULT" in texts) is leg.surfaced
        assert ("COMPANION_RESULT" in texts) is (not boundary)
        assert len(rig.admitted) == (int(leg.surfaced) if boundary else 1)

    await _for_each_leg(rig, owner, surface_a, path, consume)
