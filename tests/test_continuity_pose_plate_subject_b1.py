"""Pose Continuity subject: plates B1.

Covers implementation_contract_continuity_pose_plate_subject_b1.md §3 —
extends `declared_box_pose_declare_assist`'s subject (and, as a required
fallback for the origin segment — see the Deviation note in the
implementation report — origin) resolution to also recognize a frame-plate
noun (exact key, label, "placa principal"/"placa lipo"/"top lipo", bare
"placa"), reusing `declared_envelope_declare_assist.resolve_plate_subject_noun`
— the SAME noun set the envelope grammar already ships. No new noun table,
no writer change (`set_component_declared_box_pose`'s honesty rules are
untouched), no schema field.

  P1  "declara la placa lipo a 0 mm en z respecto a frame_plate" -> SET
      frame_plate_2, origin frame_plate, z=0
  P2  "declara frame_plate_2 a 0 mm en x y 0 mm en y y 15 mm en z respecto
      a la placa principal" -> SET (origin resolves specifically to Main
      Plate, not a spurious "which plate" ambiguity)
  P3  Envelope regression: "declara la placa lipo 100 x 100 mm" (no
      respecto) still envelope SET; pose parser returns NONE for the same
      phrase (mutually exclusive gates)
  P4  Electronics pose regression: "declara el esc a 5 mm en x respecto al
      fc" still SET esc
  P5  "quita la pose de la placa lipo" -> CLEAR frame_plate_2
  P6  Writer still rejects a pose whose origin is shapeless (frame_plate_2
      with no envelope declared) — regression of the existing rule
"""
from __future__ import annotations

import pytest

from jarvis.core.component_writers import set_component_declared_box_envelope, set_component_declared_box_pose
from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState


def _plate_spec(label: str, thickness_mm: float) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=thickness_mm, unit="mm", source="declared"),
            "label": PropertyValue(value=label, source="declared"),
        },
    )


def _fc_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        properties={
            "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        },
    )


def _live_components() -> dict:
    return {
        "frame_plate": _plate_spec("Main Plate", 4.0),
        "frame_plate_2": _plate_spec("Top (LiPo) plate", 2.0),
        "flight_controller": _fc_spec(),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
    }


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def test_p1_placa_lipo_a_0mm_en_z_respecto_a_frame_plate():
    components = _live_components()
    result = parse_declared_box_pose_declare(
        "declara la placa lipo a 0 mm en z respecto a frame_plate", components
    )
    assert result.kind == "SET"
    assert result.component_key == "frame_plate_2"
    assert result.origin_key == "frame_plate"
    assert result.z_mm == pytest.approx(0.0)
    assert result.x_mm is None
    assert result.y_mm is None


def test_p2_frame_plate_2_respecto_a_la_placa_principal():
    components = _live_components()
    result = parse_declared_box_pose_declare(
        "declara frame_plate_2 a 0 mm en x y 0 mm en y y 15 mm en z respecto a la placa principal",
        components,
    )
    assert result.kind == "SET"
    assert result.component_key == "frame_plate_2"
    assert result.origin_key == "frame_plate"
    assert (result.x_mm, result.y_mm, result.z_mm) == (0.0, 0.0, 15.0)


def test_p3_envelope_phrase_without_respecto_stays_envelope_shaped():
    components = _live_components()
    envelope_result = parse_declared_envelope_declare("declara la placa lipo 100 x 100 mm", components)
    assert envelope_result.kind == "SET"
    assert envelope_result.component_key == "frame_plate_2"

    pose_result = parse_declared_box_pose_declare("declara la placa lipo 100 x 100 mm", components)
    assert pose_result.kind == "NONE"


def test_p4_electronics_pose_regression_esc_respecto_fc():
    components = _live_components()
    result = parse_declared_box_pose_declare("declara el esc a 5 mm en x respecto al fc", components)
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.origin_key == "flight_controller"
    assert result.x_mm == pytest.approx(5.0)


def test_p5_quita_la_pose_de_la_placa_lipo_clears_frame_plate_2():
    components = _live_components()
    result = parse_declared_box_pose_declare("quita la pose de la placa lipo", components)
    assert result.kind == "CLEAR"
    assert result.component_key == "frame_plate_2"


def test_p6_writer_still_rejects_shapeless_plate_origin():
    state = _state(_live_components())
    with pytest.raises(ValueError):
        set_component_declared_box_pose(
            state, "battery", DeclaredBoxPose(origin_key="frame_plate_2", z_mm=0.0)
        )
    # ... and still succeeds once BOTH plates have a real box (the origin
    # frame_plate needs one too), per the already-shipped rule this Buy
    # does not touch.
    with_main_box = set_component_declared_box_envelope(state, "frame_plate", 150.0, 150.0, 4.0)
    with_box = set_component_declared_box_envelope(with_main_box, "frame_plate_2", 100.0, 100.0, 2.0)
    after_pose = set_component_declared_box_pose(
        with_box, "frame_plate_2", DeclaredBoxPose(origin_key="frame_plate", z_mm=0.0)
    )
    pose = after_pose.design_properties.components["frame_plate_2"].declared_box_pose
    assert pose.origin_key == "frame_plate"
