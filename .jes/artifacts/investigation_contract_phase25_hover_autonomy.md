# Investigation Contract — Phase 2.5 Hover Flight Energy Model

**Project:** Jarvis  
**Date:** 2026-09-01 (revised same day — Engineer research pass)  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_phase25_hover_autonomy.md`

**Status:** REVISED — READY FOR CLAUDE

**Revision note:** Engineer web research on **Combo A exact** (SunnySky R2205 2500KV + GF5045×3 @ 14.8 V) confirms the manufacturer test table is **already sufficient** for first hover validation. This contract replaces the prior premise “missing bench data” with “data exists — curation + resolution policy required.” **Do not implement until investigation PASS + Engineer ★ on report.**

**Type:** Architecture + physics-model investigation — define how Jarvis moves from **deterministic arithmetic** to **honest flight-energy physics** for hover autonomy, using **Discrete Operating Point Datasets** and **bounded interpolation over manufacturer-published points** — not continuous aerodynamic curves. **Not** an implementation plan.

**Checkpoint base:** commit **`0e2e71c`** — *Add minimum-universe physical catalog with verified ESC foundation* (pushed to `origin/main`)

**Prior arcs (CLOSED — do not re-open without regression proof on `0e2e71c`):**

| Delivered @ catalog foundation | Scope |
|---|---|
| **Minimum universe catalog** | Verified motor/battery/prop SKUs; identity-first; no invented `max_watts` |
| **Operating Points (P2-1 / P2-2)** | `resolve_operating_point`; `motor_op_*` bridge; dual truth `motor_power_w` vs `motor_op_power_w` |
| **Motor OP Voltage Coherence @ v0.3.4** | MOP-1/2/3; voltage gate; DSE live-params |
| **ESC catalog foundation** | `library/esc/`, `EscSpec`, `bind_esc_from_catalog` — **compatibility only**, not OP identity |
| **Electrical compatibility (ERF-2)** | `esc_vs_motor`, battery discharge, prop-motor |
| **Combo probe** | `scripts/cli_probe_minimum_universe_combo.py` — Combo A / A′ / B (3/3 PASS) |

**Still frozen (do not implement in this investigation):**

| ID | Topic |
|---|---|
| **ESC ~30 A SKU** | Deliberate `GAP-ESC-UNDERSIZED` fixture |
| **ESC efficiency / system loss model** | No invented η — separate until sourced |
| **G24-B** | `_score_candidate` rewrite |
| **FN-R** | Acquisition/routing UX polish |
| **Full mission model** | cruise/climb/descent, wind, payload phases |
| **First-principles thrust→power** | Ct/Cp / propeller aerodynamic model — **future phase** |
| **Proportional scaling** | e.g. `(T_req / T_max) × P_max` — **explicitly forbidden** |
| **Battery discharge curve** | C-rate derating, voltage sag |

**Primary source (Combo A dataset — Engineer verified):**

- [R2205 KV2500 technical PDF](https://img.banggood.com/file/products/20181018062904ER22052500KV.pdf) — GF5045×3 @ 14.8 V thrust/current/power/RPM table (200 gf–1280 gf)
- [SunnySky R2205 product page](https://sunnyskyusa.com/products/sunnysky-r2205-brushless-motors) — family specs cross-check

**Design authority (read-only — context, not proof):**

- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md)
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md`](investigation_report_dse_motor_op_dual_truth.md)

---

## Engineer locks (★★ — ratified before investigation; report must not contradict)

These **12 locks** supersede open questions in the original draft where they conflict.

| Lock | Rule |
|---|---|
| **★★1** | **Combo A manufacturer table is sufficient** for first hover validation. Gap is **curation + resolution policy**, not missing lab data. |
| **★★2** | Seed the published **14.8 V + GF5045×3** series as discrete `manufacturer_test` rows (see §Combo A Dataset). Catalog today has **one** row — investigation must treat the other nine as **approved curation target**, not research unknown. |
| **★★3** | **Hover thrust demand** = `weight_n / motor_count` (T/W ≈ 1.0 for energy). **`safety_factor` is feasibility/readiness only** — must **not** inflate hover energy demand. |
| **★★4** | **Linear interpolation permitted only** between two bracketing `manufacturer_test` or `measured_test` OPs on the **thrust_n** axis. |
| **★★5** | **No extrapolation.** Outside `[min(OP.thrust_n), max(OP.thrust_n)]` → hover power = **`UNVERIFIABLE`**. |
| **★★6** | Interpolated results use **`source_type = interpolated`** with provenance to **both** source OP rows (see §Evidence tiers). |
| **★★7** | **`P_motor_input`** (OP electrical power at motor+prop test point) **≠ `P_battery`** (pack/system). ESC/system losses remain **separate** until sourced — do not invent η. |
| **★★8** | **Operating Point identity** = **Motor + Propeller + Voltage** only. **ESC is not** part of manufacturer OP identity — ESC stays in compatibility / limits. |
| **★★9** | First Phase 2.5 validation case = **Combo A with real SunnySky dataset** — not a hypothetical future motor or synthetic curve. |

**Terminology lock (★★10):**

- Say **Discrete Operating Point Dataset** and **bounded interpolation** — **not** “thrust→power curve” or “aerodynamic model.”
- OP rows are **`manufacturer_test` bench points** — **not** `hover_test`. Hover is a **flight demand** Jarvis computes; OPs are **experimental authority** for thrust↔power mapping.

**Forbidden formulas (★★11 — block in any future IC):**

```text
P_hover ≈ (T_required / T_max_op) × P_max_op     ← proportional scaling — FORBIDDEN
P_hover = f(T) fitted to N points                  ← continuous model — FORBIDDEN in Phase 2.5
P_hover from Ct/Cp/RPM first principles          ← FORBIDDEN until dedicated aerodynamic phase
```

**Autonomous hover-energy pipeline (★★12 — LOCKED):**

Given a valid **mass model**, **motor_count**, and a resolved **motor + propeller + voltage** Discrete OP Dataset, the user **must not** need to supply `T_hover`, pick bracketing rows, or perform interpolation manually.

Jarvis **must autonomously** (deterministic engine — no LLM):

```text
ProjectState + catalog-bound components
      ↓
total_mass_kg → weight_n
      ↓
T_hover_total = weight_n
T_hover_motor = T_hover_total / motor_count
      ↓
identify applicable OP dataset (motor_sku + propeller_sku + voltage_v)
      ↓
exact match on thrust_n?  → use row
else bracket?             → bounded linear interpolation (★★4–★★6)
else                      → UNVERIFIABLE
      ↓
P_motor_input (+ I_motor_input, provenance)
      ↓
hover autonomy = f(battery_capacity_wh, P_motor_input × motor_count)
```

**Authority split (non-negotiable):**

- **Jarvis computes:** mass, weight, hover thrust demand, dataset selection, bracket choice, interpolation, autonomy propagation.  
- **Experimental OP data is authoritative only for:** the empirical thrust↔power (and current) relationship at fixed motor+prop+voltage — **not** for hover thrust demand.

Investigation must map **each step** to a concrete module/API and prove no manual/user/LLM step is required on the Combo A path.

---

## Combo A Dataset — minimum discrete OP set (Engineer-approved curation)

Investigation must use this table as the **reference dataset**. Report numeric examples **must** use these values.

**Identity:**

```text
motor_sku:      sunnysky_r2205_2500
propeller_sku:  gf_5045x3
voltage_v:      14.8
source_type:    manufacturer_test   (per row — not hover_test)
source_url:     https://img.banggood.com/file/products/20181018062904ER22052500KV.pdf
```

**Published points** (gf → N via ×0.00980665; values below match catalog convention):

| Thrust (gf) | thrust_n | current_a | power_w | Notes |
|---:|---:|---:|---:|---|
| 200 | 1.961 | 2.7 | 40 | |
| 300 | 2.942 | 4.7 | 70 | |
| 400 | 3.923 | 7.1 | 105 | |
| 500 | 4.903 | 9.7 | 144 | |
| 600 | 5.884 | 13.0 | 192 | |
| 700 | 6.864 | 16.3 | 241 | bracket low |
| 800 | 7.845 | 19.8 | 293 | bracket high |
| 900 | 8.826 | 23.8 | 352 | |
| 1000 | 9.807 | 27.9 | 413 | |
| 1280 | 12.552 | 40.0 | 592 | max row — already in catalog |

**Catalog as-is (`library/motores/_datos.json`):** only the **1280 gf / 12.552 N** row is curated. Investigation must quantify autonomy error from **using that single row for energy** vs **dataset + interpolation**.

**Reference interpolation example** (Engineer — report must reproduce):

```text
T_hover_motor ≈ 7.06 N   (example mass ~2.88 kg, 4 motors)

Bracket: 6.864 N → 241 W  and  7.845 N → 293 W

P_motor_input ≈ 241 + (7.06 - 6.864) / (7.845 - 6.864) × (293 - 241)
              ≈ 251 W/motor

P_total_hover ≈ 4 × 251 ≈ 1004 W

592 W/motor is correct for 12.55 N — wrong regime for hover energy.
```

---

## Two-level physics architecture (implements ★★12 — investigation must map to code)

Jarvis combines **deterministic first-principles** (what it can derive) with **experimental OP data** (what it cannot derive reliably in Phase 2.5). The full pipeline is **autonomous end-to-end** per ★★12 — the reference interpolation example in §Combo A Dataset is an **auditor's check**, not a user workflow.

### Level 1 — Jarvis computes (no OP table needed)

```text
total_mass_kg  (payload + structure + battery SKU + motor SKU × count)
      ↓
weight_n = total_mass_kg × g
      ↓
T_hover_total = weight_n
      ↓
T_hover_motor = T_hover_total / motor_count
```

### Level 2 — OP Dataset + Operating Point Engine (experimental authority only)

```text
Discrete Operating Point Dataset
  (manufacturer_test | measured_test rows for motor+prop+voltage)
      ↓
Operating Point Engine  (investigate: extend library vs new module vs calc helper)
  — invoked automatically from calc/bind path; user never selects rows (★★12)
      ↓
  ┌─────────────┬──────────────────────┐
  │ exact match │ bracket + linear interp │
  └─────────────┴──────────────────────┘
      ↓
P_motor_input, I_motor_input, optional RPM
source_type: manufacturer_test | interpolated | UNVERIFIABLE
      ↓
persist provenance on ProjectState / calc artifact (auditable)
```

### Level 3 — NOT Phase 2.5

```text
thrust → power from propeller/motor first principles
continuous curve fit across all OPs
extrapolation below min or above max published thrust
```

**Resolver split (investigate, likely ★★ required):**

| API purpose | Selection policy | Consumer |
|---|---|---|
| **Feasibility / max thrust** | max `thrust_n` among matching rows (today's `v1_max_thrust`) | sim margin, `available_total_thrust_n`, `motor_op_*` bridge |
| **Flight energy at required thrust** | exact or bounded interpolation at `T_hover_motor` | hover autonomy, hover-current facts |

Report must recommend **whether** this is one function with a `mode=` parameter or two explicit entry points — but **must not** use max-thrust OP for hover energy.

---

## 0. Intent

After catalog foundation, Jarvis honestly resolves **one** bench OP (often max thrust) and uses **`motor_op_power_w`** for autonomy — a **regime error**, not a missing-SKU error.

**Corrected problem statement:**

```text
REAL DATA EXISTS (SunnySky PDF — 10 points @ 14.8 V + GF5045×3)
        ↓
catalog under-curates (1/10 rows today)
        ↓
resolver selects max thrust for feasibility AND energy
        ↓
autonomy uses 592 W/motor when hover needs ~251 W/motor
```

This investigation maps **as-is** against a **to-be contract** where:

1. Jarvis **computes hover thrust** from mass (Level 1);  
2. Jarvis **resolves motor input power** from the **Discrete OP Dataset** (Level 2);  
3. **`motor_power_w` / `motor_op_*` / `motor_hover_power_w`** (or equivalent) stay **semantically separate**;  
4. **`P_motor_input` ≠ `P_battery`** until system-loss data exists;  
5. **ESC** remains outside OP identity (★★8).

**Report may conclude** (investigator verifies, does not assume):

- (A) Implementation blocked only on **catalog curation** (seed 9 rows) + resolver split + calc wiring; or  
- (B) Additional **code contract** changes beyond above; or  
- (C) **Operating Point Engine** must be a new module vs extension of `library.py` — with evidence.

**Report must NOT conclude:**

- (D) ~~Hover cannot be honest until more bench OP rows are found~~ — **superseded by ★★1/★★2.**

---

## 1. Methodology lock (★ — non-negotiable)

| ★ | Rule |
|---|---|
| **★1** | **Code + tests + probes first.** Cite `file:line`, test, probe on **`0e2e71c`**. Engineer locks ★★ are constraints, not suggestions. |
| **★2** | **No invented physics.** Interpolation only per ★★4–★★6. No proportional scaling (★★11). |
| **★★** | **Engineer locks § above are binding** for report recommendations. |
| **★3** | **Separate scope boxes** — hover energy ≠ ESC η ≠ mission profile ≠ DSE rewrite. |
| **★4** | **Preserve dual truth** + add hover flight power as third semantic. |
| **★5** | **Evidence tiers** — see §Evidence tiers; `interpolated` requires full provenance. |
| **★6** | **Mandatory table (§3)** — `YES` / `NO` / `PARTIAL` / `N/A` + evidence; no `?`. |
| **★7** | **Combo A primary** — numeric trace with **251 W/motor** interpolation example. |
| **★8** | **Ordered IC slices** — distinguish **data curation** (9 OP rows) vs **code**. |
| **★9** | **Do not reopen** Motor OP voltage coherence or Catalog V1 without regression. |

---

## Evidence tiers (★★6 — formal)

Closed set for Phase 2.5 (report must use consistently):

```text
manufacturer_test   — published vendor bench row (Combo A PDF)
measured_test       — third-party bench (e.g. Oscar Liang) — distinct from manufacturer
interpolated        — linear between two bracketing rows (see provenance block)
fallback            — fallback_only OP row
derived             — heuristic from other params (e.g. mass estimate)
estimated           — legacy_estimate / MotorSpec.thrust_n peak
assumed             — user declared, no catalog
```

**`interpolated` provenance block (required shape for report + future IC):**

```json
{
  "source_type": "interpolated",
  "interpolation_axis": "thrust_n",
  "method": "linear",
  "bounded": true,
  "target_thrust_n": 7.06,
  "source_points": [
    {"thrust_n": 6.864, "power_w": 241, "row_ref": "700gf"},
    {"thrust_n": 7.845, "power_w": 293, "row_ref": "800gf"}
  ]
}
```

Never upgrade `interpolated` → `manufacturer_test` in prose or params.

---

## 2. Investigation gates (must answer in report)

### Gate A — As-is flight-energy physics audit

Trace ProjectState → `autonomy_min` for Combo A. Mandatory table (writer/reader) as before.

**Required numeric finding:**

| Quantity | Current Jarvis (approx) | Correct regime |
|---|---:|---|
| `T_hover_motor` | uses `required_thrust_n` with `safety_factor`? | **~7.06 N** @ ~2.88 kg (verify mass from calc) |
| Power for autonomy | `motor_op_power_w` = **592 W** | **~251 W** interpolated |
| `autonomy_min` | `22.2 / (592×4) × 60` ≈ **0.56 min** | `22.2 / (251×4) × 60` ≈ **1.33 min** (illustrative — report uses exact mass) |

**Required finding:** 592 W is **correct for 12.55 N** — wrong **only** because autonomy uses bench-max regime for hover demand.

---

### Gate B — Power semantics (four concepts — do not collapse)

| Concept | Param (proposed) | Source | Use |
|---|---|---|---|
| Nominal rating | `motor_power_w` | `MotorSpec.max_watts` | Ceiling, DSE — not hover |
| Bench max OP | `motor_op_power_w` | max-thrust row via feasibility resolver | Feasibility bridge, legacy path |
| **Hover motor input** | `motor_hover_power_w` (or report alternative) | OP Engine @ `T_hover_motor` | **Autonomy numerator** |
| **Battery/system** | `P_battery` / deferred | pack + losses | Future — not `motor_op_power_w` alias |

**Lock ★★7:** Phase 2.5 v1 autonomy uses **`P_motor_input × motor_count`**, labeled honestly as motor test-point power, **not** full system draw.

---

### Gate C — Hover thrust demand (★★3 LOCKED)

Report **must adopt** (not re-debate without new Engineer approval):

```text
T_hover_total = weight_n
T_hover_motor = weight_n / motor_count
```

```text
required_thrust_n = weight_n × safety_factor   →  feasibility / sim margin ONLY
T_hover_motor                              →  energy / hover OP lookup ONLY
```

Investigate **where** `safety_factor` incorrectly enters energy path today (`calculation_engine.py` `calculate_required_thrust` chain) and recommend **minimal fix**.

---

### Gate D — Discrete OP Dataset + bounded interpolation (★★4–★★6 LOCKED)

Investigate **implementation** of:

```text
required_thrust_n  (hover motor)

if exact row match on thrust_n (within epsilon):
    use row → source_type unchanged

elif min(OP.thrust_n) ≤ required ≤ max(OP.thrust_n):
    find bracketing rows (low, high)
    linear interpolate power_w, current_a on thrust_n axis
    → source_type = interpolated + provenance block

else:
    UNVERIFIABLE — no autonomy from OP path (honest gap)
```

**Also investigate:**

1. Row identity: need stable `row_ref` / index in JSON?  
2. RPM interpolation — same policy or power-only v1?  
3. Split from `resolve_operating_point` — **required** per ★★9 workflow.  
4. Catalog curation: all 10 rows — field completeness (`rpm` from PDF per row).

**Hard rules:** no extrapolation; no curve fit; no proportional scaling.

**★★12 deliverable:** step-by-step map from `ProjectState` → `autonomy_min` with **zero** user-supplied thrust targets or manual row selection; list any today step that violates this.

---

### Gate E — Integration surfaces

Same matrix as prior draft, plus:

| Surface | New question |
|---|---|
| **`effective_motor_power_w`** | Deprecate for autonomy; keep for what? |
| **`electrical_compatibility`** | ★★6 open: hover **`I_motor`** from interpolated OP vs bench 40 A — report recommends **both facts** or hover-only for discharge |
| **Autonomy label** | User must see `flight_regime: hover` + evidence tier |
| **DSE** | Defer hover-aware explore to slice 2 unless trivial |

---

### Gate F — Reference cases (★★9 — no hypothetical dataset)

| Case | Purpose |
|---|---|
| **Combo A** | Full dataset math: current vs interpolated hover autonomy |
| **Combo A′** | ESC does not change hover power path |
| **Combo B** | Single measured OP — interpolation UNVERIFIABLE or partial? |
| **Extrapolation negative** | `T_hover` below 1.961 N → must be UNVERIFIABLE |

**Remove:** “hypothetical second OP row” — **real dataset replaces it.**

---

### Gate G — Blockers (revised)

| Candidate | Classification (report verifies) |
|---|---|
| Seed 9 missing OP rows in JSON | **BLOCKING for honest hover numbers** — **data curation**, not external research |
| Resolver split | Likely **BLOCKING** |
| `safety_factor` in energy path | Likely **BLOCKING** bug |
| G26/G27 | Likely **PARALLEL** for catalog-bound Combo A |
| ESC efficiency | **DEFER** (★★7) |
| Second motor / more sources | **NOT NEEDED** for Phase 2.5 v1 (★★1) |

---

### Gate H — IC slice options (revised)

| Option | Scope | Engineer lean |
|---|---|---|
| **H-A — Honesty gate only** | Label autonomy as bench-proxy | Interim only — **not** primary |
| **H-B — Curation + OP Engine + hover autonomy** | Seed 10 rows + resolver split + `T_hover` + interpolated power + new autonomy path | **PRIMARY (★★9)** |
| **H-C — Curation-only PR** | JSON rows without code | Prerequisite PR before H-B |
| **H-D — Full aerodynamic model** | Ct/Cp | **OUT OF SCOPE** |

Report recommends **H-C then H-B** or single IC combining both — with probe: Combo A hover autonomy ≈ 1.3 min vs ≈ 0.56 min today (verify exact numbers).

---

### Gate I — Operating Point Engine placement (new)

Investigate where Level 2 logic lives:

```text
Option 1: library.py — resolve_operating_point_at_thrust(...)
Option 2: jarvis/core/flight_energy.py (new helper — NOT "Physics Engine" subsystem)
Option 3: calculation_engine inline
```

Recommend one with import-graph / forbidden-subsystem analysis per `CLAUDE.md`.

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Hover thrust from mass (T/W≈1) | | | | |
| Discrete OP dataset (10 rows) | | 1/10 in JSON | curation | H-C/H-B |
| Hover power from bracket interpolation | | | | H-B |
| Honest hover autonomy | | | | H-B |
| No extrapolation policy | | | | H-B |
| `interpolated` provenance | | | | H-B |
| Separate bench vs hover power | | | | H-B |
| `P_motor_input` ≠ `P_battery` | | | | docs/honesty |
| ESC outside OP identity | | partial | | none |
| User-visible flight regime + tier | | | | H-B |
| **Autonomous hover-energy pipeline (★★12)** | | | | H-B |

---

## 4. IN SCOPE

1. Baseline @ `0e2e71c` + combo probe  
2. Gates A–I with ★★ locks applied  
3. Combo A numeric trace — **251 W/motor** example verified  
4. Catalog gap analysis: 1 vs 10 rows  
5. OP Engine placement recommendation (Gate I)  
6. Mandatory table populated  
7. IC slice recommendation (**H-B primary**)  
8. Engineer ★ questions — **mark which are pre-answered by ★★ locks**  
9. Optional IC outline for `implementation_contract_phase25_hover_autonomy.md`

---

## 5. OUT OF SCOPE

- Production implementation or JSON curation (investigation only)  
- Proportional scaling / curve fitting / Ct-Cp model  
- ESC efficiency invention  
- ESC as OP identity field  
- Calling manufacturer rows `hover_test`  
- Weakening Combo A probes  
- Version bump  

---

## 6. Deliverables

1. `.jes/artifacts/investigation_report_phase25_hover_autonomy.md`  
2. Baseline table (suite + combo probe)  
3. Optional investigation repro test (xfail documenting current 592 W autonomy path)  
4. IC outline for H-B (+ curation sub-PR if split)

---

## 7. Acceptance (Cursor review)

| Verdict | Criteria |
|---|---|
| **PASS** | Gates A–I; table filled; ★★ locks respected; 251 W example; rejects extrapolation/scaling; H-B primary; catalog 1/10 gap quantified |
| **PASS WITH NOTES** | Gate I placement debatable but evidence solid |
| **FAIL** | Claims missing external data for Combo A; proposes curve/scaling; ignores ★★3/★★5/★★12; requires manual T_hover or row selection; implements code |

---

## 8. Engineer ★ questions (report surfaces — many pre-locked)

| ★ | Question | Pre-lock |
|---|---|---|
| **★1** | Honest hover autonomy today? | **NO** — regime + curation gap |
| **★2** | H-A sufficient? | **NO** — H-B required for validation |
| **★3** | Hover thrust formula? | **★★3 LOCKED** — `weight/motor_count` |
| **★4** | Min rows for interpolation? | **★★4** — ≥2 bracketing published rows |
| **★5** | Resolver split? | Report confirms; Engineer expects **yes** |
| **★6** | Discharge: hover vs bench current? | Report recommends |
| **★7** | Next data task? | **★★2** — seed PDF table rows 200–1000 gf |
| **★8** | DSE in slice 1? | Report recommends; lean **defer** |
| **★9** | OP Engine placement? | **Gate I — report decides** |
| **★10** | Accept `P_motor_input` for v1 autonomy (not `P_battery`)? | **★★7 LOCKED** |
| **★11** | Must hover-energy path be fully autonomous from ProjectState? | **★★12 LOCKED** |

---

## 9. Suggested investigation order

```text
1. Baseline verify
2. Catalog audit — 1/10 rows vs Combo A Dataset §
3. Gate A — numeric trace (592 W wrong regime, 251 W correct)
4. Gate C — safety_factor leakage into energy
5. Gate D + I — interpolation contract + module placement
6. Gate B, E — power semantics + integration
7. Gate F — Combo A/A′/B + extrapolation negative
8. Gate G, H — blockers + slice recommendation
9. Mandatory table + ★ with pre-lock column
```

---

## 10. Post-investigation workflow

```text
Catalog foundation ✅
      ↓
Phase 2.5 Investigation (this contract, revised)
      ↓
Engineer ★ on report
      ↓
implementation_contract_phase25_hover_autonomy.md
  ├── slice 1: curate 9 OP rows (Combo A dataset)
  └── slice 2: OP Engine + hover thrust + hover autonomy + probe
      ↓
implement → review → probe → checkpoint
```

---

## 11. Copy-paste prompt for Claude Code

```text
You are the Investigator for Jarvis.

Read and execute (REVISED contract — Engineer locks applied):
  .jes/artifacts/investigation_contract_phase25_hover_autonomy.md

Baseline: commit 0e2e71c on main.

Deliver:
  .jes/artifacts/investigation_report_phase25_hover_autonomy.md

Non-negotiable:
  - Engineer ★★1–★★12 locks in contract § "Engineer locks"
  - ★★12: Jarvis autonomously derives hover energy from ProjectState — no manual T_hover, row pick, or interpolation
  - Combo A has SUFFICIENT manufacturer data (PDF) — problem is curation + resolver, NOT missing lab data
  - Use Combo A Dataset table (10 points @ 14.8 V + gf_5045x3)
  - Reproduce ~251 W/motor interpolation example for ~7.06 N hover thrust
  - Hover demand = weight_n / motor_count — NOT safety_factor
  - Interpolation ONLY between bracketing OPs; NO extrapolation; NO (T/Tmax)*P scaling
  - Terminology: Discrete OP Dataset — not "curve"
  - OP rows are manufacturer_test — not hover_test
  - P_motor_input ≠ P_battery; ESC not in OP identity
  - Do NOT implement production code or edit JSON
  - Cite file:line; fill mandatory table §3
  - Recommend H-B as primary IC slice
  - Mark ★ questions pre-answered where contract says LOCKED
```

---

**End of contract (rev. 2026-09-01 — Engineer research pass + ★★12 autonomous pipeline lock).**
