# Hermes OS Kernel — Hardening 0.1

Data: 2026-06-28/29

Escopo: consolidar a Fase 0 antes da próxima fase. Esta etapa revisou contratos, executou cinco ciclos read-only, gerou audit records, criou matriz preliminar R0–R5 e validou testes locais.

## Guardrails

- Runtime do James não alterado.
- Copilot não alterado.
- Autonomia real não alterada.
- Efeitos reais não habilitados.
- Ferramentas externas não instaladas.
- Nenhuma ação mutativa no James foi executada.

## Revisão dos contratos

Contratos revisados em `agent/hermes_os_kernel/`:

| Contrato | Arquivo | Resultado |
|---|---|---|
| `planner.plan()` | `planner.py` | plano read-only/dry-run com steps, riscos, fontes e critérios |
| `observer.snapshot()` | `observer.py` | Knowledge Fabric + health local + `docker ps` read-only |
| `supervisor.review()` | `supervisor.py` | compara snapshot com objetivo e classifica estado/risco |
| `executor.dry_run()` | `executor.py` | mapeia chamadas sem execução mutativa |
| `learner.reflect()` | `learner.py` | recomenda aprendizados sem escrever memória automaticamente |
| `policy.check()` | `policy.py` | preserva gates de alvo sensível, mutação, side effects e R2+ |
| `audit.record()` | `audit.py` | gera trilha com objetivo, fontes, plano, risco, confiança e aprovação |

Hardening adicional criado:

```text
agent/hermes_os_kernel/autonomy.py
```

## Cinco ciclos demonstrativos read-only

Audit records em:

```text
/home/ugo/.hermes/knowledge_fabric/reports/hermes_os_kernel_hardening_0_1/
```

| Slug | Objetivo | Snapshot | Review | Risco | Confiança | Aprovação? | Efeito real? |
|---|---|---|---|---|---:|---|---|
| james_health | avaliar saúde operacional atual do James | ok | on_track | R1 | 0.84 | False | False |
| atendimento_monitorado | avaliar atendimento monitorado | ok | on_track | R1 | 0.84 | False | False |
| workers_filas | avaliar workers e filas | ok | on_track | R1 | 0.84 | False | False |
| campanhas_dry_run | avaliar campanhas em dry-run | ok | on_track | R1 | 0.84 | False | False |
| riscos_gates | avaliar riscos/gates de efeitos reais | ok | on_track | R1 | 0.84 | False | False |

Fontes em todos os ciclos:

```text
Knowledge Fabric
James local health endpoints
docker ps
```

## Matriz preliminar de autonomia R0–R5

| Nível | Nome | Permitido sem Ugo | Requer Ugo | Proibido na Fase 0 |
|---|---|---|---|---|
| R0 | read-only observation | Knowledge Fabric query; local health GET; docker ps inventory; docs/registry reads | - | - |
| R1 | dry-run planning and simulation | planner output; supervisor recommendation; executor dry-run map; audit record write | turning dry-run into execution | mutating James runtime |
| R2 | assisted local change | - | repo edits beyond planning; Kanban state changes; service-specific diagnostics with side-effect risk | runtime change; config flip; service restart |
| R3 | controlled runtime operation | - | rebuild; restart; compose up; database migration; gateway operation | all R3 execution |
| R4 | external integration or customer-adjacent action | - | HOST/API-interna assisted lookup; Telegram real test; WhatsApp allowlist pilot | all R4 execution; customer contact |
| R5 | financial/production real side effect | - | PIX/Santander; WhatsApp customer send; HOST mutation; provider/auth/token changes | all R5 execution; secret changes; payments; customer campaigns |

## Decisão de hardening

Resultado: **PASS local**.

O Kernel permanece:

- reversível;
- modular;
- testado;
- auditável;
- sem efeito real;
- pronto para próxima fase de integração read-only com MCP e Kanban.

## Evidência de validação

Comandos executados ao final desta etapa:

```text
uv run --with pytest pytest tests/agent/test_hermes_os_kernel_phase0.py -q -o 'addopts='
python3 -m compileall -q agent/hermes_os_kernel tests/agent/test_hermes_os_kernel_phase0.py
git diff --check
scan de padrões API_KEY/TOKEN/PASSWORD/SECRET/.env/auth.json no novo módulo
```

## Próximo commit sugerido

Se Ugo aprovar versionar localmente:

```bash
git add agent/hermes_os_kernel \
  docs/hermes-os-kernel-phase0.md \
  docs/hermes-os-kernel-hardening-0.1.md \
  tests/agent/test_hermes_os_kernel_phase0.py
git commit -m "Add Hermes OS Kernel phase 0 foundation"
```

[FIM]
