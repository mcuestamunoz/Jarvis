from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jarvis.core.component_inference import infer_component
from jarvis.core.parameter_requirements import build_alias_map, normalize_alias
from jarvis.domains.registry_selector import get_registry
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import IterationDraft, IterationOperation


MATERIAL_REDUCTION_FACTOR = 0.8
VOLUME_REDUCTION_FACTOR = 0.9
PAYLOAD_REDUCTION_FACTOR = 0.9
PAYLOAD_INCREASE_FACTOR = 1.1

# Display-name → internal current_parameters key aliases.
# Computed from the domain registry — same symbol, same values, zero impact on consumers.
_PARAM_DISPLAY_ALIASES: dict[str, str] = build_alias_map()

# All valid terms for numeric-param fast-path check (keys = aliases, values = canonicals).
# Computed once at module level — _PARAM_DISPLAY_ALIASES is constant.
_NUMERIC_PARAM_KEYS: frozenset[str] = frozenset(_PARAM_DISPLAY_ALIASES.keys()) | frozenset(_PARAM_DISPLAY_ALIASES.values())


def _mass_factor_from_density_ratio(
    old_density: float,
    new_density: float,
    structural_fraction: float,
) -> tuple[float, float]:
    """Return (mass_factor, weight_change_pct) for a material substitution.

    mass_factor      — multiply old_mass by this to get new_mass
    weight_change_pct — percent change in total mass (negative = lighter)

    Formula:
        mass_factor = 1 + structural_fraction × (ρ_new/ρ_old - 1)
    """
    ratio = new_density / old_density
    mass_factor = 1.0 + structural_fraction * (ratio - 1.0)
    weight_change_pct = round((mass_factor - 1.0) * 100, 1)
    return mass_factor, weight_change_pct


class MutationEngine:
    def __init__(self, library: ComponentLibrary | None = None) -> None:
        self._library = library or default_library
    def apply_mutation(
        self,
        state: Mapping[str, Any],
        iteration_draft: IterationDraft | Mapping[str, Any],
    ) -> tuple[dict[str, Any], dict[str, float]]:
        draft = (
            iteration_draft
            if isinstance(iteration_draft, IterationDraft)
            else IterationDraft.model_validate(iteration_draft)
        )
        # ── Numeric parameter direct patch ─────────────────────────────────────
        # Must run before DEFINE routing: the wizard sets operation=REDUCE for
        # numeric params so they would otherwise fall through to resolve_strategy.
        if self._is_numeric_param_mutation(draft):
            return self.apply_numeric_param_mutation(state, draft)
        # ─────────────────────────────────────────────────────────────────────

        if draft.operation == IterationOperation.DEFINE:
            if self._is_material_definition(draft):
                return self.apply_material_definition(state, draft)
            if self._is_power_unit_definition(draft):
                return self.apply_component_definition(state, draft)
            # Generic declarative intent — record without physical mutation
            return {}, {}

        strategy = self.resolve_strategy(draft)

        if strategy == "material":
            return self.apply_material_mutation(state, draft)
        if strategy == "volumen":
            return self.apply_volume_mutation(state)
        if strategy == "payload":
            return self.apply_payload_mutation(state, draft.operation)

        raise ValueError(f"Estrategia de mutación no soportada: {strategy}")

    def is_physically_actionable(self, draft: IterationDraft) -> bool:
        """Return True iff this non-DEFINE draft can be routed to a physical mutation strategy.

        This is the public validation gate — call it BEFORE apply_mutation to guarantee
        that only resolvable drafts reach the execution layer.  It must mirror ALL
        dispatch branches of apply_mutation exactly so the two never diverge:

          1. Numeric parameter direct patch  → True  (_is_numeric_param_mutation)
          2. DEFINE operation                → False (declarative, not physical)
          3. resolve_strategy succeeds       → True
          4. resolve_strategy raises         → False

        Operation=DEFINE is not physical by definition; it always returns False here —
        callers must handle it on the DEFINE branch before reaching this check.
        """
        if draft.operation == IterationOperation.DEFINE:
            return False
        # Mirror the fast-path from apply_mutation: numeric params are always physical.
        if self._is_numeric_param_mutation(draft):
            return True
        try:
            self.resolve_strategy(draft)
            return True
        except ValueError:
            return False

    def needs_concrete_value(self, draft: IterationDraft) -> bool:
        """Return True when executing this draft would fire apply_volume_mutation
        without a user-specified value — an arbitrary fixed factor with no physical
        justification.

        Material is excluded: apply_material_mutation already hard-gates on draft.value.
        Payload is excluded: apply_payload_mutation only needs the operation direction.
        Numeric params are excluded: the wizard sets draft.value explicitly before
        routing to the numeric path.

        Callers should guard AFTER is_physically_actionable (which filters
        non-routable drafts) so resolve_strategy here is always safe to call.
        """
        if draft.operation == IterationOperation.DEFINE:
            return False
        if (draft.value or "").strip():
            return False     # explicit value provided — no issue
                             # (this also implicitly covers numeric-param mutations,
                             # which always require draft.value to be set when actionable)
        try:
            return self.resolve_strategy(draft) == "volumen"
        except ValueError:
            return False     # Bug 25 guard handles non-actionable drafts upstream

    def resolve_strategy(self, draft: IterationDraft) -> str:
        objective = normalize_alias(draft.objective or "")
        operation = (draft.operation.value if draft.operation else "").lower()
        variable = normalize_alias(draft.variable or "")
        strategy = normalize_alias(draft.strategy or "")

        normalized_candidates = [strategy, variable]
        if any("material" in candidate for candidate in normalized_candidates):
            return "material"
        if any(
            keyword in candidate
            for candidate in normalized_candidates
            for keyword in ("volumen", "tamaño", "tamano", "estructura", "dimension")
        ):
            return "volumen"
        if any("payload" in candidate or "carga" in candidate for candidate in normalized_candidates):
            return "payload"

        if objective == "peso" and operation == "reducir":
            return "material"

        raise ValueError("No se pudo resolver una estrategia de mutación determinista para la iteración.")

    def apply_material_definition(
        self,
        state: Mapping[str, Any],
        draft: IterationDraft,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        material_value = (draft.value or "").strip()
        if not material_value:
            raise ValueError("La definición de material requiere un valor explícito.")
        return {
            "design_properties": {
                "structure": {
                    "material": material_value,
                }
            }
        }, {}

    def _is_numeric_param_mutation(self, draft: IterationDraft) -> bool:
        """True when the draft targets a known numeric parameter with an explicit value."""
        variable = normalize_alias(draft.variable or "")
        has_value = bool((draft.value or "").strip())
        if not has_value:
            return False
        return variable in _NUMERIC_PARAM_KEYS and draft.operation != IterationOperation.DEFINE

    def apply_numeric_param_mutation(
        self,
        state: Mapping[str, Any],
        draft: IterationDraft,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        """Patch a numeric parameter directly in current_parameters."""
        variable = normalize_alias(draft.variable or "")
        canonical = _PARAM_DISPLAY_ALIASES.get(variable, variable)
        try:
            new_val = float(draft.value)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return {}, {}
        return {"current_parameters": {canonical: new_val}}, {}

    def apply_component_definition(self, state: Mapping[str, Any], draft: IterationDraft) -> tuple[dict[str, Any], dict[str, float]]:
        # If a component_patch is already built by the session, persist it directly.
        if draft.component_patch:
            return {
                "design_properties": {
                    "components": {key: spec.model_dump() for key, spec in draft.component_patch.items()},
                }
            }, {}

        raw_value = (draft.value or "").strip()
        if not raw_value:
            raise ValueError("La definición de components.power_unit requiere un valor explícito.")

        explicit_key, component_value = self._extract_component_key(raw_value)
        vehicle_type = str(state.get("vehicle_type") or "")
        spec = infer_component(component_value, registry=get_registry(vehicle_type=vehicle_type, text=component_value))
        component_key = explicit_key or self._next_component_key(state)

        return {
            "design_properties": {
                "components": {
                    component_key: spec.model_dump(),
                }
            }
        }, {}

    def apply_material_mutation(
        self,
        state: Mapping[str, Any],
        draft: IterationDraft,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        """Apply material change using real density ratio from the library.

        Formula:
            m_new = m_non_structural + m_structural × (ρ_new / ρ_old)
        where:
            m_structural     = masa_total × structural_fraction
            m_non_structural = masa_total × (1 - structural_fraction)
        """
        new_material = (draft.value or "").strip().lower()
        if not new_material:
            raise ValueError(
                "apply_material_mutation requiere draft.value con el nombre del material nuevo."
            )

        # ── Validate both materials exist in library (hard error) ────────────
        design = state.get("design_properties", {})
        structure = design.get("structure", {}) if isinstance(design, dict) else {}
        current_material = (
            structure.get("material") or state.get("material") or "aluminio"
        ).strip().lower()
        structural_fraction = float(structure.get("structural_fraction", 0.25))

        spec_old = self._library.get_material(current_material)  # KeyError → propagates
        spec_new = self._library.get_material(new_material)       # KeyError → propagates

        # ── Compute new mass with real density ratio ──────────────────────────
        mass_key = self._pick_key(state, "masa_total", "total_mass_kg", "mass_total")
        if mass_key is None:
            raise ValueError(
                "La mutación por material requiere una variable de masa total en el estado."
            )
        old_mass = float(state[mass_key])
        mass_factor, _ = _mass_factor_from_density_ratio(
            spec_old.density_kg_m3, spec_new.density_kg_m3, structural_fraction
        )
        new_mass = round(old_mass * mass_factor, 4)

        new_state: dict[str, Any] = {
            mass_key: new_mass,
            "material": spec_new.name,
        }
        # Derive density from library — never from old state value (rule: density is derived)
        density_key = self._pick_key(state, "densidad", "density")
        if density_key is not None:
            new_state[density_key] = spec_new.density_kg_m3

        impact: dict[str, float] = {
            mass_key: self._percent_change(old_mass, new_mass),
        }
        if density_key is not None:
            # Use library values for both ends — state density is derived, not source of truth
            impact[density_key] = self._percent_change(spec_old.density_kg_m3, spec_new.density_kg_m3)

        return new_state, impact

    def apply_volume_mutation(self, state: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, float]]:
        new_state: dict[str, Any] = {}
        impact: dict[str, float] = {}

        for dimension_key in ("volumen", "volume", "tamano", "size"):
            if dimension_key in state:
                old_value = float(state[dimension_key])
                new_value = round(old_value * VOLUME_REDUCTION_FACTOR, 4)
                new_state[dimension_key] = new_value
                impact[dimension_key] = self._percent_change(old_value, new_value)

        mass_key = self._pick_key(state, "masa_total", "total_mass_kg", "mass_total")
        if mass_key is not None:
            old_mass = float(state[mass_key])
            new_mass = round(old_mass * VOLUME_REDUCTION_FACTOR, 4)
            new_state[mass_key] = new_mass
            impact[mass_key] = self._percent_change(old_mass, new_mass)

        if not new_state:
            raise ValueError("La mutación por volumen requiere variables base de tamaño o masa en el estado.")

        return new_state, impact

    def apply_payload_mutation(
        self,
        state: Mapping[str, Any],
        operation: str | None,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        new_state: dict[str, Any] = {}
        impact: dict[str, float] = {}

        payload_key = self._pick_key(state, "payload", "payload_kg")
        if payload_key is None:
            raise ValueError("La mutación por payload requiere una variable de carga útil en el estado.")

        old_payload = float(state[payload_key])
        factor = PAYLOAD_INCREASE_FACTOR if self._is_increase_operation(operation) else PAYLOAD_REDUCTION_FACTOR
        new_payload = round(old_payload * factor, 4)
        new_state[payload_key] = new_payload
        impact[payload_key] = self._percent_change(old_payload, new_payload)

        mass_key = self._pick_key(state, "masa_total", "total_mass_kg", "mass_total")
        if mass_key is not None:
            old_mass = float(state[mass_key])
            payload_delta = new_payload - old_payload
            new_mass = round(max(old_mass + payload_delta, 0.0), 4)
            new_state[mass_key] = new_mass
            impact[mass_key] = self._percent_change(old_mass, new_mass)

        return new_state, impact

    def _pick_key(self, state: Mapping[str, Any], *candidates: str) -> str | None:
        for candidate in candidates:
            if candidate in state:
                return candidate
        return None

    def _percent_change(self, old_value: float, new_value: float) -> float:
        if old_value == 0:
            return 0.0
        return round(((new_value - old_value) / old_value) * 100, 4)

    def _light_material_name(self, current_material: str) -> str:
        normalized = current_material.strip().lower()
        material_map = {
            "acero": "aluminio",
            "steel": "aluminum",
            "aluminio": "fibra de carbono",
            "aluminum": "carbon fiber",
        }
        return material_map.get(normalized, f"{current_material}_ligero")

    def _is_increase_operation(self, operation: str | None) -> bool:
        raw_operation = operation.value if isinstance(operation, IterationOperation) else (operation or "")
        normalized = raw_operation.strip().lower()
        return any(keyword in normalized for keyword in ("aument", "increment", "subir", "sube"))

    def _is_material_definition(self, draft: IterationDraft) -> bool:
        candidates = [draft.variable or "", draft.strategy or "", draft.objective or ""]
        normalized_candidates = [candidate.strip().lower() for candidate in candidates]
        return any("material" in candidate for candidate in normalized_candidates)

    def _is_power_unit_definition(self, draft: IterationDraft) -> bool:
        candidates = [draft.variable or "", draft.strategy or "", draft.objective or ""]
        normalized_candidates = [candidate.strip().lower() for candidate in candidates]
        component_markers = ("componente", "componentes", "unidad de potencia", "power unit")
        return any(marker in candidate for candidate in normalized_candidates for marker in component_markers)

    def _extract_component_key(self, raw_value: str) -> tuple[str | None, str]:
        stripped = raw_value.strip()
        for separator in (":", "="):
            if separator not in stripped:
                continue
            candidate_key, candidate_value = [part.strip() for part in stripped.split(separator, 1)]
            sanitized_key = self._sanitize_component_key(candidate_key)
            if sanitized_key and candidate_value:
                return sanitized_key, candidate_value
        return None, stripped

    def _sanitize_component_key(self, text: str) -> str | None:
        normalized = "_".join(text.lower().strip().split())
        normalized = "".join(char for char in normalized if char.isalnum() or char == "_")
        return normalized or None

    def _next_component_key(self, state: Mapping[str, Any]) -> str:
        design_properties = state.get("design_properties", {}) if isinstance(state, Mapping) else {}
        components = design_properties.get("components", {}) if isinstance(design_properties, Mapping) else {}
        if not isinstance(components, Mapping):
            return "component_1"

        max_index = 0
        for key in components.keys():
            if not isinstance(key, str):
                continue
            if not key.startswith("component_"):
                continue
            suffix = key.removeprefix("component_")
            if suffix.isdigit():
                max_index = max(max_index, int(suffix))
        return f"component_{max_index + 1}"


def apply_mutation(
    state: Mapping[str, Any],
    iteration_draft: IterationDraft | Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, float]]:
    return MutationEngine().apply_mutation(state, iteration_draft)
