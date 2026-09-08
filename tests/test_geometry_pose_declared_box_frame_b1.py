"""Geometry pose declared box-local frame B1.

Covers implementation_contract_geometry_pose_declared_box_frame_b1.md §3.4:
  T1  Set pose ESC -> FC with x_mm=5; round-trip; Board/_fields show
      origin + honesty + Δx
  T2  Reject origin frame_plate (no box)
  T3  Reject origin motors (disk)
  T4  Reject missing origin key / self-origin
  T5  Clear pose -> None
  T6  Catalog refresh preserves declared_box_pose
  T7  Existing mounted_on tests still pass (full suite — exercised separately)
"""
from __future__ import annotations

import pytest

from jarvis.core.component_writers import refresh_component_from_catalog, set_component_declared_box_pose
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import POSE_AXES_HONESTY_LABEL, project_spatial_nodes


def _fc_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        properties={
            "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        },
    )


def _state_with_fc_esc_plate_motor() -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={
            "esc": ComponentSpec(suggested_key="esc", completeness="high"),
            "flight_controller": _fc_spec(),
            "frame_plate": ComponentSpec(
                suggested_key="frame_plate", component_type="structure_part",
                parent_key="frame", completeness="medium",
            ),
            "motors": ComponentSpec(
                suggested_key="motors", completeness="high",
                properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")},
            ),
        }),
    )


# ── T1 ───────────────────────────────────────────────────────────────────


def test_t1_set_pose_esc_on_fc_round_trip_and_board_fields():
    state = _state_with_fc_esc_plate_motor()
    pose = DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0)
    updated = set_component_declared_box_pose(state, "esc", pose)

    esc = updated.design_properties.components["esc"]
    assert esc.declared_box_pose == pose
    # round-trip through JSON, same as persisted state.json would
    restored = ComponentSpec.model_validate_json(esc.model_dump_json())
    assert restored.declared_box_pose.origin_key == "flight_controller"
    assert restored.declared_box_pose.x_mm == pytest.approx(5.0)

    nodes = project_spatial_nodes(updated)
    esc_node = next(n for n in nodes if n["id"] == "esc")
    assert {"label": "origen pose", "value": "flight_controller"} in esc_node["fields"]
    assert {"label": "ejes pose", "value": POSE_AXES_HONESTY_LABEL} in esc_node["fields"]
    assert {"label": "Δx mm", "value": "5"} in esc_node["fields"]
    assert not any(f["label"] == "Δy mm" for f in esc_node["fields"])
    assert not any(f["label"] == "Δz mm" for f in esc_node["fields"])


# ── T2/T3: reject non-box origins ───────────────────────────────────────────


def test_t2_reject_origin_frame_plate_no_box():
    state = _state_with_fc_esc_plate_motor()
    with pytest.raises(ValueError):
        set_component_declared_box_pose(state, "esc", DeclaredBoxPose(origin_key="frame_plate"))


def test_t3_reject_origin_motors_disk():
    state = _state_with_fc_esc_plate_motor()
    with pytest.raises(ValueError):
        set_component_declared_box_pose(state, "esc", DeclaredBoxPose(origin_key="motors"))


# ── T4: missing origin key / self-origin ────────────────────────────────────


def test_t4_reject_missing_origin_key():
    state = _state_with_fc_esc_plate_motor()
    with pytest.raises(ValueError):
        set_component_declared_box_pose(state, "esc", DeclaredBoxPose(origin_key="does_not_exist"))


def test_t4b_reject_self_origin():
    state = _state_with_fc_esc_plate_motor()
    with pytest.raises(ValueError):
        set_component_declared_box_pose(state, "esc", DeclaredBoxPose(origin_key="esc"))


def test_t4c_reject_missing_component_key():
    state = _state_with_fc_esc_plate_motor()
    with pytest.raises(ValueError):
        set_component_declared_box_pose(
            state, "battery", DeclaredBoxPose(origin_key="flight_controller")
        )


# ── T5: clear ────────────────────────────────────────────────────────────


def test_t5_clear_pose_sets_none():
    state = _state_with_fc_esc_plate_motor()
    mounted = set_component_declared_box_pose(
        state, "esc", DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0)
    )
    cleared = set_component_declared_box_pose(mounted, "esc", None)
    assert cleared.design_properties.components["esc"].declared_box_pose is None


def test_t5b_clear_is_idempotent_when_already_none():
    state = _state_with_fc_esc_plate_motor()
    cleared = set_component_declared_box_pose(state, "esc", None)
    assert cleared is state


# ── T6: catalog refresh preserves declared_box_pose ─────────────────────────


def test_t6_catalog_refresh_preserves_declared_box_pose():
    esc = ComponentSpec(
        name="hobbywing_xrotor_40a_6s",
        suggested_key="esc", component_type="power_control", completeness="high",
        catalog_ref=CatalogRef(family="esc", sku="hobbywing_xrotor_40a_6s"),
        declared_box_pose=DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0),
        properties={
            "current_a": PropertyValue(value=40.0, unit="A", source="declared"),
            "mass_g": PropertyValue(value=26.0, unit="g", source="declared"),
        },
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={
            "esc": esc, "flight_controller": _fc_spec(),
        }),
    )
    refreshed = refresh_component_from_catalog(state, "esc")
    new_esc = refreshed.design_properties.components["esc"]
    assert new_esc.properties["mass_g"].value == pytest.approx(15.0)
    assert new_esc.declared_box_pose == DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0)
