# Implementation Contract — SYS-MAP-002

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Type:** Architecture documentation — **navigable System Map of the real codebase**. Zero product behavior changes.  

**Supersedes:** SYS-MAP-001 rev.2 (`.jes/artifacts/implementation_contract_sys_map_001.md`) — same pause on FNs, but delivery shape is now a **multi-file navigable map**, not a single mega-doc alone.  

**Engineer intent:** Checkpoint arquitectónico antes de FN-024. No queremos otro `ARCHITECTURE.md` genérico. Queremos una **representación estructural del sistema real** (visión humana → subsistema → módulo → función → conexión → dato/evidencia).  

**Explicitly not this cut:** FN-024 / H1–H5 implementation / Create→BOM / Conversation Engine / Step D / orchestrator refactor / any `src/**` behavior change.

**Ingest (mandatory):** SYS-MAP-001 rev.2 content in [`docs/JARVIS_SYSTEM_MAP.md`](../../docs/JARVIS_SYSTEM_MAP.md) was reviewed **PASS WITH NOTES** (`.jes/artifacts/implementation_review_sys_map_001.md`). This cut is primarily a **navigability / split refactor** of that accepted analysis into `docs/system_map/**` with stable `C-xxx` IDs — re-derive from code only where needed to fill gaps or fix mismatches. Preserve §8 open questions and Failures A–E (Expected/Actual/Violation). Do not weaken RED/YELLOW findings.

**Workflow:** Claude splits/augments map tree → Engineer forwards report → Cursor reviews. No commit/push unless asked.

---

## 0. Architectural intent (read first)

After FN-014…023 and the post-arch CLI probe, isolated layers often work; **handoffs between layers** fail or stay implicit. Continuing with FN-024 without a map risks patching symptoms while connections stay undefined.

```text
System Map (this contract)
     ↓
Connection audit (visible RED/YELLOW)
     ↓
Handoff design (lifecycle, authority) — later
     ↓
FN-024 / FN-025 / … — later
     ↓
Create→BOM — later
```

From this point forward, every future FN should be able to **point at a Connection ID** it creates or repairs.

---

## 1. Intent

Claude builds a **navigable JARVIS System Map** under `docs/system_map/`, derived primarily from **real code**, such that a human can answer:

- If the user writes X, which path does it take?
- Which layer receives another layer’s output?
- Which function calls which function?
- Where is a connection present / partial / broken / missing?
- Who has authority?
- What state flows through the system?

**Not** aspirational redesign. **Not** silent “fix” of docs to match wishful architecture. Code wins; mismatches are marked.

---

## 2. Source-of-truth order (mandatory)

```text
1. Code
2. Tests
3. Runtime / CLI evidence
4. Architecture documentation
5. Continuity / JES contracts
```

If docs and code disagree:

```text
⚠ DOCUMENTATION MISMATCH
Architecture / Continuity says: …
Code currently: …
Pointers: file + symbol
```

**Do not** rewrite the map to hide the mismatch.

---

## 3. Delivery layout

### 3.1 Provisional taxonomy (starting point)

Claude **must inspect code** and may adjust taxonomy (merge/split/rename/add). Every change goes in a **Taxonomy Delta** table in the Implementation Report (and in `docs/system_map/README.md`). Cursor review may FAIL taxonomy that is arbitrary or incomplete.

**Provisional tree:**

```text
docs/system_map/
├── README.md                 # how to navigate; taxonomy; maintenance rules
├── JARVIS_SYSTEM_MAP.md      # Nivel 0/1 master — human-readable whole system
├── CONNECTIONS.md            # central connection registry (IDs)
├── AUTHORITY.md              # decision → authority → forbidden (verified vs code)
├── FLOWS.md                  # reference CLI/control flows FLOW-001…
├── MISMATCHES.md             # doc↔code discrepancies
│
├── 01_runtime/RUNTIME_MAP.md
├── 02_intent/INTENT_MAP.md
├── 03_acquisition/ACQUISITION_MAP.md
├── 04_engineering/ENGINEERING_MAP.md   # goal_planner + engineering_intent gate
├── 05_iteration/ITERATION_MAP.md
├── 06_calculation/CALCULATION_MAP.md
├── 07_simulation/SIMULATION_MAP.md
├── 08_continuity/CONTINUITY_MAP.md     # continuity + closure + phase/reasoning as needed
├── 09_state/STATE_MAP.md               # ProjectState + Runtime session + workspace
└── 10_llm/LLM_MAP.md
```

**Allowed taxonomy adjustments (examples):**

- Split Continuity vs Closure vs Reasoning if code warrants  
- Add `11_persistence/` or fold workspace into `09_state/`  
- Combine Calculation+Simulation only if justified; prefer separate if call graph is distinct  
- Add adapters (`00_entry/`) for CLI/MCP if that clarifies Nivel 0  

**Disallowed:** inventing subsystems with no code; omitting real hotspots (orchestrator dual dispatch, acquisition, DSE, etc.).

### 3.2 Depth levels

| Level | Where | Content |
|---|---|---|
| **0 — System** | `JARVIS_SYSTEM_MAP.md` | User → entry → Orchestrator → subsystem bands → State; LLM boundary; **no** full function lists |
| **1 — Subsystems** | `NN_*/…_MAP.md` intro | Responsibilities, inbound/outbound connection IDs, authority |
| **2 — Modules & functions** | Same subsystem maps | Key modules (paths), important functions, call edges to other modules |

Master map stays **legible**. Detail lives in subsystem maps + CONNECTIONS.

### 3.3 Avoid duplication

| Content | Single home |
|---|---|
| Whole-system picture | `JARVIS_SYSTEM_MAP.md` |
| Connection records | `CONNECTIONS.md` only (subsystem maps **link by ID**, do not redefine) |
| Authority table | `AUTHORITY.md` (subsystem maps may quote 2–3 local rows) |
| Doc↔code conflicts | `MISMATCHES.md` |
| CLI reference journeys | `FLOWS.md` |

Subsystem maps describe **internals**; they reference `C-xxx` for edges.

---

## 4. What is a “component” vs a “connection”

### Component

Any of: package, module (`.py`), major class/session, or named orchestrator gate that owns a responsibility.

Listed with: path, one-line role, level (0/1/2).

### Connection (first-class entity)

A directed edge that transmits **control**, **data**, and/or **state**.

Each connection in `CONNECTIONS.md` **must** include:

| Field | Requirement |
|---|---|
| **ID** | `C-NNN` stable within this map version |
| **From** | component / module / function |
| **To** | component / module / function |
| **Kind** | `CONTROL` / `DATA` / `STATE` (can be multiple) |
| **Mechanism** | how (direct call, session field, return dict key, intent route, …) |
| **Symbols** | function/method names involved |
| **Payload** | what travels (`user_input`, `goal_key`, `ExplorationResult`, …) |
| **Authority** | who is allowed to decide on this edge |
| **Mutation** | YES/NO (does it write ProjectState / runtime?) |
| **LLM** | YES/NO/INDIRECT |
| **Status** | see §5 |
| **Evidence** | file path + symbol (and test name if applicable) |

**Do not invent connections.** If unsure, mark `⚪ NOT IMPLEMENTED` or omit with a note under “Suspected missing edges”.

---

## 5. Connection status taxonomy

```text
🟢 CONNECTED     — explicit path in code; works for intended use
🟡 PARTIAL       — implicit, incomplete, or only some payloads
🔴 BROKEN        — path claims to work but fails / falls to wrong layer (CLI evidence OK)
⚪ NOT IMPLEMENTED — designed/discussed but no code path
⚠ SUSPECT        — LLM or wrong layer appears to decide (authority smell)
```

Claude may propose a better taxonomy in README; default is above.

---

## 6. Required content by file

### `README.md`

- How to navigate Level 0 → 1 → 2 → Connection → Evidence  
- Final taxonomy (after delta)  
- Maintenance: future FNs must cite `C-xxx` they touch  
- Link to this contract  

### `JARVIS_SYSTEM_MAP.md` (Nivel 0/1)

Must show a **simplified** human master diagram, including at least:

```text
USER → CLI/MCP → ORCHESTRATOR
  → INTENT / CONTINUITY / ACQUISITION / ENGINEERING
  → ITERATION / DSE
  → CALCULATION → SIMULATION
  → STATE / WORKSPACE
```

Plus LLM boundary (deterministic core vs allowed LLM roles).  
Plus dual-dispatch note (ActionRouter **and** orchestrator if-chain) — document, do not fix.  
Link to subsystem folders and to critical `C-xxx` (especially RED).

### `CONNECTIONS.md`

Central registry. Seed **must** include (verify/adjust against code):

- Entry → Orchestrator  
- Orchestrator → Intent / Acquisition / Engineering intent gate  
- Goal Planner → (session/runtime?) → DSE  (**expect RED/PARTIAL** for bare `explora opciones`)  
- Goal Plan / levers → Iterate (**expect PARTIAL/BROKEN** for `safety_factor` preseed)  
- Calc → Sim → State  
- Sim → Continuity (**expect PARTIAL**)  
- Continuity → Acquisition / next-step surfaces  
- LLM Client → Parser → Policy → Orchestrator  
- Explore → Apply  

Also list **Forbidden transitions** (normative, even if code violates — violations → ⚠ SUSPECT or 🔴):

```text
LLM → acquisition target
LLM → goal selection
LLM → DSE configuration choice
Continuity → mutate ProjectState
DSE → silent mutate without apply path
Goal Planner → write physical params directly
```

### `AUTHORITY.md`

Decision → Authority → Must-not. **Verify against code**; if code violates, mark violation with evidence. Do not rubber-stamp a wished table.

### `FLOWS.md` — reference flows (from real behavior)

Minimum:

| ID | Name |
|---|---|
| FLOW-001 | Architecture acquisition |
| FLOW-002 | Engineering intention (`aumentar empuje` → goal_plan) |
| FLOW-003 | Explore design space (incl. broken `explora opciones` after plan) |
| FLOW-004 | Concrete mutation / iterate |
| FLOW-005 | Calculate / simulate |
| FLOW-006 | Continuity / project_status / next-step help |
| FLOW-007 | LLM fallback / analyze |

Each flow: user-visible steps → modules/functions → connection IDs → notes if BROKEN.

### Subsystem `*_MAP.md`

For each: purpose, key modules/paths, important functions (Nivel 2), inbound/outbound `C-xxx`, local state touched, tests that lock behavior (names only).

### `MISMATCHES.md`

All ⚠ DOCUMENTATION MISMATCH entries + sticky-state lessons (FN-021 class) relevant to future handoff design.

**Design-only appendix (no implementation):** open questions for plan/handoff context lifecycle vs engineering goal (anti-sticky); H5 Continuity data contract still open. Point to superseded `.jes/artifacts/design_layer_connection_map.md` for A–E sketch only.

---

## 7. CLI failure visibility (must appear in CONNECTIONS + FLOWS)

Represent clearly (not fix):

```text
Goal Planner → goal_plan CTA → user "explora opciones"
  → Intent explore without goal_key → _handle_explore → analyze/LLM
```

```text
Goal Plan lever safety_factor → user increment → Iterate without lever preseed
```

```text
Sim PASS+risky → Continuity next still generic optimize/simulate
```

```text
ayúdame + goal → analyze via \bayudame\b (precedence)
```

---

## 8. Files allowed / forbidden

### Allowed

| Path | Action |
|---|---|
| `docs/system_map/**` | **Create** entire tree |
| `docs/ARCHITECTURE.md` | Short pointer to `docs/system_map/` |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD → System Map; **pause FN-024 / Create→BOM** |
| `.jes/artifacts/design_layer_connection_map.md` | Supersede banner → `docs/system_map/` |
| `.jes/artifacts/implementation_contract_sys_map_001.md` | Banner: superseded by SYS-MAP-002 |
| `.jes/artifacts/cycle_note_sys_map_002.md` | Optional |

### Forbidden

| Path | |
|---|---|
| `src/**` | No behavior edits |
| New FN contracts for 024+ | Out of scope |
| “Fixing” handoffs in code | Out of scope |
| Conversation Engine / Step D / Create→BOM | Out of scope |

---

## 9. Method

1. Inventory `src/jarvis/` call graph for orchestrator turn path and major subsystems.  
2. Finalize taxonomy (delta vs provisional).  
3. Write master map + CONNECTIONS + AUTHORITY + FLOWS + MISMATCHES + subsystem maps.  
4. Cross-link IDs; ensure every RED has FLOW or CLI evidence note.  
5. Update ARCHITECTURE / TASKS pointers.  
6. Report.

Optional read-only probes (`resolve_intent`, `resolve_explore_goal`) — OK. No product commits from Claude unless Engineer asks later.

---

## 10. Acceptance criteria

| # | Criterion |
|---|---|
| A | `docs/system_map/` exists with README, master map, CONNECTIONS, AUTHORITY, FLOWS, MISMATCHES, and subsystem maps covering real major areas |
| B | Master map is human-legible Nivel 0/1 (not a function dump) |
| C | CONNECTIONS.md treats connections as first-class; each row has evidence |
| D | Status taxonomy applied; Goal→DSE and Plan→Iterate edges reflect CLI breakage |
| E | Control / Data / State distinguished on important edges |
| F | LLM boundary visible; suspect LLM authority marked |
| G | FLOWS-001…007 present and tied to connection IDs |
| H | Doc↔code mismatches recorded, not papered over |
| I | Taxonomy Delta documented if tree ≠ provisional |
| J | No `src/` behavior changes; no FN-024 |
| K | TASKS shows System Map as current focus; FN-024/Create→BOM paused |
| L | A reader can navigate System → Engineering → function → `C-xxx` → evidence |

---

## 11. Implementation report (Claude)

1. Diff / file tree created  
2. Taxonomy Delta vs provisional  
3. Connection counts by status (🟢🟡🔴⚪⚠)  
4. Top RED/PARTIAL edges (list IDs)  
5. Confirmation: zero product code changes  
6. Open design questions (handoff context lifecycle, H5 data) — **questions only**  
7. Explicit: FN-024 not started  

No commit/push unless asked.

---

## 12. Review checklist (Cursor)

- [ ] Navigable (not a single prose dump)  
- [ ] Connections first-class with evidence  
- [ ] Code-over-docs discipline  
- [ ] CLI breakages visible as 🔴/🟡  
- [ ] LLM boundary + forbidden transitions  
- [ ] Taxonomy justified  
- [ ] No product code / no FN-024  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 13. Queue after PASS

1. Engineer + Cursor accept map as living authority  
2. Connection audit → prioritize RED handoffs  
3. Design handoff contracts (lifecycle of plan context ≠ sticky `last_engineering_goal`)  
4. **Then** FN-024+ Implementation Contracts citing `C-xxx`  
5. Create→BOM only after critical handoffs healthy  
6. Step D / Conversation Engine — blocked  

---

## 14. One-line brief for Claude

> Build `docs/system_map/` as a navigable as-is map of Jarvis from real code: master view, subsystem maps, and a connection registry with evidence—so we can see broken handoffs before any FN-024. Do not change product code.
