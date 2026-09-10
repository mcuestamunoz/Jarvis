"""Visor X stations from cited wheelbase B1.

Covers implementation_contract_geometry_visor_x_stations_b1.md §3.1-3.2: an
additive `solidCopyOffsetsMm` DTO on `motors`/`propellers` nodes, emitted
ONLY when the spec's own `solidCopies` (Motor/Propeller visor copies B1,
unchanged) is EXACTLY 4 AND the frame declares `configuration == "quad_x"`
AND a finite positive `wheelbase_mm` (motor-to-motor, per the Rooster
source_note). Points: a = W / (2*sqrt(2)); (±a,±a,0) at indices FR/FL/RL/RR.
Never a default, never coerced N=4, never read from `current_parameters`.

  P1  motors count 4 + disk + frame quad_x + wheelbase 230 -> motors
      solidCopies==4 + 4 offsets; opposite (0 vs 2) distance approx 230;
      propellers SAME 4 offsets; still one node each
  P2  count 3 + disk + quad_x + 230 -> solidCopies==3, no offsets anywhere
  P3  count 4 + disk, frame without wheelbase_mm -> no offsets
  P4  count 4 + disk, wheelbase_mm 230, no configuration -> no offsets
  P5  count 4 + disk + configuration=hex + 230 -> no offsets
  P6  motors no diameter, count 4, props disk, frame gate holds -> motors
      no geometry/no offsets; propellers HAS offsets (same points as P1)
  P7  no motor_count, frame quad_x+230, both disks -> no solidCopies, no
      offsets anywhere (quad_x does not win)
"""
from __future__ import annotations

import math

import pytest

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_P1_OFFSETS = [
    {"xMm": pytest.approx(81.317, abs=1e-2), "yMm": pytest.approx(81.317, abs=1e-2), "zMm": 0.0},
    {"xMm": pytest.approx(81.317, abs=1e-2), "yMm": pytest.approx(-81.317, abs=1e-2), "zMm": 0.0},
    {"xMm": pytest.approx(-81.317, abs=1e-2), "yMm": pytest.approx(-81.317, abs=1e-2), "zMm": 0.0},
    {"xMm": pytest.approx(-81.317, abs=1e-2), "yMm": pytest.approx(81.317, abs=1e-2), "zMm": 0.0},
]


def _motors_spec(motor_count: float | None, diameter_mm: float | None = 27.9) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_mm is not None:
        props["diameter_mm"] = PropertyValue(value=diameter_mm, unit="mm", source="declared")
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="declared")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


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


def _state(components: dict[str, ComponentSpec]) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def test_p1_count_4_quad_x_230_yields_4_offsets_matching_wheelbase():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(),
    }))
    motors = nodes["motors"]
    propellers = nodes["propellers"]

    assert motors["solidCopies"] == 4
    assert motors["solidCopyOffsetsMm"] == _P1_OFFSETS
    p0, p2 = motors["solidCopyOffsetsMm"][0], motors["solidCopyOffsetsMm"][2]
    dist = math.hypot(p0["xMm"] - p2["xMm"], p0["yMm"] - p2["yMm"])
    assert dist == pytest.approx(230.0)

    assert propellers["solidCopies"] == 4
    assert propellers["solidCopyOffsetsMm"] == motors["solidCopyOffsetsMm"]

    assert sum(1 for n in nodes.values() if n["id"] == "motors") == 1
    assert sum(1 for n in nodes.values() if n["id"] == "propellers") == 1


def test_p2_count_3_never_stations_even_with_quad_x_and_wheelbase():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(),
    }))
    assert nodes["motors"]["solidCopies"] == 3
    assert "solidCopyOffsetsMm" not in nodes["motors"]
    assert nodes["propellers"]["solidCopies"] == 3
    assert "solidCopyOffsetsMm" not in nodes["propellers"]


def test_p3_missing_wheelbase_never_invents_230():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(wheelbase_mm=None),
    }))
    assert "solidCopyOffsetsMm" not in nodes["motors"]
    assert "solidCopyOffsetsMm" not in nodes["propellers"]


def test_p4_missing_configuration_yields_no_offsets():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(configuration=None),
    }))
    assert "solidCopyOffsetsMm" not in nodes["motors"]
    assert "solidCopyOffsetsMm" not in nodes["propellers"]


def test_p5_non_quad_x_configuration_yields_no_offsets():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(configuration="hex"),
    }))
    assert "solidCopyOffsetsMm" not in nodes["motors"]
    assert "solidCopyOffsetsMm" not in nodes["propellers"]


def test_p6_mute_motors_no_offsets_propellers_still_station():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4, diameter_mm=None),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(),
    }))
    motors = nodes["motors"]
    propellers = nodes["propellers"]
    assert "geometry" not in motors
    assert "solidCopyOffsetsMm" not in motors
    assert propellers["solidCopyOffsetsMm"] == _P1_OFFSETS


def test_p7_no_motor_count_quad_x_does_not_win():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=None),
        "propellers": _propellers_spec(),
        "frame": _frame_spec(),
    }))
    assert "solidCopies" not in nodes["motors"]
    assert "solidCopyOffsetsMm" not in nodes["motors"]
    assert "solidCopies" not in nodes["propellers"]
    assert "solidCopyOffsetsMm" not in nodes["propellers"]
