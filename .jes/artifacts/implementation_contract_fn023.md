# Implementation Contract — FN-023

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Audit `audit_2026-08-10_engineering_intent_vs_sticky_session.md` §B — next-step help ignores Continuity / Acquisition Target  
**Depends on:** FN-015 (help-define pending), FN-021 (IDLE after arch), FN-022 (closed — Engineering Intent)  
**Does not implement:** Conversation Engine; Step D; Create→BOM; auto-start acquisition without confirmation; FN-022 residual (explore vs plan-first); rewriting Continuity formula  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. No commit/push unless asked.

**Hard constraint — EVERYTHING GENERIC:**  
No battery-only / propeller-only design. Field probe (“ayúdame con el siguiente paso” inventing `battery_capacity_wh` while Continuity pointed at propellers) is **acceptance evidence only**. Help must follow **Continuity / Acquisition Target authority**, whatever the real next gap is.

---

## 1. Intent

When the user asks for **orientation to the next useful engineering step** (with or without “ayúdame”), Jarvis must answer from **project state authority** — Continuity `next_useful_step` (and pending Acquisition Target when one exists) — **0 LLM**.

Field failure:

```text
Continuity / Acquisition Target: propellers / declare propulsion …
User: "ayúdame con el siguiente paso"

Today:
  intent = analyze  (ANALYZE_PATTERNS \bayudame\b wins in strong_action)
  → LLM
  → invents battery_capacity_wh (or other unrelated gap)

Target:
  project_status (or equivalent Continuity surface)
  → message / continuity.next_useful_step matches real pending target
  → 0 LLM
  → does NOT invent a different gap
```

---

## 2. Root cause

In `intent_resolver._resolve_strong_action_intent`:

1. `GUIDANCE_PATTERNS` run first (good) — but they do **not** cover `"ayúdame con el siguiente paso"`.
2. `ANALYZE_PATTERNS` include bare `\bayudame\b` → phrase becomes **`analyze`**.
3. `STATUS_PATTERNS` already include `"siguiente paso"`, but `_looks_like_status_query` only runs **after** strong_action returns `None` — so it never sees this phrase.

FN-015 only covers help-**define** markers (`definir`/`valor`/`poner`) for the **current pending value**.  
FN-014 covers named block/component.  
Neither covers generic **next-step orientation** help.

Authority already exists: `build_project_continuity` → `next_useful_step`, `build_startup_context` → Continuity, `_handle_project_status` → 0 LLM. FN-023 **routes** to that authority — does not invent a second recommender.

---

## 3. Scope

### In scope

| # | Change |
|---|---|
| 1 | Detect generic **next-step help / orientation** phrases (Spanish, normalized) that today fall to `analyze` via bare `ayudame` |
| 2 | Route them to **`project_status`** (preferred — reuses Continuity-backed startup context) **before** ANALYZE wins |
| 3 | Ensure the user-visible reply includes Continuity authority (`situation` / `next_useful_step` / equivalent already shown by status path) — **not** an LLM narrative that names a different gap |
| 4 | Tests with **at least two different real pending targets** (e.g. propellers vs another gap) so the fix is not propeller-shaped |
| Docs | Continuity / IMPLEMENTATION_TASKS short note |

### Out of scope

- Conversation Engine / Step D  
- Create→BOM  
- Auto-opening DEFINE_MISSING / declare session on the help phrase alone (unless existing `project_status` + `pending_define_missing` / Bug54 behaviour already does that for `proactive_question` — do not invent a new auto-start)  
- Changing Continuity situation formula or FN-020 coherence rules  
- Softening FN-015 / FN-014 / FN-005 / FN-011  
- Exploring / goal_plan (FN-022) — next-step help is orientation, not engineering-intent mutation  

---

## 4. Design

### 4.1 Preferred routing (thin)

**Extend `GUIDANCE_PATTERNS`** (already checked **before** `ANALYZE_PATTERNS`) so next-step orientation resolves to `project_status`.

Examples of the **kind** of patterns to add (implementer completes a coherent minimal set; not battery-specific):

```text
ayudame con el siguiente paso
ayudame con el siguiente
cual es el siguiente paso
que es el siguiente paso
ayudame a seguir
como sigo / por donde sigo   # if not already covered by STATUS after strong_action — prefer GUIDANCE when "ayudame" is present
```

Also cover close variants with/without articles. Prefer word-boundary regexes consistent with existing GUIDANCE style.

**Alternative (acceptable if cleaner):** small helper `is_next_step_help_phrase(user_input) -> bool` in `acquisition_target.py` or beside Continuity, called from orchestrator IDLE / before analyze — but **prefer intent_resolver GUIDANCE** so all entry points (`resolve_intent`) agree and CLI/tests stay coherent.

### 4.2 Authority of the answer

Once routed to `project_status`:

- Reuse `_handle_project_status` / `build_startup_context` — **do not** build a parallel “help engine”.
- Acceptance: `startup_context.continuity["next_useful_step"]` (or the rendered Continuity surface) must be **consistent with** the real pending Acquisition Target / architecture gap for that fixture — not invent energy when propulsion is pending.
- CLI presentation may already print Continuity; if `project_status` returns context without forcing Continuity into `message`, that is OK **only if** existing consumers already surface Continuity from `startup_context` the same way as `"siguiente paso"` alone. Match behaviour of bare `"siguiente paso"` / `"que falta"` — do not invent a new reply format unless the status path currently omits Continuity for this route (then add the minimal existing Continuity attachment, not a new subsystem).

### 4.3 Precedence

```text
ESCAPE / sessions …
FN-005 help-choose (motor catalog)
FN-011/013/014 named declare / acquisition mention
FN-015 help-define pending
*** FN-023 next-step help → project_status ***
FN-022 engineering intention (iterate/unknown)
analyze / LLM
```

Must **not** steal:

| Phrase class | Owner |
|---|---|
| `ayúdame a declarar propulsión` | FN-011/014 |
| `ayúdame a definir` / `ayúdame a definir el valor` | FN-015 |
| `ayúdame a elegir` / motor help | FN-005 |
| `analiza el margen` / real analyze verbs | analyze |
| `Aumentar el empuje` | FN-022 |
| bare `"siguiente paso"` | already `project_status` — regression |

### 4.4 Mid-DEFINE_MISSING

If the user says next-step help **inside** DEFINE_MISSING:

- Prefer: answer with Continuity / current pending target help **without** calling LLM — either via existing project_status soft-interrupt (already used for `project_status` in DEFINE_MISSING) or FN-015-style pending help if Continuity points at the same pending key.
- Must not invent a different component than `pending_param_definitions[0]` / Continuity next.
- Keep session mode DEFINE_MISSING unless existing status soft-interrupt behaviour already preserves it (match current `project_status` inside wizard).

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | IDLE/project with Continuity next = propellers / propulsion gap; `"ayúdame con el siguiente paso"` | `project_status` (or documented Continuity surface); **0 LLM**; next step / context mentions that real gap — **not** invented `battery_capacity_wh` as the authority |
| B | Same phrase with a **different** pending gap (e.g. battery/energy or structure — whatever fixture makes Continuity point elsewhere) | Continuity/next matches **that** gap — proves generic |
| C | bare `"siguiente paso"` | Still `project_status` — regression |
| D | `"ayúdame a definir"` / FN-015 path with pending propellers | Still FN-015 help for propellers — not broken |
| E | `"ayúdame a declarar propulsión"` | Still FN-011/014 declare path — not stolen into bare status |
| F | `"analiza el margen de seguridad"` (or clear analyze) | Still analyze — not stolen |
| G | `"Aumentar el empuje"` IDLE closed arch | Still FN-022 `engineering_intent` — not stolen |
| H | Mid DEFINE_MISSING + next-step help | No LLM inventing other gap; session preserved per §4.4 |

---

## 6. Tests (required)

File: `tests/test_fn023_next_step_help.py`

Minimum:

1. `test_ayudame_siguiente_paso_routes_project_status_not_analyze` (probe; Continuity/next matches propellers or propulsion fixture)  
2. `test_siguiente_paso_help_follows_different_pending_gap` (second fixture — generic)  
3. `test_bare_siguiente_paso_still_project_status`  
4. `test_fn015_help_define_not_stolen`  
5. `test_declare_block_help_not_stolen`  
6. `test_real_analyze_not_stolen`  
7. `test_fn022_engineering_intent_not_stolen`  
8. `test_define_missing_next_step_help_no_llm_wrong_gap`  

`_RefuseLLM` on Continuity/status paths. Full suite. Baseline: **1550**.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/intent_resolver.py` | GUIDANCE (or STATUS-before-analyze) patterns for next-step help |
| `src/jarvis/core/acquisition_target.py` | Optional `is_next_step_help_phrase` if shared helper is cleaner than regex-only |
| `src/jarvis/core/orchestrator.py` | Only if soft-interrupt / message attachment needed for Continuity visibility — prefer no parallel handler |
| `tests/test_fn023_next_step_help.py` | **Create** |
| docs Continuity / IMPLEMENTATION_TASKS | Note |

**Forbidden:** new Conversation Engine; new recommender parallel to Continuity; battery-only / propeller-only branches; Create→BOM; Continuity formula rewrite; auto-DSE.

---

## 8. Implementation report (Claude)

1. Diff per file  
2. Exact phrases/patterns added  
3. Proof: same phrase, two different pending gaps → two different Continuity nexts  
4. Proof: no LLM on probe; analyze/declare/FN-015/FN-022 not stolen  
5. Test commands + suite count  
6. Confirmation: generic only; Continuity is authority; no Conversation Engine  
7. Residuals  

No commit/push unless asked.

---

## 9. Review checklist (Cursor)

- [ ] Routes to Continuity/`project_status`, not analyze  
- [ ] Two-gap proof (generic)  
- [ ] 0 LLM on next-step help  
- [ ] FN-005/011/014/015/022 not stolen  
- [ ] No invented parallel authority  
- [ ] Suite green  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Queue after PASS

1. Create→BOM handoff  
2. Optional: plan-first vs auto-DSE consistency (FN-022 residual)  
3. Step D — blocked  
