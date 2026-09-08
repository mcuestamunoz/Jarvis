"""Geometry-for-all B1 (sourced frame text enrichment).

Covers implementation_contract_geometry_for_all_b1.md §4:
  T1  Loader: TBS 5in standoffs -> two heights 30, 22; iFlight body 202/202
      + standoffs 25/32 with counts
  T2  bind_frame_from_catalog("iflight_xl7_v4_7in") -> root body_length/width 202
  T3  frame_part_specs_from_catalog TBS -> frame_standoff height_mm == "30 / 22"
  T4  iFlight parts -> standoff height string includes both 25 and 32
  T5  Armattan unchanged: no body_*; standoff still material-only (no height)
  T6  Projector: body-only frame -> geometry absent; standoff height-only -> geometry absent
  T7  Non-regression: existing plate/arm thickness projections still pass
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.domains.aerial import FRAME_ARM_KEY, FRAME_STANDOFF_KEY
from jarvis.knowledge.library import StandoffSeed, default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec


# ── T1: loader ───────────────────────────────────────────────────────────


def test_t1_tbs_5in_standoffs_two_heights():
    spec = default_library.get_frame("tbs_source_one_v5_5in")
    assert spec.standoffs == [StandoffSeed(height_mm=30.0), StandoffSeed(height_mm=22.0)]
    assert spec.body_length_mm is None
    assert spec.body_width_mm is None


def test_t1_iflight_body_and_standoffs_with_counts():
    spec = default_library.get_frame("iflight_xl7_v4_7in")
    assert spec.body_length_mm == pytest.approx(202.0)
    assert spec.body_width_mm == pytest.approx(202.0)
    assert spec.standoffs == [
        StandoffSeed(height_mm=25.0, count=4),
        StandoffSeed(height_mm=32.0, count=4),
    ]


# ── T2: root bind ────────────────────────────────────────────────────────


def test_t2_bind_iflight_projects_body_footprint_on_root():
    spec = bind_frame_from_catalog("iflight_xl7_v4_7in")
    assert spec.properties["body_length_mm"].value == pytest.approx(202.0)
    assert spec.properties["body_length_mm"].unit == "mm"
    assert spec.properties["body_width_mm"].value == pytest.approx(202.0)


def test_t2b_bind_tbs_5in_root_has_no_body_footprint():
    spec = bind_frame_from_catalog("tbs_source_one_v5_5in")
    assert "body_length_mm" not in spec.properties
    assert "body_width_mm" not in spec.properties


# ── T3/T4: standoff part projection ──────────────────────────────────────


def test_t3_tbs_5in_standoff_height_joined_string():
    parts = frame_part_specs_from_catalog("tbs_source_one_v5_5in")
    standoff = parts[FRAME_STANDOFF_KEY]
    assert standoff.properties["height_mm"].value == "30 / 22"
    assert standoff.properties["height_mm"].unit == "mm"
    assert standoff.parent_key == "frame"
    assert "material" not in standoff.properties
    assert "count" not in standoff.properties


def test_t4_iflight_standoff_height_includes_both_values():
    parts = frame_part_specs_from_catalog("iflight_xl7_v4_7in")
    standoff = parts[FRAME_STANDOFF_KEY]
    value = standoff.properties["height_mm"].value
    assert "25" in value and "32" in value
    assert value == "25 / 32"


# ── T5: Armattan unchanged ───────────────────────────────────────────────


def test_t5_armattan_root_unchanged_no_body_footprint():
    spec = bind_frame_from_catalog("armattan_rooster_5in")
    assert "body_length_mm" not in spec.properties
    assert "body_width_mm" not in spec.properties


def test_t5b_armattan_standoff_still_material_only_no_height():
    parts = frame_part_specs_from_catalog("armattan_rooster_5in")
    standoff = parts[FRAME_STANDOFF_KEY]
    assert standoff.properties["material"].value == "aluminio"
    assert "height_mm" not in standoff.properties


def test_t5c_tbs_7in_dc_unchanged_no_new_fields():
    """The other untouched row (§3.5 lock) — no body_*, no standoffs at all."""
    spec = default_library.get_frame("tbs_source_one_v5_1_7in_dc")
    assert spec.body_length_mm is None
    assert spec.body_width_mm is None
    assert spec.standoffs is None
    parts = frame_part_specs_from_catalog("tbs_source_one_v5_1_7in_dc")
    assert FRAME_STANDOFF_KEY not in parts


# ── T6: no false glyphs ──────────────────────────────────────────────────


def test_t6_body_footprint_alone_never_a_box_glyph():
    frame_spec = ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={
            "body_length_mm": PropertyValue(value=202.0, unit="mm", source="declared"),
            "body_width_mm": PropertyValue(value=202.0, unit="mm", source="declared"),
        },
    )
    assert _geometry_from_spec(frame_spec) is None


def test_t6b_standoff_height_alone_never_a_glyph():
    standoff_spec = ComponentSpec(
        suggested_key="frame_standoff", completeness="high",
        properties={"height_mm": PropertyValue(value="25 / 32", unit="mm", source="declared")},
    )
    assert _geometry_from_spec(standoff_spec) is None


# ── T7: non-regression ───────────────────────────────────────────────────


def test_t7_existing_arm_and_plate_thickness_projection_unchanged():
    parts = frame_part_specs_from_catalog("armattan_rooster_5in")
    assert parts[FRAME_ARM_KEY].properties["thickness_mm"].value == pytest.approx(4.0)
    assert parts[FRAME_ARM_KEY].properties["material"].value == "fibra de carbono"
    assert parts["frame_plate"].properties["label"].value == "Main Plate"
    assert parts["frame_plate"].properties["thickness_mm"].value == pytest.approx(4.0)
    assert parts["frame_plate_4"].properties["label"].value == "Small rear (top) plate"
