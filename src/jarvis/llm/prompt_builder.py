from __future__ import annotations

import json

from jarvis.config import PROMPT_VERSION
from jarvis.core.parameter_requirements import build_action_space
from jarvis.schemas.state_schema import RuntimeState

# Action space is constant at runtime — build once at import time.
_ACTION_SPACE: dict = build_action_space()
_ACTION_SPACE_JSON: str = json.dumps(_ACTION_SPACE, ensure_ascii=False, indent=2)


class PromptBuilder:
    def build_messages(self, user_input: str, runtime_state: RuntimeState) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._system_prompt(runtime_state),
            }
        ]
        for turn in runtime_state.conversation_history:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append(
            {
                "role": "user",
                "content": self._user_prompt(user_input, runtime_state),
            }
        )
        return messages

    def _system_prompt(self, runtime_state: RuntimeState) -> str:
        session = runtime_state.session
        return (
            f"PROMPT_VERSION={PROMPT_VERSION}\n"
            "Eres la interfaz estructurada de Jarvis.\n"
            "RESPONDE SOLO CON JSON VALIDO.\n"
            "NO AÑADAS TEXTO FUERA DEL JSON.\n"
            "SI NO SABES, DEVUELVE LA FORMA MAS SIMPLE POSIBLE.\n"
            "Schema obligatorio:\n"
            "{\n"
            '  "action": "create_project|iterate|calculate|simulate",\n'
            '  "project_id": "string|null",\n'
            '  "parameters": {},\n'
            '  "mode": "interactive|null",\n'
            '  "raw_user_input": "string|null"\n'
            "}\n"
            "Cuando la acción sea 'iterate', añade en parameters:\n"
            '  "operacion": "increase|reduce|define|improve|optimize",\n'
            '  "variable": "<clave canónica del Action Space — NUNCA inventada>",\n'
            '  "valor": <número o null si no se especifica>,\n'
            '  "confidence": <0.0-1.0, tu confianza en la interpretación>\n'
            "\n"
            "Action Space (variables modificables del sistema):\n"
            f"{_ACTION_SPACE_JSON}\n"
            "\n"
            "Si la intención es ambigua, devuelve una acción segura e incompleta y deja el refinamiento al flujo interactivo.\n"
            "Prefiere salidas incompletas y seguras antes que inventar parámetros técnicos.\n"
            "confidence debe ser < 0.5 si el usuario NO nombró una variable del Action Space (clave o alias).\n"
            "No inventes 'valor' si el usuario no dio un número explícito.\n"
            "Slang vago sin variable (ej. 'más chicha') → confidence baja o action incompleta; no adivines battery/payload.\n"
            "Si hay una sesión activa, NO inventes una acción nueva; responde dentro del flujo actual.\n"
            f"Estado de sesión actual: mode={self._mode_label(session.mode)}, step={session.step}."
        )

    @staticmethod
    def _mode_label(mode) -> str:
        """Accept OrchestratorMode enum or legacy string from runtime snapshots."""
        return mode.value if hasattr(mode, "value") else str(mode)

    def _user_prompt(self, user_input: str, runtime_state: RuntimeState) -> str:
        session = runtime_state.session
        mode_label = self._mode_label(session.mode)
        if mode_label == "idle":
            return f"Mensaje del usuario:\n{user_input}"

        session_context = {
            "mode": mode_label,
            "step": session.step,
            "project_draft": session.project_draft.model_dump() if session.project_draft else None,
            "iteration_draft": session.iteration_draft.model_dump() if session.iteration_draft else None,
        }
        return (
            "Hay una sesión interactiva activa. Responde solo dentro del flujo en curso.\n"
            f"Contexto de sesión: {session_context}\n"
            f"Respuesta del usuario: {user_input}"
        )

    def build_analysis_messages(
        self,
        user_input: str,
        context: dict,
        analyze_type: str,
        reasoning_output: dict | None = None,
        conversation_history: list | None = None,
        goal_context: str | None = None,
    ) -> list[dict[str, str]]:
        reasoning_block = (
            "\nRazonamiento determinista (fuente de verdad):\n"
            f"{json.dumps(reasoning_output, ensure_ascii=False, indent=2)}\n"
            if reasoning_output is not None
            else ""
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de ingenieria para analisis tecnico cualitativo.\n"
                    "RESPONDE SIEMPRE EN ESPAÑOL. Nunca uses otro idioma.\n"
                    "Responde en texto claro y breve, NO en JSON.\n"
                    "No inventes calculos nuevos.\n"
                    "Si algo no esta modelado en el contexto, dilo explicitamente.\n"
                    "Separa cuando sea posible: (1) hechos del estado y (2) implicaciones cualitativas.\n"
                    "Usa como base el razonamiento determinista entregado y no lo contradigas."
                ),
            }
        ]
        for turn in (conversation_history or []):
            messages.append({"role": turn.role, "content": turn.content})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Tipo de analisis: {analyze_type}\n"
                    "Contexto estructurado:\n"
                    f"{json.dumps(context, ensure_ascii=False, indent=2)}\n"
                    f"{reasoning_block}\n"
                    + (f"Contexto del objetivo:\n{goal_context}\n\n" if goal_context else "")
                    + f"Pregunta del usuario (responde en español):\n{user_input}"
                ),
            }
        )
        # Prefill: forces the model to continue in Spanish (Ollama returns only the continuation, not this prefix)
        messages.append({"role": "assistant", "content": "En resumen,"})
        return messages
