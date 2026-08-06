"""
system_definition_session
=========================
Sesión de definición de arquitectura de sistema.

Se lanza post create_project para poblar design_properties.components con stubs
declarados antes de entrar en cálculo/iteración.

Patrón idéntico a ParamDefinitionSession: start() / answer(), usa state_manager.

Flujo:
  start(vehicle_type, project_state)
    → dominio conocido: step=0 (oferta A/B/C)
    → dominio desconocido: step=1 (modo B directo)

  answer(user_input)
    step=0 → detecta A / B / C
    step=1 → recoge bloques custom hasta "listo"
    → _apply_and_finish() → persiste, cierra sesión, devuelve status=ok
                          → si recommended_missing_params no vacío,
                            el orquestador hace bridge a ParamDefinitionSession

Reglas de prioridad para no sobrescribir componentes existentes:
  source:      user(2) > inferred(1) > declared(0)
  completeness: high(2) > medium(1) > low(0)
  Condición de skip: source_rank > 0 OR completeness_rank > 0
"""
from __future__ import annotations

from jarvis.config import ESCAPE_WORDS
from jarvis.core.parameter_requirements import missing_params_for_reason
from jarvis.core.priority_engine import compute_priority_order
from jarvis.core.state_manager import StateManager
from jarvis.core.system_architecture_catalog import (
    blocks_to_component_keys,
    get_domain_architecture,
    get_param_reason_for_block,
    normalize_block_alias,
)
from jarvis.core.system_dependency_graph import build_dependency_graph
from jarvis.schemas.action_schema import ComponentSpec, InteractiveSessionState, OrchestratorMode
from jarvis.workspace.workspace_manager import WorkspaceManager


# ── Prioridad para no sobrescribir ────────────────────────────────────────────

_COMPLETENESS_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
# "user" reservado para input directo del usuario — máxima prioridad
_SOURCE_RANK: dict[str, int] = {"declared": 0, "inferred": 1, "user": 2}


def _should_skip(existing: ComponentSpec) -> bool:
    """True si el componente existente no debe ser sobrescrito por un stub nuevo.

    Un stub nuevo (source=declared, completeness=low) nunca supera a:
      - cualquier componente inferido (source=inferred)
      - cualquier componente de usuario (source=user)
      - cualquier componente con completeness medium o high
    """
    if _COMPLETENESS_RANK.get(existing.completeness, 0) > 0:
        return True
    if _SOURCE_RANK.get(existing.source, 0) > 0:
        return True
    return False


def _build_component_stubs(
    keys: list[str],
    existing: dict[str, ComponentSpec],
) -> dict[str, ComponentSpec]:
    """Construye stubs para los keys que no deben preservarse.

    Solo añade stubs con completeness=low y source=declared.
    Keys donde _should_skip(existing[key]) == True son ignorados.
    El catálogo no construye ComponentSpec — eso es responsabilidad de esta función.
    """
    stubs: dict[str, ComponentSpec] = {}
    for key in keys:
        if key in existing and _should_skip(existing[key]):
            continue
        stubs[key] = ComponentSpec(completeness="low", source="declared")
    return stubs


def _format_block_list(arch: dict) -> str:
    labels = arch.get("block_labels", {})
    return "\n".join(f"  • {labels.get(b, b)}" for b in arch["blocks"])


class SystemDefinitionSession:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager

    def start(self, vehicle_type: str, project_state) -> dict:
        """Lanza la sesión.

        - Siempre se ofrece (nunca silenciosa).
        - Mensaje adaptado según detail_level: conceptual → skip trivial.
        - Dominio desconocido → paso 1 (modo B directo).
        """
        arch = get_domain_architecture(vehicle_type)
        detail_level = project_state.current_parameters.get("detail_level", "")

        if arch is None:
            # Dominio desconocido: modo B directo, sin propuesta base
            session = InteractiveSessionState(
                mode=OrchestratorMode.SYSTEM_DEFINITION,
                step=1,
                memory_context={
                    "vehicle_type": vehicle_type,
                    "proposed_blocks": [],
                    "proposed_component_keys": [],
                    "recommended_start": None,
                    "custom_blocks": [],
                },
            )
            self.state_manager.set_runtime_session(session)
            return {
                "status": "interactive",
                "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
                "step": 1,
                "message": (
                    f"No tengo una arquitectura base para '{vehicle_type}'.\n"
                    "Describe los bloques del sistema (uno a uno, 'listo' para terminar):\n"
                    "Ejemplo: 'visión artificial', 'comunicación', 'payload'"
                ),
            }

        blocks = arch["blocks"]
        component_keys = blocks_to_component_keys(blocks)
        graph = build_dependency_graph(vehicle_type, blocks)
        priority = compute_priority_order(graph)
        recommended_start = priority[0] if priority else None
        block_list = _format_block_list(arch)

        if detail_level == "conceptual":
            recommendation_line = (
                "Nivel conceptual detectado — puedes saltar eligiendo C "
                "y definir los bloques cuando lo necesites."
            )
        else:
            rec_label = arch.get("block_labels", {}).get(recommended_start, recommended_start)
            recommendation_line = (
                f"Recomendado: empieza por {rec_label} — "
                "es el bloque que define el dimensionado del resto."
            )

        session = InteractiveSessionState(
            mode=OrchestratorMode.SYSTEM_DEFINITION,
            step=0,
            memory_context={
                "vehicle_type": vehicle_type,
                "proposed_blocks": blocks,
                "proposed_component_keys": component_keys,
                "recommended_start": recommended_start,
                "custom_blocks": [],
            },
        )
        self.state_manager.set_runtime_session(session)

        return {
            "status": "interactive",
            "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
            "step": 0,
            "message": (
                f"Para un {vehicle_type}, la arquitectura típica incluye:\n\n"
                f"{block_list}\n\n"
                f"{recommendation_line}\n\n"
                f"  A — Usar esta arquitectura base\n"
                f"  B — Añadir o modificar bloques\n"
                f"  C — Saltar (definir después)"
            ).strip(),
        }

    def answer(self, user_input: str) -> dict:
        session = self.state_manager.get_runtime_session()
        ctx = session.memory_context or {}

        if user_input.strip().lower() in ESCAPE_WORDS:
            self.state_manager.clear_runtime_session()
            return {
                "status": "ok",
                "action": "system_definition",
                "message": "Arquitectura no definida por ahora. Escribe 'definir sistema' cuando quieras.",
                "recommended_missing_params": [],
                "recommended_reason": None,
            }

        if session.step == 0:
            return self._handle_choice(user_input, session, ctx)
        if session.step == 1:
            return self._handle_custom_blocks(user_input, session, ctx)

        self.state_manager.clear_runtime_session()
        return {
            "status": "ok",
            "action": "system_definition",
            "message": "Sesión completada.",
            "recommended_missing_params": [],
            "recommended_reason": None,
        }

    # ── Step 0: A / B / C ────────────────────────────────────────────────────

    _OPTION_A = frozenset({
        "a", "usar", "si", "sí", "ok", "usar esa", "usar esta",
        "adelante", "perfecto", "acepto", "de acuerdo",
    })
    _OPTION_B = frozenset({
        "b", "añadir", "anadir", "modificar", "personalizar",
        "quiero añadir", "quiero anadir", "quiero modificar",
    })
    _OPTION_C = frozenset({
        "c", "saltar", "skip", "despues", "después",
        "luego", "no por ahora", "no",
    })

    def _handle_choice(self, user_input: str, session, ctx: dict) -> dict:
        normalized = user_input.strip().lower()

        # Exact match first, then prefix/contains match for longer phrases
        def _matches(option_set: frozenset) -> bool:
            if normalized in option_set:
                return True
            return any(normalized.startswith(tok) or tok in normalized for tok in option_set if len(tok) > 1)

        if _matches(self._OPTION_A):
            return self._apply_and_finish(
                base_blocks=ctx["proposed_blocks"],
                all_component_keys=ctx["proposed_component_keys"],
                ctx=ctx,
            )

        if _matches(self._OPTION_B):
            updated = session.model_copy(update={"step": 1})
            self.state_manager.set_runtime_session(updated)
            return {
                "status": "interactive",
                "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
                "step": 1,
                "message": (
                    "¿Qué bloques quieres añadir o cambiar? (uno a uno, 'listo' para terminar)\n"
                    "Ejemplos: 'visión artificial', 'comunicación', 'payload'"
                ),
            }

        if _matches(self._OPTION_C):
            self.state_manager.clear_runtime_session()
            return {
                "status": "ok",
                "action": "system_definition",
                "message": "Saltado. Puedes definir la arquitectura después.",
                "recommended_missing_params": [],
                "recommended_reason": None,
            }

        # Alias de bloque directo → modo B implícito
        block = normalize_block_alias(normalized)
        if block:
            ctx_updated = {**ctx, "custom_blocks": ctx.get("custom_blocks", []) + [block]}
            updated = session.model_copy(update={"step": 1, "memory_context": ctx_updated})
            self.state_manager.set_runtime_session(updated)
            return {
                "status": "interactive",
                "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
                "step": 1,
                "message": f"Bloque '{block}' añadido. ¿Hay más? (o 'listo' para terminar)",
            }

        return {
            "status": "interactive",
            "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
            "step": 0,
            "message": "No entendí la opción. Responde A (usar base), B (personalizar) o C (saltar).",
        }

    # ── Step 1: modo B — bloques custom ──────────────────────────────────────

    _DONE_WORDS = frozenset({
        "listo", "done", "terminar", "ya", "eso es", "eso es todo", "fin",
    })

    def _handle_custom_blocks(self, user_input: str, session, ctx: dict) -> dict:
        normalized = user_input.strip().lower()

        if normalized in self._DONE_WORDS:
            base_blocks = ctx.get("proposed_blocks", [])
            custom_blocks = ctx.get("custom_blocks", [])
            # Solo expandir bloques que existen en el catálogo — custom_blocks libres
            # se guardan en system_blocks pero no generan component keys inválidos
            all_blocks = list(dict.fromkeys(base_blocks + custom_blocks))
            component_keys = blocks_to_component_keys(all_blocks)
            return self._apply_and_finish(
                base_blocks=all_blocks,
                all_component_keys=component_keys,
                ctx=ctx,
            )

        block = normalize_block_alias(normalized)
        if block:
            ctx_updated = {**ctx, "custom_blocks": ctx.get("custom_blocks", []) + [block]}
            updated = session.model_copy(update={"memory_context": ctx_updated})
            self.state_manager.set_runtime_session(updated)
            return {
                "status": "interactive",
                "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
                "step": 1,
                "message": f"Bloque '{block}' añadido. ¿Hay más? (o 'listo' para terminar)",
            }

        # Bloque libre sin alias conocido → se registra en system_blocks pero
        # NO se expande a component keys (evita componentes inválidos silenciosos)
        ctx_updated = {**ctx, "custom_blocks": ctx.get("custom_blocks", []) + [normalized]}
        updated = session.model_copy(update={"memory_context": ctx_updated})
        self.state_manager.set_runtime_session(updated)
        return {
            "status": "interactive",
            "mode": OrchestratorMode.SYSTEM_DEFINITION.value,
            "step": 1,
            "message": (
                f"Bloque '{normalized}' registrado como bloque custom "
                "(sin componentes predefinidos). ¿Hay más? (o 'listo' para terminar)"
            ),
        }

    # ── Aplicar y cerrar ──────────────────────────────────────────────────────

    def _apply_and_finish(
        self,
        base_blocks: list[str],
        all_component_keys: list[str],
        ctx: dict,
    ) -> dict:
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            self.state_manager.clear_runtime_session()
            return {
                "status": "error",
                "action": "system_definition",
                "message": "No hay proyecto activo.",
                "recommended_missing_params": [],
                "recommended_reason": None,
            }

        existing = project_state.design_properties.components
        new_stubs = _build_component_stubs(all_component_keys, existing)
        updated_components = {**existing, **new_stubs}

        vehicle_type = ctx.get("vehicle_type", "")
        graph = build_dependency_graph(vehicle_type, base_blocks)
        priority = compute_priority_order(graph)

        updated_design = project_state.design_properties.model_copy(
            update={
                "components": updated_components,
                "system_defined": True,
                "system_blocks": base_blocks,
                "system_priority": priority,
            }
        )
        updated_state = project_state.model_copy(update={"design_properties": updated_design})
        self.workspace_manager.save_state(updated_state)
        self.state_manager.clear_runtime_session()

        # Bridge: usar el primer bloque del orden de prioridad derivado
        # como punto de entrada a ParamDefinitionSession.
        recommended_start = priority[0] if priority else ctx.get("recommended_start")
        recommended_reason: str | None = None
        recommended_missing: list[str] = []

        if recommended_start:
            reason = get_param_reason_for_block(recommended_start)
            if reason:
                current_params = updated_state.current_parameters
                still_missing = missing_params_for_reason(reason, current_params)
                if still_missing:
                    recommended_reason = reason
                    recommended_missing = still_missing

        component_labels = ", ".join(all_component_keys) if all_component_keys else "(sin componentes definidos)"
        message = f"Arquitectura definida: {component_labels}."

        if recommended_missing:
            rec_label = recommended_start or ""
            message += (
                f"\n\nEmpecemos por {rec_label}. Faltan parámetros clave:\n"
                + "\n".join(f"  • {p}" for p in recommended_missing)
            )

        return {
            "status": "ok",
            "action": "system_definition",
            "defined_components": all_component_keys,
            "message": message,
            "recommended_missing_params": recommended_missing,
            "recommended_reason": recommended_reason,
        }
