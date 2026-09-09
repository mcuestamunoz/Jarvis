# Implementation Review — Propeller cited seeds B2 (`dal_7040` + `apc_10x6_ep`)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_propeller_cited_seeds_b2.md](implementation_contract_geometry_propeller_cited_seeds_b2.md)  
**Report:** [implementation_report_geometry_propeller_cited_seeds_b2.md](implementation_report_geometry_propeller_cited_seeds_b2.md)  
**Buy:** Engineer ★ `procede` — Cyclone + 10×6EP

## Verdict

**PASS WITH NOTES**

Two cited rows. `apc_10x4_5` untouched. Disk 7″/10″ from `diameter_in`. Schema/bind unused this cycle (parent B0+B1). Fit QUEUED. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| `dal_7040` Cyclone bag 5.7 g / 2 palas / hub 5/7 / Pure PC | **Pass** — T1/T2 |
| No `shaft_bore_mm` on DAL | **Pass** |
| New `apc_10x6_ep` 10×6 / 20.1 g / hub 20.3/9.9 / bore 6.35 | **Pass** — T3/T4 |
| `apc_10x4_5` pitch 4.5, no mass | **Pass** |
| Disk 254 and ≈177.8 | **Pass** — T5/T6 |
| `gf_5045x3` unchanged | **Pass** — T7 |
| 18 rows | **Pass** — T8 |
| T9 census `{gf_5045x3, dal_7040, apc_10x6_ep}` | **Pass** |
| No new PropellerSpec keys | **Pass** |
| POPO / CW in `source_note` | **Pass** |
| Suite **2497** | **Pass** — Cursor re-ran |
| Version `0.3.8` | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| 18 propellers; three `mass_g` | **Confirmed** |
| Bind EP `shaft_bore_mm` 6.35 mm | **Confirmed** |
| Bind DAL properties omit `source_note` | **Confirmed** |
| T1–T8 + T9 | **17 passed** |
| Full pytest | **2497 passed** this review |
| `apc_8x4_5` / T-Motor / HBN not given this bag | **Confirmed** JSON |

---

## Notes

### N1 — GetFPV 403 vs `source_url`

Implementer could not read GetFPV (Cloudflare). `source_url` still those listings. Bag matches Engineer GetFPV quotes (this thread) and, for EP, APC.com + another retailer, disclosed in `source_note`. IC STOP is **contradiction**, not 403. Not a reopen. Smoke: you can open the two URLs in a browser.

`identity_status: verified` is fair for the **numbers**; it is not “we parsed GetFPV HTML this run.” Honest enough with the note.

### N2 — Material wording on EP

Seeded `Composite plastic`. GetFPV “More Information” also said Nylon Long Fiber Composite. Same family; not a dim clash. Optional later quote tidy.

### N3 — Live demo

Still HBN 5″ until you bind Cyclone or EP. §6 optional.

---

## Phase

Implementation **REVIEWED PASS WITH NOTES**. Engineer smoke next ([§6](implementation_contract_geometry_propeller_cited_seeds_b2.md)). Plate L×W later ★. Fit QUEUED. Package `0.3.8` · suite **2497**.
