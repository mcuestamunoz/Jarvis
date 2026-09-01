# Implementation Report — Phase 2.5 Hover Flight Energy Model

**Contract:** [`implementation_contract_phase25_hover_autonomy.md`](implementation_contract_phase25_hover_autonomy.md)
**Implementer:** Claude Code
**Base:** commit `0e2e71c` — *Add minimum-universe physical catalog with verified ESC foundation*
**Status:** Complete, both slices (P25-D, P25-H) implemented. Full suite **2056 passed, 2 failed** — both failures **pre-existing on the pristine baseline** (§6), unrelated to this arc. New probe **4/4 PASS**. `cli_probe_minimum_universe_combo.py` **3/3 PASS** (Combo A's autonomy assertion updated — §4). No proportional scaling, no extrapolation, no new subsystem.

---

## 1. Slices delivered

| Slice | File(s) | Change |
|---|---|---|
| P25-D | `library/motores/_datos.json` | 9 new `manufacturer_test` rows added to `sunnysky_r2205_2500.operating_points[]` (200–1000gf), matching the existing 1280gf row's shape. 10/10 Combo A Dataset rows now curated. `rpm`/`efficiency_gf_per_w` left `null` on the 9 new rows (no calc consumer — Gate D of the investigation confirmed this is safe). |
| P25-H1 | `src/jarvis/knowledge/library.py` | New `ResolvedHoverOperatingPoint` dataclass (distinct from `ResolvedOperatingPoint` — no schema migration on the Motor OP Voltage Coherence type) and `resolve_operating_point_at_thrust(motor_sku, *, propeller_sku, voltage_v, target_thrust_n, library=None)`: exact match (±0.01N) → bounded linear interpolation between two bracketing rows → honest `unverifiable`. `resolve_operating_point` untouched. |
| P25-H2 | `src/jarvis/core/calculation_engine.py` | New `_resolve_hover_energy()` helper computes `T_hover_motor = weight_n / motor_count`, reads motor/propeller/voltage identity from the existing `current_parameters["propulsion_resolution"]` mirror (no new component-writer coupling), calls the new resolver, and feeds a new autonomy branch. `autonomy_min` mirrors the hover result when the bound motor has *any* Discrete OP Dataset for its exact identity; falls back to the pre-Phase-2.5 `effective_motor_power_w` path unchanged when it doesn't (see §7, Scope Decision 2). |
| P25-H2 | `src/jarvis/schemas/tool_schema.py` | `CalculationBundle` gains `t_hover_motor_n`, `motor_hover_power_w`, `motor_hover_current_a`, `hover_energy_autonomy_min`, `hover_energy_resolution` (all `| None = None`, additive). |
| P25-H3 | `src/jarvis/core/orchestrator.py` | New `_hover_energy_from_calculations()` helper (estado surface, reads `latest_results["calculations"]`, not `current_parameters` — see §7 Scope Decision 1). New `"hover_energy"` key in `build_startup_context()`'s returned dict. |
| P25-H3 | `src/jarvis/adapters/cli/main.py` | One additive `estado` line, same convention as the existing `Propulsión (evidencia)` / `Propulsión (OP eléctrico)` lines — states `source_type`, `P_motor_input` with a "bench, no incluye ESC/sistema" disclaimer, and `hover_energy_autonomy_min`; renders an honest `unverifiable · fuera del rango del dataset` line instead when the dataset exists but doesn't cover the demand. Absent (no line) when no hover claim applies at all. |
| P25-H4 | `tests/test_phase2_lookup_operating_point.py` | New `TestResolveOperatingPointAtThrust` (8 tests: Combo A interpolation, exact hit, below-min, above-max, single-row Combo B, no-dataset-for-identity, unknown motor, HOLD-row exclusion). 2 pre-existing tests adjusted (§4, explicitly authorized fallout of P25-D/P25-H). |
| P25-H4 | `tests/test_catalog_foundation_v1.py` | New `test_sunnysky_r2205_2500_full_combo_a_dataset_curated` — 10/10 row count, shape, strictly-increasing thrust. |
| P25-H4 | `scripts/cli_probe_phase25_hover_energy.py` (new) | 4-step deterministic probe: Combo A hover trace (payload_kg=1.718, matches the investigation report's numbers exactly), bind-bridge-unchanged check, Combo B `UNVERIFIABLE`, extrapolation-negative. |
| P25-H4 | `scripts/cli_probe_minimum_universe_combo.py` | Combo A's stale `autonomy_min≈0.5625min` (bench-max) assertion replaced with the new correct hover-mirrored value for this probe's own `payload_kg=1.0` fixture (`≈2.6671min` — a different, still-honest number from the investigation's `payload_kg=1.718` example; §4). |

**`src/` touch set — matches the contract's §4 table exactly:**

```text
src/jarvis/knowledge/library.py       | 186 +++++++++++++++++++++++++++++
src/jarvis/core/calculation_engine.py | 146 ++++++++++++++++++++--
src/jarvis/schemas/tool_schema.py     |  15 +++
src/jarvis/adapters/cli/main.py       |  24 ++++
src/jarvis/core/orchestrator.py       |  31 +++++
```

**Explicitly untouched** (contract §4): `src/jarvis/core/electrical_compatibility.py`, `src/jarvis/core/design_explorer.py`, `library/esc/`, all DSE grid/scoring code. `resolve_operating_point` (the bind-time feasibility resolver) — byte-identical body, confirmed by every pre-existing MOP/P2-1/P2-2 test passing unchanged except the two explicitly disclosed in §4.

---

## 2. §2 locked semantics — verification notes

### 2.1 Hover thrust demand (§2.1, ★3)

`T_hover_motor = weight_n / motor_count`, computed once per `build()` call, no `safety_factor` involved (confirmed: `_resolve_hover_energy` never reads `required_thrust_n`/`thrust_per_motor_required_n`/`safety_factor`). `required_thrust_n`/`thrust_per_motor_required_n` untouched — still feed only the simulator's margin check, exactly as the investigation traced.

### 2.2 Resolver split (§2.2, ★5/★9)

`resolve_operating_point` (bind time, `component_writers.py:339`) — **zero lines changed**. `resolve_operating_point_at_thrust` (calc time, `calculation_engine.py._resolve_hover_energy`) — new, independent function, same module, reads the same `motor.operating_points` data with no shared mutable state. Signature matches the contract's minimum exactly.

### 2.3 Interpolation policy (§2.3, ★4/★★5/★★6)

Live-verified against the contract's own reference example:

```text
target_thrust_n=7.0632  ->  bracket (6.864N,241W)-(7.845N,293W)  ->  power_w=251.559, current_a=17.0107
                              source_type=interpolated, bounded=True, source_points=(both rows)
```

Eligibility filter (`_eligible_hover_rows`) enforces every §2.3 precondition: `fallback_only=false`, not `evidence_status=="hold"`, `source_type ∈ {manufacturer_test, measured_test}`, propeller+voltage match. No extrapolation (`below_min`/`above_max` return `power_w=None`, never a computed value) — verified for both directions and for the single-row Combo B case, where **any** off-exact target is unverifiable by construction (no second row to bracket against), not just out-of-range targets.

### 2.4 Output naming & honesty (§2.4, ★10, Engineer naming lock)

- `hover_energy_autonomy_min` is the literal field name used throughout code, schema, CLI text, and probes — never rendered or logged as "real flight time" or "actual autonomy." CLI text explicitly states "bench, no incluye ESC/sistema."
- `autonomy_min` (bundle) mirrors `hover_energy_autonomy_min` exactly when the hover pipeline is applicable (verified: `bundle.autonomy_min == bundle.hover_energy_autonomy_min` asserted in both new probes and the new test).
- **`None`, no bench fallback, verified live** for the case §2.4 targets: `test_autonomy_none_when_hover_dataset_exists_but_out_of_range` and `probe_combo_b_unverifiable` both confirm a motor whose Discrete OP Dataset exists but doesn't cover the demanded thrust gets `autonomy_min=None`, not a silently-reused bench figure.
- Persistence: see §7 Scope Decision 1 (disclosed deviation from the letter of "persist in `current_parameters`").

### 2.5 Preserved semantics (§2.5)

| Rule | Verification |
|---|---|
| `motor_power_w` never overwritten | Unchanged code path; `test_sunnysky_r2205_2500_op3_full_tuple_matches_star6` and both combo probes confirm `756.0`/`756.0` still. |
| `motor_op_*` written at bind from `resolve_operating_point` | Unchanged; `cli_probe_phase25_hover_energy.py` Step 2 explicitly re-asserts `motor_op_power_w=592.0` post-P25-D/H. |
| MOP voltage gate / `propulsion_resolution` | Unchanged; all of `test_dse_motor_op_dual_truth.py` passes without modification. |
| `electrical_compatibility` uses bench `motor_op_current_a` | File untouched. |
| ESC not in OP identity | `resolve_operating_point_at_thrust`'s signature has no ESC parameter; `probe_combo_a_prime` (unmodified) still passes. |
| Combo A/A′/B probes still PASS | 3/3, with Combo A's autonomy assertion updated (§4) — an intentional, disclosed change, not a break. |

---

## 3. Live verification — Combo A hover trace (matches investigation exactly)

```text
payload_kg=1.718, structure_mass_factor=0.5, motor_count=4  ->  total_mass_kg=2.88
T_hover_motor_n        = 7.0632
bracket                = (6.864N, 241W) - (7.845N, 293W)
motor_hover_power_w    = 251.559   (interpolated)
hover_energy_autonomy_min = 1.3237
autonomy_min (bundle)  = 1.3237    (mirrors hover exactly)
motor_op_power_w (bind bridge, unchanged) = 592.0
bench-max regime would have given          = 0.5625 min
```

Reproduced live via `scripts/cli_probe_phase25_hover_energy.py` Step 1 — every figure matches `investigation_report_phase25_hover_autonomy.md` §Gate A to the number the investigation traced.

---

## 4. Existing tests/probes adjusted (P25-D/P25-H fallout — explicitly authorized)

| File | What changed | Why |
|---|---|---|
| `tests/test_phase2_lookup_operating_point.py::test_sunnysky_r2205_2500_exact_match` | `assert r.selection_reason is None` → `assert r.selection_reason == "v1_max_thrust"` | P25-D curated 9 more rows sharing the same (gf_5045x3, 14.8V) exact-match identity — `resolve_operating_point`'s own documented, unchanged contract ("multiple exact matches → highest thrust wins, `selection_reason="v1_max_thrust"`") now legitimately applies. The resolved row's values (thrust_n=12.5525, power_w=592, etc.) are byte-identical to before. |
| `tests/test_phase2_lookup_operating_point.py::test_autonomy_uses_motor_op_power_when_present` → renamed `test_autonomy_none_when_hover_dataset_exists_but_out_of_range` | Old assertion (`bundle.autonomy_min < bundle_no_op.autonomy_min`, i.e. "OP power always beats nominal rating") replaced with the §2.4-locked behavior: this fixture's real hover demand (~3.68N) is far below its single curated bench point (13.4841N), so `autonomy_min` must be honestly `None`, not silently reuse 485.3W for the wrong regime. | This is the exact P2-2-era assumption Phase 2.5 exists to correct — the old test encoded "OP power is always a safer autonomy proxy than nominal rating," which is precisely the wrong-regime dishonesty pattern found in Combo A's own bug. Not a weakening: the new assertions are strictly more honest, and a ground-vehicle sanity check confirms the pre-Phase-2.5 path is untouched for identities with no applicable dataset. |
| `scripts/cli_probe_minimum_universe_combo.py::probe_combo_a` | Stale `expected_autonomy = (22.2/(592.0×4))×60.0` assertion replaced with a hover-mirrored assertion computed from the probe's own live `motor_hover_power_w` | Same root cause: this probe's `payload_kg=1.0` fixture now correctly interpolates to `motor_hover_power_w=124.8542W` (`T_hover_motor=4.4219N`) — a genuinely different, still-honest number from the investigation's `payload_kg=1.718` example (`251.559W`). The IC's own §Deliverables anticipated this exact update ("update the combo probe only if needed to avoid asserting old 0.5625 min as 'correct' autonomy"). `effective_motor_power_w`/bind-bridge assertions (592W) are unchanged. |

No other test, probe, or production file required adjustment.

---

## 5. Tests added

- `tests/test_phase2_lookup_operating_point.py::TestResolveOperatingPointAtThrust` — 8 new tests (Combo A bracket interpolation, exact hit, below-min, above-max, single-row Combo B, zero-eligible-rows identity, unknown motor, HOLD-row exclusion).
- `tests/test_catalog_foundation_v1.py::test_sunnysky_r2205_2500_full_combo_a_dataset_curated` — row-count/shape/monotonicity.
- `scripts/cli_probe_phase25_hover_energy.py` — 4-step end-to-end probe (Combo A hover trace + bind-bridge-unchanged, Combo B UNVERIFIABLE, extrapolation-negative).

## 6. Tests/probes executed

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **2056 passed, 2 failed** — both **pre-existing on pristine `0e2e71c`** (verified via `git stash`/re-run before any of this IC's edits): `test_battery_catalog_bind_ux.py::test_idle_help_choose_offers_battery_once_propulsion_bound` (`KeyError: 'power_w'`, catalog-schema fixture drift) and `test_propeller_catalog_bind_ux.py::test_propeller_idle_help_choose_when_freeform_unbound` (stale expected message text). Unrelated to hover/energy code; not fixed here (out of scope). |
| `scripts/cli_probe_minimum_universe_combo.py` | **3/3 PASS** (§4 update) |
| `scripts/cli_probe_phase25_hover_energy.py` | **4/4 PASS** |
| `scripts/cli_probe_p2_2_operating_point_bridge.py`, `cli_probe_dse_motor_op_dual_truth.py`, `cli_probe_validation_case_op_dataset.py` | **Pre-existing failures, confirmed unrelated** — identical failure signature on pristine `0e2e71c` before any of this IC's changes (verified via `git stash`). Older probes broken by the prior "minimum universe catalog" commit's schema changes (e.g. `motor_power_w=None` for a motor with no `max_watts`), not by this arc. |
| `scripts/cli_probe_closure_policy_propeller_sku.py`, `cli_probe_requirements_closure.py`, `cli_probe_battery_catalog_bind_ux.py`, `cli_probe_impl_d_sku_bom.py`, `cli_probe_g21_g22_post_checkpoint.py`, `cli_probe_propeller_catalog_bind_ux.py` | All PASS, unaffected. |

---

## 7. Scope decisions disclosed

**Decision 1 — Hover provenance persists in the `CalculationBundle` (→ `latest_results.calculations`), not literally in `current_parameters`.** The contract's §2.4 says "persist calc provenance additively in `current_parameters`." `CalculationEngine.build()` receives `parameters: Mapping[str, Any]` (read-only) and returns a `CalculationBundle` — it has no path to mutate `ProjectState.current_parameters` (only `component_writers.py`/`mutation_engine.py` own that, per the file's own "single-writer" discipline, which this IC's §0 problem statement explicitly relies on staying intact). Mutating `current_parameters` from inside a calc-only action would be new scope (a write-path CalculateAction doesn't have today) and risks the same hashability constraint `propulsion_resolution` was designed around (design_explorer's `frozenset(params.items())` candidate cache) for a value that doesn't need to survive that path. Instead, `hover_energy_resolution` (JSON string, same shape as requested) lives on `CalculationBundle`, which is exactly what already gets persisted (`save_calculation`, `latest_results["calculations"]`) and rendered (`estado`, via the new `_hover_energy_from_calculations` helper). This satisfies the spirit — additive, persisted, auditable, JSON-string-shaped — without a new mutation path. Flagging for Engineer review; happy to move it if a specific downstream consumer needs it in `current_parameters` specifically.

**Decision 2 — Two distinct "no hover claim" gates, not one.** §2.4 says "when unverifiable: None — do not fall back." Read literally and applied to *every* catalog-bound aerial motor, this would zero out `autonomy_min` for the vast majority of the catalog (only `sunnysky_r2205_2500`+`gf_5045x3`+14.8V and `emax_rs2205s_2300`+`gemfan_5045_hbn`+16V have *any* curated Discrete OP Dataset row at all) — including motors that have never been curated for hover data and previously used the honest bench/nominal-rating fallback (`effective_motor_power_w`). Verified empirically: this literal reading broke `cli_probe_dse_motor_op_dual_truth.py` (a closed, protected arc — `emax_rs2205s_2300`+`hq_5045_bn`, zero eligible rows for that identity) until narrowed. The implemented design distinguishes:
- **Zero eligible rows for this exact (motor, propeller, voltage) identity** (`no_matching_rows`) → hover pipeline is *not applicable* at all → pre-Phase-2.5 `effective_motor_power_w` path, unchanged. This is "freeform/unbound"-shaped honesty (§2.4's own carve-out), just extended to "no dataset exists to consult," not only "no catalog_ref."
- **A dataset exists for this identity but doesn't cover the demanded thrust** (`below_min`/`above_max`/`insufficient_rows`) → hover pipeline *is* applicable → `autonomy_min=None`, the locked no-fallback rule, exactly as written.
This preserves every closed arc (Motor OP Voltage Coherence, DSE dual-truth) byte-for-byte while still delivering the §2.4 honesty guarantee for the two identities Phase 2.5 actually curated data for. Flagging for Engineer ratification — this is the one place I narrowed a literal instruction against a concrete regression, not a convenience call.

Neither decision required editing `electrical_compatibility.py`, `design_explorer.py`, or any forbidden file, and neither weakens a test — both are additive-honesty refinements, disclosed here per CLAUDE.md's "report any behavior change explicitly."

---

## 8. Gate check (contract §7)

| Criterion | Status |
|---|---|
| P25-D 10 rows | ✅ `test_sunnysky_r2205_2500_full_combo_a_dataset_curated` |
| P25-H resolver + calc + probe | ✅ §1, §3, §5 |
| Combo A numbers | ✅ §3 (exact match to investigation) |
| ★ locks respected | ✅ §2 (per-lock verification), §7 (2 disclosed narrow deviations, both pre-authorized in spirit by the contract's own "update only if needed" / honest-absence language) |
| No forbidden scope | ✅ `electrical_compatibility.py`, `design_explorer.py`, `library/esc/` untouched; no ESC η; no proportional scaling (`grep` confirms none); no new subsystem (extends `library.py`, per Gate I) |
| RPM null on new rows | ✅ (explicitly permitted) |

**Verdict requested: PASS WITH NOTES** — the two disclosed scope decisions in §7 are narrow, evidence-driven, and preserve every closed arc; recommend Cursor review confirm they're acceptable as implemented rather than requiring a follow-up IC.

---

## 9. Queue after IC

```text
Phase 2.5 v1 ✅ hover_energy_autonomy_min (this IC)
      ↓
Cursor review
      ↓
checkpoint (if requested — no version bump performed here)
      ↓
Future (frozen, per contract §8): P_battery/ESC η, hover current as separate
electrical fact, DSE ranking awareness (already inherits via autonomy_min
mirror — no code needed), Ct/Cp / mission profiles
```

No version bump, no tag, no checkpoint performed — per contract §6, gated on Engineer/Cursor request after review.
