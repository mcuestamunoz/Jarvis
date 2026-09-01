# Implementation Review — Phase 2.5 Hover Flight Energy Model

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES) — **independent code + test verification** (not report paraphrase)  
**Contract:** [`.jes/artifacts/implementation_contract_phase25_hover_autonomy.md`](implementation_contract_phase25_hover_autonomy.md)  
**Report:** [`.jes/artifacts/implementation_report_phase25_hover_autonomy.md`](implementation_report_phase25_hover_autonomy.md)  
**Base:** commit `0e2e71c`

## Verdict

**PASS WITH NOTES**

P25-D and P25-H are implemented correctly and **in harmony** with closed arcs (P2-1/P2-2, MOP, DSE dual-truth, ERF-2 electrical). Combo A hover numbers match investigation. Bind-time feasibility path is untouched. Two disclosed scope deviations (§7) are **ratified**. Two doc/probe hygiene notes are **non-blocking** but must not be hidden.

---

## Review methodology (what was actually verified)

| Step | Action | Result |
|---|---|---|
| 1 | Full suite | `2056 passed, 2 failed` — same 2 failures as report; unrelated UX tests |
| 2 | Protected unit tests | `test_dse_motor_op_dual_truth.py` **5/5**; `TestResolveOperatingPointAtThrust` **8/8**; `test_phase2_lookup_operating_point` batch **80/80** |
| 3 | Phase 2.5 probe | `cli_probe_phase25_hover_energy.py` **4/4** — reviewer re-run |
| 4 | Combo probe | `cli_probe_minimum_universe_combo.py` **3/3** |
| 5 | Git diff vs `0e2e71c` | `component_writers.py`, `electrical_compatibility.py`, `design_explorer.py` → **0 lines changed** |
| 6 | Bind resolver unchanged | `resolve_operating_point` body — **no edits** in diff; only additive code at EOF in `library.py` |
| 7 | Catalog data | `sunnysky_r2205_2500` → **10** `manufacturer_test` rows @ 14.8 V + `gf_5045x3` — values match IC table |
| 8 | Forbidden patterns | No proportional scaling code; interpolation only in `resolve_operating_point_at_thrust` |
| 9 | Stale CLI probes | `cli_probe_dse_motor_op_dual_truth.py`, `cli_probe_p2_2_operating_point_bridge.py` — **0 diff since `0e2e71c`**; fail on current tree due to **prior catalog-schema drift** (EMAX `motor_power_w` absent), **not** Phase 2.5 regression |

---

## Contract checklist (IC §7)

| Criterion | Verified | Evidence |
|---|---|---|
| P25-D — 10/10 rows | **Pass** | `library/motores/_datos.json:264-424`; `test_sunnysky_r2205_2500_full_combo_a_dataset_curated` |
| P25-H — `resolve_operating_point_at_thrust` | **Pass** | `library.py:899-990`; 8 unit tests |
| Combo A: 7.063 N → 251.559 W → 1.3237 min | **Pass** | Probe Step 1 live |
| ★3 — hover thrust = weight/motor_count | **Pass** | `calculation_engine.py:108`; never reads `safety_factor` in `_resolve_hover_energy` |
| ★4–★★6 — bracket only; no extrapolation | **Pass** | `library.py:955-964`; probe Step 4 |
| ★5/★9 — bind vs calc resolver split | **Pass** | Bind: `component_writers.py:339`; calc: `_resolve_hover_energy` → `at_thrust` |
| ★6 — no electrical changes | **Pass** | `git diff 0e2e71c electrical_compatibility.py` → empty |
| ★8 — no DSE changes | **Pass** | `git diff 0e2e71c design_explorer.py` → empty |
| ★10 — `hover_energy_autonomy_min` + disclaimer | **Pass** | `tool_schema.py`; `main.py:305-327` |
| ★11/★★12 — autonomous pipeline | **Pass** | No manual thrust/row args; reads `propulsion_resolution` + mass |
| Forbidden scope | **Pass** | No ESC η, no new subsystem file |

---

## Harmony with prior code (critical for this phase)

### Feasibility / bind path — preserved

```text
set_motor_component
  → resolve_operating_point (unchanged)
  → motor_op_power_w = 592 W (Combo A max row)
  → per_motor_max_thrust_n / sim margin unchanged
```

Reviewer confirmed: **`component_writers.py` diff vs `0e2e71c` = 0 lines.** MOP voltage gate and `propulsion_resolution` JSON unchanged.

### Energy / autonomy path — new, does not overwrite bind semantics

```text
CalculationEngine.build
  → weight_n (existing)
  → T_hover_motor = weight_n / motors (new)
  → resolve_operating_point_at_thrust (new)
  → hover_energy_autonomy_min (new)
  → autonomy_min mirrors hover when hover_applicable
```

When **`hover_applicable=False`** (`no_matching_rows`): falls back to **`effective_motor_power_w`** — same pre-Phase-2.5 path. **DSE dual-truth unit tests pass** without modification → closed arc intact.

When **`hover_applicable=True`** but thrust out of range: **`autonomy_min=None`** — no bench fallback. Verified in renamed test + probe Step 3.

### Three power concepts — now explicit in runtime

| Field | Combo A (verified) | Role |
|---|---:|---|
| `motor_power_w` | 756 W | Nominal rating — unchanged |
| `motor_op_power_w` | 592 W | Bind bench-max — unchanged |
| `motor_hover_power_w` | 251.559 W | Calc-time hover regime — **new** |

No collision: bind writer never sets `motor_hover_*`; calc engine never overwrites `motor_op_*`.

### Import graph — intentional extension

New edge: `calculation_engine.py` → `library.resolve_operating_point_at_thrust`. Consistent with existing `component_writers.py` → `library.resolve_operating_point`. `library.py` remains leaf (no `jarvis.core` imports). Matches IC Gate I and CLAUDE.md “prefer existing resolvers.”

### Sim / margin vs hover energy — correctly separated

- `required_thrust_n = weight_n × safety_factor` → still feeds `thrust_per_motor_required_n` / simulator margin only (`calculation_engine.py:252-266`).  
- Hover energy uses **`weight_n / motor_count`** only — **does not** inflate by `safety_factor`. Confirms investigation Gate C correction.

---

## Scope decisions (report §7) — ratification

### Decision 1 — Provenance on `CalculationBundle`, not `current_parameters`

**Ratified.** `CalculationEngine.build()` is read-only for `ProjectState`. `hover_energy_resolution` on bundle + `orchestrator._hover_energy_from_calculations()` + `main.py` estado line satisfies auditability without violating single-writer discipline.

### Decision 2 — Two gates: `no_matching_rows` vs out-of-range dataset

**Ratified.** Verified empirically: `test_dse_motor_op_dual_truth.py` passes; EMAX/hq combo without hover dataset keeps legacy autonomy path. Combo B single-row case correctly returns `UNVERIFIABLE` when dataset exists but cannot bracket.

---

## Independent numeric verification (Combo A)

Reviewer re-ran `cli_probe_phase25_hover_energy.py`:

```text
T_hover_motor_n              = 7.0632
motor_hover_power_w          = 251.559  (interpolated, 700–800 gf bracket)
hover_energy_autonomy_min    = 1.3237
motor_op_power_w (bind)      = 592.0
motor_power_w (nominal)      = 756.0
bench-max autonomy would be  = 0.5625 min
```

Matches investigation report §Gate A to stated precision.

---

## Findings (defect-first)

### Open blockers

**None** for Phase 2.5 checkpoint.

### Note 1 — Stale docstring on `effective_motor_power_w` (harmony / doc debt)

```36:49:src/jarvis/core/calculation_engine.py
def effective_motor_power_w(parameters: Mapping[str, Any]) -> float | None:
    """P2-2 ... single authority for "what power draw should autonomy use" ...
```

Post-Phase-2.5, autonomy for `hover_applicable` motors **no longer** uses this helper — but the docstring still claims it is the single authority. **`build()` comments are updated** (lines 268-278); helper docstring is **misleading**. Recommend one-line doc fix in a hygiene commit — **not a functional bug**.

### Note 2 — Pre-existing suite / probe failures (not Phase 2.5)

| Failure | Cause | Phase 2.5? |
|---|---|---|
| `test_battery_catalog_bind_ux` | `KeyError: 'power_w'` on EMAX fixture | No — catalog schema |
| `test_propeller_catalog_bind_ux` | Stale help text | No |
| `cli_probe_dse_motor_op_dual_truth.py` | Expects `motor_power_w` on EMAX | No — probe unchanged since `0e2e71c` |
| `cli_probe_p2_2_operating_point_bridge.py` | Same | No |

**Do not** treat these as Phase 2.5 merge gate failures; **do** schedule hygiene before claiming “full green probes.”

### Note 3 — Combo probe autonomy figure ≠ investigation example

Combo probe uses `payload_kg=1.0` → different hover power/autonomy than investigation’s `payload_kg=1.718`. Probe assertion updated to live hover interpolation — **correct behavior**, not a regression.

---

## Tests adjusted (authorized fallout)

| Change | Reviewer assessment |
|---|---|
| `test_sunnysky_r2205_2500_exact_match` expects `v1_max_thrust` | **Correct** after 10 rows — same resolved values, honest selection_reason |
| `test_autonomy_none_when_hover_dataset_exists_but_out_of_range` | **Correct** — replaces P2-2-era wrong-regime assumption |
| Combo probe autonomy assertion | **Correct** — no longer asserts 0.5625 min as “good” |

---

## Engineer next step

```text
Implementation PASS WITH NOTES (verified)
  ↓
Commit: Phase 2.5 code + tests + probes + JES artifacts
         (investigation_contract/report, implementation_contract/report/review)
  ↓
Optional checkpoint: v0.3.5 / checkpoint-phase25-hover-energy
  ↓
Hygiene arc (separate): 2 pytest + stale DSE/P2-2 probes + effective_motor_power_w docstring
```

No commit taken by reviewer.

---

**Process note:** A first review draft was written before full independent verification. This document supersedes it and reflects **direct code inspection, git diff, and re-executed tests/probes** — the standard expected after every implementation contract.

**End of review.**
