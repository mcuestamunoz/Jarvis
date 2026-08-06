"""Tests for Fase 2.6 — Battery como componente mínimo.

Commit structure:
  Commit 1 — fix extract_battery_properties mAh→Wh (cell-aware, 3.7V/cell)
  Commit 2 — _set_battery_component (atomic write: components + current_parameters)
  Commit 3 — battery dispatch in _handle_component_description + intercept in param wizard
  Commit 4 — CRITERIO DE FINALIZACIÓN (end-to-end + G1 gap documented)
"""
from __future__ import annotations

import pytest

from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.component_writers import set_battery_component
from jarvis.core.state_manager import OrchestratorMode
from jarvis.domains.aerial import (
    aerial_registry,
    extract_battery_properties,
    _battery_completeness,
)
from jarvis.core.component_inference import infer_component


# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_drone_project(orchestrator, tmp_path):
    """Create a minimal drone project."""
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


def _setup_energy_pending(orchestrator, tmp_path, *, extra_params: dict | None = None):
    """Create a project and inject MISSING_ENERGY_PARAMETERS session (energy wizard active)."""
    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure"],
        "system_priority": ["energy", "propulsion", "structure"],
    })
    params = dict(project_state.current_parameters or {})
    if extra_params:
        params.update(extra_params)
    updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
    orchestrator.workspace_manager.save_state(updated)

    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_define_missing": True,
        "pending_missing_params": ["battery_capacity_wh", "motor_power_w"],
        "pending_missing_reason": MISSING_ENERGY_PARAMETERS,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


def _setup_battery_component_pending(orchestrator, tmp_path):
    """Create a project with 'energy' block as component-driven (for direct component flow)."""
    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy", "propulsion"],
        "system_priority": ["energy", "propulsion"],
    })
    updated = project_state.model_copy(update={"design_properties": dp})
    orchestrator.workspace_manager.save_state(updated)
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["battery"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    })
    orchestrator.state_manager.set_runtime_session(session)
    return orchestrator.state_manager.runtime_state.session


def _setup_structure_pending(orchestrator, tmp_path):
    """Create a project with 'structure' block pending (expected_keys=["frame"])."""
    _create_drone_project(orchestrator, tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure"],
        "system_priority": ["structure"],
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


# ── Commit 1: extract_battery_properties mAh→Wh fix ─────────────────────────

def test_battery_mah_without_cells_uses_1s_estimate():
    """'5000mAh' alone → wh ≈ 18.5, confidence=0.5 (1S rough estimate)."""
    props = extract_battery_properties("5000mah")
    assert "battery_capacity_wh" in props
    wh = props["battery_capacity_wh"].value
    assert wh == pytest.approx(18.5, rel=1e-2)
    assert props["battery_capacity_wh"].confidence == pytest.approx(0.5)


def test_battery_mah_with_cells_correct_wh():
    """'6S 5000mAh' → wh = 5000/1000 * 6 * 3.7 = 111.0, confidence=0.9."""
    props = extract_battery_properties("6s 5000mah")
    assert "battery_capacity_wh" in props
    assert props["battery_capacity_wh"].value == pytest.approx(111.0, rel=1e-2)
    assert props["battery_capacity_wh"].confidence == pytest.approx(0.9)


def test_battery_mah_4s():
    """'4S 5000mAh' → wh = 5000/1000 * 4 * 3.7 = 74.0."""
    props = extract_battery_properties("4s 5000mah")
    assert props["battery_capacity_wh"].value == pytest.approx(74.0, rel=1e-2)


def test_battery_wh_direct_takes_priority():
    """'6S 100Wh' → battery_capacity_wh = 100.0 (Wh direct wins over mAh calc), confidence=0.9."""
    props = extract_battery_properties("6s 100wh")
    assert props["battery_capacity_wh"].value == pytest.approx(100.0)
    assert props["battery_capacity_wh"].confidence == pytest.approx(0.9)


def test_battery_completeness_medium_when_capacity_present():
    """capacity present → 'medium'."""
    from jarvis.schemas.action_schema import PropertyValue
    props = {"battery_capacity_wh": PropertyValue(value=100.0, confidence=0.9, source="declared")}
    level, _ = _battery_completeness(props)
    assert level == "medium"


def test_battery_completeness_low_when_nothing():
    """empty dict → 'low'."""
    level, missing = _battery_completeness({})
    assert level == "low"
    assert len(missing) > 0


# ── Commit 2: _set_battery_component ─────────────────────────────────────────

def test_set_battery_component_writes_both_locations(tmp_path):
    """_set_battery_component must write to components['battery'] AND current_parameters."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("LiPo 6S 5000mAh", registry=aerial_registry)

    updated = set_battery_component(project_state, spec, capacity_wh=111.0)

    assert "battery" in updated.design_properties.components
    assert updated.current_parameters.get("battery_capacity_wh") == pytest.approx(111.0)


def test_set_battery_component_invariant_coherence(tmp_path):
    """components['battery'].properties['battery_capacity_wh'].value == current_parameters['battery_capacity_wh']."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("6S 5000mAh bateria", registry=aerial_registry)
    cap_prop = spec.properties.get("battery_capacity_wh")
    capacity = cap_prop.value if cap_prop else None

    updated = set_battery_component(project_state, spec, capacity_wh=capacity)

    param_val = updated.current_parameters.get("battery_capacity_wh")
    component_val = updated.design_properties.components["battery"].properties["battery_capacity_wh"].value
    assert param_val == pytest.approx(component_val, rel=1e-4)


def test_set_battery_component_does_not_mutate_original(tmp_path):
    """_set_battery_component returns new state — disk/original unchanged."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("100wh bateria", registry=aerial_registry)

    set_battery_component(project_state, spec, capacity_wh=100.0)

    reloaded = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert "battery" not in reloaded.design_properties.components
    assert reloaded.current_parameters.get("battery_capacity_wh") is None


def test_set_battery_component_capacity_none_removes_param(tmp_path):
    """capacity_wh=None → battery_capacity_wh removed from current_parameters."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # Pre-set the param so we can verify removal
    params = dict(project_state.current_parameters or {})
    params["battery_capacity_wh"] = 100.0
    project_state = project_state.model_copy(update={"current_parameters": params})

    spec = infer_component("bateria", registry=aerial_registry)
    updated = set_battery_component(project_state, spec, capacity_wh=None)

    assert "battery_capacity_wh" not in (updated.current_parameters or {})


# ── Commit 3: dispatch + intercept ────────────────────────────────────────────

def test_handle_component_description_battery_saves_both_locations(tmp_path):
    """'6S 5000mAh' with battery block → components['battery'] + current_parameters written."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_battery_component_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("6S 5000mAh bateria", session)

    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert "battery" in saved.design_properties.components
    assert saved.current_parameters.get("battery_capacity_wh") is not None


def test_handle_component_description_battery_triggers_recalculation(tmp_path):
    """Battery save with motor_power_w present → autonomy_min available in state."""
    from jarvis.core.calculation_engine import CalculationEngine

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_battery_component_pending(orchestrator, tmp_path)

    # Pre-set motor_power_w AFTER setup so recalculation produces autonomy
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    params = dict(project_state.current_parameters or {})
    params["motor_power_w"] = 50.0
    orchestrator.workspace_manager.save_state(project_state.model_copy(update={"current_parameters": params}))

    orchestrator._handle_component_description("6S 5000mAh bateria", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.current_parameters.get("battery_capacity_wh") is not None
    # Verify engine would produce autonomy
    engine = CalculationEngine()
    calc = engine.build(dict(saved.current_parameters or {}))
    assert calc.autonomy_min is not None
    assert calc.autonomy_min > 0


def test_handle_component_description_battery_no_cross_write_to_frame(tmp_path):
    """'bateria 100Wh' with structure block (expected_keys=['frame']) → frame NOT written."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_structure_pending(orchestrator, tmp_path)

    result = orchestrator._handle_component_description("bateria 100Wh", session)

    # Should redirect — battery doesn't belong to structure block
    assert result["status"] == "interactive"
    assert result["action"] == "component_description_prompt"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = saved.design_properties.components.get("frame")
    assert frame is None or frame.completeness == "low"
    assert saved.current_parameters.get("battery_capacity_wh") is None


def test_battery_input_in_energy_wizard_intercepted(tmp_path):
    """'bateria 5000mAh' during energy param wizard → intercepted, battery saved (not wizard error)."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _setup_energy_pending(orchestrator, tmp_path)

    class _NoLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called")

    result = orchestrator.handle_user_text("bateria 5000mah", _NoLLM())

    # Must not be a wizard parse error
    assert result.get("status") != "error" or "parse" not in result.get("message", "").lower()
    # Battery must be saved
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.current_parameters.get("battery_capacity_wh") is not None


def test_battery_intercept_requires_non_low_completeness(tmp_path):
    """'bateria' alone (completeness='low') → NOT intercepted, goes to wizard."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _setup_energy_pending(orchestrator, tmp_path)

    class _NoLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called")

    # "bateria" alone → low completeness → should NOT intercept → wizard processes it
    # Wizard will likely return error/interactive (not a battery save)
    result = orchestrator.handle_user_text("bateria", _NoLLM())

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # Battery NOT saved from a low-completeness intercept
    assert saved.current_parameters.get("battery_capacity_wh") is None


def test_numeric_input_still_goes_to_wizard(tmp_path):
    """Pure numeric input during energy wizard → reaches wizard, NOT intercepted as battery.

    Protects the param-driven flow: '5000' is a valid wizard answer (e.g. for motor_power_w
    or battery_capacity_wh asked in Wh), not a component description.
    """
    class _NoLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called")

    # ── "500" (pure numeric) → wizard, not intercepted ───────────────────────
    orc1 = JarvisOrchestrator(workspace_root=tmp_path / "orc1")
    _setup_energy_pending(orc1, tmp_path / "orc1")
    intercept1: list[str] = []
    orig1 = orc1._handle_component_description

    def spy1(user_input, session):
        intercept1.append(user_input)
        return orig1(user_input, session)

    orc1._handle_component_description = spy1
    orc1.handle_user_text("500", _NoLLM())
    assert "500" not in intercept1, "Numeric '500' was intercepted as component — must go to wizard"

    # ── "5000mah" without battery keyword → wizard (mAh alone is not a battery keyword) ─
    orc2 = JarvisOrchestrator(workspace_root=tmp_path / "orc2")
    _setup_energy_pending(orc2, tmp_path / "orc2")
    intercept2: list[str] = []
    orig2 = orc2._handle_component_description

    def spy2(user_input, session):
        intercept2.append(user_input)
        return orig2(user_input, session)

    orc2._handle_component_description = spy2
    orc2.handle_user_text("5000mah", _NoLLM())
    assert "5000mah" not in intercept2, "'5000mah' alone should NOT intercept (no battery keyword)"

    # ── Sanity check: "lipo 6S 5000mAh" DOES intercept ────────────────────────
    orc3 = JarvisOrchestrator(workspace_root=tmp_path / "orc3")
    _setup_energy_pending(orc3, tmp_path / "orc3")
    intercept3: list[str] = []
    orig3 = orc3._handle_component_description

    def spy3(user_input, session):
        intercept3.append(user_input)
        return orig3(user_input, session)

    orc3._handle_component_description = spy3
    orc3.handle_user_text("lipo 6S 5000mAh", _NoLLM())
    assert len(intercept3) > 0, "'lipo 6S 5000mAh' should be intercepted as battery component"


# ── CRITERIO DE FINALIZACIÓN ─────────────────────────────────────────────────


def test_criterio_battery_capacity_affects_autonomy(tmp_path):
    """CRITERIO 1: Autonomy changes when battery_capacity_wh changes."""
    from jarvis.core.calculation_engine import CalculationEngine

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    params_base = dict(project_state.current_parameters or {})
    params_base["motor_power_w"] = 50.0
    engine = CalculationEngine()

    # Without battery
    calc_no_battery = engine.build(params_base)

    # With 100Wh battery
    params_with = {**params_base, "battery_capacity_wh": 100.0}
    calc_with_battery = engine.build(params_with)

    # With 200Wh battery
    params_more = {**params_base, "battery_capacity_wh": 200.0}
    calc_more_battery = engine.build(params_more)

    assert calc_no_battery.autonomy_min is None or calc_no_battery.autonomy_min == 0
    assert calc_with_battery.autonomy_min is not None and calc_with_battery.autonomy_min > 0
    assert calc_more_battery.autonomy_min > calc_with_battery.autonomy_min


def test_criterio_battery_coherence_components_vs_params(tmp_path):
    """CRITERIO 2: After save, components['battery'] capacity == current_parameters['battery_capacity_wh']."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_battery_component_pending(orchestrator, tmp_path)

    orchestrator._handle_component_description("6S 5000mAh bateria", session)

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    param_val = saved.current_parameters.get("battery_capacity_wh")
    component_val = (
        saved.design_properties.components["battery"]
        .properties["battery_capacity_wh"]
        .value
    )
    assert param_val == pytest.approx(component_val, rel=1e-4)


def test_criterio_battery_no_llm_called(tmp_path):
    """CRITERIO 3: Full battery flow never calls the LLM."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    session = _setup_battery_component_pending(orchestrator, tmp_path)

    llm_calls: list[str] = []
    orig = orchestrator._semantic_adapter.adapt

    def patched(text, mode=None):
        llm_calls.append(text)
        return orig(text, mode)

    orchestrator._semantic_adapter.adapt = patched

    orchestrator._handle_component_description("sí", session)
    orchestrator._handle_component_description("6S 5000mAh bateria", session)
    orchestrator._handle_component_description("batería", session)

    assert not llm_calls, f"LLM called unexpectedly: {llm_calls}"


def test_criterio_battery_param_drives_energy_block_progress(tmp_path):
    """CRITERIO 4: After _set_battery_component, _block_progress_status('energy')
    changes from 'not_started' to 'in_progress'.

    Energy is now composite (Fase 4): both battery_capacity_wh + motor_power_w must be
    defined (params_ok=True) and at least one component must be present.
    After _set_battery_component writes battery_capacity_wh, params are complete;
    battery component is present but motors component is still missing → in_progress.
    """
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["energy"],
        "system_priority": ["energy"],
    })
    # Remove only battery_capacity_wh; keep motor_power_w so that once battery is added,
    # params_ok=True (both energy params present) → composite becomes in_progress.
    params = {k: v for k, v in (project_state.current_parameters or {}).items()
              if k not in ("battery_capacity_wh",)}
    params.setdefault("motor_power_w", 50.0)
    updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})

    status_before = orchestrator._block_progress_status("energy", dp, params)
    assert status_before == "not_started"  # battery_capacity_wh missing, no battery component

    spec = infer_component("100wh bateria", registry=aerial_registry)
    updated_state = set_battery_component(updated, spec, capacity_wh=100.0)

    status_after = orchestrator._block_progress_status(
        "energy", updated_state.design_properties, updated_state.current_parameters or {}
    )
    # battery_capacity_wh + motor_power_w → params_ok=True
    # battery component set, motors still missing → components_ok=False
    # composite: params_ok=True, components_ok=False → in_progress
    assert status_after == "in_progress"


def test_criterio_dse_gap_documented(tmp_path):
    """CRITERIO 5 (D4 closed): DSE _apply_delta with a direct mirrored key
    (battery_capacity_wh) now filters it out — value in result is unchanged.

    D4 closed the direct-key path. The _factor suffix path still exists
    (battery_capacity_wh_factor is not in COMPONENT_MIRRORED_PARAMS) but
    that is intentional: DSE factor-exploration is in-memory only and
    components_delta (DA2) will be the canonical path for component variations.
    """
    from jarvis.core.design_explorer import _apply_delta

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    # First, save battery via component path
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    spec = infer_component("100wh bateria", registry=aerial_registry)
    updated = set_battery_component(project_state, spec, capacity_wh=100.0)
    orchestrator.workspace_manager.save_state(updated)

    # D4: direct mirrored key in params_delta is filtered out
    base_params = dict(updated.current_parameters or {})
    delta = {"battery_capacity_wh": 200.0}
    new_params = _apply_delta(base_params, delta)

    assert new_params is not None
    # Direct key filtered → value unchanged from base_params
    assert new_params["battery_capacity_wh"] == pytest.approx(100.0)

    # Component also unchanged — no drift introduced by _apply_delta
    component_cap = (
        updated.design_properties.components["battery"]
        .properties.get("battery_capacity_wh")
    )
    if component_cap is not None:
        assert component_cap.value == pytest.approx(100.0), (
            "G1 CONFIRMED: components['battery'] shows 100Wh but current_parameters has 200Wh after DSE delta"
        )


# ── Fase 2.6.1 — Global component interception (idle mode) ───────────────────

def test_component_detection_works_outside_wizard(tmp_path):
    """CRITICAL: 'bateria 6S 5000mAh' in idle mode → routed to component flow, not LLM.

    This is the bug found in Fase 2.6 mini-validation:
      idle → "batería LiPo 6S 5000mAh" → wizard parse → battery_capacity_wh = 6.0 ❌
    After fix:
      idle → "batería LiPo 6S 5000mAh" → component → battery_capacity_wh = 111.0 ✓
    """
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    # Ensure we are in idle mode (fresh project, no wizard started)
    session = orchestrator.state_manager.runtime_state.session
    assert str(session.mode) in ("idle", "OrchestratorMode.IDLE", ""), \
        f"Expected idle mode, got {session.mode}"

    class _NoLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called")

    result = orchestrator.handle_user_text("bateria 6S 5000mAh", _NoLLM())

    assert result["status"] == "ok"
    assert result.get("action") == "component_description_saved"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    cap = saved.current_parameters.get("battery_capacity_wh")
    comp = saved.design_properties.components.get("battery")

    # Must NOT be the erroneous 6.0 parse
    assert cap is not None, "battery_capacity_wh missing from current_parameters"
    assert cap == pytest.approx(111.0, rel=1e-2), f"Expected 111.0 Wh, got {cap}"
    assert comp is not None, "components['battery'] not set"
    comp_cap = comp.properties.get("battery_capacity_wh")
    assert comp_cap is not None and comp_cap.value == pytest.approx(111.0, rel=1e-2)


def test_global_intercept_frame_in_idle(tmp_path):
    """Global intercept is not battery-only: 'carbono 450g' in idle → frame saved."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    class _NoLLM:
        def generate(self, *a, **kw):
            raise AssertionError("LLM must not be called")

    result = orchestrator.handle_user_text("carbono 450g", _NoLLM())

    assert result["status"] == "ok"
    assert result.get("action") == "component_description_saved"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = saved.design_properties.components.get("frame")
    assert frame is not None, "Frame component not saved"
    mass = frame.properties.get("mass_kg")
    assert mass is not None and mass.value == pytest.approx(0.45, rel=1e-2)


def test_pure_numeric_in_idle_not_intercepted(tmp_path):
    """'500' in idle → does NOT enter component flow (numeric guard active)."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    intercepted: list[str] = []
    original = orchestrator._handle_component_description

    def spy(user_input, session):
        intercepted.append(user_input)
        return original(user_input, session)

    orchestrator._handle_component_description = spy

    class _StubLLM:
        def generate(self, *a, **kw): return {}
        def interpret(self, *a, **kw): return {"action": "simulate", "parameters": {}}

    orchestrator.handle_user_text("500", _StubLLM())
    assert "500" not in intercepted, "Pure numeric '500' must not enter component intercept"


def test_low_completeness_in_idle_not_intercepted(tmp_path):
    """'lipo' alone (low completeness) in idle → NOT intercepted → falls through normally."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    intercepted: list[str] = []
    original = orchestrator._handle_component_description

    def spy(user_input, session):
        intercepted.append(user_input)
        return original(user_input, session)

    orchestrator._handle_component_description = spy

    class _StubLLM:
        def generate(self, *a, **kw): return {}
        def interpret(self, *a, **kw): return {"action": "simulate", "parameters": {}}

    orchestrator.handle_user_text("lipo", _StubLLM())
    assert "lipo" not in intercepted, "'lipo' alone (low) must not intercept"


def test_battery_without_units_not_intercepted(tmp_path):
    """'bateria 5000' (no units) in idle → NOT intercepted by global intercept.

    'bateria 5000' has no energy unit (no mAh, Wh, V, S) so _should_intercept_component
    returns None. This prevents mis-routing numeric-battery combos before confirming intent.
    """
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_drone_project(orchestrator, tmp_path)

    intercepted: list[str] = []
    original = orchestrator._handle_component_description

    def spy(user_input, sess):
        intercepted.append(user_input)
        return original(user_input, sess)

    orchestrator._handle_component_description = spy

    class _StubLLM:
        def generate(self, *a, **kw): return {}
        def interpret(self, *a, **kw): return {"action": "simulate", "parameters": {}}

    orchestrator.handle_user_text("bateria 5000", _StubLLM())
    assert "bateria 5000" not in intercepted, \
        "'bateria 5000' (no units) must not intercept — units guard must block it"


def test_component_intercept_respects_wizard_priority(tmp_path):
    """Non-regression: in DEFINE_MISSING_PARAMETERS mode, _should_intercept_component
    returns None (excluded), so the existing per-reason wizard intercept is used instead.
    Battery input must still save correctly — intercepted exactly once, not twice."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _setup_energy_pending(orchestrator, tmp_path)

    intercept_calls: list[str] = []
    original = orchestrator._handle_component_description

    def spy(user_input, sess):
        intercept_calls.append(user_input)
        return original(user_input, sess)

    orchestrator._handle_component_description = spy

    class _NoLLM:
        def generate(self, *a, **kw): raise AssertionError("LLM must not be called")

    result = orchestrator.handle_user_text("bateria 6S 5000mAh", _NoLLM())

    assert result.get("status") == "ok"
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.current_parameters.get("battery_capacity_wh") == pytest.approx(111.0, rel=1e-2)
    # _handle_component_description called exactly once — wizard path, not duplicated
    assert len(intercept_calls) == 1, \
        f"Expected exactly 1 component intercept call, got {len(intercept_calls)}"
