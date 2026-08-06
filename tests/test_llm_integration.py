import json
from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.llm.llm_client import JarvisLLMInterface
from jarvis.utils.logger import StructuredLogger


class FakeLLMClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.seen_messages: list[list[dict[str, str]]] = []
        self.seen_json_modes: list[bool] = []

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        self.seen_messages.append(messages)
        self.seen_json_modes.append(json_mode)
        if not self.responses:
            raise RuntimeError("Sin respuestas fake para el LLM.")
        return self.responses.pop(0)


class TrackingLLMClient:
    def __init__(self, response: str) -> None:
        self.called = False
        self.response = response
        self.seen_json_modes: list[bool] = []

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        self.called = True
        self.seen_json_modes.append(json_mode)
        return self.response


def test_llm_interface_can_start_create_project_interactive(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    llm = JarvisLLMInterface(
        client=FakeLLMClient(
            ['{"action":"create_project","project_id":null,"parameters":{},"mode":null,"raw_user_input":null}']
        ),
        logger=StructuredLogger(root=tmp_path / "logs"),
    )

    result = orchestrator.handle_user_text("quiero diseñar un dron", llm)

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert result["step"] == 0


def test_idle_uses_local_intent_resolution_before_llm(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient([])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("drone", llm)

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert len(fake_client.seen_messages) == 0


def test_idle_falls_back_to_llm_when_local_resolution_has_no_match(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient(
        ['{"action":"create_project","project_id":null,"parameters":{},"mode":null,"raw_user_input":null}']
    )
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("haz algo útil con esto", llm)

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert len(fake_client.seen_messages) == 1


def test_llm_interface_degrades_partial_create_project_to_interactive(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    llm = JarvisLLMInterface(
        client=FakeLLMClient(
            [
                '{"action":"create_project","project_id":null,"parameters":{"type":"drone"},"mode":"interactive","raw_user_input":"quiero diseñar un dron"}'
            ]
        ),
        logger=StructuredLogger(root=tmp_path / "logs"),
    )

    result = orchestrator.handle_user_text("quiero diseñar un dron", llm)

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert result["step"] == 0
    assert len(llm.client.seen_messages) == 0


def test_llm_interface_respects_active_session_flow(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient(
        [
            '{"action":"create_project","project_id":null,"parameters":{},"mode":null,"raw_user_input":null}',
        ]
    )
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    start = orchestrator.handle_user_text("quiero diseñar un dron", llm)
    next_step = orchestrator.handle_user_text("dron", llm)

    assert start["status"] == "interactive"
    assert next_step["status"] == "interactive"
    assert next_step["step"] == 1
    assert len(fake_client.seen_messages) == 0


def test_active_session_bypasses_llm_for_user_answers(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient(
        ['{"action":"create_project","project_id":null,"parameters":{"type":"drone"},"mode":"interactive","raw_user_input":"quiero diseñar un dron"}']
    )
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    start = orchestrator.handle_user_text("quiero diseñar un dron", llm)
    next_step = orchestrator.handle_user_text("hacer volar un dron de 2kg", llm)

    assert start["status"] == "interactive"
    assert next_step["status"] == "interactive"
    assert next_step["step"] == 1
    assert len(fake_client.seen_messages) == 0


def test_llm_interface_returns_safe_fallback_and_logs_invalid_output(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    log_root = tmp_path / "logs"
    llm = JarvisLLMInterface(
        client=FakeLLMClient(["esto no es json"]),
        logger=StructuredLogger(root=log_root),
    )

    result = orchestrator.handle_user_text("hazlo mejor", llm)

    assert result["status"] == "error"
    assert result["error"] == "invalid_llm_output"
    log_files = sorted(log_root.glob("*.json"))
    assert log_files
    payload = json.loads(log_files[-1].read_text(encoding="utf-8"))
    assert payload["user_input"] == "hazlo mejor"
    assert payload["llm_raw_output"] == "esto no es json"
    assert payload["parsed_output"] is None
    assert payload["prompt_version"] == "v1"


def test_analyze_intent_uses_llm_analysis_response(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    fake_client = FakeLLMClient([
        "No esta modelada la resistencia estructural en esta version; el cambio es declarativo."
    ])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("como influye el material en la resistencia?", llm)

    assert result["status"] == "ok"
    assert result["action"] == "analyze"
    assert result["analyze_type"] == "explanation"
    assert "reasoning" in result
    assert "explanation" in result["reasoning"]
    assert "no esta modelada" in result["message"].lower()
    assert len(fake_client.seen_messages) == 1


def test_ambiguous_intent_starts_interactive_without_llm(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient([])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("dron", llm)

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert len(fake_client.seen_messages) == 0


def test_ambiguous_intent_with_active_project_routes_to_analyze(tmp_path):
    """When a project exists, 'ambiguous' input must NOT restart the wizard."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    # Create a project so there IS an active project
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    analyze_response = '{"action":"analyze","parameters":{},"mode":null,"raw_user_input":null}'
    fake_client = FakeLLMClient([analyze_response])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("dron", llm)

    # Should NOT enter the wizard for create_project_interactive
    assert result.get("mode") != "create_project_interactive"
    assert result.get("status") != "interactive" or result.get("mode") != "create_project_interactive"


def test_unknown_calls_llm(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    tracking_client = TrackingLLMClient(
        '{"action":"create_project","project_id":null,"parameters":{},"mode":null,"raw_user_input":null}'
    )
    llm = JarvisLLMInterface(client=tracking_client, logger=StructuredLogger(root=tmp_path / "logs"))

    orchestrator.handle_user_text("haz algo util con esto", llm)

    assert tracking_client.called is True


def test_question_does_not_trigger_iterate(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    fake_client = FakeLLMClient([
        "No hay modelo estructural de resistencia en esta version."
    ])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("como influye el peso", llm)

    assert result["action"] == "analyze"


def test_project_status_text_routes_to_project_status(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    fake_client = FakeLLMClient([])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("estado del proyecto", llm)

    # project_status uses build_startup_context — no LLM call
    assert result["status"] == "ok"
    assert result["action"] == "project_status"
    assert result["startup_context"]["has_project"] is True
    assert len(fake_client.seen_messages) == 0


def test_analyze_does_not_mutate_state(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    create_result = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    project_id = create_result["project_id"]
    state_before = orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager,
        project_id=project_id,
    ).model_dump()

    fake_client = FakeLLMClient([
        "No esta modelada la resistencia estructural en esta version."
    ])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))
    result = orchestrator.handle_user_text("como influye el material en la resistencia", llm)

    state_after = orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager,
        project_id=project_id,
    ).model_dump()

    assert result["action"] == "analyze"
    assert state_before == state_after


def test_analyze_uses_text_mode_json_mode_false(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    fake_client = FakeLLMClient(["Respuesta de analisis."])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("como influye el material en la resistencia", llm)

    assert result["action"] == "analyze"
    assert fake_client.seen_json_modes == [False]


def test_analyze_type_what_if(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    fake_client = FakeLLMClient(["Analisis what-if."])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("que pasa si aumento la carga util", llm)

    assert result["action"] == "analyze"
    assert result["analyze_type"] == "what_if"


def test_analyze_type_comparison(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    fake_client = FakeLLMClient(["Analisis comparativo."])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    result = orchestrator.handle_user_text("que material es mejor aluminio o fibra", llm)

    assert result["action"] == "analyze"
    assert result["analyze_type"] == "comparison"


# ── Conversation history tests ──────────────────────────────────────────────

def _create_project_params():
    return {
        "vehicle_type": "dron",
        "objective": "dron de prueba",
        "payload_kg": 2.0,
        "restrictions": "ninguna",
        "detail_level": "conceptual",
        "motors": 4,
        "per_motor_max_thrust_n": 15.0,
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
    }


def test_conversation_history_accumulates_after_analyze(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _create_project_params()})
    fake_client = FakeLLMClient([
        "Respuesta uno.",
        "Respuesta dos.",
    ])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    orchestrator.handle_user_text("como influye el material", llm)
    orchestrator.handle_user_text("como afecta el peso en este diseño", llm)

    history = orchestrator.state_manager.runtime_state.conversation_history
    assert len(history) == 4  # user + assistant × 2
    assert history[0].role == "user"
    assert history[0].content == "como influye el material"
    assert history[1].role == "assistant"
    assert history[2].role == "user"
    assert history[2].content == "como afecta el peso en este diseño"


def test_conversation_history_sent_to_llm_on_second_analyze(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _create_project_params()})
    fake_client = FakeLLMClient([
        "Primera respuesta.",
        "Segunda respuesta.",
    ])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    orchestrator.handle_user_text("como influye el material", llm)
    orchestrator.handle_user_text("que pasa si cambio la carga util", llm)

    # Second call: messages should include the previous turn as context
    second_call_messages = fake_client.seen_messages[1]
    roles = [m["role"] for m in second_call_messages]
    # system + user(turn1) + assistant(turn1) + user(current)
    assert roles.count("user") >= 2
    assert "assistant" in roles


def test_conversation_history_capped_at_max_turns(tmp_path):
    from jarvis.core.state_manager import MAX_HISTORY_TURNS
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _create_project_params()})
    responses = [f"Respuesta {i}." for i in range(10)]
    fake_client = FakeLLMClient(responses)
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    for i in range(10):
        orchestrator.handle_user_text(f"pregunta {i}", llm)

    history = orchestrator.state_manager.runtime_state.conversation_history
    assert len(history) <= MAX_HISTORY_TURNS


def test_conversation_history_not_populated_during_interactive_session(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _create_project_params()})
    fake_client = FakeLLMClient([])
    llm = JarvisLLMInterface(client=fake_client, logger=StructuredLogger(root=tmp_path / "logs"))

    # Start an interactive iterate session (no LLM needed)
    orchestrator.handle_user_text("define componentes", llm)

    history = orchestrator.state_manager.runtime_state.conversation_history
    assert len(history) == 0


# ── _handle_global_commands ───────────────────────────────────────────────────

class _NeverCallLLM:
    """Stub that fails loudly if any LLM method is invoked."""
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM must NOT be called for global commands")
    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM must NOT be called for global commands")


def test_escape_cancels_create_project_interactive_session(tmp_path):
    """cancelar during an active wizard returns global_command cancelled and clears session."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": {}})
    assert orchestrator.state_manager.runtime_state.session.mode.value == "create_project_interactive"

    result = orchestrator.handle_user_text("cancelar", _NeverCallLLM())

    assert result["status"] == "cancelled"
    assert result["action"] == "global_command"
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"


def test_escape_cancels_iterate_interactive_session(tmp_path):
    """cancelar during ITERATE_INTERACTIVE clears session without going through the handler."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _create_project_params()})
    orchestrator.handle({
        "action": "iterate",
        "parameters": {"objetivo": "peso", "operacion": "reducir"},
    })
    assert orchestrator.state_manager.runtime_state.session.mode.value == "iterate_interactive"

    result = orchestrator.handle_user_text("cancelar", _NeverCallLLM())

    assert result["status"] == "cancelled"
    assert result["action"] == "global_command"
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"


def test_escape_cancels_define_missing_params_session(tmp_path):
    """abort during DEFINE_MISSING_PARAMETERS clears session from the global layer."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    # Put orchestrator directly into DEFINE_MISSING_PARAMETERS mode
    orchestrator.start_define_missing_params(
        ["motors", "per_motor_max_thrust_n"], reason="missing_transmission_parameters"
    )
    assert orchestrator.state_manager.runtime_state.session.mode.value == "define_missing_params"

    result = orchestrator.handle_user_text("abort", _NeverCallLLM())

    assert result["status"] == "cancelled"
    assert result["action"] == "global_command"
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"


def test_exit_word_cancels_active_session(tmp_path):
    """'exit' is in _ESCAPE_WORDS and must cancel an active session."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": {}})
    assert orchestrator.state_manager.runtime_state.session.mode.value == "create_project_interactive"

    result = orchestrator.handle_user_text("exit", _NeverCallLLM())

    assert result["status"] == "cancelled"
    assert result["action"] == "global_command"
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"


def test_all_escape_words_cancel_session(tmp_path):
    """Every word in _ESCAPE_WORDS produces a cancelled global_command."""
    for word in ("cancelar", "cancel", "salir", "abortar", "abort", "exit"):
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        orchestrator.handle({"action": "create_project", "parameters": {}})

        result = orchestrator.handle_user_text(word, _NeverCallLLM())

        assert result["status"] == "cancelled", f"Expected cancelled for '{word}'"
        assert result["action"] == "global_command", f"Expected global_command for '{word}'"
        assert orchestrator.state_manager.runtime_state.session.mode.value == "idle", (
            f"Session not cleared for '{word}'"
        )


def test_escape_in_idle_mode_returns_informative_message(tmp_path):
    """cancelar with no active session returns an informative message (no LLM call)."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"

    result = orchestrator.handle_user_text("cancelar", _NeverCallLLM())

    assert result.get("action") == "global_command"
    assert result.get("status") == "ok"
    assert result.get("message") == "No hay ninguna operación activa que cancelar."
    # Mode stays IDLE after the no-op
    assert orchestrator.state_manager.runtime_state.session.mode.value == "idle"


def test_n_shortcut_starts_create_project_wizard_without_llm(tmp_path):
    """'n' is in _NEW_PROJECT_WORDS and starts the wizard immediately, no LLM call."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    result = orchestrator.handle_user_text("n", _NeverCallLLM())

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert result["step"] == 0


def test_nuevo_shortcut_starts_create_project_wizard_without_llm(tmp_path):
    """'nuevo' is in _NEW_PROJECT_WORDS and starts the wizard immediately, no LLM call."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    result = orchestrator.handle_user_text("nuevo", _NeverCallLLM())

    assert result["status"] == "interactive"
    assert result["mode"] == "create_project_interactive"
    assert result["step"] == 0


def test_escape_message_is_informative(tmp_path):
    """The cancelled message tells the user what to do next."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": {}})

    result = orchestrator.handle_user_text("cancelar", _NeverCallLLM())

    assert "message" in result
    assert len(result["message"]) > 10  # Not empty / truncated
