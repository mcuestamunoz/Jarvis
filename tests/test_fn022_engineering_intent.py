"""FN-022 — Engineering Intent → deterministic goal plan (IDLE gate).

Root cause: ITERATE_PATTERNS claims "aumentar"/"subir" before any goal layer,
and detect_goal's keyword tables omitted common intention words (e.g.
empuje/thrust) even though GOAL_STRATEGIES already own those levers. A bare
engineering intention with no numeric value ("Aumentar el empuje") opened the
iterate wizard (or fell to the LLM) instead of showing the existing
deterministic strategy plan.

Fix is generic: goal_planner.is_engineering_intention(text) -> goal_key | None
(detect_goal + a conservative "no digit present" guard) is wired once in
orchestrator's IDLE tail, before the iterate dispatch, for ANY of the four
existing goals — no thrust-only branch. "Aumentar el empuje" is used only as
one probe among several goals below, per the contract's explicit instruction
that field phrases are acceptance probes, not the design center.

Primary mapping decision (documented, not hidden in code): "aumentar
empuje"/"más thrust" maps to mejorar_estabilidad, because that goal's
strategies already lead with the thrust/margin lever
(per_motor_max_thrust_n / motors) — see goal_planner._GOAL_KEYWORDS.
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


def _closed_project(tmp_path: Path) -> JarvisOrchestrator:
    """Full architecture closed (all 4 blocks) — matches the FN-021 shape so
    the IDLE gate is actually reached (a fresh/incomplete project is
    correctly intercepted earlier by Bug54's own missing-params nudge,
    unrelated to this contract)."""
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


# 1. Probe: "Aumentar el empuje" → goal plan, not iterate ───────────────────

def test_aumentar_empuje_shows_goal_plan_not_iterate(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["status"] == "ok"
    assert result["goal_key"] == "mejorar_estabilidad"
    assert "Plan estratégico" in result["message"]
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE


# 2. Reducir masa/peso — already explore, must not regress ─────────────────

def test_reducir_masa_shows_goal_plan(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Reducir la masa", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] in ("engineering_intent", "explore_design_space")
    if result["action"] == "engineering_intent":
        assert result["goal_key"] == "reducir_masa"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE


# 3. Mejorar autonomía — already explore, must not regress ─────────────────

def test_mejorar_autonomia_shows_goal_plan(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("Mejorar la autonomia", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] in ("engineering_intent", "explore_design_space")
    if result["action"] == "engineering_intent":
        assert result["goal_key"] == "mejorar_autonomia"


# 4. Mejorar margen / estabilidad — goal or explore, coherent ──────────────

def test_mejorar_margen_or_estabilidad_goal_or_explore(tmp_path: Path):
    orch = _closed_project(tmp_path)

    for phrase in ("Mejorar el margen", "mejorar estabilidad"):
        result = orch.handle_user_text(phrase, _RefuseLLM())
        assert result["status"] == "ok"
        assert result["action"] in ("engineering_intent", "explore_design_space")
        assert result.get("action") != "component_description_prompt"


# 5. Numeric target value — iterate still owns the turn ─────────────────────

def test_numeric_iterate_not_stolen(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("sube el empuje a 15N", _RefuseLLM())

    assert result.get("action") != "engineering_intent"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("per_motor_max_thrust_n") == 15.0


def test_numeric_payload_iterate_not_stolen(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("aumentar payload a 3kg", _RefuseLLM())

    assert result.get("action") != "engineering_intent"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("payload_kg") == 3.0


# 6. Existing explore phrase — still DSE (regression) ───────────────────────

def test_existing_explore_phrase_still_dse(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("optimiza para estabilidad", _RefuseLLM())

    assert result["action"] == "explore_design_space"


# 7. Mid-acquisition — FN-022 does not intercept ────────────────────────────

def test_define_missing_session_not_intercepted_by_fn022(tmp_path: Path):
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
        motor_count=PropertyValue(value=4), kv_rating=PropertyValue(value=920))
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {"motors": motors},
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result.get("action") != "engineering_intent"
    session_after = orch.state_manager.get_runtime_session()
    assert session_after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


# ── H (FN-021 regression): session still IDLE after last arch gap ──────────

def test_fn021_arch_complete_still_idle(tmp_path: Path):
    orch = _closed_project(tmp_path)
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE
