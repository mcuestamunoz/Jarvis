"""FN-025 (H3) — "ayúdame" + named engineering goal → Goal Plan (C-025/C-044).

Root cause: ANALYZE_PATTERNS' help-verb group (ayúdame/oriéntame/...) claims
the turn as intent="analyze" before the FN-022 engineering-intent gate ever
runs (that gate only fires for intent in {"iterate","unknown"}) — even though
goal_planner.is_engineering_intention already detects a real goal for these
exact phrases. Fix: when intent resolves to "analyze" via the help-verb group
specifically (never the real analytical-verb group — "analiza"/"evalúa"/
"revisa"/... always keeps its analyze routing), check
is_engineering_intention first. A detected goal routes to the same
_handle_engineering_intent (and hence the same C-105 HandoffContext create)
FN-022/024 already use — no second goal detector, no second handoff
transport. No detectable goal (bare "ayúdame") routes to project_status/
Continuity instead of inventing a target via the LLM.

FN-023's own GUIDANCE next-step patterns ("ayúdame con el siguiente paso")
are checked earlier in resolve_intent and never even reach this branch —
that precedence is preserved by construction, not a special case here.
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


def _closed_project(tmp_path: Path) -> JarvisOrchestrator:
    """Full architecture closed (matches FN-022/024's own fixture shape) —
    reaches the IDLE tail where intent resolution and the FN-025 gate live."""
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


# T1 — help + named goal → engineering_intent, 0 LLM ────────────────────────

def test_help_plus_goal_routes_to_engineering_intent(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_estabilidad"


# T2 — same call creates/replaces HandoffContext via existing C-105 ────────

def test_help_plus_goal_creates_handoff_context(tmp_path: Path):
    orch = _closed_project(tmp_path)

    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    session = orch.state_manager.get_runtime_session()
    hc = session.handoff_context
    assert hc is not None
    assert hc.goal_key == "mejorar_estabilidad"
    assert hc.dse_capability == "active"


# T3 — FN-023 next-step help unaffected ─────────────────────────────────────

def test_fn023_next_step_help_still_project_status(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame con el siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"


# T4 — bare "ayudame" (no goal) → project_status, never an invented goal ───

def test_bare_ayudame_routes_to_project_status_not_llm(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame", _RefuseLLM())

    assert result["action"] == "project_status"


# T5 — FN-022 bare engineering intention (no help verb) unchanged ──────────

def test_fn022_bare_intention_unchanged(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_estabilidad"


# T6 — FN-024 explora opciones bind still works after a help+goal plan ─────

def test_fn024_explore_bind_after_help_goal_plan(tmp_path: Path):
    orch = _closed_project(tmp_path)
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "mejorar_estabilidad"
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.dse_capability == "consumed"


# T7 — real analyze verbs without help+goal still reach analyze ────────────

def test_real_analyze_verb_still_reaches_analyze(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("analiza el margen de seguridad", _StubLLM())

    assert result["action"] == "analyze"


def test_analyze_verb_with_help_word_still_analyze(tmp_path: Path):
    """A phrase carrying BOTH a help word and a real analytical verb keeps
    its analyze routing — the verb wins, this gate never claims it."""
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame, analiza el margen de seguridad", _StubLLM())

    assert result["action"] == "analyze"


# T8 — a different goal_key via help+goal (generic, not stability-only) ────

def test_help_plus_different_goal_generic(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("ayudame a mejorar la autonomia", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_autonomia"


# ── Regression: H4/C-043 (iterate preseed) now implemented (FN-026) ────────

def test_iterate_lever_preseed_now_implemented(tmp_path: Path):
    """FN-026 (H4) closed C-043 — a named lever after a help+goal plan now
    preseeds 'variable' and skips step 1 ("¿Qué quieres modificar?"). This
    test used to pin the pre-FN-026 broken fallback (variable stayed None,
    missing_slots == ["variable"]); it now locks in the fixed outcome. See
    tests/test_fn026_lever_iterate_preseed.py for the full FN-026 suite."""
    orch = _closed_project(tmp_path)
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())

    orch.handle_user_text("incrementa safety_factor", _RefuseLLM())
    result = orch.handle_user_text("si", _RefuseLLM())

    assert result["iteration_draft"]["variable"] == "safety_factor"
    assert result["semantic_state"]["missing_slots"] == []
