"""Prop adapter visor X copies B1.

Covers implementation_contract_geometry_prop_adapter_visor_x_b1.md §3 —
extends `_solid_copies`/`_solid_copy_offsets_mm` so a boxed `prop_adapter`
gets copies 1:1 with motors, following the SAME pattern already shipped
for `propellers` (own geometry gate, cross-read of motors' `motor_count`,
any valid N in [2,16] gets a row) — deliberately NOT the stricter
`frame_arm` gate (an adapter-per-motor is an honest fallback shape for any
N, unlike an arm whose whole point is sitting at its own quad-X station).
Station OFFSETS (`solidCopyOffsetsMm`) still only apply when N==4 AND the
frame's own quad_x+wheelbase facts hold — reusing `_quad_x_station_points`
verbatim, never a second formula. Fixture numbers: adapter 12/12/8. Never
230 as an adapter dimension.

  P1  Adapter box + motors count 4 + quad_x + wheelbase -> solidCopies==4,
      offsets identical to motors' own stations
  P2  N=3 + adapter box -> solidCopies==3 (row), no offsets — never a fake
      3-station X (documented: mirrors the propeller pattern, not the
      stricter frame_arm one)
  P3  No adapter geometry -> no solidCopies at all
  P4  Exactly one prop_adapter node regardless of copy count
  P5  Motors/propellers/frame_arm copy regressions still green
  P6  Library / version untouched
"""
from __future__ import annotations

import json
from pathlib import Path

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _motors_spec(motor_count: float | None, diameter_mm: float | None = 27.9) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_mm is not None:
        props["diameter_mm"] = PropertyValue(value=diameter_mm, unit="mm", source="declared")
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="declared")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


def _adapter_spec(with_geometry: bool = True) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if with_geometry:
        props["length_mm"] = PropertyValue(value=12.0, unit="mm", source="declared")
        props["width_mm"] = PropertyValue(value=12.0, unit="mm", source="declared")
        props["height_mm"] = PropertyValue(value=8.0, unit="mm", source="declared")
    return ComponentSpec(suggested_key="prop_adapter", completeness="medium", properties=props)


def _propellers_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")},
    )


def _frame_spec(configuration: str | None = "quad_x", wheelbase_mm: float | None = 230.0) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if configuration is not None:
        props["configuration"] = PropertyValue(value=configuration, unit="", source="declared")
    if wheelbase_mm is not None:
        props["wheelbase_mm"] = PropertyValue(value=wheelbase_mm, unit="mm", source="declared")
    return ComponentSpec(suggested_key="frame", completeness="high", properties=props)


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def test_p1_adapter_box_count_4_quad_x_wheelbase_matches_motors_stations():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "prop_adapter": _adapter_spec(),
        "frame": _frame_spec(),
    }))
    adapter = nodes["prop_adapter"]
    motors = nodes["motors"]
    assert adapter["solidCopies"] == 4
    assert len(adapter["solidCopyOffsetsMm"]) == 4
    assert adapter["solidCopyOffsetsMm"] == motors["solidCopyOffsetsMm"]


def test_p2_count_3_yields_row_never_a_fake_3_station_x():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3),
        "prop_adapter": _adapter_spec(),
        "frame": _frame_spec(),
    }))
    adapter = nodes["prop_adapter"]
    assert adapter["solidCopies"] == 3
    assert "solidCopyOffsetsMm" not in adapter


def test_p3_no_adapter_geometry_yields_no_solid_copies():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "prop_adapter": _adapter_spec(with_geometry=False),
        "frame": _frame_spec(),
    }))
    adapter = nodes["prop_adapter"]
    assert "geometry" not in adapter
    assert "solidCopies" not in adapter
    assert "solidCopyOffsetsMm" not in adapter


def test_p4_exactly_one_prop_adapter_node():
    nodes_list = project_spatial_nodes(_state({
        "motors": _motors_spec(motor_count=4),
        "prop_adapter": _adapter_spec(),
        "frame": _frame_spec(),
    }))
    assert sum(1 for n in nodes_list if n["id"] == "prop_adapter") == 1


def test_p5_motors_propellers_frame_arm_copy_regressions_still_green():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "propellers": _propellers_spec(),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", completeness="high",
            properties={
                "length_mm": PropertyValue(value=80.0, unit="mm", source="declared"),
                "width_mm": PropertyValue(value=20.0, unit="mm", source="declared"),
                "height_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            },
        ),
        "prop_adapter": _adapter_spec(),
        "frame": _frame_spec(),
    }))
    assert nodes["motors"]["solidCopies"] == 4
    assert nodes["propellers"]["solidCopies"] == 4
    assert nodes["frame_arm"]["solidCopies"] == 4
    assert nodes["prop_adapter"]["solidCopies"] == 4
    # All four families share the exact same quad-X station points.
    offsets = nodes["motors"]["solidCopyOffsetsMm"]
    assert nodes["propellers"]["solidCopyOffsetsMm"] == offsets
    assert nodes["frame_arm"]["solidCopyOffsetsMm"] == offsets
    assert nodes["prop_adapter"]["solidCopyOffsetsMm"] == offsets


def test_p6_library_and_version_untouched():
    repo_root = Path(__file__).resolve().parents[1]
    frames_data = json.loads((repo_root / "library" / "frames" / "_datos.json").read_text(encoding="utf-8"))
    for sku, row in frames_data.items():
        assert "prop_adapter_length_mm" not in row, f"{sku} unexpectedly gained prop_adapter_length_mm"

    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.4.0"' in pyproject_text
