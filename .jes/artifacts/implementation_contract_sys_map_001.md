# Implementation Contract — SYS-MAP-001 (rev. 2)

> **SUPERSEDED** by [**SYS-MAP-002**](implementation_contract_sys_map_002.md) (2026-08-10).  
> Do **not** implement this rev.2 single-file shape. Claude must follow SYS-MAP-002: navigable `docs/system_map/` tree + CONNECTIONS registry.  
> FN-024 / product code remain forbidden.

---

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** SUPERSEDED — see SYS-MAP-002  

**Type:** Architecture documentation only. **Zero product behavior changes.**  

**Engineer verdict on prior design zoom:** DESIGN → PASS WITH NOTES — **do not implement H1–H5 / FN-024 yet.**  
**This contract:** Build the **complete as-is System Map** from real code. Refine handoff *design questions* inside the map. No fixes.

**Related:** `.jes/artifacts/design_layer_connection_map.md` (post-arch zoom — **absorb**; mark superseded)  
**Depends on:** FN-014…023 closed on `main`  

**Workflow:** Claude investigates + writes map → Engineer forwards → Cursor reviews. No commit/push unless asked.

---

## 1. Intent

Produce **`docs/JARVIS_SYSTEM_MAP.md`** — the living authority for:

1. What components exist  
2. Who has authority for each decision  
3. Exact turn / checkpoint order  
4. Mode state machine + invariants  
5. Handoffs (as-is + broken)  
6. Data ownership  
7. Failure matrix (CLI probes A–E in Expected / Actual / Violation form)  
8. **Open design questions** for future handoff contracts (esp. plan context lifecycle) — **not** implementation recipes that invent sticky state  

**Explicitly forbidden in this cut:**

- Implementing FN-024 / H1–H5 / Create→BOM / Conversation Engine / Step D  
- Adding `last_engineering_goal` (or any new runtime field) to code  
- Refactoring dual dispatch (ActionRouter vs if-chain) — **document only**  
- Treating the post-arch zoom as the whole system  

---

## 2. Why this order

```text
SYSTEM MAP COMPLETE (this contract)
        │
        ▼
Refine H1–H5 with lifecycle / precedence / data contracts
        │
        ▼
THEN Implementation Contract FN-024 (only if still needed)
        │
        ▼
Implement
```

Starting FN-024 with a naive `last_engineering_goal` risks a new sticky-state class (FN-021 lesson). The map must force the distinction **engineering state vs handoff context** before any code.

---

## 3. Scope

### In scope

| # | Deliverable |
|---|---|
| 1 | `docs/JARVIS_SYSTEM_MAP.md` — sections in §4 (complete system, not only post-arch) |
| 2 | Real module inventory under `src/jarvis/` with paths |
| 3 | Exact checkpoint order from `_handle_user_text_inner` (+ nested DEFINE / ITERATE) |
| 4 | Absorb A–E + provisional H1–H5 from `design_layer_connection_map.md`, then **upgrade** them per Engineer NOTES (§4.8–4.10) |
| 5 | Pointers in `docs/ARCHITECTURE.md` + `docs/IMPLEMENTATION_TASKS.md` — FNs / Create→BOM **paused** |
| 6 | Banner on `.jes/artifacts/design_layer_connection_map.md`: superseded by SYS-MAP |
| 7 | Optional `.jes/artifacts/cycle_note_sys_map_001.md` |

### Out of scope

- Any `src/**` behavior change  
- FN-024+ implementation  
- Choosing/implementing persistence for plan context  
- Continuity copy redesign beyond documenting the gap  

---

## 4. Required structure of `docs/JARVIS_SYSTEM_MAP.md`

### 0. Meta

- Purpose: as-is map for reproducible engineering  
- Non-goals: redesign, Conversation Engine, Create→BOM  
- Maintenance rule: when an FN closes, update Authority / Handoffs / Failures  
- Links: Continuity, ARCHITECTURE, CLAUDE.md, this contract  

### 1. Mapa físico de componentes (COMPLETE)

Must include **both** control-plane and physics/LLM pipelines:

**Control / language plane:**

```text
USER → CLI/MCP adapters → Orchestrator
         ├── Runtime Session
         ├── Acquisition Target / Brief
         ├── Intent Resolver
         ├── Goal Planner
         ├── DSE
         ├── Iterate Wizard
         ├── Continuity / Closure / Phase / Reasoning
         └── ActionRouter (dual dispatch callout)
```

**Physics / persistence plane:**

```text
Project State
  → Component Inference
  → Component Resolver
  → Component Writers
  → Calculation Engine
  → Simulator
  → Workspace / views / snapshots
```

**LLM plane:**

```text
LLM Client → Response Parser → Action Policy → Orchestrator
(analyze / interpret fallback only where documented)
```

Inventory tables by package with file paths. Dual dispatch: document hotspot; **do not propose refactor in this cut**.

### 2. Mapa de autoridad

Decision → Authority → Forbidden usurper.

Must state:

> ProjectState / Acquisition / Continuity own **what is next**. LLM interprets and may narrate; **must not** choose the next engineering target or goal.

Include Acquisition, mode, intent, goal, DSE, iterate, physics, Continuity, LLM — plus FN-004 / Bug54 / catalog assist if present in code.

### 3. Mapa de flujo de un turno

Numbered checkpoints matching **current** code (old “13 checkpoints” audit is stale — replace with SYS-MAP inventory count).

Nested branches for ITERATE_INTERACTIVE and DEFINE_MISSING_PARAMETERS required.

### 4. Mapa de estados

`OrchestratorMode` machine + transitions + invariants.

**Hard invariant (enforced):**

```text
DEFINE_MISSING + _next_pending_block() is None → IDLE   (FN-021)
```

**Candidate invariants (document as open — from CLI):**

```text
ITERATE_INTERACTIVE + restriction phrase ("no cambiar tamaño")
  → still wizard answer vs new intent re-resolve?
```

### 5. Matriz de contratos de handoff (REQUIRED — Engineer note §8)

For **every** critical edge, a row:

| Handoff | Input | Output | Authority | Mutation | LLM | Status |
|---|---|---|---|---|---|---|

Minimum edges: Intent→Goal, Goal→DSE, Goal/Plan→Iterate, Sim→Continuity, Continuity→Acquisition, Inference→Resolver, Calc→Sim, LLM→Orchestrator, Explore→Apply, Orchestrator→Acquisition, etc.

Plus **Forbidden transitions** box:

```text
LLM → acquisition target          FORBIDDEN
LLM → goal selection              FORBIDDEN
LLM → DSE configuration           FORBIDDEN
Continuity → mutate               FORBIDDEN
DSE → silently mutate             FORBIDDEN
Goal Planner → physical state     FORBIDDEN
```

(Extend if code reveals more.)

### 6. Mapa de datos

ProjectState / Runtime session / Continuity payload / Simulation context / turn locals — who writes, who reads, overwrite rules, contradiction classes (FN-021 class).

### 7. Matriz de fallos — formato Expected / Actual / Violation (REQUIRED)

Not only A–E labels. For each CLI probe:

```text
ID / User input
Expected layer path
Actual layer path
Broken handoff
Authority violation
Code pointers (file + symbol)
Status: BROKEN | WEAK | OK
```

**Minimum probes:**

| ID | Input | Seed expected vs actual |
|---|---|---|
| A | `explora opciones` after plan | Expected Goal→DSE(goal); Actual explore(no goal)→analyze→LLM |
| B | `ayudame a mejorar la estabilidad` | Expected help→goal_plan; Actual analyze→LLM |
| C | `incrementa safety_factor` (+ sí) | Expected Plan→Iterate(preseed); Actual generic wizard |
| D | after sim PASS+risky | Expected Continuity uses margin thread; Actual generic “optimiza o simula” |
| E | `mejorar estabilidad` vs `aumentar empuje` | Two doors residual |

### 8. Engineering state vs handoff context (REQUIRED — Engineer note §2–3)

The map **must** introduce this distinction as a **design section**, not as an implemented feature:

```text
Engineering Goal          ← may be persistent engineering meaning (optional future)
        │
        ▼
Goal Plan (strategies/levers)
        │
        ▼
Plan / Handoff Context    ← temporary: CTA, levers, candidate DSE goal
        │
        ├── YES valid context → "explora opciones" binds to plan goal
        └── NO → require explicit resolve (optimiza para X / ask)
```

**Open questions Claude must list (answers = design proposals only, not code):**

1. Does handoff context last **one turn**, until DSE runs, until mutation, until sim, until Continuity changes thread, until project switch?  
2. Lives in **runtime only** vs ProjectState? (default recommendation in map: **runtime-only**, clear on project load — justify)  
3. How to avoid **stale handoff context** (FN-021 class)? Clear rules to propose.  
4. Explicit rejection of naive sticky `last_engineering_goal` without lifecycle.

### 9. Provisional handoff designs H1–H5 (DESIGN ONLY — not FN specs)

Absorb prior H1–H5 and **refine** with Engineer NOTES:

| ID | Topic | Must refine in map |
|---|---|---|
| **H1** | Plan → DSE | Bind via **valid Plan/Handoff Context**, not bare sticky goal; lifecycle open questions in §8 |
| **H2** | CTA honesty | CTA phrases must match resolvable paths; short `explora opciones` only if H1 context exists |
| **H3** | Help + goal | Document **normative precedence** extracted from real checkpoint order (Acquisition/help before engineering intention before analyze/LLM) |
| **H4** | Lever → Iterate | Preseed **only if** lever ∈ **current plan's strategy levers**; Iterate receives context, does not invent it |
| **H5** | Sim → Continuity | **Remain DESIGN** — specify open data contract questions (what Continuity should emit for PASS+risky + optional goal thread). **Do not** recommend FN-027 until data contract is clear |

State clearly: **no Implementation Contract for H1–H5 until SYS-MAP is PASS and Engineer picks RED edges.**

### 10. Implications

- Pause FN-024+ and Create→BOM  
- After SYS-MAP PASS: Engineer chooses which RED edge becomes the first handoff FN  
- Dual dispatch = visualize only  

### 11. Appendix

- Files read / optional probes (read-only)  
- Checkpoint count vs old “13”  

---

## 5. Method (Claude)

1. Read-only walk of `src/jarvis/` focusing on orchestrator turn path, intent_resolver, goal_planner, design_explorer, acquisition_*, continuity, closure, iterate sessions, action_router, component_*, calculation, simulator, llm pipeline.  
2. Optional probes for failure A (`resolve_intent` / `resolve_explore_goal` on `explora opciones`) — no code edits.  
3. Write `docs/JARVIS_SYSTEM_MAP.md` to §4.  
4. Update ARCHITECTURE + TASKS pointers; supersede banner on design_layer_connection_map.  
5. Report.

**Quality bar:** A new engineer can answer “who decides X?”, “what runs before LLM?”, and “what is broken between Goal and DSE?” from this doc alone.

---

## 6. Acceptance criteria

| # | Criterion |
|---|---|
| A | SYS-MAP exists with sections covering §4.0–§4.11 |
| B | Physical map includes control + physics + LLM planes |
| C | Checkpoint list matches current `_handle_user_text_inner` |
| D | Authority map forbids LLM choosing next target |
| E | Handoff **matrix** Input/Output/Authority/Mutation/LLM + Forbidden transitions |
| F | Failures A–E in Expected/Actual/Violation form with code pointers |
| G | § Engineering state vs Handoff context + lifecycle open questions; **no** naive sticky field prescribed as “just implement this” |
| H | H4 requires lever ∈ plan levers |
| I | H5 marked DESIGN-only with open data questions |
| J | Explicit: do not implement FN-024 in this cut |
| K | No `src/` behavior changes |
| L | TASKS shows FNs/Create→BOM paused pending map acceptance |

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `docs/JARVIS_SYSTEM_MAP.md` | **Create** |
| `docs/ARCHITECTURE.md` | Short pointer |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD → SYS-MAP; pause FNs |
| `.jes/artifacts/design_layer_connection_map.md` | Supersede banner |
| `.jes/artifacts/cycle_note_sys_map_001.md` | Optional |

**Forbidden:** `src/**` edits; FN-024 code; new runtime fields; Conversation Engine.

---

## 8. Implementation report (Claude)

1. Diff per file  
2. Checkpoint count (vs old 13)  
3. Confirmation: no `src/` behavior edits  
4. List of open lifecycle / H5 data questions for Engineer  
5. RED edges ranked for **future** contracts (recommendation only)  
6. Confirmation H1–H5 are design-only in the doc  

No commit/push unless asked.

---

## 9. Review checklist (Cursor)

- [ ] Complete system (not only post-arch zoom)  
- [ ] Authority + forbidden transitions  
- [ ] Checkpoint accuracy spot-check  
- [ ] A–E Expected/Actual/Violation  
- [ ] Engineering vs handoff context section present; no sticky-state trap prescribed  
- [ ] H4 lever∈plan; H5 design-only  
- [ ] No product code  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Queue after PASS

1. Engineer accepts SYS-MAP as living authority  
2. Resolve open questions in §8 / H5 (design decisions)  
3. **Then** emit first handoff Implementation Contract (likely Plan→DSE) with explicit context lifecycle  
4. Create→BOM still later  
5. Step D / Conversation Engine — blocked  
