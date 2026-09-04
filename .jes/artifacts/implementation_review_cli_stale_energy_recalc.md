# Implementation Review — CLI Continuity: recalc after watts-recovery pick

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**IC:** [implementation_contract_cli_stale_energy_recalc.md](implementation_contract_cli_stale_energy_recalc.md)  
**★:** [engineer_ratification_cli_stale_energy_recalc.md](engineer_ratification_cli_stale_energy_recalc.md) — Engineer “procede”  
**Report:** [implementation_report_cli_stale_energy_recalc.md](implementation_report_cli_stale_energy_recalc.md)  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTES**

§2.1–§2.3 match the IC. No auto-`calcular`, no Option B, no T1+2/G22/watts-recovery IDLE change. Reviewer re-ran adjacent tests (**83 passed**) and full suite (**2117 passed**). Notes are test/hygiene, not a re-implement.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2.1 predicate: target + stale minutes + has W + `motor_power_w` + Wh | **Pass** — `_await_autonomy_recalc_next_step` |
| §2.1 locked next_step / why verbatim | **Pass** |
| §2.1 after watts recovery, before `suggested_action` | **Pass** — `project_continuity.py` elif chain |
| Situation unchanged | **Pass** — helper does not touch situation |
| No `resolve_motor_catalog_surface` | **Pass** — `catalog_bound_motor_lacks_nameplate_watts` only |
| Watts recovery not stolen (emax) | **Pass** — lacks-W returns None; elif order; regression test |
| §2.2 no declare when `missing_e` empty | **Pass** — suggestions `return []`; insight skipped |
| Emax no-invent-W CTA unchanged | **Pass** — lacks-watts branch first |
| Battery-actually-missing still declares | **Pass** — extra unbound test (not required, correct) |
| §2.2 tradeoff skip (optional) | **Pass** — skipped when SKU has W and `missing_e` empty |
| §2.3 omit `puedes optimizar o simular` when undemonstrated | **Pass** — `_append_arch_progress_hint` |
| Pick bind / `set_motor_component` untouched | **Pass** |
| No auto calculate/simulate | **Pass** |
| §5 file list | **Pass** |
| Mandatory tests | **Pass** — new file 2/2; energy_params +1; watts recovery 3/3; autonomy-below still green |
| Suite | **Pass** — reviewer **2117** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| After emax→pick r2305, no `calcular`: next_step is recalc, not declare W/Wh | **Confirmed** — `test_pick_watts_recovery_candidate_awaits_recalc_not_declare` |
| Pick message omits `puedes optimizar o simular` | **Confirmed** |
| `motor_power_w` + Wh present; `autonomy_min` still None | **Confirmed** |
| Emax before pick still watts recovery | **Confirmed** — `test_emax_watts_recovery_continuity_unchanged_before_pick` |
| ReasoningLayer stale signal + both params: no declare | **Confirmed** — `test_reasoning_missing_energy_stale_signal_with_both_params_present_no_declare` |
| Emax no-W CTA | **Confirmed** — existing energy_params test green |
| 5 vs 15 autonomy-below next_step | **Confirmed** — `test_situation_thrust_feasibility_when_autonomy_calculated_below_target` (rank-2/calculated-below still first) |
| G9-A resolver once | **Confirmed** — adjacent `test_g9a_catalog_ref_gap` green |
| Full suite | **2117 passed** (reviewer) |

Condition 5 of the IC (`_watts_recovery_next_step is None`) is enforced by elif order plus `lacks_nameplate_watts` inside the new helper. Equivalent. Do not add a second watts-recovery call (that would rebuild the G22 list on every `estado`).

---

## Notes (non-blocking)

### Note 1 — Walk test does not assert `Candidato inicial`

IC §3 asked situation still `Candidato inicial`. The new test only forbids `Diseño validado`. The situation helper is unchanged; the walk path still uses `_autonomy_objective_undemonstrated`. Optional one-liner in the walk test. Not required to ship.

### Note 2 — Autonomy-below file has no “not recalc string” assertion

IC named `tests/test_project_continuity.py` so 5 vs 15 stays the locked energy next_step. Existing test still passes; it does not assert absence of `declara vatios de placa`. Rank order (calculated-below **before** recalc) is the real lock. Leave as-is.

### Note 3 — Orchestrator imports a Continuity private helper

`_append_arch_progress_hint` imports `_autonomy_objective_undemonstrated`. The IC named that helper. `_autonomy_objective_undemonstrated` is broader than the pick-only walk (also true for 5 vs 15), which **matches** §2.3 wording. Omitting “optimizar” after a below-target calc is consistent with the autonomy-below IC.

### Note 4 — Tradeoff guard has no dedicated test

Optional in the IC; implemented. Insight + suggestion tests cover the lie the walk showed.

---

## Next

Code **closed**. Optional Engineer CLI: same `autonomia-15min`, pick a W-SKU, **before** `calcular` — Siguiente paso must be the recalc sentence, not `Declarar battery_capacity_wh`. Then `calcular`/`simular` → 5 vs 15 unchanged. Option B / Tier 3 not automatic.
