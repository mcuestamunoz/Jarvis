"""Craft montage Path F on plate B1 (`B1-craft-montage-path-f`).

Covers implementation_contract_geometry_craft_montage_path_f_b1.md §2:
  T1  Boxed frame_plate (declared source) + boxed FC/ESC -> proposals
      match the locked z formula; x=y=0; origin=frame_plate
  T2  Same with estimated_temporary plate dims -> proposals still
      emitted; disclaimer mentions ESTIMATED_TEMPORARY
  T3  No plate box -> empty proposals + honest message; no write
  T4  Two plate boxes, no unambiguous main -> AMBIGUOUS; no guess
  T5  Subject missing box -> skipped with reason; others still proposed
  T6  List-alone / suggest-only never mutates ProjectState
  T7  Confirm path (retype) calls the existing pose writer; disk origin
      still rejected if somehow proposed (defense-in-depth, direct writer check)
  T8  No MY5/10min/5min project-specific string branches in the assist module
  T9  Full pytest green; package 0.4.1 (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_pose
from jarvis.core.craft_montage_stack_assist import (
    StackProposal,
    format_path_f_stack,
    is_craft_montage_stack_trigger,
    propose_path_f_stack,
)
from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _box_spec(key: str, length_mm: float, width_mm: float, height_mm: float, *, source: str = "declared") -> ComponentSpec:
    return ComponentSpec(
        suggested_key=key, completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", confidence=0.9, source=source),
            "width_mm": PropertyValue(value=width_mm, unit="mm", confidence=0.9, source=source),
            "height_mm": PropertyValue(value=height_mm, unit="mm", confidence=0.9, source=source),
        },
    )


def _full_boxed_components(plate_source: str = "declared") -> dict:
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box_spec("frame_plate", 120.0, 55.0, 2.0, source=plate_source),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
        "flight_controller": _box_spec("flight_controller", 44.0, 84.0, 12.0),
        "battery": _box_spec("battery", 105.0, 35.0, 29.0),
        "sensors": _box_spec("sensors", 40.0, 40.0, 12.0),
    }


# ── T1: cited/declared plate box -> proposals match the locked formula ──


def test_t1_declared_plate_proposals_match_locked_formula():
    components = _full_boxed_components(plate_source="declared")
    proposals = propose_path_f_stack(components)
    assert {p.subject for p in proposals} == {"flight_controller", "esc", "battery", "sensors"}
    assert all(p.kind == "proposed" for p in proposals)
    by_subject = {p.subject: p for p in proposals}

    # z = plate.height_mm/2 + child.height_mm/2; x=y=0 always
    assert by_subject["esc"].x_mm == 0.0
    assert by_subject["esc"].y_mm == 0.0
    assert by_subject["esc"].z_mm == pytest.approx(2.0 / 2 + 8.0 / 2)
    assert by_subject["flight_controller"].z_mm == pytest.approx(2.0 / 2 + 12.0 / 2)
    assert by_subject["battery"].z_mm == pytest.approx(2.0 / 2 + 29.0 / 2)
    assert by_subject["sensors"].z_mm == pytest.approx(2.0 / 2 + 12.0 / 2)
    assert all(p.origin_key == "frame_plate" for p in proposals)
    # Disclaims VERIFICADO explicitly (honest "no VERIFICADO" disclaimer,
    # never a positive claim) — never mentions ESTIMATED_TEMPORARY when
    # the plate itself is a real declared/cited box.
    assert all("no VERIFICADO" in p.reason for p in proposals)
    assert all("ESTIMATED_TEMPORARY" not in p.reason for p in proposals)


def test_t1_example_phrases_parse_as_set_via_real_parser():
    components = _full_boxed_components()
    proposals = propose_path_f_stack(components)
    for p in proposals:
        result = parse_declared_box_pose_declare(p.example_pose_phrase, components)
        assert result.kind == "SET", f"{p.example_pose_phrase!r} -> {result.kind}"
        assert result.component_key == p.subject
        assert result.origin_key == p.origin_key
        assert result.x_mm == p.x_mm
        assert result.y_mm == p.y_mm
        assert result.z_mm == pytest.approx(p.z_mm)


# ── T2: estimated_temporary plate -> disclaimer discloses it ────────────


def test_t2_estimated_temporary_plate_still_proposes_with_disclosure():
    components = _full_boxed_components(plate_source="estimated_temporary")
    proposals = propose_path_f_stack(components)
    assert len(proposals) == 4
    assert all(p.kind == "proposed" for p in proposals)
    for p in proposals:
        assert "ESTIMATED_TEMPORARY" in p.reason
        assert "supuesto" in p.reason.lower()
    message = format_path_f_stack(proposals)
    assert "no VERIFICADO" in message
    assert "cabe" not in message.lower()


# ── T3: no plate box -> empty + honest message, no write ────────────────


def test_t3_no_plate_box_yields_empty_honest_message():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(suggested_key="frame_plate", component_type="structure_part", parent_key="frame"),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
    }
    proposals = propose_path_f_stack(components)
    assert proposals == []
    message = format_path_f_stack(proposals)
    assert "no hay una placa con caja declarada" in message.lower()


# ── T4: two plate boxes, no unambiguous main -> AMBIGUOUS ───────────────


def test_t4_two_boxed_plates_no_guess():
    components = _full_boxed_components()
    components["frame_plate_2"] = _box_spec("frame_plate_2", 80.0, 40.0, 3.0)
    proposals = propose_path_f_stack(components)
    assert len(proposals) == 1
    assert proposals[0].kind == "ambiguous"
    assert set(proposals[0].candidates) == {"frame_plate", "frame_plate_2"}
    message = format_path_f_stack(proposals)
    assert "varias placas" in message.lower()
    assert "frame_plate" in message and "frame_plate_2" in message


# ── T5: subject missing box -> skipped with reason; others still proposed ──


def test_t5_boxless_subject_skipped_others_still_proposed():
    components = _full_boxed_components()
    # sensors declared but no box (identity-only, e.g. just a gps_model string)
    components["sensors"] = ComponentSpec(
        suggested_key="sensors", completeness="medium",
        properties={"gps_model": PropertyValue(value="here3", confidence=0.9)},
    )
    proposals = propose_path_f_stack(components)
    by_subject = {p.subject: p for p in proposals}
    assert by_subject["sensors"].kind == "skipped"
    assert by_subject["sensors"].reason
    assert by_subject["esc"].kind == "proposed"
    assert by_subject["flight_controller"].kind == "proposed"
    assert by_subject["battery"].kind == "proposed"
    message = format_path_f_stack(proposals)
    assert "sensors" in message
    assert "esc" in message


def test_undeclared_subject_omitted_entirely():
    """A subject not declared at all (key absent) is neither proposed nor
    skipped-with-reason — just absent, same "nothing to say" honesty as a
    stub key."""
    components = _full_boxed_components()
    del components["sensors"]
    proposals = propose_path_f_stack(components)
    assert "sensors" not in {p.subject for p in proposals}


def test_already_posed_subject_marked_done_not_reproposed():
    """N1 fix: an already-posed subject gets an explicit 'done' row
    (never silently omitted) — so a project where ALL subjects are
    already posed doesn't collapse into an ambiguous empty list (see
    test_empty_list_means_no_plate_box_never_everything_done below)."""
    components = _full_boxed_components()
    components["esc"] = components["esc"].model_copy(
        update={"declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=99.0)}
    )
    proposals = propose_path_f_stack(components)
    by_subject = {p.subject: p for p in proposals}
    assert by_subject["esc"].kind == "done"
    assert by_subject["esc"].example_pose_phrase is None
    assert by_subject["battery"].kind == "proposed"


def test_empty_list_means_no_plate_box_never_everything_done():
    components = _full_boxed_components()
    for key in ("flight_controller", "esc", "battery", "sensors"):
        components[key] = components[key].model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=1.0),
        })
    proposals = propose_path_f_stack(components)
    assert proposals != []
    assert all(p.kind == "done" for p in proposals)
    message = format_path_f_stack(proposals)
    assert "no hay una placa con caja" not in message.lower()
    assert "nada pendiente" in message.lower()


# ── T6: suggest-only never mutates ProjectState ──────────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "craft montage path f b1",
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


def test_t6_idle_checklist_never_writes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _full_boxed_components())
    result = orch.handle_user_text("apilar en placa", _RefuseLLM())
    assert result["status"] == "ok"
    assert "declara la controladora" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    for key in ("esc", "flight_controller", "battery", "sensors"):
        assert ps.design_properties.components[key].declared_box_pose is None


def test_trigger_apilar_en_placa():
    assert is_craft_montage_stack_trigger("apilar en placa")
    assert is_craft_montage_stack_trigger("Apilar En Placa")


def test_trigger_proponer_stack_centrado():
    assert is_craft_montage_stack_trigger("¿proponer stack centrado?")


def test_trigger_unrelated_phrase_is_false():
    assert not is_craft_montage_stack_trigger("montajes estándar")
    assert not is_craft_montage_stack_trigger("declara el esc a 5 mm en z respecto a frame_plate")


# ── T7: confirm via retype calls the existing writer; disk still rejected ──


def test_t7_idle_retype_confirms_via_existing_pose_bridge(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _full_boxed_components())
    offer = orch.handle_user_text("apilar en placa", _RefuseLLM())
    assert offer["status"] == "ok"
    proposals = propose_path_f_stack(
        orch.state_manager.load_active_project(orch.workspace_manager).design_properties.components
    )
    esc_phrase = next(p.example_pose_phrase for p in proposals if p.subject == "esc")

    result = orch.handle_user_text(esc_phrase, _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    pose = ps.design_properties.components["esc"].declared_box_pose
    assert pose.origin_key == "frame_plate"
    assert pose.x_mm == 0.0 and pose.y_mm == 0.0
    assert pose.z_mm == pytest.approx(5.0)


def test_t7_disk_origin_still_rejected_by_writer_directly(tmp_path: Path):
    """Defense-in-depth: propose_path_f_stack never emits a disk origin
    (motors/propellers are never in _STACK_SUBJECTS and never chosen as
    origin), but the underlying writer's own gate must still refuse one if
    ever attempted directly — proving this Buy did not weaken it."""
    orch = _orch_with_components(tmp_path, {
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
        ),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError, match="no tiene una caja declarada"):
        set_component_declared_box_pose(
            ps, "esc", DeclaredBoxPose(origin_key="motors", x_mm=0.0, y_mm=0.0, z_mm=5.0)
        )


# ── T8: no project-specific string branches ──────────────────────────────


def test_t8_module_has_no_project_specific_literals():
    import inspect

    import jarvis.core.craft_montage_stack_assist as mod

    source = inspect.getsource(mod)
    for literal in ("my5", "hglrc", "10-min", "5min", "autonomía", "autonomia"):
        assert literal not in source.lower(), f"found project-specific literal: {literal!r}"


def test_t8_same_module_works_on_two_independently_built_fixtures():
    """Project-agnostic (lock #10): two totally distinct component sets
    (different dims, different plate source) both work through the exact
    same function with no branching."""
    fixture_a = _full_boxed_components(plate_source="declared")
    fixture_b = _full_boxed_components(plate_source="estimated_temporary")
    fixture_b["esc"] = _box_spec("esc", 30.0, 30.0, 5.0)  # different real dims

    proposals_a = propose_path_f_stack(fixture_a)
    proposals_b = propose_path_f_stack(fixture_b)
    assert len(proposals_a) == 4
    assert len(proposals_b) == 4
    esc_b = next(p for p in proposals_b if p.subject == "esc")
    assert esc_b.z_mm == pytest.approx(2.0 / 2 + 5.0 / 2)


# ── Non-goals: never proposes motors/propellers (Path N stays dead) ─────


def test_never_proposes_motors_or_propellers():
    components = _full_boxed_components()
    components["motors"] = ComponentSpec(
        suggested_key="motors", completeness="high",
        properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
    )
    components["propellers"] = ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={"diameter_mm": PropertyValue(value=127.0, unit="mm", confidence=0.9, source="declared")},
    )
    proposals = propose_path_f_stack(components)
    assert "motors" not in {p.subject for p in proposals}
    assert "propellers" not in {p.subject for p in proposals}
