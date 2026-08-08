"""Tests for Fase 4 — Motors como componente del bloque energy (composite).

Commit structure:
  Commit 1 — extract_motor_properties: power_w + model, _motor_completeness con power_w
  Commit 2 — _set_motor_component (atomic write: components["motors"] + motor_power_w param)
  Commit 3 — BLOCK_TYPE["energy"] = "composite", BLOCK_TO_COMPONENTS["energy"] = ["battery", "motors"]
  Commit 4 — get_motor_power_w getter en design_utils
  Commit 5 — estos tests + backward compat
"""
from __future__ import annotations

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.component_writers import set_motor_component
from jarvis.domains.aerial import (
    aerial_registry,
    extract_motor_properties,
    _motor_completeness,
)
from jarvis.core.component_inference import infer_component
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.utils.design_utils import get_motor_power_w


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Commit 1: extract_motor_properties ────────────────────────────────────────

class TestExtractMotorProperties:

    def test_extracts_kv_rating(self):
        props = extract_motor_properties("motores 920kv")
        assert "kv_rating" in props
        assert props["kv_rating"].value == pytest.approx(920.0)
        assert props["kv_rating"].unit == "KV"

    def test_extracts_motor_count(self):
        props = extract_motor_properties("4 motores brushless")
        assert "motor_count" in props
        assert props["motor_count"].value == 4

    def test_extracts_thrust_n(self):
        props = extract_motor_properties("15N de empuje por motor")
        assert "thrust_n" in props
        assert props["thrust_n"].value == pytest.approx(15.0)

    def test_extracts_watts_and_power_w(self):
        """Fase 4: watts (legacy) and power_w (canonical) both written."""
        props = extract_motor_properties("motores 100W")
        assert "watts" in props
        assert "power_w" in props
        assert props["watts"].value == pytest.approx(100.0)
        assert props["power_w"].value == pytest.approx(100.0)
        assert props["power_w"].unit == "W"

    def test_extracts_model(self):
        props = extract_motor_properties("motor MN3510 brushless")
        assert "model" in props
        assert "MN3510" in props["model"].value

    def test_full_spec(self):
        """Combined spec: count + kv + watts → all fields extracted."""
        props = extract_motor_properties("4 motores 920kv 100W")
        assert "motor_count" in props
        assert "kv_rating" in props
        assert "watts" in props
        assert "power_w" in props

    def test_empty_input_returns_empty(self):
        props = extract_motor_properties("")
        assert props == {}


# ── Commit 1: _motor_completeness ─────────────────────────────────────────────

class TestMotorCompleteness:

    def _props(self, **kwargs) -> dict:
        return {k: PropertyValue(value=v) for k, v in kwargs.items()}

    def test_high_when_thrust_n_and_motor_count(self):
        props = self._props(thrust_n=15.0, motor_count=4)
        level, _ = _motor_completeness(props)
        assert level == "high"

    def test_high_when_power_w_and_kv_rating(self):
        """Fase 4: power_w counts as a path to high completeness."""
        props = self._props(power_w=100.0, kv_rating=920.0)
        level, _ = _motor_completeness(props)
        assert level == "high"

    def test_high_when_power_w_and_motor_count(self):
        props = self._props(power_w=200.0, motor_count=4)
        level, _ = _motor_completeness(props)
        assert level == "high"

    def test_high_when_watts_and_motor_count(self):
        """watts (legacy key) also counts as power for high completeness."""
        props = self._props(watts=100.0, motor_count=4)
        level, _ = _motor_completeness(props)
        assert level == "high"

    def test_medium_when_only_kv(self):
        props = self._props(kv_rating=920.0)
        level, missing = _motor_completeness(props)
        assert level == "medium"
        assert any("motor" in m.lower() or "número" in m.lower() for m in missing)

    def test_medium_when_only_motor_count(self):
        props = self._props(motor_count=4)
        level, missing = _motor_completeness(props)
        assert level == "medium"

    def test_low_when_no_properties(self):
        level, missing = _motor_completeness({})
        assert level == "low"
        assert len(missing) > 0


# ── Commit 2: _set_motor_component ────────────────────────────────────────────

class TestSetMotorComponent:

    def test_writes_component_and_param_atomically(self, tmp_path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        spec = infer_component("4 motores 920kv 200W", registry=aerial_registry)
        updated = set_motor_component(ps, spec, power_w=200.0)

        assert "motors" in updated.design_properties.components
        assert updated.current_parameters.get("motor_power_w") == pytest.approx(200.0)

    def test_removes_motor_power_w_when_power_none(self, tmp_path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        # Pre-set motor_power_w
        params = {**(ps.current_parameters or {}), "motor_power_w": 150.0}
        ps = ps.model_copy(update={"current_parameters": params})

        spec = infer_component("motores brushless", registry=aerial_registry)
        updated = set_motor_component(ps, spec, power_w=None)

        assert "motor_power_w" not in (updated.current_parameters or {})

    def test_does_not_mutate_original_state(self, tmp_path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        # Snapshot BEFORE — proves Pydantic immutability
        original_params = dict(ps.current_parameters or {})
        original_components = set(ps.design_properties.components.keys())

        spec = infer_component("4 motores 200W", registry=aerial_registry)
        set_motor_component(ps, spec, power_w=200.0)

        # Original ProjectState must be unchanged after the call
        assert dict(ps.current_parameters or {}) == original_params
        assert set(ps.design_properties.components.keys()) == original_components
        assert "motors" not in ps.design_properties.components
        assert ps.current_parameters.get("motor_power_w") is None

    def test_preserves_motor_count_from_current_parameters_fallback(self, tmp_path):
        """FN-007: no existing components['motors'] entry, but current_parameters
        already has motor_count declared (e.g. from create_project's motors=4).
        A new spec without a motor_count property (like a catalog pick) must not
        drop the fleet size — the resolver's count-of-entries fallback would
        otherwise collapse it to 1."""
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)  # motors=4, no components["motors"] entry
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        assert "motors" not in ps.design_properties.components
        assert ps.current_parameters.get("motor_count") == 4

        spec = ComponentSpec(
            name="sunnysky_x2212_980",
            component_type="propulsion_active",
            suggested_key="motors",
            completeness="high",
            source="declared",
            properties={"power_w": PropertyValue(value=260.0, unit="W", source="declared")},
        )
        updated = set_motor_component(ps, spec, power_w=260.0)

        motor_count_prop = updated.design_properties.components["motors"].properties.get("motor_count")
        assert motor_count_prop is not None
        assert motor_count_prop.value == 4
        assert updated.current_parameters.get("motor_count") == 4

    def test_existing_component_motor_count_still_wins_over_fallback(self, tmp_path):
        """FN-007 must not regress Bug 78: an existing components['motors'].motor_count
        still takes precedence over the current_parameters fallback."""
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        existing_spec = ComponentSpec(
            name="prev_motor",
            component_type="propulsion_active",
            suggested_key="motors",
            completeness="high",
            source="declared",
            properties={"motor_count": PropertyValue(value=6, source="declared")},
        )
        dp = ps.design_properties.model_copy(update={"components": {"motors": existing_spec}})
        ps = ps.model_copy(update={"design_properties": dp})
        assert ps.current_parameters.get("motor_count") == 4  # differs from component (6)

        new_spec = ComponentSpec(
            name="new_motor",
            component_type="propulsion_active",
            suggested_key="motors",
            completeness="high",
            source="declared",
            properties={"power_w": PropertyValue(value=260.0, unit="W", source="declared")},
        )
        updated = set_motor_component(ps, new_spec, power_w=260.0)
        assert updated.design_properties.components["motors"].properties["motor_count"].value == 6


# ── End-to-end dispatch: _handle_component_description → motors ───────────────

def _setup_motors_component_pending(orchestrator, tmp_path):
    """Project with 'energy' block active, session expecting 'motors' component."""
    from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION

    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy"],
        "system_priority": ["energy"],
    })
    orchestrator.workspace_manager.save_state(
        project_state.model_copy(update={"design_properties": dp})
    )
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["motors"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


def test_handle_component_description_motors_saves_both_locations(tmp_path):
    """'4 motores 920kv 200W' with motors block → components['motors'] + motor_power_w written."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_motors_component_pending(orch, tmp_path)

    result = orch._handle_component_description("4 motores 920kv 200W", session)

    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "motors" in saved.design_properties.components
    assert saved.current_parameters.get("motor_power_w") is not None
    assert saved.current_parameters["motor_power_w"] == pytest.approx(200.0)


def test_handle_component_description_motors_no_cross_write_to_frame(tmp_path):
    """Motor description with structure block (expected_keys=['frame']) → motors NOT written."""
    from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orch, tmp_path)
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure"],
        "system_priority": ["structure"],
    })
    orch.workspace_manager.save_state(project_state.model_copy(update={"design_properties": dp}))
    session = orch.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["frame"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orch.state_manager.set_runtime_session(session)

    result = orch._handle_component_description("4 motores 920kv 200W", session)

    # Should redirect — motors don't belong to structure block
    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "motors" not in saved.design_properties.components
    assert saved.current_parameters.get("motor_power_w") is None


# ── Commit 4: get_motor_power_w getter ────────────────────────────────────────

class TestGetMotorPowerW:

    def _make_dp(self, completeness: str, power_w: float | None):
        from jarvis.schemas.action_schema import ComponentSpec
        from jarvis.schemas.state_schema import DesignProperties
        props = {}
        if power_w is not None:
            props["power_w"] = PropertyValue(value=power_w, unit="W")
        spec = ComponentSpec(
            component_type="propulsion",
            suggested_key="motors",
            completeness=completeness,
            properties=props,
            source="declared",
        )
        return DesignProperties(components={"motors": spec})

    def test_returns_power_w_when_high(self):
        dp = self._make_dp("high", 200.0)
        assert get_motor_power_w(dp) == pytest.approx(200.0)

    def test_returns_power_w_when_medium(self):
        dp = self._make_dp("medium", 150.0)
        assert get_motor_power_w(dp) == pytest.approx(150.0)

    def test_returns_none_when_low(self):
        dp = self._make_dp("low", 200.0)
        assert get_motor_power_w(dp) is None

    def test_returns_none_when_no_motors_component(self):
        from jarvis.schemas.state_schema import DesignProperties
        dp = DesignProperties()
        assert get_motor_power_w(dp) is None

    def test_returns_none_when_power_w_missing(self):
        dp = self._make_dp("high", None)
        assert get_motor_power_w(dp) is None


# ── Commit 5: backward compat — energy block progress ────────────────────────

class TestEnergyCompositeBackwardCompat:
    """Verifies that old param-only energy state is still handled gracefully."""

    def test_energy_not_started_with_only_params(self, tmp_path):
        """Params alone (no components) cannot fully complete energy block."""
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        from jarvis.schemas.state_schema import DesignProperties
        dp = DesignProperties(
            system_defined=True,
            system_blocks=["energy"],
            system_priority=["energy"],
        )
        params = {"battery_capacity_wh": 100.0, "motor_power_w": 50.0}
        # params_ok=True but no components → in_progress (not complete)
        status = JarvisOrchestrator._block_progress_status("energy", dp, params)
        assert status == "in_progress"

    def test_energy_not_started_with_no_data(self, tmp_path):
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        from jarvis.schemas.state_schema import DesignProperties
        dp = DesignProperties(
            system_defined=True,
            system_blocks=["energy"],
            system_priority=["energy"],
        )
        status = JarvisOrchestrator._block_progress_status("energy", dp, {})
        assert status == "not_started"

    def test_set_motor_component_drives_energy_in_progress(self, tmp_path):
        """After _set_motor_component (+ motor_power_w param), energy → in_progress."""
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orch, tmp_path)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        dp = ps.design_properties.model_copy(update={
            "system_defined": True,
            "system_blocks": ["energy"],
            "system_priority": ["energy"],
            "components": {},
        })
        # Start with battery_capacity_wh already set; motors component absent
        params = {k: v for k, v in (ps.current_parameters or {}).items()
                  if k not in ("motor_power_w",)}
        params["battery_capacity_wh"] = 100.0
        updated = ps.model_copy(update={"design_properties": dp, "current_parameters": params})

        status_before = JarvisOrchestrator._block_progress_status(
            "energy", updated.design_properties, updated.current_parameters or {}
        )
        assert status_before == "not_started"  # motor_power_w missing, no components

        spec = infer_component("4 motores 920kv 200W", registry=aerial_registry)
        updated2 = set_motor_component(updated, spec, power_w=200.0)

        status_after = JarvisOrchestrator._block_progress_status(
            "energy", updated2.design_properties, updated2.current_parameters or {}
        )
        # motor_power_w + battery_capacity_wh → params_ok=True
        # motors component set; battery component absent → components_ok=False
        # composite → in_progress
        assert status_after == "in_progress"
