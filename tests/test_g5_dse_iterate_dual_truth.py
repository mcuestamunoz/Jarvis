"""G5 — DSE params vs iterate component dual-truth (fix regression).

Investigation: .jes/artifacts/investigation_report_g5_dse_iterate_dual_truth.md
Fix: .jes/artifacts/implementation_report_g5_dse_component_sync.md
Origin: CLI session `levantar-4kg-con-atonomia-de-70min` (`1f7e6e8d1a70`), iter_010
(dse_apply, mejorar_estabilidad) → iter_011 (iterate safety_factor).

Bug (fixed): after a params-only DSE apply raised motor_count/
per_motor_max_thrust_n, a completely unrelated numeric iterate turn (e.g.
safety_factor) silently reverted both fields back to their pre-DSE values —
a physics cliff with no narration, no warning, no user action targeting
motors at all.

Root cause (confirmed by trace): `IterateAction.run`'s physical (non-DEFINE)
path unconditionally calls `component_resolver.resolve_propulsion_parameters`
on `design_properties.components["motors"]` and overwrites `motor_count`/
`per_motor_max_thrust_n` in `updated_parameters` via `PhysicalOverride.apply_to`
— on EVERY physical turn, regardless of which variable is actually being
mutated. DSE's params-only apply path (`_handle_apply_exploration`) never
updated `design_properties.components` (by design — DA2 params-only deltas
work purely on the params dict), so the component went stale the moment DSE
elevated the numeric params past what the component alone would produce. The
next physical iterate turn re-derived from that stale component and clobbered
whatever DSE had just written.

Fix: `orchestrator._handle_apply_exploration` now calls
`component_sync.sync_motors_component_from_params` right after
`catalog_bind.invalidate_diverged_catalog_refs` on every params-only DSE
apply, keeping `components["motors"]` current — no change was needed in
`IterateAction.run` or `param_definition_session.py`; their
`resolve_propulsion_parameters` call is correct automatically once its one
input stops going stale.

This test was originally `xfail(strict=True)` as the investigation's proof of
the bug; promoted to a plain regression here (G5 fix contract §3.3).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


def _comp(key: str, ctype: str, **props) -> ComponentSpec:
    return ComponentSpec(
        name=key, component_type=ctype, suggested_key=key,
        completeness="high", source="declared", properties=props,
    )


def _project_with_declared_motors(tmp_path: Path) -> JarvisOrchestrator:
    """A project whose motors are declared via ComponentSpec (thrust_n=20,
    motor_count=4) — mirrors the CLI session's t-motor_antigravity_mn4006_380
    (unbound, catalog_ref=None — the bug is independent of Catalog v1)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = _comp(
        "motors", "propulsion_active",
        motor_count=PropertyValue(value=4, confidence=0.9, source="declared"),
        thrust_n=PropertyValue(value=20.0, confidence=0.9, source="declared"),
        power_w=PropertyValue(value=500.0, confidence=0.9, source="declared"),
    ).model_copy(update={"output_magnitude": "thrust_n"})
    dp = ps.design_properties.model_copy(update={"components": {"motors": motors}})
    ps2 = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {
            **ps.current_parameters,
            "motor_count": 4, "per_motor_max_thrust_n": 20.0, "motor_power_w": 500.0,
        },
    })
    orch.workspace_manager.save_state(ps2)
    return orch


def test_unrelated_numeric_iterate_does_not_revert_dse_elevated_motor_params(tmp_path: Path):
    orch = _project_with_declared_motors(tmp_path)

    # 1) DSE apply (params-only, mejorar_estabilidad) raises motor_count and
    #    per_motor_max_thrust_n above the component's declared 4 / 20.0.
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    applied = orch.handle_user_text("aplica la mejor", _RefuseLLM())
    assert applied["status"] == "ok"

    after_dse = orch.state_manager.load_active_project(orch.workspace_manager)
    elevated_motor_count = after_dse.current_parameters.get("motor_count")
    elevated_thrust = after_dse.current_parameters.get("per_motor_max_thrust_n")
    assert elevated_motor_count is not None and elevated_motor_count > 4, (
        "DSE apply did not elevate motor_count — precondition for this repro not met"
    )
    assert elevated_thrust is not None and elevated_thrust > 20.0, (
        "DSE apply did not elevate per_motor_max_thrust_n — precondition for this repro not met"
    )

    # 2) A completely unrelated numeric iterate turn — safety_factor has
    #    nothing to do with motors.
    orch.handle_user_text("cambia safety_factor", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())
    orch.handle_user_text("safety_factor", _RefuseLLM())
    orch.handle_user_text("1.4", _RefuseLLM())
    orch.handle_user_text("si", _RefuseLLM())
    final = orch.handle_user_text("si", _RefuseLLM())
    assert final["status"] == "ok"

    after_iterate = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after_iterate.current_parameters.get("safety_factor") == pytest.approx(1.4)

    # 3) FIXED: the DSE-elevated motor capacity survives an unrelated turn —
    #    sync_motors_component_from_params kept components["motors"] current
    #    right after the DSE apply, so this turn's resolve_propulsion_parameters
    #    re-derives the SAME elevated values instead of the stale pre-DSE ones.
    assert after_iterate.current_parameters.get("motor_count") == elevated_motor_count, (
        f"motor_count silently reverted: {elevated_motor_count} -> "
        f"{after_iterate.current_parameters.get('motor_count')} during an "
        "unrelated safety_factor iterate turn"
    )
    assert after_iterate.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        elevated_thrust
    ), (
        f"per_motor_max_thrust_n silently reverted: {elevated_thrust} -> "
        f"{after_iterate.current_parameters.get('per_motor_max_thrust_n')} during an "
        "unrelated safety_factor iterate turn"
    )


def test_dse_apply_itself_does_not_revert_its_own_elevation(tmp_path: Path):
    """Regression-shaped control: the DSE apply step itself is NOT where the
    revert happens — `_handle_apply_exploration` never calls
    resolve_propulsion_parameters, so its own persisted result is correct."""
    orch = _project_with_declared_motors(tmp_path)

    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    orch.handle_user_text("aplica la mejor", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") > 4
    assert saved.current_parameters.get("per_motor_max_thrust_n") > 20.0


def test_dse_apply_syncs_motors_component_to_match_elevated_params(tmp_path: Path):
    """T3 (fix contract §3.3): after a params-only DSE apply,
    components["motors"] is no longer left stale — its motor_count/thrust_n
    match the just-elevated current_parameters immediately, tagged
    source="calculated" to distinguish DSE math from a user-typed value.
    power_w (untouched by the sync — not one of the three propulsion fields
    resolve_propulsion_parameters derives) stays exactly as declared."""
    orch = _project_with_declared_motors(tmp_path)

    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    orch.handle_user_text("aplica la mejor", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_component = saved.design_properties.components["motors"]
    assert motors_component.properties["motor_count"].value == saved.current_parameters["motor_count"]
    assert motors_component.properties["thrust_n"].value == pytest.approx(
        saved.current_parameters["per_motor_max_thrust_n"]
    )
    assert motors_component.properties["motor_count"].source == "calculated"
    assert motors_component.properties["thrust_n"].source == "calculated"
    # Not one of the synced fields — stays exactly as originally declared.
    assert motors_component.properties["power_w"].value == 500.0
    assert motors_component.properties["power_w"].source == "declared"


def test_catalog_ref_invalidation_unrelated_to_this_revert(tmp_path: Path):
    """G5 Q4: invalidate_diverged_catalog_refs (Catalog v1 Impl B) is not the
    cause — it only clears catalog_ref (None here, since these motors were
    never SKU-bound) and never touches motor_count/per_motor_max_thrust_n."""
    orch = _project_with_declared_motors(tmp_path)
    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    orch.handle_user_text("aplica la mejor", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.design_properties.components["motors"].catalog_ref is None


def test_sku_bound_motor_dse_diverge_still_clears_catalog_ref_and_syncs(tmp_path: Path):
    """T5 (fix contract §5): Impl B regression, now combined with the sync.

    Call order matters (see component_sync.py's own docstring): invalidate_
    diverged_catalog_refs must run against the STILL-STALE component to
    correctly detect true SKU divergence; sync_motors_component_from_params
    then brings motor_count/thrust_n up to date. If sync ran first, the
    catalog_ref divergence check would find nothing to compare against (the
    component would already match the new params) and incorrectly leave a
    stale SKU label in place."""
    from jarvis.core.catalog_bind import bind_motor_from_catalog
    from jarvis.core.component_writers import set_motor_component

    orch = _project_with_declared_motors(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    suggestion = {
        "idx": 1, "name": "sunnysky_x2216_11", "thrust_n": 12.5, "kv_rating": 1100,
        "weight_g": 62, "max_watts": 280, "is_generic": False,
    }
    bound_spec = bind_motor_from_catalog(suggestion)
    ps_bound = set_motor_component(ps, bound_spec, 280.0)
    ps_bound = ps_bound.model_copy(update={
        "current_parameters": {**ps_bound.current_parameters, "per_motor_max_thrust_n": 12.5}
    })
    orch.workspace_manager.save_state(ps_bound)
    assert ps_bound.design_properties.components["motors"].catalog_ref is not None

    orch.handle_user_text("ayudame a mejorar la estabilidad", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())
    applied = orch.handle_user_text("aplica la mejor", _RefuseLLM())
    assert applied["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_component = saved.design_properties.components["motors"]
    # SKU identity correctly cleared — the DSE-scaled thrust no longer
    # matches sunnysky_x2216_11's real 12.5 N.
    assert motors_component.catalog_ref is None
    # ...and the component is still kept current with the new params (the
    # G5 fix itself), not left stale just because identity was cleared.
    assert motors_component.properties["thrust_n"].value == pytest.approx(
        saved.current_parameters["per_motor_max_thrust_n"]
    )
    assert motors_component.properties["thrust_n"].value > 12.5
