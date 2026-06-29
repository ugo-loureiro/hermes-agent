# Hermes OS Executive Intelligence — Fase 1A — Opportunity Engine

## Resultado

- Arquitetura congelada preservada: **sim**
- Mudança estrutural proposta: **não**
- Detecção apenas: **sim**
- Priorização/decisão: **não**
- Efeitos reais executados: **não**
- Runtime James alterado: **não**

## Benchmark

```json
{
  "elapsed_seconds": 2.509,
  "live_opportunities": 5,
  "live_capability_gaps": 0,
  "scenarios": 6
}
```

## Oportunidades detectadas com evidência atual

| # | tipo | título | origem | componente | capacidade | política | aprovação | confiança |
|---|---|---|---|---|---|---|---|---|
| 1 | module_degraded | Módulo degradado: workspace_mission_control | module_supervision.degraded_modules | workspace_mission_control | workspace.graph.propose | R1 | False | 0.72 |
| 2 | module_degraded | Módulo degradado: mcp_readonly | module_supervision.degraded_modules | mcp_readonly | gatekeeper.check | R1 | False | 0.72 |
| 3 | module_degraded | Módulo degradado: mcp_ops_gatekeeper | module_supervision.degraded_modules | mcp_ops_gatekeeper | gatekeeper.check | R1 | False | 0.72 |
| 4 | container_degraded | Container com problema: james-atendimento-worker-baileys | module_supervision.containers_with_problem | whatsapp_baileys_provider | whatsapp.provider.status.read | R2 | True | 0.84 |
| 5 | worker_stopped | Worker parado/sem evidência ativa: worker_jobs | module_supervision.workers_with_problem | worker_jobs | infra.health.read | R2 | True | 0.88 |

## Capability Gaps detectados com evidência atual

Nenhum Capability Gap detectado com a evidência atual.

## Cenários de teste/benchmark

| scenario | opportunity_count | gap_count | opportunity_types | gap_capabilities | real_side_effects_executed |
|---|---|---|---|---|---|
| inicio_mes_licenciamento | 6 | 0 | ['seasonal_campaign', 'module_degraded', 'module_degraded', 'module_degraded', 'container_degraded', 'worker_stopped'] | [] | False |
| modulo_degradado | 5 | 0 | ['module_degraded', 'module_degraded', 'module_degraded', 'container_degraded', 'worker_stopped'] | [] | False |
| fila_crescente | 5 | 1 | ['module_degraded', 'module_degraded', 'module_degraded', 'container_degraded', 'worker_stopped'] | ['queue.depth.read'] | False |
| worker_parado | 5 | 0 | ['module_degraded', 'module_degraded', 'module_degraded', 'container_degraded', 'worker_stopped'] | [] | False |
| campanha_disponivel_financeira | 6 | 0 | ['module_degraded', 'module_degraded', 'module_degraded', 'container_degraded', 'worker_stopped', 'financial_existing_data'] | [] | False |
| nenhuma_oportunidade | 0 | 0 | [] | [] | False |

## Contrato de oportunidade completa

Cada oportunidade emitida contém: título, resumo, origem, evidência, impacto, urgência, esforço, risco, confiança, capacidade disponível, política R0–R5, ação recomendada, necessidade de aprovação, componente observado e disponibilidade de ferramenta.

## Recomendações para Prioritization Engine

- Prioritization Engine deve consumir somente oportunidades completas do Opportunity Engine.
- Prioritization Engine não deve executar; apenas ordenar por regras explícitas e evidência.
- Capability Gaps devem permanecer fora de execução até existir capability/tool/policy suficiente.
