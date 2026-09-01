"""Design Space Explorer — exploración automática de configuraciones óptimas.

Flujo:
    project_state + goal_key → DesignExplorer.explore() → ExplorationResult

Garantías:
    - Operación 100% en memoria: no escribe en disco, no llama a record_action ni save_state.
    - No muta project_state ni ningún parámetro de entrada.
    - Candidatos inviables (can_fly=False) se separan antes del ranking.
    - Candidatos con parámetros requeridos ausentes se omiten sin excepción.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import apply_components_delta
from jarvis.core.system_architecture_catalog import COMPONENT_MIRRORED_PARAMS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.tool_schema import CalculationBundle, SimulationResult
from jarvis.simulation.simulator import FeasibilitySimulator
from jarvis.tools.electricity import estimate_battery_mass_kg


# ── Labels de objetivo ────────────────────────────────────────────────────────

GOAL_LABELS: dict[str, str] = {
    "mejorar_autonomia": "maximizar autonomía",
    "aumentar_payload": "maximizar carga útil",
    "reducir_payload": "minimizar carga útil",
    "reducir_masa": "minimizar masa total",
    "mejorar_estabilidad": "maximizar margen de seguridad",
}


# ── Grids de exploración ──────────────────────────────────────────────────────
# Cada entry es un dict de deltas a aplicar sobre current_parameters.
#
# Convención de claves:
#   {param}_factor  → multiplica el valor actual por el factor (float)
#   {param}_delta   → suma un entero al valor actual (útil para motors)
#   {param}_value   → fija un valor absoluto
#
# Los candidatos cuyo parámetro base no exista en current_parameters se omiten
# automáticamente en _apply_delta() — nunca se usan defaults inventados.

EXPLORATION_GRIDS: dict[str, list[dict[str, Any]]] = {
    "mejorar_autonomia": [
        # ── Batería más grande ────────────────────────────────────────────────
        {"battery_capacity_wh_factor": 1.5},
        {"battery_capacity_wh_factor": 2.0},
        {"battery_capacity_wh_factor": 2.5},
        # ── Reducción de actuadores (menos consumo) ───────────────────────────
        {"motor_count_delta": -1},
        {"motor_count_delta": -2},
        {"battery_capacity_wh_factor": 1.5, "motor_count_delta": -1},
        {"battery_capacity_wh_factor": 2.0, "motor_count_delta": -1},
        # ── Motores más eficientes (menor consumo) ────────────────────────────
        {"motor_power_w_factor": 0.75},
        {"battery_capacity_wh_factor": 2.0, "motor_power_w_factor": 0.75},
        # ── U3: Estructura más ligera (domain-agnostic: factor relativo al baseline)
        # Funciona para dron (300g frame), rover (3kg), robot arm (1kg), etc.
        # Si structure_mass_override_kg no existe en base_params, el candidato
        # se omite automáticamente (_apply_delta devuelve None).
        {"structure_mass_override_kg_factor": 0.6},
        {"structure_mass_override_kg_factor": 0.75},
        {"structure_mass_override_kg_factor": 0.6,  "battery_capacity_wh_factor": 1.5},
        # ── U3: Motores más eficientes combinados con frame ligero ─────────────
        {"motor_power_w_factor": 0.65},
        {"motor_power_w_factor": 0.65, "structure_mass_override_kg_factor": 0.75},
    ],
    "aumentar_payload": [
        {"payload_kg_factor": 1.2},
        {"payload_kg_factor": 1.5},
        {"payload_kg_factor": 2.0},
        {"per_motor_max_thrust_n_factor": 1.5},
        {"per_motor_max_thrust_n_factor": 2.0},
        {"motor_count_delta": 2},
        {"motor_count_delta": 4},
        {"motor_count_delta": 2, "per_motor_max_thrust_n_factor": 1.5},
        {"payload_kg_factor": 1.2, "motor_count_delta": 2},
    ],
    "reducir_masa": [
        {"structure_mass_factor_factor": 0.7},
        {"structure_mass_factor_factor": 0.5},
        {"structure_mass_factor_factor": 0.4},
        {"payload_kg_factor": 0.8},
        {"structure_mass_factor_factor": 0.7, "payload_kg_factor": 0.8},
    ],
    # F-1: direction-mirrored counterpart of aumentar_payload — factors below
    # 1.0 only, so candidates always explore LOWER payload than the current
    # value, never accidentally reusing the increase direction. motor_count_delta
    # stays architecture-conditional by construction: _apply_delta() already
    # omits any candidate whose referenced param is absent from base_params
    # (no motor_count on this project → that candidate is silently skipped,
    # same mechanism every other goal's motor_count_delta entries already rely on).
    "reducir_payload": [
        {"payload_kg_factor": 0.85},
        {"payload_kg_factor": 0.7},
        {"payload_kg_factor": 0.5},
        {"structure_mass_factor_factor": 0.85, "payload_kg_factor": 0.85},
        {"motor_count_delta": -1, "payload_kg_factor": 0.85},
    ],
    "mejorar_estabilidad": [
        {"motor_count_delta": 2},
        {"motor_count_delta": 4},
        {"per_motor_max_thrust_n_factor": 1.5},
        {"per_motor_max_thrust_n_factor": 2.0},
        {"per_motor_max_thrust_n_factor": 1.5, "motor_count_delta": 2},
        {"safety_factor_factor": 1.25},
        {"safety_factor_factor": 1.5},
    ],
}

# Máximo de candidatos viables devueltos en ExplorationResult.viable
MAX_VIABLE = 5


# ── Component spec helpers ────────────────────────────────────────────────────

def _build_component_spec(
    component_key: str,
    component_type: str,
    property_name: str,
    unit: str | None,
    value: Any,
) -> ComponentSpec:
    """Builds a minimal ComponentSpec for a single-property DSE variation.

    Domain-agnostic: any component_key that apply_components_delta knows how to
    route will be correctly evaluated. Components not in _APPLY_ORDER fall through
    to set_control_component (declarative storage, no physics derivation).
    """
    return ComponentSpec(
        name=f"{component_key}_{property_name}_{value}",
        component_type=component_type,
        suggested_key=component_key,
        inference_confidence=0.9,
        completeness="medium",
        source="declared",
        properties={
            property_name: PropertyValue(value=value, unit=unit, confidence=0.95, source="declared")
        },
    )


def _battery_spec(capacity_wh: float) -> ComponentSpec:
    """Battery ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("battery", "energy_storage", "battery_capacity_wh", "Wh", capacity_wh)


def _motor_spec(power_w: float) -> ComponentSpec:
    """Motor ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("motors", "propulsion_active", "power_w", "W", power_w)


def _frame_spec(mass_kg: float) -> ComponentSpec:
    """Frame ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("frame", "structure", "mass_kg", "kg", mass_kg)


# ── Component variation rules ─────────────────────────────────────────────────
# Declarative table: for each exploration goal, which component properties to
# vary and with which absolute values. Adding a new component type or goal only
# requires adding an entry here — no logic changes needed.
#
# Rule schema (each entry is a plain dict):
#   component_key  str        — key in components dict (routed by apply_components_delta)
#   component_type str        — ComponentSpec.component_type (passed to writer routing)
#   property_name  str        — property key in ComponentSpec.properties
#   unit           str|None   — unit for PropertyValue
#   values         list[Any]  — concrete values; one candidate is generated per value

COMPONENT_VARIATION_RULES: dict[str, list[dict]] = {
    "mejorar_autonomia": [
        {
            "component_key": "battery", "component_type": "energy_storage",
            "property_name": "battery_capacity_wh", "unit": "Wh",
            "values": [300.0, 500.0, 800.0, 1200.0],
        },
    ],
    "aumentar_payload": [
        {
            "component_key": "motors", "component_type": "propulsion_active",
            "property_name": "power_w", "unit": "W",
            "values": [150.0, 200.0, 300.0, 400.0],
        },
    ],
    "reducir_masa": [
        {
            "component_key": "frame", "component_type": "structure",
            "property_name": "mass_kg", "unit": "kg",
            "values": [0.280, 0.350, 0.450],
        },
    ],
    "mejorar_estabilidad": [
        {
            "component_key": "frame", "component_type": "structure",
            "property_name": "mass_kg", "unit": "kg",
            "values": [0.500, 0.700],
        },
    ],
}


# Impl C (Catalog-aware DSE v1): goals that get a motor-catalog candidate branch.
_CATALOG_MOTOR_GOAL_KEYS: frozenset[str] = frozenset({
    "aumentar_payload",
    "mejorar_estabilidad",
})

# Slice C4: appended to explore message when Strategy 3 catalog search is empty.
_CATALOG_MOTOR_FALLBACK_NOTE: str = (
    "Nota: no hay motores del catálogo que cubran el espacio de diseño actual; "
    "las opciones listadas son variaciones paramétricas o de otros componentes."
)


def _get_bound_motor_sku(project_state: Any) -> str | None:
    """Impl C: currently bound motor SKU, if any (★4 exclusion input). Pure."""
    dp = getattr(project_state, "design_properties", None)
    motors = (getattr(dp, "components", None) or {}).get("motors")
    catalog_ref = getattr(motors, "catalog_ref", None) if motors is not None else None
    if catalog_ref is not None and catalog_ref.family == "motor":
        return catalog_ref.sku
    return None


def _build_catalog_motor_spec(suggestion: Any, *, base: ComponentSpec | None) -> ComponentSpec:
    """Impl C: project a catalog MotorSuggestion into a bound ComponentSpec.

    Wraps ``catalog_bind.bind_motor_from_catalog`` (the one shared bind path —
    no parallel identity logic). Data-hygiene fix (investigation §10):
    ``bind_motor_from_catalog``'s ``base=`` merge preserves the base spec's
    ``.name`` (an old freeform description or prior SKU), never updating it to
    the new SKU — harmless for DSE labels (``_build_label_components`` reads
    ``.properties``/``.catalog_ref``, never ``.name``) but a stale field for
    any other future consumer that displays ``.name`` directly. Set explicitly
    here rather than in ``catalog_bind.py`` (out of scope — §0).
    """
    from jarvis.core.catalog_bind import bind_motor_from_catalog

    spec = bind_motor_from_catalog(suggestion, base=base)
    if base is not None:
        spec = spec.model_copy(update={"name": str(suggestion["name"])})
    return spec


def _build_catalog_motor_candidates_for_goal(
    goal_key: str,
    project_state: Any,
    *,
    normalized_state: Any,
) -> tuple[list[dict[str, ComponentSpec]], bool]:
    """Impl C ★1/★2: catalog-native motor candidates for one explore call.

    Reuses ``motor_catalog_assist.build_motor_catalog_suggestions`` — the G22
    single search authority — never a new motor search/ranking function.

    Returns ``(candidate_deltas, had_library_matches)``. ``had_library_matches``
    is True iff the search returned >=1 suggestion *before* the ★4 bound-SKU
    exclusion — it answers "was the catalog search itself empty" (Strategy 3's
    only fallback trigger), independent of whether every match happened to be
    the already-bound SKU.
    """
    if goal_key not in _CATALOG_MOTOR_GOAL_KEYS:
        return [], False

    from jarvis.core.motor_catalog_assist import build_motor_catalog_suggestions

    suggestions = build_motor_catalog_suggestions(project_state, limit=5)
    if not suggestions:
        return [], False

    bound_sku = _get_bound_motor_sku(project_state)
    dp = getattr(normalized_state, "design_properties", None)
    base_motor = (getattr(dp, "components", None) or {}).get("motors")

    deltas: list[dict[str, ComponentSpec]] = []
    for suggestion in suggestions:
        if bound_sku is not None and suggestion["name"] == bound_sku:
            continue  # ★4 — never re-offer the SKU already bound
        spec = _build_catalog_motor_spec(suggestion, base=base_motor)
        deltas.append({"motors": spec})

    return deltas, True


def _is_synthetic_motor_component_delta(comp_delta: dict[str, ComponentSpec]) -> bool:
    """Impl C: True when *comp_delta* is a synthetic (non-catalog) motors
    variation — today's COMPONENT_VARIATION_RULES motor entries, which carry
    invented property values and no catalog_ref. Used only to skip those
    entries (Strategy 3) once the real catalog branch already produced
    candidates for this goal — never to filter any other component key."""
    spec = comp_delta.get("motors")
    return spec is not None and spec.catalog_ref is None


def _build_component_candidates_for_goal(goal_key: str) -> list[dict[str, ComponentSpec]]:
    """Generates component grid entries for a goal from COMPONENT_VARIATION_RULES.

    Returns one dict[component_key → ComponentSpec] per value per rule.
    Adding new component types or goals only requires updating
    COMPONENT_VARIATION_RULES — this function never needs to change.
    """
    entries: list[dict[str, ComponentSpec]] = []
    for rule in COMPONENT_VARIATION_RULES.get(goal_key, []):
        for value in rule["values"]:
            spec = _build_component_spec(
                component_key=rule["component_key"],
                component_type=rule["component_type"],
                property_name=rule["property_name"],
                unit=rule.get("unit"),
                value=value,
            )
            entries.append({rule["component_key"]: spec})
    return entries


# ── Schemas ───────────────────────────────────────────────────────────────────

class ExplorationCandidate(BaseModel):
    params_delta: dict[str, Any] = Field(default_factory=dict)
    components_delta: dict[str, ComponentSpec] = Field(default_factory=dict)
    # generation_metadata: reserved for v2 generative path
    generation_metadata: dict[str, Any] | None = None
    calculations: CalculationBundle
    simulation: SimulationResult
    score: float
    label: str
    improvement: float = 0.0


class ExplorationResult(BaseModel):
    goal_key: str
    goal_label: str
    baseline_score: float
    baseline_calculations: CalculationBundle
    baseline_simulation: SimulationResult
    candidates: list[ExplorationCandidate] = Field(default_factory=list)
    viable: list[ExplorationCandidate] = Field(default_factory=list)
    # Impl C, Slice C4: set when a catalog-eligible goal's motor search
    # (build_motor_catalog_suggestions) returned zero matches — orchestrator
    # surfaces this as one honest line in the explore message. None for every
    # other goal / when the search found candidates.
    catalog_motor_note: str | None = None


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_candidate(
    sim: SimulationResult,
    calc: CalculationBundle,
    goal_key: str,
) -> float:
    """Devuelve un score escalar para el candidato. Mayor = mejor para todos los goals.

    Para reducir_masa se niega total_mass_kg para que sort descendente funcione.
    """
    if goal_key == "mejorar_autonomia":
        return sim.autonomy_min or 0.0
    if goal_key == "aumentar_payload":
        return sim.safety_margin_ratio * calc.payload_kg
    if goal_key == "reducir_payload":
        # Mirrors reducir_masa's shape (pure-reduction goal): lower payload_kg
        # scores higher so descending sort favors bigger reductions.
        return -calc.payload_kg
    if goal_key == "reducir_masa":
        return -calc.total_mass_kg
    if goal_key == "mejorar_estabilidad":
        return sim.safety_margin_ratio
    return 0.0


# ── Label generation ──────────────────────────────────────────────────────────

_DELTA_PARAM_LABELS: dict[str, str] = {
    "battery_capacity_wh": "batería (Wh)",
    "motor_power_w": "potencia/motor (W)",
    "payload_kg": "carga útil (kg)",
    "per_motor_max_thrust_n": "empuje/motor (N)",
    "structure_mass_factor": "factor masa estructural",
    "safety_factor": "safety factor",
    "motor_count": "motores",
}


def _build_label(delta: dict[str, Any], applied: dict[str, Any]) -> str:
    """Genera una etiqueta legible para un candidato params-driven."""
    parts = []
    for key, value in delta.items():
        if key.endswith("_factor"):
            param_name = key[: -len("_factor")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            new_val = applied.get(param_name)
            if new_val is not None:
                formatted = int(new_val) if isinstance(new_val, float) and new_val == int(new_val) else round(new_val, 1)
                parts.append(f"{human}={formatted}")
        elif key.endswith("_delta"):
            param_name = key[: -len("_delta")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            new_val = applied.get(param_name)
            if new_val is not None:
                parts.append(f"{human}={new_val}")
        elif key.endswith("_value"):
            param_name = key[: -len("_value")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            parts.append(f"{human}={value}")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else str(delta)


def _build_label_components(components_delta: dict[str, Any]) -> str:
    """Genera una etiqueta legible para un candidato component-driven.

    Impl C ★6: when a spec carries a bound ``catalog_ref`` (real SKU), the
    SKU is shown in brackets — ``motors [sku]: thrust_n=..., ...`` — so a
    catalog-native candidate is distinguishable from a synthetic one in the
    explore list. ``_score_candidate`` is unchanged (★6 locks scoring).
    """
    parts = []
    for comp_key, spec in components_delta.items():
        label_key = comp_key
        catalog_ref = getattr(spec, "catalog_ref", None)
        if catalog_ref is not None:
            label_key = f"{comp_key} [{catalog_ref.sku}]"
        if not spec.properties:
            parts.append(label_key)
            continue
        prop_summary = ", ".join(
            f"{k}={v.value}" for k, v in spec.properties.items() if v.value is not None
        )
        parts.append(f"{label_key}: {prop_summary}" if prop_summary else label_key)
    return " | ".join(parts) if parts else str(components_delta)


# ── Delta application ─────────────────────────────────────────────────────────

def _apply_delta(
    base_params: dict[str, Any],
    delta: dict[str, Any],
) -> dict[str, Any] | None:
    """Aplica un delta sobre base_params y devuelve un nuevo dict de parámetros.

    Devuelve None si algún parámetro referenciado no existe en base_params,
    lo que provoca que el candidato se omita sin error.
    """
    # DA2-prep (D4): mirrored params come from components_delta, not params_delta
    delta = {k: v for k, v in delta.items() if k not in COMPONENT_MIRRORED_PARAMS}
    result = dict(base_params)
    for key, value in delta.items():
        if key.endswith("_factor"):
            param_name = key[: -len("_factor")]
            base_value = base_params.get(param_name)
            if base_value is None:
                return None  # parámetro ausente — omitir candidato
            result[param_name] = round(float(base_value) * float(value), 4)
        elif key.endswith("_delta"):
            param_name = key[: -len("_delta")]
            base_value = base_params.get(param_name)
            if base_value is None:
                return None
            new_val = int(round(float(base_value))) + int(value)
            result[param_name] = max(1, new_val)  # discreta: mínimo 1
        elif key.endswith("_value"):
            param_name = key[: -len("_value")]
            result[param_name] = value
        else:
            result[key] = value

    # U1: keep battery_mass_kg in sync when battery_capacity_wh changes via delta.
    if "battery_capacity_wh" in result:
        result["battery_mass_kg"] = estimate_battery_mass_kg(result["battery_capacity_wh"])

    return result


def _is_catalog_native_motor_candidate(candidate: ExplorationCandidate) -> bool:
    """G24C §2.1 (locked): a candidate is catalog-native (motor) when its
    components_delta carries a bound motors spec — never a params-only
    delta. Single predicate reused by _finalize_viable_list so "catalog-
    native" has exactly one definition."""
    motors_spec = candidate.components_delta.get("motors")
    if motors_spec is None:
        return False
    catalog_ref = getattr(motors_spec, "catalog_ref", None)
    return catalog_ref is not None and catalog_ref.family == "motor"


def _finalize_viable_list(viable: list[ExplorationCandidate]) -> list[ExplorationCandidate]:
    """G24C (★3a — investigation_report_deferred_queue_post_v031.md §5.3):
    viable-list SELECTION, not scoring. Guarantees the best-scoring
    catalog-native motor candidate survives truncation to MAX_VIABLE when
    Impl C generated at least one flyable one — closing the gap the
    investigation reproduced live (0 of 4 real catalog candidates reaching
    .viable for "aumentar_payload"/"mejorar_estabilidad" on a bound-motor
    project). ``_score_candidate`` is never called here and no candidate's
    ``.score`` is ever mutated — only which already-scored candidates make
    the cut, and their order, may change. G24-B (a scoring-formula
    preference) remains explicitly out of scope (contract §0/§5 non-goals).

    Locked algorithm (contract §2.2):
      1. sort by score desc (same key as before this function existed)
      2. no catalog-native candidate at all -> sorted[:MAX_VIABLE], no-op
      3. best-scoring catalog-native already in the top MAX_VIABLE -> no-op
      4. otherwise: keep the best MAX_VIABLE-1 non-catalog-native entries,
         append the best catalog-native as the reserved final slot
    """
    ranked = sorted(viable, key=lambda c: c.score, reverse=True)

    catalog_native = [c for c in ranked if _is_catalog_native_motor_candidate(c)]
    if not catalog_native:
        return ranked[:MAX_VIABLE]

    best_catalog = catalog_native[0]
    head = ranked[:MAX_VIABLE]
    # Identity, not equality (`in`/`==`): ExplorationCandidate is a pydantic
    # BaseModel, whose default __eq__ compares field values — two distinct
    # candidates could legitimately carry identical values. All membership/
    # exclusion checks here must track the exact same object every step.
    if any(c is best_catalog for c in head):
        return head

    others = [c for c in ranked if c is not best_catalog][: MAX_VIABLE - 1]
    return others + [best_catalog]


# ── Explorer ──────────────────────────────────────────────────────────────────

class DesignExplorer:
    """Explora el espacio de diseño para un objetivo dado.

    Es una operación de solo lectura: nunca modifica el estado del proyecto
    ni escribe en disco. Usa calculation_engine y simulator como funciones puras.
    """

    def __init__(
        self,
        calculation_engine: CalculationEngine,
        simulator: FeasibilitySimulator,
    ) -> None:
        self._engine = calculation_engine
        self._simulator = simulator

    def explore(self, project_state: Any, goal_key: str) -> ExplorationResult:
        """Explora variaciones del diseño para el objetivo indicado.

        Args:
            project_state: ProjectState con current_parameters como punto de partida.
            goal_key: una de las claves de EXPLORATION_GRIDS / COMPONENT_VARIATION_RULES.

        Returns:
            ExplorationResult con baseline, todos los candidatos evaluados y
            los viables (can_fly=True) ordenados por score descendente (top MAX_VIABLE).
        """
        # ── Baseline ────────────────────────────────────────────────────────
        # Motor OP Voltage Coherence IC (MOP-3, ★2 acotado): the params-only
        # baseline/grid use LIVE current_parameters directly, not a
        # re-normalized copy — apply_components_delta({}) re-derives motor
        # OP from the CURRENT battery on every call, which used to disagree
        # with live state whenever a stale, never-voltage-validated OP
        # resolution was still sitting in current_parameters (MOP-1/MOP-2
        # now keep that from happening going forward, but the baseline
        # itself must also stop re-deriving so explore never promises a
        # number "calcular" wouldn't already show for the same state).
        # normalized_state is still computed and still used, unchanged, as
        # the substrate for catalog/component-delta candidates below (§2.4
        # rule 2) — apply_components_delta(normalized_state, comp_delta).
        normalized_state = apply_components_delta(project_state, {})
        base_params = dict(project_state.current_parameters or {})
        goal_label = GOAL_LABELS.get(goal_key, goal_key)

        baseline_calc = self._engine.build(base_params)
        baseline_sim = self._simulator.evaluate(baseline_calc)
        baseline_score = _score_candidate(baseline_sim, baseline_calc, goal_key)

        candidates: list[ExplorationCandidate] = []
        viable: list[ExplorationCandidate] = []

        # ── Simple param-hash cache: avoid re-evaluating identical params ────
        _cache: dict[frozenset, tuple] = {}

        def _evaluate(params: dict[str, Any]) -> tuple:
            # Cache por hash de params derivados.
            # TODO (v2): esta es una aproximación — el cache asume que el mapping
            # componente→params es inyectivo. Si dos ComponentSpecs distintos
            # derivan los mismos current_parameters (ej. motor A + hélice X =
            # motor B + hélice Y = 10N de thrust), producirán la misma clave y
            # el segundo candidato reutilizará el resultado del primero.
            # Impacto actual: bajo (grids con valores muy distintos).
            # Solución futura: incluir identidad de componentes en la clave de cache.
            key = frozenset(params.items())
            if key not in _cache:
                calc_ = self._engine.build(params)
                sim_ = self._simulator.evaluate(calc_)
                _cache[key] = (calc_, sim_)
            return _cache[key]

        # ── Catalog motor grid (Impl C ★1/★2) ─────────────────────────────────
        # Runs before the params/component grids so its skip guard
        # (skip_synthetic_motor_component_grid) is known by the time the
        # existing component grid loop reaches its own motor entries.
        catalog_motor_note: str | None = None
        skip_synthetic_motor_component_grid = False
        if goal_key in _CATALOG_MOTOR_GOAL_KEYS:
            catalog_deltas, had_library_matches = _build_catalog_motor_candidates_for_goal(
                goal_key, project_state, normalized_state=normalized_state,
            )
            if had_library_matches:
                skip_synthetic_motor_component_grid = True
            else:
                catalog_motor_note = _CATALOG_MOTOR_FALLBACK_NOTE

            for comp_delta in catalog_deltas:
                try:
                    temp_state = apply_components_delta(normalized_state, comp_delta)
                    applied = dict(temp_state.current_parameters or {})
                    calc, sim = _evaluate(applied)
                except Exception:
                    continue

                score = _score_candidate(sim, calc, goal_key)
                improvement = round(score - baseline_score, 4)
                candidate = ExplorationCandidate(
                    params_delta={},
                    components_delta=comp_delta,
                    calculations=calc,
                    simulation=sim,
                    score=score,
                    label=_build_label_components(comp_delta),
                    improvement=improvement,
                )
                candidates.append(candidate)
                if sim.can_fly:
                    viable.append(candidate)

        # ── Params-only grid ─────────────────────────────────────────────────
        for delta in EXPLORATION_GRIDS.get(goal_key, []):
            # Guard: mixed deltas not supported yet (DA2 keeps them separate)
            applied = _apply_delta(base_params, delta)
            if applied is None:
                continue

            try:
                calc, sim = _evaluate(applied)
            except Exception:
                continue

            score = _score_candidate(sim, calc, goal_key)
            improvement = round(score - baseline_score, 4)
            candidate = ExplorationCandidate(
                params_delta=delta,
                components_delta={},
                calculations=calc,
                simulation=sim,
                score=score,
                label=_build_label(delta, applied),
                improvement=improvement,
            )
            candidates.append(candidate)
            if sim.can_fly:
                viable.append(candidate)

        # ── Component grid ───────────────────────────────────────────────────
        for comp_delta in _build_component_candidates_for_goal(goal_key):
            if not comp_delta:
                continue  # skip empty (vacío no aporta)
            if skip_synthetic_motor_component_grid and _is_synthetic_motor_component_delta(comp_delta):
                continue  # Impl C Strategy 3: real catalog motor candidates already generated

            try:
                temp_state = apply_components_delta(normalized_state, comp_delta)
                applied = dict(temp_state.current_parameters or {})
                calc, sim = _evaluate(applied)
            except Exception:
                continue

            score = _score_candidate(sim, calc, goal_key)
            improvement = round(score - baseline_score, 4)
            candidate = ExplorationCandidate(
                params_delta={},
                components_delta=comp_delta,
                calculations=calc,
                simulation=sim,
                score=score,
                label=_build_label_components(comp_delta),
                improvement=improvement,
            )
            candidates.append(candidate)
            if sim.can_fly:
                viable.append(candidate)

        return ExplorationResult(
            goal_key=goal_key,
            goal_label=goal_label,
            baseline_score=baseline_score,
            baseline_calculations=baseline_calc,
            baseline_simulation=baseline_sim,
            candidates=candidates,
            viable=_finalize_viable_list(viable),
            catalog_motor_note=catalog_motor_note,
        )
