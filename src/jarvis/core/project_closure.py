"""Project closure helpers — physical requirements, BOM/gaps, energy honesty (v1 usable).

Pure functions over ProjectState / latest_results. No I/O.
"""
from __future__ import annotations

from typing import Any


def derive_physical_requirements(project_state: Any) -> dict[str, Any]:
    """Derive explicit engineering requirements from constraints + last calc/sim."""
    constraints = getattr(project_state, "parsed_constraints", None) or {}
    if hasattr(constraints, "model_dump"):
        constraints = constraints.model_dump()
    latest = getattr(project_state, "latest_results", None) or {}
    calculations = latest.get("calculations") or {}
    simulation = latest.get("simulation") or {}

    req: dict[str, Any] = {}
    if constraints.get("autonomy_min") is not None:
        req["autonomy_target_min"] = float(constraints["autonomy_min"])
    if constraints.get("max_weight_kg") is not None:
        req["max_mass_kg"] = float(constraints["max_weight_kg"])

    thrust = calculations.get("required_thrust_n")
    if thrust is not None:
        req["thrust_needed_n"] = float(thrust)

    mass = calculations.get("total_mass_kg")
    if mass is not None:
        req["current_mass_kg"] = float(mass)

    autonomy = calculations.get("autonomy_min")
    if autonomy is None:
        autonomy = simulation.get("autonomy_min")
    if autonomy is not None:
        req["current_autonomy_min"] = float(autonomy)

    margin = simulation.get("safety_margin_ratio")
    if margin is not None:
        req["safety_margin_ratio"] = float(margin)

    motors = (getattr(project_state, "current_parameters", None) or {}).get("motor_count")
    if motors and thrust is not None:
        try:
            n = int(motors)
            if n > 0:
                req["thrust_per_motor_needed_n"] = float(thrust) / n
        except (TypeError, ValueError):
            pass

    return req


# FN-020: keys that count as measurable engineering signal (not name-only).
# Single source of truth for "measurable" — shared by classify_component and
# build_component_bom's entry metadata. Do not fork a second copy.
_MEASURABLE = frozenset({
    "thrust_n",
    "kv_rating",
    "power_w",
    "watts",
    "battery_capacity_wh",
    "mass_kg",
    "torque_nm",
    "diameter_in",
    "pitch_in",
    "motor_count",
    "propeller_diameter_in",
    "propeller_pitch_in",
    "capacity_wh",
    "gps_model",
    "sensor_type",
    "material",
    "model",
})


def _is_motor_count_gap(field: str) -> bool:
    fl = field.lower()
    return (
        "número de motores" in fl
        or "numero de motores" in fl
        or fl.strip() == "motor_count"
    )


def _measurable_and_missing_fields(
    key: str, spec: Any, project_state: Any
) -> tuple[bool, list[str]]:
    """Shared by classify_component and build_component_bom: whether ``spec``
    carries measurable engineering signal, and its missing_fields with the P2
    motor_count-in-current_parameters gap already filtered out (motor_count
    living in current_parameters is not a BOM gap)."""
    missing_fields = list(getattr(spec, "missing_fields", None) or [])
    props = getattr(spec, "properties", None) or {}
    params = getattr(project_state, "current_parameters", None) or {}

    count_from_params = False
    if key == "motors" and params.get("motor_count") is not None:
        missing_fields = [f for f in missing_fields if not _is_motor_count_gap(f)]
        count_from_params = True

    measurable = any(k in props for k in _MEASURABLE) or count_from_params
    return measurable, missing_fields


def component_presence_tier(spec: Any) -> str:
    """'stub' if ``spec`` is absent/completeness is 'low' (or unset), else
    'present'.

    FN-020: single source of truth for "is this component present" for
    architecture-progress purposes (orchestrator._component_is_low /
    _block_progress_status), and the first branch of classify_component
    (BOM/Continuity). Presence here deliberately does NOT require measurable
    data — that finer distinction is classify_component's declared/defined
    split, which architecture progress does not need (same threshold as
    before FN-020, just named and shared explicitly now).
    """
    if spec is None:
        return "stub"
    completeness = getattr(spec, "completeness", "low") or "low"
    return "stub" if completeness == "low" else "present"


def classify_component(key: str, spec: Any, project_state: Any) -> str:
    """FN-020: single classification of component presence/completeness,
    consumed by BOTH architecture progress (via component_presence_tier) and
    BOM/Continuity reporting — eliminates the prior dual-threshold
    contradiction where a 'medium' completeness component (e.g. a battery
    with capacity_wh declared) counted as architecture-present but as a BOM/
    Continuity gap at the same time.

    Returns one of:
      "missing"  — key not in design_properties.components
      "stub"     — present but completeness is 'low' (or unset)
      "declared" — non-low, has measurable signal (or is non-low name-only —
                   same presence threshold as architecture), but not a
                   strict close
      "defined"  — completeness 'high', measurable, no outstanding
                   missing_fields (strict close)

    Pure over ProjectState-shaped objects (duck-typed via getattr). No I/O.
    """
    if spec is None:
        return "missing"
    if component_presence_tier(spec) == "stub":
        return "stub"

    completeness = getattr(spec, "completeness", "low") or "low"
    measurable, missing_fields = _measurable_and_missing_fields(key, spec, project_state)
    if completeness == "high" and measurable and not missing_fields:
        return "defined"
    return "declared"


def build_component_bom(project_state: Any) -> dict[str, Any]:
    """Light BOM: defined / incomplete / missing / declarative-only components.

    FN-020: bucket routing is driven entirely by classify_component (single
    classifier, shared with architecture progress) — "incomplete" now means
    genuinely low/stub (a real acquisition target), never a merely-medium-but-
    measurable component (that lands in "declarative", matching what
    architecture progress already treats as present).
    """
    from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS

    dp = getattr(project_state, "design_properties", None)
    components = getattr(dp, "components", None) or {}
    blocks = list(getattr(dp, "system_blocks", None) or [])
    if not blocks:
        expected_keys = list(components.keys())
    else:
        expected_keys: list[str] = []
        for block in blocks:
            for key in BLOCK_TO_COMPONENTS.get(block, []):
                if key not in expected_keys:
                    expected_keys.append(key)

    defined: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    missing: list[str] = []
    declarative: list[dict[str, Any]] = []

    def _entry(key: str, spec: Any) -> dict[str, Any]:
        _, missing_fields = _measurable_and_missing_fields(key, spec, project_state)
        return {
            "key": key,
            "name": getattr(spec, "name", key),
            "completeness": getattr(spec, "completeness", "low") or "low",
            "missing_fields": missing_fields,
            "component_type": getattr(spec, "component_type", None),
        }

    def _classify(key: str, spec: Any) -> None:
        tier = classify_component(key, spec, project_state)
        entry = _entry(key, spec)
        if tier == "stub":
            incomplete.append(entry)
        elif tier == "defined":
            defined.append(entry)
        else:  # "declared"
            declarative.append(entry)

    for key in expected_keys:
        spec = components.get(key)
        if spec is None:
            missing.append(key)
            continue
        _classify(key, spec)

    # Extra components not in architecture blocks — same classification rules
    for key, spec in components.items():
        if key in expected_keys:
            continue
        _classify(key, spec)

    return {
        "defined": defined,
        "incomplete": incomplete,
        "missing": missing,
        "declarative": declarative,
    }


def energy_model_honesty_note(project_state: Any) -> str | None:
    """When autonomy is a hard constraint, disclose the simplified energy model."""
    constraints = getattr(project_state, "parsed_constraints", None) or {}
    if hasattr(constraints, "model_dump"):
        constraints = constraints.model_dump()
    if constraints.get("autonomy_min") is None:
        return None
    return (
        "Modelo energético simplificado: autonomía ≈ (Wh / W) × 60 — "
        "sin curva de descarga ni C-rating. Úsalo como orientación, no como certificación."
    )


def format_requirements_lines(requirements: dict[str, Any]) -> list[str]:
    if not requirements:
        return []
    labels = {
        "thrust_needed_n": "Empuje requerido",
        "thrust_per_motor_needed_n": "Empuje por motor (est.)",
        "autonomy_target_min": "Autonomía objetivo",
        "current_autonomy_min": "Autonomía actual",
        "max_mass_kg": "Masa máxima",
        "current_mass_kg": "Masa actual",
        "safety_margin_ratio": "Margen de seguridad",
    }
    units = {
        "thrust_needed_n": "N",
        "thrust_per_motor_needed_n": "N",
        "autonomy_target_min": "min",
        "current_autonomy_min": "min",
        "max_mass_kg": "kg",
        "current_mass_kg": "kg",
        "safety_margin_ratio": "",
    }
    lines: list[str] = []
    for key, label in labels.items():
        if key not in requirements:
            continue
        val = requirements[key]
        unit = units.get(key, "")
        if isinstance(val, float):
            text = f"{val:.2f}".rstrip("0").rstrip(".")
        else:
            text = str(val)
        lines.append(f"{label}: {text}{(' ' + unit) if unit else ''}")
    return lines


def format_bom_lines(bom: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for entry in bom.get("defined") or []:
        lines.append(f"✓ {entry['key']}: {entry.get('name') or entry['key']} ({entry.get('completeness')})")
    for entry in bom.get("incomplete") or []:
        miss = ", ".join(entry.get("missing_fields") or []) or "incompleto"
        lines.append(f"… {entry['key']}: {entry.get('name') or entry['key']} — falta {miss}")
    for entry in bom.get("declarative") or []:
        lines.append(f"◇ {entry['key']}: {entry.get('name') or entry['key']} (declarativo)")
    for key in bom.get("missing") or []:
        lines.append(f"✗ {key}: no definido")
    return lines
