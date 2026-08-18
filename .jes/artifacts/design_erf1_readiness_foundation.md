# Design — ERF-1 Readiness Foundation

**Status:** **CLOSED — Engineer ratified 2026-08-18**  
**Type:** Design only. Zero product `src/` changes. Not an Implementation Contract.  
**Date:** 2026-08-18  
**Ratification:** Engineer locks absorbed — see §1 and §14  
**Next:** [implementation_contract_erf1.md](implementation_contract_erf1.md)
**Vision:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md)  
**Investigation:** [investigation_erf1_readiness_foundation.md](investigation_erf1_readiness_foundation.md) — **PASS**  
**Investigation contract:** [implementation_contract_erf1_investigation.md](implementation_contract_erf1_investigation.md)  
**Checkpoint base:** `checkpoint-continuity-polish` + `d224dc1` — **closes Continuity/CLI polish era; ERF-1 opens Engineering Readiness era**

---

## 0. Where this lives (document map)

Jarvis uses **two layers** on purpose:

| Layer | Path | Role |
|---|---|---|
| **Product vision (to-be)** | `docs/ENGINEERING_READINESS_VISION.md` | Stable target semantics; not as-is evidence |
| **Product as-is** | `docs/ARCHITECTURE.md`, `docs/system_map/*` | Implemented behavior only |
| **Execution queue** | `docs/IMPLEMENTATION_TASKS.md` | What to do now |
| **JES cycle state** | `.jes/state/engineering_state.json` | Active phase + gate |
| **JES artifacts** | `.jes/artifacts/*` | Investigation → design → contract → report → review |

**ERF-1 artifact chain (same pattern as G10 / Continuity Hardening):**

```text
docs/ENGINEERING_READINESS_VISION.md          ← product vision (to-be)
        │
        ▼
.jes/artifacts/implementation_contract_erf1_investigation.md
.jes/artifacts/investigation_erf1_readiness_foundation.md     ← PASS
.jes/artifacts/design_erf1_readiness_foundation.md           ← this file
        │
        ▼ (after ratification)
.jes/artifacts/implementation_contract_erf1.md                ← Cursor drafts for Claude
.jes/artifacts/implementation_report_erf1.md                  ← Claude
.jes/artifacts/implementation_review_erf1.md                  ← Cursor review
        │
        ▼ (after code lands)
docs/ARCHITECTURE.md + docs/system_map/*                      ← as-is updated
```

**Not yet created (optional, when IC is drafted):** `work_plan_erf1.md` — only if Engineer wants a separate phase plan like CLI polish had.

**Coherence check:** ERF-1 docs follow the same JES naming and placement as prior cycles. Vision lives in `docs/` (like `PHYSICAL_COMPONENT_CATALOG_V1.md`); cycle artifacts live in `.jes/artifacts/`. No duplication of as-is claims in the vision doc.

---

## 1. Locked ★ summary (authoritative)

Design order is **semantic first, DTO last**. Do not implement types before gap semantics are locked.

| ★ | Lock |
|---|---|
| **★1 — Readiness status semantics** | Per-subsystem `readiness.verdict` (`PASS`, `WARNING`, `INCOMPLETE`, `INCOMPATIBLE`, `UNVERIFIABLE`) is a **summary** derived from evidence + active gaps — not the primary artifact. `overall: ASSEMBLY_READY \| NOT_ASSEMBLY_READY` is a **derived rollup**, not the heart of ERF-1. |
| **★2 — Gap contract (central)** | **Gap registry is the core authority of ERF-1.** Readiness snapshot is its compressed view. Every gap is a deterministic derived entity with stable type id, severity, domain, `blocks[]`, `depends_on[]`, `evidence[]`, `recommended_next_step`. |
| **★3 — Evidence model** | Vision evidence states (`defined`, `calculated`, `simulated`, `validated`, `catalog_bound`, …) are **separate** from readiness verdicts. Never merge into a single label. |
| **★4 — Dependency model** | `depends_on[]` is explicit per gap type. A gap is unlockable only when all dependencies are resolved. No implicit dependency inference. |
| **★5 — Priority / ranking** | `top_gap` = first unlockable gap after deterministic sort: (1) unlockable only, (2) severity HIGH > MEDIUM > LOW, (3) **greater downstream-unblock impact first**, (4) stable `gap_id` lexicographic. Continuity consumes this; it does not re-rank. |
| **★6 — Existing-authority mapping** | Readiness Aggregator **composes** outputs from architecture, BOM/closure, requirements, simulation, phase authorities. It does **not** recompute their logic, persist a second ProjectState, or become primary authority over physics/BOM/sim truth. **ERF-1 is authoritative over gap aggregation, not over engineering facts.** |
| **★7 — No circularity** | **Forbidden:** `Continuity → Readiness → Continuity`. Readiness never reads `next_useful_step`. Flow: authorities → Readiness → gaps/snapshot/priority → Continuity → `next_useful_step`. |
| **★8 — No LLM gap inference** | **ERF-1 never creates a gap from LLM text.** Example: LLM says "quizá falta un ESC" → ❌ not a gap. Only: `components.esc = missing` (deterministic) → ✅ `GAP-ESC-NOT-DEFINED`. LLM interprets intent; Readiness owns engineering truth. |
| **★9 — Contract before Continuity surgery** | Gap contract + tests land **before** refactoring `project_continuity.py`. Continuity handoff is the last implementation slice. |
| **★10 — ERF-1 boundary** | No electrical chain solver (ERF-2), no full Impl C BOM engine, no `"aplica la mejor"` system optimizer. ERF-1 **prepares** that future authority; it does not implement it. |

---

## 2. Problem statement (why ERF-1)

Jarvis can produce a design that **calculates and simulates coherently** while still being **not assembly-ready**. Today, signals of incompleteness are distributed across:

- architecture block progress (`orchestrator`),
- BOM completeness (`project_closure`),
- physical requirements + catalog gap (`orchestrator.build_startup_context`),
- simulation verdict (`simulator`),
- next-step ranking (`project_continuity`).

Continuity currently **synthesizes** importance from these dispersed signals. ERF-1 introduces one deterministic aggregation surface so the system can answer:

> **"¿Qué le falta a este proyecto para ser ensamblable?"**

without a second state store and without circular dependency on Continuity's own output.

---

## 3. Authority model (binding)

### 3.1 Layer diagram

Readiness **coordinates** existing authorities; it does **not** replace them.

```text
                    ProjectState
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   Architecture      Component/BOM   Requirements
     authority         authority       authority
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                    Simulation
                     authority
                         │
                         ↓
              ┌─────────────────────┐
              │  READINESS         │
              │  AGGREGATOR        │
              │                     │
              │  gaps (core)       │
              │  snapshot (summary)│
              │  dependencies      │
              │  priority          │
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
        Continuity              CLI / Status
              ↓
        next_useful_step
```

### 3.2 Forbidden pattern (★7)

```text
❌ Continuity → Readiness Aggregator → Continuity
```

Readiness Aggregator inputs are **only**:

- `ProjectState`
- outputs of the five existing authorities listed above
- deterministic catalog queries already used today (e.g. motor catalog gap helpers)

Readiness Aggregator inputs are **never**:

- `continuity.next_useful_step`
- `continuity.next_useful_why`
- any prior Continuity ranking

### 3.3 What Readiness Aggregator is / is not

| Is | Is not |
|---|---|
| Thin deterministic projection | Conversation Engine / Decision Engine |
| Gap registry + readiness snapshot | Second ProjectState |
| Dependency ordering over gaps | Duplicate of `build_project_continuity` ranking logic |
| Input to Continuity (post Slice D) | LLM-narrated gap invention |

---

## 4. Target user-facing shape (what ERF-1 must enable)

The primary answer to *"¿qué le falta?"* is **TOP GAPS**, not a boolean:

```text
ENGINEERING READINESS

Requirements       PASS
Architecture       PASS
Structure          PASS
Propulsion         WARNING
Energy             PASS
Control            INCOMPLETE
Catalog            WARNING
BOM                INCOMPLETE

PROJECT STATUS: NOT ASSEMBLY READY

TOP GAPS

GAP-MOTOR-CATALOG-UNRESOLVED
  Motor SKU unresolved
  MEDIUM — blocks: catalog, bom
  depends_on: []
  next: list_motors / explore_design_space

GAP-BOM-MISSING-COMPONENT (flight_controller)
  Flight controller not defined
  HIGH — blocks: control, bom
  depends_on: []
  next: define_component
```

**ERF-1 snapshot subsystems (v1 only):** `requirements`, `architecture`, `structure`, `propulsion`, `energy`, `control`, `catalog`, `bom`.  
**Do not show** `electronics`, `communications`, `integration` until ERF-2 introduces real authority — no artificial `INCOMPLETE` lines.

Snapshot lines are **derived from gaps + evidence**. `PROJECT STATUS` is **derived from unresolved HIGH gaps + subsystem verdicts** — not the other way around.

---

## 5. Data contract (semantic layers)

### 5.1 Top-level shape (DTO comes after semantics — ★2)

```text
EngineeringReadinessResult:
  gaps: Gap[]                      # PRIMARY — deterministic registry
  prioritized_gaps: Gap[]
  top_gap: Gap | None
  subsystems: { key: SubsystemReadiness }   # SUMMARY
  overall: ASSEMBLY_READY | NOT_ASSEMBLY_READY   # ROLLUP
```

### 5.2 Subsystem line (evidence + verdict separated — ★3)

Each subsystem entry (e.g. `propulsion`, `energy`, `control`, …) MUST carry both layers:

```yaml
propulsion:
  evidence:
    defined: true
    calculated: true
    simulated: true
    validated: true
    catalog_bound: false
    # optional future: incompatible: false
  readiness:
    verdict: WARNING               # PASS | WARNING | INCOMPLETE | INCOMPATIBLE | UNVERIFIABLE
    blocked_by_gap_ids: [GAP-001]
```

**Evidence flags** map to Vision taxonomy (`DEFINED`, `CALCULATED`, …) as booleans or enumerated sub-states — they describe **what is known**, not whether the subsystem is closed.

**Readiness verdict** maps subsystem closure for assembly readiness — it describes **whether the subsystem is closed enough** given evidence + gaps.

Do **not** collapse `catalog_bound: false` into `readiness: WARNING` without retaining the evidence layer. The user must be able to see **why** WARNING.

### 5.3 Overall verdict rule (derived rollup — ★1)

```text
PASS              → may contribute to ASSEMBLY_READY
WARNING           → may contribute ONLY if warning_type ∈ ACCEPTED_WARNING_TYPES (closed list)
INCOMPLETE        → never ASSEMBLY_READY
INCOMPATIBLE      → never ASSEMBLY_READY
UNVERIFIABLE      → never ASSEMBLY_READY

ASSEMBLY_READY  iff  no unresolved HIGH-severity gaps
                 AND every subsystem verdict ∈ {PASS} ∪ ACCEPTED_WARNING_TYPES
NOT_ASSEMBLY_READY otherwise
```

**ERF-1 `ACCEPTED_WARNING_TYPES` (closed in Implementation Contract):**

| warning_type | When | Subsystem |
|---|---|---|
| `CATALOG-GAP-DEMOTED-POST-PASS` | G9-B class: sim PASS + declared `per_motor_max_thrust_n >= thrust_per_motor_needed_n` + catalog query returns 0 matches | `catalog` (may also affect `propulsion` line) |

No narrative "probably OK" WARNING — each acceptable WARNING must have a deterministic rule.

---

## 6. Gap registry (★2 — core of ERF-1)

### 6.1 Gap entity (minimum fields)

```yaml
gap_id: GAP-001
title: Motor SKU unresolved
severity: HIGH                    # HIGH | MEDIUM | LOW
domain: propulsion                # propulsion | energy | structure | control | catalog | bom | integration | ...
blocks:
  - propulsion.catalog
  - bom
  - assembly
depends_on: []                    # gap_ids that must close first
evidence:
  - source: project_closure.build_component_bom
    fact: motors.present && motors.completeness >= medium
  - source: orchestrator.build_startup_context
    fact: motor_catalog_gap.active && catalog_matches == []
  - source: simulator
    fact: thrust_requirement_met == true
recommended_next_step:
  action: list_motors             # deterministic action key — not free text
  params: {}
```

### 6.2 Gap creation rules (must be explicit in Implementation Contract)

Before writing DTOs or code, the Implementation Contract must answer for **each gap type**:

- ¿Cuándo existe un gap?
- ¿Cuándo es `HIGH` vs `MEDIUM` vs `LOW`?
- ¿Qué significa que un gap "bloquea" algo?
- ¿Cómo se determina `depends_on[]`?
- ¿Cuál gana como `top_gap`?

Each gap type shipped in ERF-1 must document:

1. **Trigger** — which existing authority outputs must be true.
2. **Evidence refs** — which computed facts are copied (not reinterpreted by LLM).
3. **Severity** — fixed per gap type (not contextual narration).
4. **blocks[]** — which readiness lines / overall gates this gap affects.
5. **depends_on[]** — other gap_ids (empty if root).
6. **recommended_next_step** — maps to an existing deterministic path (`list_motors`, `explore_design_space`, acquisition target, etc.).

**Forbidden:** gaps whose only evidence is a string template with no backing computed fact.

### 6.3 Prioritization (deterministic — ★5)

After gap extraction:

```text
1. Filter to gaps whose depends_on[] are all resolved (unlockable).
2. Sort unlockable gaps:
   a) severity HIGH > MEDIUM > LOW
   b) greater downstream-unblock impact first (more readiness lines unblocked wins)
   c) stable tiebreak: gap_id lexicographic
3. top_gap = first after sort
```

`depends_on[]` values are **declared per gap type in the contract** — never inferred from domain logic ("motor before battery because obvious").

Continuity (Slice D) reads `top_gap.recommended_next_step` — it does **not** re-rank.

### 6.4 Initial gap catalog (ERF-1 — minimum viable set)

Implementation Contract must implement at least these gap types (derived from today's real CLI pain):

| Gap type | Approx. source today | Notes |
|---|---|---|
| `GAP-MOTOR-CATALOG-UNRESOLVED` | `motor_catalog_gap` in startup context | Even when sim PASS (G9-B class) |
| `GAP-ARCH-BLOCK-INCOMPLETE` | `_next_pending_block` / block progress | Architecture not closed |
| `GAP-BOM-MISSING-COMPONENT` | `build_component_bom.missing` | Per required component key |
| `GAP-BOM-INCOMPLETE-COMPONENT` | `build_component_bom.incomplete` | Declarative-only / low completeness |
| `GAP-SIM-NOT-PASS` | `simulator.status != pass` | Physical validation blocker |
| `GAP-REQUIREMENTS-UNMET` | derived requirements vs calc/sim | When explicit requirement failed |

ERF-1 does **not** ship gap types for ESC/FC/integration/electrical incompatibility — those belong to ERF-2. Do **not** show `electronics` / `communications` / `integration` subsystem lines without authority.

---

## 7. Mapping existing authorities → evidence flags (★6)

Implementation Contract will pin exact predicates. Design intent:

| Evidence flag | Primary sources |
|---|---|
| `defined` | `classify_component` ∈ {declared, defined, …} / block progress |
| `calculated` | relevant params present in calc output / `CalculationEngine` ran |
| `simulated` | simulation result exists for project |
| `validated` | `simulator.status == pass` for subsystem-relevant checks |
| `catalog_bound` | `ComponentSpec.catalog_ref` set and not invalidated |

Verdict derivation (per subsystem) composes evidence + active gaps blocking that subsystem line.

---

## 8. Continuity handoff (★9 — last slice only)

### 8.1 Before ERF-1

Today: `build_project_continuity()` owns ranking logic internally.

### 8.2 After ERF-1 (target)

```text
readiness = build_engineering_readiness(project_state, authority_outputs)
continuity = build_project_continuity(project_state, readiness=readiness)
```

Continuity responsibilities **after** ERF-1:

- Format `situation` / `evidence` / `next_useful_step` for human surface.
- Map `readiness.top_gap.recommended_next_step` to user-facing copy.
- Preserve existing honesty notes (energy model, catalog gap demotion rules already shipped).

Continuity responsibilities **removed** from Continuity (moved to Readiness):

- Ad-hoc gap ranking across motor_catalog_gap / BOM / arch / sim branches.
- Inventing next step without gap backing.

### 8.3 Regression guard

All existing continuity hardening tests (G9-B, G19, FN-023, etc.) must pass after Slice D. Readiness must **explain** existing behavior, not silently change product semantics in Slice A–C.

---

## 9. Design order vs implementation order

### 9.1 Design closure order (this document — semantic first)

```text
1. Readiness status semantics        (★1)
2. Gap contract                      (★2) ← central
3. Evidence model                    (★3)
4. Dependency model                  (★4)
5. Priority / ranking                (★5)
6. Existing-authority mapping        (★6)
7. Continuity handoff                (★9)
```

### 9.2 Implementation slices (for Claude — future contract)

Map design sections to code slices. **Gap semantics before DTO scaffold.**

| Slice | Design input | Deliverable | Depends on |
|---|---|---|---|
| **1 — Gap contract + rules** | §6 | Gap types, creation rules, `depends_on`, prioritization — tested in isolation | — |
| **2 — Evidence + readiness mapping** | §5, §7 | Subsystem evidence flags + verdict derivation from authorities | 1 |
| **3 — Readiness aggregator** | §3, §5 | `build_engineering_readiness()` composing authorities; no Continuity input | 1, 2 |
| **4 — Continuity handoff** | §8 | `build_project_continuity(..., readiness=...)`; remove duplicated ranking | 3 |
| **5 — CLI/status surface** | §4 | TOP GAPS + snapshot on `estado` / startup | 3 |

Suggested module: `src/jarvis/core/engineering_readiness.py` (single projection module).

**Binding:** Slices 1→3 before Slice 4. Do not patch Continuity first.

---

## 10. Explicit non-goals (ERF-1)

- `"aplica la mejor"` system-level optimizer (prepare authority only).
- Motor↔ESC↔battery compatibility solver (ERF-2).
- Geometric fit, cabling, connectors (integration phase).
- Full SKU BOM with quantities/pricing (Impl C).
- New LLM authority for gap detection.
- Conversation Engine / Decision Engine.
- Rewriting acquisition target authority.

---

## 11. Acceptance probes (design-time — for Implementation Contract §tests)

1. **Sim PASS, NOT assembly ready:** project with `simulation=pass` but missing control/comms → `overall=NOT_ASSEMBLY_READY`, evidence shows `simulated/validated` true for physics, subsystems show `INCOMPLETE`.
2. **Two-layer explainability:** propulsion line shows `catalog_bound: false` AND `readiness: WARNING` AND `GAP-MOTOR-CATALOG-UNRESOLVED`.
3. **No circularity:** unit test proves Readiness builder accepts no Continuity input; mock Continuity receives readiness output.
4. **Deterministic ranking:** same ProjectState → same `top_gap` and order across runs.
5. **Continuity parity:** post-Slice D, G9-B demotion + G19 CTA paths still pass existing tests.
6. **Zero LLM:** readiness/gap snapshot computable with LLM disabled.

---

## 12. Product phase transition (context)

```text
G3 → G10 → Continuity Hardening → CLI Polish → G20 → checkpoint limpio
══════════════════════════════════════════════════════════════════════
                    ENGINEERING READINESS (new era)
══════════════════════════════════════════════════════════════════════
ERF-1 → ERF-2 → Impl C / BOM → System-level optimization ("aplica la mejor")
```

Do not accumulate G21/G22-style micro-fixes as the main track. Residual CLI gaps (G17/G14/G13) may run in parallel but must not block ERF-1 design ratification.

---

## 13. Evolution after ERF-1 (not in scope)

```text
ERF-1   → ¿Qué falta? ¿Qué bloquea? ¿Cuál gap desbloqueable?
ERF-2   → ¿Qué configuraciones son compatibles? (motor↔esc↔battery)
Impl C  → ¿Qué SKUs reales cierran el sistema?
Opt     → ¿Cuál es la mejor configuración GLOBAL? ("aplica la mejor")
```

---

## 14. Engineer decisions — CLOSED (2026-08-18)

| # | Decision | Verdict |
|---|---|---|
| 1 | **WARNING acceptance** | Only via closed `ACCEPTED_WARNING_TYPES`; G9-B `CATALOG-GAP-DEMOTED-POST-PASS` is the sole ERF-1 entry |
| 2 | **Subsystems v1** | Eight lines only: `requirements`, `architecture`, `structure`, `propulsion`, `energy`, `control`, `catalog`, `bom`. No `electronics` / `communications` / `integration` yet |
| 3 | **Gap IDs** | Stable type IDs (`GAP-MOTOR-CATALOG-UNRESOLVED`, …); instance key in evidence when multiple (e.g. component_key) |
| 4 | **Persistence** | Derived on read — no `readiness.json` or parallel persisted state |
| 5 | **Priority tiebreak** | Greater downstream-unblock impact first (not "fewer") |
| 6 | **depends_on** | Explicit per gap type in contract only — no implicit inference |
| 7 | **Gap catalog** | Six types only — do not expand in ERF-1 |

---

## 15. Next step in JES pipeline

```text
ENGINEERING_READINESS_VISION     ✅
ERF-1 INVESTIGATION              ✅ PASS
ERF-1 DESIGN                     ✅ CLOSED (Engineer ratified)
Implementation Contract          ✅ implementation_contract_erf1.md — send to Claude
Implementation (Claude)          ←
Tests + CLI                      ←
checkpoint-erf1                  ←
```
