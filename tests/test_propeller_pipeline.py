"""Tests for the propeller pipeline — Fase 2 (active propeller intent).

Covers:
- CalculationEngine: propeller_diameter_in → m conversion (0.0254 factor)
- CalculationEngine: produces correct thrust when diameter_in + rpm declared
- CalculationEngine: emits missing_propeller_parameters when propeller hint + incomplete data
- CalculationEngine: specificity rule (hint → specific, no hint → generic)
- FeasibilitySimulator: derives propeller_status from tool_results only (no design_properties)
- ReasoningLayer: missing_propeller_parameters signal + mutual exclusion with missing_physics
- ReasoningLayer: insight, tradeoff, suggested action for propeller case
- parameter_requirements: missing_propeller_parameters entry correct required_params
- Orchestrator build_startup_context: proactive_question when propeller params missing
"""
from __future__ import annotations

import math
import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    MISSING_PROPELLER_PARAMETERS,
    MISSING_PROPULSION_PARAMETERS,
    REQUIREMENT_REASONS,
    missing_params_for_reason,
)
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.simulation.simulator import FeasibilitySimulator
from jarvis.tools.aerodynamics import calculate_thrust_from_propeller


# ── test fixtures ─────────────────────────────────────────────────────────────

_BASE_AERIAL = {
    "vehicle_type": "dron",
    "objective": "dron de carga",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motor_count": 4,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
    # no per_motor_max_thrust_n — force resolution depends on propeller path
}

# 10-inch propeller at 8000 RPM — standard 2 kg UAV class
_DIAMETER_IN = 10.0
_DIAMETER_M = _DIAMETER_IN * 0.0254   # 0.254 m
_RPM = 8000.0


# ── CalculationEngine: unit conversion ───────────────────────────────────────

def test_engine_diameter_in_conversion_matches_direct_metres():
    """propeller_diameter_in=10 produces same thrust as propeller_diameter_m=0.254."""
    engine = CalculationEngine()

    bundle_via_in = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN, "propeller_rpm": _RPM})
    bundle_via_m = engine.build({**_BASE_AERIAL, "propeller_diameter_m": _DIAMETER_M, "propeller_rpm": _RPM})

    assert bundle_via_in.available_total_thrust_n is not None
    assert bundle_via_m.available_total_thrust_n is not None
    assert bundle_via_in.available_total_thrust_n == pytest.approx(bundle_via_m.available_total_thrust_n, rel=1e-5)


def test_engine_diameter_in_produces_correct_thrust_formula():
    """T per motor = ct * rho * (rpm/60)^2 * D^4; total = T * motors."""
    engine = CalculationEngine()
    bundle = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN, "propeller_rpm": _RPM})

    expected_thrust_per_motor = calculate_thrust_from_propeller(_DIAMETER_M, _RPM).outputs["thrust_n"]
    expected_total = expected_thrust_per_motor * 4  # 4 motors

    assert bundle.available_total_thrust_n == pytest.approx(expected_total, rel=1e-5)


def test_engine_diameter_m_canonical_path_unaffected():
    """When propeller_diameter_m is declared, diameter_in is ignored (canonical wins)."""
    engine = CalculationEngine()
    other_diameter_m = 0.30

    bundle_canonical = engine.build({**_BASE_AERIAL, "propeller_diameter_m": other_diameter_m, "propeller_rpm": _RPM})
    bundle_both = engine.build({
        **_BASE_AERIAL,
        "propeller_diameter_m": other_diameter_m,
        "propeller_diameter_in": _DIAMETER_IN,  # should be ignored
        "propeller_rpm": _RPM,
    })

    assert bundle_canonical.available_total_thrust_n == pytest.approx(bundle_both.available_total_thrust_n, rel=1e-5)


# ── CalculationEngine: intent detection ──────────────────────────────────────

def test_engine_emits_missing_propeller_when_diameter_in_present_but_no_rpm():
    """Propeller hint (diameter_in) present, rpm absent → missing_propeller_parameters."""
    engine = CalculationEngine()
    bundle = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN})

    reason_codes = {tr.tool_name for tr in bundle.tool_results}
    assert MISSING_PROPELLER_PARAMETERS in reason_codes
    assert MISSING_PROPULSION_PARAMETERS not in reason_codes
    assert bundle.available_total_thrust_n is None


def test_engine_emits_missing_propeller_when_rpm_present_but_no_diameter():
    """Propeller hint (rpm) present, diameter absent → missing_propeller_parameters."""
    engine = CalculationEngine()
    bundle = engine.build({**_BASE_AERIAL, "propeller_rpm": _RPM})

    reason_codes = {tr.tool_name for tr in bundle.tool_results}
    assert MISSING_PROPELLER_PARAMETERS in reason_codes
    assert bundle.available_total_thrust_n is None


def test_engine_emits_missing_propulsion_when_aerial_no_hint():
    """Aerial vehicle, no propeller hint at all → generic missing_propulsion_parameters."""
    engine = CalculationEngine()
    # No thrust, no torque, no propeller params at all
    bundle = engine.build(_BASE_AERIAL)

    reason_codes = {tr.tool_name for tr in bundle.tool_results}
    assert MISSING_PROPULSION_PARAMETERS in reason_codes
    assert MISSING_PROPELLER_PARAMETERS not in reason_codes


def test_engine_specificity_rule_hint_gives_specific_not_generic():
    """When propeller hint is present, we get specific code, NOT generic propulsion code."""
    engine = CalculationEngine()
    bundle_with_hint = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN})
    bundle_no_hint = engine.build(_BASE_AERIAL)

    codes_with_hint = {tr.tool_name for tr in bundle_with_hint.tool_results}
    codes_no_hint = {tr.tool_name for tr in bundle_no_hint.tool_results}

    # With hint: specific > generic
    assert MISSING_PROPELLER_PARAMETERS in codes_with_hint
    assert MISSING_PROPULSION_PARAMETERS not in codes_with_hint

    # Without hint: generic (not specific)
    assert MISSING_PROPULSION_PARAMETERS in codes_no_hint
    assert MISSING_PROPELLER_PARAMETERS not in codes_no_hint


# ── FeasibilitySimulator: propeller_status from tool_results only ─────────────

def test_simulator_propeller_status_missing_when_engine_emits_code():
    """Simulator derives propeller_status from tool_results — no design_properties access."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()

    bundle = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN})
    result = sim.evaluate(bundle)

    assert result.propeller_status == MISSING_PROPELLER_PARAMETERS


def test_simulator_propeller_status_valid_when_thrust_resolved_via_propeller():
    """When propeller path resolves successfully, propeller_status is valid."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()

    bundle = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN, "propeller_rpm": _RPM})
    result = sim.evaluate(bundle)

    assert result.propeller_status == "valid"
    assert result.analysis.available_thrust_n is not None


def test_simulator_propeller_status_valid_when_thrust_declared_directly():
    """Direct thrust declared → propeller_status is valid (no propeller tool was called)."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()

    bundle = engine.build({**_BASE_AERIAL, "per_motor_max_thrust_n": 15.0})
    result = sim.evaluate(bundle)

    assert result.propeller_status == "valid"


def test_simulator_propeller_status_independent_of_physics_status():
    """propeller_status and physics_status are independent fields."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()

    bundle = engine.build({**_BASE_AERIAL, "propeller_diameter_in": _DIAMETER_IN})
    result = sim.evaluate(bundle)

    # physics is missing (no available thrust), propeller is specifically missing
    assert result.physics_status == "missing_parameters"
    assert result.propeller_status == MISSING_PROPELLER_PARAMETERS


# ── ReasoningLayer: mutual exclusion ─────────────────────────────────────────

def _propeller_missing_ctx(*, energy_status: str = "valid") -> dict:
    return {
        "last_simulation": {
            "physics_status": "missing_parameters",
            "propeller_status": MISSING_PROPELLER_PARAMETERS,
            "energy_status": energy_status,
            "safety_margin_ratio": 0.0,
            "warnings": [MISSING_PROPELLER_PARAMETERS],
            "propeller_thrust_inferred": False,
        },
        "design_properties": {},
        "current_parameters": {"propeller_diameter_in": _DIAMETER_IN},
    }


def test_reasoning_missing_propeller_signal_true():
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert output.signals.get("missing_propeller_parameters") is True


def test_reasoning_missing_physics_false_when_propeller_specific():
    """mutual exclusion: specific propeller signal suppresses generic physics signal."""
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert output.signals.get("missing_physics_parameters") is False


def test_reasoning_missing_physics_true_when_no_propeller_status():
    """Without propeller_status set, generic physics signal fires normally."""
    layer = ReasoningLayer()
    ctx = {
        "last_simulation": {
            "physics_status": "missing_parameters",
            "propeller_status": "valid",
            "energy_status": "valid",
            "safety_margin_ratio": 0.0,
            "warnings": ["missing_propulsion_parameters"],
        },
        "design_properties": {},
        "current_parameters": {},
    }
    output = layer.build(ctx)
    assert output.signals.get("missing_physics_parameters") is True
    assert output.signals.get("missing_propeller_parameters") is False


# ── ReasoningLayer: insight + tradeoff + suggested action ────────────────────

def test_reasoning_propeller_missing_adds_insight():
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert any("hélice" in i or "propeller" in i.lower() for i in output.insights)


def test_reasoning_propeller_missing_adds_tradeoff():
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert any("hélice" in t or "Ct" in t for t in output.tradeoffs)


def test_reasoning_propeller_missing_suggested_action_labels_params():
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert output.suggested_actions
    label = output.suggested_actions[0].label
    assert "propeller_diameter_in" in label or "propeller_rpm" in label


def test_reasoning_propeller_suggested_action_priority_high():
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert output.suggested_actions
    assert output.suggested_actions[0].priority == pytest.approx(0.99)


def test_reasoning_propeller_missing_does_not_add_generic_physics_insight():
    """When propeller signal is active, generic 'transmisión' insight must NOT appear."""
    layer = ReasoningLayer()
    output = layer.build(_propeller_missing_ctx())
    assert not any("transmisión" in i for i in output.insights)


# ── parameter_requirements catalog ───────────────────────────────────────────

def test_requirement_reasons_has_missing_propeller_parameters_entry():
    assert MISSING_PROPELLER_PARAMETERS in REQUIREMENT_REASONS


def test_missing_propeller_parameters_requires_correct_params():
    entry = REQUIREMENT_REASONS[MISSING_PROPELLER_PARAMETERS]
    assert "propeller_diameter_in" in entry.required_params
    assert "propeller_rpm" in entry.required_params


def test_missing_propeller_parameters_domain_label():
    entry = REQUIREMENT_REASONS[MISSING_PROPELLER_PARAMETERS]
    assert entry.domain_label == "hélice"


def test_missing_propeller_parameters_hint_present():
    entry = REQUIREMENT_REASONS[MISSING_PROPELLER_PARAMETERS]
    assert entry.hint is not None
    assert "pulgadas" in entry.hint or "rpm" in entry.hint.lower()


def test_missing_params_for_reason_returns_both_params_when_none_present():
    params: dict = {}
    result = missing_params_for_reason(MISSING_PROPELLER_PARAMETERS, params)
    assert "propeller_diameter_in" in result
    assert "propeller_rpm" in result


def test_missing_params_for_reason_returns_only_missing_one():
    """If only one param is absent, only that one is returned."""
    params = {"propeller_diameter_in": 10.0}
    result = missing_params_for_reason(MISSING_PROPELLER_PARAMETERS, params)
    assert "propeller_rpm" in result
    assert "propeller_diameter_in" not in result


# ── Orchestrator build_startup_context: proactive question ────────────────────

def test_build_startup_context_propeller_proactive_when_hint_and_no_rpm(tmp_path):
    """Full pipeline: project with propeller hint (diameter_in) but no rpm.
    Battery params injected via state.json (not in CreateProjectParams).
    After recalculate + simulate the proactive_question must mention hélice.
    """
    import json
    from pathlib import Path

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    params = {
        **_BASE_AERIAL,
        "motors": 4,
        "propeller_diameter_in": _DIAMETER_IN,
        # propeller_rpm deliberately absent
    }
    result = orchestrator.handle({"action": "create_project", "parameters": params})
    workspace_path = result["workspace_path"]

    # Inject battery params so energy is complete (not in CreateProjectParams, must go via state)
    state_path = Path(workspace_path) / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["current_parameters"]["battery_capacity_wh"] = 2000.0
    data["current_parameters"]["motor_power_w"] = 50.0
    state_path.write_text(json.dumps(data), encoding="utf-8")

    # Re-run calculate (re-executes engine with updated current_parameters)
    # then simulate (uses the fresh bundle with battery + propeller_diameter_in)
    orchestrator.handle({"action": "calculate", "workspace_path": workspace_path})
    orchestrator.handle({"action": "simulate", "workspace_path": workspace_path})

    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)

    assert ctx.get("proactive_question") is not None
    pq = ctx["proactive_question"]
    assert "hélice" in pq or "propeller_rpm" in pq or "propeller_diameter_in" in pq


def test_build_startup_context_no_propeller_proactive_when_both_params_present(tmp_path):
    """When both propeller params are declared, no propeller proactive question."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    params = {
        **_BASE_AERIAL,
        "motors": 4,
        "propeller_diameter_in": _DIAMETER_IN,
        "propeller_rpm": _RPM,
        "battery_capacity_wh": 2000.0,
        "motor_power_w": 50.0,
    }
    result = orchestrator.handle({"action": "create_project", "parameters": params})
    ctx = orchestrator.build_startup_context(workspace_path=result["workspace_path"])

    # proactive_question may or may not be set for other reasons, but
    # if set it must NOT be about propeller
    pq = ctx.get("proactive_question") or ""
    assert "hélice" not in pq
    assert "propeller_rpm" not in pq
