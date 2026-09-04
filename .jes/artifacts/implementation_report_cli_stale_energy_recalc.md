# Implementation Report — CLI Continuity: recalc after watts-recovery pick

**IC:** [implementation_contract_cli_stale_energy_recalc.md](implementation_contract_cli_stale_energy_recalc.md)
**Ratification:** [engineer_ratification_cli_stale_energy_recalc.md](engineer_ratification_cli_stale_energy_recalc.md)
**Implementer:** Claude Code
**Date:** 2026-09-02

## Files changed

- `src/jarvis/core/project_continuity.py` — new `_await_autonomy_recalc_next_step` rank, wired between `_watts_recovery_next_step` and `suggested_action` in the `next_useful_step` elif chain. Added `catalog_bound_motor_lacks_nameplate_watts` to the existing `project_closure` import.
- `src/jarvis/core/reasoning_layer.py` — three guards, all gated on "SKU declares W" (`not self._catalog_bound_motor_lacks_watts(context)`) **and** `_detect_missing_energy_params(context)` empty:
  - `_build_insights`: skip the `"faltan parámetros de energía: ..."` insight when nothing is actually missing.
  - `_collect_suggested_actions`: return `[]` instead of falling back to the `"battery_capacity_wh, motor_power_w"` label when `missing_e` is empty.
  - `_build_tradeoffs`: skip the energy tradeoff line under the same condition (optional per IC, added for consistency — no test asserted its absence, none broke by adding it).
- `src/jarvis/core/orchestrator.py` — `_append_arch_progress_hint`: when architecture is complete, now checks `_autonomy_objective_undemonstrated(req, calc, sim)` (imported from `project_continuity`) via `derive_physical_requirements`; if true, returns the result unchanged (omits the `"✓ Arquitectura completa (...) — puedes optimizar o simular."` hint) so Continuity's footer is the single source of the next step on that turn.
- `tests/test_cli_stale_energy_recalc.py` — new. Two tests: (1) full walk — bind `emax_rs2205s_2300` (no W) → calcular/simular → `ayúdame a elegir` → pick `sunnysky_r2305_2500` from the watts-recovery list → assert the pick message omits "puedes optimizar o simular", both `motor_power_w` and `battery_capacity_wh` are present, `autonomy_min` is still `None`, and `build_startup_context()["continuity"]["next_useful_step"]` asks for `calcular`/`simular`, contains "No declares motor_power_w a mano", and does **not** contain "Declarar battery_capacity_wh"; situation stays off "Diseño validado". (2) regression guard — before any pick, the emax watts-recovery Continuity step is unchanged (fires ahead of the new rank in the elif chain).
- `tests/test_energy_params.py` — new `test_reasoning_missing_energy_stale_signal_with_both_params_present_no_declare`: `sunnysky_r2305_2500` bound, `battery_capacity_wh` + `motor_power_w` both in `current_parameters`, stale `energy_status=missing_energy_parameters` → no `"Declarar battery_capacity_wh"` in suggested-action labels or insights.
- `docs/IMPLEMENTATION_TASKS.md`, `.jes/state/engineering_state.json` — synced (IC entry moved from "awaiting Claude" to "implemented, awaiting review"; suite count 2114 → 2117).

## Behavior changed

- New: when a catalog-bound motor with nameplate W and battery Wh are both already in `current_parameters`, an autonomy target is set, and minutes are absent/stale (`autonomy_min is None` or `energy_status == "missing_energy_parameters"`), and the SKU is *not* itself missing W (so `_watts_recovery_next_step` didn't already fire): Continuity's `next_useful_step` becomes the locked recalc sentence instead of falling through to the generic "declare W/Wh" or "optimizar o simular" copy.
- `ReasoningLayer` no longer labels `battery_capacity_wh`/`motor_power_w` as missing when they are already present and the only signal is the stale `missing_energy_parameters` flag.
- The post-save architecture-complete hint ("puedes optimizar o simular") is omitted for a turn where the autonomy objective is not yet demonstrated (target set + minutes absent/stale/below-target).
- Everything else — `_derive_overall`, Energy PASS, Block Closure, G22, T1+2, watts-recovery list/IDLE (SKU genuinely lacking W), G21 covering-with-W, autonomy-below-target copy — unchanged; confirmed by the existing suites for those ICs passing unmodified.

## Tests

- Added: `tests/test_cli_stale_energy_recalc.py` (2 tests), `tests/test_energy_params.py::test_reasoning_missing_energy_stale_signal_with_both_params_present_no_declare` (1 test).
- Executed: full suite — `python -m pytest -q` → **2117 passed**, 0 failed (baseline 2114 + 3 new).
- Targeted re-run before the full suite: `test_cli_stale_energy_recalc.py`, `test_energy_params.py`, `test_project_continuity.py`, `test_cli_catalog_assist_watts_recovery.py`, `test_g21_g22_catalog_bind_ux.py` → 67 passed, confirming no regression in the directly adjacent ICs (watts-recovery, T1/T1+2, autonomy-below, feasibility semantics).

## Non-goals honored

No auto-`calcular`/`simular` on pick. `_derive_overall`/ASSEMBLY_READY/Option B untouched. T1+2/Tier 3/G22 filter untouched. No `motor_power_w` invented anywhere. Block Closure rollup untouched. G18 `definir motor` list untouched. `latest_results` never invalidated by code — only the user's own `calcular`/`simular` changes it.

## Remaining risks

- The `_append_arch_progress_hint` guard re-derives `physical_requirements`/`calculations`/`simulation` from the freshly reloaded `project_state` rather than reusing values already computed earlier in the same call; this mirrors the existing pattern at the `_handle_list_motors`/`build_startup_context` call sites (both re-derive `derive_physical_requirements` independently) so it is not a new inconsistency, but a future refactor could thread the already-computed `req`/`calc`/`sim` through instead of a second load+derive.
- The tradeoff-line guard in `reasoning_layer.py` is the one piece marked optional in the IC; it is behaviorally consistent with the insight/suggestion guards but has no dedicated test — flagging for JES review to confirm the intent matches (skip only when the SKU declares W and nothing is truly missing).
