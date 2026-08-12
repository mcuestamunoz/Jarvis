"""FN-026 (H4) — Goal Plan lever → Iterate wizard preseed (C-043).

Root cause (System Map C-043): once a Goal Plan names its levers
(GOAL_STRATEGIES[goal_key][*]["lever"]) and creates the active HandoffContext
(C-105), naming one of those levers still opened the iterate wizard from
scratch — step 1 always re-asked "¿Qué quieres modificar?" even though the
lever was already on the table.

Fix: jarvis.core.handoff_matching.match_plan_lever(user_input, handoff) is a
pure helper that resolves a user-referenced lever token to its canonical
iterate variable name, reusing the exact same normalize_alias /
_VARIABLE_NORMALIZATION / _fuzzy_normalize_variable / _is_valid_variable chain
iterate_interactive_session._apply_answer already uses at step 1 — no
parallel vocabulary. orchestrator._preseed_variable_from_handoff calls it
right before dispatching an "iterate" intent to self.handle(...), guarded on:
an active HandoffContext existing, handoff.iterate_capability == "active",
and handoff.project_id matching the currently loaded project. dse_capability
is never read or touched — H1's DSE consumer and H4's iterate consumer are
fully independent, per the Hybrid Operation-Scoped Context design.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


def _comp(key: str, ctype: str, **props) -> ComponentSpec:
    return ComponentSpec(
        name=key, component_type=ctype, suggested_key=key,
        completeness="high", source="declared", properties=props,
    )


def _closed_project(tmp_path: Path, objective: str = "transporte de carga") -> JarvisOrchestrator:
    """Full architecture closed (matches FN-024/025's own fixture shape) —
    reaches the IDLE tail where intent resolution and the ITERATE dispatch live."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": objective,
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
    battery = _comp("battery", "energy", battery_capacity_wh=PropertyValue(value=74))
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
            "simulation": {"status": "pass", "can_fly": True, "safety_margin_ratio": 1.4},
            "calculations": {},
        },
    })
    orch.workspace_manager.save_state(ps2)
    return orch


# T1 — plan → named lever → confirm → variable preseeded, step 1 skipped ────

def test_plan_lever_confirm_preseeds_variable(tmp_path: Path):
    orch = _closed_project(tmp_path)
    r0 = orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    assert r0["goal_key"] == "mejorar_estabilidad"

    r1 = orch.handle_user_text("incrementa safety_factor", _RefuseLLM())
    assert r1["status"] == "interactive"
    assert r1["step"] == 0
    assert r1["iteration_draft"]["variable"] == "safety_factor"

    r2 = orch.handle_user_text("si", _RefuseLLM())
    assert r2["step"] == 2  # step 1 ("¿Qué quieres modificar?") skipped
    assert r2["iteration_draft"]["variable"] == "safety_factor"
    assert r2.get("semantic_state", {}).get("missing_slots", []) == []


# T2 — no prior plan/context → still asks (honest no-op) ────────────────────

def test_no_context_still_asks(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("cambia safety_factor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["step"] == 0
    assert result["iteration_draft"]["variable"] is None


# T3 — valid iterate variable but NOT in the plan's levers → no preseed ─────

def test_valid_variable_outside_plan_levers_not_preseeded(tmp_path: Path):
    orch = _closed_project(tmp_path)
    # mejorar_estabilidad levers: "per_motor_max_thrust_n / motors", "safety_factor"
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    result = orch.handle_user_text("cambia material", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["step"] == 0
    assert result["iteration_draft"]["variable"] is None


# T4 — stale cross-project context → no preseed ─────────────────────────────

def test_cross_project_stale_context_not_preseeded(tmp_path: Path):
    tmp1 = tmp_path / "p1"
    tmp2 = tmp_path / "p2"
    tmp1.mkdir()
    tmp2.mkdir()
    orch1 = _closed_project(tmp1, objective="proyecto uno")
    orch1.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    stale_session = orch1.state_manager.get_runtime_session()
    assert stale_session.handoff_context is not None

    orch2 = _closed_project(tmp2, objective="proyecto dos")
    ps2 = orch2.state_manager.load_active_project(orch2.workspace_manager)
    assert stale_session.handoff_context.project_id != ps2.project_id
    orch2.state_manager.set_runtime_session(stale_session)

    result = orch2.handle_user_text("cambia safety_factor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["step"] == 0
    assert result["iteration_draft"]["variable"] is None


# T5 — preseed still works after DSE capability was consumed (independent) ──

def test_preseed_works_after_dse_consumed(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    explore = orch.handle_user_text("explora opciones", _RefuseLLM())
    assert explore["action"] == "explore_design_space"
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.dse_capability == "consumed"

    result = orch.handle_user_text("incrementa safety_factor", _RefuseLLM())

    assert result["iteration_draft"]["variable"] == "safety_factor"


# T6 — FN-025 help+goal path also feeds a lever preseed ─────────────────────

def test_help_plus_goal_then_lever_preseed(tmp_path: Path):
    orch = _closed_project(tmp_path)
    r0 = orch.handle_user_text("ayudame a aumentar la carga util", _RefuseLLM())
    assert r0["action"] == "engineering_intent"
    assert r0["goal_key"] == "aumentar_payload"

    result = orch.handle_user_text("cambia motors", _RefuseLLM())

    assert result["iteration_draft"]["variable"] == "motors"


# T7 — compound lever token matching, positive and negative ────────────────

def test_compound_lever_valid_sibling_token_preseeds(tmp_path: Path):
    orch = _closed_project(tmp_path)
    # aumentar_payload lever: "per_motor_max_thrust_n / motors"
    orch.handle_user_text("ayudame a aumentar la carga util", _RefuseLLM())

    result = orch.handle_user_text("cambia motors", _RefuseLLM())

    assert result["iteration_draft"]["variable"] == "motors"


def test_compound_lever_derived_token_not_preseeded(tmp_path: Path):
    orch = _closed_project(tmp_path)
    # mejorar_autonomia lever: "total_power_w / motors" — total_power_w is a
    # derived/computed quantity, not a settable PARAMETER_REQUIREMENTS entry.
    orch.handle_user_text("ayudame a mejorar la autonomia", _RefuseLLM())

    result = orch.handle_user_text("cambia total_power_w", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["step"] == 0
    assert result["iteration_draft"]["variable"] is None


# T8 — regressions: FN-022/023/024/025 smoke green ──────────────────────────

def test_fn022_bare_intention_unaffected(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_estabilidad"


def test_fn024_explore_bind_unaffected(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "mejorar_estabilidad"


def test_fn025_help_plus_goal_unaffected(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame a mejorar la autonomia", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_autonomia"


def test_iterate_without_active_context_unaffected(tmp_path: Path):
    """No HandoffContext at all — the ITERATE dispatch path itself (existing
    _semantic_preseed, manual variable keywords like "componentes") is
    completely untouched by this fix."""
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("definir componentes", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["iteration_draft"]["variable"] == "componentes"
