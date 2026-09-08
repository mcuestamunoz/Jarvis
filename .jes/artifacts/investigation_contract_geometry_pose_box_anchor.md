# Investigation Contract — Geometry pose box-anchored origin (existing solids)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede` 2026-09-08 — investigations must find a **path** toward place-in-space; origin/axes B0 on **frame_plate / front-arm** is not the end of the horizon. Next candidate: millimetre origin on a node that **already has** `geometry: box`.  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_pose_box_anchor.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **B1 declared box-local frame** (`procede` 2026-09-08) · IC READY FOR CLAUDE  
**Parents (mandatory):**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — rungs 1–2 CLOSED; rung 3 = place, guided by `mounted_on`
- [investigation_review_geometry_pose_origin_axes.md](investigation_review_geometry_pose_origin_axes.md) — **PASS WITH NOTES** · lean B0 for *plate-key / +X along arm* — **not** locked as vision-closed
- [investigation_report_geometry_pose_origin_axes.md](investigation_report_geometry_pose_origin_axes.md) — Class A ⊥ Class B; arm individuation named **not bought**
- [investigation_report_geometry_assembly_pose_b1plus.md](investigation_report_geometry_assembly_pose_b1plus.md) — origin may differ from `mounted_on` target (§A3)
- CSS 3D B1 **CLOSED** @ **2429** — `geometry` `{box, disk}` already on the visor
- Stub pose IC — **DEFERRED — DO NOT IMPLEMENT**
- Fit stub — **QUEUED — DO NOT IMPLEMENT**

**Type:** Investigation only — can a **declared box solid** supply an honest origin **point** and a **local axis triad** without inventing plate L×W, front arm, or airframe CAD?  
**Not** an Implementation Contract. **Do not implement.**  
**Not** `"cabe"`. **Not** arm individuation. **Not** Class A manufacturer fetch. **Not** N-motor copies. **Not** moving `layoutSolidsRow` in this cycle.

**Checkpoint base:** package **`0.3.8`** · suite **2429**

**Single objective (locked):**

> Determine the **minimum honest pose convention** that uses **already-declared** `box` L×W×H (live demo: FC, ESC, battery) as the origin geometry — so “colocar” has a *where on that object* and a *which way* that are functions of existing KNOW, not of `frame_plate` or `frame_arm`.

**Product sentence this would enable (only after a later ★ Buy ≠ B0):**

```text
Coloco otros nodos respecto al volumen ya declarado de un sólido-caja
(origen + ejes locales del prisma); mounted_on sigue siendo la guía; aún no cabe.
```

**Not:**

```text
El centro de la placa · +X = brazo delantero · la fila 3D ya está colocada · cabe
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy / Defer / re-scope before any READY IC.

**Do not implement. Do not bump version. Do not add pose fields. Do not invent plate L×W, plate center, front arm, or motor cylinder. Do not ★ arm individuation. Do not un-QUEUE fit. Do not treat Scene3D tilt or card `x/y` as the frame. Do not live-fetch manufacturer pages.**

---

## 0. Role split

```text
Engineer  → procede (path toward place; box-anchored origin)
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_geometry_pose_box_anchor.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists now

Origin/axes investigation answered a **narrow** question and answered it well: you cannot put millimetre zero on `frame_plate` (no surface) and you cannot name “+X along the front arm” (one `frame_arm` key). Engineer rejected treating that as **closing the vision**.

What that report **did not** decide: several live nodes **already are boxes**. The projector DTO is:

```text
{ shape: "box", length_mm, width_mm, height_mm }
```

Those three numbers are **sourced extents of that component**, already drawn as CSS 3D prisms. A point such as “geometric center of this prism” or “corner of the min-L/min-W/min-H octant” is a **function of declared dims**, not a plate-center invention.

`mounted_on` stays the **guide** (which other key). Pose origin **may** be a different key that has a box (parent pose §A3). Example: ESC `mounted_on=frame_plate` (relation) while millimetre origin is `flight_controller` (has a box).

Wrong next moves:

```text
lock B0 and idle the horizon
invent frame_arm_2
invent Main Plate 150×150
ship +Z-only schema theater
open fit
```

Right question:

> Can the **first** place-in-space convention be **local to an existing box solid**, and what is the smallest honest Buy (if any)?

---

## 2. Locked stances

1. Parent B0 stands **only** for: origin = shapeless frame part; +X = named front arm. This investigation **must not** re-litigate that; it **must** score a **different** origin class.  
2. Fuel = existing projector `geometry`. **Box** may be origin. **Disk** as origin is a question (no unique in-plane +X from diameter alone) — default lean: **disk is not origin in a first Buy**.  
3. Derived point / axes may use **only** `length_mm` / `width_mm` / `height_mm` of the origin node (plus a **named** mapping rule). No extra catalog holes.  
4. Mapping DTO L/W/H → drone “forward” is **not** automatic. The report must say whether first Buy is:  
   - **local prism frame only** (axes of that part, no claim they are airframe +X), or  
   - **airframe body frame** (needs an extra declared heading — likely still B0 for that claim).  
   Default lean to investigate: **local prism frame** is the smaller honest step.  
5. `mounted_on` ≠ pose. Do not place by walking the mount graph as millimetres.  
6. Card layout / `layoutSolidsRow` stay presentation until a later visor Buy **after** a pose fact exists.  
7. Arm individuation / N motors / Here3 unfreeze / plate L×W invention — **out**.  
8. Fit stub stays QUEUED.  
9. If even a box-center is judged invention (it should not be, unless you cannot define the rule without extra data), lean **B0** and say why.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| Live demo 14 nodes | Which have `geometry.shape === "box"` vs `"disk"` vs none. Expect **3 boxes** (FC, ESC, battery) + **2 disks** (motors, props). Re-verify projector, do not assume. |
| `spatial_board._geometry_from_spec` | Box iff all of L, W, H present; disk iff diameter. |
| DTO field names | `length_mm` / `width_mm` / `height_mm` — any comment on which is “forward”? (expect: **none**) |
| Pixhawk / ESC / battery seeds | Cite the three numbers; they are **part** extents, not airframe pose. |
| `mounted_on` of those three | Relation targets (expect plates/frame) **without** geometry. |
| `ComponentSpec` | Still no pose fields. |

---

## 4. Questions the report must answer

### A — Who can be origin?

1. List live keys with `box`. Can **any** of them be origin, or only a chosen default (e.g. FC)?  
2. May origin be **optional** and user-declared as an existing box key?  
3. Confirm disks **cannot** be origin in B1 without inventing an in-plane heading (or argue otherwise with evidence).  
4. Confirm shapeless keys (`frame_plate`, `frame_arm`, …) stay **invalid** origins — parent B0 unchanged for them.

### B — What point on the box?

5. Smallest derived point that needs **no new KNOW**: geometric center vs a named corner vs a named face center. Pick one default; say if others are later.  
6. Is that derivation **honest** (function of L×W×H + named rule) or still invention?  
7. Units: mm in the origin’s local frame.

### C — What axes?

8. Local triad: can +X/+Y/+Z of the **part** be identified with DTO `length` / `width` / `height` **as labels of the prism** without claiming drone heading?  
9. Does first Buy need an extra “which DTO axis is airframe forward” field? If yes, is that a **declared** enum (user/Engineer) or still blocked?  
10. `+Z up` (gravity) vs `height_mm` of the box — can they conflict? What is the honest first rule?

### D — Who can be placed?

11. Can another **box** be given a translation in the origin’s local mm frame as a later Buy?  
12. Can a **disk** (motor) be placed in that frame without a motor cylinder / shaft axis KNOW?  
13. Nodes with **no** `geometry`: relation-only (`mounted_on` text + 2D edge); **no** millimetre pose — confirm.

### E — Buy options

Recommend **exactly one** default lean:

| Option | Meaning |
|---|---|
| **B0 — Defer** | Even box-center / prism axes are not honest yet (say why) |
| **B1 — Named local prism frame** | Origin = existing box key; point = derived (center or corner); axes = DTO L/W/H labels; **no** airframe heading; **no** visor move this Buy (schema/text only unless you justify a later visor rider as out) |
| **B1+ — Prism frame + optional translation numbers** | Only if B1 is solid; still not fit; still not Scene3D auto-layout unless explicitly argued as a **separate** visor slice |
| **B2 — Claim airframe +X** | Only if a heading rule exists without inventing a front arm |
| **Reject** | Box-anchor is the same trap as plate-center |

Default IC lean to **prefer investigating B1** (convention + inspectable text, visor placement **later**). State what would change the lean.

If lean ≠ B0: **name-only sketch** of fields (origin key, point rule, axis labels) — **not** an IC. Do **not** sketch `x_mm` unless B1+ is the lean.

---

## 5. Non-goals (explicit)

- Implementing pose / Continuity “10 mm” / moving solids in `Scene3D`  
- Fit / `"cabe"`  
- Arm individuation / four motor solids  
- Inventing Class A envelopes  
- Manufacturer fetch  
- Three.js / pane chrome  
- Version bump · CAD · Conversation Engine

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean + one paragraph (this is a **solution path**, not a second B0 rubber-stamp unless evidence forces it).  
2. **Relation to origin/axes B0** — what stays closed (plate / front arm); what this opens.  
3. **Live box/disk census** — file:line / DTO.  
4. **Answers A–E.**  
5. **Risks** — especially treating local prism axes as airframe heading; treating visor row as placed.  
6. **Later rungs** — visor placement, disks, plates after sourced L×W, `"cabe"`.  
7. **Non-goals honored.**

---

## 7. Done criteria

- [ ] Report at the path above  
- [ ] Box vs disk vs none scored on the live demo  
- [ ] Default lean stated; B0 allowed if the path fails honesty  
- [ ] No code; no pose IC; fit still QUEUED  
- [ ] Cursor review next; Engineer ★ before any IC

---

## 8. Stop conditions

Stop and ask before: using `frame_plate` as millimetre origin; naming a front arm; inventing L×W; opening fit; writing implementation; or claiming the CSS 3D row is already placed.
