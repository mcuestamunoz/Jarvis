"""Domain registry selector — hybrid lookup by vehicle_type and/or text heuristic.

Resolves which ComponentRuleRegistry to use given available context.
Priority:
  1. vehicle_type explicit match → deterministic
  2. text heuristic (keyword scan) → probabilistic fallback
  3. default → aerial_registry (backward compatible)

Usage
-----
>>> from jarvis.domains.registry_selector import get_registry
>>> registry = get_registry(vehicle_type="drone")
>>> registry = get_registry(vehicle_type=None, text="4 ruedas motrices 50Nm")
>>> registry = get_registry()  # → aerial_registry (default)
"""
from __future__ import annotations

from jarvis.core.component_rules import ComponentRuleRegistry
from jarvis.domains.aerial import aerial_registry
from jarvis.domains.ground import ground_registry


# ── Static vehicle_type → registry map ───────────────────────────────────────
# vehicle_type acts as a logical system category for domain routing, not just
# vehicle classification. Any string identifier can be mapped here regardless
# of whether the system is a vehicle: "home_iot", "robot_arm", etc. would map
# to future registries the same way. Only rename to system_type when a 3rd+
# domain forces the ambiguity to matter.

_VEHICLE_TYPE_MAP: dict[str, ComponentRuleRegistry] = {
    # Aerial
    "drone":     aerial_registry,
    "dron":      aerial_registry,
    "uav":       aerial_registry,
    "quadcopter": aerial_registry,
    "multirotor": aerial_registry,
    "hexacopter": aerial_registry,
    "octocopter": aerial_registry,
    "fixed_wing": aerial_registry,
    # Ground
    "rover":     ground_registry,
    "car":       ground_registry,
    "coche":     ground_registry,
    "vehicle":   ground_registry,
    "ground":    ground_registry,
    "robot":     ground_registry,
    "ugv":       ground_registry,
}

# ── Text heuristic keyword sets ───────────────────────────────────────────────

_GROUND_KEYWORDS = frozenset({
    "rueda", "ruedas", "wheel", "wheels",
    "coche", "car", "rover", "ugv",
    "rpm", "par", "torque", "nm",
    "traccion", "tracción", "traction", "motriz",
    "neumatico", "neumático", "tyre", "tire",
})

_AERIAL_KEYWORDS = frozenset({
    "helice", "hélice", "propeller", "props",
    "kv", "uav", "drone", "dron",
    "vuelo", "flight", "quadcopter",
    "brushless",
})


# ── Public API ────────────────────────────────────────────────────────────────

def get_registry(
    vehicle_type: str | None = None,
    text: str | None = None,
) -> ComponentRuleRegistry:
    """Return the best ComponentRuleRegistry for the given context.

    Parameters
    ----------
    vehicle_type : explicit system type string (e.g. "drone", "rover").
                   Matched case-insensitively against _VEHICLE_TYPE_MAP.
    text         : freeform text to scan for domain keywords when vehicle_type
                   is absent or unrecognised.

    Returns
    -------
    ComponentRuleRegistry
        aerial_registry (default), ground_registry, or any registered domain.
    """
    # 1. Deterministic: vehicle_type known
    if vehicle_type:
        vt = vehicle_type.lower().strip()
        registry = _VEHICLE_TYPE_MAP.get(vt)
        if registry is not None:
            return registry

    # 2. Heuristic: scan text for domain signals
    if text:
        t = text.lower()
        ground_hits = sum(1 for kw in _GROUND_KEYWORDS if kw in t)
        aerial_hits = sum(1 for kw in _AERIAL_KEYWORDS if kw in t)
        if ground_hits > aerial_hits:
            return ground_registry
        if aerial_hits > ground_hits:
            return aerial_registry

    # 3. Default: aerial (backward compatible)
    return aerial_registry
