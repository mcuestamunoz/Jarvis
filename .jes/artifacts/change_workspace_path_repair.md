# Change — workspace_path repair on load

**Date:** 2026-08-05  
**Operation:** Implement

## Summary

`StateManager.load(state_path)` now derives and persists `workspace_path` from the real directory of `state.json` when the stored path is missing or points elsewhere (migrated / legacy trees).

## Files

| File | Change |
|---|---|
| `src/jarvis/core/state_manager.py` | `_repair_workspace_path` after validate; write-back to disk |
| `tests/test_workspace_path_repair.py` | New coverage (+ regression for define_missing persist) |
| `docs/ARCHITECTURE.md` | Default workspace root + repair rule |
| `docs/IMPLEMENTATION_TASKS.md` | Test count / status |

## Validation

- Full suite: **1337 passed** (includes previously env-failing `test_answer_wizard_bidir_no_match_falls_to_positional`)
