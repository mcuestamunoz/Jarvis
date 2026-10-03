# Design Contract — Connect plugs / real-data debt map (`DC-connect-plugs-real-data-map`)

**Date:** 2026-10-03  
**Status:** **★ CLOSED** (Engineer: index all real-data debts; IC for Claude)  
**Author:** JES / Cursor  
**Type:** Design lock — single SoT index of “structure ready → connect when real data applies”  
**Parents:** Skill-first phase B ★ @ `v0.6.40` · T32 SD-GO_TO AUTHORIZED @ `0.6.41` · PRIORIDAD parked lists · `HARDWARE_DEBT.md`

## Intent

Today connect-later seams are scattered across IC/review/CONNECTIONS/PLATFORM/code comments. This block creates **one living map** so that when real coordinates, battery, ESC, sensors, or voice arrive, the Engineer can see **where to connect** without re-deriving the cola.

## Locks

1. **One SoT artifact** (markdown under `.jes/artifacts/`) is the index of connect plugs / real-data debts. PRIORIDAD links it. Not a second product roadmap.
2. **Taxonomy (required columns):** stable `id` · type (**A** software connect plug · **B** honesty stub · **C** parked hardware/lab · **D** horizon voice/world) · deferred product meaning · seam today (file/symbol) · what “connect later” means · status · evidence paths.
3. **Scope in:** Assistant/Skill/sim/copper/ops connect seams; Intent channel stubs; ESC/GPIO/DShot/gyro/USART/baud/ELRS; sim HAL vs live sensors; HD-001…005; world package. **Scope out:** geometry Path N / Board polish as primary rows (may footnote); Continuity kit spam laterals; closed Skill-first stubs already flipped.
4. **Honesty:** map must not invent plugs that do not exist; must flag soft gaps (e.g. TAKEOFF altitude / FOLLOW target / PATROL route lack a named metadata Buy unlike SD-GO_TO).
5. **Maintenance:** when a Buy closes or opens a plug, the map row status updates in that Buy’s docs pass (or a tiny follow-on). This Buy seeds the map; it does not close the debts themselves.
6. **Out of block:** implementing GPS/ESC/voice/battery · closing T32 · changing runtime behavior.

## Opens

Implementation Buy **`B1-connect-plugs-real-data-map`** @ **`0.6.42`** (cola **T33**).
