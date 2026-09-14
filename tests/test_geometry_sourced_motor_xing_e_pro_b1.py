"""#4d Sourced motor iFlight XING-E Pro 2207 2450KV B1 (reopen ★ Path A-pending).

Covers implementation_contract_geometry_sourced_motor_xing_e_pro_b1.md
after Engineer ★ — chart peak thrust usable, verification pending disclosure.

  T1  get_motor bag: Ø28.5 · H33.1 · shaft 5 · 33.8 g · KV 2450 · thrust≈16.46
  T2  fallback OP manufacturer_test @ 16 V; note names 6045 and not craft 51466;
      note states VERIFICATION PENDING; confidence ≤ 0.85
  T3  bind + projector → motor CYLINDER Ø28.5 × H33.1 (Disk axial Visor
      B1, `B1-disk-axial-visor`: Ø + cited Motor `height_mm` both present)
  T4  emax_rs2205s_2300 + hobbywing_xrotor_2207_2450 unchanged
  T5  no 1800/2750 rows; no OP with gemfan_hurricane_mck_51466_3_v2
  T6  resolve without craft prop → fallback / legacy, not exact on 51466
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.motor_catalog_assist import motor_spec_to_suggestion
from jarvis.knowledge.library import default_library, resolve_operating_point
from jarvis.workspace.spatial_board import _geometry_from_spec

_SKU = "iflight_xing_e_pro_2207_2450"
_CRAFT_PROP = "gemfan_hurricane_mck_51466_3_v2"


def test_t1_new_sku_bag():
    spec = default_library.get_motor(_SKU)
    assert spec.diameter_mm == pytest.approx(28.5)
    assert spec.height_mm == pytest.approx(33.1)
    assert spec.shaft_diameter_mm == pytest.approx(5.0)
    assert spec.weight_g == pytest.approx(33.8)
    assert spec.kv_rating == 2450
    assert spec.max_current_a == pytest.approx(42.63)
    assert spec.max_watts == pytest.approx(682.1)
    assert spec.thrust_n == pytest.approx(16.46, abs=0.01)
    assert spec.stator_diameter_mm == pytest.approx(22.0)
    assert spec.stator_height_mm == pytest.approx(7.0)
    assert spec.identity_status == "partially_verified"
    assert spec.source_note is not None
    assert "VERIFICATION PENDING" in spec.source_note
    assert "6045" in spec.source_note
    assert "51466" in spec.source_note


def test_t2_fallback_op_manufacturer_chart_pending():
    spec = default_library.get_motor(_SKU)
    assert len(spec.operating_points) >= 1
    op = spec.operating_points[0]
    assert op.get("fallback_only") is True
    assert op.get("source_type") == "manufacturer_test"
    assert float(op["voltage_v"]) == pytest.approx(16.0)
    assert float(op["thrust_n"]) == pytest.approx(16.46, abs=0.01)
    assert float(op["current_a"]) == pytest.approx(42.63)
    assert float(op["power_w"]) == pytest.approx(682.1)
    assert float(op["confidence"]) <= 0.85
    note = op.get("source_note") or ""
    assert "6045" in note
    assert "VERIFICATION PENDING" in note
    assert _CRAFT_PROP not in note or "NOT craft" in note or "not craft" in note.lower()
    assert "51466" in note


def test_t3_bind_projects_cylinder_28_5_by_33_1():
    """Disk axial Visor B1 (`B1-disk-axial-visor`): this SKU cites both
    diameter_mm and height_mm — the projector now emits a cylinder."""
    suggestion = motor_spec_to_suggestion(default_library.get_motor(_SKU))
    bound = bind_motor_from_catalog(suggestion)
    assert bound.catalog_ref.sku == _SKU
    assert bound.properties["diameter_mm"].value == pytest.approx(28.5)
    assert bound.properties["thrust_n"].value == pytest.approx(16.46, abs=0.01)
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["diameter_mm"] == pytest.approx(28.5)
    assert geometry["height_mm"] == pytest.approx(33.1)


def test_t4_emax_and_hobbywing_unchanged():
    emax = default_library.get_motor("emax_rs2205s_2300")
    assert emax.thrust_n == pytest.approx(10.042)
    assert emax.diameter_mm == pytest.approx(27.9)
    # Catalog sourced-only purge B1 redirect: hobbywing_xrotor_2207_2450
    # had no source_url and was deleted; sunnysky_r2205_2500 is a real,
    # sourced KEEP sibling motor, still unaffected by the xing_e_pro work.
    sibling = default_library.get_motor("sunnysky_r2205_2500")
    assert sibling.thrust_n == pytest.approx(12.5525)
    assert sibling.kv_rating == 2500


def test_t5_no_1800_2750_and_no_craft_prop_op():
    motors = default_library.list_motors() if hasattr(default_library, "list_motors") else None
    if motors is None:
        # fall back: known keys only
        with pytest.raises(KeyError):
            default_library.get_motor("iflight_xing_e_pro_2207_1800")
        with pytest.raises(KeyError):
            default_library.get_motor("iflight_xing_e_pro_2207_2750")
    else:
        names = {m.name for m in motors}
        assert "iflight_xing_e_pro_2207_1800" not in names
        assert "iflight_xing_e_pro_2207_2750" not in names
    spec = default_library.get_motor(_SKU)
    for op in spec.operating_points:
        assert op.get("propeller_sku") != _CRAFT_PROP


def test_t6_resolve_with_craft_prop_is_not_exact_match():
    resolved = resolve_operating_point(
        _SKU,
        propeller_sku=_CRAFT_PROP,
        voltage_v=16.0,
    )
    assert resolved.resolution_type in {
        "fallback_operating_point",
        "legacy_estimate",
    }
    assert resolved.resolution_type != "exact_operating_point"
    assert resolved.thrust_n == pytest.approx(16.46, abs=0.01)
