"""Tests for Fase 2.5 — Control block (ComponentRule mínimo).

Commit structure:
  Commit 1+2 — extract_flight_controller_properties, extract_sensor_properties,
                _flight_controller_completeness, _sensor_completeness,
                ComponentRule FC + sensors in aerial_registry.
  Commit 3    — _set_control_component, _handle_component_description dispatch by suggested_key.
  Commit 4    — CRITERIO DE FINALIZACIÓN (end-to-end validation).
"""
from __future__ import annotations

import pytest

from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.component_writers import set_control_component
from jarvis.core.state_manager import OrchestratorMode
from jarvis.domains.aerial import (
    aerial_registry,
    extract_flight_controller_properties,
    extract_sensor_properties,
    _flight_controller_completeness,
    _sensor_completeness,
    FLIGHT_CONTROLLER_MAP,
    GPS_MAP,
)
from jarvis.core.component_inference import infer_component


# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_drone_project(orchestrator, tmp_path, *, motors=4, thrust=15.0):
    """Create a minimal drone project."""
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": motors,
            "per_motor_max_thrust_n": thrust,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _setup_control_pending(orchestrator, tmp_path):
    """Create a project and configure system so 'control' is the first pending block."""
    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["control", "propulsion", "energy"],
        "system_priority": ["control", "propulsion", "energy"],
    })
    updated = project_state.model_copy(update={"design_properties": dp})
    orchestrator.workspace_manager.save_state(updated)
    # Inject session so intercept routes to _handle_component_description
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["flight_controller", "sensors"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


def _setup_structure_pending(orchestrator, tmp_path):
    """Create a project and configure system so 'structure' is the first pending block."""
    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure", "propulsion", "energy"],
        "system_priority": ["structure", "propulsion", "energy"],
    })
    updated = project_state.model_copy(update={"design_properties": dp})
    orchestrator.workspace_manager.save_state(updated)
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["frame"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


# ── Commit 1+2: extract_flight_controller_properties ─────────────────────────

def test_extract_fc_pixhawk4():
    """'Pixhawk 4' → model='pixhawk_4', confidence=0.9 (digit in alias)."""
    props = extract_flight_controller_properties("pixhawk 4")
    assert "model" in props
    assert props["model"].value == "pixhawk_4"
    assert props["model"].confidence == pytest.approx(0.9)


def test_extract_fc_pixhawk_generic():
    """'controladora Pixhawk' → model='pixhawk', confidence=0.7 (no digit in 'pixhawk')."""
    props = extract_flight_controller_properties("controladora pixhawk")
    assert "model" in props
    assert props["model"].value == "pixhawk"
    assert props["model"].confidence == pytest.approx(0.7)


def test_extract_fc_pixhawk4_longer_match_wins():
    """'pixhawk 4 mini' → model='pixhawk_4_mini', not 'pixhawk_4' (longest match)."""
    props = extract_flight_controller_properties("pixhawk 4 mini")
    assert props["model"].value == "pixhawk_4_mini"


def test_extract_fc_ardupilot():
    """'ardupilot' → model='ardupilot', confidence=0.7."""
    props = extract_flight_controller_properties("ardupilot")
    assert props["model"].value == "ardupilot"
    assert props["model"].confidence == pytest.approx(0.7)


def test_extract_fc_unknown():
    """'computadora' → empty dict (no match in FLIGHT_CONTROLLER_MAP)."""
    props = extract_flight_controller_properties("computadora")
    assert props == {}


# ── Commit 1+2: extract_sensor_properties ────────────────────────────────────

def test_extract_sensors_gps_m9n():
    """'GPS M9N' → gps_model='ublox_m9n', confidence=0.9."""
    props = extract_sensor_properties("gps m9n")
    assert "gps_model" in props
    assert props["gps_model"].value == "ublox_m9n"
    assert props["gps_model"].confidence == pytest.approx(0.9)


def test_extract_sensors_here3():
    """'Here3' → gps_model='here3', confidence=0.9."""
    props = extract_sensor_properties("here3")
    assert props["gps_model"].value == "here3"
    assert props["gps_model"].confidence == pytest.approx(0.9)


def test_extract_sensors_here3_plus_longer_match():
    """'here3+' → gps_model='here3_plus', not 'here3' (longest match)."""
    props = extract_sensor_properties("here3+")
    assert props["gps_model"].value == "here3_plus"


def test_extract_sensors_generic_gps():
    """'gps generico' → gps_model='generic_gps', confidence=0.6."""
    props = extract_sensor_properties("gps generico")
    assert props["gps_model"].value == "generic_gps"
    assert props["gps_model"].confidence == pytest.approx(0.6)


def test_extract_sensors_unknown():
    """'camara' → empty dict (no GPS keyword)."""
    props = extract_sensor_properties("camara")
    assert props == {}


# ── Commit 1+2: completeness evaluators ──────────────────────────────────────

def test_fc_completeness_high():
    """model present with confidence=0.9 → 'high'."""
    from jarvis.schemas.action_schema import PropertyValue
    props = {"model": PropertyValue(value="pixhawk_4", confidence=0.9, source="declared")}
    level, missing = _flight_controller_completeness(props)
    assert level == "high"
    assert missing == []


def test_fc_completeness_medium():
    """model present with confidence=0.7 → 'medium'."""
    from jarvis.schemas.action_schema import PropertyValue
    props = {"model": PropertyValue(value="pixhawk", confidence=0.7, source="declared")}
    level, missing = _flight_controller_completeness(props)
    assert level == "medium"


def test_fc_completeness_low():
    """Empty dict → 'low' with missing hint."""
    level, missing = _flight_controller_completeness({})
    assert level == "low"
    assert len(missing) > 0


def test_sensor_completeness_medium():
    """gps_model present → 'medium'."""
    from jarvis.schemas.action_schema import PropertyValue
    props = {"gps_model": PropertyValue(value="ublox_m9n", confidence=0.9, source="declared")}
    level, missing = _sensor_completeness(props)
    assert level == "medium"
    assert missing == []


def test_sensor_completeness_low():
    """Empty dict → 'low' with missing hint."""
    level, missing = _sensor_completeness({})
    assert level == "low"
    assert len(missing) > 0


# ── Commit 1+2: aerial_registry keyword matching ─────────────────────────────

def test_aerial_registry_matches_pixhawk_keyword():
    """'Pixhawk 4' → suggested_key='flight_controller', completeness='high'."""
    spec = infer_component("Pixhawk 4", registry=aerial_registry)
    assert spec.suggested_key == "flight_controller"
    assert spec.completeness == "high"


def test_aerial_registry_matches_controladora_keyword():
    """'controladora Pixhawk' → suggested_key='flight_controller'."""
    spec = infer_component("controladora Pixhawk", registry=aerial_registry)
    assert spec.suggested_key == "flight_controller"


def test_aerial_registry_matches_gps_m9n_keyword():
    """'GPS M9N' → suggested_key='sensors', completeness='medium'."""
    spec = infer_component("GPS M9N", registry=aerial_registry)
    assert spec.suggested_key == "sensors"
    assert spec.completeness == "medium"


def test_aerial_registry_has_seven_rules():
    """Registry must have exactly 7 rules after Fase 2.5 additions."""
    assert len(aerial_registry) == 7


# ── Commit 3: _set_control_component ─────────────────────────────────────────

def test_set_control_component_writes_flight_controller(tmp_path):
    """_set_control_component with FC spec → components['flight_controller'] written."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("Pixhawk 4", registry=aerial_registry)

    updated = set_control_component(project_state, spec)

    assert "flight_controller" in updated.design_properties.components
    fc = updated.design_properties.components["flight_controller"]
    assert fc.completeness != "low"
    assert "model" in fc.properties


def test_set_control_component_writes_sensors(tmp_path):
    """_set_control_component with sensors spec → components['sensors'] written."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("GPS M9N", registry=aerial_registry)

    updated = set_control_component(project_state, spec)

    assert "sensors" in updated.design_properties.components
    sensors = updated.design_properties.components["sensors"]
    assert sensors.completeness != "low"


def test_set_control_component_does_not_mutate_original(tmp_path):
    """_set_control_component must return a new state — original must be unchanged."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("Pixhawk 4", registry=aerial_registry)

    set_control_component(project_state, spec)

    # Original not mutated (helper does NOT save)
    reloaded = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert "flight_controller" not in reloaded.design_properties.components


def test_set_control_component_no_physics_bypass(tmp_path):
    """_set_control_component must NOT write to current_parameters."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    original_params = dict(project_state.current_parameters or {})
    spec = infer_component("Pixhawk 4", registry=aerial_registry)

    updated = set_control_component(project_state, spec)

    assert dict(updated.current_parameters or {}) == original_params


# ── Commit 3: _handle_component_description dispatch ─────────────────────────

def test_handle_component_description_fc_saves_flight_controller(tmp_path):
    """'Pixhawk 4' with control block → components['flight_controller'] persisted."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("Pixhawk 4", session)

    # FC saved (block still in_progress — sensors missing) → status ok, message has follow-up
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    fc = saved.design_properties.components.get("flight_controller")
    assert fc is not None
    assert fc.completeness != "low"


def test_handle_component_description_sensors_saved_after_fc(tmp_path):
    """After FC saved, 'GPS M9N' with control block → both FC+sensors persisted, block complete."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    # Save FC first
    orchestrator._handle_component_description("Pixhawk 4", session)

    # Reload session (pending_missing_params unchanged: ["flight_controller", "sensors"])
    session = orchestrator.state_manager.runtime_state.session
    result = orchestrator._handle_component_description("GPS M9N", session)

    assert result["status"] == "ok"
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

    fc = saved.design_properties.components.get("flight_controller")
    sensors = saved.design_properties.components.get("sensors")
    assert fc is not None and fc.completeness != "low"
    assert sensors is not None and sensors.completeness != "low"


def test_handle_component_description_no_cross_contamination(tmp_path):
    """'Pixhawk 4' with structure block active → NOT written to frame."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    # Structure block active (expected_keys=["frame"])
    session = _setup_structure_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("Pixhawk 4", session)

    # Should redirect — FC does not belong to structure block
    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # Frame must NOT have been written
    frame = saved.design_properties.components.get("frame")
    assert frame is None or frame.completeness == "low"


def test_affirmative_control_block_prompts_fc(tmp_path):
    """'sí' with control block pending → prompt for flight_controller."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("sí", session)

    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"
    msg = result.get("message", "").lower()
    assert "controladora" in msg or "pixhawk" in msg or "flight" in msg


def test_affirmative_control_block_after_fc_prompts_sensors(tmp_path):
    """'sí' with control block and FC already saved → prompt for sensors (GPS)."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    # Save FC so only sensors is missing
    orchestrator._handle_component_description("Pixhawk 4", session)
    # Reload session
    session = orchestrator.state_manager.runtime_state.session

    result = orchestrator._handle_component_description("sí", session)

    assert result["status"] == "interactive"
    msg = result.get("message", "").lower()
    assert "gps" in msg or "sensor" in msg or "here" in msg or "m9n" in msg


# ── Commit 3: control block progress ─────────────────────────────────────────

def test_control_block_in_progress_with_only_fc(tmp_path):
    """After FC only, _block_progress_status('control') == 'in_progress'."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("Pixhawk 4", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    status = orchestrator._block_progress_status(
        "control", saved.design_properties, saved.current_parameters or {}
    )
    assert status == "in_progress"


def test_control_block_complete_after_both_components(tmp_path):
    """After FC + GPS, _block_progress_status('control') == 'complete'."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("Pixhawk 4", session)
    session = orchestrator.state_manager.runtime_state.session
    orchestrator._handle_component_description("GPS M9N", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    status = orchestrator._block_progress_status(
        "control", saved.design_properties, saved.current_parameters or {}
    )
    assert status == "complete"


# ── CRITERIO DE FINALIZACIÓN — automated end-to-end validation ────────────────


def test_criterio_pixhawk_saves_fc_component(tmp_path):
    """CRITERIO 1: 'Pixhawk 4' → components['flight_controller'].completeness != 'low'."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("Pixhawk 4", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    fc = saved.design_properties.components.get("flight_controller")
    assert fc is not None
    assert fc.completeness != "low"


def test_criterio_gps_saves_sensors_component(tmp_path):
    """CRITERIO 2: 'GPS M9N' → components['sensors'].completeness != 'low'."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("GPS M9N", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    sensors = saved.design_properties.components.get("sensors")
    assert sensors is not None
    assert sensors.completeness != "low"


def test_criterio_no_cross_write_to_frame(tmp_path):
    """CRITERIO 3: FC input with control block → frame NOT touched."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("Pixhawk 4", session)
    session = orchestrator.state_manager.runtime_state.session
    orchestrator._handle_component_description("GPS M9N", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # frame must not have been written during control block processing
    frame = saved.design_properties.components.get("frame")
    assert frame is None or frame.completeness == "low"


def test_criterio_llm_never_called_in_control_flow(tmp_path):
    """CRITERIO 4: full control flow (sí → FC → GPS) never calls the LLM."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    llm_calls: list[str] = []
    orig = orchestrator._semantic_adapter.adapt

    def patched(text, mode=None):
        llm_calls.append(text)
        return orig(text, mode)

    orchestrator._semantic_adapter.adapt = patched

    # Affirmative
    orchestrator._handle_component_description("sí", session)
    # FC
    orchestrator._handle_component_description("Pixhawk 4", session)
    session = orchestrator.state_manager.runtime_state.session
    # GPS
    orchestrator._handle_component_description("GPS M9N", session)

    assert not llm_calls, f"LLM called unexpectedly in control flow: {llm_calls}"


# ── Bug 66: IMU, barómetro, compass in extract_sensor_properties ──────────────

class TestSensorIMUBarometer:
    """Bug 66: extract_sensor_properties must recognise IMU, barómetro, compass types."""

    def test_extract_sensors_imu(self):
        """'sensores IMU' → sensor_type='imu', completeness 'medium'."""
        from jarvis.domains.aerial import extract_sensor_properties, _sensor_completeness
        props = extract_sensor_properties("sensores IMU")
        assert "sensor_type" in props, "sensor_type must be present for IMU description"
        assert props["sensor_type"].value == "imu"
        assert props["sensor_type"].confidence == pytest.approx(0.8)
        level, _ = _sensor_completeness(props)
        assert level == "medium"

    def test_extract_sensors_barometro(self):
        """'barómetro de presión' → sensor_type='barometer'."""
        from jarvis.domains.aerial import extract_sensor_properties
        props = extract_sensor_properties("barómetro de presión")
        assert "sensor_type" in props
        assert props["sensor_type"].value == "barometer"

    def test_aerial_registry_matches_imu_keyword(self):
        """infer_component('sensores IMU y barómetro') → suggested_key='sensors',
        properties not empty, completeness='medium'."""
        from jarvis.domains.aerial import aerial_registry
        from jarvis.core.component_inference import infer_component
        spec = infer_component("sensores IMU y barómetro", registry=aerial_registry)
        assert spec.suggested_key == "sensors", (
            f"Bug 66: expected suggested_key='sensors', got {spec.suggested_key!r}"
        )
        assert spec.properties, (
            "Bug 66: properties must not be empty for 'sensores IMU y barómetro'"
        )
        assert spec.completeness == "medium", (
            f"Bug 66: expected completeness='medium', got {spec.completeness!r}"
        )

    # ── Bug 68 regression ────────────────────────────────────────────────────

    def test_simula_no_interceptado_como_sensor(self):
        """Bug 68: 'simula' contains 'imu' as substring — must NOT be classified as sensor.

        extract_sensor_properties must return empty properties so that
        _should_intercept_component guard (2) already rejects it. The
        word-boundary fix in the SENSOR_TYPE_MAP loop ensures this.
        """
        from jarvis.domains.aerial import extract_sensor_properties
        props = extract_sensor_properties("simula")
        assert not props, (
            "Bug 68: 'simula' must not produce sensor properties — "
            f"got {props!r}"
        )

    def test_simular_no_interceptado_como_sensor(self):
        """Bug 68: 'simular' also contains 'imu' as substring — same guard."""
        from jarvis.domains.aerial import extract_sensor_properties
        props = extract_sensor_properties("simular")
        assert not props, (
            "Bug 68: 'simular' must not produce sensor properties — "
            f"got {props!r}"
        )

    def test_simula_no_intercepta_componente_en_orquestador(self, tmp_path):
        """Bug 68: _should_intercept_component('simula', idle_session) must return None."""
        from jarvis.core.orchestrator import JarvisOrchestrator
        orch = JarvisOrchestrator(workspace_root=tmp_path)
        session = orch.state_manager.runtime_state.session
        result = orch._should_intercept_component("simula", session)
        assert result is None, (
            "Bug 68: 'simula' must not be intercepted as a component description — "
            f"got {result!r}"
        )


def test_criterio_control_complete_advances_to_next_block(tmp_path):
    """CRITERIO 5: After both FC+GPS, _set_pending_next_block advances to next block."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_control_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("Pixhawk 4", session)
    session = orchestrator.state_manager.runtime_state.session
    orchestrator._handle_component_description("GPS M9N", session)

    # After control complete, pending block must have changed from control to the next one.
    # Priority: ["control", "propulsion", "energy"]. Propulsion is already complete (motors +
    # per_motor_max_thrust_n set at project creation), so energy is next. Energy is composite
    # with no components defined → Phase A fires → MISSING_COMPONENT_DEFINITION.
    new_session = orchestrator.state_manager.runtime_state.session
    assert new_session.pending_define_missing is True
    assert new_session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
