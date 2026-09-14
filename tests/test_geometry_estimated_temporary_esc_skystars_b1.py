"""Estimated-temporary ESC height (Skystars KO50A II) B1
(`B1-estimated-temporary-esc-skystars`).

Covers implementation_contract_geometry_estimated_temporary_esc_skystars_b1.md §2:
  T1  get_esc("skystars_ko50a_ii_bls") -> L=41, W=46, mass=13.3,
      height_mm is None
  T2  Bind ESC -> L/W declared; no H yet -> geometry not a full box
  T3  Apply estimated H -> H source=estimated_temporary; L/W still
      declared; geometry box
  T4  cabe/screening with that ESC as child -> estimated_dims refuse
  T5  Fit attestation SET involving that ESC -> refuse / no write
  T6  Fit-relations checklist row -> estimated_dims (not attested)
  T7  Success copy includes ESTIMADA/TEMPORAL + replace-when-cited signal
  T8  Full pytest green; no height_mm key added to the catalog JSON for
      this SKU
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_esc_from_catalog
from jarvis.core.component_writers import (
    refresh_component_from_catalog,
    set_component_declared_fit_attestation,
    set_estimated_temporary_esc_height,
)
from jarvis.core.estimated_temporary_esc_assist import parse_estimated_temporary_esc_height_declare
from jarvis.core.fit_relations_assist import assess_fit_relations
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.pose_envelope_screening import format_screening, screen_posed_envelope
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import _geometry_from_spec, project_spatial_nodes

_SKU = "skystars_ko50a_ii_bls"


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "length_mm": PropertyValue(value=120.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=55.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=2.0, unit="mm", source="declared"),
        },
    )


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


# ── T1: catalog row L/W/mass cited, no height_mm ─────────────────────────


def test_t1_catalog_row_has_lw_mass_no_height():
    spec = default_library.get_esc(_SKU)
    assert spec.length_mm == pytest.approx(41.0)
    assert spec.width_mm == pytest.approx(46.0)
    assert spec.mass_g == pytest.approx(13.3)
    assert spec.height_mm is None


# ── T2: bound ESC has no full box yet (H missing) ────────────────────────


def test_t2_bound_esc_no_full_box_yet():
    esc_spec = bind_esc_from_catalog(_SKU)
    assert esc_spec.properties["length_mm"].source == "declared"
    assert esc_spec.properties["width_mm"].source == "declared"
    assert "height_mm" not in esc_spec.properties
    assert _geometry_from_spec(esc_spec) is None


# ── T3: estimated H applied -> hybrid box, L/W still declared ───────────


def test_t3_estimated_height_yields_hybrid_box():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)
    esc2 = updated.design_properties.components["esc"]

    assert esc2.properties["length_mm"].source == "declared"
    assert esc2.properties["width_mm"].source == "declared"
    assert esc2.properties["height_mm"].value == pytest.approx(9.5)
    assert esc2.properties["height_mm"].source == "estimated_temporary"
    assert esc2.properties["height_mm"].confidence == pytest.approx(0.3)
    # Other catalog-projected properties survive untouched.
    assert esc2.properties["mass_g"].value == pytest.approx(13.3)

    geometry = _geometry_from_spec(esc2)
    assert geometry == {"shape": "box", "length_mm": 41.0, "width_mm": 46.0, "height_mm": 9.5}


def test_t3_writer_requires_esc_key():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec})
    with pytest.raises(ValueError, match="solo 'esc'"):
        set_estimated_temporary_esc_height(state, "motors", 9.5)


def test_t3_writer_requires_prior_lw():
    boxless_esc = ComponentSpec(suggested_key="esc", completeness="low")
    state = _state({"esc": boxless_esc})
    with pytest.raises(ValueError, match="L×W citada"):
        set_estimated_temporary_esc_height(state, "esc", 9.5)


def test_t3_writer_rejects_non_positive_height():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec})
    with pytest.raises(ValueError):
        set_estimated_temporary_esc_height(state, "esc", 0.0)
    with pytest.raises(ValueError):
        set_estimated_temporary_esc_height(state, "esc", -1.0)


# ── T4: screening/cabe refuses (estimated_dims) ──────────────────────────


def test_t4_screening_refuses_estimated_dims():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec, "frame_plate": _plate_spec(), "frame": ComponentSpec(suggested_key="frame", completeness="high")})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)
    esc2 = updated.design_properties.components["esc"].model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.75),
    })
    components = {**updated.design_properties.components, "esc": esc2}

    screening = screen_posed_envelope(esc2, components)
    assert screening.status == "estimated_dims"
    message = format_screening(screening)
    assert "no verifica ensamblaje" in message.lower()
    assert "no se compara" in message.lower()


# ── T5: fit attestation refuses ──────────────────────────────────────────


def test_t5_fit_attestation_refuses_estimated_esc():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec, "frame_plate": _plate_spec()})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)
    esc2 = updated.design_properties.components["esc"].model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.75),
    })
    components = {**updated.design_properties.components, "esc": esc2}
    state2 = updated.model_copy(update={"design_properties": updated.design_properties.model_copy(update={"components": components})})

    with pytest.raises(ValueError, match="no se puede declarar verificado"):
        set_component_declared_fit_attestation(state2, "esc", attest=True)


# ── T6: fit-relations checklist row -> estimated_dims ────────────────────


def test_t6_fit_relations_row_is_estimated_dims():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec, "frame_plate": _plate_spec(), "frame": ComponentSpec(suggested_key="frame", completeness="high")})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)
    components = updated.design_properties.components

    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "esc")
    assert row.status == "estimated_dims"
    assert assessment.ready_count == 0
    assert assessment.attested_count == 0


# ── T7: disclosure copy ──────────────────────────────────────────────────


def test_t7_trigger_and_parse():
    result = parse_estimated_temporary_esc_height_declare("declara el esc estimado 9.5 mm")
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.height_mm == pytest.approx(9.5)


def test_t7_incomplete_without_number():
    result = parse_estimated_temporary_esc_height_declare("declara el esc estimado")
    assert result.kind == "INCOMPLETE"


def test_t7_none_for_other_subjects():
    assert parse_estimated_temporary_esc_height_declare(
        "declara la placa principal estimada 120 x 55 mm"
    ).kind == "NONE"
    assert parse_estimated_temporary_esc_height_declare(
        "declara la bateria estimada 80 x 34 x 22 mm"
    ).kind == "NONE"
    assert parse_estimated_temporary_esc_height_declare(
        "declara el esc 45 x 44 x 8 mm"
    ).kind == "NONE"


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "estimated esc skystars b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_components = {**ps.design_properties.components, **components}
    updated_dp = ps.design_properties.model_copy(update={"components": updated_components})
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_t7_idle_disclosure_copy_includes_estimada_temporal_and_replace_signal(tmp_path: Path):
    esc_spec = bind_esc_from_catalog(_SKU)
    orch = _orch_with_components(tmp_path, {"esc": esc_spec})
    result = orch.handle_user_text("declara el esc estimado 9.5 mm", _RefuseLLM())
    assert result["status"] == "ok"
    message = result["message"]
    assert "ESTIMADA TEMPORAL" in message
    assert "sustituir" in message.lower()
    assert "sí" in message.lower()
    assert "cabe" in message.lower()
    assert "declaro verificado" in message.lower()
    assert "41×46" in message


# ── T8: full suite green (checked at repo level); no catalog H seed ─────


def test_t8_catalog_json_still_omits_height_mm_for_skystars():
    import json

    repo_root = Path(__file__).resolve().parents[1]
    data = json.loads((repo_root / "library" / "esc" / "_datos.json").read_text(encoding="utf-8"))
    assert "height_mm" not in data[_SKU]


# ── Replace path (lock #11): catalog refresh preserves/replaces estimate ─


def test_replace_path_refresh_preserves_estimate_while_catalog_still_lacks_h():
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)
    refreshed = refresh_component_from_catalog(updated, "esc")
    height = refreshed.design_properties.components["esc"].properties["height_mm"]
    assert height.value == pytest.approx(9.5)
    assert height.source == "estimated_temporary"


def test_replace_path_refresh_overwrites_estimate_once_catalog_cites_h(monkeypatch):
    esc_spec = bind_esc_from_catalog(_SKU)
    state = _state({"esc": esc_spec})
    updated = set_estimated_temporary_esc_height(state, "esc", 9.5)

    default_library._load_escs()
    original = default_library._escs[_SKU]
    synthetic = original.__class__(**{**original.__dict__, "height_mm": 12.0})
    monkeypatch.setitem(default_library._escs, _SKU, synthetic)

    refreshed = refresh_component_from_catalog(updated, "esc")
    height = refreshed.design_properties.components["esc"].properties["height_mm"]
    assert height.value == pytest.approx(12.0)
    assert height.source == "declared"


# ── IDLE never mutates on list-alone / unrelated triggers ────────────────


def test_idle_unrelated_phrase_falls_through(tmp_path: Path):
    esc_spec = bind_esc_from_catalog(_SKU)
    orch = _orch_with_components(tmp_path, {"esc": esc_spec})
    before = orch.state_manager.load_active_project(orch.workspace_manager)
    result = orch.handle_user_text("relaciones", _RefuseLLM())
    assert result["status"] == "ok"
    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert before.design_properties.components == after.design_properties.components


def test_projector_regression_full_suite_local_geometry_unaffected():
    """Non-Skystars ESC (no L×W×H at all) is unaffected by this Buy."""
    bare_esc = ComponentSpec(suggested_key="esc", completeness="low")
    state = _state({"esc": bare_esc})
    nodes = project_spatial_nodes(state)
    node = next(n for n in nodes if n["id"] == "esc")
    assert "geometry" not in node
