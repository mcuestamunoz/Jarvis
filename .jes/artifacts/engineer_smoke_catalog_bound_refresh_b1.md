# Engineer smoke — Catalog-bound refresh B1 ESC (2026-09-08)

**Status:** ACCEPT  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Surface:** `jarvis --chat` + `jarvis board` (`http://127.0.0.1:5173/`)  
**Parents:** [IC](implementation_contract_catalog_bound_refresh_b1.md) · [review](implementation_review_catalog_bound_refresh_b1.md) PASS WITH NOTES @ suite **2406**

## Walk

| Step | Result |
|---|---|
| Open project `1` / `autonomía-de-10min` | IDLE Continuity |
| `actualiza el esc desde catálogo` | `Actualizado desde catálogo (hobbywing_xrotor_40a_6s): mass_g 26.0 → 15.0. Montaje declarado sin cambios.` |
| Repeat same phrase | `Ya coincidía con el catálogo (hobbywing_xrotor_40a_6s) — sin cambios. Montaje declarado sin cambios.` |
| Board hard-refresh | card `esc` **15 g** · `montado en` `frame_plate` · edge to plate |

No picker. No LLM. No “corregido / verificado / cabe”.

## Verdict

**ACCEPT.** Demo ESC is no longer catalog-stale. Refresh B1 closable.

## Next

Idle. Optional Conn Continuity walk (hélices/sensores) remains demo-only. Fit frozen.
