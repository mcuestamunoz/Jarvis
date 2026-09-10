# Engineer smoke — Geometry assembly fit B1-min (2026-09-09)

**Projects:** `autonomía-de-5min` (fail-closed) + `autonomía-de-10min` (overlap)  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_assembly_fit_cabe_b1.md) §6 · [review](implementation_review_geometry_assembly_fit_cabe_b1.md) PASS WITH NOTES @ suite **2540**

| Step | Surface | Expected | Result |
|---|---|---|---|
| 5min pose 5/0/0 | ESC `ESC 40A` no box | `child_not_box` copy | **PASS** — `este componente no es una caja declarada.` Pose Δ shown. Not `cabe`/`VERIFIED` |
| 10min pose same phrase | Hobbywing box vs Pixhawk box | overlap screening | **PASS** — Board `sobres`: *Los sobres se solapan en los ejes declarados — screening, no verificado.* `origen pose: flight_controller`. `montado en: frame_plate` stays a **different** fact |
| 5min `estado` | hover / 4/4 | unchanged | **PASS** — margen **2.94**; energy gap only |
| 10min Continuity | screening must not “close” physics | sim still fail | **PASS** — `GAP-SIM-NOT-PASS`; `BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO`. That is **P-energy** on this demo (same detour as kit B1-min), not a fit defect |

IDLE `cabe` and far-pose `no_overlap` were not walked. T2/T7 cover them. Optional.

## Out of this Buy

10min sim FAIL / autonomy / “stack no cerrado” is energy evidence, not AABB. Do not reopen fit. Do not invent Rooster L×W. Do not treat visor 0 as a declared axis.

Do **not** append kit keys to `BLOCK_TO`. Do **not** port `scene3dLayout.ts`.
