"""Tests for the architecture progress engine.

Covers:
  - _block_progress_status (static helper)
  - _next_pending_block
  - _architecture_progress_str
  - _block_label_for
  - build_startup_context fields: architecture_progress, next_architecture_block,
    next_architecture_label, next_block_status
  - _append_arch_progress_hint after define_missing_params completion
  - Edge cases: skip blocks, partial completion, all complete
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec
from jarvis.schemas.state_schema import DesignProperties, ProjectState


# ── Fixtures ──────────────────────────────────────────────────────────────────

_DRONE_PARAMS_FULL = {
    "vehicle_type": "dron",
    "objective": "dron de prueba",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 20.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _make_design_props(*, components: dict | None = None, **kwargs) -> DesignProperties:
    """Helper to build a DesignProperties with given components and optional overrides."""
    base = {
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components or {},
    }
    base.update(kwargs)
    return DesignProperties(**base)


def _low_stub(component_type: str = "generic_component") -> ComponentSpec:
    return ComponentSpec(component_type=component_type, completeness="low", source="declared")


def _medium_stub(component_type: str = "generic_component") -> ComponentSpec:
    return ComponentSpec(component_type=component_type, completeness="medium", source="declared")


# ── _block_progress_status: param-driven blocks ───────────────────────────────

class TestBlockProgressStatusParamDriven:
    def _dp(self) -> DesignProperties:
        return _make_design_props()

    def test_propulsion_not_started_when_no_params(self):
        dp = self._dp()
        status = JarvisOrchestrator._block_progress_status("propulsion", dp, {})
        assert status == "not_started"

    def test_propulsion_in_progress_when_only_motors_defined(self):
        # Composite: only motor_count (no per_motor_max_thrust_n, no components) → not_started
        # With both params but no components → in_progress
        dp = self._dp()
        status = JarvisOrchestrator._block_progress_status(
            "propulsion", dp, {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        )
        assert status == "in_progress"

    def test_propulsion_complete_when_both_params_defined(self):
        # Composite: params_ok + motors + propellers + esc components → complete
        dp = _make_design_props(components={
            "motors": _medium_stub(),
            "propellers": _medium_stub(),
            "esc": _medium_stub(),  # ERF-2 ★5
        })
        status = JarvisOrchestrator._block_progress_status(
            "propulsion", dp, {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        )
        assert status == "complete"

    def test_energy_not_started_when_no_energy_params(self):
        dp = self._dp()
        status = JarvisOrchestrator._block_progress_status("energy", dp, {})
        assert status == "not_started"

    def test_energy_in_progress_when_params_ok_but_no_components(self):
        # Composite: both energy params defined but no components yet → in_progress
        dp = self._dp()
        status = JarvisOrchestrator._block_progress_status(
            "energy", dp, {"battery_capacity_wh": 100.0, "motor_power_w": 50.0}
        )
        assert status == "in_progress"

    def test_energy_complete_when_params_and_components_ok(self):
        # Composite: both params ok AND both components ok → complete
        dp = _make_design_props(components={
            "battery": _medium_stub(),
            "motors": _medium_stub(),
        })
        status = JarvisOrchestrator._block_progress_status(
            "energy", dp, {"battery_capacity_wh": 100.0, "motor_power_w": 50.0}
        )
        assert status == "complete"


# ── _block_progress_status: component-driven blocks ──────────────────────────

class TestBlockProgressStatusComponentDriven:
    def test_structure_not_started_when_frame_is_low_stub(self):
        dp = _make_design_props(components={"frame": _low_stub("frame")})
        status = JarvisOrchestrator._block_progress_status("structure", dp, {})
        assert status == "not_started"

    def test_structure_not_started_when_frame_absent(self):
        dp = _make_design_props(components={})
        status = JarvisOrchestrator._block_progress_status("structure", dp, {})
        assert status == "not_started"

    def test_structure_complete_when_frame_is_medium(self):
        dp = _make_design_props(components={"frame": _medium_stub("frame")})
        status = JarvisOrchestrator._block_progress_status("structure", dp, {})
        assert status == "complete"

    def test_control_not_started_when_all_components_low(self):
        dp = _make_design_props(components={
            "flight_controller": _low_stub(),
            "sensors": _low_stub(),
        })
        status = JarvisOrchestrator._block_progress_status("control", dp, {})
        assert status == "not_started"

    def test_control_in_progress_when_one_component_medium(self):
        dp = _make_design_props(components={
            "flight_controller": _medium_stub(),
            "sensors": _low_stub(),
        })
        status = JarvisOrchestrator._block_progress_status("control", dp, {})
        assert status == "in_progress"

    def test_control_complete_when_all_components_medium(self):
        dp = _make_design_props(components={
            "flight_controller": _medium_stub(),
            "sensors": _medium_stub(),
        })
        status = JarvisOrchestrator._block_progress_status("control", dp, {})
        assert status == "complete"


# ── _next_pending_block ───────────────────────────────────────────────────────

class TestNextPendingBlock:
    def _orchestrator(self, tmp_path: Path) -> JarvisOrchestrator:
        return JarvisOrchestrator(workspace_root=tmp_path)

    def _project_state(self, params: dict, dp: DesignProperties) -> ProjectState:
        return ProjectState(
            project_id="abc123",
            project_slug="test",
            objective="test",
            workspace_path="/tmp/test",
            current_parameters=params,
            design_properties=dp,
        )

    def test_returns_none_when_system_priority_empty(self, tmp_path: Path):
        orch = self._orchestrator(tmp_path)
        dp = DesignProperties()  # system_defined=False, priority=[]
        ps = self._project_state({}, dp)
        assert orch._next_pending_block(ps) is None

    def test_returns_first_incomplete_block(self, tmp_path: Path):
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props()
        ps = self._project_state({}, dp)
        result = orch._next_pending_block(ps)
        assert result is not None
        assert result == ("propulsion", "not_started")

    def test_advances_past_complete_propulsion(self, tmp_path: Path):
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "motors": _medium_stub(),
            "propellers": _medium_stub(),
            "esc": _medium_stub(),  # ERF-2 ★5
        })
        params = {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        ps = self._project_state(params, dp)
        result = orch._next_pending_block(ps)
        assert result is not None
        assert result[0] == "energy"

    def test_returns_in_progress_when_partial_energy(self, tmp_path: Path):
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "motors": _medium_stub(),
            "propellers": _medium_stub(),
            "esc": _medium_stub(),  # ERF-2 ★5
        })
        params = {
            "motor_count": 4,
            "per_motor_max_thrust_n": 20.0,
            "battery_capacity_wh": 100.0,
            "motor_power_w": 50.0,  # params_ok=True; components still missing → in_progress
        }
        ps = self._project_state(params, dp)
        result = orch._next_pending_block(ps)
        assert result == ("energy", "in_progress")

    def test_returns_none_when_all_blocks_complete(self, tmp_path: Path):
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "frame": _medium_stub(),
            "flight_controller": _medium_stub(),
            "sensors": _medium_stub(),
            "battery": _medium_stub(),   # energy composite component
            "motors": _medium_stub(),    # shared: propulsion + energy composite
            "propellers": _medium_stub(),  # propulsion composite component
            "esc": _medium_stub(),  # ERF-2 ★5: propulsion composite component
        })
        params = {
            "motor_count": 4,
            "per_motor_max_thrust_n": 20.0,
            "battery_capacity_wh": 100.0,
            "motor_power_w": 50.0,
        }
        ps = self._project_state(params, dp)
        result = orch._next_pending_block(ps)
        assert result is None

    def test_user_can_skip_blocks_non_sequential(self, tmp_path: Path):
        """Energy can be complete even if structure is still not_started."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "battery": _medium_stub(),    # energy composite components present
            "motors": _medium_stub(),     # shared: propulsion + energy
            "propellers": _medium_stub(), # propulsion composite component
            "esc": _medium_stub(),        # ERF-2 ★5: propulsion composite component
            # frame, flight_controller, sensors absent
        })
        params = {
            "motor_count": 4,
            "per_motor_max_thrust_n": 20.0,
            "battery_capacity_wh": 100.0,
            "motor_power_w": 50.0,
        }
        ps = self._project_state(params, dp)
        # propulsion + energy complete → next is structure
        result = orch._next_pending_block(ps)
        assert result is not None
        assert result[0] == "structure"


# ── _architecture_progress_str ────────────────────────────────────────────────

class TestArchitectureProgressStr:
    def _orch(self, tmp_path: Path) -> JarvisOrchestrator:
        return JarvisOrchestrator(workspace_root=tmp_path)

    def _ps(self, params: dict, dp: DesignProperties) -> ProjectState:
        return ProjectState(
            project_id="x", project_slug="x", objective="x",
            workspace_path="/tmp/x", current_parameters=params, design_properties=dp,
        )

    def test_returns_empty_string_when_no_priority(self, tmp_path: Path):
        orch = self._orch(tmp_path)
        ps = self._ps({}, DesignProperties())
        assert orch._architecture_progress_str(ps) == ""

    def test_zero_complete_shows_0_slash_4(self, tmp_path: Path):
        orch = self._orch(tmp_path)
        dp = _make_design_props()
        ps = self._ps({}, dp)
        assert orch._architecture_progress_str(ps) == "0/4"

    def test_one_complete_shows_1_slash_4(self, tmp_path: Path):
        orch = self._orch(tmp_path)
        dp = _make_design_props(components={
            "motors": _medium_stub(),
            "propellers": _medium_stub(),
            "esc": _medium_stub(),  # ERF-2 ★5
        })
        params = {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        ps = self._ps(params, dp)
        assert orch._architecture_progress_str(ps) == "1/4"

    def test_all_complete_shows_4_slash_4(self, tmp_path: Path):
        orch = self._orch(tmp_path)
        dp = _make_design_props(components={
            "frame": _medium_stub(),
            "flight_controller": _medium_stub(),
            "sensors": _medium_stub(),
            "battery": _medium_stub(),    # energy composite
            "motors": _medium_stub(),     # shared: propulsion + energy
            "propellers": _medium_stub(), # propulsion composite
            "esc": _medium_stub(),        # ERF-2 ★5: propulsion composite
        })
        params = {
            "motor_count": 4, "per_motor_max_thrust_n": 20.0,
            "battery_capacity_wh": 100.0, "motor_power_w": 50.0,
        }
        ps = self._ps(params, dp)
        assert orch._architecture_progress_str(ps) == "4/4"


# ── build_startup_context: architecture fields ────────────────────────────────

class TestBuildStartupContextArchitecture:
    def _create_project_with_arch(self, tmp_path: Path) -> JarvisOrchestrator:
        """Create a drone project and apply architecture (option A)."""
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        orch.handle({"action": "create_project", "parameters": _DRONE_PARAMS_FULL})
        # Apply architecture option A via system_definition_session
        project_state = orch.state_manager.load_active_project(orch.workspace_manager)
        orch.system_definition_session.start("dron", project_state)
        orch.system_definition_session.answer("A")
        # Inject propulsion components so propulsion block is complete (Fase 6: composite)
        project_state = orch.state_manager.load_active_project(orch.workspace_manager)
        dp = project_state.design_properties.model_copy(update={
            "components": {
                **project_state.design_properties.components,
                "motors": _medium_stub(),
                "propellers": _medium_stub(),
                "esc": _medium_stub(),  # ERF-2 ★5
            }
        })
        orch.workspace_manager.save_state(project_state.model_copy(update={"design_properties": dp}))
        return orch

    def test_arch_fields_absent_when_system_not_defined(self, tmp_path: Path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        orch.handle({"action": "create_project", "parameters": _DRONE_PARAMS_FULL})
        ctx = orch.build_startup_context()
        assert ctx.get("architecture_progress") is None
        assert ctx.get("next_architecture_block") is None

    def test_arch_fields_present_when_system_defined(self, tmp_path: Path):
        orch = self._create_project_with_arch(tmp_path)
        ctx = orch.build_startup_context()
        assert ctx.get("architecture_progress") is not None
        assert ctx.get("next_architecture_block") is not None
        assert ctx.get("next_architecture_label") is not None
        assert ctx.get("next_block_status") in ("not_started", "in_progress")

    def test_first_pending_block_is_energy_after_propulsion_done(self, tmp_path: Path):
        """After full propulsion params are set, next block is energy."""
        orch = self._create_project_with_arch(tmp_path)
        # _DRONE_PARAMS_FULL already has motors + per_motor_max_thrust_n → propulsion complete
        ctx = orch.build_startup_context()
        assert ctx["next_architecture_block"] == "energy"

    def test_proactive_question_references_next_block(self, tmp_path: Path):
        orch = self._create_project_with_arch(tmp_path)
        ctx = orch.build_startup_context()
        # proactive_question should mention the next block label
        pq = ctx.get("proactive_question") or ""
        assert "Siguiente bloque" in pq or "Energía" in pq or "energía" in pq.lower()

    def test_architecture_progress_1_of_4_after_propulsion_complete(self, tmp_path: Path):
        orch = self._create_project_with_arch(tmp_path)
        ctx = orch.build_startup_context()
        assert ctx["architecture_progress"] == "1/4"


# ── _append_arch_progress_hint (integration) ─────────────────────────────────

class TestAppendArchProgressHint:
    def _create_with_arch(self, tmp_path: Path) -> JarvisOrchestrator:
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        orch.handle({"action": "create_project", "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            # No motors/thrust yet so propulsion starts not_started
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        }})
        project_state = orch.state_manager.load_active_project(orch.workspace_manager)
        orch.system_definition_session.start("dron", project_state)
        orch.system_definition_session.answer("A")
        return orch

    def test_hint_appended_after_define_missing_params_ok(self, tmp_path: Path):
        orch = self._create_with_arch(tmp_path)
        # Drive through define_missing_params for motors + thrust
        orch.start_define_missing_params(
            ["motor_count", "per_motor_max_thrust_n"],
            reason="missing_propulsion_parameters",
        )
        orch.param_definition_session.answer("4")
        result = orch.param_definition_session.answer("20")
        # Apply the arch hint manually (simulating the orchestrator intercept)
        if result.get("status") == "ok":
            result = orch._append_arch_progress_hint(result)
        assert "Siguiente bloque" in result["message"] or "Arquitectura" in result["message"]

    def test_hint_not_appended_when_system_not_defined(self, tmp_path: Path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        orch.handle({"action": "create_project", "parameters": {
            "vehicle_type": "dron", "objective": "test", "payload_kg": 2.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.6, "safety_factor": 1.2,
        }})
        result = {"status": "ok", "action": "define_missing_params", "message": "Params OK."}
        out = orch._append_arch_progress_hint(result)
        # system_defined=False → message untouched
        assert out["message"] == "Params OK."


# ── G20/G20-B: _block_label_for dynamic composite labels ─────────────────────

class TestBlockLabelForG20:
    """G20/G20-B: when energy block is in_progress, the label must reflect
    what is actually missing (motor_power_w vs battery vs both), not the
    static 'Energía (batería)'.
    """

    def _orchestrator(self, tmp_path: Path) -> JarvisOrchestrator:
        return JarvisOrchestrator(workspace_root=tmp_path)

    def _project_state(self, params: dict, dp: DesignProperties) -> ProjectState:
        return ProjectState(
            project_id="g20",
            project_slug="test",
            objective="test",
            workspace_path="/tmp/test",
            current_parameters=params,
            design_properties=dp,
        )

    def test_t1_energy_missing_motor_power_w_only(self, tmp_path: Path):
        """Battery and motors components OK, battery_capacity_wh OK,
        only motor_power_w missing → label must mention 'motores', NOT 'batería'."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "battery": _medium_stub(),
            "motors": _medium_stub(),
        })
        ps = self._project_state(
            {**_DRONE_PARAMS_FULL, "battery_capacity_wh": 100.0},
            dp,
        )
        label = orch._block_label_for(ps, "energy")
        assert "potencia motores" in label.lower() or "motor" in label.lower()
        assert "batería" not in label.lower() or "motores" in label.lower()

    def test_t2_energy_missing_battery_component(self, tmp_path: Path):
        """Motors component OK + both energy params present but battery
        component missing → label must mention 'batería'."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "motors": _medium_stub(),
        })
        ps = self._project_state(
            {**_DRONE_PARAMS_FULL, "battery_capacity_wh": 100.0, "motor_power_w": 50.0},
            dp,
        )
        label = orch._block_label_for(ps, "energy")
        assert "batería" in label.lower()

    def test_t3_energy_components_ok_both_params_missing(self, tmp_path: Path):
        """Both components OK, both energy params missing →
        in_progress, label must mention both missing params."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "battery": _medium_stub(),
            "motors": _medium_stub(),
        })
        ps = self._project_state(
            {**_DRONE_PARAMS_FULL},
            dp,
        )
        label = orch._block_label_for(ps, "energy")
        assert "batería" in label.lower() or "capacidad" in label.lower()
        assert "motor" in label.lower()

    def test_t4_energy_complete_uses_static_label(self, tmp_path: Path):
        """Energy block complete → should use the static catalog label
        (regression guard)."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "battery": _medium_stub(),
            "motors": _medium_stub(),
        })
        ps = self._project_state(
            {**_DRONE_PARAMS_FULL, "battery_capacity_wh": 100.0, "motor_power_w": 50.0},
            dp,
        )
        label = orch._block_label_for(ps, "energy")
        assert label == "Energía (batería)"

    def test_t5_propulsion_unaffected(self, tmp_path: Path):
        """Propulsion label should not change (regression guard)."""
        orch = self._orchestrator(tmp_path)
        dp = _make_design_props(components={
            "motors": _medium_stub(),
        })
        ps = self._project_state(
            {**_DRONE_PARAMS_FULL, "motor_count": 4, "per_motor_max_thrust_n": 20.0},
            dp,
        )
        label = orch._block_label_for(ps, "propulsion")
        assert "Propulsión" in label
