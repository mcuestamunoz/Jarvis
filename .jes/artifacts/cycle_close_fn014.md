# Cycle close — FN-014 Acquisition Target Authority (IDLE)

**Date:** 2026-08-08  
**Status:** CLOSED  
**Review:** PASS WITH NOTES  
**Suite reported:** 1476 passed  

## Verdict summary

IDLE `definir propellers` opens deterministic acquisition via unified mention helper + existing Bug54/FN-011 bridge. Wrong-block mentions get a deterministic mismatch message (no silent jump). FN-011/013 regressions green.

## Notes (non-blocking)

1. Whole-token aliases (`motor`) can misfire in figurative phrases — verb + active-gap mitigate, not eliminate.
2. Verb-gate regression was caught by full suite (`test_frame_material_only_not_routed_to_llm`) — good discipline.
3. Generic Phase A copy (`¿Cuál es el valor de propellers?`) unchanged — deferred.

## Next

FN-015 / FN-016 Implementation Contracts when Engineer prioritizes.
