from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any

from jarvis.actions.calculate import CalculateAction
from jarvis.actions.create_project import CreateProjectAction
from jarvis.actions.iterate import IterateAction
from jarvis.actions.simulate import SimulateAction
from jarvis.core.acquisition_brief import build_acquisition_brief
from jarvis.core.acquisition_target import (
    COMPONENT_PROMPTS,
    OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS,
    is_define_missing_confusion_phrase,
    is_mention_on_active_gap,
    is_navigation_back_phrase,
    resolve_acquisition_mention,
    user_explicitly_named_component,
)
from jarvis.core.action_router import ActionRouter
from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.interactive_session import CreateProjectInteractiveSession
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.iterate_interactive_session import IterateInteractiveSession
from jarvis.core.param_definition_session import ParamDefinitionSession
from jarvis.core.project_closure import component_presence_tier
from jarvis.core.system_definition_session import SystemDefinitionSession
from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
    MISSING_PROPELLER_PARAMETERS,
    MISSING_PROPULSION_PARAMETERS,
    missing_force_reason_from_warnings,
    missing_params_for_reason,
    params_for_reason,
    reason_hint,
)
from jarvis.core.phase_layer import PhaseLayer
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.core.goal_planner import (
    GOAL_STRATEGIES,
    detect_goal,
    format_goal_plan,
    get_goal_context_for_llm,
    is_engineering_intention,
)
from jarvis.core.handoff_matching import match_plan_lever
from jarvis.core.component_writers import (
    set_battery_component,
    set_control_component,
    set_frame_material,
    set_motor_component,
    set_propeller_component,
)
from jarvis.core.design_explorer import DesignExplorer, _apply_delta, _is_catalog_native_motor_candidate
from jarvis.core.system_architecture_catalog import (
    BLOCK_TO_COMPONENTS,
    SYSTEM_ARCHITECTURES,
    VEHICLE_TYPE_ALIASES,
    get_block_type,
    get_param_reason_for_block,
)
from jarvis.schemas.state_schema import HistoryEntry, ProjectState
from jarvis.memory.memory_manager import MemoryManager
from jarvis.core.mutation_engine import MutationEngine
from jarvis.core.planner import Planner, requires_planning
from jarvis.core.state_manager import StateManager
from jarvis.schemas.action_schema import (
    ActionName,
    ActionRequest,
    ComponentSpec,
    HandoffContext,
    InteractiveSessionState,
    IterationDraft,
    IterationOperation,
    OrchestratorMode,
    ProjectDraft,
)
from jarvis.schemas.semantic_schema import SemanticState
from jarvis.config import ESCAPE_WORDS, NEW_PROJECT_WORDS
from jarvis.llm.semantic_intent_adapter import AdaptRejection, SemanticIntentAdapter, SemanticInterpretation
from jarvis.simulation.simulator import FlightSimulator
from jarvis.suggestions.suggestion_engine import SuggestionEngine
from jarvis.workspace.workspace_manager import WorkspaceManager
from jarvis.utils.design_utils import get_frame_material


# ── Display helpers ────────────────────────────────────────────────────────────

def _get_frame_material_display(design_properties) -> str:
    """Lectura canónica del material para display / contexto LLM.
    Usa el Single Read Point de Fase 3 en lugar del mirror legacy structure.material.
    """
    return get_frame_material(design_properties)


def _is_stub_or_absent(spec: Any) -> bool:
    """Prop-3 ★4: a component that still needs definition — absent, or
    completeness == "low"."""
    return spec is None or (getattr(spec, "completeness", None) or "low") == "low"


def _wants_catalog_help(spec: Any) -> bool:
    """Prop-3 ★4: "wants catalog help" predicate for help-choose / pick
    dispatch — true when the component is a stub/absent (needs definition)
    OR when it's freeform-declared without a catalog_ref (the G21
    upgrade-to-SKU case). Deliberately NOT bare key membership in
    expected_keys, which starves a later branch in a composite wizard once
    an earlier key is done (see investigation_report_propeller_catalog_bind_ux.md §4)."""
    if _is_stub_or_absent(spec):
        return True
    return getattr(spec, "catalog_ref", None) is None


def _parse_propulsion_resolution(raw: str | None) -> dict[str, Any] | None:
    """Phase 2 P2-1: current_parameters["propulsion_resolution"] is stored as
    a JSON string (must stay hashable for design_explorer's candidate cache
    — see component_writers.set_motor_component). Parsed back to a dict only
    here, for the estado/CLI surface."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _motor_op_electrical_from_params(params: dict[str, Any]) -> dict[str, Any] | None:
    """P2-2 (Operating Point Bridge): estado/CLI surface for the OP-electrical
    calc-bridge keys (component_writers.set_motor_component, exact/fallback
    only) — None when no operating point was resolved (legacy_estimate or
    unbound/freeform motor), so the caller can render a distinct "OP
    eléctrico" line only when there is real OP evidence to show, never a
    fabricated one alongside the catalog rating."""
    power_w = params.get("motor_op_power_w")
    current_a = params.get("motor_op_current_a")
    rpm = params.get("motor_op_rpm")
    if power_w is None and current_a is None and rpm is None:
        return None
    return {"power_w": power_w, "current_a": current_a, "rpm": rpm}


def _hover_energy_from_calculations(calculations: dict[str, Any] | None) -> dict[str, Any] | None:
    """Phase 2.5 (Hover Flight Energy Model, ★★10/§2.4): estado/CLI surface
    for the hover-regime resolution — distinct from both propulsion_resolution
    (bind-time feasibility/max-thrust) and motor_operating_point_electrical
    (that same bench-max OP's raw numbers). Lives in latest_results
    ["calculations"] (CalculationBundle output), not current_parameters —
    it is a calc-time derivation, not a component-bind mirror. None when no
    calculation has run yet, or the bound motor has no Discrete OP Dataset
    for its exact identity at all (calc_engine's honest-absence case)."""
    if not calculations:
        return None
    resolution_raw = calculations.get("hover_energy_resolution")
    if not resolution_raw:
        return None
    try:
        resolution = json.loads(resolution_raw)
    except (TypeError, ValueError):
        return None
    resolution["hover_energy_autonomy_min"] = calculations.get("hover_energy_autonomy_min")
    return resolution


def _battery_endurance_from_calculations(calculations: dict[str, Any] | None) -> dict[str, Any] | None:
    """Phase 2.7-B (Parametric / Estimative Battery Endurance Sweep,
    ★★1-★★13): estado/CLI surface for the OPT-IN endurance envelope —
    distinct from ``hover_energy`` above (motor-input, always-on when
    identity permits) and never merged with it. None whenever the caller
    didn't supply a sweep for this calculation (the common case) — no
    envelope, no ESTIMATIVE line, nothing to show."""
    if not calculations:
        return None
    envelope = calculations.get("battery_endurance_envelope")
    if not envelope:
        return None
    assumption_raw = calculations.get("battery_endurance_assumption")
    try:
        assumption = json.loads(assumption_raw) if assumption_raw else None
    except (TypeError, ValueError):
        assumption = None
    return {"envelope": envelope, "assumption": assumption}


# ── Component description prompts (keyed by component suggested_key) ──────────
# Used by _handle_component_description affirmative path and follow-up messages.
# FN-017: moved to acquisition_target.COMPONENT_PROMPTS (single source of truth,
# shared with param_definition_session.py) — kept as a local alias so every
# existing `_COMPONENT_PROMPTS` reference in this file needs no other change.
_COMPONENT_PROMPTS = COMPONENT_PROMPTS

# ── Proactive question hints for component-driven blocks in build_startup_context ─
_BLOCK_COMPONENT_HINTS: dict[str, str] = {
    "structure":  "describe el frame (material y masa). Ej: 'carbono 450g'",
    "control":    "describe la controladora y GPS. Ej: 'Pixhawk 4'",
    "energy":     "describe la batería y motores. Ej: 'batería LiPo 6S 5000mAh, motores 2306 2400KV'",
    "propulsion": "describe motores y hélices. Ej: '4x 2306 2400KV, hélices 10x4.5'",
}


class JarvisOrchestrator:
    def __init__(self, workspace_root: Path | None = None) -> None:
        workspace_manager = WorkspaceManager(root=workspace_root)
        state_manager = StateManager()
        simulator = FlightSimulator()
        calculation_engine = CalculationEngine()
        mutation_engine = MutationEngine()
        memory_manager = MemoryManager()
        suggestion_engine = SuggestionEngine()
        reasoning_layer = ReasoningLayer()
        phase_layer = PhaseLayer()
        planner = Planner()
        create_project_action = CreateProjectAction(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            simulator=simulator,
            calculation_engine=calculation_engine,
            suggestion_engine=suggestion_engine,
        )
        calculate_action = CalculateAction(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            calculation_engine=calculation_engine,
        )
        simulate_action = SimulateAction(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            simulator=simulator,
            calculation_engine=calculation_engine,
            suggestion_engine=suggestion_engine,
            reasoning_layer=reasoning_layer,
        )
        iterate_action = IterateAction(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            simulator=simulator,
            calculation_engine=calculation_engine,
            mutation_engine=mutation_engine,
            suggestion_engine=suggestion_engine,
            reasoning_layer=reasoning_layer,
        )
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.calculation_engine = calculation_engine
        self.simulator = simulator
        self.design_explorer = DesignExplorer(
            calculation_engine=calculation_engine,
            simulator=simulator,
        )
        self.interactive_session = CreateProjectInteractiveSession()
        self.intent_resolver = IntentResolver()
        self.iterate_interactive_session = IterateInteractiveSession()
        self._semantic_adapter = SemanticIntentAdapter()
        self.param_definition_session = ParamDefinitionSession(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            calculation_engine=calculation_engine,
            simulator=simulator,
        )
        self.system_definition_session = SystemDefinitionSession(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
        )
        self.memory_manager = memory_manager
        self.reasoning_layer = reasoning_layer
        self.phase_layer = phase_layer
        self.planner = planner
        self.router = ActionRouter(
            create_project_action=create_project_action,
            calculate_action=calculate_action,
            simulate_action=simulate_action,
            iterate_action=iterate_action,
        )
        # U4: restaurar snapshot del proyecto más reciente si existe.
        # No-op si no hay proyectos en el workspace o el snapshot está ausente/corrupto.
        try:
            _latest = state_manager.load_active_project(workspace_manager)
            _snapshot = workspace_manager.load_runtime_snapshot(Path(_latest.workspace_path))
            if _snapshot:
                state_manager.restore_from_snapshot(_snapshot)
        except FileNotFoundError:
            pass

    def requires_planning(self, goal: str | ActionName) -> bool:
        return requires_planning(goal)

    def build_plan(self, goal: str | ActionName, context: dict | None = None) -> dict:
        plan = self.planner.generate(goal, context or {})
        return plan.model_dump()

    def handle(self, request: ActionRequest | dict) -> dict:
        normalized_request = (
            request if isinstance(request, ActionRequest) else ActionRequest.model_validate(request)
        )
        runtime_session = self.state_manager.get_runtime_session()

        if runtime_session.mode in {
            OrchestratorMode.CREATE_PROJECT_INTERACTIVE,
            OrchestratorMode.ITERATE_INTERACTIVE,
        }:
            return self._handle_interactive_request(normalized_request)

        if normalized_request.action == ActionName.CREATE_PROJECT and self._should_start_create_project_interactive(
            normalized_request
        ):
            interactive_response = self.interactive_session.start(normalized_request.parameters)
            self.state_manager.set_runtime_session(
                self._session_from_response(interactive_response)
            )
            return interactive_response

        if normalized_request.action == ActionName.ITERATE:
            try:
                project_state = self.state_manager.load_active_project(
                    self.workspace_manager,
                    project_id=normalized_request.parameters.get("project_id"),
                    workspace_path=normalized_request.parameters.get("workspace_path"),
                    project_slug=normalized_request.parameters.get("project_slug"),
                )
            except FileNotFoundError as error:
                return {
                    "status": "error",
                    "action": ActionName.ITERATE.value,
                    "message": str(error),
                }

            interactive_response = self.iterate_interactive_session.start(
                {
                    **normalized_request.parameters,
                    "project_id": project_state.project_id,
                    "project_slug": project_state.project_slug,
                    "workspace_path": project_state.workspace_path,
                    "memory_context": {
                        **project_state.memory.model_dump(),
                        "vehicle_type": project_state.current_parameters.get("vehicle_type"),
                        "current_parameters": project_state.current_parameters,
                        # Fase 3: leer material del Single Read Point (getter canónico)
                        "current_material": _get_frame_material_display(project_state.design_properties),
                    },
                    "known_components": project_state.design_properties.components,
                    **self._semantic_preseed(normalized_request.model_dump()),
                }
            )
            self.state_manager.set_runtime_session(
                self._session_from_response(interactive_response)
            )
            return interactive_response

        handler = self.router.resolve(normalized_request.action)
        return handler.run(normalized_request.parameters)

    def _handle_global_commands(self, user_input: str) -> dict | None:
        """Single intercept point for universal commands — runs before ANY session or intent logic.

        Must be called as the very first check in handle_user_text.
        Returns a result dict if the input is a global command, None otherwise (caller continues).

        Handles:
            - Escape words: cancel the active session and return to idle
            - Creation shortcut: "n"/"nuevo" → start create_project wizard immediately
        Sessions (ITERATE_INTERACTIVE, DEFINE_MISSING_PARAMETERS) keep their own internal
        escape as a safety fallback for direct callers — this layer coordinates, not replaces.
        """
        normalized = user_input.strip().lower()

        # ── Escape: cancel any active session ────────────────────────────────
        if normalized in ESCAPE_WORDS:
            session = self.state_manager.runtime_state.session
            # FN-004: pending structural confirm is active even when mode is IDLE
            if session.pending_structural_change:
                self.state_manager.set_runtime_session(
                    session.model_copy(update={"pending_structural_change": None})
                )
                return {
                    "status": "cancelled",
                    "action": "structural_confirm",
                    "message": "Cambio cancelado. El proyecto conserva la configuración anterior.",
                }
            active_mode = session.mode
            if active_mode != OrchestratorMode.IDLE:
                self.state_manager.clear_runtime_session()
                return {
                    "status": "cancelled",
                    "action": "global_command",
                    "message": "Operación cancelada. Puedes escribir 'calcula', 'simula' o describir un nuevo cambio.",
                }
            # No active session → inform user instead of falling through to LLM
            return {
                "status": "ok",
                "action": "global_command",
                "message": "No hay ninguna operación activa que cancelar.",
            }

        # ── Creation shortcut: "n"/"nuevo" → wizard without LLM ──────────────
        if normalized in NEW_PROJECT_WORDS:
            return self.handle({"action": ActionName.CREATE_PROJECT.value, "parameters": {}})

        return None

    _AFFIRMATIVE_WORDS: frozenset[str] = frozenset({
        "si", "sí", "s", "ok", "dale", "claro", "venga", "va", "adelante", "perfecto",
        "de acuerdo", "por supuesto", "afirmativo", "vamos", "yes",
    })

    @classmethod
    def _is_affirmative(cls, user_input: str) -> bool:
        return user_input.strip().lower() in cls._AFFIRMATIVE_WORDS

    @staticmethod
    def _is_pure_numeric(text: str) -> bool:
        """Return True if text is a bare number (int or float, with optional comma decimal).

        Guards the global component intercept so that '500', '1.2', '5000' are never
        treated as component descriptions and always reach the numeric param wizard.
        """
        try:
            float(text.strip().replace(",", "."))
            return True
        except ValueError:
            return False

    def _interceptable_component_specs(self, text: str, session: Any) -> list:
        """Return ComponentSpecs that should route to the component flow (D7-aware).

        Same guards as ``_should_intercept_component``, but recovers *all* components
        from mixed phrases via ``infer_components``.
        """
        _norm_for_guard = self.intent_resolver._normalize_text(text)
        if self.intent_resolver._resolve_strong_action_intent(_norm_for_guard) is not None:
            return []

        from jarvis.core.component_inference import infer_components as _si_infer_many
        from jarvis.domains.aerial import aerial_registry as _si_reg

        _lower = text.lower().lstrip()
        if _lower.startswith(("que ", "qué ", "cual ", "cuál ", "¿")):
            return []
        if self._is_pure_numeric(text):
            return []
        if session.mode == OrchestratorMode.CREATE_PROJECT_INTERACTIVE:
            return []
        if session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS:
            return []
        if session.mode == OrchestratorMode.ITERATE_INTERACTIVE:
            return []

        specs = _si_infer_many(text, registry=_si_reg)
        accepted: list = []
        for spec in specs:
            if spec.suggested_key == "generic_component":
                continue
            if not spec.properties:
                continue
            if spec.suggested_key == "battery":
                if not any(u in text.lower() for u in ("mah", "wh", "v", "s")):
                    continue
            accepted.append(spec)
        if accepted:
            return accepted

        # G17/G14: aerial.py's motors/propellers ComponentRules key off literal
        # keyword substrings ("motor" / helice|hélice|propeller|props) — a bare
        # "4x 2306 1400kv" or "10x4.5" has no such keyword, so infer_components
        # falls entirely to generic_component and gets filtered out above, even
        # though infer_component_for_key resolves it perfectly. This mirrors
        # _handle_component_description's own force-motors/force-propellers
        # bypass (same guards, same ordering) so the same phrases that already
        # work mid-wizard also work at IDLE, instead of falling to the LLM.
        if all(s.suggested_key == "generic_component" for s in specs):
            forced = self._force_component_spec_idle(text)
            if forced is not None:
                return [forced]
        return accepted

    def _force_component_spec_idle(self, text: str) -> "Any | None":
        """G17/G14: IDLE-context force-motors/force-propellers bypass.

        Only fires when the active project has a genuinely pending (not yet
        defined) motors/propellers component — never with no active project,
        never to silently re-bind an already-defined component. Motor check
        runs first (same order as the wizard path); propellers only forces
        when the phrase is unambiguously propeller-shaped.

        Unlike the wizard's own force-propellers block, this never bypasses
        the shape guard just because motors isn't pending: the wizard's
        "motors not in expected_keys" bypass is safe there only because that
        specific wizard turn is already framed around propellers (a singleton
        acquisition target) — no such framing exists at IDLE, where a
        motor-shaped phrase can arrive at any time regardless of whether
        motors happens to already be defined (e.g. the user is replacing an
        already-declared motor). Always requiring the shape guard here is
        what T-g17-already-defined locks in.
        """
        project_state = self._safe_active_project()
        if project_state is None:
            return None

        from jarvis.core.component_inference import infer_component_for_key
        from jarvis.domains.aerial import aerial_registry

        components = project_state.design_properties.components
        motors_pending = component_presence_tier(components.get("motors")) != "present"
        propellers_pending = component_presence_tier(components.get("propellers")) != "present"

        if motors_pending:
            forced = infer_component_for_key(text, "motors", registry=aerial_registry)
            # Not a plain completeness=="high" guard (as the wizard-side force
            # uses): the IC's own acceptance phrase "4x 2306 1400kv" has no
            # thrust_n/power_w, so extract_motor_properties/_motor_completeness
            # only ever reaches "medium" for it — "high" would silently fail
            # the contract's own acceptance criterion #1. But a bare "medium"
            # guard alone would reopen G14 (bare "10x4.5" also reaches
            # "medium" via the same motor_count regex's spurious NxP match).
            # _looks_clearly_propeller_shaped is the same discriminator the
            # wizard path already trusts for this exact ambiguity: it returns
            # False whenever a "kv" marker is present (never true of a real
            # propeller phrase) and True for a bare realistic NxP size, so it
            # correctly keeps "4x 2306 1400kv" (has kv) on the motors path
            # while still deferring "10x4.5" (no kv) to the propellers force.
            if (
                forced is not None
                and forced.completeness != "low"
                and not self._looks_clearly_propeller_shaped(text)
            ):
                return forced

        if propellers_pending and self._looks_clearly_propeller_shaped(text):
            forced = infer_component_for_key(text, "propellers", registry=aerial_registry)
            if forced is not None and forced.completeness != "low":
                return forced

        return None

    def _should_intercept_component(self, text: str, session: Any) -> "Any | None":
        """Return first ComponentSpec if input should be routed to component flow, else None.

        Routing is based on the *type of input*, not the orchestrator mode.
        Rule: if the user describes a real physical component → always intercept,
        regardless of mode — with two exceptions:
          - CREATE_PROJECT_INTERACTIVE: would break the structured creation wizard
          - DEFINE_MISSING_PARAMETERS: already has its own per-reason intercept

        Guards (all must pass to intercept):
          (0) not a strong action intent  — 'simula', 'calcula', 'itera'… are never
              component descriptions (Bug 68: 'simula' contains 'imu' as substring)
          (1) matched a real domain rule  — suggested_key != 'generic_component'
          (2) properties extracted        — at least one property with a value present
              (separates "calidad" from "utilidad": completeness measures definition
               quality; properties measure whether there is useful signal to act on)
          (3) not an interrogative phrase — "que material es mejor..." must reach LLM
          (4) not pure-numeric input      — '500' must still reach the param wizard
          (5) mode allows interception    — not CREATE_PROJECT or DEFINE_MISSING
          (6) battery-specific units guard — 'bateria 5000' (no units) must NOT intercept
        """
        specs = self._interceptable_component_specs(text, session)
        return specs[0] if specs else None

    # Intents that abort ITERATE_INTERACTIVE and take over the turn (calibration 2026-08-05).
    # project_status / analyze stay as soft interrupts (Bug 7) and are handled earlier.
    _ITERATE_PREEMPT_INTENTS: frozenset[str] = frozenset({
        "explore_design_space",
        "apply_exploration_result",
        "calculate",
        "simulate",
        "create_project",
        "define_params",
        "iterate",
        "dismiss_suggestion",
    })

    def _should_preempt_iterate_wizard(self, user_input: str) -> bool:
        """True when input should close the iterate wizard and be handled as idle.

        Wizard step answers ("sí", "material", "fibra"…) do not match strong-action
        patterns or component inference, so they continue through the wizard.

        Component descriptions preempt only when the wizard is *not* actively
        collecting a component spec (DEFINE @ step 2) or awaiting a motor-catalog
        pick — otherwise motor suggestions / define-component flows are aborted.

        Continuity Hardening ★3 (G11): ownership is now consulted BEFORE the
        strong-intent short-circuit, not after — G11-A/B (investigation §3.4)
        reproduced a step-2/strategy-selection answer like "cambiar a pvc"
        self-preempting because it also matches `_resolve_strong_action_intent
        == "iterate"`, and the ownership guard (below) was only ever reached
        for the *component-inference* fallback, never for the strong-intent
        check. The suppression is narrow: only intents `{None, "iterate"}` are
        swallowed while the wizard owns the step — a genuinely different
        strong action (`simula`, `explora opciones`, `calcula`, ...) still
        preempts even while the wizard owns the current step, per ★3 rule 4.
        """
        normalized = self.intent_resolver._normalize_text(user_input)
        strong = self.intent_resolver._resolve_strong_action_intent(normalized)

        session = self.state_manager.runtime_state.session
        owns_input = self._iterate_owns_component_input(session)
        if owns_input and strong in (None, "iterate"):
            return False

        if strong in self._ITERATE_PREEMPT_INTENTS:
            return True

        if owns_input:
            return False

        # Component descriptions: Bug 64 blocks _should_intercept during ITERATE;
        # detect the same signal against an idle-like session so we can clear first.
        idle_probe = session.model_copy(update={"mode": OrchestratorMode.IDLE})
        return self._should_intercept_component(user_input, idle_probe) is not None

    @staticmethod
    def _iterate_owns_component_input(session) -> bool:
        """True when iterate already owns whatever input arrives next.

        Two shapes:
          - original scope: collecting a component description or motor pick
            (`DEFINE` operation, step 2, or a live `motor_suggestions` list).
          - Continuity Hardening ★3 (G11-B): a strategy-selection answer for
            an already-named variable — `variable` is set but `operation` is
            not yet resolved (e.g. "¿Cómo quieres aplicar el cambio?" right
            after `variable="material"`). A bare material name or "cambiar a
            X" at that step is this step's own answer, not a new request —
            see `_should_preempt_iterate_wizard` for how this combines with
            the strong-intent check to still let unrelated strong actions
            (simular/calcular/explorar) preempt even while owned.
        """
        if session.motor_suggestions:
            return True
        draft = session.iteration_draft
        if draft is None:
            return False
        operation = draft.operation
        op_value = operation.value if hasattr(operation, "value") else operation
        if op_value == IterationOperation.DEFINE.value and session.step == 2:
            return True
        if draft.variable is not None and operation is None:
            return True
        return False

    @staticmethod
    def _preempt_iterate_message(result: dict) -> str:
        """Prefix a short notice when an iterate wizard was aborted for a stronger intent."""
        notice = "He cerrado la iteración en curso para atender esta instrucción."
        existing = (result.get("message") or "").strip()
        if not existing:
            return notice
        if existing.startswith(notice):
            return existing
        return f"{notice}\n\n{existing}"

    # R3b: strong intents that mutate project state or switch orchestrator mode,
    # trapped mid-DEFINE_MISSING as silent Brief re-show (component sub-mode) or
    # honest refuse (R3a, numeric sub-mode). Mirrors _ITERATE_PREEMPT_INTENTS but
    # excludes explore_design_space/calculate/simulate — those already execute
    # inline as soft-interrupts within the DEFINE_MISSING branch (R3a Slice 2 and
    # the pre-existing calculate/simulate gates), so clearing the wizard for them
    # would be a regression, not a fix. Also excludes define_params (unlike
    # C-052's iterate set): the contract's own gate-ordering hard rule requires
    # R3a's refuse to run first (see the caller), and R3a's refuse already owns
    # 100% of the cases where a declare-different-block phrase would be safe to
    # act on — every case it does NOT refuse is a component genuinely shared
    # between blocks (e.g. "motors" in both propulsion and energy, per
    # BLOCK_TO_COMPONENTS), where FN-013's existing "park, don't jump" behavior
    # is the deliberately-tested outcome (test_fn013_active_block_declare_routing
    # ::test_definir_energia_while_propulsion_active_does_not_jump) — adding
    # define_params here would silently override that test's intent instead of
    # closing a real residual.
    _DEFINE_MISSING_PREEMPT_INTENTS: frozenset[str] = frozenset({
        "apply_exploration_result",
        "iterate",
        "dismiss_suggestion",
        "create_project",
    })

    def _should_preempt_define_missing_wizard(self, user_input: str, session: Any) -> bool:
        """True when input should close the DEFINE_MISSING wizard and be handled as idle.

        Reuses the same strong-intent resolver C-052's iterate preempt uses.
        """
        normalized = self.intent_resolver._normalize_text(user_input)
        strong = self.intent_resolver._resolve_strong_action_intent(normalized)
        return strong in self._DEFINE_MISSING_PREEMPT_INTENTS

    def _clear_runtime_session_preserving_dse(self, session: Any) -> None:
        """clear_runtime_session(), but carry ``last_exploration_result`` forward.

        It is runtime-only (never persisted to disk, unlike accepted components),
        so a blind clear would silently make ``apply_exploration_result`` fail
        with "no hay resultados de exploración recientes" right after the
        preempt that was supposed to execute it — defeating the intent set's
        own inclusion of that intent. Same precedent as the existing
        ``handoff_context`` forwarding in ``ParamDefinitionSession.start()``.
        """
        exploration = session.last_exploration_result
        self.state_manager.clear_runtime_session()
        if exploration is not None:
            cleared = self.state_manager.get_runtime_session()
            self.state_manager.set_runtime_session(
                cleared.model_copy(update={"last_exploration_result": exploration})
            )

    @staticmethod
    def _preempt_define_missing_message(result: dict, *, partial_apply: bool = False) -> str:
        """Prefix a short notice when a DEFINE_MISSING wizard was aborted for a stronger intent.

        ``partial_apply=True`` marks the numeric sub-mode case where the wizard
        held typed-but-unsaved ``collected_params`` that were applied as a side
        effect before the preempt — the notice MUST say so (contract §Slice 2:
        "Do not silent-apply").
        """
        notice = "He cerrado la definición en curso para atender esta instrucción."
        if partial_apply:
            notice += "\n(Se aplicaron los parámetros que ya habías indicado.)"
        existing = (result.get("message") or "").strip()
        if not existing:
            return notice
        if existing.startswith(notice):
            return existing
        return f"{notice}\n\n{existing}"

    def _consume_structural_confirm(self, user_input: str) -> dict:
        """FN-004: apply, resume original path, cancel, or re-prompt."""
        from jarvis.core.param_definition_session import (
            _STRUCTURAL_AFFIRMATIVES,
            _STRUCTURAL_NEGATIVES,
        )

        session = self.state_manager.get_runtime_session()
        pending = session.pending_structural_change
        if not pending:
            return {
                "status": "error",
                "action": "structural_confirm",
                "message": "No hay cambio estructural pendiente.",
            }
        normalized = user_input.strip().lower()
        if normalized in _STRUCTURAL_AFFIRMATIVES:
            pending_copy = dict(pending)
            self.state_manager.set_runtime_session(
                session.model_copy(update={"pending_structural_change": None})
            )
            resume_kind = pending_copy.get("resume_kind")
            if resume_kind == "component":
                resume_input = pending_copy.get("resume_user_input") or ""
                expected = list(pending_copy.get("resume_expected_keys") or [])
                resume_session = self.state_manager.get_runtime_session().model_copy(
                    update={"pending_missing_params": expected}
                )
                return self._handle_component_description(
                    str(resume_input), resume_session, structural_confirmed=True
                )
            if resume_kind == "iterate":
                draft = pending_copy.get("resume_iteration_draft")
                if draft:
                    return self.router.resolve(ActionName.ITERATE).run(
                        {
                            "iteration_draft": draft,
                            "structural_confirmed": True,
                        }
                    )
            updates = {
                k: float(v) for k, v in (pending_copy.get("updates") or {}).items()
            }
            return self.param_definition_session.apply_and_recalculate(
                updates, confirmed=True
            )
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

    def attach_project_coherence(self, result: dict) -> dict:
        """P4: attach Continuity footer after relevant successful operations.

        Project-first responses: what changed / state now / next useful step.
        No Conversation Engine — thin attach after the fact.
        """
        if not isinstance(result, dict):
            return result
        if result.get("status") != "ok":
            return result
        action_l = str(result.get("action") or "").lower()
        coherent_actions = {
            "define_missing_params",
            ActionName.ITERATE.value,
            ActionName.CALCULATE.value,
            ActionName.SIMULATE.value,
            ActionName.CREATE_PROJECT.value,
            "component_description_saved",
            "dse_apply",
            "apply_exploration_result",
        }
        if action_l not in coherent_actions:
            return result
        try:
            ctx = self.build_startup_context()
        except Exception:  # noqa: BLE001 — footer must never break the main reply
            return result
        if not ctx.get("has_project"):
            return result
        cont = ctx.get("continuity") or {}
        if not (cont.get("situation") or cont.get("next_useful_step")):
            return result
        return {
            **result,
            "startup_context": ctx,
            "continuity": cont,
            "coherence_footer": cont,
        }

    def handle_user_text(self, user_input: str, llm_interface) -> dict:
        """U4: wrapper público — delega al procesador interno y persiste el snapshot."""
        result = self._handle_user_text_inner(user_input, llm_interface)
        self._persist_runtime_snapshot()
        return result

    def _persist_runtime_snapshot(self) -> None:
        """U4: guarda historial + sesión en disco tras cada turno. No-op si no hay proyecto activo."""
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
            self.workspace_manager.save_runtime_snapshot(
                Path(project_state.workspace_path),
                [t.model_dump() for t in self.state_manager.runtime_state.conversation_history],
                self.state_manager.session_to_snapshot(),
            )
        except FileNotFoundError:
            pass

    def _handle_user_text_inner(self, user_input: str, llm_interface) -> dict:
        # ── Global command router — must be first ─────────────────────────────
        global_result = self._handle_global_commands(user_input)
        if global_result is not None:
            return global_result

        runtime_state = self.state_manager.runtime_state
        current_session = runtime_state.session

        # ── FN-004: pending structural substitution (sí/no) ───────────────────
        if current_session.pending_structural_change:
            result = self._consume_structural_confirm(user_input)
            self._track_turn(user_input, result)
            return result

        # ── Bug 54: consume pending_define_missing confirmation ───────────────
        # If the previous turn showed a proactive "¿Definimos X ahora?" and the
        # user replies affirmatively, open the define_missing wizard immediately.
        # Any non-affirmative input clears the flag and falls through normally.
        if current_session.pending_define_missing:
            # Always clear the flag first — consumed regardless of answer.
            cleared_session = current_session.model_copy(
                update={"pending_define_missing": False}
            )
            self.state_manager.set_runtime_session(cleared_session)
            if self._is_affirmative(user_input):
                result = self.start_define_missing_params(
                    current_session.pending_missing_params,
                    reason=current_session.pending_missing_reason,
                )
                self._track_turn(user_input, result)
                return result
            # Non-affirmative → fall through to process input normally
            runtime_state = self.state_manager.runtime_state
            current_session = runtime_state.session
        # ─────────────────────────────────────────────────────────────────────
        # ── FN-005: "ayúdame a elegir" while IDLE → open assisted motor flow ─
        from jarvis.core.motor_catalog_assist import is_help_choose_phrase

        if (
            current_session.mode == OrchestratorMode.IDLE
            and is_help_choose_phrase(user_input)
        ):
            assist = self._try_start_assisted_motor_help()
            if assist is None:
                # Prop-5 (★6 B): motor didn't want help (bound, or nothing to
                # do there) — try the propeller IDLE re-bind next, same IDLE
                # help-choose phrase, no separate dispatch needed.
                assist = self._try_start_assisted_propeller_help()
            if assist is None:
                # Bat-3: same fallback chain, one step further — battery
                # IDLE re-bind once motor/propeller both have nothing to do.
                assist = self._try_start_assisted_battery_help()
            if assist is not None:
                self._track_turn(user_input, assist)
                return assist
        # ─────────────────────────────────────────────────────────────────────
        # ── FN-014: "definir/declarar/completar <bloque o componente activo>" ──
        # while IDLE (including IDLE re-dispatch after an iterate preempt) —
        # must not leak to the LLM or open the iterate wizard when the state
        # already knows the real next gap. Supersedes FN-011 (block-only): a
        # strict superset, so block-only phrases keep working unchanged.
        if current_session.mode == OrchestratorMode.IDLE:
            acquisition_help = self._try_start_acquisition_from_mention(user_input)
            if acquisition_help is not None:
                self._track_turn(user_input, acquisition_help)
                return acquisition_help
        # ─────────────────────────────────────────────────────────────────────
        # ── G23: bare "ayúdame a definir" / confusion phrases while IDLE ───────
        # FN-015 — the acquisition-help feature that used to open a
        # DEFINE_MISSING wizard for these phrases — was removed entirely
        # (.jes/artifacts/implementation_contract_g23_remove_fn015.md): it
        # duplicated Continuity/FN-011/014/023 and its own in-wizard path had
        # zero value (re-showed the Brief that was already on screen). These
        # phrases must still never reach the LLM (the original bug was real),
        # so they now resolve to the same orientation authority FN-023
        # already owns — project_status/Continuity — without inventing a
        # second acquisition entry point. Kept as its own narrow IDLE check
        # rather than folded into IntentResolver.GUIDANCE_PATTERNS: that
        # table is shared with DEFINE_MISSING_PARAMETERS's own project_status
        # intercept (Bug 56, checked further down), which would otherwise
        # swallow these same phrases mid-wizard and show a full Continuity
        # dump instead of ★2's short re-ask.
        if (
            current_session.mode == OrchestratorMode.IDLE
            and is_define_missing_confusion_phrase(user_input)
        ):
            result = self._handle_project_status()
            self._track_turn(user_input, result)
            return result
        # ─────────────────────────────────────────────────────────────────────
        # ── Global component intercept ────────────────────────────────────────
        # Fires in any mode where the user might describe a physical component.
        # Input type determines routing, not orchestrator mode.
        # See _should_intercept_component for full guard logic.
        _gi_specs = self._interceptable_component_specs(user_input, current_session)
        if _gi_specs:
            _gi_session = current_session.model_copy(update={
                "pending_missing_params": [s.suggested_key for s in _gi_specs],
                "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
            })
            result = self._handle_component_description(user_input, _gi_session)
            self._track_turn(user_input, result)
            return result
        # ─────────────────────────────────────────────────────────────────────
        if current_session.mode == OrchestratorMode.CREATE_PROJECT_INTERACTIVE:
            result = self.handle(
                {
                    "action": ActionName.CREATE_PROJECT.value,
                    "raw_user_input": user_input,
                }
            )
            self._track_turn(user_input, result)
            return result
        if current_session.mode == OrchestratorMode.ITERATE_INTERACTIVE:
            # ── Bug 7: soft interrupt — read-only queries keep the wizard open ──
            # project_status and analyze are answered inline; wizard resumes same step.
            _interim_intent = self.intent_resolver.resolve_intent(user_input)
            if _interim_intent == "project_status":
                result = self._handle_project_status()
                # Bug 51: wizard is still active — append current prompt so the user
                # knows what the wizard expects next.
                result["wizard_reprompt"] = self.iterate_interactive_session.get_current_prompt(current_session)
                self._track_turn(user_input, result)
                return result
            if _interim_intent == "list_materials":
                # G10 ★8: same soft-interrupt shape as project_status above.
                result = self._handle_list_materials()
                result["wizard_reprompt"] = self.iterate_interactive_session.get_current_prompt(current_session)
                self._track_turn(user_input, result)
                return result
            if _interim_intent == "list_motors":
                # G16-A: same soft-interrupt shape as list_materials above.
                result = self._handle_list_motors()
                result["wizard_reprompt"] = self.iterate_interactive_session.get_current_prompt(current_session)
                self._track_turn(user_input, result)
                return result
            if _interim_intent == "analyze":
                result = self._handle_analyze(user_input, llm_interface)
                # Bug 51: same reprompt for analyze interruption.
                result["wizard_reprompt"] = self.iterate_interactive_session.get_current_prompt(current_session)
                self._track_turn(user_input, result)
                return result
            # ── Fix 1: semantic class guard — information/hybrid inputs never enter wizard ──
            _input_class = self.intent_resolver.classify_input_intent(user_input)
            if _input_class in ("information", "hybrid"):
                result = self._handle_analyze(user_input, llm_interface)
                result["wizard_reprompt"] = self.iterate_interactive_session.get_current_prompt(current_session)
                self._track_turn(user_input, result)
                return result
            # ── Calibration 2026-08-05: hard preempt strong intents / components ──
            # Sticky ITERATE_INTERACTIVE was eating explore, calculate, simulate,
            # new iterate requests, and component descriptions as wizard answers.
            # Clear the wizard and re-dispatch as idle so the intent owns the turn.
            if self._should_preempt_iterate_wizard(user_input):
                self.state_manager.clear_runtime_session()
                # Re-dispatch as idle. Inner paths already _track_turn.
                result = self._handle_user_text_inner(user_input, llm_interface)
                if isinstance(result, dict):
                    result = {
                        **result,
                        "preempted_iterate": True,
                        "message": self._preempt_iterate_message(result),
                    }
                return result
            # ─────────────────────────────────────────────────────────────────
            result = self.handle(
                {
                    "action": ActionName.ITERATE.value,
                    "raw_user_input": user_input,
                }
            )
            if result.get("status") == "cancelled":
                # Internal cancels (e.g. final confirmation "no") — global escape words
                # are already handled by _handle_global_commands before reaching this branch.
                self.state_manager.clear_runtime_session()
            else:
                self._track_turn(user_input, result)
            return result
        if current_session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS:
            # Bug 56: intercept read-only and action globals during DEFINE_MISSING so
            # valid commands don't fail as numeric-parse errors.
            _dm_intent = self.intent_resolver.resolve_intent(user_input)
            if _dm_intent == "project_status":
                result = self._handle_project_status()
                self._track_turn(user_input, result)
                return result
            # G10 ★8: same soft-interrupt shape as project_status above — a
            # materials catalog query mid-wizard (e.g. right after declaring
            # a frame material) must not be misread as a frame description
            # attempt by the component intercept further down.
            if _dm_intent == "list_materials":
                result = self._handle_list_materials()
                self._track_turn(user_input, result)
                return result
            # G16-A: same soft-interrupt shape as list_materials above — a
            # motors catalog query mid-wizard (including a trailing "?", which
            # would otherwise resolve to "analyze" before this dedicated
            # intent existed) must not fall to the LLM or the component
            # intercept further down.
            if _dm_intent == "list_motors":
                result = self._handle_list_motors()
                self._track_turn(user_input, result)
                return result
            # FN-013: "definir/declarar/completar <bloque activo>" while acquisition
            # is already open — re-prompt the current pending param. Do NOT parse
            # the phrase as a value, do NOT call the LLM, do NOT restart the session
            # (would wipe collected_params). Wrong-block names fall through unchanged.
            _block_reprompt = self._try_reprompt_active_block_declaration(user_input)
            if _block_reprompt is not None:
                self._track_turn(user_input, _block_reprompt)
                return _block_reprompt
            # G23 ★2: bare "ayúdame a definir (el valor)" / confusion phrases
            # — no named block/component — must never reach the LLM (the
            # original FN-015 bug was real) and must never re-show the
            # Acquisition Brief or offer the catalog as if this were help
            # (the FN-015 *feature* built on top of that bug is removed:
            # .jes/artifacts/implementation_contract_g23_remove_fn015.md).
            # Returns a single-line re-ask of the current pending item only.
            # Must run before the analyze→LLM branch below. Named-target
            # phrases (FN-011/013/014's territory) are excluded by the
            # detector itself, so this never steals a real declare-block
            # request.
            if is_define_missing_confusion_phrase(user_input):
                _reask = self._define_missing_confusion_reask(current_session)
                if _reask is not None:
                    self._track_turn(user_input, _reask)
                    return _reask
            # FN-005: "ayúdame a elegir" matches analyze patterns — keep it in the
            # assisted acquisition wizard instead of LLM analyze.
            from jarvis.core.motor_catalog_assist import is_help_choose_phrase

            if _dm_intent == "analyze" and not is_help_choose_phrase(user_input):
                result = self._handle_analyze(user_input, llm_interface)
                self._track_turn(user_input, result)
                return result
            if _dm_intent == "calculate":
                result = self.handle({"action": ActionName.CALCULATE.value, "parameters": {}})
                self._track_turn(user_input, result)
                return result
            if _dm_intent == "simulate":
                result = self.handle({"action": ActionName.SIMULATE.value, "parameters": {}})
                self._track_turn(user_input, result)
                return result
            # FN-016: navigation words ("atrás"/"volver"/"vuelve") cancel the
            # wizard cleanly — must run BEFORE the component-driven intercept
            # below, so Phase A "atrás" doesn't fall into
            # _handle_component_description's low-completeness follow-ups.
            # Scoped to acquisition wizards only (NOT added to global
            # ESCAPE_WORDS) — see acquisition_target.is_navigation_back_phrase.
            if is_navigation_back_phrase(user_input):
                self.state_manager.clear_runtime_session()
                result = {
                    "status": "cancelled",
                    "action": "define_missing_params",
                    "message": "Definición cancelada. Puedes retomar cuando quieras.",
                }
                self._track_turn(user_input, result)
                return result
            # R3a Slice 2: explore_design_space as soft-interrupt — fires
            # before the sub-mode fork so it works in both component and
            # numeric sub-modes. Only fires when the goal is resolvable
            # (explicit text or active handoff_context); otherwise falls
            # through to existing behavior (refuse or LLM analyze).
            if _dm_intent == "explore_design_space":
                _explore_goal = self.intent_resolver.resolve_explore_goal(user_input)
                _explore_resolvable = _explore_goal is not None
                if not _explore_resolvable:
                    _handoff = self.state_manager.get_runtime_session().handoff_context
                    try:
                        _active_project = self.state_manager.load_active_project(self.workspace_manager)
                        _explore_resolvable = (
                            _handoff is not None
                            and _handoff.project_id == _active_project.project_id
                            and _handoff.dse_capability == "active"
                        )
                    except FileNotFoundError:
                        pass
                if _explore_resolvable:
                    result = self._handle_explore(
                        goal_key=_explore_goal, user_input=user_input, llm_interface=llm_interface,
                    )
                    result["wizard_reprompt"] = self._get_define_missing_reprompt(current_session)
                    self._track_turn(user_input, result)
                    return result
            # R3b: real preempt — strong intents that mutate project state or
            # switch orchestrator mode close the wizard for real instead of a
            # silent Brief re-show (component sub-mode) or a refuse that never
            # executes (R3a, numeric sub-mode). Sub-mode-aware per investigation
            # §3.1: component sub-mode is safe to blind-clear (accepted
            # components are already on disk); numeric sub-mode must
            # partial-apply collected_params first so typed-but-unsaved values
            # are not silently lost.
            #
            # Hard rule (contract §0 / review checklist #1): R3a's refuse must
            # still win for inputs it already owns. "reducir payload" resolves
            # to strong-intent "iterate" (ITERATE_PATTERNS' bare "reducir")
            # AND to an R3a engineering-intent refuse — same collision shape
            # ★3 (G11-B) already documents for the iterate wizard. R3a's own
            # refuse check (whichever the active sub-mode uses) runs first;
            # only when it does NOT fire does the preempt intent get a turn.
            _dm_is_component_submode = (
                current_session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
                or current_session.param_definition_reason == MISSING_COMPONENT_DEFINITION
            )
            if _dm_is_component_submode:
                _dm_expected_keys = list(
                    current_session.pending_missing_params
                    or current_session.pending_param_definitions
                    or []
                )
                _dm_r3a_refusal = self._maybe_refuse_different_target(user_input, _dm_expected_keys)
            else:
                _dm_r3a_refusal = self._maybe_refuse_numeric_submode(user_input, current_session)
            if _dm_r3a_refusal is not None:
                self._track_turn(user_input, _dm_r3a_refusal)
                return _dm_r3a_refusal

            if self._should_preempt_define_missing_wizard(user_input, current_session):
                _dm_partial_apply = False
                if _dm_is_component_submode:
                    self._clear_runtime_session_preserving_dse(current_session)
                else:
                    _dm_collected = current_session.collected_params or {}
                    if _dm_collected:
                        # Apply on the still-active wizard session (not yet
                        # cleared) so that if this triggers FN-004's structural
                        # confirm, begin_structural_confirm layers
                        # pending_structural_change onto the intact wizard
                        # state instead of onto an already-cleared IDLE
                        # session — that is what lets the abort below actually
                        # preserve the wizard for the confirm/resume flow.
                        _dm_apply_result = self.param_definition_session.apply_and_recalculate(
                            _dm_collected
                        )
                        if _dm_apply_result.get("action") == "structural_confirm":
                            # FN-004 owns the turn — abort the preempt. Do not
                            # clear or redispatch; wizard state stays intact.
                            self._track_turn(user_input, _dm_apply_result)
                            return _dm_apply_result
                        _dm_partial_apply = True
                    self._clear_runtime_session_preserving_dse(current_session)
                result = self._handle_user_text_inner(user_input, llm_interface)
                if isinstance(result, dict):
                    result = {
                        **result,
                        "preempted_define_missing": True,
                        "message": self._preempt_define_missing_message(
                            result, partial_apply=_dm_partial_apply
                        ),
                    }
                return result
            # UX-C: intercept component-driven blocks before numeric wizard
            # FN-016: pending_missing_reason is the "about to open" signal set by
            # _set_pending_next_block BEFORE start_define_missing_params runs —
            # ParamDefinitionSession.start() builds a brand-new session that does
            # NOT carry it forward, so on the wizard's own live turns it is always
            # "". The field actually populated on an open wizard is
            # param_definition_reason. Checking pending_missing_reason only (as
            # before) meant a real component description given right after
            # opening Phase A (via Bug54/FN-011/FN-013/FN-014) never reached
            # _handle_component_description at all and fell through to
            # ParamDefinitionSession.answer()'s numeric parser instead — which,
            # before the FN-016 component-key guard, silently corrupted state
            # (e.g. current_parameters["propellers"] = 10.0). Purely additive
            # (OR): widens when the intercept fires, narrows nothing.
            if (
                current_session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
                or current_session.param_definition_reason == MISSING_COMPONENT_DEFINITION
            ):
                result = self._handle_component_description(
                    user_input, current_session, refuse_checked=True,
                )
                self._track_turn(user_input, result)
                return result
            # Component-intent intercept: user describes a component (e.g. "bateria 5000mAh")
            # while inside a param wizard. Component intent wins over numeric parsing.
            # Only fires when the spec is non-low (actual component data detected).
            from jarvis.core.component_inference import infer_component as _infer
            from jarvis.domains.aerial import aerial_registry as _aerial_reg
            _cspec = _infer(user_input, registry=_aerial_reg)
            if _cspec.suggested_key == "battery" and _cspec.completeness != "low":
                # Synthesize session so _handle_component_description sees expected_keys=["battery"]
                _battery_session = current_session.model_copy(update={
                    "pending_missing_params": ["battery"],
                    "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
                })
                result = self._handle_component_description(user_input, _battery_session)
                self._track_turn(user_input, result)
                return result
            # R3a Slice 1: port ★2 refuse to numeric sub-mode. Before
            # answer() parses the input as a numeric value, detect
            # engineering-intent, explore, and different-block-declare phrases
            # and return an honest refusal instead of the generic "No reconozco
            # X como valor." parse error.
            _numeric_refusal = self._maybe_refuse_numeric_submode(user_input, current_session)
            if _numeric_refusal is not None:
                self._track_turn(user_input, _numeric_refusal)
                return _numeric_refusal
            result = self.param_definition_session.answer(user_input)
            # Architecture progress hint: after params are applied, guide the user
            # to the next pending architecture block (only when system is defined).
            if result.get("status") == "ok" and result.get("action") == "define_missing_params":
                result = self._append_arch_progress_hint(result)
                self._set_pending_next_block()
            self._track_turn(user_input, result)
            return result
        if current_session.mode == OrchestratorMode.SYSTEM_DEFINITION:
            result = self.system_definition_session.answer(user_input)
            self._track_turn(user_input, result)
            # Bridge: arquitectura definida + parámetros recomendados pendientes
            # → lanzar ParamDefinitionSession automáticamente
            if result.get("status") == "ok":
                missing = result.get("recommended_missing_params", [])
                reason = result.get("recommended_reason")
                if missing and reason:
                    param_result = self.start_define_missing_params(missing, reason=reason)
                    param_result["message"] = result.get("message", "")
                    return param_result
            return result

        # ── Requirements Closure IC (G26 write path) ────────────────────────────
        # Must come BEFORE try_ingest: try_ingest's opportunistic numeric parser
        # has no concept of the project-level `restrictions` string and would
        # otherwise silently misinterpret a numeric keyword the sentence happens
        # to contain (the original G26 symptom — a loose current_parameters["autonomia"]).
        restrictions_update = self.param_definition_session.try_update_restrictions(user_input)
        if restrictions_update is not None:
            self._track_turn(user_input, restrictions_update)
            return restrictions_update

        # ── Parameter ingestion layer ──────────────────────────────────────────
        # Intercept direct param inputs (e.g. "4 motores") when physics are incomplete.
        # Must come BEFORE the intent resolver so these never fall into iterate_interactive.
        ingestion = self.param_definition_session.try_ingest(user_input)
        if ingestion is not None:
            self._track_turn(user_input, ingestion)
            return ingestion

        intent = self.intent_resolver.resolve_intent(user_input)
        if intent == "project_status":
            result = self._handle_project_status()
            self._track_turn(user_input, result)
            return result
        if intent == "list_materials":
            result = self._handle_list_materials()
            self._track_turn(user_input, result)
            return result
        if intent == "list_motors":
            result = self._handle_list_motors()
            self._track_turn(user_input, result)
            return result
        if intent == "analyze":
            # FN-025 (H3): a help-seeking phrase ("ayúdame", "oriéntame", ...)
            # must not silently reach the LLM when a deterministic authority
            # can already answer it. Only the help-verb half of
            # ANALYZE_PATTERNS is eligible — a phrase carrying a real
            # analytical verb ("analiza", "evalúa", "revisa", ...) always
            # keeps its analyze routing unchanged, even if it also contains a
            # help word ("ayúdame, analiza el margen" stays analyze).
            # FN-023's own GUIDANCE next-step patterns are checked earlier in
            # resolve_intent (before ANALYZE) and already return
            # "project_status" directly — they never reach this branch at
            # all, so that precedence is preserved by construction, not by a
            # special case here.
            _normalized_help = self.intent_resolver._normalize_text(user_input)
            _is_help_verb = self.intent_resolver._matches_any(
                _normalized_help, IntentResolver.ANALYZE_HELP_PATTERNS
            ) and not self.intent_resolver._matches_any(
                _normalized_help, IntentResolver.ANALYZE_VERB_PATTERNS
            )
            if _is_help_verb:
                # Reuses goal_planner.is_engineering_intention — the exact
                # same deterministic authority FN-022 already uses; no second
                # goal detector. A real project is required to name a goal
                # (mirrors FN-022's own _has_active_project() gate); bare
                # help with no detectable goal — or no active project at all
                # — falls to project_status/Continuity, never an
                # LLM-invented engineering target.
                goal_key = is_engineering_intention(user_input) if self._has_active_project() else None
                if goal_key is not None:
                    result = self._handle_engineering_intent(goal_key)
                    self._track_turn(user_input, result)
                    return result
                result = self._handle_project_status()
                self._track_turn(user_input, result)
                return result
            result = self._handle_analyze(user_input, llm_interface)
            self._track_turn(user_input, result)
            return result
        if intent == "ambiguous":
            if self._has_active_project():
                result = self._handle_analyze(user_input, llm_interface)
                self._track_turn(user_input, result)
                return result
            result = self.handle({"action": ActionName.CREATE_PROJECT.value, "parameters": {}})
            self._track_turn(user_input, result)
            return result
        # Bug 41: bridge "definir bater\u00eda" / "configurar h\u00e9lices" directly to
        # start_define_missing_params WITHOUT going through handle(), per spec.
        if intent == "define_params":
            local_action_request = self.intent_resolver.resolve_action_request(
                user_input, intent=intent
            )
            if local_action_request is not None:
                reason = local_action_request["parameters"].get("reason", "")
                try:
                    project_state = self.state_manager.load_active_project(
                        self.workspace_manager
                    )
                    params = project_state.current_parameters or {}
                except FileNotFoundError:
                    project_state = None
                    params = {}
                # G18: DEFINE_PARAMS_PATTERNS' terrestrial "motor(es)" branch
                # has no domain gate (IntentResolver is a stateless text
                # classifier by design — no vehicle_type access), so it wins
                # unconditionally even on an aerial project. Gate here, where
                # project_state is already available: an aerial project's
                # "definir motores" must never open the terrestrial
                # per_actuator_torque_nm/wheel_radius_m/gear_ratio wizard.
                if (
                    reason == "missing_transmission_parameters"
                    and project_state is not None
                    and CreateProjectInteractiveSession._domain_kind(
                        params.get("vehicle_type")
                    ) == "aerial"
                ):
                    redirect = self._redirect_aerial_motors_request(project_state)
                    if redirect is not None:
                        self._track_turn(user_input, redirect)
                        return redirect
                missing = missing_params_for_reason(reason, params)
                result = self.start_define_missing_params(missing, reason=reason)
                self._track_turn(user_input, result)
                return result

        # FN-022: bare engineering intention ("aumentar el empuje", "mejorar
        # la autonomía", ...) with no concrete target value yet — show the
        # deterministic strategy plan (goal_planner.GOAL_STRATEGIES) instead
        # of opening the iterate wizard or falling to the LLM. Only
        # intercepts intent in {"iterate", "unknown"} — every more specific
        # route already returned above (project_status, analyze,
        # define_params, dismiss_suggestion) or returns below unchanged
        # (explore_design_space, apply_exploration_result) and is untouched.
        # A phrase with a concrete value ("sube el empuje a 15N") is never
        # intercepted — is_engineering_intention() defers to iterate for
        # those (looks_like_numeric_mutate). Runs only in IDLE (this code is
        # only reached when no mode-specific branch above already returned).
        if intent in ("iterate", "unknown") and self._has_active_project():
            goal_key = is_engineering_intention(user_input)
            if goal_key is not None:
                result = self._handle_engineering_intent(goal_key)
                self._track_turn(user_input, result)
                return result

        if intent in {"create_project", "iterate", "calculate", "simulate"}:
            local_action_request = self.intent_resolver.resolve_action_request(user_input, intent=intent)
            if local_action_request is not None:
                if intent == "iterate":
                    local_action_request = self._preseed_variable_from_handoff(
                        local_action_request, user_input
                    )
                return self.handle(local_action_request)

        # Bug 49: dismiss the current top suggestion and show the next one.
        if intent == "dismiss_suggestion":
            result = self._handle_dismiss_suggestion()
            self._track_turn(user_input, result)
            return result

        # DSE: explore_design_space — pure in-memory exploration, no state mutation.
        if intent == "explore_design_space":
            goal_key = self.intent_resolver.resolve_explore_goal(user_input)
            result = self._handle_explore(goal_key=goal_key, user_input=user_input, llm_interface=llm_interface)
            self._track_turn(user_input, result)
            return result

        # DSE v1.1: apply the best candidate from the last exploration.
        # G24-1: an indexed apply phrase ("aplica la 5") selects that
        # candidate directly; unqualified ("aplica la mejor", bare "aplica")
        # keeps today's default index 1 == viable[0], byte-identical.
        if intent == "apply_exploration_result":
            apply_index = self.intent_resolver.resolve_apply_exploration_index(user_input) or 1
            result = self._handle_apply_exploration(index=apply_index)
            self._track_turn(user_input, result)
            return result

        action_request = llm_interface.interpret(user_input, runtime_state)
        if action_request.get("parameters", {}).get("error") == "invalid_llm_output":
            return {
                "status": "error",
                "error": "invalid_llm_output",
                "message": action_request["parameters"]["message"],
            }
        # Bug 52: LLM fallback must not open the iterate wizard for inputs the
        # deterministic resolver could not classify (unknown intent). The LLM
        # hallucinates iterate actions for nonsense input, which is wrong.
        if intent == "unknown" and action_request.get("action") == "iterate":
            result = self._handle_analyze(user_input, llm_interface)
            self._track_turn(user_input, result)
            return result
        result = self.handle(action_request)
        self._track_turn(user_input, result)
        return result

    def start_define_missing_params(
        self, missing_params: list[str], reason: str = DEFAULT_MISSING_FORCE_REASON
    ) -> dict:
        return self.param_definition_session.start(missing_params, reason=reason)

    def _try_start_assisted_motor_help(self) -> dict | None:
        """FN-005/FN-009: IDLE help-choose → assisted motor acquisition.

        Prioritizes an unresolved propulsion route (missing thrust) over energy
        (motor_power_w/battery): sizing power before the system has a force
        path at all is premature. Falls back to the existing energy route once
        propulsion is resolved. Returns None when there is no active project or
        nothing is missing on either surface.
        """
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None
        params = project_state.current_parameters or {}
        simulation = project_state.latest_results.get("simulation") or {}

        if simulation.get("physics_status") == "missing_parameters":
            reason = missing_force_reason_from_warnings(simulation.get("warnings") or [])
            if reason == MISSING_PROPULSION_PARAMETERS:
                propulsion_missing = missing_params_for_reason(reason, params)
                if propulsion_missing:
                    self.start_define_missing_params(propulsion_missing, reason=reason)
                    return self.param_definition_session.offer_catalog_help()

        if params.get("motor_power_w") is not None:
            motors_comp = (project_state.design_properties.components or {}).get("motors")
            catalog_ref = (
                getattr(motors_comp, "catalog_ref", None) if motors_comp is not None else None
            )
            if catalog_ref is not None:
                # Already bound — G9-A already handles catalog honesty
                # post-bind; no picker noise, help-choose is a no-op here.
                return None
            # G21 addendum: freeform-declared motor (power already set, no
            # catalog_ref yet) — open the same catalog picker via the motors
            # COMPONENT sub-mode so a numbered pick re-binds motors directly,
            # instead of dead-ending into project_status/Continuity.
            session = self.state_manager.get_runtime_session()
            updated = session.model_copy(update={
                "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
                "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
                "pending_missing_params": ["motors"],
                "pending_define_missing": False,
            })
            self.state_manager.set_runtime_session(updated)
            return self._offer_component_motor_catalog(updated, ["motors"])
        missing = ["motor_power_w"]
        if params.get("battery_capacity_wh") is None:
            constraints = project_state.parsed_constraints or {}
            autonomy = (
                constraints.get("autonomy_min")
                if isinstance(constraints, dict)
                else None
            )
            if autonomy is not None:
                missing.append("battery_capacity_wh")
        self.start_define_missing_params(missing, reason=MISSING_ENERGY_PARAMETERS)
        return self.param_definition_session.offer_catalog_help()

    def _try_start_assisted_propeller_help(self) -> dict | None:
        """Prop-5 (★6 B): IDLE help-choose → assisted propeller acquisition,
        the propeller-side counterpart to ``_try_start_assisted_motor_help``.
        Only ever reached as its fallback (called when that function
        returned None) — in practice that happens only when motors is
        already catalog-bound, which also satisfies the "motors not stub"
        guard below trivially. The explicit guard stays anyway so this
        function is correct standalone, not just by call-order accident.

        Returns None when there is no active project, motors is still a
        stub (motor IDLE path should claim that turn instead), or
        propellers doesn't want catalog help (already bound, or nothing to
        offer — no picker noise).
        """
        project_state = self._safe_active_project()
        if project_state is None:
            return None
        components = getattr(project_state.design_properties, "components", {}) or {}
        if _is_stub_or_absent(components.get("motors")):
            return None
        if not _wants_catalog_help(components.get("propellers")):
            return None

        session = self.state_manager.get_runtime_session()
        updated = session.model_copy(update={
            "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
            "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
            "pending_missing_params": ["propellers"],
            "pending_define_missing": False,
        })
        self.state_manager.set_runtime_session(updated)
        return self._offer_component_propeller_catalog(updated, ["propellers"])

    def _try_start_assisted_battery_help(self) -> dict | None:
        """Bat-3 (IDLE fallback, mirrors ``_try_start_assisted_propeller_help``):
        IDLE help-choose -> assisted battery acquisition. Only ever reached as
        the third fallback (motor -> propeller -> battery), in practice
        reached once motors AND propellers are both catalog-bound (or have
        nothing left to offer) — energy comes after propulsion in the
        architecture block order (investigation_report_project_closure_
        assembly_ready.md §1.10 S0->S1, IC §5 "battery after propulsion block
        complete"). Returns None when there is no active project or battery
        doesn't want catalog help (already bound, or nothing to offer — no
        picker noise).
        """
        project_state = self._safe_active_project()
        if project_state is None:
            return None
        components = getattr(project_state.design_properties, "components", {}) or {}
        if not _wants_catalog_help(components.get("battery")):
            return None

        session = self.state_manager.get_runtime_session()
        updated = session.model_copy(update={
            "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
            "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
            "pending_missing_params": ["battery"],
            "pending_define_missing": False,
        })
        self.state_manager.set_runtime_session(updated)
        return self._offer_component_battery_catalog(updated, ["battery"])

    def _try_declare_active_block_help(self, user_input: str) -> dict | None:
        """FN-011: 'ayúdame a declarar/completar <bloque>' → deterministic acquisition.

        FN-014: thin block-only wrapper kept for callers that want strictly
        block-level semantics. The IDLE call site now uses the superseding
        _try_start_acquisition_from_mention (blocks ∪ components) directly —
        for block-only phrases the two are behaviorally identical, since a
        block mention is the first resolution step in both.
        """
        mention = resolve_acquisition_mention(user_input, self._safe_active_project())
        if mention is None or mention["kind"] != "block":
            return None
        return self._try_start_acquisition_from_mention(user_input)

    def _safe_active_project(self):
        try:
            return self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None

    def _try_start_acquisition_from_mention(self, user_input: str) -> dict | None:
        """FN-014: unified block ∪ component acquisition gate for IDLE (including
        IDLE re-dispatch after an iterate-wizard preempt).

        Resolves user_input to a block or component mention
        (acquisition_target.resolve_acquisition_mention) and, only when that
        mention names the block that is genuinely the current pending gap
        (_next_pending_block), opens the SAME deterministic bridge already
        used by Bug54/FN-011/FN-013 (_set_pending_next_block +
        start_define_missing_params). No new acquisition logic — this only
        widens WHEN that existing bridge is entered, from block names to
        block ∪ component names.

        Wrong-block mentions (§4.6): when the phrase names a real block or
        component that belongs to a DIFFERENT block than the active pending
        one, returns a short deterministic message instead of silently
        falling through to iterate/define_params for that other block — never
        a silent cross-block jump. Mode stays IDLE, no LLM.

        Returns None (falls through to normal routing) when: there's no
        mention at all, no active/system-defined project, or no pending block
        (architecture complete or undefined) — existing routing unchanged.
        """
        project_state = self._safe_active_project()
        if project_state is None:
            return None
        if not project_state.design_properties.system_defined:
            return None

        pending = self._next_pending_block(project_state)
        pending_block_key = pending[0] if pending is not None else None
        if pending_block_key is None:
            return None

        mention = resolve_acquisition_mention(
            user_input, project_state, pending_block_key=pending_block_key
        )
        if mention is None:
            return None

        if not is_mention_on_active_gap(mention, pending_block_key, project_state):
            if mention["block_key"] != pending_block_key:
                # FN-014 §4.6: named a real block/component, but not the active
                # one — never silently open a different block's wizard.
                label = self._block_label_for(project_state, pending_block_key)
                return {
                    "status": "ok",
                    "action": "acquisition_target_mismatch",
                    "message": (
                        f"Ahora toca {label}. Cuando esté completa, "
                        "podremos definir el resto."
                    ),
                }
            if mention["kind"] == "component":
                # FN-017 B6: right block, but this specific component is
                # already resolved (e.g. "declarar motores" when motors is
                # done but propellers still isn't) — continue the SAME
                # block's remaining gap instead of falling through to
                # define_params/intent_resolver, which can route to an
                # unrelated domain's params (e.g. ground transmission torque
                # on an aerial project). Same bridge, no new acquisition logic.
                return self._continue_block_acquisition()
            return None

        return self._continue_block_acquisition()

    def _continue_block_acquisition(self) -> dict | None:
        """Shared tail for _try_start_acquisition_from_mention: load the next
        pending block's gap into the session and open it via the existing
        Bug54/FN-011/FN-013 bridge. No new acquisition logic."""
        self._set_pending_next_block()
        session = self.state_manager.get_runtime_session()
        if not session.pending_define_missing:
            return None
        return self.start_define_missing_params(
            session.pending_missing_params, reason=session.pending_missing_reason
        )

    def _redirect_aerial_motors_request(self, project_state: Any) -> dict | None:
        """G18: aerial "definir motores" → propulsion/motors acquisition,
        never the terrestrial transmission wizard (torque/rueda/gear_ratio).

        If propulsion is still the active pending block, continue that
        existing bridge (same as any other component mention on the active
        gap). Otherwise reopen the motors component wizard directly — the
        same component-level redefine any other component intercept already
        uses — rather than inventing a terrestrial project or silently
        refusing a motors-shaped phrase.
        """
        pending = (
            self._next_pending_block(project_state)
            if project_state.design_properties.system_defined
            else None
        )
        if pending is not None and pending[0] == "propulsion":
            return self._continue_block_acquisition()
        return self.start_define_missing_params(["motors"], reason=MISSING_COMPONENT_DEFINITION)

    def _fresh_pending_keys_for_block(self, project_state: Any, block_key: str) -> list[str]:
        """G12/FN-013: recompute the pending keys for *block_key* the same way
        ``_set_pending_next_block`` would for a fresh open of that block.

        Used to verify a session's stale ``pending_param_definitions`` field
        still belongs to the block it's about to be re-shown under — a
        component can legitimately appear in more than one block's
        ``BLOCK_TO_COMPONENTS`` entry (e.g. "motors" in both "propulsion" and
        "energy"), so a static membership check isn't enough: the check must
        be against what's genuinely still incomplete for THIS block right
        now, not just what the block's component set could ever contain.
        """
        block_type = get_block_type(block_key)
        components = project_state.design_properties.components
        if block_type in ("composite", "component"):
            component_keys = BLOCK_TO_COMPONENTS.get(block_key, [])
            missing_component_keys = [
                k for k in component_keys
                if components.get(k) is None or components[k].completeness == "low"
            ]
            if missing_component_keys or block_type == "component":
                return missing_component_keys
        param_reason = get_param_reason_for_block(block_key)
        if not param_reason:
            return []
        return missing_params_for_reason(param_reason, project_state.current_parameters or {})

    def _try_reprompt_active_block_declaration(self, user_input: str) -> dict | None:
        """FN-013: block-level help while DEFINE_MISSING is already active.

        If the user names the architecture block that is currently pending,
        re-ask the current pending parameter without restarting the session.
        Returns None when the phrase is not a declare-block request, or when
        the named block is not the active pending block (no cross-block jump).
        """
        block_key = self.intent_resolver.resolve_declare_block_request(user_input)
        if block_key is None:
            return None
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return None
        if not project_state.design_properties.system_defined:
            return None
        pending_block = self._next_pending_block(project_state)
        if pending_block is None or pending_block[0] != block_key:
            return None
        session = self.state_manager.get_runtime_session()
        pending = list(session.pending_param_definitions or [])
        if not pending:
            return None
        # G12/FN-013: session.pending_param_definitions can go stale — e.g. a
        # DSE apply/component_sync completes "motors" directly, bypassing the
        # wizard's own turn-by-turn chaining, while the session field still
        # names a component from a DIFFERENT (now-complete) block's own
        # earlier turn. Re-derive the fresh pending set for block_key itself
        # and only trust the session's own ordering when its head is still
        # genuinely part of it — otherwise rebuild the brief from the fresh
        # list so the body never narrates an already-resolved component.
        fresh_pending = self._fresh_pending_keys_for_block(project_state, block_key)
        if fresh_pending and pending[0] not in fresh_pending:
            pending = fresh_pending
        suggestions = list(session.motor_suggestions or [])
        label = self._block_label_for(project_state, block_key)
        message = f"Seguimos con {label} — sin reiniciar lo ya capturado."
        first = pending[0]
        # FN-018 C0: this was the one remaining path still calling
        # _question_for_param unconditionally for a component key, producing
        # "¿Cuál es el valor de propellers?" instead of the harmonized
        # COMPONENT_PROMPTS/Brief text every other entry point already uses
        # (FN-017 B5/B3). Route component keys through the same Brief
        # builder; non-component params keep the original path.
        if first in COMPONENT_PROMPTS:
            brief = build_acquisition_brief(first, project_state)
            if brief["message"]:
                message = f"{message}\n\n{brief['message']}"
            question = brief["question"]
        else:
            question = self.param_definition_session._question_for_param(
                first, suggestions
            )
        return {
            "status": "interactive",
            "action": "define_missing_params",
            "message": message,
            "question": question,
            "pending": pending,
            "motor_suggestions": suggestions,
            "block_declaration_reprompt": True,
        }

    def _define_missing_confusion_reask(self, session: Any) -> dict | None:
        """G23 ★2: anti-LLM confusion gate inside DEFINE_MISSING_PARAMETERS —
        NOT acquisition help (FN-015, removed in full — see
        .jes/artifacts/implementation_contract_g23_remove_fn015.md). Returns
        a single-line re-ask of the current pending item only:

          - component sub-mode → _component_prompt_for_first_missing (the
            same one-line prompt FN-013's reprompt uses) — no Acquisition
            Brief, no "Vamos a definir..."/"Puedes:" wrapper.
          - numeric sub-mode → _question_for_param(pending[0]) only — no
            catalog offer, even when pending[0] is an assisted motor param.

        No session mutation. Returns None when nothing is pending (caller
        falls through).
        """
        is_component_submode = (
            session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
            or session.param_definition_reason == MISSING_COMPONENT_DEFINITION
        )
        if is_component_submode:
            keys = list(session.pending_missing_params or session.pending_param_definitions or [])
            if not keys:
                return None
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "question": self._component_prompt_for_first_missing(keys),
                "pending": keys,
            }

        pending = list(session.pending_param_definitions or [])
        if not pending:
            return None
        return {
            "status": "interactive",
            "action": "define_missing_params",
            "question": self.param_definition_session._question_for_param(pending[0]),
            "pending": pending,
        }

    def _track_turn(self, user_input: str, result: dict) -> None:
        """Append user + assistant turns to conversation history (idle mode only)."""
        self.state_manager.append_conversation_turn("user", user_input)
        assistant_msg = result.get("message", "")
        if assistant_msg:
            self.state_manager.append_conversation_turn("assistant", str(assistant_msg))

    def _handle_dismiss_suggestion(self) -> dict[str, Any]:
        """Bug 49: dismiss the currently shown suggestion and return project_status
        with the next non-dismissed suggestion as the new top.

        Uses session.last_suggested_action as the label to dismiss — this is the
        exact label the user saw, so it is never out of sync with what was rendered.
        Clears pending_define_missing to avoid 'sí a qué?' ambiguity.

        Edge cases handled:
        - No active suggestion (last_suggested_action is None): no-op, returns status
          with a dismiss_noop flag so the renderer can inform the user.
        - All suggestions exhausted after dismiss: returns all_suggestions_dismissed flag.
        """
        session = self.state_manager.runtime_state.session

        # Edge case 1: dismiss fired with no active suggestion (e.g. user typed
        # a dismiss phrase before any suggestion was shown this session).
        if not session.last_suggested_action:
            return {
                "status": "ok",
                "action": "project_status",
                "startup_context": self.build_startup_context(),
                "dismiss_noop": True,
            }

        dismissed = list(session.dismissed_suggestions)
        if session.last_suggested_action not in dismissed:
            dismissed.append(session.last_suggested_action)
        updated_session = session.model_copy(update={
            "dismissed_suggestions": dismissed,
            "pending_define_missing": False,  # clear any pending proactive question
        })
        self.state_manager.set_runtime_session(updated_session)
        # Rebuild project_status with updated dismissed list already in session.
        result = self._handle_project_status()
        # Edge case 2: all non-blocked suggestions are now dismissed — inform the user.
        ctx = result.get("startup_context") or {}
        if not ctx.get("suggested_action") and dismissed:
            result["all_suggestions_dismissed"] = True
        return result

    # ── Architecture progress engine ──────────────────────────────────────────
    # Centralised here so both project_status and define_missing_params share
    # the exact same logic.  No new schema fields are added — completion is
    # derived at runtime from current_parameters and component completeness.

    @staticmethod
    def _block_progress_status(
        block: str,
        design_properties: Any,
        params: dict[str, Any],
    ) -> str:
        """Return 'complete', 'in_progress', or 'not_started' for one architecture block.

        - Param-driven blocks (actuation, transmission): driven by whether
          their required parameters are present in current_parameters.
        - Component-driven blocks (structure, control, …): driven by whether any
          component has been explicitly defined (completeness != 'low').
        - Composite blocks (energy, propulsion): require BOTH params OK and all
          component keys defined. AND-strict semantics (Fase 4/6).
        """
        block_type = get_block_type(block)

        if block_type == "param":
            param_reason = get_param_reason_for_block(block)
            if not param_reason:
                return "not_started"
            required = params_for_reason(param_reason)
            if not required:
                return "not_started"
            defined = [p for p in required if params.get(p) is not None]
            if not defined:
                return "not_started"
            return "complete" if len(defined) == len(required) else "in_progress"

        if block_type == "composite":
            # Composite: requires BOTH params OK and all component keys defined.
            # Guard: param_reason may be None if composite block has no param side yet.
            param_reason = get_param_reason_for_block(block)
            if param_reason:
                required = params_for_reason(param_reason)
                defined = [p for p in required if params.get(p) is not None] if required else []
                params_ok = bool(required) and len(defined) == len(required)
            else:
                # No param side → params criterion is satisfied trivially.
                params_ok = True

            component_keys = BLOCK_TO_COMPONENTS.get(block, [])
            components = design_properties.components
            non_low = [
                k for k in component_keys
                if k in components and not JarvisOrchestrator._component_is_low(components[k])
            ]
            components_ok = bool(component_keys) and len(non_low) == len(component_keys)

            if not params_ok and not components_ok:
                return "not_started"
            if params_ok and components_ok:
                return "complete"
            return "in_progress"

        # block_type == "component" (default / fallback)
        component_keys = BLOCK_TO_COMPONENTS.get(block, [])
        if not component_keys:
            return "not_started"
        components = design_properties.components
        # "not_started" if all components are still at the auto-stub completeness level.
        non_low = [
            k for k in component_keys
            if k in components and not JarvisOrchestrator._component_is_low(components[k])
        ]
        if not non_low:
            return "not_started"
        if len(non_low) == len(component_keys):
            return "complete"
        return "in_progress"

    @staticmethod
    def _component_is_low(component: Any) -> bool:
        """True if a component is absent/default (completeness is None or 'low').

        FN-020: thin wrapper over project_closure.component_presence_tier —
        the same presence primitive classify_component (BOM/Continuity) uses,
        so architecture progress and BOM/Continuity can never disagree on
        what counts as "present" again. Behavior unchanged (still exactly
        completeness == 'low'); only the threshold's ownership moved to a
        shared, explicitly-named helper.
        """
        return component_presence_tier(component) == "stub"

    @staticmethod
    def get_block_in_progress_reason(state: Any, block: str) -> str:
        """Return the reason a block is in_progress.

        Returns:
            "missing_components" — at least one component key is absent or has
                                   completeness='low'. Applies to composite AND component
                                   blocks that have component keys defined (Bug 67).
            "missing_params"     — all components are present but required params are
                                   missing. Also the default for param blocks.

        This function is the single source of truth for the in_progress cause.
        build_startup_context uses this value to pick the right user-facing message
        without duplicating component-completeness logic.
        """
        block_type = get_block_type(block)
        # Bug 67: "component" blocks (e.g. "control") also have component keys
        # and must show "missing_components" when those keys are absent/low.
        if block_type not in ("composite", "component"):
            return "missing_params"
        component_keys = BLOCK_TO_COMPONENTS.get(block, [])
        if not component_keys:
            return "missing_params"
        components = state.design_properties.components
        missing = [
            k for k in component_keys
            if k not in components or JarvisOrchestrator._component_is_low(components[k])
        ]
        if missing:
            return "missing_components"
        return "missing_params"

    def _set_pending_next_block(self) -> None:
        """After completing a param block, pre-load the next pending block into session state.

        Called at the end of the DEFINE_MISSING_PARAMETERS handler so that the next
        affirmative input from the user immediately opens the correct wizard — either
        the numeric param wizard (param-driven blocks) or the component description
        prompt (component-driven blocks).

        Does nothing when:
        - no active project exists
        - system is not defined (no priority order)

        FN-021: when there is genuinely no next pending block (architecture is
        fully acquired — any block, not a specific one), and the runtime
        session is still sat inside an acquisition wizard
        (DEFINE_MISSING_PARAMETERS), the session is cleared to IDLE instead of
        silently returning. Without this, the wizard's stale
        pending_missing_params/param_definition_reason survive architecture
        completion and steal the next unrelated turn (e.g. an iterate-class
        phrase gets answered with a leftover component_description_prompt).
        Gated on mode so callers that only pre-load from IDLE (Bug54/FN-011/
        FN-014 bridges — none of them are ever inside DEFINE_MISSING_PARAMETERS
        when they call this) keep working unchanged:
        "nothing left to pre-load" there is a true no-op, not a wizard finish.
        """
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return
        if not project_state.design_properties.system_defined:
            return
        pending = self._next_pending_block(project_state)
        if pending is None:
            if self.state_manager.get_runtime_session().mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS:
                self.state_manager.clear_runtime_session()
            return
        block_key, _status = pending
        block_type = get_block_type(block_key)
        if block_type == "param":
            # Param-driven block: load the missing params for the numeric wizard.
            param_reason = get_param_reason_for_block(block_key)
            missing = missing_params_for_reason(param_reason, project_state.current_parameters or {})
            if not missing:
                return
            updated_session = self.state_manager.runtime_state.session.model_copy(update={
                "pending_define_missing": True,
                "pending_missing_params": missing,
                "pending_missing_reason": param_reason,
            })
        elif block_type == "composite":
            # Composite block: Phase A (components) before Phase B (params).
            component_keys = BLOCK_TO_COMPONENTS.get(block_key, [])
            components = project_state.design_properties.components
            missing_component_keys = [
                k for k in component_keys
                if components.get(k) is None or components[k].completeness == "low"
            ]
            if missing_component_keys:
                # Phase A: components missing → component description wizard.
                updated_session = self.state_manager.runtime_state.session.model_copy(update={
                    "pending_define_missing": True,
                    "pending_missing_params": missing_component_keys,
                    "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
                })
            else:
                # Phase B: components OK → numeric param wizard.
                param_reason = get_param_reason_for_block(block_key)
                missing = missing_params_for_reason(param_reason, project_state.current_parameters or {})
                if not missing:
                    return
                updated_session = self.state_manager.runtime_state.session.model_copy(update={
                    "pending_define_missing": True,
                    "pending_missing_params": missing,
                    "pending_missing_reason": param_reason,
                })
        else:
            # Component-driven block: set MISSING_COMPONENT_DEFINITION so the intercept
            # in handle_user_text routes the next input to _handle_component_description.
            component_keys = BLOCK_TO_COMPONENTS.get(block_key, [])
            updated_session = self.state_manager.runtime_state.session.model_copy(update={
                "pending_define_missing": True,
                "pending_missing_params": component_keys,
                "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
            })
        self.state_manager.set_runtime_session(updated_session)

    def _next_pending_block(self, project_state: Any) -> tuple[str, str] | None:
        """Return (block_key, status) for the first incomplete block in system_priority.

        Status is 'not_started' or 'in_progress'.
        Returns None when all blocks are complete or system_priority is empty.
        """
        priority = project_state.design_properties.system_priority
        if not priority:
            return None
        params = project_state.current_parameters or {}
        dp = project_state.design_properties
        for block in priority:
            status = self._block_progress_status(block, dp, params)
            if status != "complete":
                return (block, status)
        return None

    def _architecture_progress_str(self, project_state: Any) -> str:
        """Return a compact fraction string, e.g. '1/4', for UI display."""
        priority = project_state.design_properties.system_priority
        if not priority:
            return ""
        params = project_state.current_parameters or {}
        dp = project_state.design_properties
        completed = sum(
            1 for b in priority
            if self._block_progress_status(b, dp, params) == "complete"
        )
        return f"{completed}/{len(priority)}"

    def _block_label_for(self, project_state: Any, block_key: str) -> str:
        """Return the human-readable label for a block.

        For composite blocks that are in_progress, the label is dynamically
        refined to reflect *what* is actually missing (components, params,
        or both) — G20/G20-B fix.
        """
        params = project_state.current_parameters or {}
        dp = project_state.design_properties
        status = self._block_progress_status(block_key, dp, params)

        if status == "in_progress" and get_block_type(block_key) == "composite":
            label = self._composite_in_progress_label(project_state, block_key)
            if label:
                return label

        vehicle_type = params.get("vehicle_type", "")
        catalog_key = VEHICLE_TYPE_ALIASES.get((vehicle_type or "").lower(), "")
        arch = SYSTEM_ARCHITECTURES.get(catalog_key)
        if arch:
            label = arch.get("block_labels", {}).get(block_key)
            if label:
                return label
        fallback: dict[str, str] = {
            "propulsion":   "Propulsión",
            "energy":       "Energía (batería)",
            "structure":    "Estructura",
            "control":      "Control",
            "actuation":    "Actuación",
            "transmission": "Transmisión",
        }
        return fallback.get(block_key, block_key)

    def _composite_in_progress_label(
        self, project_state: Any, block_key: str,
    ) -> str | None:
        """Build a specific label for a composite block that is in_progress.

        Returns None when the block is not composite or the sub-parts cannot
        be determined, so the caller falls back to the static label.
        """
        component_keys = BLOCK_TO_COMPONENTS.get(block_key, [])
        components = project_state.design_properties.components
        missing_comps = [
            k for k in component_keys
            if k not in components or self._component_is_low(components[k])
        ]

        param_reason = get_param_reason_for_block(block_key)
        if param_reason:
            required = params_for_reason(param_reason)
            current = project_state.current_parameters or {}
            missing_params = [p for p in required if current.get(p) is None] if required else []
        else:
            missing_params = []

        if not missing_comps and not missing_params:
            return None

        _COMP_LABELS: dict[str, str] = {
            "battery": "batería",
            "motors": "motores",
            "propellers": "hélices",
        }
        _PARAM_LABELS: dict[str, str] = {
            "motor_power_w": "potencia motores",
            "battery_capacity_wh": "capacidad batería",
            "motor_count": "nº motores",
            "per_motor_max_thrust_n": "empuje por motor",
        }

        parts: list[str] = []
        for k in missing_comps:
            parts.append(_COMP_LABELS.get(k, k))
        for p in missing_params:
            parts.append(_PARAM_LABELS.get(p, p))

        if not parts:
            return None

        _BLOCK_BASE: dict[str, str] = {
            "energy": "Energía",
            "propulsion": "Propulsión",
        }
        base = _BLOCK_BASE.get(block_key, block_key.capitalize())
        return f"{base} ({' + '.join(parts)})"

    def _component_prompt_for_first_missing(self, keys: list[str]) -> str:
        """Return a context-specific description prompt for the first key in ``keys``."""
        if not keys:
            return "Describe el componente."
        return _COMPONENT_PROMPTS.get(keys[0], f"Describe el componente: {keys[0]}")

    def _apply_inferred_component_spec(
        self, project_state: ProjectState, spec: ComponentSpec
    ) -> tuple[ProjectState, str]:
        """Write one inferred component and optionally recalculate. Returns (state, msg)."""
        if spec.suggested_key == "frame":
            mass_prop = spec.properties.get("mass_kg")
            mat_prop = spec.properties.get("material")
            mass_val: float | None = mass_prop.value if mass_prop else None
            material_val: str | None = mat_prop.value if mat_prop else None
            updated_state = set_frame_material(project_state, mass_val, material_val)
            try:
                params = updated_state.current_parameters or {}
                calculations = self.calculation_engine.build(params)
                autonomy_threshold = updated_state.parsed_constraints.get("autonomy_min")
                simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
                updated_state = self.state_manager.record_action(
                    state=updated_state,
                    action=HistoryEntry(
                        action=ActionName.ITERATE,
                        summary=f"Frame definido: {material_val or '?'} {mass_val or '?'}kg",
                    ),
                    latest_results={
                        "calculations": calculations.model_dump(),
                        "simulation": simulation.model_dump(),
                    },
                )
            except Exception:  # noqa: BLE001
                pass
            parts = []
            if material_val:
                parts.append(material_val.replace("_", " "))
            if mass_val is not None:
                parts.append(f"{mass_val}kg")
            desc = " ".join(parts) if parts else "frame"
            return updated_state, f"Frame registrado: {desc}."

        if spec.suggested_key == "battery":
            cap_prop = spec.properties.get("battery_capacity_wh")
            capacity_val: float | None = cap_prop.value if cap_prop else None
            updated_state = set_battery_component(project_state, spec, capacity_val)
            try:
                params = updated_state.current_parameters or {}
                calculations = self.calculation_engine.build(params)
                autonomy_threshold = updated_state.parsed_constraints.get("autonomy_min")
                simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
                updated_state = self.state_manager.record_action(
                    state=updated_state,
                    action=HistoryEntry(
                        action=ActionName.ITERATE,
                        summary=f"Batería definida: {capacity_val}Wh",
                    ),
                    latest_results={
                        "calculations": calculations.model_dump(),
                        "simulation": simulation.model_dump(),
                    },
                )
            except Exception:  # noqa: BLE001
                pass
            saved_msg = (
                f"Batería registrada: {capacity_val}Wh." if capacity_val else "Batería registrada."
            )
            return updated_state, saved_msg

        if spec.suggested_key == "motors":
            power_prop = spec.properties.get("power_w")
            power_val: float | None = power_prop.value if power_prop else None
            updated_state = set_motor_component(project_state, spec, power_val)
            try:
                params = updated_state.current_parameters or {}
                calculations = self.calculation_engine.build(params)
                autonomy_threshold = updated_state.parsed_constraints.get("autonomy_min")
                simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
                updated_state = self.state_manager.record_action(
                    state=updated_state,
                    action=HistoryEntry(
                        action=ActionName.ITERATE,
                        summary=f"Motores definidos: {power_val}W" if power_val else "Motores definidos",
                    ),
                    latest_results={
                        "calculations": calculations.model_dump(),
                        "simulation": simulation.model_dump(),
                    },
                )
            except Exception:  # noqa: BLE001
                pass
            saved_msg = (
                f"Motores registrados: {power_val}W." if power_val else "Motores registrados."
            )
            return updated_state, saved_msg

        if spec.suggested_key == "propellers":
            updated_state = set_propeller_component(project_state, spec)
            try:
                params = updated_state.current_parameters or {}
                calculations = self.calculation_engine.build(params)
                autonomy_threshold = updated_state.parsed_constraints.get("autonomy_min")
                simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
                updated_state = self.state_manager.record_action(
                    state=updated_state,
                    action=HistoryEntry(
                        action=ActionName.ITERATE,
                        summary="Hélices definidas",
                    ),
                    latest_results={
                        "calculations": calculations.model_dump(),
                        "simulation": simulation.model_dump(),
                    },
                )
            except Exception:  # noqa: BLE001
                pass
            return updated_state, "Hélices registradas."

        if spec.suggested_key == "esc":
            updated_state = set_control_component(project_state, spec)
            current_prop = spec.properties.get("current_a")
            current_val: float | None = current_prop.value if current_prop else None
            if current_val is not None:
                amps = int(current_val) if current_val == int(current_val) else current_val
                return updated_state, f"ESC registrado: {amps}A."
            return updated_state, "ESC registrado."

        updated_state = set_control_component(project_state, spec)
        return updated_state, f"{spec.suggested_key.replace('_', ' ').capitalize()} registrado."

    # Continuity Hardening ★4 (G14): the propeller ComponentRule's own keywords —
    # reused here, not duplicated, so a future keyword addition to that rule
    # automatically widens this predicate too.
    _PROPELLER_KEYWORDS = ("helice", "hélice", "propeller", "props")

    @staticmethod
    def _looks_clearly_propeller_shaped(text: str) -> bool:
        """G14 fix: is *text* unambiguously a propeller description?

        Used to gate the FN-019 force-propellers bypass when ``motors`` is
        also a pending acquisition target in the same composite wizard — see
        ``_handle_component_description``. A bare ``"NxP"`` match alone is
        NOT enough (a motor phrase like ``"1x 2306 2400KV 50W"`` matches the
        same regex with diameter=1, pitch=2306): also require the matched
        pair to fall inside a realistic propeller size band, and the absence
        of a KV marker (motor phrases almost always carry one, propeller
        phrases never do).
        """
        lower = text.lower()
        if any(kw in lower for kw in JarvisOrchestrator._PROPELLER_KEYWORDS):
            return True
        if re.search(r"\bkv\b", lower):
            return False
        match = re.search(r"\b(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\b", lower)
        if not match:
            return False
        diameter, pitch = float(match.group(1)), float(match.group(2))
        return 1.5 <= diameter <= 30 and 0.5 <= pitch <= 20

    # Continuity Hardening ★2 (G12/G8 refuse policy) — noun phrases for the
    # honest refuse line. Deliberately separate from _block_label_for's
    # block-progress labels (different vocabulary: component keys, not
    # block keys; different grammatical context: mid-sentence, lowercase).
    _ACQUISITION_TARGET_LABELS: dict[str, str] = {
        "motors": "los motores",
        "propellers": "las hélices",
        "esc": "el ESC",
        "battery": "la batería",
        "frame": "el frame",
        "flight_controller": "la controladora de vuelo",
        "sensors": "los sensores",
    }
    _BLOCK_REFUSE_LABELS: dict[str, str] = {
        "propulsion": "la propulsión",
        "energy": "la energía",
        "structure": "la estructura",
        "control": "el control",
        "actuation": "la actuación",
        "transmission": "la transmisión",
    }

    def _maybe_refuse_different_target(
        self, user_input: str, expected_keys: list[str]
    ) -> dict[str, Any] | None:
        """Continuity Hardening ★2 — refuse (never retarget) when *user_input*
        clearly names something OTHER than the active acquisition target.

        Two shapes, one shared response, per design ★2/contract Slice 2:
          - G12: "definir/declarar/completar <a different block>" while a
            DEFINE_MISSING wizard is open for a component belonging to a
            different block. `_try_reprompt_active_block_declaration`
            (C-033) already handles the SAME-block case upstream of this
            call and returns before `_handle_component_description` is ever
            reached for it — by the time this runs, any declare-block match
            found here is necessarily for a different block.
          - G8: an engineering-intent phrase ("reducir payload") or an
            explore-shaped phrase ("explora opciones") — today silently
            absorbed into this method's own low-completeness fallback,
            which just re-shows the active wizard's brief with no
            acknowledgment. See SYS-MAP-004 / investigation §3.3.

        Returns None (caller proceeds unchanged) when neither shape
        matches. Never mutates session state — `cancelar` (C-034) remains
        the only way to actually switch targets, per ★2's "refuse, not
        retarget" lock.
        """
        if not expected_keys:
            return None
        active_key = expected_keys[0]
        active_label = self._ACQUISITION_TARGET_LABELS.get(active_key, active_key)

        block_key = self.intent_resolver.resolve_declare_block_request(user_input)
        if block_key is not None and active_key not in BLOCK_TO_COMPONENTS.get(block_key, []):
            other_label = self._BLOCK_REFUSE_LABELS.get(block_key, block_key)
            return {
                "status": "interactive",
                "action": "component_description_prompt",
                "message": (
                    f"Estoy definiendo {active_label}. Escribe 'cancelar' primero "
                    f"si quieres pasar a definir {other_label}."
                ),
            }

        from jarvis.core.goal_planner import is_engineering_intention

        goal_key = is_engineering_intention(user_input)
        is_explore = (
            goal_key is None
            and self.intent_resolver.resolve_intent(user_input) == "explore_design_space"
        )
        if goal_key is not None or is_explore:
            return {
                "status": "interactive",
                "action": "component_description_prompt",
                "message": (
                    f"Estoy definiendo {active_label}. Escribe 'cancelar' primero "
                    "si quieres explorar otras opciones de diseño."
                ),
            }
        return None

    # R3a: human-readable labels for numeric wizard reasons. All four
    # MISSING_FORCE_REASONS values (parameter_requirements.py) covered —
    # MISSING_COMPONENT_DEFINITION never reaches this dict (numeric-only).
    _NUMERIC_REASON_LABELS: dict[str, str] = {
        "missing_propulsion_parameters": "los parámetros de propulsión",
        "missing_energy_parameters": "los parámetros de energía",
        "missing_propeller_parameters": "los parámetros de hélice",
        "missing_transmission_parameters": "los parámetros de transmisión",
    }

    def _maybe_refuse_numeric_submode(
        self, user_input: str, session: Any,
    ) -> dict[str, Any] | None:
        """R3a Slice 1: port ★2's refuse logic to the numeric sub-mode.

        Detects the same three shapes ``_maybe_refuse_different_target`` already
        handles for component sub-mode — engineering-intent, explore, and
        different-block-declare — and returns an honest refusal instead of
        letting them fall to ``ParamDefinitionSession.answer()``'s generic
        ``"No reconozco X como valor."`` parse error.

        Never mutates session state.
        """
        reason = session.param_definition_reason or ""
        reason_label = self._NUMERIC_REASON_LABELS.get(reason, reason)

        # Declare-different-block check FIRST — same order
        # _maybe_refuse_different_target uses (component sub-mode), and for
        # the same reason: goal_planner.is_engineering_intention has real
        # keyword overlap with component names (e.g. "definir batería" also
        # matches the "mejorar_autonomia" goal's own keyword list), so
        # checking engineering-intent first would misfire on a plain
        # different-block declare phrase and never reach the block check.
        block_key = self.intent_resolver.resolve_declare_block_request(user_input)
        if block_key is not None:
            other_label = self._BLOCK_REFUSE_LABELS.get(block_key, block_key)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": (
                    f"Estoy definiendo {reason_label}. Escribe 'cancelar' primero "
                    f"si quieres pasar a definir {other_label}."
                ),
            }

        from jarvis.core.goal_planner import is_engineering_intention

        goal_key = is_engineering_intention(user_input)
        is_explore = (
            goal_key is None
            and self.intent_resolver.resolve_intent(user_input) == "explore_design_space"
        )

        if goal_key is not None or is_explore:
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "message": (
                    f"Estoy definiendo {reason_label}. Escribe 'cancelar' primero "
                    "si quieres explorar otras opciones de diseño."
                ),
            }

        return None

    def _get_define_missing_reprompt(self, session: Any) -> str:
        """Return the current wizard's pending question for ``wizard_reprompt``.

        Works for both sub-modes: component (delegates to the same
        ``_component_prompt_for_first_missing``/``_COMPONENT_PROMPTS`` Brief
        machinery FN-017/018 established — never a hand-rolled generic
        string, same discipline ``get_current_prompt`` documents for
        ITERATE's own ``wizard_reprompt``) and numeric (delegates to
        ``ParamDefinitionSession._question_for_param``).
        """
        if (
            session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
            or session.param_definition_reason == MISSING_COMPONENT_DEFINITION
        ):
            keys = list(session.pending_missing_params or session.pending_param_definitions or [])
            return self._component_prompt_for_first_missing(keys)

        pending = list(session.pending_param_definitions or [])
        if pending:
            suggestions = list(session.motor_suggestions or [])
            return self.param_definition_session._question_for_param(pending[0], suggestions)
        return "Indica el valor del parámetro pendiente."

    def _offer_component_motor_catalog(
        self, session: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """G21 ★3: catalog list bridge for the motors COMPONENT sub-mode
        (MISSING_COMPONENT_DEFINITION) — same design-space filters and
        formatting ``ParamDefinitionSession._offer_catalog_help`` uses for
        the numeric energy wizard, but populates ``motor_suggestions`` for
        THIS sub-mode's pick-matching (``_handle_component_description``),
        not the numeric one.
        """
        from jarvis.core.motor_catalog_assist import (
            build_motor_catalog_suggestions,
            derive_kv_prop_filters,
            format_motor_catalog_suggestions,
            format_no_thrust_candidate_message,
        )

        project_state = self._safe_active_project()
        suggestions = (
            build_motor_catalog_suggestions(project_state) if project_state is not None else []
        )
        # Prop-3 ★4/§2 (Bat-3: extended to battery): offering a fresh motor
        # list retires any pending propeller/battery pick to avoid
        # cross-pick ambiguity (symmetric with _offer_component_propeller_
        # catalog / _offer_component_battery_catalog clearing motor_suggestions).
        updated = session.model_copy(update={
            "motor_suggestions": suggestions, "propeller_suggestions": [], "battery_suggestions": [],
        })
        self.state_manager.set_runtime_session(updated)
        if not suggestions:
            from jarvis.core.project_closure import derive_physical_requirements

            kv_hint, prop_inch = derive_kv_prop_filters(project_state)
            thrust_hint = (
                derive_physical_requirements(project_state).get("thrust_per_motor_needed_n")
                if project_state is not None
                else None
            )
            return {
                "status": "interactive",
                "action": "component_description_prompt",
                "message": format_no_thrust_candidate_message(
                    required_n=thrust_hint, kv=kv_hint, prop_inch=prop_inch
                ),
            }
        return {
            "status": "interactive",
            "action": "component_description_prompt",
            "message": format_motor_catalog_suggestions(
                suggestions, param="per_motor_max_thrust_n"
            ),
            "motor_suggestions": suggestions,
        }

    def _apply_component_motor_catalog_pick(
        self, suggestion: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """G21 ★3: bind a catalog pick in the motors COMPONENT sub-mode and
        advance the wizard to the next expected key. Reuses the same writers
        the numeric sub-mode's ``ParamDefinitionSession._apply_catalog_motor_pick``
        uses (``bind_motor_from_catalog`` + ``set_motor_component`` — Impl B's
        only bind path, no parallel identity path here) but advances
        ``design_properties.components``/``expected_keys`` the way
        ``_handle_component_description``'s freeform-save path does, since
        there is no numeric ``pending_param_definitions`` list in this
        sub-mode.
        """
        from jarvis.core.catalog_bind import bind_motor_from_catalog

        watts_raw = suggestion.get("max_watts")
        watts = float(watts_raw) if watts_raw is not None else None
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return {
                "status": "error",
                "action": "component_description_prompt",
                "message": "No hay proyecto activo. Crea uno primero.",
            }
        spec = bind_motor_from_catalog(suggestion)
        updated_state = set_motor_component(project_state, spec, watts)
        self.workspace_manager.save_state(updated_state)

        cleared = self.state_manager.get_runtime_session().model_copy(
            update={"motor_suggestions": []}
        )
        self.state_manager.set_runtime_session(cleared)

        power_bit = f"~{int(watts)}W, " if watts is not None else ""
        saved_msg = (
            f"Motor elegido: {suggestion['name']} ({power_bit}{suggestion['thrust_n']}N)."
        )
        components = updated_state.design_properties.components
        still_missing = [
            k for k in expected_keys
            if components.get(k) is None or components[k].completeness == "low"
        ]
        if not still_missing:
            self._set_pending_next_block()
            result: dict[str, Any] = {
                "status": "ok",
                "action": "component_description_saved",
                "message": saved_msg,
            }
            return self._append_arch_progress_hint(result)

        follow_up = self._component_prompt_for_first_missing(still_missing)
        return {
            "status": "ok",
            "action": "component_description_saved",
            "message": f"{saved_msg} {follow_up}",
        }

    def _offer_component_propeller_catalog(
        self, session: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """Prop-3: catalog list bridge for the propellers COMPONENT sub-mode
        — mirrors ``_offer_component_motor_catalog``. ★1: suggestions come
        only from ``build_propeller_catalog_suggestions`` (motor-compatibility
        filter, no full-catalog dump when no motor is bound yet). Clears
        ``motor_suggestions`` (★4/§2: offering a new list retires the other
        family's pending pick to avoid cross-pick ambiguity).
        """
        from jarvis.core.propeller_catalog_assist import (
            build_propeller_catalog_suggestions,
            format_propeller_catalog_suggestions,
        )

        project_state = self._safe_active_project()
        suggestions = (
            build_propeller_catalog_suggestions(project_state) if project_state is not None else []
        )
        updated = session.model_copy(update={
            "propeller_suggestions": suggestions,
            "motor_suggestions": [],
            "battery_suggestions": [],
        })
        self.state_manager.set_runtime_session(updated)
        return {
            "status": "interactive",
            "action": "component_description_prompt",
            "message": format_propeller_catalog_suggestions(suggestions),
            "propeller_suggestions": suggestions,
        }

    def _apply_component_propeller_catalog_pick(
        self, suggestion: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """Prop-3: bind a catalog pick in the propellers COMPONENT sub-mode
        and advance the wizard — mirrors ``_apply_component_motor_catalog_pick``.

        ★5 (locked): after ``set_propeller_component``, when motors is
        already catalog-bound, explicitly re-calls ``set_motor_component``
        with the existing motor spec so ``resolve_operating_point`` re-runs
        with the now-available propeller ``catalog_ref`` context (nothing
        else does this automatically — investigation_report_propeller_
        catalog_bind_ux.md §5). No new refresh helper — same writer, called
        again, same as the already-proven pattern in
        ``scripts/cli_probe_phase2_lookup_op.py``.
        """
        from jarvis.core.catalog_bind import bind_propeller_from_catalog

        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return {
                "status": "error",
                "action": "component_description_prompt",
                "message": "No hay proyecto activo. Crea uno primero.",
            }
        spec = bind_propeller_from_catalog(suggestion["name"])
        updated_state = set_propeller_component(project_state, spec)

        # ★5: re-resolve motor OP now that a propeller catalog_ref exists.
        motors_spec = updated_state.design_properties.components.get("motors")
        motors_catalog_ref = getattr(motors_spec, "catalog_ref", None)
        if motors_catalog_ref is not None and motors_catalog_ref.family == "motor":
            power_prop = motors_spec.properties.get("power_w")
            power_w = (
                float(power_prop.value)
                if power_prop is not None and power_prop.value is not None
                else (updated_state.current_parameters or {}).get("motor_power_w")
            )
            updated_state = set_motor_component(updated_state, motors_spec, power_w)

        self.workspace_manager.save_state(updated_state)

        cleared = self.state_manager.get_runtime_session().model_copy(
            update={"propeller_suggestions": []}
        )
        self.state_manager.set_runtime_session(cleared)

        saved_msg = f"Hélice elegida: {suggestion['name']} ({suggestion['diameter_in']}x{suggestion['pitch_in']})."
        components = updated_state.design_properties.components
        still_missing = [
            k for k in expected_keys
            if components.get(k) is None or components[k].completeness == "low"
        ]
        if not still_missing:
            self._set_pending_next_block()
            result: dict[str, Any] = {
                "status": "ok",
                "action": "component_description_saved",
                "message": saved_msg,
            }
            return self._append_arch_progress_hint(result)

        follow_up = self._component_prompt_for_first_missing(still_missing)
        return {
            "status": "ok",
            "action": "component_description_saved",
            "message": f"{saved_msg} {follow_up}",
        }

    def _offer_component_battery_catalog(
        self, session: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """Bat-3: catalog list bridge for the battery COMPONENT sub-mode —
        mirrors ``_offer_component_propeller_catalog``. ★1 (Bat-2): suggestions
        come only from ``build_battery_catalog_suggestions`` (``ComponentLibrary.
        list_batteries()``, no hardcode). Clears ``motor_suggestions``/
        ``propeller_suggestions`` (★4/§2: offering a new list retires any other
        family's pending pick to avoid cross-pick ambiguity — same rule the
        motor/propeller offers already apply to each other).
        """
        from jarvis.core.battery_catalog_assist import (
            build_battery_catalog_suggestions,
            format_battery_catalog_suggestions,
        )

        project_state = self._safe_active_project()
        suggestions = (
            build_battery_catalog_suggestions(project_state) if project_state is not None else []
        )
        updated = session.model_copy(update={
            "battery_suggestions": suggestions,
            "motor_suggestions": [],
            "propeller_suggestions": [],
        })
        self.state_manager.set_runtime_session(updated)
        return {
            "status": "interactive",
            "action": "component_description_prompt",
            "message": format_battery_catalog_suggestions(suggestions),
            "battery_suggestions": suggestions,
        }

    def _apply_component_battery_catalog_pick(
        self, suggestion: Any, expected_keys: list[str]
    ) -> dict[str, Any]:
        """Bat-3: bind a catalog pick in the battery COMPONENT sub-mode and
        advance the wizard — mirrors ``_apply_component_propeller_catalog_pick``.

        Apply path locked by the contract (§5): ``bind_battery_from_catalog``
        + ``set_battery_component`` — the same bind→writer chain the
        investigation proved sufficient (test-callable, zero production call
        sites before this IC). No new refresh helper — unlike the propeller
        pick, a battery bind does not need to re-trigger
        ``resolve_operating_point`` (P2-1's OP resolution reads the battery's
        catalog_ref for voltage, but that read happens inside
        ``set_motor_component`` itself, not here — a battery-only bind with
        no motor re-write leaves any already-resolved OP as-is until the next
        motor/propeller write, same as today's unbound-battery behavior).
        """
        from jarvis.core.catalog_bind import bind_battery_from_catalog

        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return {
                "status": "error",
                "action": "component_description_prompt",
                "message": "No hay proyecto activo. Crea uno primero.",
            }
        spec = bind_battery_from_catalog(suggestion["name"])
        updated_state = set_battery_component(
            project_state, spec, spec.properties["battery_capacity_wh"].value
        )
        self.workspace_manager.save_state(updated_state)

        cleared = self.state_manager.get_runtime_session().model_copy(
            update={"battery_suggestions": []}
        )
        self.state_manager.set_runtime_session(cleared)

        saved_msg = f"Batería elegida: {suggestion['name']} ({suggestion['energy_wh']}Wh)."
        components = updated_state.design_properties.components
        still_missing = [
            k for k in expected_keys
            if components.get(k) is None or components[k].completeness == "low"
        ]
        if not still_missing:
            self._set_pending_next_block()
            result: dict[str, Any] = {
                "status": "ok",
                "action": "component_description_saved",
                "message": saved_msg,
            }
            return self._append_arch_progress_hint(result)

        follow_up = self._component_prompt_for_first_missing(still_missing)
        return {
            "status": "ok",
            "action": "component_description_saved",
            "message": f"{saved_msg} {follow_up}",
        }

    def _handle_component_description(
        self,
        user_input: str,
        session: Any,
        *,
        structural_confirmed: bool = False,
        refuse_checked: bool = False,
    ) -> dict[str, Any]:
        """Handle user input when mode is DEFINE_MISSING_PARAMETERS and reason is MISSING_COMPONENT_DEFINITION.

        Expected component keys for the active block are read from session.pending_missing_params.
        Routing is based on spec.suggested_key:
          - matches expected key → dispatch to appropriate writer (_set_frame_material or _set_control_component)
          - does not match       → contextual redirect (no write)
        Affirmative inputs → context-aware prompt based on which components still need defining.

        D7: mixed phrases (``4 motores 920KV, hélices 10x4.5``) save every matched component
        in one turn via ``infer_components``.
        """
        from jarvis.core.component_inference import (
            infer_component,
            infer_component_for_key,
            infer_components,
        )
        from jarvis.core.param_definition_session import (
            begin_structural_confirm,
            structural_confirm_needed,
        )
        from jarvis.domains.aerial import aerial_registry

        expected_keys: list[str] = list(session.pending_missing_params or [])
        if not expected_keys and session.param_definition_reason == MISSING_COMPONENT_DEFINITION:
            # FN-017 B1 defensive read: pending_missing_params should already be
            # populated by ParamDefinitionSession.start() for this reason (see
            # param_definition_session.py), but fall back to the field the live
            # wizard actually advances (pending_param_definitions) so this method
            # never silently operates on an empty scope.
            expected_keys = list(session.pending_param_definitions or [])

        # Continuity Hardening ★2 (G12/G8): refuse before anything else gets
        # a chance to silently re-show this wizard's own brief as if the
        # user's "definir <other>" / engineering-intent / explore phrase had
        # not been understood. Skipped when the DEFINE_MISSING R3b gate already
        # ran the same check (refuse_checked=True) — same inputs, same result.
        if not refuse_checked:
            refusal = self._maybe_refuse_different_target(user_input, expected_keys)
            if refusal is not None:
                return refusal

        # G21 ★3 / Prop-3 ★4: motors + propellers catalog help-choose / pick
        # bridge in COMPONENT sub-mode — runs before infer_components so a
        # numbered pick ("1") or a help-choose phrase is never mistaken for a
        # freeform component description. Help-choose always (re)shows the
        # list; a pick is only attempted once suggestions are actually on
        # the table.
        #
        # ★4 (Prop-3, locked): gated on _wants_catalog_help (still
        # incomplete OR freeform-without-catalog_ref) — NOT bare
        # `"motors" in expected_keys`. A composite ["motors","propellers"]
        # wizard keeps expected_keys static for the whole session, so a bare
        # membership check would starve the propeller branch forever once
        # motors is bound (investigation_report_propeller_catalog_bind_ux.md
        # §4). Motors wins when both want help — existing Continuity
        # motors-first precedent (Continuity Hardening ★4/G14), unchanged.
        gate_project_state = self._safe_active_project()
        gate_components = (
            (getattr(gate_project_state.design_properties, "components", {}) or {})
            if gate_project_state is not None else {}
        )
        motors_want_help = "motors" in expected_keys and _wants_catalog_help(gate_components.get("motors"))
        propellers_want_help = "propellers" in expected_keys and _wants_catalog_help(gate_components.get("propellers"))

        if motors_want_help or ("motors" in expected_keys and session.motor_suggestions):
            from jarvis.core.motor_catalog_assist import (
                is_help_choose_phrase,
                match_suggestion_by_input,
                resolve_motor_from_text,
            )

            if motors_want_help and is_help_choose_phrase(user_input):
                return self._offer_component_motor_catalog(session, expected_keys)
            if session.motor_suggestions:
                picked = match_suggestion_by_input(user_input, session.motor_suggestions)
                if picked is None:
                    picked = resolve_motor_from_text(user_input)
                if picked is not None:
                    return self._apply_component_motor_catalog_pick(picked, expected_keys)

        if propellers_want_help or ("propellers" in expected_keys and session.propeller_suggestions):
            from jarvis.core.propeller_catalog_assist import (
                is_help_choose_phrase as propeller_is_help_choose_phrase,
                match_suggestion_by_input as propeller_match_suggestion_by_input,
            )

            if propellers_want_help and propeller_is_help_choose_phrase(user_input):
                return self._offer_component_propeller_catalog(session, expected_keys)
            if session.propeller_suggestions:
                picked = propeller_match_suggestion_by_input(user_input, session.propeller_suggestions)
                if picked is not None:
                    return self._apply_component_propeller_catalog_pick(picked, expected_keys)

        # Bat-3/4: battery catalog help-choose / pick bridge — same ★4 gate
        # shape as motors/propellers (_wants_catalog_help, not bare key
        # membership) so a composite energy wizard ["battery","motors"]
        # doesn't starve this branch once motors is bound.
        battery_wants_help = "battery" in expected_keys and _wants_catalog_help(gate_components.get("battery"))
        if battery_wants_help or ("battery" in expected_keys and session.battery_suggestions):
            from jarvis.core.battery_catalog_assist import (
                is_help_choose_phrase as battery_is_help_choose_phrase,
                match_suggestion_by_input as battery_match_suggestion_by_input,
            )

            if battery_wants_help and battery_is_help_choose_phrase(user_input):
                return self._offer_component_battery_catalog(session, expected_keys)
            if session.battery_suggestions:
                picked = battery_match_suggestion_by_input(user_input, session.battery_suggestions)
                if picked is not None:
                    return self._apply_component_battery_catalog_pick(picked, expected_keys)

        # ── Affirmative: user confirmed — emit context-specific prompt ────────
        if self._is_affirmative(user_input):
            try:
                project_state = self.state_manager.load_active_project(self.workspace_manager)
                components = project_state.design_properties.components
                missing_keys = [
                    k for k in expected_keys
                    if components.get(k) is None or components[k].completeness == "low"
                ]
            except FileNotFoundError:
                missing_keys = expected_keys
            keys_to_prompt = missing_keys if missing_keys else expected_keys
            msg = self._component_prompt_for_first_missing(keys_to_prompt)
            return {"status": "interactive", "action": "component_description_prompt", "message": msg}

        # ── Infer one or more components from freeform description (D7) ───────
        specs = infer_components(user_input, registry=aerial_registry)
        # FN-019: bare propeller size ("10x4.5", no "hélices" keyword) has
        # nothing to trigger aerial_registry's propeller rule, so it falls to
        # generic_component and loops the user on the Brief forever (FN-017/018
        # correctly refuse the generic write). When propellers is the
        # acquisition target and nothing else was recognized, force inference
        # against the propellers rule directly — reuses the same
        # extract_propeller_properties/_propeller_completeness the keyword
        # path already uses, no new regex. Never overrides a real match for
        # another component (e.g. "bateria 2000mAh" while propellers is also
        # pending stays battery) — only fires when every spec found is still
        # generic_component.
        # Continuity Hardening ★4 (G14): when "motors" is ALSO pending in this
        # same composite wizard (e.g. propulsion's ["motors","propellers"]),
        # a motor-shaped phrase like "1x 2306 2400KV 50W" must not be forced
        # into propellers just because its "NxP"-looking substring parses —
        # only force when the phrase is unambiguously propeller-shaped.
        # Singleton expected_keys=["propellers"] (no motors pending) is
        # unaffected — FN-019's original bare-size behavior is unchanged.
        # G17: aerial.py's motors ComponentRule only keys off the literal
        # substring "motor" — a phrase like "1x 2306 2400KV 50W" (no such
        # substring) falls to generic_component even though
        # infer_component_for_key resolves it perfectly (motor_count=1,
        # kv_rating=2400, power_w=50). Force-bind it here, same shape as the
        # force-propellers/force-frame blocks below. Runs FIRST (before
        # force-propellers) so a motor-shaped phrase in a composite
        # ["motors","propellers"] wizard binds motors — Continuity Hardening
        # ★4 (G14) already established "prefer motors" as the tiebreak; this
        # ordering is that tiebreak, no new logic needed.
        # completeness != "low" AND not _looks_clearly_propeller_shaped (not a
        # plain completeness == "high" check): the motors extractor's own
        # motor_count regex spuriously matches a bare "NxP" propeller size
        # (e.g. "10x4.5" → motor_count=10, completeness="medium"), so a bare
        # "medium" guard alone would reopen G14. But a real motor phrase with
        # only count+KV and no thrust/power (e.g. "4x 2306 1400kv" — CLI
        # Routing Residuals G17) never reaches "high" either, since
        # _motor_completeness requires (thrust or power) AND (count or kv) for
        # that tier. _looks_clearly_propeller_shaped is the discriminator that
        # actually distinguishes the two ambiguous cases: it returns False
        # whenever a "kv" marker is present (never true of a real propeller
        # phrase) and True for a bare realistic NxP size — so it keeps a real
        # motor phrase forcing here while still deferring a bare propeller
        # size to the propellers force block below (FN-019/G14 regression
        # guard, unchanged).
        if (
            "motors" in expected_keys
            and all(s.suggested_key == "generic_component" for s in specs)
        ):
            forced = infer_component_for_key(user_input, "motors", registry=aerial_registry)
            if (
                forced is not None
                and forced.completeness != "low"
                and not self._looks_clearly_propeller_shaped(user_input)
            ):
                specs = [forced]
        if (
            "propellers" in expected_keys
            and all(s.suggested_key == "generic_component" for s in specs)
            and (
                "motors" not in expected_keys
                or self._looks_clearly_propeller_shaped(user_input)
            )
        ):
            forced = infer_component_for_key(user_input, "propellers", registry=aerial_registry)
            if forced is not None and forced.completeness != "low":
                specs = [forced]
        # G10 ★3: mirrors the propellers force above. Frame's own keyword list
        # (aerial.ComponentRule for "frame") can miss a material stem even
        # after ★4's expansion (e.g. a future library material not yet added
        # as a keyword) — when the wizard already names frame as the expected
        # key, bypass the keyword gate entirely via infer_component_for_key,
        # same extractor/completeness evaluator, no new parser.
        if "frame" in expected_keys and all(
            s.suggested_key == "generic_component" for s in specs
        ):
            forced = infer_component_for_key(user_input, "frame", registry=aerial_registry)
            if forced is not None and forced.completeness != "low":
                specs = [forced]
        # FN-017 B4: inside a scoped wizard (expected_keys set), never silently
        # write a generic_component placeholder — it has no physical meaning
        # and previously masked the fact that the description wasn't
        # recognized as the actually-pending key. Falls through to the
        # low-completeness branch below, which re-prompts for expected_keys.
        processable = [
            s for s in specs
            if s.completeness in ("medium", "high")
            and not (expected_keys and s.suggested_key == "generic_component")
        ]

        if processable:
            # Keep only specs that belong to the active expected set (when set).
            if expected_keys:
                in_scope = [s for s in processable if s.suggested_key in expected_keys]
                if not in_scope:
                    # FN-ESC-acquisition (post-ERF-2): explicit cross-component save
                    # (e.g. "esc 20a" while wizard expects motors). Narrow: only
                    # OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS + named token in input.
                    out_of_scope = [
                        s for s in processable
                        if s.suggested_key not in expected_keys
                        and s.suggested_key in OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS
                        and s.completeness == "high"
                        and s.properties
                        and user_explicitly_named_component(user_input, s.suggested_key)
                    ]
                    if out_of_scope:
                        processable = out_of_scope
                    else:
                        keys_to_prompt = expected_keys
                        try:
                            project_state = self.state_manager.load_active_project(self.workspace_manager)
                            components = project_state.design_properties.components
                            missing_keys = [
                                k for k in expected_keys
                                if components.get(k) is None or components[k].completeness == "low"
                            ]
                            if missing_keys:
                                keys_to_prompt = missing_keys
                        except FileNotFoundError:
                            pass
                        return {
                            "status": "interactive",
                            "action": "component_description_prompt",
                            "message": self._component_prompt_for_first_missing(keys_to_prompt),
                        }
                else:
                    processable = in_scope

            try:
                project_state = self.state_manager.load_active_project(self.workspace_manager)
            except FileNotFoundError:
                return {
                    "status": "error",
                    "action": "component_description_prompt",
                    "message": "No hay proyecto activo. Crea uno primero.",
                }

            # FN-004: "4 motores" via component intercept must not silent-replace count
            if not structural_confirmed:
                new_count = None
                for spec in processable:
                    if spec.suggested_key != "motors":
                        continue
                    count_prop = (spec.properties or {}).get("motor_count")
                    if count_prop is not None and count_prop.value is not None:
                        try:
                            new_count = float(count_prop.value)
                        except (TypeError, ValueError):
                            new_count = None
                        break
                needed = structural_confirm_needed(
                    project_state.current_parameters, new_count
                )
                if needed:
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
                        param="motor_count",
                        from_value=old_f,
                        to_value=new_f,
                        updates={"motor_count": new_f},
                        impact_note=impact,
                        resume_kind="component",
                        resume_user_input=user_input,
                        resume_expected_keys=list(expected_keys),
                    )

            # D5: track which architecture blocks were incomplete before this write.
            blocks_before: dict[str, str] = {}
            params_now = project_state.current_parameters or {}
            if project_state.design_properties.system_defined:
                for block in project_state.design_properties.system_priority or []:
                    blocks_before[block] = self._block_progress_status(
                        block, project_state.design_properties, params_now
                    )

            saved_msgs: list[str] = []
            updated_state = project_state
            for spec in processable:
                updated_state, msg = self._apply_inferred_component_spec(updated_state, spec)
                saved_msgs.append(msg)

            self.workspace_manager.save_state(updated_state)
            saved_msg = " ".join(saved_msgs)

            # U5: validación inline de restricciones — informativo, nunca bloquea
            _violations = self._check_constraint_violations(updated_state)
            if _violations:
                saved_msg += f" ⚠ {'; '.join(_violations)}"

            # D5: explicit hint when a block becomes complete outside sequential guidance
            if blocks_before:
                newly_complete: list[str] = []
                params_after = updated_state.current_parameters or {}
                for block, before in blocks_before.items():
                    after = self._block_progress_status(
                        block, updated_state.design_properties, params_after
                    )
                    if before != "complete" and after == "complete":
                        newly_complete.append(self._block_label_for(updated_state, block))
                if newly_complete:
                    saved_msg += " ✓ Bloque completado: " + ", ".join(newly_complete) + "."

            components = updated_state.design_properties.components
            still_missing = [
                k for k in expected_keys
                if components.get(k) is None or components[k].completeness == "low"
            ]

            if not still_missing:
                self._set_pending_next_block()
                result: dict[str, Any] = {
                    "status": "ok",
                    "action": "component_description_saved",
                    "message": saved_msg,
                }
                return self._append_arch_progress_hint(result)

            follow_up = self._component_prompt_for_first_missing(still_missing)
            return {
                "status": "ok",
                "action": "component_description_saved",
                "message": f"{saved_msg} {follow_up}",
            }

        # ── completeness == "low" (or filtered out as generic) → targeted follow-up
        # FN-017 B3: key-aware. A scoped wizard (expected_keys set) ALWAYS
        # re-prompts for its own expected key — never the frame-specific
        # material/masa probe for a different pending component (that was the
        # root cause of "definir hélices"/"declarar batería" showing "Indica
        # material y masa..." while propellers was actually pending).
        spec = specs[0] if specs else infer_component(user_input, registry=aerial_registry)
        if spec.suggested_key == "flight_controller" and spec.hints:
            msg = spec.hints[0]
        elif spec.suggested_key == "sensors" and spec.hints:
            msg = spec.hints[0]
        elif (expected_keys and expected_keys[0] == "frame") or (
            not expected_keys and spec.suggested_key == "frame"
        ):
            # Frame's fine-grained probe stays intact — unbroken (criterion H).
            has_mass = "mass_kg" in spec.properties
            has_material = "material" in spec.properties
            if has_material and not has_mass:
                msg = "¿Cuánto pesa el frame? Ej: '450g' o '0.45kg'"
            elif has_mass and not has_material:
                msg = "¿De qué material es? Ej: 'fibra de carbono' o 'aluminio'"
            else:
                msg = "Indica material y masa. Ej: 'fibra de carbono 450g'"
        elif expected_keys:
            # FN-018 C1c: same Brief builder as the other entry points —
            # degrades to the plain COMPONENT_PROMPTS text (via
            # _component_prompt_for_first_missing's fallback) for keys with
            # no Brief blurb, identical to FN-017 behavior.
            brief = build_acquisition_brief(expected_keys[0], self._safe_active_project())
            question = brief["question"] or self._component_prompt_for_first_missing(expected_keys)
            msg = f"{brief['message']}\n\n{question}" if brief["message"] else question
        else:
            fallback_key = spec.suggested_key if spec.suggested_key not in (None, "generic_component") else None
            msg = self._component_prompt_for_first_missing([fallback_key] if fallback_key else [])

        return {
            "status": "interactive",
            "action": "component_description_prompt",
            "message": msg,
        }

    def _check_constraint_violations(self, updated_state: ProjectState) -> list[str]:
        """U5: verifica restricciones numéricas activas contra el último cálculo registrado.

        Retorna lista de strings de warning (vacía si no hay violaciones o sin datos).
        Lee total_mass_kg de updated_state.latest_results — valor ya calculado por
        record_action, sin segunda llamada al motor de cálculo.
        """
        violations: list[str] = []
        try:
            constraints = updated_state.parsed_constraints
            if not isinstance(constraints, dict) or not constraints:
                return violations
            calc = (updated_state.latest_results or {})
            if not isinstance(calc, dict):
                return violations
            calc = calc.get("calculations") or {}
            if not isinstance(calc, dict):
                return violations
            total_mass = calc.get("total_mass_kg")
            if not isinstance(total_mass, (int, float)):
                return violations
            max_weight = constraints.get("max_weight_kg")
            if isinstance(max_weight, (int, float)) and total_mass > max_weight:
                violations.append(
                    f"peso {total_mass:.2f} kg supera máximo {max_weight:.1f} kg"
                )
        except (TypeError, AttributeError):
            return violations
        return violations

    def _append_arch_progress_hint(self, result: dict) -> dict:
        """Append an architecture progress hint to the message of a completed define_missing_params."""
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return result
        if not project_state.design_properties.system_defined:
            return result
        progress = self._architecture_progress_str(project_state)
        pending = self._next_pending_block(project_state)
        if pending is None:
            hint = f"\n\n✓ Arquitectura completa ({progress}) — puedes optimizar o simular."
        else:
            block_key, block_status = pending
            label = self._block_label_for(project_state, block_key)
            if block_status == "in_progress":
                hint = (
                    f"\n\nSiguiente bloque: {label} — en progreso, "
                    f"define los parámetros que faltan. ({progress})"
                )
            else:
                hint = f"\n\nSiguiente bloque: {label} ({progress})"
        return {**result, "message": (result.get("message") or "") + hint}

    def _handle_project_status(self) -> dict[str, Any]:
        """Return a project_status result using build_startup_context (no LLM).

        Reuses the same builder as the startup display so there is a single
        source of truth for the project state snapshot.
        """
        ctx = self.build_startup_context()
        # Bug 54: when the status shows a proactive_question (¿Definimos X ahora?),
        # persist the pending confirmation in session so the next affirmative input
        # can trigger start_define_missing_params without re-reading startup context.
        # Only set in IDLE mode — inside an active wizard the flag would conflict.
        current_mode = self.state_manager.runtime_state.session.mode
        if (
            ctx.get("proactive_question")
            and current_mode == OrchestratorMode.IDLE
        ):
            current_session = self.state_manager.runtime_state.session
            updated_session = current_session.model_copy(update={
                "pending_define_missing": True,
                "pending_missing_params": ctx.get("missing_params") or [],
                "pending_missing_reason": ctx.get("param_definition_reason") or "",
            })
            self.state_manager.set_runtime_session(updated_session)
        return {
            "status": "ok",
            "action": "project_status",
            "startup_context": ctx,
        }

    def _handle_list_materials(self) -> dict[str, Any]:
        """G10 ★8: deterministic materials catalog listing — 0 LLM.

        Reuses ComponentLibrary.list_materials() directly (same authority
        acquisition/mutation already read from) — no separate materials
        vocabulary, no LLM invention of rows.
        """
        from jarvis.knowledge.library import default_library

        materials = default_library.list_materials()
        lines = [f"  • {m.name} — {m.density_kg_m3:g} kg/m³" for m in materials]
        message = "Materiales disponibles en el catálogo:\n" + "\n".join(lines)
        return {
            "status": "ok",
            "action": "list_materials",
            "message": message,
            "materials": [
                {"name": m.name, "density_kg_m3": m.density_kg_m3} for m in materials
            ],
        }

    def _handle_list_motors(self) -> dict[str, Any]:
        """G16-A: deterministic motors catalog listing — 0 LLM, mirrors
        _handle_list_materials (G10 ★8).

        Filtered by the active project's design-space (thrust/kv/prop) via
        the same authority ``build_motor_catalog_suggestions`` already uses
        for assisted acquisition — no separate motors vocabulary, no LLM
        invention of rows. Falls back to an unfiltered catalog dump when
        there's no active project or no design-space filters yet.
        """
        from jarvis.core.motor_catalog_assist import (
            build_motor_catalog_suggestions,
            derive_kv_prop_filters,
        )
        from jarvis.core.project_closure import derive_physical_requirements
        from jarvis.knowledge.library import default_library

        project_state = self._safe_active_project()
        filtered: list[dict[str, Any]] | None = None
        if project_state is not None:
            req = derive_physical_requirements(project_state)
            kv_hint, prop_inch = derive_kv_prop_filters(project_state)
            has_filters = (
                req.get("thrust_per_motor_needed_n") is not None
                or kv_hint is not None
                or prop_inch is not None
            )
            if has_filters:
                filtered = build_motor_catalog_suggestions(project_state, limit=10)

        if filtered is not None:
            lines = [
                f"  • {m['name']} — {m['thrust_n']}N, {m['kv_rating']}KV, {m['weight_g']}g"
                for m in filtered
            ] or ["  (sin candidatos para este espacio de diseño)"]
            message = "Motores del catálogo para este espacio de diseño:\n" + "\n".join(lines)
            return {
                "status": "ok",
                "action": "list_motors",
                "message": message,
                "motors": filtered,
            }

        all_motors = default_library.list_motors()
        lines = [
            f"  • {m.name} — {m.thrust_n}N, {m.kv_rating}KV, {m.weight_g}g"
            for m in all_motors
        ]
        message = "Motores disponibles en el catálogo:\n" + "\n".join(lines)
        return {
            "status": "ok",
            "action": "list_motors",
            "message": message,
            "motors": [
                {"name": m.name, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating, "weight_g": m.weight_g}
                for m in all_motors
            ],
        }

    def _handle_explore(self, goal_key: str | None, user_input: str, llm_interface: Any) -> dict:
        """DSE: explora el espacio de diseño para el goal dado.

        Operación de solo lectura: no muta state, no escribe en disco.
        Si no hay proyecto activo o no se reconoce el goal, cae a analyze.

        FN-024 (H1/C-042): when ``goal_key`` is None (bare "explora opciones"),
        binds through the active Handoff Context created by
        _handle_engineering_intent — never invents a goal, only reuses one
        goal_planner already deterministically resolved and showed to the
        user. The bind is guarded on project_id matching the currently active
        project (the actual "invalidate across a project boundary"
        mechanism — proven at every read, not assumed via a clear that could
        be missed at some other call site) and on dse_capability=="active"
        (a context whose DSE capability was already consumed for this
        operation is never silently reused — see the "already explored"
        branch below, §4.3 of the contract).
        """
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return self._handle_analyze(user_input, llm_interface)

        from jarvis.core.design_explorer import GOAL_LABELS, EXPLORATION_GRIDS
        from jarvis.core.explore_continuity import resolve_explore_goal_with_handoff

        handoff = self.state_manager.get_runtime_session().handoff_context
        context_for_project = (
            handoff is not None and handoff.project_id == project_state.project_id
        )
        bindable_handoff = handoff if context_for_project else None

        # G3 (★1-★4): precedence between a freshly text-derived goal and the
        # active HandoffContext's own goal, for explore-shaped turns only.
        # goal_key is None here for bare "explora opciones" (H1, unchanged
        # by this call — rule 2 just returns handoff.goal_key verbatim).
        text_goal = goal_key
        resolved_goal_key = resolve_explore_goal_with_handoff(user_input, text_goal, bindable_handoff)
        # using_handoff_goal gates dse_capability consumption — it must be
        # True ONLY when the handoff's goal was actually SUBSTITUTED IN
        # (bare "explora opciones", text_goal is None → H1; or a G3 rule-4
        # inheritance, where text_goal on its own would have resolved to
        # something else). An EXPLICIT goal phrase that simply happens to
        # already name the same goal as the active handoff (e.g. "optimiza
        # para estabilidad" while that plan is already active) is FN-024's
        # pre-existing "simplest option" (§4.2) — self-sufficient, capability-
        # neutral, handoff left completely untouched. Conflating the two
        # broke that exact FN-024 regression the first time this was wired.
        using_handoff_goal = bindable_handoff is not None and (
            text_goal is None
            or (
                text_goal != bindable_handoff.goal_key
                and resolved_goal_key == bindable_handoff.goal_key
            )
        )

        bound_from_context = False
        replace_handoff_goal: str | None = None
        if using_handoff_goal:
            if (
                bindable_handoff.dse_capability == "active"
                and resolved_goal_key in EXPLORATION_GRIDS
            ):
                goal_key = resolved_goal_key
                bound_from_context = True
            elif bindable_handoff.dse_capability == "consumed":
                # FN-024 §4.3: DSE for this operation already ran. Do not
                # silently re-bind (would look like magic re-activation) and
                # do not burn an LLM call narrating something already known —
                # a deterministic message is cheap and more honest here. This
                # now also covers G3 continuation phrases ("optimiza payload"
                # after the same goal was already explored), not just bare
                # "explora opciones" — both are the same continuation intent.
                goal_label = GOAL_LABELS.get(bindable_handoff.goal_key, bindable_handoff.goal_key)
                domain = self._GOAL_EXPLORE_DOMAIN.get(
                    bindable_handoff.goal_key, bindable_handoff.goal_key.replace("_", " ")
                )
                return {
                    "status": "ok",
                    "action": "explore_design_space",
                    "goal_key": None,
                    "message": (
                        f"Ya exploré opciones para «{goal_label}» en este turno de trabajo. "
                        "Puedes decir «aplica la mejor» para aplicar el resultado, o pedir "
                        f"una nueva exploración con un objetivo explícito (p. ej. 'optimiza "
                        f"para {domain}')."
                    ),
                }
            else:
                # No bindable context (none, wrong project, or unknown goal) →
                # honest clarification, unchanged from pre-FN-024 behavior.
                return self._handle_analyze(user_input, llm_interface)
        else:
            # Explicit new goal (★2) or no bindable handoff at all — resolved
            # independently of any active context, exactly like a text-derived
            # goal always worked pre-G3.
            goal_key = resolved_goal_key
            if goal_key is None or goal_key not in EXPLORATION_GRIDS:
                return self._handle_analyze(user_input, llm_interface)
            if bindable_handoff is not None and goal_key != bindable_handoff.goal_key:
                # ★4: an explicit override that resolves to a DIFFERENT goal
                # than the prior active handoff — replace it (once the
                # explore below actually succeeds) so a later bare "explora
                # opciones" stays honest about which goal is now active.
                replace_handoff_goal = goal_key

        exploration = self.design_explorer.explore(project_state, goal_key)

        goal_label = GOAL_LABELS.get(goal_key, goal_key)
        viable_count = len(exploration.viable)

        # Impl C, Slice C4: honest one-line note when a catalog-eligible goal's
        # motor search (build_motor_catalog_suggestions) found zero matches —
        # the listed candidates are params/other-component variations only,
        # not real SKUs. Sourced from exploration.catalog_motor_note itself
        # (already the exact _CATALOG_MOTOR_FALLBACK_NOTE string set in
        # design_explorer.py) — no separate import, no drift risk.
        if viable_count == 0:
            note_prefix = f"{exploration.catalog_motor_note}\n\n" if exploration.catalog_motor_note else ""
            message = (
                f"{note_prefix}He explorado {len(exploration.candidates)} variaciones para «{goal_label}» "
                f"pero ninguna produce un diseño viable (can_fly=True) con los parámetros actuales. "
                f"Considera aumentar el empuje por motor o revisar la masa estructural antes de explorar."
            )
        else:
            lines = [
                f"Exploración completada para «{goal_label}» — {viable_count} configuración(es) viable(s) encontrada(s):\n"
            ]
            if exploration.catalog_motor_note:
                lines.append(exploration.catalog_motor_note)
                lines.append("")
            baseline_sim = exploration.baseline_simulation
            lines.append(
                f"  Línea base → autonomía={baseline_sim.autonomy_min or '—'} min, "
                f"margen={round(baseline_sim.safety_margin_ratio, 3)}, "
                f"vuelo={'✓' if baseline_sim.can_fly else '✗'}"
            )
            lines.append("")
            for i, c in enumerate(exploration.viable, start=1):
                sign = "+" if c.improvement >= 0 else ""
                lines.append(
                    f"  {i}. {c.label} → score={round(c.score, 3)} ({sign}{round(c.improvement, 3)})"
                )
            # MOP-4 (optional, Motor OP Voltage Coherence IC): honest note
            # when the live motor OP resolution has never been voltage-
            # validated (e.g. motor/propeller bound before any battery) —
            # read-only, parses the same propulsion_resolution JSON
            # set_motor_component already writes; no new subsystem.
            propulsion_resolution_raw = (project_state.current_parameters or {}).get("propulsion_resolution")
            if propulsion_resolution_raw:
                try:
                    _pr = json.loads(propulsion_resolution_raw)
                except (TypeError, ValueError, json.JSONDecodeError):
                    _pr = None
                if _pr is not None and not _pr.get("voltage_validated", False):
                    lines.append(
                        "  Línea base usa estimación — voltaje de batería pendiente de validación."
                    )
            lines.append("")
            lines.append("  Di «aplica la mejor» para aplicar la configuración #1 al proyecto.")
            # G24C §2.4 (honest CTA): selection (design_explorer._finalize_
            # viable_list) already guarantees a catalog-native candidate
            # survives when one was generated — this only tells the user
            # WHERE it landed, or honestly says none did. Never mutates
            # exploration.viable itself; pure message copy.
            catalog_indices = [
                i for i, c in enumerate(exploration.viable, start=1)
                if _is_catalog_native_motor_candidate(c)
            ]
            if catalog_indices and not _is_catalog_native_motor_candidate(exploration.viable[0]):
                idx = catalog_indices[0]
                lines.append(
                    f"  ⚠ La configuración #1 es abstracta (sin SKU de catálogo) — aplicarla "
                    f"puede perder el motor vinculado. La opción #{idx} sí usa un motor de "
                    f"catálogo: di «aplica la {idx}» para conservarlo."
                )
            elif not catalog_indices and exploration.candidates and any(
                _is_catalog_native_motor_candidate(c) for c in exploration.candidates
            ):
                lines.append(
                    f"  Ningún candidato de catálogo entró en las {viable_count} opciones "
                    "principales para este objetivo (perdió por puntuación frente a las "
                    "variaciones abstractas)."
                )
            message = "\n".join(lines)

        # DSE v1.1: persist exploration result in session so _handle_apply_exploration can use it.
        current_session = self.state_manager.runtime_state.session
        session_updates: dict[str, Any] = {"last_exploration_result": exploration}
        if bound_from_context and current_session.handoff_context is not None:
            # FN-024 (H1): consume the DSE capability ONLY — goal_key, levers,
            # and iterate_capability all remain untouched for a future H4
            # lever-preseed consumer. Never wipe the whole context on a
            # successful explore (explicit contract requirement — the whole
            # point of a capability-scoped context over a sticky goal string).
            session_updates["handoff_context"] = current_session.handoff_context.model_copy(
                update={"dse_capability": "consumed"}
            )
        elif replace_handoff_goal is not None:
            # G3 (★4): the explore that just ran used an explicitly overridden
            # goal, different from the prior active handoff — replace it with
            # a fresh context for the new goal (same construction shape as
            # _handle_engineering_intent/C-105), so a later bare "explora
            # opciones" follows the goal the user just actually explored, not
            # a stale one. dse_capability starts "consumed" (not "active"):
            # this explore already ran DSE for that goal, so a further bare
            # "explora opciones" should get the same honest "already
            # explored" message H1 gives, not a silent free re-run.
            levers = [s["lever"] for s in GOAL_STRATEGIES.get(replace_handoff_goal, [])]
            session_updates["handoff_context"] = HandoffContext(
                goal_key=replace_handoff_goal,
                levers=levers,
                dse_capability="consumed",
                project_id=project_state.project_id,
            )
        updated_session = current_session.model_copy(update=session_updates)
        self.state_manager.set_runtime_session(updated_session)

        return {
            "status": "ok",
            "action": "explore_design_space",
            "goal_key": goal_key,
            "goal_label": goal_label,
            "message": message,
            "exploration": exploration.model_dump(),
            "project_id": project_state.project_id,
            "workspace_path": project_state.workspace_path,
        }

    def _handle_apply_exploration(self, *, index: int = 1) -> dict:
        """DSE v1.1 / G24-1: aplica un candidato de la última exploración al proyecto.

        Usa viable[index - 1] (1-based, default 1 == mayor score) de
        last_exploration_result en session. Escribe directamente en state
        (equivalente al physical iterate path): current_parameters ←
        merged, corre calculate + simulate, guarda.

        G24-1 (locked, does not change ranking/scoring): ``index`` only
        selects WHICH row of the already-computed, already-ordered
        ``viable[]`` gets applied — "aplica la mejor" / bare "aplica" keep
        calling this with the default ``index=1``, byte-identical to the
        pre-G24-1 ``viable[0]`` behavior.

        Edge cases:
          - Sin exploración previa → mensaje informativo
          - viable vacío → mensaje informativo
          - index fuera de rango (1..len(viable)) → mensaje informativo, sin mutar estado
          - best.score <= baseline_score → avisa pero aplica de todas formas
          - _apply_delta falla (param ausente) → fallback manual
        """
        session = self.state_manager.runtime_state.session
        exploration = session.last_exploration_result

        if exploration is None:
            return {
                "status": "error",
                "action": "apply_exploration_result",
                "message": "No hay resultados de exploración recientes. Primero di «optimiza para [objetivo]».",
            }

        if not exploration.viable:
            return {
                "status": "error",
                "action": "apply_exploration_result",
                "message": (
                    f"La última exploración para «{exploration.goal_label}» no encontró "
                    "ninguna configuración viable. No hay nada que aplicar."
                ),
            }

        if index < 1 or index > len(exploration.viable):
            return {
                "status": "error",
                "action": "apply_exploration_result",
                "message": (
                    f"No hay una configuración #{index}. Elige un número entre 1 y "
                    f"{len(exploration.viable)}, o di «aplica la mejor»."
                ),
            }

        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return {
                "status": "error",
                "action": "apply_exploration_result",
                "message": "No hay proyecto activo. Crea un proyecto antes de aplicar una configuración.",
            }

        best = exploration.viable[index - 1]

        # Resolve delta → canonical param dict + updated state
        base_params = dict(project_state.current_parameters or {})

        if best.components_delta:
            # DA2: component-driven candidate — apply writers to derive params
            from jarvis.core.component_writers import apply_components_delta
            updated_project = apply_components_delta(project_state, best.components_delta)
            canonical_params = dict(updated_project.current_parameters or {})
        else:
            # Params-only candidate (original path)
            updated_project = None
            canonical_params = _apply_delta(base_params, best.params_delta)

        if canonical_params is None:
            return {
                "status": "error",
                "action": "apply_exploration_result",
                "message": (
                    "No se pudo resolver automáticamente los parámetros del candidato. "
                    f"Inténtalo manualmente: {best.label}"
                ),
            }

        # Catalog v1 (Impl B): a params-only candidate scales physics directly
        # in current_parameters without ever touching the component spec — so
        # a SKU-bound motor/battery would otherwise keep a stale catalog_ref
        # next to a diverged number. A component-driven candidate already
        # replaces the whole spec via apply_components_delta (which never
        # carries a prior catalog_ref forward), so this is a safe no-op there.
        from jarvis.core.catalog_bind import invalidate_diverged_catalog_refs
        from jarvis.core.component_sync import sync_motors_component_from_params
        _base_components = (
            updated_project.design_properties.components
            if updated_project is not None
            else project_state.design_properties.components
        )
        # Order matters: invalidate BEFORE sync. invalidate_diverged_catalog_refs
        # needs the still-stale component to correctly detect true SKU
        # divergence; sync_motors_component_from_params then brings
        # motor_count/thrust_n up to date so the NEXT turn's
        # resolve_propulsion_parameters reads current data instead of
        # reverting to stale pre-DSE values (G5 fix — see
        # investigation_report_g5_dse_iterate_dual_truth.md).
        _invalidated_components, canonical_params = invalidate_diverged_catalog_refs(
            _base_components, canonical_params
        )
        _updated_components = sync_motors_component_from_params(
            _invalidated_components, canonical_params
        )
        if _updated_components is not _base_components:
            _source_state = updated_project if updated_project is not None else project_state
            updated_project = _source_state.model_copy(
                update={
                    "design_properties": _source_state.design_properties.model_copy(
                        update={"components": _updated_components}
                    )
                }
            )

        # ── Apply, calculate, simulate, save ─────────────────────────────────
        from pathlib import Path
        workspace_path = Path(project_state.workspace_path)
        iteration_index = project_state.active_iteration  # capturar ANTES de incrementar

        autonomy_threshold = project_state.parsed_constraints.get("autonomy_min")
        calculations = self.calculation_engine.build(canonical_params)
        simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)

        # DA2: when components_delta was used, start from updated_project (has
        # both the new components and derived params); otherwise start from base.
        base_state_for_save = updated_project if updated_project is not None else project_state

        iteration_path = self.workspace_manager.save_iteration_snapshot(
            workspace_path,
            iteration_index,
            {
                "iteration_id": iteration_index,
                "event": "dse_apply",
                "goal_key": exploration.goal_key,
                "goal_label": exploration.goal_label,
                "label": best.label,
                "params_delta": best.params_delta,
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
                "design_properties": base_state_for_save.design_properties.model_dump(),
                "current_parameters": canonical_params,
            },
        )

        history_entry = HistoryEntry(
            action=ActionName.ITERATE,
            summary=f"DSE apply: {best.label} (goal={exploration.goal_key})",
            artifacts={"iteration": str(iteration_path)},
        )
        updated_state = self.state_manager.record_action(
            state=base_state_for_save.model_copy(update={"current_parameters": canonical_params}),
            action=history_entry,
            latest_results={
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
                "mutation": {
                    "mode": "dse_apply",
                    "params_delta": best.params_delta,
                    "label": best.label,
                    "goal_key": exploration.goal_key,
                },
            },
            increment_iteration=True,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "dse_apply",
            {
                "iteration_id": iteration_index,
                "goal_key": exploration.goal_key,
                "label": best.label,
            },
        )
        self.workspace_manager.render_views(workspace_path, updated_state)

        # ── Build confirmation message ────────────────────────────────────────
        no_improvement = best.score <= exploration.baseline_score
        sim = simulation  # real result, not the predicted one

        changed = {k: v for k, v in canonical_params.items() if base_params.get(k) != v}
        change_lines = [f"  - {k}: {base_params.get(k)} → {v}" for k, v in changed.items()]
        change_desc = "\n".join(change_lines) if change_lines else "  (sin cambios detectados)"

        applied_header = (
            f"Aplicando mejor configuración de «{exploration.goal_label}»:"
            if index == 1
            else f"Aplicando configuración #{index} de «{exploration.goal_label}»:"
        )
        message_parts = [
            applied_header,
            "",
            change_desc,
            "",
            "Resultado:",
            f"  - autonomía: {round(sim.autonomy_min, 1) if sim.autonomy_min is not None else '—'} min",
            f"  - margen de seguridad: {round(sim.safety_margin_ratio, 3)}",
            f"  - vuelo: {'✓ viable' if sim.can_fly else '✗ no viable'}",
            f"  - calidad: {sim.quality}",
        ]
        if no_improvement:
            message_parts.append(
                "\n⚠️  Nota: este candidato no mejora la línea base del objetivo "
                f"«{exploration.goal_label}». Configuración aplicada por solicitud explícita."
            )

        # Bug 79: check constraint violations after applying the candidate.
        # Uses the same _check_constraint_violations helper as U5 (informative, never blocks).
        _dse_violations = self._check_constraint_violations(updated_state)
        if _dse_violations:
            message_parts.append(f"\n⚠ {'; '.join(_dse_violations)}")

        return {
            "status": "ok",
            "action": "apply_exploration_result",
            "goal_key": exploration.goal_key,
            "goal_label": exploration.goal_label,
            "applied_index": index,
            "applied_candidate": best.model_dump(),
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "message": "\n".join(message_parts),
        }

    def _handle_analyze(self, user_input: str, llm_interface: Any) -> dict:
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            project_state = None

        context = self._build_analyze_context(project_state)
        analyze_type = self._resolve_analyze_type(user_input)
        goal_key = detect_goal(user_input)
        sim_context = context.get("last_simulation")
        goal_context = get_goal_context_for_llm(goal_key) if goal_key else None
        reasoning_output = self.reasoning_layer.build(context)
        message = llm_interface.analyze(
            user_input=user_input,
            context=context,
            analyze_type=analyze_type,
            reasoning_output=reasoning_output.model_dump(),
            conversation_history=self.state_manager.runtime_state.conversation_history,
            goal_context=goal_context,
        )
        if goal_key:
            deterministic_plan = format_goal_plan(goal_key, sim_context=sim_context)
            message = deterministic_plan + "\n\n─── Evaluación contextual ───\n" + message

        payload: dict[str, Any] = {
            "status": "ok",
            "action": "analyze",
            "message": message,
            "analyze_type": analyze_type,
            "analysis_context": context,
            "reasoning": reasoning_output.model_dump(),
        }
        if project_state is not None:
            payload["project_id"] = project_state.project_id
            payload["workspace_path"] = project_state.workspace_path
        return payload

    # FN-022: canonical explore-domain word per goal, used only to compose a
    # generic CTA ("optimiza para <domain>") — not a second copy of the
    # strategy catalog, and not thrust-specific (every goal gets one).
    _GOAL_EXPLORE_DOMAIN: dict[str, str] = {
        "aumentar_payload": "payload",
        "reducir_payload": "payload",
        "mejorar_autonomia": "autonomía",
        "reducir_masa": "masa",
        "mejorar_estabilidad": "estabilidad",
    }

    def _handle_engineering_intent(self, goal_key: str) -> dict:
        """FN-022: deterministic strategy plan for a bare engineering
        intention (no numeric mutation yet, no explicit explore request).

        Same sim_context wiring as the analyze path (_build_analyze_context's
        "last_simulation") so strategies are prioritized against the real
        project state — 0 LLM, no DSE run (explore only happens via the
        existing, separate explore_design_space intent).

        FN-024 (H1): also creates/replaces the operation-scoped Handoff
        Context for this project — the bridge a later bare "explora opciones"
        (C-042, see _handle_explore) binds through. A fresh context is always
        created here with dse_capability="active", which is exactly why the
        CTA below can honestly advertise 'explora opciones' unconditionally
        (H2) — no separate conditional text needed, the promise is true by
        construction at the moment it's shown.
        """
        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            project_state = None
        analyze_context = self._build_analyze_context(project_state)
        sim_context = analyze_context.get("last_simulation")
        plan = format_goal_plan(goal_key, sim_context=sim_context)
        domain = self._GOAL_EXPLORE_DOMAIN.get(goal_key, goal_key.replace("_", " "))
        cta = (
            f"Puedes explorar configuraciones (p. ej. 'optimiza para {domain}' "
            "o 'explora opciones') o indicar un cambio concreto de una palanca."
        )
        if project_state is not None:
            levers = [s["lever"] for s in GOAL_STRATEGIES.get(goal_key, [])]
            current_session = self.state_manager.runtime_state.session
            updated_session = current_session.model_copy(update={
                "handoff_context": HandoffContext(
                    goal_key=goal_key,
                    levers=levers,
                    project_id=project_state.project_id,
                )
            })
            self.state_manager.set_runtime_session(updated_session)
        return {
            "status": "ok",
            "action": "engineering_intent",
            "goal_key": goal_key,
            "message": f"{plan}\n\n{cta}",
        }

    # ── Startup context ───────────────────────────────────────────────────────

    def build_startup_context(self, workspace_path: "Path | str | None" = None) -> dict[str, Any]:
        """Return a structured dict describing the current project state for startup display.

        Loads the most recently touched project (or the project at *workspace_path*).
        Returns ``{"has_project": False}`` when no project exists.

        Structure:
        ```
        {
            "has_project": True,
            "project_slug": str,
            "objective": str,
            "status_type": "blocking" | "warning" | "nominal" | "no_data",
            "status_reason": str | None,       # e.g. "missing_transmission_parameters"
            "active_variables": dict[str, Any], # max 3, chosen by status
            "suggested_action": {              # top ReasoningSuggestion, may be None
                "label": str,
                "reason": str,
                "hint": str | None,            # e.g. 'Puedes responder: "0.15 y 10"'
            } | None,
        }
        ```
        """
        try:
            project_state = self.state_manager.load_active_project(
                self.workspace_manager,
                workspace_path=str(workspace_path) if workspace_path else None,
            )
        except FileNotFoundError:
            return {"has_project": False}

        context = self._build_analyze_context(project_state)
        reasoning = self.reasoning_layer.build(context)
        signals = reasoning.signals
        params = project_state.current_parameters or {}
        simulation = project_state.latest_results.get("simulation") or {}

        # ── status_type: strict priority hierarchy ────────────────────────────
        if signals.get("missing_physics_parameters"):
            status_type = "blocking"
            # Read the reason code from the simulation rather than hardcoding the domain.
            status_reason = missing_force_reason_from_warnings(simulation.get("warnings") or [])
        elif signals.get("has_warnings"):
            status_type = "warning"
            status_reason = (simulation.get("warnings") or [None])[0]
        elif signals.get("has_simulation"):
            status_type = "nominal"
            status_reason = None
        else:
            status_type = "no_data"
            status_reason = None

        # ── active_variables: max 3, relevant to current status ──────────────
        def _fmt(v: Any) -> Any:
            if isinstance(v, float) and v == int(v):
                return int(v)
            return v

        if status_type == "blocking":
            keys = ["motor_count", "per_actuator_torque_nm", "payload_kg"]
        elif status_type in ("warning", "nominal"):
            keys = ["payload_kg", "motor_count", "safety_margin_ratio"]
        else:
            keys = ["payload_kg", "motor_count", "safety_factor"]

        active_variables: dict[str, Any] = {}
        for key in keys:
            if key == "safety_margin_ratio":
                value = simulation.get("safety_margin_ratio")
            else:
                value = params.get(key)
            if value is not None:
                active_variables[key] = _fmt(value)

        # ── suggested_action: top action + actionable hint ────────────────────
        # Bug 49: filter out suggestions the user has dismissed this session.
        _dismissed = set(self.state_manager.runtime_state.session.dismissed_suggestions)
        suggested_action: dict[str, Any] | None = None
        if reasoning.suggested_actions:
            top = next(
                (a for a in reasoning.suggested_actions if not a.blocked and a.label not in _dismissed),
                None,
            )
            if top:
                hint: str | None = None
                if status_type == "blocking":
                    hint = reason_hint(status_reason)
                suggested_action = {
                    "label": top.label,
                    "reason": top.reason,
                    "hint": hint,
                }
                # Bug 49: record exactly what the user will see so dismiss_suggestion
                # always operates on the label that was rendered.
                _session = self.state_manager.runtime_state.session
                _updated = _session.model_copy(update={"last_suggested_action": top.label})
                self.state_manager.set_runtime_session(_updated)
            else:
                # All non-blocked suggestions have been dismissed this session.
                # Clear stale last_suggested_action so the next dismiss is a clean no-op
                # instead of operating on a label the user is no longer seeing.
                _session = self.state_manager.runtime_state.session
                if _session.last_suggested_action is not None:
                    self.state_manager.set_runtime_session(
                        _session.model_copy(update={"last_suggested_action": None})
                    )

        # ── project phase ─────────────────────────────────────────────────────
        phase_info = self.phase_layer.infer(signals=reasoning.signals, simulation=simulation)

        # ── proactive question ───────────────────────────────────────────────────
        proactive_question: str | None = None
        missing_params: list[str] = []
        param_definition_reason: str = ""
        if status_type == "blocking":
            # Always compute missing_params for any blocking state so the UI can render them.
            missing_params = missing_params_for_reason(status_reason, params)
            param_definition_reason = status_reason or ""
            if phase_info["phase"] == "definition" and missing_params:
                param_list = " y ".join(missing_params)
                proactive_question = f"¿Definimos {param_list} ahora?"
        elif signals.get("missing_energy_parameters"):
            # Energy params needed — force physics OK but autonomy incomplete.
            # Exception: when energy is composite and components are missing (Phase A),
            # defer to the architecture block section which will emit the component hint.
            _dp = project_state.design_properties
            _energy_missing_comps: list[str] = []
            if get_block_type("energy") == "composite" and _dp.system_defined:
                _energy_missing_comps = [
                    k for k in BLOCK_TO_COMPONENTS.get("energy", [])
                    if _dp.components.get(k) is None or _dp.components[k].completeness == "low"
                ]
            if not _energy_missing_comps:
                missing_params = missing_params_for_reason(MISSING_ENERGY_PARAMETERS, params)
                if missing_params:
                    param_list = " y ".join(missing_params)
                    proactive_question = f"¿Definimos {param_list} (energía) ahora?"
                    param_definition_reason = MISSING_ENERGY_PARAMETERS
        elif signals.get("missing_propeller_parameters"):
            # Propeller params needed — aerial vehicle, propeller path started but incomplete
            missing_params = missing_params_for_reason(MISSING_PROPELLER_PARAMETERS, params)
            if missing_params:
                param_list = " y ".join(missing_params)
                proactive_question = f"¿Definimos {param_list} (hélice) ahora?"
                param_definition_reason = MISSING_PROPELLER_PARAMETERS

        # ── architecture progress ──────────────────────────────────────────────
        # Computed after all param-based proactive_questions so architecture guidance
        # only fills in when no higher-priority prompt is already active.
        arch_next_block: str | None = None
        arch_next_label: str | None = None
        arch_block_status: str | None = None
        arch_progress: str | None = None
        if project_state.design_properties.system_defined:
            arch_progress = self._architecture_progress_str(project_state)
            pending = self._next_pending_block(project_state)
            if pending is not None:
                arch_next_block, arch_block_status = pending
                arch_next_label = self._block_label_for(project_state, arch_next_block)
                if not proactive_question:
                    if arch_block_status == "in_progress":
                        # K3 (Bug 61): differentiate the in_progress message for composite blocks.
                        # A composite block can be in_progress because components are missing
                        # (user must describe them) OR because params are missing (user must give
                        # numbers). The message must reflect which case we are in.
                        # get_block_in_progress_reason is the single source of truth — it owns
                        # the component-completeness check so this branch stays logic-free.
                        if get_block_type(arch_next_block) == "composite":
                            _ip_reason = self.get_block_in_progress_reason(
                                project_state, arch_next_block
                            )
                            if _ip_reason == "missing_components":
                                proactive_question = (
                                    f"{arch_next_label} en progreso — declara los componentes necesarios."
                                )
                            else:
                                proactive_question = (
                                    f"{arch_next_label} en progreso — define los parámetros que faltan."
                                )
                        else:
                            proactive_question = (
                                f"{arch_next_label} en progreso — define los parámetros que faltan."
                            )
                    else:
                        # Route by block type: component/composite get a hint, param gets generic.
                        arch_block_type = get_block_type(arch_next_block)
                        if arch_block_type == "component":
                            component_keys = BLOCK_TO_COMPONENTS.get(arch_next_block, [])
                            missing_params = component_keys
                            param_definition_reason = MISSING_COMPONENT_DEFINITION
                            hint = _BLOCK_COMPONENT_HINTS.get(
                                arch_next_block,
                                "describe los componentes",
                            )
                            proactive_question = f"Siguiente bloque: {arch_next_label} — {hint}"
                        elif arch_block_type == "composite":
                            component_keys = BLOCK_TO_COMPONENTS.get(arch_next_block, [])
                            _components = project_state.design_properties.components
                            missing_component_keys = [
                                k for k in component_keys
                                if _components.get(k) is None or _components[k].completeness == "low"
                            ]
                            if missing_component_keys:
                                missing_params = missing_component_keys
                                param_definition_reason = MISSING_COMPONENT_DEFINITION
                                hint = _BLOCK_COMPONENT_HINTS.get(
                                    arch_next_block,
                                    "describe los componentes",
                                )
                                proactive_question = f"Siguiente bloque: {arch_next_label} — {hint}"
                            else:
                                _param_reason = get_param_reason_for_block(arch_next_block)
                                if _param_reason:
                                    missing_params = missing_params_for_reason(
                                        _param_reason, project_state.current_parameters or {}
                                    )
                                    param_definition_reason = _param_reason
                                proactive_question = f"Siguiente bloque: {arch_next_label}"
                        else:
                            proactive_question = f"Siguiente bloque: {arch_next_label}"
            else:
                if not proactive_question:
                    proactive_question = (
                        f"Arquitectura completa ({arch_progress}) — "
                        f"puedes optimizar o simular."
                    )

        # ── Project closure surface (requirements / BOM / energy honesty / D8) ─
        from jarvis.core.project_closure import (
            build_component_bom,
            derive_physical_requirements,
            energy_model_honesty_note,
            format_bom_lines,
            format_requirements_lines,
        )

        physical_requirements = derive_physical_requirements(project_state)
        bom = build_component_bom(project_state)
        energy_note = energy_model_honesty_note(project_state)

        # G9-A: readiness-first — catalog surface comes from build_engineering_readiness
        # (single resolve_motor_catalog_surface call), not a second invocation here.
        from jarvis.core.engineering_readiness import build_engineering_readiness
        from jarvis.core.project_continuity import build_project_continuity

        readiness = build_engineering_readiness(project_state)
        catalog_gap = readiness.motor_catalog_gap
        catalog_matches = readiness.motor_catalog_matches

        continuity = build_project_continuity(
            project_state=project_state,
            status_type=status_type,
            status_reason=status_reason,
            phase=phase_info["phase"],
            architecture_progress=arch_progress,
            next_architecture_label=arch_next_label,
            next_block_status=arch_block_status,
            proactive_question=proactive_question,
            suggested_action=suggested_action,
            physical_requirements=physical_requirements,
            component_bom=bom,
            energy_model_note=energy_note,
            motor_catalog_gap=catalog_gap,
            motor_catalog_matches=catalog_matches,
            readiness=readiness,
        )

        return {
            "has_project": True,
            "project_slug": project_state.project_slug,
            "objective": project_state.objective,
            "phase": phase_info["phase"],
            "phase_description": phase_info["description"],
            "phase_confidence": phase_info["confidence"],
            "status_type": status_type,
            "status_reason": status_reason,
            "active_variables": active_variables,
            "suggested_action": suggested_action,
            "proactive_question": proactive_question,
            "missing_params": missing_params,
            "param_definition_reason": param_definition_reason,
            # Architecture progress fields (None when system not yet defined)
            "architecture_progress": arch_progress,
            "next_architecture_block": arch_next_block,
            "next_architecture_label": arch_next_label,
            "next_block_status": arch_block_status,
            # v1 closure surface
            "physical_requirements": physical_requirements,
            "physical_requirements_lines": format_requirements_lines(physical_requirements),
            "component_bom": bom,
            "component_bom_lines": format_bom_lines(bom),
            # Phase 2 P2-1 (Lookup Operating Point) — provenance of the current
            # per_motor_max_thrust_n, when the motor is catalog-bound. None
            # for freeform/unbound motors (no resolution to show). Stored as
            # a JSON string in current_parameters (component_writers.py —
            # must stay hashable for design_explorer's candidate cache);
            # parsed back to a dict here for the CLI/estado surface only.
            "propulsion_resolution": _parse_propulsion_resolution(
                (project_state.current_parameters or {}).get("propulsion_resolution")
            ),
            # P2-2 (Operating Point Bridge) — distinct from propulsion_resolution
            # (thrust/provenance metadata): the OP's real electrical measurement
            # (power/current/rpm) at this exact combo, when resolved. None when
            # no operating point was resolved — additive evidence, not a
            # replacement for the catalog rating shown elsewhere.
            "motor_operating_point_electrical": _motor_op_electrical_from_params(
                project_state.current_parameters or {}
            ),
            # Phase 2.5 (Hover Flight Energy Model) — honest hover-regime
            # motor input power/current, distinct from the bench-max OP
            # line above. None until a calculation has run, or when the
            # bound motor has no Discrete OP Dataset for its identity at
            # all (calc_engine's honest-absence case, ★2.5 preserved
            # semantics — not shown as a false "unverifiable").
            "hover_energy": _hover_energy_from_calculations(
                project_state.latest_results.get("calculations")
            ),
            # Phase 2.7-B — opt-in only, None unless the caller supplied a
            # battery_endurance_sweep for this calculation (★1: ESTIMATIVE
            # sweep only, never a default single-number result).
            "battery_endurance": _battery_endurance_from_calculations(
                project_state.latest_results.get("calculations")
            ),
            "energy_model_note": energy_note,
            "motor_catalog_matches": catalog_matches,
            "motor_catalog_gap": catalog_gap,
            # A' Project Continuity — Situation / Evidence / Next useful step
            "continuity": continuity,
            # ERF-1 — Engineering Readiness (Gap Registry + 8-subsystem rollup)
            "readiness": dataclasses.asdict(readiness),
        }

    def _build_analyze_context(self, project_state) -> dict[str, Any]:
        if project_state is None:
            return {
                "objective": None,
                "current_parameters": None,
                "design_properties": None,
                "last_calculation": None,
                "material": None,
                "last_simulation": None,
                "memory": None,
                "last_mutation": None,
                "mutation_mode": None,
            }

        return {
            "objective": project_state.objective,
            "current_parameters": project_state.current_parameters,
            "design_properties": project_state.design_properties.model_dump(),
            "last_calculation": project_state.latest_results.get("calculations"),
            "material": _get_frame_material_display(project_state.design_properties),
            "last_simulation": project_state.latest_results.get("simulation"),
            "memory": project_state.memory.model_dump(),
            "last_mutation": project_state.latest_results.get("mutation"),
            "mutation_mode": (project_state.latest_results.get("mutation") or {}).get("mode"),
        }

    def _resolve_analyze_type(self, user_input: str) -> str:
        normalized = user_input.lower()
        if any(pattern in normalized for pattern in ("que pasa si", "qué pasa si", "si aumento", "si reduzco")):
            return "what_if"
        if any(pattern in normalized for pattern in ("mejor", "compar", "vs", "versus")):
            return "comparison"
        return "explanation"

    def _handle_interactive_request(self, request: ActionRequest) -> dict:
        current_session = self.state_manager.get_runtime_session()
        user_input = request.raw_user_input or str(request.parameters.get("answer", "")).strip()
        if not user_input:
            return self._interactive_handler_for(current_session.mode).answer(current_session, "")

        try:
            response = self._interactive_handler_for(current_session.mode).answer(current_session, user_input)
        except ValueError as error:
            current_response = self._error_response_for_session(current_session, str(error))
            if "question" not in current_response:
                retry_response = self._interactive_handler_for(current_session.mode).answer(current_session, "")
                current_response["question"] = retry_response["question"]
            return current_response

        response = self._apply_memory_update_if_present(current_session, response)

        if response["status"] == "confirmed":
            if current_session.mode == OrchestratorMode.CREATE_PROJECT_INTERACTIVE:
                execution_payload = self.interactive_session.build_execution_payload(
                    current_session.project_draft
                )
                self.state_manager.clear_runtime_session()
                handler = self.router.resolve(ActionName.CREATE_PROJECT)
                result = handler.run(execution_payload)
                # Launch system definition session after successful create_project.
                # Always offered — message adapts based on detail_level inside start().
                if result.get("status") == "ok":
                    try:
                        project_state = self.state_manager.load_active_project(self.workspace_manager)
                        vehicle_type = execution_payload.get("vehicle_type", "")
                        return self.system_definition_session.start(vehicle_type, project_state)
                    except FileNotFoundError:
                        pass
                return result

            execution_payload = {
                "iteration_draft": response["iteration_draft"],
            }
            self.state_manager.clear_runtime_session()
            handler = self.router.resolve(ActionName.ITERATE)
            return handler.run(execution_payload)

        if response["status"] == "cancelled":
            self.state_manager.clear_runtime_session()
            return response

        self.state_manager.set_runtime_session(
            self._session_from_response(response)
        )
        return response

    def _preseed_variable_from_handoff(self, action_request: dict, user_input: str) -> dict:
        """FN-026 (H4): if the active HandoffContext names a lever the user
        just referenced, preseed 'variable' so the wizard skips step 1
        ("¿Qué quieres modificar?"). Read-only consumer of the context C-105
        already creates — never touches dse_capability, never wipes the
        context. Honest no-op (returns action_request unchanged) when there
        is no active project, no active context, a stale (wrong-project)
        context, or no lever match — the wizard falls back to asking, exactly
        as before this fix.
        """
        params = action_request.get("parameters") or {}
        if params.get("variable"):
            return action_request

        handoff = self.state_manager.get_runtime_session().handoff_context
        if handoff is None or handoff.iterate_capability != "active":
            return action_request

        try:
            project_state = self.state_manager.load_active_project(self.workspace_manager)
        except FileNotFoundError:
            return action_request

        if handoff.project_id != project_state.project_id:
            return action_request

        matched_variable = match_plan_lever(user_input, handoff)
        if matched_variable is None:
            return action_request

        return {
            **action_request,
            "parameters": {**params, "variable": matched_variable},
        }

    def _semantic_preseed(self, llm_action_dict: dict) -> dict:
        """Return extra seed keys when the LLM provides a high-confidence iterate proposal.

        * :class:`SemanticInterpretation` with high confidence → adds ``operacion``,
          ``variable``, optionally ``valor`` and ``seed_step=2`` so the wizard opens
          directly at step 2 (value question), skipping steps 0 and 1.
        * :class:`AdaptRejection` with ``reason="derived_variable"`` → adds
          ``derived_redirect_message`` so the wizard shows it at step 0 before prompting.
        * Any other case (``None``, low confidence, unknown variable) → empty dict,
          wizard starts normally from step 0.
        """
        result = self._semantic_adapter.adapt(llm_action_dict)

        if isinstance(result, AdaptRejection):
            if result.reason == "derived_variable":
                return {"derived_redirect_message": result.redirect_message}
            return {}

        if not isinstance(result, SemanticInterpretation) or not result.is_high_confidence:
            return {}

        preseed: dict = {
            "operacion": result.operation,
            "variable": result.variable,
            "seed_step": 2,
        }
        if result.value is not None:
            preseed["valor"] = result.value
        return preseed

    def _session_from_response(self, response: dict) -> InteractiveSessionState:
        return InteractiveSessionState(
            mode=OrchestratorMode(response["mode"]),
            step=response["step"],
            project_draft=(
                ProjectDraft.model_validate(response["project_draft"])
                if "project_draft" in response
                else None
            ),
            iteration_draft=(
                IterationDraft.model_validate(response["iteration_draft"])
                if "iteration_draft" in response
                else None
            ),
            memory_context=response.get("memory_context"),
            pending_entities=response.get("pending_entities", []),
            motor_suggestions=response.get("motor_suggestions", []),
            semantic_state=(
                SemanticState.model_validate(response["semantic_state"])
                if "semantic_state" in response
                else None
            ),
        )

    def _interactive_handler_for(self, mode: OrchestratorMode):
        if mode == OrchestratorMode.CREATE_PROJECT_INTERACTIVE:
            return self.interactive_session
        if mode == OrchestratorMode.ITERATE_INTERACTIVE:
            return self.iterate_interactive_session
        raise ValueError(f"Modo interactivo no soportado: {mode}")

    def _error_response_for_session(self, session: InteractiveSessionState, error: str) -> dict:
        response = {
            "status": "interactive",
            "mode": session.mode.value,
            "step": session.step,
            "error": error,
        }
        if session.project_draft is not None:
            response["project_draft"] = session.project_draft.model_dump()
        if session.iteration_draft is not None:
            response["iteration_draft"] = session.iteration_draft.model_dump()
        if session.memory_context is not None:
            response["memory_context"] = session.memory_context
        return response

    def _should_start_create_project_interactive(self, request: ActionRequest) -> bool:
        return not self.interactive_session.is_executable(request.parameters)

    def _has_active_project(self) -> bool:
        """Return True if there is at least one project in the workspace."""
        try:
            self.state_manager.load_active_project(self.workspace_manager)
            return True
        except FileNotFoundError:
            return False

    def _apply_memory_update_if_present(self, session: InteractiveSessionState, response: dict) -> dict:
        memory_update = response.get("memory_update")
        if not memory_update or session.iteration_draft is None or not session.iteration_draft.project_id:
            return response

        project_state = self.state_manager.load_active_project(
            self.workspace_manager,
            project_id=session.iteration_draft.project_id,
            workspace_path=session.iteration_draft.workspace_path,
            project_slug=session.iteration_draft.project_slug,
        )
        updated_state = self.memory_manager.apply_conflict_resolution(
            project_state,
            initial_objective=memory_update.get("initial_objective"),
            initial_operation=memory_update.get("initial_operation"),
            conflicting_operation=memory_update.get("conflicting_operation"),
            resolution=memory_update.get("resolution"),
        )
        self.workspace_manager.save_state(updated_state)
        updated_response = dict(response)
        updated_response["memory_context"] = updated_state.memory.model_dump()
        return updated_response
