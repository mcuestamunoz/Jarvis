"""Unit tests for component_sync.sync_motors_component_from_params (G5 fix).

Design authority: .jes/artifacts/implementation_contract_g5_fix_dse_component_sync.md
Investigation: .jes/artifacts/investigation_report_g5_dse_iterate_dual_truth.md
"""
from __future__ import annotations

from jarvis.core.component_sync import sync_motors_component_from_params
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _motors_spec(**props) -> ComponentSpec:
    return ComponentSpec(
        name="motors", component_type="propulsion_active", suggested_key="motors",
        completeness="high", source="declared", output_magnitude="thrust_n",
        properties=props,
    )


def test_no_motors_component_is_a_no_op():
    components = {"frame": ComponentSpec(name="frame", component_type="structure")}
    result = sync_motors_component_from_params(components, {"motor_count": 6})
    assert result is components


def test_no_divergence_returns_same_dict_object():
    motors = _motors_spec(
        motor_count=PropertyValue(value=4, confidence=0.9, source="declared"),
        thrust_n=PropertyValue(value=20.0, unit="N", confidence=0.9, source="declared"),
    )
    components = {"motors": motors}
    params = {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
    result = sync_motors_component_from_params(components, params)
    assert result is components


def test_motor_count_and_thrust_synced_and_tagged_calculated():
    motors = _motors_spec(
        motor_count=PropertyValue(value=4, confidence=0.9, source="declared"),
        thrust_n=PropertyValue(value=20.0, unit="N", confidence=0.9, source="declared"),
        power_w=PropertyValue(value=500.0, unit="W", confidence=0.9, source="declared"),
    )
    components = {"motors": motors}
    params = {"motor_count": 6, "per_motor_max_thrust_n": 30.0}

    result = sync_motors_component_from_params(components, params)

    assert result is not components
    synced = result["motors"]
    assert synced.properties["motor_count"].value == 6
    assert synced.properties["motor_count"].source == "calculated"
    assert synced.properties["thrust_n"].value == 30.0
    assert synced.properties["thrust_n"].source == "calculated"
    # Unit/confidence preserved from the prior property, only value+source change.
    assert synced.properties["thrust_n"].unit == "N"
    assert synced.properties["thrust_n"].confidence == 0.9
    # Untouched field survives verbatim.
    assert synced.properties["power_w"].value == 500.0
    assert synced.properties["power_w"].source == "declared"


def test_motor_count_only_change_does_not_touch_thrust():
    motors = _motors_spec(
        motor_count=PropertyValue(value=4, confidence=0.9, source="declared"),
        thrust_n=PropertyValue(value=20.0, unit="N", confidence=0.9, source="declared"),
    )
    components = {"motors": motors}
    params = {"motor_count": 8, "per_motor_max_thrust_n": 20.0}  # thrust unchanged

    result = sync_motors_component_from_params(components, params)

    synced = result["motors"]
    assert synced.properties["motor_count"].value == 8
    assert synced.properties["motor_count"].source == "calculated"
    assert synced.properties["thrust_n"].value == 20.0
    assert synced.properties["thrust_n"].source == "declared"  # untouched — no divergence


def test_missing_params_key_leaves_property_untouched():
    motors = _motors_spec(
        motor_count=PropertyValue(value=4, confidence=0.9, source="declared"),
        thrust_n=PropertyValue(value=20.0, unit="N", confidence=0.9, source="declared"),
    )
    components = {"motors": motors}
    result = sync_motors_component_from_params(components, {})
    assert result is components


def test_output_magnitude_torque_syncs_torque_not_thrust():
    motors = ComponentSpec(
        name="motors", component_type="traction_active", suggested_key="motors",
        completeness="high", source="declared", output_magnitude="torque_nm",
        properties={
            "motor_count": PropertyValue(value=4, confidence=0.9, source="declared"),
            "torque_nm": PropertyValue(value=1.5, unit="N*m", confidence=0.9, source="declared"),
        },
    )
    components = {"motors": motors}
    params = {"motor_count": 4, "per_actuator_torque_nm": 2.25}

    result = sync_motors_component_from_params(components, params)

    synced = result["motors"]
    assert synced.properties["torque_nm"].value == 2.25
    assert synced.properties["torque_nm"].source == "calculated"
    assert "thrust_n" not in synced.properties


def test_component_without_motor_count_property_gets_one_created():
    """A component that never had motor_count declared at all (e.g. count
    inferred purely from eligible-entry counting) still gets a synced
    property — no crash on a missing base PropertyValue to copy from."""
    motors = _motors_spec(
        thrust_n=PropertyValue(value=20.0, unit="N", confidence=0.9, source="declared"),
    )
    components = {"motors": motors}
    params = {"motor_count": 5, "per_motor_max_thrust_n": 20.0}

    result = sync_motors_component_from_params(components, params)

    synced = result["motors"]
    assert synced.properties["motor_count"].value == 5
    assert synced.properties["motor_count"].source == "calculated"
