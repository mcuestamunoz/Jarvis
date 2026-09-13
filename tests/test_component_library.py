"""Tests for jarvis.knowledge.library — ComponentLibrary motor methods."""
import pytest
from pathlib import Path

from jarvis.knowledge.library import ComponentLibrary, MotorSpec


# Use the real library from 07_Biblioteca (integration-style)
_LIB = ComponentLibrary()


# ── Motor exact lookup ────────────────────────────────────────────────────────

# Catalog sourced-only purge B1 redirect: generic_920kv had no
# source_url and was deleted; emax_rs2205s_2300 is a real, sourced
# KEEP motor with the same "exact name lookup" shape.
def test_get_motor_exact_name_returns_spec():
    spec = _LIB.get_motor("emax_rs2205s_2300")
    assert isinstance(spec, MotorSpec)
    assert spec.name == "emax_rs2205s_2300"
    assert spec.kv_rating == 2300
    assert spec.thrust_n == 10.042


def test_get_motor_unknown_raises_keyerror():
    with pytest.raises(KeyError, match="motor_ficticio"):
        _LIB.get_motor("motor_ficticio")


def test_has_motor_true_for_known():
    # Catalog sourced-only purge B1 redirect: sunnysky_x2216_11 had no
    # source_url and was deleted; emax_rs2205s_2300 is a real, sourced KEEP motor.
    assert _LIB.has_motor("emax_rs2205s_2300") is True


def test_has_motor_false_for_unknown():
    assert _LIB.has_motor("no_existe_xyz") is False


# Catalog sourced-only purge B1 redirect: the catalog now has exactly 3
# sourced motors (was >= 6 anonymous/unsourced rows).
def test_list_motors_returns_all_sorted():
    motors = _LIB.list_motors()
    names = [m.name for m in motors]
    assert len(motors) >= 3
    assert names == sorted(names)


# ── KV-based suggestion ───────────────────────────────────────────────────────

# Catalog sourced-only purge B1 redirect: generic_920kv/sunnysky_x2212_980
# had no source_url and were deleted; emax_rs2205s_2300 (2300KV) and
# iflight_xing_e_pro_2207_2450 (2450KV, exactly 150 away) are real KEEP
# motors within the same tolerance window.
def test_find_motors_by_kv_returns_within_tolerance():
    results = _LIB.find_motors_by_kv(2300, tolerance=150)
    kv_values = [m.kv_rating for m in results]
    assert all(abs(kv - 2300) <= 150 for kv in kv_values)
    names = [m.name for m in results]
    assert "emax_rs2205s_2300" in names
    assert "iflight_xing_e_pro_2207_2450" in names


def test_find_motors_by_kv_excludes_far_motors():
    results = _LIB.find_motors_by_kv(920, tolerance=150)
    kv_values = [m.kv_rating for m in results]
    # t-motor_mn4014_400 (400KV) is 520 away — must not appear
    assert 400 not in kv_values


def test_find_motors_by_kv_result_never_has_preset_thrust():
    """Verify the result is just data — no auto-apply side effect possible."""
    results = _LIB.find_motors_by_kv(920)
    # The test is structural: results are MotorSpec dataclasses, not mutated state
    for m in results:
        assert isinstance(m.thrust_n, float)
        assert m.thrust_n > 0


def test_find_motors_by_kv_empty_for_very_tight_tolerance():
    results = _LIB.find_motors_by_kv(500, tolerance=10)
    assert results == []


# ── MotorSpec is immutable ────────────────────────────────────────────────────

# Catalog sourced-only purge B1 redirect: generic_920kv had no
# source_url and was deleted; emax_rs2205s_2300 is a real, sourced KEEP motor.
def test_motor_spec_is_frozen():
    spec = _LIB.get_motor("emax_rs2205s_2300")
    with pytest.raises((AttributeError, TypeError)):
        spec.thrust_n = 999.0  # type: ignore[misc]
