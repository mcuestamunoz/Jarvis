"""G24C — Viable Selection + Honest CTA.

Covers .jes/artifacts/implementation_contract_g24_viable_selection_honest_cta.md
G24C-2/G24C-3:
  - _finalize_viable_list (★3a — selection only, never _score_candidate)
  - primary gate: real explore() on a bound-motor project now surfaces
    >=1 catalog-native motor candidate for aumentar_payload/mejorar_
    estabilidad, where investigation_report_deferred_queue_post_v031.md §5.1
    found 0 on baseline v0.3.1 — reproduced here as a permanent regression.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.design_explorer import (
    MAX_VIABLE,
    ExplorationCandidate,
    _finalize_viable_list,
    _is_catalog_native_motor_candidate,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


def _sim(safety_margin_ratio: float = 1.5) -> SimulationResult:
    return SimulationResult(
        can_fly=True, status="pass", safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=safety_margin_ratio, autonomy_min=30.0, quality="good",
        warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0, required_thrust_n=40.0, weight_n=34.3,
            per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )


def _calc() -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="drone", payload_kg=2.0, structure_mass_kg=1.5, total_mass_kg=3.5,
        weight_n=34.3, required_thrust_n=41.2, motors=4, thrust_per_motor_required_n=10.3,
        available_total_thrust_n=60.0, autonomy_min=30.0, tool_results=[],
    )


def _abstract_candidate(score: float, label: str = "abstract") -> ExplorationCandidate:
    return ExplorationCandidate(
        params_delta={"per_motor_max_thrust_n_factor": 1.5},
        components_delta={},
        calculations=_calc(), simulation=_sim(), score=score, label=label,
    )


def _catalog_candidate(score: float, sku: str = "sunnysky_r2305_2500") -> ExplorationCandidate:
    motor_spec = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
        catalog_ref=CatalogRef(family="motor", sku=sku),
    )
    return ExplorationCandidate(
        params_delta={}, components_delta={"motors": motor_spec},
        calculations=_calc(), simulation=_sim(), score=score, label=f"motors [{sku}]",
    )


# ── _is_catalog_native_motor_candidate ──────────────────────────────────────

def test_is_catalog_native_true_for_catalog_bound_motor():
    assert _is_catalog_native_motor_candidate(_catalog_candidate(1.0)) is True


def test_is_catalog_native_false_for_abstract():
    assert _is_catalog_native_motor_candidate(_abstract_candidate(1.0)) is False


def test_is_catalog_native_false_for_freeform_motor_delta():
    """A components_delta with a motors spec that has NO catalog_ref (a
    freeform/synthetic motor candidate) must not count as catalog-native."""
    freeform_spec = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )
    candidate = ExplorationCandidate(
        params_delta={}, components_delta={"motors": freeform_spec},
        calculations=_calc(), simulation=_sim(), score=1.0, label="freeform motor",
    )
    assert _is_catalog_native_motor_candidate(candidate) is False


# ── _finalize_viable_list — G24C-2 ──────────────────────────────────────────

def test_finalize_viable_reserves_best_catalog_when_truncated():
    abstract = [_abstract_candidate(10.0 - i, f"abstract-{i}") for i in range(6)]  # scores 10..5
    catalog = _catalog_candidate(score=1.0)  # lowest score, would be truncated out
    original_scores = {id(c): c.score for c in [*abstract, catalog]}

    result = _finalize_viable_list([*abstract, catalog])

    assert len(result) <= MAX_VIABLE
    assert any(c is catalog for c in result), "catalog candidate must survive selection"
    # Scores untouched — identity + value check, not just membership.
    for c in result:
        assert c.score == original_scores[id(c)]
    assert catalog.score == pytest.approx(1.0)


def test_finalize_viable_noop_when_catalog_already_in_top5():
    abstract = [_abstract_candidate(3.0 - i, f"abstract-{i}") for i in range(3)]
    catalog = _catalog_candidate(score=10.0)  # highest score — already #1

    result = _finalize_viable_list([*abstract, catalog])

    assert result[0] is catalog
    assert len(result) == 4


def test_finalize_viable_noop_when_no_catalog_native():
    abstract = [_abstract_candidate(10.0 - i, f"abstract-{i}") for i in range(7)]
    result = _finalize_viable_list(abstract)
    assert len(result) == MAX_VIABLE
    assert [c.score for c in result] == sorted((c.score for c in abstract), reverse=True)[:MAX_VIABLE]


def test_finalize_viable_only_reserves_best_of_multiple_catalog_candidates():
    """Multiple catalog-native candidates: only the best-scoring one is
    guaranteed; the contract explicitly locks this as a single-slot
    reservation, not "all catalog candidates survive"."""
    abstract = [_abstract_candidate(10.0 - i, f"abstract-{i}") for i in range(5)]
    catalog_low = _catalog_candidate(score=0.5, sku="sku_low")
    catalog_lower = _catalog_candidate(score=0.1, sku="sku_lower")

    result = _finalize_viable_list([*abstract, catalog_low, catalog_lower])

    assert len(result) == MAX_VIABLE
    catalog_in_result = [c for c in result if _is_catalog_native_motor_candidate(c)]
    assert len(catalog_in_result) == 1
    assert catalog_in_result[0].label == "motors [sku_low]"  # the higher-scoring one


def test_finalize_viable_result_length_respects_short_input():
    """Fewer than MAX_VIABLE total candidates -> result is not padded."""
    result = _finalize_viable_list([_abstract_candidate(1.0), _catalog_candidate(0.5)])
    assert len(result) == 2


# ── Primary gate — real explore(), no G24-TF ────────────────────────────────

_BOUND_SKU = "brotherhobby_avenger_2500"


def _project_with_bound_motor(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": {
        "vehicle_type": "dron", "objective": "g24c gate", "payload_kg": 1.0,
        "restrictions": "no", "detail_level": "conceptual", "motors": 4,
        "structure_mass_factor": 0.5, "safety_factor": 1.2,
    }})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    bound_motor = default_library.get_motor(_BOUND_SKU)
    spec = bind_motor_from_catalog({
        "idx": 1, "name": _BOUND_SKU, "thrust_n": bound_motor.thrust_n,
        "kv_rating": bound_motor.kv_rating, "weight_g": bound_motor.weight_g,
        "max_watts": bound_motor.max_watts, "is_generic": bound_motor.is_generic,
    })
    ps = set_motor_component(ps, spec, bound_motor.max_watts)
    ps = ps.model_copy(update={"current_parameters": {
        **ps.current_parameters, "motor_count": 6, "propeller_diameter_in": 5.0,
        "per_motor_max_thrust_n": bound_motor.thrust_n,
    }})
    orch.workspace_manager.save_state(ps)
    return orch


@pytest.mark.parametrize("goal_key", ["aumentar_payload", "mejorar_estabilidad"])
def test_explore_bound_motor_includes_catalog_in_viable(tmp_path: Path, goal_key: str):
    """The investigation's own §5.1 repro: on baseline v0.3.1 this asserted
    0 catalog-native candidates in .viable for both goals. Now >=1."""
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    exploration = orch.design_explorer.explore(ps, goal_key)

    catalog_in_viable = [c for c in exploration.viable if _is_catalog_native_motor_candidate(c)]
    assert catalog_in_viable, (
        f"expected >=1 catalog-native candidate in .viable for {goal_key}, "
        f"got 0 of {len(exploration.viable)}"
    )
    assert len(exploration.viable) <= 5


def test_explore_reducir_masa_stays_empty_no_catalog_candidates_generated(tmp_path: Path):
    """Regression: a goal with zero catalog candidates generated must be a
    complete no-op — _finalize_viable_list must not invent one."""
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    exploration = orch.design_explorer.explore(ps, "reducir_masa")

    catalog_in_viable = [c for c in exploration.viable if _is_catalog_native_motor_candidate(c)]
    assert catalog_in_viable == []
    assert len(exploration.viable) == 5
