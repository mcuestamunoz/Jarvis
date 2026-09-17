"""Disk-station radial reach B1 (`B1-disk-station-reach`).

Covers implementation_contract_disk_station_reach_b1.md §2:

  T1  Helper: fixture quad_x + wheelbase + arm L <= R -> station_reach_ok
  T2  Helper: L > R -> station_reach_over (never silent shrink)
  T3  Helper: missing wheelbase / arm length / not quad_x -> station_reach_insufficient
  T4  estimated_temporary on arm length_mm -> estimated path; attest SET raises
  T5  assess_fit_relations: motors<->frame_arm uses reach statuses;
      propellers<->motors still n_a_disk
  T6  screen_posed_envelope still child_not_box for disk/cylinder motors — unchanged
  T7  Attest OK only on station_reach_ok; fingerprint != box fingerprint;
      clear when arm L or wheelbase changes
  T8  Copy strings contain reach/alcance honesty; never claim AABB "cabe" /
      bare VERIFIED from screening alone
  T9  Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import (
    compute_fit_attestation_fingerprint,
    compute_station_reach_fingerprint,
    set_component_declared_fit_attestation,
    set_component_mounted_on,
    upsert_frame_part,
)
from jarvis.core.fit_relations_assist import assess_fit_relations, format_fit_relations_checklist
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.pose_envelope_screening import screen_posed_envelope
from jarvis.core.station_reach_screening import format_station_reach, screen_station_reach
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _frame(*, wheelbase_mm: float | None = 225.0, configuration: str | None = "quad_x",
           wheelbase_source: str = "declared") -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if configuration is not None:
        props["configuration"] = PropertyValue(value=configuration, unit=None, confidence=0.9, source="declared")
    if wheelbase_mm is not None:
        props["wheelbase_mm"] = PropertyValue(value=wheelbase_mm, unit="mm", confidence=0.95, source=wheelbase_source)
    return ComponentSpec(suggested_key="frame", completeness="high", properties=props)


def _arm(*, length_mm: float | None = 80.0, source: str = "declared") -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if length_mm is not None:
        props["length_mm"] = PropertyValue(value=length_mm, unit="mm", confidence=0.9, source=source)
    return ComponentSpec(suggested_key="frame_arm", completeness="high", properties=props)


def _motors(*, mounted_on: str | None = "frame_arm", diameter_mm: float = 27.9, height_mm: float = 31.7) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="motors", completeness="high", mounted_on=mounted_on,
        properties={
            "diameter_mm": PropertyValue(value=diameter_mm, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=height_mm, unit="mm", confidence=0.9, source="declared"),
        },
    )


def _components(**overrides) -> dict[str, ComponentSpec]:
    base = {"frame": _frame(), "frame_arm": _arm(), "motors": _motors()}
    base.update(overrides)
    return base


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_reach_ok_when_arm_length_within_station_radius():
    components = _components()
    screening = screen_station_reach(components["motors"], "frame_arm", components)
    assert screening.status == "station_reach_ok"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_reach_over_when_arm_longer_than_station_radius_never_shrunk():
    # wheelbase 225mm -> station radius ~= 159.1mm; arm length 300mm > R.
    components = _components(frame_arm=_arm(length_mm=300.0))
    screening = screen_station_reach(components["motors"], "frame_arm", components)
    assert screening.status == "station_reach_over"


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_missing_wheelbase_is_insufficient():
    components = _components(frame=_frame(wheelbase_mm=None))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_insufficient"


def test_t3_missing_arm_length_is_insufficient():
    components = _components(frame_arm=_arm(length_mm=None))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_insufficient"


def test_t3_not_quad_x_is_insufficient():
    components = _components(frame=_frame(configuration="hexa_plus"))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_insufficient"


def test_t3_missing_mount_is_insufficient_never_inferred():
    components = _components(motors=_motors(mounted_on=None))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_insufficient"


def test_t3_missing_frame_arm_key_is_insufficient():
    components = {"frame": _frame(), "motors": _motors()}
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_insufficient"


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_estimated_temporary_arm_length_is_estimated_status():
    components = _components(frame_arm=_arm(source="estimated_temporary"))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_estimated"


def test_t4_estimated_temporary_wheelbase_is_estimated_status():
    components = _components(frame=_frame(wheelbase_source="estimated_temporary"))
    assert screen_station_reach(components["motors"], "frame_arm", components).status == "station_reach_estimated"


def test_t4_attest_set_raises_on_estimated_arm(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components(frame_arm=_arm(source="estimated_temporary")))
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError):
        set_component_declared_fit_attestation(ps, "motors", attest=True)


def test_t4_attest_set_raises_on_insufficient(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components(motors=_motors(mounted_on=None)))
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError):
        set_component_declared_fit_attestation(ps, "motors", attest=True)


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_motors_frame_arm_uses_reach_status_propellers_uses_catalog_pair():
    """B1-propellers-motors-catalog-pair: propellers/motors no longer
    hardcodes n_a_disk either — an unbound propeller (no catalog_ref, as
    here) now reads catalog_pair_unverifiable, not n_a_disk."""
    components = _components(propellers=ComponentSpec(
        suggested_key="propellers", completeness="high", mounted_on="motors",
        properties={"diameter_in": PropertyValue(value=5.1, unit="in", confidence=0.9, source="declared")},
    ))
    assessment = assess_fit_relations(components)
    by_child = {r.child: r for r in assessment.rows}
    assert by_child["motors"].status == "station_reach_ok"
    assert by_child["propellers"].status == "catalog_pair_unverifiable"
    assert assessment.ready_count == 1
    assert assessment.na_count == 0


def test_t5_motors_attested_row_after_valid_seal(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated = set_component_declared_fit_attestation(ps, "motors", attest=True)
    assessment = assess_fit_relations(updated.design_properties.components)
    row = next(r for r in assessment.rows if r.child == "motors")
    assert row.status == "attested"
    assert assessment.attested_count == 1
    assert assessment.ready_count == 0


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_screen_posed_envelope_unchanged_child_not_box_for_motors():
    components = _components()
    # motors has no declared_box_pose (never does, today) -> no_pose;
    # even if it did, its geometry is a cylinder, never a box.
    screening = screen_posed_envelope(components["motors"], components)
    assert screening.status == "no_pose"
    geometry = _geometry_from_spec(components["motors"])
    assert geometry["shape"] == "cylinder"


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_attest_ok_only_on_station_reach_ok(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components(frame_arm=_arm(length_mm=300.0)))
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError):
        set_component_declared_fit_attestation(ps, "motors", attest=True)


def test_t7_station_reach_fingerprint_differs_from_box_fingerprint():
    components = _components()
    reach_fp = compute_station_reach_fingerprint(components["frame"], components["frame_arm"], components["motors"])
    from jarvis.schemas.action_schema import DeclaredBoxPose

    pose = DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=0.0)
    box_geom = {"length_mm": 80.0, "width_mm": 20.0, "height_mm": 4.0}
    box_fp = compute_fit_attestation_fingerprint(pose, box_geom, box_geom)
    assert reach_fp != box_fp
    assert "frame_arm" in reach_fp  # child.mounted_on is part of the tuple


def test_t7_attestation_clears_when_arm_length_changes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    attested = set_component_declared_fit_attestation(ps, "motors", attest=True)
    assert attested.design_properties.components["motors"].declared_fit_attestation is not None

    changed = upsert_frame_part(attested, "frame_arm", {
        "length_mm": PropertyValue(value=95.0, unit="mm", confidence=0.9, source="declared"),
    })
    assert changed.design_properties.components["motors"].declared_fit_attestation is None


def test_t7_attestation_clears_when_mounted_on_changes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    attested = set_component_declared_fit_attestation(ps, "motors", attest=True)
    assert attested.design_properties.components["motors"].declared_fit_attestation is not None

    changed = set_component_mounted_on(attested, "motors", None)
    assert changed.design_properties.components["motors"].declared_fit_attestation is None


def test_t7_box_family_attestation_still_uses_box_fingerprint_unaffected(tmp_path: Path):
    """The `motors == "motors"` branch must never intercept any other key
    — the box-overlap path is unchanged for every non-motors component."""
    from jarvis.schemas.action_schema import DeclaredBoxPose

    plate = ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "length_mm": PropertyValue(value=80.0, unit="mm", confidence=0.9, source="declared"),
            "width_mm": PropertyValue(value=40.0, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=2.0, unit="mm", confidence=0.9, source="declared"),
        },
    )
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        properties={
            "length_mm": PropertyValue(value=10.0, unit="mm", confidence=0.9, source="declared"),
            "width_mm": PropertyValue(value=10.0, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=5.0, unit="mm", confidence=0.9, source="declared"),
        },
        declared_box_pose=DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=0.0),
    )
    orch = _orch_with_components(tmp_path, {"frame_plate": plate, "esc": esc})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated = set_component_declared_fit_attestation(ps, "esc", attest=True)
    esc_attestation = updated.design_properties.components["esc"].declared_fit_attestation
    assert esc_attestation is not None
    expected_fp = compute_fit_attestation_fingerprint(
        esc.declared_box_pose,
        {"length_mm": 10.0, "width_mm": 10.0, "height_mm": 5.0},
        {"length_mm": 80.0, "width_mm": 40.0, "height_mm": 2.0},
    )
    assert esc_attestation.fingerprint == expected_fp


# ── T8 ────────────────────────────────────────────────────────────────────


def test_t8_copy_never_claims_aabb_or_bare_verified():
    components = _components()
    screening = screen_station_reach(components["motors"], "frame_arm", components)
    text = format_station_reach(screening)
    assert "alcance de estación" in text
    forbidden = ("cabe", "no cabe", "VERIFIED", "ensamblado", "misfit geométrico")
    for token in forbidden:
        assert token not in text

    assessment = assess_fit_relations(components)
    checklist_text = format_fit_relations_checklist(assessment)
    assert "alcance de estación" in checklist_text
    assert "VERIFIED" not in checklist_text


def test_t8_relaciones_idle_shows_reach_row_never_writes(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    before = orch.state_manager.load_active_project(orch.workspace_manager)
    result = orch.handle_user_text("relaciones", _RefuseLLM())
    assert result["status"] == "ok"
    assert "alcance de estación" in result["message"]
    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.design_properties.components["motors"].declared_fit_attestation is None
    assert before.design_properties.components == after.design_properties.components


def test_t8_idle_declaro_verificado_motor_attests(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    result = orch.handle_user_text("declaro verificado el motor", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["motors"].declared_fit_attestation is not None


def test_t8_idle_bare_declaro_verificado_finds_motors_when_only_eligible(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components())
    result = orch.handle_user_text("declaro verificado", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["motors"].declared_fit_attestation is not None


# ── Shared fixture helper (mirrors tests/test_geometry_fit_relations_checklist_b1.py) ──


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "disk station reach b1",
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
