"""Structure A — masa honesta + compatibilidad de clase.

implementation_contract_structure_a.md

Walk leak: iterate "PVC 200g" registered a material string only;
structure_mass_override_kg stayed 0.65. This file locks the fix (both
iterate_interactive_session.py leak points) plus the new frame
size_class_inch class-compatibility screening (LEVEL A — never a geometric
fit proof, never VERIFIED, never "cabe"/"no cabe").
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import set_frame_material
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.domains.aerial import extract_frame_properties
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "dron de prueba estructura A",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = set_frame_material(ps, 0.65, "fibra de carbono")
    o.workspace_manager.save_state(ps)
    return o


# ── §2.1 masa: awaiting-material call site (iterate_interactive_session.py:294) ──


def test_walk_pvc_200g_awaiting_material_turn_writes_mass(tmp_path: Path):
    """The literal walk utterance, via the two-turn 'cambiar material' ->
    'PVC 200g' path (the _awaiting_material_value branch)."""
    o = _fresh(tmp_path)
    o.handle_user_text("modifica el peso del sistema", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    o.handle_user_text("material", _RefuseLLM())
    o.handle_user_text("cambiar material", _RefuseLLM())
    o.handle_user_text("PVC 200g", _RefuseLLM())
    o.handle_user_text("ninguna", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    result = o.handle_user_text("sí", _RefuseLLM())
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters.get("structure_mass_override_kg") == 0.2
    frame = ps.design_properties.components["frame"]
    assert frame.properties["mass_kg"].value == 0.2
    assert frame.properties["material"].value == "pvc"


# ── §2.1 masa: strategy-embedded call site (iterate_interactive_session.py:411) ──


def test_walk_pvc_200g_strategy_embedded_turn_writes_mass(tmp_path: Path):
    """Same fix, the other Gap-1 branch: the material name (with grams)
    arrives as the step-2 strategy answer directly, not a follow-up turn."""
    o = _fresh(tmp_path)
    o.handle_user_text("modifica el peso del sistema", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    o.handle_user_text("material", _RefuseLLM())
    # Answer the "¿Cómo quieres aplicar el cambio?" strategy step directly
    # with the material+mass text, instead of "cambiar material" first.
    o.handle_user_text("PVC 200g", _RefuseLLM())
    o.handle_user_text("ninguna", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    result = o.handle_user_text("sí", _RefuseLLM())
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters.get("structure_mass_override_kg") == 0.2
    frame = ps.design_properties.components["frame"]
    assert frame.properties["mass_kg"].value == 0.2


# ── N1 hotfix: size/material-only update must not delete an existing mass ──
# implementation_contract_structure_a_n1_hotfix.md — set_frame_material must
# mirror structure_mass_override_kg from the MERGED props, not the mass_kg
# argument, or a size-only iterate turn silently deletes an already-declared
# mass override.


def test_walk_pvc_5_pulgadas_preserves_existing_mass_override(tmp_path: Path):
    o = _fresh(tmp_path)
    ps_before = o.state_manager.load_active_project(o.workspace_manager)
    calc_before = CalculationEngine().build(ps_before.current_parameters)

    o.handle_user_text("modifica el peso del sistema", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    o.handle_user_text("material", _RefuseLLM())
    o.handle_user_text("cambiar material", _RefuseLLM())
    o.handle_user_text("pvc 5 pulgadas", _RefuseLLM())
    o.handle_user_text("ninguna", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    result = o.handle_user_text("sí", _RefuseLLM())
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters.get("structure_mass_override_kg") == 0.65
    frame = ps.design_properties.components["frame"]
    assert frame.properties["mass_kg"].value == 0.65
    assert frame.properties["size_class_inch"].value == 5.0
    assert frame.properties["material"].value == "pvc"

    calc_after = CalculationEngine().build(ps.current_parameters)
    assert calc_after.total_mass_kg == calc_before.total_mass_kg


# ── Acquisition regression (component-description path, unchanged) ──────────


def test_acquisition_carbono_450g_still_045kg(tmp_path: Path):
    o = _fresh(tmp_path)
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)
    result = o.handle_user_text("carbono 450g", _RefuseLLM())
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert ps.current_parameters.get("structure_mass_override_kg") == 0.45
    assert ps.design_properties.components["frame"].properties["mass_kg"].value == 0.45


# ── Material-only: no invented mass ──────────────────────────────────────────


def test_material_only_pvc_no_grams_does_not_invent_mass(tmp_path: Path):
    o = _fresh(tmp_path)
    ps_before = o.state_manager.load_active_project(o.workspace_manager)
    override_before = ps_before.current_parameters.get("structure_mass_override_kg")

    o.handle_user_text("modifica el peso del sistema", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    o.handle_user_text("material", _RefuseLLM())
    o.handle_user_text("cambiar material", _RefuseLLM())
    o.handle_user_text("pvc", _RefuseLLM())
    o.handle_user_text("ninguna", _RefuseLLM())
    o.handle_user_text("sí", _RefuseLLM())
    result = o.handle_user_text("sí", _RefuseLLM())
    assert result["status"] == "ok"

    ps = o.state_manager.load_active_project(o.workspace_manager)
    # Override must stay exactly what it was — no invented mass from a
    # material-only declaration (PVC's real library density is 1380 kg/m3;
    # this is not "PVC has no physical data", it's simply no grams given).
    assert ps.current_parameters.get("structure_mass_override_kg") == override_before


# ── extract_frame_properties: no cross-invention ─────────────────────────────


def test_extract_frame_properties_mass_does_not_invent_size_class():
    props = extract_frame_properties("pvc 200g")
    assert "size_class_inch" not in props
    assert props["mass_kg"].value == 0.2
    assert props["material"].value == "pvc"


def test_extract_frame_properties_size_does_not_invent_mass():
    props = extract_frame_properties("frame 5 pulgadas")
    assert "mass_kg" not in props
    assert props["size_class_inch"].value == 5.0


def test_extract_frame_properties_ignores_millimeters():
    props = extract_frame_properties("frame 250mm")
    assert "size_class_inch" not in props
    assert "mass_kg" not in props


# ── §2.2 class-compatibility screening ───────────────────────────────────────


_PRIORITY = ["propulsion", "energy", "structure", "control"]


def _propulsion_params(**overrides):
    params = {
        "vehicle_type": "dron",
        "payload_kg": 1.0,
        "motor_count": 4,
        "per_motor_max_thrust_n": 12.0,
        "battery_capacity_wh": 74.0,
        "motor_power_w": 220.0,
        "structure_mass_factor": 0.5,
        "safety_factor": 1.2,
    }
    params.update(overrides)
    return params


def _state(*, diameter_in=None, size_class_inch=None, frame_extra=None, params_extra=None):
    """Minimal ProjectState-shaped fixture: bound propeller (optional
    diameter) + frame (mass+material, optional size_class_inch)."""
    components = {
        "motors": ComponentSpec(
            suggested_key="motors", component_type="propulsion_active", completeness="high",
            properties={"thrust_n": PropertyValue(value=12.0, unit="N")},
        ),
    }
    if diameter_in is not None:
        components["propellers"] = ComponentSpec(
            suggested_key="propellers", component_type="propulsion_passive", completeness="high",
            properties={"diameter_in": PropertyValue(value=diameter_in, unit="in")},
        )
    frame_props = {
        "mass_kg": PropertyValue(value=0.5, unit="kg"),
        "material": PropertyValue(value="fibra de carbono"),
    }
    if size_class_inch is not None:
        frame_props["size_class_inch"] = PropertyValue(value=size_class_inch, unit="in")
    if frame_extra:
        frame_props.update(frame_extra)
    components["frame"] = ComponentSpec(
        suggested_key="frame", component_type="structure", completeness="high",
        properties=frame_props,
    )
    params = _propulsion_params(**(params_extra or {}))
    if diameter_in is not None:
        params["propeller_diameter_in"] = diameter_in
    return SimpleNamespace(
        current_parameters=params,
        parsed_constraints={},
        latest_results={"simulation": {"status": "pass", "can_fly": True}, "calculations": {}},
        design_properties=SimpleNamespace(
            system_defined=True,
            system_blocks=list(_PRIORITY),
            system_priority=list(_PRIORITY),
            components=components,
        ),
    )


def test_misfit_7in_prop_5in_class_gap_and_incomplete_thrust_unchanged():
    state = _state(diameter_in=7.0, size_class_inch=5.0)
    result = build_engineering_readiness(state)

    gap_types = [g.gap_type for g in result.gaps]
    assert "GAP-FRAME-PROP-SIZE" in gap_types
    assert "GAP-FRAME-SIZE-MISSING" not in gap_types
    misfit_gap = next(g for g in result.gaps if g.gap_type == "GAP-FRAME-PROP-SIZE")
    assert misfit_gap.severity == "MEDIUM"
    assert misfit_gap.blocks == ["structure"]

    status = JarvisOrchestrator._block_progress_status(
        "structure", state.design_properties, state.current_parameters
    )
    assert status != "complete"

    # Forbidden copy: never a fit/misfit claim, never VERIFIED.
    forbidden = ("cabe", "verificado", "verified", "does not fit", "fits")
    title_lower = misfit_gap.title.lower()
    for word in forbidden:
        assert word not in title_lower

    # Thrust identical with vs without the class property on the same
    # prop/motor fixture — size_class_inch never enters CalculationEngine.
    engine = CalculationEngine()
    with_class = engine.build(state.current_parameters)
    without_class_state = _state(diameter_in=7.0, size_class_inch=None)
    without_class = engine.build(without_class_state.current_parameters)
    assert with_class.available_total_thrust_n == without_class.available_total_thrust_n
    assert with_class.required_thrust_n == without_class.required_thrust_n


def test_class_compatible_5in_prop_5in_class_no_gap_structure_complete():
    state = _state(diameter_in=5.0, size_class_inch=5.0)
    result = build_engineering_readiness(state)

    gap_types = [g.gap_type for g in result.gaps]
    assert "GAP-FRAME-PROP-SIZE" not in gap_types
    assert "GAP-FRAME-SIZE-MISSING" not in gap_types

    status = JarvisOrchestrator._block_progress_status(
        "structure", state.design_properties, state.current_parameters
    )
    assert status == "complete"


def test_missing_class_5in_prop_no_class_gap_not_misfit_not_copied():
    state = _state(diameter_in=5.0, size_class_inch=None)
    result = build_engineering_readiness(state)

    gap_types = [g.gap_type for g in result.gaps]
    assert "GAP-FRAME-SIZE-MISSING" in gap_types
    assert "GAP-FRAME-PROP-SIZE" not in gap_types
    missing_gap = next(g for g in result.gaps if g.gap_type == "GAP-FRAME-SIZE-MISSING")
    assert missing_gap.severity == "MEDIUM"
    assert missing_gap.blocks == ["structure"]

    status = JarvisOrchestrator._block_progress_status(
        "structure", state.design_properties, state.current_parameters
    )
    assert status != "complete"

    # Class must never be silently copied from the propeller's diameter.
    frame = state.design_properties.components["frame"]
    assert "size_class_inch" not in frame.properties


def test_no_propeller_diameter_structure_still_complete_no_gap():
    state = _state(diameter_in=None, size_class_inch=None)
    result = build_engineering_readiness(state)

    gap_types = [g.gap_type for g in result.gaps]
    assert "GAP-FRAME-SIZE-MISSING" not in gap_types
    assert "GAP-FRAME-PROP-SIZE" not in gap_types

    status = JarvisOrchestrator._block_progress_status(
        "structure", state.design_properties, state.current_parameters
    )
    assert status == "complete"
