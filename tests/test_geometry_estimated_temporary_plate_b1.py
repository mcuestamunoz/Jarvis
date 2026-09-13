"""Estimated-temporary plate envelope B1 (`B1-estimated-temporary-plate`).

Covers implementation_contract_geometry_estimated_temporary_plate_b1.md §2:
  T1  Provisional declare -> frame_plate L×W with source=estimated_temporary;
      geometry box; root-capable (assembly-root gate reads shape==box only)
  T2  Plain (non-provisional) plate declare still source=declared
  T3  `cabe` with estimated plate as origin -> refuse (estimated_dims),
      no overlap/no_overlap verdict
  T4  Fit attestation SET with estimated dims involved -> refuse, no write
  T5  Success copy includes ESTIMADA/TEMPORAL + replace-when-arrives signal
  T6  Measured/declared overwrite clears estimated source on those keys
  T7  Full pytest green; package 0.4.1; library/frames MY5/GEP unchanged
      (checked at the repo level, not asserted here)

Fixture numbers are the Engineer's own §0.1 bag: plate 120×55 (provisional,
no evidence), height from the plate's own cited `thickness_mm`. Never body
175×173 (GEP) or 225×200 (MY5) — those are explicitly rejected sources.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.component_writers import (
    set_component_declared_box_envelope,
    set_component_declared_fit_attestation,
    set_estimated_temporary_plate_envelope,
)
from jarvis.core.estimated_temporary_plate_assist import parse_estimated_temporary_plate_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.pose_envelope_screening import format_screening, screen_posed_envelope
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.workspace.spatial_board import project_spatial_nodes


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _plate_with_thickness():
    return ComponentSpec(
        suggested_key="frame_plate", component_type="structure_part",
        parent_key="frame", completeness="medium",
        properties={"thickness_mm": PropertyValue(value=3.0, unit="mm", confidence=0.9, source="declared")},
    )


def _posed_esc_on_plate():
    return ComponentSpec(
        suggested_key="esc", completeness="high",
        properties={
            "length_mm": PropertyValue(value=30.0, unit="mm", confidence=0.9, source="declared"),
            "width_mm": PropertyValue(value=30.0, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=8.0, unit="mm", confidence=0.9, source="declared"),
        },
        declared_box_pose=DeclaredBoxPose(origin_key="frame_plate", x_mm=0.0, y_mm=0.0, z_mm=5.5),
    )


def _base_components():
    return {
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": _plate_with_thickness(),
    }


# ── Pure parse ───────────────────────────────────────────────────────────


def test_parse_provisional_exact_key_set():
    result = parse_estimated_temporary_plate_declare(
        "declara frame_plate estimada 120 x 55 mm", _base_components()
    )
    assert result.kind == "SET"
    assert result.component_key == "frame_plate"
    assert result.length_mm == 120.0
    assert result.width_mm == 55.0
    assert result.height_mm is None


def test_parse_provisional_temporal_keyword_triple():
    result = parse_estimated_temporary_plate_declare(
        "declara frame_plate temporal 120 x 55 x 3 mm", _base_components()
    )
    assert result.kind == "SET"
    assert result.height_mm == 3.0


def test_parse_plain_declare_no_provisional_keyword_is_none():
    """T2 precondition: a plain declare must never be claimed by this
    grammar at all."""
    result = parse_estimated_temporary_plate_declare(
        "declara frame_plate 120 x 55 mm", _base_components()
    )
    assert result.kind == "NONE"


def test_parse_battery_provisional_defers_not_incomplete():
    """A provisional phrase naming a KNOWN non-plate subject (out of this
    Buy's scope) must defer entirely (NONE), never surface a confusing
    'which plate?' prompt."""
    components = {**_base_components(), "battery": ComponentSpec(suggested_key="battery", completeness="high")}
    result = parse_estimated_temporary_plate_declare(
        "declara la bateria estimada 80 x 34 x 22 mm", components
    )
    assert result.kind == "NONE"


def test_parse_no_subject_named_is_incomplete():
    result = parse_estimated_temporary_plate_declare("declara estimada 120 x 55 mm", _base_components())
    assert result.kind == "INCOMPLETE"


def test_parse_ambiguous_two_plates():
    components = {
        **_base_components(),
        "frame_plate_2": ComponentSpec(
            suggested_key="frame_plate_2", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    }
    result = parse_estimated_temporary_plate_declare(
        "declara la placa estimada 120 x 55 mm", components
    )
    assert result.kind == "AMBIGUOUS_PLATE"
    assert set(result.candidates) == {("frame_plate", "—"), ("frame_plate_2", "—")}


# ── Writer ───────────────────────────────────────────────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "estimated temporary plate b1",
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


def test_writer_rejects_non_plate_key(tmp_path: Path):
    orch = _orch_with_components(tmp_path, {"battery": ComponentSpec(suggested_key="battery", completeness="high")})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError, match="no admite un sobre estimado"):
        set_estimated_temporary_plate_envelope(ps, "battery", 80.0, 34.0, 22.0)


def test_writer_rejects_non_positive_dims(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError, match="mayor que 0"):
        set_estimated_temporary_plate_envelope(ps, "frame_plate", 0.0, 55.0, 3.0)


# ── T1: provisional declare -> box, root-capable ────────────────────────


def test_t1_idle_provisional_declare_sets_estimated_source(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    result = orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())
    assert result["status"] == "ok"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    plate = ps.design_properties.components["frame_plate"]
    assert plate.properties["length_mm"].value == 120.0
    assert plate.properties["length_mm"].source == "estimated_temporary"
    assert plate.properties["width_mm"].source == "estimated_temporary"
    assert plate.properties["height_mm"].value == 3.0  # from thickness_mm
    assert plate.properties["height_mm"].source == "estimated_temporary"
    assert plate.properties["thickness_mm"].value == 3.0  # never deleted

    nodes = project_spatial_nodes(ps)
    plate_node = next(n for n in nodes if n["id"] == "frame_plate")
    assert plate_node["geometry"] == {"shape": "box", "length_mm": 120.0, "width_mm": 55.0, "height_mm": 3.0}


# ── T2: plain declare unaffected ────────────────────────────────────────


def test_t2_plain_declare_still_declared_source(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    result = orch.handle_user_text("declara frame_plate 120 x 55 mm", _RefuseLLM())
    assert result["status"] == "ok"
    assert "source=declared" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    plate = ps.design_properties.components["frame_plate"]
    assert plate.properties["length_mm"].source == "declared"


# ── T3: cabe refuses on estimated plate ─────────────────────────────────


def test_t3_cabe_refuses_estimated_origin(tmp_path: Path):
    components = {**_base_components(), "esc": _posed_esc_on_plate()}
    orch = _orch_with_components(tmp_path, components)
    orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())

    result = orch.handle_user_text("cabe el esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "ESTIMATED_TEMPORARY" in result["message"]
    assert "no se compara" in result["message"]
    for forbidden in ("no cabe", "VERIFIED", "ensamblado"):
        assert forbidden not in result["message"]
    # never answers overlap/no_overlap for this pair
    assert "se solapan" not in result["message"]


def test_screen_posed_envelope_estimated_dims_status_direct():
    """Direct unit check on the screening function itself, independent of
    the IDLE bridge — both directions (estimated child, estimated origin)
    trigger the same refusal."""
    plate_estimated = ComponentSpec(
        suggested_key="frame_plate", component_type="structure_part", parent_key="frame",
        properties={
            "length_mm": PropertyValue(value=120.0, unit="mm", confidence=0.3, source="estimated_temporary"),
            "width_mm": PropertyValue(value=55.0, unit="mm", confidence=0.3, source="estimated_temporary"),
            "height_mm": PropertyValue(value=3.0, unit="mm", confidence=0.3, source="estimated_temporary"),
        },
    )
    esc = _posed_esc_on_plate()
    components = {"frame_plate": plate_estimated, "esc": esc}
    screening = screen_posed_envelope(esc, components)
    assert screening.status == "estimated_dims"
    assert "ESTIMATED_TEMPORARY" in format_screening(screening)


# ── T4: fit attestation refuses with estimated dims ─────────────────────


def test_t4_fit_attestation_set_refuses_with_estimated_dims(tmp_path: Path):
    components = {**_base_components(), "esc": _posed_esc_on_plate()}
    orch = _orch_with_components(tmp_path, components)
    orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    with pytest.raises(ValueError, match="estimated_dims"):
        set_component_declared_fit_attestation(ps, "esc", True)

    result = orch.handle_user_text("declaro verificado el esc", _RefuseLLM())
    assert result["status"] == "error"
    ps2 = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps2.design_properties.components["esc"].declared_fit_attestation is None


# ── T5: disclosure copy ──────────────────────────────────────────────────


def test_t5_success_copy_discloses_estimated_temporary(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    result = orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())
    message = result["message"]
    assert "ESTIMATED_TEMPORARY" in message or "ESTIMADA TEMPORAL" in message
    assert "sustituir al llegar el frame" in message
    assert "SÍ" in message

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    nodes = project_spatial_nodes(ps)
    plate_node = next(n for n in nodes if n["id"] == "frame_plate")
    disclosure = next(f for f in plate_node["fields"] if f["label"] == "geometría")
    assert "ESTIMADA TEMPORAL" in disclosure["value"]
    assert "evidencia: ninguna" in disclosure["value"]


# ── T6: measured overwrite clears estimated source + stale attestation ──


def test_t6_measured_declare_overwrites_estimated_source(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())

    result = orch.handle_user_text("declara frame_plate 121 x 56 x 3 mm", _RefuseLLM())
    assert result["status"] == "ok"
    assert "source=declared" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    plate = ps.design_properties.components["frame_plate"]
    assert plate.properties["length_mm"].value == 121.0
    assert plate.properties["length_mm"].source == "declared"
    assert plate.properties["width_mm"].source == "declared"
    assert plate.properties["height_mm"].source == "declared"


def test_t6_clear_pops_estimated_dims_same_as_declared(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _base_components())
    orch.handle_user_text("declara frame_plate estimada 120 x 55 mm", _RefuseLLM())

    result = orch.handle_user_text("quita el sobre de frame_plate", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    plate = ps.design_properties.components["frame_plate"]
    assert "length_mm" not in plate.properties
    assert "width_mm" not in plate.properties
    assert "height_mm" not in plate.properties
    assert plate.properties["thickness_mm"].value == 3.0  # thickness survives clear


def test_t6_fit_attestation_clears_when_estimated_dims_written(tmp_path: Path):
    """An estimated-envelope write on the ORIGIN clears a sibling's stale
    fit attestation exactly like a declared envelope write already does
    (_clear_fit_attestations_after_geometry_change, shared helper)."""
    components = {**_base_components(), "esc": _posed_esc_on_plate()}
    orch = _orch_with_components(tmp_path, components)
    # Give the plate a real (declared) box first so the esc can attest.
    orch.handle_user_text("declara frame_plate 120 x 55 mm", _RefuseLLM())
    orch.handle_user_text("declaro verificado el esc", _RefuseLLM())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["esc"].declared_fit_attestation is not None

    orch.handle_user_text("declara frame_plate estimada 130 x 60 mm", _RefuseLLM())
    ps2 = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps2.design_properties.components["esc"].declared_fit_attestation is None


# ── Non-regression: existing declared-envelope writer untouched ────────


def test_non_regression_set_component_declared_box_envelope_plate_still_declared(tmp_path: Path):
    """The pre-existing plain-declare writer/bridge (thickness-from-cite
    fallback lives in the orchestrator, not the writer) stays byte-for-byte
    unaffected by this Buy."""
    orch = _orch_with_components(tmp_path, _base_components())
    result = orch.handle_user_text("declara la placa principal 100 x 100 mm", _RefuseLLM())
    assert result["status"] == "interactive"  # no plate labeled "Main Plate" -> AMBIGUOUS/no-match, unchanged behavior

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated = set_component_declared_box_envelope(ps, "frame_plate", 100.0, 100.0, 3.0)
    plate = updated.design_properties.components["frame_plate"]
    assert plate.properties["length_mm"].source == "declared"
    assert plate.properties["height_mm"].value == 3.0
