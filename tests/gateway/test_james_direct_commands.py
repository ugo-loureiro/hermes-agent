from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gateway.platforms.base import MessageEvent
from gateway.session import SessionSource


@pytest.mark.asyncio
async def test_james_status_direct_command_probes_current_local_ports(monkeypatch):
    from gateway.config import Platform
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    seen_urls: list[str] = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"status": "ok"}).encode("utf-8")

        def getcode(self):
            return 200

    def fake_urlopen(url, timeout=0):
        seen_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.delenv("JAMES_TELEGRAM_DIRECT_ADAPTER_BASE_URL", raising=False)
    monkeypatch.delenv("JAMES_TELEGRAM_DIRECT_CORE_BASE_URL", raising=False)
    monkeypatch.delenv("JAMES_TELEGRAM_DIRECT_WORKER_BASE_URL", raising=False)

    event = MessageEvent(
        text="/james-status",
        source=SessionSource(platform=Platform.TELEGRAM, user_id="1", chat_id="1", chat_type="dm"),
        message_id="m1",
    )

    result = await runner._handle_james_status_direct_command(event)

    assert "worker: HTTP 200" in result
    assert "http://127.0.0.1:18085/health" in seen_urls
    assert "http://127.0.0.1:18080/health" in seen_urls
    assert "http://127.0.0.1:18084/health" in seen_urls
    assert "http://127.0.0.1:18083/health" not in seen_urls
    assert "http://127.0.0.1:8700/health" not in seen_urls


def test_james_direct_host_gate_error_is_reported_as_readonly_gate():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    message = runner._james_direct_format_result(
        title="Licenciamento",
        status=403,
        data={"erro": "host_real_calls_not_approved"},
        raw='{"erro":"host_real_calls_not_approved"}',
    )

    assert "HOST read-only não aprovado" in message
    assert "host_real_calls_not_approved" in message
    assert "Dados sensíveis ocultados" in message


@pytest.mark.asyncio
async def test_james_license_command_uses_direct_adapter_flow(monkeypatch):
    from gateway.run import GatewayRunner
    from gateway.platforms.base import MessageEvent
    from gateway.session import SessionSource
    from gateway.config import Platform

    runner = object.__new__(GatewayRunner)
    calls = []

    async def fake_http_json(*, path, payload=None):
        calls.append({"path": path, "payload": payload})
        return 200, {"status": "ok", "valorFinal": 100.0, "origem": "daypag_licenciamento"}, "{}"

    monkeypatch.setattr(runner, "_james_direct_http_json", fake_http_json)
    event = MessageEvent(
        text="/licenca 123456789",
        source=SessionSource(platform=Platform.TELEGRAM, user_id="1", chat_id="1", chat_type="dm"),
        message_id="m1",
    )

    result = await runner._handle_james_vehicle_direct_command(event, "licenciamento")

    assert calls == [{"path": "/api-interna/consultar-licenciamento", "payload": {"renavam": "123456789"}}]
    assert "James direto — Licenciamento" in result
    assert "Status: OK" in result
    assert "Valor final: `100.0`" in result
    assert "Origem: `daypag_licenciamento`" in result


@pytest.mark.asyncio
async def test_james_proposta_command_calls_core_draft_without_pix_or_whatsapp(monkeypatch):
    from gateway.run import GatewayRunner
    from gateway.platforms.base import MessageEvent
    from gateway.session import SessionSource
    from gateway.config import Platform

    runner = object.__new__(GatewayRunner)
    calls = []

    async def fake_http_json(*, path, payload=None, target="adapter"):
        calls.append({"target": target, "path": path, "payload": payload})
        return 201, {
            "status": "ok",
            "proposta": {
                "estado": "aguardando_aprovacao_humana",
                "servico": "licenciamento",
                "valor_cliente_centavos": 16000,
                "side_effects": {"pix": "blocked", "whatsapp": "blocked", "campanha": "blocked"},
            },
        }, "{}"

    monkeypatch.setattr(runner, "_james_direct_http_json", fake_http_json)
    event = MessageEvent(
        text="/proposta 123456789",
        source=SessionSource(platform=Platform.TELEGRAM, user_id="1", chat_id="1", chat_type="dm"),
        message_id="m1",
    )

    result = await runner._handle_james_proposta_command(event)

    assert calls == [{"target": "core", "path": "/core/propostas/rascunho", "payload": {"renavam": "123456789", "servicos": ["licenciamento"]}}]
    assert "James direto — Proposta assistida" in result
    assert "Status: OK" in result
    assert "aguardando_aprovacao_humana" in result
    assert "PIX bloqueado" in result
    assert "WhatsApp bloqueado" in result
    assert "Dados sensíveis ocultados" in result


@pytest.mark.asyncio
async def test_james_commands_without_renavam_do_not_call_core_or_adapter(monkeypatch):
    from gateway.run import GatewayRunner
    from gateway.platforms.base import MessageEvent
    from gateway.session import SessionSource
    from gateway.config import Platform

    runner = object.__new__(GatewayRunner)

    async def fake_http_json(*, path, payload=None, target="adapter"):
        raise AssertionError("missing RENAVAM must not call Core or adapter")

    monkeypatch.setattr(runner, "_james_direct_http_json", fake_http_json)
    event = MessageEvent(
        text="/proposta",
        source=SessionSource(platform=Platform.TELEGRAM, user_id="1", chat_id="1", chat_type="dm"),
        message_id="m1",
    )

    result = await runner._handle_james_proposta_command(event)

    assert "Me manda o RENAVAM" in result
    assert "llm_calls=0" in result
    assert "sem chamada ao Core" in result


def test_james_help_command_is_operator_only_and_lists_safe_commands():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    result = runner._james_help_text()

    assert "/licenca <renavam>" in result
    assert "/licenciamento <renavam>" in result
    assert "/transferencia <renavam>" in result
    assert "/status_james" in result
    assert "/proposta <renavam>" in result
    assert "Cliente real: bloqueado" in result
    assert "WhatsApp: bloqueado" in result
    assert "PIX: bloqueado" in result


def test_command_registry_exposes_current_james_telegram_commands():
    from hermes_cli.commands import resolve_command

    assert resolve_command("licenca").name == "licenca"
    assert resolve_command("licenciamento").name == "licenca"
    assert resolve_command("transferencia").name == "transferencia"
    assert resolve_command("proposta").name == "proposta"
    assert resolve_command("status_james").name == "status_james"
    assert resolve_command("james-status").name == "status_james"
    assert resolve_command("james").name == "james"
