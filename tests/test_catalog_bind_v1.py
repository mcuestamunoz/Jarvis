"""Physical Component Catalog v1 — Impl B (Bind).

Design authority: docs/PHYSICAL_COMPONENT_CATALOG_V1.md (DESIGN CLOSED, locks
1A/2A/4A). Contract: .jes/artifacts/implementation_contract_catalog_bind_v1.md

Scope: SKU identity (catalog_ref) surviving a catalog pick (iterate +
DEFINE_MISSING) and save/load; SKU-bound mass causality (motor + battery);
catalog_ref invalidation when a later mutation diverges a bound component's
physical number from its SKU (DSE params-only apply + iterate numeric
mutation); unbound-path regression (today's physics unchanged).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
    invalidate_diverged_catalog_refs,
)
from jarvis.core.component_writers import set_battery_component, set_motor_component
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_ENERGY_PARAMETERS
from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult
from jarvis.tools.electricity import estimate_battery_mass_kg


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


def _comp(key: str, ctype: str, **props) -> ComponentSpec:
    return ComponentSpec(
        name=key, component_type=ctype, suggested_key=key,
        completeness="high", source="declared", properties=props,
    )


def _closed_project(tmp_path: Path) -> JarvisOrchestrator:
    """Full architecture closed drone project — matches FN-024/025/026's own
    fixture shape (motors/propellers/battery/frame/control all present)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = _comp("motors", "propulsion_active",
        motor_count=PropertyValue(value=4), kv_rating=PropertyValue(value=920),
        thrust_n=PropertyValue(value=12))
    propellers = _comp("propellers", "propulsion_passive",
        diameter_in=PropertyValue(value=10), pitch_in=PropertyValue(value=4.5))
    battery = _comp("battery", "energy_storage", battery_capacity_wh=PropertyValue(value=74))
    frame = _comp("frame", "structure",
        mass_kg=PropertyValue(value=0.5), material=PropertyValue(value="fibra"))
    flight_controller = _comp("flight_controller", "control",
        model=PropertyValue(value="Pixhawk 4"))
    sensors = _comp("sensors", "control", gps_model=PropertyValue(value="M9N"))

    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {
            "motors": motors, "propellers": propellers, "battery": battery,
            "frame": frame, "flight_controller": flight_controller, "sensors": sensors,
        },
    })
    ps2 = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {
            **(ps.current_parameters or {}),
            "motor_count": 4, "per_motor_max_thrust_n": 3.0,
            "battery_capacity_wh": 74.0, "motor_power_w": 50.0,
            "propeller_diameter_in": 10.0,
        },
        "latest_results": {
            "simulation": {
                "status": "pass", "can_fly": True, "safety_margin_ratio": 1.4,
                "thrust_to_weight_ratio": 1.4, "autonomy_min": 30.0, "quality": "good",
                "warnings": [],
                "analysis": {
                    "available_thrust_n": 48.0, "required_thrust_n": 37.7,
                    "weight_n": 31.4, "per_motor_load_ratio": 0.25,
                },
                "summary": "ok",
            },
            "calculations": {
                "vehicle_type": "dron", "payload_kg": 2.0, "structure_mass_kg": 1.2,
                "total_mass_kg": 3.2, "weight_n": 31.4, "required_thrust_n": 37.7,
                "motors": 4, "thrust_per_motor_required_n": 9.4,
                "available_total_thrust_n": 48.0, "autonomy_min": 30.0, "tool_results": [],
            },
        },
    })
    orch.workspace_manager.save_state(ps2)
    return orch


def _make_sim(*, safety_margin_ratio: float = 1.5) -> SimulationResult:
    return SimulationResult(
        can_fly=True, status="pass", safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=safety_margin_ratio, autonomy_min=30.0, quality="good",
        warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0, required_thrust_n=40.0, weight_n=34.3,
            per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )


def _make_calc(*, total_mass_kg: float = 3.5) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="dron", payload_kg=2.0, structure_mass_kg=1.5,
        total_mass_kg=total_mass_kg, weight_n=total_mass_kg * 9.81,
        required_thrust_n=total_mass_kg * 9.81 * 1.2, motors=4,
        thrust_per_motor_required_n=(total_mass_kg * 9.81 * 1.2) / 4,
        available_total_thrust_n=60.0, autonomy_min=30.0, tool_results=[],
    )


# ── 1. Iterate motor catalog pick → catalog_ref set + persists ─────────────

def test_iterate_motor_pick_sets_and_persists_catalog_ref(tmp_path: Path):
    orch = _closed_project(tmp_path)

    orch.handle_user_text("definir componentes", _RefuseLLM())
    r1 = orch.handle_user_text("si", _RefuseLLM())
    assert r1["status"] == "interactive"
    r2 = orch.handle_user_text("motor 4x 920KV", _RefuseLLM())
    suggestions = r2.get("motor_suggestions") or []
    if not suggestions:
        pytest.skip("no catalog matches for fixture design space")
    r3 = orch.handle_user_text("1", _RefuseLLM())
    assert r3["status"] == "interactive"
    orch.handle_user_text("ninguna", _RefuseLLM())  # step 3: restrictions
    orch.handle_user_text("si", _RefuseLLM())  # step 4: impact estimate ack
    r6 = orch.handle_user_text("si", _RefuseLLM())  # step 5: final confirm → applies
    assert r6["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = saved.design_properties.components.get("motors")
    assert motors_spec is not None
    assert motors_spec.catalog_ref is not None
    assert motors_spec.catalog_ref.family == "motor"
    assert motors_spec.catalog_ref.sku == suggestions[0]["name"]
    # Cursor review (implementation_review_catalog_bind_v1.md, PASS WITH NOTES):
    # the iterate catalog-pick apply path persisted catalog_ref but bypassed
    # component_writers.set_motor_component entirely (mutation_engine's
    # component_patch dump never touched current_parameters), so motor_mass_kg
    # was silently missing — identity-only, not atomic with mass. Closed by
    # routing catalog-bound patches through the writer in
    # actions/iterate.py::_run_declarative_iteration.
    motor_count = saved.current_parameters.get("motor_count")
    assert motor_count is not None
    assert saved.current_parameters.get("motor_mass_kg") == pytest.approx(
        suggestions[0]["weight_g"] / 1000.0 * motor_count
    )


# ── 2. DEFINE_MISSING catalog pick → catalog_ref set ────────────────────────

def test_define_missing_catalog_pick_sets_catalog_ref(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "fotografía aérea cámara 1kg",
            "payload_kg": 1.0,
            "restrictions": "autonomía mínima 20 minutos",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    help_result = orch.param_definition_session.answer("ayúdame a elegir")
    suggestions = help_result.get("motor_suggestions") or []
    if not suggestions:
        pytest.skip("no catalog matches for fixture thrust band")
    pick = orch.param_definition_session.answer("1")
    assert pick["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = saved.design_properties.components.get("motors")
    assert motors_spec is not None
    assert motors_spec.catalog_ref is not None
    assert motors_spec.catalog_ref.family == "motor"
    assert motors_spec.catalog_ref.sku == suggestions[0]["name"]


# ── 3. Save/load → catalog_ref survives ─────────────────────────────────────

def test_catalog_ref_survives_save_load_round_trip(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    suggestion: MotorSuggestion = {
        "idx": 1, "name": "sunnysky_x2216_11", "thrust_n": 12.5, "kv_rating": 1100,
        "weight_g": 62, "max_watts": 280, "is_generic": False,
    }
    spec = bind_motor_from_catalog(suggestion)
    ps2 = set_motor_component(ps, spec, 280.0)
    orch.workspace_manager.save_state(ps2)

    reloaded = orch.state_manager.load_active_project(orch.workspace_manager)
    reloaded_ref = reloaded.design_properties.components["motors"].catalog_ref
    assert reloaded_ref == CatalogRef(family="motor", sku="sunnysky_x2216_11")


# ── 4. Regression: unbound declare path → catalog_ref is None ──────────────

def test_unbound_declare_path_catalog_ref_none(tmp_path: Path):
    orch = _closed_project(tmp_path)
    result = orch.handle_user_text("motor 4x 920KV", _RefuseLLM())
    assert result["status"] in {"interactive", "ok"}
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = saved.design_properties.components.get("motors")
    assert motors_spec is not None
    assert motors_spec.catalog_ref is None


# ── 5/6. Mass causality — SKU-bound motor increases total_mass vs unbound ───

def test_bound_motor_mass_increases_total_mass_vs_unbound():
    base_params = {
        "vehicle_type": "dron", "payload_kg": 2.0, "structure_mass_factor": 0.6,
        "safety_factor": 1.2, "motor_count": 4, "per_motor_max_thrust_n": 12.0,
    }
    engine = CalculationEngine()

    unbound_result = engine.build(dict(base_params))
    bound_params = {**base_params, "motor_mass_kg": round(0.062 * 4, 4)}
    bound_result = engine.build(bound_params)

    assert bound_result.total_mass_kg > unbound_result.total_mass_kg
    assert bound_result.total_mass_kg == pytest.approx(
        unbound_result.total_mass_kg + 0.062 * 4, abs=1e-6
    )
    # Causality propagates: more mass → more weight → more required thrust.
    assert bound_result.required_thrust_n > unbound_result.required_thrust_n


def test_set_motor_component_writes_motor_mass_kg_only_when_bound(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    suggestion: MotorSuggestion = {
        "idx": 1, "name": "sunnysky_x2216_11", "thrust_n": 12.5, "kv_rating": 1100,
        "weight_g": 62, "max_watts": 280, "is_generic": False,
    }
    bound_spec = bind_motor_from_catalog(suggestion)
    ps_bound = set_motor_component(ps, bound_spec, 280.0)
    assert ps_bound.current_parameters.get("motor_mass_kg") == pytest.approx(0.062 * 4)

    unbound_spec = ComponentSpec(
        name="motors", component_type="propulsion_active",
        properties={"power_w": PropertyValue(value=280.0, unit="W")},
    )
    ps_unbound = set_motor_component(ps, unbound_spec, 280.0)
    assert "motor_mass_kg" not in ps_unbound.current_parameters


# ── 7. Battery bind → capacity_wh + mass_kg match SKU, not heuristic ───────

def test_battery_bind_uses_sku_mass_not_heuristic(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    sku_spec = default_library.get_battery("lipo_4s_5000mah")
    bound = bind_battery_from_catalog("lipo_4s_5000mah")
    ps2 = set_battery_component(ps, bound, sku_spec.energy_wh)

    assert ps2.current_parameters["battery_capacity_wh"] == sku_spec.energy_wh
    assert ps2.current_parameters["battery_mass_kg"] == pytest.approx(sku_spec.mass_g / 1000.0)
    # Confirm it's NOT the generic heuristic (this SKU's density differs from 150 Wh/kg).
    assert ps2.current_parameters["battery_mass_kg"] != pytest.approx(
        estimate_battery_mass_kg(sku_spec.energy_wh)
    )


# ── 8. Unbound battery → still heuristic mass (regression) ─────────────────

def test_unbound_battery_still_uses_heuristic(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = ComponentSpec(name="battery", component_type="energy_storage")
    ps2 = set_battery_component(ps, spec, 74.0)
    assert ps2.current_parameters["battery_mass_kg"] == pytest.approx(
        estimate_battery_mass_kg(74.0)
    )


# ── 9/10. Dual-truth: DSE apply diverges bound motor → catalog_ref cleared ──

def test_dse_apply_diverging_thrust_clears_motor_catalog_ref(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    suggestion: MotorSuggestion = {
        "idx": 1, "name": "sunnysky_x2216_11", "thrust_n": 12.5, "kv_rating": 1100,
        "weight_g": 62, "max_watts": 280, "is_generic": False,
    }
    bound_spec = bind_motor_from_catalog(suggestion)
    ps_bound = set_motor_component(ps, bound_spec, 280.0)
    ps_bound = ps_bound.model_copy(update={
        "current_parameters": {**ps_bound.current_parameters, "per_motor_max_thrust_n": 12.5}
    })
    orch.workspace_manager.save_state(ps_bound)

    exploration = ExplorationResult(
        goal_key="aumentar_payload",
        goal_label="maximizar carga útil",
        baseline_score=1.0,
        baseline_calculations=_make_calc(),
        baseline_simulation=_make_sim(),
        candidates=[],
        viable=[
            ExplorationCandidate(
                params_delta={"per_motor_max_thrust_n_factor": 2.0},
                components_delta={},
                calculations=_make_calc(total_mass_kg=4.0),
                simulation=_make_sim(safety_margin_ratio=1.8),
                score=2.0,
                label="empuje/motor=25.0",
                improvement=1.0,
            )
        ],
    )
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )

    result = orch._handle_apply_exploration()
    assert result["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = saved.design_properties.components.get("motors")
    assert motors_spec.catalog_ref is None
    # Mass mirror falls back — no longer claiming SKU-authoritative mass.
    assert "motor_mass_kg" not in saved.current_parameters
    assert saved.current_parameters["per_motor_max_thrust_n"] == pytest.approx(25.0)


def test_invalidate_diverged_catalog_refs_battery(tmp_path: Path):
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    bound = bind_battery_from_catalog("lipo_4s_5000mah")
    ps_bound = set_battery_component(ps, bound, 74.0)

    components = ps_bound.design_properties.components
    params = dict(ps_bound.current_parameters)
    params["battery_capacity_wh"] = 500.0  # diverges from the bound SKU's 74.0 Wh

    updated_components, updated_params = invalidate_diverged_catalog_refs(components, params)
    assert updated_components["battery"].catalog_ref is None
    assert updated_params["battery_mass_kg"] == pytest.approx(estimate_battery_mass_kg(500.0))


def test_invalidate_diverged_catalog_refs_no_op_when_unchanged():
    suggestion: MotorSuggestion = {
        "idx": 1, "name": "sunnysky_x2216_11", "thrust_n": 12.5, "kv_rating": 1100,
        "weight_g": 62, "max_watts": 280, "is_generic": False,
    }
    spec = bind_motor_from_catalog(suggestion)
    components = {"motors": spec}
    params = {"per_motor_max_thrust_n": 12.5}
    updated_components, updated_params = invalidate_diverged_catalog_refs(components, params)
    assert updated_components is components
    assert updated_params is params
    assert updated_components["motors"].catalog_ref is not None


def test_iterate_numeric_mutation_diverging_capacity_clears_battery_catalog_ref(tmp_path: Path):
    """Case #2 from the contract: an iterate numeric mutation (not DSE) that
    sets an explicit value different from the bound SKU's own projected
    value — covered here for battery (motor thrust divergence is covered by
    the DSE-apply test above; "thrust"/"empuje" phrasing collides with the
    FN-022 goal-detection gate before reaching iterate, so battery is the
    cleaner natural-language path to exercise this same shared invalidation
    rule end to end)."""
    orch = _closed_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    bound_spec = bind_battery_from_catalog("lipo_4s_5000mah")
    ps_bound = set_battery_component(ps, bound_spec, 74.0)
    orch.workspace_manager.save_state(ps_bound)
    assert ps_bound.design_properties.components["battery"].catalog_ref is not None

    orch.handle_user_text("cambia battery_capacity_wh", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())
    orch.handle_user_text("battery_capacity_wh", _RefuseLLM())
    orch.handle_user_text("500", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())  # impact estimate ack
    r5 = orch.handle_user_text("si", _RefuseLLM())  # final confirm → applies
    assert r5["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    battery_spec = saved.design_properties.components.get("battery")
    assert battery_spec.catalog_ref is None
    assert saved.current_parameters["battery_capacity_wh"] == pytest.approx(500.0)
    assert saved.current_parameters["battery_mass_kg"] == pytest.approx(
        estimate_battery_mass_kg(500.0)
    )


# ── Propeller bind (helper + tests only — no existing pick UX, per 2.1.D) ──

def test_bind_propeller_from_catalog_sets_catalog_ref():
    spec = bind_propeller_from_catalog("apc_10x4_5")
    assert spec.catalog_ref == CatalogRef(family="propeller", sku="apc_10x4_5")
    assert spec.properties["diameter_in"].value == 10.0
    assert spec.properties["pitch_in"].value == 4.5


# ── Regressions: FN-022...026 smoke ─────────────────────────────────────────

def test_fn026_lever_preseed_unaffected(tmp_path: Path):
    orch = _closed_project(tmp_path)
    r0 = orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    assert r0["action"] == "engineering_intent"
    r1 = orch.handle_user_text("incrementa safety_factor", _RefuseLLM())
    assert r1["iteration_draft"]["variable"] == "safety_factor"
