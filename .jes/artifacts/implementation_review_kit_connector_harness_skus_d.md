# Implementation Review — Kit SKUs D B1 (XT60 / JST-SH into existing holes)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_kit_connector_harness_skus_d.md](implementation_contract_kit_connector_harness_skus_d.md)  
**Report:** [implementation_report_kit_connector_harness_skus_d.md](implementation_report_kit_connector_harness_skus_d.md)

## Verdict

**PASS WITH NOTES**

One `kit_hardware` family, two cited rows, bind + kit single-key `"ayúdame a elegir"`. Free-text `XT60` still saves without `catalog_ref`. No geometry, no `current_a`, no `BLOCK_TO` / `KIT_TO` new keys, no adapter SKU, no N2, package still `0.3.8`. Suite **2532** re-ran here (2523 + 9). Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| Family Literal `+ kit_hardware` only | **Pass** |
| Seed exactly two rows; frozen `kit_key` pair | **Pass** |
| Loader `ValueError` on unknown `kit_key` (not silent drop) | **Pass** — code; see N2 |
| `KitHardwareSpec` has no geometry fields | **Pass** — T0 `hasattr`; `cable_length_options_mm` catalog-only |
| No `current_a` / mass / box on seed or bind | **Pass** — T1 |
| Bind harness does not copy cable mm → `length_mm` | **Pass** — T2 |
| `_geometry_from_spec` is `None` | **Pass** — T3 |
| `_bom_sku_resolved` `family==kit_hardware` | **Pass** — T4 |
| Help-choose lists connector SKU only | **Pass** — T5; no `CAB1009` |
| Pick `#1` sets `catalog_ref`; slot gone; propulsion `complete` | **Pass** — T6 |
| Free-text `XT60` → `catalog_ref is None` | **Pass** — T7 |
| Robot IDLE kit wizard does not open | **Pass** — T8 dispatch; see N1 |
| Gate: `expected_keys[0] in {power_connector, signal_harness}` (not `"esc" in`) | **Pass** |
| Gate after adapter skip, before infer | **Pass** |
| Peer lists: four offers clear `kit_hardware_suggestions`; kit offer clears the four | **Pass** |
| `COMPONENT_PROMPTS` keep free-text examples; optional help-choose clause | **Pass** |
| `ParamDefinitionSession` / composite Phase A untouched | **Pass** |
| `BLOCK_TO_COMPONENTS` / `KIT_TO_COMPONENTS` values unchanged | **Pass** — `git diff` empty on `system_architecture_catalog.py` |
| `engineering_readiness.py` / `project_continuity.py` / `ui/` empty | **Pass** |
| No `prop_adapter` catalog row | **Pass** — T0 names |
| Version `0.3.8` | **Pass** |
| Suite **2532** | **Pass** — Cursor re-ran full pytest |
| Existing tests not weakened | **Pass** — report: zero pre-existing assertions edited |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Seed fields match IC §3.2 | **Confirmed** `library/kit_hardware/_datos.json` |
| Pololu 60 A only in `source_note`, not `current_a` | **Confirmed** |
| Pi Hut `cable_length_options_mm: [100, 300]` not a box axis | **Confirmed** |
| Bind projects pin/color/pitch/AWG only | **Confirmed** — no `part_number` on `ComponentSpec` (IC “e.g.”; N5) |
| `CatalogRef(family="kit_hardware")` | **Confirmed** |
| Writer = existing `set_control_component` | **Confirmed** |
| Assist: no ranking; filter by `kit_key` | **Confirmed** |
| Suggestions not in `_PERSISTED_SESSION_FIELDS` | **Confirmed** |
| `pyproject.toml` still `0.3.8` | **Confirmed** |

---

## Notes

### N1 — T8 is the IDLE dispatch, not `handle_user_text`

IC asked the robot wizard not to open **and** not to show help-choose. Claude asserts `_try_start_kit_component_from_mention("declara el conector") is None` because the phrase falls through to the LLM on a robot project (pre-existing routing, same pattern as kit B1-min T11). That is enough: help-choose only runs inside `_handle_component_description` after a kit single-key wizard is already open. Do not “strengthen” T8 by stubbing a fake kit wizard on `robot`.

### N2 — Loader reject is untested

`_kit_hardware_from_raw` raises `ValueError` for `kit_key` outside the frozen pair (Cursor ran it: `vtx` rejected). T0 does not cover that branch. Not a reopen.

### N3 — Manufacturer `Pololu` vs page brand Generic

IC locked `manufacturer: Pololu` as seller. The live page brand string is Generic; that honesty was already in the investigation review. Seed follows the IC, not a silent current invent. Smoke: list line will say “Pololu XT60…”, not Generic.

### N4 — PASS twin is propulsion-complete after pick

IC §3.7 asked `_block_progress_status` equal with vs without `catalog_ref` on the kit key. T6 asserts propulsion still `complete` after the pick. Kit keys are not in `BLOCK_TO`, so a `catalog_ref` on `power_connector` cannot change that status. Explicit clone twin not required.

### N5 — `part_number` stays on the catalog row / suggestion line

Bind does not copy `part_number` onto `ComponentSpec.properties`. The list line still shows `PN 2175` / `PN CAB1009`. Allowed.

### N6 — Empty-catalog fallback mentions `XT60`

If a `kit_key` ever had zero rows, the assist string still uses `'XT60'` as the free-text example (including the harness hole). Dead path with the 1+1 seed.

---

## Phase

Implementation **CLOSED**. Engineer smoke: [engineer_smoke_kit_connector_harness_skus_d.md](engineer_smoke_kit_connector_harness_skus_d.md) **ACCEPT** (`autonomía-de-5min`: free-text `XT60` + harness `#1` CAB1009; connector catalog pick already on the project). Package `0.3.8` · suite **2532**.

Walk:

1. 4/4 dron (or `autonomía-de-10min`) → `definir conector` → `ayúdame a elegir` → list includes Pololu XT60 → `#1` → `catalog_ref` / BOM SKU.
2. Same hole, type `XT60` without pick — still saves.
3. `estado` / Board: no new solid for the connector.
4. Hover numbers unchanged.

Do **not**: append kit keys to `BLOCK_TO`; scrape GetFPV; project cable mm onto `length_mm`; seed `current_a`; open N2; add a `prop_adapter` SKU.
