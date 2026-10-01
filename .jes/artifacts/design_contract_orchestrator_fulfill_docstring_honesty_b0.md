# Design Contract — Orchestrator fulfill docstring honesty (`DC-orchestrator-fulfill-docstring-honesty`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer: next cola after T14/T17 ★)  
**Author:** JES / Cursor  
**Type:** Docs/comment honesty — T14 N1 residual  
**Parents:** T14 allow-list ★ @ **`v0.6.25`**

## Intent

After T14, fulfill method docstrings / intercept comments in `orchestrator.py` (and related `assistant_task` notes) still say TAKEOFF/RETURN_HOME/FOLLOW/PATROL stay `verb_not_allowed` when armed. Arm UX user copy is already correct. Fix the stale comments so code docs match tip policy.

## Locks

1. Comment/docstring only — **no** behavior change.
2. Scope: `core/orchestrator.py` fulfill/intercept comments that contradict T14 seven-verb allow-list; optional one-line `assistant_task.py` module notes if still stale.
3. Out: CHARGE · copper · Skills · phrase tables · Safety logic.

## Opens

IC **`B1-orchestrator-fulfill-docstring-honesty`** → package **`0.6.27`**.
