# Investigation Review — Kit SKUs D (XT60 / harness)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_kit_connector_harness_skus_d.md](investigation_contract_kit_connector_harness_skus_d.md)  
**Report:** [investigation_report_kit_connector_harness_skus_d.md](investigation_report_kit_connector_harness_skus_d.md)  
**Parents:** [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md) · kit B1-min CLOSED · adapter B1 REVIEWED @ **2523**

## Verdict

**PASS WITH NOTES** · recommended Buy **B1** (two cited rows + `CatalogRef` + bind + kit single-key help-choose). Claude’s **B2** (bind-only, ESC-shaped) is a valid *schema* cut but does **not** let a novice bind a named SKU in the CLI — the hole already closes with free-text `XT60`. B2 would land identity that nothing in the product reaches.

B-naive refused. One family `kit_hardware` + `kit_key` (not two MotorSpec-sized families) is the right size. No IC until Engineer ★ **B1** (or explicit **B2** / **B0**).

---

## Checklist

| Criterion | Result |
|---|---|
| Zero connector folders today | **Pass** — `library/` still 6 `_datos.json` (no `kit_hardware`) |
| `CatalogRef.family` five Literals | **Pass** — `motor`/`battery`/`propeller`/`esc`/`frame` |
| Kit UX without catalog; ESC catalog without UX | **Pass** |
| One default named | **Pass** — Claude **B2**; Cursor overrides to **B1** (N1) |
| ≤1 row per key, page-cited | **Pass** — Pololu #2175; Pi Hut CAB1009 (Cursor re-fetched) |
| No mass / no L×W×H invented | **Pass** |
| B-naive refused | **Pass** |
| No `src/` / seed this report | **Pass** — report-only; other Buys already committed |
| `prop_adapter` SKUs / N2 / scrape / `BLOCK_TO` out | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Live demo free-text, `catalog_ref: None` | **Plausible** — `/workspace/` gitignored; matches kit B1-min smoke (`XT60` + `cable JST-SH 6 pines`) |
| No `_offer_component_esc_catalog` | **Confirmed** |
| `bind_esc_from_catalog` docstring: no CLI caller | **Confirmed** |
| `_wants_catalog_help` already true for free-text XT60 | **Confirmed** — `catalog_ref is None`; no kit branch calls it |
| Pololu 2175 | **Confirmed** — item 2175, yellow, 1×2, “60 A” in product copy (not the Dimensions table), no mass/box |
| Pi Hut CAB1009 | **Confirmed** — 6 pin, 1.0 mm, 26AWG, 100/300 mm, female–female; no mass. Length is 1-D cable, not a box |
| `_geometry_from_spec` reads L×W×H / Ø only | **Confirmed** — IC must not project cable `length` onto `length_mm` |

---

## Notes

### N1 — B2 does not change the novice product

Contract: smallest hook that still lets a **novice bind** a named SKU into the hole. B2 is ESC: tests/scripts can `bind_*`; CLI still only free-text. The BOM would keep saying the word `XT60` until a later picker. That is foundation, not D-as-asked.

B1 cost is one shared `_offer_kit_hardware_catalog(key)` on the **existing** kit single-key wizard (not energy/propulsion composite). Claude is right that this is not two clones. That is cheap enough to be the default IC.

★ **B2** only if Engineer wants CatalogRef+JSON first with **no** CLI pick this Buy.

### N2 — `kit_hardware` is not a parts dump

One Literal `"kit_hardware"` + row `kit_key ∈ {power_connector, signal_harness}` is accepted. IC must freeze that Literal to those two keys. No VTX/RX/adapter rows in the same seed.

### N3 — Pololu is XT60-class, not a drone pigtail

Generic pair, brand Generic. Honest identity for the hole. Do not claim it matches the bound battery’s connector.

### N4 — 60 A is description copy

Pololu specs table does not list current. Seed `current_a` only if the IC cites the page prose; otherwise omit (fail closed on silent specs table).

### N5 — Wire length ≠ box

Pi Hut 100/300 mm must not become `length_mm` for `_geometry_from_spec`. Bind projects electrical/identity fields only this Buy.

---

## Buys (after review)

| ID | Engineer ★ |
|---|---|
| **B1** | **Default** — seed 1+1 + widen `CatalogRef` + bind + kit help-choose |
| **B2** | Schema+seed+bind, no picker (ESC-shaped) |
| **B0** | Park. Free-text only |
| **B-naive** | **Forbidden** |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. Engineer ★ **B1** (2026-09-09). IC: [implementation_contract_kit_connector_harness_skus_d.md](implementation_contract_kit_connector_harness_skus_d.md). Package `0.3.8` · suite **2523** · commit `3600b37`.
