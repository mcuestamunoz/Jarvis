"""Semantic Intent Adapter — FASE_LLM.

Converts raw LLM iterate output into a validated :class:`SemanticInterpretation`.
This is the single gate between the LLM and the iterate wizard:

* Validates ``variable`` against ``PARAMETER_REQUIREMENTS``.
* Rejects derived variables (non-settable) with a rich :class:`AdaptRejection`.
* Normalises the ``operation`` to an :class:`~jarvis.schemas.action_schema.IterationOperation` value.
* Exposes a confidence-based routing signal (``is_high_confidence``).
* Caps LLM-reported confidence when the user text does not lexically ground the
  proposed variable (calibration 2026-08-05: slang like ``más chicha`` must not
  preseed ``battery_capacity_wh`` at confidence 1.0).
* Drops invented numeric ``valor`` when the user text contains no number.

Return contract of :meth:`SemanticIntentAdapter.adapt`:

* ``None``                — input is not an iterate action or variable field is absent.
  Caller should not make any routing decision based on LLM output.
* :class:`AdaptRejection` — variable is known-invalid (derived or unknown).
  Caller should fall back to the normal wizard, optionally showing ``redirect_message``.
* :class:`SemanticInterpretation` — variable is valid and routing can proceed.

Usage::

    adapter = SemanticIntentAdapter()
    result = adapter.adapt(llm_action_request_dict)
    if isinstance(result, SemanticInterpretation) and result.is_high_confidence:
        # preseed wizard at step 2
    elif isinstance(result, AdaptRejection) and result.redirect_message:
        # show redirect_message, then open wizard at step 0
    else:
        # normal wizard from step 0
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from jarvis.core.parameter_requirements import (
    PARAMETER_REQUIREMENTS,
    build_alias_map,
    build_normalization_map,
    normalize_alias,
)
from jarvis.schemas.action_schema import IterationOperation

CONFIDENCE_THRESHOLD: float = 0.75
# When user text does not mention the proposed variable (or its aliases),
# force confidence strictly below the preseed threshold.
_UNGROUNDED_CONFIDENCE_CAP: float = CONFIDENCE_THRESHOLD - 0.01
_MIN_GROUNDING_TOKEN_LEN: int = 4
_USER_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")

# Normalised alias → canonical name (built once at import time — PARAMETER_REQUIREMENTS is static)
_ALIAS_MAP: dict[str, str] = build_alias_map()
_CONCEPT_MAP: dict[str, str] = build_normalization_map()

# English/Spanish operation words → IterationOperation canonical value
_OPERATION_MAP: dict[str, str] = {
    "increase": IterationOperation.INCREASE.value,
    "aumentar": IterationOperation.INCREASE.value,
    "reduce": IterationOperation.REDUCE.value,
    "reducir": IterationOperation.REDUCE.value,
    "decrease": IterationOperation.REDUCE.value,
    "disminuir": IterationOperation.REDUCE.value,
    "define": IterationOperation.DEFINE.value,
    "set": IterationOperation.DEFINE.value,
    "improve": IterationOperation.IMPROVE.value,
    "mejorar": IterationOperation.IMPROVE.value,
    "optimize": IterationOperation.OPTIMIZE.value,
    "optimizar": IterationOperation.OPTIMIZE.value,
}

RejectionReason = Literal["derived_variable", "unknown_variable"]


@dataclass
class AdaptRejection:
    """Structured rejection returned when the LLM proposes an invalid variable.

    ``reason`` distinguishes between two cases so the caller can tailor UX:

    * ``"derived_variable"`` — variable exists in the registry but is not settable.
      ``redirect_message`` contains a human-readable explanation sourced from the
      registry's ``derived_message`` (never None for this reason).
    * ``"unknown_variable"`` — variable was not found in the registry at all.
      ``redirect_message`` is a generic fallback.
    """

    reason: RejectionReason
    redirect_message: str


@dataclass
class SemanticInterpretation:
    """Validated interpretation of an LLM iterate proposal."""

    operation: str          # IterationOperation value (e.g. "aumentar")
    variable: str           # Canonical registry key (e.g. "battery_capacity_wh")
    value: str | None       # Raw value string, or None if not specified
    confidence: float       # 0.0–1.0, self-reported by LLM (possibly capped)
    is_high_confidence: bool  # True when confidence >= CONFIDENCE_THRESHOLD


class SemanticIntentAdapter:
    """Validates and converts LLM iterate output.

    :meth:`adapt` is the single public entry-point.

    Return values:

    * ``None`` — input is not an iterate action or the ``variable`` field is
      absent/empty.  The caller should not make a routing decision from LLM output.
    * :class:`AdaptRejection` — variable is known-invalid; show
      ``redirect_message`` and fall back to the standard wizard at step 0.
    * :class:`SemanticInterpretation` — variable is valid and settable;
      route using ``is_high_confidence``.
    """

    def adapt(self, llm_output: dict) -> SemanticInterpretation | AdaptRejection | None:
        """Validate and convert an LLM iterate output dict.

        ``llm_output`` is the full action request dict::

            {"action": "iterate", "parameters": {...}, "raw_user_input": "..."}

        Returns ``None`` when ``action != "iterate"`` or ``variable`` is absent.
        Returns :class:`AdaptRejection` for unknown or derived variables.
        Returns :class:`SemanticInterpretation` on success.
        """
        if llm_output.get("action") != "iterate":
            return None

        params = llm_output.get("parameters") or {}

        raw_variable: str = str(params.get("variable") or "").strip()
        if not raw_variable:
            return None

        canonical = self._resolve_variable(raw_variable)
        if canonical is None:
            return AdaptRejection(
                reason="unknown_variable",
                redirect_message=(
                    f"No reconozco '{raw_variable}' como variable modificable. "
                    "Puedo ayudarte a elegir una variable del sistema."
                ),
            )

        req = PARAMETER_REQUIREMENTS.get(canonical)
        if req and req.is_derived:
            return AdaptRejection(
                reason="derived_variable",
                redirect_message=(
                    req.derived_message
                    or f"'{canonical}' es una variable derivada y no se puede modificar directamente."
                ),
            )

        operation_raw: str = str(
            params.get("operacion") or params.get("operation") or ""
        ).strip().lower()
        operation = _OPERATION_MAP.get(operation_raw, IterationOperation.INCREASE.value)

        raw_value = params.get("valor") or params.get("value")
        value = self._parse_value(raw_value)

        try:
            confidence = float(params.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = 0.0

        # Calibration 2026-08-05: do not trust LLM confidence / invented values
        # when the user text does not name the proposed Action Space variable.
        raw_user_input = str(llm_output.get("raw_user_input") or "").strip()
        if raw_user_input:
            if not self._is_variable_grounded(raw_user_input, canonical):
                confidence = min(confidence, _UNGROUNDED_CONFIDENCE_CAP)
            if value is not None and not self._user_specified_number(raw_user_input):
                value = None

        return SemanticInterpretation(
            operation=operation,
            variable=canonical,
            value=value,
            confidence=confidence,
            is_high_confidence=confidence >= CONFIDENCE_THRESHOLD,
        )

    def _resolve_variable(self, raw: str) -> str | None:
        """Resolve *raw* to a canonical ``PARAMETER_REQUIREMENTS`` key.

        Resolution order (most-specific first):
        1. Direct canonical key match.
        2. Normalised canonical key match.
        3. Display alias map (``build_alias_map()``).
        4. Concept alias map (``build_normalization_map()``).
        """
        if not raw:
            return None

        # 1. Direct canonical key
        if raw in PARAMETER_REQUIREMENTS:
            return raw

        normalized = normalize_alias(raw)

        # 2. Normalised canonical match
        for canonical in PARAMETER_REQUIREMENTS:
            if normalize_alias(canonical) == normalized:
                return canonical

        # 3. Display alias (e.g. "batería" → "battery_capacity_wh")
        if normalized in _ALIAS_MAP:
            return _ALIAS_MAP[normalized]

        # 4. Concept alias (e.g. "carga" → "payload_kg")
        if normalized in _CONCEPT_MAP:
            return _CONCEPT_MAP[normalized]

        return None

    def _is_variable_grounded(self, user_input: str, canonical: str) -> bool:
        """True when *user_input* lexically mentions *canonical* (or an alias)."""
        normalized_input = normalize_alias(user_input)
        for token in self._grounding_tokens(canonical):
            if token in normalized_input:
                return True
        return False

    @staticmethod
    def _grounding_tokens(canonical: str) -> frozenset[str]:
        """Lexical evidence tokens that justify proposing *canonical*."""
        tokens: set[str] = set()
        candidates: list[str] = [canonical, *canonical.split("_")]
        req = PARAMETER_REQUIREMENTS.get(canonical)
        if req is not None:
            candidates.extend(req.aliases)
            candidates.extend(req.concept_aliases)
            if req.display_name:
                candidates.append(req.display_name)

        for candidate in candidates:
            normalized = normalize_alias(candidate)
            if len(normalized) >= _MIN_GROUNDING_TOKEN_LEN:
                tokens.add(normalized)
            for part in normalized.replace("_", " ").split():
                if len(part) >= _MIN_GROUNDING_TOKEN_LEN:
                    tokens.add(part)
        return frozenset(tokens)

    @staticmethod
    def _user_specified_number(user_input: str) -> bool:
        return _USER_NUMBER_RE.search(user_input) is not None

    @staticmethod
    def _parse_value(raw: object) -> str | None:
        """Sanitise the LLM value field into a bare numeric string or None.

        * Numbers (int / float) → ``str(raw)``
        * Strings with an embedded number → first number extracted (e.g. ``"800 Wh"`` → ``"800"``)
        * Strings with no number (e.g. ``"mucho"``) → ``None``
        * None / missing → ``None``

        The wizard validates the numeric range at step 2; this layer only ensures
        that non-numeric garbage is discarded before reaching the preseed.
        """
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return str(raw)
        text = str(raw).strip()
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return match.group(0) if match else None
