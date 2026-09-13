"""Mount standard assist B1 (CLI / IDLE).

Covers implementation_contract_mount_standard_assist_b1.md §2:
  T1  All in-scope edges undeclared -> full suggested list
  T2  Already-declared edge omitted
  T3  No frame_arm -> no motors->arm suggestion
  T4  Ambiguous multi-plate -> AMBIGUOUS, no silent pick
  T5  Every suggested example_phrase parses via parse_mounted_on_declare
      as SET; every ambiguous row's candidate phrase parses as SET too
      (once a single target key is named)
  T6  Full pytest green; package still 0.4.1 (checked at the repo level,
      not asserted here)

Plus orchestrator IDLE wiring (trigger phrases, empty-project honesty,
never-write-on-list-alone, non-regression of the mount-declare bridge).
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.mount_standard_assist import (
    build_mount_standard_checklist,
    format_mount_standard_checklist,
    is_mount_standard_assist_trigger,
)
from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _full_standard_components():
    """Every in-scope subject present, nothing declared yet — the "5min-
    shaped" fixture minus its existing declares, plus frame_arm so the
    motor->arm edge is in play too."""
    return {
        "propellers": ComponentSpec(suggested_key="propellers", completeness="high"),
        "motors": ComponentSpec(suggested_key="motors", completeness="high"),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "flight_controller": ComponentSpec(suggested_key="flight_controller", completeness="high"),
        "battery": ComponentSpec(suggested_key="battery", completeness="high"),
        "sensors": ComponentSpec(suggested_key="sensors", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    }


def _two_plate_components():
    return {
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "battery": ComponentSpec(suggested_key="battery", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Principal")},
        ),
        "frame_plate_2": ComponentSpec(
            suggested_key="frame_plate_2", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Top")},
        ),
    }


# ── T1: all in-scope edges undeclared ───────────────────────────────────


def test_t1_all_edges_undeclared_full_checklist():
    suggestions = build_mount_standard_checklist(_full_standard_components())
    subjects = {s.subject for s in suggestions}
    assert subjects == {"propellers", "motors", "esc", "flight_controller", "battery", "sensors"}
    assert all(s.kind == "suggested" for s in suggestions)

    by_subject = {s.subject: s for s in suggestions}
    assert by_subject["propellers"].target == "motors"
    assert by_subject["motors"].target == "frame_arm"
    assert by_subject["esc"].target == "frame_plate"
    assert by_subject["flight_controller"].target == "frame_plate"
    assert by_subject["battery"].target == "frame_plate"
    assert by_subject["sensors"].target == "frame_plate"


def test_t1_empty_project_no_suggestions():
    suggestions = build_mount_standard_checklist({})
    assert suggestions == []
    assert "no queda ninguno" in format_mount_standard_checklist(suggestions).lower()


# ── T2: already-declared edge omitted ───────────────────────────────────


def test_t2_5min_shaped_declared_edges_omitted():
    components = _full_standard_components()
    components["propellers"] = components["propellers"].model_copy(update={"mounted_on": "motors"})
    components["esc"] = components["esc"].model_copy(update={"mounted_on": "frame_plate"})
    suggestions = build_mount_standard_checklist(components)
    subjects = {s.subject for s in suggestions}
    assert "propellers" not in subjects
    assert "esc" not in subjects
    # motors->arm still missing on this fixture -> still suggested
    assert "motors" in subjects


def test_t2_stack_component_mounted_elsewhere_not_resuggested():
    """A subject already mounted on ANYTHING is considered declared for
    this coarse checklist — never suggested as a 'correction'."""
    components = _full_standard_components()
    components["sensors"] = components["sensors"].model_copy(update={"mounted_on": "esc"})
    suggestions = build_mount_standard_checklist(components)
    assert "sensors" not in {s.subject for s in suggestions}


# ── T3: no frame_arm -> no motors->arm suggestion ───────────────────────


def test_t3_no_frame_arm_skips_motor_arm_edge():
    components = _full_standard_components()
    del components["frame_arm"]
    suggestions = build_mount_standard_checklist(components)
    assert "motors" not in {s.subject for s in suggestions}


# ── T4: ambiguous multi-plate -> no silent pick ─────────────────────────


def test_t4_ambiguous_two_plates_no_silent_pick():
    suggestions = build_mount_standard_checklist(_two_plate_components())
    by_subject = {s.subject: s for s in suggestions}
    assert by_subject["esc"].kind == "ambiguous"
    assert set(by_subject["esc"].candidates) == {"frame_plate", "frame_plate_2"}
    assert by_subject["battery"].kind == "ambiguous"
    assert by_subject["esc"].target is None


def test_t4_ambiguous_subject_already_mounted_not_resuggested():
    components = _two_plate_components()
    components["esc"] = components["esc"].model_copy(update={"mounted_on": "frame_plate"})
    suggestions = build_mount_standard_checklist(components)
    assert "esc" not in {s.subject for s in suggestions}
    assert "battery" in {s.subject for s in suggestions}


# ── T5: suggested phrases actually parse ────────────────────────────────


def test_t5_every_suggested_phrase_parses_as_set():
    components = _full_standard_components()
    suggestions = build_mount_standard_checklist(components)
    for s in suggestions:
        assert s.kind == "suggested"
        result = parse_mounted_on_declare(s.example_phrase, components)
        assert result.kind == "SET", f"{s.example_phrase!r} -> {result.kind}"
        assert result.component_key == s.subject
        assert result.target_key == s.target


def test_t5_ambiguous_candidate_phrase_parses_as_set_once_named():
    components = _two_plate_components()
    suggestions = build_mount_standard_checklist(components)
    ambiguous = next(s for s in suggestions if s.subject == "esc")
    for candidate in ambiguous.candidates:
        phrase = f"esc montado en {candidate}"
        result = parse_mounted_on_declare(phrase, components)
        assert result.kind == "SET"
        assert result.target_key == candidate


# ── Trigger phrase recognition ──────────────────────────────────────────


def test_trigger_montajes_estandar():
    assert is_mount_standard_assist_trigger("montajes estándar")
    assert is_mount_standard_assist_trigger("Montajes Estandar")


def test_trigger_que_falta_montar():
    assert is_mount_standard_assist_trigger("¿qué falta montar?")


def test_trigger_unrelated_phrase_is_false():
    assert not is_mount_standard_assist_trigger("monta el fc en la placa")
    assert not is_mount_standard_assist_trigger("cual es el estado del proyecto")


# ── Orchestrator IDLE wiring ─────────────────────────────────────────────


def _project_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "mount standard assist b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_components = {**ps.design_properties.components, **components}
    updated_dp = ps.design_properties.model_copy(update={"components": updated_components})
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_idle_checklist_lists_missing_mounts_never_writes(tmp_path: Path):
    orch = _project_with_components(tmp_path, _full_standard_components())
    result = orch.handle_user_text("montajes estándar", _RefuseLLM())
    assert result["status"] == "ok"
    assert "hélices montadas en los motores" in result["message"]
    assert "motor montado en el brazo" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["propellers"].mounted_on is None
    assert ps.design_properties.components["motors"].mounted_on is None


def test_idle_checklist_shrinks_after_declaring_one(tmp_path: Path):
    orch = _project_with_components(tmp_path, _full_standard_components())
    orch.handle_user_text("hélices montadas en los motores", _RefuseLLM())
    result = orch.handle_user_text("qué falta montar", _RefuseLLM())
    assert "hélices montadas en los motores" not in result["message"]
    assert "motor montado en el brazo" in result["message"]


def test_idle_checklist_empty_project_honest_message(tmp_path: Path):
    orch = _project_with_components(tmp_path, {})
    result = orch.handle_user_text("montajes estándar", _RefuseLLM())
    assert result["status"] == "ok"
    assert "no queda ninguno" in result["message"].lower()
    # Disclaims ASSEMBLY READY / pose explicitly rather than staying silent
    # about what this checklist does NOT claim.
    assert "no es assembly ready" in result["message"].lower()


def test_non_regression_mount_declare_bridge_still_first(tmp_path: Path):
    """A literal 'monta X en Y' phrase must still hit the existing
    declare bridge, not the new checklist trigger."""
    components = _full_standard_components()
    orch = _project_with_components(tmp_path, components)
    result = orch.handle_user_text("monta el fc en la placa", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["flight_controller"].mounted_on == "frame_plate"
