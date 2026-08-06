"""Tests for CalculationEngine — covers aerial and ground domain paths."""
import pytest

from jarvis.core.calculation_engine import CalculationEngine


_BASE = {
    "vehicle_type": "aerial",
    "payload_kg": 2.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
    "motor_count": 4,
    "per_motor_max_thrust_n": 15.0,
}


# ── Aerial path (existing behaviour) ─────────────────────────────────────────

def test_aerial_build_nominal():
    bundle = CalculationEngine().build(_BASE)
    assert bundle.motors == 4
    assert bundle.available_total_thrust_n == 60.0
    assert bundle.required_thrust_n == pytest.approx(37.6704, abs=0.01)


def test_aerial_build_uses_max_force_per_actuator_n_alias():
    params = {**_BASE}
    del params["per_motor_max_thrust_n"]
    params["max_force_per_actuator_n"] = 15.0
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n == 60.0


def test_aerial_build_uses_actuator_count_alias():
    params = {**_BASE}
    del params["motor_count"]
    params["actuator_count"] = 4
    bundle = CalculationEngine().build(params)
    assert bundle.motors == 4


# ── Ground path — torque → force ─────────────────────────────────────────────

_BASE_GROUND = {
    "vehicle_type": "ground",
    "payload_kg": 50.0,
    "structure_mass_factor": 0.3,
    "safety_factor": 1.5,
    "motor_count": 4,
    # no per_motor_max_thrust_n → ground path
    "per_actuator_torque_nm": 80.0,
    "wheel_radius_m": 0.2,
    "gear_ratio": 10.0,
}


def test_ground_build_converts_torque_to_traction_force():
    """Engine converts torque_nm via traction formula and sets available_total_thrust_n."""
    # F = (80 * 10) / 0.2 = 4000.0 N per actuator
    bundle = CalculationEngine().build(_BASE_GROUND)
    assert bundle.available_total_thrust_n == pytest.approx(4 * 4000.0)


def test_ground_build_adds_traction_tool_result():
    bundle = CalculationEngine().build(_BASE_GROUND)
    tool_names = [r.tool_name for r in bundle.tool_results]
    assert "calculate_traction_force_from_torque" in tool_names


def test_ground_build_missing_wheel_radius_traces_error():
    """When wheel_radius_m missing, available_total_thrust_n is None and trace logged."""
    params = {**_BASE_GROUND}
    del params["wheel_radius_m"]
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is None
    tool_names = [r.tool_name for r in bundle.tool_results]
    assert "missing_transmission_parameters" in tool_names


def test_ground_build_missing_gear_ratio_traces_error():
    """When gear_ratio missing, available_total_thrust_n is None and trace logged."""
    params = {**_BASE_GROUND}
    del params["gear_ratio"]
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is None
    tool_names = [r.tool_name for r in bundle.tool_results]
    assert "missing_transmission_parameters" in tool_names


def test_ground_build_missing_transmission_trace_contains_inputs():
    params = {**_BASE_GROUND}
    del params["wheel_radius_m"]
    bundle = CalculationEngine().build(params)
    missing = next(r for r in bundle.tool_results if r.tool_name == "missing_transmission_parameters")
    assert missing.inputs["per_actuator_torque_nm"] == 80.0


def test_aerial_path_takes_priority_over_torque_when_both_present():
    """If per_motor_max_thrust_n AND per_actuator_torque_nm are both present, thrust wins."""
    params = {**_BASE_GROUND, "per_motor_max_thrust_n": 20.0}
    bundle = CalculationEngine().build(params)
    # Uses 4 * 20.0 = 80, not 4 * 4000
    assert bundle.available_total_thrust_n == 80.0


# ── None-safe paths (motors and/or thrust absent) ────────────────────────────

def test_aerial_no_thrust_no_propeller_emits_missing_propulsion_reason():
    """Aerial vehicle with no thrust source emits missing_propulsion_parameters reason code."""
    params = {
        "vehicle_type": "dron",
        "payload_kg": 2.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
        # no motors, no per_motor_max_thrust_n, no propeller geometry
    }
    bundle = CalculationEngine().build(params)
    tool_names = [r.tool_name for r in bundle.tool_results]
    assert "missing_propulsion_parameters" in tool_names
    assert "missing_transmission_parameters" not in tool_names


def test_ground_no_torque_emits_missing_transmission_reason():
    """Ground vehicle with no torque/thrust emits missing_transmission_parameters reason code."""
    params = {
        "vehicle_type": "robot",
        "payload_kg": 50.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
        # no torque, no direct thrust
    }
    bundle = CalculationEngine().build(params)
    tool_names = [r.tool_name for r in bundle.tool_results]
    assert "missing_transmission_parameters" in tool_names
    assert "missing_propulsion_parameters" not in tool_names



    """No motors, no thrust declared, no propeller → available_total_thrust_n=None."""
    params = {
        "vehicle_type": "dron",
        "payload_kg": 2.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
        # motors absent, per_motor_max_thrust_n absent
    }
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is None
    assert bundle.motors is None


def test_motors_present_no_thrust_produces_none_available():
    """motors declared but no thrust source → available_total_thrust_n=None."""
    params = {
        "vehicle_type": "dron",
        "payload_kg": 2.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
        "motor_count": 4,
    }
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is None
    assert bundle.motors == 4


def test_no_motors_with_thrust_produces_none_available():
    """per_motor_max_thrust_n declared but no motors → available_total_thrust_n=None."""
    params = {
        "vehicle_type": "dron",
        "payload_kg": 2.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
        "per_motor_max_thrust_n": 15.0,
        # motors absent
    }
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is None
    assert bundle.motors is None


def test_create_project_without_thrust_no_fictitious_simulation(tmp_path):
    """Project created without per_motor_max_thrust_n must NOT simulate with 15N fictitious value."""
    from jarvis.core.orchestrator import JarvisOrchestrator
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba sin thrust",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
            # per_motor_max_thrust_n deliberately absent
        },
    })
    sim = result["simulation"]
    assert sim["physics_status"] == "missing_parameters"
    assert result["calculations"]["available_total_thrust_n"] is None
