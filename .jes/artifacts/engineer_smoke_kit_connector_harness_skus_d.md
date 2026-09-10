# Engineer smoke — Kit SKUs D B1 (2026-09-09)

**Project:** `autonomía-de-5min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_kit_connector_harness_skus_d.md) §6 · [review](implementation_review_kit_connector_harness_skus_d.md) PASS WITH NOTES @ suite **2532**

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Catalog pick (connector) | `ayúdame a elegir` → Pololu `#1` → SKU | **PASS** — already on this project before this walk (`pololu_xt60_pair`); T5/T6 cover the list/pick. This walk then overwrote with free text (row 2) |
| 2 | Free-text `XT60` | saves without `catalog_ref` | **PASS** — `definir conector` → `XT60` → `◇ power_connector: XT60 qty=1 (declarativo)` (no `[sku]`) |
| 3 | Harness help-choose | list is harness row only | **PASS** — `1. The Pi Hut JST-SH Cable - 6 Pin (PN CAB1009)`; no Pololu/XT60 in the list |
| 4 | Harness `#1` | `catalog_ref` / BOM SKU | **PASS** — `◇ signal_harness: pihut_jst_sh_6pin_cab1009 [pihut_jst_sh_6pin_cab1009]` |
| 5 | 3D | no new solid for kit SKUs | **PASS** — cards stay declarativo; no mm on connector/harness; `calcular` masa **0.925 kg** unchanged |
| 6 | Hover | unchanged | **PASS** — margen **2.94** / sim `safety_margin_ratio=2.9387`; autonomía 1.5 min; 4/4 |
| 7 | ASSEMBLY READY | kit catalog must not become ready | **PASS** — BOM PASS; `NOT ASSEMBLY READY` · TOP GAP autonomy |

Adapter on the same paste (`con adaptador/collet`) is already [ACCEPT](engineer_smoke_kit_prop_adapter_ask_b1.md). Not this Buy.

## Out of this Buy

Autonomy ~1.5 vs 5 min is P-energy. Do not reopen D. Cable 100/300 mm did not become a box. No `current_a`. No `prop_adapter` SKU.

Do **not** append kit keys to `BLOCK_TO`. `"cabe"` stays **QUEUED** until Engineer ★.
