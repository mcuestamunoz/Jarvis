# Investigation Contract — Geometry pose origin & axes (body frame)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ **Keep B0** on pose revisit + restated horizon + Class A rule: missing envelopes are closed by **sourced** manufacturer/agent fetch (later ★), never invented.  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_pose_origin_axes.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · lean B0 for plate/front-arm · Engineer **did not** lock idle · next = [box-anchor](investigation_contract_geometry_pose_box_anchor.md)  
**Parents (mandatory):**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — product vision (rungs 1–2 **CLOSED**; this investigation is rung 3’s **blocker**)
- [investigation_review_geometry_assembly_pose_revisit.md](investigation_review_geometry_assembly_pose_revisit.md) — **PASS WITH NOTES** · Engineer ★ **Keep B0**
- [investigation_report_geometry_assembly_pose_revisit.md](investigation_report_geometry_assembly_pose_revisit.md) — §E2 **Not met** (no named origin/axes); CSS 3D ≠ pose
- [investigation_report_geometry_assembly_pose_b1plus.md](investigation_report_geometry_assembly_pose_b1plus.md) — §E condition 2 (body-frame convention) + §A origin honesty
- [investigation_report_geometry_for_all_b1.md](investigation_report_geometry_for_all_b1.md) — **cite** the 14-node envelope/glyph matrix; do **not** reopen plate L×W invention
- Stub [implementation_contract_geometry_assembly_pose_b1plus.md](implementation_contract_geometry_assembly_pose_b1plus.md) — **DEFERRED — DO NOT IMPLEMENT**
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**

**Type:** Investigation only — minimum **honest origin + axis convention** (if any) so “colocar en su lugar” can exist later; plus an **inventory** of which live components still cannot even appear as a 3D solid.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** `"cabe"` / fit. **Not** N-motor copies. **Not** 3D-pane chrome. **Not** inventing plate L×W / motor cylinder / Here3 footprint. **Not** running that fetch in this report (inventory + classify only).

**Checkpoint base:** package **`0.3.8`** · suite **2429**

**Single objective (locked):**

> Decide whether Jarvis can name a **self-consistent per-project origin and axes** (a body frame) without inventing CAD or plate centers, and inventory — without buying — which existing demo components still lack **envelope** vs still lack **placement**. Envelope gaps do **not** unblock pose; pose convention does **not** give missing solids.

**Product sentence this rung would enable (only after a later ★ Buy ≠ B0):**

```text
Las piezas con volumen declarado se pueden colocar respecto a un origen y ejes nombrados;
mounted_on sigue siendo la guía; aún no “cabe.”
```

**Not:**

```text
La fila 3D ya es el drone · las cards unidas en 2D son la pose · un L×W inventado hace ensamblaje · cabe
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy / Defer / re-scope before any READY IC.

**Do not implement. Do not bump version. Do not add pose fields. Do not invent envelopes, hole-to-hole mm, or “assume plate center.” Do not un-QUEUE fit. Do not place solids from `mounted_on` or card `x/y`. Do not treat Scene3D tilt as a body frame. Do not live-fetch manufacturer pages in this report** (Geometry-for-all already did; a later Class A ★ may).

---

## 0. Role split

```text
Engineer  → Keep B0 on pose revisit; restated horizon; this investigation
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_geometry_pose_origin_axes.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists now

Engineer vision (locked 2026-09-08, restated the same day):

```text
cards + mounted_on today
  → 3D image at declared scale     ← CLOSED (CSS 3D row)
  → click solid opens today’s card ← CLOSED
  → move / place in physical location (connections guide)
  → later "cabe" vs that spatial situation
```

Pose revisit **Keep B0**: numeric pose stays deferred because **no origin/axes** exist. CSS 3D did not create them.

Two distinct gaps are easy to flatten. This investigation must **keep them apart**:

| Class | Question | Status |
|---|---|---|
| **A — Solid (visualizar)** | Does this node have a declared box/disk so a 3D volume can exist? | **5/14** solids. Gaps: **sourced search later**, not invention. Geometry-for-all already live-fetched 4 frame pages (Armattan demo: no plate L×W). |
| **B — Placed (pose)** | Relative to **what origin**, along **which axes**, is this solid? | **This** investigation. `mounted_on` names *which* other component, not *where*. |

Wrong next moves:

```text
invent Main Plate 150×150 so the 3D “looks complete”
draw 3D edges and call it placed
add x_mm without naming +X
reopen Geometry-for-all as if it were pose
```

Right question:

> What is the **smallest named body-frame convention** Jarvis can adopt honestly, and which live families are still Class-A-blocked vs Class-B-blocked?

---

## 2. Locked stances (inherit)

1. Horizon rungs 1–2 stay **CLOSED**. This does not redo CSS 3D or click-inspect.  
2. Board `{x,y}` / `localStorage` = **layout**, never pose.  
3. `mounted_on` = **guide** (relation), not millimetre placement.  
4. CSS 3D `layoutSolidsRow` stays presentation until a later visor Buy *after* a pose fact exists.  
5. Class A: **cite** [geometry-for-all report](investigation_report_geometry_for_all_b1.md) §2. Engineer lock (2026-09-08): if a part/component still needs physical envelope, **review + realistic sourced search** (manufacturer page / datasheet, another agent) → then a **separate ★** to seed what was found. **Forbidden:** inventing L×W, motor cylinder from `stator_height_mm`, or Here3 dims under identity freeze. This report **classifies** candidates vs freeze vs shape-mismatch; it does **not** fetch or seed.  
6. Scene3D `55°/−30°` is a **camera**, not +X/+Y/+Z.  
7. Hole-pattern 30.5/20 on iFlight `source_note` is **orthogonal** (self-geometry of a mount interface) — cite pose-revisit N1/N2; do not treat as body frame.  
8. Fit stub stays QUEUED. `"cabe"` is after a **spatial situation**, not this Buy.  
9. If no origin **and** no axes can be named without invention, lean **B0** on convention too.  
10. A successful Class A fetch **still does not** place solids. Search and convention stay **parallel tracks**.

---

## 3. Baseline to inventory (cite live tree)

Re-verify; prefer delta.

| Surface | Check |
|---|---|
| Live demo 14 nodes | Class A: `geometry` present/absent (expect 5 solids). Class B: any origin/axis field (expect **none**). |
| Geometry-for-all §2 | Quote which 9 lack solids and **why**. Classify each: **search-candidate** (unsourced, page/datasheet might exist) vs **shape mismatch** (frame `wheelbase` ≠ box) vs **by-design thickness** vs **identity freeze** (Here3). Do **not** re-fetch pages in this report. |
| `ComponentSpec` | Still `parent_key` + `mounted_on` only. |
| Frame root | `wheelbase_mm` / `size_class_inch` / optional `body_*` — confirm still **not** a box origin. |
| `Scene3D` / `layoutSolidsRow` | Still no pose input. |
| Parent pose §A | Named origins = **component keys**, not invented centroids — reaffirm or challenge with evidence. |

---

## 4. Questions the report must answer

### A — Origin (what is “zero”?)

1. Which existing **component keys** can honestly be an origin today (`frame`, `frame_plate`, …) without a geometric point on that part?  
2. Is “origin = component key, point unspecified” enough to *name* a frame, or is it still not a millimetre origin?  
3. Forbidden: plate centroid, arm root, “frame center,” canvas middle.

### B — Axes (what is +X / +Y / +Z?)

4. Can Jarvis adopt an **explicit project convention** (e.g. +X forward along a named arm, +Z up, heading undefined) as a **declared rule**, not inferred from the 3D camera?  
5. Must the convention live in `ProjectState` (one per project) vs a global Jarvis constant vs only documentation?  
6. What happens to components whose `mounted_on` target has **no** envelope (plate with thickness only) — can they still be placed relative to a key?

### C — Gap matrix (Class A vs Class B)

For **each** of the 14 live demo keys, one row:

| Key | Solid today? | `mounted_on`? | Missing for a **solid** | Class A next | Missing for **placement** |
|---|---|---|---|---|---|

**Class A next** must be one of: `none` (already solid) · `sourced-search ★` · `shape-mismatch` (search won’t make a box) · `freeze` · `thickness-by-design`.

Do not fill “missing for a solid” with invented numbers. “Unsourced L×W” is a valid cell.

State in one sentence: **completing Class A does not produce an assembled 3D drone.**  
State in one sentence: **a later sourced-search ★ is how Class A grows; this investigation does not run it.**

### D — First Buy vs later visor

7. Smallest convention Buy: **names only** (document + optional schema tags for origin key / axis labels) vs **numbers** (deferred — parent B0). Default lean: convention investigation may recommend **naming** without shipping `x_mm`.  
8. May a later visor move solids using that convention + user-declared numbers? **Name** as later; do not design `Scene3D` layout here.  
9. 3D `mounted_on` **edges**: visor chrome vs pose? Default: **out** of a first convention Buy (2D edges already ship the guide).

### E — Buy options

Recommend **exactly one** default lean:

| Option | Meaning |
|---|---|
| **B0 — Defer convention** | Still cannot name origin/axes without invention; pose stays B0; inventory only |
| **B1 — Named convention, no mm** | Explicit body-frame labels (origin key + axis names) as declared product rule / optional schema **tags**, still **no** translation numbers |
| **B1+ — Convention + optional declared translation** | Only if A/B are honest; still not fit |
| **B0+risk scalar+prose** | Only if Engineer already wrote risk acceptance (they have **not**) — do not manufacture it |
| **Reject mixing** | If the only “progress” would be inventing envelopes to make 3D look assembled — reject that mix |

State what would change the lean.

---

## 5. Non-goals (explicit)

- Pose numbers IC / Continuity “10 mm” parsers  
- Fit / `"cabe"`  
- Inventing Class A envelopes (plates, motor cylinder, Here3) **in this report** — search is a **later ★**, not a silent extra  
- Running manufacturer fetches / seeding new dims here  
- Seeding iFlight 30.5/20 as pose  
- N motors / 3D pane center / Three.js  
- Version bump · CAD/FEA · Conversation Engine

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean + one paragraph.  
2. **Vision map** — rungs 1–2 shipped; this = blocker of rung 3.  
3. **Class A vs B** — one table, 14 demo keys.  
4. **Answers A–E.**  
5. **Risks** — especially “more envelopes ⇒ assembled 3D.”  
6. **Later rungs** — numbers / visor placement / `"cabe"` named, not bought.  
7. **Non-goals honored.**

No Implementation Contract in the report. If lean ≠ B0, a **name-only** sketch (origin key + axis labels) is allowed — not `x_mm/y_mm/z_mm` unless B1+ is the lean **and** axes are defined. Cursor writes any IC after ★.

---

## 7. Done criteria

- [ ] Report at the path above  
- [ ] 14-row Class A/B matrix  
- [ ] Default lean stated; B0 allowed  
- [ ] No invented envelopes; no pose code; fit still QUEUED  
- [ ] Cursor review next; Engineer ★ before any IC

---

## 8. Stop conditions

Stop and ask before: inventing plate center or L×W; treating `mounted_on` or Scene3D tilt as axes; opening fit; writing pose millimetres; recommending 3D-as-assembled from a complete envelope set; or starting a manufacturer fetch inside this report.
