"""
Domain-agnostic component resolver.

Converts declarative ComponentSpec entries into ephemeral physical overrides
that are applied during a single calculation pass and never persisted.

``PhysicalOverride`` is the generic abstraction; ``PropulsionOverride`` is an
alias kept for backward compatibility with existing tests and callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Component types recognised as active actuators across all domains
# aerial: "propulsion_active" — ground: "traction_active"
_ACTIVE_ACTUATOR_TYPES = frozenset({"propulsion_active", "traction_active"})

# Completeness levels that make a component eligible for physical override
_ELIGIBLE_COMPLETENESS = {"medium", "high"}


@dataclass(frozen=True)
class PhysicalOverride:
    """Ephemeral overrides derived from design_properties.components.

    Never persisted — applied only during a single calculation pass.

    Field names use the current calculation_engine vocabulary for backward
    compatibility.  Generic-domain aliases are exposed as properties.
    """
    motors: int | None
    per_motor_max_thrust_n: float | None
    per_actuator_torque_nm: float | None = None
    trace: dict[str, Any] = field(default_factory=dict)

    @property
    def has_any(self) -> bool:
        return (
            self.motors is not None
            or self.per_motor_max_thrust_n is not None
            or self.per_actuator_torque_nm is not None
        )

    # ── Generic-domain aliases (Fase 3 will flip these to be primary) ────────
    @property
    def actuator_count(self) -> int | None:
        return self.motors

    @property
    def max_force_per_actuator_n(self) -> float | None:
        return self.per_motor_max_thrust_n

    def apply_to(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Return a new parameters dict with overrides applied. Original is not mutated."""
        if not self.has_any:
            return parameters
        updated = dict(parameters)
        if self.motors is not None:
            updated["motor_count"] = self.motors
        if self.per_motor_max_thrust_n is not None:
            updated["per_motor_max_thrust_n"] = self.per_motor_max_thrust_n
        if self.per_actuator_torque_nm is not None:
            updated["per_actuator_torque_nm"] = self.per_actuator_torque_nm
        return updated


# Alias — new domain-agnostic name for this type
PropulsionOverride = PhysicalOverride


def resolve_propulsion_parameters(components: dict[str, Any]) -> PhysicalOverride:
    """Convert declarative ComponentSpec entries into ephemeral physical overrides.

    Activation rule:
      An entry is ELIGIBLE when:
        - completeness in ("medium", "high"), OR
        - output_magnitude key exists in properties with source="declared"
      Entries with completeness="low" and no declared magnitude value are ignored.

    Actuator count resolution (priority order):
      1. properties["motor_count"].value — explicit count declared by user
      2. Count of eligible active actuator entries

    Force resolution:
      Only when output_magnitude == "thrust_n" AND the property value has
      source="declared".  Other magnitudes (e.g. "torque_nm") are extracted
      but not converted — the resolver skips them without error.
      No text heuristics — if not explicit, no override.

    Returns a PhysicalOverride with trace for UX visibility.
    """
    if not components:
        return PhysicalOverride(
            motors=None,
            per_motor_max_thrust_n=None,
            trace={"reason": "no_components"},
        )

    eligible: list[tuple[str, dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []

    for key, entry in components.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("component_type") not in _ACTIVE_ACTUATOR_TYPES:
            continue

        completeness = entry.get("completeness", "low")
        properties = entry.get("properties") or {}
        output_magnitude = entry.get("output_magnitude")
        magnitude_prop = properties.get(output_magnitude) if output_magnitude and isinstance(properties, dict) else None
        has_declared_magnitude = (
            isinstance(magnitude_prop, dict)
            and magnitude_prop.get("source") == "declared"
            and magnitude_prop.get("value") is not None
        )

        if completeness in _ELIGIBLE_COMPLETENESS or has_declared_magnitude:
            eligible.append((key, entry))
        else:
            skipped.append({"key": key, "reason": f"completeness={completeness}, no declared {output_magnitude or 'output_magnitude'}"})

    if not eligible:
        return PhysicalOverride(
            motors=None,
            per_motor_max_thrust_n=None,
            trace={"reason": "no_eligible_components", "skipped": skipped},
        )

    # ── Actuator count ───────────────────────────────────────────────────────
    actuator_count: int | None = None
    motors_source: str = ""

    for key, entry in eligible:
        properties = entry.get("properties") or {}
        count_prop = properties.get("motor_count") if isinstance(properties, dict) else None
        if isinstance(count_prop, dict) and count_prop.get("value") is not None:
            try:
                actuator_count = int(count_prop["value"])
                motors_source = f"properties.motor_count on '{key}'"
                break
            except (TypeError, ValueError):
                pass

    if actuator_count is None and len(eligible) > 0:
        actuator_count = len(eligible)
        motors_source = f"count of eligible propulsion_active entries ({len(eligible)})"

    # ── Force per actuator ───────────────────────────────────────────────────
    # Resolved when output_magnitude == "thrust_n" (direct force, aerial).
    # For "torque_nm" the declared value is extracted and passed to the engine
    # via per_actuator_torque_nm; the conversion is the engine's responsibility.
    # Other magnitudes are counted but neither converted nor extracted.
    # No text heuristics — if not explicit, no override.
    max_force_per_actuator_n: float | None = None
    thrust_source: str = ""
    per_actuator_torque_nm: float | None = None
    torque_source: str = ""
    eligible_for_count_only: list[dict[str, Any]] = []
    # Per-component resolution audit: one entry per eligible component
    # status values: "force_resolved" | "count_only" | "missing_parameters"
    force_resolution_entries: list[dict[str, Any]] = []
    _force_found = False  # first-wins flag; does not stop the audit loop

    for key, entry in eligible:
        output_magnitude = entry.get("output_magnitude")
        if output_magnitude != "thrust_n":
            count_only_entry: dict[str, Any] = {
                "key": key,
                "reason": f"output_magnitude={output_magnitude} not supported for force calculation",
            }
            component_status = "count_only"
            # Extract torque_nm when available so the engine can convert it
            if output_magnitude == "torque_nm":
                properties = entry.get("properties") or {}
                torque_prop = properties.get("torque_nm") if isinstance(properties, dict) else None
                if (
                    isinstance(torque_prop, dict)
                    and torque_prop.get("source") == "declared"
                    and torque_prop.get("value") is not None
                ):
                    try:
                        extracted = float(torque_prop["value"])
                        if per_actuator_torque_nm is None:
                            per_actuator_torque_nm = extracted
                            torque_source = f"properties.torque_nm on '{key}'"
                            count_only_entry["torque_nm_extracted"] = extracted
                            component_status = "missing_parameters"  # torque extracted, conversion deferred to engine
                    except (TypeError, ValueError):
                        pass
            eligible_for_count_only.append(count_only_entry)
            _detail_reason = "missing_transmission_parameters" if component_status == "missing_parameters" else f"output_magnitude={output_magnitude}"
            force_resolution_entries.append({"key": key, "force_resolution_status": component_status, "reason": _detail_reason})
            continue  # resolver does not convert non-force magnitudes
        # output_magnitude == "thrust_n"
        properties = entry.get("properties") or {}
        thrust_prop = properties.get("thrust_n") if isinstance(properties, dict) else None
        if (
            not _force_found
            and isinstance(thrust_prop, dict)
            and thrust_prop.get("source") == "declared"
            and thrust_prop.get("value") is not None
        ):
            try:
                max_force_per_actuator_n = float(thrust_prop["value"])
                thrust_source = f"properties.thrust_n on '{key}'"
                _force_found = True
                force_resolution_entries.append({"key": key, "force_resolution_status": "force_resolved", "reason": "thrust_n_declared"})
                continue
            except (TypeError, ValueError):
                pass
        # thrust_n magnitude but no declared value → count_only
        force_resolution_entries.append({"key": key, "force_resolution_status": "count_only", "reason": "thrust_n_not_declared"})

    # Overall force_resolution_status: best status across all eligible entries
    _status_rank = {"force_resolved": 3, "missing_parameters": 2, "count_only": 1}
    overall_force_status = (
        max((e["force_resolution_status"] for e in force_resolution_entries), key=lambda s: _status_rank.get(s, 0))
        if force_resolution_entries
        else "count_only"
    )

    trace: dict[str, Any] = {
        "eligible_count": len(eligible),
        "skipped": skipped,
        "eligible_for_count_only": eligible_for_count_only,
        "force_resolution_status": overall_force_status,
        "force_resolution_detail": force_resolution_entries,
        "motors": {"value": actuator_count, "source": motors_source} if actuator_count is not None else {"value": None, "source": "not_resolved"},
        "per_motor_max_thrust_n": (
            {"value": max_force_per_actuator_n, "source": thrust_source}
            if max_force_per_actuator_n is not None
            else {"value": None, "source": "not_resolved"}
        ),
        "per_actuator_torque_nm": (
            {"value": per_actuator_torque_nm, "source": torque_source}
            if per_actuator_torque_nm is not None
            else {"value": None, "source": "not_extracted"}
        ),
    }

    return PhysicalOverride(
        motors=actuator_count,
        per_motor_max_thrust_n=max_force_per_actuator_n,
        per_actuator_torque_nm=per_actuator_torque_nm,
        trace=trace,
    )


# Generic alias — use this in new non-aerial code
resolve_physical_parameters = resolve_propulsion_parameters

