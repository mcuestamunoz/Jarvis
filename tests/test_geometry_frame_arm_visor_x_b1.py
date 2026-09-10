"""Frame arm envelope + visor X copies B1.

Covers implementation_contract_geometry_frame_arm_visor_x_b1.md §3 —
(1) extends the declared-envelope writer/parser allowlist to accept
`frame_arm` (subject nouns: brazo/brazos/arm/arms, exact key), requiring
the full three-number phrase like battery (never a thickness->L/W
fallback); (2) extends `_solid_copies`/`_solid_copy_offsets_mm` so a boxed
`frame_arm` gets `solidCopies==4` and the SAME quad-X `solidCopyOffsetsMm`
points as motors/propellers, but ONLY when motors' own `motor_count==4`
AND the frame's `quad_x`+`wheelbase_mm` facts hold — any other count or a
missing quad_x/wheelbase leaves the arm as a single box (never a fake
"row of 3"), since unlike motors/propellers a row of N identical arm
copies isn't an honest fallback shape. Still ONE `frame_arm` ComponentSpec
forever. Fixture numbers: arm 80/20/4. Never 230, never a Rooster catalog
seed (arm_thickness_mm stays a card fact only).

  P1  Writer SET frame_arm 3 mm -> properties source=declared
  P2  Parser "declara el brazo A x B x C mm" -> SET frame_arm
  P3  Projector: arm box + motors count 4 + quad_x + wheelbase ->
      solidCopies==4, offsets length 4, SAME points as motors' own
      stations
  P4  N=3 or missing quad_x -> arm stays a SINGLE box, no solidCopies at
      all (documented choice — never a "row of 3")
  P5  No length_mm invented on the Rooster's arm_thickness_mm seed
  P6  Battery/plate/kit envelope regressions still green
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.component_writers import set_component_declared_box_envelope
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _frame_arm_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_arm", completeness="medium",
        properties={
            "material": PropertyValue(value="fibra de carbono", source="declared"),
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
        },
    )


def _motors_spec(motor_count: float | None) -> ComponentSpec:
    props: dict[str, PropertyValue] = {"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")}
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="declared")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


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


def test_p1_writer_set_frame_arm_three_mm():
    state = _state({"frame_arm": _frame_arm_spec()})
    updated = set_component_declared_box_envelope(state, "frame_arm", 80.0, 20.0, 4.0)
    arm = updated.design_properties.components["frame_arm"]
    assert arm.properties["length_mm"].value == 80.0
    assert arm.properties["width_mm"].value == 20.0
    assert arm.properties["height_mm"].value == 4.0
    assert arm.properties["length_mm"].source == "declared"
    assert arm.properties["thickness_mm"].value == 4.0  # untouched
    assert arm.properties["material"].value == "fibra de carbono"  # untouched


def test_p2_parser_brazo_phrase_sets_frame_arm():
    components = {"frame_arm": _frame_arm_spec()}
    result = parse_declared_envelope_declare("declara el brazo 80 x 20 x 4 mm", components)
    assert result.kind == "SET"
    assert result.component_key == "frame_arm"
    assert (result.length_mm, result.width_mm, result.height_mm) == (80.0, 20.0, 4.0)


def test_p3_projector_arm_stations_match_motors_with_count_4_and_quad_x():
    components = {
        "motors": _motors_spec(motor_count=4),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", completeness="high",
            properties={
                "length_mm": PropertyValue(value=80.0, unit="mm", source="declared"),
                "width_mm": PropertyValue(value=20.0, unit="mm", source="declared"),
                "height_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
                "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            },
        ),
        "frame": _frame_spec(),
    }
    nodes = {n["id"]: n for n in project_spatial_nodes(_state(components))}
    motors = nodes["motors"]
    arm = nodes["frame_arm"]

    assert arm["solidCopies"] == 4
    assert len(arm["solidCopyOffsetsMm"]) == 4
    assert arm["solidCopyOffsetsMm"] == motors["solidCopyOffsetsMm"]
    assert sum(1 for n in nodes.values() if n["id"] == "frame_arm") == 1


@pytest.mark.parametrize("motor_count,configuration", [
    (3, "quad_x"),
    (4, None),
])
def test_p4_arm_stays_single_box_without_full_quad_x_gate(motor_count, configuration):
    components = {
        "motors": _motors_spec(motor_count=motor_count),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", completeness="high",
            properties={
                "length_mm": PropertyValue(value=80.0, unit="mm", source="declared"),
                "width_mm": PropertyValue(value=20.0, unit="mm", source="declared"),
                "height_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            },
        ),
        "frame": _frame_spec(configuration=configuration),
    }
    nodes = {n["id"]: n for n in project_spatial_nodes(_state(components))}
    arm = nodes["frame_arm"]
    assert arm["geometry"] == {"shape": "box", "length_mm": 80.0, "width_mm": 20.0, "height_mm": 4.0}
    assert "solidCopies" not in arm
    assert "solidCopyOffsetsMm" not in arm


def test_p5_no_length_width_invented_on_rooster_arm_thickness_seed():
    repo_root = Path(__file__).resolve().parents[1]
    frames_data = json.loads((repo_root / "library" / "frames" / "_datos.json").read_text(encoding="utf-8"))
    for sku, row in frames_data.items():
        assert "arm_length_mm" not in row, f"{sku} unexpectedly gained arm_length_mm"
        assert "arm_width_mm" not in row, f"{sku} unexpectedly gained arm_width_mm"
        if "arm_thickness_mm" in row:
            assert isinstance(row["arm_thickness_mm"], (int, float))


def test_p6_battery_plate_kit_envelope_regressions_still_green():
    components = {
        "battery": ComponentSpec(
            suggested_key="battery", completeness="high",
            properties={"battery_capacity_wh": PropertyValue(value=24.42, unit="Wh", source="declared")},
        ),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", completeness="high",
            properties={
                "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
                "label": PropertyValue(value="Main Plate", source="declared"),
            },
        ),
        "power_connector": ComponentSpec(suggested_key="power_connector", completeness="medium", name="XT60"),
        "frame_arm": _frame_arm_spec(),
    }

    r_battery = parse_declared_envelope_declare("declara la bateria 80 x 34 x 22 mm", components)
    assert r_battery.kind == "SET" and r_battery.component_key == "battery"

    r_plate = parse_declared_envelope_declare("declara la placa principal 100 x 100 mm", components)
    assert r_plate.kind == "SET" and r_plate.component_key == "frame_plate"
    assert r_plate.height_mm is None  # thickness fallback still plate-only

    r_kit = parse_declared_envelope_declare("declara el conector 30 x 20 x 10 mm", components)
    assert r_kit.kind == "SET" and r_kit.component_key == "power_connector"

    r_arm_pair = parse_declared_envelope_declare("declara el brazo 80 x 20 mm", components)
    assert r_arm_pair.kind == "INCOMPLETE"  # arm never gets the plate's thickness fallback
