from jarvis.schemas.tool_schema import CalculationBundle
from jarvis.simulation.simulator import FlightSimulator


def _build_calculations(
    *,
    weight_n: float,
    required_thrust_n: float,
    motors: int = 4,
    thrust_per_motor_required_n: float | None = None,
    available_total_thrust_n: float,
) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="drone",
        payload_kg=2.0,
        structure_mass_kg=1.2,
        total_mass_kg=3.2,
        weight_n=weight_n,
        required_thrust_n=required_thrust_n,
        motors=motors,
        thrust_per_motor_required_n=thrust_per_motor_required_n or (required_thrust_n / motors),
        available_total_thrust_n=available_total_thrust_n,
        tool_results=[],
    )


def test_fail_condition():
    calculations = _build_calculations(
        weight_n=31.392,
        required_thrust_n=37.6704,
        available_total_thrust_n=30.0,
    )

    result = FlightSimulator().evaluate(calculations)

    assert result.can_fly is False
    assert result.status == "fail"
    assert result.quality == "fail"
    assert result.safety_margin_ratio < 1.0


def test_risky_margin():
    calculations = _build_calculations(
        weight_n=40.0,
        required_thrust_n=44.0,
        available_total_thrust_n=46.2,
    )

    result = FlightSimulator().evaluate(calculations)

    assert result.can_fly is True
    assert result.status == "pass"
    assert result.quality == "risky"
    assert result.safety_margin_ratio == 1.05
    assert "low_margin" in result.warnings
    assert "low_force_to_weight_ratio" in result.warnings


def test_good_quality():
    calculations = _build_calculations(
        weight_n=30.0,
        required_thrust_n=33.0,
        available_total_thrust_n=45.0,
    )

    result = FlightSimulator().evaluate(calculations)

    assert result.can_fly is True
    assert result.status == "pass"
    assert result.quality == "good"
    assert result.safety_margin_ratio > 1.3
    assert result.warnings == []


def test_high_motor_load_warning():
    calculations = _build_calculations(
        weight_n=30.0,
        required_thrust_n=42.0,
        thrust_per_motor_required_n=10.5,
        available_total_thrust_n=44.0,
    )

    result = FlightSimulator().evaluate(calculations)

    assert result.can_fly is True
    assert "high_actuator_load" in result.warnings
    assert result.analysis.per_motor_load_ratio > 0.9


def test_consistency():
    calculations = _build_calculations(
        weight_n=31.392,
        required_thrust_n=37.6704,
        available_total_thrust_n=60.0,
    )

    result = FlightSimulator().evaluate(calculations)

    assert result.can_fly is True
    assert result.status == "pass"
    assert result.quality == "good"
    assert result.safety_margin_ratio >= 1.0
    assert result.status == ("pass" if result.can_fly else "fail")


# ── physics_status: normal path ───────────────────────────────────────────────

def test_normal_evaluation_has_valid_physics_status():
    calculations = _build_calculations(
        weight_n=30.0,
        required_thrust_n=33.0,
        available_total_thrust_n=45.0,
    )
    result = FlightSimulator().evaluate(calculations)
    assert result.physics_status == "valid"


# ── physics_status: missing_parameters path ───────────────────────────────────

def _build_calculations_no_force(*, weight_n: float, required_thrust_n: float, motors: int = 2) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="ground",
        payload_kg=50.0,
        structure_mass_kg=15.0,
        total_mass_kg=65.0,
        weight_n=weight_n,
        required_thrust_n=required_thrust_n,
        motors=motors,
        thrust_per_motor_required_n=required_thrust_n / motors,
        available_total_thrust_n=None,
        tool_results=[],
    )


def test_missing_parameters_returns_structured_result():
    """Simulator must not crash when available_total_thrust_n is None."""
    calculations = _build_calculations_no_force(weight_n=637.65, required_thrust_n=956.475)
    result = FlightSimulator().evaluate(calculations)

    assert result.physics_status == "missing_parameters"
    assert result.can_fly is False
    assert result.status == "fail"
    assert result.quality == "fail"
    assert "missing_transmission_parameters" in result.warnings


def test_missing_parameters_analysis_has_none_available_thrust():
    calculations = _build_calculations_no_force(weight_n=637.65, required_thrust_n=956.475)
    result = FlightSimulator().evaluate(calculations)
    assert result.analysis.available_thrust_n is None
    assert result.analysis.required_thrust_n == 956.475


def test_missing_parameters_has_descriptive_summary():
    calculations = _build_calculations_no_force(weight_n=637.65, required_thrust_n=956.475)
    result = FlightSimulator().evaluate(calculations)
    assert "transmisión" in result.summary or "transmission" in result.summary.lower()


def test_missing_parameters_ratios_are_zero():
    calculations = _build_calculations_no_force(weight_n=637.65, required_thrust_n=956.475)
    result = FlightSimulator().evaluate(calculations)
    assert result.safety_margin_ratio == 0.0
    assert result.thrust_to_weight_ratio == 0.0


# ── physics_status: domain-specific warning codes ─────────────────────────────

def _build_calculations_aerial_no_force() -> CalculationBundle:
    """Aerial vehicle with no force resolution — missing_propulsion_parameters tool result."""
    from jarvis.schemas.tool_schema import ToolResult
    return CalculationBundle(
        vehicle_type="dron",
        payload_kg=2.0,
        structure_mass_kg=1.2,
        total_mass_kg=3.2,
        weight_n=31.392,
        required_thrust_n=37.6704,
        motors=None,
        thrust_per_motor_required_n=None,
        available_total_thrust_n=None,
        tool_results=[
            ToolResult(
                tool_name="missing_propulsion_parameters",
                inputs={"vehicle_type": "dron", "motors": None},
                outputs={"reason": "no force resolution path"},
            )
        ],
    )


def test_aerial_missing_parameters_warning_is_propulsion():
    """When tool_results contains missing_propulsion_parameters, simulator emits that warning."""
    result = FlightSimulator().evaluate(_build_calculations_aerial_no_force())
    assert result.physics_status == "missing_parameters"
    assert "missing_propulsion_parameters" in result.warnings
    assert "missing_transmission_parameters" not in result.warnings


def test_aerial_missing_parameters_summary_mentions_propulsion():
    result = FlightSimulator().evaluate(_build_calculations_aerial_no_force())
    assert "propulsión" in result.summary


# ── Bug 48: high_actuator_load must NOT appear when can_fly=False ─────────────

def test_bug48_high_actuator_load_absent_when_cannot_fly():
    """Bug 48: per_motor_load_ratio > threshold but can_fly=False → no high_actuator_load warning."""
    # available < required → can_fly=False; per_motor_load_ratio will be > 1.0
    calculations = _build_calculations(
        weight_n=54.0,
        required_thrust_n=64.0,
        available_total_thrust_n=30.0,  # well below required → can_fly=False
    )
    result = FlightSimulator().evaluate(calculations)
    assert result.can_fly is False
    assert "high_actuator_load" not in result.warnings


def test_bug48_high_actuator_load_present_when_can_fly_and_overloaded():
    """Bug 48 non-regression: high_actuator_load still fires when can_fly=True and ratio > threshold."""
    calculations = _build_calculations(
        weight_n=30.0,
        required_thrust_n=42.0,
        thrust_per_motor_required_n=10.5,
        available_total_thrust_n=44.0,
    )
    result = FlightSimulator().evaluate(calculations)
    assert result.can_fly is True
    assert "high_actuator_load" in result.warnings
