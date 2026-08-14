"""G5 fix — keep design_properties.components current with params-only DSE applies.

Params-only DSE deltas (design_explorer._apply_delta, applied from
orchestrator._handle_apply_exploration) update current_parameters directly
and never touch design_properties — by design (DA2: params-only candidates
work purely on the flat params dict). This leaves the one true input of
component_resolver.resolve_propulsion_parameters (the motors ComponentSpec)
stale the instant DSE elevates motor_count/per_motor_max_thrust_n/
per_actuator_torque_nm past what the component alone declares. The next,
possibly unrelated, physical iterate turn then re-derives from that stale
component and silently reverts the DSE elevation
(investigation_report_g5_dse_iterate_dual_truth.md).

sync_motors_component_from_params closes that gap by writing the DSE-elevated
values back into the component immediately after a params-only apply, so
every subsequent read of the component is current — no change needed in
IterateAction.run or param_definition_session, whose resolve_propulsion_
parameters call becomes correct automatically once its input stops going stale.

Call order at the one call site (orchestrator._handle_apply_exploration):
catalog_bind.invalidate_diverged_catalog_refs MUST run first, using the
still-stale component to correctly detect true SKU divergence, THEN this
sync brings the component's motor_count/thrust_n/torque_nm up to date. If
sync ran first, invalidate_diverged_catalog_refs would compare an
already-synced (hence never-diverging) property and never clear a stale
catalog_ref.
"""
from __future__ import annotations

from typing import Any

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def sync_motors_component_from_params(
    components: dict[str, ComponentSpec],
    params: dict[str, Any],
) -> dict[str, ComponentSpec]:
    """Update components["motors"]'s motor_count/thrust_n/torque_nm to match
    *params*, when they differ. Pure — returns the same dict unchanged when
    there's nothing to sync (no motors component, or nothing diverged);
    never mutates inputs, never invents a motors component that doesn't exist.

    Only the three propulsion fields component_resolver.resolve_propulsion_
    parameters can derive are touched (motor_count, and thrust_n OR torque_nm
    depending on output_magnitude) — power_w, kv_rating, weight_g, catalog_ref,
    and every other property are left exactly as they were.

    Synced properties are tagged source="calculated" (an existing, previously
    unused PropertyValue.source value — no schema change) to distinguish
    "DSE calculated this" from source="declared" (the user typed it). This is
    a data tag only; no Continuity/BOM copy change is made here (deferred,
    per contract §2.4).
    """
    motors = components.get("motors")
    if motors is None:
        return components

    updated_properties = dict(motors.properties)
    changed = False

    new_motor_count = params.get("motor_count")
    count_prop = motors.properties.get("motor_count")
    old_motor_count = count_prop.value if count_prop is not None else None
    if new_motor_count is not None and old_motor_count != new_motor_count:
        base = count_prop or PropertyValue(unit=None)
        updated_properties["motor_count"] = base.model_copy(
            update={"value": new_motor_count, "source": "calculated"}
        )
        changed = True

    if motors.output_magnitude == "thrust_n":
        new_thrust = params.get("per_motor_max_thrust_n")
        thrust_prop = motors.properties.get("thrust_n")
        old_thrust = thrust_prop.value if thrust_prop is not None else None
        if new_thrust is not None and old_thrust != new_thrust:
            base = thrust_prop or PropertyValue(unit="N")
            updated_properties["thrust_n"] = base.model_copy(
                update={"value": new_thrust, "source": "calculated"}
            )
            changed = True
    elif motors.output_magnitude == "torque_nm":
        # Latent path (Q5 of the investigation) — no EXPLORATION_GRIDS entry
        # references per_actuator_torque_nm today, so this branch is
        # currently unreachable in practice, kept for architectural parity
        # with resolve_propulsion_parameters' own torque extraction.
        new_torque = params.get("per_actuator_torque_nm")
        torque_prop = motors.properties.get("torque_nm")
        old_torque = torque_prop.value if torque_prop is not None else None
        if new_torque is not None and old_torque != new_torque:
            base = torque_prop or PropertyValue(unit="N*m")
            updated_properties["torque_nm"] = base.model_copy(
                update={"value": new_torque, "source": "calculated"}
            )
            changed = True

    if not changed:
        return components

    updated_motors = motors.model_copy(update={"properties": updated_properties})
    return {**components, "motors": updated_motors}
