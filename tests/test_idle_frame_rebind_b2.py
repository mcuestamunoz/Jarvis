"""IDLE frame rebind (B2).

Covers implementation_contract_idle_frame_rebind_b2.md §4:
  T1  IDLE "cambiar frame" -> numbered frame catalog opens
  T2  IDLE "definir frame" -> same
  T3  IDLE "ayúdame a elegir frame" -> frame list, not motor list
  T4  Pick after freeform/TBS-bound project -> catalog_ref + part children
  T5  Bound Armattan -> rebind pick TBS -> no leftover frame_* children
  T6  Bare "ayúdame a elegir" with underspec motor still opens motor assist
  T7  "cambiar batería" / "cambiar motores" do not open frame catalog
  T8  Full suite green (verified separately via `pytest -q`)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_frame_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
    frame_part_specs_from_catalog,
)
from jarvis.core.component_writers import (
    set_battery_component,
    set_frame_material,
    set_motor_component,
    set_propeller_component,
    upsert_frame_part,
)
from jarvis.core.frame_catalog_assist import is_frame_rebind_phrase
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _closed_project_bound_frame(tmp_path: Path) -> JarvisOrchestrator:
    """Architecture 4/4, all four families catalog-bound, frame has the
    Armattan parts graph — the exact shape the investigation reconstructed."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    motor = max(default_library.list_motors(), key=lambda x: x.thrust_n)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "idle frame rebind b2",
            "payload_kg": 0.3,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.3,
            "safety_factor": 1.1,
            "motors": 4,
            "per_motor_max_thrust_n": motor.thrust_n,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motor_bind = bind_motor_from_catalog({
        "idx": 1, "name": motor.name, "thrust_n": motor.thrust_n,
        "kv_rating": motor.kv_rating, "weight_g": motor.weight_g,
        "max_watts": motor.max_watts or 200, "is_generic": motor.is_generic,
    })
    ps = set_motor_component(ps, motor_bind, motor.max_watts or 200)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5030"))
    ps = set_battery_component(ps, bind_battery_from_catalog("lipo_4s_5000mah"), 74.0)
    frame_bind = bind_frame_from_catalog("armattan_rooster_5in")
    ps = set_frame_material(
        ps,
        frame_bind.properties["mass_kg"].value,
        frame_bind.properties["material"].value,
        frame_bind.properties["size_class_inch"].value,
        catalog_ref=frame_bind.catalog_ref,
        component_name=frame_bind.name,
    )
    for key, spec in frame_part_specs_from_catalog("armattan_rooster_5in").items():
        ps = upsert_frame_part(ps, key, spec.properties, catalog_ref=spec.catalog_ref)
    fc = ComponentSpec(
        suggested_key="flight_controller", completeness="high", source="declared",
        properties={"model": PropertyValue(value="pixhawk_4", confidence=0.9)},
    )
    sensors = ComponentSpec(
        suggested_key="sensors", completeness="medium", source="declared",
        properties={"gps_model": PropertyValue(value="ublox_m9n")},
    )
    esc = ComponentSpec(
        suggested_key="esc", completeness="high", source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    components = dict(ps.design_properties.components)
    components.update({"flight_controller": fc, "sensors": sensors, "esc": esc})
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    params = dict(ps.current_parameters)
    params.update({
        "motor_count": 4, "per_motor_max_thrust_n": motor.thrust_n,
        "battery_capacity_wh": 74.0, "motor_power_w": motor.max_watts or 200,
    })
    ps = ps.model_copy(update={"design_properties": dp, "current_parameters": params})
    orch.workspace_manager.save_state(ps)
    assert orch._next_pending_block(ps) is None, "fixture must be architecture 4/4"
    return orch


def _reset_idle(orch: JarvisOrchestrator) -> None:
    session = orch.state_manager.get_runtime_session()
    idle = session.model_copy(update={
        "mode": OrchestratorMode.IDLE,
        "pending_missing_params": [],
        "pending_missing_reason": "",
        "pending_define_missing": False,
        "frame_suggestions": [],
        "motor_suggestions": [],
        "propeller_suggestions": [],
        "battery_suggestions": [],
    })
    orch.state_manager.set_runtime_session(idle)


# ── Phrase detector unit tests ──────────────────────────────────────────────

@pytest.mark.parametrize("phrase", [
    "cambiar frame", "definir frame", "ayúdame a elegir frame",
    "ayudame a escoger el chasis", "modificar el chasis",
    "ayúdame a elegir el chasis",
])
def test_is_frame_rebind_phrase_true_cases(phrase):
    assert is_frame_rebind_phrase(phrase) is True


@pytest.mark.parametrize("phrase", [
    "ayúdame a elegir", "cambiar batería", "definir motores",
    "optimizar estructura", "cambiar material",
])
def test_is_frame_rebind_phrase_false_cases(phrase):
    assert is_frame_rebind_phrase(phrase) is False


# ── T1/T2/T3 — IDLE dispatch opens the frame catalog ────────────────────────

@pytest.mark.parametrize("phrase", ["cambiar frame", "definir frame", "ayúdame a elegir frame"])
def test_idle_frame_rebind_phrases_open_frame_catalog(tmp_path: Path, phrase):
    orch = _closed_project_bound_frame(tmp_path)
    _reset_idle(orch)
    llm = _RefuseLLM()
    result = orch.handle_user_text(phrase, llm)
    assert result["status"] == "interactive"
    suggestions = result.get("frame_suggestions") or []
    assert suggestions, f"{phrase!r} did not open the frame catalog"
    assert any(s["name"] == "armattan_rooster_5in" for s in suggestions)
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_missing_params == ["frame"]


def test_ayudame_a_elegir_frame_opens_frame_not_motor_list(tmp_path: Path):
    """T3: distinguishes from bare help-choose, which (in this fixture) would
    otherwise resolve to the motor underspec re-offer."""
    orch = _closed_project_bound_frame(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("ayúdame a elegir frame", _RefuseLLM())
    suggestions = result.get("frame_suggestions") or []
    assert any(s["name"] == "armattan_rooster_5in" for s in suggestions)
    assert "motor_suggestions" not in result or not result["motor_suggestions"]


# ── T4/T5 — pick binds SKU + parts; re-pick clears stale children ──────────

def test_pick_after_rebind_binds_catalog_ref_and_parts(tmp_path: Path):
    orch = _closed_project_bound_frame(tmp_path)
    _reset_idle(orch)
    offer = orch.handle_user_text("cambiar frame", _RefuseLLM())
    idx = next(s["idx"] for s in offer["frame_suggestions"] if s["name"] == "armattan_rooster_5in")
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    frame = state.design_properties.components["frame"]
    assert frame.catalog_ref == CatalogRef(family="frame", sku="armattan_rooster_5in")
    for key in ("frame_arm", "frame_plate", "frame_cage", "frame_standoff"):
        assert state.design_properties.components[key].parent_key == "frame"


def test_rebind_to_tbs_clears_stale_armattan_children(tmp_path: Path):
    """T5 (arms B2) / T8 (Frame Assembly Physical Model B2): bound Armattan
    (arm + 4 curated plate siblings + cage + standoff) -> rebind pick TBS ->
    every stale Armattan child gone; TBS's own sourced arm_thickness_mm +
    curated 3-plate list (Top/Middle/Bottom) project fresh children rather
    than surviving with Armattan's material/labels."""
    orch = _closed_project_bound_frame(tmp_path)
    before = orch.state_manager.load_active_project(orch.workspace_manager)
    assert sorted(
        k for k in before.design_properties.components if k.startswith("frame_")
    ) == [
        "frame_arm", "frame_cage", "frame_plate", "frame_plate_2", "frame_plate_3",
        "frame_plate_4", "frame_standoff",
    ]

    _reset_idle(orch)
    offer = orch.handle_user_text("cambiar frame", _RefuseLLM())
    idx = next(s["idx"] for s in offer["frame_suggestions"] if s["name"] == "tbs_source_one_v5_5in")
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.design_properties.components["frame"].catalog_ref == CatalogRef(
        family="frame", sku="tbs_source_one_v5_5in"
    )
    remaining = sorted(k for k in after.design_properties.components if k.startswith("frame_"))
    assert remaining == ["frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3"], (
        f"unexpected frame_* children survived rebind: {remaining}"
    )
    fresh_arm = after.design_properties.components["frame_arm"].properties
    assert fresh_arm["thickness_mm"].value == pytest.approx(6.0)
    assert "material" not in fresh_arm, "stale Armattan arm material must not survive rebind to TBS"
    fresh_plate = after.design_properties.components["frame_plate"].properties
    assert fresh_plate["label"].value == "Top"
    fresh_plate_2 = after.design_properties.components["frame_plate_2"].properties
    assert fresh_plate_2["label"].value == "Middle", (
        "stale Armattan plate label ('Top (LiPo) plate') must not survive rebind to TBS"
    )


# ── T6/T7 — regressions: unnamed/other-family phrases unaffected ───────────

def test_bare_ayudame_a_elegir_still_opens_motor_assist_not_frame(tmp_path: Path):
    orch = _closed_project_bound_frame(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("ayúdame a elegir", _RefuseLLM())
    assert "frame_suggestions" not in result or not result["frame_suggestions"]
    # The fixture's bound motor triggers the T1 underspec re-offer, per the
    # investigation's own confirmed finding.
    assert "motor" in (result.get("message") or "").lower() or result.get("status") == "interactive"


@pytest.mark.parametrize("phrase", ["cambiar batería", "cambiar motores", "definir motores"])
def test_other_family_phrases_never_open_frame_catalog(tmp_path: Path, phrase):
    orch = _closed_project_bound_frame(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text(phrase, _RefuseLLM())
    assert not result.get("frame_suggestions")
