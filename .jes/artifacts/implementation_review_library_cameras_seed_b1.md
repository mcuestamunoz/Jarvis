# Implementation Review — First `library/cameras` seed (`B1-library-cameras-seed`)

**Date:** 2026-09-18  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_library_cameras_seed_b1.md) · [report](implementation_report_library_cameras_seed_b1.md)  
**Verdict:** **PASS WITH NOTES**

---

## Locks

| # | Lock | Result |
|---|---|---|
| 1–3 | Buy; `library/cameras/_datos.json`; only `runcam_phoenix_2` | **Pass** — cite row matches §0.1 |
| 4–6 | CameraSpec + family + ESC-shaped bind + omit-key | **Pass** |
| 7–8 | Pick = bind; mass mirror on apply + refresh writer | **Pass** — §0.2 fork followed |
| 9–12 | Assist + orchestrator + rebind + refresh **this Buy** | **Pass** — not deferred |
| 13–14 | Free-text medium; `base=` preserves mount/pose | **Pass** — T3 / E4 |
| 15 | USER_GUIDE | **Pass** — Claude patched; Cursor added §3.2bis Phoenix smoke block |
| 16–17 | Forbidden; tests-only | **Pass** — `0.4.1`; no workspace mutate |

## Tests

| ID | Result |
|---|---|
| T1–T8, E1–E6 + refresh unit | **23** tests in `test_library_cameras_seed_b1.py` |
| Cursor re-run | **23 passed** |
| T8 / suite | Report **3100** passed, 1 skipped · UI **105** · package **0.4.1** |

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Soft / named debt | `power_w` from cite mA stays in `source_note` only — M3. |
| **N2** | Soft | Single SKU (expected first cut). |
| **N3** | Process | Engineer may smoke **this Buy §3** and **M2** in one vigil session. M2 still SMOKE until ACCEPT. |
| **N4** | Info / good | Mass mirror on refresh lives in `refresh_component_from_catalog` for `_MISSION_MASS_KEYS` — hard to forget at call sites. |

## Out of scope confirmed

M2 Continuity ownership · M3 power · multi-SKU · VTX · Path D vigilancia migrate · version bump.

## Smoke (Engineer 2026-09-18 · vigilancia)

**ACCEPT WITH NOTES**

| Step | Result |
|---|---|
| `ayúdame a elegir cámara` → pick 1 | List shows 19³ + 9 g; bind → `runcam_phoenix_2` **high** |
| `cambiar cámara` / `cambia la cámara` | Reopens list |
| `estado` | Continuity still on mount CTA (correct — mounts separate) |
| `actualiza la cámara` | **Not exercised** in transcript |
| Display | `runcam_phoenix_2 (SKU sin resolver)` despite **high** — `project_closure` `sku_resolved` lacks `has_camera` (display-only soft debt) |
| Pick text `RunCam` | Bound Phoenix 2 (single-SKU prefix match) — OK for 1 SKU; watch when more land |

## Next

```text
CLOSED — soft follow-on: wire cameras into sku_resolved (display)
Cola → M3 power_w or M6/M7
```
