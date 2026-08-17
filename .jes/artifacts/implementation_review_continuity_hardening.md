# Implementation Review — Continuity Hardening

**Date:** 2026-08-15  
**Reviewer:** Cursor (Implementation Review)  
**Contract:** [implementation_contract_continuity_hardening.md](implementation_contract_continuity_hardening.md)  
**Report:** [implementation_report_continuity_hardening.md](implementation_report_continuity_hardening.md)  
**Design:** [design_continuity_hardening.md](design_continuity_hardening.md) (CLOSED ★1–★7)

**Verdict: PASS WITH NOTES**

---

## Scope check

| Gate | Result |
|---|---|
| Slices 1–4 present | ✅ |
| ★1–★7 respected | ✅ (no retarget; no thrust gate; no `_ITERATE_PREEMPT_INTENTS` narrow) |
| G10 materials modules changed for Continuity | ✅ not required — Continuity diff is orchestrator / motor_catalog_assist / param_definition_session + tests |
| Tests T1–T10 | ✅ (+ T4b, T7b) |
| Targeted re-run | ✅ `test_continuity_hardening` + `test_g10_materials_frame` + `test_fn019_bare_propeller_size` → **43 passed** |

Full suite 1753 claimed by implementer; spot suite green under review.

---

## Spot-checks (code ↔ ★)

| ★ / Slice | Evidence | Status |
|---|---|---|
| ★4 G14 | Force gated: `motors not in expected_keys or _looks_clearly_propeller_shaped` (`orchestrator.py` ~1928–1938); KV / size-band heuristic | ✅ matches N1 from investigation review |
| ★4 FN-019 | Singleton + composite bare `10x4.5` still force (T2/T3) | ✅ |
| ★2 refuse | `_maybe_refuse_different_target` before affirmative/infer; no session mutate; cancelar hint (T4/T5) | ✅ |
| ★2 no retarget | No clear-and-reopen path in refuse helper | ✅ |
| ★5 list-motors | `is_list_motors_phrase` in `_answer_assisted_motor` → `offer_catalog_help` (T6) | ✅ |
| ★6 filtered max | `format_no_thrust_candidate_message(..., kv=, prop_inch=)` uses `find_motors_for_requirements` (T7) | ✅ |
| ★3 G11 | Owns-input before strong-intent; `{None,"iterate"}` suppressed while owned; `variable`+`operation is None` ownership; `simula` still preempts (T8–T10) | ✅ |
| ★7 | No thrust under-req gate | ✅ |

---

## Notes (do not block CLI)

### N1 — Slice 1 heuristic remains tunable
`_looks_clearly_propeller_shaped` is correct for the smoking-gun phrase and FN-019 sizes. CLI BOM walk should try one odd motor phrase without `KV` (if any) and one edge propeller size. Residual risk already flagged in the report — acceptable.

### N2 — Slice 2 coverage is declare/G8-shaped only
Bare component keywords without declare verb still fall through (contract-scoped). OK for this cut; watch during CLI if users say only `frame` mid-battery.

### N3 — T6 asserts wizard stays open, not list contents
Optional follow-up: assert motor names appear in the message. Not a FAIL — `_FakeLLM` + `offer_catalog_help` path is enough for ★5 intent.

### N4 — System Map caveats still report-only
Apply after CLI PASS if Engineer wants (proposed text already in report §).

---

## Next

**CLI BOM walk** (Engineer):

```text
n → proyecto nuevo
→ A arquitectura
→ declarar motors (frase tipo 1x 2306… / catálogo) — NO "Hélices registradas"
→ propellers / battery / frame
→ mid-wizard: "definir frame" mientras battery → refuse + cancelar
→ thrust: "que motores…" → lista; "ayúdame a elegir" → max coherente
(opcional) iterate material: "pvc" / "cambiar a pvc" sin loop
```

Success: walk usable **without** `cancelar` as a required ritual except intentional retarget (★2).

Then: resume G10 PVC / `checkpoint-g10` decision; optional map doc caveats.
