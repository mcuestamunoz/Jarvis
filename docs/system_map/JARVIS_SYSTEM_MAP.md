# Jarvis System Map — Level 0/1 (Master)

**Read this first.** For connection-level detail follow the `C-xxx` IDs into `CONNECTIONS.md`. For a visual rollup of all edges see [`DIAGRAMS.md`](DIAGRAMS.md) (and the interactive [`jarvis-system-map.canvas.tsx`](jarvis-system-map.canvas.tsx)). Before any handoff FN, read [`HANDOFF_CONTEXT_DESIGN.md`](HANDOFF_CONTEXT_DESIGN.md). For module/function detail follow a subsystem link into `NN_*/…_MAP.md`. This file intentionally does not list functions — that's Level 2, and it lives in the subsystem maps.

## Whole-system picture

```text
USER
  │
  ▼
CLI / MCP adapter ──────────────────────────────────────────────  00_entry
  │  (handle_user_text — natural language)   (handle — structured action)
  ▼                                                    │
ORCHESTRATOR (core/orchestrator.py) ────────────────────  01_runtime
  │  ~25-checkpoint dispatch chain (see FLOWS.md, C-010…C-016)
  │
  ├──► INTENT (resolve_intent, one 13-way classifier) ──────────  02_intent
  │
  ├──► ACQUISITION (what gap is missing? Continuity-authoritative) ── 03_acquisition
  │       mention gate · help-define · Brief · component wizards
  │
  ├──► ENGINEERING (what design goal? deterministic plan; DSE)  ──── 04_engineering
  │       goal_planner · design_explorer · handoff_context (FN-024/025/026)
  │       (C-042 fixed FN-024 — C-105/C-106; C-025/C-044 fixed FN-025;
  │        C-043 fixed FN-026 — H1-H4 all closed, 0 RED)
  │
  ├──► ITERATION (concrete mutation wizard) ─────────────────────── 05_iteration
  │
  ├──► CALCULATION → SIMULATION (pure physics) ──────────────────── 06/07
  │       L1 hover energy always; L2 ESTIMATIVO via product writer (4S),
  │       not DSE — C-060 detail only, no new C-xxx; lab = HARDWARE_DEBT
  │
  ├──► CONTINUITY (Situation / Evidence / Next-step; BOM; readiness rollup ERF-1) ─── 08_continuity
  │       project_continuity · engineering_readiness · project_closure (C-107–C-110)
  │
  └──► STATE / WORKSPACE (ProjectState, runtime session, disk) ───── 09_state
           ▲
           │ all of the above read/write through here — this is the
           │ single source of engineering truth
  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  LLM (llm/*.py) ── reachable ONLY from Orchestrator, as a bounded    10_llm
  fallback (`interpret`, closed 4-verb action set) or narrator
  (`analyze`, return value is a message string, never routing)
```

## The LLM boundary (deterministic core vs. allowed LLM roles)

Every subsystem above the dashed line is deterministic — same input, same output, no network call, no model. The LLM is reachable from exactly two orchestrator call sites:

- `llm_interface.interpret(user_input, runtime_state)` — only when **nothing** in the deterministic chain (checkpoints 1–22 of `RUNTIME_MAP.md`) classified the turn. Its return value is validated by `ActionPolicy` against a **closed 4-action set** (`create_project`, `iterate`, `calculate`, `simulate`) — it cannot name a component, a goal, or a DSE grid. See `AUTHORITY.md` and C-100…C-104.
- `llm_interface.analyze(user_input, context, ...)` — narration only. Its return value is a message string appended to (or wrapping) deterministic content (e.g. `format_goal_plan`'s output); it is never parsed back into a routing decision.

**Nothing else in the system can reach the LLM.** Acquisition, Engineering, Iteration, Calculation, Simulation, Continuity, and State are all LLM-free by construction (verified per-module in the subsystem maps' "LLM" column).

## Dual-dispatch note (documented, not fixed)

There are two independent entrypoints into the same engine, and they are not unified:

1. `orchestrator.handle(request)` — structured action, used by MCP/tests, routes through `ActionRouter` (4 actions only) after two interactive-session short-circuits.
2. `orchestrator.handle_user_text(text, llm)` → `_handle_user_text_inner` — natural-language, ~25-checkpoint if-chain, which for a *subset* of resolved intents (`create_project`/`iterate`/`calculate`/`simulate`) calls back into `self.handle(...)` (mechanism 2 → mechanism 1), and for every other intent has its own dedicated handler that never touches `ActionRouter`.

Full detail: `00_entry/ENTRY_MAP.md` and `01_runtime/RUNTIME_MAP.md`; connection: **C-016**.

## Where the chain is currently broken (headline — full detail in CONNECTIONS.md / FLOWS.md)

| Edge | Status | ID |
|---|---|---|
| Goal Plan → DSE (bare `"explora opciones"` after a plan) | 🟢 **FIXED (FN-024, 2026-08-10)** | C-042 |
| "ayúdame" + named goal → plan/explore | 🟢 **FIXED (FN-025, 2026-08-12)** | C-025 / C-044 |
| Goal Plan lever (e.g. `safety_factor`) → Iterate preseed | 🟢 **FIXED (FN-026, 2026-08-12)** | C-043 |
| Sim PASS + risky margin → Continuity next-step thread | 🟡 PARTIAL (WEAK) — H5, deferred | C-081 |
| Readiness → full Continuity next-step handoff | 🟡 PARTIAL — catalog gap only (Slice 4b deferred) | C-108 |

C-042 (FN-024), C-025/C-044 (FN-025), and C-043 (FN-026) all bind through the same `HandoffContext` (Hybrid Operation-Scoped lifecycle — see `MISMATCHES.md`). **H1–H4 are all closed — 0 RED edges remain.** C-081 (H5) and C-108 remain 🟡 PARTIAL — **deferred map debt, not today's implementation queue.** Hardware lab is [`docs/HARDWARE_DEBT.md`](../HARDWARE_DEBT.md). **PRIORIDAD AHORA:** await Engineer next focus after Structure plate multiplicity B2 CLOSED (suite **2294**) — see `docs/IMPLEMENTATION_TASKS.md`. Baseline: **`v0.3.6`**.

## Subsystem index

| Folder | One-line role | Inbound (from) | Outbound (to) |
|---|---|---|---|
| [`00_entry`](00_entry/ENTRY_MAP.md) | CLI/MCP surface, dual-dispatch seam | User | Orchestrator |
| [`01_runtime`](01_runtime/RUNTIME_MAP.md) | Turn dispatcher, ~25 checkpoints | Entry | Intent, Acquisition, Engineering, Iteration, State, LLM |
| [`02_intent`](02_intent/INTENT_MAP.md) | Regex intent classification | Runtime | Runtime (routing decision only) |
| [`03_acquisition`](03_acquisition/ACQUISITION_MAP.md) | Next-gap authority, wizards | Runtime, Continuity | State (writes via component_writers), Runtime |
| [`04_engineering`](04_engineering/ENGINEERING_MAP.md) | Goal detection, DSE | Runtime, Intent | State (read-only DSE), Runtime |
| [`05_iteration`](05_iteration/ITERATION_MAP.md) | Concrete mutation wizard | Runtime | State, Calculation |
| [`06_calculation`](06_calculation/CALCULATION_MAP.md) | Physics build | Iteration, Actions | Simulation |
| [`07_simulation`](07_simulation/SIMULATION_MAP.md) | Feasibility verdict | Calculation | State, Continuity |
| [`08_continuity`](08_continuity/CONTINUITY_MAP.md) | Situation/Evidence/Next-step; readiness rollup (ERF-1) | State, Simulation, authorities (C-107) | Runtime (project_status), Acquisition, CLI (C-108–C-110) |
| [`09_state`](09_state/STATE_MAP.md) | Source of truth | Everything | Everything |
| [`10_llm`](10_llm/LLM_MAP.md) | Bounded fallback + narrator | Runtime | Runtime (closed action set) |

## Registries

- [`CONNECTIONS.md`](CONNECTIONS.md) — every edge, `C-001`…`C-110`, with evidence
- [`AUTHORITY.md`](AUTHORITY.md) — decision → authority → forbidden, verified against code
- [`FLOWS.md`](FLOWS.md) — `FLOW-001`…`FLOW-007`, user-visible journeys tied to connection IDs
- [`MISMATCHES.md`](MISMATCHES.md) — doc↔code discrepancies, sticky-state lesson, design-only appendix (handoff-context lifecycle, H5)
