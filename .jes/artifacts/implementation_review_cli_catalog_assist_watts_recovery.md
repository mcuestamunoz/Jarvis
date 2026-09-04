# Implementation Review — CLI catalog-assist watts recovery

**Date:** 2026-09-02  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_cli_catalog_assist_watts_recovery.md](implementation_contract_cli_catalog_assist_watts_recovery.md)  
**★:** [engineer_ratification_cli_catalog_assist_watts_recovery.md](engineer_ratification_cli_catalog_assist_watts_recovery.md) — ★1–★5  
**Report:** [implementation_report_cli_catalog_assist_watts_recovery.md](implementation_report_cli_catalog_assist_watts_recovery.md)  
**Baseline:** tag `v0.3.5` / `fc46938` plus live tree (T1+2 + G18 motors-only covering help-choose)

## Verdict

**PASS WITH NOTES**

§2.2–§2.4 and the IDLE table in §2.3 match the IC. Predicate §2.1 omits the underspec call for G9-A (Note 1); exclusivity is still wired. No T1+2, no Tier 3, no invent W, no `_derive_overall`. Reviewer re-ran suite **2114**.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2.1 `bound_motor_needs_watts_recovery` | **Pass with note** — no-W + autonomy target + no minutes / `missing_energy_parameters`. Does **not** call `bound_motor_sku_is_underspec` (N1). |
| §2.2 G22 then keep `max_watts is not None`, cap 5 | **Pass** — `build_nameplate_watts_motor_suggestions` |
| §2.2 locked header / empty / CTA | **Pass** — `format_watts_recovery_catalog` |
| §2.2 no `build_underspec_motor_offer` | **Pass** |
| §2.3 IDLE underspec → T1+2; watts recovery → filtered list; covering+W → `None` | **Pass** — `orchestrator.py` `_try_start_assisted_motor_help` |
| §2.5 G18 default list unchanged | **Pass** — `_offer_component_motor_catalog(..., watts_recovery=False)` default |
| §2.4 Continuity names W-SKUs + `ayúdame a elegir` before invent-W CTA | **Pass** — `_watts_recovery_next_step` before suggested-action |
| Situation string unchanged | **Pass** |
| T1 rank-2 still first on sim not-pass | **Pass** — underspec block is in the warning/fail branch; watts recovery is later |
| Mandatory tests | **Pass** — `test_cli_catalog_assist_watts_recovery.py` 3/3 |
| Adjacent T1 / G21 / G22 empty-strict | **Pass** |
| Non-goals | **Pass** — no Option B / Block Closure / battery picker / invent W |
| §5 file list | **Pass** |
| Suite | **Pass** — reviewer **2114** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| IDLE emax no-W + autonomy + calc/sim → numbered W-list, not `estado`, not emax SKU | **Confirmed** — `test_idle_emax_no_w_opens_watts_filtered_list` |
| Covering `r2305` (has W) IDLE still G21 | **Confirmed** — `test_idle_r2305_with_watts_stays_g21` |
| Continuity next_step is recovery + help-choose, not only the ban | **Confirmed** — `test_continuity_names_watts_recovery_not_only_ban` |
| emax without autonomy target still does not open `motor_power_w` | **Confirmed** — existing `test_idle_help_choose_catalog_bound_without_watts_opens_propellers_not_power_w` |
| G9-A resolver once | **Confirmed** — after dropping underspec from the predicate |
| Full suite | **2114 passed** (reviewer) |

---

## Notes (non-blocking)

### Note 1 — Predicate vs IC bullet “underspec is False”

IC §2.1 listed `bound_motor_sku_is_underspec is False` inside the helper. Putting that call in Continuity’s every-`estado` path doubled `resolve_motor_catalog_surface` and failed G9-A (`spy.call_count == 2`). Underspec exclusion is instead:

- IDLE checks underspec **first**
- Continuity rank-2 owns underspec on sim fail

Do not restore the resolve into the predicate without a readiness-first cache.

### Note 2 — Underspec + sim **pass** + no W

T1 rank-2 only runs when sim is not pass. A covering-fail-but-wait: underspec **and** sim pass **and** no nameplate W could show watts recovery in Continuity. IDLE still prefers T1+2. No live catalog SKU is known to hit this; not this IC.

### Note 3 — Recovery ≠ 15 min

Picking a W-SKU (e.g. `sunnysky_r2305_2500`) may still yield ~5 min vs 15. Feasibility autonomy-below path stays allowed (★5).

---

## Next

Watts recovery **closed on code**. Engineer CLI smoke on the emax walk: `ayúdame a elegir` (IDLE, without `definir motor`) → filtered W-list, not `estado` reprint. Pick a W-SKU → L0 minutes return; unmet 15 min is OK. Option B `ASSEMBLY_READY` / Tier 3 **not** automatic.
