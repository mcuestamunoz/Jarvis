# Implementation Review — CLI feasibility vs readiness semantics

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES) — independent code + test verification (not report paraphrase)  
**Contract:** [implementation_contract_cli_feasibility_semantics.md](implementation_contract_cli_feasibility_semantics.md)  
**Report:** [implementation_report_cli_feasibility_semantics.md](implementation_report_cli_feasibility_semantics.md)  
**★:** [engineer_ratification_cli_feasibility_semantics.md](engineer_ratification_cli_feasibility_semantics.md) — ★1–★5  
**Base:** tag **`v0.3.5`** / `fc46938` plus live tree (P27-B / Option A already shipped)

## Verdict

**PASS WITH NOTES**

All seven locked-copy items (§2.1–§2.7) are present, wording matches the IC, physics is unchanged, ERF Energy stays PASS on the field fixture, and the unbound / motor-only paths still behave as before. Notes below are hygiene and coverage shape — not misses of the contract.

No version bump, no checkpoint, no commit unless the Engineer asks.

---

## Review methodology

| Step | Action | Result |
|---|---|---|
| 1 | Full suite (reviewer re-run) | **2087 passed, 0 failed** |
| 2 | IC test cluster | **106 passed** — `test_cli_feasibility_semantics`, `test_project_continuity`, `test_energy_params`, `test_project_closure_v1`, `test_phase2_lookup_operating_point`, `test_g21_g22_catalog_bind_ux` |
| 3 | Adjacent suites | `test_option_a_estimative_visibility` + `test_architecture_progress` green (in the 48-test adjacent run) |
| 4 | `scripts/cli_probe_cli_feasibility_semantics.py` | **4/4** |
| 5 | Locked copy vs `src/` | §2.1–§2.7 strings match the IC verbatim (see checklist) |
| 6 | Forbidden surfaces | `engineering_readiness.py` verdict path, `resolve_operating_point`, catalog JSON, `missing_params_for_reason` global body — **not** this IC |
| 7 | Physics on field fixture | `calculations.autonomy_min is None`, `simulation.status == "pass"`, `energy_status` still missing — asserted in unit + probe |

---

## Contract checklist (IC §2 / §6)

| Gate | Result | Evidence |
|---|---|---|
| §2.1 situation only when PASS + autonomy constraint + autonomy uncalculated | **Pass** | `project_continuity.py` elif before `"Diseño validado…"`; locked string `"Comprobación de empuje: PASS. Candidato inicial — la autonomía del objetivo no está demostrada."`; incomplete BOM still `"Física orientativa…"`; no-constraint path still `"Diseño validado…"` (`test_situation_still_diseno_validado_when_no_autonomy_constraint`) |
| §2.2 evidence named negative | **Pass** | `" — no calculada (sin evidencia de potencia de hover usable)"`; no `(actual ~…)` when current is None |
| §2.3 CTA + insight catalog-aware | **Pass** | Locked label + reason; insight `"No inventes motor_power_w a mano"`; unbound still `"Declarar … motor_power_w"` |
| §2.3 reuse `catalog_bound_motor_covers_power_w`, no second predicate | **Pass** | Same function; dual-mode object vs `.model_dump()` dict (N1) |
| §2.4 orchestrator energy proactive | **Pass** | Filters `motor_power_w` when helper True; empty list → no energy proactive; unbound path unchanged |
| §2.5 honesty note three-way | **Pass** | No constraint → `None`; calculated → original L0 `(Wh/W)×60`; uncalculated → locked `"Autonomía no calculada: … No inventes motor_power_w."`; test extended to 3 cases, not weakened |
| §2.6 calcular / simular | **Pass** | Calculate via `tool_results` `missing_energy_parameters`; simulate via `energy_status`; locked clause; no `fuera del rango del dataset` / `unverifiable` / `autonomía real` / fake minute |
| §2.7 suffix BOM-aware | **Pass** | Propeller `catalog_ref` → `" (fallback de fabricante — combo exacto no usable)"`; motor-only keeps `" (sin hélice de catálogo)"` (`test_estado_renders_honest_evidence_label` unchanged) |
| §6 unbound motor still asked to declare W | **Pass** | `test_reasoning_missing_energy_unbound_motor_still_asks_to_declare` |
| §6 physics unchanged | **Pass** | Field fixture + probe: `autonomy_min is None`, sim `pass` |
| §6 ERF Energy PASS / dual allowed (★1) | **Pass** | Probe step 4: `readiness.subsystems.energy.verdict == "PASS"` |
| §6 no `src/` outside §5 **for this IC** | **Pass** | Authorized five: `project_continuity.py`, `reasoning_layer.py`, `orchestrator.py`, `project_closure.py`, `adapters/cli/main.py` (N5 on the mixed working tree) |
| ★2 no invented `motor_power_w` | **Pass** | CTA / proactive / honesty note / insights |
| ★4 resolver untouched | **Pass** | Suffix is render-time BOM lookup only |
| ★5 no Phase 2.5 hover-unverifiable copy | **Pass** | Named negative is honest-absence wording |

---

## Harmony with prior code

```text
Thrust sim PASS                 unchanged (feasibility)
energy_status missing           unchanged (no nameplate W, no hover P)
hover_energy_autonomy_min       still None on this fixture (not relabeled)
ERF Energy / ASSEMBLY_READY     unchanged (★1 dual allowed)
L1 Combo A / ESTIMATIVO Option A not this IC; adjacent tests still green
```

`missing_params_for_reason` is still the calc-truth list. Presentation layers drop `motor_power_w` when the motor is catalog-bound. That is the IC.

---

## Notes (non-blocking)

### N1 — Dual-mode `catalog_bound_motor_covers_power_w`

ReasoningLayer context carries `design_properties` as `.model_dump()`. The helper now accepts object **or** dict. Same predicate (`catalog_ref` present and `family == "motor"`), no second helper. IC said reuse the function and pass `design_properties`; this is the smallest way to do that without reshaping orchestrator analyze context.

### N2 — Catalog-bound CTA early-return vs missing battery

When `catalog_bound_motor_covers_power_w` is True, ReasoningLayer returns the locked “no declares W” suggestion and does **not** fall through to `Declarar battery_capacity_wh`. The IC locked that table. Orchestrator §2.4 only strips `motor_power_w`, so a catalog motor **without** battery Wh still gets a battery proactive. Field fixture has Wh set. Not a fail.

### N3 — Helper name vs predicate

`_catalog_bound_motor_lacks_watts` names a “no watts” fact; the predicate is “SKU bound”, including motors that **do** publish `max_watts`. ★2 asked for this helper. Bind writes `motor_power_w` when the SKU has W, so `missing_energy_parameters` rarely fires for those SKUs. Copy “este motor de catálogo no declara vatios” is correct for `emax_rs2205s_2300`. Do not tighten the predicate in a drive-by.

### N4 — E2E fixture is not the full field 4/4 walk

`tests/test_cli_feasibility_semantics.py` binds motor + propeller + 4S + constraint; it does not recreate frame/FC/ESC. Continuity unit test uses closed BOM + `architecture_progress="4/4"`. Together they cover §3. The live workspace `autonomía-de-5min-c09442c25db0` is not required for the IC.

### N5 — Working tree vs last commit is mixed

`git status` still shows files **outside** this IC (`engineering_readiness.py` architecture `param_present_for_architecture`, `motor_catalog_assist.py` / `param_definition_session.py` `format_motor_chosen_line`, Option A `calculate.py` / `iterate.py` / `simulate.py`, etc.). Those are **prior uncommitted slices**, not this implementation. Claude’s “exactly five `src/` files” is true **for this IC**. `engineering_readiness.py` was not part of §2; do not treat the dirty tree as an IC breach. Commit remains Engineer-gated and should not mix slices unless asked.

### N6 — Situation gate uses `req["autonomy_target_min"]`

IC text said `parsed_constraints.autonomy_min`. Production fills `autonomy_target_min` from that constraint in `derive_physical_requirements`. Equivalent on the orchestrator path. Direct `build_project_continuity` tests pass `physical_requirements` explicitly, which is the right seam.

---

## Next

This IC is **closed**.

Agreed queue (Engineer already locked; do not start Structure / C-081 / Option B / HD-*):

```text
Block Closure B-PROP-ENERGY
  → Engineer ★ on existing investigation
    (investigation_report_post_v034_block_closure.md
     + investigation_review_post_v034_block_closure.md)
  → Cursor writes the IC for Claude
  → stop
```

Cursor does **not** implement `src/` on Block Closure until that IC is ratified. No checkpoint from this review.
