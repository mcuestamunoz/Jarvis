# Implementation Contract — FN-024 (H1 + H2)

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** SUPERSEDED by delivery — see `.jes/artifacts/implementation_report_fn024.md` and `.jes/artifacts/implementation_review_fn024.md` (**PASS WITH NOTES**).  

**Type:** Product behavior — first **Handoff Context consumer** (Plan → DSE) + CTA honesty.  

**Closes / repairs:** **C-042** 🔴 → 🟢 (primary) · **H1** · **H2** (M-002 CTA honesty)  

**Design authority (mandatory read):**  
[`docs/system_map/HANDOFF_CONTEXT_DESIGN.md`](../../docs/system_map/HANDOFF_CONTEXT_DESIGN.md) — **Decision log §5 CLOSED**: Hybrid Operation-Scoped Context  

**Related edges (do not “fix” in this cut):** C-043 (H4), C-025/C-044 (H3), C-081 (H5) — must remain available for later consumers (do **not** wipe whole context on DSE).  

**Depends on:** FN-022 (engineering intent / goal plan) · SYS-MAP-002  

**Workflow:** Claude implements + tests + updates System Map statuses → Engineer forwards report → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Intent

Make `"explora opciones"` after a Goal Plan run **DSE for that plan’s `goal_key`**, without LLM fallback, by binding through an **operation-scoped Handoff Context**.

Simultaneously stop advertising a bare CTA that cannot resolve when no bindable context exists (**H2**).

```text
aumentar empuje
    → engineering_intent + goal_plan
    → CREATE HandoffContext (goal_key, levers[], dse=ACTIVE, iterate=ACTIVE)
    → CTA may include 'explora opciones'  (H2: only because context exists)

explora opciones
    → intent explore_design_space
    → resolve_explore_goal == None
    → BIND goal_key from active HandoffContext (DSE capability ACTIVE)
    → DesignExplorer.explore(...)
    → CONSUME DSE capability only  (goal_key + levers remain for H4)
```

**Not this cut:** help+goal routing (H3), iterate lever preseed (H4), Continuity risk thread (H5), Create→BOM.

---

## 1. Architectural constraints (non-negotiable)

| Rule | Source |
|---|---|
| No `last_engineering_goal` sticky string as the design | Handoff design — rejected |
| Context is **operation-scoped**, capability-consumable | Decision log |
| DSE success **consumes DSE capability only** | Decision log — preserves C-043 path |
| Runtime-only; **never** in `_PERSISTED_SESSION_FIELDS` / `state.json` | C-046 sibling; FN-012/021 family |
| Project switch / load → **invalidate** whole context | Absolute boundary |
| New engineering_intent → plan → **replace** context | Decision log |
| Continuity / `project_status` / analyze (unrelated) → **must not** clear context by side effect | Decision log |
| LLM must not create/choose context | AUTHORITY.md |
| Prefer existing session + orchestrator patterns; no new subsystem / Conversation Engine | CLAUDE.md |

---

## 2. Scope

### In scope

| # | Work |
|---|---|
| 1 | Minimal `HandoffContext` (or equivalent) on `InteractiveSessionState` — runtime only |
| 2 | **Create** context in `_handle_engineering_intent` after a successful plan (C-041 path) |
| 3 | **Bind** in `_handle_explore` when `goal_key is None`: if context active and DSE capability ACTIVE → use `context.goal_key` |
| 4 | After successful DSE explore for that bind: mark **DSE capability CONSUMED** (not whole context) |
| 5 | **H2 CTA:** include bare `'explora opciones'` only when a bindable context is being/was just created; otherwise only qualified phrasing (`optimiza para {domain}`) |
| 6 | Hard invalidate on project switch/load; replace on new plan; exclude from session snapshot persistence |
| 7 | Regression tests for FLOW-002 → FLOW-003 broken sub-case + blast-radius (status must not wipe; second explore without Active DSE capability behavior defined) |
| 8 | Update System Map: C-042 → 🟢; add connection IDs for create/bind if needed; FLOW-003 notes; HANDOFF / STATE map pointers |

### Out of scope

| Forbidden |
|---|
| H3 / C-025 / C-044 |
| H4 / C-043 iterate preseed (but **store levers** now for H4) |
| H5 / C-081 |
| Consuming/wiping whole context on DSE |
| Persisting context to disk |
| Dual-dispatch refactor |
| Create→BOM / Conversation Engine / Step D |
| Opportunistic hygiene deletes |

---

## 3. Data shape (minimum for FN-024)

Implement as a small typed structure (Pydantic model or TypedDict) on session, e.g. `handoff_context: … | None`.

**Required fields for this cut:**

```text
goal_key: str                         # from goal_planner
levers: list[str]                     # lever strings from strategies shown (GOAL_STRATEGIES / prioritized order)
origin: "engineering_intent"          # only this origin in FN-024
dse_capability: "active" | "consumed"
iterate_capability: "active"          # leave active; H4 later
# optional but useful:
# lever_status: map lever → active|consumed|reconciled  (default all active)
```

**Do not** store Continuity gaps, BOM, LLM text, or full plan markdown as authority.

**Create payload:** levers = those printed/used by `format_goal_plan` / `_prioritize_strategies` for this `goal_key` (deterministic). Compound lever strings (e.g. `"per_motor_max_thrust_n / motors"`) are OK to store verbatim for H4 later.

**Persistence:** add `handoff_context` alongside `last_exploration_result` as **excluded** from `_PERSISTED_SESSION_FIELDS`. On restore/load project, ensure `None`.

---

## 4. Behavioral contract

### 4.1 Create (C-041 path)

On `_handle_engineering_intent(goal_key)` success:

1. Build plan text as today.  
2. Set `session.handoff_context` with `goal_key`, `levers`, `dse_capability=active`, `iterate_capability=active`, `origin=engineering_intent`.  
3. CTA (**H2**): may include `'explora opciones'` **because** context was just created and DSE capability is active. Keep qualified `'optimiza para {domain}'` as well.

### 4.2 Bind (repairs C-042)

In `_handle_explore(goal_key, …)` when incoming `goal_key is None`:

1. If `handoff_context` is not None **and** `dse_capability == active` **and** `handoff_context.goal_key` is in `EXPLORATION_GRIDS` → use that `goal_key` (deterministic bind).  
2. Else → existing analyze fallback (honest: no bindable DSE capability).

When bind succeeds and explore runs successfully: set `dse_capability = consumed`. Context object remains (goal_key + levers + iterate_capability).

**Explicit explore with domain** (`optimiza para estabilidad`) that resolves `goal_key` without context: keep working (C-045). Optionally leave context untouched or align — do **not** require context for explicit goals. Prefer: if context exists and same goal_key, still mark DSE consumed after success; if different goal_key, do not silently overwrite context in this cut (document choice in report; simplest: leave context as-is when explore used an explicit goal_key from text).

### 4.3 Second bare `"explora opciones"` after DSE capability consumed

Must **not** pretend to bind again. Fall through to analyze **or** a short deterministic message that DSE for this operation was already run / ask for `optimiza para {domain}` or apply. Pick one; prefer deterministic non-LLM message if cheap; analyze fallback acceptable if documented. **Do not** re-activate DSE capability implicitly.

### 4.4 Hard invalidation (must implement + test)

| Event | Action |
|---|---|
| Project switch / `load_active_project` path that changes project | `handoff_context = None` |
| Session restore from snapshot | field absent / None |
| New `_handle_engineering_intent` | **Replace** entire context |
| `project_status` / Continuity | **No clear** |
| Unrelated `analyze` | **No clear** (unless you introduce explicit abandon — not required) |

### 4.5 Apply exploration (C-046)

Default: **do not** invalidate whole handoff context (Decision log). DSE capability already consumed.

---

## 5. New / updated connection IDs

| ID | Action |
|---|---|
| **C-042** | Status → 🟢; mechanism = bind from handoff_context when bare explore |
| **C-105** (new) | `_handle_engineering_intent` → create/replace `handoff_context` |
| **C-106** (new) | active handoff_context (DSE capability) → `_handle_explore` goal bind |

Update Canonical registry count to **59** after adding C-105/C-106. Update DIAGRAMS/canvas if present in-repo. FLOW-003 broken sub-case → working with note. MISMATCHES H1/H2 → implemented / partially closed as applicable.

---

## 6. Tests (required)

| # | Case |
|---|---|
| T1 | `aumentar empuje` (or equivalent) → plan → session has handoff_context with expected goal_key + dse active |
| T2 | Then `"explora opciones"` → `explore_design_space` / DSE path, **not** analyze; uses context goal_key |
| T3 | After T2, `dse_capability == consumed`; `goal_key` and levers still present |
| T4 | Second `"explora opciones"` does **not** silently re-run bind as if active (per §4.3) |
| T5 | `"optimiza para estabilidad"` still works without depending on broken bare path |
| T6 | `project_status` after plan does **not** clear handoff_context |
| T7 | New engineering intent replaces context (new goal_key) |
| T8 | Project switch / load clears context (or never restores it) |
| T9 | CTA after plan includes explora opciones only when context created (H2 smoke) |

Prefer orchestrator-level tests (existing FN-022 style) over full CLI if faster; include at least one end-to-end path matching FLOW-002→003.

---

## 7. Blast-radius proof (report section)

Implementation Report must include a table:

| Path | Context effect | Evidence (test or code pointer) |
|---|---|---|
| engineering_intent | create/replace | |
| bare explora opciones | bind + consume DSE cap | |
| explicit optimiza para … | … | |
| project_status | keep | |
| apply exploration | keep (default) | |
| project switch/load | invalidate | |
| iterate path (untouched) | keep (no H4 yet) | |

Same discipline as FN-021: show untouched paths are safe, do not only assert.

---

## 8. Acceptance criteria (Cursor review)

PASS only if:

1. FLOW-003 broken sub-case fixed: plan → `"explora opciones"` → DSE with plan’s goal_key, 0 LLM for that path.  
2. DSE capability consumed; levers/goal_key retained (H4 not broken by this cut).  
3. No persistence of handoff_context; project boundary clears.  
4. H2: bare CTA not advertised when bind would be impossible.  
5. Tests T1–T9 (or justified equivalent set) green.  
6. System Map updated (C-042, C-105, C-106, FLOW-003, counts).  
7. No H3/H4/H5 / Create→BOM / dual-dispatch refactor.  
8. Report cites Handoff Context Decision log + invalidation proof.

FAIL if:

- Whole context wiped on DSE  
- Sticky goal without capability model  
- Context restored from disk  
- C-043 path made worse (levers discarded)  
- C-025 “fixed” via drive-by regex without contract  

---

## 9. Implementation Report template (Claude)

```markdown
# Implementation Report — FN-024 (H1+H2)

## Summary
## Design citation
- Handoff Context Decision log: Hybrid Operation-Scoped …
## Behavior changed
## Files changed
## Connections
- C-042 → 🟢
- C-105 / C-106 added
## Tests run
## Blast-radius table
## Explicitly deferred
- H3, H4, H5, Create→BOM
## Risks
```

---

## 10. Prompt to paste into Claude Code

> Execute Implementation Contract **FN-024** (`.jes/artifacts/implementation_contract_fn024_h1_h2_handoff_dse.md`).
>
> Read `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` Decision log first (Hybrid Operation-Scoped Context).
>
> Implement runtime-only Handoff Context: create on successful engineering goal plan; bind bare `"explora opciones"` to context `goal_key` when DSE capability is ACTIVE; consume **DSE capability only** after successful DSE; keep goal_key/levers for future H4. Fix CTA honesty (H2). Never persist context; clear on project switch; replace on new plan. Do **not** implement H3/H4/H5.
>
> Add tests T1–T9 (or equivalent). Update System Map (C-042, C-105, C-106, FLOW-003, registry count). No commit/push unless asked. Return Implementation Report for Cursor review.
