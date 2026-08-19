"""ERF-2 Slice 3 — subsystem-level assertions (electronics line, nine keys,
mutual exclusion, evidence separation).

Covers .jes/artifacts/implementation_contract_erf2.md §10:
  test_nine_subsystems_exactly
  (electronics evidence/verdict separation, mutual exclusion table §6.0)
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.engineering_readiness import SUBSYSTEM_KEYS, build_engineering_readiness
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _design_properties(**kwargs):
    defaults = dict(components={}, system_blocks=[], system_priority=[])
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _project_state(**kwargs):
    defaults = dict(
        current_parameters={"vehicle_type": "dron"},
        parsed_constraints={},
        latest_results={"simulation": {}, "calculations": {}},
        design_properties=_design_properties(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _motors_declared():
    return ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )


def _esc_declared(current_a=None):
    props = {}
    if current_a is not None:
        props["current_a"] = PropertyValue(value=current_a, unit="A")
    return ComponentSpec(suggested_key="esc", completeness="high", source="declared", properties=props)


def test_nine_subsystems_exactly():
    result = build_engineering_readiness(_project_state())
    assert list(SUBSYSTEM_KEYS) == [
        "requirements", "architecture", "structure", "propulsion",
        "energy", "electronics", "control", "catalog", "bom",
    ]
    assert set(result.subsystems.keys()) == set(SUBSYSTEM_KEYS)
    forbidden = {"integration", "communications", "sensors"}
    assert not (set(result.subsystems.keys()) & forbidden)


def test_electronics_evidence_separated_from_verdict():
    state = _project_state(
        design_properties=_design_properties(
            components={"motors": _motors_declared(), "esc": _esc_declared(current_a=30.0)},
        ),
    )
    result = build_engineering_readiness(state)
    electronics = result.subsystems["electronics"]
    assert electronics.evidence.defined is True
    assert hasattr(electronics, "verdict")
    assert electronics.evidence is not electronics.verdict


def test_electronics_unverifiable_when_no_esc_and_no_prerequisites():
    """No motors/battery evidence at all -> flight-eval prerequisites not met
    -> esc_presence 'unverifiable' -> no GAP-ESC-UNDEFINED -> electronics line
    is INCOMPLETE only via 'not defined' fallback, never a false INCOMPATIBLE."""
    state = _project_state()
    result = build_engineering_readiness(state)
    electronics = result.subsystems["electronics"]
    assert electronics.verdict != "INCOMPATIBLE"


def test_esc_mutual_exclusion_missing_vs_undersized():
    """§6.0 mutual exclusion table: esc missing -> UNDEFINED only, never
    UNDERSIZED, regardless of other evidence being present."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron", "motor_count": 4,
            "motor_power_w": 222.0, "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motors_declared(),
                "battery": ComponentSpec(
                    suggested_key="battery", completeness="high", source="declared",
                    properties={"battery_capacity_wh": PropertyValue(value=50.0)},
                ),
            },
        ),
    )
    result = build_engineering_readiness(state)
    gap_types = {g.gap_type for g in result.gaps}
    assert "GAP-ESC-UNDEFINED" in gap_types
    assert "GAP-ESC-UNDERSIZED" not in gap_types


def test_esc_compatible_no_gap_no_incompatible_verdict():
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron", "motor_count": 4,
            "motor_power_w": 222.0, "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motors_declared(),
                "battery": ComponentSpec(
                    suggested_key="battery", completeness="high", source="declared",
                    properties={"battery_capacity_wh": PropertyValue(value=50.0)},
                ),
                "esc": _esc_declared(current_a=90.0),  # well above 30A/motor demand
            },
        ),
    )
    result = build_engineering_readiness(state)
    gap_types = {g.gap_type for g in result.gaps}
    assert "GAP-ESC-UNDEFINED" not in gap_types
    assert "GAP-ESC-UNDERSIZED" not in gap_types
    assert result.subsystems["electronics"].verdict != "INCOMPATIBLE"


def test_esc_undersized_energy_line_not_incompatible():
    """GAP-ESC-UNDERSIZED blocks energy in blocks[] but verdict impact is
    electronics + propulsion only (design §6.2)."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron", "motor_count": 4,
            "motor_power_w": 222.0, "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motors_declared(),
                "battery": ComponentSpec(
                    suggested_key="battery", completeness="high", source="declared",
                    properties={"battery_capacity_wh": PropertyValue(value=50.0)},
                ),
                "esc": _esc_declared(current_a=10.0),
            },
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-ESC-UNDERSIZED" for g in result.gaps)
    assert result.subsystems["energy"].verdict != "INCOMPATIBLE"
    assert result.subsystems["electronics"].verdict == "INCOMPATIBLE"
