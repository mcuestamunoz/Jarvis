"""CLI catalog-assist T1+2 — named G22 second pass (drop KV + prop inch).

implementation_contract_cli_catalog_assist_t1_plus_2.md

Reuses find_motors_for_requirements. Does not change
build_motor_catalog_suggestions (G22 empty-strict stays empty).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jarvis.core.engineering_readiness import bound_motor_sku_is_underspec
from jarvis.core.motor_catalog_assist import (
    build_motor_catalog_suggestions,
    build_underspec_motor_offer,
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


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "T1+2 catalog-assist unit",
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


def test_underspec_offer_names_t1_and_relaxed_with_frankenstein_warning(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is True

    result = o._try_start_assisted_motor_help()
    assert result is not None
    message = result.get("message", "")
    assert "Filtros relajados" in message
    assert "sunnysky_r2205_2500" in message
    assert "no es un combo motor+hélice+batería" in message
    assert "Elegir no garantiza sim PASS" in message
    assert "CERRADO" not in message
    assert "Diseño validado" not in message
    mismatch_lines = [
        line for line in message.splitlines()
        if "hélice vinculada puede no encajar" in line
    ]
    assert mismatch_lines, "relaxed frankenstein candidates must carry the hélice warning"
    eco_lines = [line for line in message.splitlines() if "emax_eco_ii_2207_1700" in line]
    for line in eco_lines:
        assert "hélice vinculada puede no encajar" not in line
    assert "5″ family" not in message and "5\" family" not in message


def test_covering_sku_has_no_relax_header(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2205_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert bound_motor_sku_is_underspec(ps) is False

    result = o._try_start_assisted_motor_help()
    if result is not None:
        assert "Filtros relajados" not in result.get("message", "")
        assert not (
            result.get("action") == "component_description_prompt"
            and o.state_manager.get_runtime_session().pending_missing_params == ["motors"]
        )


def test_g22_default_search_still_empty_on_strict_miss():
    project_state = SimpleNamespace(
        current_parameters={"propeller_diameter_in": 10.0, "motor_count": 4},
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
    assert build_motor_catalog_suggestions(project_state) == []


def test_pick_mismatch_does_not_unbind_propeller(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())
    o._try_start_assisted_motor_help()

    suggestions = o.state_manager.get_runtime_session().motor_suggestions or []
    mismatch = next(s for s in suggestions if s.get("prop_mismatch"))
    result = o._apply_component_motor_catalog_pick(mismatch, ["motors"])
    assert "redefine propellers" in result.get("message", "")

    ps = o.state_manager.load_active_project(o.workspace_manager)
    prop = ps.design_properties.components["propellers"]
    assert prop.catalog_ref is not None
    assert prop.catalog_ref.sku == "gf_5045x3"
    assert ps.design_properties.components["motors"].catalog_ref.sku == mismatch["name"]


def test_continuity_underspec_names_relaxed_filters(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_combo(o, motor_sku="sunnysky_r2305_2500", motor_count=2)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())
    ps = o.state_manager.load_active_project(o.workspace_manager)

    offer = build_underspec_motor_offer(ps)
    assert any(s.get("relaxed") for s in offer)

    cont = build_project_continuity(
        project_state=ps,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 15.04},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=(
            "El motor vinculado (sunnysky_r2305_2500) ya no cubre el hueco de diseño "
            "(empuje ≥ 15.0 N/motor, ~2500KV, hélice ~5\")."
        ),
        motor_catalog_matches=[{"name": "sunnysky_r2205_2500", "thrust_n": 12.5525}],
    )
    step = cont["next_useful_step"]
    assert "Filtros relajados" in step
    assert "ayúdame a elegir" in step
    assert "sunnysky_r2205_2500" in step
    assert "CERRADO" not in step
    assert "no garantiza sim PASS" in step
