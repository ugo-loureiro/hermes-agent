"""Supervisor component for Hermes OS Kernel Phase 0."""

from __future__ import annotations

from .contracts import Objective, Review, Snapshot


class Supervisor:
    """Compares objective vs observed state and emits recommendation."""

    def review(self, objective: Objective, snapshot: Snapshot) -> Review:
        findings: list[str] = [f"Snapshot status: {snapshot.status}"]
        recommendations: list[str] = []
        risk_level = "R0"
        status = "on_track"

        james_health = snapshot.observations.get("james_health", {})
        failed = [name for name, data in james_health.items() if not data.get("ok")]
        if failed:
            status = "attention"
            risk_level = "R1"
            findings.append("Unhealthy/unreachable read-only endpoints: " + ", ".join(sorted(failed)))
            recommendations.append("Keep action read-only; use deeper authorized diagnostics only if Ugo asks.")
        else:
            findings.append("Required James health endpoints responded OK in read-only probe.")
            recommendations.append("Proceed with planning and dry-run mapping; no runtime action required.")

        docker_inventory = snapshot.observations.get("docker_inventory") or {}
        if docker_inventory.get("available"):
            count = docker_inventory.get("count", 0)
            findings.append(f"Docker read-only inventory found {count} James/Evolution containers.")
        elif docker_inventory:
            findings.append("Docker inventory unavailable or failed; health endpoints remain primary evidence.")

        return Review(
            objective=objective,
            status=status,  # type: ignore[arg-type]
            findings=tuple(findings),
            recommendations=tuple(recommendations),
            risk_level=risk_level,  # type: ignore[arg-type]
            confidence=min(0.9, snapshot.confidence + 0.05),
        )
