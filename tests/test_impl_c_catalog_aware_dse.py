"""Impl C — Catalog-Aware DSE.

C1: DesignExplorer generates catalog-native motor candidates for
    aumentar_payload / mejorar_estabilidad (real SKUs, via
    motor_catalog_assist.build_motor_catalog_suggestions — the G22 single
    authority — never a new search).
C2: identity preservation through the EXISTING apply path (no production
    change expected there — investigation confirmed it already works).
C4: honest fallback note when the catalog search is empty.
C5: end-to-end integration + confirmation that untouched goals/paths regress
    to nothing (byte-identical behavior).

C3 (battery catalog) is explicitly deferred — not implemented, not tested here.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.design_explorer import (
    _CATALOG_MOTOR_FALLBACK_NOTE,
    ExplorationCandidate,
    ExplorationResult,
)
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


# brotherhobby_avenger_2500: thrust_n=9.5, max_thrust_n=11.5, kv 2300-2700,
# compatible_prop_inch=(5,) — real library fixture, used throughout G9-A/G21/G22.
_BOUND_SKU = "brotherhobby_avenger_2500"

_CREATE_PARAMS_BASE = {
    "vehicle_type": "dron",
    "objective": "dron de prueba Impl C",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": dict(_CREATE_PARAMS_BASE)})
    return orch


def _suggestion_for(sku: str) -> MotorSuggestion:
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


def _project_with_bound_motor(tmp_path: Path, *, motor_count: int = 6, prop_inch: float = 5.0):
    """Real orchestrator project, motors bound to _BOUND_SKU, propeller/prop
    within its design-space, so the catalog search has real matches.

    ``per_motor_max_thrust_n`` is set explicitly to the bound SKU's own
    thrust_n — ``apply_components_delta``/``set_motor_component`` never
    bridge that field from a component spec (only
    ``motor_power_w``/``motor_kv_rating``/``motor_count``/``motor_mass_kg``
    are bridged; ``per_motor_max_thrust_n`` is derived elsewhere, e.g. by
    ``IterateAction``/``apply_and_recalculate`` — confirmed by inspection,
    pre-existing, unrelated to Impl C). Without it, ``CalculationEngine``
    sees no thrust at all and the whole baseline is unflyable, independent
    of any DSE candidate.
    """
    orch = _fresh(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    bound_motor = default_library.get_motor(_BOUND_SKU)
    spec = bind_motor_from_catalog(_suggestion_for(_BOUND_SKU))
    ps = set_motor_component(ps, spec, bound_motor.max_watts)
    ps = ps.model_copy(update={
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": motor_count,
            "propeller_diameter_in": prop_inch,
            "per_motor_max_thrust_n": bound_motor.thrust_n,
        },
    })
    orch.workspace_manager.save_state(ps)
    return orch


def _project_with_empty_catalog_search(tmp_path: Path):
    """Real orchestrator project shaped like G22's own empty-search fixture:
    kv~2400 + prop=10.0" has zero real matches (2400KV motors only declare
    5-6" compatible props)."""
    orch = _fresh(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = ComponentSpec(
        name="motors", component_type="propulsion_active", suggested_key="motors",
        completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4), "kv_rating": PropertyValue(value=2400)},
    )
    dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, "motors": motors}}
    )
    ps = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {**ps.current_parameters, "motor_count": 4, "propeller_diameter_in": 10.0},
    })
    orch.workspace_manager.save_state(ps)
    return orch


def _make_calc(*, total_mass_kg: float = 3.5) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="dron", payload_kg=2.0, structure_mass_kg=1.5,
        total_mass_kg=total_mass_kg, weight_n=total_mass_kg * 9.81,
        required_thrust_n=total_mass_kg * 9.81 * 1.2, motors=6,
        thrust_per_motor_required_n=(total_mass_kg * 9.81 * 1.2) / 6,
        available_total_thrust_n=60.0, autonomy_min=30.0, tool_results=[],
    )


def _make_sim(*, safety_margin_ratio: float = 1.5) -> SimulationResult:
    return SimulationResult(
        can_fly=True, status="pass", safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=safety_margin_ratio, autonomy_min=30.0, quality="good",
        warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0, required_thrust_n=40.0, weight_n=34.3, per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )


def _project_ready_for_new_bind(tmp_path: Path, *, motor_count: int = 6):
    """Real orchestrator project with motor_count declared numerically only —
    no design_properties.components['motors'] entry, no catalog_ref, and
    deliberately NO pre-existing current_parameters['per_motor_max_thrust_n'].

    That last point matters: apply_components_delta/set_motor_component never
    bridge per_motor_max_thrust_n from a bound spec into current_parameters
    (confirmed by inspection — pre-existing, out of this IC's scope). If a
    *stale* per_motor_max_thrust_n were already present before the apply,
    catalog_bind.invalidate_diverged_catalog_refs would (correctly, per its
    own G5 contract) compare it against the new spec's thrust_n and clear
    catalog_ref as a false divergence — not a bug, but the wrong fixture for
    proving identity *preservation*. Leaving it unset means both sides of
    that comparison are None, so the guard never fires.
    """
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": {
        **_CREATE_PARAMS_BASE,
        "motors": motor_count,
    }})
    return orch


def _catalog_candidate(sku: str, *, base: ComponentSpec | None = None) -> ExplorationCandidate:
    spec = bind_motor_from_catalog(_suggestion_for(sku), base=base)
    return ExplorationCandidate(
        params_delta={}, components_delta={"motors": spec},
        calculations=_make_calc(), simulation=_make_sim(),
        score=2.0, label=f"motors [{sku}]", improvement=1.0,
    )


# ── C1: catalog candidate generation ─────────────────────────────────────────


def test_catalog_branch_generates_bound_motor_candidate_aumentar_payload(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    catalog_candidates = [
        c for c in result.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates, "expected >=1 real-SKU motor candidate"
    for c in catalog_candidates:
        assert c.components_delta["motors"].catalog_ref.family == "motor"
        assert c.components_delta["motors"].catalog_ref.sku


def test_catalog_branch_generates_bound_motor_candidate_mejorar_estabilidad(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "mejorar_estabilidad")

    catalog_candidates = [
        c for c in result.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates, "expected >=1 real-SKU motor candidate"


def test_bound_sku_excluded_from_catalog_candidates(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    for c in result.candidates:
        motors_spec = c.components_delta.get("motors")
        if motors_spec is not None and motors_spec.catalog_ref is not None:
            assert motors_spec.catalog_ref.sku != _BOUND_SKU


def test_strategy3_skips_synthetic_motor_on_aumentar_payload_when_library_matches(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    for c in result.candidates:
        motors_spec = c.components_delta.get("motors")
        if motors_spec is not None:
            # Every motors-touching candidate must be catalog-bound now —
            # the synthetic COMPONENT_VARIATION_RULES power_w-only entries
            # (catalog_ref=None) must not appear alongside real matches.
            assert motors_spec.catalog_ref is not None
    assert result.catalog_motor_note is None


def test_strategy3_keeps_synthetic_motor_when_library_empty(tmp_path: Path):
    orch = _project_with_empty_catalog_search(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    assert result.catalog_motor_note == _CATALOG_MOTOR_FALLBACK_NOTE
    synthetic = [
        c for c in result.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is None
    ]
    assert synthetic, "fallback must keep the synthetic motor component grid"


def test_params_grid_still_runs_with_catalog_branch(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    params_only = [c for c in result.candidates if c.params_delta and not c.components_delta]
    assert params_only, "params-only grid must keep contributing candidates"


def test_catalog_candidate_label_includes_sku(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "aumentar_payload")

    catalog_labels = [
        c.label for c in result.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_labels
    for label in catalog_labels:
        assert "[" in label and "]" in label


def test_reducir_payload_explore_unchanged(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "reducir_payload")

    assert result.catalog_motor_note is None
    for c in result.candidates:
        motors_spec = c.components_delta.get("motors")
        assert motors_spec is None or motors_spec.catalog_ref is None


def test_reducir_masa_explore_unchanged(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    result = orch.design_explorer.explore(ps, "reducir_masa")

    assert result.catalog_motor_note is None
    for c in result.candidates:
        motors_spec = c.components_delta.get("motors")
        assert motors_spec is None or motors_spec.catalog_ref is None


# ── C2: apply + identity + G9-A + G5 (mandatory) ────────────────────────────


def test_catalog_native_dse_apply_preserves_catalog_ref(tmp_path: Path):
    orch = _project_ready_for_new_bind(tmp_path)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[_catalog_candidate(_BOUND_SKU)],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )

    result = orch._handle_apply_exploration()

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == _BOUND_SKU


def test_catalog_native_dse_apply_g9a_scenario_b(tmp_path: Path):
    orch = _project_ready_for_new_bind(tmp_path)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[_catalog_candidate(_BOUND_SKU)],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )
    orch._handle_apply_exploration()
    saved = orch.state_manager.load_active_project(orch.workspace_manager)

    readiness = build_engineering_readiness(saved)

    catalog_gaps = [g for g in readiness.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert catalog_gaps == [], f"unexpected catalog gap after catalog-native DSE apply: {catalog_gaps}"


def test_catalog_native_dse_apply_survives_unrelated_iterate(tmp_path: Path):
    orch = _project_ready_for_new_bind(tmp_path)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[_catalog_candidate(_BOUND_SKU)],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )
    orch._handle_apply_exploration()

    before = orch.state_manager.load_active_project(orch.workspace_manager)
    before_motor_count = before.current_parameters.get("motor_count")
    before_sku = before.design_properties.components["motors"].catalog_ref.sku
    bound_thrust_n = before.design_properties.components["motors"].properties["thrust_n"].value
    # Impl C thrust-bridge follow-up: set_motor_component now bridges
    # thrust_n -> per_motor_max_thrust_n (★1), so a component-driven DSE
    # apply populates it immediately from the bound spec — previously this
    # asserted `is None` (the gap the follow-up IC closed;
    # implementation_review_impl_c_catalog_aware_dse.md Note A).
    assert before.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(bound_thrust_n)

    orch.handle_user_text("cambia safety_factor", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())
    orch.handle_user_text("safety_factor", _RefuseLLM())
    orch.handle_user_text("1.4", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())
    final = orch.handle_user_text("si", _RefuseLLM())
    assert final["status"] == "ok"

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.current_parameters.get("safety_factor") == pytest.approx(1.4)
    assert after.current_parameters.get("motor_count") == before_motor_count
    assert after.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(bound_thrust_n)
    assert after.design_properties.components["motors"].catalog_ref is not None
    assert after.design_properties.components["motors"].catalog_ref.sku == before_sku


# ── C4: fallback messaging ───────────────────────────────────────────────────


def test_explore_message_includes_catalog_fallback_note_when_search_empty(tmp_path: Path):
    orch = _project_with_empty_catalog_search(tmp_path)

    result = orch.handle_user_text("optimiza para aumentar payload", _RefuseLLM())

    assert _CATALOG_MOTOR_FALLBACK_NOTE in (result.get("message") or "")


def test_explore_message_no_fallback_note_when_catalog_matches(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)

    result = orch.handle_user_text("optimiza para aumentar payload", _RefuseLLM())

    assert _CATALOG_MOTOR_FALLBACK_NOTE not in (result.get("message") or "")


# ── C5: integration ──────────────────────────────────────────────────────────


def test_full_explore_apply_path_with_real_catalog_candidate(tmp_path: Path):
    """No manual ExplorationResult — real explore() output, a real catalog
    candidate picked from it, applied through the real orchestrator turn.

    Impl C thrust-bridge follow-up: uses a project with motor_count declared
    but no prior thrust (no bound/freeform motor at all) rather than
    _project_with_bound_motor — with nothing declared yet, every
    params-grid entry that needs per_motor_max_thrust_n is omitted by
    _apply_delta's own missing-param guard, so real catalog candidates
    (whose thrust now comes from their own bound spec via the bridge) land
    in .viable on genuine, unmodified physics — no forcing needed. Before
    the bridge this test only reached a skip (no candidate was viable at
    all, catalog or otherwise, without any declared thrust)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": {**_CREATE_PARAMS_BASE, "motors": 6}})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    exploration = orch.design_explorer.explore(ps, "aumentar_payload")
    catalog_candidates = [
        c for c in exploration.viable
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates, "expected a real-SKU candidate to be naturally viable with no prior thrust declared"

    picked_sku = catalog_candidates[0].components_delta["motors"].catalog_ref.sku
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )

    # Force the picked catalog candidate to the front so "aplica la mejor"
    # applies it deterministically, without depending on how it ranked.
    exploration2 = exploration.model_copy(update={"viable": [catalog_candidates[0]]})
    orch.state_manager.set_runtime_session(
        orch.state_manager.get_runtime_session().model_copy(
            update={"last_exploration_result": exploration2}
        )
    )

    result = orch.handle_user_text("aplica la mejor", _RefuseLLM())
    assert result["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.design_properties.components["motors"].catalog_ref.sku == picked_sku
