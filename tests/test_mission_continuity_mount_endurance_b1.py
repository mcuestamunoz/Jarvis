"""Mission Continuity: mount + endurance B1 (`B1-mission-continuity-mount-
endurance`).

Covers implementation_contract_mission_continuity_mount_endurance_b1.md §2:

  T1  Parse camera mount phrase -> SET
  T2  Parse radio mount phrase -> SET
  T3  `montajes estándar` includes cámara row when unmounted+present
  T4  Continuity: masses set, camera unmounted -> top suggestion is mount-camera
  T5  Continuity: mounts done, no autonomy_min -> declare-autonomy-target
  T6  Continuity: mounts done + autonomy_min present -> soft margin OK,
      still no increase_payload
  T7  Neutral high-margin project -> increase_payload still available
  T8  ReasoningLayer does NOT introduce a second autonomy regex (assert
      shared helper/context field)
  T9  Ambiguous multi-plate: Continuity/mount does not invent a plate key
  T10 Full pytest green (checked at the repo level), package 0.4.1
"""
from __future__ import annotations

import re

from jarvis.core.mount_standard_assist import build_mount_standard_checklist
from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.schemas.action_schema import ComponentSpec


def _components_one_plate(**overrides):
    base = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "cameras": ComponentSpec(suggested_key="cameras", completeness="medium"),
        "radio_module": ComponentSpec(suggested_key="radio_module", completeness="medium"),
    }
    base.update(overrides)
    return base


def _components_two_plates():
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "frame_plate_2": ComponentSpec(
            suggested_key="frame_plate_2", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "cameras": ComponentSpec(suggested_key="cameras", completeness="medium"),
    }


# ── T1 / T2 ──────────────────────────────────────────────────────────────


def test_t1_parse_camera_mount_phrase_set():
    result = parse_mounted_on_declare("cámara montada en la placa", _components_one_plate())
    assert result.kind == "SET"
    assert result.component_key == "cameras"
    assert result.target_key == "frame_plate"


def test_t2_parse_radio_mount_phrase_set():
    result = parse_mounted_on_declare("radio montado en el frame", _components_one_plate())
    assert result.kind == "SET"
    assert result.component_key == "radio_module"
    assert result.target_key == "frame"


# ── T3 ───────────────────────────────────────────────────────────────────


def test_t3_montajes_estandar_includes_camera_row_when_unmounted_present():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "cameras": ComponentSpec(suggested_key="cameras", completeness="medium"),
    }
    checklist = build_mount_standard_checklist(components)
    rows = [r for r in checklist if r.subject == "cameras"]
    assert len(rows) == 1
    assert rows[0].kind == "suggested"
    assert rows[0].target == "frame_plate"
    assert rows[0].example_phrase == "cámara montada en la placa"


# ── Continuity context helper ───────────────────────────────────────────


def _context(objective, components, *, margin=3.6196, parsed_constraints=None, restrictions="no"):
    return {
        "objective": objective,
        "current_parameters": {"restrictions": restrictions},
        "design_properties": {"components": components, "structure": {}},
        "last_calculation": None,
        "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {},
        "last_mutation": None,
        "mutation_mode": None,
        "parsed_constraints": parsed_constraints if parsed_constraints is not None else {},
    }


def _mission_components(**overrides):
    # power_w/vtx included so every terminal-margin-review test in this
    # file still reaches it after B1-mission-power-w and B1-mission-vtx-
    # identity each inserted their own ladder step between autonomy-target
    # and margin review — tests that stop earlier (mount/autonomy) are
    # unaffected by their presence.
    base = {
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
    for key, value in overrides.items():
        if value is None:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _top_suggestion(context):
    out = ReasoningLayer().build(context)
    assert out.suggested_actions, "expected at least one suggested action"
    top = out.suggested_actions[0]
    return top.label, top.action_type, top.reason


# ── T4 ───────────────────────────────────────────────────────────────────


def test_t4_masses_set_camera_unmounted_top_suggestion_is_mount_camera():
    components = _mission_components()
    components["frame"] = {"completeness": "high", "properties": {}}
    components["frame_plate"] = {
        "completeness": "medium", "component_type": "structure_part",
        "parent_key": "frame", "properties": {},
    }
    label, action_type, reason = _top_suggestion(
        _context("dron de vigilancia doméstico", components)
    )
    assert label == "Monta la cámara en la placa/frame"
    assert action_type == "declare_mission_mount"
    assert "cámara montada en la placa" in reason


# ── T5 ───────────────────────────────────────────────────────────────────


def test_t5_mounts_done_no_autonomy_min_declare_autonomy_target():
    components = _mission_components()
    components["frame"] = {"completeness": "high", "properties": {}}
    components["frame_plate"] = {
        "completeness": "medium", "component_type": "structure_part",
        "parent_key": "frame", "mounted_on": None, "properties": {},
    }
    components["cameras"]["mounted_on"] = "frame_plate"
    components["radio_module"]["mounted_on"] = "frame_plate"
    label, action_type, reason = _top_suggestion(
        _context("dron de vigilancia doméstico", components)
    )
    assert label == "Declara autonomía objetivo (min)"
    assert action_type == "declare_autonomy_target"
    assert "restricciones" in reason


# ── T6 ───────────────────────────────────────────────────────────────────


def test_t6_mounts_and_autonomy_present_soft_margin_never_increase_payload():
    components = _mission_components()
    components["frame"] = {"completeness": "high", "properties": {}}
    components["frame_plate"] = {
        "completeness": "medium", "component_type": "structure_part",
        "parent_key": "frame", "properties": {},
    }
    components["cameras"]["mounted_on"] = "frame_plate"
    components["radio_module"]["mounted_on"] = "frame_plate"
    label, action_type, _ = _top_suggestion(
        _context(
            "dron de vigilancia doméstico",
            components,
            parsed_constraints={"autonomy_min": 8.0},
        )
    )
    assert label == "Revisar margen vs carga de misión"
    assert action_type != "increase_payload"


# ── T7 ───────────────────────────────────────────────────────────────────


def test_t7_neutral_high_margin_project_increase_payload_still_available():
    label, action_type, _ = _top_suggestion(_context("prueba", {}, margin=3.6196))
    assert label == "Aumentar carga útil"
    assert action_type == "increase_payload"


# ── T8 ───────────────────────────────────────────────────────────────────


def test_t8_reasoning_layer_never_introduces_second_autonomy_regex():
    """Static: reasoning_layer.py compiles no autonomy-oriented regex of
    its own (only `_MISSION_INTENT_RE` for mission-intent keyword
    matching) — the SAME authority as `state_schema._AUTONOMY_CONSTRAINT_RE`
    is never duplicated here."""
    import jarvis.core.reasoning_layer as reasoning_layer_module

    source = open(reasoning_layer_module.__file__, encoding="utf-8").read()
    assert "AUTONOMY_CONSTRAINT_RE" not in source
    assert re.search(r"\\d.*min", source) is None

    # Behavioral: restrictions text alone ("no" — explicit no-constraint)
    # never satisfies the autonomy step; only the passed-in
    # `context["parsed_constraints"]` field does, proving ReasoningLayer
    # reads the shared context field rather than re-deriving from
    # restrictions text itself.
    components = _mission_components()
    components["frame"] = {"completeness": "high", "properties": {}}
    components["frame_plate"] = {
        "completeness": "medium", "component_type": "structure_part",
        "parent_key": "frame", "properties": {},
    }
    components["cameras"]["mounted_on"] = "frame_plate"
    components["radio_module"]["mounted_on"] = "frame_plate"

    label_without, action_without, _ = _top_suggestion(
        _context(
            "dron de vigilancia doméstico", components,
            restrictions="vuelo 8 min", parsed_constraints={},
        )
    )
    assert action_without == "declare_autonomy_target"

    label_with, action_with, _ = _top_suggestion(
        _context(
            "dron de vigilancia doméstico", components,
            restrictions="no", parsed_constraints={"autonomy_min": 8.0},
        )
    )
    assert action_with != "declare_autonomy_target"


# ── T9 ───────────────────────────────────────────────────────────────────


def test_t9_ambiguous_multi_plate_never_invents_a_plate_key():
    result = parse_mounted_on_declare("cámara montada en la placa", _components_two_plates())
    assert result.kind == "AMBIGUOUS_TARGET"
    assert result.target_key is None
    assert {k for k, _ in result.candidates} == {"frame_plate", "frame_plate_2"}

    checklist = build_mount_standard_checklist(_components_two_plates())
    rows = [r for r in checklist if r.subject == "cameras"]
    assert len(rows) == 1
    assert rows[0].kind == "ambiguous"
    assert rows[0].target is None
    assert set(rows[0].candidates) == {"frame_plate", "frame_plate_2"}

    label, action_type, reason = _top_suggestion(
        _context(
            "dron de vigilancia doméstico",
            {
                "cameras": {
                    "completeness": "medium",
                    "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}},
                },
                "radio_module": {
                    "completeness": "medium",
                    "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}},
                },
                "frame": {"completeness": "high", "properties": {}},
                "frame_plate": {
                    "completeness": "medium", "component_type": "structure_part",
                    "parent_key": "frame", "properties": {},
                },
                "frame_plate_2": {
                    "completeness": "medium", "component_type": "structure_part",
                    "parent_key": "frame", "properties": {},
                },
            },
        )
    )
    assert label == "Elige placa para el montaje de misión (montajes estándar)"
    assert action_type == "declare_mission_mount"
    assert "montajes estándar" in reason
