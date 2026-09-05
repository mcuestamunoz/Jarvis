# Engineering Readiness Vision

**Status:** Active (ERF-1 ✅, ERF-2 ✅, Project Closure ✅ §11; Claim Hygiene ✅, Control Parity ✅, Structure Foundations ✅, Structure Catalog Foundation IC-1→IC-3 ✅, Structure honesty `PASS *` ✅, Structure B Parts Graph Fase 1 ✅, G-N1 ✅, IDLE rebind B2+B3 ✅, arm `thickness_mm` B2 ✅, plate multiplicity B2 ✅ — §8)  
**Type:** Vision / To-be  
**Date:** 2026-09-05 (release **v0.3.8** @ suite **2294**; Structure smoke ACCEPT; Prop/Energy = HD-004 wall; System Optimization **deferred** until pain)

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

Out of scope (deferred): G24 DSE apply-by-index · H5 ESC catalog · frame SKU catalog **bind** (schema+seed landed — see Structure Catalog Foundation IC-1 below).

### ✅ Project Closure / Assembly Ready v1 — CLOSED

> Tag: `checkpoint-closure-policy`. Product contract: **§11** (same document). IC 1 Requirements · IC 2 Battery/G27 · IC 3 policy sync + propeller display fix.

### ✅ Claim Hygiene under ASSEMBLY READY — CLOSED (2026-09-04)

> Suite: **2160**. `.jes/artifacts/investigation_report_claim_hygiene_assembly_ready.md` / `implementation_report_claim_hygiene_assembly_ready.md`.

Delivered:

- `project_continuity.margin_claim_weak(sim)` — PASS + `quality=="risky"` or an active `low_margin`/`high_actuator_load`/`low_force_to_weight_ratio` warning no longer says "Diseño validado en simulación (PASS)"; locked situation sentence instead. Resolves H5/C-081 (`system_map/MISMATCHES.md`).
- CLI `Por qué:` line humanizes known warning codes via `WARNING_SHORT`/`WARNING_MESSAGES` (adapter-only; Continuity keeps the raw code).
- CLI `PROJECT STATUS: ASSEMBLY READY` gains one `NOTE: margen ajustado...` line when the backing simulation is margin-weak (reads a thin precomputed `margin_claim_weak` flag from `build_startup_context`).

Out of scope (deferred): a general "PASS + any live gap type" audit of Continuity's situation branch (only margin/quality was proven and fixed here — Structure Foundations below separately closed the frame-class instance) · unifying the four independent margin-threshold constants across `simulator.py`/`reasoning_layer.py`/`suggestion_engine.py`/`goal_planner.py` (cited, not touched) · weak-OP-evidence claim language (`prop_energy_block_closure` not wired into Continuity — named N4, its own later thread) · changing `_derive_overall`/`ASSEMBLY_READY` eligibility (not needed — copy-only fix).

### ✅ Control Parity (claim copy) — CLOSED (2026-09-04)

> Suite: **2164**. `.jes/artifacts/investigation_report_control_parity.md` / `implementation_report_control_parity.md`.

Delivered:

- CLI readiness block marks `Control` with `PASS *` + one footnote (`* Control: declaración — sin física de control`) whenever the verdict is `PASS` — naming, in copy only, that `_control_evidence`'s four flags (`defined`/`calculated`/`simulated`/`validated`) never reflect anything control-specific (no control-loop/PID/fusion/failsafe computation exists anywhere in the codebase; `validated` borrows the unrelated thrust-simulation pass/fail, same pattern as every other subsystem).
- BOM `flight_controller` line gains an identity-only suffix (`(high — identidad, sin dato físico)`) when it reaches the `defined` bucket via brand/model name recognition alone (`"model"` is a `_MEASURABLE` string-identity field, not a physics quantity).

Out of scope (deferred): ERF `_control_evidence`/`_derive_subsystem_verdict` honesty (investigated and explicitly rejected — making `validated` genuinely control-specific would make `PASS` structurally unreachable for control today, flipping `ASSEMBLY_READY` for virtually every real project; named as a future Engineer ★ decision, not a default) · sensor/FC catalog (not authorized; no catalog was proven necessary to fix the identified over-claim) · control-loop physics.

### ✅ Structure Foundations (claim copy) — CLOSED (2026-09-04)

> Suite: **2171**. `.jes/artifacts/investigation_report_structure_foundations.md` / `implementation_report_structure_foundations.md`.

Delivered:

- BOM `frame` line gains a suffix (`— compatibilidad de clase nivel A pendiente` / `— clase incompatible nivel A`) when a live `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` blocks `structure` — closes the disagreement where `_frame_completeness` (mass+material only, never reads `size_class_inch`) let a frame show `✓ ... (high)` while the Gap Registry already said `structure` was `INCOMPLETE`.
- Continuity situation gains `_frame_class_gap_live(readiness)` (mirrors `margin_claim_weak`'s shape) — same locked sentence for both gap types, closing the same "situation says validated, next-step names the problem" contradiction H5 fixed for margin, now for frame-class.
- Confirmed (not fixed — already correct): architecture `n/n` counters and the two `_block_progress_status` copies were already honestly gated on frame-class via the one shared `frame_size_blocks_structure_complete` predicate; `get_block_in_progress_reason`'s two-value reason enum turned out not to apply to `structure` at all (it's special-cased to `frame_next_missing_question` directly).

Out of scope (deferred): CAD/FEA/geometric fit / tip-clearance physics. Frame catalog bind+assist and declared part graph shipped later the same day — see Structure Catalog Foundation IC-2/IC-3 and Structure B below.

### ✅ Structure Catalog Foundation — IC-1 (schema + seed) — CLOSED (2026-09-04)

> Suite: **2177**. `.jes/artifacts/investigation_report_structure_catalog_foundation.md` / `implementation_report_structure_catalog_foundation_ic1.md`.

Delivered:

- `CatalogRef.family` gains `"frame"`.
- `FrameSpec` + `get_frame`/`has_frame`/`list_frames` in `ComponentLibrary`, mirroring `EscSpec`'s shape exactly.
- `library/frames/_datos.json` — 4 real, sourced seed rows (2 distinct size classes), each with `source_url`/`source_note`/`identity_status:"verified"`.

Investigation finding (why bind was not “new physics”): `set_frame_material` already writes declared mass into `structure_mass_override_kg` — a frame SKU’s mass is numerically identical in effect to free-text. Binding adds identity/traceability, not a new calculation.

### ✅ Structure Catalog Foundation — IC-2 + IC-3 — CLOSED (2026-09-04)

> Suites: **2188** (IC-2) · **2197** (IC-3).  
> Reports: `implementation_report_structure_catalog_foundation_ic2.md` / `_ic3.md`.

Delivered:

- IC-2: `bind_frame_from_catalog`, writer `catalog_ref=`, BOM `sku_resolved` for frame, diverge (mass/class/override).
- IC-3: `frame_catalog_assist`, offer/apply, acquisition-brief CTA; free-text declare intact.
- `catalog_bound` still **not** wired into Structure PASS / `_derive_subsystem_verdict`.

### ✅ Structure honesty (`PASS *`) — CLOSED (2026-09-04)

> Suite: **2200**. `.jes/artifacts/implementation_contract_structure_honesty_pass_star.md`.

Delivered:

- CLI readiness marks `Structure PASS *` with footnote  
  `* Structure: identidad / clase nivel A — sin geometría de chasis` (blanket, same posture as Control).
- ERF predicates / Continuity / BOM unchanged by this IC.

### ✅ Structure B Parts Graph Fase 1 + G-N1 — CLOSED (2026-09-04)

> Suites: **2223** (graph) · **2229** (G-N1).  
> Contracts: `implementation_contract_structure_b_parts_graph.md`,  
> `implementation_contract_structure_b_gn1_freetext_root_parts.md`.

Delivered:

- `ComponentSpec.parent_key` — first intra-project parent/child precedent; children are `frame_arm` / `frame_plate`(+ ordinal `frame_plate_2`… when curated) / `frame_cage` / `frame_standoff` with `parent_key="frame"`.
- Declared-only `configuration` (closed vocab) + `wheelbase_mm` on the frame root; part nodes carry optional `count`/`material` (arms also `thickness_mm`; plates also curated `label`/`thickness_mm`).
- BOM: children never top-level peers; display-only `└` sub-lines under `frame`.
- Catalog bind/assist upserts part children from seed (materials, arm thickness, curated plates — see below).
- **G-N1:** one free-text message may declare root + parts  
  (`"fibra 450g, 4 brazos carbono, jaula titanio"`); parts-only follow-up does not overwrite root material. Free-text remains **one node per part type** (no ordinal multi-plate parsing).
- Structure PASS evidence / `_frame_completeness` / `BLOCK_TO_COMPONENTS["structure"]==["frame"]` **unchanged**.

### ✅ IDLE catalog rebind B2+B3 — CLOSED (2026-09-04)

> Suites: **2250** (frame) · **2276** (motors/propellers/battery).  
> Named IDLE phrases reopen that family’s catalog after architecture 4/4 when the component already exists (not stub). Pure-phrase only (no trailing SKU). Mid-architecture FN-014 preserved. Frame re-pick clears all `parent_key=="frame"` children (including ordinal plates) before projecting the new SKU.

### ✅ Structure B arm `thickness_mm` (additive B2) — CLOSED (2026-09-05)

> Suite: **2286**. Contract: `implementation_contract_structure_b_thickness_arms_b2.md`. Smoke PASS.

Delivered:

- Optional `arm_thickness_mm` on `FrameSpec` + all four seed rows (sourced).
- `frame_arm.thickness_mm` display-only; N2 may create arm child from thickness alone.
- **M0** unchanged (root mass sole physics input).
- Free-text: arm-clause-gated mm only (plate-clause mm still OUT).
- Structure PASS * footnote unchanged.

### ✅ Structure B plate multiplicity B2 (Frame Assembly Physical Model) — CLOSED (2026-09-05)

> Suite: **2294**. Investigation → Buy → IC → review PASS WITH NOTES.  
> Contracts: `investigation_*_structure_b_frame_assembly_physical_model.md`,  
> `implementation_contract_structure_b_frame_assembly_physical_model.md`.

Delivered (code-backed):

- `PlateSeed` + `FrameSpec.plates: list[PlateSeed] | None` — curated per SKU (N1), max 8 (N7).
- Ordinal siblings `frame_plate` / `frame_plate_2`…`frame_plate_8` + free-text `label` property — **no** closed cross-manufacturer role taxonomy.
- N2: non-empty `plates[]` is canonical; scalar `plate_count`/`plate_material` = legacy fallback only.
- N3: equal thickness → distinct nodes (Top/Middle both 2mm stay two).
- Catalog projection + BOM `└ plate — {label}, {thickness}` display-only.
- **N4 OUT:** free-text multi-plate parsing remains debt (still one `FRAME_PLATE_KEY`).
- **N6 debt:** catalog projector may hardcode `completeness="high"`; upsert path still uses `_structure_part_completeness` — not “fixed” in this slice.
- **M0** / Structure PASS * footnote / MEASURE wall unchanged.

Out of scope (debt / MEASURE wall): tip-clearance / FEA / CAD · `mounts_on` · sum-of-parts mass into physics · arm↔motor cross-check · free-text multi-plate · G-N2 counts / G-N3 `compressed-x` / G-N4 diverge orphans / C3 assist UX · completeness hardcode polish.

### System-level Optimization — DEFERRED (Engineer lock 2026-09-05)

**Not the next phase.** Code today: local DSE (`can_fly` + goal score); apply #1 even if score does not improve (with warning). No readiness/gaps/Continuity/ASSEMBLY READY ring.

Valid product jump **later**, only when demonstrated pain — not because Vision §7 exists.  
Lock: [`.jes/artifacts/engineer_lock_system_optimization_deferred.md`](../.jes/artifacts/engineer_lock_system_optimization_deferred.md).

Prefer **not** further Structure attribute-drip without a new model Buy.

### 🧱 WALL — Prop/Energy experimental validation (Engineer lock 2026-09-05)

**Not an implementation phase.** Autonomy `~N min` remains an **orientative simplified energy estimate** — never “flight time certified.”

Closing physically defensible autonomy requires bench evidence of **Operating Point → consumption** (multi-point thrust/V/I/P), recorded as **HD-004** in [`HARDWARE_DEBT.md`](./HARDWARE_DEBT.md). Lock artifact: [`.jes/artifacts/engineer_lock_prop_energy_evidence_wall.md`](../.jes/artifacts/engineer_lock_prop_energy_evidence_wall.md).

Forbidden as default next: inventing SOC / sag / C-rate / variable efficiency / thermal models without T1/T2; framing “Prop/Energy Evidence IC” as closing autonomy.

Allowed later (optional): investigation of *what evidence schema to ingest when the bench exists* — still not 🔴 until Engineer names it after hardware exists.

---

## 9) What This Vision Does Not Change Yet

- No new source of truth replaces ProjectState.
- No LLM authority over engineering next-step decisions.
- No implicit rewrite of existing acquisition/continuity contracts — Continuity remains next-step copy authority; see [`PROJECT_CONTINUITY.md`](./PROJECT_CONTINUITY.md).
- **Execution queue** (what to implement next) lives in [`IMPLEMENTATION_TASKS.md`](./IMPLEMENTATION_TASKS.md) — not in §8 phase history above. **As of 2026-09-05** release **v0.3.8** suite **2294**; Structure + CLI smoke **CLOSED**; **no open software PRIORIDAD**. System Optimization **deferred** until pain. Prop/Energy experimental = **HD-004 wall**. MEASURE/CAD is not the default. Free-text multi-plate / G-N*/C3 / completeness hardcode remain debt.
- **Hardware-gated physics** (T1/T2 lab before any sibling field) lives in [`HARDWARE_DEBT.md`](./HARDWARE_DEBT.md) — **debt register, never 🔴 PRIORIDAD ACTUAL** (Engineer: no lab equipment). Includes HD-004 OP→consumption for autonomy. Not in the software/product queue.

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

