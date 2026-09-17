# Implementation Report — Continuity next-step vs mission intent (`B1-continuity-mission-intent`)

**IC:** `implementation_contract_continuity_mission_intent_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-16
**Checkpoint:** package `0.4.1` (unchanged) · suite **2985 passed, 1 skipped** (was 2968) · UI unaffected (no UI files touched)

---

## 1. Scope delivered

Exactly the locked scope — when mission intent is active and thrust margin is high, `increase_payload`/"Aumentar carga útil" is suppressed and replaced by one deterministic, mission-aware alternate suggestion (lock #5a–d). When mission intent is not active, behavior is byte-identical to before. No LLM, no free-form NLP beyond the frozen keyword tuple, no camera/plate/firmware invention, no `HIGH_MARGIN_THRESHOLD` change, no `ASSEMBLY_READY` flip, no new wizard, no version bump, no `workspace/` mutation (all live-project reads in this cycle were in-memory `ProjectState.model_validate(json.load(...))` verification — never `save_state`).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/reasoning_layer.py` | New frozen `_MISSION_INTENT_KEYWORDS` tuple + `_MISSION_INTENT_RE`; new `_MISSION_COMPONENT_KEYS = ("cameras", "radio_module")`; new pure function `mission_intent_active(objective, restrictions, components) -> bool`; new method `ReasoningLayer._mission_aware_high_margin_suggestion(context)` implementing the lock #5a–d waterfall; the single `increase_payload` fire-site (`_collect_suggested_actions`, previously unconditional) now calls this helper first and only falls back to the original "Aumentar carga útil" suggestion when it returns `None`. |
| `tests/test_continuity_mission_intent_b1.py` (new) | 17 tests, T1–T7 (see §5). |

No other files needed changes — see §3 for why.

## 3. Why no other files changed (confirms IC's own uncertainty points)

- **Single fire-site confirmed**: grepped the full `src/` tree for `increase_payload` — the ONLY places it appears are `reasoning_layer.py`'s own `CONFLICT_RULES` entry, its `action_map` dict entry (dead unless some future `suggestions` source emits `type: "increase_payload"` — none does today), and the one fallback append (now gated). No second fire-site exists anywhere else in the codebase.
- **`action_type` needs no schema change**: `ReasoningSuggestion.action_type: str | None` (`schemas/tool_schema.py:137`) is already an open string, not a closed `Literal` — `"complete_mission_payload"` and `"mission_margin_review"` required no allowlist edit.
- **`action` stays `"iterate"`**: already a valid member of the closed `ReasoningActionType` Literal — no schema change, no new orchestrator wizard (lock #5a).
- **Continuity/CLI need no changes**: `project_continuity.py` and `orchestrator.py`'s `build_startup_context`/`_handle_project_status` already consume `reasoning.suggested_actions[0]` (first non-blocked, non-dismissed) as `suggested_action` verbatim (`orchestrator.py:6457-6467`) and pass it straight into `build_project_continuity(..., suggested_action=suggested_action, ...)` (`orchestrator.py:6658-6667`). Since the fix lives entirely inside `ReasoningLayer`, the new suggestion flows through this existing pipe unchanged — exactly the "do not invent a parallel Continuity ranker" instruction in lock #2.

## 4. The `mission_intent_active` helper and keyword set

```python
_MISSION_INTENT_KEYWORDS: tuple[str, ...] = (
    "vigilancia", "vigilancia doméstica", "vigilancia domestica",
    "surveillance", "inspección", "inspeccion", "inspection",
    "fotografía", "fotografia", "photography",
    "cámara", "camara", "camera", "fpv",
    "comunicación", "comunicacion",
    "telemetría", "telemetria",
)
```

Exactly the IC's own minimum set (lock #4) — no extension needed; tests passed without adding more. Matched via a single `\b(?:...)\b` case-insensitive regex over `objective + " " + restrictions` — word-boundary, not bare substring, so a longer word that happens to contain a keyword (e.g. `"previsión"`, `"vehículo"`) never false-positives (T6's over-match guard test). `mission_intent_active` returns `True` on either path A (keyword in objective/restrictions) or path B (`cameras` and/or `radio_module` already a key in `design_properties.components`, any completeness) — matching lock #3 exactly.

## 5. The lock #5 waterfall

`_mission_aware_high_margin_suggestion` implements the exact fixed order from lock #5, first match wins:

| Case | Condition | Label | `action_type` |
|---|---|---|---|
| 5a | `cameras` absent | `"Declarar carga de misión (cámara)"` | `complete_mission_payload` |
| 5b | `cameras.completeness == "low"` | `"Completar identidad de cámara"` | `complete_mission_payload` |
| 5c (absent) | `radio_module` absent | `"Declarar carga de misión (radio)"` | `complete_mission_payload` |
| 5c (low) | `radio_module.completeness == "low"` | `"Completar identidad de radio"` | `complete_mission_payload` |
| 5d | both present at medium+ | `"Revisar margen vs carga de misión"` | `mission_margin_review` |

**Choice made for 5d** (the IC offered two options — soften or suppress): implemented the **softened alternate suggestion**, not silent suppression. Rationale: the IC's own product sentence ("te señala completar la carga de misión") implies Jarvis should always point at *something* actionable rather than go quiet; a fully-declared mission payload with surplus margin is itself a real, honestly-nameable state ("the margin surplus is a mission decision, not a generic payload bump") rather than nothing to say. All five outcomes share priority `0.8` (same band as the original suggestion, per lock #5).

## 6. Empirical verification (before writing tests)

Unit-level, synthetic:
```
mission_intent_active("dron de vigilancia doméstico", "no", {})  → True
mission_intent_active("prueba", "no", {})                        → False
mission_intent_active("prueba", "no", {"cameras": {}})           → True
mission_intent_active("previsión de vuelo", None, {})            → False  (word-boundary guard)
```

Full `ReasoningLayer.build()` waterfall, synthetic high-margin context:
```
neutral, no components               → "Aumentar carga útil" / increase_payload   (T2 regression)
"dron de inspección", no cameras     → "Declarar carga de misión (cámara)" / complete_mission_payload
cameras completeness=low             → "Completar identidad de cámara" / complete_mission_payload
cameras=medium, radio absent         → "Declarar carga de misión (radio)" / complete_mission_payload
cameras=medium, radio=low            → "Completar identidad de radio" / complete_mission_payload
```

**Live project** (`dron-de-vigilancia-doméstico`, read in-memory via `ProjectState.model_validate(json.load(...))`, never saved): objective `"dron de vigilancia doméstico"`, `cameras` completeness `medium` (RunCam), `radio_module` completeness `medium` (ELRS), `safety_margin_ratio=3.6196` (≥ `HIGH_MARGIN_THRESHOLD`). Top suggestion: **`"Revisar margen vs carga de misión"`** — confirms the exact live-smoke scenario named in the IC's parents section (§ "Live smoke: `dron-de-vigilancia-doméstico` → PASS + 'Aumentar carga útil' despite vigilancia/cameras declared") is now fixed.

## 7. Tests

### Added (`tests/test_continuity_mission_intent_b1.py`, 17 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_vigilancia_objective_suppresses_increase_payload` | Objective keyword suppresses `increase_payload` |
| T2 | `test_t2_neutral_objective_keeps_increase_payload_regression`, `test_t2_empty_objective_keeps_increase_payload_regression` | Regression — neutral/empty text still shows `increase_payload` |
| T3 | `test_t3_cameras_component_present_suppresses_increase_payload_no_keyword`, `test_t3_radio_component_present_suppresses_increase_payload_no_keyword` | Component-presence path (B) alone is sufficient, no keyword needed |
| T4 | `test_t4_alternate_label_when_cameras_absent_mission_text`, `test_t4_alternate_label_when_cameras_absent_via_radio_component` | 5a fires correctly, including when mission signal comes from the *other* component |
| T5 | `test_t5_cameras_low_completeness_gets_complete_identity_label`, `test_t5_radio_absent_after_camera_medium_gets_declare_radio_label`, `test_t5_radio_low_after_camera_medium_gets_complete_radio_identity_label`, `test_t5_both_medium_plus_softens_to_margin_review_5d` | 5b/5c/5d waterfall, in order |
| T6 | `test_t6_keyword_hits`, `test_t6_keyword_misses`, `test_t6_component_presence_alone_is_sufficient`, `test_t6_over_match_guard_previsualizacion_and_similar_words` | `mission_intent_active` unit coverage incl. over-match guard |
| T7 | `test_t7_continuity_vigilancia_shaped_closed_design_never_shows_increase_payload`, `test_t7_continuity_neutral_closed_design_still_shows_increase_payload_regression` | End-to-end `ReasoningLayer` → `build_project_continuity`, `architecture_progress="4/4"`, sim PASS, empty incomplete/missing BOM — mirrors the real vigilancia project's exact shape and its neutral-regression companion |

### Executed

```
python -m pytest tests/test_continuity_mission_intent_b1.py -q  → 17 passed
python -m pytest -q                                              → 2985 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected by this Buy).

## 8. Out of scope (unchanged, named debt per IC §4)

Wizard vigilancia nudge at SYSTEM_DEFINITION (queue #2) · `propellers ↔ motors` (queue #3) · bind-esc/FC change hygiene (queue #4) · `payload_bay`/`arm` identity (queue #5) · plate-box/HD-* (parked physical).

## 9. Remaining risks

None identified. `CONFLICT_RULES` (which blocks `increase_payload` under `low_margin`/`high_actuator_load`) is untouched and structurally cannot fire against the new `complete_mission_payload`/`mission_margin_review` action types (those only ever appear when `high_margin` is already true, which is mutually exclusive with `low_margin` by threshold definition). The `action_map` loop's own dead `increase_payload` entry (fed by the `suggestions` parameter, not the fallback this Buy gates) was left untouched — no production code path currently emits that suggestion type from outside `ReasoningLayer`, so it was out of this Buy's actual scope per §3's confirmation.
