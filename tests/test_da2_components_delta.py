"""DA2 + G1: components_delta in DesignExplorer.

Tests cover:
  - apply_components_delta (component writer orchestration)
  - COMPONENT_VARIATION_RULES produce viable candidates (battery, motors, frame)
  - explore() mixes and ranks params + component candidates
  - apply_exploration_result saves components + derived params
  - empty-delta guard
"""

import pytest

from jarvis.core.component_writers import apply_components_delta
from jarvis.core.design_explorer import (
    COMPONENT_VARIATION_RULES,
    DesignExplorer,
    _battery_spec,
    _build_label_components,
    _frame_spec,
    _motor_spec,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_drone_project(orchestrator):
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba DA2",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


# ── TestApplyComponentsDelta ──────────────────────────────────────────────────

class TestApplyComponentsDelta:

    def test_battery_writes_capacity_and_spec(self, tmp_path):
        """apply_components_delta with battery spec → battery_capacity_wh in params
        and components['battery'] present."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        updated = apply_components_delta(project_state, {"battery": _battery_spec(400.0)})

        assert updated.current_parameters.get("battery_capacity_wh") == pytest.approx(400.0)
        assert "battery" in updated.design_properties.components

    def test_motor_writes_power_and_spec(self, tmp_path):
        """apply_components_delta with motor spec → motor_power_w in params
        and components['motors'] present."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        updated = apply_components_delta(project_state, {"motors": _motor_spec(200.0)})

        assert updated.current_parameters.get("motor_power_w") == pytest.approx(200.0)
        assert "motors" in updated.design_properties.components

    def test_apply_order_battery_then_motors(self, tmp_path):
        """Battery + motors in same delta → both written without collision."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        updated = apply_components_delta(
            project_state,
            {"motors": _motor_spec(250.0), "battery": _battery_spec(600.0)},
        )

        assert updated.current_parameters.get("battery_capacity_wh") == pytest.approx(600.0)
        assert updated.current_parameters.get("motor_power_w") == pytest.approx(250.0)

    def test_missing_property_does_not_crash(self, tmp_path):
        """Spec without battery_capacity_wh property → no exception, component still written."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        bare_spec = ComponentSpec(
            component_type="energy_storage",
            suggested_key="battery",
            completeness="low",
            source="declared",
        )
        updated = apply_components_delta(project_state, {"battery": bare_spec})

        assert "battery" in updated.design_properties.components
        # No crash — battery_capacity_wh removed (None path in set_battery_component)
        assert updated.current_parameters.get("battery_capacity_wh") is None

    def test_empty_delta_normalizes_baseline(self, tmp_path):
        """apply_components_delta({}) re-derives params from existing components."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        # Pre-set a battery component
        state_with_battery = apply_components_delta(
            project_state, {"battery": _battery_spec(300.0)}
        )
        # Manually corrupt the param
        corrupted = state_with_battery.model_copy(update={
            "current_parameters": {
                **state_with_battery.current_parameters,
                "battery_capacity_wh": 999.0,  # stale value
            }
        })

        normalized = apply_components_delta(corrupted, {})

        # Re-derived from component — overwritten back to 300.0
        assert normalized.current_parameters.get("battery_capacity_wh") == pytest.approx(300.0)


# ── TestComponentGrid ─────────────────────────────────────────────────────────

class TestComponentGrid:

    def test_battery_grid_produces_candidates(self, tmp_path):
        """explore('mejorar_autonomia') with battery in COMPONENT_VARIATION_RULES → at least
        one candidate with non-empty components_delta."""
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)
        # Ensure energy params are present so scoring is meaningful
        params = dict(project_state.current_parameters or {})
        params["battery_capacity_wh"] = 200.0
        params["motor_power_w"] = 100.0
        project_state = project_state.model_copy(update={"current_parameters": params})

        explorer = DesignExplorer(CalculationEngine(), FeasibilitySimulator())
        result = explorer.explore(project_state, "mejorar_autonomia")

        component_candidates = [c for c in result.candidates if c.components_delta]
        expected = sum(len(r["values"]) for r in COMPONENT_VARIATION_RULES.get("mejorar_autonomia", []))
        assert len(component_candidates) == expected

    def test_component_candidate_score_differs_from_baseline(self, tmp_path):
        """Battery 800Wh candidate score > battery 200Wh baseline for autonomy goal."""
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params["battery_capacity_wh"] = 200.0
        params["motor_power_w"] = 100.0
        project_state = project_state.model_copy(update={"current_parameters": params})

        explorer = DesignExplorer(CalculationEngine(), FeasibilitySimulator())
        result = explorer.explore(project_state, "mejorar_autonomia")

        battery_candidates = [
            c for c in result.candidates
            if c.components_delta and "battery" in c.components_delta
        ]
        assert battery_candidates, "Expected at least one battery component candidate"
        best_battery = max(battery_candidates, key=lambda c: c.score)
        assert best_battery.score > result.baseline_score

    def test_params_and_component_candidates_ranked_together(self, tmp_path):
        """viable list may contain both params-driven and component-driven candidates."""
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params["battery_capacity_wh"] = 200.0
        params["motor_power_w"] = 100.0
        project_state = project_state.model_copy(update={"current_parameters": params})

        explorer = DesignExplorer(CalculationEngine(), FeasibilitySimulator())
        result = explorer.explore(project_state, "mejorar_autonomia")

        has_params = any(c.params_delta for c in result.candidates)
        has_components = any(c.components_delta for c in result.candidates)
        assert has_params, "Expected params-driven candidates"
        assert has_components, "Expected component-driven candidates"


# ── TestApplyExplorationResultDA2 ─────────────────────────────────────────────

class TestApplyExplorationResultDA2:

    def test_apply_component_candidate_saves_component_and_params(self, tmp_path):
        """apply_exploration_result with components_delta candidate → component
        saved in design_properties AND battery_capacity_wh in current_parameters."""
        from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params["battery_capacity_wh"] = 200.0
        params["motor_power_w"] = 100.0
        project_state = project_state.model_copy(update={"current_parameters": params})
        orc.workspace_manager.save_state(project_state)

        spec = _battery_spec(500.0)
        engine = CalculationEngine()
        sim_eval = FeasibilitySimulator()

        from jarvis.core.component_writers import apply_components_delta
        temp = apply_components_delta(project_state, {"battery": spec})
        calc = engine.build(dict(temp.current_parameters or {}))
        sim = sim_eval.evaluate(calc)

        candidate = ExplorationCandidate(
            params_delta={},
            components_delta={"battery": spec},
            calculations=calc,
            simulation=sim,
            score=1.0,
            label="batería: battery_capacity_wh=500.0",
            improvement=1.0,
        )
        exploration = ExplorationResult(
            goal_key="mejorar_autonomia",
            goal_label="maximizar autonomía",
            baseline_score=0.0,
            baseline_calculations=calc,
            baseline_simulation=sim,
            candidates=[candidate],
            viable=[candidate],
        )
        session = orc.state_manager.runtime_state.session.model_copy(
            update={"last_exploration_result": exploration}
        )
        orc.state_manager.set_runtime_session(session)

        result = orc._handle_apply_exploration()

        assert result["status"] == "ok"
        saved = orc.state_manager.load_active_project(orc.workspace_manager)
        assert saved.current_parameters.get("battery_capacity_wh") == pytest.approx(500.0)
        assert "battery" in saved.design_properties.components


# ── Label and misc ─────────────────────────────────────────────────────────────

def test_build_label_components_includes_property_values():
    """_build_label_components produces a readable label with property values."""
    spec = _battery_spec(400.0)
    label = _build_label_components({"battery": spec})
    assert "battery" in label
    assert "400" in label


def test_empty_delta_skipped_in_explore(tmp_path):
    """COMPONENT_VARIATION_RULES entries always have non-empty values lists."""
    for goal, rules in COMPONENT_VARIATION_RULES.items():
        for rule in rules:
            assert rule.get("values"), f"Empty values in COMPONENT_VARIATION_RULES['{goal}']"


# ── TestFrameComponentGrid ─────────────────────────────────────────────────────────

class TestFrameComponentGrid:
    """G1: frame variations in COMPONENT_VARIATION_RULES (reducir_masa, mejorar_estabilidad)."""

    def test_frame_grid_produces_candidates_reducir_masa(self, tmp_path):
        """explore('reducir_masa') → frame component candidates matching rule count."""
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        explorer = DesignExplorer(CalculationEngine(), FeasibilitySimulator())
        result = explorer.explore(project_state, "reducir_masa")

        frame_candidates = [c for c in result.candidates if "frame" in (c.components_delta or {})]
        expected = sum(
            len(r["values"])
            for r in COMPONENT_VARIATION_RULES.get("reducir_masa", [])
            if r["component_key"] == "frame"
        )
        assert len(frame_candidates) == expected

    def test_frame_candidate_score_improves_reducir_masa(self, tmp_path):
        """Lightest frame candidate score > baseline when baseline has heavier frame."""
        from jarvis.core.calculation_engine import CalculationEngine
        from jarvis.simulation.simulator import FeasibilitySimulator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params["structure_mass_override_kg"] = 0.6
        project_state = project_state.model_copy(update={"current_parameters": params})

        explorer = DesignExplorer(CalculationEngine(), FeasibilitySimulator())
        result = explorer.explore(project_state, "reducir_masa")

        frame_candidates = [c for c in result.candidates if "frame" in (c.components_delta or {})]
        assert frame_candidates, "Expected frame component candidates"
        lightest = min(
            frame_candidates,
            key=lambda c: c.components_delta["frame"].properties["mass_kg"].value,
        )
        assert lightest.score > result.baseline_score

    def test_frame_spec_applies_via_apply_components_delta(self, tmp_path):
        """_frame_spec applies correctly: structure_mass_override_kg written to params."""
        orc = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orc)
        project_state = orc.state_manager.load_active_project(orc.workspace_manager)

        updated = apply_components_delta(project_state, {"frame": _frame_spec(0.280)})

        assert updated.current_parameters.get("structure_mass_override_kg") == pytest.approx(0.280)
        assert "frame" in updated.design_properties.components
