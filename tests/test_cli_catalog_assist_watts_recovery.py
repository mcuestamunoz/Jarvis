"""CLI catalog-assist watts recovery — bound SKU with no nameplate W.

implementation_contract_cli_catalog_assist_watts_recovery.md

When thrust still covers but the catalog motor has no max_watts and an
autonomy target cannot be evaluated, IDLE help-choose reopens G22 filtered
to motors that declare W. Covering SKUs that do declare W stay G21.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.engineering_readiness import (
    bound_motor_needs_watts_recovery,
    bound_motor_sku_is_underspec,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_continuity import build_project_continuity
from jarvis.knowledge.library import default_library


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


def _bind(o: JarvisOrchestrator, *, motor_sku: str, motor_count: int = 4, battery: str = "lipo_4s_5000mah"):
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
        update={
            "current_parameters": {**ps.current_parameters, "motor_count": motor_count},
            "parsed_constraints": {"autonomy_min": 15.0},
        }
    )
    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    battery_spec = bind_battery_from_catalog(battery)
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    o.workspace_manager.save_state(ps)


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    return o


def test_idle_emax_no_w_opens_watts_filtered_list(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind(o, motor_sku="emax_rs2205s_2300")
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is False
    assert bound_motor_needs_watts_recovery(ps) is True
    assert ps.latest_results["calculations"].get("autonomy_min") is None

    result = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    message = result.get("message", "")
    assert result.get("action") != "project_status"
    assert "Solo candidatos con W de placa" in message
    assert "sunnysky_r2305_2500" in message or "emax_rs2205_2300" in message
    assert "emax_rs2205s_2300" not in message
    assert "No inventes motor_power_w" not in message or "W de placa" in message
    suggestions = o.state_manager.get_runtime_session().motor_suggestions or []
    assert suggestions
    assert all(s.get("max_watts") is not None for s in suggestions)


def test_idle_r2305_with_watts_stays_g21(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind(o, motor_sku="sunnysky_r2305_2500")
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_needs_watts_recovery(ps) is False

    result = o._try_start_assisted_motor_help()
    if result is not None:
        assert not (
            result.get("action") == "component_description_prompt"
            and o.state_manager.get_runtime_session().pending_missing_params == ["motors"]
        )


def test_continuity_names_watts_recovery_not_only_ban(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind(o, motor_sku="emax_rs2205s_2300")
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())
    ps = o.state_manager.load_active_project(o.workspace_manager)

    cont = build_project_continuity(
        project_state=ps,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action={
            "label": "No declares motor_power_w a mano — este motor de catálogo no declara vatios",
            "reason": "Inventar W",
        },
        physical_requirements={"autonomy_target_min": 15.0},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[{"name": "emax_rs2205s_2300"}],
    )
    step = cont["next_useful_step"]
    assert "ayúdame a elegir" in step
    assert "no declara vatios" in step
    assert "Candidatos que sí declaran W" in step
    assert step != (
        "No declares motor_power_w a mano — este motor de catálogo no declara vatios"
    )
    assert "Inventar W" in cont["next_useful_why"]
