"""Fit attestation B1 (Engineer-declared verified).

Covers implementation_contract_geometry_fit_attestation_b1.md §3-3.4:
  T0  Overlap pair -> attest succeeds; fingerprint stable across repeats
  T1  no_overlap -> attest raises ValueError; no field set
  T2  pose_incomplete -> attest raises ValueError
  T3  Pose write changing Δmm on the child -> attestation cleared
  T4  Envelope write on the child OR on its origin, changing L/W/H ->
      attestation cleared; an unrelated component's envelope write does
      NOT clear it
  T5  Board fields include "verificación" when attested; "sobres" still
      contains "no verificado" (screening copy never renamed)
  T6  _block_progress_status unaffected by an attestation being present
  T7  Orchestrator IDLE "declaro verificado el esc" / "quito la
      verificación del esc" with _RefuseLLM -> writer path only, LLM never
      called
  T8  format_screening("overlap") golden string unchanged
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.component_writers import (
    compute_fit_attestation_fingerprint,
    set_component_declared_box_envelope,
    set_component_declared_box_pose,
    set_component_declared_fit_attestation,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.pose_envelope_screening import Screening, format_screening
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import _geometry_from_spec, project_spatial_nodes

_FORBIDDEN_TOKENS = ("cabe", "no cabe", "VERIFIED", "ensamblado", "misfit geométrico")


def _box(length: float, width: float, height: float, pose: DeclaredBoxPose | None = None) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="x", completeness="high", source="declared",
        properties={
            "length_mm": PropertyValue(value=length, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=width, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=height, unit="mm", source="declared"),
        },
        declared_box_pose=pose,
    )


def _fc() -> ComponentSpec:
    return _box(44.0, 84.0, 12.0)


def _overlapping_esc() -> ComponentSpec:
    return _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0, y_mm=0.0, z_mm=0.0))


def _no_overlap_esc() -> ComponentSpec:
    return _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=200.0, y_mm=0.0, z_mm=0.0))


def _incomplete_pose_esc() -> ComponentSpec:
    return _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0))


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _no_forbidden(text: str) -> bool:
    lower = text.lower()
    return not any(tok.lower() in lower for tok in _FORBIDDEN_TOKENS)


def test_t0_overlap_attest_succeeds_fingerprint_stable():
    state = _state({"flight_controller": _fc(), "esc": _overlapping_esc()})
    updated = set_component_declared_fit_attestation(state, "esc", attest=True)
    attestation = updated.design_properties.components["esc"].declared_fit_attestation
    assert attestation is not None
    assert attestation.attested_at

    esc_spec = updated.design_properties.components["esc"]
    pose = esc_spec.declared_box_pose
    child_geometry = _geometry_from_spec(esc_spec)
    origin_geometry = _geometry_from_spec(updated.design_properties.components["flight_controller"])
    expected = compute_fit_attestation_fingerprint(pose, child_geometry, origin_geometry)
    assert attestation.fingerprint == expected
    # Recomputing from the same inputs is stable (no randomness/hash salt).
    assert compute_fit_attestation_fingerprint(pose, child_geometry, origin_geometry) == expected


def test_t1_no_overlap_attest_raises_no_field_set():
    state = _state({"flight_controller": _fc(), "esc": _no_overlap_esc()})
    try:
        set_component_declared_fit_attestation(state, "esc", attest=True)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert _no_forbidden(str(exc))
    assert state.design_properties.components["esc"].declared_fit_attestation is None


def test_t2_pose_incomplete_attest_raises():
    state = _state({"flight_controller": _fc(), "esc": _incomplete_pose_esc()})
    try:
        set_component_declared_fit_attestation(state, "esc", attest=True)
        assert False, "expected ValueError"
    except ValueError:
        pass
    assert state.design_properties.components["esc"].declared_fit_attestation is None


def test_t3_pose_write_changing_delta_clears_attestation():
    state = _state({"flight_controller": _fc(), "esc": _overlapping_esc()})
    attested = set_component_declared_fit_attestation(state, "esc", attest=True)
    assert attested.design_properties.components["esc"].declared_fit_attestation is not None

    moved = set_component_declared_box_pose(
        attested, "esc",
        DeclaredBoxPose(origin_key="flight_controller", x_mm=6.0, y_mm=0.0, z_mm=0.0),
    )
    assert moved.design_properties.components["esc"].declared_fit_attestation is None


def test_t4_envelope_write_on_child_or_origin_clears_never_unrelated():
    plate = _box(150.0, 150.0, 4.0)
    battery = _box(80.0, 34.0, 22.0, DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=0.0))
    unrelated = _box(1.0, 1.0, 1.0)
    state = _state({"frame_plate": plate, "battery": battery, "sensors": unrelated})
    attested = set_component_declared_fit_attestation(state, "battery", attest=True)
    assert attested.design_properties.components["battery"].declared_fit_attestation is not None

    # Own envelope write clears own attestation.
    own_write = set_component_declared_box_envelope(attested, "battery", 81.0, 34.0, 22.0)
    assert own_write.design_properties.components["battery"].declared_fit_attestation is None

    # Origin's envelope write clears the child's attestation.
    origin_write = set_component_declared_box_envelope(attested, "frame_plate", 160.0, 150.0, 4.0)
    assert origin_write.design_properties.components["battery"].declared_fit_attestation is None

    # An unrelated component's envelope write does NOT clear it.
    unrelated_write = set_component_declared_box_envelope(attested, "sensors", 2.0, 2.0, 2.0)
    assert unrelated_write.design_properties.components["battery"].declared_fit_attestation is not None


def test_t5_board_fields_show_verificacion_sobres_still_no_verificado():
    state = _state({"flight_controller": _fc(), "esc": _overlapping_esc()})
    attested = set_component_declared_fit_attestation(state, "esc", attest=True)
    nodes = project_spatial_nodes(attested)
    esc_node = next(n for n in nodes if n["id"] == "esc")
    sobres = next(f for f in esc_node["fields"] if f["label"] == "sobres")
    assert "no verificado" in sobres["value"]
    verificacion = next(f for f in esc_node["fields"] if f["label"] == "verificación")
    assert "Declarado verificado por el Engineer" in verificacion["value"]
    assert "no es una comprobación geométrica de Jarvis" in verificacion["value"]

    # Cleared (stale) attestation: no leftover "verificación" field.
    moved = set_component_declared_box_pose(
        attested, "esc",
        DeclaredBoxPose(origin_key="flight_controller", x_mm=6.0, y_mm=0.0, z_mm=0.0),
    )
    nodes2 = project_spatial_nodes(moved)
    esc_node2 = next(n for n in nodes2 if n["id"] == "esc")
    assert all(f["label"] != "verificación" for f in esc_node2["fields"])


def test_t6_block_progress_status_unaffected_by_attestation():
    arch_blocks = ["propulsion", "energy", "structure", "control"]
    components = {
        "motors": _box(1, 1, 1), "propellers": _box(1, 1, 1), "esc": _overlapping_esc(),
        "battery": _box(1, 1, 1), "frame": _box(1, 1, 1),
        "flight_controller": _fc(), "sensors": _box(1, 1, 1),
    }
    params = {
        "motor_count": 4, "per_motor_max_thrust_n": 20.0,
        "battery_capacity_wh": 100.0, "motor_power_w": 50.0,
    }
    dp_bare = DesignProperties(
        system_blocks=arch_blocks, system_priority=arch_blocks, components=components,
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=dp_bare,
    )
    attested = set_component_declared_fit_attestation(state, "esc", attest=True)
    for block in arch_blocks:
        status_bare = JarvisOrchestrator._block_progress_status(block, dp_bare, params)
        status_attested = JarvisOrchestrator._block_progress_status(
            block, attested.design_properties, params
        )
        assert status_bare == status_attested


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def test_t7_idle_declaro_verificado_and_quito_verificacion_no_llm(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "fit attest test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(
        update={"components": {"flight_controller": _fc(), "esc": _overlapping_esc()}}
    )
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))

    result = orch.handle_user_text("declaro verificado el esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Declarado verificado por el Engineer" in result["message"]
    reloaded = orch.state_manager.load_active_project(orch.workspace_manager)
    assert reloaded.design_properties.components["esc"].declared_fit_attestation is not None

    result2 = orch.handle_user_text("quito la verificación del esc", _RefuseLLM())
    assert result2["status"] == "ok"
    reloaded2 = orch.state_manager.load_active_project(orch.workspace_manager)
    assert reloaded2.design_properties.components["esc"].declared_fit_attestation is None


def test_t7b_idle_declaro_verificado_refuses_no_overlap_subject_no_llm(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "fit attest refuse test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(
        update={"components": {"flight_controller": _fc(), "esc": _no_overlap_esc()}}
    )
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))

    result = orch.handle_user_text("declaro verificado el esc", _RefuseLLM())
    assert result["status"] == "error"
    assert _no_forbidden(result["message"])
    reloaded = orch.state_manager.load_active_project(orch.workspace_manager)
    assert reloaded.design_properties.components["esc"].declared_fit_attestation is None


def test_t8_format_screening_overlap_golden_string_unchanged():
    screening = Screening(status="overlap", missing_axes=())
    assert format_screening(screening) == (
        "Los sobres se solapan en los ejes declarados — screening, no verificado."
    )
