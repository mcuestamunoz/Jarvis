# Engineering Readiness Vision

**Status:** Active (ERF-1 ✅, ERF-2 ✅, Project Closure arc ✅ — IC 1/2/3 closed, §11)  
**Type:** Vision / To-be  
**Date:** 2026-08-31 (updated post-IC-3 policy sync — Project Closure / Assembly Ready v1)

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

Target (full vision — not all subsystems implemented yet):

```text
ENGINEERING READINESS

Requirements       PASS
Architecture       PASS
Mass               PASS
Structure          PASS
Propulsion         WARNING
Energy             WARNING
Electronics        INCOMPATIBLE    ← ERF-2
Control            INCOMPLETE
Sensors            INCOMPLETE
Communications     INCOMPLETE
Integration        INCOMPLETE
Catalog            WARNING
BOM                INCOMPLETE

PROJECT STATUS: NOT ASSEMBLY READY
```

As of ERF-2, the implemented subset is 9 subsystems: `requirements`, `architecture`, `mass`, `structure`, `propulsion`, `energy`, `electronics`, `catalog`, `bom`. The `INCOMPATIBLE` verdict is new in ERF-2 and requires deterministic evidence (★3 gate).

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

### ✅ ERF-1 — Readiness Foundation (2026-08-18)

> Tag: `checkpoint-erf1` (`63c427b`). CLOSED.

Delivered:

- normalized readiness snapshot (8 subsystems),
- formal gap registry (6 gap types),
- deterministic gap prioritization,
- continuity reading from readiness/gap authority (C-108 partial — Slice 4b deferred).

Out of scope (deferred):

- full electrical chain solver → delivered in ERF-2,
- geometric fit/cabling model,
- full commercial BOM engine.

### ✅ ERF-2 — Dependency Hardening (2026-08-19)

> Tag: `checkpoint-erf2` (`9af0cc9`). CLOSED.

Delivered:

- `electrical_compatibility.py` — pure deterministic checks (ESC presence, per-motor ESC vs motor, battery discharge, prop↔motor match),
- 4 new gap types (`GAP-ESC-MISSING`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`),
- `INCOMPATIBLE` verdicts with ★3 deterministic-evidence gate,
- 9 subsystems (+ `electronics`),
- `_INCOMPATIBLE_VERDICT_SUBSYSTEMS` for narrowed verdict impact (Energy not INCOMPATIBLE from ESC-only gaps),
- ESC acquisition UX: aliases, prompt, routing, block label, out-of-scope explicit save.

Out of scope (deferred):

- KV/voltage gap,
- H5 ESC catalog,
- Slice 4b full Continuity handoff,
- dedupe gaps BOM/ESC.

### ✅ Catalog / BOM expansion (Impl C + Impl D + pick UX) — CLOSED

> Tags: `checkpoint-impl-c`, `checkpoint-impl-d`, `checkpoint-propeller-catalog-bind` (`v0.3.0`), `checkpoint-battery-catalog-bind-ux`.

Delivered:

- catalog-aware DSE + thrust bridge (Impl C),
- BOM `[sku]` / `sku_resolved` / quantity (Impl D; propeller `has_propeller` branch IC 3),
- live catalog pick UX for motor, propeller, battery.

Out of scope (deferred): G24 DSE apply-by-index · H5 ESC catalog · frame SKU catalog.

### ✅ Project Closure / Assembly Ready v1 — CLOSED

> Tag: `checkpoint-closure-policy`. Product contract: **§11** (same document). IC 1 Requirements · IC 2 Battery/G27 · IC 3 policy sync + propeller display fix.

### System-level Optimization — OPEN

Scope:

- objective-aware configuration scoring tied to readiness closure,
- safe "aplica la mejor" at system level (§7 target semantics).

---

## 9) What This Vision Does Not Change Yet

- No new source of truth replaces ProjectState.
- No LLM authority over engineering next-step decisions.
- No implicit rewrite of existing acquisition/continuity contracts — Continuity remains next-step copy authority; see [`PROJECT_CONTINUITY.md`](./PROJECT_CONTINUITY.md).
- **Execution queue** (what to implement next) lives in [`IMPLEMENTATION_TASKS.md`](./IMPLEMENTATION_TASKS.md) — not in §8 phase history above. Delivered phases (ERF-1/2, Catalog Impl C/D, Project Closure §11) are closed; new work requires a new investigation/IC, not edits to §11 without Engineer approval.

---

## 10) Sync Protocol (when this document changes)

When this vision is updated, keep docs aligned with this order:

1. Update this file (`ENGINEERING_READINESS_VISION.md`).
2. If priorities change, update `docs/IMPLEMENTATION_TASKS.md` top section only.
3. If implementation contracts are approved, update `.jes/state/engineering_state.json`.
4. Only after code + tests land, update `docs/ARCHITECTURE.md` and `docs/system_map/*`.

**Project Closure arc (2026-08-31):** step 4 completed post-`checkpoint-closure-policy` — see `ARCHITECTURE.md` Project Closure note, `system_map/` deltas (C-030/C-082/C-107 detail, acquisition/continuity/state/authority/LLM maps).

---

## 11) Project Closure — Assembly Ready v1 (IC 3 policy sync, 2026-08-31)

> Ratifies, into this vision doc, the product-level closure contract established by
> `.jes/artifacts/investigation_report_project_closure_assembly_ready.md` and implemented
> across **IC 1** (Requirements Closure), **IC 2** (Battery Catalog UX + G27 Hardening), and
> **IC 3** (this sync + the propeller `sku_resolved` display fix). This section documents a
> **ratified product contract** — distinguish it from "code changed in IC 3," which was only
> the one-line `_bom_sku_resolved` propeller branch (§11.7) plus this doc. No readiness rollup,
> gap, or verdict logic changed in IC 3.

### 11.1 Rollup rule (as-implemented reference, unchanged by this arc)

`build_engineering_readiness` (`engineering_readiness.py` → `_derive_overall`) computes
`ASSEMBLY_READY` from exactly two conditions, both still true post-arc:

```text
ASSEMBLY_READY  ⟺  zero HIGH-severity gaps anywhere
                AND every one of the 9 subsystems is PASS,
                    or the single accepted WARNING type
                    (CATALOG-GAP-DEMOTED-POST-PASS, catalog/propulsion only — ★8, unchanged)
```

9 subsystems: `requirements`, `architecture`, `structure`, `propulsion`, `energy`,
`electronics`, `control`, `catalog`, `bom`. This arc closed real blockers reachable under that
rule — it never widened or narrowed the rule itself.

### 11.2 Snapshots A / B

Two ratified, honestly-reachable target shapes for a closed project — neither requires
inventing a component or fabricating a catalog claim (★1):

| | **Snapshot A — Freeform-tolerant v1** | **Snapshot B — Catalog-evidence-strong** |
|---|---|---|
| Rollup | All 9 subsystems PASS (or accepted WARNING) | Same rollup rule |
| Motors / propellers / battery | May be honestly freeform (`catalog_ref=None`, non-low completeness) | Catalog-bound where the library supports it (motor + propeller + battery) |
| ESC / frame / flight_controller / sensors | Freeform only in both snapshots — no catalog exists for these families (§11.3) | Same |
| Requirements | Satisfied via a numeric constraint **or** ★3(b) explicit-none (§11.4) | Same |
| Reachable today | Yes — zero code prerequisites beyond this arc | Yes — IC 2's battery-bind UX is the last piece that made this fully live-reachable via CLI, not just test-callable |

Snapshot B is strictly **evidence-stronger**, never **rollup-stronger** — the same 9-subsystem
PASS rule governs both; Snapshot B simply has more `catalog_bound` truth behind it. Battery
catalog binding is **optional** for Snapshot A (★7) — a freeform battery with real declared
`battery_capacity_wh` already satisfies the `energy` subsystem.

### 11.3 Family policy matrix (★7, ratified)

| Family | Catalog data | Bind API | Live pick UX | Policy |
|---|---|---|---|---|
| motors | `library/motores/_datos.json` (22) | `bind_motor_from_catalog` | Yes | catalog-strong **optional** |
| propellers | `library/helices/_datos.json` (16) | `bind_propeller_from_catalog` | Yes (v0.3.0) | catalog-strong **optional** |
| battery | `library/baterias/_datos.json` (10) | `bind_battery_from_catalog` | Yes (IC 2) | catalog-strong **optional** |
| esc | none | none | none | **freeform_ok only** — `CatalogRef.family` schema doesn't even include `"esc"`; H5 ESC catalog is a separate, deferred effort |
| frame | materials density only, not a SKU catalog | none | none | **freeform_ok only** — frame SKU catalog deferred |
| flight_controller | none | none | none | **freeform_ok only** |
| sensors | none | none | none | **freeform_ok only** |

No family in the "freeform_ok only" row blocks `ASSEMBLY_READY` by being freeform — a
non-low-completeness declared component is sufficient for its subsystem to reach PASS
(`classify_component` tier `declared` or `defined`, never gated on `catalog_ref`).

### 11.4 Requirements semantics (IC 1)

- `requirements.defined` is satisfied by **either** a parsed numeric constraint
  (`autonomy_min` / `max_weight_kg`) **or** an explicit, closed-list "no constraint" statement
  (★3(b) — `"no"`, `"ninguna"`, `"sin restricciones"`, etc.). Never by a fabricated numeric
  key — the explicit-none branch leaves `parsed_constraints == {}`.
- An unachievable stated constraint surfaces an honest `GAP-REQUIREMENTS-UNMET` (HIGH) instead
  of silently passing or silently failing to update — `NOT_ASSEMBLY_READY` for the right,
  visible reason.
- Mid-session restatement of the project-level `restrictions` string (G26) is a live, working
  write path — it re-derives `parsed_constraints` on every update.

### 11.5 Energy / battery (IC 2)

- `bind_battery_from_catalog` + `set_battery_component` is the sole battery bind path — live
  in the CLI (component wizard "ayúdame a elegir", IDLE fallback after motor/propeller) since
  IC 2, not just test-callable.
- Catalog bind is **evidence-strong, not required** — freeform battery declaration already
  satisfies `energy` subsystem PASS (§11.2 Snapshot A).
- G27 (free-text `"LiPo 6S 10000mAh"` → silent `6 Wh`) is hardened: `semantic_intent_adapter`
  resolves chemistry/cell-count text deterministically (`mAh × cells × 3.7V`) or refuses,
  scoped to `battery_capacity_wh` only — every other iterate variable's parsing is unchanged.
- **Ratified, not to be changed without a new contract:** a battery-only catalog pick does
  **not** re-invoke `set_motor_component`. Verified in IC 2 that doing so can *downgrade* an
  already-resolved `exact_operating_point` to `fallback_operating_point` when the real battery
  voltage falls outside a curated exact row's tolerance — an energy-domain action must never
  silently regress propulsion evidence the user didn't touch.

### 11.6 S0 → S1 → S2 (investigation §10, summary)

```text
S0: PHYSICS PASS + BOM INCOMPLETE + NOT ASSEMBLY READY   (stub components remain)
S1: PHYSICS PASS + BOM COMPLETE  + NOT ASSEMBLY READY    (declare/bind remaining components;
                                                            zero catalog required)
S2: PHYSICS PASS + BOM COMPLETE  + ASSEMBLY READY        (+ requirements satisfied — §11.4)
```

S0→S1 (component completeness) and S1→S2 (requirements) are **independent levers** — neither
reads the other's state. They can be closed in either order or in parallel.

### 11.7 Propeller `sku_resolved` (IC 3, ★6 — the only code change in this cut)

`project_closure._bom_sku_resolved` re-checks a bound SKU against the live library before
ever claiming `[sku]` in a BOM line (motor/battery via `has_motor`/`has_battery`) — the
propeller branch (`has_propeller`) was missing since before the v0.3.0 propeller-bind UX
shipped, so a genuinely bound, resolving propeller displayed the honest-uncertainty marker
`(SKU sin resolver)` as if it were unresolved. Fixed as a one-line addition; **display-only** —
`sku_resolved` is never read by gap builders or subsystem verdict derivation, confirmed
unchanged by this fix.

### 11.8 Deferred (explicit, not silently dropped)

| Item | Status |
|---|---|
| **G24** — DSE apply-by-index / catalog-row scoring | Deferred. Confirmed not a closure prerequisite — identity-display debt (stale `.name` after `catalog_ref` clears), not a rollup blocker. |
| **H5 — ESC catalog** | Deferred. Requires a `CatalogRef.family` schema change (currently `Literal["motor","battery","propeller"]`) before any bind path is even possible. |
| **Frame SKU catalog** | Deferred. Materials density (`library/materiales/`) is a different mechanism than a frame-as-SKU bind and was never in scope for this arc. |
| **Conversation Engine / Step D** | Deferred. Out of scope for the entire closure arc per the original investigation contract. |
| **`catalog_bound` → subsystem verdict wiring** | Deferred, not rejected. `SubsystemEvidence.catalog_bound` remains write-only (computed, never read by `_derive_subsystem_verdict`). Would be a rollup-semantics change requiring its own ★ decision — not assumed by this arc. |

**Project Closure arc status: COMPLETE** as of IC 3 (this section). ERF-1/ERF-2 remain ✅
unchanged; this section is additive, not a revision of §8's phase history.

