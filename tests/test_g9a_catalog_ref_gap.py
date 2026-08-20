"""G9-A Catalog-Ref Blind Spot — Slice 2 (orchestrator dedup) + Slice 3 (interaction regressions).

Slice 1 (resolve_motor_catalog_surface bound-SKU logic) is covered directly in
tests/test_engineering_readiness_gaps.py. This file exercises the same fix
through orchestrator.build_startup_context (confirms the dedup wiring didn't
drop a field) and the two named interaction regressions: G9-B demotion and
G5 divergence.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.engineering_readiness import (
    build_engineering_readiness,
    resolve_motor_catalog_surface,
)
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.core.orchestrator import JarvisOrchestrator

# brotherhobby_avenger_2500: thrust_n=9.5, max_thrust_n=11.5, kv 2300-2700,
# compatible_prop_inch=(5,) — real library fixture (see test_engineering_readiness_gaps.py).
_BOUND_SKU = "brotherhobby_avenger_2500"
_SUGGESTION: MotorSuggestion = {
    "idx": 1, "name": _BOUND_SKU, "thrust_n": 9.5, "kv_rating": 2500,
    "weight_g": 32.0, "max_watts": 280.0, "is_generic": False,
}


def _project_with_bound_motor(tmp_path: Path, *, required_thrust_n: float, motor_count: int = 6):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba G9-A",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": motor_count,
            "per_motor_max_thrust_n": required_thrust_n / motor_count,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = bind_motor_from_catalog(_SUGGESTION)
    ps = set_motor_component(ps, spec, 280.0)
    ps = ps.model_copy(update={
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": motor_count,
            "propeller_diameter_in": 5.0,
        },
        "latest_results": {
            "calculations": {
                **(ps.latest_results.get("calculations") or {}),
                "required_thrust_n": required_thrust_n,
                "total_mass_kg": 1.5,
            },
            "simulation": {
                **(ps.latest_results.get("simulation") or {}),
                "status": "pass",
                "can_fly": True,
                "safety_margin_ratio": 1.2,
            },
        },
    })
    orch.workspace_manager.save_state(ps)
    return orch


# ── Slice 2: orchestrator dedup smoke ────────────────────────────────────────

def test_build_startup_context_motor_catalog_gap_from_readiness(tmp_path: Path):
    """Scenario B through orchestrator.build_startup_context — catalog surface
    is plucked from readiness (readiness-first wiring)."""
    orch = _project_with_bound_motor(tmp_path, required_thrust_n=60.0)  # 10.0 N/motor

    ctx = orch.build_startup_context()

    assert ctx["motor_catalog_gap"] is None
    assert any(m["name"] == _BOUND_SKU for m in ctx["motor_catalog_matches"])
    assert ctx["motor_catalog_gap"] == ctx["readiness"]["motor_catalog_gap"]
    assert ctx["motor_catalog_matches"] == ctx["readiness"]["motor_catalog_matches"]


def test_startup_context_invokes_catalog_resolver_once(tmp_path: Path):
    """G9-A hygiene: build_startup_context must call resolve_motor_catalog_surface
    exactly once (via build_engineering_readiness), not twice per turn."""
    orch = _project_with_bound_motor(tmp_path, required_thrust_n=60.0)
    with patch(
        "jarvis.core.engineering_readiness.resolve_motor_catalog_surface",
        wraps=resolve_motor_catalog_surface,
    ) as spy:
        orch.build_startup_context()
    assert spy.call_count == 1


def test_startup_context_catalog_surface_matches_readiness(tmp_path: Path):
    """G9-A hygiene: build_startup_context must not re-invoke the catalog
    resolver — motor_catalog_gap/matches in the startup dict match readiness."""
    orch = _project_with_bound_motor(tmp_path, required_thrust_n=60.0)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    readiness = build_engineering_readiness(ps)

    ctx = orch.build_startup_context()

    assert ctx["motor_catalog_gap"] == readiness.motor_catalog_gap
    assert ctx["motor_catalog_matches"] == readiness.motor_catalog_matches
    assert ctx["readiness"]["motor_catalog_gap"] == readiness.motor_catalog_gap
    assert ctx["readiness"]["motor_catalog_matches"] == readiness.motor_catalog_matches


def test_build_startup_context_motor_catalog_gap_underspec_delegates(tmp_path: Path):
    """Scenario C through orchestrator.build_startup_context."""
    orch = _project_with_bound_motor(tmp_path, required_thrust_n=90.0)  # 15.0 N/motor > 11.5

    ctx = orch.build_startup_context()

    assert ctx["motor_catalog_gap"] is not None
    assert _BOUND_SKU in ctx["motor_catalog_gap"]
    assert "no tengo un motor en el catálogo" not in ctx["motor_catalog_gap"]


# ── Slice 3: interaction regressions ─────────────────────────────────────────

def test_g9b_demotion_still_applies_with_bound_sku_underspec(tmp_path: Path):
    """G9-B (catalog_gap_covered_by_declared_thrust): PASS + declared thrust
    covers the physics floor still demotes the catalog gap to a WARNING
    (CATALOG-GAP-DEMOTED-POST-PASS), even when the gap itself now comes from
    a stale bound SKU (Scenario C) rather than a plain empty search. G9-A
    must not swallow or double-surface it — it only changes *why* the gap
    fired (evidence fact / message), not G9-B's independent ranking decision."""
    orch = _project_with_bound_motor(tmp_path, required_thrust_n=90.0)  # 15.0 N/motor
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    # Declared per-motor thrust already covers the physics floor (required_thrust_n/motor_count = 15.0).
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "per_motor_max_thrust_n": 15.0},
    })
    orch.workspace_manager.save_state(ps)

    result = build_engineering_readiness(ps)

    catalog_gaps = [g for g in result.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert len(catalog_gaps) == 1
    assert catalog_gaps[0].evidence[0].fact == f"bound_sku_underspec:{_BOUND_SKU}"

    catalog_subsystem = result.subsystems["catalog"]
    assert catalog_subsystem.verdict == "WARNING"
    assert catalog_subsystem.warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"
