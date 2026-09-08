# Engineer Lock — Pre-assembly honesty (demo reds before 3D place / Class A)

**Date:** 2026-09-08  
**Authority:** Engineer (CAD-validation reflection after Continuity pose ACCEPT)  
**Status:** ★ LOCKED (stance holds) — demo **R1 + R2 CLOSED** by Engineer CLI walk 2026-09-08. Scene3D-from-pose / Class A may be named again. Still **no** STEP / Here3 unfreeze / battery remap / motor cylinder / `istand`.  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)
- Continuity pose B1 **CLOSED** @ **2456** + ACCEPT
- Conn walk ACCEPT [engineer_smoke_connect_remaining_mounted_on_b1.md](engineer_smoke_connect_remaining_mounted_on_b1.md) — `sensor montado en el esc` was **relation**, not physics
- Bug 78: bind **preserves** `motor_count`
- Rooster seed `source_note`: no arm/plate counts inferred from Compressed-X / `quad_x`
- Fit stub — **QUEUED**. Airframe pose stub — **DEFERRED**

**Not an IC. Do not implement.** No STEP import. No Here3 unfreeze. No battery L/W/H remap. No motor cylinder glyph. No `istand` ontology.

---

## Locked claim

```text
envelope ≠ pieza reconstruida
Rooster (frame KNOW) is the bottleneck for a quadrotor solid, not Three.js
Do not assemble in 3D a craft the state says has 3 motors and GPS on the ESC
```

Visualizar for **5** solids (FC, ESC, battery boxes; motor/prop disks) stays honest. Frame parts without L×W stay **gaps**. CAD A/B/C:

| Level | Jarvis |
|---|---|
| **A** envelope | Closed for those 5. Motor→cylinder (Ø+height) **not** A. Frame→compressed-X 230 mm solid **not** A |
| **B** holes / contours / standoffs | No schema. Rooster mechanical = **investigation** later, not IC, not STEP-in-core |
| **C** STEP/STL | MEASURE / CAD — far ★ |

`declared_box_pose` on `frame` **no**: writer requires a box origin; the root has none.

---

## Two reds — **CLOSED** (Engineer CLI walk 2026-09-08)

Cursor re-read `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` after the walk (`active_iteration` 72):

| Red | Before | After |
|---|---|---|
| R1 `motor_count` | 3 in params + spec (`calculated`) | **4** in `current_parameters` **and** `components.motors` (`source: declared`) |
| R2 `sensors.mounted_on` | `esc` | **`frame`** |

Walk-only. No IC. No `state.json` hand-edit.

**Side effect (not a red reopen):** `motors.mounted_on` is now **`null`** (was `frame_arm`). Count/SKU rewrite did not keep the mount. Re-declare with Continuity if the Board edge is wanted: `motores montados en los brazos`. Catalog SKU also moved to `sunnysky_r2305_2500` (was emax) — product choice this session, not this lock.

`arm_count` on Rooster still **unset** (separate ★).

---

## Catalog / geometry findings — not this lock’s Buys

Left **out on purpose** (already seen). Do not “fix” them in the same cut as R1/R2:

| Topic | Stance |
|---|---|
| Motor Ø27.9; 31.7 mm + 15 mm shaft **cited in `source_note`, not seeded** | Optional later ★: seed `height_mm` 31.7 as **cited**, **no** cylinder/glyph until shape investigation |
| Thrust 10.042 vs OP Gemfan 13.4841 | Geometry ≠ thrust (locked). Bind/OP display is orthogonal |
| Prop Ø127, pala unknown | Disk envelope only |
| ESC 50×21.6×12 / PN 30901001 vs 30901013 | Variant rows stay split |
| Battery 37×35×75 unlabeled print order | Do **not** remap to “L = long side” as new KNOW |
| Pixhawk 44×84×12, no mass | Envelope yes; CAD connectors no |
| Here3 76×76×16.6 vs 68×68×16 | Identity **frozen** — sensor investigation, not Geometry |
| Rooster 230 mm ≠ CAD; GetFPV kit extras not in seed | Source = Armattan page. STEP/Yeggi = secondary |

---

## Ordered work if Engineer ★ (do not skip)

1. ~~**Close R1 + R2 in the demo**~~ → **CLOSED** CLI walk 2026-09-08.  
2. Optional motor `height_mm` 31.7 cited — no new shape.  
3. **Not** in that cut: battery remap, Here3 dims, Rooster STEP.  
4. Later: **Rooster mechanical** investigation — classify Armattan vs GetFPV kit vs third-party STEP; what can be seeded without faking a drawing.  
5. Ordered queue now in [3D mapping path](engineer_lock_geometry_3d_mapping_path.md): Scene3D-from-pose **first** (investigation); plate L×W is **rung 4**, not a co-equal next.

---

## Explicit non-goals until later ★

Scene3D placement from pose · Class A plate invention · motor cylinder from Ø+height · `istand` · Here3 unfreeze · in-product web crawl · fit/`cabe` · Conversation Engine · version bump without ask

---

## Mode

**Reds CLOSED by CLI.** Stance (envelope ≠ CAD, Rooster bottleneck, no STEP/cylinder/Here3) **holds**. Package `0.3.8`.
