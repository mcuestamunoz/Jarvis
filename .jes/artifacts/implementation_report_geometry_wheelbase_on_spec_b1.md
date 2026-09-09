# Implementation Report — Mapping rung 2 first cut: wheelbase on the bound frame spec B1

**Date:** 2026-09-09  
**Implementer:** Cursor  
**IC:** [implementation_contract_geometry_wheelbase_on_spec_b1.md](implementation_contract_geometry_wheelbase_on_spec_b1.md)  
**Baseline:** package `0.3.8` · suite **2462** · `ca7a290`

---

## Files changed

- `tests/test_geometry_wheelbase_on_spec_b1.py` — **new**, T1–T4.
- `src/` `ui/` — **empty diff**, as locked.
- Live demo `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` — Continuity-equivalent `refresh_component_from_catalog(..., "frame")` (gitignored; smoke). Diff: `wheelbase_mm` None→230, `configuration` None→`quad_x`. 14 components unchanged.

---

## Behavior changed

None in product code. The bound frame **path** already projected seed wheelbase; this Buy **locks** stale-refresh + projector honesty and **applies** it to the live demo.

Stale projector still cannot invent 230. After refresh, card fields include `wheelbase_mm` `230 mm`. Frame still has **no** `geometry` (not L×W×H).

---

## Tests

Executed: `python -m pytest -q tests/test_geometry_wheelbase_on_spec_b1.py` → **4 passed**.  
Full suite: `python -m pytest -q` → **2466 passed** (2462 + 4).  
UI: still **34** (untouched).

---

## Not done (locked out)

No binder fork · no auto-refresh · no library overlay in the projector · no 4-motor copies · no Scene3D glyph · no version bump · fit still QUEUED.

---

## Risks

Refresh also writes `configuration` — honest, tested. Live `motor_count` in parameters remains 3; not this Buy.
