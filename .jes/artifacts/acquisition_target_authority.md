# Acquisition Target Authority — Conceptual Contract (Corte 0)

**Status:** CLOSED / RATIFIED  
**Date:** 2026-08-08 (ratified with FN-014…016)  
**Plan:** Acquisition Fluency Architecture  

## Statement

Jarvis must resolve *what acquisition gap is active* from **ProjectState** (via `_next_pending_block` / missing params / component presence) **before** `intent_resolver` / LLM claim the turn for acquisition-shaped language.

## What it is / is not

| Is | Is not |
|---|---|
| Unified vocabulary: block aliases ∪ component keys ∪ pending keys | Conversation Engine |
| Gate before iterate/analyze for define/declare/help phrases | Rewrite of all orchestrator checkpoints |
| Reuse of Bug54 / FN-011 / DEFINE_MISSING bridges | Silent cross-block jumps |

## Delivered cuts

| Corte | FN | Result |
|---|---|---|
| 1 | FN-014 | IDLE gate block∪component |
| 2 | FN-015 | Help-define pending, 0 LLM |
| 3 | FN-016 | Nav-back + no float on component keys |
| 4 | Copy | Deferred |

## Next architectural thread

Post-architecture handoffs (goal_plan → DSE → iterate → Continuity):  
see `.jes/artifacts/design_layer_connection_map.md` — **not** a reopening of Acquisition Fluency.
