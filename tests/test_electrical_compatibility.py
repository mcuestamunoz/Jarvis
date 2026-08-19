"""ERF-2 Slice 1 — Electrical Compatibility authority.

Covers .jes/artifacts/implementation_contract_erf2.md §9 Slice 1 test matrix:
  T1-T4  ESC vs motor (per-motor lock ★4, boundary, topology guard, missing evidence)
  T5-T6  Battery discharge (exceeded via SKU, unverifiable without limit evidence)
  T7     Prop<->motor mismatch via library.match_motor_propeller (spy)
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.electrical_compatibility import evaluate_electrical_compatibility
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


def _design_properties(**kwargs):
    defaults = dict(components={})
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


def _esc_spec(current_a=None):
    props = {}
    if current_a is not None:
        props["current_a"] = PropertyValue(value=current_a, unit="A")
    return ComponentSpec(suggested_key="esc", completeness="high", source="declared", properties=props)


def _motor_spec_declared():
    """Motors 'declared' enough for flight-eval prerequisites, no catalog_ref."""
    return ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )


def _battery_spec_declared(**props):
    return ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        properties={k: PropertyValue(value=v) for k, v in props.items()},
    )


# ── ESC vs motor (★3, ★4) ────────────────────────────────────────────────────

def test_esc_undersized_per_motor_not_total():
    """ESC rated well above one motor's draw but below the naive total
    (motor_count x I_motor) must still read 'compatible' — proves the
    predicate compares per-motor, never x motor_count on the ESC side."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,       # 222W / 7.4V = 30A per motor
            "battery_cell_count": 2,      # V_nom = 2 * 3.7 = 7.4V
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
                "esc": _esc_spec(current_a=90.0),  # >= 30A/motor, < 120A naive total
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.i_motor_a == 30.0
    assert result.esc_current_a == 90.0
    assert result.esc_vs_motor == "compatible"


def test_esc_actually_undersized_per_motor():
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
                "esc": _esc_spec(current_a=20.0),  # < 30A per-motor draw
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.esc_vs_motor == "undersized"


def test_esc_compatible_at_boundary():
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
                "esc": _esc_spec(current_a=30.0),  # exactly == I_motor
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.esc_vs_motor == "compatible"


def test_esc_unverifiable_no_topology():
    """Non-multirotor vehicle_type -> topology not determinable -> unverifiable,
    never 'undersized', even with a real evidenced ESC shortfall."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "robot",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
                "esc": _esc_spec(current_a=5.0),
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.esc_vs_motor == "unverifiable"


def test_esc_unverifiable_missing_current():
    """ESC declared but without a current_a property -> no false undersized."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
                "esc": _esc_spec(current_a=None),
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.esc_current_a is None
    assert result.esc_vs_motor == "unverifiable"


def test_esc_undefined_mutually_exclusive_with_undersized():
    """ESC missing entirely (with flight-eval prerequisites met) -> esc_presence
    'missing', and esc_vs_motor must be 'unverifiable', never 'undersized'."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.esc_presence == "missing"
    assert result.esc_vs_motor == "unverifiable"


# ── Battery discharge ─────────────────────────────────────────────────────

def test_battery_discharge_exceeded_sku():
    battery_spec = ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="battery", sku="lipo_2s_850mah"),
    )
    # lipo_2s_850mah: c_rating=75, capacity_mah=850 -> limit = 75 * 0.85 = 63.75A
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,  # 30A/motor -> total 120A, well above 63.75A limit
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec_declared(), "battery": battery_spec},
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.battery_limit_a == 63.75
    assert result.i_total_a == 120.0
    assert result.battery_discharge == "exceeded"


def test_battery_discharge_within_limit_sku():
    battery_spec = ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="battery", sku="lipo_6s_22000mah"),
    )
    # lipo_6s_22000mah: max_continuous_current_a=220A directly.
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 6,
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec_declared(), "battery": battery_spec},
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.battery_discharge == "within_limit"


def test_battery_discharge_unverifiable_no_sku():
    """Battery declared (non-stub) but no catalog SKU/limit evidence at all."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "motor_count": 4,
            "motor_power_w": 222.0,
            "battery_cell_count": 2,
        },
        design_properties=_design_properties(
            components={
                "motors": _motor_spec_declared(),
                "battery": _battery_spec_declared(battery_capacity_wh=50.0),
            },
        ),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.battery_limit_a is None
    assert result.battery_discharge == "unverifiable"


def test_battery_discharge_not_applicable_when_battery_missing():
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "motor_count": 4},
        design_properties=_design_properties(components={"motors": _motor_spec_declared()}),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.battery_discharge == "not_applicable"


# ── Prop <-> motor (library.match_motor_propeller only, ★10) ───────────────

def test_prop_motor_mismatch_calls_library(monkeypatch):
    calls: list[tuple[str, str]] = []
    original = default_library.match_motor_propeller

    def _spy(motor_id, prop_id):
        calls.append((motor_id, prop_id))
        return original(motor_id, prop_id)

    monkeypatch.setattr(default_library, "match_motor_propeller", _spy)

    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="motor", sku="brotherhobby_avenger_2500"),
    )
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="propeller", sku="apc_10x4_5"),  # 10in vs motor's 5in
    )
    state = _project_state(
        design_properties=_design_properties(components={"motors": motors, "propellers": propellers}),
    )
    result = evaluate_electrical_compatibility(state)

    assert calls == [("brotherhobby_avenger_2500", "apc_10x4_5")]
    assert result.prop_motor == "mismatch"


def test_prop_motor_compatible_real_pair():
    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="motor", sku="brotherhobby_avenger_2500"),
    )
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="propeller", sku="gemfan_5030"),  # 5in, matches
    )
    state = _project_state(
        design_properties=_design_properties(components={"motors": motors, "propellers": propellers}),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.prop_motor == "compatible"


def test_prop_motor_unverifiable_when_only_one_bound():
    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        catalog_ref=CatalogRef(family="motor", sku="brotherhobby_avenger_2500"),
    )
    propellers = ComponentSpec(suggested_key="propellers", completeness="high", source="declared")
    state = _project_state(
        design_properties=_design_properties(components={"motors": motors, "propellers": propellers}),
    )
    result = evaluate_electrical_compatibility(state)
    assert result.prop_motor == "unverifiable"


def test_evaluate_electrical_compatibility_is_json_serializable():
    import dataclasses
    import json

    state = _project_state()
    result = evaluate_electrical_compatibility(state)
    json.dumps(dataclasses.asdict(result))
