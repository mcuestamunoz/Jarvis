from __future__ import annotations

import pytest

from jarvis.core.phase_layer import PhaseLayer
from jarvis.core.reasoning_layer import HIGH_MARGIN_THRESHOLD


# ── helpers ───────────────────────────────────────────────────────────────────

def _signals(
    *,
    has_simulation: bool = False,
    missing_physics_parameters: bool = False,
    has_warnings: bool = False,
    high_margin: bool = False,
    low_margin: bool = False,
) -> dict:
    return {
        "has_simulation": has_simulation,
        "missing_physics_parameters": missing_physics_parameters,
        "has_warnings": has_warnings,
        "high_margin": high_margin,
        "low_margin": low_margin,
        "material_defined": False,
        "power_unit_defined": False,
        "declarative_context": False,
        "declarative_not_physical": False,
    }


def _sim(quality: str, margin: float = 0.0, can_fly: bool = False) -> dict:
    return {
        "quality": quality,
        "safety_margin_ratio": margin,
        "can_fly": can_fly,
    }


layer = PhaseLayer()

# ── phase = definition ────────────────────────────────────────────────────────

def test_phase_definition_when_missing_physics_parameters():
    result = layer.infer(
        signals=_signals(has_simulation=True, missing_physics_parameters=True),
        simulation=_sim("fail"),
    )
    assert result["phase"] == "definition"


def test_phase_definition_when_no_simulation():
    result = layer.infer(
        signals=_signals(has_simulation=False),
        simulation={},
    )
    assert result["phase"] == "definition"


def test_phase_definition_missing_params_takes_priority_over_fail_quality():
    """missing_physics_parameters wins even if quality would suggest physical_validation."""
    result = layer.infer(
        signals=_signals(has_simulation=True, missing_physics_parameters=True),
        simulation=_sim("fail"),
    )
    assert result["phase"] == "definition"


# ── phase = physical_validation ───────────────────────────────────────────────

def test_phase_physical_validation_when_quality_fail():
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("fail", can_fly=False),
    )
    assert result["phase"] == "physical_validation"


def test_phase_physical_validation_when_quality_risky():
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("risky", margin=0.9, can_fly=False),
    )
    assert result["phase"] == "physical_validation"


# ── phase = optimization ───────────────────────────────────────────────────────

def test_phase_optimization_when_quality_acceptable():
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("acceptable", margin=1.3, can_fly=True),
    )
    assert result["phase"] == "optimization"


def test_phase_optimization_when_quality_good_but_low_margin():
    """quality=good but margin below HIGH_MARGIN_THRESHOLD → still optimization."""
    margin = HIGH_MARGIN_THRESHOLD - 0.1
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("good", margin=margin, can_fly=True),
    )
    assert result["phase"] == "optimization"


# ── phase = complete ───────────────────────────────────────────────────────────

def test_phase_complete_when_quality_good_high_margin_constraints_satisfied():
    result = layer.infer(
        signals=_signals(has_simulation=True, high_margin=True),
        simulation=_sim("good", margin=HIGH_MARGIN_THRESHOLD, can_fly=True),
    )
    assert result["phase"] == "complete"


def test_phase_complete_requires_constraints_satisfied():
    """High margin without can_fly → optimization, not complete."""
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("good", margin=HIGH_MARGIN_THRESHOLD, can_fly=False),
    )
    assert result["phase"] == "optimization"


def test_phase_complete_requires_high_margin():
    """can_fly=True but margin below threshold → optimization."""
    margin = HIGH_MARGIN_THRESHOLD - 0.01
    result = layer.infer(
        signals=_signals(has_simulation=True),
        simulation=_sim("good", margin=margin, can_fly=True),
    )
    assert result["phase"] == "optimization"


# ── output structure ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_input, sigs, sim", [
    ("definition_missing", _signals(missing_physics_parameters=True, has_simulation=True), _sim("fail")),
    ("definition_no_sim", _signals(has_simulation=False), {}),
    ("physical_validation", _signals(has_simulation=True), _sim("fail")),
    ("optimization", _signals(has_simulation=True), _sim("acceptable", 1.3, True)),
    ("complete", _signals(has_simulation=True), _sim("good", HIGH_MARGIN_THRESHOLD, True)),
])
def test_infer_always_returns_required_keys(phase_input, sigs, sim):
    result = layer.infer(signals=sigs, simulation=sim)
    assert "phase" in result
    assert "description" in result
    assert "confidence" in result


@pytest.mark.parametrize("phase_input, sigs, sim", [
    ("definition_missing", _signals(missing_physics_parameters=True, has_simulation=True), _sim("fail")),
    ("definition_no_sim", _signals(has_simulation=False), {}),
    ("physical_validation", _signals(has_simulation=True), _sim("fail")),
    ("optimization", _signals(has_simulation=True), _sim("acceptable", 1.3, True)),
    ("complete", _signals(has_simulation=True), _sim("good", HIGH_MARGIN_THRESHOLD, True)),
])
def test_infer_confidence_is_valid_float(phase_input, sigs, sim):
    result = layer.infer(signals=sigs, simulation=sim)
    assert isinstance(result["confidence"], float)
    assert 0.0 < result["confidence"] <= 1.0


@pytest.mark.parametrize("phase_input, sigs, sim", [
    ("definition_missing", _signals(missing_physics_parameters=True, has_simulation=True), _sim("fail")),
    ("definition_no_sim", _signals(has_simulation=False), {}),
    ("physical_validation", _signals(has_simulation=True), _sim("fail")),
    ("optimization", _signals(has_simulation=True), _sim("acceptable", 1.3, True)),
    ("complete", _signals(has_simulation=True), _sim("good", HIGH_MARGIN_THRESHOLD, True)),
])
def test_infer_description_is_nonempty_string(phase_input, sigs, sim):
    result = layer.infer(signals=sigs, simulation=sim)
    assert isinstance(result["description"], str)
    assert len(result["description"]) > 0


def test_phase_value_is_one_of_four_valid_phases():
    valid = {"definition", "physical_validation", "optimization", "complete"}
    cases = [
        (_signals(missing_physics_parameters=True, has_simulation=True), _sim("fail")),
        (_signals(has_simulation=False), {}),
        (_signals(has_simulation=True), _sim("fail")),
        (_signals(has_simulation=True), _sim("risky", 0.9)),
        (_signals(has_simulation=True), _sim("acceptable", 1.3, True)),
        (_signals(has_simulation=True), _sim("good", HIGH_MARGIN_THRESHOLD, True)),
    ]
    for sigs, sim in cases:
        result = layer.infer(signals=sigs, simulation=sim)
        assert result["phase"] in valid, f"unexpected phase {result['phase']!r}"


def test_phase_complete_blocked_by_active_warnings():
    """quality=good + high margin + can_fly=True but warnings present → optimization, NOT complete."""
    result = layer.infer(
        signals=_signals(has_simulation=True, high_margin=True),
        simulation={
            "quality": "good",
            "safety_margin_ratio": HIGH_MARGIN_THRESHOLD,
            "can_fly": True,
            "warnings": ["autonomy_below_restriction"],
        },
    )
    assert result["phase"] == "optimization"
