"""Standalone component writer functions.

Cada función es el único punto de escritura para su componente.
Son funciones puras (sin estado externo): reciben un ProjectState y devuelven
un ProjectState nuevo sin persistir — el caller es responsable de guardar.

Extraídas de JarvisOrchestrator en Fase 7 prerequisito para desbloquear DA2:
el DesignExplorer necesita llamar a estos writers sin crear un import circular
(orchestrator → design_explorer → orchestrator).

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              MIRRORED PARAM CONTRACT (ley del sistema)                 ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║ Todo writer que gestione un componente físico DEBE:                    ║
# ║                                                                        ║
# ║  (1) Escribir en design_properties.components[key]   ← canónico       ║
# ║      Fuente única de verdad del componente.                            ║
# ║                                                                        ║
# ║  (2) Escribir en current_parameters[param]           ← bridge físico  ║
# ║      Mirror para que calculation_engine consuma el valor.              ║
# ║                                                                        ║
# ║ Si (2) falta:                                                          ║
# ║  - updated_params NO tendrá el valor                                   ║
# ║  - el engine calculará con datos desactualizados                       ║
# ║  - NO se lanzará ningún error (fallo silencioso)                       ║
# ║                                                                        ║
# ║ Flujo garantizado:                                                     ║
# ║   ComponentSpec → writer → current_parameters → calculation_engine    ║
# ║                                                                        ║
# ║ Enforcement:                                                           ║
# ║  - test_d4_param_gatekeeper.py verifica ambos lados tras save_state   ║
# ║  - Cualquier nuevo mirrored param DEBE añadir su test de contrato      ║
# ║  - Definición canónica: COMPONENT_MIRRORED_PARAMS en                  ║
# ║    core/system_architecture_catalog.py                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
from typing import Any

from jarvis.domains.aerial import _frame_completeness, _structure_part_completeness
from jarvis.knowledge.library import _OP_VOLTAGE_EPSILON_V, default_library, resolve_operating_point
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.tools.electricity import estimate_battery_mass_kg


def set_frame_material(
    project_state: Any,
    mass_kg: float | None,
    material: str | None,
    size_class_inch: float | None = None,
    *,
    catalog_ref: CatalogRef | None = None,
    component_name: str | None = None,
) -> Any:
    """Único punto de escritura para propiedades del frame.

    Escribe en dos lugares de forma atómica:
      1. components["frame"].properties (canónico — fuente única de verdad)
      2. current_parameters["structure_mass_override_kg"] (bypass física existente)

    Fase 3 completada: el mirror legacy structure.material fue eliminado.
    La lectura canónica ahora se hace via get_frame_material() en design_utils.py.

    Structure A (implementation_contract_structure_a.md §2.2): size_class_inch
    is component-property-only — no current_parameters mirror, no thrust/power/
    RPM/Ct/autonomy involvement. None means "leave whatever is already declared"
    (same convention as material), never invented, never copied from the prop.

    Structure Catalog Foundation IC-2: ``catalog_ref``/``component_name`` are
    keyword-only and default to ``None`` — every existing free-text caller
    (which never passes them) keeps today's exact behavior: a fresh
    ``ComponentSpec`` is always built here, never copying a prior
    ``catalog_ref``, so a free-text rewrite of an already-bound frame
    silently clears the binding (never a stale SKU label next to numbers
    that may no longer match it). Passing ``catalog_ref`` is how a bind
    apply path (test-callable only in IC-2 — no CLI/UX caller yet) persists
    SKU identity through this same single writer, instead of a second,
    parallel frame-write path.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    # ── 1. Build / update components["frame"] ────────────────────────────
    existing = project_state.design_properties.components.get("frame")
    props: dict[str, PropertyValue] = dict(existing.properties) if existing else {}

    if mass_kg is not None:
        props["mass_kg"] = PropertyValue(
            value=mass_kg, unit="kg", confidence=0.95, source="declared"
        )
    if material is not None:
        props["material"] = PropertyValue(
            value=material, unit=None, confidence=0.9, source="declared"
        )
    if size_class_inch is not None:
        props["size_class_inch"] = PropertyValue(
            value=size_class_inch, unit="in", confidence=0.9, source="declared"
        )

    completeness, missing_fields = _frame_completeness(props)
    frame_spec = ComponentSpec(
        name=component_name or "frame",
        component_type="structure",
        suggested_key="frame",
        inference_confidence=0.9,
        properties=props,
        completeness=completeness,
        missing_fields=missing_fields,
        source="declared",
        catalog_ref=catalog_ref,
    )
    updated_components = {**project_state.design_properties.components, "frame": frame_spec}
    updated_dp = project_state.design_properties.model_copy(update={
        "components": updated_components,
    })

    # ── 2. structure_mass_override_kg in current_parameters ───────────────
    # N1 hotfix (implementation_contract_structure_a_n1_hotfix.md): mirror
    # from the MERGED props, not the mass_kg argument — a partial update
    # (e.g. size/material only, mass_kg=None) must not delete an override
    # the merged component still declares. Only pop when the merged frame
    # truly has no mass.
    updated_params = dict(project_state.current_parameters or {})
    mass_prop = props.get("mass_kg")
    if mass_prop is not None and mass_prop.value is not None:
        updated_params["structure_mass_override_kg"] = float(mass_prop.value)
    else:
        updated_params.pop("structure_mass_override_kg", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


def merge_frame_root_declared_properties(
    project_state: Any,
    extra: dict[str, PropertyValue],
) -> Any:
    """G-N1: merge declared-only root fields (configuration / wheelbase_mm)
    onto the existing frame without touching mass/material completeness
    rules. No-op when frame is absent or *extra* is empty.
    """
    if not extra:
        return project_state
    existing = project_state.design_properties.components.get("frame")
    if existing is None:
        return project_state
    allowed = {"configuration", "wheelbase_mm"}
    props = dict(existing.properties or {})
    changed = False
    for key, value in extra.items():
        if key not in allowed or value is None:
            continue
        props[key] = value
        changed = True
    if not changed:
        return project_state
    completeness, missing_fields = _frame_completeness(props)
    frame_spec = existing.model_copy(
        update={
            "properties": props,
            "completeness": completeness,
            "missing_fields": missing_fields,
        }
    )
    updated_components = {**project_state.design_properties.components, "frame": frame_spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    return project_state.model_copy(update={"design_properties": updated_dp})


def upsert_frame_part(
    project_state: Any,
    part_key: str,
    properties: dict[str, PropertyValue],
    *,
    catalog_ref: CatalogRef | None = None,
) -> Any:
    """Structure B Parts Graph — único punto de escritura para un hijo de
    tipo de parte del frame (``frame_arm``/``frame_plate``/``frame_cage``/
    ``frame_standoff``).

    G-N1: also reachable from the free-text frame apply path (root+parts
    in one message), not only catalog bind / tests.

    Merges onto any existing child spec (repeated declarations accumulate,
    e.g. declaring material after count). ``parent_key="frame"`` always —
    Fase 1 has exactly one assembly root. Child completeness
    (``_structure_part_completeness``) is independent of
    ``_frame_completeness``/Structure PASS — never read by
    ``_structure_evidence`` or any gap builder.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    existing = project_state.design_properties.components.get(part_key)
    merged_props: dict[str, PropertyValue] = dict(existing.properties) if existing else {}
    merged_props.update(properties)
    completeness, missing_fields = _structure_part_completeness(merged_props)
    part_spec = ComponentSpec(
        name=part_key,
        component_type="structure_part",
        suggested_key=part_key,
        inference_confidence=0.9,
        properties=merged_props,
        completeness=completeness,
        missing_fields=missing_fields,
        source="declared",
        catalog_ref=catalog_ref,
        parent_key="frame",
    )
    updated_components = {**project_state.design_properties.components, part_key: part_spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    return project_state.model_copy(update={"design_properties": updated_dp})


def clear_frame_part_children(project_state: Any) -> Any:
    """IDLE frame rebind (B2) — G-N4 catalog half: remove every component
    with ``parent_key == "frame"`` before a catalog re-pick upserts the new
    SKU's own part fields, so re-picking Armattan → TBS never leaves stale
    ``frame_arm``/``frame_plate``/``frame_cage``/``frame_standoff`` entries
    declaring the *previous* SKU's materials next to a root that no longer
    names it. Removes by ``parent_key`` (not the four locked keys directly)
    so it stays correct if a future slice adds more part types. A no-op
    (returns ``project_state`` unchanged) when no child exists — the plain
    free-text root rewrite path (§3.5, unchanged) is not affected, since
    this is only called from the catalog re-pick apply path.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    components = project_state.design_properties.components
    remaining = {
        key: spec for key, spec in components.items()
        if getattr(spec, "parent_key", None) != "frame"
    }
    if len(remaining) == len(components):
        return project_state
    updated_dp = project_state.design_properties.model_copy(update={"components": remaining})
    return project_state.model_copy(update={"design_properties": updated_dp})


def set_control_component(project_state: Any, spec: Any) -> Any:
    """Único punto de escritura para componentes del bloque control (FC, sensores).

    Escribe spec directamente en components[spec.suggested_key].
    Sin physics bypass — control no afecta cálculo en Fase 2.5.
    Sin mirror legacy — no hay campo equivalente en design_properties.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    key = spec.suggested_key or spec.component_type or "generic_control"
    updated_components = {**project_state.design_properties.components, key: spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    return project_state.model_copy(update={"design_properties": updated_dp})


def _resolve_battery_voltage_v(components: dict[str, Any], current_parameters: dict[str, Any]) -> float | None:
    """Derive the real pack voltage from the bound battery, if any.

    Shared by ``set_motor_component`` (OP-resolution query voltage) and
    ``set_battery_component``'s revalidation gate (Motor OP Voltage
    Coherence IC, MOP-2) — single source for this derivation so both never
    drift apart. Priority: catalog SKU's own ``nominal_voltage``/``cells``,
    else ``current_parameters["battery_cell_count"]`` (3.7V/cell estimate).
    """
    battery = components.get("battery")
    battery_catalog_ref = getattr(battery, "catalog_ref", None) if battery is not None else None
    if battery_catalog_ref is not None and battery_catalog_ref.family == "battery":
        try:
            battery_spec = default_library.get_battery(battery_catalog_ref.sku)
        except KeyError:
            battery_spec = None
        if battery_spec is not None:
            if battery_spec.nominal_voltage is not None:
                return float(battery_spec.nominal_voltage)
            if battery_spec.cells is not None:
                return float(battery_spec.cells) * 3.7
    cell_count = current_parameters.get("battery_cell_count")
    if cell_count is not None:
        try:
            return float(cell_count) * 3.7
        except (TypeError, ValueError):
            return None
    return None


def set_battery_component(
    project_state: Any,
    spec: Any,
    capacity_wh: float | None,
) -> Any:
    """Único punto de escritura para propiedades de la batería.

    Escribe en dos lugares de forma atómica:
      1. components["battery"].properties (canónico)
      2. current_parameters["battery_capacity_wh"] (bridge al calculation engine)

    Sin mirror legacy — no hay campo equivalente en StructureProperties para battery.
    Returns updated ProjectState (not persisted — caller must save).
    """
    updated_components = {**project_state.design_properties.components, "battery": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    if capacity_wh is not None:
        updated_params["battery_capacity_wh"] = capacity_wh
        # Catalog v1 (Impl B, 4A): a SKU-bound battery's mass comes from the
        # SKU's real mass_g, overriding the 150 Wh/kg heuristic. Unbound
        # batteries (catalog_ref is None — today's only case) keep the
        # heuristic exactly as before this change.
        mass_prop = spec.properties.get("mass_g") if spec.catalog_ref is not None else None
        if (
            spec.catalog_ref is not None
            and spec.catalog_ref.family == "battery"
            and mass_prop is not None
            and mass_prop.value is not None
        ):
            updated_params["battery_mass_kg"] = round(float(mass_prop.value) / 1000.0, 4)
        else:
            updated_params["battery_mass_kg"] = estimate_battery_mass_kg(capacity_wh)
    else:
        updated_params.pop("battery_capacity_wh", None)
        updated_params.pop("battery_mass_kg", None)
    # U2: bridge cell_count → battery_cell_count (needed for RPM derivation in engine)
    cell_prop = spec.properties.get("cell_count")
    if cell_prop is not None:
        updated_params["battery_cell_count"] = int(cell_prop.value)
    else:
        updated_params.pop("battery_cell_count", None)

    result = project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })

    # Motor OP Voltage Coherence IC (MOP-2, ★4 complement): a battery bind
    # can be the FIRST time the motor's operating-point resolution ever
    # learns the real pack voltage (motor/propeller are often bound before
    # any battery). Re-resolve ONLY when the stored resolution was never
    # voltage-validated, or was validated at a voltage the new battery no
    # longer matches — NEVER unconditionally. An already voltage-validated,
    # still-compatible exact match must not be re-triggered: re-running the
    # resolver can legitimately downgrade it, and that specific stability is
    # a locked P2-2/IC2 regression contract (see
    # test_battery_pick_does_not_regress_already_resolved_propulsion_op).
    # Single-writer locus (this hook, not duplicated per call site) —
    # covers every set_battery_component caller uniformly (catalog pick,
    # freeform description, DSE apply/iterate). Slightly redundant when
    # reached via apply_components_delta's own _APPLY_ORDER loop (which
    # unconditionally re-derives motors right after "battery" regardless),
    # but harmless — see implementation report §MOP-2.
    motors_spec = updated_components.get("motors")
    motors_catalog_ref = getattr(motors_spec, "catalog_ref", None)
    if motors_catalog_ref is not None and motors_catalog_ref.family == "motor":
        stored_resolution_raw = updated_params.get("propulsion_resolution")
        needs_revalidation = True
        if stored_resolution_raw:
            try:
                stored_resolution = json.loads(stored_resolution_raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                stored_resolution = None
            if stored_resolution is not None and stored_resolution.get("voltage_validated", False):
                prior_voltage = stored_resolution.get("resolved_at_voltage_v")
                new_voltage = _resolve_battery_voltage_v(updated_components, updated_params)
                if (
                    prior_voltage is not None
                    and new_voltage is not None
                    and abs(float(prior_voltage) - float(new_voltage)) <= _OP_VOLTAGE_EPSILON_V
                ):
                    needs_revalidation = False
        if needs_revalidation:
            power_prop = motors_spec.properties.get("power_w")
            power_w = (
                float(power_prop.value)
                if power_prop is not None and power_prop.value is not None
                else updated_params.get("motor_power_w")
            )
            result = set_motor_component(result, motors_spec, power_w)

    return result


def set_motor_component(
    project_state: Any,
    spec: Any,
    power_w: float | None,
) -> Any:
    """Único punto de escritura para propiedades de los motores.

    Escribe en dos lugares de forma atómica:
      1. components["motors"].properties (canónico)
      2. current_parameters["motor_power_w"] (bridge al calculation engine)

    Impl C follow-up (thrust bridge, 2026-08-21): when the spec carries a
    ``thrust_n`` property (catalog-bound motors always do —
    ``bind_motor_from_catalog`` sets it with ``output_magnitude="thrust_n"``),
    that value is the sole source for
    ``current_parameters["per_motor_max_thrust_n"]``. Never invented from
    power_w/KV/a library re-lookup — only ever the number already on the spec
    (★1). Absent when ``thrust_n`` is missing (synthetic/freeform motors) —
    deliberately NOT popped in that case, unlike ``motor_kv_rating`` below:
    a freeform re-declare (e.g. updating just power_w) must not silently
    erase a numeric-wizard-declared thrust value that has nothing to do with
    this write. Closes the gap traced in
    .jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md §4 /
    implementation_review_impl_c_catalog_aware_dse.md Note A — catalog-DSE
    candidate evaluation and SKU-switch apply both read this field and had
    no other way to see a bound spec's real thrust before this fix.

    Bug 78: preserves motor_count from the existing component when the new spec
    does not include it. Prevents double-write scenarios (first write declares count,
    second declares KV+power) from losing the count in component properties.
    The physics (current_parameters["motor_count"]) is always preserved regardless,
    but the component property must also be consistent for reasoning display.

    FN-007: when there is no existing "motors" component at all (e.g. the project
    declared motor_count only via the numeric current_parameters path and never
    had a components["motors"] entry), fall back to current_parameters["motor_count"]
    so a fresh catalog pick doesn't drop the fleet size to the resolver's
    "count of eligible entries" default (1).

    Returns updated ProjectState (not persisted — caller must save).
    """
    # Bug 78 / FN-007: preserve motor_count — from the existing component's
    # property if present, else fall back to current_parameters["motor_count"].
    existing_motors = getattr(project_state.design_properties, "components", {}).get("motors")
    if "motor_count" not in (spec.properties or {}):
        old_count = existing_motors.properties.get("motor_count") if existing_motors is not None else None
        if old_count is None:
            fallback_count = (project_state.current_parameters or {}).get("motor_count")
            if fallback_count is not None:
                old_count = PropertyValue(value=fallback_count, confidence=0.9, source="declared")
        if old_count is not None:
            spec = spec.model_copy(update={"properties": {**spec.properties, "motor_count": old_count}})

    updated_components = {**project_state.design_properties.components, "motors": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    if power_w is not None:
        updated_params["motor_power_w"] = power_w
    else:
        updated_params.pop("motor_power_w", None)
    # U2: bridge motor_count → current_parameters (necesario para calculate_thrust_per_motor)
    count_prop = spec.properties.get("motor_count")
    if count_prop is not None:
        updated_params["motor_count"] = int(count_prop.value)
    # U2: bridge kv_rating → motor_kv_rating (needed for RPM derivation in engine)
    kv_prop = spec.properties.get("kv_rating")
    if kv_prop is not None:
        updated_params["motor_kv_rating"] = float(kv_prop.value)
    else:
        updated_params.pop("motor_kv_rating", None)
    # Phase 2 P2-1 (Lookup Operating Point): when the motor is catalog-bound,
    # resolve a real (motor[, propeller][, voltage]) operating point instead
    # of mirroring the bare SKU peak thrust_n 1:1 (the pre-P2-1 Impl C bridge
    # behavior, kept unchanged below for freeform/unbound motors — ★-locked
    # regression contract: OP-miss must reproduce today's exact numeric
    # behavior). resolve_operating_point always returns a typed resolution
    # for a known SKU (exact / fallback / legacy) — never a bare float.
    resolved_op = None
    if spec.catalog_ref is not None and spec.catalog_ref.family == "motor":
        components = getattr(project_state.design_properties, "components", {}) or {}
        propellers = components.get("propellers")
        prop_catalog_ref = getattr(propellers, "catalog_ref", None) if propellers is not None else None
        propeller_sku = (
            prop_catalog_ref.sku
            if (prop_catalog_ref is not None and prop_catalog_ref.family == "propeller")
            else None
        )

        voltage_v = _resolve_battery_voltage_v(components, project_state.current_parameters or {})

        resolved_op = resolve_operating_point(
            spec.catalog_ref.sku, propeller_sku=propeller_sku, voltage_v=voltage_v,
        )

    if resolved_op is not None:
        updated_params["per_motor_max_thrust_n"] = resolved_op.thrust_n
        # Stored as a JSON string, not a nested dict: current_parameters
        # values must stay hashable — design_explorer.py's per-candidate
        # evaluation cache keys on frozenset(params.items()), and a dict
        # value there raises TypeError (silently swallowed by that loop's
        # broad except, which made every catalog DSE candidate vanish
        # during this slice's own regression testing). A JSON string is
        # still fully inspectable by callers via json.loads.
        updated_params["propulsion_resolution"] = json.dumps({
            "resolution_type": resolved_op.resolution_type,
            "thrust_n": resolved_op.thrust_n,
            "source_type": resolved_op.source_type,
            "confidence": resolved_op.confidence,
            "selection_reason": resolved_op.selection_reason,
            "voltage_v": resolved_op.voltage_v,
            "propeller_sku": resolved_op.propeller_sku,
            "fallback_only": resolved_op.fallback_only,
            "source_reference": resolved_op.source_reference,
            "motor_sku": resolved_op.motor_sku,
            # Motor OP Voltage Coherence IC (MOP-2): provenance of the QUERY
            # voltage this resolution was made with — distinct from
            # resolved_op.voltage_v (the matched row's own voltage). Lets a
            # later battery bind tell "never voltage-validated" (this was
            # None) apart from "validated at a voltage now incompatible with
            # the real pack" without re-deriving anything.
            "voltage_validated": voltage_v is not None,
            "resolved_at_voltage_v": voltage_v,
        }, sort_keys=True)
        # Keep the component property coherent with the resolved thrust for
        # exact/fallback resolutions (a real operating point) — never for
        # legacy_estimate, where the bare spec.properties["thrust_n"] set by
        # bind_motor_from_catalog already equals resolved_op.thrust_n anyway.
        # catalog_ref is never touched here — only PropertyValue mutated.
        if resolved_op.resolution_type in ("exact_operating_point", "fallback_operating_point"):
            # P2-2 (Operating Point Bridge, ★ locked Option A): additive
            # OP-electrical calc-bridge keys — never overwrite motor_power_w
            # (catalog max_watts rating keeps its own meaning; a resolved
            # operating point is a distinct, more specific measurement of
            # the SAME motor at THIS combo/voltage, not a replacement
            # rating). Written only here (a real OP row matched); popped in
            # both the legacy_estimate and unbound/freeform branches below
            # so a stale OP from a prior bind never survives a divergence.
            for _key, _value in (
                ("motor_op_power_w", resolved_op.power_w),
                ("motor_op_current_a", resolved_op.current_a),
                ("motor_op_rpm", resolved_op.rpm),
            ):
                if _value is not None:
                    updated_params[_key] = _value
                else:
                    updated_params.pop(_key, None)
            spec = spec.model_copy(update={"properties": {
                **spec.properties,
                "thrust_n": PropertyValue(
                    value=resolved_op.thrust_n, unit="N",
                    confidence=resolved_op.confidence, source="declared",
                ),
            }})
            updated_components = {**updated_components, "motors": spec}
            updated_dp = updated_dp.model_copy(update={"components": updated_components})
        else:
            updated_params.pop("motor_op_power_w", None)
            updated_params.pop("motor_op_current_a", None)
            updated_params.pop("motor_op_rpm", None)
    else:
        # Impl C follow-up (thrust bridge, ★1): thrust_n on the spec is the
        # sole source for per_motor_max_thrust_n — never invented, never
        # popped when absent (see docstring above for why no-pop is
        # deliberate here). Unchanged for freeform/unbound motors.
        thrust_prop = spec.properties.get("thrust_n")
        if thrust_prop is not None and thrust_prop.value is not None:
            updated_params["per_motor_max_thrust_n"] = float(thrust_prop.value)
        updated_params.pop("propulsion_resolution", None)
        # P2-2: no operating point resolved at all (unbound/freeform motor)
        # -> no OP-electrical data to bridge.
        updated_params.pop("motor_op_power_w", None)
        updated_params.pop("motor_op_current_a", None)
        updated_params.pop("motor_op_rpm", None)
    # Catalog v1 (Impl B, 2A): motor mass enters calc ONLY when the component
    # is SKU-bound (catalog_ref set) — free-text-declared motors keep today's
    # physics unchanged (no motor_mass_kg mirror at all, same as before this
    # change). fleet mass = per-motor weight_g × motor_count.
    weight_prop = spec.properties.get("weight_g")
    if (
        spec.catalog_ref is not None
        and spec.catalog_ref.family == "motor"
        and weight_prop is not None
        and weight_prop.value is not None
        and updated_params.get("motor_count") is not None
    ):
        updated_params["motor_mass_kg"] = round(
            float(weight_prop.value) / 1000.0 * int(updated_params["motor_count"]), 4
        )
    else:
        updated_params.pop("motor_mass_kg", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


def set_propeller_component(project_state: Any, spec: Any) -> Any:
    """Único punto de escritura para propiedades de las hélices.

    Escribe en dos lugares de forma atómica:
      1. components["propellers"].properties (canónico)
      2. current_parameters["propeller_diameter_in"] (bridge al calculation engine)

    El engine usa propeller_diameter_in para calcular thrust via aerodinámica.
    propeller_rpm NO se toca aquí — es un param dinámico de operación (Phase B).
    Returns updated ProjectState (not persisted — caller must save).
    """
    updated_components = {**project_state.design_properties.components, "propellers": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    diameter_prop = spec.properties.get("diameter_in")
    if diameter_prop is not None:
        updated_params["propeller_diameter_in"] = float(diameter_prop.value)
    else:
        updated_params.pop("propeller_diameter_in", None)
    # U2: bridge pitch_in → propeller_pitch_in (informativo; no entra al engine aún)
    pitch_prop = spec.properties.get("pitch_in")
    if pitch_prop is not None:
        updated_params["propeller_pitch_in"] = float(pitch_prop.value)
    else:
        updated_params.pop("propeller_pitch_in", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


# ── DA2: composite delta applicator ──────────────────────────────────────────

# Canonical write order: each writer may derive params from the previous component.
# frame → battery → motors → propellers → control (everything else).
_APPLY_ORDER = ("frame", "battery", "motors", "propellers")


def apply_components_delta(project_state: Any, components_delta: dict[str, Any]) -> Any:
    """Aplica un dict de ComponentSpec sobre project_state usando los writers canónicos.

    Garantías:
    - Orden determinista: _APPLY_ORDER primero, luego claves extra (control, etc.).
    - Cada writer extrae sus parámetros físicos de spec.properties — nunca de params.
    - Idempotente con delta vacío: devuelve project_state con params re-derivados
      de los componentes ya presentes (normalización de baseline).
    - Puro: no persiste ni dispara efectos secundarios.

    Returns updated ProjectState (not persisted — caller must save).

    # TODO (v2 — refactor semántico): esta función hace dos cosas distintas:
    #   1. Aplicar un delta de componentes (comportamiento esperado).
    #   2. Normalizar el estado re-derivando params desde componentes existentes
    #      cuando delta es {} (baseline normalization en explore()).
    # Separar en:
    #   normalize_state_from_components(state) -> ProjectState
    #   apply_components_delta(state, delta) -> ProjectState
    # Riesgo actual: un caller que pase {} esperando no-op obtendrá recálculo completo.
    # Refactor seguro — no cambiar hasta que haya un segundo caller con expectativa distinta.
    """
    state = project_state

    # Ordered keys first
    for key in _APPLY_ORDER:
        spec = components_delta.get(key)
        if spec is None:
            # No delta for this key — re-apply existing component if present
            # so baseline normalization works correctly (empty delta path).
            design_props = getattr(state, "design_properties", None)
            existing_components = getattr(design_props, "components", None) if design_props is not None else None
            existing = existing_components.get(key) if existing_components is not None else None
            if existing is None:
                continue
            spec = existing

        if key == "frame":
            mass_prop = spec.properties.get("mass_kg")
            material_prop = spec.properties.get("material")
            mass_kg = float(mass_prop.value) if mass_prop is not None and mass_prop.value is not None else None
            material = str(material_prop.value) if material_prop is not None and material_prop.value is not None else None
            state = set_frame_material(state, mass_kg, material)
        elif key == "battery":
            cap_prop = spec.properties.get("battery_capacity_wh")
            capacity_wh = float(cap_prop.value) if cap_prop is not None and cap_prop.value is not None else None
            state = set_battery_component(state, spec, capacity_wh)
        elif key == "motors":
            power_prop = spec.properties.get("power_w")
            power_w = float(power_prop.value) if power_prop is not None and power_prop.value is not None else None
            state = set_motor_component(state, spec, power_w)
        elif key == "propellers":
            state = set_propeller_component(state, spec)

    # Extra keys not in _APPLY_ORDER (flight_controller, sensors, esc, …)
    for key, spec in components_delta.items():
        if key not in _APPLY_ORDER:
            state = set_control_component(state, spec)

    return state
