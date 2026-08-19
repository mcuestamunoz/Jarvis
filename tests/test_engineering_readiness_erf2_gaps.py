"""ERF-2 Slice 3 — new gap types wired into build_engineering_readiness.

Covers .jes/artifacts/implementation_contract_erf2.md §10 (gap-level rows):
  test_gap_esc_undefined_not_incompatible
  test_gap_esc_undersized_incompatible
  test_sim_pass_esc_undersized_not_ready
  test_erf1_gaps_still_emit
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.engineering_readiness import build_engineering_readiness
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


def _battery_declared(capacity_wh=50.0):
    return ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        properties={"battery_capacity_wh": PropertyValue(value=capacity_wh)},
    )


def _esc_declared(current_a=None):
    props = {}
    if current_a is not None:
        props["current_a"] = PropertyValue(value=current_a, unit="A")
    return ComponentSpec(suggested_key="esc", completeness="high", source="declared", properties=props)


def test_gap_esc_undefined_not_incompatible():
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "motor_count": 4},
        design_properties=_design_properties(
            components={"motors": _motors_declared(), "battery": _battery_declared()},
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-ESC-UNDEFINED" for g in result.gaps)
    assert not any(g.gap_type == "GAP-ESC-UNDERSIZED" for g in result.gaps)
    assert result.subsystems["electronics"].verdict == "INCOMPLETE"


def test_gap_esc_undersized_incompatible():
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,       # 30A/motor at 7.4V
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motors_declared(),
                "battery": _battery_declared(),
                "esc": _esc_declared(current_a=10.0),  # well under 30A
            },
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-ESC-UNDERSIZED" for g in result.gaps)
    assert not any(g.gap_type == "GAP-ESC-UNDEFINED" for g in result.gaps)
    assert result.subsystems["electronics"].verdict == "INCOMPATIBLE"
    assert result.subsystems["propulsion"].verdict == "INCOMPATIBLE"
    # design §6.2: energy is in blocks[] but not in verdict impact — pack is fine.
    assert result.subsystems["energy"].verdict != "INCOMPATIBLE"


def test_sim_pass_esc_undersized_not_ready():
    """★6: sim PASS does not suppress an ESC-undersized INCOMPATIBLE — physics
    and assembly-readiness answer different questions."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 3.0},
            "calculations": {},
        },
        design_properties=_design_properties(
            components={
                "motors": _motors_declared(),
                "battery": _battery_declared(),
                "esc": _esc_declared(current_a=10.0),
            },
        ),
    )
    result = build_engineering_readiness(state)
    assert result.subsystems["propulsion"].verdict == "INCOMPATIBLE"
    assert result.subsystems["electronics"].verdict == "INCOMPATIBLE"
    assert result.overall == "NOT_ASSEMBLY_READY"


def test_gap_battery_discharge_exceeded():
    from jarvis.schemas.action_schema import CatalogRef

    battery = ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="battery", sku="lipo_2s_850mah"),  # limit ~63.75A
    )
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,  # 30A/motor -> 120A total, exceeds 63.75A
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={"motors": _motors_declared(), "battery": battery},
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-BATTERY-DISCHARGE-EXCEEDED" for g in result.gaps)
    assert result.subsystems["energy"].verdict == "INCOMPATIBLE"


def test_gap_prop_motor_mismatch():
    from jarvis.schemas.action_schema import CatalogRef

    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="motor", sku="brotherhobby_avenger_2500"),  # 5in
    )
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="propeller", sku="apc_10x4_5"),  # 10in, mismatch
    )
    state = _project_state(
        design_properties=_design_properties(components={"motors": motors, "propellers": propellers}),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-PROP-MOTOR-MISMATCH" for g in result.gaps)
    assert result.subsystems["propulsion"].verdict == "INCOMPATIBLE"
    assert result.subsystems["catalog"].verdict == "INCOMPATIBLE"


def test_erf1_gaps_still_emit():
    """ERF-1's six gap types must still compose correctly alongside ERF-2's four."""
    state = _project_state(
        parsed_constraints={"max_weight_kg": 1.0},
        current_parameters={"vehicle_type": "dron"},
        latest_results={
            "simulation": {"status": "fail", "warnings": ["margen insuficiente"]},
            "calculations": {"total_mass_kg": 3.0},
        },
        design_properties=_design_properties(
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    gap_types = {g.gap_type for g in result.gaps}
    assert "GAP-SIM-NOT-PASS" in gap_types
    assert "GAP-REQUIREMENTS-UNMET" in gap_types
    assert "GAP-ARCH-BLOCK-INCOMPLETE" in gap_types
    assert "GAP-BOM-MISSING-COMPONENT" in gap_types


def test_no_incompatible_when_compatibility_all_clean():
    """Regression guard: no ERF-2 gap fires and no subsystem shows
    INCOMPATIBLE when the compatibility authority is all clean/unverifiable
    (e.g. no ESC/battery/motor evidence declared at all)."""
    state = _project_state()
    result = build_engineering_readiness(state)
    erf2_gap_types = {
        "GAP-ESC-UNDEFINED", "GAP-ESC-UNDERSIZED",
        "GAP-BATTERY-DISCHARGE-EXCEEDED", "GAP-PROP-MOTOR-MISMATCH",
    }
    assert not ({g.gap_type for g in result.gaps} & erf2_gap_types)
    assert all(s.verdict != "INCOMPATIBLE" for s in result.subsystems.values())
