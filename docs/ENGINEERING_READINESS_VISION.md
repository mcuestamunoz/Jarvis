# Engineering Readiness Vision

**Status:** Draft (target architecture)  
**Type:** Vision / To-be  
**Date:** 2026-08-18

---

## 1) Purpose

Define the next product-level jump for Jarvis:

- From: "design calculates/simulates coherently"
- To: "design is engineering-complete and assembly-ready, with explicit gaps and dependencies"

This document is **not** an as-is architecture map and **must not** be used as evidence of implemented behavior.

---

## 2) Document Boundaries (anti-drift contract)

- **Current system truth (as-is):**
  - `docs/ARCHITECTURE.md`
  - `docs/system_map/README.md`
  - `docs/system_map/CONNECTIONS.md`
- **Execution queue truth (what to implement next):**
  - `docs/IMPLEMENTATION_TASKS.md`
  - `.jes/state/engineering_state.json`
- **Target vision truth (this document):**
  - `docs/ENGINEERING_READINESS_VISION.md`

Rule: this vision evolves independently until an implementation contract is approved.  
Only implemented and validated behavior moves into `ARCHITECTURE.md` and `docs/system_map/*`.

---

## 3) Core Problem

Jarvis already supports deterministic intent, acquisition, calculation, simulation, iteration, and continuity.  
The missing authority is explicit **Engineering Readiness**:

- what is complete,
- what is only provisional,
- what is physically unresolved,
- what is catalog unresolved,
- what is incompatible,
- what blocks final assembly.

Without that authority, phrases like "aplica la mejor" risk being interpreted as local optimization instead of system-level closure.

---

## 4) Readiness Language (target taxonomy)

Every relevant subsystem/entity should be classifiable with a normalized status:

- `DEFINED`
- `CALCULATED`
- `SIMULATED`
- `VALIDATED`
- `CATALOG_BOUND`
- `INCOMPLETE`
- `INCOMPATIBLE`
- `UNVERIFIABLE`

These statuses must be deterministic, evidence-backed, and computable from project state + catalog + simulation outputs.

---

## 5) Gap Model (target authority)

Introduce a formal gap contract as first-class engineering output:

```text
GAP-001
title: Motor SKU unresolved
severity: HIGH
blocks: propulsion_validation, bom_resolution
depends_on: []
evidence: [...]
next_actions: [...]
```

Minimum fields:

- `id`
- `title`
- `severity` (`HIGH|MEDIUM|LOW`)
- `domain` (propulsion, energy, control, integration, etc.)
- `blocks` (which validations/readiness gates are blocked)
- `depends_on` (gap graph edges)
- `evidence` (deterministic references)
- `recommended_next_step` (deterministic)

---

## 6) Target Readiness Output

Jarvis should eventually emit a compact engineering readiness summary:

```text
ENGINEERING READINESS

Requirements       PASS
Architecture       PASS
Mass               PASS
Structure          PASS
Propulsion         WARNING
Energy             WARNING
Electronics        INCOMPLETE
Control            INCOMPLETE
Sensors            INCOMPLETE
Communications     INCOMPLETE
Integration        INCOMPLETE
Catalog            WARNING
BOM                INCOMPLETE

PROJECT STATUS: NOT ASSEMBLY READY
```

This summary is not narrative-only; each line must map to deterministic criteria and evidence.

---

## 7) "Apply Best" Target Semantics

"Aplica la mejor" should mean:

1. Evaluate project objective + constraints + current state.
2. Query unresolved gaps and dependency graph.
3. Restrict candidate actions/configurations to feasible, unlocked options.
4. Score at system level (not component-only).
5. Apply only the best valid configuration.
6. Recompute readiness and show what changed.

Non-goal: selecting a single "best component" in isolation.

---

## 8) Proposed Evolution Phases

### ERF-1 — Readiness Foundation (first)

Scope:

- normalized readiness snapshot,
- formal gap registry,
- deterministic gap prioritization,
- continuity reading from readiness/gap authority.

Out of scope:

- full electrical chain solver,
- geometric fit/cabling model,
- full commercial BOM engine.

### ERF-2 — Dependency Hardening

Scope:

- first explicit dependency chain checks (at minimum `motor <-> esc <-> battery`),
- incompatibility states in readiness/gaps.

### Catalog/BOM Expansion (Impl C-aligned)

Scope:

- stronger SKU-resolution tracking across subsystems,
- BOM readiness (resolution, quantity, unresolved blockers).

### System-level Optimization

Scope:

- objective-aware configuration scoring tied to readiness closure,
- safe "aplica la mejor" at system level.

---

## 9) What This Vision Does Not Change Yet

- No new source of truth replaces ProjectState.
- No LLM authority over engineering next-step decisions.
- No implicit rewrite of existing acquisition/continuity contracts.
- No immediate changes to active roadmap priorities until an approved implementation contract exists.

---

## 10) Sync Protocol (when this document changes)

When this vision is updated, keep docs aligned with this order:

1. Update this file (`ENGINEERING_READINESS_VISION.md`).
2. If priorities change, update `docs/IMPLEMENTATION_TASKS.md` top section only.
3. If implementation contracts are approved, update `.jes/state/engineering_state.json`.
4. Only after code + tests land, update `docs/ARCHITECTURE.md` and `docs/system_map/*`.

This preserves clean separation between target and as-is.

