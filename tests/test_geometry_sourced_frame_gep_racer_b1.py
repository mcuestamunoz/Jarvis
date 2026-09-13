"""#4g Sourced frame GEPRC GEP-Racer B1 (P1 partial catalog seed).

Covers implementation_contract_geometry_sourced_frame_gep_racer_b1.md
§0/§3 — a new Class A frame SKU (`geprc_gep_racer_5in`) seeded from an
Engineer-provided purchase-ground-truth citation (Option A: new SKU;
`armattan_rooster_5in` untouched). `bind_frame_from_catalog`/
`frame_part_specs_from_catalog` project its root facts (wheelbase, body
footprint, mass, configuration) and curated part thicknesses/standoff
height exactly like the existing iFlight XL7 row already does — the
locked §0.1 honesty gate means NO plate/arm L×W and NO standoff Ø/section
are seeded (P1: catalog-only, per-part footprint stays UNKNOWN until a
future CAD/caliper Buy).

  T1  get_frame(new SKU) -> wheelbase 208, body 175x173, mass 78, arm
      thickness 5.0, three 2.0mm plates (Top/Aluminum/Bottom), one
      standoff height 24 count 4
  T2  bind_frame_from_catalog projects wheelbase_mm/body_*/mass_kg/
      configuration; frame_part_specs_from_catalog projects arm/plate/
      standoff thickness+label+height — never any L×W key
  T3  armattan_rooster_5in unchanged (still no body_length_mm/width_mm)
  T4  No length_mm/width_mm anywhere inside the catalog `plates[]` bag
      for the new SKU (PlateSeed has no such fields at all)
  T5  frame_standoff never carries a diameter/section key
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.knowledge.library import default_library

_NEW_SKU = "geprc_gep_racer_5in"


def test_t1_new_sku_bag():
    spec = default_library.get_frame(_NEW_SKU)
    assert spec.wheelbase_mm == pytest.approx(208.0)
    assert spec.body_length_mm == pytest.approx(175.0)
    assert spec.body_width_mm == pytest.approx(173.0)
    assert spec.mass_g == pytest.approx(78.0)
    assert spec.size_class_inch == pytest.approx(5.0)
    assert spec.configuration == "quad_x"
    assert spec.arm_thickness_mm == pytest.approx(5.0)
    assert spec.plates is not None and len(spec.plates) == 3
    labels = {p.label for p in spec.plates}
    assert labels == {"Top plate", "Aluminum plate", "Bottom plate"}
    for plate in spec.plates:
        assert plate.thickness_mm == pytest.approx(2.0)
    assert spec.standoffs is not None and len(spec.standoffs) == 1
    assert spec.standoffs[0].height_mm == pytest.approx(24.0)
    assert spec.standoffs[0].count == 4
    assert spec.manufacturer == "GEPRC"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "geprc.com" in spec.source_url


def test_t2_bind_projects_root_and_parts_no_lxw():
    bound = bind_frame_from_catalog(_NEW_SKU)
    assert bound.properties["wheelbase_mm"].value == pytest.approx(208.0)
    assert bound.properties["configuration"].value == "quad_x"
    assert bound.properties["body_length_mm"].value == pytest.approx(175.0)
    assert bound.properties["body_width_mm"].value == pytest.approx(173.0)
    assert bound.properties["mass_kg"].value == pytest.approx(0.078)
    assert bound.catalog_ref.family == "frame"
    assert bound.catalog_ref.sku == _NEW_SKU

    parts = frame_part_specs_from_catalog(_NEW_SKU)
    assert set(parts) == {"frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3", "frame_standoff"}
    for key, part_spec in parts.items():
        assert "length_mm" not in part_spec.properties
        assert "width_mm" not in part_spec.properties
    assert parts["frame_arm"].properties["thickness_mm"].value == pytest.approx(5.0)
    assert parts["frame_plate"].properties["label"].value == "Top plate"
    assert parts["frame_plate_2"].properties["label"].value == "Aluminum plate"
    assert parts["frame_plate_3"].properties["label"].value == "Bottom plate"
    assert parts["frame_standoff"].properties["height_mm"].value == pytest.approx(24.0)


def test_t3_rooster_unchanged():
    spec = default_library.get_frame("armattan_rooster_5in")
    assert spec.wheelbase_mm == pytest.approx(230.0)
    assert spec.mass_g == pytest.approx(125.0)
    assert spec.body_length_mm is None
    assert spec.body_width_mm is None
    assert spec.material == "fibra de carbono"


def test_t4_no_lxw_inside_catalog_plates_bag():
    spec = default_library.get_frame(_NEW_SKU)
    for plate in spec.plates:
        assert not hasattr(plate, "length_mm")
        assert not hasattr(plate, "width_mm")


def test_t5_standoff_never_carries_diameter_or_section():
    spec = default_library.get_frame(_NEW_SKU)
    for standoff in spec.standoffs:
        assert not hasattr(standoff, "diameter_mm")
        assert not hasattr(standoff, "width_mm")
        assert not hasattr(standoff, "length_mm")
    parts = frame_part_specs_from_catalog(_NEW_SKU)
    standoff_props = parts["frame_standoff"].properties
    for forbidden in ("diameter_mm", "length_mm", "width_mm"):
        assert forbidden not in standoff_props
