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
from jarvis.core.parameter_requirements import (
    MISSING_ENERGY_PARAMETERS,
    MISSING_PROPULSION_PARAMETERS,
    param_question,
)
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


def _propulsion_missing_project(
    tmp_path: Path, *, payload_kg: float = 3.5, motors: int = 4
) -> JarvisOrchestrator:
    """FN-009: aerial project with motor_count declared but no thrust route at
    all (mirrors the 'detallado' create flow choosing 'no sé aún' for
    propulsion) — physics_status ends up missing_parameters /
    missing_propulsion_parameters."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": payload_kg,
            "restrictions": "ninguna",
            "detail_level": "detallado",
            "motors": motors,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
            # per_motor_max_thrust_n intentionally absent — no force route at all
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


def test_fn007_catalog_pick_applies_coherent_bundle_no_false_gap(tmp_path: Path):
    """FN-007 acceptance scenario: before=count 4 / stale thrust 470N, pick sunnysky_x2212_980
    (11N, 260W, 980KV, 58g — real catalog entry). After the pick: motor_count stays 4
    (not collapsed to 1), stale thrust is replaced (not left at 470), available total
    thrust = 4 x 11 = 44N, and continuity does not flag the picked candidate as
    insufficient (no false catalog gap)."""
    orch = _energy_project(tmp_path)
    before = orch.state_manager.load_active_project(orch.workspace_manager)
    assert before.current_parameters.get("motor_count") == 4
    assert "motors" not in before.design_properties.components

    # Simulate a stale thrust value already on disk before the new pick.
    stale_params = {**before.current_parameters, "per_motor_max_thrust_n": 470.0}
    orch.workspace_manager.save_state(before.model_copy(update={"current_parameters": stale_params}))

    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    result = orch.param_definition_session.answer("sunnysky_x2212_980")
    assert result["status"] == "ok"

    after = orch.state_manager.load_active_project(orch.workspace_manager)

    # count 4 does not change to 1
    assert after.current_parameters["motor_count"] == 4
    assert after.design_properties.components["motors"].properties["motor_count"].value == 4

    # stale thrust is replaced by the picked motor's, not left at 470
    assert after.current_parameters["per_motor_max_thrust_n"] == pytest.approx(11.0)
    assert after.current_parameters["motor_power_w"] == pytest.approx(260.0)

    # coherent bundle: KV + weight land on the component too
    motors_props = after.design_properties.components["motors"].properties
    assert motors_props["kv_rating"].value == 980
    assert motors_props["weight_g"].value == pytest.approx(58.0)

    # total disponible = 4 x 11
    assert result["calculations"]["available_total_thrust_n"] == pytest.approx(44.0)

    # continuity must not declare the just-selected candidate insufficient
    ctx = orch.build_startup_context()
    assert ctx.get("motor_catalog_gap") is None


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


def test_continuity_catalog_bound_motor_without_watts_points_at_next_bom_gap():
    """Field: emax_rs2205s_2300 is bound (no nameplate W) but Continuity still
    said 'elige un motor / declara W' because motor_catalog_matches listed the
    same SKU. Next step must be the real BOM gap (propellers)."""
    from jarvis.schemas.action_schema import CatalogRef, ComponentSpec

    motors = ComponentSpec(
        name="emax_rs2205s_2300",
        component_type="propulsion_active",
        completeness="high",
        source="declared",
        catalog_ref=CatalogRef(family="motor", sku="emax_rs2205s_2300"),
    )
    state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 1.98,
                "can_fly": True,
                "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4, "per_motor_max_thrust_n": 10.042},
        design_properties=SimpleNamespace(components={"motors": motors}),
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress="1/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 5.06},
        component_bom={
            "defined": [{"key": "motors"}],
            "incomplete": [{"key": "propellers", "missing_fields": ["incompleto"]}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[{"name": "emax_rs2205s_2300"}],
    )
    step = (cont["next_useful_step"] or "").lower()
    why = (cont.get("next_why") or "").lower()
    assert "propellers" in step
    assert "elige un motor" not in step
    assert "motor_power_w" not in why


# ── FN-009: guided propulsion acquisition ──────────────────────────────────────

def test_fn009_offer_catalog_help_thrust_pending_uses_n_copy_not_watts(tmp_path: Path):
    """PASS WITH NOTES follow-up: cuando lo pendiente es per_motor_max_thrust_n,
    _offer_catalog_help debe hablar de empuje en N / combo motor-hélice, nunca
    de potencia en W — ni en 'question' ni en la línea final de 'message'."""
    orch = _propulsion_missing_project(tmp_path)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    result = orch.param_definition_session.offer_catalog_help()
    assert result.get("motor_suggestions"), "se esperaba cobertura real de catálogo"

    question = result["question"]
    message = result["message"]
    assert "empuje en n" in question.lower()
    assert "combinación motor-hélice" in question.lower()
    assert " w " not in f" {question.lower()} "
    assert "indica w a mano" not in message.lower()


def test_fn009_offer_catalog_help_power_pending_keeps_watts_copy(tmp_path: Path):
    """Cuando lo pendiente es motor_power_w, el copy en W se conserva exactamente
    como antes (sin regresión sobre el flujo existente)."""
    orch = _energy_project(tmp_path)  # thrust ya declarado; motor_power_w pendiente
    orch.start_define_missing_params(["motor_power_w"], reason=MISSING_ENERGY_PARAMETERS)
    result = orch.param_definition_session.offer_catalog_help()
    assert result.get("motor_suggestions"), "se esperaba cobertura real de catálogo"

    assert result["question"] == "Elige un número de la lista, o indica W a mano."
    # G16-B (CLI polish): the "Elige un número..." CTA now lives only in
    # `question` — `message` no longer repeats it (previously both message
    # and question showed the same instruction, G16-B's own duplication bug).
    assert "indica w a mano" not in result["message"].lower()
    assert "empuje en n" not in result["question"].lower()


def test_fn009_thrust_wizard_shows_provisional_minimum(tmp_path: Path):
    """Acceptance case: payload 3.5kg, factor 0.6, safety 1.2, 4 motores →
    mínimo provisional ≈16.5 N/motor, explícitamente marcado como provisional
    y acoplado a la batería."""
    orch = _propulsion_missing_project(tmp_path)
    start = orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    assert start["status"] == "interactive"
    assert "16.5" in start["question"]
    assert "provisional" in start["question"].lower()
    assert "bater" in start["question"].lower()


def test_fn009_idle_thrust_help_never_says_no_reconozco(tmp_path: Path):
    """'ayúdame a elegir el motor' nunca debe caer en el error genérico
    'No reconozco ... como valor', aunque lo pendiente sea empuje y no potencia."""
    orch = _propulsion_missing_project(tmp_path)
    result = orch.handle_user_text("ayúdame a elegir el motor", llm_interface=None)
    assert result.get("status") == "interactive"
    assert result.get("action") == "define_missing_params"
    assert "no reconozco" not in (result.get("error") or "").lower()
    assert "no reconozco" not in (result.get("message") or "").lower()
    assert result.get("motor_suggestions")  # el catálogo real cubre ~16.5 N/motor


def test_fn009_idle_help_prioritizes_propulsion_over_energy(tmp_path: Path):
    """Cuando faltan tanto empuje como energía, la ayuda IDLE debe abrir primero
    el asistente de propulsión, no saltar directo a energía."""
    orch = _propulsion_missing_project(tmp_path)
    result = orch.handle_user_text("ayúdame a elegir el motor", llm_interface=None)
    assert result.get("status") == "interactive"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_PROPULSION_PARAMETERS
    assert session.pending_param_definitions == ["per_motor_max_thrust_n"]


def test_fn009_idle_help_falls_back_to_energy_once_propulsion_resolved(tmp_path: Path):
    """Con el empuje ya resuelto (physics válida), la ayuda IDLE conserva la
    ruta energética existente sin cambios."""
    orch = _energy_project(tmp_path)  # thrust=12.0 declarado, potencia/batería ausentes
    result = orch.handle_user_text("ayúdame a elegir el motor", llm_interface=None)
    assert result.get("status") == "interactive"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_ENERGY_PARAMETERS


def test_fn009_no_thrust_candidate_gives_honest_deterministic_gap(tmp_path: Path):
    """Cuando ningún motor del catálogo cubre el requisito, la respuesta debe ser
    determinista: requisito, cobertura máxima del catálogo y opciones concretas
    — sin inventar SKU ni mutar motor_count."""
    orch = _propulsion_missing_project(tmp_path, payload_kg=20.0, motors=4)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    result = orch.param_definition_session.offer_catalog_help()
    assert result["status"] == "interactive"
    assert result.get("motor_suggestions") == []
    message = (result.get("message") or "").lower()
    assert "no tengo un motor en el catálogo" in message
    assert "opciones" in message
    assert "más motores" in message
    assert "fuera de catálogo" in message or "combinación" in message
    assert "no voy a inventar" in message

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == 4  # sin mutar
    assert saved.current_parameters.get("per_motor_max_thrust_n") is None  # nada inventado


def test_fn009_catalog_pick_resolves_thrust_only_pending_without_looping(tmp_path: Path):
    """Wizard con pending=['per_motor_max_thrust_n'] únicamente: un pick de
    catálogo debe resolverlo (sin bucle infinito), recalcular una sola vez y
    preservar motor_count."""
    orch = _propulsion_missing_project(tmp_path)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    help_result = orch.param_definition_session.answer("ayúdame a elegir")
    suggestions = help_result.get("motor_suggestions") or []
    assert suggestions, "se esperaba cobertura real de catálogo para ~16.5 N/motor"

    pick = orch.param_definition_session.answer("1")
    assert pick["status"] == "ok"  # resuelto en un solo turno, no se queda pidiendo de nuevo

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == 4
    assert saved.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        float(suggestions[0]["thrust_n"])
    )
    assert saved.current_parameters.get("motor_power_w") == pytest.approx(
        float(suggestions[0]["max_watts"])
    )
    assert pick["calculations"]["available_total_thrust_n"] == pytest.approx(
        4 * float(suggestions[0]["thrust_n"])
    )

    ctx = orch.build_startup_context()
    assert ctx.get("motor_catalog_gap") is None


def test_catalog_pick_verified_motor_without_nominal_watts_does_not_crash(tmp_path: Path):
    """Field: pick #5 ``emax_rs2205s_2300`` (max_watts is None by catalog
    contract) crashed DEFINE_MISSING confirmation with ``int(None)``.
    The numbered pick was already matched; only the copy assumed watts.
    """
    from jarvis.core.motor_catalog_assist import (
        format_motor_change_summary,
        format_motor_chosen_line,
    )

    no_w = {
        "idx": 5,
        "name": "emax_rs2205s_2300",
        "thrust_n": 10.042,
        "kv_rating": 2300,
        "weight_g": 30.0,
        "max_watts": None,
        "is_generic": False,
    }
    msg = format_motor_chosen_line(no_w, recalculated=True)
    assert "emax_rs2205s_2300" in msg
    assert "10.042" in msg
    assert "None" not in msg
    assert "~" not in msg
    assert format_motor_change_summary(no_w) == "motor → emax_rs2205s_2300"

    orch = _propulsion_missing_project(tmp_path, payload_kg=1.0)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    help_result = orch.param_definition_session.answer("ayúdame a elegir")
    suggestions = help_result.get("motor_suggestions") or []
    target = next((s for s in suggestions if s["name"] == "emax_rs2205s_2300"), None)
    assert target is not None, "expected emax_rs2205s_2300 in the 1 kg / 4-motor list"
    assert target["max_watts"] is None

    pick = orch.param_definition_session.answer(str(target["idx"]))
    assert pick.get("status") != "error"
    assert "int()" not in (pick.get("message") or "")
    assert "emax_rs2205s_2300" in (pick.get("message") or "")
    assert "~None" not in (pick.get("message") or "")

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = saved.design_properties.components["motors"]
    assert motors.catalog_ref is not None
    assert motors.catalog_ref.sku == "emax_rs2205s_2300"
    assert saved.current_parameters.get("motor_power_w") is None
    assert saved.current_parameters.get("per_motor_max_thrust_n") == pytest.approx(
        float(target["thrust_n"])
    )


def test_fn009_continuity_marks_thrust_requirement_as_provisional_without_battery():
    """La línea de evidencia de requisito debe marcar honestamente que es un
    mínimo provisional mientras la batería no esté declarada."""
    state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass", "quality": "good", "safety_margin_ratio": 2.0,
                "can_fly": True, "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},  # sin battery_capacity_wh
        design_properties=SimpleNamespace(components={}),
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 16.48},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
    )
    evidence_text = " ".join(cont["evidence"])
    assert "16.48" in evidence_text
    assert "provisional" in evidence_text.lower()


def test_fn009_continuity_no_provisional_note_once_battery_declared():
    """Una vez declarada la batería, la línea de requisito ya no se marca como
    provisional."""
    state = SimpleNamespace(
        latest_results={
            "simulation": {
                "status": "pass", "quality": "good", "safety_margin_ratio": 2.0,
                "can_fly": True, "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4, "battery_capacity_wh": 500.0},
        design_properties=SimpleNamespace(components={}),
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 16.48},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
    )
    evidence_text = " ".join(cont["evidence"])
    assert "16.48" in evidence_text
    assert "provisional" not in evidence_text.lower()
