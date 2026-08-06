# Field note — motor suggestions (value vs noise)

**Date:** 2026-08-05  
**Path:** orchestrator `handle_user_text` + `IterateInteractiveSession`  
**Catalog:** 6 motors (`ComponentLibrary`)

## Checklist

| # | Question | Verdict |
|---|---|---|
| 1 | Prompt at right moment (KV, no thrust)? | **Yes** — DEFINE @ step 2 |
| 2 | Options relevant to declared KV? | **Mostly** — 920→SunnySky+generic; 2300→EMAX; 1500→none |
| 3 | Pick `1` enriches thrust for physics? | **Yes** — thrust_n + weight_g on spec |
| 4 | `no` advances cleanly? | **Yes** — step 3, suggestions cleared |
| 5 | Empty catalog UX? | Was **silent skip** → **fixed**: explicit biblioteca note |
| 6 | Noise / interrupt? | Mild: `generic_920kv` next to real part; catalog thin |

## Blocking bug found (preempt regression)

Hard component preempt (LLM cycle) aborted DEFINE motor entry (`4 motores 920KV` → `component_description_saved` + closed wizard).  

**Fix:** `_iterate_owns_component_input` — no component preempt when `motor_suggestions` or `DEFINE @ step 2`. Step-4 preempt (`carbono 400g`) preserved.

## Verdict

**Suggestions aportan valor** when the catalog hits: clear numbered list, user-confirm only, no auto-apply.  

**Ruido acotado:** catálogo pequeño (gaps KV), generic fallback. Not worth killing the feature. Optional later: expand catalog / demote generics in ranking.

## Status

Validation item **done**. Code fixes shipped; 1371 tests green.
