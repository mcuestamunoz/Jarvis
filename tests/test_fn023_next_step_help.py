"""FN-023 — Generic next-step help routes to Continuity/project_status.

Root cause: intent_resolver._resolve_strong_action_intent checks
ANALYZE_PATTERNS' bare `\\bayudame\\b` before _looks_like_status_query ever
runs, so "ayúdame con el siguiente paso" resolved to "analyze" → LLM, which
would invent an unrelated gap (e.g. battery_capacity_wh) instead of reading
project state. STATUS_PATTERNS already covers "siguiente paso" but only after
strong_action_intent returns None — GUIDANCE_PATTERNS (checked before
ANALYZE) did not cover the "ayudame + siguiente paso" phrasing.

Fix: three new GUIDANCE_PATTERNS entries route these phrases to
"project_status", which _handle_project_status() already answers via
build_startup_context()'s Continuity block — 0 LLM, no new recommender. Not
propeller/battery-specific: two different fixtures below (propulsion vs
structure gap) prove the answer follows whatever the real next gap is.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue


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


def _new_project(tmp_path: Path) -> JarvisOrchestrator:
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
    return orch


def _project_propulsion_pending(tmp_path: Path) -> JarvisOrchestrator:
    """Motors declared + physics params set — propellers is the real
    remaining gap in the propulsion block."""
    orch = _new_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = _comp("motors", "propulsion_active",
        motor_count=PropertyValue(value=4), kv_rating=PropertyValue(value=920))
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {"motors": motors},
    })
    ps2 = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {
            **(ps.current_parameters or {}), "motor_count": 4, "per_motor_max_thrust_n": 3.0,
        },
    })
    orch.workspace_manager.save_state(ps2)
    return orch


def _project_structure_pending(tmp_path: Path) -> JarvisOrchestrator:
    """Propulsion + energy fully resolved — frame (structure) is the real
    remaining gap, a different block entirely from the propeller probe."""
    orch = _new_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = _comp("motors", "propulsion_active",
        motor_count=PropertyValue(value=4), kv_rating=PropertyValue(value=920))
    propellers = _comp("propellers", "propulsion_passive",
        diameter_in=PropertyValue(value=10), pitch_in=PropertyValue(value=4.5))
    battery = _comp("battery", "energy", battery_capacity_wh=PropertyValue(value=74))
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {"motors": motors, "propellers": propellers, "battery": battery},
    })
    ps2 = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {
            **(ps.current_parameters or {}),
            "motor_count": 4, "per_motor_max_thrust_n": 3.0,
            "battery_capacity_wh": 74.0, "motor_power_w": 50.0,
        },
    })
    orch.workspace_manager.save_state(ps2)
    return orch


def _next_step(result: dict) -> str:
    ctx = result.get("startup_context") or {}
    return (ctx.get("continuity") or {}).get("next_useful_step") or ""


def _label(result: dict) -> str | None:
    ctx = result.get("startup_context") or {}
    return ctx.get("next_architecture_label")


# 1. Probe: propulsion/propellers gap ───────────────────────────────────────

def test_ayudame_siguiente_paso_routes_project_status_not_analyze(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)

    result = orch.handle_user_text("ayudame con el siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"
    assert result["status"] == "ok"
    assert _label(result) == "Propulsión (motores + hélices)"
    next_step = _next_step(result).lower()
    assert "battery_capacity_wh" not in next_step
    assert "propuls" in next_step or "componentes" in next_step


# 2. Same phrase, different pending gap — proves generic ───────────────────

def test_siguiente_paso_help_follows_different_pending_gap(tmp_path: Path):
    orch = _project_structure_pending(tmp_path)

    result = orch.handle_user_text("ayudame con el siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"
    assert _label(result) == "Estructura (frame)"
    next_step = _next_step(result).lower()
    assert "estructura" in next_step or "frame" in next_step
    assert "battery_capacity_wh" not in next_step


# 3. Bare "siguiente paso" — regression ─────────────────────────────────────

def test_bare_siguiente_paso_still_project_status(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)

    result = orch.handle_user_text("siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"


# 4. FN-015 help-define not stolen ──────────────────────────────────────────

def test_fn015_help_define_not_stolen(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)
    orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result.get("action") != "analyze"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


# 5. FN-011/014 declare path not stolen into bare status ───────────────────

def test_declare_block_help_not_stolen(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)

    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())

    assert result["action"] == "define_missing_params"
    assert result.get("pending") == ["propellers"]


# 6. Real analyze verb not stolen ───────────────────────────────────────────

def test_real_analyze_not_stolen(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)

    class _StubLLM:
        def analyze(self, **kwargs):
            return "análisis simulado"

        def interpret(self, *a, **k):
            raise AssertionError("interpret must not be called")

        def generate(self, *a, **k):
            raise AssertionError("generate must not be called")

    result = orch.handle_user_text("analiza el margen de seguridad", _StubLLM())

    assert result["action"] == "analyze"


# 7. FN-022 engineering intention not stolen ────────────────────────────────

def test_fn022_engineering_intent_not_stolen(tmp_path: Path):
    orch = _project_structure_pending(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    frame = _comp("frame", "structure",
        mass_kg=PropertyValue(value=0.5), material=PropertyValue(value="fibra"))
    fc = _comp("flight_controller", "control", model=PropertyValue(value="Pixhawk 4"))
    sensors = _comp("sensors", "control", gps_model=PropertyValue(value="M9N"))
    components = dict(ps.design_properties.components)
    components.update({"frame": frame, "flight_controller": fc, "sensors": sensors})
    dp = ps.design_properties.model_copy(update={"components": components})
    orch.workspace_manager.save_state(ps.model_copy(update={
        "design_properties": dp,
        "latest_results": {
            "simulation": {"status": "pass", "can_fly": True, "safety_margin_ratio": 1.4},
            "calculations": {},
        },
    }))

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result["action"] == "engineering_intent"


# 8. Mid DEFINE_MISSING — next-step help, no invented gap, no LLM ──────────

def test_define_missing_next_step_help_no_llm_wrong_gap(tmp_path: Path):
    orch = _project_propulsion_pending(tmp_path)
    orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS

    result = orch.handle_user_text("ayudame con el siguiente paso", _RefuseLLM())

    assert result["action"] == "project_status"
    next_step = _next_step(result).lower()
    assert "battery_capacity_wh" not in next_step
    assert "propuls" in next_step or "componentes" in next_step
    session_after = orch.state_manager.get_runtime_session()
    assert session_after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
