"""Propeller cited seeds B2 (dal_7040 Cyclone + apc_10x6_ep).

Covers implementation_contract_geometry_propeller_cited_seeds_b2.md §3.2-3.4:
  T1  get_propeller("dal_7040"): mass 5.7, blades 2, hub 5/7, GetFPV
      source_url, source_note non-empty
  T2  bind dal_7040 projects those; no source_note property
  T3  get_propeller("apc_10x6_ep"): 10x6, mass 20.1, hub 20.3/9.9,
      shaft_bore_mm 6.35, blades 2
  T4  bind apc_10x6_ep projects bag; apc_10x4_5 still pitch 4.5, no mass
  T5  project_spatial_nodes synthetic 10in + hub -> disk 254; hub text
  T6  project_spatial_nodes synthetic 7in -> disk 177.8
  T7  gf_5045x3 bag unchanged (mass 4.5, hub 5/9.5)
  T8  list_propellers() includes apc_10x6_ep; 18 rows total (17+1)
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_propeller_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def test_t1_dal_7040_cyclone_bag():
    spec = default_library.get_propeller("dal_7040")
    assert spec.mass_g == pytest.approx(5.7)
    assert spec.blade_count == 2
    assert spec.material == "Pure PC"
    assert spec.hub_diameter_mm == pytest.approx(5.0)
    assert spec.hub_thickness_mm == pytest.approx(7.0)
    assert spec.identity_status == "verified"
    assert spec.source_url == "https://www.getfpv.com/dalprop-cyclone-7040-7-2-blade-propeller.html"
    assert spec.source_note
    assert spec.shaft_bore_mm is None


def test_t2_bind_dal_7040_projects_bag_no_source_note():
    spec = bind_propeller_from_catalog("dal_7040")
    assert spec.properties["mass_g"].value == pytest.approx(5.7)
    assert spec.properties["blade_count"].value == 2
    assert spec.properties["material"].value == "Pure PC"
    assert spec.properties["hub_diameter_mm"].value == pytest.approx(5.0)
    assert spec.properties["hub_thickness_mm"].value == pytest.approx(7.0)
    assert "source_note" not in spec.properties


def test_t3_apc_10x6_ep_bag():
    spec = default_library.get_propeller("apc_10x6_ep")
    assert spec.diameter_in == pytest.approx(10.0)
    assert spec.pitch_in == pytest.approx(6.0)
    assert spec.mass_g == pytest.approx(20.1)
    assert spec.hub_diameter_mm == pytest.approx(20.3)
    assert spec.hub_thickness_mm == pytest.approx(9.9)
    assert spec.shaft_bore_mm == pytest.approx(6.35)
    assert spec.blade_count == 2
    assert spec.manufacturer == "APC"
    assert spec.model == "10x6EP"


def test_t4_bind_apc_10x6_ep_and_apc_10x4_5_stay_distinct():
    ep = bind_propeller_from_catalog("apc_10x6_ep")
    assert ep.properties["pitch_in"].value == pytest.approx(6.0)
    assert ep.properties["mass_g"].value == pytest.approx(20.1)
    assert ep.properties["shaft_bore_mm"].value == pytest.approx(6.35)

    mr = bind_propeller_from_catalog("apc_10x4_5")
    assert mr.properties["pitch_in"].value == pytest.approx(4.5)
    assert "mass_g" not in mr.properties


def test_t5_geometry_10in_with_hub_yields_disk_254():
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={
            "diameter_in": PropertyValue(value=10.0, unit="in", source="declared"),
            "hub_diameter_mm": PropertyValue(value=20.3, unit="mm", source="declared"),
        },
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={"propellers": propellers}),
    )
    nodes = project_spatial_nodes(state)
    node = next(n for n in nodes if n["id"] == "propellers")
    assert node["geometry"] == {"shape": "disk", "diameter_mm": 254.0}
    assert {"label": "hub_diameter_mm", "value": "20.3 mm"} in node["fields"]


def test_t6_geometry_7in_yields_disk_177_8():
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={"diameter_in": PropertyValue(value=7.0, unit="in", source="declared")},
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={"propellers": propellers}),
    )
    nodes = project_spatial_nodes(state)
    node = next(n for n in nodes if n["id"] == "propellers")
    assert node["geometry"]["shape"] == "disk"
    assert node["geometry"]["diameter_mm"] == pytest.approx(177.8)


def test_t7_gf_5045x3_bag_unchanged():
    spec = default_library.get_propeller("gf_5045x3")
    assert spec.mass_g == pytest.approx(4.5)
    assert spec.hub_diameter_mm == pytest.approx(5.0)
    assert spec.hub_thickness_mm == pytest.approx(9.5)


def test_t8_list_propellers_includes_new_sku_18_rows():
    all_props = default_library.list_propellers()
    names = [p.name for p in all_props]
    assert "apc_10x6_ep" in names
    assert len(all_props) == 18
