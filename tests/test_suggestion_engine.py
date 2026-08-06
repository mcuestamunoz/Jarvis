from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult
from jarvis.suggestions.suggestion_engine import SuggestionEngine


def _build_calculations(
    *,
    weight_n: float = 30.0,
    required_thrust_n: float = 36.0,
    thrust_per_motor_required_n: float = 9.0,
    available_total_thrust_n: float = 80.0,
    motors: int = 4,
) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="dron",
        payload_kg=2.0,
        structure_mass_kg=1.0,
        total_mass_kg=3.0,
        weight_n=weight_n,
        required_thrust_n=required_thrust_n,
        motors=motors,
        thrust_per_motor_required_n=thrust_per_motor_required_n,
        available_total_thrust_n=available_total_thrust_n,
        tool_results=[],
    )


def _build_simulation(
    *,
    safety_margin_ratio: float,
    thrust_to_weight_ratio: float,
    warnings: list[str] | None = None,
) -> SimulationResult:
    return SimulationResult(
        status="pass" if safety_margin_ratio >= 1.0 else "fail",
        can_fly=safety_margin_ratio >= 1.0,
        quality="good",
        safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=thrust_to_weight_ratio,
        warnings=warnings or [],
        analysis=SimulationAnalysis(
            available_thrust_n=80.0,
            required_thrust_n=36.0,
            weight_n=30.0,
            per_motor_load_ratio=0.45,
        ),
        summary="summary",
    )


def test_high_margin_generates_payload_and_efficiency_suggestions():
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(safety_margin_ratio=2.0, thrust_to_weight_ratio=2.2),
        _build_calculations(),
    )

    suggestion_types = {suggestion.type for suggestion in suggestions}
    assert "increase_payload" in suggestion_types
    assert "improve_efficiency" in suggestion_types


def test_low_margin_generates_reduce_weight_suggestion():
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(safety_margin_ratio=1.2, thrust_to_weight_ratio=1.25, warnings=["low_margin"]),
        _build_calculations(available_total_thrust_n=45.0, required_thrust_n=37.5, thrust_per_motor_required_n=9.375),
    )

    assert any(suggestion.type == "reduce_weight" for suggestion in suggestions)


def test_high_motor_load_generates_increase_thrust_suggestion():
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(safety_margin_ratio=1.4, thrust_to_weight_ratio=1.5, warnings=["high_motor_load"]),
        _build_calculations(available_total_thrust_n=40.0, required_thrust_n=36.0, thrust_per_motor_required_n=9.5),
    )

    assert any(suggestion.type == "increase_thrust" for suggestion in suggestions)


def test_returns_empty_when_no_clear_suggestion_exists():
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(safety_margin_ratio=1.5, thrust_to_weight_ratio=1.45),
        _build_calculations(available_total_thrust_n=50.0, required_thrust_n=33.0, thrust_per_motor_required_n=8.25),
    )

    assert suggestions == []


def test_autonomy_warning_suppresses_increase_payload():
    """High margin does NOT generate increase_payload when autonomy_below_restriction is active."""
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(
            safety_margin_ratio=2.2,
            thrust_to_weight_ratio=2.5,
            warnings=["autonomy_below_restriction"],
        ),
        _build_calculations(),
    )

    suggestion_types = {s.type for s in suggestions}
    assert "increase_payload" not in suggestion_types


def test_autonomy_warning_generates_improve_autonomy_with_max_priority():
    """autonomy_below_restriction emits improve_autonomy with priority=1.0."""
    engine = SuggestionEngine()

    suggestions = engine.generate_suggestions(
        _build_simulation(
            safety_margin_ratio=2.2,
            thrust_to_weight_ratio=2.5,
            warnings=["autonomy_below_restriction"],
        ),
        _build_calculations(),
    )

    autonomy_suggestions = [s for s in suggestions if s.type == "improve_autonomy"]
    assert len(autonomy_suggestions) == 1
    assert autonomy_suggestions[0].priority == 1.0
