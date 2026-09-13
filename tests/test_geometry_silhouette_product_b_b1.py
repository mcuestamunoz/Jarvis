"""Silhouette Product B assist B1 (`B1-silhouette-product-b`, Path S1).

Covers implementation_contract_board_silhouette_product_b_b1.md §2:
  T1  No plate box -> verdict racimo; message no Product B
  T2  Estimated plate + all stack posed+mounted (10min-shaped fixture)
      -> silueta estimada (B*); copy has * / estimada; never "medido"
  T3  Same fixture but plate dims declared -> silueta (B) without *
  T4  Estimated plate but ESC missing pose -> racimo; suggests existing
      assist phrase; list-alone does not write
  T5  Trigger phrases resolve; unrelated phrases do not steal this bridge
  T6  IDLE list-alone never mutates ProjectState
  T7  Full pytest green; package 0.4.1 (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.silhouette_product_b_assist import (
    assess_silhouette,
    format_silhouette_checklist,
    is_silhouette_assist_trigger,
)
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _box_spec(key: str, length_mm: float, width_mm: float, height_mm: float, *, source: str = "declared") -> ComponentSpec:
    return ComponentSpec(
        suggested_key=key, completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", confidence=0.9, source=source),
            "width_mm": PropertyValue(value=width_mm, unit="mm", confidence=0.9, source=source),
            "height_mm": PropertyValue(value=height_mm, unit="mm", confidence=0.9, source=source),
        },
    )


def _full_boxed_stack_components(
    plate_source: str = "estimated_temporary", *, posed: bool = True, mounted: bool = True
) -> dict:
    """10min-shaped fixture: boxed plate + 4 boxed stack subjects, each
    optionally posed respecto a frame_plate and/or mounted on it."""
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box_spec("frame_plate", 120.0, 55.0, 2.0, source=plate_source),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
        "flight_controller": _box_spec("flight_controller", 44.0, 84.0, 12.0),
        "battery": _box_spec("battery", 105.0, 35.0, 29.0),
        "sensors": _box_spec("sensors", 40.0, 40.0, 12.0),
    }
    for key in ("esc", "flight_controller", "battery", "sensors"):
        update = {}
        if posed:
            update["declared_box_pose"] = DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0)
        if mounted:
            update["mounted_on"] = "frame_plate"
        if update:
            components[key] = components[key].model_copy(update=update)
    return components


# ── T1: no plate box -> racimo; message never mentions Product B ────────


def test_t1_no_plate_box_yields_racimo():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(suggested_key="frame_plate", component_type="structure_part", parent_key="frame"),
        "esc": _box_spec("esc", 45.6, 44.0, 8.0),
    }
    assessment = assess_silhouette(components)
    assert assessment.verdict == "racimo"
    message = format_silhouette_checklist(assessment)
    assert "racimo" in message.lower()
    assert "product b" not in message.lower()
    assert "silueta" not in message.lower()


def test_t1_ambiguous_two_plates_still_racimo_never_guessed():
    components = _full_boxed_stack_components(posed=False, mounted=False)
    components["frame_plate_2"] = _box_spec("frame_plate_2", 80.0, 40.0, 3.0)
    assessment = assess_silhouette(components)
    assert assessment.verdict == "racimo"
    message = format_silhouette_checklist(assessment)
    assert "varias placas" in message.lower()


# ── T2: estimated plate + full stack -> silueta estimada (B*) ───────────


def test_t2_estimated_plate_full_stack_yields_silueta_estimada():
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    assessment = assess_silhouette(components)
    assert assessment.verdict == "silueta_estimada"
    message = format_silhouette_checklist(assessment)
    assert "*" in message
    assert "estimada" in message.lower()
    assert "medido" not in message.lower()
    assert "verificado" not in message.lower()


# ── T3: same fixture, declared plate -> silueta (B), no * required ──────


def test_t3_declared_plate_full_stack_yields_silueta_no_star():
    components = _full_boxed_stack_components(plate_source="declared")
    assessment = assess_silhouette(components)
    assert assessment.verdict == "silueta"
    message = format_silhouette_checklist(assessment)
    assert "silueta (b)" in message.lower()
    assert "silueta estimada" not in message.lower()


# ── T4: estimated plate, ESC missing pose -> racimo; suggests phrase ────


def test_t4_missing_esc_pose_yields_racimo_with_existing_assist_suggestion():
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    components["esc"] = components["esc"].model_copy(update={"declared_box_pose": None})
    assessment = assess_silhouette(components)
    assert assessment.verdict == "racimo"
    rows_by_gate = {r.gate: r for r in assessment.rows}
    assert rows_by_gate["pose_esc"].status == "missing"
    assert rows_by_gate["pose_esc"].suggest == "apilar en placa"
    message = format_silhouette_checklist(assessment)
    assert "apilar en placa" in message


def test_t4_missing_mount_only_yields_racimo_with_mount_suggestion():
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    components["sensors"] = components["sensors"].model_copy(update={"mounted_on": None})
    assessment = assess_silhouette(components)
    assert assessment.verdict == "racimo"
    rows_by_gate = {r.gate: r for r in assessment.rows}
    assert rows_by_gate["montaje_sensors"].status == "missing"
    assert rows_by_gate["montaje_sensors"].suggest == "montajes estándar"


def test_t4_absent_subject_never_demanded():
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    del components["sensors"]
    assessment = assess_silhouette(components)
    gates = {r.gate for r in assessment.rows}
    assert not any(gate.endswith("_sensors") for gate in gates)
    assert assessment.verdict == "silueta_estimada"


def test_t4_boxless_subject_never_demanded_either():
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    components["sensors"] = ComponentSpec(
        suggested_key="sensors", completeness="medium",
        properties={"gps_model": PropertyValue(value="here3", confidence=0.9)},
    )
    assessment = assess_silhouette(components)
    gates = {r.gate for r in assessment.rows}
    assert not any(gate.endswith("_sensors") for gate in gates)
    assert assessment.verdict == "silueta_estimada"


# ── Warn-only rows never demote an otherwise-earned verdict ─────────────


def test_visor_x_and_pose_cycle_rows_are_warn_only():
    components = _full_boxed_stack_components(plate_source="declared")
    assessment = assess_silhouette(components)
    rows_by_gate = {r.gate: r for r in assessment.rows}
    assert rows_by_gate["visor_x_wb"].status == "n/a"
    assert rows_by_gate["pose_cycle"].status == "n/a"
    assert assessment.verdict == "silueta"


# ── T5: trigger phrases resolve; unrelated phrases do not steal this bridge ──


def test_t5_trigger_phrases_resolve():
    assert is_silhouette_assist_trigger("silueta")
    assert is_silhouette_assist_trigger("¿parece un dron?")
    assert is_silhouette_assist_trigger("parece un dron")
    assert is_silhouette_assist_trigger("Product B")
    assert is_silhouette_assist_trigger("PRODUCT B")


def test_t5_unrelated_phrases_do_not_trigger():
    assert not is_silhouette_assist_trigger("montajes estándar")
    assert not is_silhouette_assist_trigger("layout pack")
    assert not is_silhouette_assist_trigger("apilar en placa")
    assert not is_silhouette_assist_trigger("declara el esc a 5 mm en z respecto a frame_plate")


# ── T6: suggest-only never mutates ProjectState ──────────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "silhouette product b b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_components = {**ps.design_properties.components, **components}
    updated_dp = ps.design_properties.model_copy(update={"components": updated_components})
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_t6_idle_checklist_never_writes(tmp_path: Path):
    components = _full_boxed_stack_components(plate_source="estimated_temporary")
    components["esc"] = components["esc"].model_copy(update={"declared_box_pose": None})
    orch = _orch_with_components(tmp_path, components)

    before = orch.state_manager.load_active_project(orch.workspace_manager)
    result = orch.handle_user_text("silueta", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "silhouette_checklist"

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.design_properties.components["esc"].declared_box_pose is None
    assert before.design_properties.components == after.design_properties.components


def test_t6_idle_full_stack_reports_silhouette_and_never_writes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _full_boxed_stack_components(plate_source="declared"))
    result = orch.handle_user_text("parece un dron", _RefuseLLM())
    assert result["status"] == "ok"
    assert "silueta (b)" in result["message"].lower()


# ── T8-style: no project-specific literals in the assist module ─────────


def test_module_has_no_project_specific_literals():
    import inspect

    import jarvis.core.silhouette_product_b_assist as mod

    source = inspect.getsource(mod)
    for literal in ("my5", "hglrc", "10-min", "5min", "autonomía", "autonomia"):
        assert literal not in source.lower(), f"found project-specific literal: {literal!r}"
