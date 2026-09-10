"""Declared battery envelope + Main Plate L×W B1.

Covers implementation_contract_geometry_declared_battery_plate_envelope_b1.md
§3/§4 — an IDLE declare/clear of a box triple (`length_mm`/`width_mm`/
`height_mm`, `source=declared`) on exactly two families: `battery` and any
`frame_plate*` key. Fixture numbers are deliberately NOT catalog claims:
battery 80/34/22, plate 100/100 (H from cited `thickness_mm` 4). Never 230
(wheelbase), never 202 (iFlight), never 138.5.

  P1  Parse+write battery 80x34x22 -> those three props, source=declared;
      catalog_ref/Wh/mass/cells unchanged; projector geometry box 80/34/22
  P2  Parse+write "declara la placa principal 100 x 100 mm" -> L=100 W=100
      height_mm=4 (from thickness_mm); thickness_mm still 4; frame
      wheelbase still 230; projector box 100/100/4; one plate node
  P3  Two-number phrase on battery -> INCOMPLETE; no write
  P4  Bare "declara la placa 100 x 100 mm" with two plates -> AMBIGUOUS_PLATE
  P5  CLEAR battery pops only the three box keys; energy fields remain
  P6  Writer SET on frame/motors -> ValueError; no geometry invented
  P7  After P2, set_component_declared_box_pose battery vs frame_plate
      succeeds; before P2 it raises
  P8  Phrase with "respecto" -> envelope parse NONE
  P9  refresh_component_from_catalog battery after P1 -> L×W×H still
      80/34/22
  P10 IDLE orchestrator: SET battery phrase saves; "cambiar batería" still
      opens the battery catalog (regression)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import (
    refresh_component_from_catalog,
    set_component_declared_box_envelope,
    set_component_declared_box_pose,
)
from jarvis.core.declared_envelope_declare_assist import parse_declared_envelope_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _battery_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="battery", completeness="high",
        properties={
            "battery_capacity_wh": PropertyValue(value=24.42, unit="Wh", source="declared"),
            "mass_g": PropertyValue(value=195.0, unit="g", source="declared"),
            "cell_count": PropertyValue(value=3, source="declared"),
        },
        catalog_ref=CatalogRef(family="battery", sku="lipo_3s_2200mah"),
    )


def _main_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Main Plate", source="declared"),
            "material": PropertyValue(value="fibra de carbono", source="declared"),
        },
    )


def _second_plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate_2", completeness="high",
        properties={
            "thickness_mm": PropertyValue(value=2.0, unit="mm", source="declared"),
            "label": PropertyValue(value="Top (LiPo) plate", source="declared"),
        },
    )


def _frame_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={
            "wheelbase_mm": PropertyValue(value=230.0, unit="mm", source="declared"),
            "configuration": PropertyValue(value="quad_x", source="declared"),
        },
    )


def _motors_spec() -> ComponentSpec:
    return ComponentSpec(suggested_key="motors", completeness="high", properties={})


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _live_components(with_second_plate: bool = False) -> dict:
    components = {
        "battery": _battery_spec(),
        "frame_plate": _main_plate_spec(),
        "frame": _frame_spec(),
        "motors": _motors_spec(),
    }
    if with_second_plate:
        components["frame_plate_2"] = _second_plate_spec()
    return components


def test_p1_battery_set_writes_three_keys_and_preserves_identity():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la bateria 80 x 34 x 22 mm", components)
    assert result.kind == "SET"
    assert result.component_key == "battery"
    assert (result.length_mm, result.width_mm, result.height_mm) == (80.0, 34.0, 22.0)

    state = _state(components)
    updated = set_component_declared_box_envelope(
        state, "battery", result.length_mm, result.width_mm, result.height_mm
    )
    battery = updated.design_properties.components["battery"]
    assert battery.properties["length_mm"].value == 80.0
    assert battery.properties["width_mm"].value == 34.0
    assert battery.properties["height_mm"].value == 22.0
    assert battery.properties["length_mm"].source == "declared"
    assert battery.catalog_ref.sku == "lipo_3s_2200mah"
    assert battery.properties["battery_capacity_wh"].value == 24.42
    assert battery.properties["mass_g"].value == 195.0
    assert battery.properties["cell_count"].value == 3

    nodes = {n["id"]: n for n in project_spatial_nodes(updated)}
    assert nodes["battery"]["geometry"] == {
        "shape": "box", "length_mm": 80.0, "width_mm": 34.0, "height_mm": 22.0,
    }


def test_p2_main_plate_set_two_numbers_height_from_thickness():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la placa principal 100 x 100 mm", components)
    assert result.kind == "SET"
    assert result.component_key == "frame_plate"
    assert (result.length_mm, result.width_mm) == (100.0, 100.0)
    assert result.height_mm is None  # parser never invents it — orchestrator reads thickness

    state = _state(components)
    thickness = state.design_properties.components["frame_plate"].properties["thickness_mm"].value
    updated = set_component_declared_box_envelope(
        state, "frame_plate", result.length_mm, result.width_mm, thickness
    )
    plate = updated.design_properties.components["frame_plate"]
    assert plate.properties["length_mm"].value == 100.0
    assert plate.properties["width_mm"].value == 100.0
    assert plate.properties["height_mm"].value == 4.0
    assert plate.properties["thickness_mm"].value == 4.0  # untouched

    frame_wheelbase = updated.design_properties.components["frame"].properties["wheelbase_mm"].value
    assert frame_wheelbase == 230.0

    nodes = {n["id"]: n for n in project_spatial_nodes(updated)}
    assert nodes["frame_plate"]["geometry"] == {
        "shape": "box", "length_mm": 100.0, "width_mm": 100.0, "height_mm": 4.0,
    }
    assert sum(1 for n in nodes.values() if n["id"] == "frame_plate") == 1


def test_p3_battery_two_numbers_is_incomplete_no_write():
    components = _live_components()
    result = parse_declared_envelope_declare("declara la bateria 80 x 34 mm", components)
    assert result.kind == "INCOMPLETE"
    assert result.component_key == "battery"


def test_p4_bare_placa_with_two_plates_is_ambiguous():
    components = _live_components(with_second_plate=True)
    result = parse_declared_envelope_declare("declara la placa 100 x 100 mm", components)
    assert result.kind == "AMBIGUOUS_PLATE"
    keys = {k for k, _label in result.candidates}
    assert keys == {"frame_plate", "frame_plate_2"}


def test_p5_clear_battery_pops_only_box_keys():
    components = _live_components()
    state = _state(components)
    with_box = set_component_declared_box_envelope(state, "battery", 80.0, 34.0, 22.0)

    result = parse_declared_envelope_declare("quita el sobre de la bateria", components)
    assert result.kind == "CLEAR"
    assert result.component_key == "battery"

    cleared = set_component_declared_box_envelope(with_box, "battery", None, None, None)
    battery = cleared.design_properties.components["battery"]
    assert "length_mm" not in battery.properties
    assert "width_mm" not in battery.properties
    assert "height_mm" not in battery.properties
    assert battery.properties["battery_capacity_wh"].value == 24.42
    assert battery.properties["mass_g"].value == 195.0
    assert battery.properties["cell_count"].value == 3


def test_p6_writer_rejects_frame_root_and_motors():
    state = _state(_live_components())
    with pytest.raises(ValueError):
        set_component_declared_box_envelope(state, "frame", 100.0, 100.0, 4.0)
    with pytest.raises(ValueError):
        set_component_declared_box_envelope(state, "motors", 10.0, 10.0, 10.0)

    nodes = {n["id"]: n for n in project_spatial_nodes(state)}
    assert "geometry" not in nodes["frame"]


def test_p7_plate_box_unlocks_pose_origin():
    state = _state(_live_components())
    with pytest.raises(ValueError):
        set_component_declared_box_pose(
            state, "battery", DeclaredBoxPose(origin_key="frame_plate", z_mm=10.0)
        )

    with_plate_box = set_component_declared_box_envelope(state, "frame_plate", 100.0, 100.0, 4.0)
    after_pose = set_component_declared_box_pose(
        with_plate_box, "battery", DeclaredBoxPose(origin_key="frame_plate", z_mm=10.0)
    )
    pose = after_pose.design_properties.components["battery"].declared_box_pose
    assert pose.origin_key == "frame_plate"
    assert pose.z_mm == pytest.approx(10.0)


def test_p8_respecto_phrase_is_none():
    components = _live_components()
    result = parse_declared_envelope_declare(
        "declara la bateria 80 x 34 x 22 mm respecto a frame_plate", components
    )
    assert result.kind == "NONE"


def test_p9_refresh_from_catalog_preserves_declared_dims():
    state = _state(_live_components())
    with_box = set_component_declared_box_envelope(state, "battery", 80.0, 34.0, 22.0)
    refreshed = refresh_component_from_catalog(with_box, "battery")
    battery = refreshed.design_properties.components["battery"]
    assert battery.properties["length_mm"].value == 80.0
    assert battery.properties["width_mm"].value == 34.0
    assert battery.properties["height_mm"].value == 22.0


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "declared envelope b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, **components}}
    )
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_p10_idle_orchestrator_set_battery_saves_and_rebind_still_works(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _live_components())
    result = orch.handle_user_text("declara la bateria 80 x 34 x 22 mm", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Declarado" in result["message"]
    lower = result["message"].lower()
    for forbidden in ("cabe", "verificado", "ensamblado", "230"):
        assert forbidden not in lower

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    battery = ps.design_properties.components["battery"]
    assert battery.properties["length_mm"].value == 80.0
    assert battery.properties["width_mm"].value == 34.0
    assert battery.properties["height_mm"].value == 22.0

    rebind_result = orch.handle_user_text("cambiar bateria", _RefuseLLM())
    assert rebind_result["status"] in {"interactive", "ok"}
