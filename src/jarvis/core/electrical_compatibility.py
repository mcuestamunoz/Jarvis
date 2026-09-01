"""ERF-2 — Electrical Compatibility authority.

Pure facts, not gaps. Deterministic checks over ProjectState + the component
library only: ESC presence, ESC-vs-motor current rating, battery discharge
limit, motor<->propeller catalog pairing. No I/O, no LLM.

Authority model (design_erf2_dependency_hardening.md §3): this module owns
compatibility FACTS. It never decides what a "gap" is, never ranks, never
touches the Gap Registry — that projection is engineering_readiness.py's job
(★2). Forbidden imports: engineering_readiness, project_continuity,
orchestrator, LLM — this module must stay importable standalone, and
engineering_readiness imports THIS module, never the other way around.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from jarvis.core.project_closure import classify_component
from jarvis.knowledge.library import default_library

CheckOutcome = Literal[
    "defined", "missing",
    "compatible", "undersized",
    "within_limit", "exceeded",
    "mismatch",
    "unverifiable", "not_applicable",
]

# Aerial multirotor vehicle_type aliases — same family recognized elsewhere
# (system_architecture_catalog.VEHICLE_TYPE_ALIASES's "dron"/"uav" bucket),
# duplicated narrowly here rather than imported to keep this module's own
# import surface minimal (stdlib/schemas/library/project_closure only).
_AERIAL_MULTIROTOR_TYPES: frozenset[str] = frozenset({
    "dron", "drone", "quadcopter", "multirotor", "hexacopter", "octocopter", "uav",
})


@dataclass
class GapEvidence:
    """Shape-compatible with engineering_readiness.GapEvidence (source, fact)
    — a separate class, not imported, per the forbidden-imports rule above."""

    source: str
    fact: str


@dataclass
class CompatibilityFact:
    check: str
    outcome: CheckOutcome
    evidence: list[GapEvidence] = field(default_factory=list)


@dataclass
class CompatibilityResult:
    esc_presence: CheckOutcome
    esc_vs_motor: CheckOutcome
    battery_discharge: CheckOutcome
    prop_motor: CheckOutcome
    facts: list[CompatibilityFact]
    i_motor_a: float | None
    i_total_a: float | None
    esc_current_a: float | None
    battery_limit_a: float | None


def _components(project_state: Any) -> dict[str, Any]:
    dp = getattr(project_state, "design_properties", None)
    return getattr(dp, "components", None) or {}


# ── §5.0 — topology lock (★4) ────────────────────────────────────────────────


def _topology_determinable(project_state: Any) -> bool:
    """MVP: True when vehicle is aerial multirotor with motor_count >= 1."""
    params = getattr(project_state, "current_parameters", None) or {}
    vt = str(params.get("vehicle_type") or "").lower()
    if vt in _AERIAL_MULTIROTOR_TYPES:
        try:
            return int(params.get("motor_count") or 0) >= 1
        except (TypeError, ValueError):
            return False
    return False


# ── §5.1 — flight-evaluation prerequisites (for GAP-ESC-UNDEFINED) ─────────


def _flight_eval_prerequisites_met(project_state: Any) -> bool:
    components = _components(project_state)
    motors_t = classify_component("motors", components.get("motors"), project_state)
    battery_t = classify_component("battery", components.get("battery"), project_state)
    return motors_t in ("declared", "defined") and battery_t in ("declared", "defined")


# ── §5.3 — nominal pack voltage V_nom ────────────────────────────────────────


def _nominal_pack_voltage_v(project_state: Any) -> float | None:
    components = _components(project_state)
    battery = components.get("battery")
    catalog_ref = getattr(battery, "catalog_ref", None) if battery is not None else None
    if catalog_ref is not None and getattr(catalog_ref, "family", None) == "battery":
        try:
            spec = default_library.get_battery(catalog_ref.sku)
        except KeyError:
            spec = None
        if spec is not None:
            if spec.nominal_voltage is not None:
                return float(spec.nominal_voltage)
            if spec.cells is not None:
                return float(spec.cells) * 3.7

    params = getattr(project_state, "current_parameters", None) or {}
    cell_count = params.get("battery_cell_count")
    if cell_count is not None:
        try:
            return float(cell_count) * 3.7
        except (TypeError, ValueError):
            return None
    return None


# ── §5.2 — per-motor current I_motor ────────────────────────────────────────


def _per_motor_current_a(project_state: Any) -> float | None:
    components = _components(project_state)
    motors = components.get("motors")

    # P2-2 (Operating Point Bridge, ★ locked order): the resolved operating
    # point's real current (component_writers.set_motor_component, exact/
    # fallback only) is the most specific measured value for this exact
    # motor+propeller+voltage combo — preferred over the catalog peak
    # rating and the power/voltage estimate below, both of which are
    # coarser fallbacks for when no operating point was resolved.
    params = getattr(project_state, "current_parameters", None) or {}
    op_current_a = params.get("motor_op_current_a")
    if op_current_a is not None:
        try:
            return float(op_current_a)
        except (TypeError, ValueError):
            pass

    catalog_ref = getattr(motors, "catalog_ref", None) if motors is not None else None
    if catalog_ref is not None and getattr(catalog_ref, "family", None) == "motor":
        try:
            spec = default_library.get_motor(catalog_ref.sku)
        except KeyError:
            spec = None
        if spec is not None and spec.max_current_a is not None:
            return float(spec.max_current_a)

    props = getattr(motors, "properties", None) or {} if motors is not None else {}
    declared_current = props.get("max_current_a")
    if declared_current is not None and getattr(declared_current, "value", None) is not None:
        try:
            return float(declared_current.value)
        except (TypeError, ValueError):
            pass

    motor_power_w = params.get("motor_power_w")
    if motor_power_w is not None:
        v_nom = _nominal_pack_voltage_v(project_state)
        if v_nom:
            try:
                return float(motor_power_w) / v_nom
            except (TypeError, ValueError, ZeroDivisionError):
                return None
    return None


# ── §5.4 — ESC declared current I_esc ────────────────────────────────────────


def _esc_current_a(project_state: Any) -> float | None:
    components = _components(project_state)
    esc = components.get("esc")
    if classify_component("esc", esc, project_state) == "missing":
        return None
    props = getattr(esc, "properties", None) or {}
    current_prop = props.get("current_a")
    if current_prop is not None and getattr(current_prop, "value", None) is not None:
        try:
            return float(current_prop.value)
        except (TypeError, ValueError):
            pass
    catalog_ref = getattr(esc, "catalog_ref", None) if esc is not None else None
    if catalog_ref is not None and getattr(catalog_ref, "family", None) == "esc":
        try:
            spec = default_library.get_esc(catalog_ref.sku)
        except KeyError:
            spec = None
        if spec is not None and spec.continuous_current_a is not None:
            return float(spec.continuous_current_a)
    return None


# ── §5.5 — battery pack continuous limit I_pack_limit ───────────────────────


def _battery_pack_limit_a(project_state: Any) -> float | None:
    components = _components(project_state)
    battery = components.get("battery")
    catalog_ref = getattr(battery, "catalog_ref", None) if battery is not None else None
    if catalog_ref is None or getattr(catalog_ref, "family", None) != "battery":
        return None
    try:
        spec = default_library.get_battery(catalog_ref.sku)
    except KeyError:
        return None

    if spec.max_continuous_current_a is not None:
        return float(spec.max_continuous_current_a)
    if spec.c_rating is not None and spec.capacity_mah is not None:
        return float(spec.c_rating) * (float(spec.capacity_mah) / 1000.0)
    if spec.c_rating is not None and spec.energy_wh is not None:
        v_nom = spec.nominal_voltage
        if v_nom is None:
            v_nom = _nominal_pack_voltage_v(project_state)
        if v_nom:
            capacity_ah = float(spec.energy_wh) / v_nom
            return float(spec.c_rating) * capacity_ah
    return None


# ── §5.6 — total draw I_total (battery comparison only) ─────────────────────


def _total_current_a(i_motor: float | None, motor_count: Any) -> float | None:
    if i_motor is None or motor_count is None:
        return None
    try:
        return float(i_motor) * int(motor_count)
    except (TypeError, ValueError):
        return None


# ── §6.1 — esc_presence ──────────────────────────────────────────────────────


def _esc_presence(project_state: Any) -> CheckOutcome:
    components = _components(project_state)
    esc = components.get("esc")
    tier = classify_component("esc", esc, project_state)
    if tier in ("declared", "defined"):
        return "defined"
    if tier == "missing" and _flight_eval_prerequisites_met(project_state):
        return "missing"
    return "unverifiable"


# ── §6.2 — esc_vs_motor (★3, ★4) ─────────────────────────────────────────────


def _esc_vs_motor(
    project_state: Any,
    esc_presence: CheckOutcome,
    i_esc: float | None,
    i_motor: float | None,
) -> CheckOutcome:
    # Mutual exclusion with GAP-ESC-UNDEFINED (§6.0 table): esc missing ->
    # never "undersized", always "unverifiable" here.
    if esc_presence != "defined":
        return "unverifiable"
    if not _topology_determinable(project_state):
        return "unverifiable"
    if i_esc is None or i_motor is None:
        return "unverifiable"
    return "compatible" if i_esc >= i_motor else "undersized"


# ── §6.3 — battery_discharge ─────────────────────────────────────────────────


def _battery_discharge(
    project_state: Any, i_total: float | None, i_limit: float | None
) -> CheckOutcome:
    components = _components(project_state)
    battery = components.get("battery")
    battery_tier = classify_component("battery", battery, project_state)
    if battery_tier not in ("declared", "defined"):
        return "not_applicable"
    if i_limit is None or i_total is None:
        return "unverifiable"
    return "within_limit" if i_total <= i_limit else "exceeded"


# ── §6.4 — prop_motor (★10 — library.match_motor_propeller only) ───────────


def _prop_motor(project_state: Any) -> CheckOutcome:
    components = _components(project_state)
    motors = components.get("motors")
    propellers = components.get("propellers")
    motor_ref = getattr(motors, "catalog_ref", None) if motors is not None else None
    prop_ref = getattr(propellers, "catalog_ref", None) if propellers is not None else None
    if motor_ref is None or prop_ref is None:
        return "unverifiable"
    if getattr(motor_ref, "family", None) != "motor" or getattr(prop_ref, "family", None) != "propeller":
        return "unverifiable"
    try:
        matched = default_library.match_motor_propeller(motor_ref.sku, prop_ref.sku)
    except KeyError:
        return "unverifiable"
    return "compatible" if matched else "mismatch"


# ── public entry point ───────────────────────────────────────────────────────


def evaluate_electrical_compatibility(project_state: Any) -> CompatibilityResult:
    """Pure. No I/O. No LLM. Facts only — not gaps."""
    params = getattr(project_state, "current_parameters", None) or {}

    i_motor = _per_motor_current_a(project_state)
    i_esc = _esc_current_a(project_state)
    i_limit = _battery_pack_limit_a(project_state)
    i_total = _total_current_a(i_motor, params.get("motor_count"))

    esc_presence = _esc_presence(project_state)
    esc_vs_motor = _esc_vs_motor(project_state, esc_presence, i_esc, i_motor)
    battery_discharge = _battery_discharge(project_state, i_total, i_limit)
    prop_motor = _prop_motor(project_state)

    facts = [
        CompatibilityFact(
            check="esc_presence",
            outcome=esc_presence,
            evidence=[GapEvidence(source="project_closure.classify_component", fact=f"esc={esc_presence}")],
        ),
        CompatibilityFact(
            check="esc_vs_motor",
            outcome=esc_vs_motor,
            evidence=[
                GapEvidence(
                    source="electrical_compatibility._esc_vs_motor",
                    fact=f"I_esc={i_esc}, I_motor={i_motor}",
                )
            ],
        ),
        CompatibilityFact(
            check="battery_discharge",
            outcome=battery_discharge,
            evidence=[
                GapEvidence(
                    source="electrical_compatibility._battery_discharge",
                    fact=f"I_total={i_total}, I_pack_limit={i_limit}",
                )
            ],
        ),
        CompatibilityFact(
            check="prop_motor",
            outcome=prop_motor,
            evidence=[
                GapEvidence(
                    source="library.match_motor_propeller",
                    fact=f"prop_motor={prop_motor}",
                )
            ],
        ),
    ]

    return CompatibilityResult(
        esc_presence=esc_presence,
        esc_vs_motor=esc_vs_motor,
        battery_discharge=battery_discharge,
        prop_motor=prop_motor,
        facts=facts,
        i_motor_a=i_motor,
        i_total_a=i_total,
        esc_current_a=i_esc,
        battery_limit_a=i_limit,
    )
