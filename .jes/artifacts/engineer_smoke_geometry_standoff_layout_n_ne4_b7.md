# Engineer smoke — Standoff visor layout N≠4 B7

**Date:** 2026-09-10  
**IC / Review:** [IC](implementation_contract_geometry_standoff_layout_n_ne4_b7.md) · [review](implementation_review_geometry_standoff_layout_n_ne4_b7.md)  
**Project:** `autonomía-de-5min` · Main Plate + standoff boxes  
**Verdict:** **ACCEPT**

---

## Smoke

| # | Check | Result |
|---|---|---|
| 1 | IDLE `6 standoffs` → 6 posts on Main Plate perimeter | **PASS** — Engineer Board walk; card `count: 6` |
| 2 | `8 standoffs` → 8 posts | Walked / accepted with Option A |
| 3 | `4 standoffs` → corners only | Walked / accepted |
| 4 | `3 standoffs` → **no** copies (omit) | **PASS** — honesty; not a fake trio |
| 5 | Motors/props X unchanged | **PASS** |

**Note:** `count=3` correctly omits `solidCopies` (fail closed). A single orphan box/pose may remain; that is not “3 posts.”

---

## Also closes

IDLE frame-part count declare B1 smoke — count reaches the card without LLM (prerequisite for this walk).
