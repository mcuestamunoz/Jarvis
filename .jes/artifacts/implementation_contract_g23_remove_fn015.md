# Implementation Contract — G23 Eliminate FN-015 ("ayúdame a definir") Feature

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** Product cleanup — **total removal** of FN-015 as a user-facing acquisition feature. No dead code. No “hidden” path that still behaves like the old feature.

**Evidence:** Engineer CLI + Cursor evaluation 2026-08-20 — Brief CTA advertises “repetir esta guía” while the guide is already on screen; in-wizard path re-shows Brief (zero value); IDLE bridge duplicates Continuity / FN-011/014 / FN-023; catalog branch under `definir` competes with G21 `elegir`.

**Prerequisite:** G21/G22 closed (or same working tree after G21/G22 review PASS).  
**Blocks:** Impl C investigation may proceed after G21/G22 + this cleanup (Engineer preference: finish G23 before Impl C IC).

**Workflow:** Claude implements + tests + report + **documentation purge** → Engineer → Cursor review → commit/tag if Engineer asks.

---

## 0. Engineer decision (locked)

**Eliminación total de la feature FN-015.** Not “hide the bullet”. Not “leave an undocumented bridge”.

| Keep? | What | Why |
|---|---|---|
| **NO** | Brief bullet `decir 'ayúdame a definir' para repetir esta guía` | Active UX noise |
| **NO** | `_try_help_define_pending_idle` | Parallel acquisition entry; Continuity/FN-023 already cover orientation |
| **NO** | `_help_current_pending_acquisition` as product help (Brief replay / catalog offer) | Zero value / wrong verb for catalog |
| **NO** | FN-015 as a living Continuity/Acquisition verb in system map & docs | Documents a feature that must not exist |
| **YES (hygiene only)** | Inside `DEFINE_MISSING` only: matching confusion phrases must **not** reach `analyze`/LLM | Original bug was real; hygiene ≠ feature |
| **YES (IDLE collapse)** | At IDLE, those phrases must **not** invent a wizard — route via existing **GUIDANCE → `project_status`** (same family as FN-023) | One orientation authority |

Hard rules:

- Zero weakened tests solely to pass — rewrite/delete FN-015 tests to match new behavior.
- Do **not** reintroduce catalog under `definir` (catalog = `ayúdame a elegir` / G21).
- Do **not** start Impl C in this IC.
- Historical `.jes/artifacts/*fn015*` contracts/cycle-close: **mark SUPERSEDED by G23**, do not silently delete audit trail.

---

## 1. Design decisions (locked)

### ★1 Product: FN-015 feature deleted

No CTA, no Continuity copy, no “pending-help” product path, no IDLE auto-open of DEFINE_MISSING from bare `ayúdame a definir`.

### ★2 DEFINE_MISSING hygiene (minimal, not a feature)

While mode is `DEFINE_MISSING_PARAMETERS`, phrases that previously matched `is_help_define_pending_phrase` must:

1. **Never** call the LLM.
2. **Never** re-build / re-show `build_acquisition_brief` as “help”.
3. **Never** call `offer_catalog_help` / open catalog.
4. Return a **short** re-ask of the current pending item only:
   - Component key → `COMPONENT_PROMPTS[key]` or existing `_component_prompt_for_first_missing` / `question` field — **one line**, no Brief wrapper.
   - Numeric pending → existing `_question_for_param` for `pending[0]` only.
5. Do **not** mutate `collected_params` / restart session.

Rename for honesty (required):

- Delete public framing `is_help_define_pending_phrase` / FN-015 naming from live code comments and docs.
- Replace with a narrowly named helper, e.g. `is_define_missing_confusion_phrase` (or fold into an existing refuse helper), documented as **anti-LLM confusion gate**, not acquisition help.

Exact catch-phrases / markers may stay the same set (`ayúdame a definir`, `ayúdame a definir el valor`, `como lo defino`, `no se que poner`, `ayudame`+`definir|valor|poner`) — behavior changes; product name dies.

### ★3 IDLE: collapse into GUIDANCE / project_status (FN-023 family)

**Delete** `_try_help_define_pending_idle` entirely.

At IDLE, bare confusion / old help-define phrases must resolve to **`project_status`** (Continuity), **0 LLM**, **without** opening DEFINE_MISSING.

Preferred mechanism (implementer picks the smallest one that works):

- Add the bare phrases to `IntentResolver.GUIDANCE_PATTERNS` (or STATUS if already equivalent), **before** ANALYZE’s `\bayudame\b`, **without** stealing FN-005 `ayúdame a elegir` / named `definir propulsión` (FN-011/014).

Must **not**:

- Call `_set_pending_next_block` + `start_define_missing_params` from this phrase.
- Invent a second “next step” subsystem.

### ★4 Brief copy

In `acquisition_brief.build_acquisition_brief`, **delete** the line:

```text
  • decir 'ayúdame a definir' para repetir esta guía
```

for **all** keys (motors included). Keep G21 motors bullet for `ayúdame a elegir` only.

### ★5 Documentation purge (mandatory deliverable)

Living docs must stop describing FN-015 / C-032 as active behavior.

#### Delete or rewrite (living)

| Doc | Action |
|---|---|
| `docs/PROJECT_CONTINUITY.md` — Field note FN-015 section | Rewrite as **REMOVED (G23)** one short block: what was deleted + pointer to this IC; remove “closed feature” narrative that still teaches the verb |
| `docs/IMPLEMENTATION_TASKS.md` — FN-015 COMPLETADO section | Mark **SUPERSEDED / REMOVED by G23**; do not leave checklist as current capability |
| `docs/system_map/CONNECTIONS.md` — **C-032** | Status **REMOVED** (G23); symbols listed as deleted; do not leave 🟢 CONNECTED |
| `docs/system_map/01_runtime/RUNTIME_MAP.md` | Remove FN-015 / C-032 from active routing tables |
| `docs/system_map/03_acquisition/ACQUISITION_MAP.md` | Remove `is_help_define_pending_phrase` from live symbol list; note anti-LLM gate rename if kept |
| `docs/system_map/DIAGRAMS.md` | Remove/strike C-032 active edge |
| Any Continuity copy / comments that advertise `ayúdame a definir` as a user verb | Purge |

#### Historical artifacts (audit, not silent delete)

| Artifact | Action |
|---|---|
| `.jes/artifacts/implementation_contract_fn015.md` | Banner at top: **SUPERSEDED by G23 — feature removed** |
| `.jes/artifacts/cycle_close_fn015.md` | Same SUPERSEDED banner |
| Cross-refs in other contracts that say “FN-015 territory” as if live | Update to “removed G23; hygiene gate only” where they would mislead implementers |

#### Register this cut

- New: `.jes/artifacts/implementation_contract_g23_remove_fn015.md` (this file)
- Report: `.jes/artifacts/implementation_report_g23_remove_fn015.md`
- `docs/IMPLEMENTATION_TASKS.md` priority / REGISTRADOS: G23 IC READY → then CLOSED when done

---

## 2. Code deletion / change map

| Location | Change |
|---|---|
| `acquisition_brief.py` | Remove help-define bullet entirely |
| `orchestrator.py` | Delete `_try_help_define_pending_idle` + IDLE call site (~817–825) |
| `orchestrator.py` | Replace `_help_current_pending_acquisition` product help with ★2 short re-ask **or** delete method and inline minimal return |
| `acquisition_target.py` | Rename/repurpose detector; strip FN-015 product docs from module docstring |
| `intent_resolver.py` | IDLE collapse into GUIDANCE (★3); ensure `elegir` / named declare not stolen |
| `tests/test_fn015_pending_help.py` | **Delete file** or replace with `tests/test_g23_fn015_removed.py` asserting new behaviors (prefer new G23 file + delete old FN-015 suite) |
| Regression files (`test_fn018`, `test_fn019`, `test_fn016`, `test_fn017`, `test_fn023`, …) | Update any assertion that expects Brief-replay / IDLE-open-wizard / catalog-via-definir |

---

## 3. Tests (required)

New file `tests/test_g23_fn015_removed.py` (recommended):

1. `test_g23_brief_does_not_advertise_help_define` — motors + battery Brief messages contain no `ayúdame a definir` / `repetir esta guía`.
2. `test_g23_define_missing_confusion_no_llm_short_reask` — open component wizard (propellers pending) → `ayúdame a definir` → 0 LLM, interactive, message/question is **short** (no full Brief “Vamos a definir…” / “Puedes:” block), pending unchanged.
3. `test_g23_define_missing_confusion_does_not_open_catalog` — pending `per_motor_max_thrust_n` → `ayúdame a definir` → **no** `motor_suggestions` / no catalog list; (catalog remains `ayúdame a elegir`).
4. `test_g23_idle_help_define_is_project_status_not_wizard` — IDLE + pending gap → `ayúdame a definir` → `action == project_status` (or Continuity-bearing status), session **not** forced into `DEFINE_MISSING` solely by this phrase; 0 LLM.
5. `test_g23_help_choose_still_works` — regression: `ayúdame a elegir` still catalog (G21/FN-005 path).
6. `test_g23_real_analyze_still_may_use_llm` — `analiza el margen de seguridad` not claimed as confusion gate.

Delete obsolete FN-015 tests that assert Brief-help / IDLE acquisition-open / catalog-via-definir.

Full suite green.

---

## 4. Acceptance criteria

1. No Brief advertises `ayúdame a definir`.
2. No `_try_help_define_pending_idle` in tree.
3. DEFINE_MISSING + old phrases → 0 LLM, short re-ask, no Brief loop, no catalog.
4. IDLE + old phrases → Continuity/`project_status`, no auto wizard open from this phrase alone.
5. `ayúdame a elegir` unchanged (G21).
6. Living system map: C-032 REMOVED; RUNTIME/ACQUISITION maps cleaned.
7. Living Continuity/TASKS docs: FN-015 marked removed/superseded, not taught as current.
8. Historical FN-015 artifacts bannered SUPERSEDED.
9. Full suite green; no weakened tests.

---

## 5. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | Total feature removal | Engineer: no dead / fake product surface |
| ★2 | Keep anti-LLM short re-ask in DEFINE_MISSING only | Original bug real; must not recreate LLM leak |
| ★3 | IDLE → GUIDANCE/project_status, not wizard | One orientation authority (FN-023 family) |
| ★4 | Purge living docs + supersede historical | Clean software + honest audit trail |
| ★5 | Catalog never under `definir` | G21 owns `elegir` |

---

## 6. Review checklist (Cursor — mandatory)

1. Brief bullet gone for all keys.
2. IDLE FN-015 bridge deleted; no stealth reimplementation.
3. DEFINE_MISSING path: no Brief replay, no catalog via definir.
4. Detector renamed / FN-015 product naming gone from live code comments.
5. C-032 and living maps updated; TASKS/CONTINUITY purged or marked REMOVED.
6. Historical artifacts SUPERSEDED, not quietly deleted without banner.
7. G21 choose path green; full suite green.

---

## 7. Implementation report (Claude deliverable)

`.jes/artifacts/implementation_report_g23_remove_fn015.md` with:

- Files deleted vs changed
- Doc purge checklist (each living doc touched)
- Test file rename/deletion summary
- Suite count
- Deviations (must be empty or flagged)

---

**End of contract.**
