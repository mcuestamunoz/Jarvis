"""#4e Sourced prop Gemfan Hurricane MCK 51466-3 V2 B1.

Covers implementation_contract_geometry_sourced_prop_gemfan_51466_b1.md
§0/§3 — a new Class A propeller SKU (`gemfan_hurricane_mck_51466_3_v2`)
seeded from an Engineer-provided purchase-ground-truth citation (Option
A: new SKU, the existing `gf_5045x3` row untouched). `bind_propeller_
from_catalog` projects its diameter/pitch/mass/hub bag onto a
ComponentSpec exactly like every other cited propeller already does
(`source="declared"`, same convention as the #4/#4b/#4c ICs' own N1
note). Pitch is 3.6in taken directly from the page — never 4.66 decoded
from the model code's trailing digits.

  T1  get_propeller(new SKU) -> diameter_in~=5.189, pitch 3.6, mass 4.2,
      blades 3, hub_thickness 6.8, shaft_bore 5, no invented
      hub_diameter_mm
  T2  bind_propeller_from_catalog projects the bag (source="declared")
  T3  Projector emits disk geometry, diameter_mm ~= 131.8
  T4  gf_5045x3 unchanged (diameter/pitch/mass/hub bag)
  T5  Pitch is 3.6, never 4.66
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_propeller_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.workspace.spatial_board import _geometry_from_spec

_NEW_SKU = "gemfan_hurricane_mck_51466_3_v2"


def test_t1_new_sku_bag():
    spec = default_library.get_propeller(_NEW_SKU)
    assert spec.diameter_in == pytest.approx(5.189, abs=1e-3)
    assert spec.pitch_in == pytest.approx(3.6)
    assert spec.mass_g == pytest.approx(4.2)
    assert spec.blade_count == 3
    assert spec.hub_thickness_mm == pytest.approx(6.8)
    assert spec.shaft_bore_mm == pytest.approx(5.0)
    assert spec.hub_diameter_mm is None
    assert spec.material == "PC"
    assert spec.manufacturer == "Gemfan"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "hobbydrone.cz" in spec.source_url


def test_t2_bind_projects_bag_declared():
    bound = bind_propeller_from_catalog(_NEW_SKU)
    assert bound.properties["diameter_in"].value == pytest.approx(5.189, abs=1e-3)
    assert bound.properties["diameter_in"].source == "declared"
    assert bound.properties["pitch_in"].value == pytest.approx(3.6)
    assert bound.properties["mass_g"].value == pytest.approx(4.2)
    assert bound.properties["blade_count"].value == 3
    assert bound.properties["material"].value == "PC"
    assert bound.properties["hub_thickness_mm"].value == pytest.approx(6.8)
    assert bound.properties["shaft_bore_mm"].value == pytest.approx(5.0)
    assert "hub_diameter_mm" not in bound.properties
    assert bound.catalog_ref.family == "propeller"
    assert bound.catalog_ref.sku == _NEW_SKU


def test_t3_projector_emits_disk_diameter_131_8mm():
    bound = bind_propeller_from_catalog(_NEW_SKU)
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "disk"
    assert geometry["diameter_mm"] == pytest.approx(131.8, abs=0.01)


def test_t4_gf_5045x3_unchanged():
    spec = default_library.get_propeller("gf_5045x3")
    assert spec.diameter_in == pytest.approx(5.0)
    assert spec.pitch_in == pytest.approx(4.5)
    assert spec.mass_g == pytest.approx(4.5)
    assert spec.hub_diameter_mm == pytest.approx(5.0)
    assert spec.hub_thickness_mm == pytest.approx(9.5)
    assert spec.material == "ABS"


def test_t5_pitch_is_3_6_never_4_66():
    spec = default_library.get_propeller(_NEW_SKU)
    assert spec.pitch_in == pytest.approx(3.6)
    assert spec.pitch_in != pytest.approx(4.66)
