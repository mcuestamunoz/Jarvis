"""Continuity next-step vs mission intent B1 (`B1-continuity-mission-intent`).

Covers implementation_contract_continuity_mission_intent_b1.md §2:

  T1  Objective containing "vigilancia" + high_margin -> no increase_payload
  T2  Neutral objective + high_margin -> increase_payload still present (regression)
  T3  No keyword but components["cameras"] present -> mission active -> no increase_payload
  T4  Alternate label/reason appears when cameras absent (5a)
  T5  Cameras low -> "completar identidad" path (5b)
  T6  mission_intent_active unit cases: keyword hit / miss / over-match guard
  T7  Continuity/estado-level: vigilancia-shaped closed design does not
      surface "Aumentar carga útil" as next_useful_step
  T8  Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.project_continuity import build_project_continuity
from jarvis.core.reasoning_layer import ReasoningLayer, mission_intent_active


def _context(objective, components, *, restrictions="no", margin=2.0, parsed_constraints=None):
    return {
        "objective": objective,
        "current_parameters": {"restrictions": restrictions},
        "design_properties": {"components": components, "structure": {}},
        "last_calculation": None,
        "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {},
        "last_mutation": None,
        "mutation_mode": None,
        "parsed_constraints": parsed_constraints if parsed_constraints is not None else {},
    }


def _top_suggestion(context: dict) -> tuple[str, str | None]:
    out = ReasoningLayer().build(context)
    assert out.suggested_actions, "expected at least one suggested action"
    top = out.suggested_actions[0]
    return top.label, top.action_type


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_vigilancia_objective_suppresses_increase_payload():
    label, action_type = _top_suggestion(_context("dron de vigilancia doméstico", {}))
    assert label != "Aumentar carga útil"
    assert action_type != "increase_payload"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_neutral_objective_keeps_increase_payload_regression():
    label, action_type = _top_suggestion(_context("prueba", {}))
    assert label == "Aumentar carga útil"
    assert action_type == "increase_payload"


def test_t2_empty_objective_keeps_increase_payload_regression():
    label, action_type = _top_suggestion(_context("", {}, restrictions=""))
    assert label == "Aumentar carga útil"
    assert action_type == "increase_payload"


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_cameras_component_present_suppresses_increase_payload_no_keyword():
    label, action_type = _top_suggestion(_context("prueba", {"cameras": {"completeness": "medium"}}))
    assert action_type != "increase_payload"


def test_t3_radio_component_present_suppresses_increase_payload_no_keyword():
    label, action_type = _top_suggestion(_context("prueba", {"radio_module": {"completeness": "medium"}}))
    assert action_type != "increase_payload"


# ── T4 (lock #5a) ─────────────────────────────────────────────────────────


def test_t4_alternate_label_when_cameras_absent_mission_text():
    label, action_type = _top_suggestion(_context("dron de inspección", {}))
    assert label == "Declarar carga de misión (cámara)"
    assert action_type == "complete_mission_payload"


def test_t4_alternate_label_when_cameras_absent_via_radio_component():
    """Mission active via component presence (radio_module), cameras still
    absent -> 5a fires for cameras first (fixed waterfall order)."""
    label, action_type = _top_suggestion(_context("prueba", {"radio_module": {"completeness": "medium"}}))
    assert label == "Declarar carga de misión (cámara)"
    assert action_type == "complete_mission_payload"


# ── T5 (lock #5b/5c) ──────────────────────────────────────────────────────


def test_t5_cameras_low_completeness_gets_complete_identity_label():
    label, action_type = _top_suggestion(_context("prueba", {"cameras": {"completeness": "low"}}))
    assert label == "Completar identidad de cámara"
    assert action_type == "complete_mission_payload"


def test_t5_radio_absent_after_camera_medium_gets_declare_radio_label():
    label, action_type = _top_suggestion(_context("prueba", {"cameras": {"completeness": "medium"}}))
    assert label == "Declarar carga de misión (radio)"
    assert action_type == "complete_mission_payload"


def test_t5_radio_low_after_camera_medium_gets_complete_radio_identity_label():
    label, action_type = _top_suggestion(_context(
        "prueba", {"cameras": {"completeness": "medium"}, "radio_module": {"completeness": "low"}}
    ))
    assert label == "Completar identidad de radio"
    assert action_type == "complete_mission_payload"


def test_t5_both_medium_plus_softens_to_margin_review_5d():
    """B1-mission-mass-energy extended this ladder with a mass-declare
    step BEFORE the soft margin fallback — both identity AND mass must be
    present to reach 'Revisar margen...' now (see
    test_continuity_mission_mass_energy_b1.py for the mass-declare steps
    themselves). B1-mission-continuity-mount-endurance extended it further
    with mount + autonomy-target steps; this fixture has no frame/plate
    component at all so the mount step has nothing to suggest a target for
    (falls through), and needs parsed_constraints["autonomy_min"] to clear
    the autonomy-target step. B1-mission-power-w added a power-declare
    step after that — both components carry power_w here so it clears too.
    B1-mission-vtx-identity added a VTX-declare step after that — vtx is
    declared here so it clears too, reaching soft margin."""
    label, action_type = _top_suggestion(_context(
        "dron de vigilancia",
        {
            "cameras": {
                "completeness": "medium",
                "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}, "power_w": {"value": 1.0}},
            },
            "radio_module": {
                "completeness": "high",
                "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}, "power_w": {"value": 0.5}},
            },
            "vtx": {
                "completeness": "high",
                "properties": {"model": {"value": "hglrc"}, "mass_g": {"value": 4.8}},
            },
        },
        parsed_constraints={"autonomy_min": 8.0},
    ))
    assert label == "Revisar margen vs carga de misión"
    assert action_type == "mission_margin_review"
    assert label != "Aumentar carga útil"


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_keyword_hits():
    assert mission_intent_active("dron de vigilancia doméstico", None, {})
    assert mission_intent_active(None, "requiere fotografía aérea", {})
    assert mission_intent_active("home surveillance drone", None, {})
    assert mission_intent_active("cámara RunCam a bordo", None, {})
    assert mission_intent_active(None, "necesita telemetría", {})


def test_t6_keyword_misses():
    assert not mission_intent_active("autonomía de 5min", "sin restricciones", {})
    assert not mission_intent_active(None, None, {})
    assert not mission_intent_active("", "", {})


def test_t6_component_presence_alone_is_sufficient():
    assert mission_intent_active(None, None, {"cameras": {"completeness": "low"}})
    assert mission_intent_active(None, None, {"radio_module": {"completeness": "low"}})
    assert not mission_intent_active(None, None, {"motors": {}, "battery": {}})


def test_t6_over_match_guard_previsualizacion_and_similar_words():
    """Word-boundary matching: a longer word that happens to CONTAIN a
    keyword as a substring must not false-positive."""
    assert not mission_intent_active("previsión de vuelo estimada", None, {})
    assert not mission_intent_active("vehículo de reparto", None, {})


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_continuity_vigilancia_shaped_closed_design_never_shows_increase_payload():
    """End-to-end ReasoningLayer -> build_project_continuity, using a
    'closed design' shape (architecture 4/4, sim PASS, nothing incomplete/
    missing) mirroring the real dron-de-vigilancia-doméstico live project:
    objective names vigilancia, cameras + radio_module both declared at
    medium+ completeness, high thrust margin. No frame/plate component is
    declared so the B1-mission-continuity-mount-endurance mount step has
    no target to suggest (falls through); parsed_constraints carries
    autonomy_min so the autonomy-target step also clears; both mission
    components carry power_w (B1-mission-power-w's own ladder step), and
    vtx is declared (B1-mission-vtx-identity's own ladder step), so both
    clear too, reaching soft margin exactly as this test originally
    intended."""
    context = _context(
        "dron de vigilancia doméstico",
        {
            "cameras": {
                "completeness": "medium",
                "properties": {"model": {"value": "runcam"}, "mass_g": {"value": 28.0}, "power_w": {"value": 1.0}},
            },
            "radio_module": {
                "completeness": "medium",
                "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}, "power_w": {"value": 0.5}},
            },
            "vtx": {
                "completeness": "high",
                "properties": {"model": {"value": "hglrc"}, "mass_g": {"value": 4.8}},
            },
        },
        margin=3.6196,
        parsed_constraints={"autonomy_min": 8.0},
    )
    reasoning = ReasoningLayer().build(context)
    top = reasoning.suggested_actions[0]
    suggested_action = {"label": top.label, "reason": top.reason}

    project_state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass", "quality": "good", "safety_margin_ratio": 3.6196,
                "can_fly": True, "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    cont = build_project_continuity(
        project_state=project_state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=suggested_action,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Aumentar carga útil" not in cont["next_useful_step"]
    assert cont["next_useful_step"] == "Revisar margen vs carga de misión"


def test_t7_continuity_neutral_closed_design_still_shows_increase_payload_regression():
    """Regression companion to T7: a neutral project (no mission signal)
    with the same 'closed design' shape still surfaces increase_payload —
    proves this Buy did not touch the non-mission path."""
    context = _context("prueba", {}, margin=2.0)
    reasoning = ReasoningLayer().build(context)
    top = reasoning.suggested_actions[0]
    suggested_action = {"label": top.label, "reason": top.reason}

    project_state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass", "quality": "good", "safety_margin_ratio": 2.0,
                "can_fly": True, "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    cont = build_project_continuity(
        project_state=project_state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=suggested_action,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert cont["next_useful_step"] == "Aumentar carga útil"
