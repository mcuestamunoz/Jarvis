from jarvis.tools.mechanics import (
    calculate_force_per_actuator,
    calculate_required_force,
    calculate_required_thrust,
    calculate_total_mass,
    calculate_thrust_per_motor,
    calculate_traction_force_from_torque,
    calculate_weight,
    estimate_structure_mass,
)


def test_mechanics_chain_is_deterministic():
    structure = estimate_structure_mass(payload_kg=2.0, structure_mass_factor=0.6)
    total = calculate_total_mass(payload_kg=2.0, structure_mass_kg=structure.outputs["structure_mass_kg"])
    weight = calculate_weight(total.outputs["total_mass_kg"])
    required = calculate_required_thrust(weight.outputs["weight_n"], safety_factor=1.2)

    assert structure.outputs["structure_mass_kg"] == 1.2
    assert total.outputs["total_mass_kg"] == 3.2
    assert weight.outputs["weight_n"] == 31.392
    assert required.outputs["required_thrust_n"] == 37.6704


def test_calculate_required_force_produces_same_value_as_thrust():
    result = calculate_required_force(weight_n=31.392, safety_factor=1.2)
    assert result.outputs["required_force_n"] == 37.6704
    assert result.tool_name == "calculate_required_force"


def test_calculate_required_force_and_thrust_are_numerically_identical():
    thrust = calculate_required_thrust(weight_n=50.0, safety_factor=1.5)
    force = calculate_required_force(weight_n=50.0, safety_factor=1.5)
    assert force.outputs["required_force_n"] == thrust.outputs["required_thrust_n"]


def test_calculate_force_per_actuator_produces_same_value_as_thrust_per_motor():
    per_motor = calculate_thrust_per_motor(required_thrust_n=40.0, motors=4)
    per_actuator = calculate_force_per_actuator(required_force_n=40.0, actuator_count=4)
    assert per_actuator.outputs["force_per_actuator_required_n"] == per_motor.outputs["thrust_per_motor_required_n"]
    assert per_actuator.tool_name == "calculate_force_per_actuator"


def test_calculate_force_per_actuator_divides_correctly():
    result = calculate_force_per_actuator(required_force_n=60.0, actuator_count=3)
    assert result.outputs["force_per_actuator_required_n"] == 20.0


# ── Ground domain: traction force from torque ──────────────────────────────

def test_calculate_traction_force_from_torque_basic():
    """F = (torque * gear_ratio) / wheel_radius"""
    result = calculate_traction_force_from_torque(torque_nm=50.0, wheel_radius_m=0.1, gear_ratio=10.0)
    assert result.tool_name == "calculate_traction_force_from_torque"
    assert result.outputs["traction_force_n"] == 5000.0


def test_calculate_traction_force_from_torque_formula_correct():
    """Higher gear_ratio → higher traction force."""
    low = calculate_traction_force_from_torque(torque_nm=30.0, wheel_radius_m=0.15, gear_ratio=5.0)
    high = calculate_traction_force_from_torque(torque_nm=30.0, wheel_radius_m=0.15, gear_ratio=10.0)
    assert high.outputs["traction_force_n"] == 2 * low.outputs["traction_force_n"]


def test_calculate_traction_force_from_torque_unit_gear_ratio():
    """gear_ratio=1 → F = torque / radius."""
    result = calculate_traction_force_from_torque(torque_nm=20.0, wheel_radius_m=0.25, gear_ratio=1.0)
    assert result.outputs["traction_force_n"] == round(20.0 / 0.25, 4)


def test_calculate_traction_force_from_torque_preserves_inputs():
    result = calculate_traction_force_from_torque(torque_nm=40.0, wheel_radius_m=0.2, gear_ratio=8.0)
    assert result.inputs == {"torque_nm": 40.0, "wheel_radius_m": 0.2, "gear_ratio": 8.0}
