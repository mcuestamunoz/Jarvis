"""Declared sensors + kit envelope B1.

Covers implementation_contract_geometry_declared_sensors_kit_envelope_b1.md
§3/§4 — extends the existing declared-envelope writer + IDLE parser
(Declared battery envelope + Main Plate L×W B1) to also accept `sensors`
and the two kit keys `power_connector`/`signal_harness`. Engineer-typed
L×W×H only, `source=declared`. Fixture numbers are NOT catalog claims:
sensors 40/40/12, kit 30/20/10 and 30/10/5. Never GPS/XT60/cable marketing
dims, never `cable_length_options_mm` as `length_mm`.

  P1  Writer SET on sensors with 3 mm -> properties + source=declared
  P2  Writer SET on signal_harness / power_connector
  P3  Writer rejects esc / motors / frame (still ValueError)
  P4  Writer CLEAR sensors removes the three keys only
  P5  Parser "declara el gps ... 40 x 40 x 12 mm" -> SET sensors
  P6  Parser kit noun -> SET correct kit key when present in components
  P7  Parser pair-only on sensors -> INCOMPLETE
  P8  Parser "respecto" -> NONE
  P9  Battery + placa principal regression still SET as today
  P10 No library/kit_hardware or sensors seed gains length_mm
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_envelope
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState


def _sensors_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="sensors", completeness="medium",
        properties={"gps_model": PropertyValue(value="ublox_m9n", source="declared")},
        mounted_on="frame",
    )


def _power_connector_spec() -> ComponentSpec:
    return ComponentSpec(suggested_key="power_connector", completeness="medium", name="XT60")


def _signal_harness_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="signal_harness", completeness="medium",
        properties={
            "pin_count": PropertyValue(value=6, source="declared"),
            "pitch_mm": PropertyValue(value=1.0, unit="mm", source="declared"),
            "wire_gauge_awg": PropertyValue(value=26, unit="AWG", source="declared"),
        },
        catalog_ref=CatalogRef(family="kit_hardware", sku="pihut_jst_sh_6pin_cab1009"),
    )


def _main_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Main Plate", source="declared"),
        },
    )


def _battery_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="battery", completeness="high",
        properties={
            "battery_capacity_wh": PropertyValue(value=24.42, unit="Wh", source="declared"),
            "mass_g": PropertyValue(value=195.0, unit="g", source="declared"),
        },
        catalog_ref=CatalogRef(family="battery", sku="lipo_3s_2200mah"),
    )


def _live_components() -> dict:
    return {
        "sensors": _sensors_spec(),
        "power_connector": _power_connector_spec(),
        "signal_harness": _signal_harness_spec(),
        "frame_plate": _main_plate_spec(),
        "battery": _battery_spec(),
        "motors": ComponentSpec(suggested_key="motors", completeness="high"),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
    }


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def test_p1_writer_set_sensors_three_mm():
    state = _state(_live_components())
    updated = set_component_declared_box_envelope(state, "sensors", 40.0, 40.0, 12.0)
    sensors = updated.design_properties.components["sensors"]
    assert sensors.properties["length_mm"].value == 40.0
    assert sensors.properties["width_mm"].value == 40.0
    assert sensors.properties["height_mm"].value == 12.0
    assert sensors.properties["length_mm"].source == "declared"
    assert sensors.properties["gps_model"].value == "ublox_m9n"
    assert sensors.mounted_on == "frame"  # untouched


def test_p2_writer_set_kit_keys():
    state = _state(_live_components())

    updated_pc = set_component_declared_box_envelope(state, "power_connector", 30.0, 20.0, 10.0)
    pc = updated_pc.design_properties.components["power_connector"]
    assert pc.properties["length_mm"].value == 30.0
    assert pc.properties["width_mm"].value == 20.0
    assert pc.properties["height_mm"].value == 10.0
    assert pc.name == "XT60"  # untouched identity

    updated_sh = set_component_declared_box_envelope(state, "signal_harness", 30.0, 10.0, 5.0)
    sh = updated_sh.design_properties.components["signal_harness"]
    assert sh.properties["length_mm"].value == 30.0
    assert sh.properties["width_mm"].value == 10.0
    assert sh.properties["height_mm"].value == 5.0
    # kit identity/pin fields untouched
    assert sh.properties["pin_count"].value == 6
    assert sh.properties["pitch_mm"].value == 1.0
    assert sh.catalog_ref.sku == "pihut_jst_sh_6pin_cab1009"


def test_p3_writer_still_rejects_frame_root_arms_and_motors_esc():
    state = _state(_live_components())
    for bad_key in ("esc", "motors", "frame"):
        with pytest.raises(ValueError):
            set_component_declared_box_envelope(state, bad_key, 10.0, 10.0, 10.0)


def test_p4_writer_clear_sensors_removes_only_the_three_keys():
    state = _state(_live_components())
    with_box = set_component_declared_box_envelope(state, "sensors", 40.0, 40.0, 12.0)
    cleared = set_component_declared_box_envelope(with_box, "sensors", None, None, None)
    sensors = cleared.design_properties.components["sensors"]
    assert "length_mm" not in sensors.properties
    assert "width_mm" not in sensors.properties
    assert "height_mm" not in sensors.properties
    assert sensors.properties["gps_model"].value == "ublox_m9n"


def test_p5_parser_gps_phrase_sets_sensors():
    components = _live_components()
    result = parse_declared_envelope_declare("declara el gps 40 x 40 x 12 mm", components)
    assert result.kind == "SET"
    assert result.component_key == "sensors"
    assert (result.length_mm, result.width_mm, result.height_mm) == (40.0, 40.0, 12.0)


def test_p6_parser_kit_nouns_resolve_when_key_present():
    components = _live_components()

    r_connector = parse_declared_envelope_declare("declara el conector 30 x 20 x 10 mm", components)
    assert r_connector.kind == "SET"
    assert r_connector.component_key == "power_connector"

    r_xt60 = parse_declared_envelope_declare("declara el xt60 30 x 20 x 10 mm", components)
    assert r_xt60.kind == "SET"
    assert r_xt60.component_key == "power_connector"

    r_harness = parse_declared_envelope_declare("declara el harness 30 x 10 x 5 mm", components)
    assert r_harness.kind == "SET"
    assert r_harness.component_key == "signal_harness"

    r_cable = parse_declared_envelope_declare("declara el cable de senal 30 x 10 x 5 mm", components)
    assert r_cable.kind == "SET"
    assert r_cable.component_key == "signal_harness"

    # Missing key -> never invented: kit noun matches but no such component
    # declared -> treated as no subject (INCOMPLETE for a SET-shaped phrase).
    r_missing = parse_declared_envelope_declare("declara el conector 30 x 20 x 10 mm", {})
    assert r_missing.kind == "INCOMPLETE"


def test_p7_parser_pair_only_on_sensors_is_incomplete():
    components = _live_components()
    result = parse_declared_envelope_declare("declara el gps 40 x 40 mm", components)
    assert result.kind == "INCOMPLETE"
    assert result.component_key == "sensors"


def test_p8_parser_respecto_phrase_is_none():
    components = _live_components()
    result = parse_declared_envelope_declare(
        "declara el gps 40 x 40 x 12 mm respecto a frame_plate", components
    )
    assert result.kind == "NONE"


def test_p9_battery_and_placa_principal_regression_unchanged():
    components = _live_components()

    r_battery = parse_declared_envelope_declare("declara la bateria 80 x 34 x 22 mm", components)
    assert r_battery.kind == "SET"
    assert r_battery.component_key == "battery"
    assert (r_battery.length_mm, r_battery.width_mm, r_battery.height_mm) == (80.0, 34.0, 22.0)

    r_plate = parse_declared_envelope_declare("declara la placa principal 100 x 100 mm", components)
    assert r_plate.kind == "SET"
    assert r_plate.component_key == "frame_plate"
    assert (r_plate.length_mm, r_plate.width_mm) == (100.0, 100.0)
    assert r_plate.height_mm is None  # unchanged: orchestrator fills from thickness_mm


def test_p10_no_library_seed_gains_length_mm():
    repo_root = Path(__file__).resolve().parents[1]

    kit_data_path = repo_root / "library" / "kit_hardware" / "_datos.json"
    if kit_data_path.exists():
        kit_data = json.loads(kit_data_path.read_text(encoding="utf-8"))
        for sku, row in kit_data.items():
            assert "length_mm" not in row, f"{sku} unexpectedly gained length_mm"
            assert "width_mm" not in row, f"{sku} unexpectedly gained width_mm"
            assert "height_mm" not in row, f"{sku} unexpectedly gained height_mm"

    sensors_candidates = [
        repo_root / "library" / "sensores" / "_datos.json",
        repo_root / "library" / "sensors" / "_datos.json",
    ]
    for path in sensors_candidates:
        if path.exists():
            sensors_data = json.loads(path.read_text(encoding="utf-8"))
            for sku, row in sensors_data.items():
                assert "length_mm" not in row, f"{sku} unexpectedly gained length_mm"
