# Design Contract — Assistant chat → sim copper (`DC-assistant-chat-sim-copper`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer: next cola after T14/T17 ★)  
**Author:** JES / Cursor  
**Type:** First **allow → sim tick** bridge for chat vehicle path  
**Parents:** T14 allow-list ★ · C40 `SimAutonomyExecutor` · C41 sim policy

## Intent

Today chat armed verbs get Safety `allow` but `submit_command` always returns execution `not_implemented`. Copper Buy = wire **sim** execution for the three verbs `SimAutonomyExecutor` already supports (`HOLD`/`LAND`/`GO_TO`) after allow — still **not** live motors/ESC/GPIO, still not TAKEOFF/RH/FOLLOW/PATROL sim ticks.

## Locks

1. After Safety `allow` on chat fulfill for HOLD/LAND/GO_TO only: call `SimAutonomyExecutor.tick` (or thin orchestrator helper) with empty/default params; report honest **sim** outcome in the chat message (never claim copper flight / motors / ESC arm).
2. Extend `ExecutionState` / `submit_command` **or** keep `submit_command` as Safety-only and tick **beside** it in orchestrator — prefer **orchestrator-side tick after allow** so C4 surface honesty (“submit_command never executed”) stays true unless IC explicitly widens `surface.py`. **Preferred:** leave `submit_command` returning `not_implemented`; orchestrator, only when `safety.outcome==allow` and verb ∈ {HOLD,LAND,GO_TO}, runs sim tick and appends sim status to message (`execution` field may stay `not_implemented` **or** add new literal `"sim_ticked"` if types are extended — pick one and test).
3. TAKEOFF/RETURN_HOME/FOLLOW/PATROL: still allow + **no** sim tick (unsupported by sim executor) — message must say sim unsupported / not_implemented.
4. Disarmed path unchanged (`reject`/`disarmed`).
5. Never import ESC / never call `SimulatedEscSink.arm` from chat.
6. CHARGE / Skills out. No tip pins.

## Opens

IC **`B1-assistant-chat-sim-copper`** → package **`0.6.29`**.
