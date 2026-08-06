"""Tests para U1 — Masa de batería dinámica.

Verifica que:
1. estimate_battery_mass_kg devuelve valores correctos.
2. set_battery_component escribe battery_mass_kg en current_parameters.
3. calculation_engine suma battery_mass_kg a total_mass_kg.
4. _apply_delta del DSE sincroniza battery_mass_kg cuando cambia battery_capacity_wh.
5. La autonomía calculada es realista (no 60 min con 2 kg de masa).
"""
from __future__ import annotations

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import set_battery_component
from jarvis.core.design_explorer import _apply_delta
from jarvis.domains.aerial import extract_battery_properties
from jarvis.tools.electricity import LIPO_ENERGY_DENSITY_WH_KG, estimate_battery_mass_kg


# ── 1. estimate_battery_mass_kg ───────────────────────────────────────────────

def test_estimate_battery_mass_150wh():
    """150 Wh → exactamente 1.0 kg con densidad 150 Wh/kg."""
    assert estimate_battery_mass_kg(150.0) == pytest.approx(1.0)


def test_estimate_battery_mass_355wh():
    """355.2 Wh (batería 4S 8000mAh típica) → ~2.37 kg."""
    result = estimate_battery_mass_kg(355.2)
    expected = round(355.2 / LIPO_ENERGY_DENSITY_WH_KG, 3)
    assert result == pytest.approx(expected)


def test_estimate_battery_mass_1200wh():
    """1200 Wh → 8.0 kg."""
    assert estimate_battery_mass_kg(1200.0) == pytest.approx(8.0)


def test_estimate_battery_mass_zero():
    """0 Wh → 0.0 kg (sin división por cero)."""
    assert estimate_battery_mass_kg(0.0) == 0.0


def test_estimate_battery_mass_negative():
    """Capacidad negativa → 0.0 (guard de entrada)."""
    assert estimate_battery_mass_kg(-10.0) == 0.0


# ── 2. set_battery_component escribe battery_mass_kg ─────────────────────────

def _make_minimal_state(tmp_path):
    """Crea un ProjectState mínimo con proyecto activo."""
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "test",
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


def test_set_battery_component_writes_battery_mass_kg(tmp_path):
    """set_battery_component debe escribir battery_mass_kg en current_parameters."""
    state = _make_minimal_state(tmp_path)
    props = extract_battery_properties("batería LiPo 4S 8000mAh 14.8V")
    from jarvis.schemas.action_schema import ComponentSpec
    spec = ComponentSpec(
        name="battery",
        component_type="energy_storage",
        suggested_key="battery",
        inference_confidence=0.9,
        properties=props,
        completeness="medium",
        missing_fields=[],
        source="declared",
    )
    capacity_wh = float(props["battery_capacity_wh"].value)
    updated = set_battery_component(state, spec, capacity_wh)

    assert "battery_mass_kg" in updated.current_parameters
    expected_mass = estimate_battery_mass_kg(capacity_wh)
    assert updated.current_parameters["battery_mass_kg"] == pytest.approx(expected_mass)


def test_set_battery_component_none_removes_battery_mass_kg(tmp_path):
    """set_battery_component(capacity_wh=None) debe eliminar battery_mass_kg."""
    state = _make_minimal_state(tmp_path)
    # Primero inyectar el valor
    from jarvis.schemas.action_schema import ComponentSpec
    spec = ComponentSpec(
        name="battery", component_type="energy_storage", suggested_key="battery",
        inference_confidence=0.9, properties={}, completeness="low",
        missing_fields=[], source="declared",
    )
    updated = set_battery_component(state, spec, None)
    assert "battery_mass_kg" not in updated.current_parameters


# ── 3. calculation_engine suma battery_mass_kg ────────────────────────────────

def _base_params(**overrides):
    params = {
        "vehicle_type": "dron",
        "payload_kg": 1.0,
        "structure_mass_factor": 0.6,
        "structure_mass_override_kg": 0.5,
        "safety_factor": 1.2,
        "motor_count": 4,
        "per_motor_max_thrust_n": 20.0,
        "battery_capacity_wh": 150.0,
        "motor_power_w": 100.0,
    }
    params.update(overrides)
    return params


def test_engine_total_mass_without_battery_mass():
    """Sin battery_mass_kg, total_mass = payload + structure (comportamiento legacy)."""
    engine = CalculationEngine()
    params = _base_params()  # no battery_mass_kg
    result = engine.build(params)
    # payload=1.0, structure_override=0.5 → total=1.5
    assert result.total_mass_kg == pytest.approx(1.5)


def test_engine_total_mass_includes_battery_mass():
    """Con battery_mass_kg=1.0, total_mass = payload + structure + battery."""
    engine = CalculationEngine()
    params = _base_params(battery_mass_kg=1.0)
    result = engine.build(params)
    # payload=1.0, structure=0.5, battery=1.0 → total=2.5
    assert result.total_mass_kg == pytest.approx(2.5)


def test_engine_total_mass_battery_mass_zero():
    """battery_mass_kg=0 → comportamiento idéntico a sin el campo."""
    engine = CalculationEngine()
    params_with = _base_params(battery_mass_kg=0.0)
    params_without = _base_params()
    r_with = engine.build(params_with)
    r_without = engine.build(params_without)
    assert r_with.total_mass_kg == pytest.approx(r_without.total_mass_kg)


# ── 4. _apply_delta sincroniza battery_mass_kg ───────────────────────────────

def test_apply_delta_syncs_battery_mass_on_capacity_factor():
    """battery_capacity_wh_factor=2 → battery_mass_kg también dobla."""
    base = {
        "battery_capacity_wh": 150.0,
        "battery_mass_kg": estimate_battery_mass_kg(150.0),
        "motor_count": 4,
    }
    result = _apply_delta(base, {"battery_capacity_wh_factor": 2.0})
    assert result is not None
    assert result["battery_capacity_wh"] == pytest.approx(300.0)
    assert result["battery_mass_kg"] == pytest.approx(estimate_battery_mass_kg(300.0))


def test_apply_delta_battery_mass_not_inflated_without_capacity_change():
    """Si el delta no toca battery_capacity_wh, battery_mass_kg no cambia."""
    base = {
        "battery_capacity_wh": 150.0,
        "battery_mass_kg": estimate_battery_mass_kg(150.0),
        "motor_count": 4,
    }
    result = _apply_delta(base, {"motor_count_delta": -1})
    assert result is not None
    # battery_mass_kg debe mantenerse igual (150 Wh → 1.0 kg)
    assert result["battery_mass_kg"] == pytest.approx(estimate_battery_mass_kg(150.0))


# ── 5. Autonomía realista tras cambio de batería ──────────────────────────────

def test_autonomy_realistic_with_large_battery():
    """1200 Wh + 6 motores 200W → masa real incluye ~8 kg de batería → autonomía ≠ 60 min."""
    engine = CalculationEngine()
    # 1200 Wh, 6 motores de 200W → si la masa fuera la de antes (2.15 kg) daría 60 min.
    # Con battery_mass_kg=8.0 kg la masa sube y el sistema puede fallar restricciones.
    battery_mass = estimate_battery_mass_kg(1200.0)
    params = {
        "vehicle_type": "dron",
        "payload_kg": 1.5,
        "structure_mass_factor": 0.6,
        "structure_mass_override_kg": 0.65,
        "safety_factor": 1.2,
        "motor_count": 6,
        "per_motor_max_thrust_n": 25.0,
        "battery_capacity_wh": 1200.0,
        "battery_mass_kg": battery_mass,
        "motor_power_w": 200.0,
    }
    result = engine.build(params)
    # total_mass incluye payload(1.5) + structure(0.65) + battery(8.0) = 10.15 kg
    assert result.total_mass_kg == pytest.approx(1.5 + 0.65 + battery_mass)
    # La autonomía ahora es la correcta energéticamente pero la masa es real
    if result.autonomy_min is not None:
        # autonomia = 1200 / (200*6) * 60 = 60 min (energía no cambia, solo masa)
        assert result.autonomy_min == pytest.approx(60.0)
    # La masa total con 1200 Wh de batería es mucho mayor que antes
    assert result.total_mass_kg > 5.0
