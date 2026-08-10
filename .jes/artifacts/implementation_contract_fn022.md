# Implementation Contract — FN-022

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Audit `audit_2026-08-10_engineering_intent_vs_sticky_session.md` — Engineering Intent after FN-021  
**Depends on:** FN-021 (closed — IDLE after arch complete)  
**Does not implement:** Conversation Engine; Step D Guided Engineering subsystem; “ayúdame con el siguiente paso” → Continuity (separate); Create→BOM; auto-apply DSE without user confirm  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. No commit/push unless asked.

**Hard constraint — EVERYTHING GENERIC:**  
No thrust-only design. No one-off `if "empuje"`. Extend **catalogs and one IDLE gate** that work for **all** existing `goal_planner` / DSE goals. Field phrases (e.g. “Aumentar el empuje”) are **acceptance probes only**.

---

## 1. Intent

After a closed architecture (IDLE), the user often states an **engineering intention**, not a component to declare and not yet a numeric mutation:

```text
Aumentar el empuje
Reducir el peso
Mejorar el margen / la estabilidad
Mejorar la autonomía
```

**Today (post FN-021):** many of these resolve to `iterate` (verb `aumentar`/`subir`) and open the iterate wizard — or miss `detect_goal` entirely (`detect_goal("Aumentar el empuje")` → `None`). The desired first response is the **deterministic strategy plan** already in `goal_planner.format_goal_plan` (levers from `GOAL_STRATEGIES`), optionally inviting existing DSE (`explore_design_space`) — **0 LLM** for that first turn.

```text
User: <engineering intention>
→ detect_goal → goal_key
→ format_goal_plan(goal_key, sim_context)
→ short CTA: how to explore (existing DSE phrases) or name a lever
→ does NOT open iterate wizard on that turn
→ does NOT invent battery/propellers acquisition
```

---

## 2. Root cause

1. `ITERATE_PATTERNS` claim `aumentar`/`subir` before any goal layer.  
2. `EXPLORE_PATTERNS` intentionally **exclude** `aumenta`/`sube` (comment in intent_resolver) — so intention ≠ explore.  
3. `detect_goal` keyword tables omit common intention words (e.g. empuje/thrust) even though strategies/grids already know the levers.  
4. `format_goal_plan` is only prepended inside `_handle_analyze` (LLM path) — not offered as a deterministic IDLE first response.

Pieces already exist: `GOAL_STRATEGIES`, `_GOAL_KEYWORDS`, `DesignExplorer` / `EXPLORATION_GRIDS`, `_handle_explore`. FN-022 **wires and completes detection** — does not invent a new engine.

---

## 3. Scope

### In scope

| # | Change |
|---|---|
| 1 | Extend `_GOAL_KEYWORDS` **symmetrically** for all existing goals (`aumentar_payload`, `mejorar_autonomia`, `reducir_masa`, `mejorar_estabilidad`) so natural intention phrases detect a goal. Include thrust/empuje language under the goal whose strategies already own thrust levers (`mejorar_estabilidad` and/or `aumentar_payload` — pick one primary mapping, document it; do not create a fifth ad-hoc goal unless catalogs already need it) |
| 2 | IDLE gate **before** iterate: if `detect_goal(user_input)` returns a key **and** the input is not a clear parametric set/mutate-with-value (see §4.2), return deterministic `format_goal_plan` (+ CTA) — **0 LLM** |
| 3 | CTA must point at **existing** explore vocabulary / apply flow (e.g. optimiza/explora + goal domain, or “explora opciones para …”) — do not invent a new Dialogue Engine; reuse `_handle_explore` when user later matches `explore_design_space` |
| 4 | Pass `sim_context` from last simulation into `format_goal_plan` when available (same as analyze path) |
| 5 | Tests for **multiple goals**, not only empuje |
| Docs | Continuity / IMPLEMENTATION_TASKS short note |

### Out of scope

- Conversation Engine / Step D  
- Auto-running DSE on the first intention turn (plan first; explore on explicit explore intent — unless the phrase **already** matches `EXPLORE_PATTERNS`, keep today’s explore path)  
- Changing physics / catalog matching  
- “ayúdame con el siguiente paso” → Continuity (follow-up FN)  
- Create→BOM  
- Rewriting Continuity situation formula  
- Weakening FN-021 session clear  

---

## 4. Design

### 4.1 Keyword extension (generic)

In `goal_planner._GOAL_KEYWORDS`, add missing natural phrases for **each** goal. Examples of the **kind** of addition (implementer completes a coherent set; not thrust-only):

| Goal | Kind of keywords to add (non-exhaustive) |
|---|---|
| `mejorar_estabilidad` | margen, risky, más empuje, aumentar empuje, thrust, relación empuje/peso, … |
| `aumentar_payload` | (already strong; fill gaps if any) |
| `reducir_masa` | (already strong; fill gaps if any) |
| `mejorar_autonomia` | (already strong; avoid stealing pure “batería” acquisition phrases — see §4.3) |

**Conflict rule:** if a phrase is primarily acquisition (“declarar batería”, “definir hélices”), acquisition / FN-014 gates win — they run earlier. Goal gate only in IDLE after those return None.

Document primary mapping for “aumentar empuje” / “más thrust” → which `goal_key` (recommend `mejorar_estabilidad` because strategies lead with thrust/margin; acceptable alternative: `aumentar_payload` when margin-aware prioritization already pushes thrust first — **choose one**, test it).

### 4.2 IDLE gate: engineering intention vs iterate mutation

Suggested helper (location: `goal_planner.py` or thin orchestrator method):

```text
is_engineering_intention(user_input) -> goal_key | None
  key = detect_goal(user_input)
  if key is None: return None
  if looks_like_numeric_mutate(user_input): return None  # e.g. bare number, "a 15 N", "en 2 kg"
  return key
```

`looks_like_numeric_mutate`: keep **conservative** — if user supplies a clear target value for a variable, leave iterate alone. Intention-only phrases (no value) take the goal-plan path.

Wire in `_handle_user_text_inner` **IDLE path**, after acquisition/FN-014/015/021-safe routing, **before** the branch that opens iterate for `intent == "iterate"` / local iterate action.

Response shape (deterministic):

```text
{
  status: "ok" | "interactive",
  action: "goal_plan" | "engineering_intent",  # pick one name; document it
  goal_key: str,
  message: format_goal_plan(...) + "\n\n" + CTA,
}
```

CTA example (generic, not thrust-specific):  
“Puedes explorar configuraciones (p. ej. ‘optimiza para estabilidad’ / ‘explora opciones’) o indicar un cambio concreto de una palanca.”

### 4.3 Precedence

```text
ESCAPE / nav / sessions …
FN-014 acquisition mention
FN-015 help-define
… other existing IDLE acquisition …
*** FN-022 engineering intention → goal_plan ***
explore_design_space (unchanged if already matched)
iterate (only if not claimed by FN-022)
analyze / LLM
```

Do not steal: simulate, calculate, project_status, declare-block, component intercept.

### 4.4 DSE

- First intention turn: **plan only** (unless intent is already `explore_design_space`).  
- Second turn: existing explore/apply paths unchanged.  
- Optional thin bonus (only if cheap): CTA includes the canonical explore phrase for that `goal_key` — still generic template over `goal_key`, not hard-coded empuje copy.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | IDLE, arch complete (or any IDLE with project), `"Aumentar el empuje"` (probe) | Deterministic goal plan; **not** iterate wizard; **not** component_description; **0 LLM** |
| B | IDLE, `"Reducir el peso"` / `"Reducir la masa"` | Goal plan for `reducir_masa` (or explore if already EXPLORE — must not regress); not random acquisition |
| C | IDLE, `"Mejorar la autonomía"` / similar | Goal plan for `mejorar_autonomia` |
| D | IDLE, `"Mejorar el margen"` / `"mejorar estabilidad"` | Goal plan or existing explore path — coherent, 0 LLM on plan path |
| E | IDLE, clear iterate mutation with value (e.g. set thrust/payload to a number — use a phrase that today correctly opens iterate) | Still iterate — FN-022 must not steal |
| F | `"optimiza para estabilidad"` (existing explore) | Still `explore_design_space` / DSE — regression |
| G | Mid DEFINE_MISSING acquisition | FN-022 does not fire (session not IDLE / acquisition wins) |
| H | FN-021: after last arch gap, session IDLE | Still true |
| I | No Conversation Engine; no auto-apply exploration | Confirmed |

---

## 6. Tests (required)

File: `tests/test_fn022_engineering_intent.py`

Minimum:

1. `test_aumentar_empuje_shows_goal_plan_not_iterate` (probe)  
2. `test_reducir_masa_shows_goal_plan`  
3. `test_mejorar_autonomia_shows_goal_plan`  
4. `test_mejorar_margen_or_estabilidad_goal_or_explore`  
5. `test_numeric_iterate_not_stolen`  
6. `test_existing_explore_phrase_still_dse`  
7. `test_define_missing_session_not_intercepted_by_fn022`  

`_RefuseLLM` on plan-path tests. Full suite. Baseline: **1533**.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/goal_planner.py` | Keywords + optional `is_engineering_intention` helper |
| `src/jarvis/core/orchestrator.py` | IDLE gate before iterate; wire plan response |
| `src/jarvis/core/intent_resolver.py` | **Only if** unavoidable for precedence — prefer orchestrator gate over widening ITERATE; document any change |
| `tests/test_fn022_engineering_intent.py` | **Create** |
| `tests/test_goal_planner.py` | Update keyword coverage |
| docs Continuity / IMPLEMENTATION_TASKS | Note |

**Forbidden:** new Conversation Engine; DSE rewrite; LLM-authored strategy lists; thrust-only modules; next-step-help Continuity FN.

---

## 8. Implementation report (Claude)

1. Diff per file  
2. Keyword additions per goal_key (table)  
3. Primary mapping for empuje/thrust → which goal_key and why  
4. IDLE gate location + `looks_like_numeric_mutate` rule  
5. Proof multi-goal plan paths + iterate not stolen  
6. Test commands + suite count  
7. Confirmation: generic only; no Conversation Engine; no auto DSE on first turn  
8. Residuals  

No commit/push unless asked.

---

## 9. Review checklist (Cursor)

- [ ] Multi-goal coverage (not empuje-only)  
- [ ] Plan deterministic, 0 LLM on intention turn  
- [ ] Iterate-with-value preserved  
- [ ] Explore phrases preserved  
- [ ] Acquisition / DEFINE_MISSING not stolen  
- [ ] FN-021 still green  
- [ ] No Conversation Engine  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Queue after PASS

1. Generic next-step help → Continuity / Acquisition Target  
2. Create→BOM handoff  
3. Optional: first-turn auto-DSE (only with explicit Engineer approval)  
4. Step D — blocked  
