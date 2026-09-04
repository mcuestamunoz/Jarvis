# Investigation Review — CLI catalog-assist + misfit propose

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_cli_catalog_assist_misfit_propose.md](investigation_contract_cli_catalog_assist_misfit_propose.md)  
**Report:** [investigation_report_cli_catalog_assist_misfit_propose.md](investigation_report_cli_catalog_assist_misfit_propose.md)  
**★ (investigation):** [engineer_ratification_cli_catalog_assist_misfit_propose.md](engineer_ratification_cli_catalog_assist_misfit_propose.md)  
**Notes (hypotheses):** [engineer_notes_cli_propose_on_misfit.md](engineer_notes_cli_propose_on_misfit.md)  
**Walk:** [engineer_cli_walk_block_closure_product_scope.md](engineer_cli_walk_block_closure_product_scope.md)  
**Base:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` · commit `fc46938` (live tree + fixture `eb61a0ed6fe2`)

## Verdict

**PASS WITH NOTES**

Gates A–G answered. First-IC recommendation is **T1** (not T1+2, not STOP, not Tier 3). That matches the contract trigger: T1+2 only if Gate C T1 is empty/useless — live G22 on the fixture returns one candidate (`sunnysky_r2205_2500`), useful-but-insufficient. No `src/` / test edits in this investigation. Frozen items (H5, G24-B, Foundation, Option B, Conversation Engine, Block Closure formula) not proposed as this IC.

**Ready for Engineer ★** on T1 (and the two IC-shaping notes below). Cursor writes the Implementation Contract **for Claude** after ★. Do not implement before that IC.

---

## Contract checklist

| Criterion | Result |
|---|---|
| Fixture confirmed, not mutated | **Pass** — `state.json` SKUs, 222 Wh, sim fail, `legacy_estimate` 7.5 N |
| 3.1 Gate A — Combo A vs D8 ranking | **Pass** — live: 4.7 N + 5″ → `#1 r2305`, `r2205` **#8 of 9** (unfiltered **#11 of 22**) |
| 3.2 Gate B — post-bind help-choose | **Pass** — `_try_start_assisted_motor_help` `:1482-1483` identity short-circuit; `_wants_catalog_help` `:112-121` / `:2936` same blind spot; G9-A `bound_sku_underspec` already computed |
| 3.3 Gate C — G22 on failed combo | **Pass** — live `thrust=15.04465`, `kv=2500`, `prop=5.0` → only `r2205` 12.5525 N; drop-KV / drop-prop / thrust-only tables hold |
| 3.4 Gate D — Continuity / suggestions / DSE | **Pass** — rank 2 before rank 3 `:179-182`; SuggestionEngine no SKU; `_CATALOG_MOTOR_GOAL_KEYS`; FN-022 empuje→`mejorar_estabilidad` **is** catalog-keyed |
| 3.5 Gate E — watts CTA | **Pass** — predicate is identity; copy claims “no declara vatios”; `r2305` has `max_watts=220` |
| 3.6 Gate F — GAP vocabulary | **Pass** — leave ID; title-only on `gap_evidence_fact` prefix |
| 3.7 Frankenstein | **Pass with Note 2** — PASS-capable thrust-only motors are prop-incompatible with `gf_5045x3` |
| 3.8 Gate G — exactly one of T1 / T1+2 / STOP | **Pass** — **T1**; T1+2 deferred; STOP not used |
| 3.9 tests / probe sketch | **Pass** — G21 noop test scoped correctly; probe sketch usable |
| C1–C7 / ★4–★5 frozen | **Pass** — no second search function; no silent G22 fallback; G24-B not unlocked; battery underspec named as non-goal |
| No production code | **Pass** — investigation report only |

---

## Independent verification (spot-check)

Live `python3` against `workspace/inspección-autonomía-mínima-5-minutos-eb61a0ed6fe2/state.json` + `default_library` (read-only):

| Claim | Cursor check |
|---|---|
| `catalog_bound_motor_covers_power_w` is identity (`family == "motor"`) | **Confirmed** — `project_closure.py:45-72` |
| IDLE help-choose returns `None` when that predicate is true | **Confirmed** — `orchestrator.py:1482-1483` |
| `_wants_catalog_help` is stub **or** `catalog_ref is None` | **Confirmed** — `:112-121` |
| G22 on fixture → only `sunnysky_r2205_2500` 12.5525 N | **Confirmed** |
| `resolve_motor_catalog_surface` fact `bound_sku_underspec:sunnysky_r2305_2500` | **Confirmed** |
| Create-time 4.7 N + 5″: `#1 r2305`, `r2205` rank 8/9 | **Confirmed** |
| Drop KV + 5″: `emax_eco_ii_2207_1700` 14.5 N then `r2205`; still short of 30.09 N | **Confirmed** |
| Drop prop + KV 2500: no new SKU | **Confirmed** |
| Thrust-only PASS-capable (`2×thrust_n ≥ 30.0893`) | **6 motors**, all `match_motor_propeller(..., gf_5045x3) == False` — see Note 2 |
| `mejorar_estabilidad` in `_CATALOG_MOTOR_GOAL_KEYS` | **Confirmed** — `design_explorer.py:210-213` |
| `_catalog_bound_motor_lacks_watts` aliases the identity helper | **Confirmed** — `reasoning_layer.py:442-448` |
| G21 test does not assert “bound ⇒ always noop forever” | **Confirmed** — `test_g21_idle_help_choose_noop_when_catalog_ref_set` `:175-204` |

---

## Notes (IC must absorb; not a re-investigate)

### Note 1 — Continuity is part of contract T1, not optional

Contract §3.8 T1: post-bind help-choose **and** “Continuity after sim-fail / underspec points at that list (or names 1–5 candidates)”.

The report marks `project_continuity.py` as **optional** (“rank 2 is intentional”). Rank 2 being intentional is true (`:179-182`). It is also why `estado` after `simular` never proposes a motor. The walk spine was **propose when it doesn’t fit**, not only unstick `ayúdame a elegir`.

**Lean for Engineer ★:** first IC **includes** Continuity: when `bound_sku_underspec` (or equivalent) is live, `next_useful_step` must name the G22 candidate(s) or the help-choose CTA — even if sim is fail. Do not reorder the entire rank table. Do not send the user to a Conversation Engine.

### Note 2 — “Only `v4006` restores feasibility” is overstated; the frankenstein class is real

Thrust-only PASS-capable on this fixture (live): `sunnysky_v4006_740`, `sunnysky_x2820_900`, `t-motor_antigravity_mn4006_380`, `t-motor_mn4014_400`, `t-motor_mn5008_340`, `t-motor_u8_170`. **All** fail `match_motor_propeller` vs bound `gf_5045x3`. `generic_700kv` 2×15.0 N is just under 30.0893.

T1+2 still **not** justified as first IC (T1 list is not empty). IC prose must not say there is a single PASS motor.

`emax_eco_ii_2207_1700` `compatible_prop_inch=(6,7)` matches `gf_5045x3` via the existing **±1″** rule, not because it is a 5″ motor. Wording in a future T1+2 IC should say “tolerance match”, not “5″ family”.

### Note 3 — T1 proposes another misfit (honest)

Picking the T1 candidate (`r2205`, 2×12.55 N ≈ 25.1 N vs required 30.1 N) **does not** make this walk’s sim PASS. The IC must not claim “cierra el bloque” or “esto encaja”. Product copy: the bound SKU no longer covers; here is a catalog motor that covers **more** of the thrust floor under current G22 filters. Closure remains NO CERRADO.

That is still the right first IC: it converts the stuck loop into an evidenced offer. It is **not** Tier 3.

### Note 4 — Watts CTA: include as copy/predicate split

Walk lie is real (`r2305` has 220 W). Seam is `reasoning_layer.py` aliasing `catalog_bound_motor_covers_power_w`. **Do not** change that helper’s architecture-progress meaning. New/narrow check for the CTA only. **Lean: in the first IC** — small, same neighborhood, Engineer already saw it twice.

### Note 5 — Do not weaken G21

T1 must reopen the **motor** picker only when underspec (or equivalent readiness fact), not whenever `catalog_ref` is set. `test_g21_idle_help_choose_noop_when_catalog_ref_set` stays. Add the all-bound + underspec case from the report’s probe sketch.

### Note 6 — Battery underspec out of first IC

Report is correct: no `bound_sku_underspec` for battery; `build_battery_catalog_suggestions` is unfiltered. Named non-goal. Do not fold it in.

---

## Engineer ★ — Cursor lean (not decided)

| Decision | Lean |
|---|---|
| First IC = **T1** | **Ratify** |
| Continuity names G22 / help-choose on underspec even when sim fail (Note 1) | **In** T1 |
| Watts CTA predicate split (Note 4) | **In** T1 |
| GAP title-only, ID unchanged | **In** T1 |
| T1+2 named G22 second pass | **Defer** (second IC; frankenstein warning from day one) |
| Tier 3 joint combo | **Not this IC** (PARTIAL DSE later — report §4 accepted) |
| G24-B / H5 / Foundation / Option B | **Stay frozen** |

---

## Recommended IC scope (post-★)

Single bounded arc — **CLI catalog-assist T1 (misfit re-offer)**:

1. IDLE `_try_start_assisted_motor_help` + COMPONENT `motors_want_help`: if bound **and** `bound_sku_underspec`, offer existing `_offer_component_motor_catalog` / `build_motor_catalog_suggestions` (no new ranking).
2. Continuity `next_useful_step` when that fact is live (Note 1).
3. GAP title varies on `gap_evidence_fact` prefix; type ID unchanged.
4. Watts CTA: separate “SKU has no `max_watts`” check; do not retarget `catalog_bound_motor_covers_power_w`.
5. Tests: G21 underspec case + probe sketch; G21 false-rebind guard unchanged.

**Forbidden:** filter relax, joint combo, catalog JSON, G24-B, Block Closure formula, inventing W, “type Combo A SKU” as the product fix.

---

## Next

Engineer ★ T1 locked. Claude implements [implementation_contract_cli_catalog_assist_t1.md](implementation_contract_cli_catalog_assist_t1.md).
