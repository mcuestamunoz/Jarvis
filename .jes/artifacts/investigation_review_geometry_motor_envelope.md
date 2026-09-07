# Investigation Review — Motor Declared Envelope (Geometry axis)

**Date:** 2026-09-06  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_motor_envelope.md](investigation_contract_geometry_motor_envelope.md)  
**Report:** [investigation_report_geometry_motor_envelope.md](investigation_report_geometry_motor_envelope.md)  
**Parents:** Geometry axis lock · Battery B1 PASS @ **2316** · Board smoke ACCEPT

## Verdict

**PASS WITH NOTES**

Governing question answered. Rejecting overall axial `height_mm`/`Body Length` as one field is the load-bearing judgment — and it is correct. Default lean **B1 — Motor stator + overall diameter (+ shaft when sourced), representar only** is Buy-ready after Notes land in any IC.

Engineer ★ still required before IC / code.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present; contract questions covered | **Pass** |
| As-is + bind-path analysis | **Pass** |
| Field bag accept/reject with evidence | **Pass** — height rejected on substance |
| Seedable SKUs + live quotes | **Pass** (Cursor re-fetched both pages) |
| Honesty / ladder (`representar` only) | **Pass** |
| One default lean | **Pass** — **B1** |
| No `src/` this investigation | **Pass** (per investigator) |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `MotorSpec` has no geometry fields | **Confirmed** — `library.py:36-66` |
| Sourced rows = `emax_rs2205s_2300`, `sunnysky_r2205_2500` only | **Confirmed** |
| `emax_rs2205_2300` ≠ `emax_rs2205s_2300` (unsourced sibling) | **Confirmed** — live Board project uses the **unsourced** SKU |
| `bind_motor_from_catalog(MotorSuggestion)` — no library lookup | **Confirmed** — `catalog_bind.py:24-79` |
| `MotorSuggestion` TypedDict keys | **Confirmed** — `motor_catalog_assist.py:14-23` |
| EMAX page: stator 22/5, shaft 3, motor Ø 27.9, height 31.7, 15mm extended prop shaft | **Confirmed** — shop.emaxmodel.com |
| SunnySky page: stator 22, rotor Ø 27.4, stator thickness 5, body length 18; no shaft | **Confirmed** — sunnyskyusa.com |
| Board `_fields` generic | **Confirmed** — same path as Battery B1 |

---

## Agreement with report core

1. **Do not copy Battery L×W×H / overall height onto motors** — EMAX 31.7 vs SunnySky 18 is a convention clash (shaft-inclusive vs body), not noise. Same honesty class as rejecting closed plate-role taxonomy.
2. **Minimum bag** — `stator_diameter_mm`, `stator_height_mm`, `diameter_mm`, optional `shaft_diameter_mm` — coherent cylinder object without pretending a complete axial envelope.
3. **Bind path** — add optional `library` + `get_motor(sku)` inside `bind_motor_from_catalog`; do **not** widen `MotorSuggestion`. Correct.
4. **B2 Motor+ESC rejected** — ESC is box-shaped; separate Buy. Cursor concurs.
5. **Ladder** — stays at `representar`.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — Motor catalog count wording

Report says “20” motors; live `_datos.json` has **22** rows. Still **2 sourced**. Non-blocking — IC should say “2 of N” with N from file at implement time.

### N2 — Live project SKU will not light up dims after B1 alone

Board smoke project binds **`emax_rs2205_2300`** (no `source_url`). Seeded dims land on **`emax_rs2205s_2300`**. IC / smoke must either:

- rebind to the sourced `…s_2300` SKU for Board ACCEPT, or  
- explicitly document that the current card stays undimensioned until rebind / future sourcing of the non-S row.

Do **not** invent dims onto `emax_rs2205_2300` because the name looks similar.

### N3 — `diameter_mm` label honesty

EMAX “Motor Diameter” vs SunnySky “Rotor Diameter” — accept as overall radial envelope **only** with per-row `source_note` quote (report already requires this). IC must lock that wording.

### N4 — Bind when SKU missing from library

Report flags `KeyError` vs trust ranking. IC lean: **defensive** — if `get_motor(sku)` fails, project suggestion fields only (today’s behavior); never invent dims. Ranking already guarantees real keys in normal UX, but tests/callers can pass odd dicts.

### N5 — Overall axial height stays debt

Not an oversight. Future Buy only with an explicit convention (e.g. `body_height_mm` vs `overall_height_mm_incl_shaft`) backed by sources — not a silent `height_mm`.

---

## Buy recorded (awaiting Engineer ★)

| Option | Cursor stance |
|---|---|
| B0 | Optional vocab lock; not required — evidence enough |
| **B1 Motor envelope** | **Recommended** — after N2–N4 in IC |
| B2 +ESC | Later, separate |
| B3 glyph | Not now |
| Defer | Rejected |

**Suggested IC title:** *Motor declared envelope (stator + overall diameter + shaft) — representar only.*

---

## What Engineer decides next

1. ★ **Buy B1** → Cursor writes IC → Claude implements  
2. ★ **B0** first — Cursor does not recommend  
3. **Defer / re-scope**  

No code until ★.
