"""Tests for domains/ground.py and cross-domain validation.

Test categories:
  1. extract_wheel_actuator_properties — torque, rpm, count
  2. extract_wheel_properties — passive wheel count
  3. ground_registry — keyword matching
  4. Registry isolation — ground vs aerial don't bleed into each other
  5. Cross-domain disambiguation — same text, different registry → different meaning
  6. Resolver integration — traction_active components are now eligible
  7. Calculation engine integration — ground vehicle via actuator_count
  8. Semantic stress test — can_fly is wrong for ground (Phase 4 trigger)
"""
from __future__ import annotations

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_inference import infer_component
from jarvis.core.component_resolver import resolve_propulsion_parameters
from jarvis.domains.aerial import aerial_registry
from jarvis.domains.ground import (
    extract_wheel_actuator_properties,
    extract_wheel_properties,
    ground_registry,
)
from jarvis.schemas.tool_schema import CalculationBundle
from jarvis.simulation.simulator import FeasibilitySimulator


# ── 1. extract_wheel_actuator_properties ────────────────────────────────────

def test_wheel_actuator_extracts_torque_nm():
    props = extract_wheel_actuator_properties("motor 50nm")
    assert "torque_nm" in props
    assert props["torque_nm"].value == 50.0
    assert props["torque_nm"].unit == "Nm"


def test_wheel_actuator_extracts_torque_with_space():
    props = extract_wheel_actuator_properties("motor 120 nm")
    assert "torque_nm" in props
    assert props["torque_nm"].value == 120.0


def test_wheel_actuator_extracts_rpm():
    props = extract_wheel_actuator_properties("motor 1500rpm")
    assert "rpm" in props
    assert props["rpm"].value == 1500.0
    assert props["rpm"].unit == "rpm"


def test_wheel_actuator_extracts_motor_count_from_motores_pattern():
    props = extract_wheel_actuator_properties("4 motores 50nm")
    assert "motor_count" in props
    assert props["motor_count"].value == 4


def test_wheel_actuator_extracts_motor_count_from_4x_pattern():
    props = extract_wheel_actuator_properties("4x motor 50nm")
    assert "motor_count" in props
    assert props["motor_count"].value == 4


def test_wheel_actuator_extracts_count_from_ruedas_motrices():
    props = extract_wheel_actuator_properties("2 ruedas motrices 80nm")
    assert "motor_count" in props
    assert props["motor_count"].value == 2


def test_wheel_actuator_does_not_confuse_torque_nm_with_aerial_thrust_n():
    """50Nm must NOT be extracted as thrust_n — different unit, different physics."""
    props = extract_wheel_actuator_properties("motor 50nm")
    assert "torque_nm" in props
    # If extracted via aerial extractor, value would appear as thrust_n — verify it's clean
    assert "thrust_n" not in props


def test_wheel_actuator_returns_empty_for_unrelated_input():
    props = extract_wheel_actuator_properties("bateria lifepo4 100ah")
    assert props == {}


def test_wheel_actuator_confidence_values_are_positive():
    props = extract_wheel_actuator_properties("4 motores 50nm 1200rpm")
    for key, pv in props.items():
        assert pv.confidence > 0.0, f"confidence must be > 0 for {key}"


# ── 2. extract_wheel_properties ──────────────────────────────────────────────

def test_wheel_extracts_count():
    props = extract_wheel_properties("4 ruedas")
    assert "wheel_count" in props
    assert props["wheel_count"].value == 4


def test_wheel_extracts_count_english():
    props = extract_wheel_properties("6 wheels")
    assert "wheel_count" in props
    assert props["wheel_count"].value == 6


def test_wheel_returns_empty_without_count_pattern():
    props = extract_wheel_properties("ruedas de caucho")
    assert "wheel_count" not in props


# ── 3. ground_registry keyword matching ──────────────────────────────────────

def test_ground_registry_matches_motor_keyword():
    rule = ground_registry.match("motor 50nm", "motor")
    assert rule is not None
    assert rule.component_type == "traction_active"


def test_ground_registry_matches_par_keyword():
    rule = ground_registry.match("par 80nm", "par")
    assert rule is not None
    assert rule.component_type == "traction_active"


def test_ground_registry_matches_torque_keyword():
    rule = ground_registry.match("torque 50nm", "torque")
    assert rule is not None
    assert rule.component_type == "traction_active"


def test_ground_registry_matches_traccion_keyword():
    rule = ground_registry.match("tracción 4x4", "tracción")
    assert rule is not None
    assert rule.component_type == "traction_active"


def test_ground_registry_matches_rueda_keyword():
    rule = ground_registry.match("4 ruedas", "rueda")
    assert rule is not None
    assert rule.component_type == "rolling_passive"


def test_ground_registry_matches_wheel_keyword():
    rule = ground_registry.match("6 wheels", "wheel")
    assert rule is not None
    assert rule.component_type == "rolling_passive"


def test_ground_registry_returns_none_for_unknown_component():
    rule = ground_registry.match("bateria lifepo4 100ah", "bateria")
    assert rule is None


def test_ground_registry_has_two_rules():
    assert len(ground_registry) == 2


# ── 4. Registry isolation ─────────────────────────────────────────────────────

def test_aerial_registry_does_not_match_ground_specific_keywords():
    """Ground-only keywords (par, torque, traccion, rueda) are not in aerial_registry."""
    assert aerial_registry.match("par 80nm", "par") is None
    assert aerial_registry.match("torque 50nm", "torque") is None
    assert aerial_registry.match("traccion 4wd", "traccion") is None
    assert aerial_registry.match("4 ruedas", "rueda") is None


def test_ground_registry_does_not_match_aerial_specific_keywords():
    """Aerial-only keywords (helice, esc, kv) are not in ground_registry."""
    assert ground_registry.match("helice 10x4.5", "helice") is None
    assert ground_registry.match("esc 30a", "esc") is None
    # "kv" is not a ground keyword — it only appears alongside "motor" in aerial context


# ── 5. Cross-domain disambiguation ───────────────────────────────────────────

def test_same_motor_text_different_registry_different_component_type():
    """
    CRITICAL: same keyword 'motor' means different things in different domains.
    The registry is the domain boundary — not the text itself.
    """
    aerial_result = infer_component("4 motores", registry=aerial_registry)
    ground_result = infer_component("4 motores", registry=ground_registry)

    assert aerial_result.component_type == "propulsion_active"
    assert ground_result.component_type == "traction_active"
    # Same input text, different domain → completely different component types
    assert aerial_result.component_type != ground_result.component_type


def test_specific_aerial_description_stays_aerial():
    aerial_result = infer_component("4x 920KV motor", registry=aerial_registry)
    assert aerial_result.component_type == "propulsion_active"
    assert aerial_result.properties.get("kv_rating") is not None


def test_specific_ground_description_stays_ground():
    ground_result = infer_component("4 motores 50Nm 1200rpm", registry=ground_registry)
    assert ground_result.component_type == "traction_active"
    assert ground_result.properties.get("torque_nm") is not None
    assert ground_result.properties.get("rpm") is not None


# ── 6. Resolver integration — traction_active now eligible ───────────────────

def _ground_component_entry(motor_count: int, torque_nm: float | None = None) -> dict:
    """Build a minimal component entry as stored in design_properties.components."""
    properties = {
        "motor_count": {"value": motor_count, "unit": None, "confidence": 0.9, "source": "declared"},
    }
    if torque_nm is not None:
        properties["torque_nm"] = {"value": torque_nm, "unit": "Nm", "confidence": 0.9, "source": "declared"}
    completeness = "high" if torque_nm else "medium"
    return {
        "component_type": "traction_active",
        "completeness": completeness,
        "properties": properties,
    }


def test_resolver_recognizes_traction_active_as_eligible():
    components = {"drive_motors": _ground_component_entry(motor_count=4, torque_nm=50.0)}
    override = resolve_propulsion_parameters(components)
    assert override.motors is not None
    assert override.motors == 4


def test_resolver_extracts_motor_count_from_traction_active():
    components = {"motors": _ground_component_entry(motor_count=2)}
    override = resolve_propulsion_parameters(components)
    assert override.actuator_count == 2


def test_resolver_does_not_extract_force_from_torque():
    """
    Ground motors have torque_nm, not thrust_n.
    The resolver correctly returns per_motor_max_thrust_n=None for ground components.
    Converting torque → traction force requires wheel_radius + gear_ratio (future work).
    """
    components = {"motors": _ground_component_entry(motor_count=4, torque_nm=80.0)}
    override = resolve_propulsion_parameters(components)
    assert override.motors == 4
    assert override.per_motor_max_thrust_n is None  # not resolved — by design


# ── 7. Calculation engine integration ────────────────────────────────────────

def test_calculation_engine_accepts_ground_vocabulary():
    """
    Ground vehicle: 4 wheel actuators, each capable of 5000N traction force.
    Parameters use generic names (actuator_count, max_force_per_actuator_n).
    max_force_per_actuator_n is provided explicitly — not auto-extracted from torque.
    """
    parameters = {
        "vehicle_type": "ground_rover",
        "payload_kg": 100.0,
        "structure_mass_factor": 0.4,
        "safety_factor": 1.3,
        "actuator_count": 4,
        "max_force_per_actuator_n": 500.0,
    }
    bundle = CalculationEngine().build(parameters)

    assert bundle.actuator_count == 4
    assert bundle.available_total_force_n == 2000.0
    assert bundle.required_force_n > 0.0


def test_ground_vehicle_feasibility_check():
    parameters = {
        "vehicle_type": "ground_rover",
        "payload_kg": 50.0,
        "structure_mass_factor": 0.3,
        "safety_factor": 1.2,
        "actuator_count": 2,
        "max_force_per_actuator_n": 800.0,
    }
    bundle = CalculationEngine().build(parameters)
    result = FeasibilitySimulator().evaluate(bundle)

    assert result.constraints_satisfied is True
    assert result.safety_margin_ratio >= 1.0


# ── 8. Semantic stress test — Phase 4 trigger ────────────────────────────────

def test_can_fly_is_semantically_wrong_for_ground_vehicle():
    """
    PHASE 4 TRIGGER TEST.

    A functional ground vehicle has constraints_satisfied=True (via generic alias).
    The raw field can_fly=True is numerically correct but semantically absurd for a car.

    This test intentionally reads BOTH fields and asserts they are identical.

    When a real caller of ground domain results reads result.can_fly and it causes
    confusion or a bug, that is the signal that Phase 4 (renaming can_fly to
    constraints_satisfied as the primary field) is mandatory — not optional.

    Until then, use result.constraints_satisfied in all new domain-agnostic code.
    """
    calculations = CalculationBundle(
        vehicle_type="ground_vehicle",
        payload_kg=500.0,
        structure_mass_kg=200.0,
        total_mass_kg=700.0,
        weight_n=6867.0,
        required_thrust_n=8240.4,
        motors=4,
        thrust_per_motor_required_n=2060.1,
        available_total_thrust_n=20000.0,
        tool_results=[],
    )
    result = FeasibilitySimulator().evaluate(calculations)

    # The ground vehicle is feasible — this is correct
    assert result.constraints_satisfied is True

    # can_fly is the same value — but the NAME is semantically wrong for a car
    assert result.can_fly is True  # a car does not "fly"

    # Both aliases are always identical — the problem is naming, not logic
    assert result.can_fly == result.constraints_satisfied

    # OBSERVATION: any caller of ground domain results should use
    # result.constraints_satisfied, NOT result.can_fly
    # If can_fly bleeds into ground-domain reports or logs, complete Phase 4.
