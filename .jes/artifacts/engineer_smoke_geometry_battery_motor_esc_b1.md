# Engineer smoke — Geometry Battery + Motor + ESC on Board (2026-09-07)

**Status:** ACCEPT  
**Commit:** `56c71ee` (pushed to `origin/main`)  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Visor:** `http://127.0.0.1:5173/`

## Rebinds for smoke

| Component | Before (typical) | After (sourced) |
|---|---|---|
| battery | often `lipo_4s_10000mah` / prior smoke 1500 | `lipo_4s_1500mah` |
| motors | `emax_rs2205_2300` (no dims) | `emax_rs2205s_2300` |
| esc | freeform `ESC 40A` | `hobbywing_xrotor_40a_6s` |

## Observed (projector + Board API)

| Card | Dims |
|---|---|
| battery | 37 / 35 / 75 mm |
| motors | stator 22/5 · Ø 27.9 · shaft 3 mm |
| esc | 50 / 21.6 / 12 mm |

## Note

Workspace state was mutated for this smoke (SKU rebinds). Engineering truth for the walk is the rebound catalog SKUs.
