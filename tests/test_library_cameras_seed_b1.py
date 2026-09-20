"""First `library/cameras` seed B1 (`B1-library-cameras-seed`).

Covers implementation_contract_library_cameras_seed_b1.md §2:

  T1  list_cameras() length 1; get runcam_phoenix_2
  T2  bind_camera_from_catalog -> cameras + catalog_ref + 19³ + mass_g=9 + high
  T3  Free-text "cámara RunCam" -> medium, no seed mm/g, no catalog_ref
  T4  Assist/list exposes sku
  T5  Bind -> mission_payload_mass_kg ≈ 0.009 (P1)
  T6  Omit-key: base had extra catalog key new row omits -> dropped (synthetic)
  T7  Sensors/FC rebind+refresh regressions still green
  T8  Full pytest; 0.4.1 (checked at the repo level, sanity-pinned here)
  E1  Orchestrator: help-choose / list -> pick -> catalog_ref present + high + mass mirror
  E2  `cambiar cámara` -> rebind offer
  E3  Bound then `actualiza la cámara` -> refresh succeeds + mirror intact
  E4  Rebind `base=` preserves `mounted_on` / pose if set
  E5  Projector/box: bound cameras -> box 19³
  E6  Direct write of `mission_payload_mass_kg` still blocked (mirrored param)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from jarvis.core.camera_catalog_assist import build_camera_catalog_suggestions
from jarvis.core.catalog_bind import bind_camera_from_catalog
from jarvis.core.catalog_rebind_assist import resolve_idle_catalog_rebind
from jarvis.core.catalog_refresh_assist import resolve_catalog_refresh_component
from jarvis.core.component_inference import infer_component_for_key
from jarvis.core.component_writers import (
    refresh_component_from_catalog,
    set_control_component,
    set_mission_component_mass,
)
from jarvis.core.orchestrator import MISSING_COMPONENT_DEFINITION, JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.domains.aerial import aerial_registry
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_SKU = "runcam_phoenix_2"
_REPO_ROOT = Path(__file__).resolve().parent.parent


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _state(**components: ComponentSpec) -> ProjectState:
    return ProjectState(
        project_id="p", project_slug="p", objective="vigilancia",
        workspace_path="w", design_properties=DesignProperties(components=components),
    )


def _cameras_stub(*, mass_g: float | None = None) -> ComponentSpec:
    props = {"model": PropertyValue(value="runcam", confidence=0.8, source="declared")}
    if mass_g is not None:
        props["mass_g"] = PropertyValue(value=mass_g, unit="g", confidence=0.9, source="declared")
    return ComponentSpec(suggested_key="cameras", completeness="medium", properties=props)


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_list_and_get_camera():
    cameras = default_library.list_cameras()
    assert len(cameras) == 1
    assert cameras[0].name == _SKU
    spec = default_library.get_camera(_SKU)
    assert spec.manufacturer == "RunCam"
    assert spec.model == "Phoenix 2"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_bind_projects_box_mass_and_catalog_ref():
    bound = bind_camera_from_catalog(_SKU)
    assert bound.suggested_key == "cameras"
    assert bound.completeness == "high"
    assert bound.catalog_ref == CatalogRef(family="cameras", sku=_SKU)
    assert bound.properties["length_mm"].value == pytest.approx(19.0)
    assert bound.properties["width_mm"].value == pytest.approx(19.0)
    assert bound.properties["height_mm"].value == pytest.approx(19.0)
    assert bound.properties["mass_g"].value == pytest.approx(9.0)


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_free_text_runcam_stays_medium_no_seed_leak():
    spec = infer_component_for_key("cámara RunCam", "cameras", registry=aerial_registry)
    assert spec is not None
    assert spec.completeness == "medium"
    assert spec.catalog_ref is None
    assert "length_mm" not in spec.properties
    assert "width_mm" not in spec.properties
    assert "height_mm" not in spec.properties
    assert "mass_g" not in spec.properties


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_assist_list_exposes_sku():
    suggestions = build_camera_catalog_suggestions()
    assert any(s["name"] == _SKU for s in suggestions)


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_bind_then_mass_mirror_updates_mission_payload_mass_kg():
    bound = bind_camera_from_catalog(_SKU)
    state = _state(cameras=_cameras_stub())
    state = set_control_component(state, bound)
    mass_value = bound.properties["mass_g"].value
    updated = set_mission_component_mass(state, "cameras", mass_value)
    assert updated.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.009)


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_omit_key_hygiene_drops_stale_key_not_in_new_row(tmp_path: Path):
    """Synthetic two-row library: one row has mass_g, the other omits it —
    rebinding onto a base carrying the first SKU's mass_g must drop it,
    never leak a stale catalog value onto a new SKU that doesn't state it."""
    cameras_dir = tmp_path / "cameras"
    cameras_dir.mkdir()
    (cameras_dir / "_datos.json").write_text(
        '{"cam_with_mass": {"manufacturer": "A", "model": "1", '
        '"length_mm": 10.0, "width_mm": 10.0, "height_mm": 10.0, "mass_g": 5.0}, '
        '"cam_without_mass": {"manufacturer": "B", "model": "2", '
        '"length_mm": 12.0, "width_mm": 12.0, "height_mm": 12.0}}',
        encoding="utf-8",
    )
    lib = ComponentLibrary(library_root=tmp_path)

    with_mass = bind_camera_from_catalog("cam_with_mass", library=lib)
    assert with_mass.properties["mass_g"].value == pytest.approx(5.0)

    rebound = bind_camera_from_catalog("cam_without_mass", library=lib, base=with_mass)
    assert "mass_g" not in rebound.properties
    assert rebound.properties["length_mm"].value == pytest.approx(12.0)


# ── T7 (regression: sibling families unaffected) ───────────────────────────


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("cambiar controladora", "flight_controller"),
        ("cambiar gps", "sensors"),
        ("cambiar esc", "esc"),
        ("cambiar cámara", "cameras"),
        ("cambiar camara", "cameras"),
    ],
)
def test_t7_rebind_resolver_families_unaffected(phrase, expected):
    assert resolve_idle_catalog_rebind(phrase) == expected


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("actualiza el fc", "flight_controller"),
        ("actualiza el gps", "sensors"),
        ("actualiza la camara", "cameras"),
        ("actualiza la cámara", "cameras"),
    ],
)
def test_t7_refresh_resolver_families_unaffected(phrase, expected):
    assert resolve_catalog_refresh_component(phrase) == expected


# ── T8 ────────────────────────────────────────────────────────────────────


def test_t8_package_checkpoint_version():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match is not None
    assert match.group(1) == "0.4.2"


# ── E1 ────────────────────────────────────────────────────────────────────


def _idle_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "camera seed b1",
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


def _open_camera_wizard(orch: JarvisOrchestrator) -> None:
    session = orch.state_manager.get_runtime_session()
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["cameras"],
        "pending_define_missing": False,
        "camera_suggestions": [],
    })
    orch.state_manager.set_runtime_session(updated)


def test_e1_help_choose_pick_binds_with_catalog_ref_and_mass_mirror(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_camera_wizard(orch)
    offer = orch.handle_user_text("ayúdame a elegir cámara", _RefuseLLM())
    suggestions = offer.get("camera_suggestions") or []
    assert any(s["name"] == _SKU for s in suggestions)
    idx = next(s["idx"] for s in suggestions if s["name"] == _SKU)

    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"

    state = orch.state_manager.load_active_project(orch.workspace_manager)
    cameras = state.design_properties.components["cameras"]
    assert cameras.catalog_ref == CatalogRef(family="cameras", sku=_SKU)
    assert cameras.completeness == "high"
    assert cameras.properties["mass_g"].value == pytest.approx(9.0)
    assert state.current_parameters.get("mission_payload_mass_kg") == pytest.approx(0.009)


# ── E2 ────────────────────────────────────────────────────────────────────


def test_e2_cambiar_camara_reopens_catalog_offer(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    # First-time declare (freeform, no catalog_ref) so the rebind swap path
    # (not first-time acquisition) is exercised, mirroring the ESC visor test.
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    components = dict(project_state.design_properties.components)
    components["cameras"] = _cameras_stub()
    dp = project_state.design_properties.model_copy(update={"components": components})
    orch.workspace_manager.save_state(project_state.model_copy(update={"design_properties": dp}))

    result = orch.handle_user_text("cambiar cámara", _RefuseLLM())
    suggestions = result.get("camera_suggestions") or []
    assert any(s["name"] == _SKU for s in suggestions)
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["cameras"]
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


# ── E3 ────────────────────────────────────────────────────────────────────


def test_e3_actualiza_la_camara_refreshes_bound_component_and_keeps_mirror(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_camera_wizard(orch)
    offer = orch.handle_user_text("ayúdame a elegir cámara", _RefuseLLM())
    idx = next(s["idx"] for s in offer["camera_suggestions"] if s["name"] == _SKU)
    orch.handle_user_text(str(idx), _RefuseLLM())

    # Refresh only fires in IDLE (other architecture blocks may still be
    # pending after a singleton perception pick) — force IDLE the same way
    # the ESC visor rebind test's own `_reset_idle` does.
    session = orch.state_manager.get_runtime_session()
    idle = session.model_copy(update={
        "mode": OrchestratorMode.IDLE,
        "pending_missing_params": [],
        "pending_missing_reason": "",
        "pending_define_missing": False,
        "camera_suggestions": [],
    })
    orch.state_manager.set_runtime_session(idle)

    result = orch.handle_user_text("actualiza la cámara", _RefuseLLM())
    assert result["status"] == "ok"
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    cameras = state.design_properties.components["cameras"]
    assert cameras.catalog_ref == CatalogRef(family="cameras", sku=_SKU)
    assert cameras.properties["mass_g"].value == pytest.approx(9.0)
    assert state.current_parameters.get("mission_payload_mass_kg") == pytest.approx(0.009)


# ── E4 ────────────────────────────────────────────────────────────────────


def test_e4_rebind_base_preserves_mounted_on_and_pose():
    posed = _cameras_stub(mass_g=28.0).model_copy(update={
        "mounted_on": "frame_plate",
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0),
    })
    bound = bind_camera_from_catalog(_SKU, base=posed)
    assert bound.mounted_on == "frame_plate"
    assert bound.declared_box_pose == DeclaredBoxPose(
        origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0
    )
    # Mass mirror is the caller's job (component_writers.set_mission_component_mass),
    # never silently invented here — bind only projects the catalog property.
    assert bound.properties["mass_g"].value == pytest.approx(9.0)


# ── E5 ────────────────────────────────────────────────────────────────────


def test_e5_bound_camera_projects_19_cube_box():
    bound = bind_camera_from_catalog(_SKU)
    state = _state(cameras=bound)
    node = next(n for n in project_spatial_nodes(state) if n["id"] == "cameras")
    assert node["geometry"] == {
        "shape": "box",
        "length_mm": 19.0,
        "width_mm": 19.0,
        "height_mm": 19.0,
    }


# ── E6 ────────────────────────────────────────────────────────────────────


def test_e6_direct_mission_payload_mass_write_still_blocked(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    _open_camera_wizard(orch)
    offer = orch.handle_user_text("ayúdame a elegir cámara", _RefuseLLM())
    idx = next(s["idx"] for s in offer["camera_suggestions"] if s["name"] == _SKU)
    orch.handle_user_text(str(idx), _RefuseLLM())

    orch.param_definition_session.apply_and_recalculate({"mission_payload_mass_kg": 5.0})

    state = orch.state_manager.load_active_project(orch.workspace_manager)
    # Direct override is silently dropped (mirrored param, no bridge branch
    # for this key) — the mirror still reflects only the real bound mass.
    assert state.current_parameters.get("mission_payload_mass_kg") == pytest.approx(0.009)


# ── Refresh writer unit coverage (component_writers, no orchestrator) ─────


def test_same_sku_refresh_preserves_manually_declared_mass():
    """Code-review finding (2026-09-18): mission mass declare ("cámara 28
    g") carries the SAME confidence/source tag ("declared", 0.9) as a
    catalog projection — a same-SKU refresh silently reverting it to the
    catalog's own mass would be indistinguishable from real data loss.
    Catalog mass_g must only apply on a genuine first bind or a rebind to
    a DIFFERENT sku, never on a same-sku refresh/re-pick."""
    bound = bind_camera_from_catalog(_SKU)
    state = _state(cameras=_cameras_stub())
    state = set_control_component(state, bound)
    state = set_mission_component_mass(state, "cameras", 28.0)
    assert state.design_properties.components["cameras"].properties["mass_g"].value == pytest.approx(28.0)

    refreshed_state = refresh_component_from_catalog(state, "cameras")
    cameras = refreshed_state.design_properties.components["cameras"]
    assert cameras.properties["mass_g"].value == pytest.approx(28.0)
    assert refreshed_state.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.028)

    # Re-picking the SAME sku (not an actual SKU change) also preserves it.
    repicked = bind_camera_from_catalog(_SKU, base=cameras)
    assert repicked.properties["mass_g"].value == pytest.approx(28.0)


def test_different_sku_rebind_still_projects_new_catalog_mass(tmp_path: Path):
    """The preserve-on-refresh fix above must not swallow a genuine SKU
    change: rebinding to a DIFFERENT camera still projects that row's own
    mass_g, even when the base spec carries a manually-declared mass."""
    cameras_dir = tmp_path / "cameras"
    cameras_dir.mkdir()
    (cameras_dir / "_datos.json").write_text(
        '{"other_cam": {"manufacturer": "C", "model": "3", '
        '"length_mm": 15.0, "width_mm": 15.0, "height_mm": 15.0, "mass_g": 12.0}}',
        encoding="utf-8",
    )
    lib = ComponentLibrary(library_root=tmp_path)

    bound = bind_camera_from_catalog(_SKU)
    base = bound.model_copy(update={
        "properties": {
            **bound.properties,
            "mass_g": PropertyValue(value=28.0, unit="g", confidence=0.9, source="declared"),
        }
    })
    rebound = bind_camera_from_catalog("other_cam", library=lib, base=base)
    assert rebound.properties["mass_g"].value == pytest.approx(12.0)


def test_refresh_component_from_catalog_cameras_mirrors_mass_directly():
    bound = bind_camera_from_catalog(_SKU)
    state = _state(cameras=bound)
    state = state.model_copy(update={
        "current_parameters": {**state.current_parameters, "mission_payload_mass_kg": 0.009}
    })
    refreshed = refresh_component_from_catalog(state, "cameras")
    assert refreshed.current_parameters["mission_payload_mass_kg"] == pytest.approx(0.009)
    assert refreshed.design_properties.components["cameras"].catalog_ref == CatalogRef(
        family="cameras", sku=_SKU
    )
