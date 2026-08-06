"""Tests para Design Space Explorer (DSE).

Cubre:
  - _apply_delta: factor, delta, value, param ausente, clamp motors ≥ 1, no mutación base
  - _score_candidate: los 4 goals + edge cases
  - _build_label: legibilidad de etiquetas
  - EXPLORATION_GRIDS: integridad estructural
  - DesignExplorer.explore(): integración real con CalculationEngine + FeasibilitySimulator
    - baseline computed, viable filtrado, ranking, no-mutación, goal desconocido
  - DSE v1.1: apply_exploration_result
    - IntentResolver.APPLY_PATTERNS, session state, _handle_apply_exploration edge cases
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.design_explorer import (
    EXPLORATION_GRIDS,
    GOAL_LABELS,
    MAX_VIABLE,
    DesignExplorer,
    ExplorationCandidate,
    ExplorationResult,
    _apply_delta,
    _build_label,
    _score_candidate,
)
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult
from jarvis.simulation.simulator import FeasibilitySimulator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_sim(
    *,
    can_fly: bool = True,
    safety_margin_ratio: float = 1.5,
    autonomy_min: float | None = 30.0,
    quality: str = "good",
) -> SimulationResult:
    thrust_to_weight = safety_margin_ratio
    return SimulationResult(
        can_fly=can_fly,
        status="pass" if can_fly else "fail",
        safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=thrust_to_weight,
        autonomy_min=autonomy_min,
        quality=quality,
        warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0,
            required_thrust_n=40.0,
            weight_n=34.3,
            per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )


def _make_calc(
    *,
    total_mass_kg: float = 3.5,
    payload_kg: float = 2.0,
    available_total_thrust_n: float | None = 60.0,
    autonomy_min: float | None = 30.0,
) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="drone",
        payload_kg=payload_kg,
        structure_mass_kg=1.5,
        total_mass_kg=total_mass_kg,
        weight_n=total_mass_kg * 9.81,
        required_thrust_n=total_mass_kg * 9.81 * 1.2,
        motors=4,
        thrust_per_motor_required_n=(total_mass_kg * 9.81 * 1.2) / 4,
        available_total_thrust_n=available_total_thrust_n,
        autonomy_min=autonomy_min,
        tool_results=[],
    )


def _make_project_state(params: dict) -> SimpleNamespace:
    return SimpleNamespace(
        project_id="test-project",
        workspace_path="/tmp/test",
        current_parameters=params,
    )


# Standard drone params that produce a valid calculation
DRONE_PARAMS = {
    "vehicle_type": "drone",
    "payload_kg": 2.0,
    "motor_count": 4,
    "per_motor_max_thrust_n": 15.0,
    "battery_capacity_wh": 200.0,
    "motor_power_w": 250.0,
    "structure_mass_factor": 1.2,
    "safety_factor": 1.2,
}


# ── Tests: _apply_delta ───────────────────────────────────────────────────────

class TestApplyDelta:
    def test_factor_multiplies_base_value(self):
        base = {"battery_capacity_wh": 200.0}
        result = _apply_delta(base, {"battery_capacity_wh_factor": 2.0})
        assert result is not None
        assert result["battery_capacity_wh"] == pytest.approx(400.0)

    def test_delta_adds_to_int_param(self):
        base = {"motor_count": 4}
        result = _apply_delta(base, {"motor_count_delta": 2})
        assert result is not None
        assert result["motor_count"] == 6

    def test_delta_subtracts_correctly(self):
        base = {"motor_count": 4}
        result = _apply_delta(base, {"motor_count_delta": -1})
        assert result is not None
        assert result["motor_count"] == 3

    def test_value_sets_absolute(self):
        base = {"structure_mass_factor": 1.2}
        result = _apply_delta(base, {"structure_mass_factor_value": 0.5})
        assert result is not None
        assert result["structure_mass_factor"] == 0.5

    def test_missing_factor_param_returns_none(self):
        base = {"payload_kg": 2.0}
        result = _apply_delta(base, {"battery_capacity_wh_factor": 2.0})
        assert result is None

    def test_missing_delta_param_returns_none(self):
        base = {"payload_kg": 2.0}
        result = _apply_delta(base, {"motor_count_delta": 2})
        assert result is None

    def test_motors_clamped_to_min_1(self):
        base = {"motor_count": 1}
        result = _apply_delta(base, {"motor_count_delta": -5})
        assert result is not None
        assert result["motor_count"] == 1

    def test_no_mutation_of_base_params(self):
        base = {"battery_capacity_wh": 200.0}
        original_value = base["battery_capacity_wh"]
        _apply_delta(base, {"battery_capacity_wh_factor": 2.0})
        assert base["battery_capacity_wh"] == original_value

    def test_multiple_deltas_applied_together(self):
        base = {"battery_capacity_wh": 200.0, "motor_count": 4}
        result = _apply_delta(base, {"battery_capacity_wh_factor": 1.5, "motor_count_delta": -1})
        assert result is not None
        assert result["battery_capacity_wh"] == pytest.approx(300.0)
        assert result["motor_count"] == 3

    def test_partial_missing_returns_none(self):
        """Si UN param del delta falta, todo el candidato se omite."""
        base = {"battery_capacity_wh": 200.0}  # no motor_count
        result = _apply_delta(base, {"battery_capacity_wh_factor": 2.0, "motor_count_delta": -1})
        assert result is None


# ── Tests: _score_candidate ───────────────────────────────────────────────────

class TestScoreCandidate:
    def test_mejorar_autonomia_uses_autonomy_min(self):
        sim = _make_sim(autonomy_min=45.0)
        calc = _make_calc()
        assert _score_candidate(sim, calc, "mejorar_autonomia") == pytest.approx(45.0)

    def test_mejorar_autonomia_none_autonomy_returns_zero(self):
        sim = _make_sim(autonomy_min=None)
        calc = _make_calc()
        assert _score_candidate(sim, calc, "mejorar_autonomia") == 0.0

    def test_aumentar_payload_multiplies_margin_by_payload(self):
        sim = _make_sim(safety_margin_ratio=1.5)
        calc = _make_calc(payload_kg=3.0)
        assert _score_candidate(sim, calc, "aumentar_payload") == pytest.approx(4.5)

    def test_reducir_masa_negates_total_mass(self):
        sim = _make_sim()
        calc = _make_calc(total_mass_kg=4.0)
        assert _score_candidate(sim, calc, "reducir_masa") == pytest.approx(-4.0)

    def test_reducir_masa_lighter_scores_higher(self):
        sim = _make_sim()
        light = _make_calc(total_mass_kg=2.0)
        heavy = _make_calc(total_mass_kg=5.0)
        assert _score_candidate(sim, light, "reducir_masa") > _score_candidate(sim, heavy, "reducir_masa")

    def test_mejorar_estabilidad_uses_safety_margin(self):
        sim = _make_sim(safety_margin_ratio=1.8)
        calc = _make_calc()
        assert _score_candidate(sim, calc, "mejorar_estabilidad") == pytest.approx(1.8)

    def test_unknown_goal_returns_zero(self):
        sim = _make_sim()
        calc = _make_calc()
        assert _score_candidate(sim, calc, "unknown_goal") == 0.0


# ── Tests: _build_label ───────────────────────────────────────────────────────

class TestBuildLabel:
    def test_factor_shows_readable_label(self):
        delta = {"battery_capacity_wh_factor": 2.0}
        applied = {"battery_capacity_wh": 400.0}
        label = _build_label(delta, applied)
        assert "batería" in label
        assert "400" in label

    def test_delta_shows_readable_label(self):
        delta = {"motor_count_delta": 2}
        applied = {"motor_count": 6}
        label = _build_label(delta, applied)
        assert "motores" in label
        assert "6" in label

    def test_value_shows_absolute(self):
        delta = {"structure_mass_factor_value": 0.5}
        applied = {"structure_mass_factor": 0.5}
        label = _build_label(delta, applied)
        assert "0.5" in label

    def test_empty_delta_returns_str(self):
        """Delta vacío no debe lanzar error."""
        label = _build_label({}, {})
        assert isinstance(label, str)


# ── Tests: EXPLORATION_GRIDS integridad ───────────────────────────────────────

class TestExplorationGridsStructure:
    def test_all_four_goals_have_grids(self):
        for goal in ["mejorar_autonomia", "aumentar_payload", "reducir_masa", "mejorar_estabilidad"]:
            assert goal in EXPLORATION_GRIDS
            assert len(EXPLORATION_GRIDS[goal]) > 0

    def test_all_grid_entries_are_dicts(self):
        for goal, entries in EXPLORATION_GRIDS.items():
            for entry in entries:
                assert isinstance(entry, dict), f"grid entry for {goal} is not a dict"

    def test_all_grid_keys_use_known_conventions(self):
        for goal, entries in EXPLORATION_GRIDS.items():
            for entry in entries:
                for key in entry:
                    assert key.endswith(("_factor", "_delta", "_value")), (
                        f"Unknown delta key '{key}' in grid for '{goal}'"
                    )

    def test_goal_labels_cover_all_goals(self):
        for goal in EXPLORATION_GRIDS:
            assert goal in GOAL_LABELS


# ── Tests: DesignExplorer.explore() ───────────────────────────────────────────

class TestDesignExplorerExplore:
    """Integración real: CalculationEngine + FeasibilitySimulator."""

    @pytest.fixture
    def explorer(self):
        return DesignExplorer(
            calculation_engine=CalculationEngine(),
            simulator=FeasibilitySimulator(),
        )

    @pytest.fixture
    def project_state(self):
        return _make_project_state(dict(DRONE_PARAMS))

    def test_returns_exploration_result_instance(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert isinstance(result, ExplorationResult)

    def test_goal_key_and_label_set_correctly(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert result.goal_key == "mejorar_autonomia"
        assert result.goal_label == GOAL_LABELS["mejorar_autonomia"]

    def test_baseline_computed(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert isinstance(result.baseline_calculations, CalculationBundle)
        assert isinstance(result.baseline_simulation, SimulationResult)

    def test_candidates_list_not_empty(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert len(result.candidates) > 0

    def test_viable_only_contains_can_fly_true(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        for c in result.viable:
            assert c.simulation.can_fly is True

    def test_viable_sorted_by_score_descending(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        scores = [c.score for c in result.viable]
        assert scores == sorted(scores, reverse=True)

    def test_viable_max_5(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert len(result.viable) <= MAX_VIABLE

    def test_no_mutation_of_project_state_params(self, explorer):
        original_params = dict(DRONE_PARAMS)
        project_state = _make_project_state(dict(DRONE_PARAMS))
        explorer.explore(project_state, "mejorar_autonomia")
        assert project_state.current_parameters == original_params

    def test_unknown_goal_returns_empty_viable(self, explorer, project_state):
        result = explorer.explore(project_state, "goal_inventado")
        assert result.viable == []
        assert result.candidates == []

    def test_candidates_skip_when_param_absent(self, explorer):
        """Candidatos que requieren battery_capacity_wh se omiten si no está en params."""
        params_without_battery = {
            k: v for k, v in DRONE_PARAMS.items()
            if k != "battery_capacity_wh"
        }
        project_state = _make_project_state(params_without_battery)
        result = explorer.explore(project_state, "mejorar_autonomia")
        # Algunos candidatos de mejorar_autonomia requieren battery_capacity_wh_factor
        # → esos se omiten. Los que solo usan motor_count_delta sí deben aparecer.
        motor_candidates = [
            c for c in result.candidates
            if "motor_count" in c.params_delta or "motor_count_delta" in str(c.params_delta)
        ]
        # Al menos los candidatos motor_count_delta=-1 y motor_count_delta=-2 deben sobrevivir
        assert len(result.candidates) < len(EXPLORATION_GRIDS["mejorar_autonomia"])

    def test_explore_all_four_goals_smoke(self, explorer, project_state):
        """Smoke test: los 4 goals se ejecutan sin excepción."""
        for goal in EXPLORATION_GRIDS:
            result = explorer.explore(project_state, goal)
            assert isinstance(result, ExplorationResult)
            assert result.goal_key == goal

    def test_improvement_is_score_minus_baseline(self, explorer, project_state):
        result = explorer.explore(project_state, "mejorar_autonomia")
        for c in result.candidates:
            expected = round(c.score - result.baseline_score, 4)
            assert c.improvement == pytest.approx(expected, abs=1e-3)

    def test_candidates_have_params_delta(self, explorer, project_state):
        result = explorer.explore(project_state, "aumentar_payload")
        for c in result.candidates:
            assert isinstance(c.params_delta, dict)
            assert len(c.params_delta) > 0

    def test_label_is_non_empty_string(self, explorer, project_state):
        result = explorer.explore(project_state, "reducir_masa")
        for c in result.candidates:
            assert isinstance(c.label, str)
            assert c.label.strip() != ""

    def test_engine_exception_candidate_skipped(self):
        """Si el engine lanza excepción para un candidato, se omite sin crash."""
        engine = MagicMock(spec=CalculationEngine)
        simulator = MagicMock(spec=FeasibilitySimulator)

        call_count = 0

        def engine_side_effect(params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_calc()  # baseline ok
            raise ValueError("parámetro inválido simulado")

        engine.build.side_effect = engine_side_effect
        simulator.evaluate.return_value = _make_sim(can_fly=True, autonomy_min=40.0)

        explorer = DesignExplorer(calculation_engine=engine, simulator=simulator)
        project_state = _make_project_state(dict(DRONE_PARAMS))

        # No debe lanzar excepción
        result = explorer.explore(project_state, "mejorar_autonomia")
        assert isinstance(result, ExplorationResult)


# ── Tests: IntentResolver integración ─────────────────────────────────────────

class TestIntentResolverExploreIntegration:
    def test_resolves_explore_design_space_intent(self):
        from jarvis.core.intent_resolver import IntentResolver
        resolver = IntentResolver()
        assert resolver.resolve_intent("encuentra la mejor configuración para mi dron") == "explore_design_space"

    def test_resolves_explore_espacio_diseno(self):
        from jarvis.core.intent_resolver import IntentResolver
        resolver = IntentResolver()
        assert resolver.resolve_intent("explora el espacio de diseño") == "explore_design_space"

    def test_resolve_explore_goal_autonomia(self):
        from jarvis.core.intent_resolver import IntentResolver
        resolver = IntentResolver()
        goal = resolver.resolve_explore_goal("optimiza para mayor autonomia")
        assert goal == "mejorar_autonomia"

    def test_resolve_explore_goal_payload(self):
        from jarvis.core.intent_resolver import IntentResolver
        resolver = IntentResolver()
        goal = resolver.resolve_explore_goal("busca la mejor opción para más carga util")
        assert goal == "aumentar_payload"

    def test_resolve_explore_goal_none_when_no_goal(self):
        from jarvis.core.intent_resolver import IntentResolver
        resolver = IntentResolver()
        goal = resolver.resolve_explore_goal("explora el espacio de diseño")
        assert goal is None


# ── Tests: APPLY_PATTERNS (DSE v1.1) ──────────────────────────────────────────

class TestApplyPatterns:
    @pytest.fixture
    def resolver(self):
        from jarvis.core.intent_resolver import IntentResolver
        return IntentResolver()

    def test_aplica_simple(self, resolver):
        assert resolver.resolve_intent("aplica") == "apply_exploration_result"

    def test_aplica_la_mejor(self, resolver):
        assert resolver.resolve_intent("aplica la mejor") == "apply_exploration_result"

    def test_usa_esta_configuracion(self, resolver):
        assert resolver.resolve_intent("usa esta configuración") == "apply_exploration_result"

    def test_quedatee_con_esa(self, resolver):
        assert resolver.resolve_intent("quédate con esa") == "apply_exploration_result"

    def test_guarda_esta_configuracion(self, resolver):
        assert resolver.resolve_intent("guarda esta configuración") == "apply_exploration_result"

    def test_aplica_el_resultado(self, resolver):
        assert resolver.resolve_intent("aplica el resultado") == "apply_exploration_result"

    def test_apply_does_not_match_explore(self, resolver):
        """'aplica' solo no debe caer en explore_design_space."""
        intent = resolver.resolve_intent("aplica")
        assert intent != "explore_design_space"

    def test_explore_is_not_apply(self, resolver):
        """'optimiza para autonomia' no es apply."""
        assert resolver.resolve_intent("optimiza para autonomia") != "apply_exploration_result"


# ── Tests: _handle_apply_exploration edge cases ───────────────────────────────

class TestHandleApplyExploration:
    """Tests de _handle_apply_exploration usando mocks.

    No usan el orchestrator completo — solo el método a través de un stub mínimo.
    """

    def _make_project_state_mock(self, params=None):
        """Crea un mock de ProjectState compatible con model_copy."""
        ps = MagicMock()
        ps.project_id = "p1"
        ps.workspace_path = "/tmp/p1"
        ps.current_parameters = params or dict(DRONE_PARAMS)
        ps.parsed_constraints = {}
        ps.active_iteration = 1
        ps.latest_results = {}
        ps.model_copy.return_value = ps  # model_copy returns itself (mock)
        return ps

    def _make_orchestrator_stub(self, *, exploration=None, project_state=None):
        from jarvis.core.orchestrator import JarvisOrchestrator
        from unittest.mock import MagicMock, PropertyMock
        from types import SimpleNamespace

        # Session con last_exploration_result configurable
        session = MagicMock()
        session.last_exploration_result = exploration

        state_manager = MagicMock()
        state_manager.runtime_state.session = session

        if project_state is not None:
            state_manager.load_active_project.return_value = project_state
        else:
            state_manager.load_active_project.side_effect = FileNotFoundError

        workspace_manager = MagicMock()
        calculation_engine = CalculationEngine()
        simulator = FeasibilitySimulator()

        # Crear orchestrator sin __init__ completo
        orch = object.__new__(JarvisOrchestrator)
        orch.state_manager = state_manager
        orch.workspace_manager = workspace_manager
        orch.calculation_engine = calculation_engine
        orch.simulator = simulator

        return orch

    def _make_exploration(self, *, viable=True, best_score=1.5, baseline_score=1.2):
        """Crea un ExplorationResult mínimo con viable[0] configurado."""
        from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult

        if viable:
            best = ExplorationCandidate(
                params_delta={"battery_capacity_wh_factor": 2.0},
                calculations=_make_calc(autonomy_min=60.0),
                simulation=_make_sim(can_fly=True, safety_margin_ratio=1.5, autonomy_min=60.0),
                score=best_score,
                label="batería (Wh)=400.0",
                improvement=best_score - baseline_score,
            )
            viable_list = [best]
        else:
            viable_list = []

        return ExplorationResult(
            goal_key="mejorar_autonomia",
            goal_label="maximizar autonomía",
            baseline_score=baseline_score,
            baseline_calculations=_make_calc(),
            baseline_simulation=_make_sim(),
            candidates=[],
            viable=viable_list,
        )

    def test_no_exploration_returns_error(self):
        orch = self._make_orchestrator_stub(exploration=None)
        result = orch._handle_apply_exploration()
        assert result["status"] == "error"
        assert "No hay resultados" in result["message"]

    def test_no_viable_returns_error(self):
        exploration = self._make_exploration(viable=False)
        orch = self._make_orchestrator_stub(exploration=exploration)
        result = orch._handle_apply_exploration()
        assert result["status"] == "error"
        assert "viable" in result["message"].lower()

    def test_no_active_project_returns_error(self):
        exploration = self._make_exploration()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=None)
        result = orch._handle_apply_exploration()
        assert result["status"] == "error"
        assert "proyecto activo" in result["message"].lower()

    def test_successful_apply_returns_ok(self):
        exploration = self._make_exploration()
        project_state = self._make_project_state_mock()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)
        orch.state_manager.record_action.return_value = MagicMock()
        orch.workspace_manager.save_state.return_value = None

        result = orch._handle_apply_exploration()
        assert result["status"] == "ok"
        assert result["action"] == "apply_exploration_result"
        assert result["goal_key"] == "mejorar_autonomia"

    def test_successful_apply_calls_save_state(self):
        exploration = self._make_exploration()
        project_state = self._make_project_state_mock()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)
        orch.state_manager.record_action.return_value = MagicMock()

        orch._handle_apply_exploration()

        orch.workspace_manager.save_state.assert_called_once()

    def test_successful_apply_records_action(self):
        exploration = self._make_exploration()
        project_state = self._make_project_state_mock()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)
        orch.state_manager.record_action.return_value = MagicMock()
        orch.workspace_manager.save_state.return_value = None

        orch._handle_apply_exploration()

        orch.state_manager.record_action.assert_called_once()
        call_kwargs = orch.state_manager.record_action.call_args
        latest = call_kwargs.kwargs.get("latest_results") or call_kwargs[1].get("latest_results", {})
        assert latest.get("mutation", {}).get("mode") == "dse_apply"

    def test_no_improvement_warning_in_message(self):
        """Cuando best.score <= baseline, el mensaje debe incluir aviso."""
        exploration = self._make_exploration(best_score=1.2, baseline_score=1.5)
        project_state = self._make_project_state_mock()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)
        orch.state_manager.record_action.return_value = MagicMock()
        orch.workspace_manager.save_state.return_value = None

        result = orch._handle_apply_exploration()

        assert result["status"] == "ok"
        assert "no mejora la línea base" in result["message"]

    def test_apply_delta_none_returns_error(self):
        """Si best.params_delta referencia un param ausente, devuelve error amigable."""
        exploration = self._make_exploration()
        exploration.viable[0].params_delta["nonexistent_param_factor"] = 2.0

        params = {k: v for k, v in DRONE_PARAMS.items() if k != "nonexistent_param"}
        project_state = self._make_project_state_mock(params=params)
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)

        result = orch._handle_apply_exploration()
        assert result["status"] == "error"
        assert "manualmente" in result["message"].lower()

    def test_message_contains_autonomy_and_margin(self):
        exploration = self._make_exploration()
        project_state = self._make_project_state_mock()
        orch = self._make_orchestrator_stub(exploration=exploration, project_state=project_state)
        orch.state_manager.record_action.return_value = MagicMock()
        orch.workspace_manager.save_state.return_value = None

        result = orch._handle_apply_exploration()

        assert "autonomía" in result["message"]
        assert "margen" in result["message"]
