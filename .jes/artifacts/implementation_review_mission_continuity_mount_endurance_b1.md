# Implementation Review — Mission Continuity: mount + endurance (`B1-mission-continuity-mount-endurance`)

**Date:** 2026-09-18  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_mission_continuity_mount_endurance_b1.md) · [report](implementation_report_mission_continuity_mount_endurance_b1.md)  
**Verdict:** **PASS WITH NOTES**

---

## Locks

| # | Lock | Result |
|---|---|---|
| 1–2 | Buy; ladder after mass, before soft margin | **Pass** — identity → mass → mount → autonomy → soft margin |
| 3–4 | Widen mount subjects + checklist | **Pass** — shared `CAMERA_KEYWORDS`/`RADIO_KEYWORDS`; `_STACK_SUBJECTS` updated |
| 5–6 | Continuity mount CTAs; ambiguous plates never guessed | **Pass** — T4/T9; live vigilancia 3-plate path documented |
| 7–8 | Autonomy via shared `parsed_constraints` / `derive_parsed_constraints`; CTA | **Pass** — T5/T8; no second regex |
| 9–11 | Soft margin after target; neutral regression; guide | **Pass** — T6/T7; USER_GUIDE subsection |
| 12–13 | Forbidden; tests-only | **Pass** — `0.4.1`; no workspace mutate |

## Tests

| ID | Result |
|---|---|
| T1–T9 | Covered (9 tests) |
| Fixtures | 3 prior tests gained `parsed_constraints` — intent preserved |
| T10 | Report suite **3077**; Cursor re-ran mount-endurance + continuity-intent + mission-mass → **40 passed**; package **0.4.1** |

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Soft / pre-existing | English `"camera mounted on …"` still `NONE` (Spanish mount-verb gate in declare assist). IC allowed ES+EN **nouns**; verb grammar unchanged. Not a regression. |
| **N2** | Info / good | Live vigilancia (3 plates) exercises ambiguous Continuity CTA — stronger than synthetic-only. |
| **N3** | Process | ★ **`B1-library-cameras-seed`** (M1.5 Phoenix 2 full-path) was APPROVED earlier; this Buy (M2) landed instead. Cameras seed remains open — do not treat M2 as closing M1.5. |
| **N4** | Info | Smoke phrase for autonomy: report uses restrictions text that yields `autonomy_min` (e.g. `vuelo mínimo 8 min` / guide `restricciones:`). Engineer smoke §3 still required for CLOSED. |

## Out of scope confirmed

M3 `power_w` · M4 VTX · pose/plate invent · firmware · auto-mount on identity · version bump · UI.

## Smoke (Engineer 2026-09-18 · vigilancia)

**ACCEPT WITH NOTES**

| Step | Result |
|---|---|
| Open / `estado` | Ambiguous multi-plate CTA for **cámara** — lock #6 |
| `montajes estándar` | Lists FC + cameras + radio with keys |
| `cámara montada en frame_plate_2` | Wrote mount; CTA advanced to **radio** ambiguous |
| Radio mount | Skipped (CTA correct; not required for ACCEPT) |
| `restricciones: autonomía 8 minutos` | `autonomy_min=8.0` |
| `calcular` / `simular` | ~0.7 min vs 8 — honest WARN / `autonomy_below_restriction` · no fake validated flight |
| Soft margin only | Superseded by honest below-target (expected when target set) |

## Next

```text
CLOSED
Cola → M3 / M6 / M7
```
