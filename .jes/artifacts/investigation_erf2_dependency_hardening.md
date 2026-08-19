# Investigation — ERF-2 Dependency Hardening

**Date:** 2026-08-18  
**Status:** **CLOSED — Engineer ratified 2026-08-18**  
**Contract:** [`implementation_contract_erf2_investigation.md`](implementation_contract_erf2_investigation.md)  
**Design:** [`design_erf2_dependency_hardening.md`](design_erf2_dependency_hardening.md)  
**Checkpoint base:** tag **`checkpoint-erf1`** (`63c427b`)  
**Vision anchor:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §ERF-2  
**Builds on:** [`investigation_erf1_readiness_foundation.md`](investigation_erf1_readiness_foundation.md) · [`implementation_report_erf1.md`](implementation_report_erf1.md)

---

## 1) Executive summary

**ERF-2 is viable now** as an **extension of `engineering_readiness`**, without a new architectural subsystem and **without** waiting for Impl C or a full ESC commercial catalog.

The codebase already has:

- motor / battery / propeller **catalog + bind**,
- motor↔propeller compatibility (`match_motor_propeller`),
- ESC **free-text inference** (`extract_esc_properties` → `current_a`),
- calc bridges (KV × cell count → RPM; Wh ÷ W → autonomy),
- ERF-1 **Gap Registry + eight subsystems** with `INCOMPATIBLE` in the enum (never emitted).

What is **missing** for ERF-2:

- any **deterministic motor↔ESC↔battery checker**,
- ESC as a **first-class architecture/BOM** component (orphan today),
- gap types for **electrical incompatibility**,
- use of catalog fields `MotorSpec.max_current_a`, `BatterySpec.c_rating` / `max_continuous_current_a` in validation,
- `electronics` / `integration` readiness lines (vision-only).

**Recommendation:** ERF-2 MVP = **pure electrical compatibility evaluator** (new small module) **composed by** `build_engineering_readiness`, emitting **3–5 new gap types** + **`INCOMPATIBLE` verdicts** when evidence exists. Defer full ESC JSON catalog (H5) to a **follow-up slice** unless Engineer requires SKU-level ESC in ERF-2.

---

## 2) Answer to the central question

### Question

> "¿Cuál es el conjunto mínimo de comprobaciones deterministas motor↔ESC↔batería (y estados INCOMPATIBLE) que Jarvis puede afirmar reutilizando autoridades existentes, extendiendo ERF-1 sin solver eléctrico completo?"

### Answer

Add a **thin Electrical Compatibility Authority** — pure functions over `ProjectState` + existing catalog/calc facts — that returns **compatibility facts** (not narrative). The Readiness Aggregator **composes** those facts into:

1. new **gap types** (stable IDs),
2. **`INCOMPATIBLE`** on affected subsystem lines when a check fails with sufficient evidence,
3. optional **`depends_on`** edges between gap types (explicit in contract, never inferred).

**Do not** move compatibility logic into Continuity, simulation, or LLM. **Do not** persist compatibility state.

Minimum checks achievable **without ESC catalog**:

| Check | Evidence source | MVP? |
|---|---|---|
| Motor draw vs declared ESC `current_a` | `components["esc"].properties.current_a` vs estimated draw from `motor_power_w` or SKU `max_current_a` | ✅ |
| Battery continuous current vs pack demand | `BatterySpec.max_continuous_current_a` or `c_rating × capacity` vs estimated total draw | ✅ when SKU-bound |
| Cell count / voltage vs motor KV band | `battery_cell_count` + nominal V/cell vs declared motor KV (sanity band) | ⚠️ heuristic — needs Engineer lock |
| Missing ESC when motors+battery defined | BOM/arch + component presence | ✅ as `GAP-ESC-UNDEFINED` not INCOMPATIBLE |
| Motor↔propeller | already `match_motor_propeller` | ✅ reuse, do not duplicate |

Checks that **require** ESC catalog or wiring model → **ERF-2 non-goals** or post-ERF-2.

---

## 3) Authority map (as-is)

| Concern | Current authority | ERF-2 role |
|---|---|---|
| Gap registry / assembly rollup | `engineering_readiness.build_engineering_readiness` | **Extend** — compose new gaps |
| BOM completeness | `project_closure.build_component_bom` | Read — ESC missing unless manually in components |
| Architecture expected keys | `system_architecture_catalog.BLOCK_TO_COMPONENTS` | **Gap:** `esc` not listed under `propulsion` |
| Motor/battery catalog | `knowledge/library.py` | Read SKU fields when `catalog_ref` set |
| Motor↔prop | `library.match_motor_propeller` | Reuse as existing fact |
| ESC inference | `domains/aerial.py` `extract_esc_properties` | Read declared ESC |
| Calc electrical bridge | `calculation_engine` KV×cells | Read — not compatibility |
| Sim feasibility | `simulator.FeasibilitySimulator` | **No electrical checks** — do not overload in ERF-2 MVP |
| Human next step | `project_continuity` (C-108 partial) | **Defer** Continuity handoff pattern to post-MVP or Slice 4b-style scoped cut |
| INCOMPATIBLE verdict | `engineering_readiness` enum | **Start emitting** with evidence |

### ESC orphan (critical finding)

```text
aerial_registry     → esc inferrable (keywords "esc", current_a)
component_writers   → can store components["esc"] via set_control_component path
BLOCK_TO_COMPONENTS → propulsion: [motors, propellers]  — NO esc
acquisition_target  → COMPONENT_PROMPTS has no esc
library/            → no esc/ JSON catalog (H5 deferred)
```

**Consequence:** Jarvis can **store** an ESC but **never surfaces** it as architecture/BOM gap unless ERF-2 adds `esc` to expected keys or a dedicated gap from free presence.

---

## 4) What ERF-1 already covers (do not re-implement)

| ERF-1 gap | Overlap with ERF-2 |
|---|---|
| `GAP-MOTOR-CATALOG-UNRESOLVED` | Catalog identity — not electrical |
| `GAP-BOM-MISSING-*` | Missing FC/battery/motors — not incompatible |
| `GAP-SIM-NOT-PASS` | Physics fail — not ESC amp headroom |
| `GAP-REQUIREMENTS-UNMET` | Mass/autonomy constraints |

ERF-2 gaps must be **orthogonal** — e.g. sim PASS + `GAP-ELECTRICAL-ESC-UNDERSIZED` → `NOT_ASSEMBLY_READY`.

---

## 5) Minimum viable electrical checks (predicate draft)

Investigation predicates — **not final contract** — for design discussion:

### 5.1 `check_esc_vs_motor_current` — **corrected per Engineer ratification**

**Electrical topology lock (ERF-2 MVP):** conventional multirotor = **1 motor ↔ 1 ESC**. Compare declared `esc.current_a` against **per-motor** draw `I_motor` — **never** `I_motor × motor_count` on a single ESC rating.

**Trigger INCOMPATIBLE when:**

- `components["motors"]` defined (measurable),
- `components["esc"]` has `current_a` declared,
- per-motor draw `I_motor` computable (SKU `MotorSpec.max_current_a` preferred; else `motor_power_w / V_nom` when both present),
- topology determinable as 1:1 per MVP lock,
- `esc.current_a < I_motor`.

**Never INCOMPATIBLE when:** topology undeclared, per-motor draw unknown, or only heuristic KV/voltage evidence → **`UNVERIFIABLE`**.

~~Investigation draft (superseded):~~ ~~`esc.current_a < I_motor × motor_count`~~ — rejected; see Design §5 / ★4.

### 5.2 `check_battery_discharge_vs_load`

**Trigger when:**

- battery SKU bound with `max_continuous_current_a` or `c_rating`,
- total draw estimate available,
- pack limit exceeded.

### 5.3 `check_esc_presence`

**Trigger gap (INCOMPLETE or dedicated gap type), not INCOMPATIBLE:**

- motors + battery defined, architecture propulsion/energy blocks complete enough for flight,
- no `components["esc"]` and no declared ESC in BOM expected keys.

### 5.4 Reuse `match_motor_propeller`

If propeller + motor SKU/props present and match fails → **`GAP-PROP-MOTOR-MISMATCH`** or subsystem `propulsion: INCOMPATIBLE` (reuse library fact).

---

## 6) Gap catalog — Engineer ratified (MVP)

| Gap type | MVP | Notes |
|---|---|---|
| `GAP-ESC-UNDEFINED` | ✅ | INCOMPLETE path — not INCOMPATIBLE |
| `GAP-ESC-UNDERSIZED` | ✅ | per-motor ESC vs per-motor draw (★4) |
| `GAP-BATTERY-DISCHARGE-EXCEEDED` | ✅ | pack-level limit vs total draw |
| `GAP-PROP-MOTOR-MISMATCH` | ✅ | **Readiness integration (B)** — exposes `library.match_motor_propeller`; no new rule |
| `GAP-MOTOR-ESC-VOLTAGE-MISMATCH` | ❌ **DEFER** | KV×voltage is RPM estimate, not incompatibility without explicit limit authority |

**Forbidden in ERF-2 MVP:** integration/wiring gaps, FC protocol gaps, comms gaps, pricing/availability, voltage/KV INCOMPATIBLE.

---

## 7) Subsystem line strategy

| Option | Pros | Cons |
|---|---|---|
| **A — Extend propulsion + energy only** | Minimal UI change; matches ERF-1 discipline | Vision lines for electronics/integration still absent |
| **B — Add `electronics` subsystem** | Honest home for ESC-centric gaps | Requires authority for line; don't invent comms/integration |
| **C — Add electronics + integration (vision-full)** | Matches vision doc §6 | Risk artificial INCOMPLETE without authorities |

**Investigation recommendation:** **Option B — RATIFIED** — add **`electronics`** subsystem; **`communications` / `integration` remain out**.

---

## 8) Module placement (no new subsystem)

| Option | Verdict |
|---|---|
| Inline in `engineering_readiness.py` | Too large over time |
| New `electrical_compatibility.py` (pure) | **Recommended** — testable, reusable by calc later |
| Extend `library.py` | Wrong layer — catalog ≠ project compatibility |
| Extend `simulator.py` | Defer — sim today has no electrical surface |

```text
ProjectState + library + components
        ↓
electrical_compatibility.evaluate(project_state) → CompatibilityResult
        ↓
engineering_readiness (compose gaps + INCOMPATIBLE verdicts)
```

---

## 9) depends_on model

Inherit ERF-1 rule: **explicit per gap type in contract only.**

Candidate edges (for design, not inference):

```text
GAP-ESC-UNDERSIZED  depends_on: []     # if ESC missing, emit UNDEFINED not UNDERSIZED
GAP-BATTERY-DISCHARGE-EXCEEDED  depends_on: []
```

Do **not** auto-chain "fix battery before ESC" without declared edges.

---

## 10) Risks and controls

| Risk | Control |
|---|---|
| Heuristic amp draw wrong | Use SKU `max_current_a` when bound; else UNVERIFIABLE |
| ESC not in arch → gaps never fire | ERF-2 must add `esc` to `BLOCK_TO_COMPONENTS["propulsion"]` or explicit presence gap |
| Duplicating sim | Compatibility module separate from `FeasibilitySimulator` |
| Second truth | Facts in CompatibilityResult; gaps derived on read |
| Over-scoping to H5 catalog | MVP on declared props + motor/battery SKU fields |
| Continuity churn | Scope Continuity handoff like ERF-1 Slice 4 (catalog only) or defer |

---

## 11) Non-goals (ERF-2 investigation lock)

- Full electrical transients, wiring, connectors, PCB fit
- ESC JSON catalog (H5) — optional slice, not blocker for rule-based MVP
- Geometric integration / cabling
- `"aplica la mejor"` optimizer
- Full Impl C procurement BOM
- LLM compatibility narration as authority
- Emitting `communications` / `integration` subsystem lines without engines

---

## 12) Acceptance probes (investigation-time)

1. **Sim PASS + ESC undersized:** fixture with declared 20A ESC + 4× motors drawing >20A total → `overall NOT_ASSEMBLY_READY`, `propulsion INCOMPATIBLE`, gap `GAP-ESC-UNDERSIZED`.
2. **Missing evidence:** motors declared, no ESC, no current fields → `GAP-ESC-UNDEFINED`, not INCOMPATIBLE.
3. **SKU battery C-rating:** bound battery + exceeded draw → `GAP-BATTERY-DISCHARGE-EXCEEDED`.
4. **Prop mismatch reuse:** existing `match_motor_propeller` false → gap fires, no duplicate logic.
5. **No regression on ERF-1:** all 40 ERF-1 tests green when compatibility module returns empty.
6. **No LLM:** compatibility eval with LLM disabled.

---

## 13) Engineer decisions — CLOSED (2026-08-18)

| # | Decision | Verdict |
|---|---|---|
| D1 | ESC in architecture (`BLOCK_TO_COMPONENTS["propulsion"]`) | ✅ Yes — add `esc` |
| D2 | MVP gap types | ✅ `GAP-ESC-UNDEFINED`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH` (integration B) |
| D3 | Subsystems | ✅ Add `electronics` only; no `integration` / `communications` |
| D4 | Current model | ✅ 1 motor ↔ 1 ESC (MVP lock); per-motor compare; else `UNVERIFIABLE` |
| D5 | Continuity handoff | ❌ Defer — Readiness + CLI first; optional Slice 5 post-MVP |
| — | KV/voltage incompatibility | ❌ Defer |
| — | ESC catalog H5 | Not blocking |
| — | ERF-1 Slice 4b | Remains deferred — do not bundle |
| — | `electrical_compatibility.py` | ✅ Approved as pure authority |

**Architectural rule (Engineer lock):** ERF-2 may assert `INCOMPATIBLE` only when electrical topology and required evidence are **deterministically established**. Missing topology, missing current limits, or heuristic-only evidence → **`UNVERIFIABLE` / `INCOMPLETE`**, never upgraded to `INCOMPATIBLE`.

---

## 14) Suggested implementation slices (for later contract)

| Slice | Deliverable |
|---|---|
| **1 — Compatibility authority** | `electrical_compatibility.py` + unit tests; pure facts |
| **2 — Architecture/BOM ESC** | `esc` in `BLOCK_TO_COMPONENTS`; acquisition prompt optional |
| **3 — Readiness gaps + INCOMPATIBLE** | extend `engineering_readiness`; new gap types; `electronics` line if approved |
| **4 — CLI surface** | show incompatibility gaps in TOP GAPS / subsystem INCOMPATIBLE |
| **5 — Continuity handoff (optional)** | scoped branch for top electrical gap — mirror ERF-1 C-108 pattern |

Order: **1 → 3 before 5**; slice 2 may precede 3 if ESC presence gaps required.

---

## 15) Investigation verdict

| Criterion | Result |
|---|---|
| Viable without new subsystem? | ✅ |
| Viable without ESC catalog H5? | ✅ (with declared props + motor/battery SKU) |
| Extends ERF-1 cleanly? | ✅ |
| Blocked on Impl C? | ❌ |
| Ready for design doc? | ✅ **CLOSED** — see `design_erf2_dependency_hardening.md` |

**Next step:** Engineer ratifies design → Cursor drafts **`implementation_contract_erf2.md`**.
