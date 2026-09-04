"""Tests for battery/energy physics and semantic keyword parser.

Covers:
- calculate_autonomy_min tool
- CalculationEngine energy block (valid / missing)
- FeasibilitySimulator energy_status + autonomy_min
- ReasoningLayer missing_energy_parameters signal
- Orchestrator: _PARAM_META, energy proactive in build_startup_context
- Orchestrator: _parse_params_from_keywords semantic parser
- Handler integration: keyword input → all params completed
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.simulation.simulator import FeasibilitySimulator
from jarvis.tools.electricity import calculate_autonomy_min


# ── helpers ───────────────────────────────────────────────────────────────────

_BASE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de carga",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motor_count": 4,
    "per_motor_max_thrust_n": 15.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _make_energy_project(tmp_path: Path) -> tuple[JarvisOrchestrator, str]:
    """Project with force physics complete but energy params absent."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": {**_BASE_PARAMS, "motors": 4}})
    return orchestrator, result["workspace_path"]


def _make_energy_project_catalog_bound_no_watts(tmp_path: Path) -> tuple[JarvisOrchestrator, str]:
    """CLI feasibility vs readiness semantics IC (§2.4): catalog-bound motor
    (emax_rs2205s_2300, no nameplate max_watts) + battery Wh set — the
    remaining energy gap is honestly unsatisfiable by "defining"
    motor_power_w, not a param the proactive question should keep asking
    for."""
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component
    from jarvis.knowledge.library import default_library

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": {**_BASE_PARAMS, "motors": 4}})
    workspace_path = result["workspace_path"]

    ps = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    m = default_library.get_motor("emax_rs2205s_2300")
    assert m.max_watts is None, "fixture assumes this SKU has no nameplate wattage"
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    battery_spec = bind_battery_from_catalog("lipo_4s_10000mah")
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    orchestrator.workspace_manager.save_state(ps)
    return orchestrator, workspace_path


def _make_energy_complete_project(tmp_path: Path) -> tuple[JarvisOrchestrator, str]:
    """Project with both force AND energy params defined."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": {**_BASE_PARAMS, "motors": 4}})
    workspace_path = result["workspace_path"]
    state_path = Path(workspace_path) / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["current_parameters"]["battery_capacity_wh"] = 2000.0
    data["current_parameters"]["motor_power_w"] = 50.0
    state_path.write_text(json.dumps(data), encoding="utf-8")
    return orchestrator, workspace_path


# ── calculate_autonomy_min ────────────────────────────────────────────────────

def test_calculate_autonomy_min_basic():
    result = calculate_autonomy_min(battery_capacity_wh=2000.0, total_power_w=400.0)
    assert result.tool_name == "calculate_autonomy_min"
    assert result.outputs["autonomy_min"] == pytest.approx(300.0)  # 2000/400*60=300min


def test_calculate_autonomy_min_zero_power_returns_zero():
    result = calculate_autonomy_min(battery_capacity_wh=2000.0, total_power_w=0.0)
    assert result.outputs["autonomy_min"] == 0.0


# ── CalculationEngine energy block ────────────────────────────────────────────

def test_engine_with_energy_params_produces_autonomy_min():
    engine = CalculationEngine()
    params = {**_BASE_PARAMS, "battery_capacity_wh": 2000.0, "motor_power_w": 50.0}
    bundle = engine.build(params)
    assert bundle.autonomy_min is not None
    assert bundle.autonomy_min > 0


def test_engine_without_energy_params_autonomy_min_is_none():
    engine = CalculationEngine()
    bundle = engine.build(_BASE_PARAMS)
    assert bundle.autonomy_min is None


def test_engine_without_energy_params_traces_missing_energy():
    engine = CalculationEngine()
    bundle = engine.build(_BASE_PARAMS)
    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert "missing_energy_parameters" in tool_names


def test_engine_with_energy_params_no_missing_energy_trace():
    engine = CalculationEngine()
    params = {**_BASE_PARAMS, "battery_capacity_wh": 2000.0, "motor_power_w": 50.0}
    bundle = engine.build(params)
    tool_names = [tr.tool_name for tr in bundle.tool_results]
    assert "missing_energy_parameters" not in tool_names


# ── FeasibilitySimulator energy_status ────────────────────────────────────────

def test_simulator_energy_status_valid_when_battery_present():
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    params = {**_BASE_PARAMS, "battery_capacity_wh": 2000.0, "motor_power_w": 50.0}
    bundle = engine.build(params)
    result = sim.evaluate(bundle)
    assert result.energy_status == "valid"
    assert result.autonomy_min is not None


def test_simulator_energy_status_missing_when_no_battery():
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    bundle = engine.build(_BASE_PARAMS)
    result = sim.evaluate(bundle)
    assert result.energy_status == "missing_energy_parameters"
    assert result.autonomy_min is None


def test_simulator_missing_energy_does_not_change_physics_status():
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    bundle = engine.build(_BASE_PARAMS)
    result = sim.evaluate(bundle)
    assert result.physics_status == "valid"


def test_simulator_missing_energy_not_in_warnings():
    """Energy status is separate from force warnings — doesn't affect status_type."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    bundle = engine.build(_BASE_PARAMS)
    result = sim.evaluate(bundle)
    assert "missing_energy_parameters" not in result.warnings


def test_simulator_missing_physics_with_energy_present_energy_status_valid():
    """If physics params are missing but battery params are defined, energy_status must be 'valid'."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    # Ground domain: torque declared but wheel/gear absent → physics missing
    # Battery params present → energy block completes
    params = {
        "vehicle_type": "rover",
        "payload_kg": 5.0,
        "structure_mass_factor": 0.5,
        "safety_factor": 1.5,
        "motor_count": 2,
        "per_actuator_torque_nm": 3.0,
        # wheel_radius_m and gear_ratio deliberately absent → physics missing
        "battery_capacity_wh": 2000.0,
        "motor_power_w": 100.0,
    }
    bundle = engine.build(params)
    assert bundle.autonomy_min is not None
    result = sim.evaluate(bundle)
    assert result.physics_status == "missing_parameters"
    assert result.energy_status == "valid"
    assert result.autonomy_min is not None
    assert result.autonomy_min > 0


def test_simulator_missing_physics_without_energy_energy_status_missing():
    """If both physics and energy are missing, energy_status must be 'missing_energy_parameters'."""
    engine = CalculationEngine()
    sim = FeasibilitySimulator()
    params = {
        "vehicle_type": "rover",
        "payload_kg": 5.0,
        "structure_mass_factor": 0.5,
        "safety_factor": 1.5,
        "motor_count": 2,
        "per_actuator_torque_nm": 3.0,
        # no wheel/gear → physics missing; no battery → energy missing
    }
    bundle = engine.build(params)
    result = sim.evaluate(bundle)
    assert result.physics_status == "missing_parameters"
    assert result.energy_status == "missing_energy_parameters"
    assert result.autonomy_min is None


# ── ReasoningLayer missing_energy_parameters signal ───────────────────────────

def test_reasoning_signal_missing_energy_when_no_battery():
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {},
    }
    output = layer.build(context)
    assert output.signals.get("missing_energy_parameters") is True


def test_reasoning_signal_missing_energy_false_when_battery_present():
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "valid"},
        "current_parameters": {"battery_capacity_wh": 2000.0, "motor_power_w": 50.0},
    }
    output = layer.build(context)
    assert output.signals.get("missing_energy_parameters") is False


def test_reasoning_missing_energy_adds_insight():
    layer = ReasoningLayer()
    context = {
        "last_simulation": {
            "energy_status": "missing_energy_parameters",
            "physics_status": "valid",
            "safety_margin_ratio": 1.5,
            "can_fly": True,
        },
        "current_parameters": {},
    }
    output = layer.build(context)
    assert any("autonomía" in i for i in output.insights)


def test_reasoning_missing_energy_catalog_bound_motor_no_watts_label():
    """CLI feasibility vs readiness semantics IC (§2.3): when the motor is
    catalog-bound and honestly has no nameplate wattage, the CTA must not
    tell the user to "declare" motor_power_w — that invites an invented
    number feeding (Wh/W)x60 as if it were real evidence."""
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {"battery_capacity_wh": 148.0},
        "design_properties": {
            "components": {
                "motors": {"catalog_ref": {"family": "motor", "sku": "emax_rs2205s_2300"}}
            }
        },
    }
    output = layer.build(context)
    labels = [s.label for s in output.suggested_actions]
    assert not any("Declarar motor_power_w" in l for l in labels)
    assert any("no declara vatios" in l.lower() for l in labels)
    assert any("no inventes motor_power_w" in i.lower() for i in output.insights)


def test_reasoning_missing_energy_catalog_bound_motor_with_watts_no_cta():
    """T1 (implementation_contract_cli_catalog_assist_t1.md §2.6): a bound
    SKU that DOES declare nameplate watts (sunnysky_r2305_2500, 220W) must
    never see the "no declara vatios" CTA — that copy is now gated on
    catalog_bound_motor_lacks_nameplate_watts, not the identity-only
    catalog_bound_motor_covers_power_w. The old CTA (from the identity
    predicate) previously fired here — this reproduces the walk's reported
    bug where the CLI showed the CTA for a SKU whose real wattage was on
    screen elsewhere."""
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {"battery_capacity_wh": 148.0},
        "design_properties": {
            "components": {
                "motors": {"catalog_ref": {"family": "motor", "sku": "sunnysky_r2305_2500"}}
            }
        },
    }
    output = layer.build(context)
    labels = [s.label for s in output.suggested_actions]
    assert not any("no declara vatios" in l.lower() for l in labels)
    assert not any("no declara vatios" in i.lower() for i in output.insights)


def test_reasoning_missing_energy_stale_signal_with_both_params_present_no_declare():
    """implementation_contract_cli_stale_energy_recalc.md §2.2: a bound SKU
    that declares nameplate watts, with both battery_capacity_wh and
    motor_power_w already in current_parameters, must not be told to
    "declare" those params just because the stale
    energy_status=missing_energy_parameters signal (from a pre-pick
    simulation) has not been recalculated yet."""
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {"battery_capacity_wh": 148.0, "motor_power_w": 220.0},
        "design_properties": {
            "components": {
                "motors": {"catalog_ref": {"family": "motor", "sku": "sunnysky_r2305_2500"}}
            }
        },
    }
    output = layer.build(context)
    labels = [s.label for s in output.suggested_actions]
    assert not any("Declarar battery_capacity_wh" in l for l in labels)
    assert not any("Declarar battery_capacity_wh" in i for i in output.insights)


def test_reasoning_missing_energy_unbound_motor_still_asks_to_declare():
    """Same signal, but the motor has no catalog_ref at all — the original
    "Declarar motor_power_w" CTA must be unchanged for a genuinely unbound
    motor (this is the honest gap the CTA exists for)."""
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {"battery_capacity_wh": 148.0},
        "design_properties": {"components": {}},
    }
    output = layer.build(context)
    labels = [s.label for s in output.suggested_actions]
    assert any("Declarar motor_power_w" in l for l in labels)


def test_reasoning_missing_energy_does_not_pre_empt_declarative_context():
    """declarative_context suggestions have higher priority than energy suggestions."""
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "mutation_mode": "declarative",
        "design_properties": {
            "components": {"m1": {"component_type": "propulsion_active", "missing_fields": []}}
        },
        "current_parameters": {},
    }
    output = layer.build(context)
    # Should see declarative next steps, not energy suggestion
    labels = [s.label for s in output.suggested_actions]
    assert not any("battery_capacity_wh" in l for l in labels)


# ── build_startup_context: energy proactive ───────────────────────────────────

def test_build_startup_context_nominal_has_energy_proactive(tmp_path: Path):
    orchestrator, workspace_path = _make_energy_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx.get("proactive_question") is not None
    assert "battery" in ctx["proactive_question"] or "energía" in ctx["proactive_question"] or "battery_capacity_wh" in ctx["proactive_question"]


def test_build_startup_context_energy_complete_has_no_proactive(tmp_path: Path):
    orchestrator, workspace_path = _make_energy_complete_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx.get("proactive_question") is None


def test_build_startup_context_energy_missing_params_list(tmp_path: Path):
    orchestrator, workspace_path = _make_energy_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert isinstance(ctx.get("missing_params"), list)
    assert "battery_capacity_wh" in ctx["missing_params"] or "motor_power_w" in ctx["missing_params"]


def test_build_startup_context_status_type_stays_nominal_without_battery(tmp_path: Path):
    """Missing energy params should NOT change status_type from nominal to warning."""
    orchestrator, workspace_path = _make_energy_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx["status_type"] == "nominal"


def test_build_startup_context_energy_returns_param_definition_reason(tmp_path: Path):
    """build_startup_context must return param_definition_reason for energy proactive."""
    orchestrator, workspace_path = _make_energy_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx.get("param_definition_reason") == "missing_energy_parameters"


def test_build_startup_context_catalog_bound_motor_no_watts_no_proactive(tmp_path: Path):
    """CLI feasibility vs readiness semantics IC (§2.4): catalog-bound motor
    with no nameplate wattage + battery Wh set -> no proactive question
    asking to "define" motor_power_w (nothing left to declare)."""
    orchestrator, workspace_path = _make_energy_project_catalog_bound_no_watts(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx.get("proactive_question") is None
    assert "motor_power_w" not in (ctx.get("missing_params") or [])


def test_build_startup_context_transmission_returns_param_definition_reason(tmp_path: Path):
    """build_startup_context must return param_definition_reason for transmission proactive."""
    from test_define_transmission_params import _make_blocking_project
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    if ctx.get("proactive_question"):
        assert ctx.get("param_definition_reason") == "missing_transmission_parameters"


# ── _PARAM_META coverage ──────────────────────────────────────────────────────

def test_param_question_battery_capacity_is_human_readable():
    o = JarvisOrchestrator()
    q = o.param_definition_session.param_question("battery_capacity_wh")
    assert "bater" in q.lower() or "capacidad" in q.lower()
    assert "2000" in q


def test_param_question_motor_power_is_human_readable():
    o = JarvisOrchestrator()
    q = o.param_definition_session.param_question("motor_power_w")
    assert "potencia" in q.lower()
    assert "ayúdame a elegir" in q.lower() or "ayudame a elegir" in q.lower()
    # Internal key must not be the hero of the prompt
    assert "(motor_power_w)" not in q


# ── _parse_params_from_keywords ───────────────────────────────────────────────

@pytest.mark.parametrize("user_input, param, expected", [
    ("radio 0.15 engranaje 10", "wheel_radius_m", 0.15),
    ("radio 0.15 engranaje 10", "gear_ratio", 10.0),
    ("wheel_radius 0.25", "wheel_radius_m", 0.25),
    ("gear 8", "gear_ratio", 8.0),
    ("batería 2000", "battery_capacity_wh", 2000.0),
    ("potencia 50", "motor_power_w", 50.0),
    ("battery 1500 power 75", "battery_capacity_wh", 1500.0),
    ("battery 1500 power 75", "motor_power_w", 75.0),
])
def test_parse_params_from_keywords_extracts_known_params(user_input, param, expected):
    o = JarvisOrchestrator()
    result = o.param_definition_session.parse_params_from_keywords(user_input, [param])
    assert result.get(param) == pytest.approx(expected)


def test_parse_params_from_keywords_returns_empty_for_no_match():
    o = JarvisOrchestrator()
    result = o.param_definition_session.parse_params_from_keywords("just a number 42", ["wheel_radius_m"])
    assert result == {}


def test_parse_params_from_keywords_only_considers_pending():
    o = JarvisOrchestrator()
    # gear_ratio not in pending → should not appear in result
    result = o.param_definition_session.parse_params_from_keywords("radio 0.15 engranaje 10", ["wheel_radius_m"])
    assert "gear_ratio" not in result
    assert result.get("wheel_radius_m") == pytest.approx(0.15)


# ── Handler integration with keyword input ────────────────────────────────────

def test_keyword_input_resolves_both_params_in_one_go(tmp_path: Path):
    """'radio 0.15 engranaje 10' should complete transmission params via keyword parse."""
    from test_define_transmission_params import _make_blocking_project
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=workspace_path
    )
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    result = orchestrator.param_definition_session.answer("radio 0.15 engranaje 10")
    assert result["status"] == "ok"
    assert result["action"] == "define_missing_params"


def test_keyword_input_assigns_correct_values_regardless_of_order(tmp_path: Path):
    """'engranaje 10 radio 0.15' should assign gear_ratio=10, wheel_radius_m=0.15."""
    from test_define_transmission_params import _make_blocking_project
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=workspace_path
    )
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    result = orchestrator.param_definition_session.answer("engranaje 10 radio 0.15")
    assert result["status"] == "ok"
    state = json.loads((Path(workspace_path) / "state.json").read_text(encoding="utf-8"))
    assert state["current_parameters"]["wheel_radius_m"] == pytest.approx(0.15)
    assert state["current_parameters"]["gear_ratio"] == pytest.approx(10.0)
