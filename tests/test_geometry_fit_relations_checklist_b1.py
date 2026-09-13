"""Fit relations checklist B1 (`B1-fit-relations-checklist`).

Covers implementation_contract_geometry_fit_relations_checklist_b1.md §2:

Part A — silhouette footer scoping:
  A1  Silhouette B*/B footer contains "este checklist" (checklist-scoped
      copy), never a bare project-global "sin problemas"/"pendiente"
      claim

Part B — fit relations checklist:
  R1  No plate box -> plate relations blocked; no false "listo para
      declarar verificado"
  R2  FC posed+boxed on an ESTIMATED_TEMPORARY plate -> estimated_dims,
      blocked (not ready to attest)
  R3  FC posed+boxed on a declared plate + screening overlap -> ready,
      suggest an attest phrase that parses via the real trigger/subject
      resolution used by the live IDLE bridge
  R4  A valid (fingerprint-matching) attestation present -> attested
  R5  motors/propellers -> n_a_disk for screening; mount absence still
      shows as an independent warn annotation
  R6  Triggers resolve; silueta/montajes estándar/parece un dron never
      steal this bridge
  R7  IDLE list-alone never mutates ProjectState / never calls the
      attestation writer
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import compute_fit_attestation_fingerprint
from jarvis.core.fit_relations_assist import (
    assess_fit_relations,
    format_fit_relations_checklist,
    is_fit_relations_assist_trigger,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.silhouette_product_b_assist import (
    assess_silhouette,
    format_silhouette_checklist,
)
from jarvis.schemas.action_schema import (
    ComponentSpec,
    DeclaredBoxPose,
    DeclaredFitAttestation,
    PropertyValue,
)
from jarvis.workspace.spatial_board import _geometry_from_spec


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _box(key: str, length_mm: float, width_mm: float, height_mm: float, *, source: str = "declared") -> ComponentSpec:
    return ComponentSpec(
        suggested_key=key, completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", confidence=0.9, source=source),
            "width_mm": PropertyValue(value=width_mm, unit="mm", confidence=0.9, source=source),
            "height_mm": PropertyValue(value=height_mm, unit="mm", confidence=0.9, source=source),
        },
    )


def _posed_fc(plate_source: str = "declared") -> dict:
    pose = DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=7.0)
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box("frame_plate", 120.0, 55.0, 2.0, source=plate_source),
        "flight_controller": _box("flight_controller", 44.0, 84.0, 12.0).model_copy(
            update={"declared_box_pose": pose}
        ),
    }


# ── Part A: silhouette footer scoping ───────────────────────────────────


def test_a1_silhouette_estimada_footer_scoped_to_checklist():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box("frame_plate", 120.0, 55.0, 2.0, source="estimated_temporary"),
        "esc": _box("esc", 45.6, 44.0, 8.0).model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0),
            "mounted_on": "frame_plate",
        }),
        "flight_controller": _box("flight_controller", 44.0, 84.0, 12.0).model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=7.0),
            "mounted_on": "frame_plate",
        }),
        "battery": _box("battery", 105.0, 35.0, 29.0).model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=15.5),
            "mounted_on": "frame_plate",
        }),
        "sensors": _box("sensors", 40.0, 40.0, 12.0).model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=7.0),
            "mounted_on": "frame_plate",
        }),
    }
    assessment = assess_silhouette(components)
    assert assessment.verdict == "silueta_estimada"
    message = format_silhouette_checklist(assessment)
    assert "este checklist" in message.lower()
    assert "sin problemas" not in message.lower()
    assert "assembly ready" not in message.lower()


def test_a1_silhouette_declared_footer_also_scoped():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _box("frame_plate", 120.0, 55.0, 2.0, source="declared"),
        "esc": _box("esc", 45.6, 44.0, 8.0).model_copy(update={
            "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.0),
            "mounted_on": "frame_plate",
        }),
    }
    assessment = assess_silhouette(components)
    assert assessment.verdict == "silueta"
    message = format_silhouette_checklist(assessment)
    assert "este checklist" in message.lower()
    assert "sin problemas" not in message.lower()


# ── R1: no plate box -> blocked, never falsely "ready" ──────────────────


def test_r1_no_plate_box_blocks_plate_relations():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(suggested_key="frame_plate", component_type="structure_part", parent_key="frame"),
        "esc": _box("esc", 45.6, 44.0, 8.0),
    }
    assessment = assess_fit_relations(components)
    assert assessment.ready_count == 0
    assert assessment.attested_count == 0
    assert assessment.blocked_count == 1
    row = assessment.rows[0]
    assert row.status == "no_box_origin"
    message = format_fit_relations_checklist(assessment)
    assert "listas para declarar verificado" in message
    assert "0 listas para declarar verificado" in message
    assert "listo para verificar" not in message.lower()


def test_r1_zero_plate_key_declared_is_missing_origin():
    components = {"esc": _box("esc", 45.6, 44.0, 8.0)}
    assessment = assess_fit_relations(components)
    assert assessment.rows[0].status == "missing_origin"


# ── R2: estimated plate blocks even with pose+box ────────────────────────


def test_r2_estimated_plate_blocks_attest_even_when_posed():
    components = _posed_fc(plate_source="estimated_temporary")
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "flight_controller")
    assert row.status == "estimated_dims"
    assert assessment.ready_count == 0
    assert assessment.blocked_count == 1


# ── R3: declared plate + overlap -> ready, real attest phrase ───────────


def test_r3_declared_plate_overlap_ready_with_real_attest_phrase():
    from jarvis.core.motor_catalog_assist import _normalize_help
    from jarvis.core.mounted_on_declare_assist import resolve_component_subject_noun

    components = _posed_fc(plate_source="declared")
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "flight_controller")
    assert row.status == "screen_overlap"
    assert assessment.ready_count == 1
    assert row.suggest is not None
    assert "declaro verificad" in row.suggest

    # The suggested phrase actually resolves through the SAME trigger +
    # subject-noun table the live IDLE bridge uses.
    import re
    declaro_re = re.compile(r"\bdeclaro\s+verificad[oa]\b", re.IGNORECASE)
    assert declaro_re.search(row.suggest)
    subject = resolve_component_subject_noun(_normalize_help(row.suggest))
    assert subject == "flight_controller"


# ── R4: valid attestation -> attested ────────────────────────────────────


def test_r4_valid_attestation_shows_attested():
    components = _posed_fc(plate_source="declared")
    fc = components["flight_controller"]
    plate = components["frame_plate"]
    fingerprint = compute_fit_attestation_fingerprint(
        fc.declared_box_pose, _geometry_from_spec(fc), _geometry_from_spec(plate)
    )
    components["flight_controller"] = fc.model_copy(update={
        "declared_fit_attestation": DeclaredFitAttestation(attested_at="2026-09-13T00:00:00Z", fingerprint=fingerprint)
    })
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "flight_controller")
    assert row.status == "attested"
    assert assessment.attested_count == 1
    assert assessment.ready_count == 0


def test_r4_stale_fingerprint_never_shows_attested():
    """A pose change after attestation invalidates the fingerprint — this
    read-only checklist must re-derive it fresh (never trust the stored
    seal blindly), same discipline as spatial_board.py's own projector."""
    components = _posed_fc(plate_source="declared")
    fc = components["flight_controller"]
    plate = components["frame_plate"]
    stale_pose = DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=999.0)
    fingerprint = compute_fit_attestation_fingerprint(
        stale_pose, _geometry_from_spec(fc), _geometry_from_spec(plate)
    )
    components["flight_controller"] = fc.model_copy(update={
        "declared_fit_attestation": DeclaredFitAttestation(attested_at="2026-09-13T00:00:00Z", fingerprint=fingerprint)
    })
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "flight_controller")
    assert row.status != "attested"


# ── R5: motors/propellers n_a_disk; mount warn independent ──────────────


def test_r5_motors_propellers_are_n_a_disk_with_mount_warning():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": _box("frame_arm", 80.0, 20.0, 4.0),
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
        ),
        "propellers": ComponentSpec(
            suggested_key="propellers", completeness="high",
            properties={"diameter_in": PropertyValue(value=5.1, unit="in", confidence=0.9, source="declared")},
        ),
    }
    assessment = assess_fit_relations(components)
    by_child = {r.child: r for r in assessment.rows}
    assert by_child["motors"].status == "n_a_disk"
    assert by_child["propellers"].status == "n_a_disk"
    assert assessment.na_count == 2
    assert by_child["motors"].mount_warning is not None
    assert "brazo" in by_child["motors"].mount_warning
    assert by_child["propellers"].mount_warning is not None


def test_r5_mount_warning_absent_once_mounted():
    components = {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": _box("frame_arm", 80.0, 20.0, 4.0),
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
        ).model_copy(update={"mounted_on": "frame_arm"}),
    }
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "motors")
    assert row.status == "n_a_disk"
    assert row.mount_warning is None


def test_r5_missing_arm_is_missing_origin_for_motors_relation():
    components = {
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared")},
        ),
    }
    assessment = assess_fit_relations(components)
    row = next(r for r in assessment.rows if r.child == "motors")
    assert row.status == "missing_origin"


# ── R6: trigger family + non-theft ───────────────────────────────────────


def test_r6_trigger_phrases_resolve():
    assert is_fit_relations_assist_trigger("relaciones")
    assert is_fit_relations_assist_trigger("Relaciones")
    assert is_fit_relations_assist_trigger("fit")
    assert is_fit_relations_assist_trigger("¿qué falta verificar?")
    assert is_fit_relations_assist_trigger("verificaciones de encaje")


def test_r6_sibling_triggers_never_stolen():
    assert not is_fit_relations_assist_trigger("silueta")
    assert not is_fit_relations_assist_trigger("parece un dron")
    assert not is_fit_relations_assist_trigger("montajes estándar")
    assert not is_fit_relations_assist_trigger("layout pack")
    assert not is_fit_relations_assist_trigger("apilar en placa")


# ── R7: suggest-only never mutates / never attests ───────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "fit relations checklist b1",
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


def test_r7_idle_checklist_never_writes_or_attests(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _posed_fc(plate_source="declared"))
    before = orch.state_manager.load_active_project(orch.workspace_manager)
    result = orch.handle_user_text("relaciones", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "fit_relations_checklist"
    assert "declaro verificad" in result["message"]

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.design_properties.components["flight_controller"].declared_fit_attestation is None
    assert before.design_properties.components == after.design_properties.components


def test_module_has_no_project_specific_literals():
    import inspect

    import jarvis.core.fit_relations_assist as mod

    source = inspect.getsource(mod)
    for literal in ("my5", "hglrc", "10-min", "5min", "autonomía", "autonomia"):
        assert literal not in source.lower(), f"found project-specific literal: {literal!r}"
