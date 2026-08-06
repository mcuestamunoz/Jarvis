from __future__ import annotations

from jarvis.schemas.tool_schema import CalculationBundle, SimulationResult, Suggestion


HIGH_MARGIN_THRESHOLD = 1.8
LOW_MARGIN_THRESHOLD = 1.3
HIGH_TW_RATIO_THRESHOLD = 1.6
HIGH_MOTOR_LOAD_THRESHOLD = 0.9


class SuggestionEngine:
    def generate_suggestions(
        self,
        simulation: SimulationResult,
        calculations: CalculationBundle,
    ) -> list[Suggestion]:
        suggestions: list[Suggestion] = []
        seen_types: set[str] = set()

        def add(suggestion: Suggestion) -> None:
            if suggestion.type in seen_types:
                return
            seen_types.add(suggestion.type)
            suggestions.append(suggestion)

        has_autonomy_warning = "autonomy_below_restriction" in (simulation.warnings or [])

        if has_autonomy_warning:
            add(
                Suggestion(
                    type="improve_autonomy",
                    reason="La autonomía calculada está por debajo de la restricción definida.",
                    expected_effect="increases autonomy",
                    priority=1.0,
                )
            )

        if simulation.safety_margin_ratio > HIGH_MARGIN_THRESHOLD and not has_autonomy_warning:
            add(
                Suggestion(
                    type="increase_payload",
                    reason="El margen de empuje actual permite explorar más carga útil.",
                    expected_effect="reduces margin",
                    priority=0.9,
                )
            )
            add(
                Suggestion(
                    type="improve_efficiency",
                    reason="Hay margen suficiente para buscar una configuración más eficiente.",
                    expected_effect="improves efficiency",
                    priority=0.7,
                )
            )

        if simulation.safety_margin_ratio < LOW_MARGIN_THRESHOLD or "low_margin" in simulation.warnings:
            add(
                Suggestion(
                    type="reduce_weight",
                    reason="El margen de seguridad es ajustado para la configuración actual.",
                    expected_effect="improves margin",
                    priority=1.0 if "low_margin" in simulation.warnings else 0.95,
                )
            )

        if simulation.thrust_to_weight_ratio > HIGH_TW_RATIO_THRESHOLD and not has_autonomy_warning:
            add(
                Suggestion(
                    type="increase_payload",
                    reason="La relación empuje/peso sugiere capacidad adicional disponible.",
                    expected_effect="reduces margin",
                    priority=0.8,
                )
            )

        if self._per_motor_load_ratio(calculations) > HIGH_MOTOR_LOAD_THRESHOLD:
            add(
                Suggestion(
                    type="increase_thrust",
                    reason="La carga por motor está cerca del límite disponible.",
                    expected_effect="improves margin",
                    priority=0.85,
                )
            )

        return suggestions

    def _per_motor_load_ratio(self, calculations: CalculationBundle) -> float:
        if calculations.available_total_thrust_n is None or calculations.motors in (None, 0):
            return 0.0
        max_thrust_per_motor = calculations.available_total_thrust_n / calculations.motors
        if not max_thrust_per_motor:
            return 0.0
        return calculations.thrust_per_motor_required_n / max_thrust_per_motor
