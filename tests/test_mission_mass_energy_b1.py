"""Mission mass -> AUW + Continuity ladder B1 (`B1-mission-mass-energy`).

Covers implementation_contract_mission_mass_energy_b1.md §2:

  T1  Helper/writer: set cameras mass_g=28 -> mirrored kg ~= 0.028; calc
      total_mass_kg rises vs baseline with same payload_kg
  T2  Radio mass adds; both sum correctly
  T3  Clear/remove mass -> mirror drops; total regresses
  T4  P1 warn: payload_kg>0 + mission mass>0 -> insight/Continuity warn present
  T5  Grammar: "cámara 28 g" on project with cameras -> property set, source declared
  T6  Grammar refuse: same phrase when cameras absent -> no invent stub
  T7  Never invent: identity-only "cámara RunCam" still has no mass_g
  T8  Continuity: cameras medium+, no mass -> top mission suggestion is
      declare-camera-mass (not only soft margin)
  T9  After camera mass set, no radio mass -> declare-radio-mass (next hole)
  T10 Neutral high-margin project -> increase_payload still available (regression)
  T11 Mission intent + both masses set -> soft margin OK; still no increase_payload
  T12 Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import set_mission_component_mass
from jarvis.core.mission_mass_declare_assist import parse_mission_mass_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState

_CALC_BASE = {
    "vehicle_type": "aerial", "payload_kg": 1.0, "structure_mass_factor": 0.5,
    "safety_factor": 1.2, "motor_count": 4, "per_motor_max_thrust_n": 15.0,
}


def _cameras(mass_g: float | None = None) -> ComponentSpec:
    props = {"model": PropertyValue(value="runcam", confidence=0.8, source="declared")}
    if mass_g is not None:
        props["mass_g"] = PropertyValue(value=mass_g, unit="g", confidence=0.9, source="declared")
    return ComponentSpec(suggested_key="cameras", completeness="medium", properties=props)


def _radio(mass_g: float | None = None) -> ComponentSpec:
    props = {"model": PropertyValue(value="elrs", confidence=0.8, source="declared")}
    if mass_g is not None:
        props["mass_g"] = PropertyValue(value=mass_g, unit="g", confidence=0.9, source="declared")
    return ComponentSpec(suggested_key="radio_module", completeness="medium", properties=props)


def _state(**components) -> ProjectState:
    return ProjectState(
        project_id="p", project_slug="p", objective="dron de vigilancia", workspace_path="w",
        current_parameters={"payload_kg": 1.0}, design_properties=DesignProperties(components=components),
    )


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_camera_mass_mirrors_and_raises_total_mass():
    state = _state(cameras=_cameras())
    updated = set_mission_component_mass(state, "cameras", 28.0)
    assert updated.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.028)

    eng = CalculationEngine()
    baseline = eng.build(_CALC_BASE)
    with_mission = eng.build({**_CALC_BASE, "mission_payload_mass_kg": 0.028})
    assert with_mission.total_mass_kg > baseline.total_mass_kg
    assert with_mission.total_mass_kg == pytest.approx(baseline.total_mass_kg + 0.028, abs=1e-6)


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_radio_mass_adds_both_sum():
    state = _state(cameras=_cameras(), radio_module=_radio())
    updated = set_mission_component_mass(state, "cameras", 28.0)
    updated2 = set_mission_component_mass(updated, "radio_module", 3.0)
    assert updated2.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.031)


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_clearing_mass_drops_mirror_and_regresses_total():
    state = _state(cameras=_cameras(), radio_module=_radio())
    updated = set_mission_component_mass(state, "cameras", 28.0)
    updated = set_mission_component_mass(updated, "radio_module", 3.0)
    assert updated.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.031)

    cleared = set_mission_component_mass(updated, "cameras", None)
    assert "mass_g" not in cleared.design_properties.components["cameras"].properties
    assert cleared.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.003)

    eng = CalculationEngine()
    with_both = eng.build({**_CALC_BASE, "mission_payload_mass_kg": 0.031})
    with_camera_cleared = eng.build({**_CALC_BASE, "mission_payload_mass_kg": 0.003})
    assert with_camera_cleared.total_mass_kg < with_both.total_mass_kg


# ── T4 ────────────────────────────────────────────────────────────────────


def _reasoning_context(payload_kg, mission_kg, objective="prueba", margin=1.0):
    return {
        "objective": objective,
        "current_parameters": {"restrictions": "no", "payload_kg": payload_kg, "mission_payload_mass_kg": mission_kg},
        "design_properties": {"components": {}, "structure": {}},
        "last_calculation": None, "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {}, "last_mutation": None, "mutation_mode": None,
    }


def test_t4_double_count_warning_present_when_both_nonzero():
    out = ReasoningLayer().build(_reasoning_context(1.0, 0.028))
    assert any("contar dos veces" in i for i in out.insights)


def test_t4_double_count_warning_absent_when_either_zero():
    out_no_mission = ReasoningLayer().build(_reasoning_context(1.0, 0.0))
    assert not any("contar dos veces" in i for i in out_no_mission.insights)
    out_no_payload = ReasoningLayer().build(_reasoning_context(0.0, 0.028))
    assert not any("contar dos veces" in i for i in out_no_payload.insights)


# ── T5 ────────────────────────────────────────────────────────────────────


def _orch_with_project(tmp_path: Path, objective: str = "dron de vigilancia") -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": objective, "payload_kg": 1.0,
            "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    return orch


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def test_t5_grammar_sets_mass_with_declared_source(tmp_path: Path):
    orch = _orch_with_project(tmp_path)
    orch.handle_user_text("cámara RunCam", _RefuseLLM())
    result = orch.handle_user_text("cámara 28 g", _RefuseLLM())
    assert result["status"] == "ok"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    mass_prop = ps.design_properties.components["cameras"].properties["mass_g"]
    assert mass_prop.value == pytest.approx(28.0)
    assert mass_prop.source == "declared"


def test_t5_grammar_radio_mass_also_works(tmp_path: Path):
    orch = _orch_with_project(tmp_path)
    orch.handle_user_text("radio ELRS", _RefuseLLM())
    result = orch.handle_user_text("radio 3 g", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["radio_module"].properties["mass_g"].value == pytest.approx(3.0)


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_grammar_refuses_when_target_absent_no_stub(tmp_path: Path):
    orch = _orch_with_project(tmp_path)
    result = orch.handle_user_text("cámara 28 g", _RefuseLLM())
    assert result["status"] == "error"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "cameras" not in ps.design_properties.components


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_identity_only_declare_never_sets_mass():
    from jarvis.core.component_inference import infer_component

    spec = infer_component("cámara RunCam")
    assert "mass_g" not in spec.properties

    spec2 = infer_component("radio ELRS")
    assert "mass_g" not in spec2.properties


def test_t7_parser_never_intercepts_bare_identity_phrase():
    """Regression caught during implementation: a bare identity phrase
    ('cámara RunCam') must fall through to the identity-declare grammar,
    never be swallowed as an INCOMPLETE mass declare."""
    assert parse_mission_mass_declare("cámara RunCam").kind == "NONE"
    assert parse_mission_mass_declare("radio ELRS").kind == "NONE"


# ── T8 ────────────────────────────────────────────────────────────────────


def test_t8_continuity_top_suggestion_is_declare_camera_mass_when_missing():
    context = _reasoning_context(0.0, 0.0, objective="dron de vigilancia", margin=3.0)
    context["design_properties"]["components"] = {
        "cameras": {"completeness": "medium", "properties": {"model": {"value": "runcam"}}},
        "radio_module": {"completeness": "medium", "properties": {"model": {"value": "elrs"}}},
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara masa de cámara (g)"
    assert out.suggested_actions[0].action_type == "declare_mission_mass"


# ── T9 ────────────────────────────────────────────────────────────────────


def test_t9_next_hole_is_declare_radio_mass_after_camera_mass_set():
    context = _reasoning_context(0.0, 0.028, objective="dron de vigilancia", margin=3.0)
    context["design_properties"]["components"] = {
        "cameras": {"completeness": "medium", "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}}},
        "radio_module": {"completeness": "medium", "properties": {"model": {"value": "elrs"}}},
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara masa de radio (g)"


# ── T10 ───────────────────────────────────────────────────────────────────


def test_t10_neutral_project_increase_payload_still_available():
    out = ReasoningLayer().build(_reasoning_context(1.0, 0.0, objective="prueba", margin=3.0))
    assert out.suggested_actions[0].label == "Aumentar carga útil"
    assert out.suggested_actions[0].action_type == "increase_payload"


# ── T11 ───────────────────────────────────────────────────────────────────


def test_t11_mission_intent_both_masses_set_soft_margin_never_increase_payload():
    context = _reasoning_context(0.0, 0.031, objective="dron de vigilancia", margin=3.6196)
    context["design_properties"]["components"] = {
        "cameras": {"completeness": "medium", "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}}},
        "radio_module": {"completeness": "medium", "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}}},
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Revisar margen vs carga de misión"
    assert out.suggested_actions[0].action_type != "increase_payload"
