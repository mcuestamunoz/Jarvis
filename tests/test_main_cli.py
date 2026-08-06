import json
from urllib import error

import pytest

from jarvis.llm.ollama_client import OllamaClient
from jarvis.adapters.cli.main import render_response


class _FakeHTTPResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_ollama_client_extracts_message_content(monkeypatch):
    captured: dict[str, object] = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHTTPResponse('{"message":{"content":"{\\"action\\":\\"create_project\\",\\"project_id\\":null,\\"parameters\\":{},\\"mode\\":null,\\"raw_user_input\\":null}"}}')

    monkeypatch.setattr("jarvis.llm.ollama_client.request.urlopen", fake_urlopen)

    client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:14b")
    response = client.complete([{"role": "system", "content": "s"}, {"role": "user", "content": "u"}])

    assert '"action":"create_project"' in response
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["body"]["format"] == "json"
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"]["temperature"] == 0


def test_ollama_client_supports_text_mode_without_json_format(monkeypatch):
    captured: dict[str, object] = {}

    def fake_urlopen(http_request, timeout):
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeHTTPResponse('{"message":{"content":"Respuesta natural de analisis"}}')

    monkeypatch.setattr("jarvis.llm.ollama_client.request.urlopen", fake_urlopen)

    client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:14b")
    response = client.complete(
        [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
        json_mode=False,
    )

    assert response == "Respuesta natural de analisis"
    assert "format" not in captured["body"]


def test_ollama_client_raises_clear_error_on_connection_failure(monkeypatch):
    def fake_urlopen(http_request, timeout):
        raise error.URLError("connection refused")

    monkeypatch.setattr("jarvis.llm.ollama_client.request.urlopen", fake_urlopen)

    client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:14b")

    with pytest.raises(RuntimeError, match="No se pudo conectar con Ollama"):
        client.complete([{"role": "system", "content": "s"}, {"role": "user", "content": "u"}])


def test_render_response_formats_interactive_output():
    message = render_response(
        {
            "status": "interactive",
            "message": "Vamos a definir el proyecto paso a paso.",
            "question": "¿Qué sistema quieres diseñar?",
        }
    )

    assert "Vamos a definir el proyecto paso a paso." in message
    assert "¿Qué sistema quieres diseñar?" in message


def test_render_response_formats_suggestions():
    message = render_response(
        {
            "status": "ok",
            "action": "simulate",
            "project_id": "abc123",
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 1.9,
                "warnings": [],
            },
            "suggestions": [
                {
                    "type": "increase_payload",
                    "reason": "El margen de empuje actual permite explorar más carga útil.",
                    "expected_effect": "reduces margin",
                    "priority": 0.9,
                }
            ],
        }
    )

    assert "Sugerencias:" in message
    assert "Podrías aumentar la carga útil" in message


def test_render_response_includes_reasoning_sections():
    message = render_response(
        {
            "status": "ok",
            "action": "iterate",
            "project_id": "abc123",
            "message": "Propiedad del diseño definida.",
            "reasoning": {
                "explanation": "La definición declarativa aún no afecta el modelo físico.",
                "insights": ["Última definición: componentes: motores brushless."],
                "tradeoffs": ["Sin empuje por motor real, el modelo sigue aproximado."],
                "suggested_actions": [
                    {
                        "action": "iterate",
                        "label": "Completar especificación de motores",
                        "reason": "Faltan: empuje por motor o KV, número de motores.",
                    }
                ],
            },
        }
    )

    assert "Reasoning:" in message
    assert "Insights:" in message
    assert "Trade-offs:" in message
    assert "Siguientes pasos:" in message
    assert "Completar especificación de motores" in message


def test_render_response_formats_error():
    message = render_response({"status": "error", "message": "Proyecto no encontrado."})

    assert message == "Proyecto no encontrado."


def test_render_response_formats_cancelled():
    message = render_response(
        {"status": "cancelled", "action": "define_missing_params", "message": "Definición cancelada. Puedes retomar cuando quieras."}
    )

    assert "cancelada" in message.lower()


def test_render_response_formats_calculate_action():
    message = render_response(
        {
            "status": "ok",
            "action": "calculate",
            "project_id": "abc123",
            "calculations": {
                "total_mass_kg": 3.5,
                "weight_n": 34.3,
                "required_thrust_n": 41.2,
                "available_total_thrust_n": 60.0,
            },
        }
    )

    assert "calculate" in message
    assert "abc123" in message
    assert "masa_total" in message
    assert "60.0 N" in message


def test_render_response_formats_calculate_no_thrust():
    """When available_total_thrust_n is None it should render as 'sin definir'."""
    message = render_response(
        {
            "status": "ok",
            "action": "calculate",
            "project_id": "abc123",
            "calculations": {
                "total_mass_kg": 3.5,
                "weight_n": 34.3,
                "required_thrust_n": 41.2,
                "available_total_thrust_n": None,
            },
        }
    )

    assert "sin definir" in message


def test_render_response_formats_create_project_action():
    message = render_response(
        {
            "status": "ok",
            "action": "create_project",
            "project_id": "nuevo-proyecto-xyz",
            "message": "Proyecto creado correctamente.",
        }
    )

    assert "create_project" in message
    assert "nuevo-proyecto-xyz" in message
    assert "Proyecto creado correctamente." in message


def test_render_response_formats_global_command_message():
    message = render_response(
        {
            "status": "ok",
            "action": "global_command",
            "message": "No hay ninguna operación activa que cancelar.",
        }
    )

    assert "No hay ninguna operación activa" in message


def test_render_response_formats_simulation_missing_parameters():
    message = render_response(
        {
            "status": "ok",
            "action": "simulate",
            "project_id": "abc123",
            "simulation": {
                "physics_status": "missing_parameters",
                "status": "incomplete",
                "quality": "unknown",
                "safety_margin_ratio": 0.0,
                "warnings": ["missing_transmission_parameters"],
            },
        }
    )

    assert "incompleta" in message
    assert "missing_transmission_parameters" in message


def test_render_response_falls_back_to_json_for_unknown_shape():
    payload = {"status": "whatever", "data": 42}
    message = render_response(payload)

    assert '"status"' in message
    assert '"whatever"' in message


# ── Bug 33: improve_autonomy label ──────────────────────────────────────

def test_bug33_improve_autonomy_renders_in_spanish():
    """Bug 33: 'improve_autonomy' must render as 'mejorar la autonomía', not as raw key."""
    message = render_response(
        {
            "status": "ok",
            "action": "simulate",
            "project_id": "abc123",
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 1.5,
                "warnings": [],
            },
            "suggestions": [
                {
                    "type": "improve_autonomy",
                    "reason": "Margen de empuje disponible.",
                    "expected_effect": "increases autonomy",
                    "priority": 0.8,
                }
            ],
        }
    )
    assert "mejorar la autonomía" in message
    assert "improve_autonomy" not in message


# ── Bug 34: global_command render ───────────────────────────────────────

def test_bug34_global_command_does_not_show_action_prefix():
    """Bug 34: 'cancelar' without active session must return the message directly,
    without the generic 'Acción ejecutada: global_command' prefix."""
    message = render_response(
        {
            "status": "ok",
            "action": "global_command",
            "message": "No hay ninguna operación activa que cancelar.",
        }
    )
    assert "No hay ninguna operación activa" in message
    assert "Acción ejecutada" not in message
    assert "global_command" not in message


def test_bug34_global_command_returns_only_message():
    """Bug 34: global_command render must return ONLY the message (exact match)."""
    msg = "Operación cancelada correctamente."
    message = render_response({"status": "ok", "action": "global_command", "message": msg})
    assert message == msg


# ── Fix 2: human-readable warnings ───────────────────────────────────────────

_SIM_WITH_WARNINGS = {
    "status": "ok",
    "action": "simulate",
    "project_id": "abc",
    "simulation": {
        "status": "pass",
        "quality": "risky",
        "safety_margin_ratio": 1.06,
        "warnings": ["low_margin", "high_actuator_load", "low_force_to_weight_ratio"],
    },
}


def test_fix2_raw_warning_codes_not_shown():
    message = render_response(_SIM_WITH_WARNINGS)
    assert "low_margin" not in message
    assert "high_actuator_load" not in message
    assert "low_force_to_weight_ratio" not in message


def test_fix2_human_warning_descriptions_shown():
    message = render_response(_SIM_WITH_WARNINGS)
    assert "Margen de seguridad ajustado" in message
    assert "motores trabajan cerca" in message
    assert "relación empuje/peso" in message


def test_fix2_simulation_line_has_no_warnings_field():
    """The 'warnings=...' inline field must be removed from the Simulación: line."""
    message = render_response(_SIM_WITH_WARNINGS)
    assert "warnings=" not in message


def test_fix2_no_warnings_produces_clean_simulation_line():
    message = render_response(
        {
            "status": "ok",
            "action": "simulate",
            "project_id": "abc",
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 2.1,
                "warnings": [],
            },
        }
    )
    assert "Simulación:" in message
    assert "warnings=" not in message
    assert "⚠" not in message


def test_fix2_autonomy_restriction_still_shows_incumplida_line():
    message = render_response(
        {
            "status": "ok",
            "action": "simulate",
            "project_id": "abc",
            "simulation": {
                "status": "pass",
                "quality": "risky",
                "safety_margin_ratio": 1.1,
                "autonomy_min": 18.0,
                "warnings": ["autonomy_below_restriction"],
            },
        }
    )
    assert "RESTRICCIÓN INCUMPLIDA" in message
    assert "18.0 min" in message
    # raw code must not appear
    assert "autonomy_below_restriction" not in message


def test_fix2_warning_maps_cover_all_simulator_codes():
    """WARNING_MESSAGES and WARNING_SHORT must contain every code the simulator can emit.

    This is a regression guard: adding a new warning in simulator.py without updating
    the translation maps would cause raw codes to leak into the CLI output.
    """
    from jarvis.adapters.cli.main import WARNING_MESSAGES, WARNING_SHORT
    from jarvis.simulation.simulator import FeasibilitySimulator

    import ast, inspect, textwrap

    source = textwrap.dedent(inspect.getsource(FeasibilitySimulator))
    tree = ast.parse(source)

    emitted: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            emitted.add(node.args[0].value)

    # autonomy_below_restriction is rendered by a special branch, not _human_warning,
    # but it must still appear in WARNING_SHORT for the startup context header.
    assert emitted, "Simulator emits no warnings — check source parsing"
    for code in emitted:
        assert code in WARNING_MESSAGES, f"WARNING_MESSAGES missing code: {code!r}"
        assert code in WARNING_SHORT, f"WARNING_SHORT missing code: {code!r}"


# ── Fix 4: declarative propulsion_passive component shows next-step hint ─────

def test_fix4_propulsion_passive_hint_contains_required_params():
    """_propulsion_passive_hint must mention both propeller params from the catalog."""
    from jarvis.actions.iterate import _propulsion_passive_hint
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation, ComponentSpec

    draft = IterationDraft(
        project_id="pid",
        project_slug="slug",
        workspace_path="/tmp",
        objective="definir hélice",
        operation=IterationOperation.DEFINE,
        component_patch={
            "propulsion_passive_0": ComponentSpec(
                name="hélice 9.8x4.2",
                component_type="propulsion_passive",
            )
        },
    )
    hint = _propulsion_passive_hint(draft)
    assert hint is not None
    assert "propeller_diameter_in" in hint
    assert "propeller_rpm" in hint
    assert "definir parámetros de hélice" in hint


def test_fix4_non_propulsion_component_returns_no_hint():
    """_propulsion_passive_hint must return None for non-propulsion_passive components."""
    from jarvis.actions.iterate import _propulsion_passive_hint
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation, ComponentSpec

    draft = IterationDraft(
        project_id="pid",
        project_slug="slug",
        workspace_path="/tmp",
        objective="definir motor",
        operation=IterationOperation.DEFINE,
        component_patch={
            "motor_0": ComponentSpec(name="motor brushless", component_type="motor_active"),
        },
    )
    assert _propulsion_passive_hint(draft) is None


def test_fix4_no_component_patch_returns_no_hint():
    """_propulsion_passive_hint must return None when component_patch is absent."""
    from jarvis.actions.iterate import _propulsion_passive_hint
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation

    draft = IterationDraft(
        project_id="pid",
        project_slug="slug",
        workspace_path="/tmp",
        objective="reducir peso",
        operation=IterationOperation.REDUCE,
    )
    assert _propulsion_passive_hint(draft) is None


def test_fix4_render_response_shows_hint_for_declarative_iterate():
    """render_response must display next_step_hint when present in iterate result."""
    result = {
        "status": "ok",
        "action": "iterate",
        "project_id": "abc",
        "message": "Propiedad del diseño definida. No se recalcula impacto físico en esta versión.",
        "next_step_hint": (
            "Para conectar esta hélice al modelo físico necesito:\n"
            "  • propeller_diameter_in (diámetro de hélice en pulgadas, ej: 10)\n"
            "  • propeller_rpm (RPM del motor en rpm, ej: 8000)\n"
            "Di 'definir parámetros de hélice' cuando estés listo."
        ),
    }
    rendered = render_response(result)
    assert "propeller_diameter_in" in rendered
    assert "propeller_rpm" in rendered
    assert "definir parámetros de hélice" in rendered


def test_fix4_render_response_no_hint_when_absent():
    """render_response must not add spurious hint text when next_step_hint is absent."""
    result = {
        "status": "ok",
        "action": "iterate",
        "project_id": "abc",
        "message": "Propiedad del diseño definida. No se recalcula impacto físico en esta versión.",
    }
    rendered = render_response(result)
    assert "propeller_diameter_in" not in rendered
    assert "definir parámetros de hélice" not in rendered


def test_fix4_hint_suppressed_when_params_already_defined():
    """_propulsion_passive_hint must return None when required params are already in current_parameters."""
    from jarvis.actions.iterate import _propulsion_passive_hint
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation, ComponentSpec

    draft = IterationDraft(
        project_id="pid",
        project_slug="slug",
        workspace_path="/tmp",
        objective="definir hélice",
        operation=IterationOperation.DEFINE,
        component_patch={
            "propulsion_passive_0": ComponentSpec(
                name="hélice 9.8x4.2",
                component_type="propulsion_passive",
            )
        },
    )
    already_defined = {"propeller_diameter_in": 9.8, "propeller_rpm": 8000}
    assert _propulsion_passive_hint(draft, already_defined) is None


def test_fix4_hint_shows_only_missing_param_when_one_already_defined():
    """Hint must list only the still-missing param when one of the two is already defined."""
    from jarvis.actions.iterate import _propulsion_passive_hint
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation, ComponentSpec

    draft = IterationDraft(
        project_id="pid",
        project_slug="slug",
        workspace_path="/tmp",
        objective="definir hélice",
        operation=IterationOperation.DEFINE,
        component_patch={
            "propulsion_passive_0": ComponentSpec(
                name="hélice 9.8x4.2",
                component_type="propulsion_passive",
            )
        },
    )
    partial = {"propeller_diameter_in": 9.8}
    hint = _propulsion_passive_hint(draft, partial)
    assert hint is not None
    assert "propeller_rpm" in hint
    assert "propeller_diameter_in" not in hint
