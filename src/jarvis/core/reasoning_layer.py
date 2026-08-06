from __future__ import annotations

from typing import Any

from jarvis.core.parameter_requirements import (
    MISSING_ENERGY_PARAMETERS,
    MISSING_PROPULSION_PARAMETERS,
    MISSING_PROPELLER_PARAMETERS,
    missing_force_reason_from_warnings,
    missing_params_for_reason,
    params_for_reason,
    reason_domain_label,
)
from jarvis.schemas.tool_schema import ReasoningOutput, ReasoningSuggestion


HIGH_MARGIN_THRESHOLD = 1.5
LOW_MARGIN_THRESHOLD = 1.2
HIGH_ACTUATOR_LOAD_THRESHOLD = 0.9

CONFLICT_RULES: list[dict] = [
    {"condition": "low_margin", "blocks": ["increase_payload"], "reason": "margen de empuje insuficiente"},
    {"condition": "high_actuator_load", "blocks": ["increase_payload"], "reason": "carga de actuadores al límite"},
]


class ReasoningLayer:
    def build(self, context: dict[str, Any], suggestions: list[dict[str, Any]] | None = None) -> ReasoningOutput:
        signals = self._extract_signals(context)
        insights = self._build_insights(signals, context)
        tradeoffs = self._build_tradeoffs(signals, context)
        suggested_actions = self._build_suggested_actions(signals, context, suggestions or [])
        explanation = self._build_explanation(signals, insights, tradeoffs)
        return ReasoningOutput(
            explanation=explanation,
            insights=insights,
            tradeoffs=tradeoffs,
            suggested_actions=suggested_actions,
            signals=signals,
        )

    def _extract_signals(self, context: dict[str, Any]) -> dict[str, bool]:
        simulation = context.get("last_simulation") or {}
        design_properties = context.get("design_properties") or {}
        structure = design_properties.get("structure") or {}
        warnings = simulation.get("warnings") or []
        mutation_mode = context.get("mutation_mode")
        last_mutation = context.get("last_mutation") or {}
        components = self._component_entries(context)

        margin = float(simulation.get("safety_margin_ratio", 0.0) or 0.0)
        material_defined = bool(structure.get("material"))
        power_unit_defined = bool(components)
        has_simulation = bool(simulation)
        is_declarative_context = mutation_mode == "declarative" or last_mutation.get("mode") == "declarative"
        declarative_definition_defined = material_defined or power_unit_defined

        return {
            "has_simulation": has_simulation,
            "high_margin": has_simulation and margin >= HIGH_MARGIN_THRESHOLD,
            "low_margin": has_simulation and margin < LOW_MARGIN_THRESHOLD,
            "has_warnings": bool(warnings),
            "material_defined": material_defined,
            "power_unit_defined": power_unit_defined,
            "declarative_context": is_declarative_context,
            "declarative_not_physical": declarative_definition_defined and has_simulation and is_declarative_context,
            # missing_propeller_parameters is specific; missing_physics_parameters is the generic
            # fallback. They are mutually exclusive so reasoning never double-fires.
            "missing_propeller_parameters": simulation.get("propeller_status") == MISSING_PROPELLER_PARAMETERS,
            "missing_physics_parameters": (
                simulation.get("physics_status") == "missing_parameters"
                and simulation.get("propeller_status") != MISSING_PROPELLER_PARAMETERS
            ),
            "missing_energy_parameters": simulation.get("energy_status") == MISSING_ENERGY_PARAMETERS,
            "propeller_thrust_inferred": bool(simulation.get("propeller_thrust_inferred", False)),
            "high_actuator_load": (
                has_simulation
                and float(simulation.get("per_motor_load_ratio") or 0.0) >= HIGH_ACTUATOR_LOAD_THRESHOLD
            ),
        }

    def _build_insights(self, signals: dict[str, bool], context: dict[str, Any]) -> list[str]:
        insights: list[str] = []
        simulation = context.get("last_simulation") or {}
        margin = simulation.get("safety_margin_ratio")
        recent_definition = self._describe_recent_definition(context)
        power_unit_missing = self._detect_power_unit_missing_fields(context)

        if signals["high_margin"]:
            insights.append(f"El sistema tiene un margen de empuje elevado ({margin}).")
        if signals["missing_physics_parameters"]:
            missing_params = self._detect_missing_physics_params(context)
            if missing_params:
                insights.append(
                    f"El sistema no puede evaluar la viabilidad física porque faltan parámetros de transmisión: "
                    f"{', '.join(missing_params)}. Define estos valores en los parámetros del proyecto."
                )
            else:
                insights.append(
                    "El sistema no puede evaluar la viabilidad física porque faltan parámetros de transmisión."
                )
        if signals["missing_propeller_parameters"]:
            insights.append(
                "Faltan parámetros de hélice (propeller_diameter_in, propeller_rpm) para inferir el empuje por motor. "
                "Con estos datos el engine puede estimar el thrust (modelo Ct≈0.12)."
            )
        if signals["missing_energy_parameters"] and not signals["missing_physics_parameters"]:
            missing_e = self._detect_missing_energy_params(context)
            param_str = ", ".join(missing_e) if missing_e else "battery_capacity_wh, motor_power_w"
            insights.append(
                f"No se puede calcular la autonomía porque faltan parámetros de energía: "
                f"{param_str}. Define estos valores en los parámetros del proyecto."
            )
        if signals["material_defined"]:
            insights.append("El material estructural está definido en propiedades de diseño.")
        if signals["power_unit_defined"]:
            insights.append("Se han definido componentes para la unidad de potencia en el estado declarativo.")
        if recent_definition is not None:
            insights.append(f"Última definición declarativa registrada: {recent_definition}.")
        if signals["declarative_not_physical"]:
            insights.append("La definición declarativa reciente aún no está conectada al modelo físico de simulación.")
        if power_unit_missing:
            insights.append(
                "La definición de unidad de potencia es válida pero incompleta para el modelo físico. "
                f"Faltan: {', '.join(power_unit_missing)}."
            )
        if signals["has_warnings"]:
            insights.append("La simulación reporta warnings que requieren revisión.")
        if signals["propeller_thrust_inferred"]:
            insights.append(
                "El empuje por motor ha sido estimado desde las dimensiones de la hélice "
                "(modelo simplificado, Ct≈0.12). Para mayor precisión, declara el empuje medido."
            )
        if not signals["has_simulation"]:
            insights.append("No hay una simulación reciente para extraer señales físicas confiables.")

        return insights

    def _build_tradeoffs(self, signals: dict[str, bool], context: dict[str, Any]) -> list[str]:
        tradeoffs: list[str] = []

        if signals["low_margin"]:
            tradeoffs.append("El sistema está cerca del límite de empuje; aumentar carga puede degradar viabilidad.")
        if signals["high_margin"]:
            tradeoffs.append("Aumentar carga útil puede aprovechar margen, pero reducirá la seguridad disponible.")
        if signals["missing_physics_parameters"]:
            force_reason = self._get_missing_force_reason(context)
            all_required = params_for_reason(force_reason)
            domain_label = reason_domain_label(force_reason)
            tradeoffs.append(
                f"Sin parámetros de {domain_label} ({', '.join(all_required)}) no es posible calcular fuerza de tracción "
                "ni evaluar viabilidad del sistema."
            )
        if signals["missing_propeller_parameters"]:
            tradeoffs.append(
                "Sin diámetro y RPM de hélice no es posible calcular el empuje por motor. "
                "El modelo usa Ct=0.12; el empuje real depende del perfil aerodinámico de la hélice."
            )
        if signals["missing_energy_parameters"] and not signals["missing_physics_parameters"]:
            energy_required = params_for_reason(MISSING_ENERGY_PARAMETERS)
            tradeoffs.append(
                f"Sin parámetros de energía ({', '.join(energy_required)}) no es posible calcular la autonomía operacional."
            )
        if signals["declarative_not_physical"]:
            tradeoffs.append("Las propiedades declarativas nuevas no alteran resultados físicos hasta modelarlas en cálculo/simulación.")
        if signals["power_unit_defined"] and signals["declarative_context"]:
            tradeoffs.append("Sin datos reales de empuje por motor, el modelo de propulsión se mantiene aproximado.")
        if signals["propeller_thrust_inferred"]:
            tradeoffs.append(
                "El modelo de hélice usa coeficiente de empuje fijo (Ct=0.12); "
                "el empuje real puede variar según el diseño aerodinámico específico de la hélice."
            )

        return tradeoffs

    def _build_suggested_actions(
        self,
        signals: dict[str, bool],
        context: dict[str, Any],
        suggestions: list[dict[str, Any]],
    ) -> list[ReasoningSuggestion]:
        """Single exit point: collect → deduplicate → resolve conflicts → sort."""
        raw = self._collect_suggested_actions(signals, context, suggestions)
        raw = self._deduplicate(raw)
        resolved = self._resolve_conflicts(raw, signals)
        return sorted(resolved, key=lambda s: (not s.is_critical, -(s.priority or 0.0)))

    def _collect_suggested_actions(
        self,
        signals: dict[str, bool],
        context: dict[str, Any],
        suggestions: list[dict[str, Any]],
    ) -> list[ReasoningSuggestion]:
        if signals["missing_propeller_parameters"]:
            # Specific propeller gap — takes precedence over generic physics suggestion.
            return [
                ReasoningSuggestion(
                    action="iterate",
                    label="Declarar propeller_diameter_in y propeller_rpm",
                    reason=(
                        "El sistema no puede estimar el empuje por motor sin el diámetro de hélice y las RPM. "
                        "Decáralos para activar la ruta de inferencia aerodinámica (Ct≈0.12)."
                    ),
                    priority=0.99,
                )
            ]

        if signals["missing_physics_parameters"]:
            missing_params = self._detect_missing_physics_params(context)
            force_reason = self._get_missing_force_reason(context)
            fallback_params = params_for_reason(force_reason)
            param_list = ", ".join(missing_params) if missing_params else ", ".join(fallback_params)
            if force_reason == MISSING_PROPULSION_PARAMETERS:
                reason_text = (
                    f"El sistema no puede calcular el empuje disponible sin {param_list}. "
                    "Defínelos para completar el modelo de propulsión."
                )
            else:
                reason_text = (
                    f"El sistema tiene torque declarado pero no puede convertirlo a fuerza "
                    f"sin {param_list}. Añadelos como parámetros del sistema."
                )
            return [
                ReasoningSuggestion(
                    action="iterate",
                    label=f"Declarar {param_list} en parámetros del proyecto",
                    reason=reason_text,
                    priority=0.99,
                )
            ]

        if signals["declarative_context"]:
            return self._build_declarative_next_steps(context)

        if signals["missing_energy_parameters"]:
            missing_e = self._detect_missing_energy_params(context)
            param_list = ", ".join(missing_e) if missing_e else "battery_capacity_wh, motor_power_w"
            return [
                ReasoningSuggestion(
                    action="iterate",
                    label=f"Declarar {param_list} en parámetros del proyecto",
                    reason=(
                        f"El sistema no puede calcular autonomía operacional sin {param_list}. "
                        "Añadelos para completar el modelo energético."
                    ),
                    priority=0.95,
                )
            ]

        action_map = {
            "reduce_weight": ("iterate", "Reducir peso"),
            "increase_payload": ("iterate", "Aumentar carga útil"),
            "improve_efficiency": ("iterate", "Mejorar eficiencia"),
            "increase_thrust": ("iterate", "Aumentar empuje disponible"),
        }
        enriched: list[ReasoningSuggestion] = []

        for suggestion in suggestions:
            suggestion_type = suggestion.get("type")
            if suggestion_type not in action_map:
                continue
            action, label = action_map[suggestion_type]
            enriched.append(
                ReasoningSuggestion(
                    action=action,
                    label=label,
                    reason=suggestion.get("reason", "Sugerencia derivada del estado actual."),
                    priority=suggestion.get("priority"),
                    is_critical=suggestion_type == "increase_thrust" and signals.get("high_actuator_load", False),
                    action_type=suggestion_type,
                )
            )

        if not enriched and signals["has_simulation"] and signals["high_margin"]:
            enriched.append(
                ReasoningSuggestion(
                    action="iterate",
                    label="Aumentar carga útil",
                    reason="El margen de empuje actual permite explorar más carga útil.",
                    priority=0.8,
                    action_type="increase_payload",
                )
            )

        if signals.get("low_margin"):
            if any(s.action_type == "increase_thrust" for s in enriched):
                enriched = [
                    s.model_copy(update={"is_critical": True}) if s.action_type == "increase_thrust" else s
                    for s in enriched
                ]
            else:
                enriched.insert(
                    0,
                    ReasoningSuggestion(
                        action="iterate",
                        label="Aumentar empuje disponible",
                        reason="El margen de seguridad es bajo. El sistema puede no superar el peso máximo bajo carga.",
                        priority=0.99,
                        is_critical=True,
                        action_type="increase_thrust",
                    ),
                )

        return enriched

    def _build_declarative_next_steps(self, context: dict[str, Any]) -> list[ReasoningSuggestion]:
        components = self._component_entries(context)
        has_components = bool(components)
        power_unit_missing = self._detect_power_unit_missing_fields(context)
        component_key = self._latest_component_key(context) or "componente"

        if has_components:
            actions: list[ReasoningSuggestion] = []
            if power_unit_missing:
                actions.append(
                    ReasoningSuggestion(
                        action="iterate",
                        label=f"Completar especificación de {component_key}",
                        reason=f"Faltan: {', '.join(power_unit_missing)}.",
                        priority=0.95,
                    )
                )
            actions.extend(
                [
                    ReasoningSuggestion(
                        action="iterate",
                        label="Definir empuje por motor real",
                        reason="Ya definiste componentes de potencia; falta mapear su empuje real para refinar el modelo.",
                        priority=0.9,
                    ),
                    ReasoningSuggestion(
                        action="iterate",
                        label="Modelar unidad de potencia",
                        reason="Con una unidad de potencia declarada, el siguiente paso es conectarla al cálculo de propulsión.",
                        priority=0.8,
                    ),
                ]
            )
            return actions

        return [
            ReasoningSuggestion(
                action="iterate",
                label="Definir parámetro técnico medible",
                reason="Conviene añadir una definición declarativa con valor medible para conectarla al modelo físico.",
                priority=0.7,
            )
        ]

    def _deduplicate(self, suggestions: list[ReasoningSuggestion]) -> list[ReasoningSuggestion]:
        """Keep at most one suggestion per action_type (highest priority wins).
        Suggestions with action_type=None are always kept as-is."""
        seen: dict[str, ReasoningSuggestion] = {}
        result: list[ReasoningSuggestion] = []
        for s in suggestions:
            if s.action_type is None:
                result.append(s)
            elif s.action_type not in seen or (s.priority or 0.0) > (seen[s.action_type].priority or 0.0):
                seen[s.action_type] = s
        result.extend(seen.values())
        return result

    def _resolve_conflicts(
        self,
        suggestions: list[ReasoningSuggestion],
        signals: dict[str, bool],
    ) -> list[ReasoningSuggestion]:
        """Return copies of suggestions with blocked=True for any whose action_type
        matches a rule whose condition signal is active. Never mutates in place."""
        blocked_map: dict[str, str] = {}  # action_type → block_reason
        for rule in CONFLICT_RULES:
            if signals.get(rule["condition"]):
                for action_type in rule["blocks"]:
                    blocked_map[action_type] = rule.get("reason", "bloqueado por regla de conflicto")
        if not blocked_map:
            return suggestions
        return [
            s.model_copy(update={"blocked": True, "block_reason": blocked_map[s.action_type]})
            if (s.action_type and s.action_type in blocked_map)
            else s
            for s in suggestions
        ]

    def _get_missing_force_reason(self, context: dict[str, Any]) -> str:
        """Return the missing-force reason code from simulation warnings.

        Reads from context["last_simulation"]["warnings"] — the reason code is
        emitted by the engine so there is a single source of truth.
        Falls back to the legacy transmission code for states without a record.
        """
        simulation = context.get("last_simulation") or {}
        warnings = simulation.get("warnings") or []
        return missing_force_reason_from_warnings(warnings)

    def _detect_missing_physics_params(self, context: dict[str, Any]) -> list[str]:
        """Return params required for force conversion that are absent from current_parameters.

        Derives the required param list from parameter_requirements so new
        conversion domains only need an entry in that catalog.
        """
        params = context.get("current_parameters") or {}
        reason = self._get_missing_force_reason(context)
        return missing_params_for_reason(reason, params)

    def _detect_missing_energy_params(self, context: dict[str, Any]) -> list[str]:
        """Return params required for energy calculation that are absent from current_parameters."""
        params = context.get("current_parameters") or {}
        return missing_params_for_reason(MISSING_ENERGY_PARAMETERS, params)

    def _detect_power_unit_missing_fields(self, context: dict[str, Any]) -> list[str]:
        latest_entry = self._latest_component_entry(context)
        if latest_entry is not None:
            entry_missing = latest_entry.get("missing_fields") or []
            if isinstance(entry_missing, list) and entry_missing:
                return [str(item) for item in entry_missing]

        latest_inference = self._latest_component_inference(context)
        if latest_inference is not None:
            missing = latest_inference.get("missing_fields") or []
            if isinstance(missing, list):
                return [str(item) for item in missing]

        if latest_entry is None:
            return []

        value = str(latest_entry.get("value") or "").strip().lower()
        if not value or "motor" not in value:
            return []

        missing: list[str] = []
        has_number = any(char.isdigit() for char in value)
        has_metric = any(keyword in value for keyword in ("kv", "n", "kgf", "a", "w", "esc"))
        if not (has_number or has_metric):
            missing.append("empuje por motor o KV")

        has_motor_count = ("x" in value) or (" motores" in value and has_number)
        if not has_motor_count:
            missing.append("número de motores")

        return missing

    def _latest_component_inference(self, context: dict[str, Any]) -> dict[str, Any] | None:
        latest_entry = self._latest_component_entry(context)
        if latest_entry is None:
            return None
        inference = latest_entry.get("inference")
        if isinstance(inference, dict):
            return inference
        return None

    _COMPONENT_TYPE_LABELS: dict[str, str] = {
        "propulsion_active": "motor",
        "propulsion_passive": "hélice",
        "power_supply": "batería",
        "control": "controlador",
        "structure": "estructura",
        "sensor": "sensor",
        "generic_component": "componente",
    }

    def _humanize_component_label(self, key: str, entry: dict[str, Any]) -> str:
        """Returns the most descriptive human label for a component entry."""
        component_type = str(entry.get("component_type") or "").strip()
        if component_type:
            return self._COMPONENT_TYPE_LABELS.get(component_type, component_type.replace("_", " "))
        name = str(entry.get("name") or "").strip()
        if name:
            return name
        # fallback: humanize the dict key
        return key.replace("_", " ")

    def _latest_component_key(self, context: dict[str, Any]) -> str | None:
        entries = self._component_entries(context)
        if not entries:
            return None
        # Prefer the entry that has missing_fields (most actionable)
        for key, entry in entries.items():
            if isinstance(entry, dict) and entry.get("missing_fields"):
                return self._humanize_component_label(key, entry)
        # Fallback: first entry
        key = next(iter(entries))
        entry = entries[key]
        if isinstance(entry, dict):
            return self._humanize_component_label(key, entry)
        return key.replace("_", " ")

    def _latest_component_entry(self, context: dict[str, Any]) -> dict[str, Any] | None:
        entries = self._component_entries(context)
        if not entries:
            return None
        key = next(iter(entries))
        entry = entries.get(key)
        if isinstance(entry, dict):
            return entry
        return None

    def _component_entries(self, context: dict[str, Any]) -> dict[str, Any]:
        design_properties = context.get("design_properties") or {}
        components = design_properties.get("components") or {}
        if not isinstance(components, dict):
            return {}

        if "power_unit" in components:
            # Legacy compatibility: synthesize a single entry from older shape.
            inferred_items = components.get("inferred_items") or {}
            if isinstance(inferred_items, dict) and inferred_items:
                key = next(iter(inferred_items))
                legacy_entry = inferred_items.get(key)
                if isinstance(legacy_entry, dict):
                    return {str(key): legacy_entry}
            power_unit = components.get("power_unit")
            if power_unit:
                return {"component_legacy": {"value": power_unit}}

        return {key: value for key, value in components.items() if isinstance(value, dict)}

    def _describe_recent_definition(self, context: dict[str, Any]) -> str | None:
        last_mutation = context.get("last_mutation") or {}
        if last_mutation.get("mode") != "declarative":
            return None

        # Prefer reading from current design_properties for accuracy
        entries = self._component_entries(context)
        if entries:
            labels = []
            for key, entry in entries.items():
                if isinstance(entry, dict):
                    labels.append(self._humanize_component_label(key, entry))
            if labels:
                return "componentes: " + ", ".join(labels)

        # Fallback to last_mutation draft if no components in design_properties
        draft = last_mutation.get("draft") or {}
        variable = draft.get("variable")
        value = draft.get("value")
        if variable and value:
            return f"{variable}: {value}"
        if variable:
            return str(variable)
        return None

    def _build_explanation(self, signals: dict[str, bool], insights: list[str], tradeoffs: list[str]) -> str:
        if signals["missing_physics_parameters"]:
            base = "El sistema no puede evaluar la viabilidad física: faltan parámetros de transmisión."
        elif signals["has_simulation"] and signals["high_margin"]:
            base = "El sistema actual es estable y tiene margen técnico suficiente."
        elif signals["has_simulation"] and signals["low_margin"]:
            base = "El sistema actual está en una zona de margen ajustado y requiere cautela."
        elif signals["has_simulation"]:
            base = "El sistema tiene una simulación reciente y estado técnico utilizable."
        else:
            base = "No hay simulación reciente; la explicación se basa en estado declarativo y contexto disponible."

        if signals["declarative_not_physical"]:
            base += " La definición declarativa reciente aún no afecta los resultados físicos en esta versión."

        if insights:
            return base + " " + insights[0]
        if tradeoffs:
            return base + " " + tradeoffs[0]
        return base
