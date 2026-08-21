"""Impl C follow-up — Catalog DSE Thrust Bridge.

Closes the residual traced in
.jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md §4 and
confirmed independently in
.jes/artifacts/implementation_review_impl_c_catalog_aware_dse.md Note A:
``set_motor_component`` never bridged ``ComponentSpec.motors.properties
.thrust_n`` into ``current_parameters["per_motor_max_thrust_n"]``, so
catalog-DSE candidate evaluation used stale/missing thrust, and a real
SKU-switch apply had its ``catalog_ref`` cleared by G5's own (correct,
untouched) divergence check comparing the new spec's thrust against the old,
never-updated params value.

The bridge itself lives in ``component_writers.set_motor_component`` — this
file proves it closes the gap for: direct bridging, DSE evaluation, a real
SKU-switch apply (identity + new thrust), survival across an unrelated
iterate turn, viable-membership with correct thrust (no scoring change), and
the two named regressions (first-bind C2, params-only divergence still
clears as before).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog, invalidate_diverged_catalog_refs
from jarvis.core.component_writers import apply_components_delta, set_motor_component
from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


# Real library fixtures — same as test_impl_c_catalog_aware_dse.py.
_SKU_A = "brotherhobby_avenger_2500"  # thrust_n=9.5, kv 2300-2700, prop (5,)
_SKU_B = "sunnysky_r2305_2500"        # thrust_n=7.5, kv 2300-2700, prop (5,)

_CREATE_PARAMS_BASE = {
    "vehicle_type": "dron",
    "objective": "dron de prueba Impl C thrust bridge",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _suggestion_for(sku: str) -> MotorSuggestion:
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


def _fresh(tmp_path: Path, *, motor_count: int | None = None) -> JarvisOrchestrator:
    params = dict(_CREATE_PARAMS_BASE)
    if motor_count is not None:
        params["motors"] = motor_count
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": params})
    return orch


def _project_bound_to(tmp_path: Path, sku: str, *, motor_count: int = 6, prop_inch: float = 5.0):
    """Real orchestrator project with motors bound to *sku* — no explicit
    per_motor_max_thrust_n set at creation; the bridge (this IC) is what
    makes it appear, derived from the bound spec itself."""
    orch = _fresh(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = bind_motor_from_catalog(_suggestion_for(sku))
    ps = set_motor_component(ps, spec, default_library.get_motor(sku).max_watts)
    ps = ps.model_copy(update={
        "current_parameters": {
            **ps.current_parameters, "motor_count": motor_count, "propeller_diameter_in": prop_inch,
        },
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


def _catalog_candidate(sku: str, *, base=None) -> ExplorationCandidate:
    spec = bind_motor_from_catalog(_suggestion_for(sku), base=base)
    return ExplorationCandidate(
        params_delta={}, components_delta={"motors": spec},
        calculations=_make_calc(), simulation=_make_sim(),
        score=2.0, label=f"motors [{sku}]", improvement=1.0,
    )


# ── Bridge itself ─────────────────────────────────────────────────────────


def test_component_driven_catalog_thrust_bridges_to_params(tmp_path: Path):
    orch = _fresh(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = bind_motor_from_catalog(_suggestion_for(_SKU_A))

    updated = set_motor_component(ps, spec, default_library.get_motor(_SKU_A).max_watts)

    assert updated.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        default_library.get_motor(_SKU_A).thrust_n
    )

    # apply_components_delta (the DSE/apply entry point) routes through the
    # same writer — confirm the bridge fires there too.
    updated2 = apply_components_delta(ps, {"motors": spec})
    assert updated2.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        default_library.get_motor(_SKU_A).thrust_n
    )


def test_synthetic_motor_without_thrust_n_leaves_param_untouched(tmp_path: Path):
    """★1: bridge only fires when thrust_n is present — a synthetic
    COMPONENT_VARIATION_RULES-shaped spec (power_w only) must not clear or
    invent per_motor_max_thrust_n."""
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

    orch = _fresh(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "per_motor_max_thrust_n": 12.0},
    })
    synthetic_spec = ComponentSpec(
        name="motors_power_w_300.0", component_type="propulsion_active", suggested_key="motors",
        completeness="medium", source="declared",
        properties={"power_w": PropertyValue(value=300.0, unit="W", confidence=0.95, source="declared")},
    )

    updated = set_motor_component(ps, synthetic_spec, 300.0)

    assert updated.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(12.0)


# ── DSE evaluation uses candidate thrust ────────────────────────────────────


def test_catalog_dse_evaluation_uses_candidate_thrust(tmp_path: Path):
    """Project bound to SKU A (thrust 9.5N). Catalog candidates for other
    real SKUs must be evaluated with THEIR OWN thrust, not A's — proven by
    distinct, non-uniform safety margins tracking each SKU's real thrust_n."""
    orch = _project_bound_to(tmp_path, _SKU_A)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        default_library.get_motor(_SKU_A).thrust_n
    )

    result = orch.design_explorer.explore(ps, "mejorar_estabilidad")
    catalog_candidates = [
        c for c in result.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates

    margins_by_sku = {
        c.components_delta["motors"].catalog_ref.sku: c.simulation.safety_margin_ratio
        for c in catalog_candidates
    }
    # Distinct thrust -> distinct margin; a stale-A-thrust bug would make
    # every candidate's margin identical (all evaluated as if still A).
    assert len(set(margins_by_sku.values())) > 1, f"margins collapsed to one value: {margins_by_sku}"

    thrusts_by_sku = {
        sku: default_library.get_motor(sku).thrust_n for sku in margins_by_sku
    }
    # Higher real thrust -> higher margin (monotonic with each SKU's own number).
    ranked_by_margin = sorted(margins_by_sku, key=margins_by_sku.get)
    ranked_by_thrust = sorted(thrusts_by_sku, key=thrusts_by_sku.get)
    assert ranked_by_margin == ranked_by_thrust


# ── SKU-switch — primary acceptance chain (contract §4) ─────────────────────


def test_catalog_native_sku_switch_preserves_identity_and_new_thrust(tmp_path: Path):
    orch = _project_bound_to(tmp_path, _SKU_A)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    base_motor = ps.design_properties.components["motors"]
    assert base_motor.catalog_ref.sku == _SKU_A

    candidate_b = _catalog_candidate(_SKU_B, base=base_motor)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[candidate_b],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )

    result = orch._handle_apply_exploration()
    assert result["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    sku_b_thrust = default_library.get_motor(_SKU_B).thrust_n

    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == _SKU_B
    assert motors.properties["thrust_n"].value == pytest.approx(sku_b_thrust)
    assert saved.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(sku_b_thrust)
    assert saved.current_parameters.get("motor_count") == 6

    # G9-A: bound-and-sufficient SKU B must not show a false catalog gap.
    readiness = build_engineering_readiness(saved)
    catalog_gaps = [g for g in readiness.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert catalog_gaps == []


def test_catalog_native_sku_switch_survives_unrelated_iterate(tmp_path: Path):
    orch = _project_bound_to(tmp_path, _SKU_A)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    base_motor = ps.design_properties.components["motors"]

    candidate_b = _catalog_candidate(_SKU_B, base=base_motor)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[candidate_b],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )
    orch._handle_apply_exploration()

    before = orch.state_manager.load_active_project(orch.workspace_manager)
    before_motor_count = before.current_parameters.get("motor_count")
    before_thrust = before.current_parameters.get("per_motor_max_thrust_n")
    before_sku = before.design_properties.components["motors"].catalog_ref.sku
    assert before_sku == _SKU_B
    assert before_thrust == pytest.approx(default_library.get_motor(_SKU_B).thrust_n)

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
    assert after.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(before_thrust)
    after_motors = after.design_properties.components["motors"]
    assert after_motors.catalog_ref is not None
    assert after_motors.catalog_ref.sku == before_sku
    assert after_motors.properties["thrust_n"].value == pytest.approx(before_thrust)


# ── Viability (explore physics) ──────────────────────────────────────────


def test_real_catalog_candidate_can_be_viable_with_correct_thrust(tmp_path: Path):
    """No prior thrust declared anywhere (no bound/freeform motor) — every
    params-grid entry that needs per_motor_max_thrust_n is omitted by
    _apply_delta's own missing-param guard, so a catalog candidate (whose
    thrust comes from its OWN bound spec via the bridge, independent of
    base_params) can win .viable on real, unmodified physics — no forced
    score, no fixture trickery beyond 'nothing declared yet'."""
    orch = _fresh(tmp_path, motor_count=6)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components.get("motors") is None
    assert ps.current_parameters.get("per_motor_max_thrust_n") is None

    for goal in ("aumentar_payload", "mejorar_estabilidad"):
        result = orch.design_explorer.explore(ps, goal)
        catalog_viable = [
            c for c in result.viable
            if c.components_delta.get("motors") is not None
            and c.components_delta["motors"].catalog_ref is not None
        ]
        assert catalog_viable, f"{goal}: expected >=1 real-SKU candidate in .viable"
        for c in catalog_viable:
            assert c.simulation.can_fly is True


# ── Regressions ───────────────────────────────────────────────────────────


def test_first_bind_c2_regression_still_preserves_catalog_ref(tmp_path: Path):
    """Prior C2 shape (no pre-existing thrust at all — genuinely first
    bind) must still preserve catalog_ref after the bridge lands."""
    orch = _fresh(tmp_path, motor_count=6)
    session = orch.state_manager.get_runtime_session()
    exploration = ExplorationResult(
        goal_key="mejorar_estabilidad", goal_label="maximizar margen de seguridad",
        baseline_score=1.0, baseline_calculations=_make_calc(), baseline_simulation=_make_sim(),
        candidates=[], viable=[_catalog_candidate(_SKU_A)],
    )
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )

    result = orch._handle_apply_exploration()

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == _SKU_A
    assert saved.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        default_library.get_motor(_SKU_A).thrust_n
    )


def test_params_only_diverging_apply_still_clears_catalog_ref(tmp_path: Path):
    """Regression mirror of test_catalog_bind_v1.py::
    test_dse_apply_diverging_thrust_clears_motor_catalog_ref — params-only
    divergence-clearing semantics are untouched by the component-writer
    bridge (★6: G5 logic/order unmodified)."""
    orch = _project_bound_to(tmp_path, _SKU_A)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    components = ps.design_properties.components
    diverged_params = dict(ps.current_parameters)
    diverged_params["per_motor_max_thrust_n"] = default_library.get_motor(_SKU_A).thrust_n * 2

    updated_components, updated_params = invalidate_diverged_catalog_refs(components, diverged_params)

    assert updated_components["motors"].catalog_ref is None
    assert "motor_mass_kg" not in updated_params
