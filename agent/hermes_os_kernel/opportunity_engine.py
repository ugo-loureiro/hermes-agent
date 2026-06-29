"""Executive Intelligence Phase 1A: Opportunity Engine.

This module is intentionally detection-only. It turns current read-only evidence
from Hermes OS snapshots into opportunities or capability gaps. It does not
prioritize, decide, execute, write memory, or mutate James runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .contracts import RiskLevel

OpportunityType = Literal[
    "seasonal_campaign",
    "queue_growth",
    "module_degraded",
    "container_degraded",
    "worker_stopped",
    "watcher_risk",
    "operational_bottleneck",
    "financial_existing_data",
    "documentation_outdated",
    "technical_backlog",
]

SUPPORTED_TYPES: tuple[OpportunityType, ...] = (
    "seasonal_campaign",
    "queue_growth",
    "module_degraded",
    "container_degraded",
    "worker_stopped",
    "watcher_risk",
    "operational_bottleneck",
    "financial_existing_data",
    "documentation_outdated",
    "technical_backlog",
)


@dataclass(frozen=True)
class Opportunity:
    title: str
    summary: str
    origin: str
    evidence: dict[str, Any]
    impact: str
    urgency: str
    effort: str
    risk: RiskLevel
    confidence: float
    available_capability: str
    policy_r0_r5: RiskLevel
    recommended_action: str
    approval_required: bool
    observed_component: str
    execution_tool_available: bool
    opportunity_type: OpportunityType


@dataclass(frozen=True)
class CapabilityGap:
    missing_capability: str
    expected_impact: str
    priority: str
    reason: str
    dependencies: tuple[str, ...]
    origin: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OpportunityReport:
    opportunities: tuple[Opportunity, ...]
    capability_gaps: tuple[CapabilityGap, ...]
    supported_types: tuple[OpportunityType, ...] = SUPPORTED_TYPES
    detection_only: bool = True
    priority_assigned: bool = False
    decision_made: bool = False
    real_side_effects_executed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class OpportunityEngine:
    """Detect evidence-backed opportunities without execution or prioritization."""

    def detect(self, observations: dict[str, Any]) -> OpportunityReport:
        dashboard = observations.get("module_supervision") or observations.get("dashboard") or {}
        modules = _modules_by_name(dashboard)
        opportunities: list[Opportunity] = []
        gaps: list[CapabilityGap] = []

        self._seasonal_campaign(observations, modules, opportunities, gaps)
        self._degraded_modules(dashboard, modules, opportunities, gaps)
        self._containers_degraded(dashboard, modules, opportunities, gaps)
        self._workers_stopped(dashboard, modules, opportunities, gaps)
        self._watchers_risk(dashboard, modules, opportunities, gaps)
        self._queue_growth(observations, modules, opportunities, gaps)
        self._financial_existing_data(observations, modules, opportunities, gaps)
        self._documentation_outdated(observations, opportunities, gaps)
        self._technical_backlog(observations, opportunities, gaps)

        return OpportunityReport(opportunities=tuple(opportunities), capability_gaps=tuple(gaps))

    def _seasonal_campaign(
        self,
        observations: dict[str, Any],
        modules: dict[str, dict[str, Any]],
        opportunities: list[Opportunity],
        gaps: list[CapabilityGap],
    ) -> None:
        evidence = observations.get("seasonal_licensing") or {}
        if not evidence.get("active"):
            return
        module = _first_existing_module(modules, ("campaign", "campaign_center", "campaign_engine"))
        capability = _capability(module, "campaign") if module else ""
        if not module or not capability:
            gaps.append(
                CapabilityGap(
                    missing_capability="campaign.seasonal_licensing.detect_or_draft",
                    expected_impact="Não detectar campanhas sazonais mesmo com evidência de calendário.",
                    priority="medium",
                    reason="Evidência sazonal existe, mas não há módulo/capability de campanha suficiente.",
                    dependencies=("campaign module", "vehicle/license data"),
                    origin="seasonal_licensing",
                    evidence=evidence,
                )
            )
            return
        self._append_if_complete(
            opportunities,
            gaps,
            Opportunity(
                title="Campanha sazonal de licenciamento detectada",
                summary="Há evidência de janela sazonal; somente detecção/draft é permitido nesta fase.",
                origin="seasonal_licensing",
                evidence=evidence,
                impact="Antecipar atendimento de licenciamento com base em dados existentes.",
                urgency=str(evidence.get("urgency", "normal")),
                effort="medium",
                risk=_risk(module),
                confidence=float(evidence.get("confidence", 0.78)),
                available_capability=capability,
                policy_r0_r5="R1",
                recommended_action="Gerar plano/draft de campanha; não enviar mensagens.",
                approval_required=True,
                observed_component=str(module.get("name")),
                execution_tool_available=True,
                opportunity_type="seasonal_campaign",
            ),
            "campaign.seasonal_licensing.detect_or_draft",
        )

    def _degraded_modules(self, dashboard: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        for name in dashboard.get("degraded_modules", ()):
            module = modules.get(str(name), {})
            evidence = {"module": name, "health": module.get("health"), "status": module.get("status"), "observations": module.get("observations", ()), "metrics": module.get("metrics", {})}
            capability = _capability(module, "health")
            self._append_if_complete(
                opportunities,
                gaps,
                Opportunity(
                    title=f"Módulo degradado: {name}",
                    summary="Supervisão modular indica degradação; apenas investigação read-only/dry-run é recomendada.",
                    origin="module_supervision.degraded_modules",
                    evidence=evidence,
                    impact="Reduzir risco operacional antes de efeitos em atendimento/campanhas.",
                    urgency="high",
                    effort="low",
                    risk=_risk(module),
                    confidence=float(module.get("confidence", 0.72) or 0.72),
                    available_capability=capability,
                    policy_r0_r5="R1",
                    recommended_action=f"Abrir plano dry-run de diagnóstico para {name}; sem restart/rebuild.",
                    approval_required=False,
                    observed_component=str(name),
                    execution_tool_available=True,
                    opportunity_type="module_degraded",
                ),
                f"{name}.health.read",
            )

    def _containers_degraded(self, dashboard: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        container_to_module = _container_index(modules)
        for container in dashboard.get("containers_with_problem", ()):
            module = container_to_module.get(str(container), {})
            evidence = {"container": container, "module": module.get("name"), "metrics": module.get("metrics", {})}
            capability = _capability(module, "status")
            self._append_if_complete(
                opportunities,
                gaps,
                Opportunity(
                    title=f"Container com problema: {container}",
                    summary="Inventário read-only aponta container problemático; recuperação real exige aprovação separada.",
                    origin="module_supervision.containers_with_problem",
                    evidence=evidence,
                    impact="Evitar perda de observabilidade/capacidade do módulo vinculado.",
                    urgency="high",
                    effort="medium",
                    risk=_risk(module),
                    confidence=float(module.get("confidence", 0.7) or 0.7),
                    available_capability=capability,
                    policy_r0_r5="R2",
                    recommended_action="Preparar handoff de recuperação; não executar start/restart/rebuild.",
                    approval_required=True,
                    observed_component=str(module.get("name") or container),
                    execution_tool_available=True,
                    opportunity_type="container_degraded",
                ),
                f"{container}.status.read",
            )

    def _workers_stopped(self, dashboard: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        for name in dashboard.get("workers_with_problem", ()):
            module = modules.get(str(name), {})
            evidence = {"module": name, "metrics": module.get("metrics", {}), "workers": module.get("workers_related", ())}
            capability = _capability(module, "worker")
            self._append_if_complete(
                opportunities,
                gaps,
                Opportunity(
                    title=f"Worker parado/sem evidência ativa: {name}",
                    summary="Modelo modular indica worker sem evidência ativa; apenas diagnóstico dry-run.",
                    origin="module_supervision.workers_with_problem",
                    evidence=evidence,
                    impact="Reduzir gargalo em processamento assíncrono.",
                    urgency="medium",
                    effort="medium",
                    risk=_risk(module),
                    confidence=float(module.get("confidence", 0.7) or 0.7),
                    available_capability=capability,
                    policy_r0_r5="R2",
                    recommended_action="Planejar diagnóstico do worker; não reiniciar container/processo.",
                    approval_required=True,
                    observed_component=str(name),
                    execution_tool_available=True,
                    opportunity_type="worker_stopped",
                ),
                f"{name}.worker.status.read",
            )

    def _watchers_risk(self, dashboard: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        for name in dashboard.get("watchers_with_problem", ()):
            module = modules.get(str(name), {})
            evidence = {"module": name, "watchers": module.get("watchers_related", ()), "risk": module.get("risk")}
            capability = _capability(module, "watcher")
            self._append_if_complete(
                opportunities,
                gaps,
                Opportunity(
                    title=f"Watcher sinalizando risco/ausência: {name}",
                    summary="Supervisão indica ausência/risco de watcher em módulo sensível.",
                    origin="module_supervision.watchers_with_problem",
                    evidence=evidence,
                    impact="Melhorar cobertura de monitoramento sem alterar runtime.",
                    urgency="medium",
                    effort="low",
                    risk=_risk(module),
                    confidence=float(module.get("confidence", 0.7) or 0.7),
                    available_capability=capability,
                    policy_r0_r5="R1",
                    recommended_action="Registrar lacuna de monitoramento e plano dry-run de cobertura.",
                    approval_required=False,
                    observed_component=str(name),
                    execution_tool_available=True,
                    opportunity_type="watcher_risk",
                ),
                f"{name}.watcher.status.read",
            )

    def _queue_growth(self, observations: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        queues = observations.get("queues") or {}
        if not queues:
            return
        for queue_name, queue_evidence in queues.items():
            if not isinstance(queue_evidence, dict) or not queue_evidence.get("growing"):
                continue
            module = modules.get(str(queue_evidence.get("module", "worker_jobs")), {})
            capability = _capability(module, "queue")
            if not capability:
                gaps.append(
                    CapabilityGap(
                        missing_capability="queue.depth.read",
                        expected_impact="Fila crescente não pode virar oportunidade acionável sem contrato read-only de fila.",
                        priority="high",
                        reason="Evidência de crescimento existe, mas falta capability de leitura/diagnóstico da fila.",
                        dependencies=("queue depth metric", "worker/module mapping"),
                        origin="queues",
                        evidence={"queue": queue_name, **queue_evidence},
                    )
                )
                continue
            self._append_if_complete(
                opportunities,
                gaps,
                Opportunity(
                    title=f"Fila crescendo: {queue_name}",
                    summary="Métrica read-only indica crescimento de fila.",
                    origin="queues",
                    evidence={"queue": queue_name, **queue_evidence},
                    impact="Evitar atraso acumulado no fluxo operacional.",
                    urgency="high",
                    effort="medium",
                    risk=_risk(module),
                    confidence=float(queue_evidence.get("confidence", 0.76)),
                    available_capability=capability,
                    policy_r0_r5="R1",
                    recommended_action="Gerar diagnóstico dry-run de gargalo da fila.",
                    approval_required=False,
                    observed_component=str(module.get("name") or queue_evidence.get("module") or queue_name),
                    execution_tool_available=True,
                    opportunity_type="queue_growth",
                ),
                "queue.depth.read",
            )

    def _financial_existing_data(self, observations: dict[str, Any], modules: dict[str, dict[str, Any]], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        evidence = observations.get("financial_existing_data") or {}
        if not evidence.get("detected"):
            return
        module = _first_existing_module(modules, ("billing_pix", "campaign", "campaign_center"))
        capability = _capability(module or {}, "billing")
        if not module or not capability:
            gaps.append(
                CapabilityGap(
                    missing_capability="financial.opportunity.read_existing_data",
                    expected_impact="Oportunidade financeira baseada em dados existentes não pode ser qualificada.",
                    priority="medium",
                    reason="Evidência financeira existe, mas falta capability operacional segura.",
                    dependencies=("billing/campaign capability", "existing debt/service evidence"),
                    origin="financial_existing_data",
                    evidence=evidence,
                )
            )
            return
        self._append_if_complete(
            opportunities,
            gaps,
            Opportunity(
                title="Oportunidade financeira baseada em dados existentes",
                summary="Dados existentes indicam potencial de cobrança/serviço; execução real é proibida sem aprovação.",
                origin="financial_existing_data",
                evidence=evidence,
                impact=str(evidence.get("impact", "Aumentar conversão de serviços já identificados.")),
                urgency=str(evidence.get("urgency", "normal")),
                effort="medium",
                risk="R5",
                confidence=float(evidence.get("confidence", 0.74)),
                available_capability=capability,
                policy_r0_r5="R5",
                recommended_action="Preparar lista/draft sanitizado para revisão; não criar PIX/cobrança/envio.",
                approval_required=True,
                observed_component=str(module.get("name")),
                execution_tool_available=True,
                opportunity_type="financial_existing_data",
            ),
            "financial.existing_data.read",
        )

    def _documentation_outdated(self, observations: dict[str, Any], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        docs = observations.get("documentation") or {}
        if not docs.get("outdated"):
            return
        capability = "docs.audit.read"
        self._append_if_complete(
            opportunities,
            gaps,
            Opportunity(
                title="Documentação desatualizada detectada",
                summary="Evidência de divergência documental; correção deve ser proposta como plano, não aplicada automaticamente.",
                origin="documentation",
                evidence=docs,
                impact="Reduzir erro operacional por runbook/relatório obsoleto.",
                urgency=str(docs.get("urgency", "normal")),
                effort="low",
                risk="R1",
                confidence=float(docs.get("confidence", 0.73)),
                available_capability=capability,
                policy_r0_r5="R1",
                recommended_action="Gerar plano de atualização documental com evidência; não editar automaticamente nesta fase.",
                approval_required=False,
                observed_component=str(docs.get("component", "docs")),
                execution_tool_available=True,
                opportunity_type="documentation_outdated",
            ),
            capability,
        )

    def _technical_backlog(self, observations: dict[str, Any], opportunities: list[Opportunity], gaps: list[CapabilityGap]) -> None:
        backlog = observations.get("technical_backlog") or {}
        items = backlog.get("items") or []
        if not items:
            return
        capability = "kanban.backlog.read"
        self._append_if_complete(
            opportunities,
            gaps,
            Opportunity(
                title="Backlog técnico acionável detectado",
                summary="Backlog técnico possui itens observáveis; somente detecção e agrupamento são permitidos.",
                origin="technical_backlog",
                evidence={"items": items[:10], "count": len(items)},
                impact="Reduzir dívida técnica por triagem executiva futura.",
                urgency=str(backlog.get("urgency", "normal")),
                effort="medium",
                risk="R1",
                confidence=float(backlog.get("confidence", 0.72)),
                available_capability=capability,
                policy_r0_r5="R1",
                recommended_action="Enviar para próxima competência Prioritization Engine; não priorizar agora.",
                approval_required=False,
                observed_component="kanban/backlog",
                execution_tool_available=True,
                opportunity_type="technical_backlog",
            ),
            capability,
        )

    def _append_if_complete(
        self,
        opportunities: list[Opportunity],
        gaps: list[CapabilityGap],
        candidate: Opportunity,
        missing_capability: str,
    ) -> None:
        required = (
            candidate.title,
            candidate.summary,
            candidate.origin,
            candidate.evidence,
            candidate.impact,
            candidate.urgency,
            candidate.effort,
            candidate.risk,
            candidate.confidence,
            candidate.available_capability,
            candidate.policy_r0_r5,
            candidate.recommended_action,
            candidate.observed_component,
        )
        if all(value not in (None, "", {}, ()) for value in required) and candidate.execution_tool_available:
            opportunities.append(candidate)
            return
        gaps.append(
            CapabilityGap(
                missing_capability=missing_capability,
                expected_impact=candidate.impact or "Oportunidade não pode ser transformada em ação segura.",
                priority="medium",
                reason="Resposta essencial ausente para oportunidade; convertida para Capability Gap.",
                dependencies=(candidate.observed_component or "unknown_component", candidate.origin or "unknown_origin"),
                origin=candidate.origin or "unknown",
                evidence=candidate.evidence,
            )
        )


def detect_opportunities(observations: dict[str, Any]) -> dict[str, Any]:
    return OpportunityEngine().detect(observations).as_dict()


def _modules_by_name(dashboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(module.get("name")): module for module in dashboard.get("modules", ()) if isinstance(module, dict) and module.get("name")}


def _first_existing_module(modules: dict[str, dict[str, Any]], names: tuple[str, ...]) -> dict[str, Any] | None:
    for name in names:
        if name in modules:
            return modules[name]
    return None


def _capability(module: dict[str, Any], hint: str) -> str:
    capabilities = [str(item) for item in module.get("capabilities_related", ())]
    if hint:
        for capability in capabilities:
            if hint.lower() in capability.lower():
                return capability
    if capabilities:
        return capabilities[0]
    policy = module.get("policy") or {}
    observe = policy.get("r0_observe") or ()
    return str(observe[0]) if observe else ""


def _risk(module: dict[str, Any]) -> RiskLevel:
    risk = str(module.get("risk") or "R1")
    if risk in {"R0", "R1", "R2", "R3", "R4", "R5"}:
        return risk  # type: ignore[return-value]
    return "R1"


def _container_index(modules: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for module in modules.values():
        metrics = module.get("metrics", {})
        for container in metrics.get("containers_problem", ()):
            index[str(container)] = module
    return index
