# Design Contract — Chat GO_TO destination (`DC-assistant-chat-go-to-destination`)

**Date:** 2026-10-03  
**Status:** **★ CLOSED** (Engineer: open Buy now — close SD-GO_TO before next block)  
**Author:** JES / Cursor  
**Type:** Design lock — how chat GO_TO obtains `x_m`/`y_m` for the existing T20 sim tick  
**Parents:** [SD-GO_TO OPEN note](engineer_note_t20_goto_chat_sim_destination_debt.md) · T20 ★ @ `v0.6.29` · T25 GO_TO Skill-first ★ @ `v0.6.34` · T31 ★ @ `v0.6.40`

## Intent

Close **SD-GO_TO**: leave the chat→sim path ready so that when real coordinates exist later (GPS/world/voice), the only work is **connecting a source** into one resolver — not inventing a second sim stack.

## Locks

1. **One resolver seam** owns destination for chat GO_TO. Ordered sources this block:
   1. **Connect plug (primary for later):** if `intent.metadata` has both finite `go_to_x_m` and `go_to_y_m` → use them. Future providers (GPS/world/voice) only fill these keys.
   2. **Finite prove-now parse:** exact normalized patterns `go to <x> <y>` / `goto <x> <y>` / `ir a <x> <y>` / `ve a <x> <y>` with two finite floats → use them (proves the wire in chat today).
   3. **Else `None`** — bare `VEHICLE_GO_TO_PHRASES` stay honest “sin destino” (no invent `0,0` / home).
2. **Same T20 tick path:** when destination present after Safety `allow`, pass `SimAutonomyParams(x_m=…, y_m=…)` into existing `_sim_autonomy_tick_note` / executor.tick. When absent, keep today’s sin-destino note (wording may mention parse/connect, not invent).
3. **`propose_command` params** mirror the resolver (empty `{}` if None; `{x_m,y_m}` when set). `submit_command` / execution stay `not_implemented` — not a copper Buy.
4. **Classify:** GO_TO Task/Skill match for bare phrases **and** destination-bearing prove-now patterns. Sibling try_* refuse those patterns. Skill-first `run_skill("skill.request_go_to")` stays first.
5. **Out of block:** inventing default coordinates · live ESC/copper · TAKEOFF/RH/FOLLOW/PATROL sim ticks · voice ingress · real GPS hardware.

## Opens

Implementation Buy **`B1-assistant-chat-go-to-destination`** @ **`0.6.41`** (cola **T32**). On ★ ACCEPT: close [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md).
