"""Geometry assembly fit B1-min (posed box-box screening).

Covers implementation_contract_geometry_assembly_fit_cabe_b1.md §3-3.4:
  T0  Pose x_mm=5 only -> pose_incomplete; formatted text has "incompleta"
      and not "cabe"/"VERIFIED"
  T1  Pose (5, 0, 0) -> overlap (live-shaped numbers; inclusive)
  T2  Pose (200, 0, 0) -> no_overlap
  T3  Origin disk / missing origin -> origin_unusable
  T4  Child disk -> child_not_box (no cylinder path)
  T5  project_spatial_nodes ESC fields include "sobres" with incomplete
      copy; no new declaredBoxPose keys
  T6  _block_progress_status propulsion/energy twin: incomplete vs
      complete pose, same PASS (not flipped by screening)
  T7  Orchestrator IDLE "cabe"/"¿cabe el esc?" with _RefuseLLM returns
      screening text; LLM not called

(T8 — ui/ and scene3dLayout.ts empty diff — is a report-level git check,
not a pytest test; recorded in the implementation report instead.)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.pose_envelope_screening import format_screening, screen_posed_envelope
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

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


def _disk(diameter: float, pose: DeclaredBoxPose | None = None) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="x", completeness="high", source="declared",
        properties={"diameter_mm": PropertyValue(value=diameter, unit="mm", source="declared")},
        declared_box_pose=pose,
    )


def _fc() -> ComponentSpec:
    return _box(44.0, 84.0, 12.0)


def _no_forbidden(text: str) -> bool:
    lower = text.lower()
    return not any(tok.lower() in lower for tok in _FORBIDDEN_TOKENS)


def test_t0_incomplete_pose_x_only():
    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0))
    components = {"flight_controller": _fc(), "esc": esc}
    screening = screen_posed_envelope(esc, components)
    assert screening.status == "pose_incomplete"
    assert set(screening.missing_axes) == {"y", "z"}
    text = format_screening(screening)
    assert "incompleta" in text
    assert _no_forbidden(text)


def test_t1_pose_5_0_0_overlaps_inclusive():
    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0, y_mm=0.0, z_mm=0.0))
    components = {"flight_controller": _fc(), "esc": esc}
    screening = screen_posed_envelope(esc, components)
    assert screening.status == "overlap"
    assert _no_forbidden(format_screening(screening))


def test_t2_pose_200_0_0_no_overlap():
    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=200.0, y_mm=0.0, z_mm=0.0))
    components = {"flight_controller": _fc(), "esc": esc}
    screening = screen_posed_envelope(esc, components)
    assert screening.status == "no_overlap"
    assert _no_forbidden(format_screening(screening))


def test_t3_origin_disk_and_missing_origin_are_origin_unusable():
    prop = _disk(127.0, DeclaredBoxPose(origin_key="motors", x_mm=1.0, y_mm=1.0, z_mm=1.0))
    motors_disk = _disk(27.9)
    screening = screen_posed_envelope(prop, {"motors": motors_disk, "propellers": prop})
    assert screening.status == "origin_unusable"
    assert _no_forbidden(format_screening(screening))

    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="does_not_exist", x_mm=1.0, y_mm=1.0, z_mm=1.0))
    screening2 = screen_posed_envelope(esc, {"esc": esc})
    assert screening2.status == "origin_unusable"


def test_t4_child_disk_is_child_not_box_never_cylinder():
    prop = _disk(127.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=1.0, y_mm=1.0, z_mm=1.0))
    components = {"flight_controller": _fc(), "propellers": prop}
    screening = screen_posed_envelope(prop, components)
    assert screening.status == "child_not_box"
    assert _no_forbidden(format_screening(screening))


def test_t5_board_fields_show_sobres_no_new_dto_keys():
    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0))
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={"flight_controller": _fc(), "esc": esc}),
    )
    nodes = project_spatial_nodes(state)
    esc_node = next(n for n in nodes if n["id"] == "esc")
    sobres = next(f for f in esc_node["fields"] if f["label"] == "sobres")
    assert "incompleta" in sobres["value"]
    assert _no_forbidden(sobres["value"])
    # Machine DTO unchanged — still exactly originKey/xMm, no screening keys added.
    assert set(esc_node["declaredBoxPose"].keys()) == {"originKey", "xMm"}


def test_t6_twin_block_progress_status_unaffected_by_screening():
    arch_blocks = ["propulsion", "energy", "structure", "control"]
    components_incomplete = {
        "motors": _box(1, 1, 1), "propellers": _box(1, 1, 1), "esc": _box(50.0, 21.6, 12.0,
            DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0)),
        "battery": _box(1, 1, 1), "frame": _box(1, 1, 1),
        "flight_controller": _fc(), "sensors": _box(1, 1, 1),
    }
    components_complete_pose = dict(components_incomplete)
    components_complete_pose["esc"] = _box(
        50.0, 21.6, 12.0,
        DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0, y_mm=0.0, z_mm=0.0),
    )
    params = {
        "motor_count": 4, "per_motor_max_thrust_n": 20.0,
        "battery_capacity_wh": 100.0, "motor_power_w": 50.0,
    }
    dp_incomplete = DesignProperties(
        system_blocks=arch_blocks, system_priority=arch_blocks, components=components_incomplete,
    )
    dp_complete = DesignProperties(
        system_blocks=arch_blocks, system_priority=arch_blocks, components=components_complete_pose,
    )
    for block in arch_blocks:
        status_incomplete = JarvisOrchestrator._block_progress_status(block, dp_incomplete, params)
        status_complete = JarvisOrchestrator._block_progress_status(block, dp_complete, params)
        assert status_incomplete == status_complete


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def test_t7_idle_cabe_returns_screening_text_no_llm(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "fit test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = _box(50.0, 21.6, 12.0, DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0, y_mm=0.0, z_mm=0.0))
    dp = ps.design_properties.model_copy(
        update={"components": {"flight_controller": _fc(), "esc": esc}}
    )
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))

    result = orch.handle_user_text("cabe el esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "solapan" in result["message"]
    assert _no_forbidden(result["message"])

    result2 = orch.handle_user_text("¿cabe el esc?", _RefuseLLM())
    assert "solapan" in result2["message"]
