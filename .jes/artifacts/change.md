# Change — FN-012 draftless wizard snapshot sanitize

**Date:** 2026-08-08  
**Operation:** Implement (minimum cycle)

## Summary

Never persist or restore `create_project_interactive` / `iterate_interactive` without drafts. Demote to `IDLE` so reopen cannot trap the router.

## Files

| File | Change |
|---|---|
| `state_manager.py` | `_sanitize_draftless_wizard_session` on persist + restore |
| `tests/test_u4_conversation_persistence.py` | 4 FN-012 regressions |
| Docs | IMPLEMENTATION_TASKS + PROJECT_CONTINUITY |

## Validation

- `pytest tests/test_u4_conversation_persistence.py tests/test_session_mode_coercion.py` → **17 passed**
