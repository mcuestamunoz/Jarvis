from __future__ import annotations

from typing import Any

from jarvis.core.reasoning_layer import HIGH_MARGIN_THRESHOLD

# Phase labels in display order (definition → complete).
# To add a new phase insert it here AND add a rule in PhaseLayer.infer().
_PHASE_DESCRIPTIONS: dict[str, str] = {
    "definition": "Faltan parámetros de sistema para completar la validación física.",
    "definition_no_sim": "Sin simulación previa — el sistema está en fase de definición inicial.",
    "physical_validation": "La simulación indica inviabilidad; el diseño necesita ajustes físicos.",
    "optimization": "El sistema es físicamente viable. Próximo paso: optimizar rendimiento y margen.",
    "complete": "El sistema cumple todos los criterios de viabilidad con margen suficiente.",
}


class PhaseLayer:
    """Deterministic project phase inferrer.

    Consumes reasoning signals + simulation result and returns a structured
    dict describing where the project stands in the engineering process.

    Rules are applied in strict priority order — the first matching rule wins.
    Never calls the LLM; never modifies state.
    """

    def infer(
        self,
        signals: dict[str, bool],
        simulation: dict[str, Any],
    ) -> dict[str, Any]:
        """Infer the current project phase.

        Returns::

            {
                "phase": "definition" | "physical_validation" | "optimization" | "complete",
                "description": str,
                "confidence": float,
            }
        """
        quality = simulation.get("quality") or ""
        margin = float(simulation.get("safety_margin_ratio") or 0.0)
        constraints_satisfied = bool(simulation.get("can_fly", False))

        # ── Priority 1: physics blocking (missing transmission params) ─────────
        if signals.get("missing_physics_parameters"):
            return {
                "phase": "definition",
                "description": _PHASE_DESCRIPTIONS["definition"],
                "confidence": 0.95,
            }

        # ── Priority 2: no simulation yet ──────────────────────────────────────
        if not signals.get("has_simulation"):
            return {
                "phase": "definition",
                "description": _PHASE_DESCRIPTIONS["definition_no_sim"],
                "confidence": 0.7,
            }

        # ── Priority 3: simulation ran but design is not viable ────────────────
        if quality in ("fail", "risky"):
            return {
                "phase": "physical_validation",
                "description": _PHASE_DESCRIPTIONS["physical_validation"],
                "confidence": 0.9,
            }

        # ── Priority 4: viable + sufficient margin + no unmet constraints → complete
        warnings = simulation.get("warnings") or []
        if quality in ("acceptable", "good") and constraints_satisfied and not warnings and margin >= HIGH_MARGIN_THRESHOLD:
            return {
                "phase": "complete",
                "description": _PHASE_DESCRIPTIONS["complete"],
                "confidence": 0.95,
            }

        # ── Priority 5: viable but room to improve ─────────────────────────────
        if quality in ("acceptable", "good"):
            return {
                "phase": "optimization",
                "description": _PHASE_DESCRIPTIONS["optimization"],
                "confidence": 0.85,
            }

        # ── Fallback ───────────────────────────────────────────────────────────
        return {
            "phase": "definition",
            "description": _PHASE_DESCRIPTIONS["definition_no_sim"],
            "confidence": 0.5,
        }
