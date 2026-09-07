"""Spatial board projector: ProjectState → visor cards. No BOM. B3 slots only for declared-architecture missing keys."""
from __future__ import annotations

from pathlib import Path

import pytest

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


def test_missing_expected_keys_of_declared_blocks_become_slots():
    """B3 (Spatial Board Product Limits, honest absence) supersedes the old
    'never invent anything' rule: a declared block's expected key that
    isn't in components now renders as a display-only kind="slot" node —
    never for an undeclared block (wheels/actuation stays invisible)."""
    state = _state(
        {"motors": ComponentSpec(name="M")},
        blocks=["propulsion", "energy", "structure", "control"],
    )
    nodes = project_spatial_nodes(state)
    by_id = {node["id"]: node for node in nodes}
    assert "wheels" not in by_id  # actuation not declared — still invents nothing there
    assert by_id["motors"]["kind"] == "component"
    for key in ("propellers", "esc", "battery", "frame", "flight_controller", "sensors"):
        assert by_id[key]["kind"] == "slot"
    assert set(by_id) == {
        "motors", "propellers", "esc", "battery", "frame", "flight_controller", "sensors",
    }


def test_no_declared_blocks_still_invents_nothing():
    state = _state({"motors": ComponentSpec(name="M")}, blocks=[])
    ids = [node["id"] for node in project_spatial_nodes(state)]
    assert ids == ["motors"]


def test_empty_components_with_declared_blocks_yields_only_slots():
    """N2 lock: empty components + non-empty system_blocks must NOT
    short-circuit to []. Every expected key (deduped across blocks) of the
    four declared blocks becomes a slot."""
    state = _state({}, blocks=["propulsion", "energy", "structure", "control"])
    nodes = project_spatial_nodes(state)
    assert set(n["id"] for n in nodes) == {
        "motors", "propellers", "esc", "battery", "frame", "flight_controller", "sensors",
    }
    assert all(n["kind"] == "slot" for n in nodes)


def test_fixture_a_present_components_plus_missing_expected_slots():
    """Investigation report Fixture A, reconstructed as a regression test:
    motors/battery/frame/frame_arm/empty-name flight_controller declared;
    propellers/esc/sensors missing from a declared 4/4 architecture."""
    state = _state(
        {
            "motors": ComponentSpec(
                name="emax_rs2205_2300",
                properties={"thrust_n": PropertyValue(value=8.0, unit="N")},
                catalog_ref=CatalogRef(family="motor", sku="emax_rs2205_2300"),
            ),
            "battery": ComponentSpec(name="lipo_4s_1500"),
            "frame": ComponentSpec(name="armattan_rooster_5in"),
            "frame_arm": ComponentSpec(
                name="brazos", parent_key="frame",
                properties={"thickness_mm": PropertyValue(value=4.0, unit="mm")},
            ),
            "flight_controller": ComponentSpec(name=""),
        },
        blocks=["propulsion", "energy", "structure", "control"],
    )
    by_id = {node["id"]: node for node in project_spatial_nodes(state)}
    for key in ("propellers", "esc", "sensors"):
        assert by_id[key]["kind"] == "slot"
    fc = by_id["flight_controller"]
    assert fc["kind"] == "component"
    assert fc["declaredName"] == ""
    assert by_id["frame_arm"]["kind"] == "part"


def test_present_key_never_dual_slot_and_card():
    state = _state(
        {"esc": ComponentSpec(name="afro_esc_30a")},
        blocks=["propulsion", "energy", "structure", "control"],
    )
    nodes = project_spatial_nodes(state)
    esc_nodes = [n for n in nodes if n["id"] == "esc"]
    assert len(esc_nodes) == 1
    assert esc_nodes[0]["kind"] == "component"


def test_slot_payload_shape():
    state = _state({}, blocks=["structure"])
    nodes = project_spatial_nodes(state)
    assert len(nodes) == 1
    slot = nodes[0]
    assert slot["id"] == "frame"
    assert slot["kind"] == "slot"
    assert slot["declaredName"] == ""
    assert slot["fields"] == [{"label": "estado", "value": "no declarado"}]
    assert not any(f["label"] == "SKU" for f in slot["fields"])


def test_projector_module_does_not_import_bom_or_readiness_or_continuity():
    """Module isolation (locked stance): the projector must stay a pure
    ProjectState reader — no BOM bucket, ERF, or Continuity authority."""
    import inspect

    import jarvis.workspace.spatial_board as mod

    source = inspect.getsource(mod)
    for forbidden in ("build_component_bom", "engineering_readiness", "project_continuity"):
        assert forbidden not in source


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


# ── Board glyphs (Geometry Progression Lock B1, `visualizar`) ───────────────

def test_geometry_box_from_full_lwh_triple():
    """A full length/width/height triple emits a box glyph — no cylinder,
    no stitching, verbatim mm values."""
    state = _state(
        {
            "battery": ComponentSpec(
                name="lipo_4s_1500mah",
                properties={
                    "length_mm": PropertyValue(value=37.0, unit="mm"),
                    "width_mm": PropertyValue(value=35.0, unit="mm"),
                    "height_mm": PropertyValue(value=75.0, unit="mm"),
                },
            )
        }
    )
    node = project_spatial_nodes(state)[0]
    assert node["geometry"] == {
        "shape": "box",
        "length_mm": 37.0,
        "width_mm": 35.0,
        "height_mm": 75.0,
    }


def test_geometry_disk_from_diameter_mm():
    """A bare diameter_mm (e.g. a motor's overall bell diameter) emits a
    disk — never a cylinder, even though the spec below also carries a
    stator height for a DIFFERENT physical reference (N: no stitching)."""
    state = _state(
        {
            "motors": ComponentSpec(
                name="emax_rs2205s_2300",
                properties={
                    "diameter_mm": PropertyValue(value=27.9, unit="mm"),
                    "stator_diameter_mm": PropertyValue(value=22.0, unit="mm"),
                    "stator_height_mm": PropertyValue(value=5.0, unit="mm"),
                },
            )
        }
    )
    node = project_spatial_nodes(state)[0]
    assert node["geometry"] == {"shape": "disk", "diameter_mm": 27.9}


def test_geometry_disk_from_diameter_in_converts_to_mm():
    """diameter_in converts to an mm-equivalent for the glyph only — the
    text field keeps declaring the original inch unit unchanged."""
    state = _state(
        {
            "propellers": ComponentSpec(
                name="gemfan_5030",
                properties={"diameter_in": PropertyValue(value=5.0, unit="in")},
            )
        }
    )
    node = project_spatial_nodes(state)[0]
    assert node["geometry"] == {"shape": "disk", "diameter_mm": pytest.approx(127.0)}
    assert {"label": "diameter_in", "value": "5 in"} in node["fields"]


def test_geometry_absent_when_only_thickness_declared():
    """Thickness alone (frame arm/plate) cannot define a 2D area — no
    geometry key at all, never a partial/dashed shape."""
    state = _state(
        {
            "frame_arm": ComponentSpec(
                name="brazos",
                parent_key="frame",
                properties={"thickness_mm": PropertyValue(value=4.0, unit="mm")},
            ),
        }
    )
    node = project_spatial_nodes(state)[0]
    assert "geometry" not in node


def test_geometry_absent_when_no_dimension_properties():
    """A component with no dimension-shaped properties at all gets no
    geometry key (baseline absence case)."""
    state = _state({"motors": ComponentSpec(name="M", properties={"thrust_n": PropertyValue(value=8.0, unit="N")})})
    node = project_spatial_nodes(state)[0]
    assert "geometry" not in node


def test_geometry_never_on_slots():
    """B3 slot nodes never carry a geometry key, even when the column's
    other real components do."""
    state = _state(
        {
            "motors": ComponentSpec(
                name="M",
                properties={"diameter_mm": PropertyValue(value=27.9, unit="mm")},
            ),
        },
        blocks=["propulsion"],
    )
    by_id = {n["id"]: n for n in project_spatial_nodes(state)}
    assert by_id["motors"]["geometry"] == {"shape": "disk", "diameter_mm": 27.9}
    assert by_id["propellers"]["kind"] == "slot"
    assert "geometry" not in by_id["propellers"]
    assert "geometry" not in by_id["esc"]


def test_geometry_box_wins_over_diameter_when_both_present():
    """N: a complete L×W×H triple takes priority over any diameter also
    present on the same spec — box, never disk, never both keys."""
    state = _state(
        {
            "flight_controller": ComponentSpec(
                name="pixhawk_4",
                properties={
                    "length_mm": PropertyValue(value=44.0, unit="mm"),
                    "width_mm": PropertyValue(value=84.0, unit="mm"),
                    "height_mm": PropertyValue(value=12.0, unit="mm"),
                    "diameter_mm": PropertyValue(value=30.5, unit="mm"),
                },
            )
        }
    )
    node = project_spatial_nodes(state)[0]
    assert node["geometry"]["shape"] == "box"
    assert "diameter_mm" not in node["geometry"]


def test_geometry_does_not_affect_card_pixel_layout():
    """Card width/height stay the projector's pixel-layout defaults —
    unrelated to and untouched by the new geometry payload."""
    state = _state(
        {
            "battery": ComponentSpec(
                name="lipo_4s_1500mah",
                properties={
                    "length_mm": PropertyValue(value=37.0, unit="mm"),
                    "width_mm": PropertyValue(value=35.0, unit="mm"),
                    "height_mm": PropertyValue(value=75.0, unit="mm"),
                },
            )
        }
    )
    node = project_spatial_nodes(state)[0]
    assert node["width"] == 280
    assert isinstance(node["height"], int)
    assert node["height"] != node["geometry"]["height_mm"]
