"""Top LiPo plate (`frame_plate_2`) envelope noun B1.

Covers implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md
§3/§4 — a dedicated noun ("placa lipo"/"placa top lipo"/"top lipo"/"top
lipo plate") that resolves to the plate whose OWN label normalizes to
exactly "top (lipo) plate" (live Rooster `frame_plate_2`), mirroring
"placa principal"/`_resolve_main_plate`. No writer allowlist change was
needed — `is_frame_plate_key` already covers any plate key. Fixture
numbers: plate 100/100 (H from cited thickness_mm 2). Never 230, never a
Rooster catalog seed.

  P1  Parser "declara la placa lipo 100 x 100 mm" -> SET frame_plate_2,
      height None (same two-number plate shape as Main Plate)
  P2  Apply path (writer, mirroring the existing thickness-fill
      convention): height_mm becomes 2 from thickness_mm; thickness_mm
      itself untouched; projector box 100/100/2
  P3  "placa principal" still -> frame_plate (regression)
  P4  Bare "placa" with Main + Top LiPo declared -> AMBIGUOUS_PLATE
  P5  Pose writer accepts frame_plate_2 as origin AFTER it has a box
      triple; raises before (regression of the existing rule)
  P6  No length_mm/width_mm added to Rooster plate seeds in
      library/frames/_datos.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_envelope, set_component_declared_box_pose
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _plate_spec(label: str, thickness_mm: float) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=thickness_mm, unit="mm", source="declared"),
            "label": PropertyValue(value=label, source="declared"),
        },
    )


def _main_plate_spec() -> ComponentSpec:
    return _plate_spec("Main Plate", 4.0)


def _top_lipo_plate_spec() -> ComponentSpec:
    return _plate_spec("Top (LiPo) plate", 2.0)


def _live_components() -> dict:
    return {
        "frame_plate": _main_plate_spec(),
        "frame_plate_2": _top_lipo_plate_spec(),
        "frame": ComponentSpec(
            suggested_key="frame", completeness="high",
            properties={"wheelbase_mm": PropertyValue(value=230.0, unit="mm", source="declared")},
        ),
        "battery": ComponentSpec(suggested_key="battery", completeness="high", mounted_on="frame_plate_2"),
    }


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


@pytest.mark.parametrize("phrase", [
    "declara la placa lipo 100 x 100 mm",
    "declara la placa top lipo 100 x 100 mm",
    "declara la top lipo 100 x 100 mm",
    "declara la top lipo plate 100 x 100 mm",
])
def test_p1_top_lipo_nouns_resolve_to_frame_plate_2(phrase):
    components = _live_components()
    result = parse_declared_envelope_declare(phrase, components)
    assert result.kind == "SET"
    assert result.component_key == "frame_plate_2"
    assert (result.length_mm, result.width_mm) == (100.0, 100.0)
    assert result.height_mm is None  # parser never invents it — apply step reads thickness


def test_p2_apply_path_fills_height_from_thickness_and_preserves_it():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la placa lipo 100 x 100 mm", components)

    state = _state(components)
    thickness = state.design_properties.components["frame_plate_2"].properties["thickness_mm"].value
    updated = set_component_declared_box_envelope(
        state, result.component_key, result.length_mm, result.width_mm, thickness
    )
    plate2 = updated.design_properties.components["frame_plate_2"]
    assert plate2.properties["length_mm"].value == 100.0
    assert plate2.properties["width_mm"].value == 100.0
    assert plate2.properties["height_mm"].value == 2.0
    assert plate2.properties["thickness_mm"].value == 2.0  # untouched

    frame_wheelbase = updated.design_properties.components["frame"].properties["wheelbase_mm"].value
    assert frame_wheelbase == 230.0  # never stitched into the plate box

    nodes = {n["id"]: n for n in project_spatial_nodes(updated)}
    assert nodes["frame_plate_2"]["geometry"] == {
        "shape": "box", "length_mm": 100.0, "width_mm": 100.0, "height_mm": 2.0,
    }
    assert sum(1 for n in nodes.values() if n["id"] == "frame_plate_2") == 1


def test_p3_placa_principal_still_resolves_main_plate():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la placa principal 100 x 100 mm", components)
    assert result.kind == "SET"
    assert result.component_key == "frame_plate"


def test_p4_bare_placa_with_main_and_top_lipo_is_ambiguous():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la placa 100 x 100 mm", components)
    assert result.kind == "AMBIGUOUS_PLATE"
    keys = {k for k, _label in result.candidates}
    assert keys == {"frame_plate", "frame_plate_2"}


def test_p5_pose_writer_accepts_frame_plate_2_only_after_it_has_a_box():
    state = _state(_live_components())
    with pytest.raises(ValueError):
        set_component_declared_box_pose(
            state, "battery", DeclaredBoxPose(origin_key="frame_plate_2", z_mm=10.0)
        )

    with_box = set_component_declared_box_envelope(state, "frame_plate_2", 100.0, 100.0, 2.0)
    after_pose = set_component_declared_box_pose(
        with_box, "battery", DeclaredBoxPose(origin_key="frame_plate_2", z_mm=10.0)
    )
    pose = after_pose.design_properties.components["battery"].declared_box_pose
    assert pose.origin_key == "frame_plate_2"
    assert pose.z_mm == pytest.approx(10.0)


def test_p6_no_length_width_seed_on_rooster_plates():
    repo_root = Path(__file__).resolve().parents[1]
    frames_path = repo_root / "library" / "frames" / "_datos.json"
    frames_data = json.loads(frames_path.read_text(encoding="utf-8"))
    for sku, row in frames_data.items():
        plates = row.get("plates") or []
        for plate in plates:
            assert "length_mm" not in plate, f"{sku} plate {plate.get('label')} unexpectedly gained length_mm"
            assert "width_mm" not in plate, f"{sku} plate {plate.get('label')} unexpectedly gained width_mm"
