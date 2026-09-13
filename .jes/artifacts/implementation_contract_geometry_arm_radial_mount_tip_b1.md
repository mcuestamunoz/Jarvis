# Implementation Contract — Arm radial Visor + Mount tip/parse align B1

**Buy ids:** `B1-arm-radial-visor` + `B1-mount-tip-parse-align` (one Claude cycle, two parts)  
**Project:** Jarvis  
**Date:** 2026-09-13 (rev: L-aware radial placement)  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★  
**Parents:**
- [FN arm radial](field_note_arm_radial_to_plate_b0.md) · [FN mount tip](field_note_mount_ambiguous_tip_parse_mismatch_b0.md)  
- Visor X arms CLOSED — stations = motor points ([IC arm visor X](implementation_contract_geometry_frame_arm_visor_x_b1.md))  
- Mount-standard CLOSED · silhouette S1 CLOSED  
- Engineer: use **declared arm L** to estimate assembly placement along the ray (not fixed station/2)  
- Continuity lock — no invent mm · no silent Continuity pose/mount write for arms this Buy  

**Type:** (A) Fix mount checklist tips + subject parse. (B) Visor-only: place+yaw `frame_arm` copies as **diagonal beams** using **declared L** along the origin→motor ray.  
**Not** inventing arm L from wheelbase/body. **Not** stretching/shrinking declared L. **Not** writing Continuity `mounted_on` / pose for `frame_arm`. **Not** moving motors/prop stations. **Not** four BOM arm keys. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_geometry_arm_radial_mount_tip_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2844** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **Combined** — Part A mount tip/parse + Part B arm radial Visor |
| 2 | Part A — tips | Ambiguous tips use **Spanish nouns** from `example_phrase` (controladora / sensor / …), **not** bare keys `flight_controller` / `sensors` |
| 3 | Part A — parse | Subject segment accepts **exact component keys** via `_exact_key_match` → `flight_controller montado en frame_plate` / `sensors montado en …` SET |
| 4 | Part A — optional | Singular `montaje estándar` / `montaje estandar` trigger — thin if cheap |
| 5 | Part B — placement | **`frame_arm` only.** Center each copy on the ray origin→`station[i]` using **declared `length_mm` (L)** — see §0.1. Motors/propellers/prop_adapter **unchanged** (full station points) |
| 6 | Part B — yaw | Yaw about +Z so box **length** axis aligns with the ray. Smallest DTO (`yawDeg` on offset points) + Scene3D `rotation.z` |
| 7 | Part B — L authority | L comes **only** from the declared arm box. **Never** set L from wheelbase. If L ≠ gap, draw honest size (may overhang or leave gap) — do not rescale geometry |
| 8 | Part B — gates | Same as today: arm box + `motor_count==4` + `quad_x` + `wheelbase_mm` or omit copies. If L missing/invalid → omit radial layout (keep prior omit/single-box honesty) |
| 9 | Part B — Continuity | **Visor layout only** this Buy — no new arm pose / `mounted_on` writers |
| 10 | Forbidden | Invent plate/arm mm · move motor/prop stations · silent Continuity writes · claim CAD-verified arms |
| 11 | Version | **No** bump |

**Product sentence:**

```text
Declaro L×W×H del brazo; el Visor lo coloca en diagonal hacia cada motor
usando ese L sobre el rayo (estimado de ensamblaje). No inventa el largo.
Los tips de montaje con clave también parsean.
```

### 0.1 Geometry — L-aware radial placement (locked)

```text
station[i] = _quad_x_station_points(wheelbase)[i]   # motors/props still use this raw
R = hypot(station.x, station.y)                    # radial gap origin → motor station
û = (station.x/R, station.y/R)                     # unit toward motor (R>0)
L = frame_arm.length_mm                            # declared only

# Place box so the DISTAL end (toward motor) sits on the motor station
# when L fits in the gap; length axis = û after yaw.
if L <= R:
  # distal end at station → center = station - û*(L/2)
  C = (station.x - û.x*(L/2), station.y - û.y*(L/2), 0)
else:
  # L longer than gap: do NOT shrink L; center on the available span
  C = (û.x*(R/2), û.y*(R/2), 0)

arm_offset[i] = { xMm: C.x, yMm: C.y, zMm: 0, yawDeg: atan2(station.y, station.x) in deg }
# Document which local box axis is "length" (must match Scene3D box convention).
```

**Honesty:** Visor **supuesto de ensamblaje** from declared L + cited wheelbase stations — not OEM arm CAD, not Continuity pose. Report must say so.

**Why not station/2:** Engineer locked L-aware placement so a declared 80 mm arm on ~80 mm ray reads as plate→motor; fixed midpoint ignored L.

---

## 1. You (Claude) — after ★

### Part A — Mount tip + parse

1. `format_mount_standard_checklist`: ambiguous tips use parseable nouns (`controladora montada en <clave>`, `sensor montado en <clave>`, …).  
2. `parse_mounted_on_declare`: subject segment → nouns first, else `_exact_key_match`.  
3. Tests A1–A4.

### Part B — Arm radial Visor (L-aware)

1. Helper e.g. `_frame_arm_radial_offsets_mm(spec, components)` implementing §0.1; call only for `frame_arm` from `_solid_copy_offsets_mm` (or equivalent).  
2. Thread `yawDeg` → UI expand → mesh yaw.  
3. Tests: L≤R → distal at station; L>R → center at R/2, geometry L unchanged; motors still at full station; gate omit unchanged.  
4. No Continuity writer changes.

Do **not** bump version. Do **not** mutate `workspace/`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| A1–A4 | As before (exact-key + tip nouns + non-reg) |
| B1 | Motors offsets = full `station`; arm ≠ station |
| B2 | Fixture L≤R: `\|C - (station - û*L/2)\| ≈ 0` |
| B3 | Fixture L>R: C ≈ û*(R/2); emitted box still uses declared L (not R) |
| B4 | Yaw = atan2(sy, sx) (or documented equivalent) |
| B5 | Missing L / gate fail → omit arm copies as today |
| B6 | UI rotation applied |
| T | Full suite green; package `0.4.1` |

---

## 3. Smoke (Engineer) — `10-min-autonomía`

**A:** Mount tip paste for FC/sensors works.  
**B:** Board: arms diagonal toward motors; with current ~80 mm arm vs ~wb/√2 station, distal near motor — not boxes under motor disks.  
**C:** `parece un dron` still B\*.

---

## 4. Out of scope

Invent/stretch L from wb · Continuity arm pose/mount · plate-edge inset from plate L×W · standoff · silhouette S2 · HD-005

---

## 5. Done when

- [ ] Engineer ★  
- [ ] Part A + Part B + tests + report  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ this IC
Claude   → implement + report
Cursor   → review
Engineer → smoke §3
```

### Paste for Claude (after ★)

```text
Implementá B1-arm-radial-visor + B1-mount-tip-parse-align per
.jes/artifacts/implementation_contract_geometry_arm_radial_mount_tip_b1.md
— Part A: ambiguous tips use nouns + exact-key subject parse.
— Part B: frame_arm L-aware radial placement (§0.1: distal at station if L≤R;
  else center at R/2; never rescale L) + yaw; motors/props unchanged.
No invent arm L from wheelbase; no Continuity arm pose write; no version bump;
no workspace/ mutation.
Report → implementation_report_geometry_arm_radial_mount_tip_b1.md
```
