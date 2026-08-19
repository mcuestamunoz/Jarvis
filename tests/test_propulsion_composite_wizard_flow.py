"""Tests for Fase 6 — Propulsion como bloque composite (motors + propellers + params).

Commit structure:
  Commit 1 — BLOCK_TYPE["propulsion"] = "composite"  (system_architecture_catalog.py)
  Commit 2 — propellers dispatcher + UX strings      (orchestrator.py)
  Commit 3 — DA-MOTORS-3 rename motor_count          (parameter_requirements.py + workspace_manager.py + …)
  Commit 4 — estos tests
"""
from __future__ import annotations

import pytest

from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_PROPULSION_PARAMETERS,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.system_architecture_catalog import BLOCK_TYPE, BLOCK_TO_COMPONENTS
from jarvis.schemas.action_schema import ComponentSpec


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_drone_project(orchestrator, tmp_path):
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _medium_stub(component_type: str = "generic") -> ComponentSpec:
    return ComponentSpec(component_type=component_type, completeness="medium", source="declared")


def _patch_propulsion_as_next_block(orchestrator, *, with_components: bool):
    """Configure project state so propulsion is the first pending block.

    If with_components=True, inject motors and propellers with completeness='medium'
    so Phase B (params wizard) fires. Otherwise leave components absent (Phase A).
    """
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
    })
    params = dict(project_state.current_parameters or {})
    # Remove propulsion params so the block is not complete.
    params.pop("motor_count", None)
    params.pop("per_motor_max_thrust_n", None)

    if with_components:
        components = dict(dp.components)
        components["motors"] = _medium_stub("motors")
        components["propellers"] = _medium_stub("propellers")
        # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"].
        components["esc"] = _medium_stub("esc")
        dp = dp.model_copy(update={"components": components})

    updated = project_state.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
    })
    orchestrator.workspace_manager.save_state(updated)


# ── Catalog: propulsion is composite ─────────────────────────────────────────

def test_propulsion_block_type_is_composite():
    """Fase 6: BLOCK_TYPE['propulsion'] must be 'composite'."""
    assert BLOCK_TYPE["propulsion"] == "composite"


def test_propulsion_components_are_motors_and_propellers():
    """BLOCK_TO_COMPONENTS['propulsion'] must include motors and propellers."""
    keys = BLOCK_TO_COMPONENTS.get("propulsion", [])
    assert "motors" in keys
    assert "propellers" in keys


# ── _set_pending_next_block: Phase A (no components) ─────────────────────────

class TestSetPendingNextBlockPropulsionComposite:

    def test_no_motors_no_propellers_triggers_phase_a(self, tmp_path):
        """When propulsion is next and no components are defined, Phase A fires:
        pending_missing_reason == MISSING_COMPONENT_DEFINITION."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_propulsion_as_next_block(orchestrator, with_components=False)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_define_missing is True
        assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
        assert "motors" in session.pending_missing_params
        assert "propellers" in session.pending_missing_params

    def test_motors_from_energy_propellers_absent_still_phase_a(self, tmp_path):
        """DA-MOTORS-2: motors component shared with energy. If only motors is present
        (completeness=medium) but propellers is absent, Phase A still fires for propellers."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        dp = project_state.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["propulsion", "energy"],
            "system_priority": ["propulsion", "energy"],
            "components": {"motors": _medium_stub("motors")},  # motors present, propellers absent
        })
        params = dict(project_state.current_parameters or {})
        params.pop("motor_count", None)
        params.pop("per_motor_max_thrust_n", None)
        updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
        orchestrator.workspace_manager.save_state(updated)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
        assert "propellers" in session.pending_missing_params

    def test_both_components_ok_triggers_phase_b(self, tmp_path):
        """When motors + propellers present (medium+), Phase B fires:
        pending_missing_reason == MISSING_PROPULSION_PARAMETERS."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_propulsion_as_next_block(orchestrator, with_components=True)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_define_missing is True
        assert session.pending_missing_reason == MISSING_PROPULSION_PARAMETERS
        assert "motor_count" in session.pending_missing_params
        assert "per_motor_max_thrust_n" in session.pending_missing_params


# ── Propellers dispatcher ─────────────────────────────────────────────────────

class TestPropellersDispatcher:

    def test_propellers_description_saves_to_propellers_component(self, tmp_path):
        """'hélices 10x4.5' → _set_propeller_component, NOT _set_control_component.

        The component key must be 'propellers' (not 'flight_controller' or 'sensors').
        """
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        # Set up session with propellers as the pending component key.
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        dp = project_state.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["propulsion"],
            "system_priority": ["propulsion"],
        })
        updated = project_state.model_copy(update={"design_properties": dp})
        orchestrator.workspace_manager.save_state(updated)

        session = orchestrator.state_manager.runtime_state.session.model_copy(update={
            "pending_define_missing": True,
            "pending_missing_params": ["propellers"],
            "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        })
        orchestrator.state_manager.set_runtime_session(session)

        result = orchestrator._handle_component_description("hélices 10x4.5 carbono", session)

        assert result["status"] == "ok"
        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert "propellers" in saved.design_properties.components
        # Must NOT have been routed to control components
        assert "flight_controller" not in saved.design_properties.components
        assert "sensors" not in saved.design_properties.components

    def test_propellers_description_does_not_overwrite_motors(self, tmp_path):
        """Propellers save must not touch the 'motors' component key."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        motors_spec = _medium_stub("motors")
        dp = project_state.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["propulsion"],
            "system_priority": ["propulsion"],
            "components": {"motors": motors_spec},
        })
        updated = project_state.model_copy(update={"design_properties": dp})
        orchestrator.workspace_manager.save_state(updated)

        session = orchestrator.state_manager.runtime_state.session.model_copy(update={
            "pending_define_missing": True,
            "pending_missing_params": ["propellers"],
            "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        })
        orchestrator.state_manager.set_runtime_session(session)

        orchestrator._handle_component_description("hélices 10x4.5", session)

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        # motors must still be present and unchanged
        assert "motors" in saved.design_properties.components
        assert saved.design_properties.components["motors"].completeness == "medium"


# ── build_startup_context: proactive hint ─────────────────────────────────────

class TestBuildStartupContextPropulsion:

    def test_propulsion_no_components_proactive_question_mentions_propulsion(self, tmp_path):
        """When propulsion is the next block (Phase A), build_startup_context must
        produce a proactive_question mentioning propulsion/motors/hélices."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_propulsion_as_next_block(orchestrator, with_components=False)

        ctx = orchestrator.build_startup_context()

        assert ctx.get("next_architecture_block") == "propulsion"
        pq = ctx.get("proactive_question") or ""
        assert pq, "proactive_question must not be empty"
        # Must reference propulsion domain in some form
        pq_lower = pq.lower()
        assert (
            "propuls" in pq_lower
            or "motor" in pq_lower
            or "hélice" in pq_lower
            or "propeller" in pq_lower
        ), f"proactive_question must mention propulsion/motors/hélices, got: '{pq}'"

    def test_propulsion_no_components_missing_params_lists_motors_and_propellers(self, tmp_path):
        """Phase A: missing_params in startup context must list motors and propellers."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_propulsion_as_next_block(orchestrator, with_components=False)

        ctx = orchestrator.build_startup_context()

        assert "motors" in ctx["missing_params"]
        assert "propellers" in ctx["missing_params"]

    def test_propulsion_with_components_status_is_in_progress(self, tmp_path):
        """Phase B: when motors + propellers present but params absent,
        build_startup_context reports propulsion as in_progress (not not_started).
        The param wizard is pre-loaded via _set_pending_next_block (tested separately)."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_propulsion_as_next_block(orchestrator, with_components=True)

        ctx = orchestrator.build_startup_context()

        assert ctx.get("next_architecture_block") == "propulsion"
        assert ctx.get("next_block_status") == "in_progress"


# ── Full wizard flow: propulsion completes after both components ───────────────

class TestPropulsionCompletesAfterBothComponents:

    def test_propulsion_complete_after_motors_and_propellers_and_params(self, tmp_path):
        """End-to-end: propulsion goes complete once motors, propellers and params are all set."""
        from jarvis.core.orchestrator import JarvisOrchestrator

        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        dp = project_state.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["propulsion", "energy"],
            "system_priority": ["propulsion", "energy"],
            "components": {
                "motors": _medium_stub("motors"),
                "propellers": _medium_stub("propellers"),
                # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"].
                "esc": _medium_stub("esc"),
            },
        })
        params = dict(project_state.current_parameters or {})
        # motor_count already set via workspace_manager remap of "motors": 4
        # per_motor_max_thrust_n also set from create_project
        updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
        orchestrator.workspace_manager.save_state(updated)

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        status = JarvisOrchestrator._block_progress_status(
            "propulsion",
            project_state.design_properties,
            project_state.current_parameters or {},
        )
        assert status == "complete", (
            f"propulsion must be 'complete' with params + motors + propellers + esc, got '{status}'"
        )


# ── D6: Propellers physics bridge ─────────────────────────────────────────────

class TestPropellersPhysicsBridge:

    def test_set_propeller_component_writes_diameter_bridge(self, tmp_path):
        """set_propeller_component with '10x4.5' spec → propeller_diameter_in == 10.0 in params."""
        from jarvis.core.component_writers import set_propeller_component
        from jarvis.core.component_inference import infer_component
        from jarvis.domains.aerial import aerial_registry

        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

        spec = infer_component("hélices 10x4.5", registry=aerial_registry)
        updated = set_propeller_component(project_state, spec)

        assert updated.current_parameters.get("propeller_diameter_in") == pytest.approx(10.0)

    def test_set_propeller_component_diameter_none_removes_param(self, tmp_path):
        """Spec without diameter_in → propeller_diameter_in removed from params."""
        from jarvis.core.component_writers import set_propeller_component
        from jarvis.schemas.action_schema import ComponentSpec

        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        # Pre-set the param to verify it gets removed
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params["propeller_diameter_in"] = 10.0
        project_state = project_state.model_copy(update={"current_parameters": params})

        spec = ComponentSpec(
            component_type="propulsion_passive",
            suggested_key="propellers",
            completeness="medium",
            source="declared",
        )
        updated = set_propeller_component(project_state, spec)

        assert "propeller_diameter_in" not in (updated.current_parameters or {})

    def test_propeller_diameter_affects_thrust_calculation(self, tmp_path):
        """propeller_diameter_in + propeller_rpm → thrust_total_n > 0 (not missing_propulsion)."""
        from jarvis.core.component_writers import set_propeller_component
        from jarvis.core.component_inference import infer_component
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.domains.aerial import aerial_registry

        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        # Create project WITHOUT per_motor_max_thrust_n so propeller path is the only route
        orchestrator.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron de prueba",
                "payload_kg": 1.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "motors": 4,
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

        spec = infer_component("hélices 10x4.5", registry=aerial_registry)
        updated = set_propeller_component(project_state, spec)

        params = dict(updated.current_parameters or {})
        params["propeller_rpm"] = 8000.0  # operational param, set directly for this test

        engine = CalculationEngine()
        result = engine.build(params)

        assert result.available_total_thrust_n is not None
        assert result.available_total_thrust_n > 0, (
            f"Expected available_total_thrust_n > 0 with propeller bridge, got {result.available_total_thrust_n}"
        )
