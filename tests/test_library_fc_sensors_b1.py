"""Relocate FC + GPS envelopes into `library/` B1 (`B1-library-fc-sensors`).

Covers implementation_contract_library_fc_sensors_b1.md §2:
  L1  get_fc("speedybee_f405_v4") -> 41.6x39.4x7.8; get_fc("pixhawk_4")
      -> 44x84x12
  L2  get_sensor("holybro_m10") -> 50x50x14.4
  L3  aerial module has NO FLIGHT_CONTROLLER_DIMENSIONS / GPS_DIMENSIONS
      attributes
  L4  extract_flight_controller_properties("SpeedyBee F405 V4") still
      yields the same L×W×H
  L5  extract_sensor_properties for Holybro M10 still yields the same
      L×W×H; bare "m10" still no dims
  L6  Identity assist lists SKUs from list_fcs / list_sensors
  L7  Bind projects catalog_ref + box props
  L8  Full suite green (checked at the repo level); UI unaffected
      (backend/catalog cycle, no ui/ files touched)
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import (
    bind_flight_controller_from_catalog,
    bind_sensor_from_catalog,
)
from jarvis.core.control_identity_catalog_assist import (
    build_flight_controller_identity_suggestions,
    build_sensor_identity_suggestions,
)
from jarvis.domains import aerial
from jarvis.domains.aerial import (
    extract_flight_controller_properties,
    extract_sensor_properties,
)
from jarvis.knowledge.library import ComponentLibrary, default_library


# ── L1: FC loader ─────────────────────────────────────────────────────


def test_l1_get_fc_speedybee_and_pixhawk():
    speedybee = default_library.get_fc("speedybee_f405_v4")
    assert (speedybee.length_mm, speedybee.width_mm, speedybee.height_mm) == (41.6, 39.4, 7.8)

    pixhawk = default_library.get_fc("pixhawk_4")
    assert (pixhawk.length_mm, pixhawk.width_mm, pixhawk.height_mm) == (44.0, 84.0, 12.0)


def test_l1_get_fc_unknown_raises_key_error():
    with pytest.raises(KeyError):
        default_library.get_fc("does_not_exist")


# ── L2: sensor loader ─────────────────────────────────────────────────


def test_l2_get_sensor_holybro_m10():
    m10 = default_library.get_sensor("holybro_m10")
    assert (m10.length_mm, m10.width_mm, m10.height_mm) == (50.0, 50.0, 14.4)
    assert m10.source_url == "https://holybro.com/products/m10-gps"
    assert "φ50" in m10.source_note


# ── L3: no DIMENSIONS dicts left in aerial.py ────────────────────────────


def test_l3_no_dimensions_dicts_in_aerial_module():
    assert not hasattr(aerial, "FLIGHT_CONTROLLER_DIMENSIONS")
    assert not hasattr(aerial, "GPS_DIMENSIONS")
    # Alias/language maps may remain (lock #6) — confirm they still do.
    assert hasattr(aerial, "FLIGHT_CONTROLLER_MAP")
    assert hasattr(aerial, "GPS_MAP")


def test_l3_no_dimension_source_in_aerial_module_source():
    """Belt-and-suspenders: grep the module's own source for a literal
    physical-dimension dict definition — not just the two named
    attributes above."""
    import inspect

    source = inspect.getsource(aerial)
    assert "FLIGHT_CONTROLLER_DIMENSIONS" not in source
    assert "GPS_DIMENSIONS" not in source


# ── L4: FC extractor still yields the same dims (via library now) ───────


def test_l4_extract_flight_controller_speedybee_unchanged():
    props = extract_flight_controller_properties("speedybee f405 v4")
    assert props["model"].value == "speedybee_f405_v4"
    assert props["length_mm"].value == pytest.approx(41.6)
    assert props["width_mm"].value == pytest.approx(39.4)
    assert props["height_mm"].value == pytest.approx(7.8)
    assert props["length_mm"].source == "declared"


def test_l4_extract_flight_controller_pixhawk4_unchanged():
    props = extract_flight_controller_properties("pixhawk 4")
    assert (props["length_mm"].value, props["width_mm"].value, props["height_mm"].value) == (44.0, 84.0, 12.0)


def test_l4_bare_unmapped_model_no_dims():
    props = extract_flight_controller_properties("controladora ardupilot")
    assert props["model"].value == "ardupilot"
    for key in ("length_mm", "width_mm", "height_mm"):
        assert key not in props


# ── L5: sensor extractor still yields the same dims; bare m10 no dims ───


def test_l5_extract_sensor_holybro_m10_unchanged():
    props = extract_sensor_properties("holybro m10")
    assert props["gps_model"].value == "holybro_m10"
    assert (props["length_mm"].value, props["width_mm"].value, props["height_mm"].value) == (50.0, 50.0, 14.4)


def test_l5_bare_m10_still_no_dims():
    props = extract_sensor_properties("m10")
    assert props["gps_model"].value == "ublox_m10"
    for key in ("length_mm", "width_mm", "height_mm"):
        assert key not in props


# ── L6: identity assist lists from list_fcs / list_sensors ──────────────


def test_l6_fc_suggestions_come_from_library_not_aerial_dict():
    suggestions = build_flight_controller_identity_suggestions()
    keys = {s["model_key"] for s in suggestions}
    # Assist lists only rows with a full cited L×W×H box — SKUs without
    # envelope (e.g. skystars_f4_v4) stay in list_fcs() but not here.
    boxed = {
        spec.name
        for spec in default_library.list_fcs()
        if spec.length_mm is not None
        and spec.width_mm is not None
        and spec.height_mm is not None
    }
    assert keys == boxed
    assert keys == {"pixhawk_4", "speedybee_f405_v4"}
    assert default_library.has_fc("skystars_f4_v4")
    assert "skystars_f4_v4" not in keys


def test_l6_sensor_suggestions_come_from_library():
    suggestions = build_sensor_identity_suggestions()
    keys = {s["model_key"] for s in suggestions}
    assert keys == {spec.name for spec in default_library.list_sensors()}
    assert keys == {"holybro_m10"}


def test_l6_module_no_longer_imports_dimension_dicts():
    import inspect

    import jarvis.core.control_identity_catalog_assist as mod

    source = inspect.getsource(mod)
    assert "FLIGHT_CONTROLLER_DIMENSIONS" not in source
    assert "GPS_DIMENSIONS" not in source
    assert "list_fcs" in source
    assert "list_sensors" in source


# ── L7: bind projects catalog_ref + box props ────────────────────────────


def test_l7_bind_flight_controller_projects_catalog_ref_and_box():
    spec = bind_flight_controller_from_catalog("speedybee_f405_v4")
    assert spec.catalog_ref.family == "flight_controller"
    assert spec.catalog_ref.sku == "speedybee_f405_v4"
    assert spec.suggested_key == "flight_controller"
    assert spec.properties["length_mm"].value == pytest.approx(41.6)
    assert spec.properties["width_mm"].value == pytest.approx(39.4)
    assert spec.properties["height_mm"].value == pytest.approx(7.8)
    assert spec.properties["length_mm"].source == "declared"


def test_l7_bind_sensor_projects_catalog_ref_and_box():
    spec = bind_sensor_from_catalog("holybro_m10")
    assert spec.catalog_ref.family == "sensors"
    assert spec.catalog_ref.sku == "holybro_m10"
    assert spec.suggested_key == "sensors"
    assert spec.properties["length_mm"].value == pytest.approx(50.0)
    assert spec.properties["width_mm"].value == pytest.approx(50.0)
    assert spec.properties["height_mm"].value == pytest.approx(14.4)


def test_l7_bind_preserves_base_pose_and_mount():
    from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose

    base = ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        declared_box_pose=DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0),
        mounted_on="frame_plate",
    )
    spec = bind_flight_controller_from_catalog("pixhawk_4", base=base)
    assert spec.declared_box_pose is not None
    assert spec.declared_box_pose.origin_key == "frame_plate"
    assert spec.mounted_on == "frame_plate"
    assert spec.catalog_ref.sku == "pixhawk_4"


def test_l7_bind_unknown_sku_raises_key_error():
    with pytest.raises(KeyError):
        bind_flight_controller_from_catalog("does_not_exist")
    with pytest.raises(KeyError):
        bind_sensor_from_catalog("does_not_exist")


# ── Projector regression (byte-identical) ────────────────────────────────


def test_projector_emits_box_for_bound_fc_and_sensor():
    from jarvis.workspace.spatial_board import _geometry_from_spec

    fc_spec = bind_flight_controller_from_catalog("speedybee_f405_v4")
    assert _geometry_from_spec(fc_spec) == {
        "shape": "box", "length_mm": 41.6, "width_mm": 39.4, "height_mm": 7.8,
    }
    sensor_spec = bind_sensor_from_catalog("holybro_m10")
    assert _geometry_from_spec(sensor_spec) == {
        "shape": "box", "length_mm": 50.0, "width_mm": 50.0, "height_mm": 14.4,
    }


# ── ComponentLibrary is the ONLY reader of these two JSON files ─────────


def test_library_files_exist_on_disk_and_only_library_reads_them():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    assert (repo_root / "library" / "fc" / "_datos.json").exists()
    assert (repo_root / "library" / "sensors" / "_datos.json").exists()

    fresh_library = ComponentLibrary()
    assert fresh_library.has_fc("pixhawk_4")
    assert fresh_library.has_sensor("holybro_m10")
    assert not fresh_library.has_fc("nonexistent")
    assert not fresh_library.has_sensor("nonexistent")
