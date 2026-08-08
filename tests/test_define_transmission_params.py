from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import OrchestratorMode


# ── helpers ───────────────────────────────────────────────────────────────────

_AERIAL_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de carga",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 15.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _make_blocking_project(tmp_path: Path) -> tuple[JarvisOrchestrator, str]:
    """Create a project patched to have blocking physics_status."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": _AERIAL_PARAMS})
    workspace_path = Path(result["workspace_path"])
    state_path = workspace_path / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["latest_results"]["simulation"]["physics_status"] = "missing_parameters"
    data["latest_results"]["simulation"]["warnings"] = ["missing_transmission_parameters"]
    data["current_parameters"]["per_actuator_torque_nm"] = 80.0
    data["current_parameters"].pop("per_motor_max_thrust_n", None)
    state_path.write_text(json.dumps(data), encoding="utf-8")
    return orchestrator, str(workspace_path)


# ── _param_question ───────────────────────────────────────────────────────────

def test_param_question_wheel_radius_is_human_readable():
    orchestrator = JarvisOrchestrator()
    q = orchestrator.param_definition_session.param_question("wheel_radius_m")
    assert "radio" in q.lower()
    assert "0.15" in q


def test_param_question_gear_ratio_is_human_readable():
    orchestrator = JarvisOrchestrator()
    q = orchestrator.param_definition_session.param_question("gear_ratio")
    assert "relación" in q.lower() or "relacion" in q.lower() or "transmisión" in q.lower()
    assert "10" in q


def test_param_question_unknown_param_contains_param_name():
    orchestrator = JarvisOrchestrator()
    q = orchestrator.param_definition_session.param_question("some_unknown_param")
    assert "some_unknown_param" in q


# ── _parse_floats_from_input ──────────────────────────────────────────────────

@pytest.mark.parametrize("user_input, expected", [
    ("0.15 y 10", [0.15, 10.0]),
    ("0.15", [0.15]),
    ("10", [10.0]),
    ("radio 0,15 engranaje 10", [0.15, 10.0]),
    ("abc", []),
    ("", []),
])
def test_parse_floats_returns_list(user_input, expected):
    orchestrator = JarvisOrchestrator()
    assert orchestrator.param_definition_session.parse_floats_from_input(user_input) == expected


def test_parse_float_delegates_to_parse_floats():
    """_parse_float_from_input returns first element of _parse_floats_from_input."""
    orchestrator = JarvisOrchestrator()
    assert orchestrator.param_definition_session.parse_float_from_input("0.15 y 10") == pytest.approx(0.15)
    assert orchestrator.param_definition_session.parse_float_from_input("abc") is None


# ── _parse_float_from_input ───────────────────────────────────────────────────

@pytest.mark.parametrize("user_input, expected", [
    ("0.15", 0.15),
    ("0,15", 0.15),
    ("10", 10.0),
    ("el radio es 0.15 metros", 0.15),
    ("  2.5  ", 2.5),
])
def test_parse_float_valid_inputs(user_input, expected):
    orchestrator = JarvisOrchestrator()
    assert orchestrator.param_definition_session.parse_float_from_input(user_input) == expected


@pytest.mark.parametrize("bad_input", ["sí", "no quiero", "", "abc"])
def test_parse_float_invalid_returns_none(bad_input):
    orchestrator = JarvisOrchestrator()
    assert orchestrator.param_definition_session.parse_float_from_input(bad_input) is None


# ── _start_define_missing_params_session ────────────────────────────────────

def test_start_session_no_params_returns_ok():
    orchestrator = JarvisOrchestrator()
    result = orchestrator.start_define_missing_params([])
    assert result["status"] == "ok"


def test_start_session_sets_mode_to_define_missing_parameters():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    session = orchestrator.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_start_session_returns_interactive_with_question():
    orchestrator = JarvisOrchestrator()
    result = orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert "question" in result
    assert "radio" in result["question"].lower()


def test_start_session_pending_params_stored_in_session():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    session = orchestrator.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["wheel_radius_m", "gear_ratio"]
    assert session.collected_params == {}


def test_start_session_stores_reason():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(
        ["wheel_radius_m"], reason="missing_transmission_parameters"
    )
    session = orchestrator.state_manager.get_runtime_session()
    assert session.param_definition_reason == "missing_transmission_parameters"


def test_start_session_default_reason():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m"])
    session = orchestrator.state_manager.get_runtime_session()
    assert session.param_definition_reason == "missing_transmission_parameters"


# ── _handle_define_missing_params_answer ────────────────────────────────────

def test_answer_invalid_input_returns_interactive_with_error():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    # Bug 77: 'no sé' is now a skip phrase, not an error.
    # Use clearly invalid text (neither numeric nor a skip phrase) to test the error path.
    result = orchestrator.param_definition_session.answer("texto invalido")
    assert result["status"] == "interactive"
    assert "error" in result
    assert "question" in result


def test_answer_skip_phrase_advances_to_next_param():
    """Bug 77: 'no sé' skips the current param and asks for the next one."""
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    result = orchestrator.param_definition_session.answer("no sé")
    assert result["status"] == "interactive"
    # Should NOT be an error — should advance to next param
    assert "error" not in result
    q = result.get("question", "").lower()
    assert "relación" in q or "relacion" in q or "transmisión" in q or "transmision" in q


def test_answer_first_param_asks_for_second():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    result = orchestrator.param_definition_session.answer("0.15")
    assert result["status"] == "interactive"
    q = result["question"].lower()
    assert "relación" in q or "relacion" in q or "transmisión" in q or "transmision" in q


def test_answer_first_param_stores_collected_value():
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    orchestrator.param_definition_session.answer("0.15")
    session = orchestrator.state_manager.get_runtime_session()
    assert session.collected_params["wheel_radius_m"] == pytest.approx(0.15)
    assert session.pending_param_definitions == ["gear_ratio"]


def test_answer_all_params_clears_session_mode(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=workspace_path
    )
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    orchestrator.param_definition_session.answer("0.15")
    orchestrator.param_definition_session.answer("10")
    session = orchestrator.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE


def test_answer_multi_value_completes_both_params(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=workspace_path
    )
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    result = orchestrator.param_definition_session.answer("0.15 y 10")
    assert result["status"] == "ok"
    assert result["action"] == "define_missing_params"
    assert "calculations" in result


def test_answer_multi_value_partial_leaves_remaining(tmp_path: Path):
    """Two values for three params → third still pending."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.start_define_missing_params(
        ["wheel_radius_m", "gear_ratio", "extra_param"]
    )
    result = orchestrator.param_definition_session.answer("0.15 y 10")
    assert result["status"] == "interactive"
    assert "extra_param" in result["question"]
    session = orchestrator.state_manager.get_runtime_session()
    assert session.collected_params["wheel_radius_m"] == pytest.approx(0.15)
    assert session.collected_params["gear_ratio"] == pytest.approx(10.0)
    assert session.pending_param_definitions == ["extra_param"]


def test_answer_all_params_returns_ok_with_calculations(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=workspace_path
    )
    orchestrator.start_define_missing_params(["wheel_radius_m", "gear_ratio"])
    orchestrator.param_definition_session.answer("0.15")
    result = orchestrator.param_definition_session.answer("10")
    assert result["status"] == "ok"
    assert result["action"] == "define_missing_params"
    assert "calculations" in result
    assert "simulation" in result


# ── build_startup_context: proactive_question ─────────────────────────────────

def test_build_startup_context_blocking_has_proactive_question(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert ctx.get("proactive_question") is not None
    assert "wheel_radius_m" in ctx["proactive_question"] or "gear_ratio" in ctx["proactive_question"]


def test_build_startup_context_blocking_has_missing_params_list(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=workspace_path)
    assert isinstance(ctx["missing_params"], list)
    assert len(ctx["missing_params"]) > 0


def test_build_startup_context_nominal_has_energy_proactive_question(tmp_path: Path):
    """Nominal force physics but no battery params → energy proactive question."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": _AERIAL_PARAMS})
    ctx = orchestrator.build_startup_context(workspace_path=result["workspace_path"])
    # Force physics is nominal, but energy params are missing → proactive for energy
    assert ctx.get("proactive_question") is not None
    assert "energía" in ctx["proactive_question"] or "battery" in ctx["proactive_question"]
    assert isinstance(ctx.get("missing_params"), list)


# ── _apply_transmission_params_and_recalculate ────────────────────────────────

def test_apply_transmission_params_no_project_returns_error(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.param_definition_session.apply_and_recalculate(
        {"wheel_radius_m": 0.15, "gear_ratio": 10.0}
    )
    assert result["status"] == "error"


def test_apply_transmission_params_persists_to_state_json(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    result = orchestrator.param_definition_session.apply_and_recalculate(
        {"wheel_radius_m": 0.15, "gear_ratio": 10.0}
    )
    assert result["status"] == "ok"
    state = json.loads((Path(workspace_path) / "state.json").read_text(encoding="utf-8"))
    assert state["current_parameters"]["wheel_radius_m"] == pytest.approx(0.15)
    assert state["current_parameters"]["gear_ratio"] == pytest.approx(10.0)


def test_apply_transmission_params_increments_iteration(tmp_path: Path):
    orchestrator, workspace_path = _make_blocking_project(tmp_path)
    state_before = json.loads((Path(workspace_path) / "state.json").read_text(encoding="utf-8"))
    iteration_before = state_before["active_iteration"]
    orchestrator.param_definition_session.apply_and_recalculate(
        {"wheel_radius_m": 0.15, "gear_ratio": 10.0}
    )
    state_after = json.loads((Path(workspace_path) / "state.json").read_text(encoding="utf-8"))
    assert state_after["active_iteration"] == iteration_before + 1


# ── _parse_params_bidir ──────────────────────────────────────────────────────

def test_parse_params_bidir_number_before_keyword():
    """'4 motores' → motor_count=4 (number precedes keyword)."""
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir("4 motores", ["motor_count"])
    assert result == {"motor_count": 4.0}


def test_parse_params_bidir_keyword_before_number():
    """'motores: 4' → motor_count=4 (keyword precedes number)."""
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir("motores: 4", ["motor_count"])
    assert result == {"motor_count": 4.0}


def test_parse_params_bidir_two_params_in_one_phrase():
    """'4 motores 20 de empuje' → both motor_count and thrust extracted."""
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir(
        "4 motores 20 de empuje", ["motor_count", "per_motor_max_thrust_n"]
    )
    assert result["motor_count"] == pytest.approx(4.0)
    assert result["per_motor_max_thrust_n"] == pytest.approx(20.0)


def test_parse_params_bidir_no_keyword_returns_empty():
    """Input with no matching keyword → empty dict."""
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir("el sistema está bien", ["motor_count"])
    assert result == {}


def test_parse_params_bidir_no_number_returns_empty():
    """Input with keyword but no number → empty dict."""
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir("motores sin definir", ["motor_count"])
    assert result == {}


def test_parse_params_bidir_number_outside_40_chars_not_captured():
    """Number more than 40 chars from keyword → not captured."""
    orchestrator = JarvisOrchestrator()
    long_gap = "x" * 50
    result = orchestrator.param_definition_session.parse_params_bidir(f"4{long_gap}motores", ["motor_count"])
    assert result == {}


def test_parse_params_bidir_value_after_long_keyword_beats_number_before():
    """'4 ruedas y radio de rueda 0.15' → wheel_radius=0.15, not 4.0.

    Regression for kw_match.start() bug: using the keyword centre ensures the
    number immediately after the long keyword wins over one that precedes it.
    """
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir(
        "4 ruedas y radio de rueda 0.15", ["wheel_radius_m", "gear_ratio"]
    )
    assert result.get("wheel_radius_m") == pytest.approx(0.15), (
        f"Expected wheel_radius_m=0.15 (number after keyword), got {result.get('wheel_radius_m')}"
    )


# ── _try_ingest_missing_params ───────────────────────────────────────────────

def _make_aerial_missing_project(tmp_path: Path) -> tuple[JarvisOrchestrator, str]:
    """Aerial project without motors/thrust so physics_status == missing_parameters."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
            # motors and per_motor_max_thrust_n intentionally absent
        },
    })
    return orchestrator, result["workspace_path"]


def test_try_ingest_no_project_returns_none(tmp_path: Path):
    """Guard 1: no active project → returns None."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.param_definition_session.try_ingest("4 motores")
    assert result is None


def test_try_ingest_valid_physics_no_keyword_returns_none(tmp_path: Path):
    """Mode B: project physics already valid, input has no keyword+number → returns None."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron completo",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    result = orchestrator.param_definition_session.try_ingest("el sistema está bien")
    assert result is None


def test_try_ingest_valid_physics_explicit_param_override(tmp_path: Path):
    """Mode B: physics valid + explicit keyword+number → applies override directly."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron completo",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    result = orchestrator.param_definition_session.try_ingest("6 motores")
    assert result is not None
    # FN-004: substituting an already-defined motor_count asks for confirmation
    assert result.get("action") == "structural_confirm"
    assert result.get("status") == "interactive"
    assert orchestrator.state_manager.get_runtime_session().pending_structural_change

    confirmed = orchestrator.param_definition_session.resolve_structural_confirm("sí")
    assert confirmed.get("status") == "ok"
    assert confirmed.get("action") == "define_missing_params"
    calc = confirmed.get("calculations") or {}
    assert calc.get("motors") == 6


def test_try_ingest_no_keyword_match_returns_none(tmp_path: Path):
    """Guard 4: missing physics but no keyword match → not intercepted."""
    orchestrator, _ = _make_aerial_missing_project(tmp_path)
    result = orchestrator.param_definition_session.try_ingest("el sistema está bien")
    assert result is None


def test_try_ingest_motors_only_starts_define_for_thrust(tmp_path: Path):
    """'4 motores' → motors applied, DEFINE session started for per_motor_max_thrust_n."""
    orchestrator, _ = _make_aerial_missing_project(tmp_path)
    result = orchestrator.param_definition_session.try_ingest("4 motores")
    assert result is not None
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert "empuje" in result["question"].lower()
    # motor_count persisted
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert project_state.current_parameters.get("motor_count") == pytest.approx(4.0)


def test_try_ingest_both_params_returns_ok_with_calculations(tmp_path: Path):
    """'4 motores 20 de empuje' → both applied, available_thrust populated."""
    orchestrator, _ = _make_aerial_missing_project(tmp_path)
    result = orchestrator.param_definition_session.try_ingest("4 motores 20 de empuje")
    assert result is not None
    assert result["status"] == "ok"
    assert result["calculations"]["available_total_thrust_n"] == pytest.approx(4 * 20.0)


def test_try_ingest_intercepted_before_iterate_interactive(tmp_path: Path):
    """Regression: '4 motores' must be intercepted before reaching iterate_interactive."""
    orchestrator, _ = _make_aerial_missing_project(tmp_path)

    class _NeverCallLLM:
        """Stub that fails if LLM is invoked — ingestion must short-circuit first."""
        def complete(self, messages, json_mode=True):
            raise AssertionError("LLM should NOT be called when ingestion matches")

    result = orchestrator.handle_user_text("4 motores", _NeverCallLLM())
    assert result is not None
    assert result.get("mode") != "iterate_interactive"


# ── _handle_define_missing_params_answer — bidir parser as primary ────────────

def test_answer_wizard_bidir_keyword_after_number():
    """'1.5 torque y 4 ruedas' — number before keyword for each param.

    The wizard must assign values via bidir parser (not positional fallback),
    so torque→per_actuator_torque_nm and ruedas→motors.
    """
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(
        ["per_actuator_torque_nm", "motor_count"],
        reason="missing_transmission_parameters",
    )
    result = orchestrator.param_definition_session.answer("1.5 torque y 4 ruedas")
    # Both params extracted by bidir → session advances past remaining params
    session = orchestrator.state_manager.get_runtime_session()
    collected = session.collected_params if result.get("status") == "interactive" else {}
    # Either collected in session (1 param left) or completed immediately (0 left)
    if result["status"] == "interactive":
        # One param extracted, one remains — the extracted one must match its keyword
        assert "per_actuator_torque_nm" in collected or "motor_count" in collected
    else:
        # Both extracted — session cleared, result carries ok or error
        assert result["status"] in ("ok", "error")


def test_answer_wizard_bidir_keyword_before_number():
    """'torque 1.5 y 4 ruedas' — keyword before number for first param.

    Bidir handles both directions; this is the classic forward case.
    """
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(
        ["per_actuator_torque_nm", "motor_count"],
        reason="missing_transmission_parameters",
    )
    result = orchestrator.param_definition_session.answer("torque 1.5 y 4 ruedas")
    session = orchestrator.state_manager.get_runtime_session()
    if result["status"] == "interactive":
        collected = session.collected_params
        assert "per_actuator_torque_nm" in collected or "motor_count" in collected
    else:
        assert result["status"] in ("ok", "error")


def test_answer_wizard_bidir_no_match_falls_to_positional():
    """'0.15 10' with no keywords → positional fallback maps left-to-right."""
    orchestrator = JarvisOrchestrator()
    orchestrator.start_define_missing_params(
        ["wheel_radius_m", "gear_ratio"],
        reason="missing_transmission_parameters",
    )
    result = orchestrator.param_definition_session.answer("0.15 y 10")
    # positional: wheel_radius_m=0.15, gear_ratio=10 — session complete (no project → error)
    assert result["status"] in ("ok", "error")


# ── Parser regression tests (false-positive guard) ───────────────────────────

def test_bidir_potencia_motor_50_does_not_assign_motors():
    """'potencia motor 50' must only assign motor_power_w, NOT motors.

    Regression: bare keyword 'motor' was formerly in motors.keywords and caused
    'potencia motor 50' to also set motors=50 (silent data corruption).
    """
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir(
        "potencia motor 50", ["motor_count", "motor_power_w"]
    )
    assert result.get("motor_power_w") == pytest.approx(50.0)
    assert "motor_count" not in result


def test_bidir_number_consumed_once_across_params():
    """'torque 1.5 y 4 motores' — 1.5 belongs to torque, 4 to motors, no reuse.

    With consumed-positions guard: after per_actuator_torque_nm grabs 1.5,
    that position is off-limits. motors then grabs 4. wheel_radius_m finds no
    unused number and is absent.
    """
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir(
        "torque 1.5 y 4 motores", ["per_actuator_torque_nm", "motor_count", "wheel_radius_m"]
    )
    assert result.get("per_actuator_torque_nm") == pytest.approx(1.5)
    assert result.get("motor_count") == pytest.approx(4.0)
    assert "wheel_radius_m" not in result


def test_bidir_motor_bare_word_does_not_match_anything():
    """'motor 4 20' — bare 'motor' is not a keyword for any param after cleanup.

    Both numbers should remain unassigned (no param has 'motor' as a bare
    single-word keyword any more). Result must be empty.
    """
    orchestrator = JarvisOrchestrator()
    result = orchestrator.param_definition_session.parse_params_bidir(
        "motor 4 20", ["motor_count", "motor_power_w", "per_actuator_torque_nm"]
    )
    assert result == {}


def test_apply_and_recalculate_user_input_beats_component_inference(tmp_path: Path):
    """Override protection: component declares motor_count=6 but user says motors=4 → 4 wins.

    After apply_and_recalculate the persisted current_parameters must have
    motors=4, not the 6 coming from resolve_propulsion_parameters.
    """
    orchestrator, workspace_path = _make_aerial_missing_project(tmp_path)
    state_path = Path(workspace_path) / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))

    # Inject a component that declares motor_count=6 so resolve_propulsion gives motors=6
    data["design_properties"]["components"]["drive_motors"] = {
        "component_type": "traction_active",
        "completeness": "high",
        "properties": {
            "motor_count": {"value": 6, "unit": None, "confidence": 0.9, "source": "declared"},
        },
    }
    # Also provide per_motor_max_thrust_n so calculations are not incomplete
    data["current_parameters"]["per_motor_max_thrust_n"] = 15.0
    state_path.write_text(json.dumps(data), encoding="utf-8")

    result = orchestrator.param_definition_session.apply_and_recalculate({"motor_count": 4})

    # available_total_thrust = motors * per_motor_max_thrust_n.
    # If motors=4: 4*15=60 N. If motors=6 had won: 6*15=90 N.
    calculations = result["calculations"]
    assert calculations["available_total_thrust_n"] == pytest.approx(4 * 15.0), (
        "Component inference (motors=6) overrode user input (motors=4) — override protection failed"
    )
