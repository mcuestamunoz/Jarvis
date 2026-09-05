"""Spatial board projector: ProjectState → visor cards. No BOM, no invented slots."""
from __future__ import annotations

from pathlib import Path

from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import (
    project_spatial_nodes,
    project_spatial_nodes_from_path,
)


def _state(
    components: dict[str, ComponentSpec],
    blocks: list[str] | None = None,
) -> ProjectState:
    return ProjectState(
        project_id="p1",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
        design_properties=DesignProperties(
            system_blocks=blocks or [],
            components=components,
        ),
    )


def test_empty_components_yield_no_cards():
    assert project_spatial_nodes(_state({})) == []


def test_one_spec_is_one_card_with_properties_and_sku():
    state = _state(
        {
            "motors": ComponentSpec(
                name="emax_rs2205_2300",
                properties={
                    "thrust_n": PropertyValue(value=8.0, unit="N"),
                    "kv_rating": PropertyValue(value=2300),
                },
                catalog_ref=CatalogRef(family="motor", sku="emax_rs2205_2300"),
            )
        }
    )
    nodes = project_spatial_nodes(state)
    assert len(nodes) == 1
    node = nodes[0]
    assert node["id"] == "motors"
    assert node["title"] == "motors"
    assert node["declaredName"] == "emax_rs2205_2300"
    assert node["kind"] == "component"
    assert {"label": "thrust_n", "value": "8 N"} in node["fields"]
    assert {"label": "SKU", "value": "emax_rs2205_2300"} in node["fields"]
    labels = [row["label"] for row in node["fields"]]
    assert "completeness" not in labels
    assert "missing_fields" not in labels


def test_empty_name_stays_empty():
    nodes = project_spatial_nodes(_state({"flight_controller": ComponentSpec(name="")}))
    assert nodes[0]["declaredName"] == ""


def test_does_not_invent_missing_architecture_slots():
    state = _state(
        {"motors": ComponentSpec(name="M")},
        blocks=["propulsion", "energy", "structure", "control"],
    )
    ids = [node["id"] for node in project_spatial_nodes(state)]
    assert ids == ["motors"]


def test_parts_are_kind_part_stacked_under_parent_lane():
    state = _state(
        {
            "frame": ComponentSpec(name="armattan_rooster_5in"),
            "frame_arm": ComponentSpec(
                name="brazos",
                parent_key="frame",
                properties={"thickness_mm": PropertyValue(value=4.0, unit="mm")},
            ),
        },
        blocks=["propulsion", "energy", "structure", "control"],
    )
    by_id = {node["id"]: node for node in project_spatial_nodes(state)}
    frame = by_id["frame"]
    arm = by_id["frame_arm"]
    assert arm["kind"] == "part"
    assert frame["kind"] == "component"
    assert arm["x"] == frame["x"]
    assert arm["y"] > frame["y"]


def test_four_blocks_place_roots_in_separate_lanes():
    state = _state(
        {
            "motors": ComponentSpec(name="M"),
            "battery": ComponentSpec(name="B"),
            "frame": ComponentSpec(name="F"),
            "flight_controller": ComponentSpec(name="C"),
        },
        blocks=["propulsion", "energy", "structure", "control"],
    )
    by_id = {node["id"]: node for node in project_spatial_nodes(state)}
    assert by_id["motors"]["x"] < by_id["battery"]["x"] < by_id["frame"]["x"] < by_id[
        "flight_controller"
    ]["x"]


def test_load_from_state_json_path(tmp_path: Path):
    state = _state({"battery": ComponentSpec(name="lipo")})
    path = tmp_path / "state.json"
    path.write_text(state.model_dump_json(), encoding="utf-8")
    nodes = project_spatial_nodes_from_path(path)
    assert [node["id"] for node in nodes] == ["battery"]
    assert nodes[0]["declaredName"] == "lipo"
