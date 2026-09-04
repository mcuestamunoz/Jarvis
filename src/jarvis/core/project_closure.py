"""Project closure helpers — physical requirements, BOM/gaps, energy honesty (v1 usable).

Pure functions over ProjectState / latest_results. No I/O.
"""
from __future__ import annotations

import json
from typing import Any


def catalog_gap_covered_by_declared_thrust(
    project_state: Any, sim_status: str, req: dict[str, Any]
) -> bool:
    """G9-B: is a motor catalog gap a BOM identity note, not a physics blocker?

    True only when the simulation PASSes AND the user already declared a
    per-motor thrust that covers the computed floor — in that case a catalog
    gap (no SKU for this KV/prop/thrust combo) is honest but not actionable.
    Any other case (no PASS, no declared thrust, or declared thrust under the
    floor) returns False — this is a `>=` comparison, never a blanket
    suppression on ``sim_status == "pass"`` alone.

    ERF-1 (engineering_readiness) authority home for this predicate —
    formerly private to project_continuity, moved here so a non-Continuity
    consumer (Readiness) can use it without importing project_continuity
    (circularity forbidden by design). project_continuity keeps its own copy
    until Slice 4 switches it to import this one.
    """
    if sim_status != "pass":
        return False
    declared = (getattr(project_state, "current_parameters", None) or {}).get(
        "per_motor_max_thrust_n"
    )
    if declared is None:
        return False
    needed = req.get("thrust_per_motor_needed_n")
    if needed is None:
        return False
    try:
        return float(declared) >= float(needed)
    except (TypeError, ValueError):
        return False


def catalog_bound_motor_covers_power_w(design_properties: Any) -> bool:
    """A catalog SKU on motors is identity enough for energy-block progress.

    Verified motors such as ``emax_rs2205s_2300`` honestly have no nameplate
    ``max_watts`` — ``set_motor_component`` therefore omits ``motor_power_w``.
    Continuity and the energy composite must not keep asking the user to
    invent W, or to re-pick the same SKU, while propellers/battery/frame
    are still the real gaps.

    CLI feasibility vs readiness semantics IC (§2.3): accepts either the
    live ``DesignProperties`` object (``orchestrator.py``'s own callers) or
    the ``.model_dump()``-shaped dict ``ReasoningLayer.build()`` already
    receives on ``context["design_properties"]`` — same predicate, two
    equivalent input shapes, no second helper.
    """
    if design_properties is None:
        return False
    if isinstance(design_properties, dict):
        components = design_properties.get("components") or {}
        motors = components.get("motors") if isinstance(components, dict) else None
        ref = motors.get("catalog_ref") if isinstance(motors, dict) else None
        family = ref.get("family") if isinstance(ref, dict) else None
    else:
        components = getattr(design_properties, "components", None) or {}
        motors = components.get("motors")
        ref = getattr(motors, "catalog_ref", None)
        family = getattr(ref, "family", None)
    return ref is not None and family == "motor"


def catalog_bound_motor_lacks_nameplate_watts(design_properties: Any) -> bool:
    """T1 (implementation_contract_cli_catalog_assist_t1.md §2.6) — the
    "este motor de catálogo no declara vatios" CTA's own predicate.

    Deliberately separate from ``catalog_bound_motor_covers_power_w``, which
    is identity-only (any catalog-bound motor reads as "done" for
    architecture-progress/energy-nag purposes, regardless of whether that
    SKU declares watts). This one answers a narrower, different question:
    does the *specific bound SKU* actually lack a nameplate ``max_watts`` —
    so the CTA is never shown for a SKU (like ``sunnysky_r2305_2500``, 220W)
    that does declare watts, while a genuinely watts-less SKU (like
    ``emax_rs2205s_2300``) still gets it. True only when identity-bound
    *and* the library lookup confirms ``max_watts is None``; a SKU missing
    from the library returns False rather than raising.
    """
    if design_properties is None:
        return False
    if isinstance(design_properties, dict):
        components = design_properties.get("components") or {}
        motors = components.get("motors") if isinstance(components, dict) else None
        ref = motors.get("catalog_ref") if isinstance(motors, dict) else None
        family = ref.get("family") if isinstance(ref, dict) else None
        sku = ref.get("sku") if isinstance(ref, dict) else None
    else:
        components = getattr(design_properties, "components", None) or {}
        motors = components.get("motors")
        ref = getattr(motors, "catalog_ref", None)
        family = getattr(ref, "family", None)
        sku = getattr(ref, "sku", None)
    if ref is None or family != "motor" or not sku:
        return False

    from jarvis.knowledge.library import default_library

    if not default_library.has_motor(sku):
        return False
    return default_library.get_motor(sku).max_watts is None


def propeller_diameter_in(project_state: Any) -> float | None:
    """Structure A (implementation_contract_structure_a.md §2.2): the known
    propeller diameter in inches, or None when unknown.

    Priority order (locked, single source per rank — never averages/guesses):
      1. components["propellers"].properties["diameter_in"] (numeric).
      2. current_parameters["propeller_diameter_in"] (set_propeller_component
         already bridges 1 -> 2; this covers a freeform/numeric-only project
         that never had a propeller component at all).
      3. A catalog-bound propeller SKU's own declared diameter_in.

    Never parses millimetres, never invents from a SKU name.
    """
    design_properties = getattr(project_state, "design_properties", None)
    components = getattr(design_properties, "components", None) or {}
    propellers = components.get("propellers")

    props = getattr(propellers, "properties", None) or {}
    diameter_prop = props.get("diameter_in")
    if diameter_prop is not None and diameter_prop.value is not None:
        try:
            return float(diameter_prop.value)
        except (TypeError, ValueError):
            pass

    params = getattr(project_state, "current_parameters", None) or {}
    param_val = params.get("propeller_diameter_in")
    if param_val is not None:
        try:
            return float(param_val)
        except (TypeError, ValueError):
            pass

    catalog_ref = getattr(propellers, "catalog_ref", None)
    if catalog_ref is not None and getattr(catalog_ref, "family", None) == "propeller":
        sku = getattr(catalog_ref, "sku", None)
        if sku:
            from jarvis.knowledge.library import default_library

            try:
                spec = default_library.get_propeller(sku)
            except KeyError:
                return None
            return float(spec.diameter_in)

    return None


def frame_class_compatibility_state(project_state: Any) -> str:
    """Structure A (§2.2): class-compatibility screening state — LEVEL A, not
    a geometric fit proof.

    Returns one of:
      "not_required"       — no known propeller diameter; size not required.
      "missing"             — D known, frame declares no size_class_inch.
      "class_compatible"    — D known, class set, D <= size_class_inch.
      "class_incompatible"  — D known, class set, D > size_class_inch.

    Single shared predicate — both ``_block_progress_status`` copies and the
    ERF-2 gap builders call this so architecture progress and the Gap
    Registry can never disagree on the state. Never copies size_class_inch
    from the propeller, never adds slack, never touches thrust/power/RPM/Ct.
    """
    diameter_in = propeller_diameter_in(project_state)
    if diameter_in is None:
        return "not_required"

    design_properties = getattr(project_state, "design_properties", None)
    components = getattr(design_properties, "components", None) or {}
    frame = components.get("frame")
    props = getattr(frame, "properties", None) or {}
    size_prop = props.get("size_class_inch")
    if size_prop is None or size_prop.value is None:
        return "missing"

    try:
        size_class_inch = float(size_prop.value)
    except (TypeError, ValueError):
        return "missing"

    return "class_compatible" if diameter_in <= size_class_inch else "class_incompatible"


def frame_size_blocks_structure_complete(design_properties: Any, params: dict[str, Any]) -> bool:
    """True when the frame's class-compatibility state alone must prevent the
    ``"structure"`` architecture block from reading ``"complete"`` — i.e.
    ``frame_class_compatibility_state`` is ``"missing"`` or
    ``"class_incompatible"`` — even though its components are otherwise
    non-stub (mass + material present).

    Thin duck-typed adapter: ``_block_progress_status`` (both the
    ``orchestrator.py`` and ``engineering_readiness.py`` copies) only carries
    ``design_properties``/``params`` separately, not a full ``project_state``,
    so this wraps them into the shape ``frame_class_compatibility_state``
    expects — single shared predicate, no duplicated size-required logic
    between architecture progress and the Gap Registry
    (implementation_contract_structure_a.md §2.2).
    """
    from types import SimpleNamespace

    shim = SimpleNamespace(design_properties=design_properties, current_parameters=params)
    return frame_class_compatibility_state(shim) in ("missing", "class_incompatible")


def frame_next_missing_datum(project_state: Any) -> str | None:
    """CLI fail-routing coherence (implementation_contract_cli_fail_routing_
    coherence.md §2.1): the single next thing the frame needs, composing the
    existing mass/material persistence and ``frame_class_compatibility_state``
    — never re-deriving completeness itself (``_frame_completeness`` in
    ``domains.aerial`` stays the mass+material authority for
    ``ComponentSpec.completeness``; this is a *routing* view, not a second
    completeness definition).

    Returns one of:
      "mass"               — frame has no declared mass_kg yet.
      "material"            — mass known, no declared material yet.
      "size_class"           — mass+material known, D known, no size_class_inch.
      "class_incompatible"   — mass+material known, D known, class set, D > class.
      None                   — nothing left to ask (includes D unknown: class
                                screening is not required, per Structure A §6).

    Order: mass/material first (a class the user can't act on yet is useless
    without a frame to put it on), then size class, then incompatibility.
    """
    design_properties = getattr(project_state, "design_properties", None)
    components = getattr(design_properties, "components", None) or {}
    frame = components.get("frame")
    props = getattr(frame, "properties", None) or {}

    mass_prop = props.get("mass_kg")
    if mass_prop is None or mass_prop.value is None:
        return "mass"
    material_prop = props.get("material")
    if material_prop is None or material_prop.value is None:
        return "material"

    state = frame_class_compatibility_state(project_state)
    if state == "missing":
        return "size_class"
    if state == "class_incompatible":
        return "class_incompatible"
    return None


def frame_next_missing_question(project_state: Any) -> str | None:
    """Locked copy for ``frame_next_missing_datum`` — single source shared by
    Acquisition Brief and the orchestrator's frame prompts, so the two never
    diverge on what to ask next for the frame (implementation_contract_cli_
    fail_routing_coherence.md §2.1/§2.3). LEVEL A / CLASS-BASED throughout —
    never "cabe"/"no cabe", never VERIFIED.
    """
    datum = frame_next_missing_datum(project_state)
    if datum is None:
        return None

    if datum == "size_class":
        return (
            "El frame ya tiene material y masa. Declara la clase en pulgadas "
            "(ej. 'frame 5 pulgadas'). El empuje lo da la hélice, no el frame."
        )

    if datum == "class_incompatible":
        diameter_in = propeller_diameter_in(project_state)
        design_properties = getattr(project_state, "design_properties", None)
        components = getattr(design_properties, "components", None) or {}
        frame = components.get("frame")
        props = getattr(frame, "properties", None) or {}
        size_prop = props.get("size_class_inch")
        size_class_inch = size_prop.value if size_prop is not None else None
        d_bit = f"{float(diameter_in):g}" if diameter_in is not None else "declarada"
        c_bit = f"{float(size_class_inch):g}" if size_class_inch is not None else "declarada"
        return (
            f"La hélice ({d_bit} in) supera la clase de frame declarada ({c_bit} in) "
            "— compatibilidad de clase nivel A, no verificada. Declara una clase de "
            "frame mayor (ej. 'frame 6 pulgadas') o cambia de hélice."
        )

    # datum in ("mass", "material") — one combined prompt regardless of which
    # single field is missing, per §2.1.
    if propeller_diameter_in(project_state) is not None:
        return (
            "Describe el frame del dron (material, masa y clase en pulgadas). "
            "Ej: 'fibra de carbono 450g 5 pulgadas'"
        )
    return "Describe el frame del dron (material y masa). Ej: 'fibra de carbono 450g'"


def param_present_for_architecture(
    param: str, params: dict[str, Any], design_properties: Any
) -> bool:
    """Architecture-progress view of a required param (not a calc input)."""
    if (params or {}).get(param) is not None:
        return True
    if param == "motor_power_w":
        return catalog_bound_motor_covers_power_w(design_properties)
    return False


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


def _bom_catalog_ref_dict(spec: Any) -> dict[str, str] | None:
    """Impl D ★2: plain-dict projection of spec.catalog_ref, or None.

    No new schema — a straight passthrough of the existing CatalogRef.
    """
    catalog_ref = getattr(spec, "catalog_ref", None)
    if catalog_ref is None:
        return None
    if hasattr(catalog_ref, "model_dump"):
        return catalog_ref.model_dump()
    return {"family": catalog_ref.family, "sku": catalog_ref.sku}


def _bom_sku_resolved(catalog_ref: dict[str, str] | None) -> bool:
    """Impl D ★2/§2.2 (non-negotiable): computed from ``catalog_ref`` +
    a live library re-check — NEVER from ``.name`` shape. This is the one
    rule that closes Scenario D (frankenstein): after G5's
    ``invalidate_diverged_catalog_refs`` clears ``catalog_ref`` but leaves
    ``.name`` as the old SKU string, this function sees ``catalog_ref is
    None`` and returns False regardless of what ``.name`` looks like — the
    caller never even passes ``.name`` in here to be tempted by it. Scenario
    C (SKU removed from the library after binding) also resolves False, via
    the same ``has_motor``/``has_battery``/``has_propeller`` re-check G9-A
    already uses elsewhere — no second catalog reader.

    IC 3 (★6): propeller branch added post-v0.3.0 propeller-bind UX
    (`checkpoint-propeller-catalog-bind`), which shipped after this
    function's original ★2 comment ("no v1 resolve path for other
    families") was written — nothing updated it when propeller binding went
    live, so a genuinely bound, resolving propeller displayed the
    "SKU sin resolver" honest-uncertainty marker as if it were unresolved
    (investigation_report_project_closure_assembly_ready.md §6.1). Display-
    only: `sku_resolved` is never read by gap builders or subsystem verdict
    derivation (confirmed in the Impl D investigation and unchanged by this
    fix) — only `format_bom_lines`/`_bom_identity_suffix` consume it.
    """
    if catalog_ref is None:
        return False
    sku = catalog_ref.get("sku")
    if not sku:
        return False
    from jarvis.knowledge.library import default_library

    family = catalog_ref.get("family")
    if family == "motor":
        return default_library.has_motor(sku)
    if family == "battery":
        return default_library.has_battery(sku)
    if family == "propeller":
        return default_library.has_propeller(sku)
    if family == "esc":
        return default_library.has_esc(sku)
    return False  # no v1 resolve path for other families (★2)


def _bom_quantity(key: str, spec: Any, project_state: Any) -> int | None:
    """Impl D §2.3: minimal, non-invented per-family quantity.

    - motors / propellers: ``current_parameters["motor_count"]`` (the same
      single source of truth ``set_motor_component``'s own Bug78/FN-007
      fallback already uses), falling back to the motors component's own
      ``motor_count`` property when the params-side value is absent.
      Propellers reuses this number as a documented *convention* (1
      propeller per motor for the aerial domain) — no independent
      ``propeller_count`` field exists anywhere in this codebase.
    - esc: ``None`` — honest unknown. A 4-in-1 ESC vs. one-per-motor is a
      real design choice this codebase has no data to distinguish; guessing
      would violate "never invent quantities".
    - everything else (battery, frame, flight_controller, sensors, ...):
      ``1`` — every other family this codebase tracks is a singleton; no
      count field is ever collected for them, so 1 is not an invention.
    """
    if key in ("motors", "propellers"):
        params = getattr(project_state, "current_parameters", None) or {}
        count = params.get("motor_count")
        if count is None:
            dp = getattr(project_state, "design_properties", None)
            components = getattr(dp, "components", None) or {}
            motors_spec = components.get("motors")
            count_prop = (getattr(motors_spec, "properties", None) or {}).get("motor_count")
            count = count_prop.value if count_prop is not None else None
        if count is None:
            return None
        try:
            return int(count)
        except (TypeError, ValueError):
            return None
    if key == "esc":
        return None
    return 1


def build_component_bom(project_state: Any) -> dict[str, Any]:
    """Light BOM: defined / incomplete / missing / declarative-only components.

    FN-020: bucket routing is driven entirely by classify_component (single
    classifier, shared with architecture progress) — "incomplete" now means
    genuinely low/stub (a real acquisition target), never a merely-medium-but-
    measurable component (that lands in "declarative", matching what
    architecture progress already treats as present).

    Impl D (★1/★2): each entry additionally carries ``catalog_ref``,
    ``sku_resolved``, and ``quantity`` — the BOM projection now consumes SKU
    identity instead of only completeness buckets. Pure additive fields; no
    existing key removed or renamed (``name`` stays ``name`` — not
    ``display_name``).
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
        catalog_ref = _bom_catalog_ref_dict(spec)
        return {
            "key": key,
            "name": getattr(spec, "name", key),
            "completeness": getattr(spec, "completeness", "low") or "low",
            "missing_fields": missing_fields,
            "component_type": getattr(spec, "component_type", None),
            "catalog_ref": catalog_ref,
            "sku_resolved": _bom_sku_resolved(catalog_ref),
            "quantity": _bom_quantity(key, spec, project_state),
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
    """When autonomy is a hard constraint, disclose the simplified energy model.

    CLI feasibility vs readiness semantics IC (§2.5): the L0 ``(Wh/W)×60``
    sentence presumes a number exists to interpret — it must not fire when
    no autonomy was actually calculated (``latest_results.calculations.
    autonomy_min`` absent), since that reads as "here is the model behind
    your result" when there is no result. That case gets its own honest
    sentence instead.
    """
    constraints = getattr(project_state, "parsed_constraints", None) or {}
    if hasattr(constraints, "model_dump"):
        constraints = constraints.model_dump()
    if constraints.get("autonomy_min") is None:
        return None
    calculations = (getattr(project_state, "latest_results", None) or {}).get("calculations") or {}
    if calculations.get("autonomy_min") is None:
        return (
            "Autonomía no calculada: no hay potencia de hover usable ni W de placa. "
            "No inventes motor_power_w."
        )
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


def _bom_identity_suffix(entry: dict[str, Any]) -> str:
    """Impl D §3.1: ``[sku]`` only when actually resolved. A bound-but-
    unresolved SKU (Scenario C) gets an honest "sin resolver" marker instead
    of silently looking identical to a resolved one; an unbound/frankenstein
    entry (``catalog_ref is None``) gets neither — never inferred from
    ``.name`` shape."""
    catalog_ref = entry.get("catalog_ref")
    if catalog_ref is None:
        return ""
    if entry.get("sku_resolved"):
        return f" [{catalog_ref.get('sku')}]"
    return " (SKU sin resolver)"


def _bom_quantity_suffix(entry: dict[str, Any]) -> str:
    """Impl D §2.3: ``qty=N`` only when a real quantity is known — never for
    ESC (honest unknown, quantity is None)."""
    qty = entry.get("quantity")
    return "" if qty is None else f" qty={qty}"


def format_bom_lines(bom: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for entry in bom.get("defined") or []:
        lines.append(
            f"✓ {entry['key']}: {entry.get('name') or entry['key']}"
            f"{_bom_identity_suffix(entry)}{_bom_quantity_suffix(entry)} ({entry.get('completeness')})"
        )
    for entry in bom.get("incomplete") or []:
        miss = ", ".join(entry.get("missing_fields") or []) or "incompleto"
        lines.append(
            f"… {entry['key']}: {entry.get('name') or entry['key']}"
            f"{_bom_identity_suffix(entry)}{_bom_quantity_suffix(entry)} — falta {miss}"
        )
    for entry in bom.get("declarative") or []:
        lines.append(
            f"◇ {entry['key']}: {entry.get('name') or entry['key']}"
            f"{_bom_identity_suffix(entry)}{_bom_quantity_suffix(entry)} (declarativo)"
        )
    for key in bom.get("missing") or []:
        lines.append(f"✗ {key}: no definido")
    return lines


def derive_prop_energy_block_closure(
    project_state: Any, *, readiness: Any | None = None
) -> dict[str, Any]:
    """Block Closure B-PROP-ENERGY IC §3 — derivable rollup over EXISTING
    signals (readiness + electrical compatibility + sim + catalog identity).
    Pure derivation, same discipline as this module's other helpers: does
    not mutate state, does not touch ``ASSEMBLY_READY``'s own 9-way
    conjunction (``engineering_readiness._derive_overall`` untouched, not
    even imported here except at call time), does not add new engineering
    physics — every fact below is read from ``build_engineering_readiness``/
    ``evaluate_electrical_compatibility``, both already pure.

    Answers a DIFFERENT question than ``ASSEMBLY_READY``
    (investigation_report_post_v034_block_closure.md Finding B-3): is the
    propulsion/energy/electronics stack specifically done, independent of
    frame/control/requirements/architecture/catalog/bom subsystems. A
    project can be block-``closed`` and simultaneously ``NOT_ASSEMBLY_READY``
    — that dual is the point, not a bug.

    ``SubsystemEvidence.validated`` (the shared ``ctx.sim_status=="pass"``
    boolean, Finding B-2) is deliberately NOT read as ESC proof here — the
    real, per-fact ``electrical_compatibility`` checks (``esc_vs_motor``,
    ``battery_discharge``, ``prop_motor``, ``esc_presence``) are what gate
    ``closed``, exactly as the investigation found they are the one place a
    real, block-specific physics fact already exists in this codebase.

    ``readiness`` (keyword, optional): pass an already-computed
    ``EngineeringReadinessResult`` when the caller has one (e.g.
    ``build_startup_context``, which already builds it once for the
    ``readiness`` ctx key) — G9-A's "single catalog resolve per turn"
    regression guard means a second, independent
    ``build_engineering_readiness`` call here would double-invoke
    ``resolve_motor_catalog_surface``. ``None`` (every direct/test caller,
    e.g. ``derive_prop_energy_block_closure(project_state)`` alone) computes
    it fresh — this function stays callable with just ``project_state``.
    """
    from jarvis.core.electrical_compatibility import evaluate_electrical_compatibility

    if readiness is None:
        from jarvis.core.engineering_readiness import build_engineering_readiness

        readiness = build_engineering_readiness(project_state)
    compat = evaluate_electrical_compatibility(project_state)
    sim = (getattr(project_state, "latest_results", None) or {}).get("simulation") or {}
    components = getattr(getattr(project_state, "design_properties", None), "components", None) or {}

    def _verdict(key: str) -> str | None:
        entry = readiness.subsystems.get(key)
        return entry.verdict if entry is not None else None

    checks: list[tuple[bool, str]] = [
        (_verdict("propulsion") == "PASS", "propulsion_not_pass"),
        (_verdict("energy") == "PASS", "energy_not_pass"),
        (_verdict("electronics") == "PASS", "electronics_not_pass"),
        (compat.battery_discharge == "within_limit", "battery_discharge_exceeded"),
        (compat.esc_vs_motor == "compatible", "esc_vs_motor_incompatible"),
        (compat.prop_motor == "compatible", "prop_motor_incompatible"),
        (compat.esc_presence == "defined", "esc_not_defined"),
        (sim.get("status") == "pass", "sim_not_pass"),
    ]
    for key, family in (("motors", "motor"), ("propellers", "propeller"), ("battery", "battery")):
        spec = components.get(key)
        ref = getattr(spec, "catalog_ref", None)
        ok = ref is not None and getattr(ref, "family", None) == family
        checks.append((ok, f"{key}_not_catalog_bound"))

    reasons = [reason for ok, reason in checks if not ok]
    status = "closed" if not reasons else "not_closed"

    # ★6 evidence tier — descriptive only, never gates `status` (§3.3: a
    # fallback-tier OP can still be `closed`; a manufacturer_test-tier OP
    # with a failed check above is still `not_closed`).
    resolution_type: str | None = None
    source_type: str | None = None
    propulsion_resolution_raw = (getattr(project_state, "current_parameters", None) or {}).get(
        "propulsion_resolution"
    )
    if propulsion_resolution_raw:
        try:
            parsed = json.loads(propulsion_resolution_raw)
            resolution_type = parsed.get("resolution_type")
            source_type = parsed.get("source_type")
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    if resolution_type == "exact_operating_point" and source_type == "manufacturer_test":
        evidence_tier = "manufacturer_test"
    elif resolution_type == "fallback_operating_point":
        evidence_tier = "fallback"
    elif resolution_type == "legacy_estimate":
        evidence_tier = "legacy_estimate"
    else:
        evidence_tier = "none"

    return {
        "block_id": "B-PROP-ENERGY",
        "status": status,
        "evidence_tier": evidence_tier,
        "reasons": reasons,
        "facts": {
            "propulsion_verdict": _verdict("propulsion"),
            "energy_verdict": _verdict("energy"),
            "electronics_verdict": _verdict("electronics"),
            "battery_discharge": compat.battery_discharge,
            "esc_vs_motor": compat.esc_vs_motor,
            "prop_motor": compat.prop_motor,
            "esc_presence": compat.esc_presence,
            "sim_status": sim.get("status"),
            "resolution_type": resolution_type,
            "source_type": source_type,
        },
    }
