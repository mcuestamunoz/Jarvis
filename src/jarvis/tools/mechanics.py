from __future__ import annotations

from jarvis.config import GRAVITY
from jarvis.schemas.tool_schema import ToolResult


def estimate_structure_mass(payload_kg: float, structure_mass_factor: float) -> ToolResult:
    structure_mass_kg = payload_kg * structure_mass_factor
    return ToolResult(
        tool_name="estimate_structure_mass",
        inputs={
            "payload_kg": payload_kg,
            "structure_mass_factor": structure_mass_factor,
        },
        outputs={"structure_mass_kg": round(structure_mass_kg, 4)},
    )


def calculate_total_mass(payload_kg: float, structure_mass_kg: float) -> ToolResult:
    total_mass_kg = payload_kg + structure_mass_kg
    return ToolResult(
        tool_name="calculate_total_mass",
        inputs={
            "payload_kg": payload_kg,
            "structure_mass_kg": structure_mass_kg,
        },
        outputs={"total_mass_kg": round(total_mass_kg, 4)},
    )


def calculate_weight(total_mass_kg: float) -> ToolResult:
    weight_n = total_mass_kg * GRAVITY
    return ToolResult(
        tool_name="calculate_weight",
        inputs={"total_mass_kg": total_mass_kg},
        outputs={"weight_n": round(weight_n, 4)},
    )


def calculate_required_force(weight_n: float, safety_factor: float) -> ToolResult:
    required_force_n = weight_n * safety_factor
    return ToolResult(
        tool_name="calculate_required_force",
        inputs={"weight_n": weight_n, "safety_factor": safety_factor},
        outputs={"required_force_n": round(required_force_n, 4)},
    )


def calculate_force_per_actuator(required_force_n: float, actuator_count: int) -> ToolResult:
    force_per_actuator_required_n = required_force_n / actuator_count
    return ToolResult(
        tool_name="calculate_force_per_actuator",
        inputs={"required_force_n": required_force_n, "actuator_count": actuator_count},
        outputs={"force_per_actuator_required_n": round(force_per_actuator_required_n, 4)},
    )


# Aerial domain wrappers — semantic aliases only, no formula duplication

def calculate_required_thrust(weight_n: float, safety_factor: float) -> ToolResult:
    result = calculate_required_force(weight_n, safety_factor)
    return ToolResult(
        tool_name="calculate_required_thrust",
        inputs=result.inputs,
        outputs={"required_thrust_n": result.outputs["required_force_n"]},
    )


def calculate_thrust_per_motor(required_thrust_n: float, motors: int) -> ToolResult:
    result = calculate_force_per_actuator(required_thrust_n, motors)
    return ToolResult(
        tool_name="calculate_thrust_per_motor",
        inputs={"required_thrust_n": required_thrust_n, "motors": motors},
        outputs={"thrust_per_motor_required_n": result.outputs["force_per_actuator_required_n"]},
    )


# Ground domain — traction force conversion

def calculate_traction_force_from_torque(
    torque_nm: float,
    wheel_radius_m: float,
    gear_ratio: float,
) -> ToolResult:
    """Convert actuator torque to traction force at wheel contact.

    Formula: F = (torque_nm * gear_ratio) / wheel_radius_m
    """
    traction_force_n = (torque_nm * gear_ratio) / wheel_radius_m
    return ToolResult(
        tool_name="calculate_traction_force_from_torque",
        inputs={
            "torque_nm": torque_nm,
            "wheel_radius_m": wheel_radius_m,
            "gear_ratio": gear_ratio,
        },
        outputs={"traction_force_n": round(traction_force_n, 4)},
    )
