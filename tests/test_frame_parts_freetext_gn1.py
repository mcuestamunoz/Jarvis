"""Structure B G-N1 — free-text root+parts in one frame message."""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.project_closure import build_component_bom, format_bom_lines
from jarvis.domains.aerial import (
    FRAME_ARM_KEY,
    FRAME_CAGE_KEY,
    FRAME_STANDOFF_KEY,
    extract_all_frame_part_properties,
    extract_frame_part_properties,
    extract_frame_properties,
)
from jarvis.schemas.action_schema import OrchestratorMode


class _RefuseLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called in G-N1 frame free-text path")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "test",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    return o


def _open_frame_wizard(o: JarvisOrchestrator) -> None:
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)


def test_extract_all_root_plus_parts_clause_isolation():
    text = "fibra 450g, 4 brazos carbono, jaula titanio"
    root = extract_frame_properties(text)
    assert root["mass_kg"].value == pytest.approx(0.45)
    assert root["material"].value == "fibra de carbono"

    parts = dict(extract_all_frame_part_properties(text))
    assert set(parts) == {FRAME_ARM_KEY, FRAME_CAGE_KEY}
    assert parts[FRAME_ARM_KEY]["count"].value == 4
    assert parts[FRAME_ARM_KEY]["material"].value == "fibra de carbono"
    assert parts[FRAME_CAGE_KEY]["material"].value == "titanio"
    assert "count" not in parts[FRAME_CAGE_KEY]


def test_extract_all_empty_for_bare_number_or_motors():
    assert extract_all_frame_part_properties("4") == []
    assert extract_all_frame_part_properties("4 motores") == []
    assert extract_frame_part_properties("4 motores") is None


def test_extract_frame_part_properties_wrapper_still_single():
    result = extract_frame_part_properties("4 brazos fibra de carbono")
    assert result is not None
    key, props = result
    assert key == FRAME_ARM_KEY
    assert props["count"].value == 4


def test_orchestrator_root_plus_parts_single_message(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)
    result = o.handle_user_text(
        "fibra de carbono 450g 5 pulgadas, 4 brazos carbono, jaula titanio", llm
    )
    assert result.get("status") == "ok"
    ps = o.state_manager.load_active_project(o.workspace_manager)
    components = ps.design_properties.components
    assert components["frame"].properties["mass_kg"].value == pytest.approx(0.45)
    assert FRAME_ARM_KEY in components
    assert components[FRAME_ARM_KEY].parent_key == "frame"
    assert components[FRAME_ARM_KEY].properties["count"].value == 4
    assert FRAME_CAGE_KEY in components
    assert components[FRAME_CAGE_KEY].properties["material"].value == "titanio"

    bom = build_component_bom(ps)
    top = {
        e["key"]
        for bucket in ("defined", "incomplete", "declarative")
        for e in bom.get(bucket) or []
    }
    assert FRAME_ARM_KEY not in top
    assert FRAME_CAGE_KEY not in top
    lines = "\n".join(format_bom_lines(bom, ps))
    assert "└ arm" in lines
    assert "└ cage" in lines


def test_orchestrator_parts_only_after_frame_exists(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)
    o.handle_user_text("fibra de carbono 450g 5 pulgadas", llm)
    _open_frame_wizard(o)
    result = o.handle_user_text("standoffs aluminio", llm)
    assert result.get("status") == "ok"
    ps = o.state_manager.load_active_project(o.workspace_manager)
    assert FRAME_STANDOFF_KEY in ps.design_properties.components
    assert ps.design_properties.components[FRAME_STANDOFF_KEY].parent_key == "frame"
    assert ps.design_properties.components["frame"].properties["material"].value == (
        "fibra de carbono"
    )


def test_extract_arm_clause_thickness_mm():
    """Structure B additive enrichment B2, T4 — arm clause with mm is
    keyword-gated onto frame_arm.thickness_mm."""
    parts = dict(extract_all_frame_part_properties("brazos 6mm"))
    assert FRAME_ARM_KEY in parts
    assert parts[FRAME_ARM_KEY]["thickness_mm"].value == pytest.approx(6.0)
    assert parts[FRAME_ARM_KEY]["thickness_mm"].unit == "mm"


def test_wheelbase_mm_alone_never_becomes_arm_thickness():
    """A bare root wheelbase clause with no arm keyword must not leak into
    frame_arm.thickness_mm."""
    parts = dict(extract_all_frame_part_properties("wheelbase 230mm"))
    assert FRAME_ARM_KEY not in parts


def test_plate_clause_with_mm_never_extracts_thickness():
    """B2 is arms-only in this IC — a plate clause with mm must not produce
    thickness_mm anywhere."""
    parts = dict(extract_all_frame_part_properties("placa 2mm"))
    assert "thickness_mm" not in parts.get("frame_plate", {})


def test_arm_clause_thickness_and_material_together():
    parts = dict(extract_all_frame_part_properties("4 brazos fibra de carbono 6mm"))
    props = parts[FRAME_ARM_KEY]
    assert props["count"].value == 4
    assert props["material"].value == "fibra de carbono"
    assert props["thickness_mm"].value == pytest.approx(6.0)


def test_freetext_multiple_plate_clauses_never_gain_ordinal_siblings():
    """Frame Assembly Physical Model B2, T9 — N4 lock: free-text multi-plate
    stays OUT. A message naming two plates by different words (both mapping
    to the single locked FRAME_PLATE_KEY) must not fabricate frame_plate_2
    or any other ordinal sibling — only the existing single-key behavior."""
    text = "placa superior 2mm, placa inferior 2.5mm"
    parts = dict(extract_all_frame_part_properties(text))
    assert "frame_plate_2" not in parts
    # Only the single locked key may ever appear from free-text.
    plate_keys = [k for k in parts if k.startswith("frame_plate")]
    assert plate_keys in ([], ["frame_plate"])
    # And B2 (arms-only) still holds: no thickness_mm ever lands on it.
    if "frame_plate" in parts:
        assert "thickness_mm" not in parts["frame_plate"]


def test_merge_configuration_wheelbase_on_freetext_apply(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)
    o.handle_user_text("fibra 450g 5 pulgadas quad-x wheelbase 230mm", llm)
    ps = o.state_manager.load_active_project(o.workspace_manager)
    props = ps.design_properties.components["frame"].properties
    assert props["configuration"].value == "quad_x"
    assert props["wheelbase_mm"].value == pytest.approx(230.0)
