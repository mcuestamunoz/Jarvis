from __future__ import annotations

import re
from typing import Any, Literal

from jarvis.schemas.action_schema import IterationOperation
from jarvis.schemas.semantic_schema import SemanticState, SlotValue


MAX_CLARIFICATION_ROUNDS = 2
REQUIRED_SLOTS = ["operation", "variable"]
CONFIDENCE_PROCEED = 0.75
CONFIDENCE_CONFIRM = 0.4

_OPERATION_MAP: dict[IterationOperation, list[str]] = {
    IterationOperation.DEFINE: [
        "defin", "establec", "usar", "seleccion",
        "diseñar", "disenar", "especific", "poner", "asignar",
        "configur", "fijar",
    ],
    IterationOperation.REDUCE: [
        "reduc", "disminu", "bajar", "menos", "achicar", "disminuy",
    ],
    IterationOperation.INCREASE: [
        "aument", "increment", "subir", "sube",
    ],
    IterationOperation.IMPROVE: [
        "mejor", "perfec",
    ],
    IterationOperation.OPTIMIZE: [
        "optim", "maximiz", "minimiz",
    ],
}

_VARIABLE_KEYWORDS: dict[str, list[str]] = {
    "material":     ["material", "fibra", "carbono", "aluminio", "madera", "plastico", "pvc"],
    "componentes":  ["motor", "esc", "helice", "hélice", "propulsor", "bateria", "batería",
                     "controlador", "sensor", "actuador", "cable", "receptor"],
    "payload":      ["payload", "carga", "peso útil"],
    "estructura":   ["estructura", "chasis", "frame", "brazo", "soporte"],
    "dimensiones":  ["tamaño", "tamano", "dimension", "dimensión", "longitud", "anchura", "altura"],
}


def update(
    state: SemanticState,
    user_input: str,
    context: dict[str, Any] | None = None,
) -> SemanticState:
    """
    Devuelve un estado enriquecido con la información del nuevo input.
    Nunca reduce la confianza de slots con source='confirmed'.
    """
    updated_history = state.history + [user_input]

    updated_slots = dict(state.slots)
    _merge_slot(updated_slots, "operation", _extract_operation_slot(user_input), state.slots)
    _merge_slot(updated_slots, "variable", _extract_variable_slot(user_input), state.slots)
    _merge_slot(updated_slots, "value", _extract_value_slot(user_input), state.slots)
    _merge_slot(updated_slots, "objective", _extract_objective_slot(user_input), state.slots)

    missing = _compute_missing_slots(updated_slots)
    intent, intent_conf = _extract_intent(updated_slots)
    alternatives = _compute_alternatives(updated_slots, user_input)

    clarification_round = state.clarification_round
    forced = state.forced
    if clarification_round >= MAX_CLARIFICATION_ROUNDS and missing:
        forced = True

    # ── multi-entity + focus + active_intent ──────────────────────────────
    new_entities = _extract_entities(user_input)
    merged_entities = list(dict.fromkeys(state.entities + new_entities))  # preserve order, dedupe
    new_focus = _detect_focus(user_input, merged_entities) or state.focus
    new_active_intent = _detect_active_intent(user_input, updated_slots) or state.active_intent
    # ──────────────────────────────────────────────────────────────────────

    return state.model_copy(update={
        "slots": updated_slots,
        "missing_slots": missing,
        "history": updated_history,
        "intent": intent,
        "intent_confidence": intent_conf,
        "alternatives": alternatives,
        "forced": forced,
        "entities": merged_entities,
        "focus": new_focus,
        "active_intent": new_active_intent,
    })


def decide(state: SemanticState) -> Literal["proceed", "confirm", "clarify"]:
    """
    proceed  → todos los required_slots tienen confidence >= 0.75, o se alcanzó MAX_CLARIFICATION_ROUNDS
    confirm  → todos los required_slots presentes pero alguno en [0.4, 0.75)
    clarify  → un required slot ausente o confidence < 0.4
    """
    if state.clarification_round >= MAX_CLARIFICATION_ROUNDS:
        return "proceed"

    all_present = True
    min_confidence = 1.0

    for slot_name in REQUIRED_SLOTS:
        slot = state.slots.get(slot_name)
        if slot is None or slot.value is None:
            all_present = False
            break
        min_confidence = min(min_confidence, slot.confidence)

    if not all_present:
        return "clarify"
    if min_confidence < CONFIDENCE_CONFIRM:
        return "clarify"
    if min_confidence < CONFIDENCE_PROCEED:
        return "confirm"
    return "proceed"


def to_draft_patch(state: SemanticState) -> dict[str, Any]:
    """
    Mapea slots a campos de IterationDraft.
    operation siempre es IterationOperation | None — nunca raw string.
    Omite slots con value=None.
    """
    patch: dict[str, Any] = {}

    op_slot = state.slots.get("operation")
    if op_slot and op_slot.value:
        op = _slot_to_operation(op_slot)
        if op is not None:
            patch["operation"] = op

    for field in ("variable", "value", "objective", "restrictions"):
        slot = state.slots.get(field)
        if slot and slot.value:
            patch[field] = slot.value

    return patch


def extract_entities(text: str) -> list[str]:
    """Public wrapper around _extract_entities for use by session handlers."""
    return _extract_entities(text)


def increment_clarification_round(state: SemanticState) -> SemanticState:
    return state.model_copy(update={"clarification_round": state.clarification_round + 1})


# ─── Helpers privados ─────────────────────────────────────────────────────────

def _merge_slot(
    target: dict[str, SlotValue],
    name: str,
    candidate: SlotValue,
    existing: dict[str, SlotValue],
) -> None:
    """
    Actualiza target[name] con candidate solo si:
    - no existe aún
    - el candidato tiene mayor confianza
    - el slot existente NO es 'confirmed'
    """
    if candidate.value is None:
        return
    current = existing.get(name)
    if current is None:
        target[name] = candidate
        return
    if current.source == "confirmed":
        return
    if candidate.confidence > current.confidence:
        target[name] = candidate


def _extract_operation_slot(text: str) -> SlotValue:
    normalized = text.lower()
    for op, keywords in _OPERATION_MAP.items():
        if any(k in normalized for k in keywords):
            return SlotValue(value=op.value, confidence=0.8, source="inferred")
    return SlotValue(value=None, confidence=0.0, source="inferred")


def _extract_variable_slot(text: str) -> SlotValue:
    normalized = text.lower()
    for variable, keywords in _VARIABLE_KEYWORDS.items():
        if any(k in normalized for k in keywords):
            return SlotValue(value=variable, confidence=0.75, source="inferred")
    return SlotValue(value=None, confidence=0.0, source="inferred")


def _extract_value_slot(text: str) -> SlotValue:
    """
    Extrae un valor técnico explícito si el texto tiene al menos 2 palabras
    y parece una especificación (no es solo una operación).
    """
    stripped = text.strip()
    if len(stripped.split()) >= 2 and not _is_pure_operation_phrase(stripped):
        return SlotValue(value=stripped, confidence=0.6, source="inferred")
    return SlotValue(value=None, confidence=0.0, source="inferred")


def _extract_objective_slot(text: str) -> SlotValue:
    stripped = text.strip()
    if len(stripped.split()) >= 3:
        return SlotValue(value=stripped, confidence=0.5, source="inferred")
    return SlotValue(value=None, confidence=0.0, source="inferred")


def _is_pure_operation_phrase(text: str) -> bool:
    normalized = text.lower()
    all_keywords = [k for keywords in _OPERATION_MAP.values() for k in keywords]
    return all(any(k in word for k in all_keywords) for word in normalized.split())


def _compute_missing_slots(slots: dict[str, SlotValue]) -> list[str]:
    missing = []
    for name in REQUIRED_SLOTS:
        slot = slots.get(name)
        if slot is None or slot.value is None or slot.confidence < CONFIDENCE_CONFIRM:
            missing.append(name)
    return missing


def _extract_intent(slots: dict[str, SlotValue]) -> tuple[str | None, float]:
    op_slot = slots.get("operation")
    var_slot = slots.get("variable")
    if op_slot and op_slot.value and var_slot and var_slot.value:
        intent = f"{op_slot.value} {var_slot.value}"
        confidence = min(op_slot.confidence, var_slot.confidence)
        return intent, confidence
    if op_slot and op_slot.value:
        return op_slot.value, op_slot.confidence * 0.5
    return None, 0.0


def _compute_alternatives(slots: dict[str, SlotValue], user_input: str) -> list[str]:
    """Genera alternativas solo cuando la operación es 'mejorar' (ambigua por naturaleza)."""
    op_slot = slots.get("operation")
    if op_slot and op_slot.value == IterationOperation.IMPROVE.value:
        normalized = user_input.lower()
        alts = []
        if "rendimiento" in normalized or "eficiencia" in normalized:
            alts = ["reducir peso", "cambiar hélices", "mejorar motor"]
        return alts
    return []


def _slot_to_operation(slot: SlotValue) -> IterationOperation | None:
    if not slot.value:
        return None
    try:
        return IterationOperation(slot.value)
    except ValueError:
        return None


# ─── Multi-entity + focus + active_intent ─────────────────────────────────────

_LIST_SEPARATORS = re.compile(r"\s*[,;]\s*|\s+y\s+|\s+e\s+")

_FOCUS_MARKERS = ("primero", "primero las", "empezar con", "empecemos con", "quiero las", "las")


def _extract_entities(text: str) -> list[str]:
    """
    Extrae entidades independientes de un texto en dos fases:
    1. Split por separadores de lista.
    2. Validar cada candidato: si _extract_variable_slot tiene confianza >= 0.5
       es entidad independiente, si no se descarta (probable modificador).
    """
    candidates = [t.strip() for t in _LIST_SEPARATORS.split(text) if t.strip()]
    if len(candidates) <= 1:
        return []  # no hay lista — no inferir entidades falsas

    entities: list[str] = []
    last_valid: str | None = None
    for candidate in candidates:
        slot = _extract_variable_slot(candidate)
        if slot.confidence >= 0.5:
            entities.append(candidate)
            last_valid = candidate
        elif last_valid is not None:
            # modificador del anterior — merge al último válido
            idx = entities.index(last_valid)
            entities[idx] = f"{last_valid} {candidate}"
            last_valid = entities[idx]
    return entities


def _detect_focus(text: str, entities: list[str]) -> str | None:
    """
    Detecta si el texto señala un foco dentro de una lista de entidades.
    "Quiero definir primero las helices" → "helices"
    """
    normalized = text.lower()
    for marker in _FOCUS_MARKERS:
        if marker in normalized:
            # buscar qué entidad se menciona tras el marker
            for entity in entities:
                if entity.lower() in normalized:
                    return entity
            # sin coincidencia exacta: usar _extract_variable_slot sobre el input
            slot = _extract_variable_slot(text)
            if slot.confidence >= 0.5 and slot.value:
                return slot.value
    # sin marker: si hay una sola entidad coercible, usarla como foco
    if len(entities) == 1:
        return entities[0]
    return None


_ACTIVE_INTENT_MAP: list[tuple[str, list[str]]] = [
    ("define_components", ["componen", "motores", "helice", "bateria", "esc", "cableado", "actuador", "sensor"]),
    ("define_property",   ["peso", "tamaño", "tamano", "altura", "longitud", "diámetro", "diametro"]),
    ("modify_component",  ["cambiar", "reemplazar", "sustituir", "actualizar"]),
]


def _detect_active_intent(text: str, slots: dict[str, SlotValue]) -> str | None:
    """
    Devuelve el intent de alto nivel de la acción en curso.
    Se preserva entre turns (update() no borra el valor existente).
    """
    normalized = text.lower()
    op_slot = slots.get("operation")
    op_value = op_slot.value if op_slot else None

    for intent_key, keywords in _ACTIVE_INTENT_MAP:
        if any(kw in normalized for kw in keywords):
            # solo señalar define_components si la operación es define o no está definida
            if intent_key == "define_components" and op_value not in (None, "define"):
                continue
            return intent_key
    return None
