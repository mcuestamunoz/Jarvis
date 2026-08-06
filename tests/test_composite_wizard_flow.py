"""Tests for Fase 5 — Wizard dinámico para bloques composite.

Commit structure:
  Commit 1 — _set_pending_next_block: rama composite (orchestrator.py)
  Commit 2 — build_startup_context: proactive hint para composite (orchestrator.py)
  Commit 3 — estos tests
"""
from __future__ import annotations

import pytest

from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
)
from jarvis.core.orchestrator import JarvisOrchestrator
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


def _high_completeness_battery() -> ComponentSpec:
    """Return a battery ComponentSpec with completeness='high' (not 'low')."""
    return ComponentSpec(
        name="LiPo 6S 5000mAh",
        component_type="battery",
        completeness="high",
        properties={},
    )


def _high_completeness_motors() -> ComponentSpec:
    """Return a motors ComponentSpec with completeness='high' (not 'low')."""
    return ComponentSpec(
        name="2306 2400KV",
        component_type="motors",
        completeness="high",
        properties={},
    )


def _patch_energy_as_next_block(orchestrator, *, with_components: bool):
    """
    Configure project state so that energy is the first pending block.
    If with_components=True, inject battery and motors with completeness='high'
    so Phase B (params wizard) is activated. Otherwise leave components absent
    so Phase A (component description wizard) fires.
    """
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy", "structure", "control"],
        "system_priority": ["energy", "structure", "control"],
    })
    params = dict(project_state.current_parameters or {})
    # Remove energy params so the block is not complete.
    params.pop("battery_capacity_wh", None)
    params.pop("motor_power_w", None)

    if with_components:
        components = dict(dp.components)
        components["battery"] = _high_completeness_battery()
        components["motors"] = _high_completeness_motors()
        dp = dp.model_copy(update={"components": components})

    updated = project_state.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
    })
    orchestrator.workspace_manager.save_state(updated)


# ── Commit 1: _set_pending_next_block ─────────────────────────────────────────

class TestSetPendingNextBlockComposite:

    def test_energy_no_components_sets_missing_component_definition(self, tmp_path):
        """When energy is the next block and no components are defined,
        _set_pending_next_block must activate the component description wizard
        (Phase A) via MISSING_COMPONENT_DEFINITION."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=False)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_define_missing is True
        assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
        # pending_missing_params must list the expected component keys
        assert len(session.pending_missing_params) > 0
        assert all(k in session.pending_missing_params for k in ("battery", "motors"))

    def test_energy_with_components_sets_missing_energy_parameters(self, tmp_path):
        """When energy is the next block and all components are already defined
        (completeness != 'low'), _set_pending_next_block must activate the
        numeric param wizard (Phase B) via MISSING_ENERGY_PARAMETERS."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=True)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_define_missing is True
        assert session.pending_missing_reason == MISSING_ENERGY_PARAMETERS
        assert len(session.pending_missing_params) > 0

    def test_energy_no_components_params_list_contains_battery_and_motors(self, tmp_path):
        """Phase A must list the missing component keys (battery, motors) as
        pending_missing_params so that the component description intercept
        routes the description to the correct dispatcher."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=False)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert "battery" in session.pending_missing_params
        assert "motors" in session.pending_missing_params

    def test_energy_low_completeness_motors_triggers_phase_a(self, tmp_path):
        """A motors component with completeness='low' is treated as absent.
        Even when battery is present and high, Phase A must fire."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)

        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        dp = project_state.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["energy", "structure"],
            "system_priority": ["energy", "structure"],
        })
        params = dict(project_state.current_parameters or {})
        params.pop("battery_capacity_wh", None)
        params.pop("motor_power_w", None)

        low_motors = ComponentSpec(name="", component_type="motors", completeness="low")
        components = {"battery": _high_completeness_battery(), "motors": low_motors}
        dp = dp.model_copy(update={"components": components})
        updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
        orchestrator.workspace_manager.save_state(updated)

        orchestrator._set_pending_next_block()

        session = orchestrator.state_manager.runtime_state.session
        assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION


# ── Commit 2: build_startup_context ───────────────────────────────────────────

class TestBuildStartupContextComposite:

    def test_composite_no_components_proactive_question_contains_block_label(self, tmp_path):
        """When energy is not_started and has no components, build_startup_context
        must produce a proactive_question that names the block."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=False)

        ctx = orchestrator.build_startup_context()

        assert ctx["next_architecture_block"] == "energy"
        # Proactive question must mention the block and include the component hint.
        pq = ctx["proactive_question"]
        assert pq is not None
        assert "energy" in pq.lower() or "energía" in pq.lower() or "Energía" in pq

    def test_composite_no_components_param_definition_reason_is_missing_component_definition(
        self, tmp_path
    ):
        """build_startup_context must expose MISSING_COMPONENT_DEFINITION as
        param_definition_reason when the composite block is in Phase A."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=False)

        ctx = orchestrator.build_startup_context()

        assert ctx["param_definition_reason"] == MISSING_COMPONENT_DEFINITION

    def test_composite_no_components_missing_params_lists_components(self, tmp_path):
        """When Phase A fires, missing_params in startup context must list
        the component keys that are absent."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=False)

        ctx = orchestrator.build_startup_context()

        assert "battery" in ctx["missing_params"]
        assert "motors" in ctx["missing_params"]

    def test_composite_with_components_param_definition_reason_is_energy_params(self, tmp_path):
        """When Phase B fires (all components present), build_startup_context must
        expose MISSING_ENERGY_PARAMETERS as param_definition_reason."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=True)

        ctx = orchestrator.build_startup_context()

        assert ctx["param_definition_reason"] == MISSING_ENERGY_PARAMETERS


# ── K3 (Bug 61): differentiated in_progress message ──────────────────────────

def _patch_energy_inprogress_components_missing(orchestrator):
    """Energy block: params_ok=True (motor_power_w present), components still at low.
    _block_progress_status → 'in_progress' because components_ok=False.
    """
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy", "structure"],
        "system_priority": ["energy", "structure"],
    })
    params = dict(project_state.current_parameters or {})
    # Ensure the param side of energy is satisfied so status is in_progress, not not_started.
    params["battery_capacity_wh"] = 5000.0
    params["motor_power_w"] = 120.0

    # Leave components at default (low completeness) so components_ok=False.
    updated = project_state.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
    })
    orchestrator.workspace_manager.save_state(updated)


def _patch_energy_inprogress_params_missing(orchestrator):
    """Energy block: components present with completeness='high', params absent.
    _block_progress_status → 'in_progress' because params_ok=False.
    """
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy", "structure"],
        "system_priority": ["energy", "structure"],
    })
    params = dict(project_state.current_parameters or {})
    # Remove energy params so params_ok=False.
    params.pop("battery_capacity_wh", None)
    params.pop("motor_power_w", None)

    # Inject components at high completeness so components_ok=True.
    components = dict(dp.components)
    components["battery"] = _high_completeness_battery()
    components["motors"] = _high_completeness_motors()
    dp = dp.model_copy(update={"components": components})

    updated = project_state.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
    })
    orchestrator.workspace_manager.save_state(updated)


class TestGetBlockInProgressReason:
    """Unit tests for get_block_in_progress_reason — single source of truth for Bug 61."""

    def test_composite_components_missing_returns_missing_components(self, tmp_path):
        """When components are low/absent: reason must be 'missing_components'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        # Default state: no non-low components defined.
        reason = orchestrator.get_block_in_progress_reason(project_state, "energy")
        assert reason == "missing_components"

    def test_composite_components_present_returns_missing_params(self, tmp_path):
        """When all components are non-low: reason must be 'missing_params'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_as_next_block(orchestrator, with_components=True)
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        reason = orchestrator.get_block_in_progress_reason(project_state, "energy")
        assert reason == "missing_params"

    def test_composite_both_missing_reason_is_components(self, tmp_path):
        """Edge: both components AND params missing → 'missing_components' has priority.
        (_block_progress_status returns 'not_started' in this case, but
        get_block_in_progress_reason must still return the correct priority.)"""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        # Remove components and params: both sides missing.
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        dp = project_state.design_properties.model_copy(update={"components": {}})
        params = {k: v for k, v in (project_state.current_parameters or {}).items()
                  if k not in ("battery_capacity_wh", "motor_power_w")}
        updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
        orchestrator.workspace_manager.save_state(updated)
        project_state_clean = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        reason = orchestrator.get_block_in_progress_reason(project_state_clean, "energy")
        assert reason == "missing_components", (
            "When both components and params are missing, components have priority"
        )


class TestBuildStartupContextInProgressMessage:
    """K3 (Bug 61): proactive_question must reflect the actual reason for in_progress."""

    def test_inprogress_components_missing_shows_component_message(self, tmp_path):
        """params_ok=True, components_ok=False → 'declara los componentes'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_inprogress_components_missing(orchestrator)

        ctx = orchestrator.build_startup_context()

        pq = ctx.get("proactive_question", "")
        assert "declara los componentes" in pq, (
            f"Expected 'declara los componentes' in proactive_question, got: {pq!r}"
        )

    def test_inprogress_params_missing_shows_params_message(self, tmp_path):
        """params_ok=False, components_ok=True → in_progress due to missing params.

        Note: when params are missing, the higher-priority param proactive question
        (e.g. "¿Definimos battery_capacity_wh?") fires before the architecture
        in_progress branch. So the proactive_question will be param-specific,
        not the generic in_progress message — but it must NOT say "declara los
        componentes", since components are already present.
        """
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        _patch_energy_inprogress_params_missing(orchestrator)

        ctx = orchestrator.build_startup_context()

        pq = ctx.get("proactive_question", "")
        assert "declara los componentes" not in pq, (
            f"Must NOT suggest declaring components when components are already present. Got: {pq!r}"
        )


# ── Bug 67: get_block_in_progress_reason for 'component'-type blocks ──────────

class TestGetBlockInProgressReasonComponentType:
    """Bug 67: 'control' block (type='component') must report 'missing_components'
    when sensors are absent, not the generic 'missing_params'."""

    def test_control_block_returns_missing_components_when_sensor_absent(self, tmp_path):
        """Bloque control sin sensors → reason must be 'missing_components'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator, tmp_path)
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        # Ensure no sensors component is present (default state after project creation).
        components = project_state.design_properties.components
        assert "sensors" not in components or True  # may or may not be present; ensure absent
        dp = project_state.design_properties.model_copy(
            update={"components": {k: v for k, v in components.items() if k != "sensors"}}
        )
        updated = project_state.model_copy(update={"design_properties": dp})
        orchestrator.workspace_manager.save_state(updated)
        clean_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

        reason = orchestrator.get_block_in_progress_reason(clean_state, "control")

        assert reason == "missing_components", (
            f"Bug 67: 'control' block without sensors must report 'missing_components', "
            f"got {reason!r}"
        )
