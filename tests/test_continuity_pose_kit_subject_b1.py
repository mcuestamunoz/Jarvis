"""Pose Continuity subject: kit keys B1.

Covers implementation_contract_continuity_pose_kit_subject_b1.md §3 —
extends `declared_box_pose_declare_assist`'s subject resolution with a
third tier (after electronics, then plates): presence-gated kit keys
(`power_connector`/`signal_harness`), reusing the SAME noun set the
envelope grammar already ships via the newly-public
`declared_envelope_declare_assist.resolve_kit_subject_noun` — no new noun
table, no writer change, no schema field. Fixed precedence: electronics ->
plate -> kit.

  P1  "declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a
      frame_plate" -> SET power_connector
  P2  "declara el harness a 0 mm en x y 0 mm en y y 5 mm en z respecto a
      frame_plate" -> SET signal_harness
  P3  "xt60" / "cable de senal" nouns resolve the same keys when present
  P4  Kit noun with the key missing -> INCOMPLETE (never invented)
  P5  Electronics + plate pose regressions still SET
  P6  Envelope phrase (no "respecto") still pose NONE
"""
from __future__ import annotations

import pytest

from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _frame_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Main Plate", source="declared"),
        },
    )


def _top_lipo_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate_2", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=2.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Top (LiPo) plate", source="declared"),
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
        "frame_plate": _frame_plate_spec(),
        "frame_plate_2": _top_lipo_plate_spec(),
        "flight_controller": _fc_spec(),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "power_connector": ComponentSpec(suggested_key="power_connector", completeness="medium", name="XT60"),
        "signal_harness": ComponentSpec(suggested_key="signal_harness", completeness="medium"),
    }


def test_p1_conector_respecto_a_frame_plate_sets_power_connector():
    components = _live_components()
    result = parse_declared_box_pose_declare(
        "declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate", components
    )
    assert result.kind == "SET"
    assert result.component_key == "power_connector"
    assert result.origin_key == "frame_plate"
    assert (result.x_mm, result.y_mm, result.z_mm) == (0.0, 0.0, 5.0)


def test_p2_harness_respecto_a_frame_plate_sets_signal_harness():
    components = _live_components()
    result = parse_declared_box_pose_declare(
        "declara el harness a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate", components
    )
    assert result.kind == "SET"
    assert result.component_key == "signal_harness"
    assert result.origin_key == "frame_plate"
    assert (result.x_mm, result.y_mm, result.z_mm) == (0.0, 0.0, 5.0)


@pytest.mark.parametrize("phrase,expected_key", [
    ("declara el xt60 a 0 mm en x respecto a frame_plate", "power_connector"),
    ("declara el cable de senal a 0 mm en x respecto a frame_plate", "signal_harness"),
])
def test_p3_alternate_kit_nouns_resolve_when_key_present(phrase, expected_key):
    components = _live_components()
    result = parse_declared_box_pose_declare(phrase, components)
    assert result.kind == "SET"
    assert result.component_key == expected_key


def test_p4_kit_noun_with_missing_key_is_incomplete_not_invented():
    result = parse_declared_box_pose_declare(
        "declara el conector a 0 mm en x respecto a frame_plate", {}
    )
    assert result.kind == "INCOMPLETE"
    assert result.component_key is None


def test_p5_electronics_and_plate_pose_regressions_still_set():
    components = _live_components()

    esc_result = parse_declared_box_pose_declare("declara el esc a 5 mm en x respecto al fc", components)
    assert esc_result.kind == "SET"
    assert esc_result.component_key == "esc"
    assert esc_result.origin_key == "flight_controller"

    plate_result = parse_declared_box_pose_declare(
        "declara la placa lipo a 0 mm en z respecto a frame_plate", components
    )
    assert plate_result.kind == "SET"
    assert plate_result.component_key == "frame_plate_2"
    assert plate_result.origin_key == "frame_plate"


def test_p6_envelope_phrase_without_respecto_stays_pose_none():
    components = _live_components()
    envelope_result = parse_declared_envelope_declare("declara el conector 30 x 20 x 10 mm", components)
    assert envelope_result.kind == "SET"
    assert envelope_result.component_key == "power_connector"

    pose_result = parse_declared_box_pose_declare("declara el conector 30 x 20 x 10 mm", components)
    assert pose_result.kind == "NONE"
