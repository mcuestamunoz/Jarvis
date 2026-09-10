"""Live motor visor via sourced SKU rebind B1.

Covers implementation_contract_geometry_motor_visor_rebind_b1.md §3/§4: the
already-shipped bind (`bind_motor_from_catalog`) + count-preserving writer
(`set_motor_component`, Bug78) + copies projector (`_solid_copies`) seam,
glued end to end for the RaceSpec SKU `emax_rs2205s_2300` (sourced
Ø 27.9 / height 31.7). No `src/` edit was needed — this file proves the
seam already holds.

  P1  Bind S SKU + set_motor_component on motor_count=4 + prop disk ->
      motors disk 27.9, solidCopies==4, catalog_ref.sku==S-SKU; one motors
      node; propellers still solidCopies==4, still disk
  P2  Same with motor_count=3 -> motors solidCopies==3 (10min-shaped)
  P3  Bind mute emax_rs2205_2300 + motor_count=4 + prop disk -> motors no
      geometry, no solidCopies; propellers still 4
  P4  Library: emax_rs2205_2300.diameter_mm is None; S-row is 27.9
  P5  height_mm 31.7 is a field on the motors node after P1 bind;
      geometry.shape == "disk" (never a cylinder)
"""
from __future__ import annotations

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.motor_catalog_assist import motor_spec_to_suggestion
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_MUTE_SKU = "emax_rs2205_2300"
_S_SKU = "emax_rs2205s_2300"


def _mute_motors_spec(motor_count: int, sku: str = _MUTE_SKU) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="motors",
        completeness="high",
        properties={"motor_count": PropertyValue(value=motor_count, unit="", source="declared")},
        catalog_ref=CatalogRef(family="motor", sku=sku),
    )


def _propellers_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="propellers",
        completeness="high",
        properties={"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")},
    )


def _state(motors: ComponentSpec, current_parameters: dict | None = None) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters=current_parameters or {},
        design_properties=DesignProperties(components={"motors": motors, "propellers": _propellers_spec()}),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def _rebind(initial_state: ProjectState, sku: str) -> ProjectState:
    suggestion = motor_spec_to_suggestion(default_library.get_motor(sku))
    bound_spec = bind_motor_from_catalog(suggestion)
    return set_motor_component(initial_state, bound_spec, power_w=None)


def test_p1_s_sku_rebind_with_motor_count_4_yields_4_motor_disks():
    initial = _state(_mute_motors_spec(motor_count=4), current_parameters={"motor_count": 4})
    updated = _rebind(initial, _S_SKU)

    motors_spec = updated.design_properties.components["motors"]
    assert motors_spec.catalog_ref.sku == _S_SKU

    nodes = _nodes_by_id(updated)
    motors = nodes["motors"]
    propellers = nodes["propellers"]
    assert motors["geometry"] == {"shape": "disk", "diameter_mm": 27.9}
    assert motors["solidCopies"] == 4
    assert sum(1 for n in nodes.values() if n["id"] == "motors") == 1
    assert propellers["geometry"] == {"shape": "disk", "diameter_mm": 127.0}
    assert propellers["solidCopies"] == 4


def test_p2_s_sku_rebind_with_motor_count_3_yields_3_not_coerced_to_4():
    initial = _state(_mute_motors_spec(motor_count=3), current_parameters={"motor_count": 3})
    updated = _rebind(initial, _S_SKU)

    nodes = _nodes_by_id(updated)
    assert nodes["motors"]["solidCopies"] == 3
    assert nodes["propellers"]["solidCopies"] == 3


def test_p3_mute_sku_rebind_stays_invisible_propellers_unaffected():
    initial = _state(_mute_motors_spec(motor_count=4), current_parameters={"motor_count": 4})
    updated = _rebind(initial, _MUTE_SKU)

    motors_spec = updated.design_properties.components["motors"]
    assert motors_spec.catalog_ref.sku == _MUTE_SKU

    nodes = _nodes_by_id(updated)
    motors = nodes["motors"]
    assert "geometry" not in motors
    assert "solidCopies" not in motors
    assert nodes["propellers"]["solidCopies"] == 4


def test_p4_library_mute_sku_has_no_diameter_s_row_does():
    assert default_library.get_motor(_MUTE_SKU).diameter_mm is None
    assert default_library.get_motor(_S_SKU).diameter_mm == 27.9


def test_p5_height_mm_is_a_card_field_never_a_cylinder():
    initial = _state(_mute_motors_spec(motor_count=4), current_parameters={"motor_count": 4})
    updated = _rebind(initial, _S_SKU)

    nodes = _nodes_by_id(updated)
    motors = nodes["motors"]
    assert motors["geometry"]["shape"] == "disk"
    field_labels = {f["label"]: f["value"] for f in motors["fields"]}
    assert field_labels["height_mm"] == "31.7 mm"
