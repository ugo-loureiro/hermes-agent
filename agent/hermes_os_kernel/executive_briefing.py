"""Executive Daily Briefing engine for Hermes OS.

The engine renders a deterministic, evidence-only daily briefing from the
already-frozen Hermes OS architecture: Observer/Supervisor evidence, the module
supervision dashboard, Opportunity Engine output, read-only MCP/Kanban/health
observations, registries, watchers, workers, containers and policies.

It does not schedule, notify, execute, mutate James runtime, write memory, or
create new structural contracts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .opportunity_engine import OpportunityEngine

BRIEFING_SECTIONS: tuple[str, ...] = (
    "executive_summary",
    "general_state",
    "modules_needing_attention",
    "opportunities_detected",
    "capability_gaps",
    "risks",
    "pending_items",
    "recommendations",
    "possible_actions_today",
    "actions_requiring_approval",
    "justification",
    "confidence",
    "evidence_used",
)


@dataclass(frozen=True)
class BriefingRecommendation:
    text: str
    origin: str
    confidence: float
    available_capability: str
    policy_r0_r5: str
    approval_required: bool


@dataclass(frozen=True)
class ExecutiveDailyBriefing:
    executive_summary: str
    general_state: dict[str, Any]
    modules_needing_attention: tuple[dict[str, Any], ...]
    opportunities_detected: tuple[dict[str, Any], ...]
    capability_gaps: tuple[dict[str, Any], ...]
    risks: tuple[dict[str, Any], ...]
    pending_items: tuple[dict[str, Any], ...]
    recommendations: tuple[BriefingRecommendation, ...]
    possible_actions_today: tuple[dict[str, Any], ...]
    actions_requiring_approval: tuple[dict[str, Any], ...]
    justification: str
    confidence: float
    evidence_used: tuple[dict[str, Any], ...]
    sections: tuple[str, ...] = BRIEFING_SECTIONS
    generated_spontaneously_capable: bool = True
    scheduled: bool = False
    notification_sent: bool = False
    real_side_effects_executed: bool = False
    memory_written: bool = False
    mutative_calls_made: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = ["# Executive Daily Briefing", ""]
        lines.extend(["## 1. Resumo Executivo", "", self.executive_summary, ""])
        lines.extend(["## 2. Estado Geral", "", _jsonish(self.general_state), ""])
        lines.extend(["## 3. Módulos que precisam atenção", "", _list_block(self.modules_needing_attention), ""])
        lines.extend(["## 4. Oportunidades detectadas", "", _list_block(self.opportunities_detected), ""])
        lines.extend(["## 5. Capability Gaps", "", _list_block(self.capability_gaps), ""])
        lines.extend(["## 6. Riscos", "", _list_block(self.risks), ""])
        lines.extend(["## 7. Pendências", "", _list_block(self.pending_items), ""])
        lines.extend(["## 8. Recomendações", "", _list_block(tuple(asdict(item) for item in self.recommendations)), ""])
        lines.extend(["## 9. Ações possíveis hoje", "", _list_block(self.possible_actions_today), ""])
        lines.extend(["## 10. Ações que exigem aprovação", "", _list_block(self.actions_requiring_approval), ""])
        lines.extend(["## 11. Justificativa", "", self.justification, ""])
        lines.extend(["## 12. Confiança", "", str(self.confidence), ""])
        lines.extend(["## 13. Evidências utilizadas", "", _list_block(self.evidence_used), ""])
        return "\n".join(lines)


class ExecutiveBriefingEngine:
    """Build an evidence-only daily briefing; no scheduling/notification."""

    def __init__(self, opportunity_engine: OpportunityEngine | None = None) -> None:
        self.opportunity_engine = opportunity_engine or OpportunityEngine()

    def generate(self, observations: dict[str, Any], *, review: dict[str, Any] | None = None) -> ExecutiveDailyBriefing:
        dashboard = observations.get("module_supervision") or {}
        opportunity_report = self.opportunity_engine.detect(observations).as_dict()
        opportunities = tuple(_normalize_opportunity(item) for item in opportunity_report.get("opportunities", ()))
        gaps = tuple(_normalize_gap(item) for item in opportunity_report.get("capability_gaps", ()))
        modules_attention = tuple(_module_attention_items(dashboard))
        risks = tuple(_risk_items(dashboard, opportunities, gaps, review))
        pending = tuple(_pending_items(observations, dashboard, gaps))
        recommendations = tuple(_recommendations(opportunities, gaps))
        possible_actions = tuple(_possible_actions(opportunities))
        approval_actions = tuple(_approval_actions(opportunities, gaps))
        evidence = tuple(_evidence_used(observations, opportunity_report, review))
        confidence = _briefing_confidence(observations, dashboard, opportunity_report, review)
        summary = _executive_summary(dashboard, opportunities, gaps, risks, pending)
        general_state = {
            "overall": dashboard.get("overall_state") or observations.get("global_state", {}).get("overall") or "unknown",
            "read_only": bool(observations.get("read_only", True)),
            "max_autonomy_without_ugo": (dashboard.get("benchmark") or {}).get("max_autonomy_without_ugo", "R1"),
            "module_count": (dashboard.get("benchmark") or {}).get("module_count", 0),
            "healthy_count": (dashboard.get("benchmark") or {}).get("healthy_count", 0),
            "degraded_count": (dashboard.get("benchmark") or {}).get("degraded_count", 0),
            "critical_count": (dashboard.get("benchmark") or {}).get("critical_count", 0),
            "opportunity_count": len(opportunities),
            "capability_gap_count": len(gaps),
            "real_side_effects_allowed": False,
        }
        return ExecutiveDailyBriefing(
            executive_summary=summary,
            general_state=general_state,
            modules_needing_attention=modules_attention,
            opportunities_detected=opportunities,
            capability_gaps=gaps,
            risks=risks,
            pending_items=pending,
            recommendations=recommendations,
            possible_actions_today=possible_actions,
            actions_requiring_approval=approval_actions,
            justification=_justification(evidence, opportunities, gaps),
            confidence=confidence,
            evidence_used=evidence,
        )


def generate_executive_daily_briefing(observations: dict[str, Any], *, review: dict[str, Any] | None = None) -> dict[str, Any]:
    return ExecutiveBriefingEngine().generate(observations, review=review).as_dict()


def _normalize_opportunity(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title"),
        "summary": item.get("summary"),
        "origin": item.get("origin"),
        "evidence": item.get("evidence"),
        "impact": item.get("impact"),
        "urgency": item.get("urgency"),
        "effort": item.get("effort"),
        "risk": item.get("risk"),
        "confidence": item.get("confidence"),
        "available_capability": item.get("available_capability"),
        "policy_r0_r5": item.get("policy_r0_r5"),
        "recommended_action": item.get("recommended_action"),
        "approval_required": item.get("approval_required"),
        "observed_component": item.get("observed_component"),
        "opportunity_type": item.get("opportunity_type"),
    }


def _normalize_gap(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "missing_capability": item.get("missing_capability"),
        "expected_impact": item.get("expected_impact"),
        "priority": item.get("priority"),
        "reason": item.get("reason"),
        "dependencies": item.get("dependencies", ()),
        "origin": item.get("origin"),
        "evidence": item.get("evidence", {}),
    }


def _module_attention_items(dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    modules = {str(item.get("name")): item for item in dashboard.get("modules", ()) if isinstance(item, dict)}
    names = list(dict.fromkeys(list(dashboard.get("attention_now", ())) + list(dashboard.get("degraded_modules", ())) + list(dashboard.get("critical_modules", ()))))
    items: list[dict[str, Any]] = []
    for name in names:
        module = modules.get(str(name), {})
        items.append(
            {
                "module": name,
                "health": module.get("health"),
                "status": module.get("status"),
                "risk": module.get("risk"),
                "confidence": module.get("confidence"),
                "evidence": {"observations": module.get("observations", ()), "metrics": module.get("metrics", {})},
                "policy_r0_r5": module.get("autonomy_max_allowed", "R1"),
                "approval_required": str(module.get("risk", "R1")) in {"R2", "R3", "R4", "R5"},
            }
        )
    return items


def _risk_items(dashboard: dict[str, Any], opportunities: tuple[dict[str, Any], ...], gaps: tuple[dict[str, Any], ...], review: dict[str, Any] | None) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for name in dashboard.get("degraded_modules", ()):
        risks.append({"risk": "module_degraded", "component": name, "origin": "module_supervision.degraded_modules", "confidence": 0.72})
    for container in dashboard.get("containers_with_problem", ()):
        risks.append({"risk": "container_problem", "component": container, "origin": "module_supervision.containers_with_problem", "confidence": 0.8})
    for gap in gaps:
        risks.append({"risk": "capability_gap", "component": gap.get("missing_capability"), "origin": gap.get("origin"), "confidence": 0.7})
    for opp in opportunities:
        if opp.get("approval_required"):
            risks.append({"risk": "approval_required", "component": opp.get("observed_component"), "origin": opp.get("origin"), "confidence": opp.get("confidence")})
    if review and review.get("status") in {"attention", "blocked"}:
        risks.append({"risk": f"review_{review.get('status')}", "component": "Supervisor", "origin": "supervisor.review", "confidence": review.get("confidence", 0.7)})
    return risks


def _pending_items(observations: dict[str, Any], dashboard: dict[str, Any], gaps: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    pending = []
    kanban = (((observations.get("james_operational") or {}).get("operational_view") or {}).get("kanban") or {})
    if kanban:
        pending.append({"item": "kanban_readonly_snapshot", "origin": "Kanban read-only", "evidence": kanban, "approval_required": False})
    for gap in gaps:
        pending.append({"item": gap.get("missing_capability"), "origin": gap.get("origin"), "evidence": gap.get("evidence"), "approval_required": False})
    if dashboard.get("queues_growing"):
        pending.append({"item": "queues_growing", "origin": "module_supervision.queues_growing", "evidence": dashboard.get("queues_growing"), "approval_required": False})
    return pending


def _recommendations(opportunities: tuple[dict[str, Any], ...], gaps: tuple[dict[str, Any], ...]) -> list[BriefingRecommendation]:
    recommendations = []
    for opp in opportunities:
        if not _opportunity_has_required_fields(opp):
            continue
        recommendations.append(
            BriefingRecommendation(
                text=str(opp.get("recommended_action")),
                origin=str(opp.get("origin")),
                confidence=float(opp.get("confidence") or 0.0),
                available_capability=str(opp.get("available_capability")),
                policy_r0_r5=str(opp.get("policy_r0_r5")),
                approval_required=bool(opp.get("approval_required")),
            )
        )
    for gap in gaps:
        recommendations.append(
            BriefingRecommendation(
                text=f"Não executar; preencher Capability Gap {gap.get('missing_capability')} antes de qualquer ação.",
                origin=str(gap.get("origin")),
                confidence=0.7,
                available_capability="missing",
                policy_r0_r5="R0",
                approval_required=False,
            )
        )
    return recommendations


def _possible_actions(opportunities: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [
        {
            "action": opp.get("recommended_action"),
            "origin": opp.get("origin"),
            "capability": opp.get("available_capability"),
            "policy_r0_r5": opp.get("policy_r0_r5"),
            "approval_required": opp.get("approval_required"),
            "execution": "not_executed_detection_only",
        }
        for opp in opportunities
        if _opportunity_has_required_fields(opp) and not opp.get("approval_required")
    ]


def _approval_actions(opportunities: tuple[dict[str, Any], ...], gaps: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    actions = [
        {
            "action": opp.get("recommended_action"),
            "origin": opp.get("origin"),
            "capability": opp.get("available_capability"),
            "policy_r0_r5": opp.get("policy_r0_r5"),
            "approval_required": True,
            "execution": "blocked_until_ugo_approval",
        }
        for opp in opportunities
        if _opportunity_has_required_fields(opp) and opp.get("approval_required")
    ]
    actions.extend(
        {
            "action": f"Capability Gap: {gap.get('missing_capability')}",
            "origin": gap.get("origin"),
            "capability": "missing",
            "policy_r0_r5": "R0",
            "approval_required": False,
            "execution": "not_executable_gap",
        }
        for gap in gaps
    )
    return actions


def _evidence_used(observations: dict[str, Any], opportunity_report: dict[str, Any], review: dict[str, Any] | None) -> list[dict[str, Any]]:
    evidence = []
    if observations.get("knowledge_fabric"):
        evidence.append({"source": "Knowledge Fabric", "origin": "observer.knowledge_fabric", "confidence": observations["knowledge_fabric"].get("confidence")})
    if observations.get("james_operational"):
        evidence.append({"source": "MCP read-only / James operational", "origin": "observer.james_operational", "confidence": observations["james_operational"].get("confidence", 0.86)})
    if observations.get("module_supervision"):
        evidence.append({"source": "Module supervision dashboard", "origin": "observer.module_supervision", "confidence": 0.86})
    if observations.get("docker_inventory"):
        evidence.append({"source": "Containers", "origin": "observer.docker_inventory", "confidence": 0.8})
    if review:
        evidence.append({"source": "Supervisor", "origin": "supervisor.review", "confidence": review.get("confidence")})
    evidence.append({"source": "Opportunity Engine", "origin": "opportunity_engine.detect", "confidence": 0.82, "opportunities": len(opportunity_report.get("opportunities", ())), "capability_gaps": len(opportunity_report.get("capability_gaps", ()))})
    return evidence


def _briefing_confidence(observations: dict[str, Any], dashboard: dict[str, Any], opportunity_report: dict[str, Any], review: dict[str, Any] | None) -> float:
    values = [0.82]
    if observations.get("knowledge_fabric", {}).get("confidence"):
        values.append(float(observations["knowledge_fabric"]["confidence"]))
    if dashboard.get("benchmark", {}).get("module_count"):
        values.append(0.86)
    if review and review.get("confidence"):
        values.append(float(review["confidence"]))
    if opportunity_report.get("opportunities") or opportunity_report.get("capability_gaps"):
        values.append(0.82)
    return round(sum(values) / len(values), 2)


def _executive_summary(dashboard: dict[str, Any], opportunities: tuple[dict[str, Any], ...], gaps: tuple[dict[str, Any], ...], risks: tuple[dict[str, Any], ...], pending: tuple[dict[str, Any], ...]) -> str:
    benchmark = dashboard.get("benchmark") or {}
    if not benchmark and not opportunities and not gaps and not risks:
        return "Sem evidência suficiente para apontar oportunidades, gaps ou riscos hoje."
    return (
        f"James está em estado {dashboard.get('overall_state', 'unknown')} com "
        f"{benchmark.get('module_count', 0)} módulos observados, "
        f"{benchmark.get('degraded_count', 0)} degradados, "
        f"{len(opportunities)} oportunidades detectadas, "
        f"{len(gaps)} Capability Gaps e {len(pending)} pendências read-only."
    )


def _justification(evidence: tuple[dict[str, Any], ...], opportunities: tuple[dict[str, Any], ...], gaps: tuple[dict[str, Any], ...]) -> str:
    sources = ", ".join(str(item.get("source")) for item in evidence)
    return (
        "Briefing gerado exclusivamente a partir de evidências permitidas: "
        f"{sources}. Oportunidades sem campos obrigatórios não são emitidas; "
        f"casos incompletos viram Capability Gaps. Contagem: {len(opportunities)} oportunidades, {len(gaps)} gaps."
    )


def _opportunity_has_required_fields(opp: dict[str, Any]) -> bool:
    required = (
        "title",
        "summary",
        "origin",
        "evidence",
        "impact",
        "urgency",
        "effort",
        "risk",
        "confidence",
        "available_capability",
        "policy_r0_r5",
        "recommended_action",
        "approval_required",
    )
    return all(opp.get(field) not in (None, "", {}, ()) for field in required)


def _jsonish(value: Any) -> str:
    return "\n".join(f"- {key}: {val}" for key, val in value.items()) if isinstance(value, dict) else str(value)


def _list_block(items: tuple[dict[str, Any], ...]) -> str:
    if not items:
        return "- none"
    lines = []
    for item in items:
        label = item.get("title") or item.get("module") or item.get("risk") or item.get("action") or item.get("missing_capability") or item.get("source") or "item"
        lines.append(f"- {label}: {item}")
    return "\n".join(lines)
