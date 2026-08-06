"""Tests para Fase N — validación propeller-only path + bugs 76-79.

Bug 76: vehicle type con descripción larga → arquitectura base correcta
Bug 77: escape suave en DEFINE_MISSING_PARAMETERS
Bug 78: doble declaración de motor preserva motor_count
Bug 79: DSE apply emite warning de restricción
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Bug 76 — vehicle type normalization
# ─────────────────────────────────────────────────────────────────────────────

class TestVehicleTypeNormalization:
    """CreateProjectInteractiveSession._normalize_vehicle_type debe mapear
    cualquier texto que contenga una palabra de dominio canónica a su alias."""

    def _make_session(self):
        from jarvis.core.interactive_session import CreateProjectInteractiveSession
        return CreateProjectInteractiveSession()

    def test_exact_canonical_unchanged(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("dron") == "dron"

    def test_drone_alias_maps_to_dron(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("drone") == "dron"

    def test_description_with_dron_word_maps_to_dron(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("dron de inspección de infraestructuras") == "dron"

    def test_description_with_rover_word_maps_to_rover(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("rover de exploración marciana") == "rover"

    def test_description_with_robot_word_maps_to_robot(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("robot terrestre autónomo") == "robot"

    def test_uav_maps_correctly(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("uav de larga distancia") == "uav"

    def test_unknown_type_returned_lowercased(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("submarino") == "submarino"

    def test_mixed_case_handled(self):
        s = self._make_session()
        assert s._normalize_vehicle_type("DRON de inspeccion") == "dron"

    def test_apply_answer_step0_uses_normalization(self):
        """_apply_answer step 0 must produce normalized vehicle_type in draft."""
        from jarvis.core.interactive_session import CreateProjectInteractiveSession
        from jarvis.schemas.action_schema import ProjectDraft
        s = CreateProjectInteractiveSession()
        draft = ProjectDraft.model_validate({})
        result, next_step = s._apply_answer(draft, step=0, user_input="dron de inspeccion de puentes")
        assert result.vehicle_type == "dron"
        assert next_step == 1


# ─────────────────────────────────────────────────────────────────────────────
# Bug 77 — escape suave en DEFINE_MISSING_PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

class TestDefineParamSkip:
    """ParamDefinitionSession.answer debe omitir el param actual
    cuando el usuario escribe una frase de deferimiento."""

    def _make_session_with_pending(self, params: list[str]):
        """Helper: crea un estado de sesión con los params dados como pendientes."""
        from jarvis.schemas.action_schema import InteractiveSessionState, OrchestratorMode
        return InteractiveSessionState.model_validate({
            "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
            "pending_param_definitions": params,
            "collected_params": {},
        })

    def _make_param_session(self):
        from unittest.mock import MagicMock
        from jarvis.core.param_definition_session import ParamDefinitionSession
        workspace_manager = MagicMock()
        state_manager = MagicMock()
        calculation_engine = MagicMock()
        simulator = MagicMock()
        session = ParamDefinitionSession(
            workspace_manager=workspace_manager,
            state_manager=state_manager,
            calculation_engine=calculation_engine,
            simulator=simulator,
        )
        return session, state_manager

    def test_skip_phrase_advances_to_next_param(self):
        """'no sé' con dos params pendientes → omite el primero, pregunta el segundo."""
        session, state_manager = self._make_param_session()
        mock_session = self._make_session_with_pending(
            ["per_motor_max_thrust_n", "motor_count"]
        )
        state_manager.get_runtime_session.return_value = mock_session

        result = session.answer("no sé")

        assert result["status"] == "interactive"
        assert result["action"] == "define_missing_params"
        assert "omitido" in result.get("message", "").lower()
        # Session updated with first param removed
        updated_session = state_manager.set_runtime_session.call_args[0][0]
        assert "per_motor_max_thrust_n" not in updated_session.pending_param_definitions
        assert "motor_count" in updated_session.pending_param_definitions

    def test_skip_phrase_no_se_variant(self):
        """'no se' (sin tilde) también debe omitir."""
        session, state_manager = self._make_param_session()
        mock_session = self._make_session_with_pending(["per_motor_max_thrust_n"])
        mock_session = mock_session.model_copy(update={"collected_params": {}})
        state_manager.get_runtime_session.return_value = mock_session
        # apply_and_recalculate will be called with empty dict — mock it
        session.apply_and_recalculate = lambda p: {"status": "ok", "action": "define_missing_params", "message": "ok"}

        result = session.answer("no se")
        # With no remaining params, apply_and_recalculate is called
        assert result["status"] == "ok"

    def test_skip_phrase_all_skipped_calls_apply(self):
        """Cuando el único param se omite, apply_and_recalculate se llama."""
        session, state_manager = self._make_param_session()
        mock_session = self._make_session_with_pending(["per_motor_max_thrust_n"])
        state_manager.get_runtime_session.return_value = mock_session

        apply_called_with = []

        def fake_apply(params):
            apply_called_with.append(params)
            return {"status": "ok", "action": "define_missing_params", "message": "aplicado"}

        session.apply_and_recalculate = fake_apply

        result = session.answer("no sé")

        assert result["status"] == "ok"
        assert len(apply_called_with) == 1
        # Called with whatever was collected (empty in this case)
        assert apply_called_with[0] == {}

    def test_numeric_input_not_affected(self):
        """Un input numérico válido no debe ser tratado como skip."""
        session, state_manager = self._make_param_session()
        mock_session = self._make_session_with_pending(["per_motor_max_thrust_n"])
        state_manager.get_runtime_session.return_value = mock_session

        # '15' is a valid float — should NOT call apply with empty dict
        # Should trigger the normal numeric path (keyword match or positional)
        # We just verify it does NOT set an "omitido" message
        # apply_and_recalculate is mocked
        session.apply_and_recalculate = lambda p: {"status": "ok", "action": "define_missing_params", "message": "params applied", "params_applied": p}

        result = session.answer("15")

        assert result.get("message", "") != "Parámetro 'per_motor_max_thrust_n' omitido — puedes definirlo después."


# ─────────────────────────────────────────────────────────────────────────────
# Bug 78 — motor merge preserva motor_count
# ─────────────────────────────────────────────────────────────────────────────

class TestMotorComponentMerge:
    """set_motor_component debe preservar motor_count de la declaración anterior
    cuando el nuevo spec no lo incluye."""

    def _make_project_state_with_motors(self, motor_count: int):
        """Helper: crea un ProjectState con un componente motors que tiene motor_count."""
        from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
        from jarvis.schemas.state_schema import ProjectState, DesignProperties
        count_prop = PropertyValue(value=motor_count, unit=None, confidence=0.9, source="declared")
        motors_spec = ComponentSpec.model_validate({
            "name": "4 motores",
            "component_type": "propulsion_active",
            "suggested_key": "motors",
            "inference_confidence": 0.9,
            "properties": {"motor_count": count_prop},
            "completeness": "medium",
            "missing_fields": [],
            "hints": [],
            "source": "declared",
            "output_magnitude": "thrust_n",
        })
        dp = DesignProperties.model_validate({
            "components": {"motors": motors_spec},
            "structure": {},
        })
        return ProjectState.model_validate({
            "project_id": "test-merge",
            "project_slug": "test-merge",
            "objective": "test",
            "workspace_path": "/tmp/test-merge",
            "current_parameters": {"motor_count": motor_count, "payload_kg": 1.0},
            "design_properties": dp,
        })

    def test_motor_count_preserved_when_missing_from_new_spec(self):
        """Segundo write con KV+W pero sin motor_count → motor_count debe seguir en properties."""
        from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
        from jarvis.core.component_writers import set_motor_component

        project_state = self._make_project_state_with_motors(motor_count=4)

        # New spec only has kv and power — no motor_count
        kv_prop = PropertyValue(value=2400.0, unit="KV", confidence=0.9, source="declared")
        pw_prop = PropertyValue(value=150.0, unit="W", confidence=0.9, source="declared")
        new_spec = ComponentSpec.model_validate({
            "name": "2306 2400KV 150W",
            "component_type": "propulsion_active",
            "suggested_key": "motors",
            "inference_confidence": 0.9,
            "properties": {"kv_rating": kv_prop, "power_w": pw_prop},
            "completeness": "medium",
            "missing_fields": [],
            "hints": [],
            "source": "declared",
            "output_magnitude": "thrust_n",
        })

        updated = set_motor_component(project_state, new_spec, power_w=150.0)

        motors_component = updated.design_properties.components["motors"]
        assert "motor_count" in motors_component.properties, (
            "motor_count debe preservarse del componente anterior"
        )
        assert motors_component.properties["motor_count"].value == 4

    def test_motor_count_not_overridden_when_new_spec_has_different_count(self):
        """Si el nuevo spec sí declara motor_count, se usa el nuevo valor."""
        from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
        from jarvis.core.component_writers import set_motor_component

        project_state = self._make_project_state_with_motors(motor_count=4)

        new_count_prop = PropertyValue(value=6, unit=None, confidence=0.9, source="declared")
        new_spec = ComponentSpec.model_validate({
            "name": "6 motores 2306",
            "component_type": "propulsion_active",
            "suggested_key": "motors",
            "inference_confidence": 0.9,
            "properties": {"motor_count": new_count_prop},
            "completeness": "medium",
            "missing_fields": [],
            "hints": [],
            "source": "declared",
            "output_magnitude": "thrust_n",
        })

        updated = set_motor_component(project_state, new_spec, power_w=None)

        assert updated.design_properties.components["motors"].properties["motor_count"].value == 6

    def test_current_parameters_motor_count_always_preserved(self):
        """Independientemente del merge, current_parameters['motor_count'] no se pierde."""
        from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
        from jarvis.core.component_writers import set_motor_component

        project_state = self._make_project_state_with_motors(motor_count=4)
        pw_prop = PropertyValue(value=100.0, unit="W", confidence=0.9, source="declared")
        new_spec = ComponentSpec.model_validate({
            "name": "motores 100W",
            "component_type": "propulsion_active",
            "suggested_key": "motors",
            "inference_confidence": 0.9,
            "properties": {"power_w": pw_prop},
            "completeness": "medium",
            "missing_fields": [],
            "hints": [],
            "source": "declared",
            "output_magnitude": "thrust_n",
        })

        updated = set_motor_component(project_state, new_spec, power_w=100.0)

        # current_parameters must still have motor_count (was 4, no new count in spec)
        assert updated.current_parameters.get("motor_count") == 4


# ─────────────────────────────────────────────────────────────────────────────
# Bug 79 — DSE apply emite warning de constraint
# ─────────────────────────────────────────────────────────────────────────────

class TestDSEApplyConstraintWarning:
    """_check_constraint_violations debe detectar max_weight_kg en updated_state
    y producir una violación cuando la masa total la supera."""

    def _make_state_with_weight_constraint(
        self,
        total_mass_kg: float,
        max_weight_kg: float,
    ):
        """Helper: construye un ProjectState con cálculo y restricción de peso."""
        from jarvis.schemas.state_schema import ProjectState, DesignProperties
        dp = DesignProperties.model_validate({"components": {}, "structure": {}})
        return ProjectState.model_validate({
            "project_id": "test-dse-constraint",
            "project_slug": "test",
            "objective": "test",
            "workspace_path": "/tmp/test",
            "current_parameters": {
                "payload_kg": 0.5,
                "restrictions": f"peso máximo {max_weight_kg}kg",
            },
            "design_properties": dp,
            "parsed_constraints": {"max_weight_kg": max_weight_kg},
            "latest_results": {
                "calculations": {"total_mass_kg": total_mass_kg},
            },
        })

    def _make_orchestrator(self):
        from unittest.mock import MagicMock, patch
        with patch("jarvis.core.orchestrator.WorkspaceManager"), \
             patch("jarvis.core.orchestrator.StateManager"), \
             patch("jarvis.core.orchestrator.FlightSimulator"), \
             patch("jarvis.core.orchestrator.CalculationEngine"), \
             patch("jarvis.core.orchestrator.MutationEngine"), \
             patch("jarvis.core.orchestrator.MemoryManager"), \
             patch("jarvis.core.orchestrator.SuggestionEngine"), \
             patch("jarvis.core.orchestrator.ReasoningLayer"), \
             patch("jarvis.core.orchestrator.PhaseLayer"), \
             patch("jarvis.core.orchestrator.Planner"), \
             patch("jarvis.core.orchestrator.CreateProjectAction"), \
             patch("jarvis.core.orchestrator.CalculateAction"), \
             patch("jarvis.core.orchestrator.SimulateAction"), \
             patch("jarvis.core.orchestrator.IterateAction"):
            from jarvis.core.orchestrator import JarvisOrchestrator
            return JarvisOrchestrator.__new__(JarvisOrchestrator)

    def test_no_violation_when_within_limit(self):
        """Masa 1.5kg con límite 2.0kg → lista vacía."""
        from unittest.mock import patch
        from jarvis.core.orchestrator import JarvisOrchestrator
        orch = object.__new__(JarvisOrchestrator)
        state = self._make_state_with_weight_constraint(
            total_mass_kg=1.5, max_weight_kg=2.0
        )
        violations = orch._check_constraint_violations(state)
        assert violations == []

    def test_violation_when_mass_exceeds_limit(self):
        """Masa 2.85kg con límite 2.0kg → warning en la lista."""
        from jarvis.core.orchestrator import JarvisOrchestrator
        orch = object.__new__(JarvisOrchestrator)
        state = self._make_state_with_weight_constraint(
            total_mass_kg=2.85, max_weight_kg=2.0
        )
        violations = orch._check_constraint_violations(state)
        assert len(violations) == 1
        assert "2.85" in violations[0]
        assert "2.0" in violations[0]

    def test_no_violation_when_no_constraints(self):
        """Sin restricciones definidas → lista vacía."""
        from jarvis.schemas.state_schema import ProjectState, DesignProperties
        from jarvis.core.orchestrator import JarvisOrchestrator
        orch = object.__new__(JarvisOrchestrator)
        dp = DesignProperties.model_validate({"components": {}, "structure": {}})
        state = ProjectState.model_validate({
            "project_id": "test",
            "project_slug": "test",
            "objective": "test",
            "workspace_path": "/tmp",
            "current_parameters": {},
            "design_properties": dp,
            "parsed_constraints": {},
            "latest_results": {"calculations": {"total_mass_kg": 5.0}},
        })
        violations = orch._check_constraint_violations(state)
        assert violations == []

    def test_no_violation_when_no_calculation(self):
        """Sin cálculo previo → lista vacía (no crash)."""
        from jarvis.schemas.state_schema import ProjectState, DesignProperties
        from jarvis.core.orchestrator import JarvisOrchestrator
        orch = object.__new__(JarvisOrchestrator)
        dp = DesignProperties.model_validate({"components": {}, "structure": {}})
        state = ProjectState.model_validate({
            "project_id": "test",
            "project_slug": "test",
            "objective": "test",
            "workspace_path": "/tmp",
            "current_parameters": {},
            "design_properties": dp,
            "parsed_constraints": {"max_weight_kg": 2.0},
            "latest_results": {},
        })
        violations = orch._check_constraint_violations(state)
        assert violations == []
