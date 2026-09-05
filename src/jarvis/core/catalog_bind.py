"""Physical Component Catalog v1 — Impl B (Bind).

Pure/deterministic helpers that project a confirmed catalog SKU into a
ComponentSpec carrying CatalogRef identity, plus the shared divergence check
that clears catalog_ref when a later mutation moves a physical number away
from what the bound SKU actually is (Design §8: forbid silent overwrite —
never keep a stale SKU label next to numbers that no longer match it).

Design authority: docs/PHYSICAL_COMPONENT_CATALOG_V1.md (CLOSED, locks
1A/2A/4A). No LLM. No second JSON reader — all catalog reads go through
jarvis.knowledge.library.ComponentLibrary.
"""
from __future__ import annotations

from typing import Any

from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.domains.aerial import _frame_completeness
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.tools.electricity import estimate_battery_mass_kg


def bind_motor_from_catalog(
    suggestion: MotorSuggestion, *, base: ComponentSpec | None = None
) -> ComponentSpec:
    """Project a catalog ``MotorSuggestion`` into a ``ComponentSpec`` with
    ``catalog_ref`` set.

    Single shared helper for both catalog-pick entry points (the iterate
    wizard's mid-session pick and the DEFINE_MISSING wizard's first pick) —
    avoids the two paths diverging on what gets bound (the pre-Impl-B bug:
    iterate's pick only copied ``thrust_n``/``weight_g``, discarding the SKU).

    * ``base=None``   — builds a fresh spec (DEFINE_MISSING's pick shape).
    * ``base=<spec>`` — merges onto an existing draft spec, preserving
      whatever properties were already collected (e.g. ``motor_count``) —
      the iterate wizard's mid-session pick shape.
    """
    watts_raw = suggestion.get("max_watts")
    sku = str(suggestion["name"])
    catalog_ref = CatalogRef(family="motor", sku=sku)
    projected = {
        "thrust_n": PropertyValue(
            value=float(suggestion["thrust_n"]), unit="N", confidence=0.9, source="declared"
        ),
        "kv_rating": PropertyValue(
            value=int(suggestion["kv_rating"]), confidence=0.9, source="declared"
        ),
        "weight_g": PropertyValue(
            value=float(suggestion["weight_g"]), unit="g", confidence=0.9, source="declared"
        ),
    }
    if watts_raw is not None:
        projected["power_w"] = PropertyValue(
            value=float(watts_raw), unit="W", confidence=0.9, source="declared"
        )
    if base is not None:
        merged_properties = {**(base.properties or {}), **projected}
        return base.model_copy(update={
            "properties": merged_properties,
            "completeness": "high",
            "catalog_ref": catalog_ref,
            # FN-007 precedent: thrust_n is the resolvable magnitude for this
            # component so component_resolver derives per_motor_max_thrust_n
            # from it on every recalculation.
            "output_magnitude": "thrust_n",
        })
    return ComponentSpec(
        name=sku,
        component_type="propulsion_active",
        suggested_key="motors",
        inference_confidence=0.95,
        completeness="high",
        source="declared",
        properties=projected,
        output_magnitude="thrust_n",
        catalog_ref=catalog_ref,
    )


def bind_battery_from_catalog(
    sku: str,
    *,
    library: ComponentLibrary | None = None,
    base: ComponentSpec | None = None,
) -> ComponentSpec:
    """Project a catalog battery SKU into a ``ComponentSpec`` with
    ``catalog_ref`` set.

    No CLI/UX entry point calls this yet — no battery catalog pick flow
    exists (Impl A's 5A lock: no Continuity/assist redesign for batteries in
    Foundation). Exposed as a deterministic, test-callable API so Impl B can
    prove the Bind → writer → calc causality chain without inventing a
    Continuity UX ahead of when it's actually needed.
    """
    lib = library or default_library
    spec = lib.get_battery(sku)
    catalog_ref = CatalogRef(family="battery", sku=sku)
    projected = {
        "battery_capacity_wh": PropertyValue(
            value=spec.energy_wh, unit="Wh", confidence=0.95, source="declared"
        ),
        "mass_g": PropertyValue(value=spec.mass_g, unit="g", confidence=0.95, source="declared"),
        "chemistry": PropertyValue(value=spec.chemistry, confidence=0.95, source="declared"),
    }
    if spec.cells is not None:
        projected["cell_count"] = PropertyValue(
            value=spec.cells, confidence=0.9, source="declared"
        )
    if base is not None:
        merged_properties = {**(base.properties or {}), **projected}
        return base.model_copy(update={
            "properties": merged_properties,
            "completeness": "high",
            "catalog_ref": catalog_ref,
        })
    return ComponentSpec(
        name=sku,
        component_type="energy_storage",
        suggested_key="battery",
        inference_confidence=0.95,
        completeness="high",
        source="declared",
        properties=projected,
        catalog_ref=catalog_ref,
    )


def bind_propeller_from_catalog(
    sku: str,
    *,
    library: ComponentLibrary | None = None,
    base: ComponentSpec | None = None,
) -> ComponentSpec:
    """Project a catalog propeller SKU into a ``ComponentSpec`` with
    ``catalog_ref`` set.

    Same status as the battery helper — no existing pick UX, deterministic
    test-callable API only. Propeller mass is **not** wired into calc in this
    cut (contract §2.1.D — optional, explicitly deferred; motor + battery
    already prove the causality chain end to end).
    """
    lib = library or default_library
    spec = lib.get_propeller(sku)
    catalog_ref = CatalogRef(family="propeller", sku=sku)
    projected = {
        "diameter_in": PropertyValue(
            value=spec.diameter_in, unit="in", confidence=0.95, source="declared"
        ),
        "pitch_in": PropertyValue(
            value=spec.pitch_in, unit="in", confidence=0.95, source="declared"
        ),
    }
    if spec.mass_g is not None:
        projected["mass_g"] = PropertyValue(
            value=spec.mass_g, unit="g", confidence=0.9, source="declared"
        )
    if base is not None:
        merged_properties = {**(base.properties or {}), **projected}
        return base.model_copy(update={
            "properties": merged_properties,
            "completeness": "high",
            "catalog_ref": catalog_ref,
        })
    return ComponentSpec(
        name=sku,
        component_type="propulsion_passive",
        suggested_key="propellers",
        inference_confidence=0.95,
        completeness="high",
        source="declared",
        properties=projected,
        catalog_ref=catalog_ref,
    )


def bind_esc_from_catalog(
    sku: str,
    *,
    library: ComponentLibrary | None = None,
    base: ComponentSpec | None = None,
) -> ComponentSpec:
    """Project a catalog ESC SKU into a ``ComponentSpec`` with ``catalog_ref`` set.

    Projects ``continuous_current_a`` from the catalog into ``current_a`` —
    the property ``electrical_compatibility`` already reads for per-channel
    ESC-vs-motor comparison. No CLI/UX entry point calls this yet; exposed as
    a deterministic, test-callable API mirroring ``bind_battery_from_catalog``.
    """
    lib = library or default_library
    spec = lib.get_esc(sku)
    catalog_ref = CatalogRef(family="esc", sku=sku)
    projected = {
        "current_a": PropertyValue(
            value=spec.continuous_current_a,
            unit="A",
            confidence=0.95,
            source="declared",
        ),
    }
    if spec.mass_g is not None:
        projected["mass_g"] = PropertyValue(
            value=spec.mass_g, unit="g", confidence=0.9, source="declared"
        )
    if base is not None:
        merged_properties = {**(base.properties or {}), **projected}
        return base.model_copy(update={
            "properties": merged_properties,
            "completeness": "high",
            "catalog_ref": catalog_ref,
        })
    return ComponentSpec(
        name=sku,
        component_type="power_control",
        suggested_key="esc",
        inference_confidence=0.95,
        completeness="high",
        source="declared",
        properties=projected,
        catalog_ref=catalog_ref,
    )


def bind_frame_from_catalog(
    sku: str,
    *,
    library: ComponentLibrary | None = None,
    base: ComponentSpec | None = None,
) -> ComponentSpec:
    """Structure Catalog Foundation IC-2 — project a catalog frame SKU into a
    ``ComponentSpec`` with ``catalog_ref`` set.

    Same status as the battery/propeller/ESC helpers: no CLI/UX entry point
    calls this yet (IC-3 assist is a separate, not-yet-authorized thread) —
    exposed as a deterministic, test-callable API. ``completeness``/
    ``missing_fields`` are derived via ``_frame_completeness`` (the same
    mass+material authority ``set_frame_material`` already uses) instead of
    a hardcoded ``"high"`` like the other three binders, because a real seed
    row may honestly lack a stated ``material`` (Structure Catalog Foundation
    IC-1's two TBS rows) — completeness must reflect that, not paper over it.

    Structure A composition, not replacement: projects the same two fields
    ``set_frame_material``/``_frame_completeness``/
    ``frame_class_compatibility_state`` already read (``mass_kg``,
    ``size_class_inch``), plus optional ``material`` — never a new field,
    never geometry/fit/strength data.
    """
    lib = library or default_library
    spec = lib.get_frame(sku)
    catalog_ref = CatalogRef(family="frame", sku=sku)
    projected = {
        "mass_kg": PropertyValue(
            value=spec.mass_g / 1000.0, unit="kg", confidence=0.95, source="declared"
        ),
        "size_class_inch": PropertyValue(
            value=spec.size_class_inch, unit="in", confidence=0.95, source="declared"
        ),
    }
    if spec.material is not None:
        projected["material"] = PropertyValue(
            value=spec.material, unit=None, confidence=0.9, source="declared"
        )
    # Structure B Parts Graph (Fase 1) — root-only additive projections;
    # neither enters _frame_completeness (still mass+material only).
    if spec.wheelbase_mm is not None:
        projected["wheelbase_mm"] = PropertyValue(
            value=spec.wheelbase_mm, unit="mm", confidence=0.95, source="declared"
        )
    if spec.configuration is not None:
        projected["configuration"] = PropertyValue(
            value=spec.configuration, unit=None, confidence=0.9, source="declared"
        )
    if base is not None:
        merged_properties = {**(base.properties or {}), **projected}
        completeness, missing_fields = _frame_completeness(merged_properties)
        return base.model_copy(update={
            "properties": merged_properties,
            "completeness": completeness,
            "missing_fields": missing_fields,
            "catalog_ref": catalog_ref,
        })
    completeness, missing_fields = _frame_completeness(projected)
    return ComponentSpec(
        name=sku,
        component_type="structure",
        suggested_key="frame",
        inference_confidence=0.95,
        completeness=completeness,
        missing_fields=missing_fields,
        source="declared",
        properties=projected,
        catalog_ref=catalog_ref,
    )


def frame_part_specs_from_catalog(sku: str, *, library: ComponentLibrary | None = None) -> dict[str, ComponentSpec]:
    """Structure B Parts Graph (Fase 1) — project a catalog frame SKU's
    declared part-level fields into child ``ComponentSpec`` objects, keyed
    by the locked dict keys (``FRAME_ARM_KEY`` etc.), each with
    ``parent_key="frame"``.

    Returns an **empty dict** when the SKU has no part fields — no fabricated
    children, same "no part fields → no children" rule ``bind_frame_from_catalog``
    itself follows for the root. With curated ``plates`` / ``arm_thickness_mm``
    seeded (2026-09-05), all four current seed rows typically project at least
    an arm and one or more plate siblings. Pure projection; does not write to any
    ``ProjectState`` — the caller (catalog-assist apply path) upserts these
    via ``component_writers.upsert_frame_part``.
    """
    from jarvis.domains.aerial import (
        FRAME_ARM_KEY,
        FRAME_CAGE_KEY,
        FRAME_PLATE_KEY,
        FRAME_PLATE_MAX_SIBLINGS,
        FRAME_STANDOFF_KEY,
        frame_plate_key,
    )

    lib = library or default_library
    spec = lib.get_frame(sku)
    parts: dict[str, ComponentSpec] = {}

    def _part(
        key: str,
        component_type_label: str,
        count: int | None,
        material: str | None,
        thickness_mm: float | None = None,
        label: str | None = None,
    ) -> None:
        if count is None and material is None and thickness_mm is None and label is None:
            return
        props: dict[str, PropertyValue] = {}
        if count is not None:
            props["count"] = PropertyValue(value=count, unit=None, confidence=0.9, source="declared")
        if material is not None:
            props["material"] = PropertyValue(value=material, unit=None, confidence=0.9, source="declared")
        if thickness_mm is not None:
            props["thickness_mm"] = PropertyValue(
                value=thickness_mm, unit="mm", confidence=0.9, source="declared"
            )
        if label is not None:
            props["label"] = PropertyValue(value=label, unit=None, confidence=0.9, source="declared")
        # N6 (locked, not "fixed" incidentally): every catalog-projected part
        # is hardcoded "high" here, independent of _structure_part_completeness
        # (which only free-text/upsert_frame_part ever call). Known
        # inconsistency, named debt — see investigation report / IC §3.3.4.
        parts[key] = ComponentSpec(
            name=key,
            component_type="structure_part",
            suggested_key=key,
            inference_confidence=0.9,
            properties=props,
            completeness="high",
            source="declared",
            parent_key="frame",
        )

    # thickness_mm (Structure B additive enrichment B2) projects onto
    # frame_arm only — cage/standoff never carry it in this slice.
    _part(FRAME_ARM_KEY, "arm", spec.arm_count, spec.arm_material, spec.arm_thickness_mm)

    # Frame Assembly Physical Model B2 (N2 precedence): when curated
    # `plates` is set (non-empty), it is the ONLY plate source — the legacy
    # plate_count/plate_material scalars are ignored entirely, never merged
    # or used as a fallback/fifth path. Each curated entry becomes its own
    # ordinal sibling (frame_plate, frame_plate_2, ...) even when two
    # entries share the same thickness (N3 — never merged by equal value).
    if spec.plates:
        if len(spec.plates) > FRAME_PLATE_MAX_SIBLINGS:
            raise ValueError(
                f"Frame '{sku}': {len(spec.plates)} plates declared, "
                f"max {FRAME_PLATE_MAX_SIBLINGS} ordinal siblings."
            )
        for index, plate in enumerate(spec.plates):
            _part(
                frame_plate_key(index),
                "plate",
                None,
                plate.material,
                plate.thickness_mm,
                plate.label,
            )
    else:
        _part(FRAME_PLATE_KEY, "plate", spec.plate_count, spec.plate_material)

    _part(FRAME_CAGE_KEY, "cage", None, spec.cage_material)
    _part(FRAME_STANDOFF_KEY, "standoff", spec.standoff_count, spec.standoff_material)
    return parts


# G24D (Frankenstein .name clear, ★ locked §2.4): fixed, honest label for a
# motor whose catalog_ref was just cleared by divergence — replaces the
# stale SKU string so a BOM/estado reader never mistakes a no-longer-bound
# motor for a still-bound one just because its .name still looks like a
# product code. Deliberately not SKU-shaped (no snake_case product-name
# pattern) and never a live library key — see
# test_impl_d_sku_bom.py::test_frankenstein_motor_name_is_never_a_real_sku.
_DIVERGED_MOTOR_NAME: str = "motor (parámetros divergentes)"

# Structure Catalog Foundation IC-2 — same G24D discipline for frame: never
# SKU-shaped, never a live library key.
_DIVERGED_FRAME_NAME: str = "frame (parámetros divergentes)"


def invalidate_diverged_catalog_refs(
    components: dict[str, ComponentSpec],
    params: dict[str, Any],
    *,
    epsilon: float = 1e-6,
) -> tuple[dict[str, ComponentSpec], dict[str, Any]]:
    """Clear ``catalog_ref`` on any component whose SKU-projected physical
    number no longer matches *params*. Pure — returns the same objects
    unchanged when nothing diverged, new dicts otherwise; never mutates
    inputs in place.

    Covers the two divergence paths named in the contract: a DSE params-only
    apply that scales ``per_motor_max_thrust_n``/``battery_capacity_wh``
    directly in ``current_parameters`` (never touching ``components`` at
    all), and an iterate numeric mutation that does the same
    (``_apply_mutation_to_parameters`` patches params directly; a numeric
    mutation's ``mutated_state`` carries no ``design_properties.components``
    patch, so the component spec — and any ``catalog_ref`` on it — is left
    completely untouched by construction). Both bypass the component spec
    entirely; this is the one shared place that reconciles them afterward.

    A component-driven DSE candidate (``apply_components_delta`` full-spec
    replace) already drops any prior ``catalog_ref`` by construction — the
    delta spec never carries one — so it needs no extra handling here; a
    no-op call on it is harmless (its ``catalog_ref`` is already ``None``).

    Motor: compares ``components["motors"].properties["thrust_n"]`` against
    ``params["per_motor_max_thrust_n"]``. On divergence, clears
    ``catalog_ref``, drops ``motor_mass_kg`` — falls back to no
    motor-mass contribution, identical to today's unbound behavior — and
    (G24D) replaces ``.name`` with ``_DIVERGED_MOTOR_NAME`` so a stale
    SKU-shaped string never survives next to a cleared ``catalog_ref``
    (investigation_report_deferred_queue_post_v031.md §6.1).

    Battery: compares ``components["battery"].properties["battery_capacity_wh"]``
    against ``params["battery_capacity_wh"]``. On divergence, clears
    ``catalog_ref`` and reverts ``battery_mass_kg`` to the 150 Wh/kg
    heuristic (``estimate_battery_mass_kg``) — the same fallback an unbound
    battery already uses.

    Frame (Structure Catalog Foundation IC-2): a different shape from
    motor/battery because ``size_class_inch`` has no ``current_parameters``
    mirror at all (Structure A §2.2 — component-property-only, locked) and
    free-text ``set_frame_material`` already clears ``catalog_ref`` by
    construction on any rewrite (a new ``ComponentSpec`` is always built,
    never copying a prior ref) — so there is no free-text-vs-bound-property
    divergence path to reconcile here, unlike motor/battery. Instead:
    (1) SKU vanished from the library → clear (frankenstein-safe, never
    invented); (2) the bound component's own ``mass_kg``/``size_class_inch``
    no longer match what the live ``FrameSpec`` declares → clear (catches a
    corrected/removed seed row); (3) ``params["structure_mass_override_kg"]``
    diverges from the component's own ``mass_kg`` → clear (same
    params-bypass hazard class as motor/battery, for the one frame field
    that does have a params mirror). On any divergence: clear ``catalog_ref``
    and rename to ``_DIVERGED_FRAME_NAME`` — mass/class properties
    themselves are left untouched (no fallback needed; free-text physics
    already treats any declared mass/class the same way regardless of
    provenance).
    """
    updated_components = dict(components)
    updated_params = dict(params)
    changed = False

    motor = components.get("motors")
    if motor is not None and motor.catalog_ref is not None and motor.catalog_ref.family == "motor":
        old_prop = motor.properties.get("thrust_n")
        old_value = old_prop.value if old_prop is not None else None
        new_value = updated_params.get("per_motor_max_thrust_n")
        if (
            old_value is not None
            and new_value is not None
            and abs(float(old_value) - float(new_value)) > epsilon
        ):
            updated_components["motors"] = motor.model_copy(update={
                "catalog_ref": None,
                "name": _DIVERGED_MOTOR_NAME,
            })
            updated_params.pop("motor_mass_kg", None)
            changed = True

    battery = components.get("battery")
    if battery is not None and battery.catalog_ref is not None and battery.catalog_ref.family == "battery":
        old_prop = battery.properties.get("battery_capacity_wh")
        old_value = old_prop.value if old_prop is not None else None
        new_value = updated_params.get("battery_capacity_wh")
        if (
            old_value is not None
            and new_value is not None
            and abs(float(old_value) - float(new_value)) > epsilon
        ):
            updated_components["battery"] = battery.model_copy(update={"catalog_ref": None})
            updated_params["battery_mass_kg"] = estimate_battery_mass_kg(float(new_value))
            changed = True

    frame = components.get("frame")
    if frame is not None and frame.catalog_ref is not None and frame.catalog_ref.family == "frame":
        sku = frame.catalog_ref.sku
        diverged = not default_library.has_frame(sku)
        if not diverged:
            live = default_library.get_frame(sku)
            mass_prop = frame.properties.get("mass_kg")
            mass_value = float(mass_prop.value) if mass_prop is not None and mass_prop.value is not None else None
            size_prop = frame.properties.get("size_class_inch")
            size_value = float(size_prop.value) if size_prop is not None and size_prop.value is not None else None
            if mass_value is not None and abs(mass_value - live.mass_g / 1000.0) > epsilon:
                diverged = True
            if size_value is not None and abs(size_value - live.size_class_inch) > epsilon:
                diverged = True
            override = updated_params.get("structure_mass_override_kg")
            if (
                not diverged
                and mass_value is not None
                and override is not None
                and abs(mass_value - float(override)) > epsilon
            ):
                diverged = True
        if diverged:
            updated_components["frame"] = frame.model_copy(update={
                "catalog_ref": None,
                "name": _DIVERGED_FRAME_NAME,
            })
            changed = True

    if not changed:
        return components, params
    return updated_components, updated_params


# ── DSE apply honesty (implementation_contract_dse_apply_honest.md) ──────────

def catalog_motor_nameplate_watts(
    components: dict[str, Any],
    *,
    library: ComponentLibrary | None = None,
) -> float | None:
    """The bound motor SKU's real nameplate ``max_watts``, or ``None`` when
    no motor is catalog-bound or the bound SKU honestly declares no watts
    (e.g. ``emax_rs2205s_2300``). Single library lookup — never invents a
    number, never rounds beyond what the catalog itself declares.
    """
    lib = library or default_library
    motor = components.get("motors")
    catalog_ref = getattr(motor, "catalog_ref", None)
    if catalog_ref is None or catalog_ref.family != "motor":
        return None
    try:
        spec = lib.get_motor(catalog_ref.sku)
    except KeyError:
        return None
    return spec.max_watts


def find_battery_skus_for_energy_wh(
    energy_wh: float,
    *,
    library: ComponentLibrary | None = None,
    epsilon: float = 1e-6,
) -> list[str]:
    """All catalog battery SKUs whose declared ``energy_wh`` matches
    *energy_wh* within *epsilon* (same order as the G5 divergence epsilon).
    """
    lib = library or default_library
    return [
        b.name for b in lib.list_batteries() if abs(float(b.energy_wh) - float(energy_wh)) <= epsilon
    ]


def find_unique_battery_sku_for_energy_wh(
    energy_wh: float,
    *,
    library: ComponentLibrary | None = None,
    epsilon: float = 1e-6,
) -> str | None:
    """The single catalog battery SKU matching *energy_wh*, or ``None`` when
    zero or more than one SKU matches — DSE apply must never silently pick
    among ambiguous packs (implementation_contract_dse_apply_honest.md §2.2).
    """
    matches = find_battery_skus_for_energy_wh(energy_wh, library=library, epsilon=epsilon)
    return matches[0] if len(matches) == 1 else None
