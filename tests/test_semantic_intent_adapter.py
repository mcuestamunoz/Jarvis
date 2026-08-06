"""Tests for SemanticIntentAdapter (FASE_LLM)."""
from jarvis.llm.semantic_intent_adapter import (
    CONFIDENCE_THRESHOLD,
    AdaptRejection,
    SemanticIntentAdapter,
    SemanticInterpretation,
)
from jarvis.schemas.action_schema import IterationOperation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_output(
    variable: str,
    operacion: str = "increase",
    confidence: float = 0.9,
    valor=None,
    raw_user_input: str | None = None,
) -> dict:
    params: dict = {"variable": variable, "operacion": operacion, "confidence": confidence}
    if valor is not None:
        params["valor"] = valor
    out: dict = {"action": "iterate", "parameters": params}
    if raw_user_input is not None:
        out["raw_user_input"] = raw_user_input
    return out


adapter = SemanticIntentAdapter()


# ---------------------------------------------------------------------------
# Variable resolution
# ---------------------------------------------------------------------------

def test_direct_canonical_key_resolves():
    result = adapter.adapt(_make_llm_output("battery_capacity_wh"))
    assert isinstance(result, SemanticInterpretation)
    assert result.variable == "battery_capacity_wh"


def test_display_alias_resolves():
    """'batería' is an alias for battery_capacity_wh."""
    result = adapter.adapt(_make_llm_output("batería"))
    assert result is not None
    assert result.variable == "battery_capacity_wh"


def test_display_alias_without_accent_resolves():
    """'bateria' (no tilde) normalises identically."""
    result = adapter.adapt(_make_llm_output("bateria"))
    assert result is not None
    assert result.variable == "battery_capacity_wh"


def test_concept_alias_resolves():
    """'carga' is a concept alias for payload_kg."""
    result = adapter.adapt(_make_llm_output("carga"))
    assert result is not None
    assert result.variable == "payload_kg"


def test_concept_alias_payload_resolves():
    result = adapter.adapt(_make_llm_output("payload"))
    assert result is not None
    assert result.variable == "payload_kg"


def test_unknown_variable_returns_adapt_rejection():
    """Invented variable → AdaptRejection with reason=unknown_variable."""
    result = adapter.adapt(_make_llm_output("turbocompresor"))
    assert isinstance(result, AdaptRejection)
    assert result.reason == "unknown_variable"
    assert "turbocompresor" in result.redirect_message


def test_empty_variable_returns_none():
    result = adapter.adapt(_make_llm_output(""))
    assert result is None


def test_missing_variable_key_returns_none():
    llm_output = {"action": "iterate", "parameters": {"operacion": "increase", "confidence": 0.9}}
    result = adapter.adapt(llm_output)
    assert result is None


# ---------------------------------------------------------------------------
# Derived variables are rejected with AdaptRejection
# ---------------------------------------------------------------------------

def test_derived_variable_autonomia_returns_adapt_rejection():
    """autonomia is_derived=True → AdaptRejection with reason=derived_variable."""
    result = adapter.adapt(_make_llm_output("autonomia"))
    assert isinstance(result, AdaptRejection)
    assert result.reason == "derived_variable"


def test_derived_variable_redirect_message_is_non_empty():
    result = adapter.adapt(_make_llm_output("autonomia"))
    assert isinstance(result, AdaptRejection)
    assert result.redirect_message  # non-empty


def test_derived_variable_redirect_message_contains_registry_text():
    """The redirect message should come from the registry's derived_message."""
    from jarvis.core.parameter_requirements import PARAMETER_REQUIREMENTS
    expected = PARAMETER_REQUIREMENTS["autonomia"].derived_message
    result = adapter.adapt(_make_llm_output("autonomia"))
    assert isinstance(result, AdaptRejection)
    assert result.redirect_message == expected


def test_derived_variable_via_alias_returns_adapt_rejection():
    """Even if the LLM uses 'autonomía' alias, derived must be rejected."""
    result = adapter.adapt(_make_llm_output("autonomía"))
    assert isinstance(result, AdaptRejection)
    assert result.reason == "derived_variable"


# ---------------------------------------------------------------------------
# Non-iterate actions are ignored
# ---------------------------------------------------------------------------

def test_non_iterate_action_returns_none():
    llm_output = {"action": "calculate", "parameters": {"variable": "motors", "confidence": 0.9}}
    result = adapter.adapt(llm_output)
    assert result is None


def test_missing_action_returns_none():
    result = adapter.adapt({"parameters": {"variable": "motors", "confidence": 0.9}})
    assert result is None


# ---------------------------------------------------------------------------
# Confidence routing
# ---------------------------------------------------------------------------

def test_high_confidence_sets_flag():
    result = adapter.adapt(_make_llm_output("motors", confidence=CONFIDENCE_THRESHOLD))
    assert result is not None
    assert result.is_high_confidence is True


def test_high_confidence_above_threshold():
    result = adapter.adapt(_make_llm_output("motors", confidence=0.95))
    assert result is not None
    assert result.is_high_confidence is True


def test_low_confidence_below_threshold():
    result = adapter.adapt(_make_llm_output("motors", confidence=0.74))
    assert result is not None
    assert result.is_high_confidence is False


def test_zero_confidence():
    result = adapter.adapt(_make_llm_output("motors", confidence=0.0))
    assert result is not None
    assert result.is_high_confidence is False


def test_confidence_clamped_to_one():
    result = adapter.adapt(_make_llm_output("motors", confidence=5.0))
    assert result is not None
    assert result.confidence == 1.0
    assert result.is_high_confidence is True


def test_confidence_clamped_to_zero():
    result = adapter.adapt(_make_llm_output("motors", confidence=-1.0))
    assert result is not None
    assert result.confidence == 0.0


def test_invalid_confidence_defaults_to_zero():
    llm_output = {"action": "iterate", "parameters": {"variable": "motors", "confidence": "bad"}}
    result = adapter.adapt(llm_output)
    assert result is not None
    assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Operation normalisation
# ---------------------------------------------------------------------------

def test_operation_increase_english():
    result = adapter.adapt(_make_llm_output("motors", operacion="increase"))
    assert result is not None
    assert result.operation == IterationOperation.INCREASE.value


def test_operation_reduce_english():
    result = adapter.adapt(_make_llm_output("motors", operacion="reduce"))
    assert result is not None
    assert result.operation == IterationOperation.REDUCE.value


def test_operation_define():
    result = adapter.adapt(_make_llm_output("motors", operacion="define"))
    assert result is not None
    assert result.operation == IterationOperation.DEFINE.value


def test_operation_spanish_reducir():
    result = adapter.adapt(_make_llm_output("motors", operacion="reducir"))
    assert result is not None
    assert result.operation == IterationOperation.REDUCE.value


def test_unknown_operation_defaults_to_increase():
    result = adapter.adapt(_make_llm_output("motors", operacion="mystery_op"))
    assert result is not None
    assert result.operation == IterationOperation.INCREASE.value


# ---------------------------------------------------------------------------
# Value extraction
# ---------------------------------------------------------------------------

def test_valor_numeric_is_extracted_as_string():
    result = adapter.adapt(_make_llm_output("battery_capacity_wh", valor=900))
    assert result is not None
    assert result.value == "900"


def test_valor_float_is_extracted():
    result = adapter.adapt(_make_llm_output("payload_kg", valor=3.0))
    assert result is not None
    assert result.value == "3.0"


def test_valor_none_when_not_provided():
    result = adapter.adapt(_make_llm_output("battery_capacity_wh"))
    assert result is not None
    assert result.value is None


# ---------------------------------------------------------------------------
# Additional canonical keys
# ---------------------------------------------------------------------------

def test_structure_mass_factor_canonical():
    result = adapter.adapt(_make_llm_output("structure_mass_factor"))
    assert result is not None
    assert result.variable == "structure_mass_factor"


def test_structure_mass_factor_alias():
    result = adapter.adapt(_make_llm_output("factor_estructura"))
    assert result is not None
    assert result.variable == "structure_mass_factor"


def test_safety_factor_alias():
    result = adapter.adapt(_make_llm_output("factor_seguridad"))
    assert result is not None
    assert result.variable == "safety_factor"


# ---------------------------------------------------------------------------
# _parse_value: value sanitisation
# ---------------------------------------------------------------------------

def test_parse_value_integer():
    result = adapter.adapt(_make_llm_output("battery_capacity_wh", valor=900))
    assert isinstance(result, SemanticInterpretation)
    assert result.value == "900"


def test_parse_value_float():
    result = adapter.adapt(_make_llm_output("payload_kg", valor=2.5))
    assert isinstance(result, SemanticInterpretation)
    assert result.value == "2.5"


def test_parse_value_string_with_units():
    """'800 Wh' → first number '800'."""
    result = adapter.adapt(_make_llm_output("battery_capacity_wh", valor="800 Wh"))
    assert isinstance(result, SemanticInterpretation)
    assert result.value == "800"


def test_parse_value_string_with_embedded_number():
    result = adapter.adapt(_make_llm_output("motors", valor="4 motores"))
    assert isinstance(result, SemanticInterpretation)
    assert result.value == "4"


def test_parse_value_non_numeric_string_returns_none():
    """'mucho' has no number → value is None (wizard will ask)."""
    result = adapter.adapt(_make_llm_output("battery_capacity_wh", valor="mucho"))
    assert isinstance(result, SemanticInterpretation)
    assert result.value is None


def test_parse_value_none_stays_none():
    result = adapter.adapt(_make_llm_output("motors"))
    assert isinstance(result, SemanticInterpretation)
    assert result.value is None


# ---------------------------------------------------------------------------
# Lexical grounding (calibration 2026-08-05 — slang overconfidence)
# ---------------------------------------------------------------------------

def test_slang_mas_chicha_does_not_preseed_battery():
    """LLM invents battery_capacity_wh @ 1.0 for 'más chicha' → must not preseed."""
    result = adapter.adapt(
        _make_llm_output(
            "battery_capacity_wh",
            confidence=1.0,
            valor=150,
            raw_user_input="más chicha",
        )
    )
    assert isinstance(result, SemanticInterpretation)
    assert result.variable == "battery_capacity_wh"
    assert result.is_high_confidence is False
    assert result.confidence < CONFIDENCE_THRESHOLD
    assert result.value is None  # invented number discarded


def test_grounded_battery_request_keeps_high_confidence_and_value():
    result = adapter.adapt(
        _make_llm_output(
            "battery_capacity_wh",
            confidence=0.95,
            valor=120,
            raw_user_input="sube la batería a 120 Wh",
        )
    )
    assert isinstance(result, SemanticInterpretation)
    assert result.is_high_confidence is True
    assert result.value == "120"


def test_grounded_variable_without_number_strips_invented_valor():
    """User named the variable but gave no number — keep confidence, drop invented valor."""
    result = adapter.adapt(
        _make_llm_output(
            "battery_capacity_wh",
            confidence=0.9,
            valor=150,
            raw_user_input="aumenta la batería",
        )
    )
    assert isinstance(result, SemanticInterpretation)
    assert result.is_high_confidence is True
    assert result.value is None


def test_autonomia_slang_mapped_to_battery_is_ungrounded():
    """'quiero más autonomía' does not lexically name battery → no step-2 preseed."""
    result = adapter.adapt(
        _make_llm_output(
            "battery_capacity_wh",
            confidence=1.0,
            valor=150,
            raw_user_input="quiero más autonomía",
        )
    )
    assert isinstance(result, SemanticInterpretation)
    assert result.is_high_confidence is False
    assert result.value is None


def test_missing_raw_user_input_preserves_llm_confidence():
    """Unit/legacy callers without raw_user_input keep previous confidence behaviour."""
    result = adapter.adapt(_make_llm_output("battery_capacity_wh", confidence=0.95, valor=100))
    assert isinstance(result, SemanticInterpretation)
    assert result.is_high_confidence is True
    assert result.value == "100"
