# Hermes OS Kernel — Fase 0

Status: fundação inicial, reversível, read-only + planejamento + dry-run.

## Não objetivos desta fase

- Não alterar runtime do James.
- Não alterar Copilot.
- Não alterar autonomia real.
- Não habilitar efeitos reais.
- Não instalar LangGraph, Temporal, Letta, Mem0 ou Graphiti.
- Não executar ações mutativas no James.

## Missão

Criar a primeira fundação do Hermes OS como camada de governança sobre James. O James é tratado como sistema operacional/ERP modular do Despachante Itamaraty, não como um agente simples.

## Componentes

```text
Ugo
 |
 v
Hermes OS Kernel Phase 0
 |
 +-- Planner      -> transforma objetivo em plano, dependências, riscos e critérios
 +-- Observer     -> lê Knowledge Fabric e James read-only
 +-- Supervisor   -> compara plano/objetivo com estado real
 +-- Executor     -> dry-run; mapeia chamadas sem executá-las
 +-- Learner      -> recomenda aprendizados/memórias/skills sem escrever automaticamente
 +-- Policy/Gates -> decide autonomia, riscos, aprovação exigida
 +-- Audit        -> registra objetivo, fontes, plano, risco, confiança e aprovação
 |
 v
Knowledge Fabric -> Providers
 |
 v
James read-only surfaces: health, MCP read-only, registries, logs sanitizados, bancos agregados
```

## Contratos iniciais

| Componente | Contrato | Efeito real |
|---|---|---:|
| Planner | `planner.plan(objective, snapshot=None, review=None)` | não |
| Observer | `observer.snapshot(objective)` | não; read-only |
| Supervisor | `supervisor.review(objective, snapshot)` | não |
| Executor | `executor.dry_run(plan)` | não; simulado |
| Learner | `learner.reflect(objective, review, dry_run)` | não escreve automaticamente |
| Policy | `policy.check(action)` | não; decisão/gate |
| Audit | `audit.record(plan, review, dry_run, reflection, path=None)` | só grava trilha se `path` explícito |

## Policy/Gates

A Fase 0 preserva os gates existentes. Exigem aprovação do Ugo e não são executados pela Fase 0:

- WhatsApp real.
- Telegram real fora do controle aprovado.
- PIX/Santander.
- HOST/API-interna mutativo.
- Cloudflare/nginx/SQL Server/APIs do HOST.
- Restart/rebuild/deploy/migration/delete/update/write.
- Qualquer ação R2+.

## Knowledge Fabric

A Knowledge Fabric é a fonte oficial de conhecimento do Hermes. O Observer consulta a Fabric para contexto do objetivo antes/depois de probes read-only. O Kernel não lê diretamente Holographic/session DB/canonical indexes.

## James

James é consultado apenas por canais read-only nesta fase:

- endpoints locais de health/status quando permitidos;
- inventário `docker ps` sem mutação;
- MCP read-only no futuro;
- relatórios, registries, docs e bancos agregados/sanitizados quando explicitamente usados.

## Ciclo demonstrativo

Objetivo exemplo:

```text
avaliar saúde operacional atual do James
```

Fluxo:

```text
Observer.snapshot()
  -> Knowledge Fabric search
  -> James health endpoints read-only
  -> docker ps read-only
Supervisor.review()
  -> classifica on_track/attention/blocked
Planner.plan()
  -> gera plano de observação, revisão, dry-run e auditoria
Executor.dry_run()
  -> mapeia chamadas pretendidas sem mutar James
Learner.reflect()
  -> recomenda aprendizados sem escrita automática
Audit.record()
  -> gera trilha de objetivo/fontes/plano/risco/confiança/aprovação
```

## Artefatos

Código:

```text
agent/hermes_os_kernel/
```

Teste:

```text
tests/agent/test_hermes_os_kernel_phase0.py
```

Demo:

```bash
python3 -m agent.hermes_os_kernel.demo \
  --objective "avaliar saúde operacional atual do James" \
  --audit-path /tmp/hermes-os-kernel-phase0-audit.json
```

## Próximos passos recomendados

1. Rodar múltiplos ciclos read-only e comparar estabilidade das decisões.
2. Definir schemas versionados para eventos de Planner/Observer/Supervisor/Executor/Learner.
3. Integrar MCP read-only do James como fonte formal do Observer.
4. Criar policy matrix por nível de autonomia.
5. Só depois criar cards de execução assistida com aprovação explícita.
