# Engineer smoke — Declared sensors + kit envelope B1 (2026-09-09)

**Project:** `autonomía-de-5min` (Board + 3D screenshot)  
**Status:** **ACCEPT** (envelope Buy)  
**Authority:** Engineer screenshot — GPS box 40×40×12 present; noted “sensor añadido pero fuera del conjunto”  
**Parents:** [IC](implementation_contract_geometry_declared_sensors_kit_envelope_b1.md) §6 · [review](implementation_review_geometry_declared_sensors_kit_envelope_b1.md) **PASS** @ **2593**

| Step | Expected | Result |
|---|---|---|
| 1 | `declara el gps … mm` → sensors box | **PASS** — card shows 40×40×12; solid in 3D |
| 2 | Identity unchanged | **PASS** — GPS M9N / model field still present |
| 3 | No invented catalog dims without declare | **PASS** |
| 4 | Kit optional | not required this smoke |

### Note — “fuera del conjunto” (not a fail of this Buy)

IC §0.9: **pose / visor out.** Unposed box → remaining **row slot** (assembly root + X keep the racimo at world 0).  
`mounted_on=frame` is relation only — **not** millimetres. Pose origin must be a **box** (`frame` root is not).

**Situar (already shipped Continuity — not a new IC):** e.g.  
`declara el gps a 0 mm en x y 0 mm en y y 20 mm en z respecto a frame_plate`  
(adjust Δ to Engineer’s intent; origin = Main Plate box.)

**Not this smoke:** auto-pose · invent GPS mm · `#3` plate_2 · `#4` sourced dims.
