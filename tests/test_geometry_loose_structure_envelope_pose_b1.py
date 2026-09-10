"""Loose structure/kit envelopes + pose subjects B1.

Covers implementation_contract_geometry_loose_structure_envelope_pose_b1.md
§3 — extends the declared-envelope writer/parser AND the pose Continuity
subject resolver with exactly four presence-gated keys:
`prop_adapter`/`frame_standoff`/`frame_cage`/`frame_caps`. Reuses existing
nouns where they exist (`frame_cage`/`frame_standoff` via
`resolve_declared_part_noun`'s own jaula/standoff handling) and a small new
presence-gated pattern table for the two keys with no existing noun
anywhere (`prop_adapter` via adaptador/adapter/collet; `frame_caps` via
caps/tapas). No new noun table for the pose side — the exact same resolver
(`resolve_loose_structure_subject_noun`) backs both grammars. Fixture
numbers: adapter 12/12/8, standoff 5/5/25, cage 40/40/30, caps 10/10/2.
Never Rooster marketing dims.

  P1  Writer SET each new key (when present) -> three props source=declared
  P2  Parser nouns -> SET for adapter/standoff/cage/caps
  P3  Missing key + noun -> no invent (INCOMPLETE for SET-shaped)
  P4  Pose subject same nouns -> SET when origin is a box
  P5  Pair-only phrase -> INCOMPLETE (no thickness fallback)
  P6  Battery/plate/kit/arm envelope regressions still green
  P7  Library untouched — no new L×W×H seeds on these SKUs
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_envelope
from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState

_LOOSE_KEYS = ("prop_adapter", "frame_standoff", "frame_cage", "frame_caps")


def _loose_components() -> dict:
    return {
        "prop_adapter": ComponentSpec(
            suggested_key="prop_adapter", completeness="medium", name="con adaptador/collet",
        ),
        "frame_standoff": ComponentSpec(
            suggested_key="frame_standoff", completeness="high",
            properties={"material": PropertyValue(value="aluminio", source="declared")},
        ),
        "frame_cage": ComponentSpec(
            suggested_key="frame_cage", completeness="high",
            properties={"material": PropertyValue(value="titanio", source="declared")},
        ),
        "frame_caps": ComponentSpec(suggested_key="frame_caps", completeness="medium"),
    }


def _frame_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Main Plate", source="declared"),
        },
    )


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


@pytest.mark.parametrize("key,dims", [
    ("prop_adapter", (12.0, 12.0, 8.0)),
    ("frame_standoff", (5.0, 5.0, 25.0)),
    ("frame_cage", (40.0, 40.0, 30.0)),
    ("frame_caps", (10.0, 10.0, 2.0)),
])
def test_p1_writer_set_each_new_key(key, dims):
    state = _state(_loose_components())
    updated = set_component_declared_box_envelope(state, key, *dims)
    spec = updated.design_properties.components[key]
    assert spec.properties["length_mm"].value == dims[0]
    assert spec.properties["width_mm"].value == dims[1]
    assert spec.properties["height_mm"].value == dims[2]
    assert spec.properties["length_mm"].source == "declared"


@pytest.mark.parametrize("phrase,expected_key,dims", [
    ("declara el adaptador 12 x 12 x 8 mm", "prop_adapter", (12.0, 12.0, 8.0)),
    ("declara el collet 12 x 12 x 8 mm", "prop_adapter", (12.0, 12.0, 8.0)),
    ("declara el standoff 5 x 5 x 25 mm", "frame_standoff", (5.0, 5.0, 25.0)),
    ("declara la jaula 40 x 40 x 30 mm", "frame_cage", (40.0, 40.0, 30.0)),
    ("declara los caps 10 x 10 x 2 mm", "frame_caps", (10.0, 10.0, 2.0)),
])
def test_p2_parser_nouns_resolve_expected_key(phrase, expected_key, dims):
    components = _loose_components()
    result = parse_declared_envelope_declare(phrase, components)
    assert result.kind == "SET"
    assert result.component_key == expected_key
    assert (result.length_mm, result.width_mm, result.height_mm) == dims


@pytest.mark.parametrize("phrase", [
    "declara el adaptador 12 x 12 x 8 mm",
    "declara el standoff 5 x 5 x 25 mm",
    "declara la jaula 40 x 40 x 30 mm",
    "declara los caps 10 x 10 x 2 mm",
])
def test_p3_missing_key_never_invented(phrase):
    result = parse_declared_envelope_declare(phrase, {})
    assert result.kind == "INCOMPLETE"
    assert result.component_key is None


def test_p4_pose_subject_same_nouns_set_when_origin_is_box():
    components = {**_loose_components(), "frame_plate": _frame_plate_spec()}

    r_adapter = parse_declared_box_pose_declare(
        "declara el adaptador a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate", components
    )
    assert r_adapter.kind == "SET"
    assert r_adapter.component_key == "prop_adapter"
    assert r_adapter.origin_key == "frame_plate"

    r_standoff = parse_declared_box_pose_declare(
        "declara el standoff a 5 mm en x respecto a frame_plate", components
    )
    assert r_standoff.kind == "SET"
    assert r_standoff.component_key == "frame_standoff"

    r_cage = parse_declared_box_pose_declare(
        "declara la jaula a 0 mm en x respecto a frame_plate", components
    )
    assert r_cage.kind == "SET"
    assert r_cage.component_key == "frame_cage"

    r_caps = parse_declared_box_pose_declare(
        "declara los caps a 0 mm en x respecto a frame_plate", components
    )
    assert r_caps.kind == "SET"
    assert r_caps.component_key == "frame_caps"

    # respecto/envelope collision unchanged: same phrase without "respecto"
    # never reaches the pose parser's SET branch.
    envelope_only = parse_declared_envelope_declare("declara el adaptador 12 x 12 x 8 mm", components)
    assert envelope_only.kind == "SET"
    pose_only = parse_declared_box_pose_declare("declara el adaptador 12 x 12 x 8 mm", components)
    assert pose_only.kind == "NONE"

    # CLEAR still resolves the same subjects.
    clear_result = parse_declared_box_pose_declare("quita la pose del adaptador", components)
    assert clear_result.kind == "CLEAR"
    assert clear_result.component_key == "prop_adapter"


@pytest.mark.parametrize("phrase,expected_key", [
    ("declara el adaptador 12 x 12 mm", "prop_adapter"),
    ("declara el standoff 5 x 5 mm", "frame_standoff"),
])
def test_p5_pair_only_phrase_is_incomplete_no_thickness_fallback(phrase, expected_key):
    components = _loose_components()
    result = parse_declared_envelope_declare(phrase, components)
    assert result.kind == "INCOMPLETE"
    assert result.component_key == expected_key


def test_p6_battery_plate_kit_arm_envelope_regressions_still_green():
    components = {
        "battery": ComponentSpec(
            suggested_key="battery", completeness="high",
            properties={"battery_capacity_wh": PropertyValue(value=24.42, unit="Wh", source="declared")},
        ),
        "frame_plate": _frame_plate_spec(),
        "power_connector": ComponentSpec(suggested_key="power_connector", completeness="medium", name="XT60"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", completeness="medium",
            properties={"thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared")},
        ),
    }

    r_battery = parse_declared_envelope_declare("declara la bateria 80 x 34 x 22 mm", components)
    assert r_battery.kind == "SET" and r_battery.component_key == "battery"

    r_plate = parse_declared_envelope_declare("declara la placa principal 100 x 100 mm", components)
    assert r_plate.kind == "SET" and r_plate.component_key == "frame_plate"
    assert r_plate.height_mm is None  # thickness fallback still plate-only

    r_kit = parse_declared_envelope_declare("declara el conector 30 x 20 x 10 mm", components)
    assert r_kit.kind == "SET" and r_kit.component_key == "power_connector"

    r_arm = parse_declared_envelope_declare("declara el brazo 80 x 20 x 4 mm", components)
    assert r_arm.kind == "SET" and r_arm.component_key == "frame_arm"


def test_p7_library_untouched_no_new_lxwxh_seeds():
    repo_root = Path(__file__).resolve().parents[1]
    frames_data = json.loads((repo_root / "library" / "frames" / "_datos.json").read_text(encoding="utf-8"))
    forbidden_keys = (
        "prop_adapter_length_mm", "prop_adapter_width_mm", "prop_adapter_height_mm",
        "standoff_length_mm", "standoff_width_mm",
        "cage_length_mm", "cage_width_mm",
        "caps_length_mm", "caps_width_mm",
    )
    for sku, row in frames_data.items():
        for forbidden in forbidden_keys:
            assert forbidden not in row, f"{sku} unexpectedly gained {forbidden}"
