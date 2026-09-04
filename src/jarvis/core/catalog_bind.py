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


# G24D (Frankenstein .name clear, ★ locked §2.4): fixed, honest label for a
# motor whose catalog_ref was just cleared by divergence — replaces the
# stale SKU string so a BOM/estado reader never mistakes a no-longer-bound
# motor for a still-bound one just because its .name still looks like a
# product code. Deliberately not SKU-shaped (no snake_case product-name
# pattern) and never a live library key — see
# test_impl_d_sku_bom.py::test_frankenstein_motor_name_is_never_a_real_sku.
_DIVERGED_MOTOR_NAME: str = "motor (parámetros divergentes)"


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
