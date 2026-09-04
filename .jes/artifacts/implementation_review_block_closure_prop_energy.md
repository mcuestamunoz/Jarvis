# Implementation Review — Block Closure B-PROP-ENERGY

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES) — independent code + live fixture traces (not report paraphrase)  
**Contract:** [implementation_contract_block_closure_prop_energy.md](implementation_contract_block_closure_prop_energy.md)  
**Report:** [implementation_report_block_closure_prop_energy.md](implementation_report_block_closure_prop_energy.md)  
**★:** [engineer_ratification_block_closure_prop_energy.md](engineer_ratification_block_closure_prop_energy.md) — ★1–★6  
**Base:** tag **`v0.3.5`** / `fc46938` plus live tree (P27-B / Option A / CLI feasibility already shipped)

## Verdict

**PASS WITH NOTES** — **N1 closed** (re-check 2026-09-01). Engineer CLI walk Combo A / PRODUCT_SCOPE is now the next gate.

The rollup, Gate A tests, re-bind IDLE phrases, `_derive_overall`, and CLI feasibility locked strings are in place. N1 (false `descarga excedida` on unverifiable discharge) is **patched and re-checked**. Notes N2–N7 below are residual, not walk blockers.

No version bump, no checkpoint, no commit unless asked.

---

## Review methodology

| Step | Action | Result |
|---|---|---|
| 1 | Full suite (reviewer re-run) | **2094 passed, 0 failed** |
| 2 | IC tests | `tests/test_block_closure_prop_energy.py` **7/7** |
| 3 | G27 | `tests/test_battery_catalog_bind_ux.py` **13/13** |
| 4 | Adjacent | CLI feasibility + Option A + continuity + energy + P27-B + G21 — **100** in the clustered run, all green |
| 5 | Probes | `cli_probe_block_closure_prop_energy.py` **4/4** · `cli_probe_cli_feasibility_semantics.py` **4/4** |
| 6 | Forbidden surfaces | `_derive_overall` body unchanged; eight `validated = ctx.sim_status == "pass"` still there; no `BLOCK_STATUS`; no tenth `SUBSYSTEM_KEYS`; `electrical_compatibility.py` / `library/` / `design_explorer.py` not this IC |
| 7 | Live harmony traces (reviewer, not in report) | Combo A dual render; emax fixture; emax+ESC; G27 phrase vs SKU detect; wizard-then-SKU |

---

## Contract checklist

| Gate | Result | Evidence |
|---|---|---|
| §2 IDLE `definir bateria <sku>` / `cambia la bateria a <sku>` | **Pass** | Live path is `try_ingest` → `detect_battery_sku_token` → `bind_battery_from_catalog` + `set_battery_component` via `battery_catalog_spec`. Wh = **222.0**, not 6.0. G27 `"LiPo 6S 10000mAh"` does **not** match a SKU token (reviewer confirmed `detect_battery_sku_token(...) is None`). |
| §3.1 return shape | **Pass** | `block_id`, `status`, `evidence_tier`, `reasons`, `facts` |
| §3.2 closed iff 9 conditions | **Pass** | Verdicts + four electrical facts + sim pass + three `catalog_ref` families. Does **not** read `electronics.evidence.validated` as ESC proof. |
| §3.3 tier | **Pass** | Reads `current_parameters["propulsion_resolution"]` JSON (same store as P2-1). `closed` allowed at fallback; failed checks stay `not_closed` even at `manufacturer_test` (Gate A incompatible: tier still `manufacturer_test`, status `not_closed`). |
| §3.4 ctx-only | **Pass** | `ctx["prop_energy_block_closure"]`; optional `readiness=` kwarg so G9-A resolver-once still holds (report §3 — credible, suite includes that guard). Not an `EngineeringReadinessResult` field. |
| §4 locked CERRADO strings | **Pass** | manufacturer_test / fallback / débil match the IC verbatim |
| §4 NO CERRADO discharge vs other | **Miss — N1** | Discharge sentence fires whenever `battery_discharge != "within_limit"`, including **`unverifiable`**. Gate A `exceeded` is correct; field-like fixture is not. |
| §4 does not replace `PROJECT STATUS` | **Pass** | Line appended after `_render_readiness_block` |
| §6.1–6.5 | **Pass** | Reviewer re-run |
| §6.2 dual | **Pass** (stronger live check) | Same Combo A render: `BLOQUE … CERRADO` **and** `PROJECT STATUS: NOT ASSEMBLY READY` |
| §6.6 unbound propeller | **Pass** | `propellers_not_catalog_bound` |
| ★1 derivable, no new subsystem | **Pass** | Function in `project_closure.py` |
| ★6 fallback-honest | **Pass** on the closed path; N1 is the not-closed copy |
| No CLI feasibility copy rewrite | **Pass** | `Comprobación de empuje…` / `Diseño validado…` untouched |
| No `src/` outside §5 **for this IC** | **Pass** | Authorized set. Dirty tree still has Option A `iterate.py` and G21 `engineering_readiness.py` from **prior** slices — not this IC. |

---

## Harmony (this is the point of the deep pass)

Jarvis is one surface. Independently traced:

### What is coherent

- **Finding B-3 dual works on Combo A:** block `closed` + overall `NOT_ASSEMBLY_READY` in one `estado`. That is the IC.
- **CLI feasibility fixture (emax + HQ + 4S, no ESC):** block `not_closed`, Continuity `Comprobación de empuje… autonomía no está demostrada`, Energy ERF still `PASS`, `PROJECT STATUS: NOT ASSEMBLY READY`. Status side is honest. Copy is not (N1).
- **Gate A incompatible:** `sim=pass` (thrust), `battery_discharge=exceeded`, propulsion/energy `INCOMPATIBLE`, discharge line **correct**.
- **Re-bind vs G27:** SKU token vs human `6S 10000mAh` are different strings; G27 path is not stolen.
- **Physics:** no new W, minutes, resolver rules, or `_energy_evidence` rewrite.

### What is not coherent — N1 (blocking for walk)

Reviewer reconstruction of the **field-like** stack (`emax_rs2205s_2300` + `hq_5045_bn` + `lipo_4s_10000mah` + freeform ESC 40A, autonomy 5 min):

```text
facts.battery_discharge = unverifiable
facts.esc_vs_motor      = unverifiable
status                  = not_closed
CLI                     = NO CERRADO — descarga de batería excedida   ← false
Situación               = Comprobación de empuje: PASS. Candidato inicial…
```

Cause: `derive_prop_energy_block_closure` labels every failed `within_limit` check `battery_discharge_exceeded`, and the CLI treats that token as the Gate A discharge sentence.

Same fixture without ESC also prints the discharge sentence (`unverifiable` + `esc_presence=missing`).

The Engineer will see this on a walk. Do not walk until patched.

**Required fix (Claude, still this IC — not a new slice):**

1. Reason tokens must follow the actual `CheckOutcome` (`exceeded` vs `unverifiable` vs `not_applicable`), **or** keep a generic reason and only emit the locked discharge sentence when `facts["battery_discharge"] == "exceeded"`.
2. All other not-closed cases use the locked generic: `NO CERRADO — el stack de propulsión/energía no está cerrado`.
3. Regression: emax+HQ+4S (CLI feasibility fixture) rendered `estado` must **not** contain `descarga de batería excedida`. Gate A `motor_count=4` must still contain it.
4. Do not change `_derive_overall`, electrical formulas, or closed-path copy.

---

## Notes (non-blocking unless marked)

### N2 — Wizard-then-SKU still scrapes (IDLE phrases are fixed)

`try_ingest` runs on IDLE, **before** intent. The two IC phrases never open the wizard.

If the user first says `definir bateria` (opens `ParamDefinitionSession.answer`) and then types `lipo_6s_10000mah`, reviewer trace: SKU stays `lipo_4s_1500mah`, Wh stays 22.2 (wizard did not bind). `answer()` has no SKU intercept.

IC said one intercept is enough for those phrases. IDLE is done. The two-step wizard remains a G27-class hole. Fix in the same patch if cheap (`answer()` when `pending[0]==battery_capacity_wh` reuse `detect_battery_sku_token`); otherwise document and leave for a follow-up — **not** a reason to reopen G27.

### N3 — `try_ingest` binds on any utterance that contains a SKU token

`"compara lipo_4s_1500mah y lipo_6s_10000mah"` binds the **first** name in `list_batteries()` sort (`lipo_4s_1500mah`), mutates state, skips analyze. Acceptable for the IC phrases; aggressive for questions. Do not broaden in this patch.

### N4 — `views/estado_actual.md` does not get the block line

IC scoped `render_startup_context`. Workspace markdown is a different surface. Walk is the **CLI**. Do not treat the file view as the product.

### N5 — Combo A Continuity still says `Diseño validado` when autonomy **was** calculated

Fixture has no unmet autonomy constraint, so CLI feasibility’s situation branch does not fire. Same `estado` can show `Diseño validado` + `NOT ASSEMBLY READY` + `BLOQUE CERRADO`. That is pre-existing Continuity vs ERF, not a miss of §3. The walk should use Combo A **with** the 5 min constraint if you want the CLI-feasibility situation in the same screen.

### N6 — Double `evaluate_electrical_compatibility` per `estado`

`build_engineering_readiness` already runs it; the rollup calls it again. Pure, no G9-A spy. Fine.

### N7 — Working tree still mixed with prior uncommitted slices

`iterate.py` (Option A ESTIMATIVO) and `engineering_readiness.py` (`param_present_for_architecture`) are **not** this IC. Commit remains Engineer-gated and should not dump the whole tree as Block Closure.

---

## Report vs code

The implementer report is accurate on files, live `try_ingest` root cause (better than the IC’s `parse_floats_from_input` guess), G9-A double-readiness fix, and Gate A numbers. It did **not** catch N1. That is why the review traces fixtures the tests did not render.

---

---

## N1 re-check (2026-09-01)

**Pass.** Claude gated the locked discharge sentence on `facts["battery_discharge"] == "exceeded"` (`adapters/cli/main.py`). Reason tokens in `derive_prop_energy_block_closure` were left as-is (allowed). New test `test_unverifiable_discharge_does_not_claim_exceeded` covers the emax fixture.

Reviewer live traces:

| Fixture | `battery_discharge` | CLI line |
|---|---|---|
| Gate A `motor_count=4` | `exceeded` | `… descarga de batería excedida` |
| emax + HQ + 4S, no ESC | `unverifiable` | generic `… el stack … no está cerrado` |
| emax + HQ + 4S + ESC 40A (field-like) | `unverifiable` | generic (not discharge) |

Suite **2095**. G27 / CLI feasibility tests green. `_derive_overall` untouched.

Optional N2: `answer()` binds a live SKU when **`pending[0] == battery_capacity_wh`**. Reviewer confirmed: that wizard + `lipo_6s_10000mah` → sku + 222.0 Wh. `"definir bateria"` on an already-bound battery still opens `motor_power_w` first — typing a SKU on *that* turn does not re-bind (IDLE full phrases still do). Residual, not a walk blocker.

## Next

Engineer **CLI walk Combo A / PRODUCT_SCOPE** (required). If that walk lies, that is the next investigation — not Option B / H5 / Catalog Foundation by default.
