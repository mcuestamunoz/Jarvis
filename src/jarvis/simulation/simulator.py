from __future__ import annotations

from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
    MISSING_ENERGY_PARAMETERS,
    MISSING_FORCE_REASONS,
    MISSING_PROPELLER_PARAMETERS,
    reason_domain_label,
)
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


LOW_MARGIN_THRESHOLD = 1.15
HIGH_LOAD_THRESHOLD = 0.9
LOW_TW_RATIO = 1.3


class FeasibilitySimulator:
    def evaluate(self, calculations: CalculationBundle, autonomy_threshold: float | None = None) -> SimulationResult:
        available = calculations.available_total_thrust_n

        # ── Missing-parameters branch ────────────────────────────────────────
        # No force available means no physics — but we still return a
        # structured, traceable result instead of crashing or returning None.
        # Energy block runs independently: bridge its results even here.
        if available is None:
            has_missing_energy_early = any(
                tr.tool_name == MISSING_ENERGY_PARAMETERS
                for tr in calculations.tool_results
            )
            has_missing_propeller_early = any(
                tr.tool_name == MISSING_PROPELLER_PARAMETERS
                for tr in calculations.tool_results
            )
            # Read the domain reason code emitted by the engine — avoids hardcoding the domain here.
            missing_reason = next(
                (tr.tool_name for tr in calculations.tool_results if tr.tool_name in MISSING_FORCE_REASONS),
                DEFAULT_MISSING_FORCE_REASON,  # fallback for legacy states without a tool record
            )
            domain_label = reason_domain_label(missing_reason)
            return SimulationResult(
                physics_status="missing_parameters",
                energy_status=MISSING_ENERGY_PARAMETERS if has_missing_energy_early else "valid",
                propeller_status=MISSING_PROPELLER_PARAMETERS if has_missing_propeller_early else "valid",
                status="fail",
                can_fly=False,
                quality="fail",
                safety_margin_ratio=0.0,
                thrust_to_weight_ratio=0.0,
                autonomy_min=calculations.autonomy_min,
                propeller_thrust_inferred=False,
                warnings=[missing_reason],
                analysis=SimulationAnalysis(
                    available_thrust_n=None,
                    required_thrust_n=round(calculations.required_thrust_n, 4),
                    weight_n=round(calculations.weight_n, 4),
                    per_motor_load_ratio=0.0,
                ),
                summary=(
                    f"Estado fail. Calidad fail. "
                    f"Parámetros de {domain_label} ausentes: "
                    f"no es posible calcular fuerza de tracción."
                ),
            )

        required = calculations.required_thrust_n
        weight = calculations.weight_n
        can_fly = available >= required
        safety_margin_ratio = available / required if required else 0.0
        thrust_to_weight_ratio = available / weight if weight else 0.0
        max_thrust_per_motor = available / calculations.motors if calculations.motors not in (None, 0) else 0.0
        per_motor_load_ratio = (
            calculations.thrust_per_motor_required_n / max_thrust_per_motor
            if (max_thrust_per_motor and calculations.thrust_per_motor_required_n is not None)
            else 0.0
        )
        status = "pass" if can_fly else "fail"
        quality = self._resolve_quality(safety_margin_ratio)
        warnings = self._resolve_warnings(
            can_fly=can_fly,
            safety_margin_ratio=safety_margin_ratio,
            thrust_to_weight_ratio=thrust_to_weight_ratio,
            per_motor_load_ratio=per_motor_load_ratio,
            autonomy_min=calculations.autonomy_min,
            autonomy_threshold=autonomy_threshold,
        )

        # ── Energy status ────────────────────────────────────────────────────
        energy_status = "valid"
        has_missing_energy = any(
            tr.tool_name == MISSING_ENERGY_PARAMETERS
            for tr in calculations.tool_results
        )
        if has_missing_energy:
            energy_status = MISSING_ENERGY_PARAMETERS
        # Note: energy_status is intentionally NOT added to warnings so it doesn't
        # affect the force-physics status_type hierarchy in build_startup_context.
        # ── Propeller status ────────────────────────────────────────────────────────────
        # Independent field, NOT added to warnings — parallel to energy_status.
        has_missing_propeller = any(
            tr.tool_name == MISSING_PROPELLER_PARAMETERS
            for tr in calculations.tool_results
        )
        propeller_status = MISSING_PROPELLER_PARAMETERS if has_missing_propeller else "valid"
        analysis = SimulationAnalysis(
            available_thrust_n=round(available, 4),
            required_thrust_n=round(required, 4),
            weight_n=round(weight, 4),
            per_motor_load_ratio=round(per_motor_load_ratio, 4),
        )
        summary = self._build_summary(
            status=status,
            quality=quality,
            safety_margin_ratio=safety_margin_ratio,
            warnings=warnings,
        )
        has_propeller_inference = any(
            tr.tool_name == "calculate_thrust_from_propeller"
            for tr in calculations.tool_results
        )
        return SimulationResult(
            energy_status=energy_status,
            propeller_status=propeller_status,
            status=status,
            can_fly=can_fly,
            quality=quality,
            safety_margin_ratio=round(safety_margin_ratio, 4),
            thrust_to_weight_ratio=round(thrust_to_weight_ratio, 4),
            autonomy_min=calculations.autonomy_min,
            propeller_thrust_inferred=has_propeller_inference,
            warnings=warnings,
            analysis=analysis,
            summary=summary,
        )

    def _resolve_quality(self, safety_margin_ratio: float) -> str:
        if safety_margin_ratio < 1.0:
            return "fail"
        if safety_margin_ratio < 1.1:
            return "risky"
        if safety_margin_ratio < 1.3:
            return "acceptable"
        return "good"

    def _resolve_warnings(
        self,
        *,
        can_fly: bool,
        safety_margin_ratio: float,
        thrust_to_weight_ratio: float,
        per_motor_load_ratio: float,
        autonomy_min: float | None = None,
        autonomy_threshold: float | None = None,
    ) -> list[str]:
        warnings: list[str] = []
        if can_fly and safety_margin_ratio < LOW_MARGIN_THRESHOLD:
            warnings.append("low_margin")
        if can_fly and thrust_to_weight_ratio < LOW_TW_RATIO:
            warnings.append("low_force_to_weight_ratio")
        if can_fly and per_motor_load_ratio > HIGH_LOAD_THRESHOLD:
            warnings.append("high_actuator_load")
        if autonomy_min is not None and autonomy_threshold is not None and autonomy_min < autonomy_threshold:
            warnings.append("autonomy_below_restriction")
        return warnings

    def _build_summary(
        self,
        *,
        status: str,
        quality: str,
        safety_margin_ratio: float,
        warnings: list[str],
    ) -> str:
        summary = (
            f"Estado {status}. Calidad {quality}. "
            f"Margen de seguridad {safety_margin_ratio:.2f}."
        )
        if warnings:
            return f"{summary} Warnings: {', '.join(warnings)}."
        return summary


FlightSimulator = FeasibilitySimulator  # backward-compat alias
