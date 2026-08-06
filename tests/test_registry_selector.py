"""Tests for domains/registry_selector.py — hybrid domain routing."""
from __future__ import annotations

import pytest

from jarvis.domains.aerial import aerial_registry
from jarvis.domains.ground import ground_registry
from jarvis.domains.registry_selector import get_registry


# ── 1. vehicle_type explicit match ────────────────────────────────────────────

def test_drone_maps_to_aerial():
    assert get_registry("drone") is aerial_registry


def test_dron_maps_to_aerial():
    assert get_registry("dron") is aerial_registry


def test_uav_maps_to_aerial():
    assert get_registry("uav") is aerial_registry


def test_rover_maps_to_ground():
    assert get_registry("rover") is ground_registry


def test_car_maps_to_ground():
    assert get_registry("car") is ground_registry


def test_coche_maps_to_ground():
    assert get_registry("coche") is ground_registry


def test_vehicle_type_is_case_insensitive():
    assert get_registry("DRONE") is aerial_registry
    assert get_registry("Rover") is ground_registry
    assert get_registry("UAV") is aerial_registry


def test_vehicle_type_strips_whitespace():
    assert get_registry("  drone  ") is aerial_registry
    assert get_registry("rover ") is ground_registry


# ── 2. Unknown vehicle_type falls through to heuristic or default ─────────────

def test_unknown_vehicle_type_returns_aerial_default():
    assert get_registry("unknown") is aerial_registry


def test_unknown_vehicle_type_with_ground_text_returns_ground():
    assert get_registry("unknown", text="4 ruedas motrices 50Nm") is ground_registry


def test_unknown_vehicle_type_with_aerial_text_returns_aerial():
    assert get_registry("unknown", text="motor 920kv helice") is aerial_registry


# ── 3. Text heuristic (no vehicle_type) ──────────────────────────────────────

def test_ground_text_with_rpm_returns_ground():
    assert get_registry(text="motor 3000rpm traccion") is ground_registry


def test_ground_text_with_rueda_returns_ground():
    assert get_registry(text="4 ruedas motrices 80nm") is ground_registry


def test_ground_text_with_nm_torque_returns_ground():
    assert get_registry(text="motor 50nm par motor") is ground_registry


def test_aerial_text_with_kv_returns_aerial():
    assert get_registry(text="motor 920kv brushless") is aerial_registry


def test_aerial_text_with_helice_returns_aerial():
    assert get_registry(text="helice 10x4.5 propeller") is aerial_registry


def test_aerial_text_wins_when_more_aerial_keywords():
    # kv + helice + drone = 3 aerial hits vs 0 ground hits
    assert get_registry(text="drone motor 920kv helice") is aerial_registry


def test_ground_text_wins_when_more_ground_keywords():
    # ruedas + rpm + torque + traccion = 4 ground hits vs 0 aerial
    assert get_registry(text="4 ruedas rpm torque traccion") is ground_registry


# ── 4. No arguments → default ─────────────────────────────────────────────────

def test_no_args_returns_aerial_default():
    assert get_registry() is aerial_registry


def test_none_vehicle_type_returns_aerial_default():
    assert get_registry(vehicle_type=None) is aerial_registry


def test_empty_text_returns_aerial_default():
    assert get_registry(text="") is aerial_registry


def test_none_text_returns_aerial_default():
    assert get_registry(vehicle_type=None, text=None) is aerial_registry


# ── 5. Tie-breaking — equal keyword hits → default (aerial) ──────────────────

def test_equal_keyword_hits_returns_aerial_default():
    # "drone" (1 aerial) + "rover" (0 aerial ground keyword direct, but rover is in map)
    # Constructing a tie: 1 aerial keyword + 1 ground keyword → tie → aerial default
    assert get_registry(text="kv rueda") is aerial_registry  # 1 aerial hit, 1 ground hit → tie → default


# ── 6. vehicle_type supersedes text heuristic ────────────────────────────────

def test_explicit_vehicle_type_wins_over_contradicting_text():
    """vehicle_type=drone should return aerial even if text has ground keywords."""
    result = get_registry(vehicle_type="drone", text="rueda rpm torque traccion")
    assert result is aerial_registry


def test_explicit_ground_vehicle_type_wins_over_aerial_text():
    result = get_registry(vehicle_type="rover", text="kv helice brushless drone")
    assert result is ground_registry


# ── 7. vehicle_type from project current_parameters reaches mutation_engine ──

def test_vehicle_type_in_state_dict_reaches_get_registry():
    """Simulates the exact path: _build_mutable_state → mutation_engine reads vehicle_type."""
    state = {"vehicle_type": "rover", "payload_kg": 10.0}
    registry = get_registry(vehicle_type=state.get("vehicle_type"), text="motor 50nm")
    # vehicle_type "rover" must win over ground text (both point to ground in this case,
    # but the key test is that vehicle_type is NOT ignored when present in state dict)
    assert registry is ground_registry


def test_drone_vehicle_type_in_state_dict_wins_over_ground_text():
    """Ground keywords in component text must NOT override the project's vehicle_type."""
    state = {"vehicle_type": "drone"}
    registry = get_registry(vehicle_type=state.get("vehicle_type"), text="rueda rpm torque traccion")
    assert registry is aerial_registry


def test_missing_vehicle_type_in_state_falls_back_to_text():
    """When vehicle_type absent from state (None/empty), text heuristic takes over."""
    state = {"payload_kg": 10.0}  # no vehicle_type key
    registry = get_registry(vehicle_type=state.get("vehicle_type"), text="rueda rpm torque traccion")
    assert registry is ground_registry


def test_empty_string_vehicle_type_falls_back_to_text():
    """Empty string vehicle_type (falsy) must not block text heuristic."""
    registry = get_registry(vehicle_type="", text="motor 920kv brushless")
    assert registry is aerial_registry
