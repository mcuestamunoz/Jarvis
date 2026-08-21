"""Phase 2 P2-1 — Lookup Operating Point.

resolve_operating_point (library.py) resolves real thrust from curated
operating_points[] rows instead of the bare MotorSpec.thrust_n peak, with an
honest resolution_type (exact_operating_point / fallback_operating_point /
legacy_estimate) and provenance. component_writers.set_motor_component
bridges the resolution into current_parameters["per_motor_max_thrust_n"] +
["propulsion_resolution"] (JSON string — must stay hashable for
design_explorer's candidate cache, see ★-locked note in that file).

★6 dataset (.jes/artifacts/phase2_star6_operating_point_validation_case.md):
  emax_rs2205s_2300  — OP-0 (fallback, 16.8V, 10.042N), OP-1 (16V/hq_5045_bn,
                       9.1986N), OP-2 (16V/hq_5045_bn, 9.7086N)
  sunnysky_r2205_2500 — OP-3 (14.8V/gf_5045x3, 12.5525N, rpm=27082)
  emax_rs2205_2300    — UNCHANGED legacy (no OP data; do not confuse with S)
  sunnysky_r2305_2500 — UNCHANGED legacy (untouched)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
from jarvis.core.component_writers import set_motor_component, set_propeller_component
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library, resolve_operating_point
from jarvis.schemas.action_schema import CatalogRef

_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba Phase 2 P2-1",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _suggestion_for(sku: str):
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


def _fresh_project(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": dict(_CREATE_PARAMS)})
    return orch


# ── 1. resolve_operating_point — pure resolver contract ─────────────────────


def test_exact_match_single_row():
    r = resolve_operating_point(
        "emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=16.0,
    )
    # Two exact rows exist at this (prop, voltage) — max-thrust policy applies.
    assert r.resolution_type == "exact_operating_point"
    assert r.thrust_n == pytest.approx(9.7086)
    assert r.selection_reason == "v1_max_thrust"
    assert r.source_type == "manufacturer_test"
    assert r.fallback_only is False


def test_fallback_when_no_propeller_bound():
    r = resolve_operating_point("emax_rs2205s_2300")
    assert r.resolution_type == "fallback_operating_point"
    assert r.thrust_n == pytest.approx(10.042)
    assert r.fallback_only is True
    assert r.source_type == "manufacturer_test"


def test_legacy_path_for_unenriched_motor():
    """emax_rs2205_2300 (non-S) deliberately carries no operating_points —
    must never see the RS2205S table (locked: do not copy OPs across SKUs)."""
    r = resolve_operating_point("emax_rs2205_2300")
    assert r.resolution_type == "legacy_estimate"
    assert r.source_type == "estimated"
    assert r.thrust_n == pytest.approx(default_library.get_motor("emax_rs2205_2300").thrust_n)
    assert r.thrust_n == pytest.approx(8.0)


def test_sunnysky_r2305_2500_untouched_legacy():
    """Locked: sunnysky_r2305_2500 must never be overwritten with R2205 data."""
    r = resolve_operating_point("sunnysky_r2305_2500")
    assert r.resolution_type == "legacy_estimate"
    assert r.thrust_n == pytest.approx(7.5)


def test_sunnysky_r2205_2500_exact_match():
    r = resolve_operating_point(
        "sunnysky_r2205_2500", propeller_sku="gf_5045x3", voltage_v=14.8,
    )
    assert r.resolution_type == "exact_operating_point"
    assert r.thrust_n == pytest.approx(12.5525)
    assert r.rpm == pytest.approx(27082)
    assert r.selection_reason is None  # only one exact match here


def test_fallback_only_row_never_classified_as_exact():
    """★6 hard rule: a fallback_only row must never resolve as exact, even
    when a propeller_sku happens to be passed (OP-0 has propeller_sku=None,
    so it can never satisfy the exact-match propeller-equality condition)."""
    r = resolve_operating_point(
        "emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=16.8,
    )
    # 16.8V has no exact-row match (exact rows are at 16.0V) — falls through
    # to the 16.8V fallback row, never mislabeled exact.
    assert r.resolution_type == "fallback_operating_point"
    assert r.fallback_only is True


def test_unknown_motor_returns_none():
    assert resolve_operating_point("does_not_exist_xyz") is None


def test_voltage_mismatch_excludes_exact_but_not_fallback():
    """A voltage far from the exact rows (16.0V) must not match exactly, but
    the (single, only) fallback row is still returned regardless of voltage
    exactness — proven by asserting resolution_type, not by coincidence."""
    r = resolve_operating_point(
        "emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=22.2,
    )
    assert r.resolution_type == "fallback_operating_point"


# ── 2. Bridge — set_motor_component writes params + propulsion_resolution ──


def test_bridge_writes_exact_resolution(tmp_path: Path):
    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog("hq_5045_bn")
    ps = set_propeller_component(ps, prop_spec)

    motor_spec = bind_motor_from_catalog(_suggestion_for("emax_rs2205s_2300"))
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "battery_cell_count": 4},  # ~14.8V, not 16V
    })
    updated = set_motor_component(ps, motor_spec, default_library.get_motor("emax_rs2205s_2300").max_watts)

    # 4S (~14.8V) doesn't match the 16.0V exact rows within epsilon —
    # falls back honestly rather than fabricating an exact match.
    raw = updated.current_parameters.get("propulsion_resolution")
    assert raw is not None
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "fallback_operating_point"
    assert updated.current_parameters["per_motor_max_thrust_n"] == pytest.approx(10.042)


def test_bridge_writes_exact_resolution_with_matching_voltage(tmp_path: Path):
    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog("hq_5045_bn")
    ps = set_propeller_component(ps, prop_spec)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "battery_cell_count": 4.32},  # 4.32*3.7~=16.0V
    })

    motor_spec = bind_motor_from_catalog(_suggestion_for("emax_rs2205s_2300"))
    updated = set_motor_component(ps, motor_spec, default_library.get_motor("emax_rs2205s_2300").max_watts)

    raw = updated.current_parameters.get("propulsion_resolution")
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "exact_operating_point"
    assert resolution["selection_reason"] == "v1_max_thrust"
    assert updated.current_parameters["per_motor_max_thrust_n"] == pytest.approx(9.7086)
    # Component property stays coherent with the resolved thrust; catalog_ref preserved.
    motors_component = updated.design_properties.components["motors"]
    assert motors_component.properties["thrust_n"].value == pytest.approx(9.7086)
    assert motors_component.catalog_ref == CatalogRef(family="motor", sku="emax_rs2205s_2300")


def test_bridge_battery_catalog_ref_voltage_takes_precedence(tmp_path: Path):
    """Battery catalog_ref (real SKU voltage) wins over the cell-count
    estimate when both are somehow present."""
    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog("gf_5045x3")
    ps = set_propeller_component(ps, prop_spec)

    battery_sku = next(b.name for b in default_library.list_batteries() if b.nominal_voltage == pytest.approx(14.8))
    from jarvis.core.catalog_bind import bind_battery_from_catalog
    from jarvis.core.component_writers import set_battery_component
    battery_spec = bind_battery_from_catalog(battery_sku)
    ps = set_battery_component(ps, battery_spec, default_library.get_battery(battery_sku).energy_wh)

    motor_spec = bind_motor_from_catalog(_suggestion_for("sunnysky_r2205_2500"))
    updated = set_motor_component(ps, motor_spec, default_library.get_motor("sunnysky_r2205_2500").max_watts)

    raw = updated.current_parameters.get("propulsion_resolution")
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "exact_operating_point"
    assert updated.current_parameters["per_motor_max_thrust_n"] == pytest.approx(12.5525)


def test_bridge_legacy_path_for_freeform_motor_unchanged(tmp_path: Path):
    """Freeform (non-catalog-bound) motors keep exactly the pre-P2-1
    behavior — no resolve_operating_point call, no propulsion_resolution."""
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    freeform_spec = ComponentSpec(
        name="4x 2306 2400KV 50W", component_type="propulsion_active", suggested_key="motors",
        completeness="high", source="declared",
        properties={
            "thrust_n": PropertyValue(value=6.3, unit="N", confidence=0.7, source="declared"),
            "motor_count": PropertyValue(value=4, confidence=0.9, source="declared"),
        },
    )
    updated = set_motor_component(ps, freeform_spec, 50.0)

    assert updated.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(6.3)
    assert "propulsion_resolution" not in updated.current_parameters


def test_bridge_legacy_resolution_for_catalog_motor_without_op_data(tmp_path: Path):
    """A catalog-bound motor with zero operating_points (e.g. the pre-P2-1
    brotherhobby_avenger_2500 fixture) still gets a typed propulsion_resolution
    (legacy_estimate), and the numeric thrust is byte-identical to before
    P2-1 — the regression contract for every already-seeded SKU."""
    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    sku = "brotherhobby_avenger_2500"
    motor_spec = bind_motor_from_catalog(_suggestion_for(sku))
    updated = set_motor_component(ps, motor_spec, default_library.get_motor(sku).max_watts)

    raw = updated.current_parameters.get("propulsion_resolution")
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "legacy_estimate"
    assert resolution["source_type"] == "estimated"
    assert updated.current_parameters["per_motor_max_thrust_n"] == pytest.approx(
        default_library.get_motor(sku).thrust_n
    )


# ── 3. estado / CLI surface ──────────────────────────────────────────────────


def test_estado_renders_honest_evidence_label(tmp_path: Path):
    from jarvis.adapters.cli.main import render_startup_context

    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motor_spec = bind_motor_from_catalog(_suggestion_for("emax_rs2205s_2300"))
    ps = set_motor_component(ps, motor_spec, default_library.get_motor("emax_rs2205s_2300").max_watts)
    orch.workspace_manager.save_state(ps)

    ctx = orch.build_startup_context()
    rendered = render_startup_context(ctx)

    assert "Propulsión (evidencia): fallback_operating_point · manufacturer_test" in rendered
    assert "10.042 N" in rendered
    assert "(sin hélice de catálogo)" in rendered


def test_estado_hides_line_for_freeform_motor(tmp_path: Path):
    from jarvis.adapters.cli.main import render_startup_context

    orch = _fresh_project(tmp_path)
    ctx = orch.build_startup_context()
    rendered = render_startup_context(ctx)

    assert "Propulsión (evidencia):" not in rendered


# ── 4. Regression: named Impl C/D suites stay green (spot check here too) ──


def test_regression_brotherhobby_bind_still_works(tmp_path: Path):
    orch = _fresh_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    sku = "brotherhobby_avenger_2500"
    motor_spec = bind_motor_from_catalog(_suggestion_for(sku))
    updated = set_motor_component(ps, motor_spec, default_library.get_motor(sku).max_watts)
    assert updated.design_properties.components["motors"].catalog_ref.sku == sku
    assert updated.current_parameters["per_motor_max_thrust_n"] == pytest.approx(9.5)
