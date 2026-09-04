# Investigation Review — CLI feasibility vs readiness semantics

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_cli_feasibility_semantics.md`](investigation_contract_cli_feasibility_semantics.md)  
**Report:** [`.jes/artifacts/investigation_report_cli_feasibility_semantics.md`](investigation_report_cli_feasibility_semantics.md)  
**Seed notes (not proof):** [`.jes/artifacts/engineer_notes_cli_feasibility_semantics.md`](engineer_notes_cli_feasibility_semantics.md)  
**Base:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` · commit `fc46938` (live tree + field fixture, as the report discloses)

## Verdict

**PASS WITH NOTES**

Contract gates 3.1–3.6 answered with file:line. Fixture fields confirmed. Option A recommended; Option B recorded and **not** adopted (C1). Option C rejected. No `src/` / test edits. No stop-and-rewrite.

The four claim-language findings hold under independent spot-check. Two notes for the **future IC** (not a reject): (1) the hover “named negative” is a **different Phase 2.5 case** than this fixture’s honest omission; (2) a test **does** pin the suffix string that §8 said was not found.

**Ready for Engineer ★.** Cursor writes the Implementation Contract **for Claude** after ★. Do not implement before that IC.

---

## Contract checklist

| Criterion | Result |
|---|---|
| Fixture confirmed in `state.json` | **Pass** — report table matches live `c09442c25db0` (spot-check: `autonomy_min` null, `energy_status` missing, `hq_5045_bn` catalog_ref, fallback `propeller_sku` null) |
| 3.1 situation predicate | **Pass** — `project_continuity.py:83-104`; upgrade is BOM-complete + sim PASS, not energy |
| 3.2 which surface won | **Pass** — ReasoningLayer `_collect_suggested_actions` `:235-248` → Continuity `:226-228`; FN-005 `:183-208` correctly shown as not firing |
| Dual contract `param_present_for_architecture` vs `missing_params_for_reason` | **Pass** — `:61-69` vs `:333-334` |
| 3.3 silent autonomy | **Pass** — `main.py:442-443,463-464`; see Note 1 |
| 3.4 suffix vs BOM | **Pass** — `main.py:316-317`; fixture dual-truth confirmed |
| 3.5 Option A/B/C | **Pass** — A recommended; B mechanism traced (`_energy_evidence:943-952`) and left for a later ERF slice; C rejected |
| 3.6 tests / probe sketch | **Pass with Note 2** — probe sketch usable; suffix test miss |
| C1–C5 respected | **Pass** — no ERF rollup, no invented W, no ladder, no resolver policy, no DSE/HD/Block Closure |
| No production code | **Pass** |

---

## Independent verification (spot-check)

| Claim | Cursor check |
|---|---|
| Situation `elif sim_status == "pass"` has no energy read | **Confirmed** — `project_continuity.py:101-102` |
| `_collect_suggested_actions` (not only `_build_`) emits Declarar `motor_power_w` | **Confirmed** — `_build_suggested_actions` `:176` delegates to `_collect` `:188`; energy branch `:235-248` |
| `missing_params_for_reason` is `params.get is None` | **Confirmed** — `parameter_requirements.py:333-334` |
| `catalog_bound_motor_covers_power_w` docstring names `emax_rs2205s_2300` | **Confirmed** — `project_closure.py:44-51` |
| `_energy_evidence.calculated` = Wh **or** autonomy | **Confirmed** — `engineering_readiness.py:943-952` |
| `energy_model_honesty_note` unconstrained by calc | **Confirmed** — `project_closure.py:390-400` |
| Suffix keyed only on `fallback_operating_point` | **Confirmed** — `main.py:316-317` |
| Literal suffix asserted in tests | **Found** — `tests/test_phase2_lookup_operating_point.py:349` (report §8 missed this) |
| Honesty note test | **Found** — `tests/test_project_closure_v1.py:61-65` (report named the file; IC must update it if gating changes) |

---

## Notes (non-blocking — IC must absorb)

### Note 1 — Do not paste Phase 2.5 “unverifiable” onto this fixture

The hover block at `main.py:349-356` renders a named negative only when `ctx["hover_energy"]` is present and `source_type == "unverifiable"` (dataset exists, thrust out of range).

This fixture has `hover_energy_resolution: null` → `_hover_energy_from_calculations` returns None (`orchestrator.py:151-164`, locked honest **absence** when there is no Discrete OP Dataset). `estado` therefore **omits** the hover line entirely. That is Phase 2.5 policy, not the same case as `below_min`/`above_max`.

IC copy for `calcular`/`simular` should use a **missing-energy / no hover dataset** reason class, **not** “fuera del rango del dataset”. Do not invent `hover_energy_autonomy_min`. Do not relabel L1.

Also: `calcular` may return `calculations` without `simulation.energy_status`. Gate the named negative on `autonomy_min is None` plus an already-present signal (`tool_results` / `parsed_constraints.autonomy_min` / latest sim `energy_status` if the action included sim). Do not assume `energy_status` is on the calculate payload.

### Note 2 — Suffix test exists

`test_estado_renders_honest_evidence_label` asserts `"(sin hélice de catálogo)" in rendered` for motor-only bind (no propeller yet). That string is **correct** for that fixture. Option A must keep it when BOM has **no** `propellers.catalog_ref`, and drop/replace it when the propeller **is** bound (this field walk). Update that test with a second case; do not delete the motor-only assertion.

### Note 3 — Orchestrator proactive still catalog-blind

Contract surface: `build_startup_context` `:4115-4131` still sets `proactive_question = "¿Definimos motor_power_w (energía) ahora?"` via the same `missing_params_for_reason`. Continuity did not use that string as the visible CTA on the closed-BOM path (ReasoningLayer label won). IC should still **gate this branch** with `catalog_bound_motor_covers_power_w` (or stop setting `missing_params` to `motor_power_w`) so a later rank/UI cannot resurrect the W wizard. Add `orchestrator.py` to the Option A file list.

### Note 4 — Situation copy vs ERF dual (in scope to name, not to merge)

Option A will make Continuity say something like “comprobación de empuje / candidato inicial” while ERF can still print `ASSEMBLY READY`. That dual is **allowed under C1**. IC must not paraphrase ERF as “5 min demonstrated,” and must not change `_energy_evidence`.

---

## Engineer ★ — Cursor lean (ratification, not decided)

| Topic | Lean |
|---|---|
| Accept report Option A as IC target | **Yes** |
| Keep C1 (no Energy PASS / `ASSEMBLY_READY` change) | **Yes** |
| Include honesty-note gating (§7) in the same IC | **Yes** — adjacent, cheap, same claim-language bug |
| Include orchestrator `:4115` gate (Note 3) | **Yes** |
| Option B as follow-up ERF investigation | **Later** — not this IC |
| Claude implements from IC only | **Yes** — Cursor writes IC after ★ |

If Engineer disagrees with C1 (wants Energy PASS aligned in the same cut), rewrite the investigation contract — do not stretch Option A.
