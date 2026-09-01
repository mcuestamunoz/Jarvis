# Investigation Report — DSE ↔ `motor_op_power_w` Dual-Truth (Post-P2-2)

**Contract:** [`investigation_contract_dse_motor_op_dual_truth.md`](investigation_contract_dse_motor_op_dual_truth.md)
**Checkpoint base:** `v0.3.3` / `checkpoint-validation-case-regression-gate` (`ceb44b4`)
**Investigator:** Claude Code
**Status:** Complete. Repro tests added and confirmed failing on baseline (as required). No production fix — investigation only, per contract §4/§5.

---

## 0. Executive summary

The field-walk numbers reproduce almost exactly with a minimal, controlled fixture: **explore baseline 8.325 min** (field walk: 8.325), **live calc 7.7083 min** (field walk: 7.7), **explore's apply-#1 promise 12.8077 min** (field walk: 12.808), **post-apply actual 7.7083 min** (field walk: 7.7 min unchanged). This is not a coincidence-shaped bug — it is the exact mechanism.

**Root cause, one level deeper than the contract's own hypothesis:** `resolve_operating_point`'s `voltage_v is None` clause (`library.py:606-609`) treats "voltage unknown" as "matches everything." When a motor (and/or propeller) is bound **before** a battery is bound, this clause lets an `exact_operating_point` resolution lock in with **zero voltage validation**. `component_writers.set_motor_component` is (by deliberate P2-2/IC2 design) **never re-called** after a battery-only catalog bind — so once a real, incompatible-voltage battery is later bound, the motor's `motor_op_power_w`/`propulsion_resolution` stays frozen and voltage-incoherent with the actual battery, indefinitely, with nothing to detect or correct it.

`design_explorer.explore()`'s baseline normalization (`apply_components_delta(state, {})`) re-derives voltage from the **current, real** battery on every call. This is not the bug — it is explore being more honest than the frozen live state. The dual truth is between "live `current_parameters`" (stale, never revalidated) and "explore's fresh normalization" (voltage-correct given the real battery), not between two independently-buggy code paths.

This reframes the fix-option analysis (§7): a fix that merely makes explore and apply *agree* with each other (Option D) would make both **consistently wrong**, not correct. The deepest-aligned fix is closer to Option C, extended to **voltage coherence**, not just thrust-value coherence — which reopens the exact tension P2-2/IC2 deliberately avoided (re-validating OP after a battery-only bind risks downgrading an already-good exact match). This is a genuine architectural trade-off, not a bug with an obvious one-line fix, and is flagged for explicit Engineer ★.

---

## 1. Baseline verification

| Check | Result |
|---|---|
| `pytest tests/` (before repro tests) | **2029 passed** |
| `pytest tests/` (with repro tests added) | **2030 passed, 2 failed (expected, documented), 1 skipped (CASE C, documented)** |
| Field-walk workspace | Present: `workspace/autonomía-15-min-7efc98205ee6/` |

No suite corruption. The 2 failures are the intended deliverable (contract §3: "must FAIL on current main").

---

## 2. Field-walk state — read directly, not summarized from the contract

```text
state.json (post apply #3):
  motor_power_w        = 260.0   (params-only delta from apply #1, motor_power_w_factor)
  motor_op_power_w      = 432.0   (frozen since before the battery was bound — see §4)
  motor_op_current_a    = 27.0
  motor_op_rpm           = 23560.0
  battery_capacity_wh   = 333.0  (params-only delta from apply #3)
  battery_cell_count    = 6      (lipo_6s_10000mah — 6S, 22.2V nominal)
  battery.catalog_ref   = None   (cleared by G5 divergence on the Wh change)
  motors.catalog_ref    = {family: motor, sku: emax_rs2205s_2300}  (still bound)
  latest sim: autonomy_min=11.5625 (rounds 11.6), can_fly=False, margin=0.9981
```

`333 / (432 × 4) × 60 = 11.5625` — the **live** calc is using `motor_op_power_w=432`, confirming `effective_motor_power_w()` (P2-2) is working correctly at the final-calc step; the bug is entirely about *what that 432 actually means* and *when explore agrees with it*.

Reading `iterations/iter_001.json` through `iter_005.json` confirms the actual turn sequence: motor bound alone first (`iter_001`, fallback thrust `10.042`, no battery yet); propeller + battery bound before `iter_003`'s DSE apply (which already shows `motor_op_power_w=432.0` and `battery_cell_count=6` together) — i.e., **the motor+propeller exact match was resolved before the battery's real voltage was ever known**, then a 6S battery was bound afterward without ever re-checking it.

---

## 3. Root cause — traced and reproduced (Q1, Q3, Q5)

### 3.1 The lock-in (Q1's real answer)

`resolve_operating_point` (`library.py:604-621`):

```python
voltage_matches = (
    voltage_v is None
    or row_voltage is None
    or abs(float(row_voltage) - voltage_v) <= _OP_VOLTAGE_EPSILON_V
)
```

`voltage_v is None` **unconditionally** satisfies `voltage_matches` — an "I don't know the voltage yet" state is treated identically to "the voltage matches." `set_motor_component` (`component_writers.py:250-284`) derives `voltage_v` from the bound battery's `catalog_ref` (or `current_parameters["battery_cell_count"]`) — if **no battery is bound yet** at motor/propeller-bind time, `voltage_v=None`, and any curated exact row for the bound propeller auto-qualifies. Live-verified:

```text
resolve_operating_point("emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=None)
  -> exact_operating_point, thrust_n=9.7086, power_w=432.0, voltage_v=16.0, selection_reason=v1_max_thrust
```

### 3.2 The freeze (Q5's real answer)

Once a battery **is** later bound via `bind_battery_from_catalog` + `set_battery_component`, `component_writers.set_motor_component` is **never re-invoked** — confirmed unchanged since the P2-2 implementation report's own explicit finding: *"battery-only bind does NOT re-call set_motor_component... verified empirically... re-calling can DOWNGRADE an already-resolved exact_operating_point to fallback."* That finding was correct and the decision not to re-call was the right call **given the specific case it was tested against** — but it has a mirror-image failure mode this investigation surfaces: an exact match that was **never actually voltage-validated in the first place** (because it was resolved with `voltage_v=None`) can survive indefinitely, silently, even when the real battery is *definitively* incompatible (22.2V vs. a 16.0V-only curated row — nowhere near the 0.05V epsilon).

Live-verified: at the real bound battery's voltage, the honest resolution is completely different:

```text
resolve_operating_point("emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=22.2)
  -> fallback_operating_point, thrust_n=10.042, power_w=None, current_a=None
```

### 3.3 The disagreement (Q1/Q3's mechanical trace)

`DesignExplorer.explore()` (`design_explorer.py:499-514`) computes its `base_params` via:

```python
normalized_state = apply_components_delta(project_state, {})
base_params = dict(normalized_state.current_parameters or {})
```

`apply_components_delta(state, {})` (`component_writers.py:421-480`), for the empty-delta "motors" case, re-applies the **existing component's own `properties["power_w"]`** (`400.0` — the original catalog rating, *never* mutated by `sync_motors_component_from_params`, which deliberately only touches `motor_count`/`thrust_n`/`torque_nm`) through `set_motor_component` again. This re-triggers full OP re-resolution — and this time, voltage is derived from the **real, current** battery (`battery_cell_count=6` → 22.2V, since `battery.catalog_ref` may or may not still be set but `battery_cell_count` always is). At 22.2V, §3.2's honest fallback result fires: `motor_op_power_w` gets **popped** (per the P2-2 write/pop rule: only set on `exact`/`fallback` *with* a non-`None` field — OP-0's fallback row has `power_w=None`), and `motor_power_w` resets to `400.0` (the catalog rating).

Meanwhile, `orchestrator._handle_apply_exploration`'s params-only branch (`orchestrator.py:3579+`) builds its own `base_params = dict(project_state.current_parameters or {})` — **directly from live state**, never through `apply_components_delta`'s re-normalization — so the stale `motor_op_power_w=432` survives untouched through `_apply_delta`'s merge (which only ever mutates the specific keys named in a delta, e.g. `motor_power_w_factor`).

**Two different `base_params` dicts, for what the code treats as "the same baseline project state," disagree specifically on `motor_op_power_w` — and disagree for a *reason* (voltage re-derivation), not by omission.**

### 3.4 Reproduced live, matching the field walk to four significant figures

```text
CalculationEngine().build(live_params).autonomy_min       = 7.7083   (field walk: 7.7)
design_explorer.explore(...).baseline_simulation.autonomy_min = 8.325  (field walk: 8.325)
exploration.viable[0].simulation.autonomy_min (motor_power_w_factor=0.65) = 12.8077  (field walk: 12.808)
post-"aplica la mejor" actual autonomy_min                 = 7.7083   (field walk: 7.7, "unchanged")
```

---

## 4. Answers to Q1–Q9

**Q1 (explore path/keys):** Answered in §3.1/§3.3. `apply_components_delta(state, {})`'s motor re-apply reads the component's **own** `properties["power_w"]` (stale catalog rating, `400.0`), not the live `current_parameters["motor_power_w"]` — then re-resolves OP using the **current** battery voltage. `motor_op_power_w` is absent from `base_params` specifically because the real 22.2V doesn't match any curated exact row for this motor+propeller — not because the key is unconditionally dropped.

**Q2 (candidate eval uses `effective_motor_power_w`?):** Confirmed **NO error in `effective_motor_power_w` itself** — `calculation_engine.py`'s autonomy branch correctly checks `motor_op_power_w` first, falls back to `motor_power_w`. The candidates are evaluated against the *voltage-honest* `base_params` (400W rating, since the honest resolution for the real battery is `fallback_operating_point` with no OP-electrical fields) — `effective_motor_power_w()` correctly returns `400.0` in that context. The "error" (§3.4: 8.325 vs. 7.7083) is **not** a scoring-function bug; it is that explore's baseline and the live state disagree about which resolution is currently true.

**Q3 (apply path merge):** Answered in §3.3. `base_params` in `_handle_apply_exploration` is `dict(project_state.current_parameters)` — a direct, unre-normalized copy of live state, so `motor_op_power_w` (and anything else not targeted by the delta) survives verbatim. This is **not** clearly "intentional per P2-2 Option A" — Option A's lock is about `motor_power_w` never being *overwritten by* OP data; it says nothing about whether a stale OP resolution should be re-validated on apply. This is an open gap, not a documented decision.

**Q4 (battery apply #3 margin cliff):** Traced `invalidate_diverged_catalog_refs` (`catalog_bind.py:229-241`) and `_apply_delta`'s own `battery_mass_kg` heuristic (`design_explorer.py`, `estimate_battery_mass_kg`) — both use the same 150 Wh/kg heuristic once `battery.catalog_ref` is cleared, so battery **mass** modeling is consistent between explore and apply once divergence has already happened once. The dominant driver of the margin/thrust discrepancy this investigation found is the **same** OP-voltage incoherence (§3): explore's normalized candidates are scored using whichever `per_motor_max_thrust_n` the honest, re-derived resolution produces, while the applied/live state can retain a different, stale thrust value the delta itself never touches. CASE C (§5) was built to isolate this precisely but did not trigger with the two goals/sequences attempted — documented honestly as a partial result, not suppressed.

**Q5 (G5 interaction):** Answered in §3.2. `sync_motors_component_from_params` never touches `motor_op_*` or `power_w`/`catalog_ref` — it is scoped to `motor_count`/`thrust_n`/`torque_nm` only (by its own docstring, unchanged). No refresh or revert of OP happens on DSE apply via G5's mechanism — G5 and this bug are genuinely independent, confirming the contract's own framing.

**Q6 (scope of hazard):** Any goal/delta that (a) doesn't touch `per_motor_max_thrust_n`/`motor_count` (so G5's `invalidate_diverged_catalog_refs` thrust-divergence check never fires) and (b) is evaluated via `explore()`'s re-normalized `base_params` is affected whenever the underlying motor's OP resolution is voltage-incoherent with the real battery. This is not `mejorar_autonomia`-specific — `reducir_masa`/`aumentar_payload`/`mejorar_estabilidad` all call the same `explore()` → same `apply_components_delta(state, {})` normalization → same disagreement, for **any** project in this specific state shape (motor/propeller bound before battery, or battery later swapped to an incompatible-voltage SKU). `electrical_compatibility._per_motor_current_a` (P2-2 IC) reads `motor_op_current_a` first — it would show the same stale-vs-honest disagreement pattern, not independently verified numerically here (out of this contract's repro scope) but structurally identical.

**Q7 (fix options — analysis only, no implementation):**

| Option | Assessment |
|---|---|
| **A — explore preserves `motor_op_*` when components unchanged** | **Rejected on the evidence.** This would make explore *also* trust the stale, voltage-unvalidated 432W — extending the honesty bug into explore rather than fixing the underlying incoherence. Explore's current behavior (re-deriving voltage) is the *more correct* half of the disagreement, not the buggy half. |
| **B — explore strips `motor_op_*`, apply strips/refreshes when delta touches power/energy fields** | Partial. The incoherence exists at the very first `explore()` call, before any delta is chosen — gating on "delta touches power/energy fields" misses the baseline-vs-baseline disagreement (§3.4's 8.325 vs. 7.7083 happens before any candidate is picked). |
| **C — explicit OP-vs-rating reconciliation helper (mirrors `invalidate_diverged_catalog_refs`)** | **Closest to root-cause-aligned**, but must be scoped to **voltage coherence**, not just thrust-value divergence (today's `invalidate_diverged_catalog_refs` only compares `thrust_n` vs `per_motor_max_thrust_n`, never voltage). This directly reopens the P2-2/IC2 trade-off: re-validating OP whenever the real battery becomes known/changes is exactly what IC2 chose *not* to do, because a naive re-validation can also **downgrade** an already-good exact match (documented, tested regression in `test_battery_pick_does_not_regress_already_resolved_propulsion_op`, P2-2's own IC). Doing this correctly requires distinguishing "the stored resolution was never voltage-validated (this bug)" from "the stored resolution WAS validated and a later action would needlessly downgrade it (P2-2's protected case)" — a real design decision, not a mechanical fix. |
| **D — DSE scoring uses `effective_motor_power_w()` on both explore and apply, enforce one authority** | Makes the two paths **consistently** report the same number — removes the *broken promise* symptom — but if the underlying `motor_op_power_w` is itself voltage-incoherent, both paths become consistently wrong instead of inconsistently wrong. Safer UX (no cliff), not necessarily correct physics. Could be a legitimate **first, smaller cut** while ★C's deeper question is decided separately. |
| **E — message-only/CTA honesty** | **Confirmed insufficient alone**, as the contract itself expected — this investigation shows the actual *computed numbers* (autonomy, margin) disagree, not just the narration around them; a CTA cannot fix a wrong calculation. |

**Q8 (regression surface):** `tests/test_dse_motor_op_dual_truth.py` (new, this investigation) — 3 documenting failures/skip + 1 passing sanity check. If an IC follows: extend this same file with post-fix assertions (flip the `==` expectations to hold), add a case exercising `electrical_compatibility._per_motor_current_a`'s equivalent disagreement (Q6), and a probe script (e.g. `scripts/cli_probe_dse_motor_op_dual_truth.py`) mirroring the CLI walk exactly, gated on whichever fix option Engineer selects.

**Q9 (recommendation):** See §6.

---

## 5. Repro tests (`tests/test_dse_motor_op_dual_truth.py`)

| Test | Result on `v0.3.3` |
|---|---|
| `test_live_state_has_stale_voltage_incoherent_exact_op` (sanity/precondition) | **PASS** — confirms the fixture reproduces the field-walk state shape |
| `test_case_a_explore_baseline_disagrees_with_live_calc` | **FAIL** (expected) — `8.325 != 7.7083` |
| `test_case_b_apply_does_not_deliver_explore_promise` | **FAIL** (expected) — `12.8077 != 7.7083` |
| `test_case_c_battery_candidate_viable_in_explore_fails_after_apply` | **SKIP** (honest, disclosed) |

**CASE C disclosure:** attempted both a single-round fixture and a two-round fixture mirroring the field walk's actual turn sequence (explore → apply #1 → explore again → apply battery candidate). In both attempts, no pure battery-capacity candidate reached `.viable` for `mejorar_autonomia` on this specific fixture (motor-power-reduction candidates outscored battery-capacity candidates and filled all 5 slots). This does **not** contradict the root-cause finding — CASE A and B already demonstrate the identical mechanism with exact field-walk-matching numbers — it means this particular margin-cliff manifestation (viable→fail specifically) needs a fixture closer to the field walk's actual near-margin mass/payload state than this investigation reconstructed. Documented honestly per contract §3's own "if reproducible without fragile tuning" allowance, rather than force-tuning parameters to manufacture a coincidental cliff.

---

## 6. Recommendation

**Primary:** This is a genuine architectural trade-off, not a bounded bugfix — recommend Engineer ★ on the **conceptual question** before any IC is drafted: *should a motor's OP resolution ever be re-validated after being locked in with `voltage_v=None`, and if so, when?* Two defensible answers exist:

1. **Re-validate on any battery bind/divergence** (extends Option C to voltage) — closes this bug, but reopens the exact regression risk P2-2/IC2's own test suite locks against (an already-good exact match could legitimately downgrade to fallback if the real battery turns out incompatible — which is *correct*, not a regression, but is exactly the behavior IC2's test names as "must not happen").
2. **Never lock in `exact_operating_point` from `voltage_v=None` in the first place** — require a real, bound-battery voltage before a curated exact row can be selected; fall back to `fallback_operating_point`/`legacy_estimate` until a battery is bound. This avoids ever creating the stale state to begin with, at the cost of a motor-only bind (no battery yet) never showing `exact_operating_point` even when it would turn out correct.

Recommend Engineer choose between these before an IC is drafted, since they touch the resolver's own matching-priority rules (frozen per this contract's constraints) or the P2-2/IC2 test contract (also frozen) — either direction requires an explicit new ★ to unlock one of those two locks, not a mechanical fix within existing bounds.

**As an independent, smaller, lower-risk parallel step:** Option D (single-authority `effective_motor_power_w()` on both explore and apply) would at minimum remove the *broken promise* symptom (§3.4's apply-#1 case) without touching the resolver or reopening either lock — recommend this as a first, safe cut regardless of which direction Engineer picks for the deeper question, since it strictly reduces user-visible harm (no more "explore says 12.8, apply delivers 7.7") even if the underlying number both paths agree on is itself still voltage-incoherent in the rare motor-before-battery sequencing.

**Explicit non-recommendation:** do not implement Option A (would extend the honesty bug into explore itself) or Option E alone (confirmed insufficient — the numbers, not just the narration, are wrong).

**Does this need a P2-2 contract amendment or new G5-style slice?** Neither cleanly — it is closer to a new, narrow slice analogous to G5's own `sync_motors_component_from_params`, but keyed on **voltage coherence** rather than thrust-value coherence, and it must explicitly account for (not silently override) the P2-2/IC2 regression test that currently locks the opposite behavior for a *different* scenario. Recommend a dedicated IC title distinct from both prior arcs (e.g. "Motor OP Voltage Coherence") once Engineer ★ resolves the trade-off in §6.

---

## 7. ★ Decisions for Engineer

**★1 — Conceptual direction:** (1) re-validate OP on battery bind/divergence (extends Option C) vs. (2) never lock in exact-match from unknown voltage (changes resolver priority). *No recommendation — genuine product/architecture trade-off, not an engineering-risk call.*

**★2 — Parallel safe cut (Option D):** ratify as an independent, lower-risk first step regardless of ★1's outcome? *Recommended: yes, ship this first if Engineer wants immediate symptom relief while ★1 is decided.*

**★3 — CASE C fixture:** worth a follow-up attempt with a closer field-walk-matching fixture (near-margin payload/mass), or accept CASE A+B as sufficient evidence? *No recommendation — CASE A+B already conclusively demonstrate the root cause.*

**★4 — Regression test contract conflict:** `test_battery_pick_does_not_regress_already_resolved_propulsion_op` (P2-2 IC) currently asserts an exact match must survive a battery bind unchanged. If ★1 selects direction (1), this test's *scenario* (a battery bind that happens to be voltage-compatible) would still pass, but the underlying rule would need updating to distinguish "compatible battery, don't touch" from "incompatible battery, do revalidate" — flagged so the eventual IC doesn't silently weaken this test without addressing why.

---

## 8. Explicit "do not implement yet" queue

- Any resolver/matching-rule change (`resolve_operating_point`'s `voltage_v is None` clause) — frozen pending ★1.
- Any change to `apply_components_delta`'s empty-delta normalization semantics — frozen pending ★1.
- FN-R1–R5 (secondary field notes) — out of this contract's scope, untouched.
- H5, G24-B, battery/ESC data curation — untouched, unrelated.
- Version bump / checkpoint — Engineer's call after ★ ratification and any resulting IC.

---

**End of report.**
