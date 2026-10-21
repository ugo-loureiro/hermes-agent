"""Child-process watch, registry, and delegation notices follow the owning profile."""

import pytest

from tests.gateway.test_child_notice_profile_admission import (
    OWNERS,
    _build_rig,
    _consumer_event,
    _for_each_leg,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("surface_a", [True, False])
@pytest.mark.parametrize("owner", OWNERS)
@pytest.mark.parametrize("path", ["watch_match", "heartbeat"])
async def test_watch_events_follow_the_owning_profile(
    monkeypatch, tmp_path, request, surface_a, owner, path, private_db_probe_cleanup,
):
    rig = _build_rig(monkeypatch, tmp_path, request, surface_a, "all")

    async def consume(leg):
        evt = _consumer_event(rig, leg, owner, path)
        rig.registry.completion_queue.put(evt)
        await rig.runner._drain_watch_notifications(rig.registry.completion_queue)
        assert len(rig.admitted) == int(leg.surfaced)
        assert rig.registry.completion_queue.empty()

    await _for_each_leg(rig, owner, surface_a, path, consume)


@pytest.mark.asyncio
@pytest.mark.parametrize("surface_a", [True, False])
@pytest.mark.parametrize("owner", OWNERS)
async def test_registry_drain_follows_the_owning_profile(
    monkeypatch, tmp_path, request, surface_a, owner, private_db_probe_cleanup,
):
    from gateway.run import _profile_runtime_scope

    rig = _build_rig(monkeypatch, tmp_path, request, surface_a, "all")

    async def consume(leg):
        evt = _consumer_event(rig, leg, owner, "registry")
        evt["type"] = "completion"
        evt["exit_code"] = 0
        rig.registry.completion_queue.put(evt)
        with _profile_runtime_scope(rig.homes[leg.name]):
            drained = rig.registry.drain_notifications(session_key=leg.entry.session_key)
        assert len(drained) == int(leg.surfaced)

    await _for_each_leg(rig, owner, surface_a, "registry", consume)


@pytest.mark.asyncio
@pytest.mark.parametrize("surface_a", [True, False])
@pytest.mark.parametrize("owner", OWNERS)
@pytest.mark.parametrize("path", ["async_delegation", "async_delegation_work_closeout"])
async def test_delegation_results_are_never_process_noise(
    monkeypatch, tmp_path, request, surface_a, owner, path, private_db_probe_cleanup,
):
    rig = _build_rig(monkeypatch, tmp_path, request, surface_a, "all")

    async def consume(leg):
        evt = _consumer_event(rig, leg, owner, path)
        evt.pop("parent_session_id")
        async with rig.runner._completion_event_scope(evt):
            assert await rig.runner._deliver_completion_notification_scoped("result", evt) is True
        assert len(rig.admitted) == 1

    await _for_each_leg(rig, owner, surface_a, path, consume)
