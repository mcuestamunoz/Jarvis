# Implementation Report — BOM `sku_resolved` cameras/FC/sensors (`B1-bom-sku-resolved-cameras`)

**IC:** [implementation_contract_bom_sku_resolved_cameras_b1.md](implementation_contract_bom_sku_resolved_cameras_b1.md)  
**Implementer:** Cursor (Engineer-authorized “ejecuta tú”)  
**Date:** 2026-09-18  
**Baseline:** package `0.4.1` unchanged · targeted tests **18 passed** (6 new + Impl D BOM regression)

## Change

`project_closure._bom_sku_resolved` — added live-library branches:

| `CatalogRef.family` | Check |
|---|---|
| `cameras` | `has_camera` |
| `flight_controller` | `has_fc` |
| `sensors` | `has_sensor` |

Display-only. No bind/writers/gaps/ERF changes. Same class as the historical propeller miss.

## Tests

`tests/test_bom_sku_resolved_cameras_b1.py` — T1–T5 (bound Phoenix → `[runcam_phoenix_2]`; unknown → sin resolver; free-text no suffix; FC/sensors + motor regression; version checkpoint).

## Smoke (Engineer)

On vigilancia with Phoenix already bound: `estado` should show `cameras: runcam_phoenix_2 [runcam_phoenix_2]` (or equivalent), **not** `(SKU sin resolver)`.
