"""Tests for domains/aerial.py — extractors and registry in isolation."""
from __future__ import annotations

import pytest

from jarvis.domains.aerial import (
    aerial_registry,
    extract_battery_properties,
    extract_esc_properties,
    extract_motor_properties,
    extract_propeller_properties,
    extract_frame_properties,
    _frame_completeness,
    MATERIAL_MAP,
)


# ── extract_motor_properties ──────────────────────────────────────────────────

def test_motor_extracts_kv_rating():
    props = extract_motor_properties("motor 920kv")
    assert "kv_rating" in props
    assert props["kv_rating"].value == 920.0
    assert props["kv_rating"].unit == "KV"


def test_motor_extracts_count_from_NxKV_pattern():
    props = extract_motor_properties("4x 920kv motors")
    assert "motor_count" in props
    assert props["motor_count"].value == 4


def test_motor_extracts_count_from_N_motores_pattern():
    props = extract_motor_properties("4 motores 920kv")
    assert "motor_count" in props
    assert props["motor_count"].value == 4


def test_motor_extracts_thrust_n():
    props = extract_motor_properties("motor 15n de empuje")
    assert "thrust_n" in props
    assert props["thrust_n"].value == 15.0
    assert props["thrust_n"].unit == "N"


def test_motor_extracts_watts():
    props = extract_motor_properties("motor 100w 920kv")
    assert "watts" in props
    assert props["watts"].value == 100.0
    assert props["watts"].unit == "W"


def test_motor_returns_empty_for_unrelated_input():
    props = extract_motor_properties("bateria lipo 6s 5000mah")
    assert props == {}


def test_motor_confidence_values_are_positive():
    props = extract_motor_properties("4x 920kv 15n 100w")
    for key, pv in props.items():
        assert pv.confidence > 0.0, f"confidence should be > 0 for {key}"


# ── extract_propeller_properties ──────────────────────────────────────────────

def test_propeller_extracts_diameter_and_pitch():
    props = extract_propeller_properties("helice 10x4.5")
    assert "diameter_in" in props
    assert "pitch_in" in props
    assert props["diameter_in"].value == 10.0
    assert props["pitch_in"].value == 4.5
    assert "count" not in props  # must not steal pitch decimal "5"


def test_propeller_bare_size_does_not_invent_count():
    """FN-019 residual: bare NxP must not set count from diameter/pitch digits."""
    for phrase in ("10x4.5", "10 x 4.5", "hélices 10x4.5"):
        props = extract_propeller_properties(phrase)
        assert props["diameter_in"].value == 10.0
        assert props["pitch_in"].value == 4.5
        assert "count" not in props, phrase


def test_propeller_explicit_count_still_extracted():
    props = extract_propeller_properties("6 hélices 15x5")
    assert props["diameter_in"].value == 15.0
    assert props["pitch_in"].value == 5.0
    assert props["count"].value == 6


def test_propeller_returns_empty_without_size_pattern():
    props = extract_propeller_properties("helice de fibra de carbono")
    assert "diameter_in" not in props
    assert "pitch_in" not in props


def test_propeller_units_are_inches():
    props = extract_propeller_properties("helice 12x4.7")
    assert props["diameter_in"].unit == "in"
    assert props["pitch_in"].unit == "in"


# ── extract_esc_properties ────────────────────────────────────────────────────

def test_esc_extracts_current():
    props = extract_esc_properties("esc 30a")
    assert "current_a" in props
    assert props["current_a"].value == 30.0
    assert props["current_a"].unit == "A"


def test_esc_returns_empty_without_amperage():
    props = extract_esc_properties("esc blheli_s")
    assert props == {}


# ── aerial_registry ───────────────────────────────────────────────────────────

def test_aerial_registry_matches_motor_keyword():
    rule = aerial_registry.match("motor 920kv", "motor")
    assert rule is not None
    assert rule.component_type == "propulsion_active"


def test_aerial_registry_matches_propeller_keyword():
    rule = aerial_registry.match("helice 10x4.5", "helice")
    assert rule is not None
    assert rule.component_type == "propulsion_passive"


def test_aerial_registry_matches_propeller_english_keyword():
    rule = aerial_registry.match("propeller 10x4.5", "propeller")
    assert rule is not None
    assert rule.component_type == "propulsion_passive"


def test_aerial_registry_matches_esc_keyword():
    rule = aerial_registry.match("esc 30a", "esc")
    assert rule is not None
    assert rule.component_type == "power_control"


def test_aerial_registry_returns_none_for_unknown_component():
    rule = aerial_registry.match("servo pwm 10kg", "servo")
    assert rule is None


def test_aerial_registry_propeller_wins_over_motor_when_both_absent():
    """Propeller rule is first in registry — verify ordering is stable."""
    rule = aerial_registry.match("helice", "helice")
    assert rule is not None
    assert rule.suggested_key == "propellers"


def test_aerial_registry_has_four_rules():
    assert len(aerial_registry) == 7  # propeller, motor, esc, battery, frame, flight_controller, sensors


# ── extract_battery_properties ────────────────────────────────────────────

def test_battery_extracts_capacity_from_wh():
    props = extract_battery_properties("bateria 100wh")
    assert "battery_capacity_wh" in props
    assert props["battery_capacity_wh"].value == 100.0
    assert props["battery_capacity_wh"].unit == "Wh"
    assert props["battery_capacity_wh"].confidence == 0.9


def test_battery_extracts_capacity_from_mah():
    props = extract_battery_properties("lipo 5000mah")
    assert "battery_capacity_wh" in props
    assert props["battery_capacity_wh"].value > 0


def test_battery_extracts_cell_count():
    props = extract_battery_properties("lipo 4s 5000mah")
    assert "cell_count" in props
    assert props["cell_count"].value == 4
    assert props["cell_count"].unit == "S"


def test_battery_returns_empty_for_unrelated_input():
    props = extract_battery_properties("motor 920kv")
    assert props == {}


def test_aerial_registry_matches_battery_keyword():
    rule = aerial_registry.match("bateria lipo 6s", "bateria")
    assert rule is not None
    assert rule.component_type == "energy_storage"
    assert rule.suggested_key == "battery"


def test_aerial_registry_matches_lipo_keyword():
    rule = aerial_registry.match("lipo 4s 5000mah", "lipo")
    assert rule is not None
    assert rule.component_type == "energy_storage"


# ── Commit 4: frame extractor + completeness + registry ──────────────────────

def test_extract_frame_mass_grams():
    props = extract_frame_properties("500g")
    assert "mass_kg" in props
    assert abs(props["mass_kg"].value - 0.5) < 1e-6


def test_extract_frame_mass_kg():
    props = extract_frame_properties("0.45 kg")
    assert "mass_kg" in props
    assert abs(props["mass_kg"].value - 0.45) < 1e-6


def test_extract_frame_mass_with_material():
    props = extract_frame_properties("fibra de carbono 450g")
    assert "mass_kg" in props
    assert abs(props["mass_kg"].value - 0.45) < 1e-6
    assert "material" in props
    # G10 ★1: canonical value is the library's own Spanish name, not an
    # internal English slug — get_material() must accept it directly.
    assert props["material"].value == "fibra de carbono"


def test_extract_frame_material_only():
    props = extract_frame_properties("aluminio")
    assert "material" in props
    assert props["material"].value == "aluminio"
    assert "mass_kg" not in props


def test_extract_frame_material_covers_all_library_materials():
    """G10: every library material must be extractable via its own name."""
    from jarvis.knowledge.library import default_library

    for spec in default_library.list_materials():
        props = extract_frame_properties(f"{spec.name} 400g")
        assert "material" in props, f"{spec.name!r} not recognized"
        assert props["material"].value == spec.name
        # Must round-trip through the library without KeyError.
        assert default_library.has_material(props["material"].value)


def test_frame_completeness_low_empty():
    completeness, _ = _frame_completeness({})
    assert completeness == "low"


def test_frame_completeness_medium_with_mass():
    from jarvis.schemas.action_schema import PropertyValue
    props = {"mass_kg": PropertyValue(value=0.5, unit="kg", confidence=0.9, source="declared")}
    completeness, _ = _frame_completeness(props)
    assert completeness == "medium"


def test_frame_completeness_high_with_mass_and_material():
    from jarvis.schemas.action_schema import PropertyValue
    props = {
        "mass_kg": PropertyValue(value=0.5, unit="kg", confidence=0.9, source="declared"),
        "material": PropertyValue(value="carbon_fiber", unit=None, confidence=0.9, source="declared"),
    }
    completeness, missing = _frame_completeness(props)
    assert completeness == "high"
    assert missing == []


def test_aerial_registry_matches_frame_keyword():
    rule = aerial_registry.match("frame de carbono", "frame")
    assert rule is not None
    assert rule.component_type == "structure"


def test_aerial_registry_matches_carbon_keyword():
    rule = aerial_registry.match("carbono 450g", "carbono")
    assert rule is not None
    assert rule.component_type == "structure"
