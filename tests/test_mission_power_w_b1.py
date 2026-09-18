"""Mission `power_w` → energy/autonomía B1 (`B1-mission-power-w`).

Covers implementation_contract_mission_power_w_b1.md §2:

  T1  Parse "cámara 1 W" -> cameras.power_w declared
  T2  Parse radio W similarly
  T3  Missing identity -> honest refuse
  T4  Mirror mission_accessory_power_w = sum W
  T5  Calc: with accessory > 0, autonomy_min strictly less than identical
      state with 0 (same battery/motors)
  T6  Accessory 0 / absent -> autonomy unchanged vs pre-Buy fixture
  T7  Continuity CTA when power missing (mission intent)
  T8  Neutral project (no mission) -> no power CTA / no behavior change
  T9  Direct write of mirrored param still blocked (gatekeeper)
  T10 Full suite; 0.4.1
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import set_mission_component_power
from jarvis.core.mission_power_declare_assist import parse_mission_power_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState

_REPO_ROOT = Path(__file__).resolve().parent.parent

_CALC_BASE = {
    "vehicle_type": "aerial", "payload_kg": 1.0, "structure_mass_factor": 0.5,
    "safety_factor": 1.2, "motor_count": 4, "per_motor_max_thrust_n": 15.0,
    "battery_capacity_wh": 74.0, "motor_power_w": 120.0,
}


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _cameras(*, mass_g: float | None = 28.0, power_w: float | None = None) -> ComponentSpec:
    props = {"model": PropertyValue(value="runcam", confidence=0.8, source="declared")}
    if mass_g is not None:
        props["mass_g"] = PropertyValue(value=mass_g, unit="g", confidence=0.9, source="declared")
    if power_w is not None:
        props["power_w"] = PropertyValue(value=power_w, unit="W", confidence=0.9, source="declared")
    return ComponentSpec(suggested_key="cameras", completeness="medium", properties=props)


def _radio(*, mass_g: float | None = 3.0, power_w: float | None = None) -> ComponentSpec:
    props = {"model": PropertyValue(value="elrs", confidence=0.8, source="declared")}
    if mass_g is not None:
        props["mass_g"] = PropertyValue(value=mass_g, unit="g", confidence=0.9, source="declared")
    if power_w is not None:
        props["power_w"] = PropertyValue(value=power_w, unit="W", confidence=0.9, source="declared")
    return ComponentSpec(suggested_key="radio_module", completeness="medium", properties=props)


def _state(**components) -> ProjectState:
    return ProjectState(
        project_id="p", project_slug="p", objective="dron de vigilancia", workspace_path="w",
        current_parameters={"payload_kg": 1.0}, design_properties=DesignProperties(components=components),
    )


def _reasoning_context(objective="prueba", margin=1.0, parsed_constraints=None):
    return {
        "objective": objective,
        "current_parameters": {"restrictions": "no", "payload_kg": 1.0, "mission_payload_mass_kg": 0.031},
        "design_properties": {"components": {}, "structure": {}},
        "last_calculation": None, "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {}, "last_mutation": None, "mutation_mode": None,
        "parsed_constraints": parsed_constraints or {},
    }


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_parse_camera_watts():
    result = parse_mission_power_declare("cámara 1 W")
    assert result.kind == "SET"
    assert result.component_key == "cameras"
    assert result.power_w == pytest.approx(1.0)

    result2 = parse_mission_power_declare("declara la cámara 1.0W")
    assert result2.kind == "SET"
    assert result2.power_w == pytest.approx(1.0)


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_parse_radio_watts():
    result = parse_mission_power_declare("radio 3 W")
    assert result.kind == "SET"
    assert result.component_key == "radio_module"
    assert result.power_w == pytest.approx(3.0)

    result2 = parse_mission_power_declare("elrs 0.5 vatios")
    assert result2.kind == "SET"
    assert result2.component_key == "radio_module"
    assert result2.power_w == pytest.approx(0.5)


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_missing_identity_honest_refuse(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "dron de vigilancia",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    result = orch.handle_user_text("cámara 1 W", _RefuseLLM())
    assert result["status"] == "error"
    assert "cámara" in result["message"]
    assert "declara primero" in result["message"]


def test_t3_writer_raises_when_component_absent():
    state = _state()
    with pytest.raises(ValueError):
        set_mission_component_power(state, "cameras", 1.0)


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_mirror_sums_declared_watts():
    state = _state(cameras=_cameras(), radio_module=_radio())
    state = set_mission_component_power(state, "cameras", 1.0)
    assert state.current_parameters["mission_accessory_power_w"] == pytest.approx(1.0)
    state = set_mission_component_power(state, "radio_module", 0.5)
    assert state.current_parameters["mission_accessory_power_w"] == pytest.approx(1.5)
    # Clearing recomputes from scratch, never an incremental subtract.
    state = set_mission_component_power(state, "cameras", None)
    assert state.current_parameters["mission_accessory_power_w"] == pytest.approx(0.5)


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_accessory_power_strictly_lowers_autonomy():
    eng = CalculationEngine()
    baseline = eng.build(_CALC_BASE)
    with_accessory = eng.build({**_CALC_BASE, "mission_accessory_power_w": 1.5})
    assert baseline.autonomy_min is not None
    assert with_accessory.autonomy_min is not None
    assert with_accessory.autonomy_min < baseline.autonomy_min


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_zero_or_absent_accessory_matches_pre_buy_autonomy():
    eng = CalculationEngine()
    absent = eng.build(_CALC_BASE)
    explicit_zero = eng.build({**_CALC_BASE, "mission_accessory_power_w": 0.0})
    assert absent.autonomy_min == pytest.approx(explicit_zero.autonomy_min)
    # Byte-identical to the exact pre-Buy formula: Wh / (motor_power_w * motors) * 60.
    expected = (_CALC_BASE["battery_capacity_wh"] / (_CALC_BASE["motor_power_w"] * _CALC_BASE["motor_count"])) * 60.0
    assert absent.autonomy_min == pytest.approx(round(expected, 4))


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_continuity_cta_when_power_missing():
    context = _reasoning_context(
        objective="dron de vigilancia", margin=3.6196, parsed_constraints={"autonomy_min": 8.0},
    )
    context["design_properties"]["components"] = {
        "cameras": {"completeness": "medium", "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}}},
        "radio_module": {"completeness": "medium", "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}}},
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara potencia de cámara (W)"
    assert out.suggested_actions[0].action_type == "declare_mission_power"


def test_t7_radio_power_is_next_hole_after_camera_power_set():
    context = _reasoning_context(
        objective="dron de vigilancia", margin=3.6196, parsed_constraints={"autonomy_min": 8.0},
    )
    context["design_properties"]["components"] = {
        "cameras": {
            "completeness": "medium",
            "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}, "power_w": {"value": 1.0}},
        },
        "radio_module": {"completeness": "medium", "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}}},
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara potencia de radio (W)"


def test_t7_both_power_declared_reaches_margin_review():
    """B1-mission-vtx-identity note: reaching the terminal margin-review
    step now also requires `vtx` declared (its own ladder step, after
    power) — added here to keep testing this test's own concern (the power
    step clearing), not the newer vtx step."""
    context = _reasoning_context(
        objective="dron de vigilancia", margin=3.6196, parsed_constraints={"autonomy_min": 8.0},
    )
    context["design_properties"]["components"] = {
        "cameras": {
            "completeness": "medium",
            "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}, "power_w": {"value": 1.0}},
        },
        "radio_module": {
            "completeness": "medium",
            "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}, "power_w": {"value": 0.5}},
        },
        "vtx": {
            "completeness": "high",
            "properties": {"model": {"value": "hglrc"}, "mass_g": {"value": 4.8}},
        },
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Revisar margen vs carga de misión"
    assert out.suggested_actions[0].action_type != "increase_payload"


# ── T8 ────────────────────────────────────────────────────────────────────


def test_t8_neutral_project_no_power_cta_no_behavior_change():
    context = _reasoning_context(objective="prueba", margin=3.0)
    context["current_parameters"]["mission_payload_mass_kg"] = 0.0
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Aumentar carga útil"
    assert out.suggested_actions[0].action_type == "increase_payload"
    assert not any(a.action_type == "declare_mission_power" for a in out.suggested_actions)


# ── T9 ────────────────────────────────────────────────────────────────────


def test_t9_direct_mission_accessory_power_write_blocked(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "dron de vigilancia",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    orch.handle_user_text("cámara RunCam", _RefuseLLM())
    orch.handle_user_text("cámara 1 W", _RefuseLLM())

    orch.param_definition_session.apply_and_recalculate({"mission_accessory_power_w": 99.0})

    state = orch.state_manager.load_active_project(orch.workspace_manager)
    # Direct override is silently dropped (mirrored param, no bridge branch
    # for this key) — the mirror still reflects only the declared watts.
    assert state.current_parameters.get("mission_accessory_power_w") == pytest.approx(1.0)


# ── T10 ───────────────────────────────────────────────────────────────────


def test_t10_package_checkpoint_version():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match is not None
    assert match.group(1) == "0.4.1"


# ── Extra: never invent from model / mA citation ───────────────────────────


def test_never_invent_watts_from_identity_alone():
    """Regression guard mirroring mission_mass_declare_assist's own T7:
    a bare identity phrase ('cámara RunCam') must never be swallowed as an
    INCOMPLETE power declare.

    SUPERSEDED boundary (`B1-catalog-camera-power-w`, 2026-09-18): this test
    originally also asserted `bind_camera_from_catalog("runcam_phoenix_2")`
    carried no `power_w` at all — that follow-on Buy deliberately added an
    Engineer-locked `power_w=1.0` (P=I×V from the row's own cited mA@V) as
    an explicit JSON field on the seed row, projected the same way
    `mass_g` already is. The boundary that still holds — verified below —
    is that this is a structured JSON field read at load time, never a
    runtime parse of `source_note`'s free-text mA citation, and a row
    without an explicit `power_w` field still gets none invented."""
    assert parse_mission_power_declare("cámara RunCam").kind == "NONE"
    assert parse_mission_power_declare("radio ELRS").kind == "NONE"

    from jarvis.core.catalog_bind import bind_camera_from_catalog

    bound = bind_camera_from_catalog("runcam_phoenix_2")
    assert bound.properties["power_w"].value == pytest.approx(1.0)


def test_row_without_power_w_field_still_invents_nothing(tmp_path: Path):
    """The actual surviving 'never invent' boundary: a camera row with no
    explicit power_w JSON field (e.g. every camera seeded before this Buy,
    or a future row the Engineer hasn't cited power for yet) gets no
    power_w projected — never derived from its own mA@V source_note text,
    never a default, never copied from a sibling row."""
    from jarvis.core.catalog_bind import bind_camera_from_catalog
    from jarvis.knowledge.library import ComponentLibrary

    cameras_dir = tmp_path / "cameras"
    cameras_dir.mkdir()
    (cameras_dir / "_datos.json").write_text(
        '{"no_power_cam": {"manufacturer": "X", "model": "1", '
        '"length_mm": 10.0, "width_mm": 10.0, "height_mm": 10.0, "mass_g": 5.0, '
        '"source_note": "Current 300mA@5V per datasheet — no power_w field on this row."}}',
        encoding="utf-8",
    )
    lib = ComponentLibrary(library_root=tmp_path)
    bound = bind_camera_from_catalog("no_power_cam", library=lib)
    assert "power_w" not in bound.properties
