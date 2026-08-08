# Cycle close — FN-013 active block declaration in DEFINE_MISSING

**Date:** 2026-08-08  
**Status:** CLOSED  
**Review:** implemented under approved contract (Engineer)

## Intent

Inside `DEFINE_MISSING_PARAMETERS`, block-level define/declare/completar for the **active** block must re-prompt the current pending acquisition — not parse as a value, not call the LLM, not restart the session.

## Fix

`_try_reprompt_active_block_declaration` in the DEFINE_MISSING branch (before analyze / component / value parse). Reuses `resolve_declare_block_request` + `_next_pending_block`.

## Validation

- `tests/test_fn013_active_block_declare_routing.py` + FN-011 → **12 passed**
- Smoke on workspace project: second `definir propulsión` → `block_declaration_reprompt`, no “No reconozco”
