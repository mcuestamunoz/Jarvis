from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

from jarvis.config import ESCAPE_WORDS
from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_resolver import resolve_propulsion_parameters
from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
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
from jarvis.core.system_architecture_catalog import COMPONENT_MIRRORED_PARAMS
from jarvis.workspace.workspace_manager import WorkspaceManager

logger = logging.getLogger(__name__)

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
        session = InteractiveSessionState(
            mode=OrchestratorMode.DEFINE_MISSING_PARAMETERS,
            step=0,
            pending_param_definitions=list(missing_params),
            collected_params={},
            param_definition_reason=reason,
        )
        self.state_manager.set_runtime_session(session)
        return {
            "status": "interactive",
            "action": "define_missing_params",
            "question": self.param_question(missing_params[0]),
            "pending": list(missing_params),
        }

    def answer(self, user_input: str) -> dict:
        session = self.state_manager.get_runtime_session()

        if user_input.strip().lower() in ESCAPE_WORDS:
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

        values = self.parse_floats_from_input(user_input)
        if not values:
            _normalized = unicodedata.normalize("NFC", user_input.strip().lower())
            if _normalized in {"si", "sí", "yes", "ok", "dale", "adelante", "claro"}:
                return {
                    "status": "interactive",
                    "action": "define_missing_params",
                    "question": self.param_question(pending[0]),
                }
            # Bug 77: skip phrases — user wants to defer the current parameter.
            # Remove it from pending and continue; apply_and_recalculate is called
            # once all params are either answered or skipped.
            if _normalized in _SKIP_PHRASES:
                remaining = pending[1:]
                if remaining:
                    updated_session = session.model_copy(
                        update={"pending_param_definitions": remaining}
                    )
                    self.state_manager.set_runtime_session(updated_session)
                    return {
                        "status": "interactive",
                        "action": "define_missing_params",
                        "message": f"Parámetro '{pending[0]}' omitido — puedes definirlo después.",
                        "question": self.param_question(remaining[0]),
                    }
                # All params processed (some skipped) — apply whatever was collected.
                self.state_manager.clear_runtime_session()
                return self.apply_and_recalculate(session.collected_params)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "error": f"No reconozco '{user_input}' como número. Escribe un valor numérico.",
                "question": self.param_question(pending[0]),
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
            for param, value in zip(pending, values):
                collected[param] = value
            consumed = min(len(values), len(pending))
            remaining = pending[consumed:]

        if remaining:
            updated_session = session.model_copy(
                update={
                    "pending_param_definitions": remaining,
                    "collected_params": collected,
                }
            )
            self.state_manager.set_runtime_session(updated_session)
            return {
                "status": "interactive",
                "action": "define_missing_params",
                "question": self.param_question(remaining[0]),
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

    def apply_and_recalculate(self, param_updates: dict[str, float]) -> dict:
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

        return {
            "status": "ok",
            "action": "define_missing_params",
            "message": f"Parámetros aplicados: {param_str}. Sistema recalculado.",
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "project_id": project_state.project_id,
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
