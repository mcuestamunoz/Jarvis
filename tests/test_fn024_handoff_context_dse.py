"""FN-024 (H1 + H2) — Operation-scoped Handoff Context: Plan → DSE (C-042).

Root cause (System Map C-042): a bare "explora opciones" after
_handle_engineering_intent showed a Goal Plan had no way to recover which
goal the plan was for — resolve_explore_goal(text) re-derives from scratch,
finds no domain keyword in the bare phrase, and _handle_explore fell to the
LLM. The CTA that _handle_engineering_intent prints promised 'explora
opciones' would work; it didn't (M-002, CTA honesty / H2).

Fix: a small, capability-scoped, project-scoped, runtime-only HandoffContext
(schemas.action_schema.HandoffContext) — never a sticky `last_engineering_goal`
string. Created/replaced on every successful _handle_engineering_intent call;
bound (never invented) by _handle_explore only when goal_key is None, the
context belongs to the CURRENT project, and its DSE capability is still
"active"; a successful bind+explore consumes the DSE capability only —
goal_key/levers/iterate_capability survive for a future H4 (lever preseed)
consumer. Never persisted (state_manager._PERSISTED_SESSION_FIELDS excludes
it, same tier as last_exploration_result).
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import _PERSISTED_SESSION_FIELDS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


class _StubLLM:
    def analyze(self, **kwargs):
        return "stub analyze"

    def interpret(self, *args, **kwargs):
        raise AssertionError("interpret must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("generate must not be called")


def _comp(key: str, ctype: str, **props) -> ComponentSpec:
    return ComponentSpec(
        name=key, component_type=ctype, suggested_key=key,
        completeness="high", source="declared", properties=props,
    )


def _closed_project(tmp_path: Path, objective: str = "transporte de carga") -> JarvisOrchestrator:
    """Full architecture closed (matches FN-022's own fixture shape) — reaches
    the IDLE tail where the engineering-intent gate and explore intent live."""
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


# T1 — plan creates an active handoff_context ──────────────────────────────

def test_plan_creates_active_handoff_context(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_estabilidad"
    session = orch.state_manager.get_runtime_session()
    hc = session.handoff_context
    assert hc is not None
    assert hc.goal_key == "mejorar_estabilidad"
    assert hc.dse_capability == "active"
    assert hc.iterate_capability == "active"
    assert hc.levers  # non-empty — the plan's own strategy levers
    assert hc.project_id == orch.state_manager.load_active_project(orch.workspace_manager).project_id


# T2 + T3 — bare "explora opciones" binds; DSE capability consumed only ────

def test_bare_explore_binds_context_and_consumes_dse_capability_only(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "mejorar_estabilidad"
    session = orch.state_manager.get_runtime_session()
    hc = session.handoff_context
    assert hc is not None
    assert hc.dse_capability == "consumed"
    assert hc.goal_key == "mejorar_estabilidad"
    assert hc.iterate_capability == "active"
    assert hc.levers  # still present — H4 will need these later


# T4 — second bare "explora opciones" does not silently re-bind ────────────

def test_second_bare_explore_after_consumed_does_not_rebind(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("Aumentar el empuje", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["status"] == "ok"
    assert "Ya exploré" in result["message"]
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.dse_capability == "consumed"


# T5 — explicit "optimiza para X" still works, context untouched ───────────

def test_explicit_explore_domain_still_works_context_untouched(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("Aumentar el empuje", _RefuseLLM())
    before = orch.state_manager.get_runtime_session().handoff_context.dse_capability
    assert before == "active"

    result = orch.handle_user_text("optimiza para estabilidad", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "mejorar_estabilidad"
    after = orch.state_manager.get_runtime_session().handoff_context.dse_capability
    assert after == "active"  # untouched — explicit goal_key path, "simplest" per contract §4.2


# T6 — project_status after plan does not clear context ────────────────────

def test_project_status_does_not_clear_handoff_context(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    result = orch.handle_user_text("siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context is not None
    assert session.handoff_context.goal_key == "mejorar_estabilidad"


# T7 — new engineering_intent replaces the whole context ───────────────────

def test_new_engineering_intent_replaces_context(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("Aumentar el empuje", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    consumed = orch.state_manager.get_runtime_session().handoff_context
    assert consumed.dse_capability == "consumed"

    result = orch.handle_user_text("aumentar la carga util", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "aumentar_payload"
    session = orch.state_manager.get_runtime_session()
    hc = session.handoff_context
    assert hc.goal_key == "aumentar_payload"
    assert hc.dse_capability == "active"  # fresh, not the stale consumed one


# T8 — project boundary: a context bound to a different project is inert ───

def test_handoff_context_inert_across_project_boundary(tmp_path: Path):
    tmp1 = tmp_path / "p1"
    tmp2 = tmp_path / "p2"
    tmp1.mkdir()
    tmp2.mkdir()
    orch1 = _closed_project(tmp1, objective="proyecto uno")
    orch1.handle_user_text("Aumentar el empuje", _RefuseLLM())
    stale_session = orch1.state_manager.get_runtime_session()
    assert stale_session.handoff_context is not None

    orch2 = _closed_project(tmp2, objective="proyecto dos")
    ps2 = orch2.state_manager.load_active_project(orch2.workspace_manager)
    assert stale_session.handoff_context.project_id != ps2.project_id
    # Inject the stale, other-project context directly into orch2's session —
    # simulates any path that could otherwise leak a context across projects.
    orch2.state_manager.set_runtime_session(stale_session)

    result = orch2.handle_user_text("explora opciones", _StubLLM())

    # No bindable context for THIS project → same honest fallback as if no
    # context existed at all (unchanged pre-FN-024 behavior), never a bind
    # to the wrong project's goal.
    assert result["action"] == "analyze"


def test_handoff_context_never_persisted(tmp_path: Path):
    assert "handoff_context" not in _PERSISTED_SESSION_FIELDS


# T9 — CTA honesty smoke: mentions 'explora opciones' only backed by a real,
# just-created active context (true by construction — see _handle_engineering_intent)

def test_cta_advertises_explore_backed_by_real_context(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert "explora opciones" in result["message"]
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context is not None
    assert session.handoff_context.dse_capability == "active"


# ── Regressions: FN-020/021/022/023 unaffected ──────────────────────────────

def test_fn021_arch_complete_still_idle(tmp_path: Path):
    from jarvis.schemas.action_schema import OrchestratorMode
    orch = _closed_project(tmp_path)
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE


def test_fn023_next_step_help_unaffected(tmp_path: Path):
    orch = _closed_project(tmp_path)
    result = orch.handle_user_text("ayudame con el siguiente paso", _RefuseLLM())
    assert result["action"] == "project_status"
