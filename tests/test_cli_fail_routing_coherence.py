"""CLI fail-routing coherence.

implementation_contract_cli_fail_routing_coherence.md

Walk (field note): after 'PVC 650g' with propeller diameter already known,
'ayúdame a elegir' re-asked for mass/material instead of the missing size
class. A FAIL simulation with an autonomy warning rendered a contradictory
"WARNING" line beside Continuity's honest "fail" situation. Autonomy-below
next step claimed "el empuje ya es PASS" even when thrust itself failed.
Architecture 4/4 suggested "puedes optimizar o simular" while the active
simulation was a real failure.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jarvis.adapters.cli.main import render_startup_context
from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
)
from jarvis.core.component_writers import (
    set_battery_component,
    set_frame_material,
    set_motor_component,
    set_propeller_component,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.project_continuity import build_project_continuity
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "autonomia 10 min",
    "payload_kg": 1.0,
    "restrictions": "autonomia 10 min",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    return o


def _build_walk_project(
    o: JarvisOrchestrator, *, motor_sku: str,
    battery_sku: str = "lipo_6s_6000mah", payload_kg: float = 1.0,
) -> None:
    """Field fixture: 4 motors, propeller D=5in, battery, frame class 5in,
    ESC + control, architecture 4/4.

    Catalog sourced-only purge B1 redirect: this fixture used to default to
    gemfan_5030 / lipo_4s_10000mah / a weak no-watts DROP motor at
    payload_kg=1.0 to naturally reach a thrust-fail state. Every KEEP motor
    is stronger (10-16.5N vs the old 7.5-8N), so callers needing a genuine
    thrust fail now pass a heavier ``payload_kg`` explicitly (see call
    sites below for the specific, empirically-verified values)."""
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": 4, "payload_kg": payload_kg},
        "parsed_constraints": {"autonomy_min": 10.0},
    })
    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    battery_spec = bind_battery_from_catalog(battery_sku)
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )
    ps = set_frame_material(ps, 0.65, "pvc", 5.0)

    esc = ComponentSpec(
        name="ESC 40A", suggested_key="esc", component_type="propulsion_active",
        completeness="high", properties={"current_a": PropertyValue(value=40.0, unit="A")},
    )
    fc = ComponentSpec(
        name="Pixhawk 4", suggested_key="flight_controller", component_type="control",
        completeness="high", properties={"model": PropertyValue(value="pixhawk_4")},
    )
    sensors = ComponentSpec(
        name="Here3", suggested_key="sensors", component_type="control",
        completeness="high", properties={"gps_model": PropertyValue(value="here3")},
    )
    components = dict(ps.design_properties.components)
    components["esc"] = esc
    components["flight_controller"] = fc
    components["sensors"] = sensors
    dp = ps.design_properties.model_copy(update={
        "components": components,
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
    })
    ps = ps.model_copy(update={"design_properties": dp})
    o.workspace_manager.save_state(ps)


# ── §2.1/§2.2/§2.3 — frame class prompt, not mass/material again ───────────


def test_frame_wizard_pvc_650g_asks_size_class_not_mass_material_on_save(tmp_path: Path):
    o = _fresh(tmp_path)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))  # D known
    o.workspace_manager.save_state(ps)

    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("PVC 650g", _RefuseLLM())
    assert result["status"] == "ok"
    message = result["message"]
    assert "clase en pulgadas" in message
    assert "Indica material y masa" not in message
    assert "define los parámetros que faltan" not in message


def test_frame_wizard_unrecognized_reply_asks_size_class_from_persisted_state(tmp_path: Path):
    """Structure Catalog Foundation IC-3 note: this test used to send
    'ayúdame a elegir' as its follow-up phrase, but that phrase now
    legitimately opens the frame catalog for a pending frame (IC-3's whole
    point) — see test_frame_wizard_ayudame_a_elegir_opens_frame_catalog
    below for that new, intended behavior. This test's actual subject was
    always "an unrecognized follow-up re-derives the missing-datum prompt
    from persisted state," so it now uses a neutral, non-catalog,
    non-affirmative phrase to keep testing exactly that."""
    o = _fresh(tmp_path)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    o.workspace_manager.save_state(ps)

    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)
    o.handle_user_text("PVC 650g", _RefuseLLM())

    result = o.handle_user_text("continuar", _RefuseLLM())
    message = result.get("message") or ""
    assert "clase en pulgadas" in message
    assert "Indica material y masa" not in message


def test_frame_wizard_ayudame_a_elegir_opens_frame_catalog(tmp_path: Path):
    """Structure Catalog Foundation IC-3: with frame pending and no
    catalog_ref yet, 'ayúdame a elegir' now opens the real curated frame
    catalog (IC-1 seed) instead of falling through to the generic
    missing-datum prompt."""
    o = _fresh(tmp_path)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    o.workspace_manager.save_state(ps)

    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)
    o.handle_user_text("PVC 650g", _RefuseLLM())

    result = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    message = result.get("message") or ""
    assert "Frames del catálogo" in message
    assert "clase en pulgadas" not in message


# ── §2.4/§2.6 — FAIL vs WARNING, no false thrust-PASS claim ─────────────────


def test_thrust_fail_autonomy_below_real_walk_no_false_pass_no_warning_line(tmp_path: Path):
    # Catalog sourced-only purge B1 redirect: emax_rs2205_2300 (weak,
    # no-watts DROP motor) reached this fail+autonomy-below state at
    # payload_kg=1.0. Every KEEP motor is stronger, so this uses a
    # watts-declaring KEEP motor (sunnysky_r2205_2500, needed so
    # autonomy_min is even computable) at a heavier, empirically-verified
    # payload that genuinely fails thrust while also missing the 10-min
    # restriction — real physics throughout, no injected state.
    o = _fresh(tmp_path)
    _build_walk_project(
        o, motor_sku="sunnysky_r2205_2500",
        battery_sku="tattu_2300mah_4s_75c_xt60", payload_kg=5.0,
    )
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    sim = ps.latest_results.get("simulation") or {}
    assert sim.get("status") == "fail"
    assert sim.get("can_fly") is False
    assert "autonomy_below_restriction" in (sim.get("warnings") or [])

    ctx = o.build_startup_context()
    cont = ctx.get("continuity") or {}
    next_step = cont.get("next_useful_step") or ""
    assert "el empuje ya es PASS" not in next_step

    rendered = render_startup_context(ctx)
    assert "Última simulación: WARNING" not in rendered
    assert "fail" in cont.get("situation", "")


def test_thrust_fail_autonomy_met_no_optimizar_cta(tmp_path: Path):
    """Catalog sourced-only purge B1 redirect: the prior fixture
    (sunnysky_r2305_2500, 220W/7.5N) reached "thrust fails but autonomy is
    comfortably met" at payload_kg=1.0 with a real KEEP-sized battery.
    Every KEEP motor is 10-16.5N and needs near-max-rated power to fail
    thrust at all — at that power draw, no KEEP battery (max 133.2 Wh)
    sustains 10+ minutes, so this exact combination is no longer reachable
    from real catalog hardware alone. The thrust-fail state itself is
    still 100% real physics (payload_kg=5.0, same as the sibling test
    above); only the warnings/autonomy_min fields — which is what this
    COPY/CTA-suppression test actually exercises, not the physics engine
    — are then set directly to represent "autonomy met" honestly, the
    same synthetic-SimulationResult pattern test_impl_c_catalog_aware_dse.py
    already uses for its own exploration-candidate fixtures."""
    o = _fresh(tmp_path)
    _build_walk_project(
        o, motor_sku="sunnysky_r2205_2500",
        battery_sku="tattu_2300mah_4s_75c_xt60", payload_kg=5.0,
    )
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    sim = dict(ps.latest_results.get("simulation") or {})
    assert sim.get("status") == "fail"  # real physics: thrust genuinely fails
    sim["warnings"] = []
    sim["autonomy_min"] = 15.0
    # derive_physical_requirements reads calculations["autonomy_min"] FIRST,
    # falling back to simulation's only when the calc one is None — both
    # must agree "autonomy met" for _autonomy_objective_undemonstrated to
    # see it that way.
    calc = dict(ps.latest_results.get("calculations") or {})
    calc["autonomy_min"] = 15.0
    ps = ps.model_copy(update={
        "latest_results": {**ps.latest_results, "simulation": sim, "calculations": calc},
    })
    o.workspace_manager.save_state(ps)

    ps = o.state_manager.load_active_project(o.workspace_manager)
    sim = ps.latest_results.get("simulation") or {}
    assert sim.get("status") == "fail"
    assert sim.get("can_fly") is False
    assert sim.get("warnings") == []

    ctx = o.build_startup_context()
    cont = ctx.get("continuity") or {}
    next_step = cont.get("next_useful_step") or ""
    assert "puedes optimizar o simular" not in next_step
    assert "el empuje ya es PASS" not in next_step
    assert "fail" in cont.get("situation", "")
    assert ctx.get("proactive_question") is None or (
        "puedes optimizar o simular" not in ctx["proactive_question"]
    )


# ── §2.4 regression — PASS thrust + autonomy below keeps the locked sentence ──


def _continuity_state(**kwargs):
    defaults = dict(
        latest_results={
            "simulation": {
                "status": "pass", "quality": "good", "safety_margin_ratio": 1.75,
                "can_fly": True, "warnings": ["autonomy_below_restriction"],
            },
            "calculations": {"autonomy_min": 5.0},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_pass_thrust_autonomy_below_still_says_empuje_ya_es_pass():
    """Regression: the original autonomy-below IC's locked sentence must
    stay verbatim when thrust genuinely passed (can_fly=True) — only the
    thrust-FAIL variants are new."""
    state = _continuity_state()
    cont = build_project_continuity(
        project_state=state,
        status_type="warning",
        status_reason="autonomy_below_restriction",
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question="Arquitectura completa (4/4) — puedes optimizar o simular.",
        suggested_action={"label": "Optimiza o itera el diseño.", "reason": "margen"},
        physical_requirements={
            "autonomy_target_min": 15.0, "current_autonomy_min": 5.0,
            "thrust_per_motor_needed_n": 4.30,
        },
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "empuje ya es PASS" in cont["next_useful_step"]
    assert cont["next_useful_why"] == "autonomy_below_restriction"


def test_thrust_fail_autonomy_below_names_both_never_claims_pass():
    """Same shape, can_fly=False — must switch to the new honest sentence,
    never the old 'empuje ya es PASS' one."""
    state = _continuity_state(
        latest_results={
            "simulation": {
                "status": "fail", "quality": "fail", "safety_margin_ratio": 0.9,
                "can_fly": False, "warnings": ["autonomy_below_restriction"],
            },
            "calculations": {"autonomy_min": 5.0},
        },
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="warning",
        status_reason="autonomy_below_restriction",
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question="Arquitectura completa (4/4) — puedes optimizar o simular.",
        suggested_action=None,
        physical_requirements={
            "autonomy_target_min": 15.0, "current_autonomy_min": 5.0,
            "thrust_per_motor_needed_n": 4.30,
        },
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "empuje ya es PASS" not in cont["next_useful_step"]
    assert "empuje" in cont["next_useful_step"]
    assert "autonomía" in cont["next_useful_step"]
    assert "puedes optimizar o simular" not in cont["next_useful_step"]
    assert "ayúdame a elegir" not in cont["next_useful_step"]


# ── §2.5 — _append_arch_progress_hint suppression beyond autonomy-only ─────


def test_append_arch_progress_hint_suppressed_on_thrust_fail_autonomy_met(tmp_path: Path):
    """Catalog sourced-only purge B1 redirect: see
    test_thrust_fail_autonomy_met_no_optimizar_cta's own docstring above —
    same real-thrust-fail-then-honest-autonomy-override pattern."""
    o = _fresh(tmp_path)
    _build_walk_project(
        o, motor_sku="sunnysky_r2205_2500",
        battery_sku="tattu_2300mah_4s_75c_xt60", payload_kg=5.0,
    )
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ps = o.state_manager.load_active_project(o.workspace_manager)
    sim = dict(ps.latest_results.get("simulation") or {})
    assert sim.get("status") == "fail"
    sim["warnings"] = []
    sim["autonomy_min"] = 15.0
    # derive_physical_requirements reads calculations["autonomy_min"] FIRST,
    # falling back to simulation's only when the calc one is None.
    calc = dict(ps.latest_results.get("calculations") or {})
    calc["autonomy_min"] = 15.0
    ps = ps.model_copy(update={
        "latest_results": {**ps.latest_results, "simulation": sim, "calculations": calc},
    })
    o.workspace_manager.save_state(ps)

    result = o._append_arch_progress_hint({"status": "ok", "message": "base"})
    assert "puedes optimizar o simular" not in result["message"]
    assert "Arquitectura completa" in result["message"]
