from __future__ import annotations

from jarvis.schemas.tool_schema import ToolResult

# ── Aerodynamics domain ───────────────────────────────────────────────────────
# Simplified propeller thrust model (Level 1).
# Formula: T = Ct · ρ · n² · D⁴   where n = rpm / 60
# Default Ct ≈ 0.12 covers typical hobby/UAV propellers.
# For higher accuracy the caller can override ct and air_density.


def calculate_thrust_from_propeller(
    diameter_m: float,
    rpm: float,
    ct: float = 0.12,
    air_density: float = 1.225,
) -> ToolResult:
    """Estimate per-motor thrust from propeller geometry (simplified aerodynamic model).

    Parameters
    ----------
    diameter_m:
        Propeller diameter in metres.
    rpm:
        Motor rotational speed in revolutions per minute.
    ct:
        Dimensionless thrust coefficient (default 0.12, typical for UAV props).
    air_density:
        Air density in kg/m³ (default 1.225 at sea level, 15 °C).

    Returns
    -------
    ToolResult with ``thrust_n`` in outputs.
    """
    n = rpm / 60.0
    thrust_n = ct * air_density * (n ** 2) * (diameter_m ** 4)
    return ToolResult(
        tool_name="calculate_thrust_from_propeller",
        inputs={
            "diameter_m": diameter_m,
            "rpm": rpm,
            "ct": ct,
            "air_density": air_density,
        },
        outputs={"thrust_n": round(thrust_n, 6)},
    )
