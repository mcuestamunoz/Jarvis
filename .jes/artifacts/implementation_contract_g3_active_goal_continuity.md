# Implementation Contract — G3 (Active Goal Continuity for Explore)

**Project:** Jarvis  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — explore-path precedence (handoff continuity).  

**Closes:** G3 🟡 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)  
**Design authority (mandatory):** [`.jes/artifacts/design_g3_active_goal_continuity.md`](design_g3_active_goal_continuity.md) — **DESIGN CLOSED** (★1–★4 locked)  

**Checkpoint base:** `checkpoint-g5-dse-component-sync` · commit `ada0a32`  

**Explicitly deferred:** G6 · G7 · G1/G2 · H5 · Catalog Impl C · F-1b · changing F-1 bare-payload default globally · H4 lever synonyms  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews → CLI probe. **No commit/push unless Engineer asks.**

---

## 0. Intent

When a Goal Plan has an active bindable `HandoffContext`, explore-shaped phrases that are **continuations** (undirected / same-dimension soft domain) must use the **active goal**, not silently invert it via text re-derive.

```text
Plan: reducir_payload
"optimiza payload"  → DSE(reducir_payload)   ← G3
"explora opciones"  → DSE(reducir_payload)   ← H1 (unchanged)
"ahora aumenta…"    → DSE(aumentar_payload)  ← explicit override
"optimiza autonomia"→ DSE(mejorar_autonomia) ← different dimension
```

Precedence (locked):

```text
explicit new goal  >  active goal  >  inferred/default goal
```

---

## 1. Engineer locks (from Design)

| # | Lock |
|---|---|
| ★1 | `"optimiza payload"` + active `reducir_payload` → **inherit reduce** |
| ★2 | Different dimension explore → **override** |
| ★3 | If routed as explore → text/precedence resolution; if engineering_intent → existing plan path. No dual-fire |
| ★4 | On successful explore with a **new** resolved goal ≠ prior handoff goal → **replace** `HandoffContext` (fresh `goal_key` + levers from `GOAL_STRATEGIES`) |

---

## 2. IN SCOPE

### 2.1 Pure precedence helper

Add a testable pure function (name illustrative), e.g.:

```text
resolve_explore_goal_with_handoff(
    user_input: str,
    text_goal: str | None,
    handoff: HandoffContext | None,
) -> str | None
```

Rules (must match Design §4):

1. No bindable handoff → return `text_goal`.  
2. `text_goal is None` → return `handoff.goal_key` (H1).  
3. `text_goal == handoff.goal_key` → return `text_goal`.  
4. Same dimension family **and** not opposite direction **and** no explicit opposite direction in text → return `handoff.goal_key` (★1).  
5. Else → return `text_goal` (★2 / explicit).

Dimension families + opposite pairs: per Design §3 (payload pair required; others as listed).

Reuse F-1 `_direction_of` / payload direction signals where possible for opposite detection — **do not** invent a parallel synonym NLP stack.

### 2.2 Wire into explore path

Call the helper from `_handle_explore` (or immediately before) so bare H1 behavior remains correct and G3 cases land.

**Do not** change `detect_goal`'s global bare-`"payload"` → `aumentar_payload` default (F-1). Continuity is resolved at explore+handoff layer.

### 2.3 Handoff replace on override (★4)

When explore succeeds with `resolved_goal != prior handoff.goal_key`, replace session `HandoffContext` with a new context for `resolved_goal` (same construction pattern as `_handle_engineering_intent`: levers from `GOAL_STRATEGIES`, `dse_capability` appropriate — if this explore consumed DSE, mark consumed consistently with H1).

Document in report how capability flags are set after override explore.

### 2.4 Files expected

| File | Change |
|---|---|
| New small helper module **or** extend existing handoff/goal helper | precedence function |
| `src/jarvis/core/orchestrator.py` | wire `_handle_explore` + ★4 replace |
| Focused tests | new `tests/test_g3_active_goal_continuity.py` (or similar) |
| FN-024 / F-1 regressions | must stay green |

---

## 3. OUT OF SCOPE

| Forbidden |
|---|
| G6 mass breakdown |
| G7 iterate `operation=None` |
| Always-inherit active goal |
| H4 `match_plan_lever` synonym expansion |
| Catalog / Impl C / H5 / G1 |
| Global rewrite of `goal_planner` |
| Changing bare `"payload"` default outside explore+handoff |

---

## 4. Tests (required)

| ID | Case |
|---|---|
| T1 | Plan `reducir_payload` → `explora opciones` → DSE reducir (H1 regression) |
| T2 | Plan `reducir_payload` → `optimiza payload` → DSE **reducir** (★1) |
| T3 | Plan `reducir_payload` → explore-shaped increase (`ahora aumenta el payload` / clear increase+payload) → DSE **aumentar** |
| T4 | Plan `reducir_payload` → `optimiza para autonomia` → DSE **autonomia** (★2) |
| T5 | No handoff → `optimiza payload` → today's text derive (`aumentar_payload`) |
| T6 | After T3/T4 successful explore, next bare `explora opciones` uses **new** handoff goal (★4) |
| T7 | Plan `aumentar_payload` → `optimiza payload` → DSE **aumentar** (symmetric continuation) |
| T8 | FN-024 / FN-025 / FN-026 / F-1 smoke green |
| T9 | Full suite green |

---

## 5. CLI probe (Engineer, post-review)

```text
1) Active project → "reducir payload" → Plan Reducir
2) "optimiza payload" → DSE minimizar/reducir carga útil  (NOT maximizar)
3) "ahora aumenta el payload" or clear increase explore → DSE maximizar
4) "explora opciones" → follows the last successful explore's handoff goal
```

---

## 6. Deliverables

1. Code + tests  
2. `.jes/artifacts/implementation_report_g3_active_goal_continuity.md`  
3. Update cli_findings G3 → 🟢 when Engineer confirms  

**Do not commit or push.**

---

## 7. Acceptance criteria (Cursor review)

**PASS** only if:

1. ★1 case closed (`optimiza payload` inherits reduce).  
2. Explicit opposite / other dimension still overrides.  
3. ★4 handoff replace verified.  
4. H1 bare explore unchanged.  
5. No G6/G7/catalog scope creep.  
6. Full suite green.

---

## 8. Queue after G3

```text
G3 PASS + CLI
        ↓
G1/G2 + H5 design
        ↓
(G6/G7 separate micro-contracts if prioritized)
        ↓
UX catálogo → Impl C
```
