"""D4: COMPONENT_MIRRORED_PARAMS bridge.

Verifica que apply_and_recalculate enruta los mirrored params
(battery_capacity_wh, motor_power_w, propeller_diameter_in) a través de
los component writers (no noop, no escritura directa). try_ingest los
omite correctamente para que la arquitectura los gestione.
"""

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator


def _create_drone_project(orchestrator):
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba D4",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


class TestParamGatekeeper:

    def test_mirrored_param_contract_battery(self, tmp_path):
        """MIRRORED PARAM CONTRACT: battery_capacity_wh → set_battery_component → components + params."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        result = orchestrator.param_definition_session.apply_and_recalculate({"battery_capacity_wh": 500.0})

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert result["status"] == "ok"
        # (1) canónico — components actualizado
        assert "battery" in saved.design_properties.components
        # (2) bridge — current_parameters contiene el mirror
        assert (saved.current_parameters or {}).get("battery_capacity_wh") == pytest.approx(500.0)

    def test_mirrored_param_contract_motor(self, tmp_path):
        """MIRRORED PARAM CONTRACT: motor_power_w → set_motor_component → components + params."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        result = orchestrator.param_definition_session.apply_and_recalculate({"motor_power_w": 120.0})

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert result["status"] == "ok"
        # (1) canónico — components actualizado
        assert "motors" in saved.design_properties.components
        # (2) bridge — current_parameters contiene el mirror
        assert (saved.current_parameters or {}).get("motor_power_w") == pytest.approx(120.0)

    def test_mirrored_param_contract_propeller(self, tmp_path):
        """MIRRORED PARAM CONTRACT: propeller_diameter_in → set_propeller_component → components + params."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        result = orchestrator.param_definition_session.apply_and_recalculate({"propeller_diameter_in": 12.0})

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert result["status"] == "ok"
        # (1) canónico — components actualizado
        assert "propellers" in saved.design_properties.components
        # (2) bridge — current_parameters contiene el mirror
        assert (saved.current_parameters or {}).get("propeller_diameter_in") == pytest.approx(12.0)

    def test_non_mirrored_param_written(self, tmp_path):
        """apply_and_recalculate({"motor_count": ...}) (non-mirrored) → IS written, status == 'ok'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        result = orchestrator.param_definition_session.apply_and_recalculate({"motor_count": 6.0})

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert (saved.current_parameters or {}).get("motor_count") == pytest.approx(6.0)
        assert result["status"] == "ok"

    def test_try_ingest_skips_mirrored_missing(self, tmp_path):
        """try_ingest when physics missing == only mirrored params → returns None (let arch handle)."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        # Inject physics_incomplete simulation with MISSING_ENERGY_PARAMETERS
        # and clear the mirrored params so missing_params_for_reason returns them.
        project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        params = dict(project_state.current_parameters or {})
        params.pop("battery_capacity_wh", None)
        params.pop("motor_power_w", None)
        updated = project_state.model_copy(update={
            "current_parameters": params,
            "latest_results": {
                "simulation": {
                    "physics_status": "missing_parameters",
                    "warnings": ["missing_energy_parameters"],
                }
            },
        })
        orchestrator.workspace_manager.save_state(updated)

        result = orchestrator.param_definition_session.try_ingest("5000")

        assert result is None

    def test_motors_alias_normalized_in_apply_and_recalculate(self, tmp_path):
        """Bug 63: apply_and_recalculate({'motors': 6}) normaliza 'motors' a 'motor_count'."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _create_drone_project(orchestrator)

        result = orchestrator.param_definition_session.apply_and_recalculate({"motors": 6.0})

        saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
        assert result["status"] == "ok"
        assert (saved.current_parameters or {}).get("motor_count") == pytest.approx(6.0), (
            "'motors' debe normalizarse a 'motor_count' en apply_and_recalculate"
        )
        assert "motors" not in (saved.current_parameters or {}), (
            "la clave alias 'motors' no debe persistir en current_parameters"
        )
