"""FN-005 Assisted Acquisition — motor power help + catalog picker."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.core.motor_catalog_assist import (
    assisted_motor_power_question,
    format_motor_catalog_suggestions,
    is_bare_watts_input,
    is_help_choose_phrase,
    looks_like_motor_model_text,
    match_suggestion_by_input,
    resolve_motor_from_text,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_ENERGY_PARAMETERS, param_question
from jarvis.core.project_continuity import build_project_continuity
from jarvis.knowledge.library import default_library


def test_help_choose_phrases():
    assert is_help_choose_phrase("ayúdame a elegir")
    assert is_help_choose_phrase("ayudame a elegir")
    assert is_help_choose_phrase("busca motores")
    assert not is_help_choose_phrase("350")
    assert not is_help_choose_phrase("calcula")


def test_motor_power_question_has_three_paths_not_raw_key():
    q = param_question("motor_power_w")
    assert "potencia" in q.lower()
    assert "ayúdame a elegir" in q.lower() or "ayudame" in q.lower()
    assert "(motor_power_w)" not in q
    # Menu must NOT use 1/2/3 (collides with catalog picks)
    assert "\n  1. Indica" not in q
    assert "•" in q or "Puedes:" in q


def test_assisted_question_inlines_candidates_without_menu_number_collision():
    q = assisted_motor_power_question(
        [{"idx": 1, "name": "demo_motor", "thrust_n": 12.0, "max_watts": 280, "is_generic": False}],
        thrust_hint_n=4.7,
    )
    assert "4.7" in q
    assert "demo_motor" in q
    assert "~280W" in q
    assert "Candidatos rápidos" in q
    assert "\n  1. Indica" not in q


def test_bare_watts_and_model_detection():
    assert is_bare_watts_input("350")
    assert is_bare_watts_input("350W")
    assert is_bare_watts_input("350 w")
    assert not is_bare_watts_input("T-Motor MN3508 KV700")
    assert looks_like_motor_model_text("T-Motor MN3508 KV700")
    assert looks_like_motor_model_text("sunnysky_x2216_11")
    assert not looks_like_motor_model_text("350")


def test_match_suggestion_rejects_short_substring():
    sugg = [
        {"idx": 1, "name": "sunnysky_x2216_11", "max_watts": 280},
        {"idx": 2, "name": "t-motor_mn3110_700", "max_watts": 350},
    ]
    assert match_suggestion_by_input("motor", sugg) is None
    assert match_suggestion_by_input("2", sugg)["name"] == "t-motor_mn3110_700"
    assert match_suggestion_by_input("t-motor_mn3110_700", sugg)["name"] == "t-motor_mn3110_700"


def test_resolve_unknown_model_returns_none():
    assert resolve_motor_from_text("T-Motor MN3508 KV700") is None


def test_resolve_known_catalog_key():
    motors = default_library.list_motors()
    assert motors
    name = motors[0].name
    hit = resolve_motor_from_text(name)
    assert hit is not None
    assert hit["name"] == name


def _energy_project(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "fotografía aérea cámara 1kg",
            "payload_kg": 1.0,
            "restrictions": "autonomía mínima 20 minutos",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
            # motor_power_w / battery intentionally absent
        },
    })
    return orch


def test_define_wizard_help_opens_catalog(tmp_path: Path):
    orch = _energy_project(tmp_path)
    start = orch.start_define_missing_params(
        ["motor_power_w", "battery_capacity_wh"],
        reason=MISSING_ENERGY_PARAMETERS,
    )
    assert start["status"] == "interactive"
    assert "ayúdame a elegir" in start["question"].lower() or "ayudame" in start["question"].lower()
    assert "(motor_power_w)" not in start["question"]

    help_result = orch.param_definition_session.answer("ayúdame a elegir")
    assert help_result["status"] == "interactive"
    assert help_result.get("motor_suggestions") or "catálogo" in (help_result.get("message") or "").lower()
    assert help_result.get("action") == "define_missing_params"
    assert "impacto" not in (help_result.get("message") or "").lower()


def test_help_choose_not_stolen_by_analyze_during_define(tmp_path: Path):
    orch = _energy_project(tmp_path)
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    result = orch.handle_user_text("ayúdame a elegir", llm_interface=None)
    assert result.get("action") == "define_missing_params"
    assert result.get("status") == "interactive"
    assert result.get("motor_suggestions") or "catálogo" in (result.get("message") or "").lower()


def test_idle_help_choose_opens_assisted_flow(tmp_path: Path):
    """FN-005: outside wizard, help must not fall through to LLM analyze."""
    orch = _energy_project(tmp_path)
    result = orch.handle_user_text("ayúdame a elegir", llm_interface=None)
    assert result.get("action") == "define_missing_params"
    assert result.get("status") == "interactive"
    assert result.get("motor_suggestions") or "candidato" in (result.get("message") or "").lower()


def test_idle_help_choose_does_not_reenter_answer(tmp_path: Path, monkeypatch):
    """FN-006: the IDLE assisted-help path must call offer_catalog_help() directly,
    not simulate a user turn via answer("ayúdame a elegir")."""
    orch = _energy_project(tmp_path)
    original_answer = orch.param_definition_session.answer
    calls: list[str] = []

    def spy(user_input: str):
        calls.append(user_input)
        return original_answer(user_input)

    monkeypatch.setattr(orch.param_definition_session, "answer", spy)
    result = orch.handle_user_text("ayúdame a elegir", llm_interface=None)

    assert calls == []
    assert result.get("action") == "define_missing_params"
    assert result.get("status") == "interactive"
    assert result.get("motor_suggestions") or "candidato" in (result.get("message") or "").lower()


def test_offer_catalog_help_is_public_session_entry_point(tmp_path: Path):
    """FN-006: offer_catalog_help() takes no args and resolves the runtime session itself."""
    orch = _energy_project(tmp_path)
    session = orch.param_definition_session

    assert hasattr(session, "offer_catalog_help")
    assert hasattr(session, "_offer_catalog_help")  # private worker still present, reused internally

    orch.start_define_missing_params(
        ["motor_power_w", "battery_capacity_wh"], reason=MISSING_ENERGY_PARAMETERS
    )
    result = session.offer_catalog_help()
    assert result["status"] == "interactive"
    assert result.get("action") == "define_missing_params"
    assert result.get("motor_suggestions") or "catálogo" in (result.get("message") or "").lower()
    assert result.get("pending") == ["motor_power_w", "battery_capacity_wh"]


def test_format_candidate_line_detailed_and_quick_forms():
    """FN-006: _format_candidate_line is the single source of candidate-line text
    for both the full catalog listing and the inline quick menu."""
    suggestion = {
        "idx": 1,
        "name": "demo_motor",
        "thrust_n": 12.0,
        "weight_g": 55.0,
        "kv_rating": 900,
        "max_watts": 280,
        "is_generic": False,
    }
    full = format_motor_catalog_suggestions([suggestion])
    assert "1. demo_motor  →  12.0N, 55.0g, 900KV, ~280W" in full

    quick = assisted_motor_power_question([suggestion], thrust_hint_n=4.7)
    assert "1. demo_motor  →  12.0N, ~280W" in quick
    # Quick form must not leak the detailed fields (weight/KV)
    assert "55.0g" not in quick
    assert "900KV" not in quick


def test_model_with_digits_does_not_apply_garbage_watts(tmp_path: Path):
    orch = _energy_project(tmp_path)
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    result = orch.handle_user_text("T-Motor MN3508 KV700", llm_interface=None)
    assert result["status"] == "interactive"
    assert result.get("error")
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_power_w") is None


def test_bare_watts_still_applies(tmp_path: Path):
    orch = _energy_project(tmp_path)
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    result = orch.param_definition_session.answer("350")
    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_power_w") == pytest.approx(350.0)


def test_define_wizard_pick_applies_watts(tmp_path: Path):
    orch = _energy_project(tmp_path)
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    help_result = orch.param_definition_session.answer("ayúdame a elegir")
    suggestions = help_result.get("motor_suggestions") or []
    if not suggestions:
        pytest.skip("no catalog matches for fixture thrust band")
    pick = orch.param_definition_session.answer("1")
    assert pick["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_power_w") == pytest.approx(
        float(suggestions[0]["max_watts"])
    )
    motors = saved.design_properties.components.get("motors")
    assert motors is not None
    assert "thrust_n" in (motors.properties or {})


def test_catalog_key_as_model_applies(tmp_path: Path):
    orch = _energy_project(tmp_path)
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    motors = default_library.list_motors()
    # Pick a motor that covers ~4N band if possible, else first
    name = motors[0].name
    watts = motors[0].max_watts
    result = orch.param_definition_session.answer(name)
    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_power_w") == pytest.approx(float(watts))


def test_match_suggestion_by_number():
    sugg = [{"idx": 2, "name": "foo", "max_watts": 100}]
    assert match_suggestion_by_input("2", sugg)["name"] == "foo"


def test_continuity_prefers_motor_assist_when_power_missing():
    state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 4.0,
                "can_fly": True,
                "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress="2/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 4.7},
        component_bom={
            "defined": [],
            "incomplete": [{"key": "motors", "missing_fields": ["empuje"]}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[{"name": "sunnysky_x2216_11"}],
    )
    assert (
        "ayúdame a elegir" in cont["next_useful_step"].lower()
        or "potencia" in cont["next_useful_step"].lower()
    )
    assert "completa la especificación de motors" not in cont["next_useful_step"].lower()
