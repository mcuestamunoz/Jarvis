"""Battery Catalog UX + G27 Hardening (IC 2 / Project Closure arc).

Covers .jes/artifacts/implementation_contract_battery_catalog_bind_ux_g27.md
Bat-7 minimum 8 tests + regression anchors:
  - component wizard help-choose -> battery catalog list (Bat-2/3)
  - pick -> bind_battery_from_catalog + set_battery_component (locked apply
    path, §5) -> real catalog_ref/Wh/mass/cells
  - autonomy_min after "calcular" uses the real SKU Wh, not the 150 Wh/kg
    heuristic or a G27-corrupted value
  - IDLE help-choose dispatch precedence: motor -> propeller -> battery
  - G27: "LiPo 6S 10000mAh" resolves to ~222 Wh, never a silent 6.0
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog
from jarvis.core.component_writers import set_battery_component, set_motor_component
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.llm.semantic_intent_adapter import SemanticIntentAdapter
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _fresh_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orc = JarvisOrchestrator(workspace_root=tmp_path)
    orc.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba battery catalog ux",
            "payload_kg": 1.0,
            "restrictions": "no",
            "detail_level": "conceptual",
            "motors": 4,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    return orc


def _drive_to_battery_wizard(orc: JarvisOrchestrator, llm: _RefuseLLM) -> None:
    """Real turns: architecture A, motor+propeller catalog-bound, ESC
    declared -> energy block auto-opens with battery as the active gap."""
    ps = orc.state_manager.load_active_project(orc.workspace_manager)
    orc.system_definition_session.start("dron", ps)
    orc.system_definition_session.answer("A")
    orc.handle_user_text("definir propulsion", llm)
    orc.handle_user_text("ayúdame a elegir", llm)
    orc.handle_user_text("1", llm)
    orc.handle_user_text("ayúdame a elegir", llm)
    orc.handle_user_text("1", llm)
    orc.handle_user_text("ESC 30A", llm)


# ── Bat-7 #1/#2/#3 — help-choose -> pick -> real Wh/mass/cells -> autonomy ──


def test_battery_help_choose_lists_catalog_including_seed_sku(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()
    _drive_to_battery_wizard(orc, llm)

    result = orc.handle_user_text("ayúdame a elegir", llm)
    suggestions = result.get("battery_suggestions") or []
    assert suggestions, "battery_suggestions empty"
    assert any(s["name"] == "lipo_6s_10000mah" for s in suggestions)


def test_battery_pick_binds_catalog_ref_and_real_energy_mass_cells(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()
    _drive_to_battery_wizard(orc, llm)

    result = orc.handle_user_text("ayúdame a elegir", llm)
    suggestions = result["battery_suggestions"]
    idx = next(s["idx"] for s in suggestions if s["name"] == "lipo_6s_10000mah")
    pick = orc.handle_user_text(str(idx), llm)
    assert pick["status"] == "ok"

    state = orc.state_manager.load_active_project(orc.workspace_manager)
    battery = state.design_properties.components["battery"]
    assert battery.catalog_ref == CatalogRef(family="battery", sku="lipo_6s_10000mah")
    seed = default_library.get_battery("lipo_6s_10000mah")
    assert state.current_parameters["battery_capacity_wh"] == seed.energy_wh == 222.0
    assert state.current_parameters["battery_mass_kg"] == pytest.approx(seed.mass_g / 1000.0)
    assert state.current_parameters["battery_cell_count"] == seed.cells == 6


def test_battery_pick_does_not_regress_already_resolved_propulsion_op(tmp_path):
    """A battery-only pick must never silently change motors'
    propulsion_resolution/per_motor_max_thrust_n. Verified during
    implementation (report §4 point 3): re-invoking set_motor_component
    after a battery bind can actually DOWNGRADE an exact_operating_point
    resolution to fallback_operating_point when the real battery voltage
    falls outside the curated exact rows' tolerance — this is exactly why
    _apply_component_battery_catalog_pick deliberately does not re-call
    motor/propeller writers (unlike the propeller pick's own ★5 re-call)."""
    import json

    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()
    _drive_to_battery_wizard(orc, llm)

    before = orc.state_manager.load_active_project(orc.workspace_manager)
    res_before = json.loads(before.current_parameters["propulsion_resolution"])
    thrust_before = before.current_parameters.get("per_motor_max_thrust_n")

    result = orc.handle_user_text("ayúdame a elegir", llm)
    idx = next(s["idx"] for s in result["battery_suggestions"] if s["name"] == "lipo_6s_10000mah")
    orc.handle_user_text(str(idx), llm)

    after = orc.state_manager.load_active_project(orc.workspace_manager)
    res_after = json.loads(after.current_parameters["propulsion_resolution"])
    assert res_after["resolution_type"] == res_before["resolution_type"]
    assert res_after["thrust_n"] == res_before["thrust_n"]
    assert after.current_parameters.get("per_motor_max_thrust_n") == thrust_before


def test_autonomy_min_reflects_real_sku_wh_after_calcular(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()
    _drive_to_battery_wizard(orc, llm)

    result = orc.handle_user_text("ayúdame a elegir", llm)
    idx = next(s["idx"] for s in result["battery_suggestions"] if s["name"] == "lipo_6s_10000mah")
    orc.handle_user_text(str(idx), llm)

    calc = orc.handle_user_text("calcular", llm)
    assert calc["status"] == "ok"
    state = orc.state_manager.load_active_project(orc.workspace_manager)
    autonomy = state.latest_results["calculations"]["autonomy_min"]
    assert autonomy is not None and autonomy > 5.0, (
        f"autonomy_min={autonomy} looks like a 6Wh-class collapse, not 222 Wh"
    )


# ── Bat-7 #4/#5/#6 — IDLE dispatch precedence ───────────────────────────────


def test_idle_help_choose_offers_battery_once_propulsion_bound(tmp_path):
    """Bat-3 IDLE fallback: motor and propeller both catalog-bound (nothing
    left to offer there) -> battery is the one that wants catalog help."""
    orc = _fresh_orchestrator(tmp_path)
    state = orc.state_manager.load_active_project(orc.workspace_manager)

    motor_spec = bind_motor_from_catalog({
        "name": "emax_rs2205s_2300",
        "max_watts": default_library.get_motor("emax_rs2205s_2300").max_watts,
        "thrust_n": default_library.get_motor("emax_rs2205s_2300").thrust_n,
        "kv_rating": default_library.get_motor("emax_rs2205s_2300").kv_rating,
        "weight_g": default_library.get_motor("emax_rs2205s_2300").weight_g,
    })
    state = set_motor_component(
        state, motor_spec, default_library.get_motor("emax_rs2205s_2300").max_watts,
    )

    propeller_spec = ComponentSpec(
        name="hq_5045_bn", component_type="propulsion_passive", suggested_key="propellers",
        completeness="high", source="declared",
        properties={"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")},
        catalog_ref=CatalogRef(family="propeller", sku="hq_5045_bn"),
    )
    components = dict(state.design_properties.components)
    components["propellers"] = propeller_spec
    dp = state.design_properties.model_copy(update={"components": components})
    state = state.model_copy(update={"design_properties": dp})
    orc.workspace_manager.save_state(state)

    assist = orc._try_start_assisted_battery_help()
    assert assist is not None
    assert assist.get("battery_suggestions")


def test_idle_battery_help_noop_when_already_catalog_bound(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    state = orc.state_manager.load_active_project(orc.workspace_manager)

    battery_spec = bind_battery_from_catalog("lipo_4s_5000mah")
    state = set_battery_component(
        state, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    orc.workspace_manager.save_state(state)

    assert orc._try_start_assisted_battery_help() is None


def test_motor_help_choose_wins_over_battery_when_both_incomplete(tmp_path):
    """Existing Continuity precedent (Prop-5/★6 B) — motor must not be
    starved by a new battery branch inserted after it in the fallback chain."""
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()
    result = orc.handle_user_text("ayúdame a elegir", llm)
    assert result.get("motor_suggestions"), (
        f"expected motor picker to win when nothing is bound yet, got action={result.get('action')}"
    )
    assert not result.get("battery_suggestions")


# ── Bat-7 #7/#8 — G27 ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw_user_input,raw_value",
    [
        ("aumentar bateria a LiPo 6S 10000mAh", "6S 10000mAh"),
        ("aumentar bateria a LiPo 6S 10000mAh", "6"),  # LLM already mangled valor to bare "6"
        ("cambia la bateria a 6s 10000 mah", None),
    ],
)
def test_g27_6s_10000mah_never_yields_6wh(raw_user_input, raw_value):
    adapter = SemanticIntentAdapter()
    params = {"variable": "battery_capacity_wh", "operacion": "aumentar", "confidence": 0.9}
    if raw_value is not None:
        params["valor"] = raw_value
    result = adapter.adapt({
        "action": "iterate",
        "parameters": params,
        "raw_user_input": raw_user_input,
    })
    assert result is not None
    assert result.value != "6.0" and result.value != "6"
    if result.value is not None:
        assert float(result.value) == pytest.approx(222.0)


def test_g27_bare_cell_count_without_capacity_is_refused_not_guessed():
    """No mAh alongside '6S' -> Wh cannot be honestly computed -> value must
    be suppressed (wizard re-asks), never fall back to the naive digit grab
    that would read '6' as Wh."""
    adapter = SemanticIntentAdapter()
    result = adapter.adapt({
        "action": "iterate",
        "parameters": {
            "variable": "battery_capacity_wh", "operacion": "aumentar",
            "valor": "6S", "confidence": 0.9,
        },
        "raw_user_input": "pon la bateria a 6S",
    })
    assert result is not None
    assert result.value is None


def test_g27_post_bind_adapter_is_stateless_never_touches_catalog_ref(tmp_path):
    """The adapter is a pure function over the LLM output dict — it has no
    project_state access and therefore cannot clear a bound catalog_ref by
    itself. Confirmed here: adapting the G27 phrase against a project that
    already has a catalog-bound battery leaves the on-disk catalog_ref
    completely untouched, and still resolves to the correct 222 Wh (or a
    refusal) rather than corrupting it to 6.0."""
    orc = _fresh_orchestrator(tmp_path)
    state = orc.state_manager.load_active_project(orc.workspace_manager)
    battery_spec = bind_battery_from_catalog("lipo_6s_10000mah")
    state = set_battery_component(
        state, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    orc.workspace_manager.save_state(state)
    before = orc.state_manager.load_active_project(orc.workspace_manager)

    adapter = SemanticIntentAdapter()
    result = adapter.adapt({
        "action": "iterate",
        "parameters": {
            "variable": "battery_capacity_wh", "operacion": "aumentar",
            "valor": "6S 10000mAh", "confidence": 0.9,
        },
        "raw_user_input": "aumentar bateria a LiPo 6S 10000mAh",
    })
    assert result is not None and result.value is not None
    assert float(result.value) == pytest.approx(222.0)

    after = orc.state_manager.load_active_project(orc.workspace_manager)
    assert after.design_properties.components["battery"].catalog_ref == before.design_properties.components["battery"].catalog_ref
    assert after.current_parameters == before.current_parameters


def test_g27_generic_parse_value_unchanged_for_non_battery_variables():
    """★5 (locked): the G27 fix is battery_capacity_wh-only — a non-battery
    numeric variable containing an 'S'-shaped token must keep the original
    first-number regex behavior unchanged."""
    adapter = SemanticIntentAdapter()
    result = adapter.adapt({
        "action": "iterate",
        "parameters": {
            "variable": "motor_power_w", "operacion": "aumentar",
            "valor": "6S 400W", "confidence": 0.9,
        },
        "raw_user_input": "aumenta la potencia a 6S 400W",
    })
    assert result is not None
    assert result.value == "6"
