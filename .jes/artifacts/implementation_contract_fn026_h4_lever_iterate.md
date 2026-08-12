# Implementation Contract — FN-026 (H4)

**Project:** Jarvis  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** DONE — PASS WITH NOTES (review `.jes/artifacts/implementation_review_fn026.md`; awaiting commit + tag `checkpoint-fn026-h4`)  

**Type:** Product behavior — third **Handoff Context consumer** (Plan lever → Iterate preseed).  

**Closes / repairs:** **C-043** 🔴 → 🟢 · **H4**  

**Design authority (mandatory read):**  
- [`docs/system_map/HANDOFF_CONTEXT_DESIGN.md`](../../docs/system_map/HANDOFF_CONTEXT_DESIGN.md) — Hybrid Operation-Scoped Context  
- [`docs/system_map/MISMATCHES.md`](../../docs/system_map/MISMATCHES.md) — H4 membership rule  
- FN-024 (C-105 populates `levers` / `iterate_capability`; C-106 consumes DSE only)  

**Checkpoint base:** tag `checkpoint-fn025-h3` · commits `ff550f3` (FN-024) + `1442d44` (FN-025)  

**Explicitly deferred:** H5 / C-081 · Create→BOM · dual-dispatch · Conversation Engine / Step D  

**Workflow:** Claude implements + tests + updates System Map → Engineer forwards → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Intent

When a Goal Plan has established an active `HandoffContext`, and the user names a **lever that belongs to that plan**, Iterate must **preseed `variable`** so the wizard does not re-ask “¿Qué quieres modificar?”.

```text
aumentar empuje / ayudame a mejorar la estabilidad
        ↓
Goal Plan + HandoffContext
  goal_key, levers[], iterate_capability=active
        ↓
"incrementa safety_factor" → (confirm if needed)
        ↓
ITERATE with variable=safety_factor preseeded
        ↓
ask operation/value as needed — NOT "¿qué modificar?"
```

Today (C-043): lever text stays in free-text `objective`; `iteration_draft.variable is None`; `missing_slots == ["variable"]`.

**This is a session/continuation fix**, not an intent-routing fix (H3 already closed entry).

---

## 1. Non-negotiable membership rule (Engineer)

> **Only preseed a variable if it belongs to the `levers` of the currently active `HandoffContext`.**

Forbidden:

```text
if "safety_factor" in text:
    iterate("safety_factor")   # invents capability outside the plan
```

Allowed:

```text
active handoff_context
  && project_id matches
  && iterate_capability == "active"
  && candidate_variable ∈ expanded(context.levers)
  && candidate is a valid iterate variable
  → preseed variable
```

Without a bindable context (none / wrong project / iterate capability consumed / no membership) → **keep today's honest wizard** (“¿Qué quieres modificar?”). That is not a regression.

---

## 2. Lever matching (compound strings)

`HandoffContext.levers` stores strategy lever strings from `GOAL_STRATEGIES`, often compound:

```text
"safety_factor"                         → exact
"per_motor_max_thrust_n / motors"       → tokens: per_motor_max_thrust_n, motors
"structure_mass_factor / material"      → tokens …
```

**Membership expansion (deterministic):**

1. Exact match of full lever string (normalized), **or**  
2. Match of a slash-separated token (strip whitespace) to a candidate variable canonical name.

Normalization must reuse existing iterate alias / `_is_valid_variable` / `normalize_alias` machinery where possible — do not invent a parallel vocabulary.

If the user names something **not** in the expanded lever set → do not preseed (even if it is a valid iterate variable globally).

---

## 3. Architectural constraints

| Rule | Why |
|---|---|
| Read existing `HandoffContext` only | No second store; same C-105 writer |
| `project_id` guard at read (like C-106) | FN-024 lesson — prove, don’t assume clear-on-switch |
| Do not wipe whole context on preseed | Capability/lever scoped |
| Prefer mark lever used/reconciled after **successful mutation apply** (not on wizard open) | Decision log “after mutation → RECONCILED” |
| Leave `dse_capability` alone | H1 consumer independent |
| No LLM choosing the variable | AUTHORITY |
| No Create→BOM / H5 / dual-dispatch | Scope |

---

## 4. Preferred implementation shape

Place the bind where Iterate is about to open / first fill slots from user text — smallest path that closes the CLI failure:

| Option | Where | Notes |
|---|---|---|
| **A (preferred)** | When `IterateInteractiveSession` starts / seeds from user text (or orchestrator handoff into ITERATE), if `variable` empty: try resolve candidate from input against active context levers → seed `variable` (+ operation if already clear) | Keeps membership next to wizard |
| **B** | Orchestrator before `IterateInteractiveSession.start`, inject preseed dict similar to `_semantic_preseed` | OK if clearer; must still call shared membership helper |

**Required shared helper** (pure, testable): e.g. `match_plan_lever(user_input, handoff_context) -> str | None` living near `goal_planner` or a tiny handoff helper — **not** inside LLM adapter.

After a successful iterate apply that mutated the preseeded lever: mark that lever consumed/reconciled on the context (or drop it from active levers). Do **not** invalidate whole context solely because one lever was applied (Decision log). If all levers reconciled and DSE already consumed, invalidating/clearing context is allowed if documented — optional polish, not required to flip C-043.

---

## 5. Scope

### In scope

| # | Work |
|---|---|
| 1 | Preseed iterate `variable` from active plan levers (membership-gated) |
| 2 | `project_id` + `iterate_capability` guards |
| 3 | Compound lever token matching |
| 4 | Honest no-op when no membership / no context |
| 5 | Tests + System Map (C-043 → 🟢; rollup **0 RED**) |
| 6 | Cosmetic map fixes if still stale (C-025 To column already fixed at FN-025 commit) |

### Out of scope

| Forbidden |
|---|
| H5 / C-081 Continuity risk thread |
| Create→BOM |
| Preseding variables from global keyword lists without plan membership |
| Changing FN-024/025 routing |
| Dual-dispatch refactor |

---

## 6. Tests (required)

| # | Case |
|---|---|
| T1 | Plan (`aumentar empuje` or help+goal) → `"incrementa safety_factor"` → confirm → `variable == "safety_factor"` (or canonical), **not** stuck on missing variable |
| T2 | Same without prior plan/context → still asks “¿Qué quieres modificar?” (honest) |
| T3 | Plan for estabilidad → user names a valid iterate var **not** in that plan’s levers → **no** preseed |
| T4 | Cross-project: stale context `project_id` ≠ active → no preseed |
| T5 | After DSE consumed (FN-024), levers still work for iterate preseed (`iterate_capability` still active) |
| T6 | FN-025 help+goal → plan → lever preseed still works |
| T7 | Compound lever: if plan has `"per_motor_max_thrust_n / motors"`, naming `per_motor_max_thrust_n` (when valid iterate var) preseeds; naming unrelated token does not |
| T8 | Regressions: FN-022/023/024/025 smoke (or subset) green |

---

## 7. System Map updates (required)

| Artifact | Change |
|---|---|
| `CONNECTIONS.md` | C-043 → 🟢; evidence; note H4 consumer |
| Rollup | **59 · 58🟢 · 0🔴 · 1🟡** (C-081) |
| `MISMATCHES.md` | H4 → IMPLEMENTED |
| `FLOWS.md` FLOW-004 | broken sub-case → working |
| `DIAGRAMS.md` / canvas | C-043 green; Next → H5/C-081 / Create→BOM paused |
| `04_engineering` / `05_iteration` maps | pointers |
| Optional new C-xxx | Only if a distinct edge is warranted (e.g. C-107 context→iterate preseed); else document under C-043 |

---

## 8. Blast-radius table (report must fill)

| Path | Expected |
|---|---|
| Plan → named plan lever → iterate | preseed variable |
| No context / wrong project | no preseed |
| Var valid globally but ∉ plan levers | no preseed |
| DSE-consumed context | iterate preseed still works |
| Help+goal plan (FN-025) | works |
| Continuity / bare help | untouched |
| Explore bind (FN-024) | untouched |

---

## 9. Acceptance criteria (Cursor review)

PASS only if:

1. CLI Failure C closed: plan lever → iterate does not re-ask variable when membership holds.  
2. Membership rule enforced (negative tests T2/T3/T4).  
3. Reuses `HandoffContext`; no sticky `last_engineering_goal`.  
4. C-043 🟢; registry **0 RED**; C-081 still 🟡.  
5. FN-024/025 regressions green.  
6. No H5 / Create→BOM.

FAIL if:

- Global “if keyword in text → variable” without plan membership  
- Whole context wiped on preseed  
- C-081 marked fixed without Continuity data contract  
- Map claims 0 YELLOW by lying about C-081  

---

## 10. Implementation Report template (Claude)

```markdown
# Implementation Report — FN-026 (H4)

## Summary
## Option A/B + membership helper location
## Behavior changed
## Files changed
## Connections (C-043 [+ optional C-107])
## Tests run
## Blast-radius table
## Explicitly deferred (H5, Create→BOM)
## Risks
```

---

## 11. Prompt to paste into Claude Code

> Execute Implementation Contract **FN-026** (`.jes/artifacts/implementation_contract_fn026_h4_lever_iterate.md`).
>
> Read `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` and C-043 in `CONNECTIONS.md` first.
>
> Close C-043 (H4): after a Goal Plan has created `HandoffContext`, when the user names a lever that **belongs to `handoff_context.levers`** (exact or slash-token match), preseed Iterate’s `variable` so the wizard does not ask “¿Qué quieres modificar?”. Guard with `project_id` and `iterate_capability == "active"`. Never preseed from global keywords alone. Reuse existing HandoffContext (C-105) — no second store. Do **not** implement H5/C-081 or Create→BOM.
>
> Add tests T1–T8. Update System Map to **0 RED** (C-081 remains YELLOW). No commit/push unless asked. Return Implementation Report for Cursor review.

---

## 12. After FN-026 (Engineer)

```text
FN-026 PASS
  → commit + tag checkpoint-fn026-h4  (H1–H4 closed; 0 RED)
  → sit with System Map
  → then C-081 / H5 design OR Create→BOM — Engineer chooses
```
