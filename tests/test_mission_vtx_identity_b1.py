"""VTX identity + first catalog seed B1 (`B1-mission-vtx-identity`).

Covers implementation_contract_mission_vtx_identity_b1.md §2:

  T1  list_vtx length 1; get hglrc_zeus_800
  T2  Bind -> vtx + catalog_ref + 37x37x5 + mass_g=4.8 + high
  T3  Free-text "vtx HGLRC" -> medium, no seed mm/g, no catalog_ref
  T4  Orchestrator pick -> catalog_ref + mass mirror (mission_payload_mass_kg
      includes 0.0048)
  T5  "cambiar vtx" / "actualiza el vtx"
  T6  Preserve manual mass on same-SKU refresh
  T7  No power_w on bind from RF levels
  T8  Continuity CTA when cameras & no vtx; clears when vtx present
  T9  radio_module / cameras paths unstolen
  T10 BOM [hglrc_zeus_800] via has_vtx
  T11 video_link resolvable; perception still cameras-only
  T12 Full suite; 0.4.1
"""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.core.catalog_bind import bind_vtx_from_catalog
from jarvis.core.catalog_rebind_assist import resolve_idle_catalog_rebind
from jarvis.core.catalog_refresh_assist import resolve_catalog_refresh_component
from jarvis.core.component_inference import infer_component, infer_component_for_key
from jarvis.core.component_writers import (
    refresh_component_from_catalog,
    set_control_component,
    set_mission_component_mass,
)
from jarvis.core.orchestrator import MISSING_COMPONENT_DEFINITION, JarvisOrchestrator
from jarvis.core.project_closure import _bom_sku_resolved, build_component_bom
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.core.state_manager import OrchestratorMode
from jarvis.core.system_architecture_catalog import (
    BLOCK_TO_COMPONENTS,
    block_components_are_resolvable,
)
from jarvis.core.vtx_catalog_assist import build_vtx_catalog_suggestions
from jarvis.domains.aerial import aerial_registry
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKU = "hglrc_zeus_800"


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _state(**components) -> ProjectState:
    return ProjectState(
        project_id="p", project_slug="p", objective="vigilancia",
        workspace_path="w", design_properties=DesignProperties(components=components),
    )


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_list_and_get_vtx():
    vtx_rows = default_library.list_vtx()
    assert len(vtx_rows) == 1
    assert vtx_rows[0].name == _SKU
    spec = default_library.get_vtx(_SKU)
    assert spec.manufacturer == "HGLRC"
    assert spec.model == "Zeus 800"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_bind_projects_box_mass_and_catalog_ref():
    bound = bind_vtx_from_catalog(_SKU)
    assert bound.suggested_key == "vtx"
    assert bound.completeness == "high"
    assert bound.catalog_ref == CatalogRef(family="vtx", sku=_SKU)
    assert bound.properties["length_mm"].value == pytest.approx(37.0)
    assert bound.properties["width_mm"].value == pytest.approx(37.0)
    assert bound.properties["height_mm"].value == pytest.approx(5.0)
    assert bound.properties["mass_g"].value == pytest.approx(4.8)


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_free_text_hglrc_stays_medium_no_seed_leak():
    spec = infer_component_for_key("vtx HGLRC", "vtx", registry=aerial_registry)
    assert spec is not None
    assert spec.completeness == "medium"
    assert spec.catalog_ref is None
    assert "length_mm" not in spec.properties
    assert "width_mm" not in spec.properties
    assert "height_mm" not in spec.properties
    assert "mass_g" not in spec.properties


def test_t3_bare_vtx_stays_low():
    spec = infer_component("vtx")
    assert spec is not None
    assert spec.suggested_key == "vtx"
    assert spec.completeness == "low"


# ── T4 ────────────────────────────────────────────────────────────────────


def _idle_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "vtx identity b1",
            "payload_kg": 0.3,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.3,
            "safety_factor": 1.1,
            "motors": 4,
            "per_motor_max_thrust_n": 5.0,
        },
    })
    return orch


def _open_vtx_wizard(orch: JarvisOrchestrator) -> None:
    session = orch.state_manager.get_runtime_session()
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["vtx"],
        "pending_define_missing": False,
        "vtx_suggestions": [],
    })
    orch.state_manager.set_runtime_session(updated)


def test_t4_orchestrator_pick_binds_with_catalog_ref_and_mass_mirror(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_vtx_wizard(orch)
    offer = orch.handle_user_text("ayúdame a elegir vtx", _RefuseLLM())
    suggestions = offer.get("vtx_suggestions") or []
    assert any(s["name"] == _SKU for s in suggestions)
    idx = next(s["idx"] for s in suggestions if s["name"] == _SKU)

    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"

    state = orch.state_manager.load_active_project(orch.workspace_manager)
    vtx = state.design_properties.components["vtx"]
    assert vtx.catalog_ref == CatalogRef(family="vtx", sku=_SKU)
    assert vtx.completeness == "high"
    assert vtx.properties["mass_g"].value == pytest.approx(4.8)
    assert state.current_parameters.get("mission_payload_mass_kg") == pytest.approx(0.0048)


def test_idle_ayudame_elegir_vtx_opens_catalog_when_vtx_absent(tmp_path: Path):
    """Smoke 2026-09-18 regression: first-time IDLE 'ayúdame a elegir vtx'
    must open the Zeus list even when no vtx component exists yet (rebind
    path used to require an existing non-stub component and fell through
    to motor triage / estado)."""
    orch = _idle_orchestrator(tmp_path)
    # Architecture complete (no pending block) + cameras present, vtx absent
    # — mirrors vigilancia-shaped IDLE.
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    components = dict(state.design_properties.components)
    components["cameras"] = ComponentSpec(
        name="runcam_phoenix_2",
        suggested_key="cameras",
        completeness="high",
        properties={},
    )
    blocks = list(getattr(state.design_properties, "system_blocks", None) or [])
    for b in ("propulsion", "energy", "structure", "perception"):
        if b not in blocks:
            blocks.append(b)
    dp = state.design_properties.model_copy(
        update={"components": components, "system_blocks": blocks, "system_defined": True}
    )
    orch.workspace_manager.save_state(state.model_copy(update={"design_properties": dp}))

    offer = orch.handle_user_text("ayúdame a elegir vtx", _RefuseLLM())
    suggestions = offer.get("vtx_suggestions") or []
    assert any(s["name"] == _SKU for s in suggestions), offer
    assert "Zeus" in (offer.get("message") or "") or "37" in (offer.get("message") or "")


# ── T5 ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("cambiar vtx", "vtx"),
        ("cambiar el vtx", "vtx"),
        ("ayúdame a elegir vtx", "vtx"),
        ("cambiar esc", "esc"),
        ("ayúdame a elegir", None),
    ],
)
def test_t5_rebind_resolver_vtx_family(phrase, expected):
    assert resolve_idle_catalog_rebind(phrase) == expected


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("actualiza el vtx", "vtx"),
        ("actualiza la cámara", "cameras"),
    ],
)
def test_t5_refresh_resolver_vtx_family(phrase, expected):
    assert resolve_catalog_refresh_component(phrase) == expected


def test_t5_cambiar_vtx_reopens_catalog_offer(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    components = dict(project_state.design_properties.components)
    components["vtx"] = ComponentSpec(
        suggested_key="vtx", completeness="medium",
        properties={"model": PropertyValue(value="hglrc", confidence=0.8, source="declared")},
    )
    dp = project_state.design_properties.model_copy(update={"components": components})
    orch.workspace_manager.save_state(project_state.model_copy(update={"design_properties": dp}))

    result = orch.handle_user_text("cambiar vtx", _RefuseLLM())
    suggestions = result.get("vtx_suggestions") or []
    assert any(s["name"] == _SKU for s in suggestions)
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["vtx"]
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_t5_actualiza_el_vtx_refreshes_bound_component(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_vtx_wizard(orch)
    offer = orch.handle_user_text("ayúdame a elegir vtx", _RefuseLLM())
    idx = next(s["idx"] for s in offer["vtx_suggestions"] if s["name"] == _SKU)
    orch.handle_user_text(str(idx), _RefuseLLM())

    session = orch.state_manager.get_runtime_session()
    idle = session.model_copy(update={
        "mode": OrchestratorMode.IDLE,
        "pending_missing_params": [],
        "pending_missing_reason": "",
        "pending_define_missing": False,
        "vtx_suggestions": [],
    })
    orch.state_manager.set_runtime_session(idle)

    result = orch.handle_user_text("actualiza el vtx", _RefuseLLM())
    assert result["status"] == "ok"
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    vtx = state.design_properties.components["vtx"]
    assert vtx.catalog_ref == CatalogRef(family="vtx", sku=_SKU)
    assert state.current_parameters.get("mission_payload_mass_kg") == pytest.approx(0.0048)


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_same_sku_refresh_preserves_manually_declared_mass():
    bound = bind_vtx_from_catalog(_SKU)
    state = _state(vtx=bound)
    state = set_mission_component_mass(state, "vtx", 6.0)
    assert state.design_properties.components["vtx"].properties["mass_g"].value == pytest.approx(6.0)

    refreshed_state = refresh_component_from_catalog(state, "vtx")
    vtx = refreshed_state.design_properties.components["vtx"]
    assert vtx.properties["mass_g"].value == pytest.approx(6.0)
    assert refreshed_state.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.006)

    repicked = bind_vtx_from_catalog(_SKU, base=vtx)
    assert repicked.properties["mass_g"].value == pytest.approx(6.0)


def test_t6_rebind_preserves_pose_and_manual_mass_together():
    posed = bind_vtx_from_catalog(_SKU).model_copy(update={
        "properties": {
            "mass_g": PropertyValue(value=6.0, unit="g", confidence=0.9, source="declared"),
        },
        "mounted_on": "frame_plate",
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0),
    })
    refreshed = bind_vtx_from_catalog(_SKU, base=posed)
    assert refreshed.properties["mass_g"].value == pytest.approx(6.0)
    assert refreshed.mounted_on == "frame_plate"
    assert refreshed.declared_box_pose == DeclaredBoxPose(
        origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0
    )


def test_t6_omit_key_hygiene_drops_stale_key_not_in_new_row(tmp_path: Path):
    vtx_dir = tmp_path / "vtx"
    vtx_dir.mkdir()
    (vtx_dir / "_datos.json").write_text(
        '{"vtx_with_mass": {"manufacturer": "A", "model": "1", '
        '"length_mm": 10.0, "width_mm": 10.0, "height_mm": 10.0, "mass_g": 5.0}, '
        '"vtx_without_mass": {"manufacturer": "B", "model": "2", '
        '"length_mm": 12.0, "width_mm": 12.0, "height_mm": 12.0}}',
        encoding="utf-8",
    )
    lib = ComponentLibrary(library_root=tmp_path)

    with_mass = bind_vtx_from_catalog("vtx_with_mass", library=lib)
    assert with_mass.properties["mass_g"].value == pytest.approx(5.0)

    rebound = bind_vtx_from_catalog("vtx_without_mass", library=lib, base=with_mass)
    assert "mass_g" not in rebound.properties
    assert rebound.properties["length_mm"].value == pytest.approx(12.0)


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_no_power_w_projected_from_rf_levels():
    bound = bind_vtx_from_catalog(_SKU)
    assert "power_w" not in bound.properties
    # The library dataclass itself carries no power_w field for VTX at all
    # (unlike CameraSpec) — never invented from the RF mW citation text.
    assert not hasattr(default_library.get_vtx(_SKU), "power_w")


def test_t7_mission_component_power_refuses_vtx_key():
    from jarvis.core.component_writers import set_mission_component_power

    bound = bind_vtx_from_catalog(_SKU)
    state = _state(vtx=bound)
    with pytest.raises(ValueError):
        set_mission_component_power(state, "vtx", 1.0)


# ── T8 ────────────────────────────────────────────────────────────────────


def _reasoning_context(margin=3.6196, parsed_constraints=None):
    return {
        "objective": "dron de vigilancia",
        "current_parameters": {"restrictions": "no", "payload_kg": 0.0, "mission_payload_mass_kg": 0.012},
        "design_properties": {"components": {}, "structure": {}},
        "last_calculation": None, "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {}, "last_mutation": None, "mutation_mode": None,
        "parsed_constraints": parsed_constraints or {"autonomy_min": 8.0},
    }


def _fully_closed_camera_radio_components(*, with_vtx: bool) -> dict:
    components = {
        "cameras": {
            "completeness": "high",
            "properties": {
                "model": {"value": "runcam"}, "mass_g": {"value": 9.0}, "power_w": {"value": 1.0},
            },
        },
        "radio_module": {
            "completeness": "medium",
            "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}, "power_w": {"value": 0.5}},
        },
    }
    if with_vtx:
        components["vtx"] = {
            "completeness": "high",
            "properties": {"model": {"value": "hglrc"}, "mass_g": {"value": 4.8}},
        }
    return components


def test_t8_cta_when_cameras_present_and_no_vtx():
    context = _reasoning_context()
    context["design_properties"]["components"] = _fully_closed_camera_radio_components(with_vtx=False)
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara VTX (enlace de vídeo)"
    assert out.suggested_actions[0].action_type == "declare_mission_vtx"


def test_t8_cta_clears_when_vtx_present():
    context = _reasoning_context()
    context["design_properties"]["components"] = _fully_closed_camera_radio_components(with_vtx=True)
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].action_type != "declare_mission_vtx"
    assert out.suggested_actions[0].label == "Revisar margen vs carga de misión"


# ── T9 ────────────────────────────────────────────────────────────────────


def test_t9_radio_free_text_unaffected_by_vtx():
    spec = infer_component_for_key("radio ELRS", "radio_module", registry=aerial_registry)
    assert spec is not None
    assert spec.suggested_key == "radio_module"
    assert spec.completeness == "medium"


def test_t9_camera_free_text_unaffected_by_vtx():
    spec = infer_component_for_key("cámara RunCam", "cameras", registry=aerial_registry)
    assert spec is not None
    assert spec.suggested_key == "cameras"
    assert spec.completeness == "medium"


def test_t9_bare_fpv_still_resolves_camera_not_vtx():
    """VTX_KEYWORDS deliberately excludes bare 'fpv' (already claimed by
    CAMERA_KEYWORDS) — only the qualified 'fpv vtx' phrase is VTX's own."""
    spec = infer_component("cámara fpv")
    assert spec is not None
    assert spec.suggested_key == "cameras"


def test_t9_bare_vtx_word_resolves_vtx_not_cameras():
    """"vtx" itself has no overlap with CAMERA_KEYWORDS, so it reaches the
    VTX rule cleanly — unlike any "fpv"-containing phrase (see the test
    above): ComponentRuleRegistry is first-match-wins by registration
    order, and cameras (registered first) already claims bare "fpv" for
    itself, so no "fpv"-containing alias could ever reach the VTX rule."""
    spec = infer_component("vtx")
    assert spec is not None
    assert spec.suggested_key == "vtx"


def test_t9_composite_wizard_does_not_apply_vtx_pick(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_vtx_wizard(orch)
    leftover = orch.handle_user_text("ayúdame a elegir vtx", _RefuseLLM()).get("vtx_suggestions") or []
    assert leftover
    session = orch.state_manager.get_runtime_session()
    composite = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_params": ["cameras", "vtx"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "param_definition_reason": MISSING_COMPONENT_DEFINITION,
        "vtx_suggestions": leftover,
        "camera_suggestions": [],
    })
    orch.state_manager.set_runtime_session(composite)
    orch.handle_user_text("1", _RefuseLLM())
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    # "cameras" is expected_keys[0], not "vtx" — the vtx gate is head-key
    # only, so it must never apply here even with a pending vtx_suggestions
    # list; "1" targets cameras' own routing (or falls through unmatched).
    vtx_spec = state.design_properties.components.get("vtx")
    assert vtx_spec is None or vtx_spec.catalog_ref is None


# ── T10 ───────────────────────────────────────────────────────────────────


def test_t10_bom_shows_bracket_sku_via_has_vtx():
    assert _bom_sku_resolved({"family": "vtx", "sku": _SKU}) is True
    assert _bom_sku_resolved({"family": "vtx", "sku": "phantom_vtx_9000"}) is False

    bound = bind_vtx_from_catalog(_SKU)
    project_state = SimpleNamespace(
        parsed_constraints={}, latest_results={}, current_parameters={},
        design_properties=SimpleNamespace(
            components={"vtx": bound}, system_blocks=["video_link"],
            system_defined=True, system_priority=["video_link"],
        ),
    )
    bom = build_component_bom(project_state)
    entry = next(
        e for e in bom["defined"] + bom["declarative"] + bom["incomplete"]
        if e["key"] == "vtx"
    )
    assert entry["sku_resolved"] is True
    assert entry["catalog_ref"]["sku"] == _SKU


# ── T11 ───────────────────────────────────────────────────────────────────


def test_t11_video_link_block_resolvable():
    assert block_components_are_resolvable("video_link")
    assert BLOCK_TO_COMPONENTS["video_link"] == ["vtx"]


def test_t11_perception_block_still_cameras_only():
    assert BLOCK_TO_COMPONENTS["perception"] == ["cameras"]


# ── T12 ───────────────────────────────────────────────────────────────────


def test_t12_package_checkpoint_version():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match is not None
    assert match.group(1) == "0.4.3"


# ── Extra: assist list exposes the seed sku ────────────────────────────────


def test_assist_list_exposes_sku():
    suggestions = build_vtx_catalog_suggestions()
    assert any(s["name"] == _SKU for s in suggestions)
