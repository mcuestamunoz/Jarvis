# Implementation Review — CLI catalog-assist T1 (misfit re-offer)

**Date:** 2026-09-02  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_cli_catalog_assist_t1.md](implementation_contract_cli_catalog_assist_t1.md)  
**★:** [engineer_ratification_cli_catalog_assist_t1.md](engineer_ratification_cli_catalog_assist_t1.md) — ★1–★5  
**Report:** [implementation_report_cli_catalog_assist_t1.md](implementation_report_cli_catalog_assist_t1.md)  
**Baseline:** tag `v0.3.5` / `fc46938` plus live tree (Block Closure + CLI feasibility)

## Verdict

**PASS WITH NOTES**

§2.1–§2.6 implemented on the named files. No new ranking, no G22 filter relax, no `catalog_bound_motor_covers_power_w` semantic change. Reviewer re-ran suite **2103** and probe `scripts/cli_probe_cli_catalog_assist_t1.py` (4 scenarios). Notes are IC-hygiene, not a re-implement.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2.1 `bound_motor_sku_is_underspec` uses `resolve_motor_catalog_surface` | **Pass** — `engineering_readiness.py:303-314` |
| §2.2 IDLE underspec → `_offer_component_motor_catalog`, covering → `None` | **Pass** — `orchestrator.py:1489-1502` |
| §2.3 COMPONENT `motors_want_help` OR underspec; prop/battery untouched | **Pass** — `:2964-2971` |
| §2.4 Rank 2 kept; underspec copy + disclaimer; empty-search sentence | **Pass** — `project_continuity.py:191-218`; prefers `readiness.motor_catalog_gap_fact` |
| §2.5 GAP titles; type ID unchanged | **Pass** — `_motor_catalog_gaps` `:483-492` |
| §2.6 Watts helper; identity helper unchanged | **Pass** — `catalog_bound_motor_lacks_nameplate_watts`; `covers_power_w` still identity `:45-72` |
| ReasoningLayer CTA uses nameplate helper | **Pass** — `:442-457` |
| G21 noop test untouched in intent | **Pass** — `test_g21_idle_help_choose_noop_when_catalog_ref_set` still green |
| Mandatory tests | **Pass** — G21 underspec + twice; Continuity 2; GAP titles; r2305 watts; `test_cli_catalog_assist_t1.py` 4 |
| Non-goals | **Pass** — no T1+2, no library JSON, no `_derive_overall` / Block Closure / G24-B / `find_motors_for_requirements` edits |
| §5 file list | **Pass** |
| Suite | **Pass** — reviewer **2103** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| IDLE underspec lists G22 (not `estado`) | **Confirmed** — probe + `test_g21_idle_help_choose_reopens_motor_list_when_bound_sku_underspec`; same phrase twice still a list |
| Covering bound SKU does not reopen motors | **Confirmed** — G21 noop; probe scenario 2 → `project_status` |
| Continuity sim-fail + underspec names SKUs + “no garantiza sim PASS” | **Confirmed** — unit test + probe `estado` line |
| emax no-W CTA kept; r2305 no “no declara vatios” | **Confirmed** — probe 3/4 + `test_energy_params.py` |
| Missing library SKU → watts helper False (no crash) | **Confirmed** — `has_motor` then `max_watts is None` `:109-111` |
| Full suite | **2103 passed** (reviewer) |

---

## Notes (non-blocking)

### Note 1 — Composite covering assertion is weak

`test_component_gate_covering_bound_sku_does_not_reopen_motor_list` asserts `pending_missing_params != ["motors"]`. In a composite wizard pending is already `["motors","propellers"]`, so a false motor re-offer would still pass that check. IDLE covering + G21 noop + probe scenario 2 cover the real contract. Optional follow-up: assert `"Candidatos del catálogo"` not in the covering composite message. Not required to ship T1.

### Note 2 — Continuity unit test hits the no-`readiness` substring path

`test_continuity_sim_fail_underspec_names_candidates` omits `readiness`, so it exercises `"ya no cubre el hueco de diseño" in motor_catalog_gap`. The `estado` path uses `motor_catalog_gap_fact` (probe confirmed). If `resolve_motor_catalog_surface` copy changes, the fallback can desync — already flagged in the implementation report. Leave as-is unless a later IC retouches Continuity.

### Note 3 — T1 still proposes a stack that may fail sim

Probe underspec list leads with `sunnysky_r2205_2500` (~12.6 N). Honest per ★ and IC. Do not treat that as T1+2.

---

## Next

T1 **closed on code**. Optional Engineer CLI: on the walk project, `ayudame a elegir` should print the numbered list (not `estado`). T1+2 / Tier 3 / H5 / Foundation stay **not** automatic.
