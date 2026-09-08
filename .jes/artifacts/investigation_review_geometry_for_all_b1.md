# Investigation Review — Geometry for All B1 (Fase 2 / G)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_for_all_b1.md](investigation_contract_geometry_for_all_b1.md)  
**Report:** [investigation_report_geometry_for_all_b1.md](investigation_report_geometry_for_all_b1.md)

## Verdict

**PASS WITH NOTES**

Evidence quality is high (live projector + live page re-fetch). Lean **B1** (narrow text enrichment) is Buy-eligible; **B0** (defer → Conn) is equally honest given zero new glyphs and tiny Board payoff. Engineer ★ picks B1 or B0 — **IC authored on ★ Buy B1** (see [implementation_contract_geometry_for_all_b1.md](implementation_contract_geometry_for_all_b1.md)).

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + B0 peer | **Pass** |
| Gap matrix vs live demo | **Pass** — Cursor reconfirmed 5 glyphs / 9 absent |
| Propeller disk live | **Pass** — Ø127.0 from `diameter_in=5` |
| Source table (plates/cage/standoff) | **Pass** — iFlight + TBS quotes reconfirmed live |
| B1+/B2 rejected | **Pass** |
| Here3 out / freeze | **Pass** |
| Contingency sketch + open questions | **Pass** |
| Conn/fit/pose/CAD out | **Pass** |
| No code | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Demo `project_spatial_nodes` → 5 glyphs | **Confirmed** (motors disk 27.9 · propellers disk 127.0 · esc/battery/FC boxes) |
| 9 without glyph | **Confirmed** (frame + 4 plates + arm + cage + standoff + sensors) |
| Seed lacks body/standoff height fields | **Confirmed** (`library/frames/_datos.json`) |
| iFlight page: Body 202×202 · standoffs 25/32 · mount 30.5/20 | **Confirmed** (fpv24 product page still lists them) |
| TBS 5in page: Standoff Height 30mm and 22mm | **Confirmed** (RaceDayQuads specs) |
| Plate L×W on Armattan / TBS 7in | **Not stated** — agrees with report |

---

## Notes for ★

### N1 — Choose B1 or B0 explicitly

| Pick | Consequence |
|---|---|
| **B1** | Cursor writes READY IC: seed + `FrameSpec` standoff height (list-capable) + project to `frame_standoff`; iFlight body L×W on **locked target key**; text-only; no glyph claim |
| **B0** | Close G as investigated/deferred; PRIORIDAD → Fase 3 **Conn** investigation or IC |

Do not ship a half-B1 that drops the second standoff length — report correctly flags scalar-vs-list.

### N2 — Footprint target key stays open until IC

Page says “Body dimensions” → lean **frame root** (`body_length_mm` / `body_width_mm`), not a plate sibling. Lock in IC if B1.

### N3 — Mount-hole patterns are pose-reversal evidence, not this Buy

30.5 / 20 patterns correctly flagged for deferred pose thread — do not fold into G IC.

### N4 — Demo project is Armattan

B1 enrichment helps **catalog rows** iFlight/TBS; the live demo (Armattan) gains **no** new standoff/body text until a different SKU is bound. Product honesty for smoke: do not expect Armattan Board cards to change after B1 alone.

---

## Agreement

1. Glyph-for-all is largely already done or honestly impossible without invention.  
2. Propeller gap closed — already live.  
3. B1+ “plate footprint family” correctly rejected.  
4. B2 new glyph correctly rejected.  
5. Dual lean B1≈B0 is correct engineering judgment, not waffling.

---

## Phase

Investigation **reviewable**. Awaiting Engineer ★ **B1** (IC next) or **B0** (Conn next). No implementation.
