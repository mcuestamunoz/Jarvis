# Investigation Review — ESC XRotor Variant Coherence (PN ↔ dims ↔ mass)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_catalog_esc_variant_coherence.md](investigation_contract_catalog_esc_variant_coherence.md)  
**Report:** [investigation_report_catalog_esc_variant_coherence.md](investigation_report_catalog_esc_variant_coherence.md)  
**Parents:** ESC Geometry B1 @ **2327** · Glyphs B1 @ **2344**

## Verdict

**PASS WITH NOTES**

Governing question answered. The row is **one** coherent physical variant (International Version B / `30901001` / 50×21.6×12) with a **single-field** defect: `mass_g: 26` matches **no** official variant. Default lean **B1 — correct mass 26→15, rewrite `source_note`, update four test pins** is Buy-ready.

Engineer ★ still required before IC / code. **No pose. No Here3/Pixhawk. No motor thrust.**

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present | **Pass** |
| Live variant table + seed delta | **Pass** |
| Provenance of 26 (or unknown) | **Pass** — unknown, diligence honest |
| H1–H3 + reject H3 | **Pass** |
| One default lean | **Pass** — **B1** |
| Out-of-scope held (pose / FC / thrust) | **Pass** |
| No `src/`/seed/test edits this investigation | **Pass** (report-only; Cursor verified working tree) |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Live Hobbywing table: Int’l B `30901001` = 50.0×21.6×12.0 mm / **15 g** / no output wires | **Confirmed** — `https://www.hobbywing.com/en/products/xrotor-40a122` (this review) |
| Version A = 42.0×21.6×12.0 / 18.5 g / wires | **Confirmed** |
| Seed PN + dims match Version B | **Confirmed** — `library/esc/_datos.json` |
| Seed `mass_g: 26` | **Confirmed** |
| 26 ≠ 15, 18.5, or average | **Confirmed** |
| Exactly **4** test assertions pin `26.0` in `test_catalog_foundation_v1.py` | **Confirmed** (lines 399, 417, 455, 469) |
| `test_esc_mass_unchanged_by_geometry_addition` is N2 debt lock | **Confirmed** — name/docstring become stale under B1 |
| `_geometry_from_spec` never reads `mass_g` | **Confirmed** — only L/W/H and diameter paths |
| No other production pin of ESC mass 26 | **Confirmed** (seed + those four asserts) |

---

## Agreement with report core

1. **Not a split-identity problem** — correct; H3 rejected for this Buy.
2. **H1 mass-only** — correct; smallest defensible fix.
3. **Glyph untouched** — correct.
4. **Thrust / Here3 / Pixhawk out** — correct; cola 2 remains formalized, not opened.
5. **B0 insufficient** — agree; known-wrong number must not stay live.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — Seed correction (locked numbers)

| Field | After B1 |
|---|---|
| `part_number` | **unchanged** `30901001` |
| `length_mm` / `width_mm` / `height_mm` | **unchanged** 50.0 / 21.6 / 12.0 |
| `mass_g` | **15** (not 26) |

`source_note` must: (a) quote manufacturer **15 g** for this PN; (b) state that prior **26 g** had **no** cited primary provenance and was corrected; (c) drop the “flagged as debt / left unchanged” Geometry-B1 framing; (d) keep `www.` URL citation.

### N2 — Test rename required

`test_esc_mass_unchanged_by_geometry_addition` must be **renamed + re-docstringed** (premise was “leave debt untouched”). Suggested intent: mass matches page for PN; dims remain independent / still present. Do **not** weaken coverage — retarget assertions to **15.0**.

### N3 — Four assert sites (exhaustive list)

Same file as report §G — IC done-criteria must list all four. No silent leftover `26.0` for this SKU.

### N4 — Live projects / rebind honesty

Changing the seed updates **new** binds and library reads. Projects that already persisted `properties.mass_g = 26` from an earlier bind keep the stale value until **rebind** (or equivalent writer refresh). IC / smoke must say this explicitly — Board text can still show 26 g on old cards without implying the seed fix failed.

### N5 — Non-goals (carry forward)

No glyph/UI change · no pose/`mounted_on` · no Version-A second SKU · no Here3/Pixhawk · no motor `thrust_n` · no version bump · no Continuity ESC picker · no electrical-rating edits unless a live conflict appears (none found).

---

## Disagreements

**None** on substance. Minor: report’s suggested IC title is fine; Cursor may shorten to *ESC mass hygiene B1 (`hobbywing_xrotor_40a_6s` 26→15)*.

---

## Buy recommendation (for Engineer ★)

| Option | Cursor stance |
|---|---|
| B0 doc-only | Reject — wrong number stays live |
| **B1 mass 26→15 + note + tests** | **Recommend ★** — **★ RATIFIED 2026-09-07 (`procede`)** → [IC](implementation_contract_catalog_esc_mass_hygiene_b1.md) |
| B2 split / rematch PN | Reject for this Buy |
| Defer | Reject — value known and cited |

**Default:** ★ **Buy B1** → Cursor writes IC → Claude implements → Cursor reviews.

**After this closes:** cola 2 remains — open `catalog_motor_thrust_not_intrinsic` investigation (or Engineer ★ parallel) — **not** part of this Buy.
