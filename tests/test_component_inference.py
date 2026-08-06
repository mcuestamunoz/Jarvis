"""
Tests for infer_component — property extraction, completeness, key deduplication.

Covers:
  - Motor count extraction ("4 motores", "4x")
  - KV rating extraction ("920KV")
  - Thrust extraction ("15N", "15N de empuje")
  - Completeness levels
  - Full spec from combined input
  - Merging same-type entities in "todos" path (via _handle_pending_entity_selection indirectly)
"""
import pytest

from jarvis.core.component_inference import infer_component


# ── Motor property extraction ─────────────────────────────────────────────────

def test_motor_count_extracted_from_motores_pattern():
    spec = infer_component("4 motores brushless")
    assert spec.properties["motor_count"].value == 4
    assert spec.properties["motor_count"].source == "declared"


def test_motor_count_extracted_from_4x_pattern():
    spec = infer_component("4x motores 920KV")
    assert spec.properties["motor_count"].value == 4


def test_kv_rating_extracted():
    spec = infer_component("4 motores brushless 920KV")
    assert spec.properties["kv_rating"].value == 920.0
    assert spec.properties["kv_rating"].unit == "KV"


def test_thrust_n_extracted():
    spec = infer_component("15N de empuje por motor")
    assert spec.properties["thrust_n"].value == 15.0
    assert spec.properties["thrust_n"].unit == "N"
    assert spec.properties["thrust_n"].source == "declared"


def test_thrust_n_extracted_inline():
    spec = infer_component("motor 920KV 15N")
    assert spec.properties["thrust_n"].value == 15.0
    assert spec.properties["kv_rating"].value == 920.0


# ── Completeness levels ───────────────────────────────────────────────────────

def test_completeness_high_when_thrust_and_count():
    spec = infer_component("4 motores brushless 920KV, 15N de empuje por motor")
    assert spec.completeness == "high"
    assert spec.missing_fields == []
    assert spec.hints == []


def test_completeness_high_when_thrust_and_kv():
    spec = infer_component("motor 920KV 15N")
    assert spec.completeness == "high"


def test_completeness_medium_when_only_kv():
    spec = infer_component("motor 920KV")
    assert spec.completeness == "medium"
    assert "número de motores" in spec.missing_fields


def test_completeness_medium_when_only_count():
    spec = infer_component("4 motores brushless")
    assert spec.completeness == "medium"
    assert "empuje por motor, KV o potencia (W)" in spec.missing_fields


def test_completeness_low_when_no_properties():
    spec = infer_component("motores brushless")
    assert spec.completeness == "low"
    assert "empuje por motor, KV o potencia (W)" in spec.missing_fields
    assert "número de motores" in spec.missing_fields


# ── Full combined input (the bug case from CLI test) ─────────────────────────

def test_full_spec_combined_input():
    """The exact input from the failing CLI test: merged entities string."""
    spec = infer_component("4 motores brushless 920KV, 15N de empuje por motor")
    assert spec.component_type == "propulsion_active"
    assert spec.suggested_key == "motors"
    assert spec.properties["motor_count"].value == 4
    assert spec.properties["kv_rating"].value == 920.0
    assert spec.properties["thrust_n"].value == 15.0
    assert spec.completeness == "high"


# ── Propeller: unchanged behavior ─────────────────────────────────────────────

def test_propeller_low_when_no_size():
    spec = infer_component("helices")
    assert spec.component_type == "propulsion_passive"
    assert spec.completeness == "low"
    assert "diámetro/paso" in spec.missing_fields


def test_propeller_high_when_sized():
    spec = infer_component("4 helices 10x4.5")
    assert spec.component_type == "propulsion_passive"
    assert spec.completeness == "high"
    assert spec.missing_fields == []
