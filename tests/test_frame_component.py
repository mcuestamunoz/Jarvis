"""Tests for Fase 2 — UX-C (Commit 1) and UX-A (Commit 2)."""
from __future__ import annotations

import pytest

from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.component_writers import set_frame_material
from jarvis.core.state_manager import OrchestratorMode


# ── Commit 1: constant + stub ─────────────────────────────────────────────────

def test_missing_component_definition_constant_exists():
    """MISSING_COMPONENT_DEFINITION must be a non-empty string constant."""
    assert isinstance(MISSING_COMPONENT_DEFINITION, str)
    assert MISSING_COMPONENT_DEFINITION == "missing_component_definition"


def test_si_with_component_reason_returns_description_prompt(tmp_path):
    """'sí' while pending_missing_reason == MISSING_COMPONENT_DEFINITION returns an interactive
    description prompt, not a numeric wizard question."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    # Create a minimal project so the orchestrator has an active project to load.
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })

    # Force the session into DEFINE_MISSING_PARAMETERS + MISSING_COMPONENT_DEFINITION
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["material", "mass_kg"],
        "pending_define_missing": False,
    })
    orchestrator.state_manager.set_runtime_session(updated)

    class _FakeLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called in component description handler")

    result = orchestrator.handle_user_text("sí", _FakeLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"
    # The message must guide the user — not be empty or generic-error
    msg = result.get("message", "")
    assert "frame" in msg.lower() or "material" in msg.lower() or "describe" in msg.lower()


# ── Commit 2: _set_pending_next_block ─────────────────────────────────────────

def _create_drone_project(orchestrator, tmp_path, *, motors=4, thrust=15.0):
    """Helper: create a minimal drone project and return workspace_path."""
    result = orchestrator.handle({
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
    return result.get("workspace_path")


def test_pending_next_block_set_after_propulsion_complete(tmp_path):
    """After propulsion params are complete, _set_pending_next_block must pre-load the
    energy wizard into session so the next 'sí' opens it without re-reading startup context."""
    from jarvis.schemas.state_schema import DesignProperties
    from jarvis.schemas.action_schema import ComponentSpec

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    workspace_path = _create_drone_project(orchestrator, tmp_path)

    # Patch project state: system_defined=True, priority=[propulsion, energy, structure, control],
    # current_parameters have propulsion complete → next pending is energy.
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
    })
    params = dict(project_state.current_parameters or {})
    params["motors"] = 4
    params["per_motor_max_thrust_n"] = 15.0
    # Remove energy params to ensure energy is "not_started"
    params.pop("battery_capacity_wh", None)
    params.pop("motor_power_w", None)

    updated_state = project_state.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
    })
    orchestrator.workspace_manager.save_state(updated_state)

    # Call _set_pending_next_block directly
    orchestrator._set_pending_next_block()

    session = orchestrator.state_manager.runtime_state.session
    assert session.pending_define_missing is True
    # energy is composite: with no components present, Phase A fires → MISSING_COMPONENT_DEFINITION
    assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION
    assert len(session.pending_missing_params) > 0


def test_set_pending_next_block_component_driven_sets_missing_component_definition(tmp_path):
    """When the next pending block is component-driven (structure), _set_pending_next_block
    must set pending_missing_reason == MISSING_COMPONENT_DEFINITION."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        # Put structure first so it's the next pending block
        "system_priority": ["structure", "propulsion", "energy", "control"],
    })
    updated_state = project_state.model_copy(update={"design_properties": dp})
    orchestrator.workspace_manager.save_state(updated_state)

    orchestrator._set_pending_next_block()

    session = orchestrator.state_manager.runtime_state.session
    assert session.pending_define_missing is True
    assert session.pending_missing_reason == MISSING_COMPONENT_DEFINITION


def test_set_pending_next_block_noop_when_system_not_defined(tmp_path):
    """_set_pending_next_block must not mutate session when system is not defined."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    # system_defined defaults to False in a freshly created project
    session_before = orchestrator.state_manager.runtime_state.session
    orchestrator._set_pending_next_block()
    session_after = orchestrator.state_manager.runtime_state.session

    assert session_after.pending_define_missing == session_before.pending_define_missing


# ── Commit 5: _set_frame_material ────────────────────────────────────────────

def test_set_frame_material_writes_all_three_locations(tmp_path):
    """_set_frame_material must write atomically to:
      1. components['frame'].properties (canonical — Single Write + Read Point)
      2. current_parameters['structure_mass_override_kg'] (physics bypass)
    Fase 3: mirror legacy (structure.material) eliminado — ya no se escribe.
    """
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated = set_frame_material(project_state, mass_kg=0.45, material="carbon_fiber")

    # 1. canonical components
    assert "frame" in updated.design_properties.components
    frame = updated.design_properties.components["frame"]
    assert frame.properties["mass_kg"].value == 0.45
    assert frame.properties["material"].value == "carbon_fiber"

    # 2. physics bypass
    assert updated.current_parameters.get("structure_mass_override_kg") == 0.45


def test_set_frame_material_mass_only_no_material_key(tmp_path):
    """When material is None, structure.material should not be overwritten with None."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated = set_frame_material(project_state, mass_kg=0.3, material=None)

    # mass written
    assert updated.current_parameters.get("structure_mass_override_kg") == 0.3
    # material not overwritten with None — original value preserved
    assert updated.design_properties.structure.material is not None or \
           updated.design_properties.structure.material == project_state.design_properties.structure.material


def test_set_frame_material_size_only_preserves_existing_mass_override(tmp_path):
    """N1 hotfix (implementation_contract_structure_a_n1_hotfix.md): the
    override must mirror from the MERGED props, not the mass_kg argument.
    A size-only update (mass_kg=None) on a frame that already declares mass
    must not delete structure_mass_override_kg — walk: 'pvc 5 pulgadas' on
    a 0.65 kg frame must not drop total_mass_kg."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    state = set_frame_material(project_state, 0.65, "fibra de carbono")
    assert state.current_parameters.get("structure_mass_override_kg") == 0.65

    updated = set_frame_material(state, None, "pvc", 5.0)
    assert updated.current_parameters.get("structure_mass_override_kg") == 0.65
    frame = updated.design_properties.components["frame"]
    assert frame.properties["mass_kg"].value == 0.65
    assert frame.properties["size_class_inch"].value == 5.0
    assert frame.properties["material"].value == "pvc"


def test_set_frame_material_material_only_preserves_existing_mass_override(tmp_path):
    """Same bug, material-only shape (no size)."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    state = set_frame_material(project_state, 0.45, "fibra de carbono")
    assert state.current_parameters.get("structure_mass_override_kg") == 0.45

    updated = set_frame_material(state, None, "aluminum")
    assert updated.current_parameters.get("structure_mass_override_kg") == 0.45
    assert updated.design_properties.components["frame"].properties["mass_kg"].value == 0.45


def test_set_frame_material_completeness_high_when_both(tmp_path):
    """ComponentSpec.completeness must be 'high' when both mass and material are provided."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated = set_frame_material(project_state, mass_kg=0.5, material="aluminum")

    frame = updated.design_properties.components["frame"]
    assert frame.completeness == "high"


def test_set_frame_material_size_class_inch_written_and_none_leaves_existing(tmp_path):
    """Structure A (implementation_contract_structure_a.md §2.2):
    size_class_inch is component-property-only (no current_parameters
    mirror), None means "leave whatever is already declared" (same
    convention as material), and completeness stays mass+material-only —
    _frame_completeness is unchanged by this IC, so a frame with mass +
    material but no size_class_inch is still "high"."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated = set_frame_material(project_state, 0.45, "carbon_fiber", 5.0)
    frame = updated.design_properties.components["frame"]
    assert frame.properties["size_class_inch"].value == 5.0
    assert frame.completeness == "high"
    # size_class_inch never mirrors into current_parameters.
    assert "size_class_inch" not in updated.current_parameters

    # A later call with size_class_inch=None must not erase the declared class.
    updated2 = set_frame_material(updated, 0.5, "carbon_fiber")
    frame2 = updated2.design_properties.components["frame"]
    assert frame2.properties["size_class_inch"].value == 5.0


def test_set_frame_material_does_not_mutate_original(tmp_path):
    """_set_frame_material must return a new state — original must be unchanged."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    original_params = dict(project_state.current_parameters or {})
    set_frame_material(project_state, mass_kg=0.6, material="carbon_fiber")

    # Reload — original on disk unchanged (helper doesn't save)
    reloaded = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert reloaded.current_parameters.get("structure_mass_override_kg") is None


# ── Commit 7: remaining spec tests + CRITERIO DE FINALIZACIÓN ─────────────────


def test_physics_uses_frame_mass_when_available(tmp_path):
    """structure_mass_override_kg=0.3 must produce a lower total_mass_kg than the factor path.

    With payload_kg=1.0 and structure_mass_factor=0.5:
      - factor path: structure_mass = 1.0 * 0.5 = 0.5 → total = 1.5 kg
      - override path: structure_mass = 0.3 → total = 1.3 kg

    _set_frame_material with mass_kg=0.3 must write structure_mass_override_kg=0.3 so that
    calculation_engine.build() uses the override instead of the factor.
    """
    from jarvis.core.calculation_engine import CalculationEngine

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path, motors=4, thrust=15.0)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    params_base = dict(project_state.current_parameters or {})

    # ── Baseline: total mass with factor (no override) ────────────────────────
    engine = CalculationEngine()
    calc_factor = engine.build(params_base)
    total_factor = calc_factor.total_mass_kg

    # ── Override: _set_frame_material writes structure_mass_override_kg=0.3 ──
    updated = set_frame_material(project_state, mass_kg=0.3, material=None)
    params_override = dict(updated.current_parameters or {})

    assert params_override.get("structure_mass_override_kg") == 0.3

    calc_override = engine.build(params_override)
    total_override = calc_override.total_mass_kg

    # Override (0.3 kg structure) < factor (0.5 * payload kg)
    assert total_override < total_factor, (
        f"Expected override total ({total_override}) < factor total ({total_factor})"
    )


# ── CRITERIO DE FINALIZACIÓN — automated end-to-end validation ────────────────


def test_criterio_frame_in_natural_language_saved_correctly(tmp_path):
    """CRITERIO 1+2: Define frame en lenguaje natural → guardado en los 3 lugares canónicos."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("fibra de carbono 450g", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

    # components["frame"].properties (canónico)
    frame = saved.design_properties.components.get("frame")
    assert frame is not None
    assert "mass_kg" in frame.properties
    assert "material" in frame.properties
    assert frame.properties["mass_kg"].value == pytest.approx(0.45, rel=1e-3)
    assert frame.properties["material"].value == "fibra de carbono"

    # current_parameters["structure_mass_override_kg"] (bypass física)
    # Nota: mirror legacy structure.material eliminado en Fase 3 — ya no se verifica aquí.
    assert saved.current_parameters.get("structure_mass_override_kg") == pytest.approx(0.45, rel=1e-3)


def test_criterio_total_mass_changes_vs_factor(tmp_path):
    """CRITERIO 3: La masa total cambia respecto al cálculo con factor."""
    from jarvis.core.calculation_engine import CalculationEngine

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    engine = CalculationEngine()
    params_base = dict(project_state.current_parameters or {})
    total_factor = engine.build(params_base).total_mass_kg

    # Set frame with a very different mass (0.1 kg vs factor default ~0.5 kg)
    updated = set_frame_material(project_state, mass_kg=0.1, material=None)
    total_override = engine.build(dict(updated.current_parameters or {})).total_mass_kg

    assert abs(total_override - total_factor) > 0.01, (
        "total_mass_kg must differ meaningfully when structure_mass_override_kg is set"
    )


def test_criterio_block_progress_complete_after_frame(tmp_path):
    """CRITERIO 4: _block_progress_status('structure') == 'complete' after frame saved."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("fibra de carbono 500g", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    status = orchestrator._block_progress_status(
        "structure", saved.design_properties, saved.current_parameters or {}
    )
    assert status == "complete"


def test_criterio_no_llm_called_in_component_flow(tmp_path):
    """CRITERIO 5: El flujo de componentes no llama al LLM en ningún paso."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    llm_calls: list[str] = []
    orig = orchestrator._semantic_adapter.adapt
    def patched(text, mode=None):
        llm_calls.append(text)
        return orig(text, mode)
    orchestrator._semantic_adapter.adapt = patched

    # Affirmative (must NOT call LLM)
    orchestrator._handle_component_description("sí", session)
    # Description (must NOT call LLM)
    orchestrator._handle_component_description("aluminio 400g", session)
    # Vague (must NOT call LLM)
    orchestrator._handle_component_description("cosa", session)

    assert not llm_calls, f"LLM called unexpectedly in component flow: {llm_calls}"


# ── Commit 6: _handle_component_description full logic + build_startup_context ─


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
    # Inject session so the intercept routes to _handle_component_description
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["frame"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


def test_component_description_saves_frame_and_recalculates(tmp_path):
    """'fibra de carbono 450g' → status ok, frame persisted with mass + material."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("fibra de carbono 450g", session)

    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
    assert "frame" in result["message"].lower() or "registrado" in result["message"].lower()

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = saved.design_properties.components.get("frame")
    assert frame is not None
    assert frame.properties["mass_kg"].value == pytest.approx(0.45, rel=1e-3)
    assert frame.properties["material"].value == "fibra de carbono"


def test_component_description_updates_structure_material(tmp_path):
    """After a successful description, components[frame] and override param must be persisted.
    Fase 3: mirror legacy (structure.material) eliminado — se verifica solo la fuente canónica.
    """
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("aluminio 600g", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = saved.design_properties.components.get("frame")
    assert frame is not None
    assert frame.properties.get("material") is not None
    assert frame.properties["material"].value == "aluminio"
    assert saved.current_parameters.get("structure_mass_override_kg") == pytest.approx(0.6, rel=1e-3)


def test_si_after_structure_hint_returns_frame_example(tmp_path):
    """Affirmative input while component description pending must return a prompt with an example."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("sí", session)

    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"
    assert "ej:" in result["message"].lower() or "450g" in result["message"].lower()


def test_vague_component_description_stays_interactive(tmp_path):
    """Vague input with no mass or material stays interactive and state is NOT persisted."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    before = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator._handle_component_description("frame del dron", session)

    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"

    after = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert "frame" not in after.design_properties.components or \
           after.design_properties.components["frame"].completeness == "low"


def test_structure_block_complete_after_frame_medium(tmp_path):
    """After a medium-completeness frame (mass only), structure block must not be 'not_started'."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    # "estructura 0.45kg" → frame rule matches (keyword 'estructura') + mass extracted → completeness "medium"
    result = orchestrator._handle_component_description("estructura 0.45kg", session)

    assert result["status"] == "ok"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    status = orchestrator._block_progress_status(
        "structure", saved.design_properties, saved.current_parameters or {}
    )
    assert status != "not_started"


def test_proactive_question_for_structure_includes_example(tmp_path):
    """build_startup_context with structure as next pending block must use MISSING_COMPONENT_DEFINITION
    and include an example in proactive_question."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # Provide energy params so missing_energy_parameters signal is suppressed
    params = dict(project_state.current_parameters or {})
    params["battery_capacity_wh"] = 200.0
    params["motor_power_w"] = 50.0
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure", "energy"],
        "system_priority": ["structure", "energy"],
    })
    updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
    orchestrator.workspace_manager.save_state(updated)

    ctx = orchestrator.build_startup_context()

    assert ctx["param_definition_reason"] == MISSING_COMPONENT_DEFINITION
    assert "frame" in (ctx.get("missing_params") or [])
    pq = ctx.get("proactive_question") or ""
    assert "carbono" in pq.lower() or "ej" in pq.lower() or "material" in pq.lower()


# ── Bug 62: frame material-only must intercept, not reach LLM ─────────────────

class TestFrameMaterialOnlyIntercept:
    """Bug 62 — 'estructura de fibra de carbono' (material, sin masa) debe interceptarse
    por el flujo de componente y no llegar al LLM.

    Root cause: el guard anterior usaba `completeness == "low"` como proxy para
    "no hay señal útil", pero calidad ≠ utilidad. El fix cambia el criterio a
    presencia de propiedades extraídas (spec.properties no vacío).
    """

    def test_frame_material_only_not_routed_to_llm(self, tmp_path):
        """'estructura de fibra de carbono' (material sin masa) → intercept, no LLM.

        El sistema debe preguntar por la masa — nunca llamar al LLM.
        """
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _setup_structure_pending(orchestrator, tmp_path)

        llm_called = []

        class _SpyLLM:
            def generate(self, *a, **kw):
                llm_called.append(True)
                return {}
            def interpret(self, *a, **kw):
                llm_called.append(True)
                return {"action": "unknown", "parameters": {}}

        result = orchestrator.handle_user_text("estructura de fibra de carbono", _SpyLLM())

        assert not llm_called, "LLM no debe ser llamado para frame con material sin masa"
        assert result.get("action") in ("component_description_saved", "component_description_prompt")

    def test_frame_material_only_prompts_for_mass(self, tmp_path):
        """Tras interceptar 'estructura de fibra de carbono', el sistema pide la masa."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _setup_structure_pending(orchestrator, tmp_path)

        class _NoLLM:
            def generate(self, *a, **kw): raise AssertionError("LLM must not be called")
            def interpret(self, *a, **kw): raise AssertionError("LLM must not be called")

        result = orchestrator.handle_user_text("estructura de fibra de carbono", _NoLLM())

        # Si completeness es low (material sin masa), _handle_component_description
        # devuelve un prompt interactivo pidiendo la masa.
        if result.get("action") == "component_description_prompt":
            msg = result.get("message", "").lower()
            assert "peso" in msg or "masa" in msg or "pesa" in msg or "kg" in msg or "g" in msg, \
                f"El mensaje de prompt debe pedir la masa, got: {result.get('message')!r}"

    def test_frame_no_properties_not_intercepted(self, tmp_path):
        """'frame' solo (sin propiedades extraíbles) → properties vacío → NO intercepta."""
        orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
        _setup_structure_pending(orchestrator, tmp_path)

        session = orchestrator.state_manager.runtime_state.session
        # Mode must be IDLE so the global intercept path runs
        idle_session = session.model_copy(update={"mode": OrchestratorMode.IDLE})
        orchestrator.state_manager.set_runtime_session(idle_session)
        idle_session = orchestrator.state_manager.runtime_state.session

        spec = orchestrator._should_intercept_component("frame", idle_session)
        assert spec is None, "'frame' sin propiedades no debe interceptarse"
