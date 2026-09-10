# Investigation Contract — 4 motors + 4 hélices in space (product B, then remaining pieces)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_quadrotor_kit_in_space_b0.md`  
**Review:** [investigation_review_geometry_quadrotor_kit_in_space_b0.md](investigation_review_geometry_quadrotor_kit_in_space_b0.md)

**Status:** INVESTIGATION CLOSED — Engineer ★ **B1-copies-prop** → [IC](implementation_contract_geometry_propeller_visor_copies_b1.md) APPROVED  
**Parents:**
- `"cabe"` B1-min **CLOSED** + ACCEPT — ESC vs FC screening; **not** this Buy
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — product **A racimo** vs **B silueta quadrotor** (do not collapse)
- Motor visor copies B1 **CLOSED** @ **2473** — N copies, **pose stripped**, **not** quad-X of 230, **no** propeller copies
- Scene3D-from-pose B1 **CLOSED** @ **2462** — pose origin must be a **box**; single-level; 1 hop
- Wheelbase-on-spec B1 **CLOSED** @ **2466** — Rooster `wheelbase_mm` 230 on the **card**, **no** frame solid
- Plate L×W **B0** — Rooster still **no** box
- Motor height cited **CLOSED** — disk stays disk; Ø+height **never** a cylinder
- Kit B1-min / adapter / SKUs D **CLOSED** — **out** (identity, no geometry)

**Type:** How (if at all) N motor disks + N propeller disks can sit in millimetres without inventing a frame prism or N BOM nodes.  
**Not** an IC. **Do not implement. Do not seed Ø. Do not invent Rooster L×W. Do not bump version.**

**Checkpoint:** package **`0.3.8`** · suite **2540**

**You are Claude Code.** Write the report only.

---

## 0. Role split

```text
Engineer  → 4 motores + 4 hélices visibles y juntar el resto en el espacio
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_geometry_quadrotor_kit_in_space_b0.md
```

---

## 1. Why this exists

ESC↔FC pose + AABB screening is **one pair of boxes**. The Engineer now wants the **kit in space**: first the propulsion set (N motors with N hélices), then other pieces the same way.

That is mapping-path **product B** (silueta), not “run `screen_posed_envelope` on every card.”

Wrong next step:

```text
N ComponentSpec / N cards / N BOM motors
· poner 4 copias en cruz de wheelbase 230 porque configuration=quad_x
· origin=motors (disk) con el gate actual de caja
· cilindro motor+hélice
· inventar L×W del Rooster para tener un sólido-origen
· AABB “cabe” de disco contra disco
· Conversation Engine
```

Right question:

> On the **live tree**, what blocks 4 motor solids + 4 propeller solids from sitting at **distinct millimetre stations**? What is the **minimum honest first Buy** — including **B0** — so copies are not a row of clones and hélices are not a single disk in the pile?

---

## 2. Locked stances

1. **Still one `motors` identity / one `propellers` identity.** Copies are visor-only unless a later ★ explicitly splits BOM. Click any copy → the **one** card.  
2. **N from the spec, never a default 4.** Use `components["motors"].motor_count`. If the live project is 3, do not draw 4. `configuration=quad_x` does **not** win.  
3. **Pose on copies is the bug to name, not ignore.** Today `expandSolidCopies` **strips** `declaredBoxPose` (U3) so N copies would stack. Any “in space” Buy must say how **N distinct offsets** exist without N `ComponentSpec`.  
4. **Pose origin is a box today.** `_declared_box_pose_dto` / `layoutSolidsFromPose` refuse a disk origin. Hélices `respecto a motors` **cannot** ship on the current gate. Do not quietly loosen that in the report as “obvious.” Name it as a Buy or a park.  
5. **Frame has no box.** Do not stitch `wheelbase_mm`+thickness into a prism. Quad-X stations from 230 mm without a frame solid is a **named** option, not the default — Engineer previously locked **not** X of 230 in copies B1.  
6. **Disk stays disk.** No cylinder. Screening `"cabe"` stays box–box; do not propose disk AABB this investigation.  
7. **Kit SKUs / adapter / plates thickness** are not 3D solids. Out.  
8. **Remaining pieces** (battery, sensors, …) only after the first Buy is named. This report’s default recommendation is **motors+hélices only**, not “all components this week.”  
9. No Conversation Engine. No version bump. No `workspace/` mutation.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `_solid_copies` / `expandSolidCopies` | Pose stripped; propellers never `solidCopies` |
| `_declared_box_pose_dto` + `layoutSolidsFromPose` | Origin **box** only; disk origin omitted |
| `emax_rs2205_2300` / live 5min and 10min motors | Ø / height / `motor_count` / `solidCopies` / geometry yes/no |
| Propellers live (`gf_5045x3` / `gemfan_5045_hbn`) | One disk; `mounted_on=motors`; pose? |
| Frame `wheelbase_mm` / `configuration` | Card facts vs no solid |
| Pose writer | One `DeclaredBoxPose` per `ComponentSpec` — no per-copy array today |
| `"cabe"` helper | Box–box only; copies / disks out |

Do **not** mutate `workspace/`. Read-only.

---

## 4. Report sections (required)

### A. As-is census

Table per live project: motors geometry / N / copies in 3D; propellers geometry / copies; which identities already have pose; whether any disk can be a pose origin.

### B. Why “the same as ESC–FC” does not scale

At most one page: copies strip pose; one pose field; origin-must-be-box; no frame prism.

### C. Honest Buys (ranked)

Recommend **exactly one** as the **first** IC (motors+hélices only):

| ★ | Meaning |
|---|---|
| **`B0`** | Leave copies in a row. Not enough stations / origin / per-copy pose. No IC. |
| **`B1-copies-prop`** | Propeller visor copies = `motor_count` (row only). Pose still stripped. **Not** in millimetres. |
| **`B1-stations`** | N distinct visor stations from **declared** offsets (schema for N poses on one spec) **or** another **cited** mechanism you prove exists — **not** silent quad-X from 230 unless Engineer ★ that explicitly. |
| **`B1-disk-origin`** | Allow pose origin = disk (motors) so **one** hélice can sit on **one** motor identity — still not 4 stations unless combined with stations. |

Park: remaining pieces (battery/sensors/kit), frame box, cylinder, `"cabe"` on disks, N BOM motors.

### D. Out of scope (explicit)

Invent Rooster L×W · default-4 · cylinder · Conversation Engine · widening `cabe` to every card this week.

---

## 5. Done when

- [ ] Report written; live census filled  
- [ ] No `src/` / `ui/` / library edit  
- [ ] Single recommended first Buy (`B0` / `B1-copies-prop` / `B1-stations` / `B1-disk-origin`)  
- [ ] Explicit: remaining pieces are **later ★**, not this IC  

---

## Explicitly not this investigation

Implement quad-X layout · seed motor Ø · N motor cards · `"cabe"` for disks · version bump
