"""FN-021 — Session hygiene: architecture-complete must return to IDLE.

Root cause: on acquisition completion, when _next_pending_block() is None,
_set_pending_next_block() did a bare `return` — leaving mode=DEFINE_MISSING_
PARAMETERS with stale pending_missing_params/param_definition_reason. The
DEFINE_MISSING branch in _handle_user_text_inner runs before iterate, so any
later turn (regardless of what it's about) got answered with a leftover
component_description_prompt for whatever key happened to be pending last.

Fix is generic: it triggers on "no next architecture block" for ANY block
type (component/param/composite), not a specific block or field. The primary
proof below (test_last_architecture_gap_clears_to_idle /
test_non_final_block_still_sets_next_pending) uses a minimal single/two-block
fixture with no domain-specific branching. The field-evidence shape (control
block, "Aumentar el empuje") is used only as an acceptance probe, matching
the contract's explicit instruction that field phrases are probes, not the
design center.
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


# ── 1. Generic: single-block system, last (only) gap completes → IDLE ──────

def test_last_architecture_gap_clears_to_idle(tmp_path: Path):
    """No domain-specific branching: a single component-type block
    (structure/frame) is the entire architecture. Completing it is, by
    definition, completing the last gap."""
    orch = _new_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure"],
        "system_priority": ["structure"],
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))

    opened = orch.handle_user_text("ayúdame a declarar estructura", _RefuseLLM())
    assert opened["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS

    result = orch.handle_user_text("fibra de carbono 450g", _RefuseLLM())
    assert result["status"] == "ok"

    session_after = orch.state_manager.get_runtime_session()
    assert session_after.mode == OrchestratorMode.IDLE
    assert session_after.pending_param_definitions == []
    assert session_after.pending_missing_params == []
    assert session_after.param_definition_reason in ("", None)
    assert session_after.pending_define_missing is False


# ── 2. Generic: non-final block completion still chains to the next one ────

def test_non_final_block_still_sets_next_pending(tmp_path: Path):
    """Two-block system: completing the first block must still pre-load the
    second (Bug54/FN-011 chaining), not clear to IDLE — clearing is reserved
    for the case where _next_pending_block is genuinely None."""
    orch = _new_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure", "control"],
        "system_priority": ["structure", "control"],
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))

    orch.handle_user_text("ayúdame a declarar estructura", _RefuseLLM())
    result = orch.handle_user_text("fibra de carbono 450g", _RefuseLLM())
    assert result["status"] == "ok"

    session_after = orch.state_manager.get_runtime_session()
    # Not cleared — a real next block (control) exists.
    assert session_after.pending_define_missing is True
    assert session_after.pending_missing_params == ["flight_controller", "sensors"]
    assert session_after.pending_missing_reason == "missing_component_definition"


# ── 3. FN-016 cancel/atrás still clears to IDLE (regression smoke) ─────────

def test_atras_still_clears_to_idle(tmp_path: Path):
    orch = _new_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure", "control"],
        "system_priority": ["structure", "control"],
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    orch.handle_user_text("ayúdame a declarar estructura", _RefuseLLM())

    result = orch.handle_user_text("atrás", _RefuseLLM())

    assert result["status"] == "cancelled"
    assert orch.state_manager.get_runtime_session().mode == OrchestratorMode.IDLE


# ── 4. Acceptance probe (field evidence, not the design center) ────────────

def test_after_arch_complete_iterate_phrase_not_stale_component_prompt(tmp_path: Path):
    """4-block drone walk, control (component-type) is the last block —
    matches the field evidence exactly, but exercises the same generic
    _set_pending_next_block code path as test 1/2 above, not a control-
    specific branch in production code."""
    orch = _new_project(tmp_path)
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
    esc = _comp("esc", "propulsion_active", current_a=PropertyValue(value=30.0))  # ERF-2 ★5

    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {
            "motors": motors, "propellers": propellers, "battery": battery,
            "frame": frame, "flight_controller": flight_controller, "esc": esc,
        },
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

    orch.handle_user_text("ayúdame a declarar control", _RefuseLLM())
    complete = orch.handle_user_text("GPS M9N", _RefuseLLM())
    assert "Arquitectura completa" in complete["message"]

    session_after = orch.state_manager.get_runtime_session()
    assert session_after.mode == OrchestratorMode.IDLE

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())

    assert result.get("action") != "component_description_prompt"
    message_blob = f"{result.get('message') or ''} {result.get('question') or ''}"
    assert "controladora" not in message_blob.lower()
    # FN-021 landed this on iterate_interactive (the only alternative to the
    # stale component prompt at the time). FN-022 supersedes that with the
    # deterministic goal plan (action="engineering_intent") — still not a
    # zombie DEFINE_MISSING session, which is what this test actually
    # guards; accept either outcome so this stays a regression check for
    # FN-021's own concern, not a pin on FN-022's specific routing choice.
    assert result.get("mode") in ("iterate_interactive",) or result.get("status") in (
        "interactive", "ok"
    )
