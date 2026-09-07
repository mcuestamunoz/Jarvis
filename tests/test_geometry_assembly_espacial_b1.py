"""Geometry Assembly Espacial B1 (`mounted_on`, relation-only).

Covers implementation_contract_geometry_assembly_espacial_b1.md §4:
  - ComponentSpec.mounted_on schema default / round-trip
  - set_component_mounted_on: set / clear / reject-missing-target / reject-self-mount
  - Board projector: "montado en" text field appears when set, omitted otherwise
  - Non-regression: parent_key ("frame" BOM topology) unaffected by mounted_on;
    clear_frame_part_children still filters only parent_key == "frame"
"""
from __future__ import annotations

import pytest

from jarvis.core.component_writers import clear_frame_part_children, set_component_mounted_on
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _state(components: dict[str, ComponentSpec], blocks: list[str] | None = None) -> ProjectState:
    return ProjectState(
        project_id="p1",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
        design_properties=DesignProperties(system_blocks=blocks or [], components=components),
    )


# ── 1. Schema ─────────────────────────────────────────────────────────────


def test_component_spec_mounted_on_default_none():
    spec = ComponentSpec(suggested_key="flight_controller")
    assert spec.mounted_on is None


def test_component_spec_mounted_on_round_trip():
    spec = ComponentSpec(suggested_key="flight_controller", mounted_on="frame_plate_1")
    restored = ComponentSpec.model_validate_json(spec.model_dump_json())
    assert restored.mounted_on == "frame_plate_1"


def test_mounted_on_orthogonal_to_parent_key():
    """A spec may carry both — they answer different questions."""
    spec = ComponentSpec(suggested_key="frame_plate_1", parent_key="frame", mounted_on=None)
    assert spec.parent_key == "frame"
    assert spec.mounted_on is None


# ── 2. Writer: set / clear / reject ─────────────────────────────────────────


def _two_component_state() -> ProjectState:
    return _state({
        "flight_controller": ComponentSpec(
            suggested_key="flight_controller", component_type="flight_controller",
            completeness="high",
        ),
        "frame_plate_1": ComponentSpec(
            suggested_key="frame_plate_1", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    })


def test_set_mounted_on_persists_on_spec():
    state = _two_component_state()
    updated = set_component_mounted_on(state, "flight_controller", "frame_plate_1")
    fc = updated.design_properties.components["flight_controller"]
    assert fc.mounted_on == "frame_plate_1"
    # parent_key of the target is untouched by this writer
    assert updated.design_properties.components["frame_plate_1"].parent_key == "frame"


def test_set_mounted_on_rejects_missing_target():
    state = _two_component_state()
    with pytest.raises(ValueError):
        set_component_mounted_on(state, "flight_controller", "frame_plate_9")


def test_set_mounted_on_rejects_missing_component():
    state = _two_component_state()
    with pytest.raises(ValueError):
        set_component_mounted_on(state, "esc", "frame_plate_1")


def test_set_mounted_on_rejects_self_mount():
    state = _two_component_state()
    with pytest.raises(ValueError):
        set_component_mounted_on(state, "flight_controller", "flight_controller")


def test_clear_mounted_on_sets_none():
    state = _two_component_state()
    mounted = set_component_mounted_on(state, "flight_controller", "frame_plate_1")
    cleared = set_component_mounted_on(mounted, "flight_controller", None)
    assert cleared.design_properties.components["flight_controller"].mounted_on is None


def test_clear_mounted_on_is_idempotent_when_already_none():
    state = _two_component_state()
    cleared = set_component_mounted_on(state, "flight_controller", None)
    assert cleared.design_properties.components["flight_controller"].mounted_on is None
    assert cleared is state  # no-op returns the same object, no spurious copy


# ── 3. Board projector ──────────────────────────────────────────────────────


def test_board_shows_montado_en_field_when_set():
    state = _state({
        "flight_controller": ComponentSpec(
            name="pixhawk_4", suggested_key="flight_controller",
            properties={"model": PropertyValue(value="pixhawk_4")},
            mounted_on="frame_plate_1",
        ),
    })
    nodes = project_spatial_nodes(state)
    fc_node = next(n for n in nodes if n["id"] == "flight_controller")
    assert {"label": "montado en", "value": "frame_plate_1"} in fc_node["fields"]


def test_board_omits_montado_en_field_when_none():
    state = _state({
        "flight_controller": ComponentSpec(
            name="pixhawk_4", suggested_key="flight_controller",
            properties={"model": PropertyValue(value="pixhawk_4")},
        ),
    })
    nodes = project_spatial_nodes(state)
    fc_node = next(n for n in nodes if n["id"] == "flight_controller")
    assert all(f["label"] != "montado en" for f in fc_node["fields"])


def test_board_montado_en_does_not_change_kind_or_layout():
    """A component with mounted_on set stays kind: 'component' (not 'part') —
    mounted_on is orthogonal to parent_key, which is what drives kind/lane."""
    state = _state({
        "motors": ComponentSpec(
            name="4x 2306", suggested_key="motors",
            properties={"thrust_n": PropertyValue(value=12.0, unit="N")},
            mounted_on="frame_arm",
        ),
    })
    nodes = project_spatial_nodes(state)
    motors_node = next(n for n in nodes if n["id"] == "motors")
    assert motors_node["kind"] == "component"
    # x/y are still the deterministic lane layout, unrelated to mounted_on
    assert isinstance(motors_node["x"], int)
    assert isinstance(motors_node["y"], int)


# ── 4. Non-regression: parent_key / clear_frame_part_children unaffected ───


def test_frame_part_kind_and_bucket_unchanged_by_mounted_on_feature():
    """A frame_plate_1 with only parent_key='frame' (no mounted_on) still
    projects as kind: 'part' — unchanged by this IC."""
    state = _state({
        "frame": ComponentSpec(name="tbs_source_one", suggested_key="frame", completeness="high"),
        "frame_plate_1": ComponentSpec(
            suggested_key="frame_plate_1", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    })
    nodes = project_spatial_nodes(state)
    plate_node = next(n for n in nodes if n["id"] == "frame_plate_1")
    assert plate_node["kind"] == "part"
    assert all(f["label"] != "montado en" for f in plate_node["fields"])


def test_clear_frame_part_children_still_filters_only_parent_key_frame():
    """A component with mounted_on (but parent_key=None) must survive
    clear_frame_part_children — it is not a frame part."""
    state = _state({
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", parent_key="frame", completeness="medium",
        ),
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high", mounted_on="frame_arm",
        ),
    })
    cleared = clear_frame_part_children(state)
    remaining = cleared.design_properties.components
    assert "frame_arm" not in remaining
    assert "motors" in remaining
    assert remaining["motors"].mounted_on == "frame_arm"
