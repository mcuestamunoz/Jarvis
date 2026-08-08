# Change — FN-013 active block declaration in DEFINE_MISSING

**Date:** 2026-08-08  
**Closed:** `.jes/artifacts/cycle_close_fn013.md`

## Summary

While DEFINE_MISSING is open, declare/define/completar + the active architecture block re-prompts the current pending parameter. Session and `collected_params` are preserved; 0 LLM; no cross-block jump.

## Files

| File | Change |
|---|---|
| `orchestrator.py` | `_try_reprompt_active_block_declaration` before analyze/value |
| `tests/test_fn013_active_block_declare_routing.py` | 5 regressions |
| Docs / `.jes` | FN-013 closed |

## Validation

- Focused FN-011+013: **12 passed**
- Workspace smoke: `definir propulsión` twice → reprompt, no value error
