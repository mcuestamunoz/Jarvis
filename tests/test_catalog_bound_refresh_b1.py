"""Catalog-bound property freshness B1 (refresh-from-catalog_ref).

Covers implementation_contract_catalog_bound_refresh_b1.md §4:
  T1  Writer: stale ESC mass 26 + catalog_ref -> 15; mounted_on preserved
  T2  Writer: no catalog_ref -> ValueError, no write
  T3  Writer: missing key -> ValueError
  T4  Parse SET for esc/motors/battery phrases; NONE for bare "actualizar"
  T5  Orchestrator IDLE refresh esc on fixture project -> persisted 15 + honest message
  T6  Non-regression: idle "cambiar frame" / mounted_on declare still work (smoke)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_refresh_assist import resolve_catalog_refresh_component
from jarvis.core.component_writers import diff_refreshed_properties, refresh_component_from_catalog
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _stale_esc_state() -> ProjectState:
    return ProjectState(
        project_id="p1",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
        design_properties=DesignProperties(
            components={
                "esc": ComponentSpec(
                    name="hobbywing_xrotor_40a_6s",
                    suggested_key="esc",
                    component_type="power_control",
                    completeness="high",
                    mounted_on="frame_plate",
                    catalog_ref=CatalogRef(family="esc", sku="hobbywing_xrotor_40a_6s"),
                    properties={
                        "current_a": PropertyValue(value=40.0, unit="A", source="declared"),
                        "mass_g": PropertyValue(value=26.0, unit="g", source="declared"),
                        "length_mm": PropertyValue(value=50.0, unit="mm", source="declared"),
                        "width_mm": PropertyValue(value=21.6, unit="mm", source="declared"),
                        "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
                    },
                ),
                "frame_plate": ComponentSpec(
                    suggested_key="frame_plate", component_type="structure_part",
                    parent_key="frame", completeness="medium",
                ),
            }
        ),
    )


# ── T1-T3: writer ────────────────────────────────────────────────────────


def test_t1_refresh_esc_fixes_stale_mass_preserves_mounted_on():
    state = _stale_esc_state()
    updated = refresh_component_from_catalog(state, "esc")
    esc = updated.design_properties.components["esc"]
    assert esc.properties["mass_g"].value == pytest.approx(15.0)
    assert esc.mounted_on == "frame_plate"
    assert esc.catalog_ref == CatalogRef(family="esc", sku="hobbywing_xrotor_40a_6s")
    # unrelated, already-fresh properties untouched
    assert esc.properties["current_a"].value == pytest.approx(40.0)
    assert esc.properties["length_mm"].value == pytest.approx(50.0)


def test_t1b_diff_helper_reports_only_the_changed_value():
    state = _stale_esc_state()
    old_spec = state.design_properties.components["esc"]
    updated = refresh_component_from_catalog(state, "esc")
    new_spec = updated.design_properties.components["esc"]
    changed = diff_refreshed_properties(old_spec, new_spec)
    assert changed == {"mass_g": (26.0, 15.0)}


def test_t2_no_catalog_ref_raises_no_write():
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={
            "esc": ComponentSpec(
                suggested_key="esc", component_type="power_control", completeness="medium",
                properties={"current_a": PropertyValue(value=30.0, unit="A", source="declared")},
            ),
        }),
    )
    with pytest.raises(ValueError):
        refresh_component_from_catalog(state, "esc")
    # untouched
    assert state.design_properties.components["esc"].properties["current_a"].value == 30.0


def test_t3_missing_key_raises():
    state = _stale_esc_state()
    with pytest.raises(ValueError):
        refresh_component_from_catalog(state, "battery")


# ── T4: pure parse ───────────────────────────────────────────────────────


@pytest.mark.parametrize("phrase,expected", [
    ("actualiza el esc desde catalogo", "esc"),
    ("refresca el esc", "esc"),
    ("actualiza motores", "motors"),
    ("refrescar bateria", "battery"),
    ("actualiza la frame", "frame"),
    ("actualiza las helices", "propellers"),
])
def test_t4_parse_set(phrase, expected):
    assert resolve_catalog_refresh_component(phrase) == expected


@pytest.mark.parametrize("phrase", [
    "hay que actualizar el proyecto",
    "cual es el estado del proyecto",
    "actualizar",
])
def test_t4_parse_none(phrase):
    assert resolve_catalog_refresh_component(phrase) is None


# ── T5: orchestrator IDLE ────────────────────────────────────────────────


def _orch_with_stale_esc(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "catalog refresh b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    stale = _stale_esc_state()
    updated_dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, **stale.design_properties.components}}
    )
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_t5_idle_refresh_persists_and_confirms(tmp_path: Path):
    orch = _orch_with_stale_esc(tmp_path)
    result = orch.handle_user_text("actualiza el esc desde catalogo", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Actualizado desde catálogo" in result["message"]
    assert "26" in result["message"] and "15" in result["message"]
    assert "Montaje declarado sin cambios" in result["message"]
    for forbidden in ("corregido automáticamente", "verificado", "cabe", "ensamblado"):
        assert forbidden not in result["message"].lower()

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = ps.design_properties.components["esc"]
    assert esc.properties["mass_g"].value == pytest.approx(15.0)
    assert esc.mounted_on == "frame_plate"


def test_t5b_idle_refresh_already_fresh_reports_no_change(tmp_path: Path):
    orch = _orch_with_stale_esc(tmp_path)
    orch.handle_user_text("actualiza el esc desde catalogo", _RefuseLLM())
    result = orch.handle_user_text("refresca el esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "ya coincidía con el catálogo" in result["message"].lower()


def test_t5c_idle_refresh_missing_component_honest_error(tmp_path: Path):
    orch = _orch_with_stale_esc(tmp_path)
    result = orch.handle_user_text("actualiza la bateria desde catalogo", _RefuseLLM())
    assert result["status"] == "error"
    assert "aún no declarado" in result["message"].lower() or "aun no declarado" in result["message"].lower()


# ── T6: non-regression ───────────────────────────────────────────────────


def test_t6_non_regression_idle_catalog_rebind_still_works(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "non regression",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    result = orch.handle_user_text("cambiar frame", _RefuseLLM())
    assert result["status"] in {"interactive", "ok"}


def test_t6b_non_regression_mounted_on_declare_still_works(tmp_path: Path):
    orch = _orch_with_stale_esc(tmp_path)
    result = orch.handle_user_text("quita el montaje del esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "eliminado" in result["message"]
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["esc"].mounted_on is None
