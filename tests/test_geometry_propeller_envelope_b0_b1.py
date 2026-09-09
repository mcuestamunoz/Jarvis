"""Propeller B0 honesty + B1 cited bag (gf_5045x3 only).

Covers implementation_contract_geometry_propeller_envelope_b0_b1.md §3.1-3.7:
  T1  gemfan_5045_hbn: identity_status partially_verified; mass_g None; no
      hub/blade_count
  T2  hq_5045_bn still partially_verified; mass_g None
  T3  gf_5045x3: mass_g ~4.5, blade_count 3, hub 5/9.5, source_note non-empty
  T4  bind_propeller_from_catalog("gf_5045x3") projects the bag; diameter_in 5
  T5  bind gemfan_5030 -> no mass_g key
  T6  bind tmotor_15x5 -> no mass_g key
  T7  project_spatial_nodes: diameter_in + hub_thickness_mm -> disk Ø 127,
      hub field shown as text
  T8  tmotor_22x6_7.pitch_in == 6.7; mass_g None; key/pitch unchanged
  T9  among list_propellers(), only gf_5045x3 has mass_g is not None
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_propeller_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def test_t1_gemfan_5045_hbn_partially_verified_no_bag():
    spec = default_library.get_propeller("gemfan_5045_hbn")
    assert spec.identity_status == "partially_verified"
    assert spec.mass_g is None
    assert spec.hub_diameter_mm is None
    assert spec.hub_thickness_mm is None
    assert spec.blade_count is None


def test_t2_hq_5045_bn_still_partially_verified_no_mass():
    spec = default_library.get_propeller("hq_5045_bn")
    assert spec.identity_status == "partially_verified"
    assert spec.mass_g is None


def test_t3_gf_5045x3_bag_seeded_with_source_note():
    spec = default_library.get_propeller("gf_5045x3")
    assert spec.mass_g == pytest.approx(4.5)
    assert spec.blade_count == 3
    assert spec.material == "ABS"
    assert spec.hub_diameter_mm == pytest.approx(5.0)
    assert spec.hub_thickness_mm == pytest.approx(9.5)
    assert spec.source_note
    assert spec.mass_tolerance_g is None
    assert spec.shaft_bore_mm is None


def test_t4_bind_gf_5045x3_projects_bag():
    spec = bind_propeller_from_catalog("gf_5045x3")
    assert spec.properties["diameter_in"].value == pytest.approx(5.0)
    assert spec.properties["mass_g"].value == pytest.approx(4.5)
    assert spec.properties["blade_count"].value == 3
    assert spec.properties["material"].value == "ABS"
    assert spec.properties["hub_diameter_mm"].value == pytest.approx(5.0)
    assert spec.properties["hub_diameter_mm"].unit == "mm"
    assert spec.properties["hub_thickness_mm"].value == pytest.approx(9.5)
    assert "source_note" not in spec.properties
    assert "mass_tolerance_g" not in spec.properties
    assert "shaft_bore_mm" not in spec.properties


def test_t5_bind_gemfan_5030_no_mass_g_key():
    spec = bind_propeller_from_catalog("gemfan_5030")
    assert "mass_g" not in spec.properties


def test_t6_bind_tmotor_15x5_no_mass_g_key():
    spec = bind_propeller_from_catalog("tmotor_15x5")
    assert "mass_g" not in spec.properties


def test_t7_geometry_still_disk_hub_shown_as_text():
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={
            "diameter_in": PropertyValue(value=5.0, unit="in", source="declared"),
            "hub_thickness_mm": PropertyValue(value=9.5, unit="mm", source="declared"),
        },
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={"propellers": propellers}),
    )
    nodes = project_spatial_nodes(state)
    node = next(n for n in nodes if n["id"] == "propellers")
    assert node["geometry"] == {"shape": "disk", "diameter_mm": 127.0}
    assert {"label": "hub_thickness_mm", "value": "9.5 mm"} in node["fields"]


def test_t8_tmotor_22x6_7_pitch_and_key_unchanged():
    spec = default_library.get_propeller("tmotor_22x6_7")
    assert spec.pitch_in == pytest.approx(6.7)
    assert spec.mass_g is None
    assert spec.name == "tmotor_22x6_7"


def test_t9_only_cited_propellers_have_mass_g():
    """Propeller cited seeds B2 (implementation_contract_geometry_propeller_
    cited_seeds_b2.md §3.5): the cited set grew from {gf_5045x3} to
    {gf_5045x3, dal_7040, apc_10x6_ep} — a required census update, not a
    weaken (every other row's mass_g is still None, unchanged)."""
    with_mass = {p.name for p in default_library.list_propellers() if p.mass_g is not None}
    assert with_mass == {"gf_5045x3", "dal_7040", "apc_10x6_ep"}
