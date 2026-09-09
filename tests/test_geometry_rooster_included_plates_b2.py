"""Rooster Included plates B2 (HD Cam + Rear VTX text; max_stack_height_mm).

Covers implementation_contract_geometry_rooster_included_plates_b2.md §3.1-3.4:
  T1  get_frame("armattan_rooster_5in").plates length 6; last two rows as
      seeded; first four unchanged
  T2  max_stack_height_mm == 22; other frame SKUs None
  T3  frame_part_specs_from_catalog has frame_plate_5/frame_plate_6,
      parent_key frame
  T4  bind_frame_from_catalog root has max_stack_height_mm 22; no
      height_mm/length_mm/width_mm/body_*
  T5  _geometry_from_spec(bound root) is None
  T6  synthetic ComponentSpec with only max_stack_height_mm -> None
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec

_SKU = "armattan_rooster_5in"


def test_t1_plates_length_six_first_four_unchanged_last_two_as_seeded():
    plates = default_library.get_frame(_SKU).plates
    assert len(plates) == 6

    assert plates[0].label == "Main Plate"
    assert plates[0].thickness_mm == pytest.approx(4.0)
    assert plates[0].material == "fibra de carbono"
    assert plates[1].label == "Top (LiPo) plate"
    assert plates[1].thickness_mm == pytest.approx(2.0)
    assert plates[2].label == "Small front (top) plate"
    assert plates[2].thickness_mm == pytest.approx(1.5)
    assert plates[3].label == "Small rear (top) plate"
    assert plates[3].thickness_mm == pytest.approx(1.5)

    assert plates[4].label == "HD Cam plate"
    assert plates[4].thickness_mm == pytest.approx(1.5)
    assert plates[4].material is None
    assert plates[5].label == "Rear VTX plates (Standard and TBS)"
    assert plates[5].thickness_mm == pytest.approx(2.0)
    assert plates[5].material is None


def test_t2_max_stack_height_mm_22_other_frames_none():
    assert default_library.get_frame(_SKU).max_stack_height_mm == pytest.approx(22.0)
    for other_sku in ("tbs_source_one_v5_5in", "tbs_source_one_v5_1_7in_dc", "iflight_xl7_v4_7in"):
        assert default_library.get_frame(other_sku).max_stack_height_mm is None


def test_t3_frame_part_specs_has_plate_5_and_6_with_parent_frame():
    parts = frame_part_specs_from_catalog(_SKU)
    plate_5 = parts["frame_plate_5"]
    plate_6 = parts["frame_plate_6"]
    assert plate_5.parent_key == "frame"
    assert plate_5.properties["label"].value == "HD Cam plate"
    assert plate_5.properties["thickness_mm"].value == pytest.approx(1.5)
    assert plate_6.parent_key == "frame"
    assert plate_6.properties["label"].value == "Rear VTX plates (Standard and TBS)"
    assert plate_6.properties["thickness_mm"].value == pytest.approx(2.0)


def test_t4_bind_root_has_max_stack_height_no_box_keys():
    spec = bind_frame_from_catalog(_SKU)
    assert spec.properties["max_stack_height_mm"].value == pytest.approx(22.0)
    assert spec.properties["max_stack_height_mm"].unit == "mm"
    assert "height_mm" not in spec.properties
    assert "length_mm" not in spec.properties
    assert "width_mm" not in spec.properties
    assert "body_length_mm" not in spec.properties
    assert "body_width_mm" not in spec.properties


def test_t5_geometry_from_spec_bound_root_is_none():
    spec = bind_frame_from_catalog(_SKU)
    assert _geometry_from_spec(spec) is None


def test_t6_synthetic_max_stack_height_only_yields_no_geometry():
    spec = ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={"max_stack_height_mm": PropertyValue(value=22.0, unit="mm", source="declared")},
    )
    assert _geometry_from_spec(spec) is None
