# Implementation Contract — IDLE catalog rebind B3 (motors / propellers / battery)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (Engineer-approved implement-in-place)  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2276**)  
**Review:** [implementation_review_idle_catalog_rebind_b3.md](implementation_review_idle_catalog_rebind_b3.md)  
**Report:** [implementation_report_idle_catalog_rebind_b3.md](implementation_report_idle_catalog_rebind_b3.md)  
**Parent:** [implementation_contract_idle_frame_rebind_b2.md](implementation_contract_idle_frame_rebind_b2.md) — **CLOSED** suite **2250** · field smoke ACCEPT

**Type:** Same B2 bridge for the other three catalog families.  
**Not** name→SKU. **Not** arms↔motors coherence. **Not** Structure reopen. **Not** FC/sensors/ESC catalog.

**Baseline:** Structure block CLOSED @ suite **2229** · B2 CLOSED **2250**

**Buy (locked):** **B3** — Engineer “sí… implementa tú” after B2 smoke.

---

## 0. You

- Mirror B2: IDLE named phrase → `DEFINE_MISSING` + `pending_missing_params=[key]` → existing `_offer_component_*_catalog` **directly** (bypass `_wants_catalog_help` and FN-014 complete gate).
- Reuse existing apply/pick paths unchanged (no frame-style children clear for these families).
- Keep bare `"ayúdame a elegir"` triage (motor→prop→battery) unchanged when **no** family noun is named.
- Do not weaken B2 frame tests. Do not bump version. Full suite green.

---

## 1. Intent

```text
IDLE + architecture 4/4 + component already bound:
  "cambiar motor(es)" | "definir motor" | "ayúdame a elegir motor"
  "cambiar hélice(s)" | "ayúdame a elegir hélice"
  "cambiar batería"   | "ayúdame a elegir batería"
        ↓
  offer that family's numbered catalog (even if catalog_ref set)
        ↓
  pick N → existing apply path
```

Frame phrases remain B2 behavior.

---

## 2. Locked behavior

### 2.1 Resolver

Add `resolve_idle_catalog_rebind(user_input) -> "motors"|"propellers"|"battery"|"frame"|None` (prefer new thin `catalog_rebind_assist.py`, or extend existing assist modules without duplicating normalize).

Requires **family noun** + (rebind verb **or** help-choose soft tokens), same as B2:

| Key | Nouns (normalized, word-boundary) |
|---|---|
| `frame` | `frame`, `chasis` |
| `motors` | `motor`, `motores` |
| `propellers` | `helice`, `helices`, `propeller`, `propellers` |
| `battery` | `bateria`, `baterias`, `battery`, `batteries` |

Verbs: `cambiar|cambia|definir|define|modificar|modifica`  
Help-choose: `ayudame` + `elegir|escoger`

If multiple nouns (pathological), pick **one** deterministic priority: `frame` > `motors` > `propellers` > `battery` (document in code). Normal phrases name one.

`is_frame_rebind_phrase` may become a thin wrapper `resolve(...) == "frame"` so B2 tests keep working.

### 2.2 IDLE dispatch

Replace frame-only block with:

```text
IF IDLE and (key := resolve_idle_catalog_rebind(user_input)):
    set DEFINE_MISSING + pending=[key] + MISSING_COMPONENT_DEFINITION
    call matching _offer_component_{frame|motor|propeller|battery}_catalog(session, [key])
    return
ELIF IDLE and is_help_choose_phrase(...):
    existing motor → prop → battery chain
```

### 2.3 Unchanged

- Apply/pick writers for motors/propellers/battery  
- Frame `clear_frame_part_children` on frame pick only  
- Free-text intercept  
- Continuity coherence  

---

## 3. Tests

Extend `tests/test_idle_frame_rebind_b2.py` **or** add `tests/test_idle_catalog_rebind_b3.py`:

| # | Case |
|---|---|
| B3-T1 | IDLE `cambiar motores` / `cambiar motor` → `motor_suggestions` non-empty; not frame |
| B3-T2 | IDLE `ayúdame a elegir motor` → motor list (not bare triage ambiguity — must be motors) |
| B3-T3 | IDLE `cambiar batería` → battery catalog |
| B3-T4 | IDLE `cambiar hélice` / `ayúdame a elegir hélice` → propeller catalog |
| B3-T5 | Pick after rebind binds new `catalog_ref` (one family enough, e.g. battery) |
| B3-T6 | Bare `ayúdame a elegir` still not forced to a named family via resolver (`resolve` is None) |
| B3-T7 | B2 regressions: `cambiar frame` still frame; Armattan→TBS clear still green |
| Full suite | Green |

---

## 4. Files

| File | Change |
|---|---|
| `src/jarvis/core/catalog_rebind_assist.py` (new) **or** shared helper | resolver |
| `src/jarvis/core/frame_catalog_assist.py` | wrapper for `is_frame_rebind_phrase` |
| `src/jarvis/core/orchestrator.py` | generalized IDLE dispatch |
| `tests/test_idle_catalog_rebind_b3.py` | B3 cases |

---

## 5. Done

Behavior + tests + report `.jes/artifacts/implementation_report_idle_catalog_rebind_b3.md` + suite green.
