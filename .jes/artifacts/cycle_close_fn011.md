# Cycle close — FN-011 Propulsion declaration deterministic routing

**Date:** 2026-08-08  
**Status:** CLOSED  
**Baseline tests at close:** 1456 passed (7 new)  
**Review:** PASS WITH NOTES

## Intent

`"ayúdame a declarar propulsión"` must not wake the LLM when project state already knows the next acquisition gap for that architecture block.

## Evidence

- Root cause: `ANALYZE_PATTERNS` `\bayudame\b` matched before any declare+block route existed.
- Fix: `resolve_declare_block_request` (verb + `normalize_block_alias`) + IDLE `_try_declare_active_block_help` only when named block == `_next_pending_block`, reusing Bug 54 bridge.
- Smoke CLI: IDLE project with pending propulsion → define_missing with `['motors','propellers']`, 0 LLM.

## Deferred (explicitly not in this cut)

1. Same leak inside active `DEFINE_MISSING_PARAMETERS` — needs re-prompt, not session rebuild.
2. Pre-existing generic first question for component keys (`¿Cuál es el valor de motors?`).

## Verdict

FN-011 **closed**. Architectural leak on the IDLE field-note path is fixed without new acquisition logic.
