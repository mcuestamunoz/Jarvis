"""Tests for aerodynamics domain: propeller thrust inference.

Covers:
- calculate_thrust_from_propeller tool (formula + edge cases)
- CalculationEngine: propeller path (inferred) vs direct thrust (declared)
- FeasibilitySimulator: propeller_thrust_inferred flag propagation
- ReasoningLayer: propeller_thrust_inferred signal, insight, tradeoff
"""
from __future__ import annotations

import math

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.simulation.simulator import FeasibilitySimulator
from jarvis.tools.aerodynamics import calculate_thrust_from_propeller


# ── helpers ───────────────────────────────────────────────────────────────────

_BASE_PARAMS_NO_THRUST = {
    "vehicle_type": "dron",
    "objective": "dron de carga",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motor_count": 4,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
    # no per_motor_max_thrust_n, no torque params
}

_BASE_PARAMS_DIRECT_THRUST = {
    **_BASE_PARAMS_NO_THRUST,
    "per_motor_max_thrust_n": 15.0,
}

# 10 inch propeller (≈ 0.254 m) at 8000 RPM — typical for 2 kg UAV class
_PROPELLER_DIAMETER_M = 0.254
_PROPELLER_RPM = 8000.0


# ── calculate_thrust_from_propeller ──────────────────────────────────────────

def test_calculate_thrust_from_propeller_formula():
    """T = ct * rho * (rpm/60)^2 * D^4"""
    ct, rho, rpm, d = 0.12, 1.225, 8000.0, 0.254
    expected = ct * rho * (rpm / 60.0) ** 2 * (d ** 4)
    result = calculate_thrust_from_propeller(diameter_m=d, rpm=rpm)
    assert result.tool_name == "calculate_thrust_from_propeller"
    assert result.outputs["thrust_n"] == pytest.approx(expected, rel=1e-5)


def test_calculate_thrust_from_propeller_custom_ct():
    """Custom ct overrides default 0.12."""
    r1 = calculate_thrust_from_propeller(diameter_m=0.254, rpm=8000.0, ct=0.12)
    r2 = calculate_thrust_from_propeller(diameter_m=0.254, rpm=8000.0, ct=0.16)
    assert r2.outputs["thrust_n"] == pytest.approx(r1.outputs["thrust_n"] * (0.16 / 0.12), rel=1e-5)


def test_calculate_thrust_from_propeller_custom_air_density():
    """Custom air_density scales thrust proportionally."""
    r1 = calculate_thrust_from_propeller(diameter_m=0.254, rpm=8000.0, air_density=1.225)
    r2 = calculate_thrust_from_propeller(diameter_m=0.254, rpm=8000.0, air_density=1.0)
    ratio = r2.outputs["thrust_n"] / r1.outputs["thrust_n"]
    assert ratio == pytest.approx(1.0 / 1.225, rel=1e-5)


def test_calculate_thrust_from_propeller_inputs_recorded():
    """Tool records all inputs for traceability."""
    result = calculate_thrust_from_propeller(diameter_m=0.3, rpm=5000.0, ct=0.14, air_density=1.1)
    assert result.inputs["diameter_m"] == 0.3
    assert result.inputs["rpm"] == 5000.0
    assert result.inputs["ct"] == 0.14
    assert result.inputs["air_density"] == 1.1


def test_calculate_thrust_from_propeller_zero_rpm_zero_thrust():
    result = calculate_thrust_from_propeller(diameter_m=0.254, rpm=0.0)
    assert result.outputs["thrust_n"] == pytest.approx(0.0)


# ── CalculationEngine — propeller inference path ─────────────────────────────

def test_engine_propeller_path_produces_thrust():
    """Engine infers per_motor thrust from propeller geometry when no direct thrust declared."""
    engine = CalculationEngine()
    params = {
        **_BASE_PARAMS_NO_THRUST,
        "propeller_diameter_m": _PROPELLER_DIAMETER_M,
        "propeller_rpm": _PROPELLER_RPM,
    }
    bundle = engine.build(params)
    assert bundle.available_total_thrust_n is not None
    assert bundle.available_total_thrust_n > 0.0
    # Verify tool trace contains propeller result
    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert "calculate_thrust_from_propeller" in tool_names


def test_engine_propeller_path_not_used_when_direct_thrust_declared():
    """When per_motor_max_thrust_n is present, propeller params are ignored."""
    engine = CalculationEngine()
    params = {
        **_BASE_PARAMS_DIRECT_THRUST,
        "propeller_diameter_m": _PROPELLER_DIAMETER_M,
        "propeller_rpm": _PROPELLER_RPM,
    }
    bundle = engine.build(params)
    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert "calculate_thrust_from_propeller" not in tool_names
    # Thrust should come from declared value, not propeller model
    expected_total = 15.0 * 4
    assert bundle.available_total_thrust_n == pytest.approx(expected_total)


def test_engine_propeller_custom_ct_propagates():
    """Engine passes propeller_ct override to calculate_thrust_from_propeller."""
    engine = CalculationEngine()
    base_params = {
        **_BASE_PARAMS_NO_THRUST,
        "propeller_diameter_m": _PROPELLER_DIAMETER_M,
        "propeller_rpm": _PROPELLER_RPM,
    }
    bundle_default = engine.build(base_params)
    bundle_custom = engine.build({**base_params, "propeller_ct": 0.16})

    thrust_default = bundle_default.available_total_thrust_n
    thrust_custom = bundle_custom.available_total_thrust_n
    assert thrust_custom == pytest.approx(thrust_default * (0.16 / 0.12), rel=1e-4)


def test_engine_no_propeller_params_still_missing():
    """No direct thrust AND no propeller params → available_total_thrust_n stays None."""
    engine = CalculationEngine()
    bundle = engine.build(_BASE_PARAMS_NO_THRUST)
    assert bundle.available_total_thrust_n is None


# ── FeasibilitySimulator — propeller_thrust_inferred flag ────────────────────

def test_simulator_propeller_thrust_inferred_flag_set():
    """SimulationResult.propeller_thrust_inferred=True when propeller path used."""
    engine = CalculationEngine()
    simulator = FeasibilitySimulator()
    params = {
        **_BASE_PARAMS_NO_THRUST,
        "propeller_diameter_m": _PROPELLER_DIAMETER_M,
        "propeller_rpm": _PROPELLER_RPM,
    }
    bundle = engine.build(params)
    result = simulator.evaluate(bundle)
    assert result.propeller_thrust_inferred is True


def test_simulator_propeller_flag_false_with_direct_thrust():
    """propeller_thrust_inferred=False when thrust declared explicitly."""
    engine = CalculationEngine()
    simulator = FeasibilitySimulator()
    bundle = engine.build(_BASE_PARAMS_DIRECT_THRUST)
    result = simulator.evaluate(bundle)
    assert result.propeller_thrust_inferred is False


def test_simulator_propeller_flag_false_with_no_thrust():
    """propeller_thrust_inferred=False when there is no thrust at all (missing params)."""
    engine = CalculationEngine()
    simulator = FeasibilitySimulator()
    bundle = engine.build(_BASE_PARAMS_NO_THRUST)
    result = simulator.evaluate(bundle)
    assert result.propeller_thrust_inferred is False


# ── ReasoningLayer — propeller_thrust_inferred signal ────────────────────────

def _make_simulation_ctx(propeller_thrust_inferred: bool = False) -> dict:
    return {
        "last_simulation": {
            "physics_status": "valid",
            "energy_status": "valid",
            "safety_margin_ratio": 1.5,
            "thrust_to_weight_ratio": 2.0,
            "warnings": [],
            "propeller_thrust_inferred": propeller_thrust_inferred,
        },
        "design_properties": {},
        "current_parameters": {
            "propeller_diameter_m": _PROPELLER_DIAMETER_M,
            "propeller_rpm": _PROPELLER_RPM,
        },
    }


def test_reasoning_propeller_inferred_signal_true():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=True))
    assert output.signals.get("propeller_thrust_inferred") is True


def test_reasoning_propeller_inferred_signal_false():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=False))
    assert output.signals.get("propeller_thrust_inferred") is False


def test_reasoning_propeller_inferred_insight_present():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=True))
    assert any("hélice" in insight for insight in output.insights)


def test_reasoning_propeller_inferred_insight_absent_when_not_inferred():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=False))
    assert not any("hélice" in insight and "estimado" in insight for insight in output.insights)


def test_reasoning_propeller_inferred_tradeoff_present():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=True))
    assert any("Ct=0.12" in t for t in output.tradeoffs)


def test_reasoning_propeller_inferred_tradeoff_absent_when_not_inferred():
    layer = ReasoningLayer()
    output = layer.build(_make_simulation_ctx(propeller_thrust_inferred=False))
    assert not any("Ct=0.12" in t for t in output.tradeoffs)
