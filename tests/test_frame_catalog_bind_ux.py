"""Structure Catalog Foundation IC-3 (assist).

Covers implementation_contract_structure_catalog_foundation_ic3.md §4:
  1. build_frame_catalog_suggestions returns all IC-1 seed SKUs (>=2 classes)
  2. format_frame_catalog_suggestions includes mass + size class + identity
  3. Offer path: help-choose with frame pending -> frame_suggestions
     populated; peer suggestion lists cleared
  4. Apply path: pick index -> catalog_ref set, structure_mass_override_kg
     matches projected mass, sku_resolved True
  5. TBS-style seed without material -> bind/apply does not invent material
  6. Free-text frame path still works (regression smoke)
  7. LEVEL A still fires on bound class vs oversized prop
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.frame_catalog_assist import (
    build_frame_catalog_suggestions,
    format_frame_catalog_suggestions,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.project_closure import _bom_sku_resolved
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "dron de prueba frame catalog ux",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
    "propeller_diameter_in": 10.0,
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


# ── 1/2 — pure suggestion builder/formatter ─────────────────────────────────

def test_build_frame_catalog_suggestions_returns_seed_with_two_classes():
    suggestions = build_frame_catalog_suggestions(None)
    assert 2 <= len(suggestions) <= 6
    sizes = {s["size_class_inch"] for s in suggestions}
    assert len(sizes) >= 2
    assert any(s["name"] == "armattan_rooster_5in" for s in suggestions)


def test_format_frame_catalog_suggestions_shows_identity_mass_class():
    suggestions = build_frame_catalog_suggestions(None)
    text = format_frame_catalog_suggestions(suggestions)
    assert "Armattan" in text
    assert "125" in text  # mass_g
    assert "5\"" in text  # size class


# ── 3 — offer path: help-choose with frame pending ──────────────────────────

def test_frame_help_choose_populates_suggestions_and_clears_peers(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)
    # Seed a stale peer suggestion list to prove it gets cleared.
    session = o.state_manager.get_runtime_session()
    o.state_manager.set_runtime_session(
        session.model_copy(update={"motor_suggestions": [{"idx": 1, "name": "stale"}]})
    )

    result = o.handle_user_text("ayúdame a elegir", llm)
    assert result["status"] == "interactive"
    suggestions = result.get("frame_suggestions") or []
    assert suggestions, "frame_suggestions empty"
    assert any(s["name"] == "armattan_rooster_5in" for s in suggestions)

    session_after = o.state_manager.get_runtime_session()
    assert session_after.motor_suggestions == []
    assert session_after.propeller_suggestions == []
    assert session_after.battery_suggestions == []


# ── 4 — apply path: pick -> bind + BOM sku_resolved ─────────────────────────

def test_frame_pick_binds_catalog_ref_and_mass_mirror(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    offer = o.handle_user_text("ayúdame a elegir", llm)
    suggestions = offer["frame_suggestions"]
    idx = next(s["idx"] for s in suggestions if s["name"] == "armattan_rooster_5in")
    pick = o.handle_user_text(str(idx), llm)
    assert pick["status"] == "ok"

    state = o.state_manager.load_active_project(o.workspace_manager)
    frame = state.design_properties.components["frame"]
    assert frame.catalog_ref == CatalogRef(family="frame", sku="armattan_rooster_5in")
    seed = default_library.get_frame("armattan_rooster_5in")
    assert state.current_parameters["structure_mass_override_kg"] == pytest.approx(seed.mass_g / 1000.0)
    assert _bom_sku_resolved({"family": "frame", "sku": "armattan_rooster_5in"}) is True

    session_after = o.state_manager.get_runtime_session()
    assert session_after.frame_suggestions == []


def test_frame_pick_with_seeded_parts_upserts_children(tmp_path: Path):
    """Structure B Parts Graph (Fase 1): picking a SKU with declared part
    fields (armattan_rooster_5in) upserts frame_arm/plate/cage/standoff as
    children, parent_key="frame", not as top-level BOM peers."""
    from jarvis.core.project_closure import build_component_bom

    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    offer = o.handle_user_text("ayúdame a elegir", llm)
    idx = next(s["idx"] for s in offer["frame_suggestions"] if s["name"] == "armattan_rooster_5in")
    o.handle_user_text(str(idx), llm)

    state = o.state_manager.load_active_project(o.workspace_manager)
    components = state.design_properties.components
    for key in ("frame_arm", "frame_plate", "frame_cage", "frame_standoff"):
        assert components[key].parent_key == "frame"

    bom = build_component_bom(state)
    all_top_level = (
        [e["key"] for e in bom["defined"]]
        + [e["key"] for e in bom["incomplete"]]
        + [e["key"] for e in bom["declarative"]]
    )
    assert "frame_arm" not in all_top_level
    assert "frame_cage" not in all_top_level


def test_frame_pick_tbs_row_creates_arm_thickness_and_curated_plates_no_cage_standoff(
    tmp_path: Path,
):
    """A SKU with no seeded arm/cage/standoff material or count but a
    sourced arm_thickness_mm (arms B2) and a curated plates list (Frame
    Assembly Physical Model B2 — any TBS row) must project frame_arm
    (thickness only) plus its ordinal plate siblings, never fabricate
    frame_cage/frame_standoff and never fabricate arm material/count."""
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    offer = o.handle_user_text("ayúdame a elegir", llm)
    idx = next(s["idx"] for s in offer["frame_suggestions"] if s["name"] == "tbs_source_one_v5_5in")
    o.handle_user_text(str(idx), llm)

    state = o.state_manager.load_active_project(o.workspace_manager)
    components = state.design_properties.components
    for key in ("frame_cage", "frame_standoff"):
        assert key not in components
    assert components["frame_arm"].parent_key == "frame"
    assert components["frame_arm"].properties["thickness_mm"].value == pytest.approx(6.0)
    assert "material" not in components["frame_arm"].properties
    assert "count" not in components["frame_arm"].properties
    assert components["frame_plate"].properties["label"].value == "Top"
    assert components["frame_plate_2"].properties["label"].value == "Middle"
    assert components["frame_plate_3"].properties["label"].value == "Bottom"
    for key in ("frame_plate", "frame_plate_2", "frame_plate_3"):
        assert components[key].parent_key == "frame"


# ── 5 — TBS-style seed without material: honest, no fabrication ────────────

def test_frame_pick_tbs_seed_without_material_does_not_invent_one(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    offer = o.handle_user_text("ayúdame a elegir", llm)
    suggestions = offer["frame_suggestions"]
    idx = next(s["idx"] for s in suggestions if s["name"] == "tbs_source_one_v5_5in")
    pick = o.handle_user_text(str(idx), llm)
    assert pick["status"] == "ok"

    state = o.state_manager.load_active_project(o.workspace_manager)
    frame = state.design_properties.components["frame"]
    assert "material" not in frame.properties
    assert frame.completeness == "medium"  # honest: mass+class known, material not


# ── 6 — free-text frame path regression smoke ───────────────────────────────

def test_frame_free_text_path_still_works(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    result = o.handle_user_text("fibra de carbono 450g 6 pulgadas", llm)
    assert result["status"] == "ok"
    state = o.state_manager.load_active_project(o.workspace_manager)
    frame = state.design_properties.components["frame"]
    assert frame.catalog_ref is None
    assert frame.properties["mass_kg"].value == pytest.approx(0.45)
    assert frame.properties["size_class_inch"].value == pytest.approx(6.0)


# ── 7 — LEVEL A still fires on a bound frame vs oversized propeller ────────

def test_bound_frame_still_triggers_level_a_gap_when_prop_oversized(tmp_path: Path):
    o = _fresh(tmp_path)
    llm = _RefuseLLM()
    _open_frame_wizard(o)

    offer = o.handle_user_text("ayúdame a elegir", llm)
    suggestions = offer["frame_suggestions"]
    idx = next(s["idx"] for s in suggestions if s["name"] == "armattan_rooster_5in")
    o.handle_user_text(str(idx), llm)  # 5" class frame

    state = o.state_manager.load_active_project(o.workspace_manager)
    # _CREATE declares propeller_diameter_in=10.0 -> 5" frame is incompatible.
    readiness = build_engineering_readiness(state)
    assert any(g.gap_type == "GAP-FRAME-PROP-SIZE" for g in readiness.gaps)
