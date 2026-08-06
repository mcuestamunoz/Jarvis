import pytest

from jarvis.core.iterate_interactive_session import IterateInteractiveSession
from jarvis.core.semantic_interpreter import update, decide, to_draft_patch, MAX_CLARIFICATION_ROUNDS
from jarvis.schemas.action_schema import (
    InteractiveSessionState,
    IterationDraft,
    IterationOperation,
    OrchestratorMode,
)
from jarvis.schemas.semantic_schema import SemanticState, SlotValue


# ─── update() ─────────────────────────────────────────────────────────────────

def test_update_extracts_define_operation_from_disenar():
    state = update(SemanticState(), "diseñar el motor")
    slot = state.slots.get("operation")
    assert slot is not None
    assert slot.value == IterationOperation.DEFINE.value
    assert slot.confidence >= 0.75


def test_update_extracts_reduce_operation():
    state = update(SemanticState(), "reducir el peso del dron")
    slot = state.slots.get("operation")
    assert slot is not None
    assert slot.value == IterationOperation.REDUCE.value


def test_update_extracts_increase_operation():
    state = update(SemanticState(), "aumentar la carga útil")
    slot = state.slots.get("operation")
    assert slot is not None
    assert slot.value == IterationOperation.INCREASE.value


def test_update_extracts_variable_from_motor():
    state = update(SemanticState(), "cambiar los motores brushless")
    slot = state.slots.get("variable")
    assert slot is not None
    assert slot.value == "componentes"


def test_update_accumulates_slots_across_inputs():
    state = SemanticState()
    state = update(state, "quiero definir algo")
    state = update(state, "los motores del dron")
    assert state.slots["operation"].value == IterationOperation.DEFINE.value
    assert state.slots["variable"].value == "componentes"


def test_update_does_not_overwrite_confirmed_slot():
    confirmed = SlotValue(value="reducir", confidence=1.0, source="confirmed")
    state = SemanticState(slots={"operation": confirmed})
    state = update(state, "diseñar el motor")
    # confirmed slot must not be replaced
    assert state.slots["operation"].value == "reducir"
    assert state.slots["operation"].source == "confirmed"


def test_update_appends_to_history():
    state = SemanticState()
    state = update(state, "primer input")
    state = update(state, "segundo input")
    assert len(state.history) == 2
    assert state.history[0] == "primer input"
    assert state.history[1] == "segundo input"


# ─── decide() ─────────────────────────────────────────────────────────────────

def test_decide_proceed_when_all_required_slots_high_confidence():
    state = SemanticState(slots={
        "operation": SlotValue(value="define", confidence=0.8, source="inferred"),
        "variable": SlotValue(value="componentes", confidence=0.85, source="inferred"),
    })
    assert decide(state) == "proceed"


def test_decide_confirm_when_slots_present_but_medium_confidence():
    state = SemanticState(slots={
        "operation": SlotValue(value="define", confidence=0.6, source="inferred"),
        "variable": SlotValue(value="componentes", confidence=0.6, source="inferred"),
    })
    assert decide(state) == "confirm"


def test_decide_clarify_when_operation_missing():
    state = SemanticState(slots={
        "variable": SlotValue(value="componentes", confidence=0.8, source="inferred"),
    })
    assert decide(state) == "clarify"


def test_decide_proceed_when_max_clarification_rounds_reached():
    state = SemanticState(clarification_round=MAX_CLARIFICATION_ROUNDS)
    assert decide(state) == "proceed"


# ─── to_draft_patch() ─────────────────────────────────────────────────────────

def test_to_draft_patch_maps_operation_to_enum():
    state = SemanticState(slots={
        "operation": SlotValue(value="define", confidence=0.8, source="inferred"),
        "variable": SlotValue(value="componentes", confidence=0.8, source="inferred"),
    })
    patch = to_draft_patch(state)
    assert patch["operation"] is IterationOperation.DEFINE
    assert patch["variable"] == "componentes"


def test_to_draft_patch_never_emits_raw_string_for_operation():
    state = SemanticState(slots={
        "operation": SlotValue(value="diseñar el motor", confidence=0.5, source="inferred"),
    })
    patch = to_draft_patch(state)
    # "diseñar el motor" is not a valid enum value → should be omitted
    assert "operation" not in patch


def test_to_draft_patch_omits_empty_slots():
    state = SemanticState(slots={
        "operation": SlotValue(value=None, confidence=0.0, source="inferred"),
    })
    patch = to_draft_patch(state)
    assert "operation" not in patch


# ─── Regression: "diseñar el motor" en step 2 no debe crashear ────────────────

def _session_from_response(response: dict) -> InteractiveSessionState:
    return InteractiveSessionState(
        mode=OrchestratorMode(response["mode"]),
        step=response["step"],
        iteration_draft=IterationDraft.model_validate(response["iteration_draft"]),
        semantic_state=None,
    )


def test_disenar_el_motor_at_step2_does_not_crash():
    """Regression: escribir 'diseñar el motor' en step 2 no lanza Pydantic ValidationError."""
    session = IterateInteractiveSession()
    start = session.start({
        "project_id": "abc123",
        "project_slug": "dron-test",
        "workspace_path": "/tmp/test",
        "objetivo": "sistema propulsivo",
        "operacion": "define",
    })
    current = _session_from_response(start)

    # Step 0: confirmar
    r1 = session.answer(current, "sí")
    current = _session_from_response(r1)

    # Step 1: variable
    r2 = session.answer(current, "componentes")
    current = _session_from_response(r2)

    # Step 2: strategy — exactamente el input que causaba el crash
    r3 = session.answer(current, "diseñar el motor")

    # Debe avanzar sin lanzar excepción
    assert r3.get("status") in {"interactive", "confirmed"}
    draft = r3.get("iteration_draft", {})
    operation = draft.get("operation")
    # La operación debe ser un valor válido del enum o None — nunca el raw string
    if operation is not None:
        assert operation in {op.value for op in IterationOperation}
