from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jarvis.core.parameter_requirements import MISSING_PROPELLER_PARAMETERS
from jarvis.schemas.tool_schema import CalculationBundle, ToolResult

from jarvis.tools.aerodynamics import calculate_thrust_from_propeller
from jarvis.tools.electricity import calculate_autonomy_min
from jarvis.tools.mechanics import (
    calculate_required_thrust,
    calculate_thrust_per_motor,
    calculate_total_mass,
    calculate_traction_force_from_torque,
    calculate_weight,
    estimate_structure_mass,
)

# Vehicle types whose primary force mechanism is propulsion (motors/thrust/propeller).
# All other vehicle types fall back to the transmission domain (torque→force).
AERIAL_VEHICLE_TYPES: frozenset[str] = frozenset({
    "dron", "drone", "uav", "quadcopter", "multirotor", "helicopter", "aerial",
})

# Parameters that indicate propeller-path intent. If any is present in the inputs
# and the aerial force resolution path fails, emit missing_propeller_parameters
# (specific) instead of missing_propulsion_parameters (generic).
_PROPELLER_HINT_PARAMS: frozenset[str] = frozenset({
    "propeller_diameter_m", "propeller_diameter_in", "propeller_rpm",
})


class CalculationEngine:
    def build(self, parameters: Mapping[str, Any]) -> CalculationBundle:
        payload_kg = float(parameters["payload_kg"])
        structure_mass_override_kg = parameters.get("structure_mass_override_kg")
        tool_results = []

        if structure_mass_override_kg is None:
            structure_mass = estimate_structure_mass(
                payload_kg,
                float(parameters["structure_mass_factor"]),
            )
            tool_results.append(structure_mass)
            structure_mass_kg = structure_mass.outputs["structure_mass_kg"]
        else:
            structure_mass_kg = round(float(structure_mass_override_kg), 4)

        # U1: battery mass enters total mass. Derived from battery_capacity_wh via
        # estimate_battery_mass_kg (150 Wh/kg LiPo). Zero when battery not declared.
        battery_mass_kg = round(float(parameters.get("battery_mass_kg") or 0.0), 4)

        total_mass = calculate_total_mass(payload_kg, structure_mass_kg + battery_mass_kg)
        tool_results.append(total_mass)
        total_mass_kg = total_mass.outputs["total_mass_kg"]

        weight = calculate_weight(total_mass_kg)
        tool_results.append(weight)
        weight_n = weight.outputs["weight_n"]

        required_thrust = calculate_required_thrust(weight_n, float(parameters["safety_factor"]))
        tool_results.append(required_thrust)
        required_thrust_n = required_thrust.outputs["required_thrust_n"]

        motors_raw = parameters.get("actuator_count") or parameters.get("motor_count")
        motors: int | None = int(motors_raw) if motors_raw is not None else None

        # Resolve force per actuator — aerial path (direct thrust) or ground path (torque → force)
        per_motor_max_thrust_n: float | None = None
        per_motor_max_thrust_n_raw = parameters.get("max_force_per_actuator_n") or parameters.get("per_motor_max_thrust_n")

        if per_motor_max_thrust_n_raw is not None:
            per_motor_max_thrust_n = float(per_motor_max_thrust_n_raw)
        else:
            per_actuator_torque_nm = parameters.get("per_actuator_torque_nm")
            wheel_radius_m = parameters.get("wheel_radius_m")
            gear_ratio = parameters.get("gear_ratio")
            if per_actuator_torque_nm is not None:
                if wheel_radius_m is not None and gear_ratio is not None:
                    traction = calculate_traction_force_from_torque(
                        float(per_actuator_torque_nm),
                        float(wheel_radius_m),
                        float(gear_ratio),
                    )
                    tool_results.append(traction)
                    per_motor_max_thrust_n = traction.outputs["traction_force_n"]
                else:
                    # Torque extracted but conversion params missing — engine cannot complete
                    tool_results.append(ToolResult(
                        tool_name="missing_transmission_parameters",
                        inputs={"per_actuator_torque_nm": per_actuator_torque_nm},
                        outputs={"reason": "wheel_radius_m and/or gear_ratio not in parameters"},
                    ))
            else:
                # No direct thrust, no torque — try aerodynamic inference from propeller geometry.
                # Accept diameter in inches (user-facing) or metres (internal canonical).
                propeller_diameter_m = parameters.get("propeller_diameter_m")
                if propeller_diameter_m is None:
                    diameter_in = parameters.get("propeller_diameter_in")
                    if diameter_in is not None:
                        propeller_diameter_m = float(diameter_in) * 0.0254
                propeller_rpm = parameters.get("propeller_rpm")
                # U2: derive RPM from KV rating and battery cell count when not declared.
                # Formula: RPM ≈ KV × V_nominal × 0.85 (85% load factor for multirotor hover).
                # V_nominal = cells × 3.7 V (LiPo nominal per cell).
                if propeller_rpm is None:
                    motor_kv = parameters.get("motor_kv_rating")
                    batt_cells = parameters.get("battery_cell_count")
                    if motor_kv is not None and batt_cells is not None:
                        estimated_voltage = float(batt_cells) * 3.7
                        propeller_rpm = float(motor_kv) * estimated_voltage * 0.85
                if propeller_diameter_m is not None and propeller_rpm is not None:
                    prop_ct = float(parameters.get("propeller_ct") or 0.12)
                    prop_air_density = float(parameters.get("air_density_kg_m3") or 1.225)
                    propeller_result = calculate_thrust_from_propeller(
                        float(propeller_diameter_m),
                        float(propeller_rpm),
                        prop_ct,
                        prop_air_density,
                    )
                    tool_results.append(propeller_result)
                    per_motor_max_thrust_n = propeller_result.outputs["thrust_n"]
                else:
                    # No force resolution path found. Emit a domain-specific reason code
                    # so downstream consumers (simulator, reasoning) know WHY, not just THAT.
                    vt = str(parameters.get("vehicle_type") or "").lower()
                    has_propeller_hint = any(
                        parameters.get(k) is not None
                        for k in _PROPELLER_HINT_PARAMS
                    )
                    if vt in AERIAL_VEHICLE_TYPES and has_propeller_hint:
                        # Propeller path was attempted (user declared some propeller data)
                        # but diameter or rpm is still missing — specific reason code.
                        missing_reason = MISSING_PROPELLER_PARAMETERS
                    elif vt in AERIAL_VEHICLE_TYPES:
                        # Aerial vehicle, no propeller data at all — generic propulsion gap.
                        missing_reason = "missing_propulsion_parameters"
                    else:
                        missing_reason = "missing_transmission_parameters"
                    tool_results.append(ToolResult(
                        tool_name=missing_reason,
                        inputs={"vehicle_type": vt, "motors": motors},
                        outputs={"reason": "no force resolution path: no thrust, no torque, no propeller geometry"},
                    ))

        if motors is not None:
            thrust_per_motor = calculate_thrust_per_motor(required_thrust_n, motors)
            tool_results.append(thrust_per_motor)
            thrust_per_motor_required_n: float | None = thrust_per_motor.outputs["thrust_per_motor_required_n"]
        else:
            thrust_per_motor_required_n = None
        available_total_thrust_n = round(motors * per_motor_max_thrust_n, 4) if (motors is not None and per_motor_max_thrust_n is not None) else None

        # Resolve energy autonomy — requires battery_capacity_wh + motor_power_w
        autonomy_min: float | None = None
        battery_capacity_wh = parameters.get("battery_capacity_wh")
        motor_power_w = parameters.get("motor_power_w")
        if battery_capacity_wh is not None and motor_power_w is not None and motors is not None:
            total_power_w = float(motor_power_w) * motors
            energy_result = calculate_autonomy_min(float(battery_capacity_wh), total_power_w)
            tool_results.append(energy_result)
            autonomy_min = energy_result.outputs["autonomy_min"]
        else:
            tool_results.append(ToolResult(
                tool_name="missing_energy_parameters",
                inputs={"battery_capacity_wh": battery_capacity_wh, "motor_power_w": motor_power_w},
                outputs={"reason": "battery_capacity_wh and/or motor_power_w not in parameters"},
            ))

        return CalculationBundle(
            vehicle_type=str(parameters["vehicle_type"]),
            payload_kg=payload_kg,
            structure_mass_kg=structure_mass_kg,
            total_mass_kg=total_mass_kg,
            weight_n=weight_n,
            required_thrust_n=required_thrust_n,
            motors=motors,
            thrust_per_motor_required_n=thrust_per_motor_required_n,
            available_total_thrust_n=available_total_thrust_n,
            autonomy_min=autonomy_min,
            tool_results=tool_results,
        )
