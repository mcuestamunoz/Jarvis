"""#4b Sourced FC + GPS envelopes B1.

Covers implementation_contract_geometry_sourced_fc_gps_b1.md §0/§3 — two
new identity-linked declared boxes from Engineer purchase-ground-truth
citations, same pattern `FLIGHT_CONTROLLER_DIMENSIONS`/`pixhawk_4` already
established (no `library/fc/`, no `library/sensors/`, no bind, no
`catalog_ref`): SpeedyBee F405 V4 (FC, 41.6x39.4x7.8mm) and Holybro M10
(GPS, new `GPS_DIMENSIONS` table, 50x50x14.4mm). A bare "f405"/"betaflight"
never picks up SpeedyBee's dims; a bare "m10" still resolves to
`ublox_m10` but WITHOUT dims — GPS_DIMENSIONS has no entry for it.

  T1  "SpeedyBee F405 V4" -> model=speedybee_f405_v4, 41.6/39.4/7.8
  T2  pixhawk_4 still 44/84/12; bare "betaflight"/"f405" no dims
  T3  "Holybro M10" -> gps_model=holybro_m10, 50/50/14.4
  T4  bare "m10" -> gps_model=ublox_m10, no L/W/H
  T5  Projector emits box geometry for both bound specs
"""
from __future__ import annotations

import pytest

from jarvis.domains.aerial import (
    GPS_DIMENSIONS,
    extract_flight_controller_properties,
    extract_sensor_properties,
)
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec


def test_t1_speedybee_f405_v4_dims():
    props = extract_flight_controller_properties("speedybee f405 v4")
    assert props["model"].value == "speedybee_f405_v4"
    assert props["length_mm"].value == pytest.approx(41.6)
    assert props["length_mm"].unit == "mm"
    assert props["length_mm"].source == "declared"
    assert props["width_mm"].value == pytest.approx(39.4)
    assert props["height_mm"].value == pytest.approx(7.8)

    # Shorter aliases also resolve to the same model + dims.
    for text in ("speedybee f405", "f405 v4"):
        props2 = extract_flight_controller_properties(text)
        assert props2["model"].value == "speedybee_f405_v4"
        assert props2["length_mm"].value == pytest.approx(41.6)


def test_t2_pixhawk4_regression_and_bare_terms_no_dims():
    props = extract_flight_controller_properties("pixhawk 4")
    assert props["length_mm"].value == pytest.approx(44.0)
    assert props["width_mm"].value == pytest.approx(84.0)
    assert props["height_mm"].value == pytest.approx(12.0)

    bare_betaflight = extract_flight_controller_properties("controladora betaflight")
    assert bare_betaflight["model"].value == "betaflight"
    for key in ("length_mm", "width_mm", "height_mm"):
        assert key not in bare_betaflight

    bare_f405 = extract_flight_controller_properties("f405")
    assert bare_f405 == {}


def test_t3_holybro_m10_dims():
    props = extract_sensor_properties("holybro m10")
    assert props["gps_model"].value == "holybro_m10"
    # Engineer SoT URL (holybro.com); HobbyDrone is corroboration only.
    urls = GPS_DIMENSIONS["holybro_m10"]["source_urls"]
    assert urls[0] == "https://holybro.com/products/m10-gps"
    assert "φ50" in GPS_DIMENSIONS["holybro_m10"]["source_note"]
    assert props["length_mm"].value == pytest.approx(50.0)
    assert props["length_mm"].unit == "mm"
    assert props["length_mm"].source == "declared"
    assert props["width_mm"].value == pytest.approx(50.0)
    assert props["height_mm"].value == pytest.approx(14.4)

    props_gps = extract_sensor_properties("holybro m10 gps")
    assert props_gps["gps_model"].value == "holybro_m10"
    assert props_gps["length_mm"].value == pytest.approx(50.0)


def test_t4_bare_m10_is_ublox_without_dims():
    props = extract_sensor_properties("m10")
    assert props["gps_model"].value == "ublox_m10"
    for key in ("length_mm", "width_mm", "height_mm"):
        assert key not in props


def test_t5_projector_emits_box_for_both():
    fc_props = extract_flight_controller_properties("speedybee f405 v4")
    fc_spec = ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        properties={
            "length_mm": PropertyValue(value=fc_props["length_mm"].value, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=fc_props["width_mm"].value, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=fc_props["height_mm"].value, unit="mm", source="declared"),
        },
    )
    assert _geometry_from_spec(fc_spec) == {
        "shape": "box", "length_mm": 41.6, "width_mm": 39.4, "height_mm": 7.8,
    }

    gps_props = extract_sensor_properties("holybro m10")
    gps_spec = ComponentSpec(
        suggested_key="sensors", completeness="medium",
        properties={
            "length_mm": PropertyValue(value=gps_props["length_mm"].value, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=gps_props["width_mm"].value, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=gps_props["height_mm"].value, unit="mm", source="declared"),
        },
    )
    assert _geometry_from_spec(gps_spec) == {
        "shape": "box", "length_mm": 50.0, "width_mm": 50.0, "height_mm": 14.4,
    }
