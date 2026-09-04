# Independent review — last three CLI implementations

**Date:** 2026-09-02  
**Reviewer:** JES / Cursor (Engineer Interface) — this pass is against the ICs and live code, not a checklist copy of the implementer self-reviews.  
**Suite re-run this review:** 41 targeted tests passed (`test_project_continuity`, `test_cli_feasibility_semantics`, T1, T1+2, G21/G22, watts recovery, G9-A, emax no-invent-W CTA). Full suite was **2114** at watts close-out.

**ICs in scope (newest last):**

1. [CLI feasibility: calculated autonomy below target](implementation_contract_cli_feasibility_autonomy_below.md)
2. [CLI catalog-assist T1+2](implementation_contract_cli_catalog_assist_t1_plus_2.md)
3. [CLI catalog-assist watts recovery](implementation_contract_cli_catalog_assist_watts_recovery.md)

**Out of this trio, but recorded:** G18 `definir motor` + covering help-choose (shipped after T1+2, **no IC**). T1 (underspec re-offer) is the parent of 2 and 3; not re-opened here.

---

## Protocol (locked)

**Engineer `ratifico` / `bien ratifico` = publish the Implementation Contract for Claude. Do not implement `src/` in this session.**

This JES chat writes the IC (and ★ file). Claude (code agent) implements. This chat reviews against the IC after Claude reports.

The last three ICs were implemented in the same Cursor session that wrote them. That is a process miss. It does not by itself fail the product checks below. Watts recovery is already in the tree; this review does **not** revert it.

---

## Combined verdict

| IC | Verdict | Ship? |
|---|---|---|
| Autonomy-below | **PASS** | Yes |
| T1+2 | **PASS WITH NOTES** | Yes |
| Watts recovery | **PASS WITH NOTES** | Yes |
| G18 covering motors-only (uncontracted) | **Recorded leak** | Already in tree; retro-IC only if Engineer wants it on paper |

No FAIL. No Option B / Tier 3 / invent-W / G22 silent relax found.

---

## 1. Autonomy-below — PASS

**Intent:** sim PASS + 15 vs 5.0 must not say `Diseño validado`. Same locked thrust-feasibility situation. Next step: energía/requisito, not architecture-complete / iterate / motor picker.

**Code:** `_autonomy_objective_undemonstrated` + `_autonomy_calculated_below_target` in `project_continuity.py`. Locked strings verbatim. Evidence line unchanged. `src/` outside Continuity: none (matches §5).

**Live rank (Walk A):** `autonomy_below_restriction` is a sim warning → `has_warnings` → `status_type=warning` → rank-2 `elif _autonomy_calculated_below_target` wins. The later `sim_status == pass` copy of the same next-step is the dual path already noted in the first review; still harmless.

**Tests:** both mandatory Continuity cases present; parent uncalculated + no-constraint still green; `ayúdame a elegir` asserted **absent** on the below-target next step.

**Non-goals:** sim still `pass`; ERF dual still allowed. Untouched.

---

## 2. T1+2 — PASS WITH NOTES

**Intent:** underspec offer = T1 G22 first, then named drop-KV+prop second pass. Frankenstein line on `match_motor_propeller` fail. Pick binds motor only. Covering: no relax. G22 default empty-strict unchanged.

**Code:** `build_underspec_motor_offer` calls `find_motors_for_requirements(min_thrust_n=…, kv=None, prop_inch=None)` after unchanged `build_motor_catalog_suggestions`. `_offer_component_motor_catalog` uses it only when `bound_motor_sku_is_underspec`. Pick appends the locked hélice note; `gf_5045x3` stays bound. Continuity two-band string matches §2.4.

**Independent probe (same T1 fixture, 2026-09-02):**

- T1: `sunnysky_r2205_2500`, `t-motor_f80_2400`, `hobbywing_xrotor_2207_2450`
- Extras (5): `sunnysky_x2216_11` (mismatch), `emax_mt2216_810` (mismatch), `t-motor_mn3110_700` (mismatch), `emax_eco_ii_2207_1700` (**match**, no warning — correct), `sunnysky_x2212_980` (mismatch)
- `sunnysky_v4006_740` **not** in the first 5 extras (D8 closest-fit)

**Notes**

**N1 — IC §3 example SKU not locked.** Mandatory table said “e.g. `sunnysky_v4006_740`”. Tests lock frankenstein copy on any `prop_mismatch` extra. Product is honest; do not add a second ranker to force v4006.

**N2 — Continuity extras test lives in `test_cli_catalog_assist_t1_plus_2.py`, not `test_project_continuity.py`.** Behavior is covered; §5 file list not followed. Hygiene only.

**N3 — Covering IDLE assertion is weak.** `test_covering_sku_has_no_relax_header` no-ops if help-choose returns `None` (the G21 path). G21 noop test still carries the real covering guarantee.

**N4 — G18 follow-up is outside this IC.** T1+2 §2.5 said covering `definir motor` is out of the T1+2 *offer* (no relax). The later change opens **G22** on motors-only covering help-choose. That is a product delta without an IC (see below). Composite covering still does not reopen motors.

G22 empty-strict and `build_motor_catalog_suggestions` were not silently relaxed.

---

## 3. Watts recovery — PASS WITH NOTES

**Intent:** bound SKU with no nameplate W + autonomy target + no minutes → IDLE numbered list of W-motors; Continuity names them + `ayúdame a elegir`; do not invent W; covering-with-W stays G21.

**Code:** IDLE table in `_try_start_assisted_motor_help` matches §2.3 (underspec first, then watts recovery, else `None`). List helper filters G22 to `max_watts is not None`, cap 5, no T1+2 relax. Locked header/empty/CTA present. G18 default offer still `watts_recovery=False`.

**Independent probe (emax + `gemfan_5045_hbn` + 4S + 15 min, calc/sim):**

- `bound_motor_sku_is_underspec` False; `bound_motor_needs_watts_recovery` True
- sim `pass`, `energy_status=missing_energy_parameters`, warnings `[]`, `autonomy_min is None`
- List: `sunnysky_r2305_2500` (220), `emax_rs2205_2300` (250), `brotherhobby_avenger_2500` (280), `hobbywing_xrotor_2207_2450` (300), `t-motor_f80_2400` (320)
- `emax_rs2205s_2300` **absent** (no-W SKU not re-offered)

Live Continuity reaches watts recovery because energy-missing does **not** flip `status_type` to warning (stays `nominal`), and `catalog_bound_motor_covers_power_w` is identity-true so the old “declara W” rank is skipped. Both are load-bearing.

**Notes**

**N1 — Predicate vs IC bullet 1.** `bound_motor_needs_watts_recovery` does not call `bound_motor_sku_is_underspec` (G9-A: one `resolve_motor_catalog_surface` per `build_startup_context`). Exclusivity is IDLE-first + Continuity rank-2 on sim-not-pass. Do not put resolve back into the Continuity helper.

**N2 — Rank-2 can steal watts recovery if emax ever gets a sim warning.** Watts `elif` is after the entire warning/fail rank. Today emax warnings are empty. If a future warning appears that is not `autonomy_below_restriction`, next_step becomes “Corrige la causa…” and the recovery CTA disappears. Not this walk.

**N3 — Recovery ≠ 15 min.** Picking r2305 may still yield ~5 vs 15. Feasibility autonomy-below owns that path (★5). Allowed.

---

## Continuity rank (how the three compose)

First match wins. Live CLI:

| Walk | status_type | Winner |
|---|---|---|
| A — r2305, 5.0 vs 15, sim pass | `warning` (`autonomy_below_restriction`) | Autonomy-below next_step |
| C — emax no-W, no minutes, sim pass | `nominal` (no warnings) | Watts recovery next_step |
| Underspec + sim fail | fail → rank 2 | T1 / T1+2 |

Situation string for A and C is the same locked thrust-feasibility sentence. Dual Continuity vs ERF `ASSEMBLY_READY` is still the parent ★1 allowance — **not** Option B.

---

## Uncontracted: G18 covering motors-only

After T1+2, `definir motor` (wizard `expected_keys == ["motors"]`) + `ayúdame a elegir` reopens G22 even when the bound SKU covers thrust. IDLE covering and composite covering unchanged.

Test: `test_definir_motor_help_choose_lists_catalog_when_covering`. The assertion allows `Filtros relajados` as well as G22 — too loose for covering (code path should be G22 only).

This is the Walk B reprint fix. Honest product. **Not** in any of the three ICs. Engineer can (a) leave it as field patch, or (b) ★ a one-page retro-IC. Do not treat it as T1+2.

---

## What this review is not

- Not Option B (`_derive_overall` / `ASSEMBLY_READY`).
- Not Tier 3.
- Not a request to revert watts recovery.
- Not a Claude implementation ticket.

---

## Engineer next

1. Treat future `ratifico` as IC-for-Claude only.
2. Optional CLI smoke still valid: emax IDLE `ayúdame a elegir` → W-list; r2305 covering IDLE → no picker; `estado` on 15 vs 5 → not `Diseño validado`.
3. Option B / Tier 3 stay frozen until a new ★.
