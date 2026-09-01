# Implementation Contract — Phase 2.5 Hover Flight Energy Model

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR IMPLEMENTER — Engineer ★ ratified 2026-09-01

**Type:** Catalog curation + deterministic hover-energy physics — closes **thrust-demand-blind OP binding** for autonomy. **Not** full flight mission model. **Not** ESC/system loss model. **Not** DSE rewrite. **Not** proportional thrust→power scaling.

**Investigation:** [`.jes/artifacts/investigation_report_phase25_hover_autonomy.md`](investigation_report_phase25_hover_autonomy.md)  
**Investigation contract:** [`.jes/artifacts/investigation_contract_phase25_hover_autonomy.md`](investigation_contract_phase25_hover_autonomy.md) (rev. ★★1–★★12)  
**Investigation verdict:** **PASS WITH NOTES**

**Checkpoint base:** commit **`0e2e71c`** — *Add minimum-universe physical catalog with verified ESC foundation*  
**Pre-fix combo probe:** `scripts/cli_probe_minimum_universe_combo.py` — **3/3 PASS**

**Arc:** Phase 2.5 Hover Energy @ post-catalog foundation → target checkpoint after review (version bump only if Engineer asks).

**Workflow:** Engineer ★ ✅ → implement **P25-D** then **P25-H** → suite green → probe → implementation report → Cursor review → checkpoint if requested.

---

## 0. Engineer ratification (★ ENGINEER — RATIFIED 2026-09-01)

| ★ | Decision | IC obligation |
|---|---|---|
| **★1** | Current autonomy is **not** hover-energy honest | Fix regime error; do not label bench OP power as hover |
| **★2** | H-A insufficient; **P25-D → P25-H** | Two ordered slices below |
| **★3** | `T_hover_motor = weight_n / motor_count` | **P25-H** calc; `safety_factor` **must not** enter hover energy |
| **★4** | Interpolation only between bracketing OPs | **P25-H** resolver |
| **★5** | Split feasibility/max-thrust vs energy-at-thrust | Keep `resolve_operating_point` for bind/feasibility; add `resolve_operating_point_at_thrust` for calc-time energy |
| **★6** | Hover current = separate fact later; **do not** change discharge logic in v1 | **No** `electrical_compatibility.py` changes in this IC |
| **★7** | Complete 9 remaining SunnySky PDF rows | **P25-D** |
| **★8** | DSE out of slice 1 | **No** `design_explorer.py` changes |
| **★9** | `resolve_operating_point_at_thrust(...)` in **`library.py`** | **P25-H** — no new subsystem module |
| **★10** | v1 energy uses `P_motor_input × motor_count`; **not** full battery/system draw | Label honestly (§2.4) |
| **★11** | Autonomous pipeline mass → hover thrust → OP → power → autonomy | **P25-H** end-to-end (★★12) |

**Naming lock (Engineer precision):**

> Do **not** call the ~1.32 min Combo A figure “real drone flight time” or “actual autonomy.”

Use:

```text
hover_energy_autonomy_min
```

**Definition (locked):** estimated minutes from `battery_capacity_wh / (P_motor_input × motor_count) × 60`, where `P_motor_input` is motor+propeller **bench input power** at the resolved operating point (exact or bounded-interpolated `manufacturer_test` rows). **Excludes:** ESC losses, wiring, avionics, battery sag, C-rate derating, non-hover regimes.

---

## 1. Problem / intent

### 1.1 Root cause (investigation-verified — corrected mechanism)

```text
set_motor_component @ bind
  resolve_operating_point(motor, prop, voltage)   ← no thrust argument
  v1_max_thrust when multiple rows exist
  motor_op_power_w = bench-max (592 W @ 12.552 N for Combo A)
        ↓
CalculationEngine.build @ calc time
  weight_n, thrust_per_motor_required_n computed
  BUT never passed to any OP resolver
  effective_motor_power_w → motor_op_power_w (592 W)
        ↓
autonomy_min = Wh / (592 × 4) × 60 = 0.5625 min
```

**Not** `safety_factor` leakage — `safety_factor` never touches the energy branch (`investigation_report` Gate C). The defect is **thrust-demand-blind OP binding** plus **single-row catalog** (invisible until curation adds rows).

### 1.2 Target end state (Combo A reference)

| Quantity | Before | After (expected) |
|---|---:|---:|
| Curated OP rows @ 14.8 V + gf_5045x3 | 1 / 10 | **10 / 10** |
| `T_hover_motor` (2.88 kg, 4 motors) | not computed | **7.063 N** |
| `P_motor_input` / motor | 592 W (bench max) | **~251.6 W** (interpolated) |
| `hover_energy_autonomy_min` | absent / wrong | **~1.32 min** |
| `motor_op_power_w` @ bind | 592 W | **592 W unchanged** (feasibility bridge) |

**Regime statement (locked):** 592 W remains **correct for 12.55 N**; hover energy must resolve at **~7.06 N**.

### 1.3 Architecture (locked framing)

```text
             ┌── deterministic physics ──► mass → weight → T_hover_motor
             │
ProjectState ┤
             │
             └── experimental OP dataset ──► exact / bracket / interpolate
                                             │
                                             ▼
                                      P_motor_input (per motor)
                                             │
                                             ▼
                                      hover_energy_autonomy_min
```

**Authority split:** Jarvis computes hover **demand**; catalog OP rows authorize thrust↔power **only**.

---

## 2. Locked semantics (non-negotiable)

### 2.1 Hover thrust demand (★3)

```text
T_hover_total = weight_n                    # NOT weight_n × safety_factor
T_hover_motor = T_hover_total / motor_count # motor_count from params; require >= 1
```

- Computed in `calculation_engine.py` **after** `weight_n` is known.  
- **Do not** rename `required_thrust_n` / `thrust_per_motor_required_n` — they keep `safety_factor` for sim margin only.

### 2.2 Resolver split (★5 / ★9)

| Function | When | Thrust policy | Consumers |
|---|---|---|---|
| `resolve_operating_point(...)` | **Bind time** (`component_writers.set_motor_component`) | Existing: exact/fallback/legacy; max thrust among exact rows | `motor_op_*`, `per_motor_max_thrust_n`, feasibility |
| **`resolve_operating_point_at_thrust(...)`** | **Calc time** (`calculation_engine.build`) | Exact match on `thrust_n` (ε); else bracket + linear interp; else UNVERIFIABLE | `motor_hover_*`, `hover_energy_autonomy_min` |

**Signature (minimum):**

```python
def resolve_operating_point_at_thrust(
    motor_sku: str,
    *,
    propeller_sku: str | None,
    voltage_v: float | None,
    target_thrust_n: float,
    library: ComponentLibrary | None = None,
) -> ResolvedHoverOperatingPoint: ...
```

**New result type `ResolvedHoverOperatingPoint`** — **do not** extend `ResolvedOperatingPoint` / `resolution_type` Literal (regression-safe for P2-1/MOP).

Required fields (minimum):

| Field | Notes |
|---|---|
| `target_thrust_n` | Input demand |
| `thrust_n` | Resolved thrust (exact or interpolated target) |
| `current_a`, `power_w` | Motor input at resolved point |
| `source_type` | `manufacturer_test` \| `measured_test` \| `interpolated` \| `unverifiable` |
| `interpolation_axis` | `"thrust_n"` when interpolated |
| `method` | `"linear"` when interpolated |
| `bounded` | `true` when interpolated |
| `source_points` | Two dicts `{thrust_n, power_w, current_a}` when interpolated |
| `motor_sku`, `propeller_sku`, `voltage_v` | Identity |
| `selection_reason` | e.g. `"exact_thrust"`, `"bracket_interpolate"`, `"below_min"`, `"above_max"`, `"insufficient_rows"` |

### 2.3 Interpolation policy (★4 / ★★5 / ★★6)

**Permitted:** linear interpolation on **`thrust_n`** between two eligible rows where:

```text
row_low.thrust_n ≤ target_thrust_n ≤ row_high.thrust_n
```

Both rows: same `motor_sku`, `propeller_sku`, `voltage_v` (within `_OP_VOLTAGE_EPSILON_V`), `fallback_only=false`, not `evidence_status=="hold"`, `source_type ∈ {manufacturer_test, measured_test}`.

Interpolate `power_w` and `current_a` independently on thrust axis. Set `source_type="interpolated"`.

**Forbidden:**

- Extrapolation below `min(thrust_n)` or above `max(thrust_n)` → `source_type="unverifiable"`, no power/current.  
- Proportional scaling `(T_req/T_max)×P_max`.  
- Curve fit across N points.  
- Fewer than **2** eligible rows → cannot interpolate (Combo B case).

### 2.4 Output naming & honesty (★10 / Engineer naming lock)

| Output | Meaning |
|---|---|
| `motor_hover_power_w` | `P_motor_input` per motor at hover thrust resolution |
| `motor_hover_current_a` | Matching bench current (exact or interpolated) |
| `hover_energy_autonomy_min` | Minutes from hover motor input power — **not** “real flight time” |
| `autonomy_min` (bundle) | For aerial multirotor when hover pipeline **succeeds**: **mirror** `hover_energy_autonomy_min`. When **unverifiable**: **`None`** — **do not** fall back to `motor_op_power_w` / `effective_motor_power_w` |

Persist calc provenance additively in `current_parameters`:

```json
"hover_energy_resolution": "{...json...}"
```

Include at minimum: `source_type`, `target_thrust_n`, `T_hover_motor`, `P_motor_input`, `source_points` when interpolated.

**CLI / estado:** extend existing propulsion evidence pattern (`adapters/cli/main.py` ~270–303) with one line, e.g.:

```text
Energía hover (evidencia): interpolated · P_motor_input=251.6 W/motor · hover_energy_autonomy_min≈1.3 min
```

Must state this is **bench motor input power**, not pack/system consumption.

### 2.5 Preserved semantics (do not break)

| Rule | Status |
|---|---|
| `motor_power_w` never overwritten | **Unchanged** |
| `motor_op_*` written at bind from `resolve_operating_point` | **Unchanged** |
| MOP voltage gate / `propulsion_resolution` | **Unchanged** |
| `electrical_compatibility` uses bench `motor_op_current_a` | **Unchanged** (★6) |
| ESC not in OP identity | **Unchanged** (★★8) |
| Combo A/A′/B probes (pre-hover) | **Must still PASS** after P25-D; extend with new probe in P25-H |

### 2.6 Forbidden in this IC

- ESC efficiency, cable loss, battery sag, discharge curve, temperature model  
- RPM required on new catalog rows (may be `null`)  
- Ct/Cp aerodynamic model  
- Cruise/climb/wind/mission profiles  
- DSE / G24-B changes  
- New subsystem module (`flight_energy.py` as parallel owner)  
- Weakening tests to hide 0.5625 → 1.32 transition  

---

## 3. Implementation slices (execute in order)

### P25-D — DATA: Combo A discrete OP dataset (★7)

**Goal:** 10/10 manufacturer_test rows for `sunnysky_r2205_2500` + `gf_5045x3` @ 14.8 V.

**File:** `library/motores/_datos.json` — extend `sunnysky_r2205_2500.operating_points[]`.

**Add 9 rows** (200 gf–1000 gf). Shape matches existing 1280 gf row:

```json
{
  "propeller_sku": "gf_5045x3",
  "voltage_v": 14.8,
  "thrust_n": <from table>,
  "current_a": <from table>,
  "power_w": <from table>,
  "fallback_only": false,
  "source_type": "manufacturer_test",
  "confidence": 0.97,
  "source_reference": "https://img.banggood.com/file/products/20181018062904ER22052500KV.pdf",
  "source_note": "R2205 KV2500 table: GF5045x3, 14.8 V, <gf> gf, ...",
  "approved_by": "Engineer research pass",
  "approved_date": "2026-09-01"
}
```

**Authoritative values** (from investigation contract / Engineer table):

| gf | thrust_n | current_a | power_w |
|---:|---:|---:|---:|
| 200 | 1.961 | 2.7 | 40 |
| 300 | 2.942 | 4.7 | 70 |
| 400 | 3.923 | 7.1 | 105 |
| 500 | 4.903 | 9.7 | 144 |
| 600 | 5.884 | 13.0 | 192 |
| 700 | 6.864 | 16.3 | 241 |
| 800 | 7.845 | 19.8 | 293 |
| 900 | 8.826 | 23.8 | 352 |
| 1000 | 9.807 | 27.9 | 413 |

(1280 gf row already present — do not mutate its numbers.)

**Optional fields:** `rpm`, `efficiency_gf_per_w` — **may be null** in v1 (no calc consumer). Source from PDF in same PR if easy; not blocking.

**Tests (P25-D):**

- `tests/test_catalog_foundation_v1.py` or `tests/test_phase2_lookup_operating_point.py`:
  - `sunnysky_r2205_2500` has **10** active OP rows for `gf_5045x3` @ 14.8 V.  
  - All new rows `source_type == "manufacturer_test"`, `fallback_only is False`.  
  - `thrust_n` strictly increasing across curated set (sanity).  
- Existing resolver tests for max-thrust bind path **still pass** (regression).

**Acceptance P25-D:** suite green; combo probe 3/3; no `resolve_operating_point_at_thrust` yet.

---

### P25-H — PHYSICS: Hover energy pipeline (★9 / ★11 / ★★12)

**Goal:** Autonomous calc-time chain → `hover_energy_autonomy_min`.

#### P25-H1 — Library resolver

**File:** `src/jarvis/knowledge/library.py`

- Add `ResolvedHoverOperatingPoint` dataclass.  
- Implement `resolve_operating_point_at_thrust` per §2.2–2.3.  
- Filter rows: matching prop + voltage; exclude `evidence_status=="hold"`.  
- Unit tests in `tests/test_phase2_lookup_operating_point.py` (new class `TestResolveOperatingPointAtThrust`):
  - Combo A @ `target_thrust_n=7.0632` → interpolated ~251.6 W (tolerance ±0.5 W).  
  - Exact hit @ 12.552 → 592 W, `manufacturer_test`.  
  - Below 1.961 N → `unverifiable`.  
  - Above 12.552 N → `unverifiable`.  
  - Single-row motor (Combo B fixture or tmp catalog) → cannot interpolate.

#### P25-H2 — Calculation engine wiring

**File:** `src/jarvis/core/calculation_engine.py`

After `weight_n` computed:

1. Derive `T_hover_motor` (§2.1).  
2. Resolve catalog identities from params/components mirror:
   - Prefer bound motor/prop/battery catalog refs if present in parameters (investigate existing param mirrors; minimum: read SKUs from params if already mirrored, else require catalog-bound project path for v1).  
   - Pack voltage: same derivation as MOP (`nominal_voltage` / cells × 3.7).  
3. Call `resolve_operating_point_at_thrust(...)`.  
4. On success: set `motor_hover_power_w`, `motor_hover_current_a`, compute `hover_energy_autonomy_min`.  
5. On unverifiable: omit hover fields; `hover_energy_autonomy_min=None`; emit `ToolResult` reason e.g. `hover_energy_unverifiable`.  
6. **`autonomy_min`:** set from `hover_energy_autonomy_min` when present; **never** use `effective_motor_power_w` for aerial hover path when motor+prop catalog-bound.  
7. **`effective_motor_power_w`:** remove aerial hover use; may remain unused or deprecated — **no production caller** besides autonomy (investigation confirmed).

**Schema:** extend `CalculationBundle` in `schemas/tool_schema.py` with `hover_energy_autonomy_min: float | None`.

**Params mirror (additive):** `hover_energy_resolution` JSON string; `motor_hover_power_w`; `motor_hover_current_a`; optional `T_hover_motor` for probes.

**Scope v1 gate:** hover pipeline runs when **all** hold:

- `vehicle_type` aerial multirotor (existing `AERIAL_VEHICLE_TYPES` set),  
- `motor_count >= 1`,  
- `weight_n` known,  
- motor + propeller + voltage resolvable for OP dataset lookup (catalog-bound components on `ProjectState` — wire via passing needed SKUs from orchestrator calc path or reading from params if component writers mirror them; **investigation minimum: Combo A bind path must work end-to-end**).

Freeform/unbound projects: **no hover energy** (honest absence — do not invent).

#### P25-H3 — Display honesty

**File:** `src/jarvis/adapters/cli/main.py` (or existing estado helper)

- One additive line for hover energy evidence when `hover_energy_resolution` present.  
- Wording must include **bench motor input** disclaimer per §2.4.

#### P25-H4 — Probes & regression

**New:** `scripts/cli_probe_phase25_hover_energy.py` (or extend combo probe with Combo A hover section)

Must assert on Combo A (`payload_kg=1.718`, defaults → `total_mass_kg≈2.88`):

| Assert | Expected |
|---|---|
| `T_hover_motor` | ≈ 7.063 N (±0.01) |
| `motor_hover_power_w` | ≈ 251.6 W (±1 W) |
| `hover_energy_autonomy_min` | ≈ 1.32 min (±0.05) |
| `motor_op_power_w` | still **592** (bind bridge unchanged) |
| `hover_energy_resolution.source_type` | `interpolated` |

Combo B / extrapolation-negative: document `unverifiable` in probe or test.

Update `scripts/cli_probe_minimum_universe_combo.py` **only** if needed to avoid asserting old 0.5625 min as “correct” autonomy — prefer **new probe** so combo probe stays Phase 2 regression.

**Acceptance P25-H:** full suite green (fix **pre-existing** 2 failures on baseline if trivially in scope — otherwise document unchanged); new probe PASS; combo probe 3/3; Combo A hover trace matches investigation.

---

## 4. Files touched (expected)

| File | P25-D | P25-H |
|---|---|---|
| `library/motores/_datos.json` | ✓ | |
| `src/jarvis/knowledge/library.py` | | ✓ |
| `src/jarvis/core/calculation_engine.py` | | ✓ |
| `src/jarvis/schemas/tool_schema.py` | | ✓ |
| `src/jarvis/adapters/cli/main.py` | | ✓ (display) |
| `tests/test_phase2_lookup_operating_point.py` | ✓ loader | ✓ resolver |
| `tests/test_catalog_foundation_v1.py` | ✓ row count | |
| `scripts/cli_probe_phase25_hover_energy.py` | | ✓ new |

**Explicitly not touched:** `electrical_compatibility.py`, `design_explorer.py`, `library/esc/`, DSE grids.

---

## 5. Verification checklist

| # | Check |
|---|---|
| 1 | `pytest -q` — full suite green |
| 2 | `python scripts/cli_probe_minimum_universe_combo.py` — 3/3 |
| 3 | `python scripts/cli_probe_phase25_hover_energy.py` — PASS |
| 4 | Combo A: `hover_energy_autonomy_min` ≈ 1.32 min, **not** 0.56 min |
| 5 | Combo A: `motor_op_power_w` still 592 W |
| 6 | No proportional scaling code paths |
| 7 | `resolve_operating_point` bind behavior unchanged (MOP regression tests) |
| 8 | CLI shows hover energy disclaimer text |

---

## 6. Deliverables (implementer → reviewer)

1. Code + tests per §3  
2. `.jes/artifacts/implementation_report_phase25_hover_autonomy.md` — files changed, behavior delta, probe output, remaining risks  
3. Optional: `.jes/artifacts/implementation_review_phase25_hover_autonomy.md` (Cursor)

**No version bump / tag unless Engineer requests after review.**

---

## 7. Acceptance (Cursor implementation review)

| Verdict | Criteria |
|---|---|
| **PASS** | P25-D 10 rows; P25-H resolver + calc + probe; Combo A numbers; ★ locks respected; no forbidden scope |
| **PASS WITH NOTES** | RPM null on new rows; minor CLI wording |
| **FAIL** | Bench OP still drives hover autonomy; extrapolation; new subsystem; discharge logic changed; invented η |

---

## 8. Post-implementation roadmap (out of scope — do not implement here)

```text
Phase 2.5 v1 ✅ hover_energy_autonomy_min
      ↓
Future: P_battery / ESC η (sourced data only)
      ↓
Future: hover current as separate electrical fact
      ↓
Future: DSE ranking awareness (inherits via autonomy_min mirror)
      ↓
Future: Ct/Cp / mission profiles
```

---

## 9. Copy-paste prompt for Claude Code (implementer)

```text
You are the Implementer for Jarvis.

Read and execute:
  .jes/artifacts/implementation_contract_phase25_hover_autonomy.md

Engineer ★ ratified 2026-09-01 — implement in order P25-D then P25-H.

Baseline: 0e2e71c. Investigation report for numeric targets.

Locks:
  - T_hover_motor = weight_n / motor_count (NOT safety_factor)
  - resolve_operating_point_at_thrust in library.py (new ResolvedHoverOperatingPoint)
  - Bounded linear interpolation only; no extrapolation; no (T/Tmax)*P
  - hover_energy_autonomy_min — NOT "real flight time"
  - autonomy_min mirrors hover when resolvable; None when unverifiable — no bench fallback
  - Do NOT change electrical_compatibility or DSE
  - Keep motor_op_* bind path unchanged

Deliver: code, tests, cli_probe_phase25_hover_energy.py, implementation_report artifact.
```

---

**End of contract.**
