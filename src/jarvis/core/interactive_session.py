from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from pydantic import ValidationError

from jarvis.config import (
    DEFAULT_SIMULATION_MARGIN,
    DEFAULT_STRUCTURE_MASS_FACTOR,
)
from jarvis.schemas.action_schema import CreateProjectParams, InteractiveSessionState, OrchestratorMode, ProjectDraft
from jarvis.core.system_architecture_catalog import VEHICLE_TYPE_ALIASES

# Step ids — trunk 0–4, detallado factors 5–6, aerial 10–14, ground 20–23, confirm 90
STEP_VEHICLE = 0
STEP_OBJECTIVE = 1
STEP_PAYLOAD = 2
STEP_RESTRICTIONS = 3
STEP_DETAIL = 4
STEP_STRUCTURE_FACTOR = 5
STEP_SAFETY_FACTOR = 6
STEP_AERIAL_MOTORS = 10
STEP_AERIAL_PATH = 11
STEP_AERIAL_THRUST = 12
STEP_AERIAL_PROP_DIAMETER = 13
STEP_AERIAL_PROP_RPM = 14
STEP_GROUND_ACTUATORS = 20
STEP_GROUND_PATH = 21
STEP_GROUND_TORQUE = 22
STEP_GROUND_FORCE = 23
STEP_CONFIRM = 90

_AERIAL_CANONICAL = frozenset({"dron", "uav"})
_GROUND_CANONICAL = frozenset({"robot", "coche", "rover"})

_UNKNOWN_PATH_PHRASES = frozenset({
    "no se", "no sé", "nose", "ns", "skip", "despues", "después",
    "mas tarde", "más tarde", "aun no", "aún no", "no lo se", "no lo sé",
    "no se aun", "no sé aún", "unknown", "ninguno", "ninguna",
})


@dataclass(frozen=True)
class InteractivePrompt:
    step: int
    field_name: str
    question: str


class CreateProjectInteractiveSession:
    PROMPTS: dict[int, InteractivePrompt] = {
        STEP_VEHICLE: InteractivePrompt(
            STEP_VEHICLE, "vehicle_type", "¿Qué sistema quieres diseñar? (dron, robot, etc.)"
        ),
        STEP_OBJECTIVE: InteractivePrompt(
            STEP_OBJECTIVE, "objective", "¿Cuál es el objetivo principal? (ej: levantar 2kg)"
        ),
        STEP_PAYLOAD: InteractivePrompt(
            STEP_PAYLOAD, "payload_kg", "¿Cuál es la carga útil en kg?"
        ),
        STEP_RESTRICTIONS: InteractivePrompt(
            STEP_RESTRICTIONS, "restrictions", "¿Tienes restricciones? (tamaño, autonomía, presupuesto, etc.)"
        ),
        STEP_DETAIL: InteractivePrompt(
            STEP_DETAIL, "detail_level", "Nivel de diseño: conceptual o detallado"
        ),
        STEP_STRUCTURE_FACTOR: InteractivePrompt(
            STEP_STRUCTURE_FACTOR,
            "structure_mass_factor",
            "Factor de masa estructural (ej: 0.6). Enter para default 0.6.",
        ),
        STEP_SAFETY_FACTOR: InteractivePrompt(
            STEP_SAFETY_FACTOR,
            "safety_factor",
            "Factor de seguridad / margen de empuje (ej: 1.2). Enter para default 1.2.",
        ),
        STEP_AERIAL_MOTORS: InteractivePrompt(
            STEP_AERIAL_MOTORS, "motors", "¿Cuántos motores tiene el sistema?"
        ),
        STEP_AERIAL_PATH: InteractivePrompt(
            STEP_AERIAL_PATH,
            "aerial_path",
            "¿Cómo defines la fuerza de propulsión? (empuje declarado / hélices / no sé aún)",
        ),
        STEP_AERIAL_THRUST: InteractivePrompt(
            STEP_AERIAL_THRUST, "per_motor_max_thrust_n", "Empuje máximo por motor en N (ej: 15)"
        ),
        STEP_AERIAL_PROP_DIAMETER: InteractivePrompt(
            STEP_AERIAL_PROP_DIAMETER, "propeller_diameter_in", "Diámetro de hélice en pulgadas (ej: 10)"
        ),
        STEP_AERIAL_PROP_RPM: InteractivePrompt(
            STEP_AERIAL_PROP_RPM, "propeller_rpm", "RPM de hélice (ej: 7500)"
        ),
        STEP_GROUND_ACTUATORS: InteractivePrompt(
            STEP_GROUND_ACTUATORS, "motors", "¿Cuántos actuadores / motores de tracción tiene?"
        ),
        STEP_GROUND_PATH: InteractivePrompt(
            STEP_GROUND_PATH,
            "ground_path",
            "¿Cómo defines la fuerza de tracción? (torque / fuerza directa / no sé aún)",
        ),
        STEP_GROUND_TORQUE: InteractivePrompt(
            STEP_GROUND_TORQUE, "per_actuator_torque_nm", "Torque por actuador en N·m (ej: 5)"
        ),
        STEP_GROUND_FORCE: InteractivePrompt(
            STEP_GROUND_FORCE, "max_force_per_actuator_n", "Fuerza máxima por actuador en N (ej: 40)"
        ),
        STEP_CONFIRM: InteractivePrompt(STEP_CONFIRM, "confirmation", ""),
    }

    def start(self, seed_parameters: dict | None = None) -> dict:
        project_draft = self._build_initial_draft(seed_parameters or {})
        session = InteractiveSessionState(
            mode=OrchestratorMode.CREATE_PROJECT_INTERACTIVE,
            step=self._resolve_next_step(project_draft),
            project_draft=project_draft,
        )
        return self._build_question_response(session)

    def answer(self, session: InteractiveSessionState, user_input: str) -> dict:
        if session.mode != OrchestratorMode.CREATE_PROJECT_INTERACTIVE or session.project_draft is None:
            raise ValueError("No hay una sesión interactiva activa.")

        normalized = user_input.strip()
        if not normalized and session.step not in {STEP_STRUCTURE_FACTOR, STEP_SAFETY_FACTOR}:
            return self._build_question_response(session, error="Necesito una respuesta para continuar.")

        if session.step == STEP_CONFIRM:
            return self._handle_confirmation(session, normalized)

        updated_draft, next_step = self._apply_answer(session.project_draft, session.step, normalized)
        updated_session = session.model_copy(
            update={
                "step": next_step,
                "project_draft": updated_draft,
            }
        )
        return self._build_question_response(updated_session)

    def build_execution_payload(self, draft: ProjectDraft) -> dict:
        params = CreateProjectParams(
            objective=draft.objective,
            payload_kg=draft.payload_kg,
            vehicle_type=draft.vehicle_type,
            restrictions=draft.restrictions,
            detail_level=draft.detail_level,
            motors=draft.motors,
            per_motor_max_thrust_n=draft.per_motor_max_thrust_n,
            structure_mass_factor=draft.structure_mass_factor or DEFAULT_STRUCTURE_MASS_FACTOR,
            safety_factor=draft.safety_factor or DEFAULT_SIMULATION_MARGIN,
            propeller_diameter_in=draft.propeller_diameter_in,
            propeller_rpm=draft.propeller_rpm,
            per_actuator_torque_nm=draft.per_actuator_torque_nm,
            max_force_per_actuator_n=draft.max_force_per_actuator_n,
        )
        return params.model_dump()

    def is_executable(self, parameters: dict | None) -> bool:
        try:
            CreateProjectParams.model_validate(parameters or {})
        except ValidationError:
            return False
        return True

    def _build_initial_draft(self, seed_parameters: dict) -> ProjectDraft:
        normalized = dict(seed_parameters)
        if "type" in normalized and "vehicle_type" not in normalized:
            normalized["vehicle_type"] = normalized["type"]
        return ProjectDraft.model_validate(
            {
                "vehicle_type": normalized.get("vehicle_type"),
                "objective": normalized.get("objective"),
                "payload_kg": normalized.get("payload_kg"),
                "restrictions": normalized.get("restrictions"),
                "detail_level": normalized.get("detail_level"),
                "motors": normalized.get("motors"),
                "per_motor_max_thrust_n": normalized.get("per_motor_max_thrust_n"),
                "structure_mass_factor": normalized.get("structure_mass_factor"),
                "safety_factor": normalized.get("safety_factor"),
                "propeller_diameter_in": normalized.get("propeller_diameter_in"),
                "propeller_rpm": normalized.get("propeller_rpm"),
                "per_actuator_torque_nm": normalized.get("per_actuator_torque_nm"),
                "max_force_per_actuator_n": normalized.get("max_force_per_actuator_n"),
            }
        )

    def _resolve_next_step(self, draft: ProjectDraft) -> int:
        """Resume wizard at first incomplete trunk/branch step (seed-aware)."""
        if not draft.vehicle_type:
            return STEP_VEHICLE
        if not draft.objective:
            return STEP_OBJECTIVE
        if draft.payload_kg is None:
            return STEP_PAYLOAD
        if not draft.restrictions:
            return STEP_RESTRICTIONS
        if not draft.detail_level:
            return STEP_DETAIL
        if draft.detail_level == "detallado":
            if draft.structure_mass_factor is None:
                return STEP_STRUCTURE_FACTOR
            if draft.safety_factor is None:
                return STEP_SAFETY_FACTOR
        # conceptual (or factors already present): branch entry does not require factors
        # to be set here — build_execution_payload applies defaults if missing.

        domain = self._domain_kind(draft.vehicle_type)
        if domain == "aerial":
            if draft.motors is None:
                return STEP_AERIAL_MOTORS
            # Path already resolved if any force param set, or if motors set and we
            # cannot know "unknown" vs pending — if motors set but no force path fields
            # and user is resuming mid-wizard we land on path choice.
            if (
                draft.per_motor_max_thrust_n is None
                and draft.propeller_diameter_in is None
                and draft.propeller_rpm is None
            ):
                # Ambiguous: could be "no sé" already chosen. Seed with motors only → ask path.
                return STEP_AERIAL_PATH
            if draft.propeller_diameter_in is not None and draft.propeller_rpm is None:
                return STEP_AERIAL_PROP_RPM
            return STEP_CONFIRM
        if domain == "ground":
            if draft.motors is None:
                return STEP_GROUND_ACTUATORS
            if draft.per_actuator_torque_nm is None and draft.max_force_per_actuator_n is None:
                return STEP_GROUND_PATH
            return STEP_CONFIRM
        return STEP_CONFIRM

    @staticmethod
    def _normalize_vehicle_type(raw: str) -> str:
        """Bug 76: normalize vehicle_type by matching each word against VEHICLE_TYPE_ALIASES.

        'dron de inspección de infraestructuras' → 'dron'
        'rover exploración' → 'rover'
        Falls back to the lowercased raw string if no alias word is found.
        """
        lowered = raw.lower().strip()
        if lowered in VEHICLE_TYPE_ALIASES:
            return VEHICLE_TYPE_ALIASES[lowered]
        for word in lowered.split():
            if word in VEHICLE_TYPE_ALIASES:
                return VEHICLE_TYPE_ALIASES[word]
        return lowered

    @classmethod
    def _domain_kind(cls, vehicle_type: str | None) -> str:
        if not vehicle_type:
            return "unknown"
        key = VEHICLE_TYPE_ALIASES.get(vehicle_type.lower().strip(), vehicle_type.lower().strip())
        if key in _AERIAL_CANONICAL:
            return "aerial"
        if key in _GROUND_CANONICAL:
            return "ground"
        return "unknown"

    def _first_branch_step(self, draft: ProjectDraft) -> int:
        domain = self._domain_kind(draft.vehicle_type)
        if domain == "aerial":
            return STEP_AERIAL_MOTORS
        if domain == "ground":
            return STEP_GROUND_ACTUATORS
        return STEP_CONFIRM

    def _apply_answer(self, draft: ProjectDraft, step: int, user_input: str) -> tuple[ProjectDraft, int]:
        if step == STEP_VEHICLE:
            updated = draft.model_copy(update={"vehicle_type": self._normalize_vehicle_type(user_input)})
            return updated, STEP_OBJECTIVE

        if step == STEP_OBJECTIVE:
            return draft.model_copy(update={"objective": user_input}), STEP_PAYLOAD

        if step == STEP_PAYLOAD:
            try:
                payload_kg = self._parse_float(user_input)
            except ValueError as error:
                raise ValueError("La carga útil debe ser un número en kg.") from error
            return draft.model_copy(update={"payload_kg": payload_kg}), STEP_RESTRICTIONS

        if step == STEP_RESTRICTIONS:
            return draft.model_copy(update={"restrictions": user_input}), STEP_DETAIL

        if step == STEP_DETAIL:
            normalized = user_input.lower()
            if normalized not in {"conceptual", "detallado"}:
                raise ValueError("El nivel de diseño debe ser 'conceptual' o 'detallado'.")
            if normalized == "conceptual":
                updated = draft.model_copy(
                    update={
                        "detail_level": normalized,
                        "structure_mass_factor": DEFAULT_STRUCTURE_MASS_FACTOR,
                        "safety_factor": DEFAULT_SIMULATION_MARGIN,
                    }
                )
                return updated, self._first_branch_step(updated)
            updated = draft.model_copy(update={"detail_level": normalized})
            return updated, STEP_STRUCTURE_FACTOR

        if step == STEP_STRUCTURE_FACTOR:
            factor = self._parse_optional_float(user_input, DEFAULT_STRUCTURE_MASS_FACTOR)
            if factor < 0:
                raise ValueError("El factor de masa estructural debe ser ≥ 0.")
            return draft.model_copy(update={"structure_mass_factor": factor}), STEP_SAFETY_FACTOR

        if step == STEP_SAFETY_FACTOR:
            factor = self._parse_optional_float(user_input, DEFAULT_SIMULATION_MARGIN)
            if factor <= 1:
                raise ValueError("El factor de seguridad debe ser > 1.")
            updated = draft.model_copy(update={"safety_factor": factor})
            return updated, self._first_branch_step(updated)

        if step == STEP_AERIAL_MOTORS:
            count = self._parse_positive_int(user_input, "número de motores")
            return draft.model_copy(update={"motors": count}), STEP_AERIAL_PATH

        if step == STEP_AERIAL_PATH:
            path = self._parse_aerial_path(user_input)
            if path == "thrust":
                return draft, STEP_AERIAL_THRUST
            if path == "propellers":
                return draft, STEP_AERIAL_PROP_DIAMETER
            return draft, STEP_CONFIRM

        if step == STEP_AERIAL_THRUST:
            value = self._parse_float(user_input)
            if value <= 0:
                raise ValueError("El empuje por motor debe ser > 0.")
            return draft.model_copy(update={"per_motor_max_thrust_n": value}), STEP_CONFIRM

        if step == STEP_AERIAL_PROP_DIAMETER:
            value = self._parse_float(user_input)
            if value <= 0:
                raise ValueError("El diámetro de hélice debe ser > 0.")
            return draft.model_copy(update={"propeller_diameter_in": value}), STEP_AERIAL_PROP_RPM

        if step == STEP_AERIAL_PROP_RPM:
            value = self._parse_float(user_input)
            if value <= 0:
                raise ValueError("Las RPM de hélice deben ser > 0.")
            return draft.model_copy(update={"propeller_rpm": value}), STEP_CONFIRM

        if step == STEP_GROUND_ACTUATORS:
            count = self._parse_positive_int(user_input, "número de actuadores")
            return draft.model_copy(update={"motors": count}), STEP_GROUND_PATH

        if step == STEP_GROUND_PATH:
            path = self._parse_ground_path(user_input)
            if path == "torque":
                return draft, STEP_GROUND_TORQUE
            if path == "force":
                return draft, STEP_GROUND_FORCE
            return draft, STEP_CONFIRM

        if step == STEP_GROUND_TORQUE:
            value = self._parse_float(user_input)
            if value <= 0:
                raise ValueError("El torque por actuador debe ser > 0.")
            return draft.model_copy(update={"per_actuator_torque_nm": value}), STEP_CONFIRM

        if step == STEP_GROUND_FORCE:
            value = self._parse_float(user_input)
            if value <= 0:
                raise ValueError("La fuerza por actuador debe ser > 0.")
            return draft.model_copy(update={"max_force_per_actuator_n": value}), STEP_CONFIRM

        raise ValueError(f"Step no soportado: {step}")

    def _handle_confirmation(self, session: InteractiveSessionState, user_input: str) -> dict:
        normalized = user_input.lower()
        if normalized in {"si", "sí", "s", "confirmo", "ok"}:
            return {
                "status": "confirmed",
                "mode": session.mode.value,
                "step": session.step,
                "project_draft": session.project_draft.model_dump(),
            }
        if normalized in {"no", "n", "editar", "corregir"}:
            reset_session = session.model_copy(update={"step": STEP_VEHICLE})
            return self._build_question_response(
                reset_session,
                message="Reiniciamos la definición del proyecto para corregir los datos.",
            )
        return self._build_question_response(
            session,
            error="Responde 'sí' para ejecutar o 'no' para corregir antes de confirmar.",
        )

    def _parse_float(self, user_input: str) -> float:
        normalized = user_input.strip().lower().replace(",", ".")
        match = re.search(r"(\d+(?:\.\d+)?)", normalized)
        if not match:
            raise ValueError("No se encontró un valor numérico.")
        return float(match.group(1))

    def _parse_optional_float(self, user_input: str, default: float) -> float:
        if not user_input.strip():
            return default
        return self._parse_float(user_input)

    def _parse_payload_kg(self, user_input: str) -> float:
        return self._parse_float(user_input)

    def _parse_positive_int(self, user_input: str, label: str) -> int:
        value = self._parse_float(user_input)
        as_int = int(value)
        if as_int < 1 or value != as_int:
            raise ValueError(f"El {label} debe ser un entero ≥ 1.")
        return as_int

    @staticmethod
    def _strip_diacritics(text: str) -> str:
        nfd = unicodedata.normalize("NFD", text.strip().lower())
        return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

    def _parse_aerial_path(self, user_input: str) -> str:
        text = self._strip_diacritics(user_input)
        if text in _UNKNOWN_PATH_PHRASES or "no se" in text:
            return "unknown"
        if any(k in text for k in ("empuje", "thrust", "declarad")):
            return "thrust"
        if any(k in text for k in ("helice", "helices", "propeller", "prop")):
            return "propellers"
        raise ValueError("Elige: empuje declarado, hélices, o no sé aún.")

    def _parse_ground_path(self, user_input: str) -> str:
        text = self._strip_diacritics(user_input)
        if text in _UNKNOWN_PATH_PHRASES or "no se" in text:
            return "unknown"
        if "torque" in text:
            return "torque"
        if any(k in text for k in ("fuerza", "force", "direct")):
            return "force"
        raise ValueError("Elige: torque, fuerza directa, o no sé aún.")

    def _build_question_response(
        self,
        session: InteractiveSessionState,
        message: str | None = None,
        error: str | None = None,
    ) -> dict:
        prompt = self.PROMPTS.get(session.step)
        response = {
            "status": "interactive",
            "mode": session.mode.value,
            "step": session.step,
            "project_draft": session.project_draft.model_dump() if session.project_draft else {},
        }
        if error:
            response["error"] = error
        if message:
            response["message"] = message

        if session.step == STEP_CONFIRM and session.project_draft is not None:
            response["message"] = self._build_confirmation_message(session.project_draft)
            response["question"] = "¿Confirmas?"
        else:
            if "message" not in response:
                response["message"] = "Vamos a definir el proyecto paso a paso."
            response["question"] = prompt.question if prompt else "Continúa."
        return response

    def _build_confirmation_message(self, draft: ProjectDraft) -> str:
        domain = self._domain_kind(draft.vehicle_type)
        motors_str = str(draft.motors) if draft.motors is not None else "sin definir"
        lines = [
            "Resumen del proyecto:",
            f"- Tipo: {draft.vehicle_type}",
            f"- Objetivo: {draft.objective}",
            f"- Payload: {draft.payload_kg} kg",
            f"- Restricciones: {draft.restrictions}",
            f"- Nivel de detalle: {draft.detail_level}",
            "- Parámetros técnicos:",
            f"  factor_estructura={draft.structure_mass_factor}, "
            f"factor_seguridad={draft.safety_factor}",
        ]
        if domain == "aerial":
            thrust_str = (
                f"{draft.per_motor_max_thrust_n} N"
                if draft.per_motor_max_thrust_n is not None
                else "sin definir"
            )
            prop_str = (
                f"{draft.propeller_diameter_in}\" @ {draft.propeller_rpm} rpm"
                if draft.propeller_diameter_in is not None
                else "sin definir"
            )
            lines.append(f"  motores={motors_str}, empuje_max_por_motor={thrust_str}, helices={prop_str}")
        elif domain == "ground":
            torque_str = (
                f"{draft.per_actuator_torque_nm} N·m"
                if draft.per_actuator_torque_nm is not None
                else "sin definir"
            )
            force_str = (
                f"{draft.max_force_per_actuator_n} N"
                if draft.max_force_per_actuator_n is not None
                else "sin definir"
            )
            lines.append(
                f"  actuadores={motors_str}, torque_por_actuador={torque_str}, "
                f"fuerza_max_por_actuador={force_str}"
            )
        else:
            lines.append(f"  motores/actuadores={motors_str}")
        return "\n".join(lines)
