"""Cited kit layout pack B1 (`B1-layout-pack-cited`).

Covers implementation_contract_geometry_layout_pack_cited_b1.md §2:
  T1  Filled fixture pack (hglrc_my5_flush_stack_b1) -> proposals match
      §0.1 Δmm / origins (recomputed live from the same Path F formula,
      not read back out of the frozen bag numbers)
  T2  List-alone never mutates ProjectState
  T3  Missing plate box + requires_plate_box=yes -> honest empty/skip
  T4  Disk origin rejected/skipped (writer not weakened) — defense in depth
  T5  Full pytest green; package 0.4.1 (checked at the repo level)

Fixture dims are the §0.1 bag's own live-project numbers (10-min-
autonomía, 2026-09-13 smoke): plate 120x55x2 (estimated_temporary), FC
H=7.8, ESC H=8.0, battery H=29.0, sensors H=14.4 -> z 4.9/5.0/15.5/8.2,
matching the bag's own worked-example floats exactly.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_pose
from jarvis.core.layout_pack_assist import (
    format_layout_pack,
    list_pack_ids,
    propose_layout_pack,
    resolve_layout_pack_trigger,
)
from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue

_PACK_ID = "hglrc_my5_flush_stack_b1"


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


def _bag_fixture_components() -> dict:
    """§0.1's own live-project numbers (10-min-autonomía, 2026-09-13)."""
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box_spec("frame_plate", 120.0, 55.0, 2.0, source="estimated_temporary"),
        "flight_controller": _box_spec("flight_controller", 41.6, 39.4, 7.8),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
        "battery": _box_spec("battery", 105.0, 35.0, 29.0),
        "sensors": _box_spec("sensors", 50.0, 50.0, 14.4),
    }


# ── T1: fixture pack proposals match §0.1's own worked-example Δmm ──────


def test_t1_proposals_match_bag_worked_example_z_values():
    components = _bag_fixture_components()
    rows = propose_layout_pack(_PACK_ID, components)
    by_subject = {r.subject: r for r in rows}
    assert all(r.kind == "proposed" for r in rows)
    assert all(r.origin_key == "frame_plate" for r in rows)

    # §0.1's own disclosed worked example: FC 4.9 / ESC 5.0 / battery 15.5 / sensors 8.2
    assert by_subject["flight_controller"].z_mm == pytest.approx(4.9)
    assert by_subject["esc"].z_mm == pytest.approx(5.0)
    assert by_subject["battery"].z_mm == pytest.approx(15.5)
    assert by_subject["sensors"].z_mm == pytest.approx(8.2)


def test_t1_pose_and_mount_phrases_parse_via_real_parsers():
    components = _bag_fixture_components()
    rows = propose_layout_pack(_PACK_ID, components)
    for row in rows:
        pose_result = parse_declared_box_pose_declare(row.example_pose_phrase, components)
        assert pose_result.kind == "SET"
        assert pose_result.component_key == row.subject
        assert pose_result.origin_key == "frame_plate"
        assert pose_result.z_mm == pytest.approx(row.z_mm)

        mount_result = parse_mounted_on_declare(row.example_mount_phrase, components)
        assert mount_result.kind == "SET"
        assert mount_result.component_key == row.subject
        assert mount_result.target_key == "frame_plate"


def test_t1_z_recomputed_live_not_frozen_bag_value():
    """The pack must never read a frozen z back out of its own registry —
    a live project with DIFFERENT real child heights gets a DIFFERENT,
    correctly-recomputed z, not the bag's worked example."""
    components = _bag_fixture_components()
    components["esc"] = _box_spec("esc", 30.0, 30.0, 4.0)  # different real ESC
    rows = propose_layout_pack(_PACK_ID, components)
    esc_row = next(r for r in rows if r.subject == "esc")
    assert esc_row.z_mm == pytest.approx(2.0 / 2 + 4.0 / 2)
    assert esc_row.z_mm != pytest.approx(5.0)


def test_unknown_pack_id_returns_empty():
    components = _bag_fixture_components()
    assert propose_layout_pack("no_existe_xyz", components) == []
    message = format_layout_pack("no_existe_xyz", [])
    assert "no conozco el pack" in message.lower()
    assert _PACK_ID in message


def test_list_pack_ids_includes_the_registered_pack():
    assert _PACK_ID in list_pack_ids()


# ── T2: list-alone never mutates ProjectState ────────────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "layout pack cited b1",
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


def test_t2_idle_pack_checklist_never_writes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _bag_fixture_components())
    result = orch.handle_user_text(f"aplicar layout {_PACK_ID}", _RefuseLLM())
    assert result["status"] == "ok"
    assert "declara la controladora" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    for key in ("esc", "flight_controller", "battery", "sensors"):
        spec = ps.design_properties.components[key]
        assert spec.declared_box_pose is None
        assert spec.mounted_on is None


def test_bare_layout_pack_trigger_resolves_the_only_registered_pack():
    assert resolve_layout_pack_trigger("layout pack") == _PACK_ID
    assert resolve_layout_pack_trigger(f"aplicar layout {_PACK_ID}") == _PACK_ID


def test_unrelated_phrase_is_not_a_trigger():
    assert resolve_layout_pack_trigger("montajes estándar") is None
    assert resolve_layout_pack_trigger("aplicar layout no_existe_xyz") is None


# ── T3: missing plate box -> honest empty/skip ───────────────────────────


def test_t3_no_plate_box_yields_empty_honest_message():
    components = _bag_fixture_components()
    components["frame_plate"] = ComponentSpec(
        suggested_key="frame_plate", component_type="structure_part", parent_key="frame"
    )  # thickness-only, no box
    rows = propose_layout_pack(_PACK_ID, components)
    assert rows == []
    message = format_layout_pack(_PACK_ID, rows)
    assert "nada que proponer" in message.lower()


def test_t3_idle_no_plate_box_honest_message(tmp_path: Path):
    components = _bag_fixture_components()
    del components["frame_plate"]
    orch = _orch_with_components(tmp_path, components)
    result = orch.handle_user_text("layout pack", _RefuseLLM())
    assert result["status"] == "ok"
    assert "nada que proponer" in result["message"].lower()


# ── T4: disk origin still rejected (defense in depth) ───────────────────


def test_t4_disk_origin_still_rejected_by_writer_directly(tmp_path: Path):
    """This pack always hardcodes origin_key=frame_plate (never a disk),
    but the underlying writer's own gate must still refuse a disk origin
    if ever attempted directly — proving this Buy did not weaken it."""
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


def test_pack_never_names_motors_or_propellers_or_frame_arm():
    """Locked exclusion list (§0.1's own "explicitly not in pack" section)
    — never invented into this or any future pack row."""
    components = _bag_fixture_components()
    components["motors"] = ComponentSpec(
        suggested_key="motors", completeness="high",
        properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
    )
    components["frame_arm"] = _box_spec("frame_arm", 50.0, 10.0, 5.0)
    rows = propose_layout_pack(_PACK_ID, components)
    assert "motors" not in {r.subject for r in rows}
    assert "propellers" not in {r.subject for r in rows}
    assert "frame_arm" not in {r.subject for r in rows}


# ── Already posed/mounted subjects drop out of the pack cleanly ─────────


def test_already_posed_and_mounted_subject_marked_done_not_reproposed():
    components = _bag_fixture_components()
    components["esc"] = components["esc"].model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0),
        "mounted_on": "frame_plate",
    })
    rows = propose_layout_pack(_PACK_ID, components)
    by_subject = {r.subject: r for r in rows}
    assert by_subject["esc"].kind == "done"
    assert by_subject["esc"].example_pose_phrase is None
    assert by_subject["esc"].example_mount_phrase is None
    assert by_subject["battery"].kind == "proposed"


def test_empty_list_means_prereq_unmet_never_everything_done():
    """A bare [] must only ever mean the plate-box prerequisite itself
    was unmet — "everything already done" is always represented by
    explicit "done" rows, so the two are never confused in the copy."""
    components = _bag_fixture_components()
    for key in ("flight_controller", "esc", "battery", "sensors"):
        components[key] = components[key].model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=1.0),
            "mounted_on": "frame_plate",
        })
    rows = propose_layout_pack(_PACK_ID, components)
    assert rows != []
    assert all(r.kind == "done" for r in rows)
    message = format_layout_pack(_PACK_ID, rows)
    assert "falta la caja" not in message.lower()
    assert "nada pendiente" in message.lower()


def test_already_posed_but_not_mounted_still_offers_mount_only():
    components = _bag_fixture_components()
    components["esc"] = components["esc"].model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0),
    })
    rows = propose_layout_pack(_PACK_ID, components)
    esc_row = next(r for r in rows if r.subject == "esc")
    assert esc_row.example_pose_phrase is None
    assert esc_row.example_mount_phrase is not None


# ── Boxless declared subject -> skipped with reason ─────────────────────


def test_boxless_subject_skipped_with_reason():
    components = _bag_fixture_components()
    components["sensors"] = ComponentSpec(
        suggested_key="sensors", completeness="medium",
        properties={"gps_model": PropertyValue(value="here3", confidence=0.9)},
    )
    rows = propose_layout_pack(_PACK_ID, components)
    by_subject = {r.subject: r for r in rows}
    assert by_subject["sensors"].kind == "skipped"
    assert by_subject["sensors"].reason
    assert by_subject["esc"].kind == "proposed"
