"""ERF-1 Slice 2 — Evidence + subsystem mapping.

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 2:
  - exactly eight subsystem keys, no electronics/communications/integration
  - evidence flags separated from readiness verdict
  - ACCEPTED_WARNING_TYPES / G9-B path on catalog (+ propulsion)
  - overall rollup
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.engineering_readiness import (
    ACCEPTED_WARNING_TYPES,
    SUBSYSTEM_KEYS,
    build_engineering_readiness,
)
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


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


def _motor_spec(kv=None, catalog_ref=None):
    props = {}
    if kv is not None:
        props["kv_rating"] = PropertyValue(value=kv, unit="KV")
    return ComponentSpec(
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        properties=props,
        source="declared",
        catalog_ref=catalog_ref,
    )


def test_readiness_emits_exactly_nine_subsystems():
    """ERF-2 ★8: eight ERF-1 lines + electronics."""
    result = build_engineering_readiness(_project_state())
    assert set(result.subsystems.keys()) == set(SUBSYSTEM_KEYS)
    assert len(result.subsystems) == 9


def test_no_integration_or_communications_subsystem_lines():
    """ERF-2 ★8: electronics is expected now; integration/communications
    remain forbidden without new authority."""
    result = build_engineering_readiness(_project_state())
    assert "electronics" in result.subsystems
    forbidden = {"communications", "integration"}
    assert not (set(result.subsystems.keys()) & forbidden)


def test_evidence_and_verdict_are_separate_objects():
    result = build_engineering_readiness(_project_state())
    propulsion = result.subsystems["propulsion"]
    assert hasattr(propulsion, "evidence")
    assert hasattr(propulsion, "verdict")
    assert propulsion.evidence is not propulsion.verdict


def test_g9b_warning_type_catalog_subsystem():
    """Sim PASS + declared thrust covers floor + catalog query returns 0
    matches -> catalog (and propulsion) show WARNING + CATALOG-GAP-DEMOTED-POST-PASS,
    not INCOMPLETE."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 30.0,
            "motor_count": 6,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 9.1},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec(kv=2400)},
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED" for g in result.gaps)

    catalog = result.subsystems["catalog"]
    assert catalog.verdict == "WARNING"
    assert catalog.warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"
    assert catalog.warning_type in ACCEPTED_WARNING_TYPES

    propulsion = result.subsystems["propulsion"]
    assert propulsion.verdict == "WARNING"
    assert propulsion.warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"


def test_g9b_undemoted_catalog_gap_is_incomplete_not_warning():
    """Regression guard: PASS but declared thrust UNDER the floor must not be
    silently accepted — catalog line stays INCOMPLETE."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 2.0,
            "motor_count": 6,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 9.1},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec(kv=2400)},
        ),
    )
    result = build_engineering_readiness(state)
    catalog = result.subsystems["catalog"]
    assert catalog.verdict == "INCOMPLETE"
    assert catalog.warning_type is None


def test_assembly_ready_false_when_high_gap():
    state = _project_state(
        design_properties=_design_properties(
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    assert any(g.severity == "HIGH" for g in result.gaps)
    assert result.overall == "NOT_ASSEMBLY_READY"


def _fully_closed_components():
    frame = ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={"mass_kg": PropertyValue(value=0.4), "material": PropertyValue(value="carbono")},
        catalog_ref=CatalogRef(family="motor", sku="dummy"),
    )
    battery = ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        properties={"battery_capacity_wh": PropertyValue(value=100.0)},
    )
    fc = ComponentSpec(suggested_key="flight_controller", completeness="high", source="declared")
    sensors = ComponentSpec(suggested_key="sensors", completeness="high", source="declared")
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        properties={"diameter_in": PropertyValue(value=10.0)},
    )
    # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"] — declared
    # here so these "everything closed, no gaps" fixtures stay genuinely
    # gap-free (electronics/esc gap types land in ERF-2 Slice 3, not here).
    esc = ComponentSpec(
        suggested_key="esc", completeness="high", source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    return frame, battery, fc, sensors, propellers, esc


_FULLY_CLOSED_PARAMS = {
    "vehicle_type": "dron",
    "per_motor_max_thrust_n": 30.0,
    "motor_count": 6,
    "battery_capacity_wh": 100.0,
    "motor_power_w": 50.0,
}
_FULLY_CLOSED_RESULTS = {
    "simulation": {"status": "pass", "safety_margin_ratio": 9.1},
    "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5, "autonomy_min": 20.0},
}
_FULLY_CLOSED_BLOCKS = ["structure", "energy", "control", "propulsion"]


def test_assembly_ready_true_when_everything_pass_no_gaps():
    """Crafted fixture: every subsystem PASS, no gaps at all (motor catalog
    query finds a real match — kv/prop left unfiltered) -> ASSEMBLY_READY."""
    frame, battery, fc, sensors, propellers, esc = _fully_closed_components()
    motors = _motor_spec()  # no kv_rating -> unfiltered catalog query finds matches
    state = _project_state(
        current_parameters=dict(_FULLY_CLOSED_PARAMS),
        parsed_constraints={"max_weight_kg": 999.0},
        latest_results=_FULLY_CLOSED_RESULTS,
        design_properties=_design_properties(
            components={
                "frame": frame, "battery": battery, "flight_controller": fc,
                "sensors": sensors, "motors": motors, "propellers": propellers, "esc": esc,
            },
            system_blocks=_FULLY_CLOSED_BLOCKS, system_priority=_FULLY_CLOSED_BLOCKS,
        ),
    )
    result = build_engineering_readiness(state)
    assert result.gaps == [], [g.gap_id for g in result.gaps]
    assert result.overall == "ASSEMBLY_READY"


def test_demoted_catalog_gap_warns_catalog_propulsion_but_bom_keeps_not_ready():
    """★1/§5.3: ACCEPTED_WARNING_TYPES applies only to catalog/propulsion —
    "bom" is deliberately NOT in that closed list, even though the same gap
    also blocks bom[]. A demoted catalog gap therefore shows WARNING on
    catalog/propulsion but overall stays NOT_ASSEMBLY_READY via bom — the
    system is physically fine but not literally sourceable yet."""
    frame, battery, fc, sensors, propellers, esc = _fully_closed_components()
    motors = _motor_spec(kv=2400)  # kv+prop combo with zero catalog matches
    params = dict(_FULLY_CLOSED_PARAMS)
    params["propeller_diameter_in"] = 10.0
    state = _project_state(
        current_parameters=params,
        parsed_constraints={"max_weight_kg": 999.0},
        latest_results=_FULLY_CLOSED_RESULTS,
        design_properties=_design_properties(
            components={
                "frame": frame, "battery": battery, "flight_controller": fc,
                "sensors": sensors, "motors": motors, "propellers": propellers, "esc": esc,
            },
            system_blocks=_FULLY_CLOSED_BLOCKS, system_priority=_FULLY_CLOSED_BLOCKS,
        ),
    )
    result = build_engineering_readiness(state)
    non_catalog_gaps = [g for g in result.gaps if g.gap_type != "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert non_catalog_gaps == [], [g.gap_id for g in non_catalog_gaps]

    assert result.subsystems["catalog"].verdict == "WARNING"
    assert result.subsystems["propulsion"].verdict == "WARNING"
    assert result.subsystems["bom"].verdict == "INCOMPLETE"
    assert result.overall == "NOT_ASSEMBLY_READY"


def test_overall_not_ready_when_uncaccepted_warning_type_would_exist():
    """No warning_type outside the closed list can ever be produced — this is
    a structural guarantee test (only one accepted type exists in ERF-1)."""
    assert ACCEPTED_WARNING_TYPES == frozenset({"CATALOG-GAP-DEMOTED-POST-PASS"})
