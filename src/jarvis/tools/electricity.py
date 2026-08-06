from __future__ import annotations

from jarvis.schemas.tool_schema import ToolResult


# Energy domain — battery mass estimation

# Conservative LiPo energy density (Wh/kg).
# Real range: 120–200 Wh/kg. 150 is a safe mid-range for 4S–6S packs.
LIPO_ENERGY_DENSITY_WH_KG: float = 150.0


def estimate_battery_mass_kg(capacity_wh: float) -> float:
    """Estimate battery mass from capacity using LiPo energy density.

    Returns 0.0 for non-positive capacity to avoid division errors.
    """
    if capacity_wh <= 0.0:
        return 0.0
    return round(capacity_wh / LIPO_ENERGY_DENSITY_WH_KG, 3)


# Energy domain — battery autonomy

def calculate_autonomy_min(battery_capacity_wh: float, total_power_w: float) -> ToolResult:
    """Calculate operational autonomy in minutes.

    Formula: autonomy_min = (battery_capacity_wh / total_power_w) * 60
    """
    autonomy_min = (battery_capacity_wh / total_power_w) * 60.0 if total_power_w > 0 else 0.0
    return ToolResult(
        tool_name="calculate_autonomy_min",
        inputs={
            "battery_capacity_wh": battery_capacity_wh,
            "total_power_w": total_power_w,
        },
        outputs={"autonomy_min": round(autonomy_min, 4)},
    )
