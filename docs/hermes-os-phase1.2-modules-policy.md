# Hermes OS Fase 1.2 — Módulos + Política de Autonomia

## Resultado

- Runtime James alterado: **não**
- Autonomia real alterada: **não**
- Copilot alterado: **não**
- Efeitos reais executados: **não**
- MCP James: **read-only real quando disponível**
- Kanban: **read-only no board james-despachante**

## Dashboard textual

- Estado geral: `degraded`
- Resumo executivo: James supervision: 26 modules mapped; 13 healthy; 3 degraded; 8 critical/guarded high-risk; max autonomy remains R1 dry-run.
- critical_modules: `campaign, whatsapp_provider, billing_pix, campaign_center, campaign_engine, messaging_gateway, whatsapp_baileys_provider, evolution_provider`
- degraded_modules: `workspace_mission_control, mcp_readonly, mcp_ops_gatekeeper`
- watchers_with_problem: `none`
- workers_with_problem: `worker_jobs`
- containers_with_problem: `james-atendimento-worker-baileys`
- queues_growing: `none`
- missing_dependencies: `HOST_Windows_API_Interna_Daypag_readonly, Santander_HOST_API_boundary, Telegram_employee_channel, host_loopback_network`
- attention_now: `workspace_mission_control, mcp_readonly, mcp_ops_gatekeeper, campaign, whatsapp_provider, billing_pix, campaign_center, campaign_engine, messaging_gateway, whatsapp_baileys_provider, evolution_provider, worker_jobs`
- can_wait: `core, adapter_api_host_boundary, atendimento, employee_telegram, mcp, infra_ops, memory_policy, ocr_nf, atendimento_api, atendimento_cockpit, employee_telegram_gateway, ocr_nf_worker`

## Benchmark

```json
{
  "elapsed_seconds": 24.166,
  "cycles": 10,
  "module_count": 26,
  "healthy_count": 13,
  "degraded_count": 3,
  "critical_count": 8,
  "containers_problem_count": 1,
  "max_autonomy_without_ugo": "R1",
  "real_side_effects_allowed": false
}
```

## 10 cenários

| # | Objetivo | Snapshot | Review | Risco | Módulos | Healthy | Degraded | Critical | Exige aprovação | Efeito real |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | estado geral do James | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 2 | estado por módulo | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 3 | módulos críticos | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 4 | módulos degradados | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 5 | watchers com problema | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 6 | workers com problema | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 7 | containers com problema | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 8 | filas crescendo | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 9 | dependências ausentes | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |
| 10 | ações que exigem aprovação | degraded | attention | R1 | 26 | 13 | 3 | 8 | 25 | false |

## Mapa completo dos módulos

| Módulo | Manager | Health | Status | Risco | Conf. | Containers | Workers | Watchers | Capabilities | Autonomia |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| core | james.core.director | healthy | ok | R2 | 0.88 | 1/1 | 0 | 5 | 5 | R1 |
| adapter_api_host_boundary | james.hostapis.manager | healthy | ok | R3 | 0.88 | 1/1 | 0 | 3 | 3 | R1 |
| atendimento | james.atendimento.manager | healthy | ok | R2 | 0.88 | 2/2 | 1 | 1 | 3 | R1 |
| campaign | james.campaign.manager | guarded | approval_required | R5 | 0.84 | 1/2 | 0 | 1 | 3 | R1 |
| whatsapp_provider | james.provider.whatsapp.manager | guarded | approval_required | R5 | 0.84 | 2/3 | 2 | 2 | 2 | R1 |
| employee_telegram | james.telegram.manager | healthy | ok | R2 | 0.88 | 1/1 | 0 | 1 | 2 | R1 |
| billing_pix | james.hostapis.manager | guarded | approval_required | R5 | 0.84 | 1/1 | 1 | 3 | 3 | R1 |
| mcp | james.mcp.manager | healthy | ok | R2 | 0.88 | 0/0 | 0 | 1 | 3 | R1 |
| infra_ops | james.infra.manager | guarded | watch | R4 | 0.84 | 1/1 | 0 | 3 | 4 | R1 |
| workspace_mission_control | james.workspace.manager | degraded | attention | R2 | 0.72 | 0/1 | 0 | 1 | 2 | R1 |
| memory_policy | james.memory.manager | healthy | ok | R1 | 0.88 | 0/0 | 0 | 2 | 3 | R1 |
| ocr_nf | james.core.director | healthy | ok | R2 | 0.88 | 1/1 | 1 | 6 | 6 | R1 |
| atendimento_api | james.atendimento.manager | healthy | ok | R2 | 0.88 | 1/1 | 0 | 1 | 3 | R1 |
| atendimento_cockpit | james.atendimento.manager | healthy | ok | R2 | 0.88 | 1/1 | 0 | 1 | 3 | R1 |
| employee_telegram_gateway | james.telegram.manager | healthy | ok | R2 | 0.88 | 1/1 | 0 | 1 | 2 | R1 |
| ocr_nf_worker | james.core.director | healthy | ok | R2 | 0.88 | 1/1 | 1 | 5 | 6 | R1 |
| worker_jobs | james.infra.manager | healthy | ok | R3 | 0.88 | 1/1 | 0 | 3 | 4 | R1 |
| campaign_center | james.campaign.manager | guarded | approval_required | R5 | 0.84 | 1/2 | 0 | 1 | 3 | R1 |
| campaign_engine | james.campaign.manager | guarded | approval_required | R5 | 0.84 | 1/1 | 0 | 1 | 3 | R1 |
| messaging_gateway | james.provider.whatsapp.manager | guarded | approval_required | R5 | 0.84 | 1/1 | 1 | 2 | 2 | R1 |
| whatsapp_baileys_provider | james.provider.whatsapp.manager | guarded | approval_required | R5 | 0.84 | 1/2 | 1 | 2 | 2 | R1 |
| evolution_provider | james.provider.whatsapp.manager | guarded | approval_required | R5 | 0.84 | 3/3 | 0 | 2 | 2 | R1 |
| ingestion_enrichment_external_consult_mock | james.infra.manager | healthy | ok | R2 | 0.88 | 3/3 | 2 | 3 | 4 | R1 |
| ops_runtime | james.infra.manager | guarded | watch | R4 | 0.84 | 1/1 | 0 | 3 | 4 | R1 |
| mcp_readonly | james.mcp.manager | degraded | attention | R2 | 0.72 | 0/1 | 0 | 1 | 3 | R1 |
| mcp_ops_gatekeeper | james.mcp.manager | degraded | attention | R4 | 0.72 | 0/1 | 0 | 1 | 3 | R1 |

## Matriz R0-R5

### core
- R0 observar: core.status.read, core.db_summary.read
- R1 planejar: core.plan.dry_run, core.risk.review, core.kanban.scope_readonly
- R2 só com Ugo: core.local_code_or_config_change_with_ugo_approval, core.runtime_recovery_handoff_only
- R3 proibido: core.runtime_restart_or_rebuild_without_approval, core.db_migration_or_state_change, gate_preserved:REAL_SIDE_EFFECTS_ENABLED=false, gate_preserved:webhook_pix_real_requires_explicit_approval_and_review, gate_preserved:no_T29_unlock
- R4 integrações externas bloqueadas: core.external_provider_or_HOST_call, core.real_channel_interaction
- R5 efeitos reais proibidos: core.customer_contact_or_financial_effect, core.WhatsApp/Telegram/Pix/Santander real execution

### adapter_api_host_boundary
- R0 observar: adapter.status.read, billing.status.read
- R1 planejar: adapter_api_host_boundary.plan.dry_run, adapter_api_host_boundary.risk.review, adapter_api_host_boundary.kanban.scope_readonly
- R2 só com Ugo: adapter_api_host_boundary.local_code_or_config_change_with_ugo_approval, adapter_api_host_boundary.runtime_recovery_handoff_only
- R3 proibido: adapter_api_host_boundary.runtime_restart_or_rebuild_without_approval, adapter_api_host_boundary.db_migration_or_state_change, gate_preserved:HOST_REAL_CALLS_APPROVED must remain explicit, gate_preserved:HOST mutation forbidden from VM worker, gate_preserved:secrets outside git
- R4 integrações externas bloqueadas: adapter_api_host_boundary.external_provider_or_HOST_call, adapter_api_host_boundary.real_channel_interaction
- R5 efeitos reais proibidos: adapter_api_host_boundary.customer_contact_or_financial_effect, adapter_api_host_boundary.WhatsApp/Telegram/Pix/Santander real execution

### atendimento
- R0 observar: atendimento.status.read
- R1 planejar: atendimento.plan.dry_run, atendimento.risk.review, atendimento.kanban.scope_readonly
- R2 só com Ugo: atendimento.local_code_or_config_change_with_ugo_approval, atendimento.runtime_recovery_handoff_only
- R3 proibido: atendimento.runtime_restart_or_rebuild_without_approval, atendimento.db_migration_or_state_change
- R4 integrações externas bloqueadas: atendimento.external_provider_or_HOST_call, atendimento.real_channel_interaction
- R5 efeitos reais proibidos: atendimento.customer_contact_or_financial_effect, atendimento.WhatsApp/Telegram/Pix/Santander real execution

### campaign
- R0 observar: campaign.status.read
- R1 planejar: campaign.plan.dry_run, campaign.risk.review, campaign.kanban.scope_readonly
- R2 só com Ugo: campaign.local_code_or_config_change_with_ugo_approval, campaign.runtime_recovery_handoff_only
- R3 proibido: campaign.runtime_restart_or_rebuild_without_approval, campaign.db_migration_or_state_change
- R4 integrações externas bloqueadas: campaign.external_provider_or_HOST_call, campaign.real_channel_interaction
- R5 efeitos reais proibidos: campaign.customer_contact_or_financial_effect, campaign.WhatsApp/Telegram/Pix/Santander real execution

### whatsapp_provider
- R0 observar: whatsapp.provider.status.read
- R1 planejar: whatsapp_provider.plan.dry_run, whatsapp_provider.risk.review, whatsapp_provider.kanban.scope_readonly
- R2 só com Ugo: whatsapp_provider.local_code_or_config_change_with_ugo_approval, whatsapp_provider.runtime_recovery_handoff_only
- R3 proibido: whatsapp_provider.runtime_restart_or_rebuild_without_approval, whatsapp_provider.db_migration_or_state_change
- R4 integrações externas bloqueadas: whatsapp_provider.external_provider_or_HOST_call, whatsapp_provider.real_channel_interaction
- R5 efeitos reais proibidos: whatsapp_provider.customer_contact_or_financial_effect, whatsapp_provider.WhatsApp/Telegram/Pix/Santander real execution

### employee_telegram
- R0 observar: telegram.status.read
- R1 planejar: employee_telegram.plan.dry_run, employee_telegram.risk.review, employee_telegram.kanban.scope_readonly
- R2 só com Ugo: employee_telegram.local_code_or_config_change_with_ugo_approval, employee_telegram.runtime_recovery_handoff_only
- R3 proibido: employee_telegram.runtime_restart_or_rebuild_without_approval, employee_telegram.db_migration_or_state_change
- R4 integrações externas bloqueadas: employee_telegram.external_provider_or_HOST_call, employee_telegram.real_channel_interaction
- R5 efeitos reais proibidos: employee_telegram.customer_contact_or_financial_effect, employee_telegram.WhatsApp/Telegram/Pix/Santander real execution

### billing_pix
- R0 observar: adapter.status.read, billing.status.read
- R1 planejar: billing_pix.plan.dry_run, billing_pix.risk.review, billing_pix.kanban.scope_readonly
- R2 só com Ugo: billing_pix.local_code_or_config_change_with_ugo_approval, billing_pix.runtime_recovery_handoff_only
- R3 proibido: billing_pix.runtime_restart_or_rebuild_without_approval, billing_pix.db_migration_or_state_change, gate_preserved:PIX_MODE=sandbox, gate_preserved:Santander/Pix real blocked, gate_preserved:explicit_approval_required_for_R5
- R4 integrações externas bloqueadas: billing_pix.external_provider_or_HOST_call, billing_pix.real_channel_interaction
- R5 efeitos reais proibidos: billing_pix.customer_contact_or_financial_effect, billing_pix.WhatsApp/Telegram/Pix/Santander real execution

### mcp
- R0 observar: mcp.registry.read, mcp.health.read
- R1 planejar: mcp.plan.dry_run, mcp.risk.review, mcp.kanban.scope_readonly
- R2 só com Ugo: mcp.local_code_or_config_change_with_ugo_approval, mcp.runtime_recovery_handoff_only
- R3 proibido: mcp.runtime_restart_or_rebuild_without_approval, mcp.db_migration_or_state_change
- R4 integrações externas bloqueadas: mcp.external_provider_or_HOST_call, mcp.real_channel_interaction
- R5 efeitos reais proibidos: mcp.customer_contact_or_financial_effect, mcp.WhatsApp/Telegram/Pix/Santander real execution

### infra_ops
- R0 observar: infra.inventory.read, infra.health.read, ocr_nf.status.read
- R1 planejar: infra_ops.plan.dry_run, infra_ops.risk.review, infra_ops.kanban.scope_readonly
- R2 só com Ugo: infra_ops.local_code_or_config_change_with_ugo_approval, infra_ops.runtime_recovery_handoff_only
- R3 proibido: infra_ops.runtime_restart_or_rebuild_without_approval, infra_ops.db_migration_or_state_change
- R4 integrações externas bloqueadas: infra_ops.external_provider_or_HOST_call, infra_ops.real_channel_interaction
- R5 efeitos reais proibidos: infra_ops.customer_contact_or_financial_effect, infra_ops.WhatsApp/Telegram/Pix/Santander real execution

### workspace_mission_control
- R0 observar: workspace.status.read
- R1 planejar: workspace_mission_control.plan.dry_run, workspace_mission_control.risk.review, workspace_mission_control.kanban.scope_readonly
- R2 só com Ugo: workspace_mission_control.local_code_or_config_change_with_ugo_approval, workspace_mission_control.runtime_recovery_handoff_only
- R3 proibido: workspace_mission_control.runtime_restart_or_rebuild_without_approval, workspace_mission_control.db_migration_or_state_change, gate_preserved:local_only, gate_preserved:not_a_parallel_James_worker_ui, gate_preserved:no_update_or_runtime_mutation_from_experimental_UI
- R4 integrações externas bloqueadas: workspace_mission_control.external_provider_or_HOST_call, workspace_mission_control.real_channel_interaction
- R5 efeitos reais proibidos: workspace_mission_control.customer_contact_or_financial_effect, workspace_mission_control.WhatsApp/Telegram/Pix/Santander real execution

### memory_policy
- R0 observar: memory_policy.registry.read, memory_policy.health.read
- R1 planejar: memory_policy.plan.dry_run, memory_policy.risk.review, memory_policy.kanban.scope_readonly
- R2 só com Ugo: memory_policy.local_code_or_config_change_with_ugo_approval, memory_policy.runtime_recovery_handoff_only
- R3 proibido: memory_policy.runtime_restart_or_rebuild_without_approval, memory_policy.db_migration_or_state_change
- R4 integrações externas bloqueadas: memory_policy.external_provider_or_HOST_call, memory_policy.real_channel_interaction
- R5 efeitos reais proibidos: memory_policy.customer_contact_or_financial_effect, memory_policy.WhatsApp/Telegram/Pix/Santander real execution

### ocr_nf
- R0 observar: core.status.read, core.db_summary.read, ocr_nf.status.read
- R1 planejar: ocr_nf.plan.dry_run, ocr_nf.risk.review, ocr_nf.kanban.scope_readonly
- R2 só com Ugo: ocr_nf.local_code_or_config_change_with_ugo_approval, ocr_nf.runtime_recovery_handoff_only
- R3 proibido: ocr_nf.runtime_restart_or_rebuild_without_approval, ocr_nf.db_migration_or_state_change
- R4 integrações externas bloqueadas: ocr_nf.external_provider_or_HOST_call, ocr_nf.real_channel_interaction
- R5 efeitos reais proibidos: ocr_nf.customer_contact_or_financial_effect, ocr_nf.WhatsApp/Telegram/Pix/Santander real execution

### atendimento_api
- R0 observar: atendimento.status.read
- R1 planejar: atendimento_api.plan.dry_run, atendimento_api.risk.review, atendimento_api.kanban.scope_readonly
- R2 só com Ugo: atendimento_api.local_code_or_config_change_with_ugo_approval, atendimento_api.runtime_recovery_handoff_only
- R3 proibido: atendimento_api.runtime_restart_or_rebuild_without_approval, atendimento_api.db_migration_or_state_change, gate_preserved:JAMES_ATENDIMENTO_DRAFT_ONLY=true, gate_preserved:JAMES_ATENDIMENTO_SEND_ENABLED=false, gate_preserved:JAMES_ATENDIMENTO_OUTBOUND_KILL_SWITCH=true, gate_preserved:human_approval_required_for_outbound
- R4 integrações externas bloqueadas: atendimento_api.external_provider_or_HOST_call, atendimento_api.real_channel_interaction
- R5 efeitos reais proibidos: atendimento_api.customer_contact_or_financial_effect, atendimento_api.WhatsApp/Telegram/Pix/Santander real execution

### atendimento_cockpit
- R0 observar: atendimento.status.read
- R1 planejar: atendimento_cockpit.plan.dry_run, atendimento_cockpit.risk.review, atendimento_cockpit.kanban.scope_readonly
- R2 só com Ugo: atendimento_cockpit.local_code_or_config_change_with_ugo_approval, atendimento_cockpit.runtime_recovery_handoff_only
- R3 proibido: atendimento_cockpit.runtime_restart_or_rebuild_without_approval, atendimento_cockpit.db_migration_or_state_change, gate_preserved:UI apenas para operacao assistida, gate_preserved:no_auto_send_from_frontend, gate_preserved:no_parallel_worker_ui
- R4 integrações externas bloqueadas: atendimento_cockpit.external_provider_or_HOST_call, atendimento_cockpit.real_channel_interaction
- R5 efeitos reais proibidos: atendimento_cockpit.customer_contact_or_financial_effect, atendimento_cockpit.WhatsApp/Telegram/Pix/Santander real execution

### employee_telegram_gateway
- R0 observar: telegram.status.read
- R1 planejar: employee_telegram_gateway.plan.dry_run, employee_telegram_gateway.risk.review, employee_telegram_gateway.kanban.scope_readonly
- R2 só com Ugo: employee_telegram_gateway.local_code_or_config_change_with_ugo_approval, employee_telegram_gateway.runtime_recovery_handoff_only
- R3 proibido: employee_telegram_gateway.runtime_restart_or_rebuild_without_approval, employee_telegram_gateway.db_migration_or_state_change, gate_preserved:JAMES_EMPLOYEE_TELEGRAM_SEND_ENABLED=false unless explicitly approved, gate_preserved:rate_limit_required_before_autonomy_noise, gate_preserved:Telegram is internal Ugo channel not client channel
- R4 integrações externas bloqueadas: employee_telegram_gateway.external_provider_or_HOST_call, employee_telegram_gateway.real_channel_interaction
- R5 efeitos reais proibidos: employee_telegram_gateway.customer_contact_or_financial_effect, employee_telegram_gateway.WhatsApp/Telegram/Pix/Santander real execution

### ocr_nf_worker
- R0 observar: core.status.read, core.db_summary.read, ocr_nf.status.read
- R1 planejar: ocr_nf_worker.plan.dry_run, ocr_nf_worker.risk.review, ocr_nf_worker.kanban.scope_readonly
- R2 só com Ugo: ocr_nf_worker.local_code_or_config_change_with_ugo_approval, ocr_nf_worker.runtime_recovery_handoff_only
- R3 proibido: ocr_nf_worker.runtime_restart_or_rebuild_without_approval, ocr_nf_worker.db_migration_or_state_change, gate_preserved:no_dedicated_ui, gate_preserved:called_by_core_or_employee_gateway_only, gate_preserved:input_roots_allowlisted, gate_preserved:no_external_network
- R4 integrações externas bloqueadas: ocr_nf_worker.external_provider_or_HOST_call, ocr_nf_worker.real_channel_interaction
- R5 efeitos reais proibidos: ocr_nf_worker.customer_contact_or_financial_effect, ocr_nf_worker.WhatsApp/Telegram/Pix/Santander real execution

### worker_jobs
- R0 observar: infra.inventory.read, infra.health.read, ocr_nf.status.read
- R1 planejar: worker_jobs.plan.dry_run, worker_jobs.risk.review, worker_jobs.kanban.scope_readonly
- R2 só com Ugo: worker_jobs.local_code_or_config_change_with_ugo_approval, worker_jobs.runtime_recovery_handoff_only
- R3 proibido: worker_jobs.runtime_restart_or_rebuild_without_approval, worker_jobs.db_migration_or_state_change, gate_preserved:OPERATIONAL_PAUSE=true by default, gate_preserved:human_gate_required_before_simulated_jobs, gate_preserved:no_real_side_effects
- R4 integrações externas bloqueadas: worker_jobs.external_provider_or_HOST_call, worker_jobs.real_channel_interaction
- R5 efeitos reais proibidos: worker_jobs.customer_contact_or_financial_effect, worker_jobs.WhatsApp/Telegram/Pix/Santander real execution

### campaign_center
- R0 observar: campaign.status.read
- R1 planejar: campaign_center.plan.dry_run, campaign_center.risk.review, campaign_center.kanban.scope_readonly
- R2 só com Ugo: campaign_center.local_code_or_config_change_with_ugo_approval, campaign_center.runtime_recovery_handoff_only
- R3 proibido: campaign_center.runtime_restart_or_rebuild_without_approval, campaign_center.db_migration_or_state_change, gate_preserved:CAMP-7 remains blocked, gate_preserved:T29 remains blocked, gate_preserved:campaign_send_enabled=false, gate_preserved:dry_run_only_until_review_HJ_MAP_7, gate_preserved:real_campaign_requires_explicit_Ugo_approval
- R4 integrações externas bloqueadas: campaign_center.external_provider_or_HOST_call, campaign_center.real_channel_interaction
- R5 efeitos reais proibidos: campaign_center.customer_contact_or_financial_effect, campaign_center.WhatsApp/Telegram/Pix/Santander real execution

### campaign_engine
- R0 observar: campaign.status.read
- R1 planejar: campaign_engine.plan.dry_run, campaign_engine.risk.review, campaign_engine.kanban.scope_readonly
- R2 só com Ugo: campaign_engine.local_code_or_config_change_with_ugo_approval, campaign_engine.runtime_recovery_handoff_only
- R3 proibido: campaign_engine.runtime_restart_or_rebuild_without_approval, campaign_engine.db_migration_or_state_change, gate_preserved:CAMPAIGN_SEND_ENABLED=false, gate_preserved:CAMP-7 blocked, gate_preserved:no_real_whatsapp
- R4 integrações externas bloqueadas: campaign_engine.external_provider_or_HOST_call, campaign_engine.real_channel_interaction
- R5 efeitos reais proibidos: campaign_engine.customer_contact_or_financial_effect, campaign_engine.WhatsApp/Telegram/Pix/Santander real execution

### messaging_gateway
- R0 observar: whatsapp.provider.status.read
- R1 planejar: messaging_gateway.plan.dry_run, messaging_gateway.risk.review, messaging_gateway.kanban.scope_readonly
- R2 só com Ugo: messaging_gateway.local_code_or_config_change_with_ugo_approval, messaging_gateway.runtime_recovery_handoff_only
- R3 proibido: messaging_gateway.runtime_restart_or_rebuild_without_approval, messaging_gateway.db_migration_or_state_change, gate_preserved:MESSAGING_MODE=sandbox, gate_preserved:JAMES_WHATSAPP_SEND_ENABLED=false, gate_preserved:allowlist local-sandbox-only
- R4 integrações externas bloqueadas: messaging_gateway.external_provider_or_HOST_call, messaging_gateway.real_channel_interaction
- R5 efeitos reais proibidos: messaging_gateway.customer_contact_or_financial_effect, messaging_gateway.WhatsApp/Telegram/Pix/Santander real execution

### whatsapp_baileys_provider
- R0 observar: whatsapp.provider.status.read
- R1 planejar: whatsapp_baileys_provider.plan.dry_run, whatsapp_baileys_provider.risk.review, whatsapp_baileys_provider.kanban.scope_readonly
- R2 só com Ugo: whatsapp_baileys_provider.local_code_or_config_change_with_ugo_approval, whatsapp_baileys_provider.runtime_recovery_handoff_only
- R3 proibido: whatsapp_baileys_provider.runtime_restart_or_rebuild_without_approval, whatsapp_baileys_provider.db_migration_or_state_change, gate_preserved:JAMES_ATENDIMENTO_BAILEYS_CONNECT=false unless approved, gate_preserved:expected_pre_T30_state=exited_restart_no, gate_preserved:JAMES_WHATSAPP_SEND_ENABLED=false, gate_preserved:pairing_requires_approval_ref, gate_preserved:no_client_real_send
- R4 integrações externas bloqueadas: whatsapp_baileys_provider.external_provider_or_HOST_call, whatsapp_baileys_provider.real_channel_interaction
- R5 efeitos reais proibidos: whatsapp_baileys_provider.customer_contact_or_financial_effect, whatsapp_baileys_provider.WhatsApp/Telegram/Pix/Santander real execution

### evolution_provider
- R0 observar: whatsapp.provider.status.read
- R1 planejar: evolution_provider.plan.dry_run, evolution_provider.risk.review, evolution_provider.kanban.scope_readonly
- R2 só com Ugo: evolution_provider.local_code_or_config_change_with_ugo_approval, evolution_provider.runtime_recovery_handoff_only
- R3 proibido: evolution_provider.runtime_restart_or_rebuild_without_approval, evolution_provider.db_migration_or_state_change, gate_preserved:outbound_real_blocked_by_James_side, gate_preserved:EVOLUTION credential outside git, gate_preserved:no_real_client_whatsapp_without_approval
- R4 integrações externas bloqueadas: evolution_provider.external_provider_or_HOST_call, evolution_provider.real_channel_interaction
- R5 efeitos reais proibidos: evolution_provider.customer_contact_or_financial_effect, evolution_provider.WhatsApp/Telegram/Pix/Santander real execution

### ingestion_enrichment_external_consult_mock
- R0 observar: infra.inventory.read, infra.health.read, ocr_nf.status.read
- R1 planejar: ingestion_enrichment_external_consult_mock.plan.dry_run, ingestion_enrichment_external_consult_mock.risk.review, ingestion_enrichment_external_consult_mock.kanban.scope_readonly
- R2 só com Ugo: ingestion_enrichment_external_consult_mock.local_code_or_config_change_with_ugo_approval, ingestion_enrichment_external_consult_mock.runtime_recovery_handoff_only
- R3 proibido: ingestion_enrichment_external_consult_mock.runtime_restart_or_rebuild_without_approval, ingestion_enrichment_external_consult_mock.db_migration_or_state_change, gate_preserved:MOCK_MODE=true, gate_preserved:REAL_ENRICHMENT_ENABLED=false, gate_preserved:EXTERNAL_NETWORK_ENABLED=false
- R4 integrações externas bloqueadas: ingestion_enrichment_external_consult_mock.external_provider_or_HOST_call, ingestion_enrichment_external_consult_mock.real_channel_interaction
- R5 efeitos reais proibidos: ingestion_enrichment_external_consult_mock.customer_contact_or_financial_effect, ingestion_enrichment_external_consult_mock.WhatsApp/Telegram/Pix/Santander real execution

### ops_runtime
- R0 observar: infra.inventory.read, infra.health.read, ocr_nf.status.read
- R1 planejar: ops_runtime.plan.dry_run, ops_runtime.risk.review, ops_runtime.kanban.scope_readonly
- R2 só com Ugo: ops_runtime.local_code_or_config_change_with_ugo_approval, ops_runtime.runtime_recovery_handoff_only
- R3 proibido: ops_runtime.runtime_restart_or_rebuild_without_approval, ops_runtime.db_migration_or_state_change, gate_preserved:OPS_JOBS_ENABLED=false, gate_preserved:restart_deploy_requires_review_and_ops_exec, gate_preserved:no_generic_shell_as_autonomous_tool
- R4 integrações externas bloqueadas: ops_runtime.external_provider_or_HOST_call, ops_runtime.real_channel_interaction
- R5 efeitos reais proibidos: ops_runtime.customer_contact_or_financial_effect, ops_runtime.WhatsApp/Telegram/Pix/Santander real execution

### mcp_readonly
- R0 observar: mcp_readonly.registry.read, mcp_readonly.health.read
- R1 planejar: mcp_readonly.plan.dry_run, mcp_readonly.risk.review, mcp_readonly.kanban.scope_readonly
- R2 só com Ugo: mcp_readonly.local_code_or_config_change_with_ugo_approval, mcp_readonly.runtime_recovery_handoff_only
- R3 proibido: mcp_readonly.runtime_restart_or_rebuild_without_approval, mcp_readonly.db_migration_or_state_change, gate_preserved:read_only_only, gate_preserved:no_generic_shell, gate_preserved:no_secrets
- R4 integrações externas bloqueadas: mcp_readonly.external_provider_or_HOST_call, mcp_readonly.real_channel_interaction
- R5 efeitos reais proibidos: mcp_readonly.customer_contact_or_financial_effect, mcp_readonly.WhatsApp/Telegram/Pix/Santander real execution

### mcp_ops_gatekeeper
- R0 observar: mcp_ops_gatekeeper.registry.read, mcp_ops_gatekeeper.health.read
- R1 planejar: mcp_ops_gatekeeper.plan.dry_run, mcp_ops_gatekeeper.risk.review, mcp_ops_gatekeeper.kanban.scope_readonly
- R2 só com Ugo: mcp_ops_gatekeeper.local_code_or_config_change_with_ugo_approval, mcp_ops_gatekeeper.runtime_recovery_handoff_only
- R3 proibido: mcp_ops_gatekeeper.runtime_restart_or_rebuild_without_approval, mcp_ops_gatekeeper.db_migration_or_state_change, gate_preserved:gatekeeper_required_for_R2_plus, gate_preserved:ledger_required, gate_preserved:no_T29_CAMP7_unlock, gate_preserved:no_shell_docker_git_write_anywhere_generic
- R4 integrações externas bloqueadas: mcp_ops_gatekeeper.external_provider_or_HOST_call, mcp_ops_gatekeeper.real_channel_interaction
- R5 efeitos reais proibidos: mcp_ops_gatekeeper.customer_contact_or_financial_effect, mcp_ops_gatekeeper.WhatsApp/Telegram/Pix/Santander real execution

## Auditoria

```json
{
  "read_only": true,
  "runtime_mutated": false,
  "autonomy_changed": false,
  "copilot_changed": false,
  "main_changed": false,
  "real_side_effects_executed": false,
  "mcp_real": true,
  "kanban_target": {
    "board_slug": "james-despachante",
    "tenant": "james-despachante",
    "db_path": "/home/ugo/.hermes/kanban/boards/james-despachante/kanban.db",
    "source": "board_slug",
    "task_count": 526,
    "status_counts": {
      "archived": 55,
      "blocked": 2,
      "done": 463,
      "todo": 6
    },
    "tenant_counts": {
      "None": 511,
      "james-despachante": 15
    }
  }
}
```

## Próximos passos

- Separar fase comportamental sem alterar gates atuais.
- Adicionar sondas read-only especificas por fila quando contratos existirem.
- Criar respostas operacionais curtas a partir do dashboard consolidado.
