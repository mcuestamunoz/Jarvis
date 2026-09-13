"""#4 Sourced dims B1 (5min Class A seed pack).

Covers implementation_contract_geometry_sourced_dims_b1.md §0/§3 — a new
Class A battery SKU (`gens_ace_2200mah_3s_35c_gtech`) seeded from an
Engineer-provided purchase-ground-truth citation bag (Option A: new SKU,
generic `lipo_3s_2200mah` untouched). `bind_battery_from_catalog` projects
its L×W×H/mass onto a ComponentSpec exactly like every other Class A
battery already does (`source="declared"` — the IC's own lock #6 STOP
condition: `test_catalog_bind_v1.py`'s golden `length_mm.source ==
"declared"` assertion on `lipo_4s_1500mah` means this Buy keeps the
existing convention rather than introducing a second `source="catalog"`
value; documented as N1 in the implementation report). No Rooster
Main Plate L×W invented — `plates[]` entries stay thickness-only.

  T1  get_battery(new SKU) -> L/W/H 74.7/33.5/25.4, mass 143, C 35
  T2  bind_battery_from_catalog projects the three mm keys + mass onto
      properties (source="declared", same as every other Class A battery)
  T3  Projector emits box geometry for the bound spec
  T4  lipo_3s_2200mah still has no L×W×H; mass 180; C 50 (byte-stable)
  T5  Rooster armattan_rooster_5in plates[] still thickness-only
  T6  Other seeded Class A batteries (lipo_4s_1500mah/6s_6000mah)
      unchanged
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_battery_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.workspace.spatial_board import _geometry_from_spec

_NEW_SKU = "gens_ace_2200mah_3s_35c_gtech"


def test_t1_new_sku_dims_mass_c_rating():
    spec = default_library.get_battery(_NEW_SKU)
    assert spec.length_mm == pytest.approx(74.7)
    assert spec.width_mm == pytest.approx(33.5)
    assert spec.height_mm == pytest.approx(25.4)
    assert spec.mass_g == pytest.approx(143.0)
    assert spec.c_rating == pytest.approx(35.0)
    assert spec.cells == 3
    assert spec.nominal_voltage == pytest.approx(11.1)
    assert spec.capacity_mah == pytest.approx(2200.0)
    assert spec.manufacturer == "Gens Ace"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "genstattu.com" in spec.source_url


def test_t2_bind_projects_dims_and_mass_declared():
    bound = bind_battery_from_catalog(_NEW_SKU)
    assert bound.properties["length_mm"].value == pytest.approx(74.7)
    assert bound.properties["length_mm"].unit == "mm"
    assert bound.properties["length_mm"].source == "declared"
    assert bound.properties["width_mm"].value == pytest.approx(33.5)
    assert bound.properties["width_mm"].source == "declared"
    assert bound.properties["height_mm"].value == pytest.approx(25.4)
    assert bound.properties["height_mm"].source == "declared"
    assert bound.properties["mass_g"].value == pytest.approx(143.0)
    assert bound.properties["mass_g"].source == "declared"
    assert bound.catalog_ref.family == "battery"
    assert bound.catalog_ref.sku == _NEW_SKU


def test_t3_projector_emits_box_geometry():
    bound = bind_battery_from_catalog(_NEW_SKU)
    geometry = _geometry_from_spec(bound)
    assert geometry == {"shape": "box", "length_mm": 74.7, "width_mm": 33.5, "height_mm": 25.4}


# test_t4_generic_lipo_3s_2200mah_byte_stable removed (catalog sourced-only
# purge B1): its subject, lipo_3s_2200mah, had no source_url and was
# deleted — that row no longer exists to stay byte-stable, which is this
# Buy's own intended outcome (★1/★2), not a gap.


def test_t5_rooster_plates_still_thickness_only():
    repo_root = Path(__file__).resolve().parents[1]
    frames_data = json.loads((repo_root / "library" / "frames" / "_datos.json").read_text(encoding="utf-8"))
    rooster = frames_data["armattan_rooster_5in"]
    for plate in rooster["plates"]:
        assert "length_mm" not in plate
        assert "width_mm" not in plate


def test_t6_other_class_a_batteries_unchanged():
    cnhl = default_library.get_battery("lipo_4s_1500mah")
    assert cnhl.length_mm == pytest.approx(37.0)
    assert cnhl.width_mm == pytest.approx(35.0)
    assert cnhl.height_mm == pytest.approx(75.0)
    assert cnhl.mass_g == pytest.approx(183.0)

    gnb = default_library.get_battery("lipo_6s_6000mah")
    assert gnb.length_mm == pytest.approx(141.0)
    assert gnb.width_mm == pytest.approx(64.0)
    assert gnb.height_mm == pytest.approx(41.0)
    assert gnb.mass_g == pytest.approx(793.0)
