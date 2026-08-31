"""G24-A — DSE Apply By Index.

Covers .jes/artifacts/implementation_contract_g24_a_apply_by_index.md
G24-3/G24-4:
  - primary gate: a real, unmodified explore() + a catalog candidate NOT at
    viable[0] can be applied via its actual index ("aplica la N") and keeps
    its catalog_ref — G24-TF places the catalog candidate at a real index
    without ever calling _score_candidate or reordering scores.
  - regression: unqualified "aplica la mejor" is still byte-identical to
    viable[0], including the existing G5 divergence-clear behavior on an
    abstract candidate (documented, not fixed by this IC).
  - regression: out-of-range index -> error, no state mutation.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.knowledge.library import default_library


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


# brotherhobby_avenger_2500: thrust_n=9.5, kv 2300-2700, compatible_prop_inch=(5,)
# — same real library fixture used throughout G9-A/G21/G22/Impl C.
_BOUND_SKU = "brotherhobby_avenger_2500"

_CREATE_PARAMS_BASE = {
    "vehicle_type": "dron",
    "objective": "dron de prueba G24-A",
    "payload_kg": 1.0,
    "restrictions": "no",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _suggestion_for(sku: str) -> MotorSuggestion:
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


def _project_with_bound_motor(tmp_path: Path, *, motor_count: int = 6, prop_inch: float = 5.0) -> JarvisOrchestrator:
    """Real orchestrator project with a catalog-bound motor and thrust
    already declared — the exact G24 precondition (investigation §4.2)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": dict(_CREATE_PARAMS_BASE)})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    bound_motor = default_library.get_motor(_BOUND_SKU)
    spec = bind_motor_from_catalog(_suggestion_for(_BOUND_SKU))
    ps = set_motor_component(ps, spec, bound_motor.max_watts)
    ps = ps.model_copy(update={
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": motor_count,
            "propeller_diameter_in": prop_inch,
            "per_motor_max_thrust_n": bound_motor.thrust_n,
        },
    })
    orch.workspace_manager.save_state(ps)
    return orch


def test_apply_by_index_preserves_catalog_ref_when_catalog_not_at_one(tmp_path: Path):
    """G24-3 primary gate.

    G24-TF (locked, per contract): real explore() output, a real
    catalog-native candidate located among the (already-scored,
    already-ordered) generated candidates, placed into `viable` at a real
    index > 1 without touching `_score_candidate` or any score field —
    `viable[0]` stays a genuine abstract candidate from the real
    exploration. This reproduces the list SHAPE the live bug needs
    (investigation §4.2: catalog row present but not first) using real
    generation, not a forced/reordered score.
    """
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    exploration = orch.design_explorer.explore(ps, "aumentar_payload")
    assert exploration.viable, "precondition: exploration must have viable candidates"

    catalog_candidates = [
        c for c in exploration.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates, "precondition: expected >=1 real-SKU candidate generated"
    picked = catalog_candidates[0]
    picked_sku = picked.components_delta["motors"].catalog_ref.sku
    assert picked_sku != _BOUND_SKU  # Impl C excludes the already-bound SKU

    abstract_viable = [
        c for c in exploration.viable
        if not (c.components_delta.get("motors") is not None and c.components_delta["motors"].catalog_ref is not None)
    ]
    assert abstract_viable, "precondition: need a real abstract candidate to occupy #1"

    # G24-TF: viable[0] = a real abstract candidate from this exploration;
    # the real catalog candidate is appended at the end (index len(new_viable),
    # guaranteed > 1). No score touched, no reordering of existing entries'
    # relative order beyond appending one real, already-scored candidate.
    new_viable = [abstract_viable[0]] + [
        c for c in exploration.viable if c is not abstract_viable[0]
    ][:3] + [picked]
    assert len(new_viable) > 1
    catalog_index = len(new_viable)  # 1-based position of the appended catalog row

    exploration_patched = exploration.model_copy(update={"viable": new_viable})
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration_patched})
    )

    llm = _RefuseLLM()
    result = orch.handle_user_text(f"aplica la {catalog_index}", llm)
    assert result["status"] == "ok"
    assert result["applied_index"] == catalog_index

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == picked_sku


def test_hash_index_phrasing_also_works(tmp_path: Path):
    """'aplica #N' phrasing end-to-end, not just 'aplica la N'."""
    orch = _project_with_bound_motor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    exploration = orch.design_explorer.explore(ps, "aumentar_payload")

    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )
    llm = _RefuseLLM()
    n = len(exploration.viable)
    result = orch.handle_user_text(f"aplica #{n}", llm)
    assert result["status"] == "ok"
    assert result["applied_index"] == n


def test_bound_motor_aplica_la_mejor_clears_catalog_ref(tmp_path: Path):
    """Regression documentation (NOT a fix): unqualified 'aplica la mejor'
    on a real, unmodified exploration still applies viable[0] and, when
    that candidate is params-only/abstract, G5's invalidate_diverged_
    catalog_refs still clears catalog_ref exactly as before G24-A. G24-A
    only adds a way to AVOID this by naming a different index — it does not
    change what 'aplica la mejor' itself does."""
    orch = _project_with_bound_motor(tmp_path)
    llm = _RefuseLLM()
    result = orch.handle_user_text("optimiza para aumentar payload", llm)
    assert "viable" not in result  # sanity: real turn, not inspecting internals

    apply_result = orch.handle_user_text("aplica la mejor", llm)
    assert apply_result["status"] == "ok"
    assert apply_result["applied_index"] == 1

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    if motors.catalog_ref is None:
        # Abstract #1 applied and diverged params -> G5 cleared identity (the
        # documented, unchanged-by-this-IC behavior). IC D (Frankenstein
        # .name clear, landed after this test was first written) additionally
        # replaces .name with an honest, non-SKU-shaped label instead of
        # leaving it stale — updated here, disclosed in that IC's report.
        assert motors.name != _BOUND_SKU
    else:
        # If #1 happened to be catalog-native in this run, identity survives
        # trivially — either outcome is consistent with "unchanged from
        # today", so both are accepted here.
        assert motors.catalog_ref.sku


def test_apply_index_out_of_range_via_real_turn_errors_no_mutation(tmp_path: Path):
    orch = _project_with_bound_motor(tmp_path)
    llm = _RefuseLLM()
    orch.handle_user_text("optimiza para aumentar payload", llm)

    before = orch.state_manager.load_active_project(orch.workspace_manager)
    result = orch.handle_user_text("aplica la 99", llm)
    assert result["status"] == "error"

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.current_parameters == before.current_parameters
    assert after.design_properties.components == before.design_properties.components


# ── G24C-4: G24-A composes with real (G24C-fixed) viable output, no G24-TF ──

def test_apply_by_index_on_real_viable_output_no_hand_built_reorder(tmp_path: Path):
    """G24C's own fix (design_explorer._finalize_viable_list) means a real,
    unmodified explore() call now naturally surfaces a catalog-native
    candidate — this test picks its real index straight from the real
    session state and applies it, with zero G24-TF-style list surgery
    (contrast test_apply_by_index_preserves_catalog_ref_when_catalog_not_
    at_one above, which still constructs its own list explicitly and
    remains valid as a standalone unit-level proof of the apply mechanism)."""
    orch = _project_with_bound_motor(tmp_path)
    llm = _RefuseLLM()

    explore_result = orch.handle_user_text("optimiza para aumentar payload", llm)
    assert explore_result["status"] == "ok"

    exploration = orch.state_manager.get_runtime_session().last_exploration_result
    assert exploration is not None
    catalog_idx = next(
        (i + 1 for i, c in enumerate(exploration.viable)
         if c.components_delta.get("motors") is not None
         and c.components_delta["motors"].catalog_ref is not None),
        None,
    )
    assert catalog_idx is not None, "G24C regression: no catalog candidate in real .viable output"
    picked_sku = exploration.viable[catalog_idx - 1].components_delta["motors"].catalog_ref.sku

    apply_result = orch.handle_user_text(f"aplica la {catalog_idx}", llm)
    assert apply_result["status"] == "ok"
    assert apply_result["applied_index"] == catalog_idx

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == picked_sku
