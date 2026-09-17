# Implementation Review — Disk-station radial reach (`B1-disk-station-reach`)

**Date:** 2026-09-15  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_disk_station_reach_b1.md) · [report](implementation_report_disk_station_reach_b1.md)  
**Verdict:** **PASS WITH NOTES** · smoke **ACCEPT** (2026-09-16)

---

## Locks

| # | Lock | Result |
|---|---|---|
| 1–2 | Buy · motors↔frame_arm only · props stay `n_a_disk` | **Pass** |
| 3 | New helper · not widen `screen_posed_envelope` | **Pass** — `station_reach_screening.py` |
| 4–5 | Inputs + L≤R / L>R · Visor math reused | **Pass** — imports `_quad_x_*` from `spatial_board` |
| 6 | Status vocabulary `station_reach_*` | **Pass** |
| 7 | Copy honesty (alcance, no VERIFIED / no cabe AABB) | **Pass** — `format_station_reach` |
| 8 | fit_relations wire · `relaciones` | **Pass** |
| 9 | Attest on reach-ok · new fingerprint · clear-on-change | **Pass** — motors branch in writer |
| 10–11 | Forbidden / tests-only | **Pass** — `0.4.1` · no `workspace/` persist |

## Tests (IC §2)

| ID | Result |
|---|---|
| T1–T8 | Covered in `tests/test_disk_station_reach_b1.py` (23) |
| T9 | Report suite **2968** · Cursor re-ran reach + fit-relations + fit-attestation → **48 passed** |

## Notes (soft — not FAIL)

| ID | Note |
|---|---|
| **N1** | `jarvis.core` imports private helpers from `jarvis.workspace.spatial_board` — correct for “one math”, mild layer inversion. Acceptable this Buy; later extract `_quad_x_*` to a shared pure module if the cycle bites. |
| **N2** | `set_component_mounted_on` now **always clears** `declared_fit_attestation` on the subject — including box-family keys whose fingerprint does not include `mounted_on`. Safer than stale seals; slightly broader than “clear only station fingerprint inputs”. Documented in report; no FAIL. |
| **N3** | Claude’s §3 smoke was **in-memory** on live projects (not persisted). Engineer CLI smoke still valuable for ACCEPT, or waive on tests + report. |

## Smoke (Engineer 2026-09-16) — **ACCEPT**

1. `relaciones` → motors↔frame_arm `→` reach-ok + suggest `declaro verificado el motor`; propellers still `n_a_disk`; plate stack blocked on estimated (orthogonal).  
2. `declaro verificado el motor` → seal granted with honesty copy.  

## Out of scope confirmed

prop↔motor · margin · Path N · plate-box · ASSEMBLY_READY · version bump · UI.

## Next

```text
CLOSED — plate-box still await §0.1 bag · Path N HOLD
```
