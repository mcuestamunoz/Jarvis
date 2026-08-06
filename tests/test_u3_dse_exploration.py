"""Tests para U3 — DSE espacio de exploración ampliado (domain-agnostic).

Verifica que:
1. EXPLORATION_GRIDS["mejorar_autonomia"] incluye candidatos de frame ligero y motor eficiente.
2. Los candidatos de frame usan factores relativos (domain-agnostic), no valores absolutos.
3. Si structure_mass_override_kg no está en current_parameters, el candidato se omite (no falla).
4. DesignExplorer.explore() genera y evalúa candidatos de frame y motor correctamente.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.design_explorer import (
    EXPLORATION_GRIDS,
    DesignExplorer,
    ExplorationResult,
    _apply_delta,
)
from jarvis.simulation.simulator import FeasibilitySimulator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_project_state(params: dict) -> SimpleNamespace:
    return SimpleNamespace(
        project_id="test-u3",
        workspace_path="/tmp/test-u3",
        current_parameters=params,
        design_properties=SimpleNamespace(components={}),
    )


# Params con structure_mass_override_kg — dron con frame declarado
DRONE_WITH_FRAME = {
    "vehicle_type": "dron",
    "payload_kg": 1.0,
    "motor_count": 4,
    "per_motor_max_thrust_n": 15.0,
    "battery_capacity_wh": 200.0,
    "battery_mass_kg": 200.0 / 150.0,
    "motor_power_w": 120.0,
    "structure_mass_override_kg": 0.6,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}

# Params sin structure_mass_override_kg — proyecto sin frame declarado
DRONE_WITHOUT_FRAME = {k: v for k, v in DRONE_WITH_FRAME.items()
                       if k != "structure_mass_override_kg"}


# ── 1. EXPLORATION_GRIDS contiene los nuevos candidatos ──────────────────────

def test_exploration_grid_autonomia_has_frame_factor():
    """mejorar_autonomia debe incluir al menos un candidato de structure_mass_override_kg_factor."""
    grid = EXPLORATION_GRIDS["mejorar_autonomia"]
    has_frame = any("structure_mass_override_kg_factor" in entry for entry in grid)
    assert has_frame, "No hay candidatos de frame en mejorar_autonomia"


def test_exploration_grid_autonomia_has_motor_power_factor_low():
    """mejorar_autonomia debe incluir motor_power_w_factor < 0.75 (más eficiente que antes)."""
    grid = EXPLORATION_GRIDS["mejorar_autonomia"]
    low_power = [e for e in grid if e.get("motor_power_w_factor", 1.0) < 0.7]
    assert len(low_power) >= 1, "No hay candidato motor_power_w_factor < 0.70"


def test_exploration_grid_frame_factors_are_relative():
    """Los factores de frame deben ser < 1.0 (reducción relativa, no valores absolutos)."""
    grid = EXPLORATION_GRIDS["mejorar_autonomia"]
    for entry in grid:
        factor = entry.get("structure_mass_override_kg_factor")
        if factor is not None:
            assert 0 < factor < 1.0, (
                f"structure_mass_override_kg_factor={factor} no es una reducción "
                f"(debe ser 0 < f < 1.0 para ser domain-agnostic)"
            )


# ── 2. _apply_delta con factores de frame ─────────────────────────────────────

def test_apply_delta_frame_factor_reduces_mass():
    """structure_mass_override_kg_factor=0.75 → masa frame reducida al 75%."""
    base = {"structure_mass_override_kg": 0.6}
    result = _apply_delta(base, {"structure_mass_override_kg_factor": 0.75})
    assert result is not None
    assert result["structure_mass_override_kg"] == pytest.approx(0.6 * 0.75)


def test_apply_delta_frame_factor_skipped_when_absent():
    """Sin structure_mass_override_kg en base, _apply_delta devuelve None (candidato omitido)."""
    base = {"battery_capacity_wh": 200.0, "motor_count": 4}
    result = _apply_delta(base, {"structure_mass_override_kg_factor": 0.75})
    assert result is None


def test_apply_delta_motor_power_factor_65():
    """motor_power_w_factor=0.65 → motor_power_w reducido al 65%."""
    base = {"motor_power_w": 120.0}
    result = _apply_delta(base, {"motor_power_w_factor": 0.65})
    assert result is not None
    assert result["motor_power_w"] == pytest.approx(120.0 * 0.65)


def test_apply_delta_frame_and_battery_combined():
    """Combinación frame 0.6 + batería 1.5 aplicada correctamente."""
    base = {"structure_mass_override_kg": 0.6, "battery_capacity_wh": 200.0}
    result = _apply_delta(base, {
        "structure_mass_override_kg_factor": 0.6,
        "battery_capacity_wh_factor": 1.5,
    })
    assert result is not None
    assert result["structure_mass_override_kg"] == pytest.approx(0.6 * 0.6)
    assert result["battery_capacity_wh"] == pytest.approx(200.0 * 1.5)


# ── 3. DesignExplorer genera candidatos de frame ──────────────────────────────

@pytest.fixture
def explorer():
    return DesignExplorer(
        calculation_engine=CalculationEngine(),
        simulator=FeasibilitySimulator(),
    )


def test_dse_autonomia_explores_frame_mass(explorer):
    """Con frame declarado, el DSE genera candidatos de estructura ligera."""
    state = _make_project_state(dict(DRONE_WITH_FRAME))
    result = explorer.explore(state, "mejorar_autonomia")

    # params_delta guarda las claves del delta (con sufijo _factor)
    frame_candidates = [
        c for c in result.candidates
        if "structure_mass_override_kg_factor" in c.params_delta
    ]
    assert len(frame_candidates) >= 2, (
        f"Se esperaban ≥2 candidatos de frame, encontrados: {len(frame_candidates)}"
    )


def test_dse_autonomia_explores_motor_power_factor(explorer):
    """Con motor_power_w declarado, el DSE genera candidatos de motor eficiente."""
    state = _make_project_state(dict(DRONE_WITH_FRAME))
    result = explorer.explore(state, "mejorar_autonomia")

    # factor 0.65 o 0.75 sobre motor_power_w → candidato con motor_power_w_factor
    motor_eff_candidates = [
        c for c in result.candidates
        if c.params_delta.get("motor_power_w_factor", 1.0) < 0.8
    ]
    assert len(motor_eff_candidates) >= 1, (
        "No hay candidatos con motor_power_w_factor reducido (motor más eficiente)"
    )


def test_dse_frame_candidate_skipped_when_no_override(explorer):
    """Sin structure_mass_override_kg en params, candidatos de frame se omiten, no fallan."""
    state = _make_project_state(dict(DRONE_WITHOUT_FRAME))
    # No debe lanzar excepción
    result = explorer.explore(state, "mejorar_autonomia")
    assert isinstance(result, ExplorationResult)

    # Ningún candidato debe tener structure_mass_override_kg en params_delta
    frame_candidates = [
        c for c in result.candidates
        if "structure_mass_override_kg" in c.params_delta
    ]
    assert len(frame_candidates) == 0


def test_dse_domain_agnostic_rover_frame(explorer):
    """Un rover con frame de 3kg usa el mismo factor y el candidato es válido."""
    rover_params = {
        "vehicle_type": "rover",
        "payload_kg": 5.0,
        "motor_count": 4,
        "per_motor_max_thrust_n": 80.0,
        "battery_capacity_wh": 500.0,
        "battery_mass_kg": 500.0 / 150.0,
        "motor_power_w": 200.0,
        "structure_mass_override_kg": 3.0,   # rover: 3 kg de chasis
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
    }
    state = _make_project_state(rover_params)
    result = explorer.explore(state, "mejorar_autonomia")

    frame_candidates = [
        c for c in result.candidates
        if "structure_mass_override_kg_factor" in c.params_delta
    ]
    # El factor 0.75 sobre 3.0kg = 2.25kg — candidato físicamente sensato para rover
    assert len(frame_candidates) >= 1
    # Verificar que el valor calculado es una reducción respecto al baseline (3.0kg)
    for c in frame_candidates:
        factor = c.params_delta["structure_mass_override_kg_factor"]
        assert factor < 1.0, f"Factor de frame no es reducción: {factor}"
