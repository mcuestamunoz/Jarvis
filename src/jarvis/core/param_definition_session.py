from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

from jarvis.config import ESCAPE_WORDS
from jarvis.core.acquisition_brief import build_acquisition_brief
from jarvis.core.acquisition_target import COMPONENT_PROMPTS, is_navigation_back_phrase
from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_resolver import resolve_propulsion_parameters
from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
from jarvis.core.motor_catalog_assist import (
    ASSISTED_MOTOR_PARAMS,
    MotorSuggestion,
    build_motor_catalog_suggestions,
    derive_kv_prop_filters,
    format_motor_catalog_suggestions,
    format_no_thrust_candidate_message,
    is_bare_watts_input,
    is_help_choose_phrase,
    is_list_motors_phrase,
    looks_like_motor_model_text,
    match_suggestion_by_input,
    resolve_motor_from_text,
)
from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
    MISSING_COMPONENT_DEFINITION,
    all_parameter_names,
    keywords_for_param,
    missing_force_reason_from_warnings,
    missing_params_for_reason,
    param_question,
)
from jarvis.core.state_manager import StateManager
from jarvis.schemas.action_schema import ActionName, ComponentSpec, InteractiveSessionState, OrchestratorMode, PropertyValue
from jarvis.schemas.state_schema import HistoryEntry
from jarvis.simulation.simulator import FlightSimulator
from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS, COMPONENT_MIRRORED_PARAMS
from jarvis.workspace.workspace_manager import WorkspaceManager

logger = logging.getLogger(__name__)

# FN-016: all component suggested_keys across every architecture block —
# single source of truth (system_architecture_catalog.BLOCK_TO_COMPONENTS),
# not orchestrator._COMPONENT_PROMPTS, to avoid a circular import (orchestrator
# already imports this module at load time). A component key is never a
# numeric engineering parameter — answer()'s float/positional parser must
# never assign a value to one, even as defense-in-depth (the normal path
# routes MISSING_COMPONENT_DEFINITION to _handle_component_description before
# answer() is ever called).
_ACQUISITION_COMPONENT_KEYS: frozenset[str] = frozenset(
    key for keys in BLOCK_TO_COMPONENTS.values() for key in keys
)

_STRUCTURAL_PARAMS = ("motor_count",)

_STRUCTURAL_AFFIRMATIVES = frozenset({
    "si", "sí", "s", "ok", "dale", "claro", "venga", "va", "adelante",
    "perfecto", "de acuerdo", "por supuesto", "afirmativo", "vamos",
    "yes", "confirmo",
})
_STRUCTURAL_NEGATIVES = frozenset({
    "no", "n", "cancelar", "cancela", "cancel", "mejor no", "salir", "abortar", "abort", "exit",
})


def begin_structural_confirm(
    state_manager: StateManager,
    *,
    param: str,
    from_value: float,
    to_value: float,
    updates: dict[str, float],
    impact_note: str = "",
    **resume_fields: object,
) -> dict:
    """FN-004: park a structural substitution and ask Sí/No before writing.

    Clears ``pending_define_missing`` to avoid the affirmative race that would
    reopen the define wizard after the user confirms the substitution.
    """
    session = state_manager.get_runtime_session()
    pending: dict = {
        "param": param,
        "from_value": from_value,
        "to_value": to_value,
        "updates": {k: float(v) for k, v in updates.items()},
        **resume_fields,
    }
    state_manager.set_runtime_session(
        session.model_copy(
            update={
                "pending_structural_change": pending,
                "pending_define_missing": False,
            }
        )
    )
    label = "motores" if param == "motor_count" else param
    return {
        "status": "interactive",
        "action": "structural_confirm",
        "message": (
            f"El proyecto usa ahora {int(from_value)} {label}. "
            f"¿Quieres sustituirlos por {int(to_value)}?{impact_note}"
        ),
        "question": "Responde sí para aplicar el cambio, o no para cancelar.",
        "pending_structural_change": pending,
    }


def structural_confirm_needed(
    current_parameters: dict | None,
    new_motor_count: float | None,
) -> tuple[float, float] | None:
    """Return (old, new) when motor_count would replace an existing different value."""
    if new_motor_count is None:
        return None
    if not current_parameters or current_parameters.get("motor_count") is None:
        return None
    try:
        old_f = float(current_parameters["motor_count"])
        new_f = float(new_motor_count)
    except (TypeError, ValueError):
        return None
    if old_f == new_f:
        return None
    return old_f, new_f


# Bug 77: phrases that indicate the user wants to skip/defer a parameter.
# Detected before the numeric parse error so the wizard doesn't block.
_SKIP_PHRASES: frozenset[str] = frozenset({
    "no sé", "no se", "no lo sé", "no lo se",
    "skip", "omitir", "omite",
    "después", "despues", "más tarde", "mas tarde",
    "no tengo", "no dispongo", "no sé aún", "no se aun",
})


# ── Spec builders para bridge D4 ─────────────────────────────────────────────
# Crean ComponentSpecs mínimos con completeness="medium" a partir de un valor
# declarado por el usuario. Solo se usan cuando el wizard de parámetros captura
# valores que pertenecen a componentes (mirrored params). El source="declared"
# indica que el valor viene del usuario, no de una biblioteca.

def _make_battery_spec(capacity_wh: float) -> ComponentSpec:
    return ComponentSpec(
        name=f"bateria_{int(capacity_wh)}Wh",
        component_type="energy_storage",
        suggested_key="battery",
        inference_confidence=0.9,
        completeness="medium",
        source="declared",
        properties={
            "battery_capacity_wh": PropertyValue(
                value=capacity_wh, unit="Wh", confidence=0.95, source="declared"
            )
        },
    )


def _make_motor_spec(power_w: float) -> ComponentSpec:
    return ComponentSpec(
        name=f"motor_{int(power_w)}W",
        component_type="propulsion_active",
        suggested_key="motors",
        inference_confidence=0.85,
        completeness="medium",
        source="declared",
        properties={
            "power_w": PropertyValue(
                value=power_w, unit="W", confidence=0.9, source="declared"
            )
        },
    )


def _make_propeller_spec(diameter_in: float) -> ComponentSpec:
    return ComponentSpec(
        name=f"helice_{diameter_in}in",
        component_type="propulsion_passive",
        suggested_key="propellers",
        inference_confidence=0.85,
        completeness="medium",
        source="declared",
        properties={
            "diameter_in": PropertyValue(
                value=diameter_in, unit="in", confidence=0.9, source="declared"
            )
        },
    )


def _strip_diacritics(text: str) -> str:
    """Remove combining diacritics: 'número' → 'numero', 'motóres' → 'motores'.

    Usa NFD (descomposición canónica), mismo patrón que _normalize en
    system_architecture_catalog. El caller es responsable de llamar .lower()
    antes si necesita comparación case-insensitive.
    """
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


class ParamDefinitionSession:
    def __init__(
        self,
        *,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
        calculation_engine: CalculationEngine,
        simulator: FlightSimulator,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.calculation_engine = calculation_engine
        self.simulator = simulator

    def start(self, missing_params: list[str], reason: str = DEFAULT_MISSING_FORCE_REASON) -> dict:
        if not missing_params:
            return {
                "status": "ok",
                "action": "define_missing_params",
                "message": "No hay parámetros pendientes.",
            }
        suggestions: list[dict] = []
        first = missing_params[0]
        if first in ASSISTED_MOTOR_PARAMS:
            suggestions = self._catalog_suggestions_for_active_project()
        is_component_definition = reason == MISSING_COMPONENT_DEFINITION
        session = InteractiveSessionState(
            mode=OrchestratorMode.DEFINE_MISSING_PARAMETERS,
            step=0,
            pending_param_definitions=list(missing_params),
            collected_params={},
            param_definition_reason=reason,
            motor_suggestions=suggestions,
            # FN-017 B1: keep pending_missing_params coherent with the live
            # wizard for component-definition reasons. Before this, the field
            # went stale to [] the moment the wizard opened (it only ever
            # carried the Bug54 "about to open" signal), and
            # _handle_component_description reads it as expected_keys —
            # meaning a real component description given right after opening
            # Phase A had no scope to match against.
            pending_missing_params=list(missing_params) if is_component_definition else [],
            pending_missing_reason=reason if is_component_definition else "",
        )
        self.state_manager.set_runtime_session(session)
        # FN-017 B5 / FN-018 C1b: opening question for a component-definition
        # wizard is the concrete "describe this component" prompt
        # (COMPONENT_PROMPTS), never the generic "¿Cuál es el valor de
        # propellers?" fallback. FN-018 additionally wraps it in the thin
        # Acquisition Brief (acquisition_brief.build_acquisition_brief) when
        # one exists for this key — degrades to COMPONENT_PROMPTS-only
        # ("message": "") otherwise, identical to FN-017 behavior.
        message = ""
        if is_component_definition and first in COMPONENT_PROMPTS:
            brief = build_acquisition_brief(first, self._safe_active_project())
            message = brief["message"]
            question = brief["question"]
        else:
            question = self._question_for_param(first, suggestions)
        result: dict = {
            "status": "interactive",
            "action": "define_missing_params",
            "question": question,
            "pending": list(missing_params),
            "motor_suggestions": suggestions,
        }
        if message:
            result["message"] = message
        return result

    def _safe_active_project(self):
        try:
            return self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None

    def _catalog_suggestions_for_active_project(self) -> list[MotorSuggestion]:
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return []
        return build_motor_catalog_suggestions(project_state)

    def _thrust_hint_for_active_project(self) -> float | None:
        from jarvis.core.project_closure import derive_physical_requirements

        try:
            state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None
        return derive_physical_requirements(state).get("thrust_per_motor_needed_n")

    def _question_for_param(self, param: str, suggestions: list[dict] | None = None) -> str:
        from jarvis.core.parameter_requirements import param_question_with_context

        thrust_hint = self._thrust_hint_for_active_project()
        return param_question_with_context(
            param, suggestions=suggestions, thrust_hint_n=thrust_hint
        )

    def _offer_catalog_help(self, session: InteractiveSessionState, pending: list[str]) -> dict:
        suggestions = self._catalog_suggestions_for_active_project()
        updated = session.model_copy(update={"motor_suggestions": suggestions})
        self.state_manager.set_runtime_session(updated)
        if not suggestions:
            # FN-009: honest deterministic gap — requirement, catalog coverage,
            # concrete options. Never invents a SKU or mutates motor_count.
            thrust_hint = self._thrust_hint_for_active_project()
            # Continuity Hardening ★6: same kv/prop filters the (empty)
            # suggestions search above already used, so "máximo cubierto"
            # never quotes an unfiltered figure next to a filtered verdict.
            try:
                active_state = self.state_manager.load_active_project(self.workspace_manager)
            except FileNotFoundError:
                active_state = None
            kv_hint, prop_inch = derive_kv_prop_filters(active_state)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": format_no_thrust_candidate_message(
                    required_n=thrust_hint, kv=kv_hint, prop_inch=prop_inch
                ),
                "question": self._question_for_param(pending[0], []),
                "pending": list(pending),
                "motor_suggestions": [],
            }
        # FN-009 copy fix: pending param decides N (thrust) vs W (power) copy —
        # the catalog matching/pick flow itself is unchanged either way.
        current = pending[0]
        if current == "per_motor_max_thrust_n":
            question = (
                "Elige un número, indica empuje en N (de una combinación motor-hélice) "
                "o di 'no' para omitir."
            )
        else:
            question = "Elige un número de la lista, o indica W a mano."
        return {
            "status": "interactive",
            "action": "define_missing_params",
            # G16-B: question (below) already carries the "Elige un número..."
            # instruction — suppress the formatter's own trailing copy of it
            # so the CLI doesn't render the same CTA twice.
            "message": format_motor_catalog_suggestions(
                suggestions, param=current, include_cta=False
            ),
            "question": question,
            "pending": list(pending),
            "motor_suggestions": suggestions,
        }

    def offer_catalog_help(self) -> dict:
        """FN-006: session-level public entry point for catalog assistance.

        Resolves the active runtime session and its pending param definitions
        internally, then delegates to the existing worker.
        """
        session = self.state_manager.get_runtime_session()
        pending = list(session.pending_param_definitions)
        return self._offer_catalog_help(session, pending)

    def _apply_catalog_motor_pick(
        self, suggestion: MotorSuggestion, session: InteractiveSessionState, pending: list[str]
    ) -> dict:
        """Apply a catalog pick: power bridge + rich motors component, then continue wizard.

        FN-009: a catalog pick always resolves motor_power_w AND
        per_motor_max_thrust_n coherently (same physical motor produces both).
        Only params actually pending are removed from the wizard queue —
        ASSISTED_MOTOR_PARAMS is exactly the set a single pick can satisfy.
        """
        watts = float(suggestion["max_watts"])
        collected = {**session.collected_params, "motor_power_w": watts}
        remaining = [p for p in pending if p not in ASSISTED_MOTOR_PARAMS]

        # Persist rich motor component (power/thrust/kv/weight + preserved
        # motor_count + catalog_ref identity) before recalc.
        # output_magnitude="thrust_n" on the spec (set in bind_motor_from_catalog)
        # lets resolve_propulsion_parameters derive per_motor_max_thrust_n from
        # the component on every recalculation below — no separate manual
        # current_parameters patch needed here, so there is a single coherent
        # write followed by a single recalculation. Catalog v1 (Impl B): shared
        # with the iterate wizard's catalog pick via bind_motor_from_catalog —
        # both paths set catalog_ref identically, no dual divergence.
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
            spec = bind_motor_from_catalog(suggestion)
            project_state = set_motor_component(project_state, spec, watts)
            self.workspace_manager.save_state(project_state)
        except FileNotFoundError:
            pass

        if remaining:
            next_suggestions = (
                self._catalog_suggestions_for_active_project()
                if remaining[0] in ASSISTED_MOTOR_PARAMS
                else []
            )
            updated = session.model_copy(
                update={
                    "pending_param_definitions": remaining,
                    "collected_params": collected,
                    "motor_suggestions": next_suggestions,
                }
            )
            self.state_manager.set_runtime_session(updated)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": (
                    f"Motor elegido: {suggestion['name']} "
                    f"(~{int(watts)}W, {suggestion['thrust_n']}N)."
                ),
                "question": self._question_for_param(remaining[0], next_suggestions),
                "pending": remaining,
                "project_change_summary": f"motor → {suggestion['name']} (~{int(watts)}W)",
            }

        self.state_manager.clear_runtime_session()
        # Rich motors component already saved — do not re-bridge motor_power_w/
        # per_motor_max_thrust_n via param_updates (would fight the resolver's
        # output_magnitude-driven derivation and risk stale/duplicate writes).
        other_updates = {k: v for k, v in collected.items() if k not in ASSISTED_MOTOR_PARAMS}
        result = self.apply_and_recalculate(other_updates, confirmed=True)
        result["project_change_summary"] = (
            f"motor → {suggestion['name']} (~{int(watts)}W)"
        )
        result["message"] = (
            f"Motor elegido: {suggestion['name']} (~{int(watts)}W, "
            f"{suggestion['thrust_n']}N). Sistema recalculado."
        )
        return result

    def _answer_assisted_motor(
        self,
        user_input: str,
        session: InteractiveSessionState,
        pending: list[str],
        suggestions: list[MotorSuggestion],
    ) -> dict | None:
        """FN-005/FN-006: catalog help / pick / model while defining motor power.

        Returns ``None`` when nothing in the assisted-motor branch matched, so
        the caller falls through to the generic numeric/keyword parsing in
        ``answer()``.
        """
        current = pending[0]
        # Continuity Hardening ★5 (G15): "qué motores tenemos en el catálogo"
        # today falls all the way to answer()'s "No reconozco X como valor"
        # (investigation A12) — reuse the same deterministic listing
        # "ayúdame a elegir" already returns; no new formatter, no LLM, wizard
        # stays open (offer_catalog_help never clears pending).
        if is_list_motors_phrase(user_input) or is_help_choose_phrase(user_input):
            return self.offer_catalog_help()
        picked = match_suggestion_by_input(user_input, suggestions) if suggestions else None
        if picked is None:
            # Also try against fresh catalog (inline numbers from start, or full library name)
            fresh = suggestions or self._catalog_suggestions_for_active_project()
            picked = match_suggestion_by_input(user_input, fresh)
            if picked is None:
                picked = resolve_motor_from_text(user_input)
        if picked is not None:
            return self._apply_catalog_motor_pick(picked, session, pending)
        # Decline catalog → re-ask for manual W
        _norm = unicodedata.normalize("NFC", user_input.strip().lower())
        if _norm in {"no", "n", "ninguno", "ninguna"} and suggestions:
            cleared = session.model_copy(update={"motor_suggestions": []})
            self.state_manager.set_runtime_session(cleared)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": "De acuerdo. Indica la potencia aproximada en W.",
                "question": self._question_for_param(current, []),
                "pending": list(pending),
            }
        # Model-like text that didn't resolve — never scrape MN3508 as watts
        if looks_like_motor_model_text(user_input) and not is_bare_watts_input(user_input):
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "error": (
                    f"No encuentro el motor '{user_input.strip()}' en el catálogo. "
                    "Elige un número de la lista, indica W (ej: 350), "
                    "o di 'ayúdame a elegir'."
                ),
                "question": self._question_for_param(current, suggestions),
                "pending": list(pending),
            }
        # Only accept numeric power when input is bare watts or keyword+number
        if not is_bare_watts_input(user_input):
            bidir = self.parse_params_bidir(user_input, ["motor_power_w"])
            if "motor_power_w" not in bidir:
                # Digits embedded with letters without potencia keyword → refuse
                if self.parse_floats_from_input(user_input) and re.search(
                    r"[a-záéíóúñA-ZÁÉÍÓÚÑ]", user_input
                ):
                    return {
                        "status": "interactive",
                        "action": "define_missing_params",
                        "error": (
                            "No reconozco ese valor como potencia en W ni como modelo "
                            "de catálogo. Ejemplo: 350  ·  o  'ayúdame a elegir'."
                        ),
                        "question": self._question_for_param(current, suggestions),
                        "pending": list(pending),
                    }
        return None

    def answer(self, user_input: str) -> dict:
        session = self.state_manager.get_runtime_session()

        if user_input.strip().lower() in ESCAPE_WORDS:
            self.state_manager.clear_runtime_session()
            return {
                "status": "cancelled",
                "action": "define_missing_params",
                "message": "Definición cancelada. Puedes retomar cuando quieras.",
            }

        # FN-016: navigation words ("atrás"/"volver"/"vuelve") are never a value
        # and never a skip — same cancel outcome as ESCAPE_WORDS, so backing out
        # of the wizard doesn't produce "No reconozco 'atrás' como valor."
        # Fallback for direct callers (tests/tools); the orchestrator already
        # short-circuits this earlier in the DEFINE_MISSING_PARAMETERS branch.
        if is_navigation_back_phrase(user_input):
            self.state_manager.clear_runtime_session()
            return {
                "status": "cancelled",
                "action": "define_missing_params",
                "message": "Definición cancelada. Puedes retomar cuando quieras.",
            }

        pending = list(session.pending_param_definitions)
        if not pending:
            self.state_manager.clear_runtime_session()
            return {"status": "ok", "action": "define_missing_params", "message": "Sesión ya completada."}

        current = pending[0]
        suggestions = list(session.motor_suggestions or [])

        # FN-005/FN-006: catalog help / pick / model while defining motor power
        if current in ASSISTED_MOTOR_PARAMS:
            assisted_result = self._answer_assisted_motor(user_input, session, pending, suggestions)
            if assisted_result is not None:
                return assisted_result

        # FN-016: a component key (motors/propellers/battery/frame/…) is never
        # a numeric engineering parameter. Defense-in-depth: the normal path
        # never reaches answer() for these (orchestrator routes
        # MISSING_COMPONENT_DEFINITION to _handle_component_description first),
        # but if pending[0] is ever a component key here, refuse to zip a bare
        # float onto it and re-prompt instead.
        if current in _ACQUISITION_COMPONENT_KEYS:
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": f"Seguimos definiendo {current}.",
                "question": self._question_for_param(current, suggestions),
                "pending": list(pending),
            }

        values = self.parse_floats_from_input(user_input)
        if not values:
            _normalized = unicodedata.normalize("NFC", user_input.strip().lower())
            if _normalized in {"si", "sí", "yes", "ok", "dale", "adelante", "claro"}:
                return {
                    "status": "interactive",
                    "action": "define_missing_params",
                    "question": self._question_for_param(pending[0], suggestions),
                }
            # Bug 77: skip phrases — user wants to defer the current parameter.
            # Remove it from pending and continue; apply_and_recalculate is called
            # once all params are either answered or skipped.
            if _normalized in _SKIP_PHRASES:
                remaining = pending[1:]
                if remaining:
                    next_sugg = (
                        self._catalog_suggestions_for_active_project()
                        if remaining[0] in ASSISTED_MOTOR_PARAMS
                        else []
                    )
                    updated_session = session.model_copy(
                        update={
                            "pending_param_definitions": remaining,
                            "motor_suggestions": next_sugg,
                        }
                    )
                    self.state_manager.set_runtime_session(updated_session)
                    return {
                        "status": "interactive",
                        "action": "define_missing_params",
                        "message": f"Parámetro '{pending[0]}' omitido — puedes definirlo después.",
                        "question": self._question_for_param(remaining[0], next_sugg),
                    }
                # All params processed (some skipped) — apply whatever was collected.
                self.state_manager.clear_runtime_session()
                return self.apply_and_recalculate(session.collected_params)
            hint = ""
            if current in ASSISTED_MOTOR_PARAMS:
                hint = " Puedes dar W, un modelo, o decir 'ayúdame a elegir'."
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "error": f"No reconozco '{user_input}' como valor.{hint}",
                "question": self._question_for_param(pending[0], suggestions),
            }

        keyword_matches = self.parse_params_bidir(user_input, pending)
        # Legacy forward-only fallback — kept as safety net; remove once bidir is confirmed stable
        # if not keyword_matches:
        #     keyword_matches = self.parse_params_from_keywords(user_input, pending)
        if keyword_matches:
            collected = {**session.collected_params, **keyword_matches}
            remaining = [param for param in pending if param not in keyword_matches]
        else:
            collected = {**session.collected_params}
            remaining = []
            values_iter = iter(values)
            for param in pending:
                # FN-016: defense-in-depth — never zip a bare float onto a
                # component key, even if it's not the first pending item.
                # It stays pending; no value is consumed for it.
                if param in _ACQUISITION_COMPONENT_KEYS:
                    remaining.append(param)
                    continue
                try:
                    collected[param] = next(values_iter)
                except StopIteration:
                    remaining.append(param)

        if remaining:
            next_sugg = (
                self._catalog_suggestions_for_active_project()
                if remaining[0] in ASSISTED_MOTOR_PARAMS
                else []
            )
            updated_session = session.model_copy(
                update={
                    "pending_param_definitions": remaining,
                    "collected_params": collected,
                    "motor_suggestions": next_sugg,
                }
            )
            self.state_manager.set_runtime_session(updated_session)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "question": self._question_for_param(remaining[0], next_sugg),
            }

        self.state_manager.clear_runtime_session()
        return self.apply_and_recalculate(collected)

    def try_ingest(self, user_input: str) -> dict | None:
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None

        simulation = project_state.latest_results.get("simulation") or {}
        physics_incomplete = simulation.get("physics_status") == "missing_parameters"

        if physics_incomplete:
            current_params = project_state.current_parameters or {}
            reason = missing_force_reason_from_warnings(simulation.get("warnings") or [])
            missing_params = missing_params_for_reason(reason, current_params)
            if not missing_params:
                return None
            # D4: mirrored params are written via component writers, not directly
            missing_params = [p for p in missing_params if p not in COMPONENT_MIRRORED_PARAMS]
            if not missing_params:
                return None

            parsed = self.parse_params_bidir(user_input, missing_params)
            if parsed:
                result = self.apply_and_recalculate(parsed)
                remaining = [param for param in missing_params if param not in parsed]
                if remaining:
                    new_sim = result.get("simulation") or {}
                    if new_sim.get("physics_status") == "missing_parameters":
                        return self.start(remaining, reason=reason)
                return result

            normalized_input = user_input.lower()
            keyword_matched = [
                param
                for param in missing_params
                if any(keyword.lower() in normalized_input for keyword in keywords_for_param(param))
            ]
            if keyword_matched:
                seen = set(keyword_matched)
                ordered = list(keyword_matched) + [param for param in missing_params if param not in seen]
                return self.start(ordered, reason=reason)

            return None

        parsed = self.parse_params_bidir(user_input, all_parameter_names())
        if parsed:
            return self.apply_and_recalculate(parsed)
        return None

    def apply_and_recalculate(
        self, param_updates: dict[str, float], *, confirmed: bool = False
    ) -> dict:
        # K2: normalizar alias de motor count antes de procesar.
        # Cubre callers externos que pasen 'motors' en vez de 'motor_count'.
        # Nota: no usar {**d, key: d.pop(key)} — el ** spread ocurre antes del pop.
        if "motors" in param_updates and "motor_count" not in param_updates:
            param_updates = dict(param_updates)
            param_updates["motor_count"] = param_updates.pop("motors")
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return {
                "status": "error",
                "action": "define_missing_params",
                "message": "No hay proyecto activo para aplicar los parámetros.",
            }

        # FN-004: conscious substitution for structural params already defined
        if not confirmed:
            for key in _STRUCTURAL_PARAMS:
                if key not in param_updates:
                    continue
                needed = structural_confirm_needed(
                    project_state.current_parameters, param_updates.get(key)
                )
                if not needed:
                    continue
                old_f, new_f = needed
                margin = None
                sim = (project_state.latest_results or {}).get("simulation") or {}
                if sim.get("safety_margin_ratio") is not None:
                    margin = float(sim["safety_margin_ratio"])
                impact = ""
                if margin is not None:
                    impact = f" Margen de seguridad actual: {margin:.2f}."
                return begin_structural_confirm(
                    self.state_manager,
                    param=key,
                    from_value=old_f,
                    to_value=new_f,
                    updates={k: float(v) for k, v in param_updates.items()},
                    impact_note=impact,
                )

        # === MIRRORED PARAM CONTRACT — punto de aplicación ===
        # Los params en COMPONENT_MIRRORED_PARAMS no se escriben directamente
        # en current_parameters. Se enrutan a través de los component writers
        # (ver contract header en component_writers.py) que escriben atómicamente
        # en components[key] (canónico) Y en current_parameters[param] (bridge).
        #
        # Si se añade un nuevo mirrored param:
        #   1. Añadir la clave a COMPONENT_MIRRORED_PARAMS
        #   2. Crear su writer en component_writers.py (cumpliendo el contrato)
        #   3. Añadir su spec builder (_make_*_spec) en este archivo
        #   4. Añadir su rama en el bloque `if blocked:` de abajo
        #   5. Añadir test_mirrored_param_contract_* en test_d4_param_gatekeeper.py
        blocked = set(param_updates.keys()) & COMPONENT_MIRRORED_PARAMS
        bridged_updates: dict[str, float] = {}
        if blocked:
            logger.debug("D4: bridging mirrored params through component writers: %s", blocked)
            if "battery_capacity_wh" in blocked:
                cap = param_updates["battery_capacity_wh"]
                project_state = set_battery_component(project_state, _make_battery_spec(cap), cap)
                bridged_updates["battery_capacity_wh"] = cap
            if "motor_power_w" in blocked:
                pw = param_updates["motor_power_w"]
                project_state = set_motor_component(project_state, _make_motor_spec(pw), pw)
                bridged_updates["motor_power_w"] = pw
            if "propeller_diameter_in" in blocked:
                d = param_updates["propeller_diameter_in"]
                project_state = set_propeller_component(project_state, _make_propeller_spec(d))
                bridged_updates["propeller_diameter_in"] = d

        filtered_updates = {k: v for k, v in param_updates.items() if k not in COMPONENT_MIRRORED_PARAMS}

        # current_parameters already contains bridged values (set by writers above).
        # filtered_updates (non-mirrored) override on top.
        updated_params = {**project_state.current_parameters, **filtered_updates}
        propulsion_override = resolve_propulsion_parameters(
            {key: value.model_dump() for key, value in project_state.design_properties.components.items()}
        )
        updated_params = propulsion_override.apply_to(updated_params)
        # User-provided parameters have absolute priority over inferred/declarative values.
        # Layer rule: user input > component inference > parameter defaults.
        updated_params = {**updated_params, **filtered_updates}

        calculations = self.calculation_engine.build(updated_params)
        autonomy_threshold = project_state.parsed_constraints.get("autonomy_min")
        simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)

        workspace_path = Path(project_state.workspace_path)
        iteration_index = project_state.active_iteration
        iteration_path = self.workspace_manager.save_iteration_snapshot(
            workspace_path,
            iteration_index,
            {
                "iteration_id": iteration_index,
                "event": "params_defined",
                "params": {**bridged_updates, **filtered_updates},
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
                "design_properties": project_state.design_properties.model_dump(),
                "current_parameters": updated_params,
            },
        )

        all_written = {**bridged_updates, **filtered_updates}
        param_str = ", ".join(f"{key}={value}" for key, value in all_written.items())
        history_entry = HistoryEntry(
            action=ActionName.ITERATE,
            summary=f"Parámetros definidos: {param_str}.",
            artifacts={"iteration": str(iteration_path)},
        )
        updated_state = self.state_manager.record_action(
            state=project_state.model_copy(update={"current_parameters": updated_params}),
            action=history_entry,
            latest_results={
                "mutation": {"state_patch": all_written, "mode": "physical"},
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
            },
            increment_iteration=True,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "params_defined",
            {"iteration_id": iteration_index, "params": list(all_written.keys())},
        )
        self.workspace_manager.render_views(workspace_path, updated_state)

        # Clear any pending structural confirmation
        session = self.state_manager.get_runtime_session()
        if session.pending_structural_change:
            self.state_manager.set_runtime_session(
                session.model_copy(update={"pending_structural_change": None})
            )

        change_bits = []
        for k, v in all_written.items():
            if k == "motor_count":
                change_bits.append(f"motores → {int(v)}")
            else:
                change_bits.append(f"{k}={v}")
        change_summary = ", ".join(change_bits) if change_bits else param_str

        return {
            "status": "ok",
            "action": "define_missing_params",
            "message": f"Parámetros aplicados: {param_str}. Sistema recalculado.",
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "project_id": project_state.project_id,
            "project_change_summary": change_summary,
        }

    def resolve_structural_confirm(self, user_input: str) -> dict | None:
        """FN-004: sí/no for pending substitution (param-only resume).

        When pending has ``resume_kind`` (component / iterate), the orchestrator
        must handle affirmation — this method only clears + applies param updates
        or cancels / re-prompts.
        """
        session = self.state_manager.get_runtime_session()
        pending = session.pending_structural_change
        if not pending:
            return None
        normalized = user_input.strip().lower()
        if normalized in _STRUCTURAL_AFFIRMATIVES:
            if pending.get("resume_kind"):
                # Orchestrator resumes the original path; signal via special status.
                return {
                    "status": "structural_resume",
                    "action": "structural_confirm",
                    "pending_structural_change": pending,
                }
            updates = {k: float(v) for k, v in (pending.get("updates") or {}).items()}
            self.state_manager.set_runtime_session(
                session.model_copy(update={"pending_structural_change": None})
            )
            return self.apply_and_recalculate(updates, confirmed=True)
        if normalized in _STRUCTURAL_NEGATIVES:
            self.state_manager.set_runtime_session(
                session.model_copy(update={"pending_structural_change": None})
            )
            return {
                "status": "cancelled",
                "action": "structural_confirm",
                "message": "Cambio cancelado. El proyecto conserva la configuración anterior.",
            }
        return {
            "status": "interactive",
            "action": "structural_confirm",
            "message": (
                f"Pendiente: sustituir {pending.get('param')} "
                f"{pending.get('from_value')} → {pending.get('to_value')}."
            ),
            "question": "Responde sí para aplicar, o no para cancelar.",
        }

    def param_question(self, param: str) -> str:
        return param_question(param)

    def parse_params_from_keywords(self, user_input: str, pending: list[str]) -> dict[str, float]:
        normalized = user_input.lower().replace(",", ".")
        result: dict[str, float] = {}
        number_pattern = r"(\d+(?:\.\d+)?)"
        for param in pending:
            for keyword in keywords_for_param(param):
                keyword_re = re.escape(keyword.lower())
                match = re.search(rf"{keyword_re}.{{0,40}}?{number_pattern}", normalized)
                if match:
                    try:
                        result[param] = float(match.group(1))
                    except ValueError:
                        pass
                    break
        return result

    def parse_floats_from_input(self, user_input: str) -> list[float]:
        normalized = user_input.replace(",", ".")
        result = []
        for match in re.findall(r"\d+(?:\.\d+)?", normalized):
            try:
                result.append(float(match))
            except ValueError:
                pass
        return result

    def parse_float_from_input(self, user_input: str) -> float | None:
        values = self.parse_floats_from_input(user_input)
        return values[0] if values else None

    def parse_params_bidir(self, user_input: str, pending: list[str]) -> dict[str, float]:
        """Bidirectional keyword→number parser.

        Rules:
        - Both text and keywords are diacritic-normalised before matching.
        - Keyword matches require word boundaries (\b) to avoid partial matches
          (e.g. "motor" must not fire inside "motores").
        - Each number position may only be consumed once across all params
          (used_positions set). This prevents `"potencia motor 50"` from
          assigning 50 to both `motors` and `motor_power_w`.
        - When multiple numbers are equidistant from a keyword centre, numbers
          that appear AFTER the keyword are preferred (more natural in Spanish).
        """
        normalized = _strip_diacritics(user_input.lower().replace(",", "."))
        number_positions: list[tuple[int, float]] = []
        for match in re.finditer(r"\d+(?:\.\d+)?", normalized):
            try:
                number_positions.append((match.start(), float(match.group())))
            except ValueError:
                pass
        if not number_positions:
            return {}

        result: dict[str, float] = {}
        used_positions: set[int] = set()

        for param in pending:
            if param in result:
                continue
            for keyword in keywords_for_param(param):
                keyword_norm = _strip_diacritics(keyword.lower())
                keyword_re = r"\b" + re.escape(keyword_norm) + r"\b"
                keyword_match = re.search(keyword_re, normalized)
                if not keyword_match:
                    continue
                kw_center = (keyword_match.start() + keyword_match.end()) // 2

                # Candidates: within 40 chars and not already consumed.
                # Tuples are (distance, text_position, value) so that on an
                # exact distance tie the leftmost number wins (stable, predictable).
                candidates = [
                    (abs(num_pos - kw_center), num_pos, value)
                    for num_pos, value in number_positions
                    if abs(num_pos - kw_center) <= 40 and num_pos not in used_positions
                ]
                if not candidates:
                    continue

                candidates.sort(key=lambda c: (c[0], c[1]))
                _, best_pos, value = candidates[0]
                result[param] = value
                used_positions.add(best_pos)
                break

        return result
