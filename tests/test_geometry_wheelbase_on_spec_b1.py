"""Mapping rung 2 first cut — wheelbase on the bound frame spec B1.

Covers implementation_contract_geometry_wheelbase_on_spec_b1.md:
  T1  Stale rooster-like frame refresh → wheelbase_mm 230; sibling plate untouched
  T2  Stale projector card does not invent 230 from the seed
  T3  After refresh, projector shows wheelbase_mm 230 mm
  T4  IDLE "actualiza la frame" persists 230; no cabe/ensamblado copy
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import refresh_component_from_catalog
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _stale_rooster_frame() -> ComponentSpec:
    return ComponentSpec(
        name="armattan_rooster_5in",
        suggested_key="frame",
        component_type="structure",
        completeness="high",
        catalog_ref=CatalogRef(family="frame", sku="armattan_rooster_5in"),
        properties={
            "mass_kg": PropertyValue(value=0.125, unit="kg", source="declared"),
            "size_class_inch": PropertyValue(value=5.0, unit="in", source="declared"),
            "material": PropertyValue(value="fibra de carbono", source="declared"),
        },
    )


def _stale_state() -> ProjectState:
    plate = ComponentSpec(
        name="Main Plate",
        suggested_key="frame_plate",
        component_type="structure_part",
        parent_key="frame",
        completeness="medium",
        properties={
            "thickness_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
        },
    )
    return ProjectState(
        project_id="p1",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
        design_properties=DesignProperties(
            components={"frame": _stale_rooster_frame(), "frame_plate": plate}
        ),
    )


def _frame_fields(nodes: list[dict]) -> list[dict[str, str]]:
    frame = next(n for n in nodes if n["id"] == "frame")
    return frame["fields"]


def test_t1_refresh_stale_rooster_projects_wheelbase_leaves_plate():
    state = _stale_state()
    plate_before = state.design_properties.components["frame_plate"].model_dump()
    updated = refresh_component_from_catalog(state, "frame")
    frame = updated.design_properties.components["frame"]
    assert frame.properties["wheelbase_mm"].value == pytest.approx(230.0)
    assert frame.properties["wheelbase_mm"].unit == "mm"
    assert frame.properties["configuration"].value == "quad_x"
    assert frame.properties["mass_kg"].value == pytest.approx(0.125)
    assert frame.properties["material"].value == "fibra de carbono"
    assert updated.design_properties.components["frame_plate"].model_dump() == plate_before


def test_t2_stale_projector_does_not_invent_wheelbase_from_seed():
    fields = _frame_fields(project_spatial_nodes(_stale_state()))
    labels = [f["label"] for f in fields]
    assert "wheelbase_mm" not in labels
    assert all("230" not in f["value"] for f in fields)


def test_t3_refreshed_projector_shows_wheelbase_230_mm():
    updated = refresh_component_from_catalog(_stale_state(), "frame")
    fields = _frame_fields(project_spatial_nodes(updated))
    by_label = {f["label"]: f["value"] for f in fields}
    assert by_label["wheelbase_mm"] == "230 mm"


def test_t4_idle_refresh_persists_wheelbase(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "wheelbase on spec b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    stale = _stale_state()
    updated_dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, **stale.design_properties.components}}
    )
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)

    result = orch.handle_user_text("actualiza la frame", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Actualizado desde catálogo" in result["message"]
    assert "230" in result["message"]
    for forbidden in ("corregido automáticamente", "verificado", "cabe", "ensamblado"):
        assert forbidden not in result["message"].lower()

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    frame = ps.design_properties.components["frame"]
    assert frame.properties["wheelbase_mm"].value == pytest.approx(230.0)
    plate = ps.design_properties.components["frame_plate"]
    assert plate.parent_key == "frame"
    assert plate.properties["thickness_mm"].value == pytest.approx(4.0)
