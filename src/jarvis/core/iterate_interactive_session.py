from __future__ import annotations

from dataclasses import dataclass

from jarvis.core.component_inference import infer_component
import jarvis.core.semantic_interpreter as sem
from jarvis.domains.registry_selector import get_registry

from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.core.mutation_engine import MutationEngine, _mass_factor_from_density_ratio, _PARAM_DISPLAY_ALIASES
from jarvis.core.parameter_requirements import PARAMETER_REQUIREMENTS, VariableType, normalize_alias, get_derived_message, get_display_name
from jarvis.core.iterate_domain import (
    _VARIABLE_NORMALIZATION,
    _normalize_variable_input,
    _fuzzy_normalize_variable,
    _is_valid_variable,
    _KNOWN_MATERIALS,
)
from jarvis.memory.history import build_conflict_type, latest_conflict_by_type
from jarvis.schemas.semantic_schema import SemanticState, SlotValue
from jarvis.schemas.state_schema import ProjectMemory
from jarvis.config import ESCAPE_WORDS
from jarvis.core.intent_resolver import IntentResolver
from jarvis.schemas.action_schema import (
    ActionName,
    ImpactEstimate,
    InteractiveSessionState,
    IterationConflict,
    IterationDraft,
    IterationOperation,
    OrchestratorMode,
    PropertyValue,
)


# Terms that look like physical components but are not valid iterate variables.
# When a user types one of these in step 1, the error message adds a targeted
# redirect: "di 'componentes'", instead of just the generic hint list.
_COMPONENT_REDIRECT_TERMS: frozenset[str] = frozenset({
    "sensor", "sensores",
    "esc", "controladora", "controladoras",
    "frame", "chasis", "chassis",
    "lipo",
})
# Bug 42: propeller-specific redirect terms get a more precise hint so the user
# knows to say "configurar hélices" (which maps to define_params wizard).
_PROPELLER_REDIRECT_TERMS: frozenset[str] = frozenset({
    "helice", "helices", "propeller", "propellers", "palas",
})


@dataclass(frozen=True)
class IteratePrompt:
    step: int
    field_name: str
    question: str


class IterateInteractiveSession:
    PROMPTS = (
        IteratePrompt(0, "objective_confirmation", "Quieres modificar el sistema actual. ¿Cuál es el objetivo de la iteración?"),
        IteratePrompt(1, "variable", "¿Qué quieres modificar? (material, dimensiones, componentes, carga, etc.)"),
        IteratePrompt(2, "strategy", "¿Cómo quieres aplicar el cambio? (cambiar material, optimizar estructura, reducir carga, etc.)"),
        IteratePrompt(3, "restrictions", "¿Hay restricciones? (ej: mantener resistencia, no cambiar tamaño, etc.)"),
        IteratePrompt(4, "impact_estimate", ""),
        IteratePrompt(5, "confirmation", "¿Confirmas la iteración?"),
    )

    def __init__(self, library: ComponentLibrary | None = None) -> None:
        self._library = library or default_library
        self._mutation_engine = MutationEngine(self._library)  # used for Bug 24 coherence check

    def _registry_for_session(
        self,
        session: InteractiveSessionState,
        text: str = "",
    ):
        """Return the best ComponentRuleRegistry for the session's domain context.

        Priority:
          1. session.memory_context["vehicle_type"] — explicit project type
          2. text heuristic — signal from component description
          3. default (aerial_registry) — backward compatible
        """
        vehicle_type = (session.memory_context or {}).get("vehicle_type")
        return get_registry(vehicle_type=vehicle_type, text=text)

    def start(self, seed_parameters: dict | None = None) -> dict:
        seed = seed_parameters or {}
        initial_draft = self._build_initial_draft(seed)

        # Seed semantic state from known project components and enrichment context
        enrich_component: str | None = seed.get("enrich_component")
        known_components: dict = seed.get("known_components") or {}
        initial_semantic: SemanticState | None = None
        if known_components or enrich_component:
            base = SemanticState()
            if enrich_component:
                base = base.model_copy(update={"focus": enrich_component})
            initial_semantic = self._seed_semantic_from_state(base, known_components)

        # Preload existing ComponentSpec for the focused component into the draft
        if enrich_component and known_components:
            existing_spec = self._find_spec_by_name(known_components, enrich_component)
            if existing_spec is not None:
                spec_key = existing_spec.suggested_key or enrich_component
                initial_draft = initial_draft.model_copy(
                    update={"component_patch": {spec_key: existing_spec}}
                )

        # Jump to step 2 (definition) when enriching a specific component
        start_step = 2 if enrich_component else 0
        # Allow callers (e.g. orchestrator after high-confidence LLM interpretation)
        # to override the starting step when operation + variable are already known.
        if "seed_step" in seed:
            start_step = int(seed["seed_step"])

        session = InteractiveSessionState(
            mode=OrchestratorMode.ITERATE_INTERACTIVE,
            step=start_step,
            iteration_draft=initial_draft,
            memory_context=seed.get("memory_context"),
            semantic_state=initial_semantic,
        )
        # If the LLM proposed a derived (non-settable) variable, surface the
        # redirect message at step 0 before the normal objective question.
        redirect_msg: str | None = seed.get("derived_redirect_message")
        return self._build_response(session, message=redirect_msg)

    def answer(self, session: InteractiveSessionState, user_input: str) -> dict:
        if session.mode != OrchestratorMode.ITERATE_INTERACTIVE or session.iteration_draft is None:
            raise ValueError("No hay una sesión interactiva de iteración activa.")

        normalized = user_input.strip()

        # ── Global escape hatch ───────────────────────────────────────────────
        # Safety fallback — uses the same ESCAPE_WORDS as the orchestrator (jarvis.config).
        # The orchestrator intercepts these first; this catches direct callers.
        if normalized.lower() in ESCAPE_WORDS:
            return {
                "status": "cancelled",
                "action": "iterate",
                "message": "Iteración cancelada. Puedes escribir 'calcula', 'simula' o describir un nuevo cambio.",
            }
        # ─────────────────────────────────────────────────────────────────────

        # Allow empty input at step 3 (restrictions are optional)
        if not normalized and session.step == 3:
            normalized = "ninguna"
        if not normalized:
            return self._build_response(session, error="Necesito una respuesta para continuar.")

        # ── Safety: motor_suggestions are only valid at step 2 ───────────────
        # Any other step arriving with stale suggestions is a zombie — purge it.
        if session.step != 2 and session.motor_suggestions:
            session = session.model_copy(update={"motor_suggestions": []})
        # ────────────────────────────────────────────────────────────────────

        # ── Seed desde draft + enriquecer con nuevo input ──────────────────────
        seeded = self._seed_semantic_from_draft(
            session.semantic_state or SemanticState(),
            session.iteration_draft,
        )
        new_semantic = sem.update(seeded, normalized, context=session.memory_context)
        session = session.model_copy(update={"semantic_state": new_semantic})
        # ──────────────────────────────────────────────────────────────────────

        if session.step == 0:
            return self._handle_objective_confirmation(session, normalized)
        if session.step == 2 and session.iteration_draft.conflict is not None:
            return self._handle_conflict_resolution(session, normalized)
        if session.step == 4:
            return self._handle_apply_decision(session, normalized)
        if session.step == 5:
            return self._handle_final_confirmation(session, normalized)

        # ── Step 1: domain validation ───────────────────────────────────────
        # REGLA DE ORO FASE G: NINGÚN input del usuario entra al sistema sin
        # pasar por validación de dominio.  Any variable outside the closed set
        # is rejected here — before _apply_answer touches the draft.
        if session.step == 1 and not _is_valid_variable(normalized):
            _var_norm = _normalize_variable_input(normalized)
            if _var_norm in _PROPELLER_REDIRECT_TERMS:
                _component_hint = (
                    " Para configurar las hélices di: \"configurar hélices\"."
                )
            elif _var_norm in _COMPONENT_REDIRECT_TERMS:
                _component_hint = (
                    " Para definir componentes físicos (hélices, motores, batería, sensores), di 'componentes'."
                )
            else:
                _component_hint = ""
            return self._build_response(
                session,
                error=(
                    f"No reconozco '{normalized}' como variable modificable. "
                    "Prueba con: material, dimensiones, motores, bateria, "
                    f"potencia_motor, carga, componentes, estructura.{_component_hint}"
                ),
            )
        # ─────────────────────────────────────────────────────────────────────

        # ── Step 1: detect derived/non-settable variables (Bug 5) ────────────
        # Variables like "autonomía" are derived results, not direct inputs.
        # Redirect the user to the underlying settable parameters without
        # advancing the session — no state change, no inconsistency risk.
        if session.step == 1:
            redirect_message = get_derived_message(normalize_alias(normalized))
            if redirect_message:
                return self._build_response(
                    session,
                    message=redirect_message,
                    question="¿Qué parámetro concreto quieres modificar?",
                )
        # ──────────────────────────────────────────────────────────────────────

        # ── pending_entities sub-loop (multi-entity define) ─────────────────
        if session.pending_entities:
            return self._handle_pending_entity_selection(session, normalized)
        # ──────────────────────────────────────────────────────────────────

        # ── Motor suggestion sub-loop — awaiting user selection ───────────
        if session.motor_suggestions:
            return self._handle_motor_suggestion_selection(session, normalized)
        # ────────────────────────────────────────────────────────────────

        # ── Bug 40: Re-intent detector — step 2 ──────────────────────────
        # If the user types a clearly different high-level iteration goal while
        # the wizard is already in step 2, restart the session with the new goal.
        # Only fires when an EXPLICIT canonical variable keyword is detected in
        # the input (not just any noun after a verb), to avoid false-positives
        # on valid strategy phrases like "optimizar estructura" for "componentes".
        # Explicit variable keywords mirror those checked in resolve_action_request.
        _BUG40_EXPLICIT_VARS = frozenset({"carga", "material", "bateria", "dimensiones", "autonomia", "potencia"})
        if session.step == 2 and session.iteration_draft.variable:
            _cur_var = (session.iteration_draft.variable or "").strip().lower()
            _hit_var = None
            for _v in _BUG40_EXPLICIT_VARS:
                if _v in normalized.lower():
                    _raw = normalize_alias(_normalize_variable_input(_v))
                    _canon = _VARIABLE_NORMALIZATION.get(_raw) or _fuzzy_normalize_variable(_raw) or _raw
                    if _canon != _cur_var:
                        _hit_var = _v
                        break
            if _hit_var:
                _resolver = IntentResolver()
                _action_req = _resolver.resolve_action_request(normalized)
                if _action_req is not None and _action_req.get("action") == ActionName.ITERATE.value:
                    new_seed = {
                        **(_action_req.get("parameters") or {}),
                        "project_id": session.iteration_draft.project_id,
                        "project_slug": session.iteration_draft.project_slug,
                        "workspace_path": session.iteration_draft.workspace_path,
                    }
                    return self.start(new_seed)
        # ─────────────────────────────────────────────────────────────────

        # ── Gap 1: material sub-step — awaiting explicit material name ───
        # ── Numeric parameter — treat input as new numeric value ─────────────
        # When variable matches a known numeric param in current_parameters,
        # the user's step-2 input IS the new value (not a strategy description).
        # Skip strategy/restrictions and go straight to the impact + confirm flow.
        if session.step == 2:
            current_params = (session.memory_context or {}).get("current_parameters") or {}
            _var = session.iteration_draft.variable or ""
            _var_req = PARAMETER_REQUIREMENTS.get(_var)
            canonical = (
                None if (_var_req and _var_req.variable_type == VariableType.SEMANTIC_MUTATION)
                else self._match_numeric_param(_var, current_params)
            )
            if canonical:
                try:
                    new_value = float(normalized.replace(",", "."))
                except ValueError:
                    old_val = current_params.get(canonical, "?")
                    display_name = session.iteration_draft.variable or canonical
                    return self._build_response(
                        session,
                        error="Necesito un valor numérico.",
                        question=f"¿Cuál es el nuevo valor de {display_name}? (actual: {old_val})",
                    )
                updated_draft = session.iteration_draft.model_copy(update={
                    "value": str(new_value),
                    "strategy": f"establecer {session.iteration_draft.variable or canonical} = {new_value}",
                    # Infer INCREASE/REDUCE/DEFINE by comparing new value vs current.
                    "operation": self._infer_numeric_operation(new_value, current_params.get(canonical)),
                })
                updated_draft = self._attach_numeric_impact_estimate(updated_draft, canonical, current_params)
                updated_session = session.model_copy(update={"step": 4, "iteration_draft": updated_draft})
                return self._build_response(updated_session)
        # ─────────────────────────────────────────────────────────────────────

        if session.step == 2 and self._awaiting_material_value(session.iteration_draft):
            material_name = self._extract_material_from_text(normalized)
            if not material_name:
                return self._build_response(
                    session,
                    question="No reconozco ese material. ¿Cuál es? (fibra de carbono, titanio, aluminio, acero, etc.)",
                )
            # Bug 43: reject same material before touching the draft.
            current_material = (session.memory_context or {}).get("current_material")
            if (
                current_material is not None
                and self._normalize_material(material_name) == self._normalize_material(current_material)
            ):
                return self._build_response(
                    session,
                    question=(
                        f"El material '{material_name}' ya es el material actual del sistema. "
                        "No hay cambio que aplicar. ¿Quieres usar otro material?"
                    ),
                )
            # Preserve the original physical operation (e.g. REDUCE) so that
            # _estimate_impact can compute a real delta.  Fall back to DEFINE only when
            # no operation was set (avoids operation=None reaching _handle_final_confirmation).
            _op = session.iteration_draft.operation or IterationOperation.DEFINE
            updated_draft = session.iteration_draft.model_copy(update={
                "value": material_name,
                "operation": _op,
            })
            return self._build_response(
                session.model_copy(update={"step": 3, "iteration_draft": updated_draft})
            )
        # ────────────────────────────────────────────────────────────────

        if session.step == 2 and self._needs_definition_value(session.iteration_draft):
            focus = session.semantic_state.focus if session.semantic_state else None
            # ── multi-entity intercept (only when no active focus) ───────
            # When focus is set the user is specifying ONE component → full
            # input is a single spec string, not a list of separate entities.
            if not focus:
                entities = sem.extract_entities(normalized)
                if len(entities) >= 2:
                    pending = [e for e in entities if e != focus]
                    entity_list = ", ".join(entities)
                    updated_session = session.model_copy(update={"pending_entities": pending})
                    return self._build_response(
                        updated_session,
                        message=(
                            f"He identificado {len(entities)} componentes: {entity_list}.\n"
                            f"¿Por cuál empezamos? (o escribe \"todos\" para registrarlos con nivel bajo de detalle)"
                        ),
                    )
            # ── single entity OR focus-aware spec ────────────────────────
            # Reject question-shaped input when user should be giving a spec
            if focus and self._input_looks_like_question(normalized):
                question = self._definition_value_question(session.iteration_draft, focus)
                return self._build_response(
                    session,
                    message=(
                        "Parece una pregunta, no una especificación.\n"
                        "Por favor, describe directamente los datos del componente.\n"
                        f"{question}"
                    ),
                )

            feedback_message = None
            if (session.iteration_draft.variable or "").strip().lower() != "material":
                feedback_message = self._definition_feedback_message(normalized)
            spec = infer_component(normalized, registry=self._registry_for_session(session, normalized))
            updated_patch = dict(session.iteration_draft.component_patch or {})
            component_key = spec.suggested_key or "component_1"
            updated_patch[component_key] = spec
            updated_draft = session.iteration_draft.model_copy(
                update={
                    "value": normalized,
                    "strategy": session.iteration_draft.strategy or f"definir {session.iteration_draft.variable or 'propiedad'}",
                    "operation": IterationOperation.DEFINE,
                    "component_patch": updated_patch,
                }
            )
            updated_session = session.model_copy(update={"step": 3, "iteration_draft": updated_draft})

            # ── Motor KV without thrust → suggest before advancing ────────
            project_state = self._project_state_for_session(session)
            motor_suggestions = self._build_motor_suggestions(spec, project_state=project_state)
            if motor_suggestions:
                updated_session = updated_session.model_copy(
                    update={"step": 2, "motor_suggestions": motor_suggestions}
                )
                suggestion_text = self._format_motor_suggestions(motor_suggestions)
                return self._build_response(
                    updated_session,
                    message=suggestion_text,
                    question="¿Quieres usar alguno? (1/2/… o 'no', especifica el tuyo)",
                )
            empty_catalog_note = self._empty_motor_catalog_note(spec, project_state=project_state)
            if empty_catalog_note:
                feedback_message = (
                    f"{feedback_message}\n{empty_catalog_note}"
                    if feedback_message
                    else empty_catalog_note
                )
            # ─────────────────────────────────────────────────────────────

            return self._build_response(updated_session, message=feedback_message)
        if session.step == 2:
            definition_response = self._detect_definition_response(session, normalized)
            if definition_response is not None:
                return definition_response
            conflict_response = self._detect_conflict_response(session, normalized)
            if conflict_response is not None:
                return conflict_response

        updated_draft = self._apply_answer(session.iteration_draft, session.step, normalized, session.semantic_state)

        # ── decide() routing: activo en step 2 ───────────────────────────────
        if session.step == 2:
            # ── Gap 1: material variable → try to extract name from strategy ──
            if (updated_draft.variable or "").lower() == "material" and updated_draft.value is None:
                material_name = self._extract_material_from_text(updated_draft.strategy or "")
                if material_name:
                    # Name embedded in strategy → store and go to restrictions
                    updated_draft = updated_draft.model_copy(update={"value": material_name})
                    return self._build_response(
                        session.model_copy(update={"step": 3, "iteration_draft": updated_draft})
                    )
                else:
                    # Strategy given but no material name → ask for it
                    return self._build_response(
                        session.model_copy(update={"iteration_draft": updated_draft}),
                        message="¿A qué material quieres cambiar? (ej: fibra de carbono, titanio, aluminio)",
                        question="¿Qué material?",
                    )
            # ────────────────────────────────────────────────────────────────

            # ── Bug 24: variable ↔ strategy coherence check ──────────────────
            # After step 2 records the strategy we have the full (variable, strategy)
            # pair. If it cannot be routed to any physical mutation AND is not a
            # structural downgrade candidate, the combination is semantically
            # incoherent. Warn the user here — before step 3 restrictions —
            # so they don’t go through the full wizard only to hit a wall.
            if (
                updated_draft.operation != IterationOperation.DEFINE
                and updated_draft.variable
                and not self._should_downgrade_to_declarative(updated_draft)
                and not self._mutation_engine.is_physically_actionable(updated_draft)
            ):
                return self._build_response(
                    session,  # keep session unchanged so user retypes strategy
                    message=(
                        f"La estrategia '{updated_draft.strategy}' no es compatible con "
                        f"la variable '{updated_draft.variable}'. "
                        "Describe cómo quieres modificar esa variable "
                        "(ej: 'reducir material', 'optimizar dimensiones', 'reducir carga')."
                    ),
                    question="¿Cómo quieres aplicar el cambio?",
                )
            # ──────────────────────────────────────────────────────────────────

            decision = sem.decide(session.semantic_state)

            if decision == "proceed":
                # Reject vacuous strategy before advancing.
                # If the user hasn't given a real strategy (None, empty, or just an
                # operation keyword like "mejorar"), ask explicitly instead of
                # auto-synthesising a meaningless string like "reducir payload_kg".
                strategy_text = updated_draft.strategy or ""
                if not strategy_text.strip() or sem._is_pure_operation_phrase(strategy_text):
                    updated_semantic = sem.increment_clarification_round(session.semantic_state or SemanticState())
                    return self._build_response(
                        session.model_copy(update={"iteration_draft": updated_draft, "semantic_state": updated_semantic}),
                        message=self._missing_slot_question("la estrategia"),
                    )
                # Always go to step 3 (restrictions) — never skip it, even when confident
                return self._build_response(
                    session.model_copy(update={"step": 3, "iteration_draft": updated_draft})
                )

            if decision == "confirm":
                intent = session.semantic_state.intent if session.semantic_state else None
                msg = f"Entendido: quieres {intent}." if intent else None
                return self._build_response(
                    session.model_copy(update={"step": 3, "iteration_draft": updated_draft}),
                    message=msg,
                )

            if decision == "clarify":
                missing = (session.semantic_state.missing_slots or []) if session.semantic_state else []
                slot_question = self._missing_slot_question(missing[0] if missing else "la estrategia")
                updated_semantic = sem.increment_clarification_round(session.semantic_state or SemanticState())
                updated_session = session.model_copy(
                    update={"iteration_draft": updated_draft, "semantic_state": updated_semantic}
                )
                return self._build_response(updated_session, message=slot_question)
        # ────────────────────────────────────────────────────────────────────

        updated_session = session.model_copy(update={"step": session.step + 1, "iteration_draft": updated_draft})
        if updated_session.step == 4:
            # Pass current_parameters so _estimate_impact can compute real deltas.
            ctx_params = (session.memory_context or {}).get("current_parameters") or {}
            ctx_material = (session.memory_context or {}).get("current_material")
            updated_session = updated_session.model_copy(
                update={"iteration_draft": self._attach_impact_estimate(updated_session.iteration_draft, ctx_params, current_material=ctx_material)}
            )
        # After step 1 resolves to a known numeric param, emit a brief confirmation
        # so the user understands we jumped straight to the value question.
        if session.step == 1 and updated_session.step == 2:
            ctx_params = (session.memory_context or {}).get("current_parameters") or {}
            _v = updated_draft.variable or ""
            _v_req = PARAMETER_REQUIREMENTS.get(_v)
            if not (_v_req and _v_req.variable_type == VariableType.SEMANTIC_MUTATION) and self._match_numeric_param(_v, ctx_params) is not None:
                return self._build_response(
                    updated_session,
                    message=f"Entendido: modificaremos {_v}.",
                )
        return self._build_response(updated_session)

    def _build_initial_draft(self, seed_parameters: dict) -> IterationDraft:
        operation = seed_parameters.get("operacion") or seed_parameters.get("operation")
        objective = seed_parameters.get("objetivo") or seed_parameters.get("objective")
        if operation == IterationOperation.DEFINE or operation == IterationOperation.DEFINE.value:
            objective = objective or "definición declarativa"

        return IterationDraft(
            project_id=seed_parameters.get("project_id"),
            project_slug=seed_parameters.get("project_slug"),
            workspace_path=seed_parameters.get("workspace_path"),
            objective=objective,
            operation=operation,
            variable=seed_parameters.get("variable"),
        )

    def _handle_objective_confirmation(self, session: InteractiveSessionState, user_input: str) -> dict:
        normalized = user_input.lower()
        if normalized in {"si", "sí", "s", "correcto", "ok"}:
            next_step = 2 if session.iteration_draft.variable else 1
            updated_draft = session.iteration_draft
            if updated_draft.operation == IterationOperation.DEFINE and not updated_draft.objective:
                updated_draft = updated_draft.model_copy(update={"objective": "definición declarativa"})
            updated_session = session.model_copy(update={"step": next_step, "iteration_draft": updated_draft})
            return self._build_response(updated_session)
        if normalized in {"no", "n"}:
            reset_draft = session.iteration_draft.model_copy(update={"objective": None, "operation": None})
            updated_session = session.model_copy(update={"iteration_draft": reset_draft})
            return self._build_response(
                updated_session,
                message="Indica de nuevo el objetivo de la iteración antes de continuar.",
            )
        updated_draft = session.iteration_draft.model_copy(update={"objective": user_input})
        updated_session = session.model_copy(update={"step": 1, "iteration_draft": updated_draft})
        return self._build_response(updated_session)

    def _apply_answer(
        self,
        draft: IterationDraft,
        step: int,
        user_input: str,
        semantic_state: SemanticState | None = None,
    ) -> IterationDraft:
        if step == 1:
            # Normalize user-facing concept names to canonical parameter keys.
            raw = normalize_alias(user_input)
            normalized_var = _VARIABLE_NORMALIZATION.get(raw)
            if normalized_var is None:
                # Fuzzy substring fallback for typos (e.g. "dimesniones").
                normalized_var = _fuzzy_normalize_variable(raw)
            return draft.model_copy(update={"variable": normalized_var})
        if step == 2:
            return draft.model_copy(
                update={
                    "strategy": user_input,
                    "operation": self._operation_from_semantic(semantic_state, fallback=draft.operation),
                    "conflict": None,
                }
            )
        if step == 3:
            return draft.model_copy(update={"restrictions": user_input})
        raise ValueError(f"Step de iterate no soportado: {step}")

    def _attach_impact_estimate(self, draft: IterationDraft, current_params: dict | None = None, current_material: str | None = None) -> IterationDraft:
        # Gap 2: structural iteration without concrete value → downgrade to declarative
        if self._should_downgrade_to_declarative(draft):
            estimate = ImpactEstimate(
                summary=(
                    "Sin un parámetro concreto (factor de masa, dimensión específica), "
                    "no es posible calcular impacto físico. "
                    "Se registra como intención de mejora declarativa."
                )
            )
            return draft.model_copy(
                update={"impact_estimate": estimate, "operation": IterationOperation.DEFINE}
            )
        estimate = self._estimate_impact(draft, current_params, current_material=current_material)
        return draft.model_copy(update={"impact_estimate": estimate})

    def _estimate_impact(self, draft: IterationDraft, current_params: dict | None = None, current_material: str | None = None) -> ImpactEstimate:
        variable = (draft.variable or "").lower()
        strategy = (draft.strategy or "").lower()
        material_value = (draft.value or "").strip().lower()
        params = current_params or {}

        if "material" in variable or "material" in strategy:
            return self._estimate_material_impact(draft, material_value, current_material=current_material)

        if draft.operation == IterationOperation.DEFINE:
            return ImpactEstimate(
                summary=(
                    "Esta iteración define una propiedad del diseño.\n"
                    "No se recalcula impacto físico en esta versión."
                )
            )

        # Payload: compute real delta when current value and target are known.
        is_payload = (
            "carga" in variable or "carga" in strategy
            or variable in ("payload_kg", "payload", "carga util", "carga útil")
        )
        if is_payload:
            payload_current = params.get("payload_kg")
            try:
                new_payload = float(draft.value)
            except (TypeError, ValueError):
                new_payload = None

            if payload_current and new_payload is not None:
                current_f = float(payload_current)
                delta_pct = round((new_payload - current_f) / current_f * 100, 1) if current_f else 0.0
                sign = "+" if delta_pct >= 0 else ""
                thrust = "negativo" if delta_pct > 0 else ("positivo" if delta_pct < 0 else "neutro")
                return ImpactEstimate(
                    weight_change_percent=delta_pct,
                    thrust_impact=thrust,
                    stability_impact="a revisar",
                    summary=(
                        f"Payload {current_f} kg → {new_payload} kg ({sign}{delta_pct}%). "
                        "Impacto en empuje disponible requiere recálculo completo."
                    ),
                )
            # Fallback: no concrete value available
            if self._is_increase_operation(draft.operation):
                return ImpactEstimate(
                    weight_change_percent=10.0,
                    thrust_impact="negativo",
                    stability_impact="a revisar",
                    summary="Estimación preliminar: payload ↑ ~10%, reduce el margen de empuje.",
                )
            return ImpactEstimate(
                weight_change_percent=-10.0,
                thrust_impact="positivo",
                stability_impact="neutro",
                summary="Estimación preliminar: payload ↓ ~10%, mejora del margen de empuje.",
            )
        return ImpactEstimate(
            weight_change_percent=-5.0,
            thrust_impact="ligeramente positivo",
            stability_impact="a revisar",
            summary="Estimación preliminar: mejora moderada, requiere validación posterior.",
        )

    @staticmethod
    def _normalize_material(name: str) -> str:
        """Normalize a material name for equality comparison (Bug 43).

        Strips whitespace, lowercases, and removes diacritics so that
        'Aluminio', 'aluminio', 'ALUMINIO' all compare equal.
        """
        import unicodedata as _ud
        lowered = name.strip().lower()
        nfkd = _ud.normalize("NFKD", lowered)
        return "".join(c for c in nfkd if not _ud.combining(c))

    def _estimate_material_impact(
        self, draft: IterationDraft, new_material: str, current_material: str | None = None
    ) -> ImpactEstimate:
        """Preview using the same density-ratio formula as mutation_engine.

        Bug 44: returns a clear, user-facing message when the material is
        recognised by name but has no physics data in the library.
        """
        structural_fraction = 0.25
        # Use provided context (injected from memory_context); fall back to
        # aluminium only when no project state is available.
        current_material = current_material or "aluminio"

        if not new_material:
            return ImpactEstimate(
                summary="No se especificó material. Indica el nombre antes de calcular el impacto."
            )

        # Bug 44: fetch new material first — distinguish "unknown" (typo) from
        # "recognised but no physics data" (e.g. madera, PVC).
        try:
            spec_new = self._library.get_material(new_material)
        except KeyError:
            available = ", ".join(sorted(m.name for m in self._library.list_materials()))
            return ImpactEstimate(
                summary=(
                    f"El material '{new_material}' ha sido registrado en el diseño, "
                    "pero no tengo datos físicos para calcular su impacto en peso o simulación.\n"
                    f"Materiales con datos disponibles: {available}."
                ),
            )

        try:
            spec_old = self._library.get_material(current_material)
        except KeyError:
            spec_old = self._library.get_material("aluminio")

        # Use the same helper as mutation_engine — identical math guarantees preview == result
        _, weight_change_pct = _mass_factor_from_density_ratio(
            spec_old.density_kg_m3, spec_new.density_kg_m3, structural_fraction
        )
        thrust_impact = "positivo" if weight_change_pct < 0 else ("negativo" if weight_change_pct > 0 else "neutro")

        return ImpactEstimate(
            weight_change_percent=weight_change_pct,
            thrust_impact=thrust_impact,
            stability_impact="neutro",
            summary=(
                f"Cambio {spec_old.name} → {spec_new.name}: "
                f"ρ {spec_old.density_kg_m3}→{spec_new.density_kg_m3} kg/m³, "
                f"peso total estimado {'+' if weight_change_pct > 0 else ''}{weight_change_pct}% "
                f"(fracción estructural {int(structural_fraction*100)}%)."
            ),
        )

    def _handle_apply_decision(self, session: InteractiveSessionState, user_input: str) -> dict:
        normalized = user_input.lower()
        if normalized in {"si", "sí", "s", "aplicar", "ok"}:
            return self._build_response(session.model_copy(update={"step": 5}))
        if normalized in {"no", "n", "editar", "corregir"}:
            clean_draft = IterationDraft(
                project_id=session.iteration_draft.project_id if session.iteration_draft else None,
                project_slug=session.iteration_draft.project_slug if session.iteration_draft else None,
                workspace_path=session.iteration_draft.workspace_path if session.iteration_draft else None,
            )
            return self._build_response(
                session.model_copy(update={"step": 1, "iteration_draft": clean_draft, "semantic_state": None}),
                message="Volvemos al ajuste de la variable para corregir la iteración.",
            )
        return self._build_response(
            session,
            error=(
                f"No reconozco '{user_input}'. "
                "Responde 'sí' (o 's') para pasar a confirmación final, "
                "'no' (o 'n') para volver a corregir."
            ),
        )

    def _handle_final_confirmation(self, session: InteractiveSessionState, user_input: str) -> dict:
        normalized = user_input.lower()
        if normalized in {"si", "sí", "s", "confirmo", "ok"}:
            draft = session.iteration_draft
            # Reject incoherent drafts before confirming.
            if draft is None or draft.operation is None:
                return self._build_response(
                    session,
                    error="La iteración no tiene operación definida. Responde 'no' para corregirla.",
                )
            if draft.variable is None:
                return self._build_response(
                    session,
                    error="La iteración no tiene variable definida. Responde 'no' para corregirla.",
                )
            if draft.operation != IterationOperation.DEFINE and (draft.strategy is None or not draft.strategy.strip()):
                return self._build_response(
                    session,
                    error="La iteración no tiene estrategia definida. Responde 'no' para corregirla.",
                )
            return {
                "status": "confirmed",
                "mode": session.mode.value,
                "step": session.step,
                "iteration_draft": draft.model_dump(),
            }
        if normalized in {"no", "n", "editar", "corregir"}:
            # Reset the draft - keep only project identity, clear all stale user data
            clean_draft = IterationDraft(
                project_id=session.iteration_draft.project_id if session.iteration_draft else None,
                project_slug=session.iteration_draft.project_slug if session.iteration_draft else None,
                workspace_path=session.iteration_draft.workspace_path if session.iteration_draft else None,
            )
            clean_session = session.model_copy(update={"step": 1, "iteration_draft": clean_draft, "semantic_state": None})
            return self._build_response(
                clean_session,
                message="Iteración no confirmada. Puedes corregir la definición antes de ejecutar.",
            )
        return self._build_response(
            session,
            error=(
                f"No reconozco '{user_input}'. "
                "Responde 'sí' (o 's') para aplicar los cambios, "
                "'no' (o 'n') para volver a corregir."
            ),
        )

    def _handle_conflict_resolution(self, session: InteractiveSessionState, user_input: str) -> dict:
        normalized = user_input.lower()
        draft = session.iteration_draft
        conflict = draft.conflict

        if self._is_keep_initial_resolution(normalized):
            updated_draft = draft.model_copy(update={"conflict": None})
            response = self._build_response(
                session.model_copy(update={"iteration_draft": updated_draft}),
                message="Mantendremos el objetivo inicial. Describe una estrategia alineada con ese objetivo.",
            )
            response["memory_update"] = {
                "initial_objective": conflict.initial_objective,
                "initial_operation": conflict.initial_operation,
                "conflicting_operation": conflict.conflicting_operation,
                "resolution": "keep_initial_goal",
            }
            return response

        if self._is_apply_new_change_resolution(normalized):
            updated_draft = draft.model_copy(
                update={
                    "operation": conflict.conflicting_operation or draft.operation,
                    "strategy": conflict.conflicting_input,
                    "conflict": None,
                }
            )
            updated_session = session.model_copy(update={"step": 3, "iteration_draft": updated_draft})
            response = self._build_response(updated_session)
            response["memory_update"] = {
                "initial_objective": conflict.initial_objective,
                "initial_operation": conflict.initial_operation,
                "conflicting_operation": conflict.conflicting_operation,
                "resolution": "apply_new_change",
            }
            return response

        if self._is_cancel_resolution(normalized):
            return {
                "status": "cancelled",
                "mode": session.mode.value,
                "step": session.step,
                "message": "Iteración cancelada por conflicto detectado.",
                "memory_update": {
                    "initial_objective": conflict.initial_objective,
                    "initial_operation": conflict.initial_operation,
                    "conflicting_operation": conflict.conflicting_operation,
                    "resolution": "cancel_iteration",
                },
            }

        return self._build_response(
            session,
            error=(
                "Responde con 1/2/3 o con texto como "
                "'mantener el objetivo inicial', 'aplicar el nuevo cambio' o 'cancelar iteración'."
            ),
        )

    def _build_response(
        self,
        session: InteractiveSessionState,
        message: str | None = None,
        error: str | None = None,
        question: str | None = None,
    ) -> dict:
        response = {
            "status": "interactive",
            "mode": session.mode.value,
            "step": session.step,
            "iteration_draft": session.iteration_draft.model_dump() if session.iteration_draft else {},
            "memory_context": session.memory_context,
            "pending_entities": session.pending_entities,
            "motor_suggestions": session.motor_suggestions,
        }
        if session.semantic_state is not None:
            response["semantic_state"] = session.semantic_state.model_dump()
        if error:
            response["error"] = error

        if session.step == 0:
            operation = (
                session.iteration_draft.operation.value
                if isinstance(session.iteration_draft.operation, IterationOperation)
                else (session.iteration_draft.operation or "ajustar")
            )
            objective = session.iteration_draft.objective or "el diseño"
            if operation == IterationOperation.DEFINE.value and objective == "definición declarativa":
                body = "Quieres definir una propiedad declarativa del sistema actual."
            else:
                body = f"Quieres {operation} {objective} del sistema actual."
            response["message"] = message or (
                f"Proyecto activo: {session.iteration_draft.project_slug} ({session.iteration_draft.project_id})\n"
                f"{body}"
            )
            response["question"] = "¿Correcto?"
            return response

        if session.step == 2 and session.iteration_draft is not None and session.iteration_draft.conflict is not None:
            response["message"] = self._conflict_message(session.iteration_draft.conflict, session.memory_context)
            response["question"] = (
                "¿Quieres:\n"
                "1. mantener el objetivo inicial\n"
                "2. aplicar el nuevo cambio\n"
                "3. cancelar iteración"
            )
            return response

        if session.step == 4 and session.iteration_draft is not None:
            response["message"] = self._impact_message(session.iteration_draft)
            response["question"] = "¿Aplicar cambio?"
            return response

        if session.step == 5 and session.iteration_draft is not None:
            response["message"] = self._final_summary(session.iteration_draft)
            response["question"] = "¿Confirmas la iteración?"
            return response

        prompt = self.PROMPTS[session.step]
        response["message"] = message or "Vamos a definir la iteración paso a paso."
        response["question"] = question or self._question_for_session(session, prompt.question)
        return response

    def _impact_message(self, draft: IterationDraft) -> str:
        estimate = draft.impact_estimate
        if draft.operation == IterationOperation.DEFINE:
            # Bug 44: when the estimate contains a meaningful summary (e.g. no
            # physics data message), surface it instead of the generic fallback.
            # Bug 58: avoid duplication when summary already starts with the prefix.
            if estimate and estimate.summary and estimate.weight_change_percent is None:
                if estimate.summary.startswith("Esta iteración define"):
                    return estimate.summary
                return f"Esta iteración define una propiedad del diseño.\n{estimate.summary}"
            return (
                "Esta iteración define una propiedad del diseño.\n"
                "No se recalcula impacto físico en esta versión."
            )
        lines = ["Estimación:"]
        if estimate.weight_change_percent is not None:
            lines.append(f"- peso: {estimate.weight_change_percent}%")
        if estimate.thrust_impact is not None:
            lines.append(f"- impacto en empuje: {estimate.thrust_impact}")
        if estimate.stability_impact is not None:
            lines.append(f"- impacto en estabilidad: {estimate.stability_impact}")
        lines.append(f"- resumen: {estimate.summary}")
        return "\n".join(lines)

    def _final_summary(self, draft: IterationDraft) -> str:
        return (
            "Resumen de iteración:\n"
            f"- Proyecto: {draft.project_slug} ({draft.project_id})\n"
            f"- Objetivo: {draft.objective}\n"
            f"- Variable: {draft.variable}\n"
            f"- Operación: {draft.operation.value if isinstance(draft.operation, IterationOperation) else draft.operation}\n"
            f"- Estrategia: {draft.strategy}\n"
            f"- Valor: {draft.value}\n"
            f"- Restricciones: {draft.restrictions}\n"
            f"- Impacto estimado: {draft.impact_estimate.summary if draft.impact_estimate else 'pendiente'}"
        )

    def _detect_conflict_response(self, session: InteractiveSessionState, user_input: str) -> dict | None:
        draft = session.iteration_draft
        initial_operation = self._normalize_operation(draft.operation)
        # Extracción fresca desde ESTE input solo — no el estado acumulado,
        # para detectar operaciones que contradicen el objetivo inicial.
        fresh_semantic = sem.update(SemanticState(), user_input)
        new_operation_enum = self._operation_from_semantic(fresh_semantic, fallback=None)
        new_operation = new_operation_enum.value if new_operation_enum else None

        if new_operation == IterationOperation.DEFINE.value:
            return None
        if not self._is_conflicting(initial_operation, new_operation):
            return None

        conflict = IterationConflict(
            initial_objective=draft.objective,
            initial_operation=initial_operation,
            conflicting_operation=new_operation,
            conflicting_input=user_input,
        )
        updated_draft = draft.model_copy(update={"conflict": conflict})
        updated_session = session.model_copy(update={"iteration_draft": updated_draft})
        return self._build_response(updated_session)

    def _conflict_message(self, conflict: IterationConflict, memory_context: dict | None) -> str:
        hint = self._memory_hint(conflict, memory_context)
        message = (
            "Detecto una inconsistencia:\n"
            f"- inicialmente querías {conflict.initial_operation} {conflict.initial_objective}\n"
            f"- ahora estás intentando {conflict.conflicting_input}\n"
            "El nuevo cambio contradice el objetivo inicial y puede cambiar el sentido de la iteración."
        )
        if hint:
            return f"{message}\n{hint}"
        return message

    def _handle_pending_entity_selection(
        self,
        session: InteractiveSessionState,
        user_input: str,
    ) -> dict:
        """
        El usuario ha respondido a "¿Por cuál empezamos?" o está eligiendo
        el próximo componente de la lista pending_entities.
        """
        normalized = user_input.strip().lower()

        # "todos" → registrar todos con completeness=low y pasar a restricciones
        if normalized in {"todos", "all", "todos ellos"}:
            # Check if all entities resolve to the same component type → merge into one
            _reg = self._registry_for_session(session)
            specs = [infer_component(entity, registry=_reg) for entity in session.pending_entities]
            keys = [spec.suggested_key or entity.replace(" ", "_") for spec, entity in zip(specs, session.pending_entities)]
            if len(set(keys)) == 1 and len(keys) > 1:
                # All same type: merge by calling infer_component on the full combined text
                full_text = ", ".join(session.pending_entities)
                merged_spec = infer_component(full_text, registry=_reg)
                updated_patch = {keys[0]: merged_spec}
            else:
                # Different types or single entity: deduplicate keys with index suffix
                updated_patch = {}
                for spec, base_key in zip(specs, keys):
                    key = base_key
                    idx = 2
                    while key in updated_patch:
                        key = f"{base_key}_{idx}"
                        idx += 1
                    updated_patch[key] = spec
            entity_list = ", ".join(session.pending_entities)
            updated_draft = session.iteration_draft.model_copy(
                update={
                    "value": entity_list,
                    "strategy": session.iteration_draft.strategy or f"definir {session.iteration_draft.variable or 'componentes'}",
                    "operation": IterationOperation.DEFINE,
                    "component_patch": updated_patch,
                }
            )
            updated_session = session.model_copy(
                update={"step": 3, "iteration_draft": updated_draft, "pending_entities": []}
            )
            return self._build_response(
                updated_session,
                message=f"Registrados con detalle pendiente: {entity_list}.",
            )

        # selección concreta → tomar ese componente como foco y procesarlo
        focus_entity = user_input.strip()
        spec = infer_component(focus_entity, registry=self._registry_for_session(session, focus_entity))
        feedback = self._definition_feedback_message(focus_entity)

        updated_patch = dict(session.iteration_draft.component_patch or {})
        component_key = spec.suggested_key or focus_entity.replace(" ", "_")
        updated_patch[component_key] = spec

        remaining = [e for e in session.pending_entities if e.lower() != focus_entity.lower()]

        if remaining:
            next_entity = remaining[0]
            still_pending = remaining[1:]
            updated_draft = session.iteration_draft.model_copy(
                update={
                    "operation": IterationOperation.DEFINE,
                    "component_patch": updated_patch,
                }
            )
            updated_session = session.model_copy(
                update={"iteration_draft": updated_draft, "pending_entities": still_pending}
            )
            return self._build_response(
                updated_session,
                message=(
                    f"{feedback}\n"
                    f"Siguiente: {next_entity}. "
                    f"¿Quieres definirlo ahora o escribir 'todos' para registrar el resto con detalle pendiente?"
                ),
            )

        # último componente → avanzar al paso de restricciones
        updated_draft = session.iteration_draft.model_copy(
            update={
                "operation": IterationOperation.DEFINE,
                "strategy": session.iteration_draft.strategy or "definir componentes",
                "value": ", ".join(list(updated_patch.keys())),
                "component_patch": updated_patch,
            }
        )
        updated_session = session.model_copy(
            update={"step": 3, "iteration_draft": updated_draft, "pending_entities": []}
        )
        return self._build_response(updated_session, message=feedback)

    def _find_spec_by_name(self, known_components: dict, name: str):
        """
        Busca un ComponentSpec en known_components por nombre, clave sugerida o clave de dict.
        Primero intenta coincidencia exacta; si falla, coincidencia de prefijo/contenido.
        Devuelve el primero que coincida, o None.
        """
        name_lower = name.strip().lower()
        # Pass 1: exact match
        for key, spec in known_components.items():
            if key.lower() == name_lower:
                return spec
            if (spec.suggested_key or "").lower() == name_lower:
                return spec
            if (spec.name or "").lower() == name_lower:
                return spec
        # Pass 2: prefix / substring match (handles motor↔motors, motor↔motores)
        for key, spec in known_components.items():
            candidates = [
                key.lower(),
                (spec.suggested_key or "").lower(),
                (spec.name or "").lower(),
            ]
            if any(
                c and (c.startswith(name_lower) or name_lower.startswith(c))
                for c in candidates
            ):
                return spec
        return None

    def _seed_semantic_from_state(
        self,
        state: SemanticState,
        known_components: dict,
    ) -> SemanticState:
        """
        Añade al estado semántico las entidades ya conocidas en design_properties.components.
        Autoridad Layer 1 → Layer 3. Solo rellena — nunca sobreescribe confirmed.
        """
        if not known_components:
            return state
        existing_entities = list(known_components.keys())
        if not existing_entities:
            return state
        merged = list(dict.fromkeys(state.entities + existing_entities))
        if merged == state.entities:
            return state
        return state.model_copy(update={"entities": merged})

    def _seed_semantic_from_draft(
        self,
        state: SemanticState,
        draft: IterationDraft | None,
    ) -> SemanticState:
        """
        Añade al estado semántico los valores ya establecidos en el draft,
        como slots 'confirmed'. Solo rellena huecos — nunca sobreescribe.
        """
        if draft is None:
            return state
        slots = dict(state.slots)
        if draft.operation is not None and "operation" not in slots:
            slots["operation"] = SlotValue(
                value=draft.operation.value, confidence=1.0, source="confirmed"
            )
        if draft.variable is not None and "variable" not in slots:
            slots["variable"] = SlotValue(
                value=draft.variable, confidence=1.0, source="confirmed"
            )
        if draft.objective is not None and "objective" not in slots:
            slots["objective"] = SlotValue(
                value=draft.objective, confidence=1.0, source="confirmed"
            )
        if slots == state.slots:
            return state
        return state.model_copy(update={"slots": slots})

    def _missing_slot_question(self, slot_name: str) -> str:
        questions: dict[str, str] = {
            "operation": "¿Qué acción quieres aplicar? (reducir, aumentar, mejorar, definir...)",
            "variable": "¿Sobre qué propiedad o componente quieres trabajar?",
        }
        return questions.get(slot_name, f"Necesito más información sobre: {slot_name}")

    def _operation_from_semantic(
        self,
        semantic_state: SemanticState | None,
        fallback: IterationOperation | None = None,
    ) -> IterationOperation | None:
        """
        Extrae la operación del estado semántico.
        Siempre retorna IterationOperation | None — nunca un raw string.
        """
        if semantic_state is not None:
            op_slot = semantic_state.slots.get("operation")
            if op_slot and op_slot.value:
                try:
                    return IterationOperation(op_slot.value)
                except ValueError:
                    pass
        return fallback

    def _normalize_operation(self, operation: str | None) -> str | None:
        if operation is None:
            return None
        normalized = operation.value if isinstance(operation, IterationOperation) else operation.strip().lower()
        if any(keyword in normalized for keyword in ("defin", "establec", "usar", "seleccion")):
            return IterationOperation.DEFINE.value
        if self._is_increase_operation(normalized):
            return IterationOperation.INCREASE.value
        if any(keyword in normalized for keyword in ("reduc", "disminu", "bajar")):
            return IterationOperation.REDUCE.value
        return normalized

    def _is_increase_operation(self, operation: str | None) -> bool:
        normalized = operation.value.lower() if isinstance(operation, IterationOperation) else (operation or "").lower()
        return any(keyword in normalized for keyword in ("aument", "increment", "subir", "sube"))

    @staticmethod
    def _infer_numeric_operation(
        new_value: float,
        old_value_raw: object,
    ) -> IterationOperation:
        """Infer INCREASE / REDUCE / DEFINE from value comparison.

        - new > old  → INCREASE
        - new < old  → REDUCE
        - new == old → DEFINE (no-op)
        - old unknown → DEFINE (first-time set, direction unknown)
        """
        try:
            old = float(old_value_raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return IterationOperation.DEFINE
        if new_value > old:
            return IterationOperation.INCREASE
        if new_value < old:
            return IterationOperation.REDUCE
        return IterationOperation.DEFINE

    def _is_conflicting(self, initial_operation: str | None, new_operation: str | None) -> bool:
        return {
            initial_operation,
            new_operation,
        } == {"aumentar", "reducir"}

    def _memory_hint(self, conflict: IterationConflict, memory_context: dict | None) -> str | None:
        if not memory_context:
            return None
        history = memory_context.get("conflict_history", [])
        if not history:
            return None
        conflict_type = build_conflict_type(conflict.initial_objective, conflict.initial_operation)
        previous = latest_conflict_by_type(
            ProjectMemory.model_validate(memory_context),
            conflict_type,
        )
        if previous is None:
            return None
        resolution_label = {
            "keep_initial_goal": "mantener el objetivo inicial",
            "apply_new_change": "aplicar el nuevo cambio",
            "cancel_iteration": "cancelar la iteración",
        }.get(previous.resolution, previous.resolution)
        return f"En un conflicto similar anterior elegiste {resolution_label}."

    def _is_keep_initial_resolution(self, normalized: str) -> bool:
        return normalized in {"1", "mantener", "objetivo inicial"} or (
            "mantener" in normalized and "inicial" in normalized
        ) or "mantener el objetivo" in normalized

    def _is_apply_new_change_resolution(self, normalized: str) -> bool:
        return normalized in {"2", "aplicar", "nuevo cambio"} or (
            "aplicar" in normalized and ("nuevo" in normalized or "cambio" in normalized)
        )

    def _is_cancel_resolution(self, normalized: str) -> bool:
        return normalized in {"3", "cancelar", "cancel"} or (
            "cancel" in normalized and "iter" in normalized
        )

    # ── Material helpers (Gap 1) ──────────────────────────────────────────────

    def _extract_material_from_text(self, text: str) -> str | None:
        """Return canonical material name if any known material appears in *text*."""
        normalized = text.lower()
        # Sorted by key length descending so multi-word keys match before substrings.
        for key, canonical in sorted(_KNOWN_MATERIALS.items(), key=lambda x: -len(x[0])):
            if key in normalized:
                return canonical
        return None

    def _awaiting_material_value(self, draft: IterationDraft) -> bool:
        """True when the user said 'cambiar material' but has not yet named the material."""
        return (
            (draft.variable or "").strip().lower() == "material"
            and draft.strategy is not None
            and draft.value is None
            and draft.operation != IterationOperation.DEFINE
        )

    # ── Motor suggestion helpers ──────────────────────────────────────────────

    @staticmethod
    def _project_state_for_session(session: InteractiveSessionState):
        """Best-effort load of ProjectState from the draft workspace (for D8 matching)."""
        draft = session.iteration_draft
        if draft is None or not draft.workspace_path:
            return None
        try:
            from pathlib import Path
            import json
            from jarvis.schemas.state_schema import ProjectState

            path = Path(draft.workspace_path) / "state.json"
            if not path.exists():
                return None
            return ProjectState.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001 — suggestion path must never fail the wizard
            return None

    def _build_motor_suggestions(self, spec, project_state=None) -> list[dict]:
        """Return library suggestions when *spec* is a motor with kv_rating but no thrust_n.

        Only fires when component_type == "propulsion_active" — never for batteries,
        propellers, or other components that may also carry a kv_rating property.
        Returns empty list when thrust_n is already present (user-declared data
        takes absolute priority) or when no motor matches the design space.
        Prefer D8 ``find_motors_for_requirements`` when thrust/prop constraints exist.
        Never auto-applies — for display and selection only.
        """
        # Guard: only motor components trigger this
        if getattr(spec, "component_type", None) != "propulsion_active":
            return []
        props = getattr(spec, "properties", {}) or {}
        if "thrust_n" in props:
            return []  # user already declared thrust — never override
        kv_prop = props.get("kv_rating")
        if kv_prop is None:
            return []

        if project_state is not None:
            from jarvis.core.motor_catalog_assist import build_motor_catalog_suggestions

            kv = int(kv_prop.value)
            return build_motor_catalog_suggestions(
                project_state, library=self._library, kv=kv
            )

        kv = int(kv_prop.value)
        matches = self._library.find_motors_by_kv(kv)
        return [
            {
                "idx": i + 1,
                "name": m.name,
                "thrust_n": m.thrust_n,
                "kv_rating": m.kv_rating,
                "weight_g": m.weight_g,
                "max_watts": m.max_watts,
                "is_generic": m.is_generic,
            }
            for i, m in enumerate(matches)
        ]

    @staticmethod
    def _empty_motor_catalog_note(spec, project_state=None) -> str | None:
        """Explain silent skip when KV/requirements are known but the library has no match."""
        if getattr(spec, "component_type", None) != "propulsion_active":
            return None
        props = getattr(spec, "properties", {}) or {}
        if "thrust_n" in props:
            return None
        kv_prop = props.get("kv_rating")
        if kv_prop is None:
            return None
        kv = int(kv_prop.value)
        need_bits = [f"~{kv}KV"]
        if project_state is not None:
            from jarvis.core.project_closure import derive_physical_requirements
            req = derive_physical_requirements(project_state)
            thrust = req.get("thrust_per_motor_needed_n")
            if thrust is not None:
                need_bits.insert(0, f"empuje ≥ {thrust:.1f} N/motor")
        need = ", ".join(need_bits)
        return (
            f"Necesitas {need}; no tengo un motor en el catálogo que cubra ese espacio. "
            "Cuando puedas, declara el empuje real (N) para calcular."
        )

    @staticmethod
    def _format_motor_suggestions(suggestions: list[dict]) -> str:
        from jarvis.core.motor_catalog_assist import format_motor_catalog_suggestions

        text = format_motor_catalog_suggestions(suggestions)
        if suggestions:
            return text + "\nPara calcular necesito empuje real. Elige un número o di 'no'."
        return text

    def _handle_motor_suggestion_selection(
        self, session: InteractiveSessionState, user_input: str
    ) -> dict:
        """Process the user's answer to the motor-catalog suggestion prompt."""
        normalized = user_input.strip().lower()

        # User declines — clear suggestions and advance to step 3 without thrust
        if normalized in {"no", "n", "ninguno", "ninguna"}:
            updated_session = session.model_copy(update={"step": 3, "motor_suggestions": []})
            return self._build_response(
                updated_session,
                message="De acuerdo. Continúa sin especificar empuje por ahora.",
            )

        # User picks a numbered option
        suggestions = session.motor_suggestions
        for s in suggestions:
            if normalized == str(s["idx"]):
                # Enrich the motor component spec — never replace, only add missing fields
                draft = session.iteration_draft
                component_patch = dict(draft.component_patch or {})
                # Find the motor key by component_type, not by position
                target_key = next(
                    (
                        k for k, v in component_patch.items()
                        if getattr(v, "component_type", None) == "propulsion_active"
                    ),
                    None,
                )
                if target_key is not None:
                    existing_spec = component_patch[target_key]
                    # Preserve all original properties — only add what was missing
                    updated_props = dict(existing_spec.properties or {})
                    updated_props["thrust_n"] = PropertyValue(value=s["thrust_n"], unit="N")
                    updated_props["weight_g"] = PropertyValue(value=s["weight_g"], unit="g")
                    updated_spec = existing_spec.model_copy(
                        update={"properties": updated_props, "completeness": "high"}
                    )
                    component_patch[target_key] = updated_spec
                    updated_draft = draft.model_copy(update={"component_patch": component_patch})
                else:
                    updated_draft = draft
                updated_session = session.model_copy(
                    update={"step": 3, "motor_suggestions": [], "iteration_draft": updated_draft}
                )
                return self._build_response(
                    updated_session,
                    message=f"Usando {s['name']}: {s['thrust_n']}N de empuje, {s['weight_g']}g por motor.",
                )

        # Unrecognised input — re-prompt
        suggestion_text = self._format_motor_suggestions(suggestions)
        return self._build_response(
            session,
            message=f"No entendí la selección.\n{suggestion_text}",
            question="¿Quieres usar alguno? (1/2/… o 'no', especifica el tuyo)",
        )

    # ── Structural downgrade helper (Gap 2) ──────────────────────────────────

    def _should_downgrade_to_declarative(self, draft: IterationDraft) -> bool:
        """True when a structural iteration has no concrete numeric/named value."""
        variable = (draft.variable or "").lower()
        # Numeric params with a value always take the physical path
        all_param_keys = set(_PARAM_DISPLAY_ALIASES.keys()) | set(_PARAM_DISPLAY_ALIASES.values())
        if variable in all_param_keys and bool((draft.value or "").strip()):
            return False
        is_structural = any(
            k in variable for k in ("dimension", "estructura", "topolog", "forma")
        )
        has_concrete_value = bool((draft.value or "").strip())
        return is_structural and not has_concrete_value and draft.operation != IterationOperation.DEFINE

    # ─────────────────────────────────────────────────────────────────────────

    def _match_numeric_param(self, variable: str, current_parameters: dict) -> str | None:
        """Return the canonical current_parameters key if variable names a known numeric param, else None.

        Three recognition tiers; does NOT require the param to already exist in
        current_parameters (e.g. new projects without battery_capacity_wh set yet):
          1. Direct key in current_parameters with numeric value (fastest path)
          2. Display alias → canonical key in current_parameters with numeric value
          3. Display alias → canonical key KNOWN (alias exists) even if not yet set
             — activates the numeric-value path so the wizard asks for the value
             instead of falling through to the strategy question.
        """
        normalized = normalize_alias(variable)
        # 1. Direct key in current_parameters and its value is numeric
        if normalized in current_parameters:
            try:
                float(current_parameters[normalized])
                return normalized
            except (TypeError, ValueError):
                pass
        # 2. Display alias — canonical exists in current_parameters
        canonical = _PARAM_DISPLAY_ALIASES.get(normalized)
        if canonical and canonical in current_parameters:
            try:
                float(current_parameters[canonical])
                return canonical
            except (TypeError, ValueError):
                pass
        # 3. Bug 28 — display alias known even if canonical not yet in project state.
        # A known alias always routes to the numeric-value sub-step regardless of
        # whether the project has defined the param yet.
        if canonical:
            return canonical
        return None

    def _attach_numeric_impact_estimate(
        self,
        draft: IterationDraft,
        canonical: str,
        current_params: dict,
    ) -> IterationDraft:
        """Build a plain-language impact estimate for a numeric parameter change."""
        old_val = current_params.get(canonical)
        old_str = str(round(float(old_val), 4)) if old_val is not None else "?"
        new_str = draft.value or "?"
        summary = (
            f"Cambio directo de parámetro: {draft.variable or canonical} "
            f"{old_str} → {new_str}. Recálculo físico completo."
        )
        return draft.model_copy(update={"impact_estimate": ImpactEstimate(summary=summary)})

    def _needs_definition_value(self, draft: IterationDraft) -> bool:
        if draft.operation != IterationOperation.DEFINE or draft.value:
            return False
        return self._is_supported_define_variable(draft.variable)

    def _input_looks_like_question(self, text: str) -> bool:
        """Returns True when the input looks like a question or instruction rather than a spec value."""
        lower = text.strip().lower()
        if lower.startswith("¿"):
            return True
        QUESTION_STARTERS = (
            "cómo ", "como ", "qué ", "que ", "cuál ", "cual ",
            "por qué ", "por que ", "puedes", "puede ", "podría",
            "quiero que me ayudes", "me ayudes", "ayuda",
        )
        IMPERATIVE_STARTERS = (
            "describe ", "explica ", "muéstrame ", "muéstrame",
            "díme ", "dime ", "explica", "define ",
            "ayúdame", "necesito que",
        )
        return (
            any(lower.startswith(s) for s in QUESTION_STARTERS)
            or any(lower.startswith(s) for s in IMPERATIVE_STARTERS)
            or "ayúdame" in lower
        )

    def _is_supported_define_variable(self, variable: str | None) -> bool:
        normalized = (variable or "").strip().lower()
        if not normalized:
            return False
        if "material" in normalized:
            return True
        return any(token in normalized for token in ("componente", "componentes", "unidad de potencia", "power unit"))

    def _definition_value_question(self, draft: IterationDraft, focus: str | None = None) -> str:
        variable = (draft.variable or "").strip().lower()
        if "material" in variable:
            return "¿Qué material quieres usar? (ej: aluminio, fibra de carbono, plástico reforzado)"
        if focus:
            lines = [f"Describe la especificación del componente '{focus}'."]
            # Show missing fields and hints from the preloaded spec if available
            patch = draft.component_patch or {}
            spec = self._find_spec_by_name(patch, focus)
            if spec and spec.missing_fields:
                lines.append(f"Falta: {', '.join(spec.missing_fields)}.")
            if spec and spec.hints:
                lines.append(f"Pista: {spec.hints[0]}")
            return "\n".join(lines)
        context = " ".join(
            [
                (draft.objective or "").strip().lower(),
                (draft.strategy or "").strip().lower(),
                variable,
            ]
        )
        if any(marker in context for marker in ("unidad de potencia", "power unit", "sistema de potencia")):
            return "¿Qué componentes quieres usar en la unidad de potencia? (ej: motores brushless + ESC 30A)"
        return "¿Qué componentes quieres definir?"

    def _definition_feedback_message(self, value: str) -> str:
        spec = infer_component(value, registry=get_registry(text=value))
        confidence_label = (
            "alta" if spec.inference_confidence >= 0.75
            else "media" if spec.inference_confidence >= 0.5
            else "baja"
        )
        lines = [
            f"Guardado: \"{value}\"",
            f"Tipo inferido: {spec.component_type} (confianza: {confidence_label})",
        ]
        if spec.suggested_key:
            lines.append(f"Clave sugerida (no autoritativa): {spec.suggested_key}")

        if spec.completeness != "high":
            lines.append(f"Nivel de definición: {spec.completeness}")
            if spec.missing_fields:
                lines.append("Falta información:")
                lines.extend(f"- {field}" for field in spec.missing_fields)
            if spec.hints:
                lines.append(f"→ Sugerencia: {spec.hints[0]}")

        return "\n".join(lines)

    def _detect_definition_response(self, session: InteractiveSessionState, user_input: str) -> dict | None:
        draft = session.iteration_draft
        if not self._is_supported_define_variable(draft.variable):
            return None
        if self._operation_from_semantic(session.semantic_state, fallback=draft.operation) != IterationOperation.DEFINE:
            return None

        updated_draft = draft.model_copy(
            update={
                "operation": IterationOperation.DEFINE,
                "strategy": user_input,
            }
        )
        updated_session = session.model_copy(update={"iteration_draft": updated_draft})
        return self._build_response(
            updated_session,
            message="Has indicado una definición declarativa. Necesito el valor explícito para guardarlo en el estado.",
        )

    def _classify_variable_type(self, variable: str, current_params: dict) -> str:
        """Classify *variable* into a UX-routing category for step-2 question selection.

        NOTE: this classification governs question text only — it does NOT decide
        whether a mutation is physically actionable.  Bug 3 (mutation_engine.
        is_physically_actionable) remains the sole execution gate.

        Priority order (most-specific first to avoid false matches):
          1. semantic_mutation   — variable uses a dedicated semantic-mutation path
          2. numeric_direct      — variable names a numeric param in current_parameters
          3. material            — variable maps to material change
          4. structural_physical — quantifiable structural dimension (potentially computable)
          5. structural_abstract — abstract structural concept (always declarative)
          6. component_define    — variable triggers component-definition sub-flow
          7. unknown             — fallback
        """
        norm = (variable or "").strip().lower()
        # 1. semantic_mutation — check FIRST via registry (source of truth).
        #    Variables with variable_type=SEMANTIC_MUTATION have a dedicated path
        #    and must NEVER be routed through direct numeric assignment even when
        #    their key exists in current_parameters (e.g. payload_kg=2.0 is numeric
        #    but the mutation is conceptual — reducir/aumentar, not set-to-value).
        #    NOTE: is_derived is NOT checked here — derived variables are intercepted
        #    in step 1 (before this method is ever called in step 2).
        _req = PARAMETER_REQUIREMENTS.get(variable)
        if _req and _req.variable_type == VariableType.SEMANTIC_MUTATION:
            return "semantic_mutation"
        # 2. numeric_direct — safe now because semantic_mutation already filtered.
        #    Also fires before structural_* so that "factor_estructura" (contains
        #    'estructur') resolves correctly.
        if self._match_numeric_param(variable, current_params) is not None:
            return "numeric_direct"
        # 3. material
        if "material" in norm:
            return "material"
        # 4. structural_physical — potentially computable with an explicit factor
        if any(k in norm for k in ("dimension", "volum", "geometr")):
            return "structural_physical"
        # 5. structural_abstract — always declarative; no numeric path available
        if any(k in norm for k in ("estructur", "forma", "topolog")):
            return "structural_abstract"
        # 6. component_define
        if self._is_supported_define_variable(variable):
            return "component_define"
        # 7. unknown
        return "unknown"

    def _question_for_session(self, session: InteractiveSessionState, default_question: str) -> str:
        draft = session.iteration_draft
        if session.step == 2 and draft is not None:
            if self._needs_definition_value(draft):
                focus = (session.semantic_state.focus if session.semantic_state else None)
                return self._definition_value_question(draft, focus=focus)

            current_params = (session.memory_context or {}).get("current_parameters") or {}
            _var = draft.variable or ""
            # Bugs 14/15: route question by variable type.
            # _classify_variable_type returns most-specific category first, so
            # "factor_estructura" correctly resolves to "numeric_direct" before
            # the "estructur" substring check fires.
            vtype = self._classify_variable_type(_var, current_params)

            if vtype == "numeric_direct":
                canonical = self._match_numeric_param(_var, current_params)
                old_val = current_params.get(canonical, "?") if canonical else "?"
                display_name = _var or canonical
                return f"¿Cuál es el nuevo valor de {display_name}? (actual: {old_val})"

            if vtype == "semantic_mutation":
                display = get_display_name(_var) or _var
                return (
                    f"¿Cómo quieres modificar {display}? "
                    "Indica un valor o cambio concreto (ej: +10%, -0.5 kg, total 3 kg)."
                )

            if vtype == "structural_physical":
                return (
                    "¿Cómo quieres aplicar el cambio?\n"
                    "Los cambios estructurales requieren un factor cuantitativo para impactar la física "
                    "(ej: 'reducir al 85%', 'aumentar volumen 10%'). "
                    "Sin un valor concreto, el cambio se registrará como intención declarativa."
                )

            if vtype == "structural_abstract":
                return (
                    "¿Cómo quieres aplicar el cambio?\n"
                    "Los cambios de estructura/topología/forma no tienen impacto físico computable — "
                    "se registrarán como intención declarativa."
                )

        return default_question

    def get_current_prompt(self, session: InteractiveSessionState) -> str:
        """Return the question the wizard is currently waiting for.

        Used for Bug 51: after an inline interruption (project_status / analyze),
        the caller appends this prompt so the user knows the wizard is still active.
        Reuses the existing _question_for_session machinery — the orchestrator must
        NOT reconstruct this logic independently.
        """
        # step 0: confirmation question is always the same
        if session.step == 0:
            return "¿Correcto?"

        # step 2 conflict override
        if (
            session.step == 2
            and session.iteration_draft is not None
            and session.iteration_draft.conflict is not None
        ):
            return (
                "¿Quieres:\n"
                "1. mantener el objetivo inicial\n"
                "2. aplicar el nuevo cambio\n"
                "3. cancelar iteración"
            )

        # step 4 (impact shown, awaiting apply)
        if session.step == 4:
            return "¿Aplicar cambio?"

        # step 5 (final confirmation)
        if session.step == 5:
            return "¿Confirmas la iteración?"

        # steps 1 and 3 (and fallback for step 2 without conflict)
        prompt = self.PROMPTS[min(session.step, len(self.PROMPTS) - 1)]
        return self._question_for_session(session, prompt.question)
