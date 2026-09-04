"""CLI catalog-assist T1 (misfit re-offer) — orchestrator unit coverage.

implementation_contract_cli_catalog_assist_t1.md ·
investigation_report_cli_catalog_assist_misfit_propose.md

Reuses resolve_motor_catalog_surface + build_motor_catalog_suggestions
(no second search) to fix the stuck loop: a catalog-bound motor that no
longer covers current thrust must reopen the existing numbered G22 list
instead of dead-ending "ayúdame a elegir" into a bare estado reprint.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.engineering_readiness import bound_motor_sku_is_underspec
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "T1 catalog-assist unit",
    "payload_kg": 0.5,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _bind_combo(o: JarvisOrchestrator, *, motor_sku: str, motor_count: int = 2):
    from jarvis.core.catalog_bind import (
        bind_battery_from_catalog,
        bind_motor_from_catalog,
        bind_propeller_from_catalog,
    )
    from jarvis.core.component_writers import (
        set_battery_component,
        set_motor_component,
        set_propeller_component,
    )

    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = ps.model_copy(
        update={"current_parameters": {**ps.current_parameters, "motor_count": motor_count}}
    )
    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    battery_spec = bind_battery_from_catalog("lipo_6s_10000mah")
    ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
    o.workspace_manager.save_state(ps)


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return o


def test_idle_underspec_opens_component_motor_catalog(tmp_path: Path):
    """§2.2 — underspec: IDLE help-choose opens the COMPONENT motor catalog
    (not a bare estado reprint), via the existing _offer_component_motor_
    catalog bridge, no new search."""
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is True

    result = o._try_start_assisted_motor_help()

    assert result is not None
    assert result.get("action") == "component_description_prompt"
    assert "Candidatos del catálogo" in result.get("message", "") or "No tengo un motor" in result.get(
        "message", ""
    )
    session = o.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
    assert session.pending_missing_params == ["motors"]


def test_idle_covering_bound_sku_falls_through(tmp_path: Path):
    """§2.2 — G21 preserved: a bound SKU that still covers requirements at
    this thrust floor must fall through to propeller/battery help (or
    None), never reopen the motor picker."""
    o = _fresh(tmp_path)
    # sunnysky_r2205_2500: thrust_n=12.5525, design_space max 15.5 — covers a
    # light 2-motor / 0.5kg-payload requirement comfortably.
    _bind_combo(o, motor_sku="sunnysky_r2205_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is False

    result = o._try_start_assisted_motor_help()

    # None (fall through) is the historical G21 contract; if anything is
    # returned it must not be a motor re-bind prompt.
    if result is not None:
        assert not (
            result.get("action") == "component_description_prompt"
            and o.state_manager.get_runtime_session().pending_missing_params == ["motors"]
        )


def test_component_gate_reopens_motor_list_when_underspec_in_composite_wizard(tmp_path: Path):
    """§2.3 — composite ["motors","propellers"] wizard: motors_want_help
    must OR in bound_motor_sku_is_underspec so a drifted bound SKU still
    gets re-offered even though _wants_catalog_help alone reads any bound
    catalog_ref as "done"."""
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    session = o.state_manager.get_runtime_session()
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["motors", "propellers"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("ayúdame a elegir", _RefuseLLM())

    assert "Candidatos del catálogo" in result.get("message", "") or "No tengo un motor" in result.get(
        "message", ""
    )


def test_component_gate_covering_bound_sku_does_not_reopen_motor_list(tmp_path: Path):
    """§2.3 — composite wizard, bound SKU still covers: motors_want_help
    stays False on the motors leg (G21/G9-A intact); the wizard advances to
    propellers instead of re-showing the motor list."""
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2205_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is False

    session = o.state_manager.get_runtime_session()
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["motors", "propellers"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("ayúdame a elegir", _RefuseLLM())

    # Wizard must advance past motors, never re-show the motor list (the
    # SKU already covers requirements).
    session_after = o.state_manager.get_runtime_session()
    assert session_after.pending_missing_params != ["motors"]


def test_definir_motor_help_choose_lists_catalog_when_covering(tmp_path: Path):
    """G18 motors-only wizard: the user already asked to redefine motors.
    Help-choose must show the numbered catalog even if the bound SKU still
    covers thrust — the autonomia-15min reprint of the Acquisition Brief.
    IDLE covering + composite covering stay G21/T1 (tests above)."""
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=4)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is False

    opened = o.handle_user_text("definir motor", _RefuseLLM())
    assert opened.get("action") in ("define_missing_params", "component_description_prompt")
    session = o.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["motors"]

    result = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    message = result.get("message", "")
    assert "Candidatos del catálogo" in message or "Filtros relajados" in message
    assert "Describe los motores" not in message
    assert "4x 2306" not in message
    session_after = o.state_manager.get_runtime_session()
    assert session_after.motor_suggestions
