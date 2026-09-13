"""#4c Sourced ESC SpeedyBee BLS 60A 4-in-1 B1.

Covers implementation_contract_geometry_sourced_esc_speedybee_b1.md §0/§3
— a new Class A ESC SKU (`speedybee_bls_60a_30x30_4in1`) seeded from an
Engineer-provided purchase-ground-truth citation (Option A: new SKU, the
existing `hobbywing_xrotor_40a_6s` row untouched). `bind_esc_from_catalog`
projects its L×W×H/mass/current onto a ComponentSpec exactly like the
existing Class A ESC already does (`source="declared"`, same convention
as every other family's bind helper — see the #4/#4b ICs' own N1 note).

  T1  get_esc(new SKU) -> L/W/H 45.6/44/8, mass 23.5, continuous 60A,
      channels 4, topology "4in1", burst 80A
  T2  bind_esc_from_catalog projects L×W×H + mass + current_a
      (source="declared")
  T3  Projector emits box geometry for the bound spec
  T4  hobbywing_xrotor_40a_6s unchanged (topology/current/dims/mass)
  T5  Rooster frame / GenS Ace battery untouched
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_esc_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.workspace.spatial_board import _geometry_from_spec

_NEW_SKU = "speedybee_bls_60a_30x30_4in1"


def test_t1_new_sku_dims_mass_electrical_identity():
    spec = default_library.get_esc(_NEW_SKU)
    assert spec.length_mm == pytest.approx(45.6)
    assert spec.width_mm == pytest.approx(44.0)
    assert spec.height_mm == pytest.approx(8.0)
    assert spec.mass_g == pytest.approx(23.5)
    assert spec.continuous_current_a == pytest.approx(60.0)
    assert spec.burst_current_a == pytest.approx(80.0)
    assert spec.channels == 4
    assert spec.esc_topology == "4in1"
    assert spec.cells_min == 3
    assert spec.cells_max == 6
    assert spec.manufacturer == "SpeedyBee"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "speedybee.com" in spec.source_url


def test_t2_bind_projects_dims_mass_current_declared():
    bound = bind_esc_from_catalog(_NEW_SKU)
    assert bound.properties["length_mm"].value == pytest.approx(45.6)
    assert bound.properties["length_mm"].source == "declared"
    assert bound.properties["width_mm"].value == pytest.approx(44.0)
    assert bound.properties["width_mm"].source == "declared"
    assert bound.properties["height_mm"].value == pytest.approx(8.0)
    assert bound.properties["height_mm"].source == "declared"
    assert bound.properties["mass_g"].value == pytest.approx(23.5)
    assert bound.properties["mass_g"].source == "declared"
    assert bound.properties["current_a"].value == pytest.approx(60.0)
    assert bound.catalog_ref.family == "esc"
    assert bound.catalog_ref.sku == _NEW_SKU


def test_t3_projector_emits_box_geometry():
    bound = bind_esc_from_catalog(_NEW_SKU)
    geometry = _geometry_from_spec(bound)
    assert geometry == {"shape": "box", "length_mm": 45.6, "width_mm": 44.0, "height_mm": 8.0}


def test_t4_hobbywing_unchanged():
    spec = default_library.get_esc("hobbywing_xrotor_40a_6s")
    assert spec.esc_topology == "individual"
    assert spec.channels == 1
    assert spec.continuous_current_a == pytest.approx(40.0)
    assert spec.burst_current_a == pytest.approx(60.0)
    assert spec.length_mm == pytest.approx(50.0)
    assert spec.width_mm == pytest.approx(21.6)
    assert spec.height_mm == pytest.approx(12.0)
    assert spec.mass_g == pytest.approx(15.0)
    assert spec.manufacturer == "HOBBYWING"


def test_t5_rooster_and_gens_ace_untouched():
    repo_root = Path(__file__).resolve().parents[1]
    frames_data = json.loads((repo_root / "library" / "frames" / "_datos.json").read_text(encoding="utf-8"))
    rooster = frames_data["armattan_rooster_5in"]
    for plate in rooster["plates"]:
        assert "length_mm" not in plate
        assert "width_mm" not in plate

    battery = default_library.get_battery("gens_ace_2200mah_3s_35c_gtech")
    assert battery.length_mm == pytest.approx(74.7)
    assert battery.width_mm == pytest.approx(33.5)
    assert battery.height_mm == pytest.approx(25.4)
    assert battery.mass_g == pytest.approx(143.0)
