"""G21 + G22 Catalog Bind UX — pre-Impl C.

G21 (Slice 1): motors component-wizard + IDLE catalog bind entry points.
G22 (Slice 2): single strict catalog authority (KV-only fallback removed).
Slice 3: integration — bound-via-new-path Scenario B through G9-A's own gap check.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.motor_catalog_assist import build_motor_catalog_suggestions
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library


class _FakeLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")

    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba G21/G22",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh(tmp_path):
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return o


def _open_component_wizard(o, pending_keys):
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": pending_keys,
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)


# ── Slice 1 (G21): component wizard catalog bind ────────────────────────────


def test_g21_component_wizard_help_choose_shows_numbered_catalog(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert result.get("status") == "interactive"
    assert "Candidatos del catálogo" in result.get("message", "")
    suggestions = result.get("motor_suggestions") or []
    assert len(suggestions) > 0
    session = o.state_manager.runtime_state.session
    assert session.motor_suggestions == suggestions
    # Regression guard: not a bare Brief re-show (no numbered list).
    assert "Puedes:" not in result.get("message", "")


def test_g21_component_wizard_pick_sets_catalog_ref(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors", "propellers"])
    listed = o.handle_user_text("ayúdame a elegir", _FakeLLM())
    suggestions = listed["motor_suggestions"]
    first_name = suggestions[0]["name"]

    result = o.handle_user_text("1", _FakeLLM())

    assert result.get("status") == "ok"
    assert result.get("action") == "component_description_saved"
    project = o.state_manager.load_active_project(o.workspace_manager)
    motors = project.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.family == "motor"
    assert motors.catalog_ref.sku == first_name
    # Wizard continues — propellers still pending, not silently cleared.
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert "propellers" in (session.pending_missing_params or [])
    assert session.motor_suggestions == []


def _project_with_unbound_freeform_motor(tmp_path: Path, *, catalog_ref=None):
    """Motor already declared (power AND thrust already answered — e.g. via a
    manual N value, not a catalog pick) so propulsion params are no longer
    'missing' — the exact state where the pre-existing early branch in
    ``_try_start_assisted_motor_help`` (propulsion-missing → numeric wizard)
    does NOT fire, and the bare ``motor_power_w is not None: return None``
    dead-end (G21 addendum) was the only remaining code path."""
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

    o = _fresh(tmp_path)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    motors = ComponentSpec(
        name="motors", component_type="propulsion_active", suggested_key="motors",
        completeness="high", source="declared",
        properties={
            "motor_count": PropertyValue(value=4),
            "kv_rating": PropertyValue(value=2400),
            "power_w": PropertyValue(value=50.0),
        },
        catalog_ref=catalog_ref,
    )
    dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, "motors": motors}}
    )
    ps2 = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": 4,
            "motor_power_w": 50.0,
            "per_motor_max_thrust_n": 6.9,
        },
        "latest_results": {
            "calculations": {"required_thrust_n": 27.6, "total_mass_kg": 1.5},
            "simulation": {"physics_status": "valid", "status": "pass", "warnings": []},
        },
    })
    o.workspace_manager.save_state(ps2)
    return o


def test_g21_idle_help_choose_when_power_set_unbound_motor(tmp_path: Path):
    o = _project_with_unbound_freeform_motor(tmp_path)

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert result.get("action") != "project_status"
    assert (
        "Candidatos del catálogo" in result.get("message", "")
        or "No tengo un motor" in result.get("message", "")
    )
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_missing_params == ["motors"]


def test_g21_idle_help_choose_noop_when_catalog_ref_set(tmp_path: Path):
    """Regression guard: a catalog-bound motor must never reopen the MOTOR
    picker (the original G21 dead-end bug this test was written for).

    Prop-3/Prop-5 (★6 B, post P2-1): this fixture's project has no
    ``propellers`` component at all (a genuine stub), and motors is already
    catalog-bound — so the IDLE help-choose fallback now legitimately opens
    the PROPELLER picker instead of falling through to nothing. That is the
    intended P2-1-unlock behavior (investigation_report_propeller_catalog_
    bind_ux.md §5/§7), not a regression. What this test must still guard
    against is a false MOTOR re-bind — asserted directly below.
    """
    from jarvis.schemas.action_schema import CatalogRef

    o = _project_with_unbound_freeform_motor(
        tmp_path, catalog_ref=CatalogRef(family="motor", sku="brotherhobby_avenger_2500")
    )

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    session = o.state_manager.runtime_state.session
    # The actual G21 regression this test guards: never a false motor re-bind.
    assert not (
        session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
        and session.pending_missing_params == ["motors"]
    )
    # If a picker opened at all, it must be the legitimate propeller one —
    # never a stray/misrouted motor prompt.
    if result.get("action") == "component_description_prompt":
        assert session.pending_missing_params == ["propellers"]


# ── Slice 2 (G22): single strict catalog authority ──────────────────────────


def test_g22_strict_empty_when_prop_excludes_kv_matches():
    """thrust~6.9N/motor, kv~2400, prop=10.0" — real ~2400KV motors only
    declare compatible_prop_inch 5-6", so the strict search is empty. Before
    G22, build_motor_catalog_suggestions softened this via find_motors_by_kv;
    it must not anymore."""
    strict = default_library.find_motors_for_requirements(
        min_thrust_n=6.9, kv=2400, prop_inch=10.0
    )
    assert strict == []
    kv_only = default_library.find_motors_by_kv(2400)
    assert kv_only != []  # sanity: the old fallback source is non-empty

    from types import SimpleNamespace

    project_state = SimpleNamespace(
        current_parameters={"propeller_diameter_in": 10.0},
        design_properties=SimpleNamespace(components={
            "motors": SimpleNamespace(
                properties={"kv_rating": SimpleNamespace(value=2400)}
            ),
        }),
        parsed_constraints={},
        latest_results={
            "calculations": {"required_thrust_n": 27.6},
            "simulation": {},
        },
    )
    project_state.current_parameters["motor_count"] = 4  # 27.6/4 = 6.9 N/motor

    suggestions = build_motor_catalog_suggestions(project_state)
    assert suggestions == []


def test_g22_list_motors_and_gap_agree_on_strict_empty():
    """resolve_motor_catalog_surface (gap) and build_motor_catalog_suggestions
    (list_motors/FN-005) must agree — both empty — on the same project state,
    same design-space filters."""
    from types import SimpleNamespace

    from jarvis.core.engineering_readiness import resolve_motor_catalog_surface
    from jarvis.core.project_closure import derive_physical_requirements

    project_state = SimpleNamespace(
        current_parameters={"propeller_diameter_in": 10.0, "motor_count": 4},
        design_properties=SimpleNamespace(components={
            "motors": SimpleNamespace(
                properties={"kv_rating": SimpleNamespace(value=2400)},
                catalog_ref=None,
            ),
        }),
        parsed_constraints={},
        latest_results={
            "calculations": {"required_thrust_n": 27.6},
            "simulation": {},
        },
    )

    req = derive_physical_requirements(project_state)
    catalog_gap, catalog_matches, _fact = resolve_motor_catalog_surface(project_state, req)
    list_suggestions = build_motor_catalog_suggestions(project_state)

    assert catalog_gap is not None
    assert catalog_matches == []
    assert list_suggestions == []


# ── Slice 3: integration — bound-via-new-path clears the G9-A gap ───────────


def test_g21_bound_motor_catalog_gap_cleared(tmp_path: Path):
    """Bind through the NEW component-wizard pick path (not the pre-existing
    numeric energy wizard G9-A's own tests used) — G9-A's Scenario B must
    still hold: no GAP-MOTOR-CATALOG-UNRESOLVED once bound-and-sufficient."""
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])
    listed = o.handle_user_text("ayúdame a elegir", _FakeLLM())
    suggestions = listed["motor_suggestions"]
    picked = suggestions[0]

    o.handle_user_text("1", _FakeLLM())

    project = o.state_manager.load_active_project(o.workspace_manager)
    # No propeller/thrust filters set on this fresh project — the bound
    # motor's own design-space trivially "covers" (no requirement to miss).
    result = build_engineering_readiness(project)
    catalog_gaps = [g for g in result.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert catalog_gaps == []
    assert project.design_properties.components["motors"].catalog_ref.sku == picked["name"]
