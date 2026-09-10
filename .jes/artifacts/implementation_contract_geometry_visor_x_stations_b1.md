# Implementation Contract — Visor X stations from cited wheelbase B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2562** + smoke **ACCEPT**  
**Parents:**
- [implementation_review_geometry_motor_visor_rebind_b1.md](implementation_review_geometry_motor_visor_rebind_b1.md) **PASS WITH NOTES**
- [engineer_next_geometry_motors_then_stations.md](engineer_next_geometry_motors_then_stations.md) ★2
- Mapping path product **B** — visor instancing from `motor_count` + **cited** wheelbase ([lock](engineer_lock_geometry_3d_mapping_path.md))
- Motor copies **CLOSED** @ **2473** — row; **this Buy replaces the row with X only when the gate holds**
- Hélices copies **CLOSED** @ **2550**
- Pose origin = **box** **CLOSED** — **do not** declare hélice pose vs motor disk
- Plate L×W **B0** — Rooster still **no** frame solid
- Wheelbase-on-spec **CLOSED** @ **2466** — `wheelbase_mm` is **motor-to-motor** (Rooster source_note: “230mm motor-to-motor”)

**Type:** Projector **additive DTO** `solidCopyOffsetsMm` (N points, declared mm) + visor placement of **copies**. Derived from **declared** frame `wheelbase_mm` + `configuration=quad_x` + motors spec `motor_count==4`.  
**Not** N `ComponentSpec`. **Not** a per-copy pose schema / writer change. **Not** a frame prism. **Not** silent 4 from `quad_x` alone. **Not** disk-origin pose.

**Baseline:** package **`0.3.8`** · suite **2555**

**Output:** `.jes/artifacts/implementation_report_geometry_visor_x_stations_b1.md`

---

## 0. Engineer Buy (locked)

Engineer: ver motores, **después juntar en el espacio**, then “redacta el siguiente IC de situar”.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-visor-x** — four stations in an X, visor-only |
| 2 | Count SoT | Spec `motor_count` **must be 4**. `quad_x` does **not** create a fourth motor. Live 10min (**3**) **stays a row** |
| 3 | Frame facts | `components["frame"].properties["configuration"].value == "quad_x"` **and** `wheelbase_mm` is a finite number. Missing either → **row** (do **not** read the library seed from the projector) |
| 4 | Wheelbase meaning | **Opposite** motor centers = `wheelbase_mm` (cited motor-to-motor). Center to motor = `W/2`. Quad-X at 45° |
| 5 | Formula | `a = W / (2 * sqrt(2))`. Index **0..3** in declared L→+X W→+Y, Z=0: `(+a,+a)`, `(+a,-a)`, `(-a,-a)`, `(-a,+a)` (FR, FL, RL, RR). Opposite pair distance **W** |
| 6 | Who gets offsets | `motors` and `propellers` **each** emit the **same** 4-point array **iff** that spec has `_geometry_from_spec` and the gate in #2–#3 holds. Independent geometry: props may station with mute motors still invisible |
| 7 | Cards | Still one motors card, one hélices card. Click copy `i` → that identity |
| 8 | Pose writer | **Unchanged.** No disk origin. Copies still **strip** `declaredBoxPose`. Stations are **not** `DeclaredBoxPose` |
| 9 | Z | **0** this Buy (coplanar silhouette). Do not stack hélices on `height_mm` 31.7 |
| 10 | Version | **No** bump |

**Product sentence:**

```text
Si el proyecto tiene 4 motores y el frame declara quad_x + wheelbase
motor-a-motor, el visor pone 4 discos motor y 4 discos hélice en X
alrededor del origen, W entre opuestos. Una card cada identidad.
Si N≠4 o falta wheelbase/quad_x, siguen en fila. Aún no hay sólido frame
ni pose hélice→motor.
```

**Not:**

```text
10min con 3 motores en 4 brazos · 230 inventado si la card no lo tiene
· cilindro · N cards · writer disk-origin · schema de N poses
```

---

## 1. You (Claude)

- Do **not** invent Rooster L×W or a frame box.
- Do **not** coerce `motor_count` to 4.
- Do **not** read `current_parameters` for N.
- Do **not** change `set_component_declared_box_pose`.
- Do **not** seed `emax_rs2205_2300` Ø.
- Do **not** mutate `workspace/`.
- Domain math in **Python** (`spatial_board.py`). Do **not** recompute `a` from card text in TypeScript.
- Full pytest green. `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.
- **Stop** if you need a per-copy pose array on `ComponentSpec` or a disk pose origin.

---

## 2. Intent

```text
frame.wheelbase_mm + frame.configuration==quad_x
  + motors.motor_count==4
        ↓
projector: solidCopyOffsetsMm[4]  (same formula, both identities with geometry)
        ↓
expandSolidCopies: copy i at remap(offset[i]), skip row slot
        ↓
clusterCenterPx still visor chrome
```

2D cards unchanged.

---

## 3. Locked behavior

### 3.1 Gate (`_solid_copy_offsets_mm(spec, components) -> list[dict] | None`)

Return **None** (omit DTO key) unless **all**:

1. `spec.suggested_key` in `("motors", "propellers")`
2. `_geometry_from_spec(spec)` is not None
3. motors spec exists; its `motor_count` parses with the **same** integer gate as `_solid_copies` and **`N == 4`**
4. frame spec exists; `configuration` value is exactly `"quad_x"` (string; not inferred from N)
5. `wheelbase_mm` is a finite number `W > 0`

Else omit — visor keeps today’s **row**.

**Never** substitute W=230. **Never** use N=3 corners.

### 3.2 Points

```text
a = W / (2 * sqrt(2))
[ {xMm: +a, yMm: +a, zMm: 0},   # 0 FR
  {xMm: +a, yMm: -a, zMm: 0},   # 1 FL
  {xMm: -a, yMm: -a, zMm: 0},   # 2 RL
  {xMm: -a, yMm: +a, zMm: 0} ]  # 3 RR
```

Emit only when `_solid_copies(spec, components)` is 4 (so DTO `solidCopies` and offsets length match).

### 3.3 Projector DTO

Additive `solidCopyOffsetsMm?: {xMm: number, yMm: number, zMm: number}[]` on motors / propellers nodes only.

### 3.4 Visor

`expandSolidCopies` / `layoutSolidsFromPose`:

- If a node has `solidCopies === 4` **and** `solidCopyOffsetsMm.length === 4`: each copy `i` is placed from offset `i` with the **same axis remap as pose** (declared +X→`originX`, +Y→`originZ`/depth, +Z→`originY`). **No** row slot. **No** `declaredBoxPose` on copies.
- Else: today’s row (pose stripped on copies).

Other solids (FC, battery, …) unchanged.

`types.ts`: add the optional array.

### 3.5 Copy

No `"cabe"`, `"ensamblado"`, `"verificado"` in new strings.

---

## 4. Tests

### Python — `tests/test_geometry_visor_x_stations_b1.py`

`project_spatial_nodes`. Motor disk 27.9 + prop `diameter_in` 5. Frame properties as specified.

| ID | Behavior |
|---|---|
| P1 | motors count **4** + disk + frame `quad_x` + `wheelbase_mm` **230** → motors `solidCopies===4` and 4 offsets; opposite (0 vs 2) distance `pytest.approx(230)`; props **same** 4 offsets; still one node each |
| P2 | count **3** + disk + `quad_x` + 230 → `solidCopies===3`, **no** `solidCopyOffsetsMm` on motors or props |
| P3 | count 4 + disk, frame **without** `wheelbase_mm` → no offsets (do not invent 230) |
| P4 | count 4 + disk, `wheelbase_mm` 230, **no** `configuration` → no offsets |
| P5 | count 4 + disk + `configuration=hex` + 230 → no offsets |
| P6 | motors **no** Ø, count 4, props disk, frame gate holds → motors no geometry/no offsets; props **have** offsets (same points as P1) |
| P7 | no `motor_count`, frame `quad_x`+230, both disks → **no** `solidCopies`, **no** offsets (quad_x does not win) |

### UI — `scene3dLayout.test.ts`

| ID | Behavior |
|---|---|
| U1 | motors `solidCopies:4` + 4 offsets (P1 numbers) → four layout ids; positions **not** a packed row (e.g. copy 0 and 2 separated on X or Z) |
| U2 | `solidCopies:4` **without** offsets → still today’s row (`motors#0..#3`, increasing `originX`) |
| U3 | offsets present → `declaredBoxPose` still stripped on copies |
| U4 | existing U1–U5 still green |

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | offsets helper + emit |
| `ui/spatial-board/src/types.ts` | `solidCopyOffsetsMm?` |
| `ui/spatial-board/src/scene3dLayout.ts` | place copies from offsets |
| `ui/spatial-board/src/Scene3D.tsx` | pass offsets into expand/layout if needed |
| `tests/test_geometry_visor_x_stations_b1.py` | P1–P7 |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U1–U3 |
| `.jes/artifacts/implementation_report_geometry_visor_x_stations_b1.md` | write |

`library/` empty. `workspace/` empty. Pose writer empty.

---

## 6. Engineer smoke (after Cursor review)

Live Board. Combine with rebind (still mute SKU today):

**`autonomía-de-5min` (N=4, frame currently no wheelbase):**

| Step | Expected |
|---|---|
| `actualiza la frame` (existing) | card `wheelbase_mm` **230**, `configuration` `quad_x` |
| `cambiar motor` → `emax_rs2205s_2300` | Ø 27.9; `motor_count` still **4** |
| 3D | **4** motor disks + **4** hélice disks in **X**, not a line. Opposite span ~230 mm at visor scale. Frame still **no** box |

**`autonomía-de-10min` (N=3, frame already 230/`quad_x`):**

| Step | Expected |
|---|---|
| `cambiar motor` → RaceSpec (optional this smoke) | still `motor_count` **3** |
| 3D | **row** of 3 (+ 3 hélices). **Not** 3-on-4-arms. **Not** a fourth motor |

Hover/W change from rebind is **ACCEPT**.

Record [engineer_smoke_geometry_visor_x_stations_b1.md](engineer_smoke_geometry_visor_x_stations_b1.md) after review.

---

## 7. Done when

- [ ] P1–P7 and U1–U3 green; prior copy tests still green
- [ ] Full pytest green; UI tests + typecheck green
- [ ] 10min-shaped count 3 never stations; missing wheelbase never 230
- [ ] No version bump; no mute-SKU Ø; no writer disk-origin
- [ ] Report written

---

## Explicitly not this IC

Per-copy `DeclaredBoxPose` array · disk-origin writer · invent 230 · coerce N=4 · cylinder · frame box / Rooster L×W · remaining pieces · Three.js · Conversation Engine · version bump
