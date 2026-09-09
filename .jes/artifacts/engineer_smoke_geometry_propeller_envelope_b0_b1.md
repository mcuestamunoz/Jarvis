# Engineer smoke — Propeller B0+B1 (2026-09-09)

**Project:** `autonomía-de-10min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_propeller_envelope_b0_b1.md) · [review](implementation_review_geometry_propeller_envelope_b0_b1.md) PASS WITH NOTES @ suite **2489**

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Card `propellers` | SKU `gemfan_5045_hbn`; `diameter_in` 5 in; `pitch_in` 4.5 in; **no** `mass_g` / hub / `blade_count` | **PASS** |
| 2 | Glyph | disk **Ø 127 mm** | **PASS** |
| 3 | Bind relation | `montado en` `motors` | **PASS** (unchanged) |

Live card is HBN, not `gf_5045x3` — bag B1 is catalog-only until rebind. Empty grams/hub on this SKU is locked ACCEPT (Oscar Liang ≠ ficha física).

Optional `gf_5045x3` refresh not required for this ACCEPT.
