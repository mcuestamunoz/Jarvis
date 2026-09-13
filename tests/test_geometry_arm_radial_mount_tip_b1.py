"""Arm radial Visor + Mount tip/parse align B1
(`B1-arm-radial-visor` + `B1-mount-tip-parse-align`).

Covers implementation_contract_geometry_arm_radial_mount_tip_b1.md §2:

Part A — mount tip/parse:
  A1  Exact-key subject match on the SET path (flight_controller / sensors
      typed literally) parses as SET
  A2  Ambiguous-plate checklist tip uses the parseable Spanish noun
      (controladora / sensor / ...), never the bare component key
  A3  Singular "montaje estándar" trigger resolves the same as the plural
  A4  Non-regression: existing noun-based phrases still parse; CLEAR path
      is unchanged (still noun-only)

Part B — arm radial Visor (L-aware):
  B1  Motors/propellers/prop_adapter offsets stay the raw quad-X station
      points; frame_arm's own offsets differ
  B2  Fixture L<=R: center = station - unit*(L/2) (distal end at station)
  B3  Fixture L>R: center = unit*(R/2); the emitted box geometry still
      uses the declared L (never rescaled down to R)
  B4  yawDeg == atan2(station.y, station.x) in degrees, per station
  B5  Missing/invalid L, or gate fail (no wheelbase/count!=4) -> omit arm
      copies exactly as before this Buy
"""
from __future__ import annotations

import math

import pytest

from jarvis.core.mount_standard_assist import (
    build_mount_standard_checklist,
    format_mount_standard_checklist,
    is_mount_standard_assist_trigger,
)
from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import (
    _quad_x_station_points,
    _solid_copies,
    _solid_copy_offsets_mm,
)


def _box(key: str, length_mm: float, width_mm: float, height_mm: float) -> ComponentSpec:
    return ComponentSpec(
        suggested_key=key, completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", confidence=0.9, source="declared"),
            "width_mm": PropertyValue(value=width_mm, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=height_mm, unit="mm", confidence=0.9, source="declared"),
        },
    )


def _two_plate_components() -> dict:
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(suggested_key="frame_plate", component_type="structure_part", parent_key="frame"),
        "frame_plate_2": ComponentSpec(suggested_key="frame_plate_2", component_type="structure_part", parent_key="frame"),
        "flight_controller": ComponentSpec(suggested_key="flight_controller", completeness="high"),
        "sensors": ComponentSpec(suggested_key="sensors", completeness="high"),
    }


# ── Part A ────────────────────────────────────────────────────────────


def test_a1_exact_key_subject_parses_as_set():
    components = _two_plate_components()
    del components["frame_plate_2"]  # single plate -> unambiguous target
    r_fc = parse_mounted_on_declare("flight_controller montado en frame_plate", components)
    assert r_fc.kind == "SET"
    assert r_fc.component_key == "flight_controller"
    assert r_fc.target_key == "frame_plate"

    r_sensors = parse_mounted_on_declare("sensors montado en frame_plate", components)
    assert r_sensors.kind == "SET"
    assert r_sensors.component_key == "sensors"
    assert r_sensors.target_key == "frame_plate"


def test_a2_ambiguous_tip_uses_noun_not_bare_key():
    components = _two_plate_components()
    suggestions = build_mount_standard_checklist(components)
    message = format_mount_standard_checklist(suggestions)
    assert "controladora montada en <clave>" in message
    assert "sensor montado en <clave>" in message
    assert "flight_controller montado en <clave>" not in message
    assert "sensors montado en <clave>" not in message

    # And the tip itself parses once a real key replaces <clave>.
    by_subject = {s.subject: s for s in suggestions}
    parse_result = parse_mounted_on_declare("controladora montada en frame_plate", components)
    assert parse_result.kind == "SET"
    assert parse_result.component_key == by_subject["flight_controller"].subject


def test_a3_singular_montaje_trigger_matches_plural():
    assert is_mount_standard_assist_trigger("montaje estandar")
    assert is_mount_standard_assist_trigger("Montaje Estándar")
    assert is_mount_standard_assist_trigger("montajes estandar")


def test_a4_noun_based_phrases_still_parse_non_regression():
    components = _two_plate_components()
    del components["frame_plate_2"]
    result = parse_mounted_on_declare("controladora montada en frame_plate", components)
    assert result.kind == "SET"
    assert result.component_key == "flight_controller"


def test_a4_clear_path_unchanged_noun_only():
    components = {"flight_controller": ComponentSpec(suggested_key="flight_controller", completeness="high")}
    # A raw key CLEAR phrase is NOT locked in scope (SET-only per IC §0
    # lock #3) — must still fall through to NONE, proving CLEAR wasn't
    # silently widened as a side effect of the SET fix.
    result = parse_mounted_on_declare("quita el montaje de flight_controller", components)
    assert result.kind == "NONE"
    # The noun form still works, unchanged.
    result_noun = parse_mounted_on_declare("quita el montaje de la controladora", components)
    assert result_noun.kind == "CLEAR"
    assert result_noun.component_key == "flight_controller"


# ── Part B ────────────────────────────────────────────────────────────


def _quad_x_components(arm_length_mm: float | None, wheelbase_mm: float | None = 180.0, motor_count: float | None = 4) -> dict:
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high", properties={
            **({"configuration": PropertyValue(value="quad_x", confidence=0.9, source="declared")}),
            **({"wheelbase_mm": PropertyValue(value=wheelbase_mm, unit="mm", confidence=0.9, source="declared")} if wheelbase_mm is not None else {}),
        }),
        "motors": ComponentSpec(suggested_key="motors", completeness="high", properties={
            "diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared"),
            **({"motor_count": PropertyValue(value=motor_count, confidence=0.9, source="declared")} if motor_count is not None else {}),
        }),
    }
    if arm_length_mm is not None:
        components["frame_arm"] = _box("frame_arm", arm_length_mm, 10.0, 5.0)
    return components


def _radial_gap_mm(wheelbase_mm: float) -> float:
    a = wheelbase_mm / (2 * (2 ** 0.5))
    return math.hypot(a, a)


# ── B1: motors/propellers/prop_adapter unchanged; frame_arm differs ────


def test_b1_motors_propellers_prop_adapter_keep_raw_station_points():
    components = _quad_x_components(arm_length_mm=80.0)
    components["propellers"] = ComponentSpec(suggested_key="propellers", completeness="high", properties={
        "diameter_in": PropertyValue(value=5.1, unit="in", confidence=0.9, source="declared"),
    })
    components["prop_adapter"] = _box("prop_adapter", 12.0, 12.0, 8.0)

    stations = _quad_x_station_points(180.0)
    for key in ("motors", "propellers", "prop_adapter"):
        copies = _solid_copies(components[key], components)
        offsets = _solid_copy_offsets_mm(components[key], components, copies)
        assert offsets == stations

    arm_copies = _solid_copies(components["frame_arm"], components)
    arm_offsets = _solid_copy_offsets_mm(components["frame_arm"], components, arm_copies)
    assert arm_offsets != stations


# ── B2: L <= R -> distal end at the station ─────────────────────────────


def test_b2_l_less_equal_r_distal_end_at_station():
    wheelbase = 180.0
    R = _radial_gap_mm(wheelbase)
    L = 80.0
    assert L <= R
    components = _quad_x_components(arm_length_mm=L, wheelbase_mm=wheelbase)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    stations = _quad_x_station_points(wheelbase)

    for offset, station in zip(offsets, stations):
        sx, sy = station["xMm"], station["yMm"]
        radius = math.hypot(sx, sy)
        ux, uy = sx / radius, sy / radius
        expected_x = sx - ux * (L / 2)
        expected_y = sy - uy * (L / 2)
        assert offset["xMm"] == pytest.approx(expected_x)
        assert offset["yMm"] == pytest.approx(expected_y)


# ── B3: L > R -> centered on R/2; geometry L never rescaled ─────────────


def test_b3_l_greater_than_r_centers_on_half_gap_l_unchanged():
    wheelbase = 180.0
    R = _radial_gap_mm(wheelbase)
    L = 300.0
    assert L > R
    components = _quad_x_components(arm_length_mm=L, wheelbase_mm=wheelbase)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    stations = _quad_x_station_points(wheelbase)

    for offset, station in zip(offsets, stations):
        sx, sy = station["xMm"], station["yMm"]
        radius = math.hypot(sx, sy)
        ux, uy = sx / radius, sy / radius
        assert offset["xMm"] == pytest.approx(ux * (radius / 2))
        assert offset["yMm"] == pytest.approx(uy * (radius / 2))

    # The emitted box geometry itself is never shrunk to fit R.
    from jarvis.workspace.spatial_board import _geometry_from_spec
    geometry = _geometry_from_spec(components["frame_arm"])
    assert geometry["length_mm"] == 300.0


# ── B4: yaw = atan2(station.y, station.x) ───────────────────────────────


def test_b4_yaw_matches_atan2_station():
    wheelbase = 180.0
    components = _quad_x_components(arm_length_mm=80.0, wheelbase_mm=wheelbase)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    stations = _quad_x_station_points(wheelbase)

    for offset, station in zip(offsets, stations):
        expected_yaw = math.degrees(math.atan2(station["yMm"], station["xMm"]))
        assert offset["yawDeg"] == pytest.approx(expected_yaw)

    assert {round(o["yawDeg"]) for o in offsets} == {45, -45, -135, 135}


# ── B5: missing L / gate fail -> omit exactly as before ─────────────────


def test_b5_missing_length_mm_omits_offsets():
    components = _quad_x_components(arm_length_mm=None)
    components["frame_arm"] = ComponentSpec(
        suggested_key="frame_arm", completeness="low",
        properties={"diameter_mm": PropertyValue(value=10.0, unit="mm", confidence=0.5, source="declared")},
    )
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    assert offsets is None


def test_b5_no_wheelbase_omits_offsets_and_copies():
    components = _quad_x_components(arm_length_mm=80.0, wheelbase_mm=None)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    assert copies is None
    assert offsets is None


def test_b5_motor_count_not_four_omits_offsets_and_copies():
    components = _quad_x_components(arm_length_mm=80.0, motor_count=3)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    assert copies is None
    assert offsets is None


def test_b5_negative_or_zero_length_omits_offsets():
    components = _quad_x_components(arm_length_mm=None)
    components["frame_arm"] = _box("frame_arm", 0.0, 10.0, 5.0)
    copies = _solid_copies(components["frame_arm"], components)
    offsets = _solid_copy_offsets_mm(components["frame_arm"], components, copies)
    assert offsets is None


# ── No Continuity writer changes (lock #9) ──────────────────────────────


def test_no_new_frame_arm_pose_or_mount_writer_call():
    """Visor-only this Buy: the projector never touches declared_box_pose
    or mounted_on for frame_arm — confirmed by construction (the helper
    only reads geometry/frame facts, no ComponentSpec is mutated) and by
    re-checking the spec objects are unchanged after projection."""
    components = _quad_x_components(arm_length_mm=80.0)
    before = components["frame_arm"].model_copy(deep=True)
    _solid_copies(components["frame_arm"], components)
    _solid_copy_offsets_mm(components["frame_arm"], components, 4)
    assert components["frame_arm"] == before
    assert components["frame_arm"].declared_box_pose is None
    assert components["frame_arm"].mounted_on is None
