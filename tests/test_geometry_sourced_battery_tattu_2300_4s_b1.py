"""#4f Sourced battery Tattu 2300mAh 4S 75C XT60 B1.

Covers implementation_contract_geometry_sourced_battery_tattu_2300_4s_b1.md
§0/§3 — a new Class A battery SKU (`tattu_2300mah_4s_75c_xt60`) seeded
from an Engineer-provided purchase-ground-truth citation (Option A: new
SKU; `gens_ace_2200mah_3s_35c_gtech` and all `lipo_4s_*` rows untouched).
`bind_battery_from_catalog` projects its L×W×H/mass/energy onto a
ComponentSpec exactly like every other Class A battery already does.

  T1  get_battery(new SKU) -> L/W/H 105/35/29, mass 270, C 75, cells 4,
      energy_wh ~= 34.04
  T2  bind_battery_from_catalog projects the bag (source="declared")
  T3  Projector emits box geometry for the bound spec
  T4  gens_ace_2200mah_3s_35c_gtech unchanged
  T5  Other lipo_4s_* rows unchanged
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_battery_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.workspace.spatial_board import _geometry_from_spec

_NEW_SKU = "tattu_2300mah_4s_75c_xt60"


def test_t1_new_sku_dims_mass_electrical():
    spec = default_library.get_battery(_NEW_SKU)
    assert spec.length_mm == pytest.approx(105.0)
    assert spec.width_mm == pytest.approx(35.0)
    assert spec.height_mm == pytest.approx(29.0)
    assert spec.mass_g == pytest.approx(270.0)
    assert spec.c_rating == pytest.approx(75.0)
    assert spec.cells == 4
    assert spec.nominal_voltage == pytest.approx(14.8)
    assert spec.capacity_mah == pytest.approx(2300.0)
    assert spec.energy_wh == pytest.approx(34.04)
    assert spec.max_continuous_current_a == pytest.approx(172.5)
    assert spec.manufacturer == "Tattu"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "rcdrone.top" in spec.source_url


def test_t2_bind_projects_bag_declared():
    bound = bind_battery_from_catalog(_NEW_SKU)
    assert bound.properties["length_mm"].value == pytest.approx(105.0)
    assert bound.properties["length_mm"].source == "declared"
    assert bound.properties["width_mm"].value == pytest.approx(35.0)
    assert bound.properties["height_mm"].value == pytest.approx(29.0)
    assert bound.properties["mass_g"].value == pytest.approx(270.0)
    assert bound.properties["battery_capacity_wh"].value == pytest.approx(34.04)
    assert bound.properties["chemistry"].value == "lipo"
    assert bound.properties["cell_count"].value == 4
    assert bound.catalog_ref.family == "battery"
    assert bound.catalog_ref.sku == _NEW_SKU


def test_t3_projector_emits_box_geometry():
    bound = bind_battery_from_catalog(_NEW_SKU)
    geometry = _geometry_from_spec(bound)
    assert geometry == {"shape": "box", "length_mm": 105.0, "width_mm": 35.0, "height_mm": 29.0}


def test_t4_gens_ace_unchanged():
    spec = default_library.get_battery("gens_ace_2200mah_3s_35c_gtech")
    assert spec.length_mm == pytest.approx(74.7)
    assert spec.width_mm == pytest.approx(33.5)
    assert spec.height_mm == pytest.approx(25.4)
    assert spec.mass_g == pytest.approx(143.0)
    assert spec.c_rating == pytest.approx(35.0)
    assert spec.cells == 3


def test_t5_other_lipo_4s_rows_unchanged():
    cnhl = default_library.get_battery("lipo_4s_1500mah")
    assert cnhl.length_mm == pytest.approx(37.0)
    assert cnhl.width_mm == pytest.approx(35.0)
    assert cnhl.height_mm == pytest.approx(75.0)
    assert cnhl.mass_g == pytest.approx(183.0)

    spektrum = default_library.get_battery("lipo_4s_5000mah")
    assert spektrum.length_mm == pytest.approx(138.5)
    assert spektrum.width_mm == pytest.approx(47.7)
    assert spektrum.height_mm == pytest.approx(40.7)
    assert spektrum.mass_g == pytest.approx(498.0)

    plain_10000 = default_library.get_battery("lipo_4s_10000mah")
    assert plain_10000.length_mm is None
    assert plain_10000.mass_g == pytest.approx(980.0)
