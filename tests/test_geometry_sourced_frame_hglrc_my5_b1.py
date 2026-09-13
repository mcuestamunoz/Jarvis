"""#4g+ Sourced frame HGLRC MY5 B1 (catalog-only seed).

Covers implementation_contract_geometry_sourced_frame_hglrc_my5_b1.md —
Engineer ★ catalog-only (no live workspace rebind). New SKU
`hglrc_my5_5in`; GEP/Rooster peers byte-stable on checked fields.
Dimensions 225×200 → body_* only; never plate L×W.
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.knowledge.library import default_library

_NEW_SKU = "hglrc_my5_5in"


def test_t1_new_sku_bag():
    spec = default_library.get_frame(_NEW_SKU)
    assert spec.wheelbase_mm == pytest.approx(225.0)
    assert spec.body_length_mm == pytest.approx(225.0)
    assert spec.body_width_mm == pytest.approx(200.0)
    assert spec.mass_g == pytest.approx(140.0)
    assert spec.size_class_inch == pytest.approx(5.0)
    assert spec.configuration == "quad_x"
    assert spec.arm_thickness_mm == pytest.approx(5.0)
    assert spec.plates is not None and len(spec.plates) == 3
    by_label = {p.label: p.thickness_mm for p in spec.plates}
    assert by_label == {
        "Top plate": pytest.approx(2.0),
        "Middle plate": pytest.approx(3.0),
        "Bottom plate": pytest.approx(2.0),
    }
    assert not spec.standoffs
    assert spec.manufacturer == "HGLRC"
    assert spec.model == "MY5"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "rotorama.com" in spec.source_url


def test_t2_peers_unchanged():
    gep = default_library.get_frame("geprc_gep_racer_5in")
    assert gep.wheelbase_mm == pytest.approx(208.0)
    assert gep.mass_g == pytest.approx(78.0)
    rooster = default_library.get_frame("armattan_rooster_5in")
    assert rooster.wheelbase_mm == pytest.approx(230.0)
    assert rooster.mass_g == pytest.approx(125.0)
    assert rooster.body_length_mm is None
    assert rooster.body_width_mm is None


def test_t3_bind_projects_body_and_plates_no_lxw():
    bound = bind_frame_from_catalog(_NEW_SKU)
    assert bound.properties["wheelbase_mm"].value == pytest.approx(225.0)
    assert bound.properties["body_length_mm"].value == pytest.approx(225.0)
    assert bound.properties["body_width_mm"].value == pytest.approx(200.0)
    assert bound.properties["mass_kg"].value == pytest.approx(0.140)
    assert bound.catalog_ref.sku == _NEW_SKU

    parts = frame_part_specs_from_catalog(_NEW_SKU)
    assert set(parts) == {"frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3"}
    assert "frame_standoff" not in parts
    for part_spec in parts.values():
        assert "length_mm" not in part_spec.properties
        assert "width_mm" not in part_spec.properties
    assert parts["frame_arm"].properties["thickness_mm"].value == pytest.approx(5.0)
    assert parts["frame_plate"].properties["label"].value == "Top plate"
    assert parts["frame_plate"].properties["thickness_mm"].value == pytest.approx(2.0)
    assert parts["frame_plate_2"].properties["label"].value == "Middle plate"
    assert parts["frame_plate_2"].properties["thickness_mm"].value == pytest.approx(3.0)
    assert parts["frame_plate_3"].properties["label"].value == "Bottom plate"
    assert parts["frame_plate_3"].properties["thickness_mm"].value == pytest.approx(2.0)


def test_t4_no_lxw_on_plate_seed_objects():
    spec = default_library.get_frame(_NEW_SKU)
    for plate in spec.plates:
        assert not hasattr(plate, "length_mm")
        assert not hasattr(plate, "width_mm")
