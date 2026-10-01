# Design Contract — Assistant chat Skill-first (`DC-assistant-chat-skill-first`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer: after T21 ★ — next block)  
**Author:** JES / Cursor  
**Type:** Block lock — chat becomes a **Skill client** (phased)  
**Parents:** T21 Skills runtime ★ @ `v0.6.30` · C0 Skill/Capability architecture · Engineer horizon (Skill-first → voz/world → phased CLI)

## Intent

Today chat still fulfills explain/status (and vehicle/ops) via the **Task** seam. T21 added `run_skill` but chat does not call it. This block makes the Assistant chat path **Skill-first** for what is already honestly runnable — starting with the two software Skills — so later voice and CLI slices reuse the same brain.

## Block phases (not one Buy)

| Phase | Buy (indicative) | Scope |
|---|---|---|
| **A — software** | `B1-assistant-chat-skill-first-software` @ `0.6.31` | explain + project_status via `run_skill` |
| **B — vehicle/ops** | HOLD ★ @ `0.6.32` · LAND @ `0.6.33` (next); later ICs for siblings | Skill-first only where Skill is `available` and fulfill truth exists; stubs stay honest rejects; **never** SoftwareCapabilitySafetyGate-only for vehicle |
| **C — channels** | voz / world / CLI migrate | same Skills; new ingress only |

## Locks (block-level)

1. **Skill is the control surface** for in-scope kinds: chat must not bypass `run_skill` for those kinds once their phase ★ lands.
2. **No invented capability:** vehicle/ops Skills remain `stub` until a later Buy makes them `available` with a real fulfill path (sim/ops honesty unchanged).
3. **Classify may stay** (`try_*` / phrase tables) as the way to choose a Skill id — Skill-first means **fulfill through `run_skill`**, not “delete Tasks overnight.”
4. **Forward friction from T21 N1/N2** (capabilities↔intelligence edge; status provider shape) is expected to be refined in this block — already annotated; not a reopen of T21.
5. **Out of block unless ★:** live copper · SD-GO_TO destination parse · full CLI voice migrate in one Buy.

## Opens

Phase A ★ CLOSED @ **`v0.6.31`**. Phase B HOLD ★ CLOSED @ **`v0.6.32`**. Next IC: **`B1-assistant-chat-skill-first-vehicle-land`** → package **`0.6.33`** (cola **T24**).
