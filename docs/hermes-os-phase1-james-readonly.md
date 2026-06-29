# Hermes OS — Fase 1 — Integração read-only com James MCP + Kanban

Data: 2026-06-28/29
Branch: `hermes-os-kernel-phase0`

## Escopo

Integrar o Hermes OS Kernel com superfícies read-only reais/declaradas do James para dar visão operacional ao Observer/Supervisor sem executar ações.

## Guardrails preservados

- Não alterou runtime do James.
- Não alterou Copilot.
- Não alterou autonomia real.
- Não executou ação mutativa.
- Não habilitou WhatsApp real.
- Não habilitou Telegram real.
- Não habilitou PIX/Santander.
- Não tocou HOST mutativo.
- Não instalou ferramentas.
- Não mexeu na `main`.
- Não fez rebase/merge/force-push.

## Arquivos criados/alterados

```text
agent/hermes_os_kernel/james_readonly.py
agent/hermes_os_kernel/observer.py
agent/hermes_os_kernel/supervisor.py
agent/hermes_os_kernel/planner.py
agent/hermes_os_kernel/executor.py
agent/hermes_os_kernel/audit.py
agent/hermes_os_kernel/contracts.py
agent/hermes_os_kernel/__init__.py
tests/agent/test_hermes_os_kernel_phase0.py
docs/hermes-os-phase1-james-readonly.md
```

## Superfícies James mapeadas

MCP/read-only tools esperadas:

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

Observação: nesta sessão o import direto do pacote MCP read-only do James ficou indisponível por dependência de transporte MCP (`mcp.server.fastmcp`) no ambiente Hermes. Como instalação era proibida, o adaptador usou fallback local read-only compatível com os mesmos nomes de tools: GET local, SQLite read-only, registries e inventário de artefatos. Isso preservou semântica read-only sem instalar nada.

Fontes usadas:

- Knowledge Fabric via `knowledge_call("search", ...)`.
- James local health/status endpoints via GET local.
- Registries:
  - `james_modules_registry.yaml`
  - `james_workers_registry.yaml`
  - `james_watchers_registry.yaml`
  - `james_capabilities_registry.yaml`
- Kanban SQLite em modo read-only.
- Runtime inventory declarativo do repo James.
- `docker ps` read-only como compatibilidade/inventário secundário.

## Ciclos read-only executados

Audit records:

```text
/home/ugo/.hermes/knowledge_fabric/reports/hermes_os_phase1_readonly/*_audit.json
/home/ugo/.hermes/knowledge_fabric/reports/hermes_os_phase1_readonly/summary.json
```

| Slug | Objetivo | Snapshot | Review | Saúde | Risco | Confiança | Transporte | Tools | Módulos | Containers | Kanban | Efeito real? |
|---|---|---|---|---|---|---:|---|---:|---:|---:|---:|---|
| visao_geral_james | visão geral do James | ok | on_track | ok | R1 | 0.86 | local_readonly_fallback | 10 | 26 | 11 | 0 | false |
| atendimento_monitorado | atendimento monitorado | ok | on_track | ok | R1 | 0.86 | local_readonly_fallback | 10 | 26 | 11 | 0 | false |
| workers_filas | workers/filas | ok | on_track | ok | R1 | 0.86 | local_readonly_fallback | 10 | 26 | 11 | 0 | false |
| campanhas_dry_run | campanhas dry-run | ok | on_track | ok | R1 | 0.86 | local_readonly_fallback | 10 | 26 | 11 | 0 | false |
| gates_efeitos_reais | gates e efeitos reais | ok | on_track | ok | R1 | 0.86 | local_readonly_fallback | 10 | 26 | 11 | 0 | false |

## Evoluções por componente

### JamesReadOnlyAdapter

Novo adaptador em `agent/hermes_os_kernel/james_readonly.py`:

- mapeia as 10 tools MCP read-only esperadas;
- tenta usar funções Python do pacote James MCP read-only quando disponíveis;
- usa fallback local read-only quando o transporte MCP não está importável;
- consolida health, módulos, workers, watchers, capabilities, Kanban, campanhas, atendimento, Employee Telegram e gates;
- sanitiza chaves/valores sensíveis;
- declara `mutative_methods_allowed=[]`.

### Observer

Agora produz `james_operational.operational_view` com:

- saúde geral;
- containers;
- módulos;
- workers;
- watchers;
- capabilities;
- atendimento;
- campanhas;
- Employee Telegram;
- Kanban read-only;
- riscos/gates;
- pendências detectadas.

### Supervisor

Agora analisa o snapshot operacional e retorna:

- status geral;
- riscos e bloqueios;
- inconsistências/pendências;
- áreas de atenção;
- evidências e confiança.

### Planner

Agora transforma achados read-only em plano sem execução:

- subtarefas;
- dependências;
- prioridade implícita por achados;
- critérios de sucesso;
- follow-ups read-only ou recomendações R2+ bloqueadas.

### Executor

Permanece dry-run:

- lista tools/APIs/MCP que seriam usadas;
- não invoca ações mutativas;
- anexa policy por ação;
- `real_side_effects_executed=false`.

### Learner

Permanece recomendativo:

- não escreve memória automaticamente.

### Audit

Agora registra também o `snapshot` completo no audit record além de objetivo, fontes, review, plano, dry-run, aprendizado, risco, confiança e aprovação.

## Validação

Executado:

```text
uv run --with pytest pytest tests/agent/test_hermes_os_kernel_phase0.py -q -o 'addopts='
PYTHONPATH=/home/ugo/.hermes:/home/ugo/.hermes/hermes-agent python3 -m compileall -q agent/hermes_os_kernel tests/agent/test_hermes_os_kernel_phase0.py
git diff --check
scan simples de secrets no novo módulo
scan de padrões mutativos no Kernel
```

Resultado desta rodada:

```text
6 passed in 0.66s
compileall OK
git diff --check OK
secrets/mutative HTTP method scan: 0 hits
```

## Estado James observado

`git -C /home/ugo/ops/james-2 status --short` mostrou somente alterações/untracked preexistentes em docs/reports T50F; esta missão não editou James.

`docker ps` read-only mostrou containers James/Evolution `Up/healthy`; nenhum restart/rebuild/start/stop foi executado.

## Riscos / limites

- O transporte MCP stdio real não foi iniciado/importado no Hermes porque instalar dependência era proibido. Foi usado fallback read-only compatível.
- Kanban read-only retornou 0 tasks para tenant `james-despachante` no snapshot atual.
- Próxima fase deve decidir se a integração passa a usar MCP client real do Hermes ou mantém fallback local até a camada MCP ser carregada na sessão.

## Próximos passos recomendados

1. Integrar MCP read-only real via toolset/config do Hermes, sem instalar nada ad hoc durante runtime.
2. Adicionar métricas específicas por módulo a partir dos registries do James.
3. Conectar Observer ao Kanban read-only com filtro por boards/camadas corretas.
4. Manter Executor dry-run até matriz R0–R5 ser promovida para policy operacional aprovada.
5. Tratar divergência da `main` em missão separada; não resolver agora.

[FIM]
