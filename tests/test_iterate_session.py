import pytest

from jarvis.core.iterate_interactive_session import IterateInteractiveSession
from jarvis.schemas.action_schema import (
    ImpactEstimate,
    InteractiveSessionState,
    IterationDraft,
    IterationOperation,
    OrchestratorMode,
)


def _session_from_response(response: dict) -> InteractiveSessionState:
    return InteractiveSessionState(
        mode=OrchestratorMode(response["mode"]),
        step=response["step"],
        iteration_draft=IterationDraft.model_validate(response["iteration_draft"]),
    )


def test_iterate_session_flow_reaches_confirmation():
    session = IterateInteractiveSession()

    start = session.start(
        {
            "project_id": "abc123",
            "project_slug": "dron-base",
            "workspace_path": "/tmp/dron-base-abc123",
            "objetivo": "peso",
            "operacion": "reducir",
        }
    )
    assert start["status"] == "interactive"
    assert start["mode"] == OrchestratorMode.ITERATE_INTERACTIVE.value
    assert start["step"] == 0
    assert "Proyecto activo: dron-base" in start["message"]
    assert "Quieres reducir peso" in start["message"]

    current = _session_from_response(start)

    answer_1 = session.answer(current, "sí")
    assert answer_1["step"] == 1
    current = _session_from_response(answer_1)

    answer_2 = session.answer(current, "material")
    assert answer_2["step"] == 2
    current = _session_from_response(answer_2)

    # strategy "cambiar material" triggers Gap 1: ask which material
    answer_3 = session.answer(current, "cambiar material")
    assert answer_3["step"] == 2  # still at step 2 — awaiting material name
    current = _session_from_response(answer_3)

    # user names the material → advances to step 3 (restrictions)
    answer_3b = session.answer(current, "fibra de carbono")
    assert answer_3b["step"] == 3
    current = _session_from_response(answer_3b)

    # restrictions answer advances to step 4 with impact estimate attached
    answer_4 = session.answer(current, "ninguna")
    assert answer_4["step"] == 4
    # aluminio(2700)→fibra de carbono(1600), structural_fraction=0.25 → ~-10.2%
    assert "peso: -10.2%" in answer_4["message"]
    current = _session_from_response(answer_4)

    answer_5 = session.answer(current, "sí")
    assert answer_5["step"] == 5
    assert answer_5["question"] == "¿Confirmas la iteración?"
    current = _session_from_response(answer_5)

    confirmed = session.answer(current, "sí")
    assert confirmed["status"] == "confirmed"
    assert confirmed["iteration_draft"]["variable"] == "material"
    assert confirmed["iteration_draft"]["impact_estimate"]["thrust_impact"] == "positivo"


def test_iterate_session_can_return_to_editing_after_impact_estimate():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "peso",
                "operacion": "reducir",
            }
        )
    )
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "componentes"))
    # strategy always advances to step 3 (restrictions)
    at_restrictions = session.answer(current, "optimizar estructura")
    assert at_restrictions["step"] == 3
    current = _session_from_response(at_restrictions)

    # answer restrictions to reach apply decision
    impact = session.answer(current, "ninguna")
    assert impact["step"] == 4
    current = _session_from_response(impact)

    back_to_edit = session.answer(current, "no")

    assert back_to_edit["status"] == "interactive"
    assert back_to_edit["step"] == 1
    assert "corregir" in back_to_edit["message"].lower()


def test_iterate_session_detects_conflict_with_initial_goal():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "carga",
                "operacion": "aumentar",
            }
        )
    )
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "carga"))
    conflict = session.answer(current, "reducir carga")

    assert conflict["status"] == "interactive"
    assert conflict["step"] == 2
    assert "Detecto una inconsistencia" in conflict["message"]
    assert "1. mantener el objetivo inicial" in conflict["question"]


def test_iterate_session_can_cancel_after_conflict():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "carga",
                "operacion": "aumentar",
            }
        )
    )
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "carga"))
    conflict = session.answer(current, "reducir carga")
    current = _session_from_response(conflict)

    cancelled = session.answer(current, "3")

    assert cancelled["status"] == "cancelled"
    assert "conflicto" in cancelled["message"].lower()


def test_iterate_session_accepts_textual_resolution_for_keep_initial_goal():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "carga",
                "operacion": "aumentar",
            }
        )
    )
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "carga"))
    conflict = session.answer(current, "reducir carga")
    current = _session_from_response(conflict)

    resolved = session.answer(current, "mantener el objetivo inicial")

    assert resolved["status"] == "interactive"
    assert resolved["step"] == 2
    assert "Mantendremos el objetivo inicial" in resolved["message"]


def test_iterate_session_accepts_textual_resolution_for_cancel():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "carga",
                "operacion": "aumentar",
            }
        )
    )
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "carga"))
    conflict = session.answer(current, "reducir carga")
    current = _session_from_response(conflict)

    cancelled = session.answer(current, "cancelar iteración")

    assert cancelled["status"] == "cancelled"


def test_iterate_session_material_definition_avoids_numeric_impact():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "material",
                "operacion": "define",
                "variable": "material",
            }
        )
    )

    current = _session_from_response(session.answer(current, "sí"))
    assert current.step == 2

    current = _session_from_response(session.answer(current, "fibra de carbono"))
    impact = session.answer(current, "mantener resistencia")

    assert impact["step"] == 4
    assert "- peso:" in impact["message"]
    assert "fibra de carbono" in impact["message"].lower()


def test_iterate_session_components_definition_requires_explicit_value():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "objetivo": "sistema de potencia",
                "operacion": "define",
                "variable": "componentes",
            }
        )
    )

    step_1 = session.answer(current, "sí")
    assert "¿Qué componentes quieres usar en la unidad de potencia?" in step_1["question"]

    current = _session_from_response(step_1)
    step_2 = session.answer(current, "motores brushless + esc 30a")
    assert step_2["step"] == 3
    assert step_2["iteration_draft"]["value"] == "motores brushless + esc 30a"


def test_iterate_session_components_prompt_is_generic_without_power_unit_context():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "operacion": "define",
                "variable": "componentes",
            }
        )
    )

    step_1 = session.answer(current, "sí")
    assert "¿Qué componentes quieres definir?" in step_1["question"]


def test_iterate_session_define_defaults_objective_when_missing():
    session = IterateInteractiveSession()

    start = session.start(
        {
            "project_id": "abc123",
            "project_slug": "dron-base",
            "workspace_path": "/tmp/dron-base-abc123",
            "operacion": "define",
            "variable": "componentes",
        }
    )

    assert start["iteration_draft"]["objective"] == "definición declarativa"


def test_iterate_session_accepts_generic_components_value_and_provides_guidance():
    session = IterateInteractiveSession()

    current = _session_from_response(
        session.start(
            {
                "project_id": "abc123",
                "project_slug": "dron-base",
                "workspace_path": "/tmp/dron-base-abc123",
                "operacion": "define",
                "variable": "componentes",
            }
        )
    )

    current = _session_from_response(session.answer(current, "sí"))
    response = session.answer(current, "motores")

    assert response["step"] == 3
    assert "Guardado:" in response["message"]
    assert "Nivel de definición" in response["message"]


def test_focus_aware_spec_not_split_into_multiple_entities():
    """
    Regression: when focus is set (enriching a component), comma-separated
    technical properties ("4 motores 920KV, 15N") must NOT trigger multi-entity
    split. The full text must be passed to infer_component as a single spec.
    """
    from jarvis.schemas.action_schema import ComponentSpec, InteractiveSessionState, IterationDraft, OrchestratorMode
    from jarvis.schemas.semantic_schema import SemanticState

    existing_motor = ComponentSpec(
        name="motors",
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="low",
        missing_fields=["número de motores"],
    )

    # Build session state directly with focus="motor" so focus is preserved
    semantic = SemanticState(focus="motor")
    draft = IterationDraft(
        project_id="abc123",
        project_slug="dron-base",
        workspace_path="/tmp/dron-base-abc123",
        objective="definición declarativa",
        operation="define",
        variable="componentes",
        component_patch={"motors": existing_motor},
    )
    current = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=draft,
        semantic_state=semantic,
    )

    session = IterateInteractiveSession()
    response = session.answer(current, "4 motores brushless 920KV, 15N de empuje por motor")

    # Must NOT produce a pending_entities split — should go straight to step 3
    assert response.get("pending_entities") == [], (
        "focus-aware input should not be split into multiple entities"
    )
    assert response["step"] == 3

    # The stored component patch must have structured properties
    patch = response["iteration_draft"].get("component_patch") or {}
    assert "motors" in patch
    motors = patch["motors"]
    props = motors.get("properties") or {}
    assert "motor_count" in props, "motor_count must be extracted"
    assert props["motor_count"]["value"] == 4
    assert "thrust_n" in props, "thrust_n must be extracted"
    assert props["thrust_n"]["value"] == 15.0
    assert motors["completeness"] == "high"


# ── Gap 1: material capture ─────────────────────────────────────────────────

def test_material_step_asks_for_material_when_not_in_strategy():
    """'cambiar material' without a material name must keep session at step 2."""
    session = IterateInteractiveSession()
    start = session.start(
        {
            "project_id": "t1",
            "project_slug": "dron",
            "workspace_path": "/tmp/t1",
            "objetivo": "peso",
            "operacion": "reducir",
        }
    )
    s = _session_from_response(start)
    s = _session_from_response(session.answer(s, "sí"))
    s = _session_from_response(session.answer(s, "material"))
    resp = session.answer(s, "cambiar material")
    assert resp["step"] == 2, "must stay at step 2 awaiting material name"
    assert "material" in resp["message"].lower()


def test_material_step_name_embedded_in_strategy_advances_directly():
    """'cambiar a fibra de carbono' contains the material → go to step 3."""
    session = IterateInteractiveSession()
    start = session.start(
        {
            "project_id": "t2",
            "project_slug": "dron",
            "workspace_path": "/tmp/t2",
            "objetivo": "peso",
            "operacion": "reducir",
        }
    )
    s = _session_from_response(start)
    s = _session_from_response(session.answer(s, "sí"))
    s = _session_from_response(session.answer(s, "material"))
    resp = session.answer(s, "cambiar a fibra de carbono")
    assert resp["step"] == 3, "material in strategy text must advance to restrictions"


def test_material_draft_value_set_after_naming_material():
    """After naming the material, draft.value must be set to the canonical name."""
    session = IterateInteractiveSession()
    start = session.start(
        {
            "project_id": "t3",
            "project_slug": "dron",
            "workspace_path": "/tmp/t3",
            "objetivo": "peso",
            "operacion": "reducir",
        }
    )
    s = _session_from_response(start)
    s = _session_from_response(session.answer(s, "sí"))
    s = _session_from_response(session.answer(s, "material"))
    s = _session_from_response(session.answer(s, "cambiar material"))  # stays at 2
    resp = session.answer(s, "titanio")
    assert resp["step"] == 3
    assert resp["iteration_draft"]["value"] == "titanio"


# ── Gap 2: structural downgrade ─────────────────────────────────────────────

def test_structural_iteration_without_value_downgraded_to_declarative():
    """'optimizar estructura' without a concrete value → operation downgraded to DEFINE."""
    from jarvis.schemas.action_schema import InteractiveSessionState, IterationDraft, OrchestratorMode
    from jarvis.schemas.semantic_schema import SemanticState

    draft = IterationDraft(
        project_id="t4",
        project_slug="dron",
        workspace_path="/tmp/t4",
        objective="reducir peso",
        operation="reducir",
        variable="estructura",
        strategy="optimizar estructura",
    )
    current = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=3,
        iteration_draft=draft,
        semantic_state=SemanticState(),
    )
    session = IterateInteractiveSession()
    resp = session.answer(current, "ninguna")
    assert resp["step"] == 4
    assert resp["iteration_draft"]["operation"] == "define", (
        "structural iteration without concrete value must be downgraded to DEFINE"
    )
    assert "concreto" in resp["iteration_draft"]["impact_estimate"]["summary"].lower()


# ── Motor suggestion sub-step ────────────────────────────────────────────────

def _start_define_session(session: IterateInteractiveSession, project_id: str = "m1") -> InteractiveSessionState:
    """Helper: start a DEFINE session and advance to the component spec step."""
    start = session.start(
        {
            "project_id": project_id,
            "project_slug": "dron",
            "workspace_path": f"/tmp/{project_id}",
            "objetivo": "definición declarativa",
            "operacion": "define",
            "variable": "componentes",
            "enrich_component": "motors",
        }
    )
    return _session_from_response(start)


def test_motor_kv_without_thrust_triggers_suggestion_not_autoset():
    """Defining a motor with KV but no thrust must show suggestions and stay at step 2."""
    session = IterateInteractiveSession()
    s = _start_define_session(session)
    # Define 4 motors 920KV — no thrust declared
    resp = session.answer(s, "4 motores 920KV")
    # Must stay at step 2 waiting for motor selection
    assert resp["step"] == 2, "KV-only motor must stay at step 2 for motor suggestion"
    assert "920" in resp["message"] or "motor" in resp["message"].lower()
    # draft must NOT have thrust_n auto-set
    draft = resp["iteration_draft"]
    patch = draft.get("component_patch") or {}
    for spec_data in patch.values():
        props = spec_data.get("properties") or {}
        assert "thrust_n" not in props, "thrust_n must NOT be auto-set from KV alone"


def test_motor_kv_suggestion_user_picks_option():
    """User picks a suggestion number → thrust_n applied and session advances to step 3."""
    session = IterateInteractiveSession()
    s = _start_define_session(session, "m2")
    resp = session.answer(s, "4 motores 920KV")
    assert resp["step"] == 2
    suggestions = resp.get("motor_suggestions") or []
    assert len(suggestions) > 0, "must have motor suggestions when KV known but no thrust"

    # Rebuild session with motor_suggestions from response
    from jarvis.schemas.action_schema import InteractiveSessionState as ISS
    s2 = ISS.model_validate({
        "mode": resp["mode"],
        "step": resp["step"],
        "iteration_draft": resp["iteration_draft"],
        "motor_suggestions": suggestions,
    })
    resp2 = session.answer(s2, "1")
    assert resp2["step"] == 3, "picking a motor suggestion must advance to restrictions"
    patch = resp2["iteration_draft"].get("component_patch") or {}
    # Verify thrust_n and weight_g were added while original properties survive
    for spec_data in patch.values():
        props = spec_data.get("properties") or {}
        if "kv_rating" in props:  # this is our motor
            assert props.get("thrust_n", {}).get("value") is not None, "thrust_n must be set"
            assert props.get("weight_g", {}).get("value") is not None, "weight_g must be set"
            assert "kv_rating" in props, "original kv_rating must be preserved"


def test_motor_kv_suggestion_user_declines():
    """User says 'no' → advances to step 3 without thrust_n."""
    from jarvis.schemas.action_schema import InteractiveSessionState as ISS
    session = IterateInteractiveSession()
    s_with_suggestions = ISS.model_validate({
        "mode": OrchestratorMode.ITERATE_INTERACTIVE.value,
        "step": 2,
        "iteration_draft": IterationDraft(
            project_id="m3",
            project_slug="dron",
            workspace_path="/tmp/m3",
            objective="definición declarativa",
            operation="define",
            variable="componentes",
            value="4 motores 920KV",
        ).model_dump(),
        "motor_suggestions": [
            {"idx": 1, "name": "generic_920kv", "thrust_n": 10.0, "kv_rating": 920, "weight_g": 65}
        ],
    })
    resp = session.answer(s_with_suggestions, "no")
    assert resp["step"] == 3, "declining suggestions must advance to step 3"
    # No thrust_n should have been injected
    patch = resp["iteration_draft"].get("component_patch") or {}
    for spec_data in patch.values():
        props = spec_data.get("properties") or {}
        assert "thrust_n" not in props


def test_motor_with_thrust_declared_skips_suggestion():
    """If thrust_n is already declared, no suggestion loop must be entered."""
    session = IterateInteractiveSession()
    s = _start_define_session(session, "m4")
    resp = session.answer(s, "4 motores 920KV 15N")
    # Should go directly to step 3 — thrust declared, no suggestions needed
    assert resp["step"] == 3, "motor with explicit thrust_n must skip suggestion sub-step"


def test_motor_kv_empty_catalog_explains_and_advances():
    """KV with no library match must not silence the gap — note + step 3."""
    session = IterateInteractiveSession()
    s = _start_define_session(session, "m_empty")
    resp = session.answer(s, "4 motores 6000KV")
    assert resp["step"] == 3
    assert resp.get("motor_suggestions") in (None, [])
    message = resp.get("message") or ""
    assert "6000" in message
    assert "catálogo" in message.lower() or "catalogo" in message.lower() or "empuje" in message.lower()
    assert "empuje" in message.lower()


def test_non_motor_component_with_kv_does_not_trigger_suggestion():
    """A non-motor component (e.g. battery/generic) with a numeric property
    must never enter the motor suggestion sub-step."""
    from jarvis.core.iterate_interactive_session import IterateInteractiveSession
    from jarvis.knowledge.library import ComponentLibrary
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

    session = IterateInteractiveSession()
    # Build a spec that has kv_rating but is NOT propulsion_active
    fake_spec = ComponentSpec(
        name="battery",
        component_type="power_control",  # not propulsion_active
        suggested_key="battery",
        properties={"kv_rating": PropertyValue(value=920.0, unit="KV")},
    )
    suggestions = session._build_motor_suggestions(fake_spec)
    assert suggestions == [], "non-motor component must never produce motor suggestions"


def test_stale_motor_suggestions_cleared_when_step_not_2():
    """Motor suggestions that somehow survive past step 2 must be purged on next answer call.
    Simulates the zombie state: step=3 but motor_suggestions still populated."""
    from jarvis.schemas.action_schema import InteractiveSessionState as ISS

    session = IterateInteractiveSession()
    # Build a zombie state: step 3 with stale motor_suggestions
    zombie = ISS.model_validate({
        "mode": OrchestratorMode.ITERATE_INTERACTIVE.value,
        "step": 3,
        "iteration_draft": IterationDraft(
            project_id="z1",
            project_slug="dron",
            workspace_path="/tmp/z1",
            objective="definición declarativa",
            operation="define",
            variable="componentes",
            value="4 motores 920KV",
        ).model_dump(),
        "motor_suggestions": [
            {"idx": 1, "name": "generic_920kv", "thrust_n": 10.0, "kv_rating": 920, "weight_g": 65}
        ],
    })
    # Answer step 3 (restrictions) — must NOT enter motor suggestion sub-loop
    resp = session.answer(zombie, "sin restricciones")
    assert resp["step"] == 4, "stale motor_suggestions at step 3 must not block step advance"
    assert resp.get("motor_suggestions") == [], "stale suggestions must be cleared"


# ── Numeric parameter mutation ────────────────────────────────────────────────

def _make_session_at_step2_numeric(variable: str, current_parameters: dict) -> InteractiveSessionState:
    """Helper: build a session at step 2 with a numeric variable and current_parameters in memory_context."""
    draft = IterationDraft(
        project_id="np1",
        project_slug="dron-base",
        workspace_path="/tmp/np1",
        objective="reducir peso",
        operation="reducir",
        variable=variable,
    )
    return InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=draft,
        memory_context={"current_parameters": current_parameters},
    )


def test_numeric_param_display_alias_skips_to_impact():
    """factor_estructura (ES alias) → wizard asks for value, goes directly to step 4."""
    session = IterateInteractiveSession()
    current = _make_session_at_step2_numeric(
        "factor_estructura", {"structure_mass_factor": 0.6, "safety_factor": 1.2}
    )
    # Question at step 2 must ask for new value, not strategy
    question = session._question_for_session(current, "fallback")
    assert "factor_estructura" in question
    assert "0.6" in question

    # User gives new value → should jump to step 4
    resp = session.answer(current, "0.45")
    assert resp["step"] == 4
    assert resp["iteration_draft"]["value"] == "0.45"
    assert resp["iteration_draft"]["operation"] == "reducir"
    assert "0.6" in resp["iteration_draft"]["impact_estimate"]["summary"]
    assert "0.45" in resp["iteration_draft"]["impact_estimate"]["summary"]


def test_numeric_param_direct_key_match():
    """motors (direct key) → same numeric param flow."""
    session = IterateInteractiveSession()
    current = _make_session_at_step2_numeric(
        "motor_count", {"motor_count": 4.0, "structure_mass_factor": 0.6}
    )
    resp = session.answer(current, "6")
    assert resp["step"] == 4
    assert resp["iteration_draft"]["value"] == "6.0"


def test_numeric_param_invalid_value_re_asks():
    """Non-numeric input → re-ask with error, stay at step 2."""
    session = IterateInteractiveSession()
    current = _make_session_at_step2_numeric(
        "factor_estructura", {"structure_mass_factor": 0.6}
    )
    resp = session.answer(current, "fibra de carbono")
    assert resp["step"] == 2
    assert "error" in resp
    assert "numérico" in resp["error"]


def test_should_downgrade_not_triggered_for_numeric_param_with_value():
    """_should_downgrade_to_declarative must be False when variable is numeric and value is set."""
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation
    session = IterateInteractiveSession()
    draft = IterationDraft(
        variable="factor_estructura",
        value="0.45",
        operation=IterationOperation.REDUCE,
    )
    assert not session._should_downgrade_to_declarative(draft)


def test_mutation_engine_applies_numeric_param():
    """apply_numeric_param_mutation patches current_parameters with canonical key."""
    from jarvis.core.mutation_engine import MutationEngine
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation

    engine = MutationEngine()
    draft = IterationDraft(
        variable="factor_estructura",
        value="0.45",
        operation=IterationOperation.REDUCE,
        strategy="establecer factor_estructura = 0.45",
    )
    state = {"vehicle_type": "dron", "payload_kg": 2.0}
    mutated, impact = engine.apply_mutation(state, draft)
    assert mutated == {"current_parameters": {"structure_mass_factor": 0.45}}


def test_apply_mutation_removes_override_when_factor_patched():
    """_apply_mutation_to_parameters clears structure_mass_override_kg when structure_mass_factor is patched."""
    from jarvis.actions.iterate import IterateAction
    from unittest.mock import MagicMock

    action = IterateAction(
        workspace_manager=MagicMock(),
        state_manager=MagicMock(),
        simulator=MagicMock(),
        calculation_engine=MagicMock(),
        mutation_engine=MagicMock(),
        suggestion_engine=MagicMock(),
        reasoning_layer=MagicMock(),
    )
    current = {
        "payload_kg": 2.0,
        "structure_mass_factor": 0.6,
        "structure_mass_override_kg": 0.72,
    }
    mutated = {"current_parameters": {"structure_mass_factor": 0.45}}
    result = action._apply_mutation_to_parameters(current, mutated)
    assert result["structure_mass_factor"] == 0.45
    assert "structure_mass_override_kg" not in result


# ── Bug 25 — pre-execution guard in IterateAction.run() ───────────────────────

def _make_iterate_action_with_mock_project(project_id: str = "pid-1"):
    """Return an IterateAction wired to a mock state_manager that always loads a minimal project."""
    from unittest.mock import MagicMock
    from jarvis.actions.iterate import IterateAction
    from jarvis.core.mutation_engine import MutationEngine
    from jarvis.schemas.state_schema import ProjectState

    project_state = ProjectState(
        project_id=project_id,
        project_slug="test-slug",
        objective="reducir peso",
        workspace_path="/tmp/test",
        current_parameters={"payload_kg": 2.0, "masa_total": 3.2},
    )
    state_manager = MagicMock()
    state_manager.load_active_project.return_value = project_state

    action = IterateAction(
        workspace_manager=MagicMock(),
        state_manager=state_manager,
        simulator=MagicMock(),
        calculation_engine=MagicMock(),
        mutation_engine=MutationEngine(),
        suggestion_engine=MagicMock(),
        reasoning_layer=MagicMock(),
    )
    return action


def test_iterate_action_returns_definition_status_for_unresolvable_draft():
    """Non-DEFINE draft with no physical strategy → status=definition, no mutation executed."""
    action = _make_iterate_action_with_mock_project()

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-1",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test",
            "operation": "mejorar",
            "variable": "autonomia",
            "strategy": "mejorar autonomia",
        }
    })

    assert result["status"] == "definition"
    assert "message" in result
    assert result["action"] == "iterate"


def test_iterate_action_guard_does_not_block_numeric_param_mutation():
    """Wizard-produced numeric param draft (motores) must NOT be blocked by the guard."""
    action = _make_iterate_action_with_mock_project()
    action.suggestion_engine.generate_suggestions.return_value = []
    action.reasoning_layer.build.return_value = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(model_dump=lambda: {})

    from jarvis.schemas.state_schema import ProjectState
    project_state = ProjectState(
        project_id="pid-1",
        project_slug="test-slug",
        objective="cambiar motores",
        workspace_path="/tmp/test",
        current_parameters={"payload_kg": 2.0, "masa_total": 3.2, "motor_count": 4},
    )
    action.state_manager.load_active_project.return_value = project_state
    action.state_manager.record_action.return_value = project_state

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-1",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test",
            "operation": "reducir",   # wizard sets REDUCE for numeric params
            "variable": "motores",
            "value": "6",
            "strategy": "establecer motores = 6",
        }
    })

    # Must NOT be blocked by the guard
    assert result["status"] != "definition", (
        "Guard incorrectamente bloqueó una mutación de parámetro numérico válida"
    )


def test_iterate_action_guard_does_not_block_resolvable_physical_draft():
    """Valid physical draft (payload) clears the guard and reaches full execution path."""
    from unittest.mock import MagicMock
    from jarvis.actions.iterate import IterateAction
    from jarvis.core.mutation_engine import MutationEngine
    from jarvis.schemas.state_schema import ProjectState

    project_state = ProjectState(
        project_id="pid-2",
        project_slug="test-slug",
        objective="reducir carga",
        workspace_path="/tmp/test2",
        current_parameters={"payload_kg": 2.0, "masa_total": 3.2},
    )
    state_manager = MagicMock()
    state_manager.load_active_project.return_value = project_state
    state_manager.record_action.return_value = project_state

    action = IterateAction(
        workspace_manager=MagicMock(),
        state_manager=state_manager,
        simulator=MagicMock(),
        calculation_engine=MagicMock(),
        mutation_engine=MutationEngine(),
        suggestion_engine=MagicMock(),
        reasoning_layer=MagicMock(),
    )
    action.suggestion_engine.generate_suggestions.return_value = []
    action.reasoning_layer.build.return_value = MagicMock(model_dump=lambda: {})

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-2",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test2",
            "operation": "reducir",
            "variable": "payload",
            "strategy": "reducir carga",
        }
    })

    # Must NOT return definition — guard passed, physical execution ran
    assert result["status"] != "definition"


# ── Bug 4: variable normalization at step 1 ───────────────────────────────────

def test_variable_carga_normalized_to_payload_kg():
    """'carga' typed at step 1 must be stored as 'payload_kg' in the draft."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="reducir peso",
            operation=IterationOperation.REDUCE,
        ),
    )
    response = session.answer(state, "carga")
    assert response["iteration_draft"]["variable"] == "payload_kg"


def test_variable_payload_normalized_to_payload_kg():
    """'payload' typed at step 1 must also normalize to 'payload_kg'."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="reducir carga",
            operation=IterationOperation.REDUCE,
        ),
    )
    response = session.answer(state, "payload")
    assert response["iteration_draft"]["variable"] == "payload_kg"


def test_unknown_variable_passes_through_unchanged():
    """Variable names not in the normalization table must be stored as-is."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="reducir tamaño",
            operation=IterationOperation.REDUCE,
        ),
    )
    response = session.answer(state, "dimensiones")
    assert response["iteration_draft"]["variable"] == "dimensiones"


# ── Bug 5: derived variable redirect at step 1 ───────────────────────────────

def test_autonomia_at_step1_returns_redirect_message():
    """Typing 'autonomia' at step 1 must return a redirect — session stays at step 1."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="mejorar autonomia",
            operation=IterationOperation.IMPROVE,
        ),
    )
    response = session.answer(state, "autonomia")
    # Must stay at step 1 — do not advance
    assert response["step"] == 1
    # Must contain the redirect message mentioning battery or motor
    assert "battery_capacity_wh" in response["message"] or "motor_power_w" in response["message"]


def test_autonomia_with_accent_also_redirects():
    """Diacritics in 'autonomía' must not bypass the redirect."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="mejorar autonomía",
            operation=IterationOperation.IMPROVE,
        ),
    )
    response = session.answer(state, "autonomía")
    assert response["step"] == 1
    assert "battery_capacity_wh" in response["message"] or "motor_power_w" in response["message"]


# ── Bug 24: variable ↔ strategy coherence check at step 2 ────────────────────

def test_incoherent_strategy_at_step2_returns_error_not_advance():
    """strategy='mejorar aerodinamica' + variable='payload_kg' is not actionable → re-ask at step 2."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="mejorar rendimiento",
            operation=IterationOperation.IMPROVE,
            variable="temperatura",   # not resolvable to any physical strategy
        ),
    )
    response = session.answer(state, "mejorar aerodinamica")
    # Step must NOT advance to 3
    assert response["step"] == 2
    assert "no es compatible" in response.get("message", "").lower() or response.get("error")


def test_coherent_strategy_at_step2_advances_to_step3():
    """strategy='reducir material' + variable='material' is valid → advances to step 3."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="reducir peso",
            operation=IterationOperation.REDUCE,
            variable="material",
        ),
    )
    response = session.answer(state, "reducir material")
    # Must advance past step 2 OR handle as material sub-step (asks for material name)
    # Either way, NOT stuck at step 2 with an incoherence error
    assert response.get("step") != 2 or "material" in response.get("question", "").lower()


# ── Bug 1/2: volume strategy without concrete value → degraded to definition ─

def test_volume_strategy_no_value_degraded_to_definition():
    """Variable='dimensiones' + strategy='optimizar estructura' with no value
    must be blocked by the Bug 1/2 guard and return status='definition'."""
    action = _make_iterate_action_with_mock_project()

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-1",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test",
            "operation": "reducir",
            "variable": "dimensiones",
            "strategy": "optimizar estructura",
            # No 'value' field
        }
    })

    assert result["status"] == "definition", (
        "Bug 1/2 guard debe degradar una mutación de volumen sin valor concreto"
    )
    assert "valor concreto" in result["message"].lower() or "parámetro" in result["message"].lower()
    assert result["action"] == "iterate"


def test_volume_strategy_with_explicit_value_not_blocked():
    """Same variable+strategy but with an explicit value must NOT be blocked."""
    action = _make_iterate_action_with_mock_project()
    action.suggestion_engine.generate_suggestions.return_value = []
    action.reasoning_layer.build.return_value = __import__(
        "unittest.mock", fromlist=["MagicMock"]
    ).MagicMock(model_dump=lambda: {})

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-1",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test",
            "operation": "reducir",
            "variable": "dimensiones",
            "strategy": "optimizar estructura",
            "value": "0.4",   # explicit user value → guard must not fire
        }
    })

    assert result["status"] != "definition", (
        "Bug 1/2 guard NO debe bloquear una mutación de volumen con valor concreto"
    )


def test_payload_reduce_no_value_not_blocked_by_bug1_guard():
    """Payload mutation without explicit value must NOT be blocked — it only needs
    the operation direction (reduce/increase), not an explicit value."""
    action = _make_iterate_action_with_mock_project()
    action.suggestion_engine.generate_suggestions.return_value = []
    action.reasoning_layer.build.return_value = __import__(
        "unittest.mock", fromlist=["MagicMock"]
    ).MagicMock(model_dump=lambda: {})

    result = action.run({
        "iteration_draft": {
            "project_id": "pid-1",
            "project_slug": "test-slug",
            "workspace_path": "/tmp/test",
            "operation": "reducir",
            "variable": "payload",
            "strategy": "reducir carga",
            # No 'value' — payload only needs direction
        }
    })

    assert result["status"] != "definition", (
        "Bug 1/2 guard NO debe bloquear mutaciones de payload (solo necesitan dirección)"
    )


def test_needs_concrete_value_returns_false_for_material():
    """needs_concrete_value must return False for material strategy — apply_material_mutation
    gates on draft.value internally, so this method must not double-block it."""
    from jarvis.core.mutation_engine import MutationEngine
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation

    engine = MutationEngine()
    draft = IterationDraft(
        project_id="p", project_slug="s", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="material",
        strategy="cambiar material",
        # No value: apply_material_mutation will raise, but needs_concrete_value should
        # still return False (it's not a "volume without value" case).
    )
    assert engine.needs_concrete_value(draft) is False, (
        "needs_concrete_value no debe retornar True para estrategia 'material'"
    )


# ── Capa 4: Bug 9 (fuzzy normalization) ─────────────────────────────────────

def _make_session_at_step1(variable_answer: str = "sí") -> tuple[IterateInteractiveSession, InteractiveSessionState]:
    """Helper: start an iterate session and advance to step 1 (variable question)."""
    session = IterateInteractiveSession()
    start = session.start({
        "project_id": "pid", "project_slug": "test-slug", "workspace_path": "/tmp",
        "objetivo": "peso", "operacion": "reducir",
    })
    current = _session_from_response(start)
    answer_step0 = session.answer(current, "sí")  # confirm objective
    return session, _session_from_response(answer_step0)


def test_fuzzy_typo_dimesniones_maps_to_dimensiones():
    """Bug 9: typo 'dimesniones' at step 1 must normalize to 'dimensiones'."""
    session, current = _make_session_at_step1()
    result = session.answer(current, "dimesniones")
    variable = result["iteration_draft"]["variable"]
    assert variable == "dimensiones", (
        f"'dimesniones' debería normalizarse a 'dimensiones', obtuvimos '{variable}'"
    )


def test_fuzzy_prefix_estructur_maps_to_estructura():
    """Bug 9: substring 'estructur' at step 1 must normalize to 'estructura'."""
    session, current = _make_session_at_step1()
    result = session.answer(current, "estructur")
    variable = result["iteration_draft"]["variable"]
    assert variable == "estructura", (
        f"'estructur' debería normalizarse a 'estructura', obtuvimos '{variable}'"
    )


def test_exact_normalization_takes_priority_over_fuzzy():
    """Bug 9: exact lookup in _VARIABLE_NORMALIZATION must win over fuzzy match."""
    session, current = _make_session_at_step1()
    result = session.answer(current, "carga")
    variable = result["iteration_draft"]["variable"]
    assert variable == "payload_kg", (
        f"'carga' (exact match) debería mapear a 'payload_kg', obtuvimos '{variable}'"
    )


# ── Capa 4: Bug 8 (orientative error messages) ───────────────────────────────

def _make_session_at_step4() -> tuple[IterateInteractiveSession, InteractiveSessionState]:
    """Helper: drive session to step 4 (apply decision) via dimensiones/optimizar path."""
    session = IterateInteractiveSession()
    start = session.start({
        "project_id": "pid", "project_slug": "test-slug", "workspace_path": "/tmp",
        "objetivo": "peso", "operacion": "reducir",
    })
    current = _session_from_response(start)
    current = _session_from_response(session.answer(current, "sí"))         # step 0 → 1
    current = _session_from_response(session.answer(current, "componentes")) # step 1 → 2
    current = _session_from_response(session.answer(current, "optimizar estructura"))  # step 2 → 3
    current = _session_from_response(session.answer(current, "sin restricciones"))    # step 3 → 4
    assert current.step == 4
    return session, current


def test_apply_decision_unrecognized_echoes_input():
    """Bug 8: unrecognised input at step 4 error must include the user's text and 'sí'/'no'."""
    session, current = _make_session_at_step4()
    result = session.answer(current, "quizas")
    error = result.get("error", "")
    assert "quizas" in error, f"El error debería incluir el input del usuario, obtuvimos: '{error}'"
    assert "sí" in error or "si" in error.lower(), f"El error debería mencionar 'sí', obtuvimos: '{error}'"


def test_final_confirmation_unrecognized_echoes_input():
    """Bug 8: unrecognised input at step 5 error must include the user's text and 'sí'/'no'."""
    session, current = _make_session_at_step4()
    current = _session_from_response(session.answer(current, "sí"))  # step 4 → 5
    assert current.step == 5
    result = session.answer(current, "tal vez")
    error = result.get("error", "")
    assert "tal vez" in error, f"El error debería incluir el input del usuario, obtuvimos: '{error}'"
    assert "sí" in error or "si" in error.lower(), f"El error debería mencionar 'sí', obtuvimos: '{error}'"


# ── Bugs 14/15: _classify_variable_type and adaptive step-2 questions ─────────

def _make_session_at_step2(variable: str, current_params: dict | None = None) -> tuple:
    """Helper: session at step 2 with the given variable and optional current_params."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="mejorar diseño",
            operation=IterationOperation.REDUCE,
            variable=variable,
        ),
        memory_context={"current_parameters": current_params or {}},
    )
    return session, state


def test_classify_variable_type_numeric_direct_beats_structural():
    """'factor_estructura' must classify as 'numeric_direct', NOT 'structural_abstract'.

    Critical ordering test: 'estructura' substring in 'factor_estructura' must NOT
    trigger structural classification when the key exists in current_parameters.
    """
    session = IterateInteractiveSession()
    params = {"structure_mass_factor": 0.6}
    vtype = session._classify_variable_type("factor_estructura", params)
    assert vtype == "numeric_direct", (
        f"'factor_estructura' should be 'numeric_direct' (params has 'structure_mass_factor'), "
        f"got '{vtype}'"
    )


def test_classify_variable_type_semantic_mutation():
    """'payload_kg' must classify as 'semantic_mutation' even when the key exists
    in current_parameters (real-project case).  This mirrors the answer() guard:
      canonical = None if _var in _SEMANTIC_MUTATION_PARAMS else ...
    so the question and the routing are always consistent.
    """
    session = IterateInteractiveSession()
    # Test with empty params (basic)
    assert session._classify_variable_type("payload_kg", {}) == "semantic_mutation"
    # Test with realistic project params — critical case that was broken
    real_params = {"payload_kg": 2.0, "motor_count": 4, "safety_factor": 1.5}
    vtype = session._classify_variable_type("payload_kg", real_params)
    assert vtype == "semantic_mutation", (
        f"'payload_kg' with real current_params should be 'semantic_mutation' (not "
        f"'numeric_direct'), got '{vtype}'. Mirrors answer() exclusion of "
        f"_SEMANTIC_MUTATION_PARAMS from the numeric path."
    )


def test_classify_variable_type_material():
    """'material' must classify as 'material'."""
    session = IterateInteractiveSession()
    vtype = session._classify_variable_type("material", {})
    assert vtype == "material", f"Expected 'material', got '{vtype}'"


def test_classify_variable_type_structural_physical():
    """'dimensiones' must classify as 'structural_physical' (quantifiable)."""
    session = IterateInteractiveSession()
    vtype = session._classify_variable_type("dimensiones", {})
    assert vtype == "structural_physical", f"Expected 'structural_physical', got '{vtype}'"


def test_classify_variable_type_structural_abstract():
    """'estructura' must classify as 'structural_abstract' (always declarative)."""
    session = IterateInteractiveSession()
    vtype = session._classify_variable_type("estructura", {})
    assert vtype == "structural_abstract", f"Expected 'structural_abstract', got '{vtype}'"


def test_classify_variable_type_component_define():
    """'componentes' must classify as 'component_define'."""
    session = IterateInteractiveSession()
    vtype = session._classify_variable_type("componentes", {})
    assert vtype == "component_define", f"Expected 'component_define', got '{vtype}'"


def test_classify_variable_type_unknown():
    """Unrecognised variable must fall back to 'unknown'."""
    session = IterateInteractiveSession()
    vtype = session._classify_variable_type("xyz_desconocido", {})
    assert vtype == "unknown", f"Expected 'unknown', got '{vtype}'"


def test_step2_question_semantic_mutation_payload():
    """Step 2 with variable='payload_kg' must ask for a concrete value or change.

    Uses realistic current_params (payload_kg is always a numeric key in real
    projects) to ensure _question_for_session is consistent with answer() routing.
    """
    # Use realistic params — payload_kg IS numeric but must NOT get numeric question
    session, state = _make_session_at_step2("payload_kg", current_params={"payload_kg": 2.0, "motor_count": 4})
    question = session._question_for_session(state, "default")
    assert "concreto" in question.lower() or "kg" in question.lower(), (
        f"Step-2 payload question should mention concrete value or kg, got: '{question}'"
    )
    # Consistency check: same question whether params are empty or realistic
    session2, state2 = _make_session_at_step2("payload_kg", current_params={})
    question2 = session2._question_for_session(state2, "default")
    assert question == question2, (
        f"Payload question must be identical regardless of current_params presence.\n"
        f"  With params={{'payload_kg': 2.0}}: '{question}'\n"
        f"  Without params: '{question2}'"
    )


def test_step2_question_structural_physical_warns_about_factor():
    """Step 2 with variable='dimensiones' must warn that a quantitative factor is needed."""
    session, state = _make_session_at_step2("dimensiones")
    question = session._question_for_session(state, "default")
    assert "cuantitativo" in question.lower() or "declarativ" in question.lower(), (
        f"Step-2 structural_physical question should mention quantitative factor or declarative, got: '{question}'"
    )


def test_step2_question_structural_abstract_always_declarative():
    """Step 2 with variable='estructura' must state that change is always declarative."""
    session, state = _make_session_at_step2("estructura")
    question = session._question_for_session(state, "default")
    assert "declarativ" in question.lower(), (
        f"Step-2 structural_abstract question should mention 'declarativa', got: '{question}'"
    )


# ── Bug 23: pre-confirmation draft validation ─────────────────────────────────

def _make_session_at_step5() -> tuple[IterateInteractiveSession, InteractiveSessionState]:
    """Helper: drive session to step 5 (final confirmation) via dimensiones path."""
    session, current = _make_session_at_step4()
    current = _session_from_response(session.answer(current, "sí"))  # step 4 → 5
    assert current.step == 5
    return session, current


def test_final_confirmation_valid_draft_confirms():
    """Bug 23: a complete draft (op + variable + strategy) must confirm normally."""
    session, current = _make_session_at_step5()
    result = session.answer(current, "sí")
    assert result["status"] == "confirmed", (
        f"A complete draft should confirm, got status='{result.get('status')}'"
    )
    assert result["iteration_draft"]["variable"] is not None


def test_final_confirmation_missing_operation_blocked():
    """Bug 23: draft with operation=None must not confirm — must return error."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=5,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=None,
            variable="material",
            strategy="cambiar a fibra de carbono",
        ),
    )
    result = session.answer(state, "sí")
    assert result.get("status") != "confirmed", "draft with operation=None must not confirm"
    assert result.get("error"), "Must return an error message when operation is None"


def test_final_confirmation_missing_variable_blocked():
    """Bug 23: draft with variable=None must not confirm — must return error."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=5,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=IterationOperation.REDUCE,
            variable=None,
            strategy="reducir carga",
        ),
    )
    result = session.answer(state, "sí")
    assert result.get("status") != "confirmed", "draft with variable=None must not confirm"
    assert result.get("error"), "Must return an error message when variable is None"


def test_final_confirmation_missing_strategy_non_define_blocked():
    """Bug 23: non-DEFINE draft with strategy=None must not confirm."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=5,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=IterationOperation.REDUCE,
            variable="payload_kg",
            strategy=None,
        ),
    )
    result = session.answer(state, "sí")
    assert result.get("status") != "confirmed", "non-DEFINE draft with strategy=None must not confirm"
    assert result.get("error"), "Must return an error message when strategy is None"


def test_final_confirmation_define_without_strategy_allowed():
    """Bug 23: DEFINE operation without strategy must still confirm (declarative intent)."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=5,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=IterationOperation.DEFINE,
            variable="estructura",
            strategy=None,
        ),
    )
    result = session.answer(state, "sí")
    assert result.get("status") == "confirmed", (
        "DEFINE operation without strategy should still confirm"
    )


# ── Bug 20: no auto-synthesis of vacuous strategy ─────────────────────────────

def _make_step2_tuple_for_bug20(variable: str = "bateria") -> tuple:
    """Session at step 2 with a non-numeric, physically-actionable variable at step 2.

    semantic_state is pre-seeded with operation+variable slots so that sem.decide()
    returns 'proceed', which is the path where Bug 20 auto-synthesis fires.
    objective='peso' + operation=REDUCE ensures is_physically_actionable=True for the
    variable without a numeric value (resolve_strategy falls through to the "peso+reducir"
    → "material" heuristic path, which doesn't require draft.value).
    """
    from jarvis.schemas.semantic_schema import SemanticState, SlotValue

    session = IterateInteractiveSession()
    # Pre-seed semantic_state: operation and variable slots present at high confidence
    # → sem.decide() returns "proceed", reaching the Bug 20 guard.
    semantic = SemanticState(
        slots={
            "operation": SlotValue(value="reducir", confidence=0.9, source="confirmed"),
            "variable": SlotValue(value=variable, confidence=0.9, source="confirmed"),
        },
        missing_slots=[],
        clarification_round=0,
    )
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            objective="peso",  # enables resolve_strategy "peso+reducir" heuristic
            operation=IterationOperation.REDUCE,
            variable=variable,
        ),
        semantic_state=semantic,
        memory_context={"current_parameters": {}},
    )
    return session, state


def test_step2_pure_operation_keyword_asks_for_strategy():
    """Bug 20: a step-2 input that is just an operation keyword must trigger clarification.

    Without the fix, the wizard auto-synthesises 'reducir structure_mass_factor' and
    advances to step 3.  With the fix, it asks the user for a concrete strategy.
    """
    session, state = _make_step2_tuple_for_bug20()
    result = session.answer(state, "mejorar")
    # Must NOT advance to step 3
    assert result.get("status") != "confirmed"
    result_session = _session_from_response(result)
    assert result_session.step == 2, (
        f"Pure operation input 'mejorar' must keep step at 2, got step={result_session.step}"
    )
    # Must contain a question prompting for strategy
    assert result.get("question") or result.get("message"), (
        "Must return a question or message prompting for strategy clarification"
    )


def test_step2_none_strategy_asks_for_strategy():
    """Bug 20: an empty strategy after step-2 processing must trigger clarification."""
    session, state = _make_step2_tuple_for_bug20()
    # Empty string → no strategy
    result = session.answer(state, "")
    result_session = _session_from_response(result)
    assert result_session.step == 2, (
        f"Empty step-2 input must keep step at 2, got step={result_session.step}"
    )


def test_step2_concrete_strategy_advances_to_step3():
    """Bug 20 + Bug 28: 'bateria' is now a known numeric param; a concrete numeric value
    must advance directly to step 4 (impact estimate), skipping the strategy step."""
    session, state = _make_step2_tuple_for_bug20()
    # Bug 28: "bateria" → battery_capacity_wh is resolved even with empty current_params.
    # The numeric path receives "1000" → parses to 1000.0 → jumps to step 4.
    result = session.answer(state, "1000")
    result_session = _session_from_response(result)
    assert result_session.step == 4, (
        f"Numeric value for known param must advance to step 4, got step={result_session.step}; "
        f"response={result}"
    )


# ── Bug 21: real physical delta estimates ─────────────────────────────────────

def test_estimate_impact_payload_real_delta_when_params_known():
    """Bug 21: with current_params and a numeric draft.value, impact delta must be real."""
    from jarvis.schemas.action_schema import ImpactEstimate

    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="carga",
        strategy="reducir carga a 1.5 kg",
        value="1.5",
    )
    current_params = {"payload_kg": 2.0}
    estimate = session._estimate_impact(draft, current_params)
    # Real delta: (1.5 - 2.0) / 2.0 * 100 = -25.0%
    assert estimate.weight_change_percent == -25.0, (
        f"Expected real delta -25.0%, got {estimate.weight_change_percent}"
    )
    assert estimate.thrust_impact == "positivo", (
        f"Reducing payload must be positivo, got '{estimate.thrust_impact}'"
    )
    assert "1.5" in estimate.summary and "2.0" in estimate.summary, (
        f"Summary must include real values, got: '{estimate.summary}'"
    )


def test_estimate_impact_payload_fallback_without_params():
    """Bug 21: without current_params, must fall back to ±10% estimate."""
    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="carga",
        strategy="reducir carga",
        value=None,
    )
    estimate = session._estimate_impact(draft, None)
    assert estimate.weight_change_percent == -10.0, (
        f"Fallback must be -10.0%, got {estimate.weight_change_percent}"
    )


def test_estimate_impact_payload_fallback_no_numeric_value():
    """Bug 21: with params but no parseable numeric value, must still fall back."""
    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="carga",
        strategy="reducir carga lo máximo posible",
        value=None,
    )
    current_params = {"payload_kg": 2.0}
    estimate = session._estimate_impact(draft, current_params)
    assert estimate.weight_change_percent == -10.0, (
        f"No-value fallback must be -10.0%, got {estimate.weight_change_percent}"
    )


# ── Bug 22: _PARAM_DISPLAY_ALIASES coverage ───────────────────────────────────

def test_param_display_aliases_energy_params_present():
    """Bug 22: Spanish aliases for energy params must resolve to canonical keys.

    Since _PARAM_DISPLAY_ALIASES is now computed via build_alias_map(), all keys
    are normalized (lowercase, no diacritics).  Runtime consumers call
    _normalize_alias() before lookup so accented inputs still resolve correctly.
    """
    from jarvis.core.mutation_engine import _PARAM_DISPLAY_ALIASES

    assert _PARAM_DISPLAY_ALIASES.get("bateria") == "battery_capacity_wh", (
        "'bateria' (normalized form) must alias to 'battery_capacity_wh'"
    )
    # 'batería' normalizes to 'bateria' — dict has the normalized key only
    assert "bateria" in _PARAM_DISPLAY_ALIASES, (
        "normalized 'bateria' must be present (covers both 'bateria' and 'batería' inputs)"
    )
    assert _PARAM_DISPLAY_ALIASES.get("potencia_motor") == "motor_power_w", (
        "'potencia_motor' must alias to 'motor_power_w'"
    )
    assert _PARAM_DISPLAY_ALIASES.get("potencia_motores") == "motor_power_w", (
        "'potencia_motores' must alias to 'motor_power_w'"
    )
    assert _PARAM_DISPLAY_ALIASES.get("num_motores") == "motor_count", (
        "'num_motores' must alias to 'motor_count'"
    )


def test_param_display_aliases_existing_entries_not_regressed():
    """Bug 22: pre-existing aliases must still be present after the new additions."""
    from jarvis.core.mutation_engine import _PARAM_DISPLAY_ALIASES

    assert _PARAM_DISPLAY_ALIASES.get("factor_estructura") == "structure_mass_factor"
    assert _PARAM_DISPLAY_ALIASES.get("factor_seguridad") == "safety_factor"
    assert _PARAM_DISPLAY_ALIASES.get("empuje_max_por_motor") == "per_motor_max_thrust_n"
    assert _PARAM_DISPLAY_ALIASES.get("motores") == "motor_count"


# ── Bug 31: space-variant battery aliases ─────────────────────────────────────

def test_bug31_space_aliases_in_param_display_aliases():
    """Bug 31: space-variant aliases must be in _PARAM_DISPLAY_ALIASES.

    Keys are normalized (no diacritics).  Accented inputs (e.g. 'capacidad de
    batería') normalize to the same key at the consumption site via _normalize_alias.
    """
    from jarvis.core.mutation_engine import _PARAM_DISPLAY_ALIASES

    assert _PARAM_DISPLAY_ALIASES.get("capacidad de bateria") == "battery_capacity_wh"
    assert _PARAM_DISPLAY_ALIASES.get("capacidad bateria") == "battery_capacity_wh"
    # 'capacidad de batería' normalizes to 'capacidad de bateria' at lookup time
    assert _PARAM_DISPLAY_ALIASES.get("capacidad de bateria") == "battery_capacity_wh", (
        "normalized form covers both 'capacidad de bateria' and 'capacidad de batería'"
    )
    assert _PARAM_DISPLAY_ALIASES.get("potencia motores") == "motor_power_w"
    assert _PARAM_DISPLAY_ALIASES.get("potencia por motor") == "motor_power_w"


def test_bug31_space_aliases_pass_domain_validation():
    """Bug 31: space-variant aliases must pass the Bug 30 domain guard at step 1."""
    from jarvis.core.iterate_interactive_session import _is_valid_variable

    assert _is_valid_variable("capacidad de bateria"), "space alias must be valid"
    assert _is_valid_variable("capacidad bateria"), "space alias must be valid"
    assert _is_valid_variable("capacidad de batería"), "accented space alias must be valid"
    assert _is_valid_variable("potencia motores"), "potencia motores must be valid"
    assert _is_valid_variable("potencia por motor"), "potencia por motor must be valid"


def test_bug31_space_alias_resolves_to_canonical_via_match_numeric_param():
    """Bug 31: _match_numeric_param must map space-variant aliases to their canonical key."""
    session = IterateInteractiveSession()

    assert session._match_numeric_param("capacidad de bateria", {}) == "battery_capacity_wh"
    assert session._match_numeric_param("capacidad bateria", {}) == "battery_capacity_wh"
    assert session._match_numeric_param("potencia motores", {}) == "motor_power_w"
    assert session._match_numeric_param("potencia por motor", {}) == "motor_power_w"


# ── Bug 35: numeric operation inferred from value comparison ──────────────────

def test_bug35_infer_numeric_operation_reduce():
    """Bug 35: new value < old value → REDUCE."""
    session = IterateInteractiveSession()
    op = session._infer_numeric_operation(200.0, 250.0)
    assert op == IterationOperation.REDUCE


def test_bug35_infer_numeric_operation_increase():
    """Bug 35: new value > old value → INCREASE."""
    session = IterateInteractiveSession()
    op = session._infer_numeric_operation(400.0, 250.0)
    assert op == IterationOperation.INCREASE


def test_bug35_infer_numeric_operation_no_op():
    """Bug 35: new value == old value → DEFINE (no-op)."""
    session = IterateInteractiveSession()
    op = session._infer_numeric_operation(250.0, 250.0)
    assert op == IterationOperation.DEFINE


def test_bug35_infer_numeric_operation_unknown_old():
    """Bug 35: old value unknown (None or non-numeric) → DEFINE."""
    session = IterateInteractiveSession()
    assert session._infer_numeric_operation(400.0, None) == IterationOperation.DEFINE
    assert session._infer_numeric_operation(400.0, "?") == IterationOperation.DEFINE


def test_bug35_numeric_path_sets_increase_when_value_goes_up():
    """Bug 35: end-to-end — numeric path must set INCREASE when new value > old."""
    session, state = _make_step2_tuple_for_bug20(variable="bateria")
    # Seed current_params so the comparison can be made
    state = state.model_copy(update={
        "memory_context": {"current_parameters": {"battery_capacity_wh": 250.0}}
    })
    result = session.answer(state, "400")
    result_session = _session_from_response(result)
    assert result_session.step == 4, f"Must advance to step 4, got {result_session.step}"
    assert result_session.iteration_draft.operation == IterationOperation.INCREASE, (
        f"New 400 > old 250 → INCREASE, got {result_session.iteration_draft.operation}"
    )


def test_bug35_numeric_path_sets_reduce_when_value_goes_down():
    """Bug 35: end-to-end — numeric path must set REDUCE when new value < old."""
    session, state = _make_step2_tuple_for_bug20(variable="bateria")
    state = state.model_copy(update={
        "memory_context": {"current_parameters": {"battery_capacity_wh": 250.0}}
    })
    result = session.answer(state, "100")
    result_session = _session_from_response(result)
    assert result_session.step == 4
    assert result_session.iteration_draft.operation == IterationOperation.REDUCE


# ── Bug 36: confirmation message after step 1 redirect resolves to numeric param ─

def test_bug36_step1_numeric_param_emits_confirmation_message():
    """Bug 36: when step 1 input resolves to a known numeric param, the response
    must include a short confirmation message before the value question."""
    session = IterateInteractiveSession()
    base_session = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=IterationOperation.REDUCE,
        ),
        memory_context={"current_parameters": {"battery_capacity_wh": 250.0}},
    )
    result = session.answer(base_session, "bateria")
    assert result["step"] == 2, f"Must advance to step 2, got step={result['step']}"
    msg = result.get("message", "")
    assert "bateria" in msg.lower() or "modificaremos" in msg.lower(), (
        f"Confirmation message must mention the variable; got: '{msg}'"
    )


def test_bug36_step1_semantic_mutation_param_does_not_emit_confirmation():
    """Bug 36: semantic mutation params (payload_kg) must NOT take the numeric
    fast-path — no confirmation message, normal strategy step 2 continues."""
    session = IterateInteractiveSession()
    base_session = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid", project_slug="slug", workspace_path="/tmp",
            operation=IterationOperation.REDUCE,
        ),
        memory_context={"current_parameters": {"payload_kg": 2.0}},
    )
    # "carga" normalises to "payload_kg" which is in _SEMANTIC_MUTATION_PARAMS
    result = session.answer(base_session, "carga")
    assert result["step"] == 2
    msg = result.get("message", "")
    # Must NOT have the numeric confirmation
    assert "modificaremos" not in msg.lower(), (
        f"Semantic mutation param must not get numeric confirmation; got: '{msg}'"
    )


# ── Bug 32: _impact_message must omit None fields ─────────────────────────────

def test_bug32_impact_message_omits_none_fields_for_numeric_param():
    """Bug 32: when the estimate only has a summary (numeric path), None fields
    must NOT appear in the rendered message."""
    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="battery_capacity_wh",
        impact_estimate=ImpactEstimate(summary="Batería reducida."),
    )
    msg = session._impact_message(draft)
    assert "None" not in msg, f"None must not appear in impact message; got: '{msg}'"
    assert "resumen: Batería reducida." in msg
    assert "Estimación:" in msg


def test_bug32_impact_message_shows_all_fields_when_present():
    """Bug 32: when all estimate fields are populated, all lines must appear."""
    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.REDUCE,
        variable="structure_mass_factor",
        impact_estimate=ImpactEstimate(
            weight_change_percent=-10.0,
            thrust_impact="neutro",
            stability_impact="neutro",
            summary="Reducción de masa.",
        ),
    )
    msg = session._impact_message(draft)
    assert "peso: -10.0%" in msg
    assert "impacto en empuje: neutro" in msg
    assert "impacto en estabilidad: neutro" in msg
    assert "resumen: Reducción de masa." in msg
    assert "None" not in msg


def test_bug32_impact_message_define_path_unaffected():
    """Bug 32: DEFINE operation still returns the declarative message (no regression)."""
    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="pid", project_slug="slug", workspace_path="/tmp",
        operation=IterationOperation.DEFINE,
        impact_estimate=ImpactEstimate(summary="X"),
    )
    msg = session._impact_message(draft)
    assert "define una propiedad" in msg
    assert "None" not in msg


# ── Registry normalization sync ────────────────────────────────────────────────

def test_normalize_alias_and_normalize_variable_input_are_equivalent():
    """CROSS-1: normalize_alias (registry) and _normalize_variable_input (iterate_domain)
    must produce identical output for any input.

    Both layers share the same normalization contract (NFKD + no-combining + lower + strip).
    This test enforces that they never silently diverge: a change to one that is not
    reflected in the other would break alias lookups at the domain boundary.
    """
    from jarvis.core.parameter_requirements import normalize_alias
    from jarvis.core.iterate_domain import _normalize_variable_input

    cases = [
        "Batería",
        "batería",
        "BATERÍA",
        "capacidad de batería",
        "Potencia Motores",
        "payload",
        "Autonomía",
        "  Hélice  ",
        "autonomia",
        "factor_estructura",
        "",
    ]
    for text in cases:
        assert normalize_alias(text) == _normalize_variable_input(text), (
            f"normalize_alias and _normalize_variable_input diverge for '{text}': "
            f"{normalize_alias(text)!r} != {_normalize_variable_input(text)!r}"
        )


# ── Fix 3: unknown variable error guides toward 'componentes' ────────────────

def _make_step1_state() -> "InteractiveSessionState":
    return InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="mejorar diseño",
            operation=IterationOperation.IMPROVE,
        ),
    )


def test_fix3_component_term_adds_componentes_hint():
    """Unknown terms that look like physical components must include a redirect hint.
    Bug 42: propeller-specific terms get a targeted 'configurar helices' message;
    other components still get the generic 'Para definir componentes' message.
    """
    session = IterateInteractiveSession()
    # Non-propeller component terms: must still show generic "Para definir componentes" hint
    for term in ("sensor", "esc", "frame", "lipo"):
        response = session.answer(_make_step1_state(), term)
        assert response["step"] == 1, f"Step must stay at 1 for '{term}'"
        assert "componentes" in (response.get("error") or ""), (
            f"'componentes' hint missing for term '{term}'"
        )
        assert "Para definir componentes" in (response.get("error") or ""), (
            f"Targeted hint missing for term '{term}'"
        )
    # Propeller terms: must show targeted "configurar helices" hint (Bug 42)
    for term in ("helices", "helice", "propeller"):
        response = session.answer(_make_step1_state(), term)
        assert response["step"] == 1, f"Step must stay at 1 for '{term}'"
        error = response.get("error") or ""
        assert "configurar" in error.lower() or "helice" in error.lower(), (
            f"Bug 42: propeller hint missing for term '{term}', got: {error!r}"
        )


def test_fix3_generic_unknown_has_no_componentes_hint():
    """Truly unknown terms unrelated to components must NOT include the targeted hint."""
    session = IterateInteractiveSession()
    response = session.answer(_make_step1_state(), "xyzabc_desconocido")
    assert response["step"] == 1
    error = response.get("error") or ""
    assert "No reconozco" in error
    assert "Para definir componentes" not in error


def test_fix3_unknown_error_always_contains_fallback_list():
    """Both component and generic unknown terms must include the fallback variable list."""
    session = IterateInteractiveSession()
    for term in ("helices", "xyzabc_desconocido"):
        response = session.answer(_make_step1_state(), term)
        error = response.get("error") or ""
        assert "material" in error, f"Fallback list missing for '{term}'"
        assert "componentes" in error, f"'componentes' must appear in fallback list for '{term}'"


# ── H2: Bugs 43, 44, 45 ─────────────────────────────────────────────────────

def _make_material_step2_state(current_material: str = "aluminio") -> InteractiveSessionState:
    """Return an InteractiveSessionState at step 2, variable='material', with
    current_material in memory_context (as injected by the orchestrator)."""
    from jarvis.schemas.action_schema import InteractiveSessionState, IterationDraft, IterationOperation, OrchestratorMode
    return InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=2,
        iteration_draft=IterationDraft(
            project_id="h2",
            project_slug="dron-h2",
            workspace_path="/tmp/h2",
            objective="cambiar material",
            operation=IterationOperation.REDUCE,
            variable="material",
            strategy="cambiar material",  # required by _awaiting_material_value
        ),
        memory_context={"current_material": current_material},
    )


def test_bug43_same_material_rejected():
    """Bug 43: answering with the same material that is already set must NOT advance step."""
    session = IterateInteractiveSession()
    state = _make_material_step2_state(current_material="aluminio")
    resp = session.answer(state, "aluminio")
    assert resp["step"] == 2, "same material must keep session at step 2"
    text = (resp.get("question") or resp.get("message") or "").lower()
    assert "ya es el material actual" in text or "cambio que aplicar" in text


def test_bug43_same_material_capitalized():
    """Bug 43: comparison must be case-insensitive and accent-insensitive."""
    session = IterateInteractiveSession()
    state = _make_material_step2_state(current_material="aluminio")
    resp = session.answer(state, "Aluminio")
    assert resp["step"] == 2, "capitalised same material must also be rejected"


def test_bug43_different_material_advances():
    """Bug 43: a genuinely different material must advance to step 3."""
    session = IterateInteractiveSession()
    state = _make_material_step2_state(current_material="aluminio")
    resp = session.answer(state, "titanio")
    assert resp["step"] == 3, "different material must advance to step 3"
    assert resp["iteration_draft"]["value"] == "titanio"


def test_bug44_material_without_physics_data():
    """Bug 44: when the chosen material has no library physics data (e.g. madera),
    the impact message must say it was 'registered but no physics data' instead of
    a generic 'cannot calculate' error."""
    from jarvis.core.iterate_interactive_session import IterateInteractiveSession
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation, ImpactEstimate

    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="h2b",
        project_slug="dron",
        workspace_path="/tmp/h2b",
        objective="cambiar material",
        operation=IterationOperation.REDUCE,
        variable="material",
        value="madera",
        strategy="cambiar a madera",
    )
    estimate = session._estimate_material_impact(draft, "madera")
    assert estimate.summary is not None
    assert "registrado" in estimate.summary or "datos f" in estimate.summary, (
        f"Expected friendly no-physics message, got: {estimate.summary}"
    )
    # Must NOT still say "no se puede calcular el impacto"
    assert "no se puede calcular" not in estimate.summary.lower()


def test_bug44_uses_real_current_material_in_summary():
    """Bug 44: when current_material is passed, it must appear in the summary."""
    from jarvis.core.iterate_interactive_session import IterateInteractiveSession
    from jarvis.schemas.action_schema import IterationDraft, IterationOperation

    session = IterateInteractiveSession()
    draft = IterationDraft(
        project_id="h2c",
        project_slug="dron",
        workspace_path="/tmp/h2c",
        objective="cambiar material",
        operation=IterationOperation.REDUCE,
        variable="material",
        value="titanio",
        strategy="cambiar a titanio",
    )
    estimate = session._estimate_material_impact(draft, "titanio", current_material="acero")
    assert estimate.summary is not None
    assert "acero" in estimate.summary.lower(), (
        f"Expected 'acero' in summary (as current material), got: {estimate.summary}"
    )


def test_bug45_unrecognised_material_returns_only_question():
    """Bug 45: when material name is not recognised, response must use only
    'question' — not a parallel 'message' + 'question' combination."""
    session = IterateInteractiveSession()
    state = _make_material_step2_state(current_material="aluminio")
    resp = session.answer(state, "adamantium")  # unknown material
    assert resp["step"] == 2
    # 'question' must carry the material prompt (Bug 45: single question source)
    question_text = resp.get("question") or ""
    assert question_text, "must have a question"
    assert "material" in question_text.lower(), (
        f"Bug 45: question must ask for material, got: {question_text!r}"
    )
    # Bug 45: the message must NOT be a second material-asking question
    # (_build_response adds a generic intro banner to message, which is fine).
    message_text = (resp.get("message") or "").lower()
    assert "¿qué material" not in message_text, (
        f"Bug 45: duplicate material question in message: {resp.get('message')!r}"
    )


def test_normalize_material_strips_diacritics():
    """_normalize_material must compare 'fibra de carbono' variants as equal."""
    from jarvis.core.iterate_interactive_session import IterateInteractiveSession
    norm = IterateInteractiveSession._normalize_material
    assert norm("Aluminio") == norm("aluminio")
    assert norm("ALUMINIO") == norm("aluminio")
    assert norm("  titanio  ") == norm("titanio")


# ── Bug 42: helice/propeller in step 1 shows targeted "configurar helices" hint ──

@pytest.mark.parametrize("variable", ["helice", "helices", "propeller", "propellers", "palas"])
def test_bug42_propeller_in_step1_shows_configurar_hint(variable):
    """Bug 42: typing a propeller term in step 1 must include 'configurar helices' hint."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="ajustar helices",
        ),
    )
    resp = session.answer(state, variable)
    assert resp["step"] == 1, f"Expected step to stay at 1, got {resp['step']}"
    full_text = (resp.get("error") or "") + (resp.get("message") or "")
    assert "configurar helices" in full_text.lower() or "configurar h" in full_text.lower(), (
        f"Bug 42: '{variable}' hint must say 'configurar helices', got: {full_text!r}"
    )


def test_bug42_generic_component_in_step1_shows_di_componentes():
    """Bug 42 inverse: non-propeller components (sensor, esc) must still say 'di componentes'."""
    session = IterateInteractiveSession()
    state = InteractiveSessionState(
        mode=OrchestratorMode.ITERATE_INTERACTIVE,
        step=1,
        iteration_draft=IterationDraft(
            project_id="pid",
            project_slug="slug",
            workspace_path="/tmp",
            objective="ajustar sensor",
        ),
    )
    resp = session.answer(state, "sensor")
    full_text = (resp.get("error") or "") + (resp.get("message") or "")
    # must NOT say "configurar helices" for generic component
    assert "configurar h" not in full_text.lower(), (
        f"Bug 42 regression: 'sensor' hint incorrectly shows propeller redirect: {full_text!r}"
    )


# ── Bug 40: re-intent detector in step 2 ─────────────────────────────────────

def test_bug40_new_variable_in_step2_restarts_session():
    """Bug 40: expressing a new iterate goal with a DIFFERENT variable in step 2 restarts the wizard."""
    session, state = _make_session_at_step2("material")
    # User says "reducir carga" while wizard was on "material" → should restart on "carga"
    resp = session.answer(state, "reducir carga")
    # After restart, step should be 0 (new session) or 1 (if seed has objetivo)
    assert resp["step"] in (0, 1), (
        f"Bug 40: new intent in step 2 should restart wizard (step 0 or 1), got {resp['step']}"
    )


def test_bug40_same_variable_strategy_not_restarted():
    """Bug 40 guard: step-2 input that is actually a strategy for the current variable must NOT restart."""
    session, state = _make_session_at_step2("material")
    # "cambiar material" is a valid step-2 strategy for variable "material"
    resp = session.answer(state, "cambiar material")
    # Should stay in step 2 (awaiting material name) or advance to 3
    assert resp["step"] in (2, 3, 4), (
        f"Bug 40: strategy 'cambiar material' for 'material' should NOT restart, got step {resp['step']}"
    )


def test_bug40_non_iterate_input_in_step2_not_restarted():
    """Bug 40 guard: generic text in step 2 (not a strong iterate intent) must NOT restart."""
    session, state = _make_session_at_step2("material")
    resp = session.answer(state, "algo diferente")
    assert resp["step"] in (2, 3, 4), (
        f"Bug 40: non-iterate input should not restart, got step {resp['step']}"
    )
