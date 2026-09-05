# Implementation Review — Structure Catalog Foundation IC-1

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_structure_catalog_foundation_ic1.md](implementation_contract_structure_catalog_foundation_ic1.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic1.md](implementation_report_structure_catalog_foundation_ic1.md)  
**Baseline:** suite **2171** · reviewer targeted **44** catalog tests · full suite **2177**

## Verdict

**PASS WITH NOTES**

IC-1 matches the contract: schema + seed + library readers only. No bind,
BOM, Continuity, or product path. Frame catalog posture now matches ESC
(identity in library, unreached in production). **IC-1 CLOSED.**

IC-2 / IC-3 remain **Not Buy** unless Engineer reopens.

---

## IC checklist

| Criterion | Result |
|---|---|
| §2.1 `CatalogRef.family` += `"frame"` | **Pass** |
| §2.2 `FrameSpec` + get/has/list; required mass/class | **Pass** |
| §2.2 No wheelbase/arm_count/configuration | **Pass** |
| §2.3 Seed 2–6 SKUs, ≥2 classes, provenance | **Pass** — 4 SKUs, classes {5, 7} |
| §2.4 Doc deferred hygiene | **Pass** — status table + “bind still deferred” |
| Forbidden: bind/writers/BOM/Continuity | **Pass** — no `bind_frame`; forbidden product files not edited for this IC |
| Mandatory tests | **Pass** — 6 new + unknown-SKU extended |
| Full suite | **Pass** — reviewer **2177** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `CatalogRef(family="frame")` constructs | **Confirmed** |
| `get_frame` / `has_frame` / `list_frames` | **Confirmed** — 4 frames; phantom → KeyError/False |
| No `bind_frame_from_catalog` | **Confirmed** — repo grep |
| Material omitted when unsourced (TBS) | **Confirmed** — honest omit |
| Suite | **Confirmed** — `pytest -q` → **2177** |

---

## Notes

### N1 — Retailer vs OEM URLs

Three of four seed rows cite **retailer** product pages (RaceDayQuads,
ProgressiveRC, FPV24); one cites manufacturer domain (Armattan). Numbers are
disclosed and material omitted when unsourced — acceptable for IC-1 seed
honesty. Prefer OEM/datasheet URLs if rows are refreshed later (not blocking).

### N2 — Legacy deferred prose

`PHYSICAL_COMPONENT_CATALOG_V1.md` §6 historical deferred list may still
mention “frame SKU catalogs” in older narrative; §13 status table is the
authoritative IC-1 update. No doctrine rewrite required.

### N3 — CLI walk

**Not required.** Zero user-visible / claim-path change. Structure A free-text
remains the only live frame path; `catalog_bound` stays False in production.

---

## Slice / phase

| Item | Status |
|---|---|
| Catalog Foundation **IC-1** | **CLOSED** |
| IC-2 bind / IC-3 assist | **Not authorized** |
| Structure Foundations claim-copy | Already CLOSED |
| CAD / layout | Out |
