# Hermes OS — Fase 1.1 — MCP real + Kanban target fix

Branch: `hermes-os-kernel-phase0`

## Escopo

Refinar a integração read-only do Hermes OS Kernel para usar a superfície MCP real do James quando disponível e corrigir o alvo Kanban read-only.

## Guardrails

- Não alterou runtime do James.
- Não instalou ferramentas.
- Não executou ação mutativa.
- Não habilitou WhatsApp real, Telegram real, PIX/Santander ou HOST mutativo.
- Não alterou Copilot/autonomia.
- Não mexeu na `main`.
- Não fez rebase/merge/force-push.

## Investigação MCP

Superfície oficial documentada pelo James:

```text
/home/ugo/ops/james-2/packages/james_mcp_readonly/server.py
/home/ugo/ops/james-2/docs/hj-1-mcp-james-readonly-v0.md
```

Transporte oficial: MCP stdio.

Comando oficial no contexto do repo James:

```text
uv run python -m packages.james_mcp_readonly.server
```

Resultado da investigação:

```text
mcp disponível no venv/uv do James: sim
mcp disponível diretamente no Python do Hermes: não
instalação nova: não realizada
```

Implementação: o adaptador Hermes chama o MCP real do James via stdio usando o ambiente já existente do repo James (`uv run python`) e mantém fallback local read-only se a chamada falhar.

Tools confirmadas na integração:

```text
james_health_summary
james_container_status
james_core_status
james_adapter_status
james_atendimento_status
james_employee_telegram_status
james_campaign_center_status
james_kanban_snapshot_readonly
james_runtime_inventory
james_modules_registry_readonly
```

## Investigação Kanban

O alvo anterior `/home/ugo/.hermes/kanban.db` existe mas tem 0 tasks.

Targets detectados:

- `hermes-otimizacao`: 14 tasks; statuses={'done': 14} tenants={'None': 14}
- `hermes-workspace-pilot`: 5 tasks; statuses={'done': 5} tenants={'None': 5}
- `hj-gateway-stability`: 12 tasks; statuses={'blocked': 3, 'done': 9} tenants={'None': 12}
- `james-despachante`: 526 tasks; statuses={'archived': 55, 'blocked': 2, 'done': 463, 'todo': 6} tenants={'None': 511, 'james-despachante': 15}
- `legacy_root`: 0 tasks; statuses={} tenants={}

Alvo corrigido:

```text
board_slug: james-despachante
db_path: /home/ugo/.hermes/kanban/boards/james-despachante/kanban.db
total_tasks: 526
status_counts: {'archived': 55, 'blocked': 2, 'done': 463, 'todo': 6}
tenant_counts: {'None': 511, 'james-despachante': 15}
```

Observação: o board correto é `james-despachante`; há 526 tasks no board, sendo 15 com coluna `tenant='james-despachante'` e 511 históricas com `tenant=NULL`. O MCP read-only mantém o filtro tenant para o snapshot retornado, mas o Observer agora registra também o board total e os targets detectados para evitar falso vazio.

## Arquivos alterados

```text
agent/hermes_os_kernel/james_readonly.py
agent/hermes_os_kernel/__init__.py
tests/agent/test_hermes_os_kernel_phase0.py
docs/hermes-os-phase1.1-mcp-kanban.md
```

## Ciclos read-only executados

Audit records:

```text
/home/ugo/.hermes/knowledge_fabric/reports/hermes_os_phase1_1_mcp_kanban/*_audit.json
/home/ugo/.hermes/knowledge_fabric/reports/hermes_os_phase1_1_mcp_kanban/summary.json
```

| Ciclo | Snapshot | Review | Saúde | Risco | Confiança | Transporte | MCP real | Tools | Kanban board | Kanban total | Tasks retornadas | Efeito real? |
|---|---|---|---|---|---:|---|---|---:|---|---:|---:|---|
| visao_geral_james | ok | on_track | ok | R1 | 0.86 | mcp_real_stdio | true | 10 | james-despachante | 526 | 15 | false |
| atendimento_monitorado | ok | on_track | ok | R1 | 0.86 | mcp_real_stdio | true | 10 | james-despachante | 526 | 15 | false |
| workers_filas | ok | on_track | ok | R1 | 0.86 | mcp_real_stdio | true | 10 | james-despachante | 526 | 15 | false |
| campanhas_dry_run | ok | on_track | ok | R1 | 0.86 | mcp_real_stdio | true | 10 | james-despachante | 526 | 15 | false |
| gates_efeitos_reais | ok | on_track | ok | R1 | 0.86 | mcp_real_stdio | true | 10 | james-despachante | 526 | 15 | false |

## Resultado técnico

- `mcp_transport=mcp_real_stdio` em todos os ciclos.
- `mcp_real_available=true` em todos os ciclos.
- `source_by_tool=mcp_real` para as 10 tools.
- `kanban_target.board_slug=james-despachante`.
- `kanban_target.task_count=526`.
- `james_kanban_snapshot_readonly` retornou 15 tasks filtradas por tenant.
- `limitations=[]` nos ciclos executados.

## Validações

```text
uv run --with pytest pytest tests/agent/test_hermes_os_kernel_phase0.py -q -o 'addopts='
7 passed in 0.70s
```

```text
PYTHONPATH=/home/ugo/.hermes:/home/ugo/.hermes/hermes-agent python3 -m compileall -q agent/hermes_os_kernel tests/agent/test_hermes_os_kernel_phase0.py
OK
```

```text
git diff --check
OK
```

Scans:

```text
secret scan refinado: 0 hits
mutative-call scan refinado: 0 hits
```

## Estado James

`git -C /home/ugo/ops/james-2 status --short` mostrou apenas alterações/untracked preexistentes em `docs/reports/` T50F.

`docker ps` read-only mostrou containers James/Evolution `Up/healthy`. Nenhum restart/rebuild/start/stop foi executado.

## Riscos e próximos passos

1. A integração MCP real depende do venv/uv do repo James; se esse ambiente mudar, o fallback local read-only entra.
2. O MCP atual retorna 15 tasks por filtro tenant; para visão histórica completa, avaliar se o contrato James deve aceitar `tenant=None/all` de forma read-only em missão própria.
3. Manter `main` fora de escopo; reconciliação definitiva deve ser missão separada.
4. Próxima fase pode consolidar métricas por módulo e conexão com policy R0–R5, ainda sem execução.

[FIM]
