"""DSE apply honest — nameplate W + battery SKU on params-only apply.

implementation_contract_dse_apply_honest.md

Walk (Engineer CLI, autonomia-15min): after watts-recovery pick
sunnysky_r2305_2500 (220 W nameplate) + lipo_4s_5000mah (74 Wh, catalog_ref
set), "optimiza para autonomía" -> "aplica la mejor" on a mixed
params_delta ({battery_capacity_wh_factor: 2.0, motor_power_w_factor: 0.75})
must not invent a lower motor_power_w (165 W) next to a catalog SKU that
declares 220 W, and must not leave the battery at 148 Wh with
catalog_ref=None and name still lipo_4s_5000mah when 148 Wh is exactly
lipo_4s_10000mah's catalog energy.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
    find_battery_skus_for_energy_wh,
    find_unique_battery_sku_for_energy_wh,
)
from jarvis.core.component_writers import (
    set_battery_component,
    set_motor_component,
    set_propeller_component,
)
from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "autonomia 15min",
    "payload_kg": 0.5,
    "restrictions": "autonomia 15 min",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    return o


def _bind_r2305_and_5000mah(o: JarvisOrchestrator, *, motor_count: int = 4) -> None:
    """r2305 (220W nameplate) + gemfan_5045_hbn + lipo_4s_5000mah (74 Wh)."""
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = ps.model_copy(update={"current_parameters": {**ps.current_parameters, "motor_count": motor_count}})
    m = default_library.get_motor("sunnysky_r2305_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    battery_spec = bind_battery_from_catalog("lipo_4s_5000mah")
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    o.workspace_manager.save_state(ps)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())


def _make_sim(**kw) -> SimulationResult:
    defaults = dict(
        can_fly=True, status="pass", safety_margin_ratio=1.5, thrust_to_weight_ratio=1.5,
        autonomy_min=30.0, quality="good", warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0, required_thrust_n=40.0, weight_n=34.3, per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )
    defaults.update(kw)
    return SimulationResult(**defaults)


def _make_calc(**kw) -> CalculationBundle:
    defaults = dict(
        vehicle_type="drone", payload_kg=0.5, structure_mass_kg=1.0, total_mass_kg=2.5,
        weight_n=24.5, required_thrust_n=29.4, motors=4, thrust_per_motor_required_n=7.35,
        available_total_thrust_n=60.0, autonomy_min=30.0, tool_results=[],
    )
    defaults.update(kw)
    return CalculationBundle(**defaults)


def _seed_exploration(o: JarvisOrchestrator, *, params_delta: dict) -> None:
    candidate = ExplorationCandidate(
        params_delta=params_delta,
        components_delta={},
        calculations=_make_calc(),
        simulation=_make_sim(),
        score=2.0,
        label="mixed candidate",
        improvement=0.5,
    )
    exploration = ExplorationResult(
        goal_key="mejorar_autonomia",
        goal_label="maximizar autonomía",
        baseline_score=1.0,
        baseline_calculations=_make_calc(),
        baseline_simulation=_make_sim(),
        candidates=[candidate],
        viable=[candidate],
    )
    session = o.state_manager.runtime_state.session
    o.state_manager.set_runtime_session(session.model_copy(update={"last_exploration_result": exploration}))


def test_mixed_apply_keeps_nameplate_w_and_binds_battery_sku(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_r2305_and_5000mah(o)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters["motor_power_w"] == 220
    assert ps.current_parameters["battery_capacity_wh"] == 74.0

    _seed_exploration(o, params_delta={
        "battery_capacity_wh_factor": 2.0, "motor_power_w_factor": 0.75,
    })

    result = o._handle_apply_exploration()
    assert result["status"] == "ok"
    message = result["message"]

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters["motor_power_w"] == 220
    assert ps.current_parameters["battery_capacity_wh"] == 148.0
    assert ps.current_parameters["battery_mass_kg"] == 0.98

    battery = ps.design_properties.components["battery"]
    assert battery.catalog_ref is not None
    assert battery.catalog_ref.sku == "lipo_4s_10000mah"
    assert battery.name == "lipo_4s_10000mah"

    motors = ps.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == "sunnysky_r2305_2500"

    assert "sunnysky_r2305_2500 declara 220 W de placa" in message
    assert "Batería vinculada a lipo_4s_10000mah (148 Wh" in message


def test_unmatched_wh_stays_parametric(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_r2305_and_5000mah(o)

    _seed_exploration(o, params_delta={"battery_capacity_wh_factor": 2.5})  # 185 Wh — no pack

    result = o._handle_apply_exploration()
    assert result["status"] == "ok"
    message = result["message"]

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters["battery_capacity_wh"] == 185.0
    assert ps.current_parameters["motor_power_w"] == 220

    battery = ps.design_properties.components["battery"]
    assert battery.catalog_ref is None

    assert "185 Wh no coinciden con un pack del catálogo" in message
    assert "paramétrica" in message


def test_wh_only_delta_binds_battery_motor_untouched(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_r2305_and_5000mah(o)

    _seed_exploration(o, params_delta={"battery_capacity_wh_factor": 2.0})

    result = o._handle_apply_exploration()
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters["motor_power_w"] == 220
    battery = ps.design_properties.components["battery"]
    assert battery.catalog_ref.sku == "lipo_4s_10000mah"
    assert ps.current_parameters["battery_capacity_wh"] == 148.0


def test_unbound_motor_delta_writes_invented_w_battery_still_binds(tmp_path: Path):
    """Documented fixture choice: motor is NOT catalog-bound here (freeform
    motor_power_w=220 only), so §2.1 does not apply and the delta-derived
    165 W is written as today. Battery stays catalog-bound at 74 Wh so the
    Wh-match bind in §2.2 is exercised independent of motor bind state."""
    o = _fresh(tmp_path)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": 4,
            "motor_power_w": 220,
        }
    })
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    battery_spec = bind_battery_from_catalog("lipo_4s_5000mah")
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    o.workspace_manager.save_state(ps)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.design_properties.components.get("motors") is None or (
        ps.design_properties.components["motors"].catalog_ref is None
    )

    _seed_exploration(o, params_delta={
        "battery_capacity_wh_factor": 2.0, "motor_power_w_factor": 0.75,
    })

    result = o._handle_apply_exploration()
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters["motor_power_w"] == 165.0
    battery = ps.design_properties.components["battery"]
    assert battery.catalog_ref.sku == "lipo_4s_10000mah"


def test_two_or_more_matches_refuses_apply(tmp_path: Path, monkeypatch):
    o = _fresh(tmp_path)
    _bind_r2305_and_5000mah(o)
    ps_before = o.state_manager.load_active_project(o.workspace_manager)
    params_before = dict(ps_before.current_parameters)

    monkeypatch.setattr(
        "jarvis.core.catalog_bind.find_battery_skus_for_energy_wh",
        lambda energy_wh, **kw: ["lipo_4s_10000mah", "fake_other_pack_148wh"],
    )

    _seed_exploration(o, params_delta={"battery_capacity_wh_factor": 2.0})

    result = o._handle_apply_exploration()
    assert result["status"] == "error"
    assert result["action"] == "apply_exploration_result"
    assert "más de un pack" in result["message"]

    ps_after = o.state_manager.load_active_project(o.workspace_manager)
    assert dict(ps_after.current_parameters) == params_before


def test_find_unique_battery_sku_for_energy_wh():
    assert find_unique_battery_sku_for_energy_wh(148.0) == "lipo_4s_10000mah"
    assert find_unique_battery_sku_for_energy_wh(74.0) == "lipo_4s_5000mah"
    assert find_unique_battery_sku_for_energy_wh(185.0) is None


def test_find_battery_skus_for_energy_wh_count():
    assert find_battery_skus_for_energy_wh(148.0) == ["lipo_4s_10000mah"]
    assert find_battery_skus_for_energy_wh(185.0) == []
