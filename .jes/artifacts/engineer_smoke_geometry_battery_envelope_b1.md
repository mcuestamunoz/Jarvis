# Engineer smoke — Geometry B1 Battery envelope on Board (2026-09-06)

**Status:** ACCEPT  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Visor:** `http://127.0.0.1:5173/`

## Setup

Live project had `lipo_4s_10000mah` (no `source_url` → correctly **no** dims).  
For smoke, battery rebound to sourced SKU `lipo_4s_1500mah` via `bind_battery_from_catalog` + `set_battery_component` + `save_state`.

## Observed on Board (CDP + screenshot)

Card `battery` / `lipo_4s_1500mah` fields include:

| Field | Value |
|---|---|
| `length_mm` | 37 mm |
| `width_mm` | 35 mm |
| `height_mm` | 75 mm |

API `/api/projects/9ada1a1b0cca/nodes` matched. Zero UI code change.

## Note

Project battery SKU changed for smoke (10000 → 1500). Engineer may rebind back to 10000 if desired — that card will again omit L×W×H (honest).

## Next

Motor Geometry investigation: [investigation_contract_geometry_motor_envelope.md](investigation_contract_geometry_motor_envelope.md)
