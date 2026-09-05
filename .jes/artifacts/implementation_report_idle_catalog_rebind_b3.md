# Implementation Report — IDLE catalog rebind B3

**Project:** Jarvis  
**Date:** 2026-09-04  
**Implementer:** Cursor (Engineer-approved)  
**IC:** [implementation_contract_idle_catalog_rebind_b3.md](implementation_contract_idle_catalog_rebind_b3.md)  
**Parent:** B2 CLOSED suite 2250 · field smoke ACCEPT

---

## Files changed

- `src/jarvis/core/catalog_rebind_assist.py` (**new**) — `resolve_idle_catalog_rebind` + `is_frame_rebind_phrase` wrapper. Pure-phrase gate (rejects trailing SKU payloads). Family nouns: frame/chasis, motor(es), helice(s)/propeller(s), bateria(s)/battery.
- `src/jarvis/core/frame_catalog_assist.py` — re-exports `is_frame_rebind_phrase` from shared module (B2 API preserved).
- `src/jarvis/core/orchestrator.py` — IDLE dispatch generalized: resolve key → offer matching `_offer_component_*_catalog`. Gates: `_next_pending_block is None` **and** target component present / not stub (no steal of FN-009/FN-014 first acquisition).
- `tests/test_idle_catalog_rebind_b3.py` (**new**) — resolver + IDLE dispatch + battery pick + mid-arch gate + B2 regression.
- B2 tests unchanged and still green.

## Behavior

When architecture has no pending block and the named component already exists:

| Phrase | Opens |
|---|---|
| `cambiar motores` / `ayúdame a elegir motor` | motor catalog |
| `cambiar hélice` / `ayúdame a elegir hélice` | propeller catalog |
| `cambiar batería` / `ayúdame a elegir batería` | battery catalog |
| `cambiar frame` (B2) | frame catalog |

Does **not** fire for: bare `ayúdame a elegir`; `definir bateria lipo_…` (SKU residual); mid-architecture pending block; absent/stub component; terrestrial first-time `definir motores` without motors component.

## Tests executed

- Targeted rebind + FN-014 + assisted + polish: **113 passed**
- Full suite: see review / command output

## Residual

- Name→SKU still out  
- ESC / FC / sensors — no catalog rebind  
- Free-text frame orphan half (G-N4) unchanged  
