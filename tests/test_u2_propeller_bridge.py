"""Tests para U2 — Bridge propellers → parámetros físicos.

Verifica que:
1. set_propeller_component escribe propeller_pitch_in en current_parameters.
2. set_motor_component escribe motor_kv_rating en current_parameters.
3. set_battery_component escribe battery_cell_count en current_parameters.
4. CalculationEngine deriva RPM a partir de motor_kv_rating + battery_cell_count.
5. E2E: motores 920KV + batería 4S + hélices 15x5 → propeller_status = "valid".
6. Sin KV o sin cells → RPM no se deriva (backward compat).
"""
from __future__ import annotations

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import (
    set_battery_component,
    set_motor_component,
    set_propeller_component,
)
from jarvis.domains.aerial import (
    extract_battery_properties,
    extract_motor_properties,
    extract_propeller_properties,
)
from jarvis.schemas.action_schema import ComponentSpec


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_spec(key: str, component_type: str, props: dict) -> ComponentSpec:
    return ComponentSpec(
        name=key,
        component_type=component_type,
        suggested_key=key,
        inference_confidence=0.9,
        properties=props,
        completeness="medium",
        missing_fields=[],
        source="declared",
    )


def _make_minimal_state(tmp_path):
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "fotografía aérea",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    return orch.state_manager.load_active_project(orch.workspace_manager)


# ── 1. set_propeller_component bridges diameter_in and pitch_in ───────────────

def test_set_propeller_bridges_diameter(tmp_path):
    """'15x5' → propeller_diameter_in = 15.0 en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_propeller_properties("6 hélices 15x5 pulgadas")
    spec = _make_spec("propellers", "propulsion_component", props)

    updated = set_propeller_component(state, spec)

    assert "propeller_diameter_in" in updated.current_parameters
    assert updated.current_parameters["propeller_diameter_in"] == pytest.approx(15.0)


def test_set_propeller_bridges_pitch(tmp_path):
    """'15x5' → propeller_pitch_in = 5.0 en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_propeller_properties("6 hélices 15x5 pulgadas")
    spec = _make_spec("propellers", "propulsion_component", props)

    updated = set_propeller_component(state, spec)

    assert "propeller_pitch_in" in updated.current_parameters
    assert updated.current_parameters["propeller_pitch_in"] == pytest.approx(5.0)


def test_set_propeller_no_pitch_when_not_extracted(tmp_path):
    """Sin especificación NxM, propeller_pitch_in no aparece en current_parameters."""
    state = _make_minimal_state(tmp_path)
    # Descripción sin formato NxM — no extrae pitch
    props = extract_propeller_properties("hélices grandes")
    spec = _make_spec("propellers", "propulsion_component", props)

    updated = set_propeller_component(state, spec)

    assert "propeller_pitch_in" not in updated.current_parameters


# ── 2. set_motor_component bridges kv_rating ─────────────────────────────────

def test_set_motor_bridges_kv_rating(tmp_path):
    """'4x 920KV' → motor_kv_rating = 920.0 en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_motor_properties("4 motores brushless 920KV")
    spec = _make_spec("motors", "motor", props)

    updated = set_motor_component(state, spec, power_w=None)

    assert "motor_kv_rating" in updated.current_parameters
    assert updated.current_parameters["motor_kv_rating"] == pytest.approx(920.0)


def test_set_motor_no_kv_when_not_extracted(tmp_path):
    """Sin KV en descripción, motor_kv_rating no aparece en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_motor_properties("4 motores brushless 45W")
    spec = _make_spec("motors", "motor", props)

    updated = set_motor_component(state, spec, power_w=45.0)

    assert "motor_kv_rating" not in updated.current_parameters


# ── 3. set_battery_component bridges cell_count ───────────────────────────────

def test_set_battery_bridges_cell_count(tmp_path):
    """'4S 8000mAh' → battery_cell_count = 4 en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_battery_properties("batería LiPo 4S 8000mAh")
    spec = _make_spec("battery", "energy_storage", props)
    capacity_wh = float(props["battery_capacity_wh"].value)

    updated = set_battery_component(state, spec, capacity_wh)

    assert "battery_cell_count" in updated.current_parameters
    assert updated.current_parameters["battery_cell_count"] == 4


def test_set_battery_no_cell_count_when_absent(tmp_path):
    """Sin celda declarada, battery_cell_count no aparece en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_battery_properties("batería 100Wh")
    spec = _make_spec("battery", "energy_storage", props)
    capacity_wh = float(props["battery_capacity_wh"].value)

    updated = set_battery_component(state, spec, capacity_wh)

    assert "battery_cell_count" not in updated.current_parameters


# ── 4. CalculationEngine deriva RPM desde KV + cells ─────────────────────────

_BASE_AERIAL = {
    "payload_kg": 1.0,
    "motor_count": 4,
    "vehicle_type": "dron",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def test_engine_derives_rpm_from_kv_and_cells():
    """Con motor_kv_rating=920 y battery_cell_count=4 y diameter → thrust calculado."""
    engine = CalculationEngine()
    params = {
        **_BASE_AERIAL,
        "propeller_diameter_in": 10.0,   # 10 pulgadas
        "motor_kv_rating": 920.0,
        "battery_cell_count": 4,
    }
    bundle = engine.build(params)

    # RPM estimado: 920 * (4*3.7) * 0.85 ≈ 11582 RPM
    # El path de propulsión se resolvió si calculate_thrust_from_propeller está en tool_results
    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert "calculate_thrust_from_propeller" in tool_names
    # El empuje total disponible debe ser positivo
    assert bundle.available_total_thrust_n is not None
    assert bundle.available_total_thrust_n > 0.0


def test_engine_no_rpm_derivation_without_kv():
    """Sin motor_kv_rating, el engine no puede derivar RPM → propulsión no resuelta."""
    from jarvis.core.parameter_requirements import MISSING_PROPELLER_PARAMETERS

    engine = CalculationEngine()
    params = {
        **_BASE_AERIAL,
        "propeller_diameter_in": 10.0,
        "battery_cell_count": 4,
        # motor_kv_rating ausente
    }
    bundle = engine.build(params)

    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert MISSING_PROPELLER_PARAMETERS in tool_names


def test_engine_no_rpm_derivation_without_cells():
    """Sin battery_cell_count, el engine no puede derivar RPM → propulsión no resuelta."""
    from jarvis.core.parameter_requirements import MISSING_PROPELLER_PARAMETERS

    engine = CalculationEngine()
    params = {
        **_BASE_AERIAL,
        "propeller_diameter_in": 10.0,
        "motor_kv_rating": 920.0,
        # battery_cell_count ausente
    }
    bundle = engine.build(params)

    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert MISSING_PROPELLER_PARAMETERS in tool_names


# ── 5. E2E: motores 920KV + batería 4S + hélices 15x5 → propeller_status valid ─

def test_propeller_status_valid_after_component_set(tmp_path):
    """E2E: declarar motores 920KV + batería 4S + hélices 15x5 → propeller_status='valid'."""
    from jarvis.simulation.simulator import FeasibilitySimulator

    state = _make_minimal_state(tmp_path)

    # Declarar motores con KV
    motor_props = extract_motor_properties("4 motores brushless 920KV")
    motor_spec = _make_spec("motors", "motor", motor_props)
    state = set_motor_component(state, motor_spec, power_w=None)

    # Declarar batería 4S
    batt_props = extract_battery_properties("batería LiPo 4S 8000mAh")
    batt_spec = _make_spec("battery", "energy_storage", batt_props)
    capacity_wh = float(batt_props["battery_capacity_wh"].value)
    state = set_battery_component(state, batt_spec, capacity_wh)

    # Declarar hélices 15x5
    prop_props = extract_propeller_properties("6 hélices 15x5 pulgadas")
    prop_spec = _make_spec("propellers", "propulsion_component", prop_props)
    state = set_propeller_component(state, prop_spec)

    # Construir bundle y simular
    engine = CalculationEngine()
    bundle = engine.build(state.current_parameters)
    simulator = FeasibilitySimulator()
    result = simulator.evaluate(bundle)

    assert result.propeller_status == "valid"
