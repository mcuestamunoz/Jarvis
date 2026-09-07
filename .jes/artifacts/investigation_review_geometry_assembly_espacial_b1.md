# Investigation Review — Geometry Assembly Espacial B1 (minimum pose / `mounted_on`)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_assembly_espacial_b1.md](investigation_contract_geometry_assembly_espacial_b1.md)  
**Report:** [investigation_report_geometry_assembly_espacial_b1.md](investigation_report_geometry_assembly_espacial_b1.md)  
**Parents:** Progression Lock · Glyphs CLOSED @ **2344** · Hygiene CLOSED @ **2350** · Structure parts graph

## Verdict

**PASS WITH NOTES**

Governing questions answered. Clean zero assembly-spatial state; **diverge** from `parent_key`; Board layout already quarantined; no catalog mount sources → **numeric pose (B1+) correctly rejected**. Default lean **B1 — relation-only `mounted_on`** is Buy-ready.

Engineer ★ still required before IC / code.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present | **Pass** |
| As-is inventory (schema / Structure / Board / glyphs) | **Pass** |
| Reuse vs diverge `parent_key` | **Pass** — diverge |
| Field bag + source rules | **Pass** — `mounted_on` only |
| Honesty / ladder matrix | **Pass** |
| Buy options + default lean | **Pass** — **B1** |
| No `src/`/`tests/` this investigation | **Pass** (per investigator) |
| Fit / layout-as-truth / CAD out | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `ComponentSpec.parent_key` only relational field | **Confirmed** (`action_schema.py`) |
| Writers set `parent_key="frame"` only | **Confirmed** (`component_writers` / `catalog_bind`) |
| BOM peer-exclusion on any non-`None` `parent_key` | **Confirmed** (`project_closure.py`) |
| Board lane/`kind: part` via `parent_key` | **Confirmed** (`spatial_board.py`) |
| `clear_frame_part_children` removes `parent_key == "frame"` only | **Confirmed** — see **N1** |
| `_fields()` only walks `properties` + SKU — not bare ComponentSpec attrs | **Confirmed** — see **N2** |
| No `mounted_on`/pose in production schema | **Confirmed** |
| Glyphs envelope-only, no shared origin | **Confirmed** |

---

## Agreement with report core

1. **Zero assembly state today** — correct.
2. **Diverge: new `mounted_on`, leave `parent_key` alone** — correct and load-bearing (BOM + Board).
3. **B1 relation-only; defer B1+ pose** — correct (no source, no reference frame).
4. **Never infer from Board proximity / BOM co-membership** — correct.
5. **Board layout ≠ SoT already** — correct; must stay that way in any IC.
6. **B2 edges later** — agree; text field first.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — `clear_frame_part_children` nuance

Report §C slightly overstates: removal is **`parent_key == "frame"` only**, not every non-`None` `parent_key`. BOM peer-exclusion and Board lane grouping **still** make reuse unsafe. IC must **not** overload `parent_key`; diverge stands.

### N2 — Board text is not free via `_fields()`

`_fields()` emits only `spec.properties` (+ SKU). A bare `ComponentSpec.mounted_on` **will not** appear on the card unless `spatial_board.py` (or equivalent) **explicitly** appends a field (e.g. `"montado en"`). IC must list that projector one-liner as in-scope for B1 if “Board shows the relation” is part of the Buy — still zero geometry math, but not automatic.

### N3 — Provenance shape

Report correctly leaves IC to choose: bare `str | None` vs provenance wrapper. **Lean for IC:** bare optional string + writer always treats it as declared (ComponentSpec already has `source: declared|inferred` at spec level — do **not** invent a second PropertyValue unless needed). Document “never inferred” in writer docstring / validation.

### N4 — Validation floor

Target key must exist in `components` at write time (or render honest absence). Exact reject-vs-badge = IC choice; prefer **writer-time reject** for dangling refs (simpler, matches “don’t invent”).

### N5 — Non-goals (carry forward)

No pose mm/orientation · no fit · no edge drawing (B2) · no layout-as-truth · no catalog mount invention · no hygiene reopen · no version bump.

---

## Disagreements

**None** on Buy direction. N1–N2 are precision for the IC, not rejects.

---

## Buy recommendation (for Engineer ★)

| Option | Cursor stance |
|---|---|
| B0 defer | Valid only if sequencing elsewhere |
| **B1 `mounted_on` relation-only + Board text field** | **Recommend ★** |
| B1+ numeric pose | Reject this cycle |
| B2 edges | Follow-on after B1 |

**Default:** ★ **Buy B1** — **★ RATIFIED 2026-09-07 (`escribe IC`)** → [IC](implementation_contract_geometry_assembly_espacial_b1.md) → Claude implements → Cursor reviews.
