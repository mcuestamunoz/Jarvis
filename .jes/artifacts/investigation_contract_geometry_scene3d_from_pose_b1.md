# Investigation Contract — Scene3D-from-pose B1 (visor reads `declared_box_pose`)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede` 2026-09-08 — document the five mapping rungs, commit shipped Geometry, then investigate rung **1**.  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_scene3d_from_pose_b1.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **B1** (`escribe IC` 2026-09-08) · IC READY FOR CLAUDE  
**Report:** [investigation_report_geometry_scene3d_from_pose_b1.md](investigation_report_geometry_scene3d_from_pose_b1.md)  
**Review:** [investigation_review_geometry_scene3d_from_pose_b1.md](investigation_review_geometry_scene3d_from_pose_b1.md)  
**IC:** [implementation_contract_geometry_scene3d_from_pose_b1.md](implementation_contract_geometry_scene3d_from_pose_b1.md)  
**Parents (mandatory):**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — ★ five rungs; this is **rung 1 only**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — place in space; drag/`localStorage` ≠ pose
- Continuity pose B1 **CLOSED** @ **2456** + smoke **ACCEPT** — writer exists; visor still `layoutSolidsRow`
- CSS 3D B1 **CLOSED** @ **2429** — 5 solids; **1 `ComponentSpec` = 1 solid**
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — envelope ≠ reconstructed part; R1/R2 **CLOSED**
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- Airframe pose stub — **still DEFERRED**
- Mapping rungs **2–5** (wheelbase / 4-motor sketch / motor height 31.7 / plate L×W / `"cabe"`) — **out of this report’s Buy**

**Type:** Investigation only — minimum honest path for the **existing** CSS 3D visor to place existing solids from **already-written** `declared_box_pose`.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** new catalog KNOW. **Not** N-motor copies. **Not** plate L×W. **Not** motor cylinder. **Not** `"cabe"`. **Not** Three.js unless CSS 3D is proven unable to translate a solid. **Not** Conversation Engine.

**Checkpoint base:** package **`0.3.8`** · suite **2456** · commit `8930c0b`

**Single objective (locked):**

> Decide the **minimum honest visor placement** that reads `declared_box_pose` (origin = geometric center of a **box**; axes = declared L→+X, W→+Y, H→+Z) so a solid **leaves the presentation row** and sits in millimetres relative to that origin — still 1 identity = 1 solid, still not a quadrotor, still not `"cabe"`.

**Product sentence this would enable (only after a later ★ Buy ≠ B0):**

```text
El sólido deja la fila y se coloca en mm respecto al centro de una caja
origen, ejes L→+X W→+Y H→+Z declarados. Aún no es el Rooster ni “cabe.”
```

**Not:**

```text
Cuatro motores en X de 230 mm · la placa 150×150 · el visor parsea Δx mm
de la card · mounted_on es milímetros · cabe
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy / Defer / re-scope before any READY IC.

**Do not implement. Do not bump version. Do not add Three.js / r3f. Do not instance `motor_count`. Do not seed wheelbase / plate L×W / motor height. Do not un-QUEUE fit. Do not treat card `x/y` or `mountedOn` as millimetres. Do not change Continuity grammar unless a visor hole forces a named residual (default: grammar stays closed).**

---

## 0. Role split

```text
Engineer  → procede (rung 1 after mapping-path lock + commit)
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_geometry_scene3d_from_pose_b1.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists now

Pose is a **fact** in `ProjectState`. Continuity writes it. The Board **card** already shows `origen pose` / `Δx mm` / honesty axes. Scene3D still calls `layoutSolidsRow` and the CSS 3D IC explicitly forbade reading pose (review N1: row = presentation, not placement).

The mapping-path lock says the catalog dump is **not** the first missing piece. The first missing piece is: **the visor does not read the pose it already has.**

Wrong next moves:

```text
open rung 2 (wheelbase / 4 motors) because the row “looks like a drone”
parse card fields[] instead of projecting machine keys
place by walking mounted_on as mm
sit every unposed solid at the same origin (unreadable — CSS 3D review N1)
lift to Three.js because translate3d exists
```

Right question:

> What is the smallest honest change so the **existing** 5 solids can occupy **declared millimetre relation**, and what stays a presentation row?

---

## 2. Locked stances (inherited)

1. Board remains a **projection of `ProjectState`**. No mesh store as model of record.  
2. Fuel = existing `_geometry_from_spec` `{box, disk}` + existing `DeclaredBoxPose`. Absence of geometry = no solid. Absence of pose = **not placed** (see §4 D).  
3. Origin point = geometric center of `origin_key`’s **box** (schema docstring). Disk / shapeless remain **invalid origins** (writer already rejects).  
4. Axes = declared L→+X, W→+Y, H→+Z — **not** morro, **not** gravity, **not** catalog. Same honesty string as `POSE_AXES_HONESTY_LABEL`.  
5. `mounted_on` stays the **guide** (which component), never millimetres.  
6. Card `x/y` / `localStorage` stay **layout**.  
7. **1 `ComponentSpec` = 1 solid** until a later mapping-path ★ (rung 2). `motor_count=4` is a property, not four visor nodes.  
8. Disk stays **flat** (no cylinder / ε height). A disk **may** be a **placed** node (translation in a box frame) without becoming an origin.  
9. Fit stub stays QUEUED. Rungs 2–5 stay later ★.  
10. Click-inspect stays one `selectedId` / `onSelect` via `boardSelection.ts`. Cards stay the inspect surface.

---

## 3. Baseline to inventory (cite live tree, file:line)

| Surface | Check |
|---|---|
| `DeclaredBoxPose` | `action_schema.py` — `origin_key`, optional `x_mm`/`y_mm`/`z_mm`; origin = box center |
| Writer | `set_component_declared_box_pose` — reject disk/shapeless/self/missing |
| Projector | `_fields` emits **text** `origen pose` / `Δx mm` / … when origin still exists; **`_emit` has no machine pose key** (only `geometry` + `mountedOn`) |
| `SpatialNode` (`types.ts`) | `mountedOn?` · `fields[]` · **no** pose object |
| `Scene3D.tsx` | filters `geometry`; `layoutSolidsRow`; `Solid3D` `originX` only |
| `scene3dLayout.ts` | comment still says pose B0 DEFERRED — stale vs writer; still a **row** |
| `scene3dScale.ts` | box: `length_mm→x`, `width_mm→y`, `height_mm→z` — **visor display**, not CAD |
| `Solid3D.tsx` | box wrapper CSS `width=L`, `height=H`; cuboid depth = W (`translateZ(±d/2)`); disk `rotateX(90deg)` |
| `.sb-solid` | `position: absolute`; faces `top:0; left:0` — cite whether wrapper top-left or 50%/50% is the **drawn** center |
| Live demo | Re-verify 3 box / 2 disk / 9 none. Any node with `declared_box_pose` set? (smoke cleared ESC pose; do not assume a live offset) |
| Click-inspect | `InfiniteCanvas` `selectedId` shared with `Scene3D` / cards |

Do **not** invent a census from memory. Projector JSON or `state.json` + `_geometry_from_spec` / `_fields`.

---

## 4. Questions the report must answer

### A — How does pose reach the visor?

1. Prefer **additive machine DTO** on the node (mirror `mountedOn`: omit when origin vanished / pose None) vs parsing `fields` labels (`"Δx mm"`). Default lean to investigate: **DTO**. Parsing presentation text is a second SoT.  
2. Name the keys (sketch only, not an IC): e.g. `declaredBoxPose: { originKey, xMm?, yMm?, zMm? }`. Units mm. Omission rule = same honest-absence as B2 `mountedOn`.  
3. Confirm the projector stays the **only** writer of that DTO (Python). Visor never infers from `mountedOn` or card `x/y`.

### B — Where is the origin solid, and do we compose?

4. The origin node typically **has no** `declared_box_pose` (writer forbids self-origin). Where does **its center** sit in the scene? Pick a named rule (e.g. first referenced origin box at scene 0).  
5. If the origin **itself** is posed relative to a third box (ESC origin=FC, battery origin=ESC): is world position **composed** (battery at placed ESC center + offset) or always “center of origin’s **unposed** box at 0”? Schema says center of origin’s box — it does **not** say unposed. Default lean to investigate: **compose** along the origin chain; detect cycles; if origin has no pose, that box’s center is the chain root.  
6. Missing origin key / origin no longer a box: projector already omits pose **text**. Confirm visor omits placement (node falls back to unposed rule), never a guessed origin.

### C — CSS 3D axes vs declared L→+X

7. Cite `solidExtentPx` + `Solid3D` face transforms. Declared +X/+Y/+Z are L/W/H. CSS wrapper uses **width=L, height=H, depth=W**. A naive `translate3d(x_mm, y_mm, z_mm)` in CSS **does not** match declared +Y/+Z.  
8. Pick **one** remapping table (pose mm → CSS `translate3d` / `translateX/Y/Z`) that is the **same convention** the cuboid already uses. Do not claim CSS-Y is gravity-up. Do not relabel manufacturer L/W/H.  
9. Confirm `pxPerMm` stays `SCENE3D.pxPerMm` (linear, uncapped).  
10. Disk: where is its **center** relative to the wrapper after `rotateX(90deg)`? Can a disk take the same translation as a box without inventing axial height?

### D — Who stays in the row?

11. Unposed solids (no DTO pose): **must not** all collapse on the origin (CSS 3D review N1). Options to score: keep `layoutSolidsRow` for the unposed remainder (offset aside); hide unposed from 3D; sit unposed at a labeled “sin pose” row. Default lean: **remainder row**, posed nodes leave it.  
12. Origin box with no pose: it is **placed** (as root), not a remainder-row item, if any child references it — or still in the row with children offset from its row slot? Pick one and say why it is honest.  
13. Nodes with geometry but pose origin missing: remainder row.

### E — What this Buy must not become

14. Confirm `mountedOn` edges stay **2D Board** (or stay non-mm if any 3D hint is proposed — default: **no 3D mount edges this Buy**).  
15. Confirm **no** `motor_count` instancing.  
16. Confirm click-inspect: clicking a placed solid still `onSelect(id)` — no second selection model.  
17. Three.js: only if CSS `transform` cannot express the remapping in §C. Default lean: **keep CSS 3D**.

### F — Buy options

Recommend **exactly one** default lean:

| Option | Meaning |
|---|---|
| **B0 — Defer** | Pose stays card-text; visor stays a row until axes/DTO/composition is honest (say why) |
| **B1 — DTO + CSS place** | Additive projector keys; Scene3D places posed nodes with named axis remap; unposed remainder stays a row; 1 identity = 1 solid; no Three.js; no N-motors |
| **B1− — DTO only** | Machine keys for a later visor ★; 3D still `layoutSolidsRow` (usually too thin — pose text already exists) |
| **B1+ — Compose + place** | B1 plus explicit origin-chain composition (only if B1 would lie without it) |
| **B2 — Three.js** | Only if CSS 3D cannot translate a center in the declared frame |
| **Reject** | Parse `fields`; place by `mounted_on`; 4 motor copies; treat row as already placed |

Default IC lean to **prefer investigating B1 or B1+** (whichever composition evidence requires). State what would change the lean to B0.

If lean ≠ B0: **name-only sketch** of DTO + layout function split (`layoutSolidsRow` remains for remainder; new placer does **not** read card `x/y`). **Not** an IC. Do not sketch wheelbase.

---

## 5. Non-goals (explicit)

- Implementing Scene3D placement / projector DTO in this cycle  
- Rung 2: project `wheelbase_mm` / instance 4 motors  
- Rung 3: seed motor `height_mm` 31.7 / cylinder  
- Rung 4: plate L×W search or invention  
- Rung 5 / fit / `"cabe"`  
- Continuity grammar changes (unless a visor-only hole is proven — then name it as residual, do not reopen the assist as this Buy’s center)  
- Here3 unfreeze · battery L/W/H remap · STEP · Conversation Engine · version bump

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean + one paragraph.  
2. **As-is visor vs as-is pose** — DTO gap; `originX`-only; stale `layoutSolidsRow` comment.  
3. **Live census** — boxes/disks/none; any live `declared_box_pose`.  
4. **Answers A–F** including the **CSS ↔ declared axis table**.  
5. **Risks** — treating local prism axes as airframe; treating remainder row as “unassembled”; CSS top-left vs geometric center; composition cycles.  
6. **Later rungs** — 2–5 stay named, not this IC.  
7. **Non-goals honored.**

---

## 7. Done criteria

- [ ] Report at the path above  
- [ ] DTO vs `fields` scored; axis remap table cited from `Solid3D` / `scene3dScale`  
- [ ] Unposed remainder rule named (not “all at 0”)  
- [ ] Default lean stated; B0 allowed if honesty fails  
- [ ] No code; no Scene3D IC; fit still QUEUED; rungs 2–5 not bought  
- [ ] Cursor review next; Engineer ★ before any IC

---

## 8. Stop conditions

Stop and ask before: instancing motors; inventing plate L×W; opening fit; writing implementation; parsing card text as SoT; placing by `mounted_on`; or claiming the CSS 3D row is already a spatial situation.
