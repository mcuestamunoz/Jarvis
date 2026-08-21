# Implementation Report — Phase 2 P2-1 Lookup Operating Point

**Contract:** [`implementation_contract_phase2_lookup_operating_point.md`](implementation_contract_phase2_lookup_operating_point.md)
**★6 dataset:** [`phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — used verbatim, no invented numbers
**Checkpoint base:** `checkpoint-impl-d` (`24fa7ba`)
**Status:** Implemented — P2-1 through P2-6 complete. 16 new tests + CLI probe (5/5), full suite green (**1939 passed**, up from 1923 baseline). **Not committed.**

---

## 1. Files changed

| File | What |
|---|---|
| `library/motores/_datos.json` | **P2-1.** Added `emax_rs2205s_2300` (OP-0 fallback + OP-1/OP-2 exact rows) and `sunnysky_r2205_2500` (OP-3 exact row). `emax_rs2205_2300` and `sunnysky_r2305_2500` byte-unchanged. |
| `library/helices/_datos.json` | **P2-1.** Added `hq_5045_bn`, `gf_5045x3` (diameter/pitch/tags only — no `ct`/`cp`, not needed by lookup). |
| `src/jarvis/knowledge/library.py` | **P2-2.** New `ResolvedOperatingPoint` frozen dataclass + `resolve_operating_point()` pure function + `_resolved_from_op_row()` helper. No existing class/function touched. |
| `src/jarvis/core/component_writers.py` | **P2-3.** `set_motor_component`: when `spec.catalog_ref` is a motor SKU, resolves propeller/voltage context from bound components and calls `resolve_operating_point`; writes `per_motor_max_thrust_n` from the resolution and a JSON-string `propulsion_resolution` param; updates the component's `thrust_n` property (not `catalog_ref`) for exact/fallback resolutions. Freeform/unbound motors fall through to the original Impl C bridge branch, byte-identical. |
| `src/jarvis/core/orchestrator.py` | **P2-4 (data).** `build_startup_context` adds `"propulsion_resolution"` to its return dict, parsed from the JSON string via new `_parse_propulsion_resolution()` helper. |
| `src/jarvis/adapters/cli/main.py` | **P2-4 (surface).** `render_startup_context` renders one honest evidence line ("Propulsión (evidencia): …") when `propulsion_resolution` is present; never shown for freeform motors. |
| `tests/test_phase2_lookup_operating_point.py` | **P2-5.** New — 16 tests (resolver contract, bridge, estado surface, regression). |
| `scripts/cli_probe_phase2_lookup_op.py` | **P2-6.** New — CLI probe, 5/5 PASS. |

No changes to `calculation_engine.py`, `simulator.py`, `engineering_readiness.py`, `project_continuity.py`, `project_closure.py` (BOM), `catalog_bind.py`, `design_explorer.py`'s scoring/grids, or `PropertyValue.source`'s `Literal`. Confirmed via `git diff --stat -- src/ library/ tests/ scripts/`: exactly the 6 files above + 2 new test/probe files.

---

## 2. Behavior changed (and explicitly what did not)

**Changed:**
- A catalog-bound motor's `per_motor_max_thrust_n` is now resolved via `resolve_operating_point` instead of mirrored 1:1 from `MotorSpec.thrust_n`. For the two new SKUs with real `operating_points[]` data, this can differ from the bare catalog peak (e.g. `emax_rs2205s_2300` alone → 10.042 N fallback; with `hq_5045_bn` + ~16 V → 9.7086 N exact).
- `current_parameters["propulsion_resolution"]` (new key, JSON string) is written whenever the motor is catalog-bound, and popped when it's not (freeform motor).
- `estado` shows one new line when `propulsion_resolution` is present, labeling the evidence quality honestly (`exact_operating_point` / `fallback_operating_point` / `legacy_estimate`).

**Explicitly unchanged (verified, not assumed):**
- Every catalog-bound SKU with **zero** `operating_points[]` data (all 18 pre-existing motors, including `emax_rs2205_2300` and `sunnysky_r2305_2500`) resolves to `legacy_estimate` with `thrust_n` **numerically identical** to the pre-P2-1 bare `MotorSpec.thrust_n` value — proven by `test_bridge_legacy_resolution_for_catalog_motor_without_op_data` and `test_regression_brotherhobby_bind_still_works`.
- Freeform (non-catalog-bound) motors: zero code-path change — `resolved_op` stays `None`, original Impl C bridge branch runs unchanged, no `propulsion_resolution` written — proven by `test_bridge_legacy_path_for_freeform_motor_unchanged`.
- `calculation_engine.py`'s force-resolution chain, `FeasibilitySimulator`, `engineering_readiness.py` gap derivation, Impl D BOM (`build_component_bom`/`format_bom_lines`), G5 divergence semantics (`invalidate_diverged_catalog_refs`), `design_explorer.py`'s scoring policy and `EXPLORATION_GRIDS` — zero lines touched, confirmed by `git diff --stat`.
- `PropertyValue.source`'s `Literal["declared","inferred","calculated"]` — unchanged, per ★1. Provenance lives entirely on `ResolvedOperatingPoint`/the `propulsion_resolution` param, never widening that enum.

---

## 3. ★ compliance + SKU add list

| ★ | Compliance |
|---|---|
| ★1 (OP-only `source_type`, not widen `PropertyValue.source`) | Implemented exactly — `ResolvedOperatingPoint.source_type` is a plain `str` field, `PropertyValue` untouched. |
| ★2 (Option A — Lookup OP) | Implemented — no propeller-bind-mandatory UX, no full electro-mech; a curated table lookup with honest fallback. |
| ★3/★4 (G26/G27/G24 out of scope) | Untouched — no code in `semantic_intent_adapter.py`, `state_schema.py`, or `design_explorer.py`'s apply path was modified. |
| ★5 (provenance surface — IC detail) | Resolved as: `current_parameters["propulsion_resolution"]` (JSON string, for hashability — see §6 Note 1) + one `estado` line. |
| ★6 (dataset — final, no invention) | Used verbatim: `emax_rs2205s_2300` OP-0/OP-1/OP-2, `sunnysky_r2205_2500` OP-3, exactly as approved in `phase2_star6_operating_point_validation_case.md`. `emax_rs2205_2300` and `sunnysky_r2305_2500` confirmed byte-unchanged (`git diff` shows only additive JSON blocks appended after the existing content). |

**Engineer additional locks — all honored:**
- `fallback_only: true` (OP-0) → resolver returns `resolution_type="fallback_operating_point"` in code (not docs-only) — enforced by `resolve_operating_point`'s classification logic and proven by `test_fallback_when_no_propeller_bound` / `test_fallback_only_row_never_classified_as_exact`.
- Multi-exact-match → max `thrust_n` + `selection_reason="v1_max_thrust"` — proven by `test_exact_match_single_row` (OP-1 9.1986 N vs OP-2 9.7086 N at the same prop+voltage → 9.7086 wins).
- `efficiency_gf_per_w` stored and passed through as-is (g/W) — never interpreted as η∈[0,1] anywhere in `resolve_operating_point` or the bridge (the field is carried but not consumed by any calculation in this slice).
- `calculation_engine.py` / `FeasibilitySimulator` control flow untouched (§1 table, confirmed by `git diff --stat`).
- Impl D BOM schema not reopened (confirmed by `git diff --stat` — `project_closure.py` absent from the changed-files list).
- No `physics_engine.py` or second calc authority created — `resolve_operating_point` lives in `library.py`, the existing catalog reader module.

---

## 4. Tests added + commands run + results

`tests/test_phase2_lookup_operating_point.py` — 16 tests:

1. `test_exact_match_single_row` — OP-1/OP-2 dual match → max thrust 9.7086 N + `v1_max_thrust`.
2. `test_fallback_when_no_propeller_bound` — OP-0 → `fallback_operating_point`, 10.042 N.
3. `test_legacy_path_for_unenriched_motor` — `emax_rs2205_2300` (non-S) → `legacy_estimate`, 8.0 N; confirms RS2205S table never leaked onto it.
4. `test_sunnysky_r2305_2500_untouched_legacy` — confirms the untouched SKU still resolves legacy at 7.5 N.
5. `test_sunnysky_r2205_2500_exact_match` — OP-3 exact, 12.5525 N, rpm=27082, `selection_reason=None` (single match).
6. `test_fallback_only_row_never_classified_as_exact` — ★6 hard rule.
7. `test_unknown_motor_returns_none` — non-library SKU → `None`.
8. `test_voltage_mismatch_excludes_exact_but_not_fallback` — voltage far from exact rows still resolves via fallback.
9. `test_bridge_writes_exact_resolution` — bridge integration, 4S (~14.8V) doesn't match the 16.0V exact rows → honest fallback (not a fabricated exact match).
10. `test_bridge_writes_exact_resolution_with_matching_voltage` — real orchestrator project, propeller + battery-cell-count context → exact resolution, component `thrust_n` property updated, `catalog_ref` preserved.
11. `test_bridge_battery_catalog_ref_voltage_takes_precedence` — real battery SKU bind → catalog voltage drives exact resolution.
12. `test_bridge_legacy_path_for_freeform_motor_unchanged` — freeform motor, zero `propulsion_resolution`.
13. `test_bridge_legacy_resolution_for_catalog_motor_without_op_data` — regression contract: numeric byte-identity for any catalog SKU without OP data.
14. `test_estado_renders_honest_evidence_label` — real `render_startup_context` output contains the fallback line, `10.042 N`, `manufacturer_test`, and the "sin hélice de catálogo" honesty suffix.
15. `test_estado_hides_line_for_freeform_motor` — no line at all when nothing to report.
16. `test_regression_brotherhobby_bind_still_works` — spot-check byte-identical Impl C behavior.

```
python -m pytest tests/test_phase2_lookup_operating_point.py -v
# 16 passed

python -m pytest tests/test_impl_c_catalog_dse_thrust_bridge.py tests/test_impl_c_catalog_aware_dse.py \
  tests/test_impl_d_sku_bom.py tests/test_catalog_foundation_v1.py tests/test_d4_param_gatekeeper.py -v
# 60 passed (named Impl C/D regressions, zero modified assertions)

python -m pytest -q
# 1939 passed
```

1923 baseline (post-`checkpoint-impl-d`) + 16 new = 1939. Zero weakened tests — every named regression file passed byte-for-byte unchanged.

---

## 5. CLI probe result

`scripts/cli_probe_phase2_lookup_op.py` — **5/5 PASS**:

1. Real wizard: `definir propulsion` → `ayúdame a elegir` lists `emax_rs2205s_2300` as candidate `#5` (10.042N, 30.0g, 2300KV, ~400W) → picked by number (G21 path, unmodified) → bound.
2. `estado` (no propeller bound) → `Propulsión (evidencia): fallback_operating_point · manufacturer_test · 10.042 N (sin hélice de catálogo)`.
3. Propeller `hq_5045_bn` bound (test-callable `bind_propeller_from_catalog`, per IC §7 note — no live propeller-pick UX exists yet, same status as Impl C/D's battery-bind probes); motor re-resolved with propeller + ~16 V battery-cell-count context.
4. `estado` → `Propulsión (evidencia): exact_operating_point · manufacturer_test · 9.7086 N` — `v1_max_thrust` policy correctly picked the higher-thrust OP-2 over OP-1.
5. `sunnysky_r2305_2500` bound independently in the same session → resolves legacy at 7.5 N, confirming it was never touched by the new SKU additions.

---

## 6. Remaining risks / deferred

1. **Hashability constraint discovered and fixed during this slice (worth flagging for future Phase 2.x work):** `design_explorer.py`'s per-candidate evaluation cache keys on `frozenset(params.items())` (`design_explorer.py:537`). An earlier draft of this bridge wrote `propulsion_resolution` as a nested `dict` directly into `current_parameters`, which is unhashable and silently broke **every** catalog DSE candidate (caught via the existing `except Exception: continue` in that loop) — regression-tested via `tests/test_impl_c_catalog_aware_dse.py`/`test_impl_c_catalog_dse_thrust_bridge.py`, which is exactly how this was caught before it shipped. Fixed by storing `propulsion_resolution` as a JSON string (hashable) and parsing it back to a dict only at the `build_startup_context`/CLI boundary. **Any future Phase 2 param must stay a hashable value** — this is now a real, undocumented-elsewhere constraint on `current_parameters` values that a future IC should be aware of (not fixed at the `design_explorer.py` cache-key level in this slice, per the IC's "no scoring/DSE-machinery change" scope).
2. **Propeller-bind live UX still doesn't exist** (confirmed again in this slice) — the CLI probe's step 3 uses the test-callable `bind_propeller_from_catalog` API, same status as Impl C/D's battery-bind probes. A real product path (Continuity/assist) is future Phase 2.x work, not this slice.
3. **Multi-OP current-limit selection is v1/provisional** (`selection_reason="v1_max_thrust"`) — picking the highest-thrust exact match ignores that it also draws more current (27 A vs 25 A). No current-budget-aware selection exists yet; explicitly flagged as future Phase 2.x per the ★6 lock ("provisional").
4. **G27 remains open, independent debt** — untouched by this slice, as scoped.
5. **`efficiency_gf_per_w` is stored but not consumed anywhere yet** — no calc/sim path reads it in this slice; reserved for a future power/efficiency-aware cut.
