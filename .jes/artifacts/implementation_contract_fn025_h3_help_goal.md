# Implementation Contract — FN-025 (H3)

**Project:** Jarvis  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** SUPERSEDED by delivery — see `.jes/artifacts/implementation_report_fn025.md` and `.jes/artifacts/implementation_review_fn025.md` (**PASS WITH NOTES**).  

**Type:** Product behavior — second **Handoff Context consumer path** (Help + Goal → Engineering Intent).  

**Closes / repairs:** **C-025** 🔴 → 🟢 · **C-044** 🔴 → 🟢 (same root; count once) · **H3**  

**Design authority (mandatory read):**  
- [`docs/system_map/HANDOFF_CONTEXT_DESIGN.md`](../../docs/system_map/HANDOFF_CONTEXT_DESIGN.md) — Hybrid Operation-Scoped Context (§5 CLOSED)  
- [`docs/system_map/AUTHORITY.md`](../../docs/system_map/AUTHORITY.md) — GUIDANCE before ANALYZE; FN-022 gate shape  
- FN-024 delivery (C-105 already creates `HandoffContext` on successful plan)  

**Depends on:** FN-022 · FN-023 · FN-024 (checkpoint `ff550f3`)  

**Explicitly deferred:** FN-026 / H4 / C-043 · H5 / C-081 · Create→BOM · dual-dispatch refactor  

**Workflow:** Claude implements + tests + updates System Map → Engineer forwards report → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Intent

Route **help + named engineering goal** into the deterministic Goal Plan path (same as FN-022), **0 LLM**, and thereby enter / refresh the engineering thread via the existing Handoff Context create path (C-105).

```text
"ayúdame a mejorar la estabilidad"
        ↓
  detect engineering goal (goal_planner)
        ↓
  _handle_engineering_intent(goal_key)
        ↓
  Goal Plan + CREATE/REPLACE HandoffContext   (C-105, already shipped)
        ↓
  0 LLM
```

Today:

```text
"ayúdame a mejorar la estabilidad"
        ↓
  ANALYZE_PATTERNS \bayudame\b wins
        ↓
  intent = analyze
        ↓
  FN-022 gate never sees it (gate only iterate|unknown)
        ↓
  LLM ❌
```

**This is an entry-to-thread fix**, not a continuation-inside-thread fix (that is FN-026 / C-043).

---

## 1. Precedence (Engineer — non-negotiable)

Do **not** “move `ayúdame` above everything.” Semantics **after** the help verb matter:

| User text | Required destination | Existing / this cut |
|---|---|---|
| `"ayúdame con el siguiente paso"` / FN-023 variants | `project_status` / Continuity | **Must remain** (FN-023) |
| `"ayúdame a mejorar la estabilidad"` (help + detectable goal) | Engineering Intent / Goal Plan | **This cut (C-025/C-044)** |
| Bare `"ayúdame"` / `"ayúdame"` without detectable goal and not FN-023 | Continuity / clarification — **not** LLM inventing a goal | **This cut** — prefer `project_status` over `analyze` |

Authority for “which goal”: **`goal_planner.is_engineering_intention` / `detect_goal`** — same deterministic authority as FN-022. LLM must not choose the goal.

---

## 2. Architectural constraints

| Rule | Why |
|---|---|
| Reuse `_handle_engineering_intent` / C-105 | Do **not** invent a second handoff transport |
| Do **not** invent a new sticky field | HandoffContext already exists |
| Do **not** break FN-023 | GUIDANCE next-step patterns must still win |
| Do **not** implement H4 / C-043 | No iterate preseed in this cut |
| Do **not** soften remaining REDs in the map without code | Honesty |
| Prefer smallest change that restores authority | CLAUDE.md — no new subsystem |

---

## 3. Root cause (verified)

1. `ANALYZE_PATTERNS` includes bare `\bayudame\b` (and relatives).  
2. `_resolve_strong_action_intent` checks GUIDANCE then ANALYZE **before** EXPLORE/ITERATE.  
3. FN-023 only carved out *next-step* help into GUIDANCE.  
4. Orchestrator FN-022 gate runs only when `intent in ("iterate", "unknown")`.  
5. Empirically: `resolve_intent("ayudame a mejorar la estabilidad") == "analyze"` while `is_engineering_intention(...)` would return `mejorar_estabilidad` if reached.

C-025 and C-044 are the **same finding** listed under Intent and Engineering — one fix, two registry rows flip.

---

## 4. Preferred implementation shape

**Primary (required):** when the user text would otherwise become `analyze` **solely because of a help-verb pattern**, but `is_engineering_intention(user_input)` returns a `goal_key`, route to `_handle_engineering_intent(goal_key)` instead of `_handle_analyze`.

Two acceptable placements (pick the smaller, clearer one; document choice in report):

| Option | Where | Notes |
|---|---|---|
| **A (preferred)** | Orchestrator: widen FN-022-adjacent gate so `intent == "analyze"` + `is_engineering_intention` → engineering plan | Keeps intent_resolver tables stable; mirrors existing gate |
| **B** | IntentResolver: before returning `analyze` for help verbs, if `is_engineering_intention` → return an intent that already reaches the plan path (e.g. treat as iterate/unknown for gate purposes, or a dedicated value handled once) | Must not break FN-023 GUIDANCE order |

**Forbidden approaches:**

- Blanket “all `ayúdame` → engineering”  
- LLM classify help vs goal  
- New parallel planner / Conversation Engine  
- Matching goal keywords without going through `goal_planner`  
- Implementing iterate lever preseed “while here”

### 4.1 Bare `"ayúdame"` (no goal)

When help-verb matches ANALYZE but `is_engineering_intention` is `None` and FN-023 GUIDANCE did not match:

→ Route to **`project_status` / Continuity** (deterministic clarification of *what is next*), **not** LLM analyze.

Rationale (Engineer): bare help must not invent an engineering target. Continuity already owns “what is next.”

### 4.2 After plan is shown

Successful path **must** go through existing `_handle_engineering_intent` so C-105 creates/replaces `HandoffContext` exactly as FN-024. No duplicate context writer.

Then the chain Engineer cares about becomes available without further work in this cut:

```text
ayúdame a mejorar la estabilidad  → plan + HandoffContext
explora opciones                  → DSE via C-106 (already 🟢)
```

---

## 5. Scope

### In scope

| # | Work |
|---|---|
| 1 | Help + detectable engineering goal → Goal Plan (0 LLM) |
| 2 | Preserve FN-023 next-step → Continuity |
| 3 | Bare help without goal → Continuity / `project_status` (not LLM goal invention) |
| 4 | Ensure C-105 still fires (context create/replace) on that plan path |
| 5 | Regression tests + map update (C-025/C-044 → 🟢; AUTHORITY/FLOWS/MISMATCHES H3) |
| 6 | Blast-radius proof vs FN-022/023/024 |

### Out of scope

| Forbidden |
|---|
| C-043 / H4 iterate preseed |
| C-081 / H5 |
| Create→BOM |
| Changing DSE bind / capability consumption (FN-024) |
| Dual-dispatch refactor |
| Opportunistic hygiene deletes |

---

## 6. Tests (required)

| # | Case |
|---|---|
| T1 | `"ayudame a mejorar la estabilidad"` → `engineering_intent`, `goal_key=mejorar_estabilidad`, 0 LLM (`RefuseLLM`) |
| T2 | Same → `handoff_context` created/replaced (C-105), `dse_capability=active` |
| T3 | `"ayudame con el siguiente paso"` → still `project_status` (FN-023) |
| T4 | Bare `"ayudame"` → `project_status` (or documented Continuity path), **not** analyze/LLM inventing a goal |
| T5 | `"aumentar el empuje"` still → engineering_intent (FN-022 unchanged) |
| T6 | After T1, `"explora opciones"` still → DSE bind (FN-024 regression) |
| T7 | Analyze phrases **without** help+engineering-intention still reach analyze when appropriate (do not swallow all analyze) |
| T8 | At least one other goal_key via help+goal (e.g. autonomía / payload) — generic, not stability-only |

Prefer orchestrator-level tests (FN-022/023/024 style).

---

## 7. System Map updates (required)

| Artifact | Change |
|---|---|
| `CONNECTIONS.md` | C-025 🟢, C-044 🟢; evidence + FN-025 note; rollup 🔴 count −2 (unique finding once) |
| `AUTHORITY.md` | Document help+goal vs FN-023 vs bare help precedence |
| `FLOWS.md` | Note on FLOW-002 / help+goal entry (or short FLOW note) |
| `MISMATCHES.md` | H3 → IMPLEMENTED |
| `DIAGRAMS.md` / canvas | Status flip for C-025/C-044 |
| `02_intent` / `04_engineering` maps | Brief pointer |

No new `C-xxx` required unless Claude introduces a distinct connection worth registering (prefer reuse of C-040/C-105). If a new edge is clearly warranted, append (do not renumber); update canonical count.

---

## 8. Blast-radius table (report must fill)

| Path | Expected effect | Evidence |
|---|---|---|
| help + goal | → engineering_intent + C-105 | |
| FN-023 next-step help | → project_status unchanged | |
| bare ayudame | → Continuity, not LLM goal | |
| FN-022 bare iterate intention | unchanged | |
| FN-024 explora opciones bind | unchanged | |
| explicit analyze without eng. intention | still analyze | |
| H4 / iterate preseed | untouched | |

---

## 9. Acceptance criteria (Cursor review)

PASS only if:

1. Help + named goal → Goal Plan, 0 LLM, context created via existing C-105.  
2. FN-023 still green.  
3. Bare help does not invent a goal via LLM.  
4. FN-022 and FN-024 regressions green.  
5. C-025 and C-044 marked 🟢; H3 marked implemented; no false claim that C-043 is fixed.  
6. No H4/H5/Create→BOM / dual-dispatch.  
7. Report cites Handoff Decision log + chosen Option A/B.

FAIL if:

- FN-023 broken  
- All `ayúdame` forced into engineering  
- New sticky goal string  
- Iterate preseed snuck in  
- Map softens C-043 without code  

---

## 10. Implementation Report template (Claude)

```markdown
# Implementation Report — FN-025 (H3)

## Summary
## Option chosen (A or B) + why
## Behavior changed
## Files changed
## Connections (C-025, C-044)
## Tests run
## Blast-radius table
## Explicitly deferred (H4, H5, Create→BOM)
## Risks
```

---

## 11. Prompt to paste into Claude Code

> Execute Implementation Contract **FN-025** (`.jes/artifacts/implementation_contract_fn025_h3_help_goal.md`).
>
> Read `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` and `AUTHORITY.md` first.
>
> Fix C-025/C-044 (H3): `"ayúdame" + named engineering goal` must reach `_handle_engineering_intent` (Goal Plan + existing C-105 HandoffContext), **0 LLM**. Preserve FN-023 (`"ayúdame con el siguiente paso"` → Continuity). Bare `"ayúdame"` without a detectable goal must go to Continuity/clarification, not LLM inventing a goal. Reuse `goal_planner.is_engineering_intention` — do not invent a second goal detector. Do **not** implement H4/C-043, H5, or Create→BOM.
>
> Add tests T1–T8 (or equivalent). Update System Map. No commit/push unless asked. Return Implementation Report for Cursor review.

---

## 12. After FN-025 (Engineer — not this cut)

```text
FN-025 green
  → replay: help+goal → plan → explora opciones → DSE
  → then FN-026 / H4 / C-043 (lever ∈ HandoffContext.levers only)
  → checkpoint
  → C-081 / H5 design later
  → Create→BOM later
```
