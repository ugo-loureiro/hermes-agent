"""API admission never blocks the shared owner loop on a held SQLite writer (every HTTP door)."""
import asyncio
import sqlite3
import threading

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

KEY = 'off-loop-admission-key-long-enough'
HOLD_S = 1.5
AUTH = {'Authorization': 'Bearer ' + KEY}

DOORS = [
    ('chat', '/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'hi'}]}, {}, 200),
    ('responses', '/v1/responses', {'input': 'hi'}, {'Idempotency-Key': 'resp-1'}, 200),
    ('runs', '/v1/runs', {'input': 'hi'}, {}, 202),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('name,path,body,headers,expected', DOORS, ids=[d[0] for d in DOORS])
async def test_admission_waits_for_the_writer_off_the_owner_loop(api, owner, monkeypatch, name, path, body,
                                                                headers, expected):
    from gateway.platforms import api_server_runs

    async def handle(event):
        from gateway.session_results import execution_result
        execution_result.get()['result'] = {'final_response': 'ok', 'messages': []}
        return 'ok'

    async def no_execution(*args, **kwargs):
        pass
    owner.runner._handle_message = handle
    monkeypatch.setattr(api_server_runs, '_execute_run', no_execution)
    api._api_key = KEY
    app = web.Application()
    app.router.add_post(path, getattr(api, {'chat': '_handle_chat_completions', 'responses': '_handle_responses',
                                            'runs': '_handle_runs'}[name]))
    async with TestClient(TestServer(app)) as client:
        # Another process holds the profile's state.db writer for HOLD_S (a long transaction).
        holder = sqlite3.connect(owner.db.db_path, timeout=0, isolation_level=None, check_same_thread=False)
        holder.execute('BEGIN IMMEDIATE')
        write_started = threading.Event()
        writer_released = threading.Event()
        execute_write = owner.db._execute_write

        def release_writer():
            try:
                holder.execute('COMMIT')
            finally:
                writer_released.set()

        release_timer = threading.Timer(HOLD_S, release_writer)

        def observe_contended_write(write):
            # Start the hold budget when the admission actually reaches SQLite, not while a cold
            # request imports/parses ahead of it.  The old max-gap threshold measured unrelated OS
            # scheduling under a parallel full gate and failed despite many 20 ms loop heartbeats.
            if not write_started.is_set():
                write_started.set()
                release_timer.start()
            return execute_write(write)

        monkeypatch.setattr(owner.db, '_execute_write', observe_contended_write)
        request = asyncio.create_task(client.post(path, json=body, headers={**AUTH, **headers}))
        heartbeats_while_contended = 0
        while not request.done():
            await asyncio.sleep(0.02)
            if write_started.is_set() and not writer_released.is_set():
                heartbeats_while_contended += 1
        response = await request
        if write_started.is_set():
            release_timer.join(timeout=HOLD_S)
        else:
            holder.execute('ROLLBACK')
        holder.close()
        assert response.status == expected, await response.text()
    # Other sessions, timers and sockets kept running while the admission waited on the writer.
    assert write_started.is_set(), 'request never reached the contended admission write'
    assert heartbeats_while_contended > 0, 'owner loop made no progress behind the admission write'
