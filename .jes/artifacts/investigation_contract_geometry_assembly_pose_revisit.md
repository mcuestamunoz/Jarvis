# Investigation Contract — Geometry assembly pose revisit (after visualizar-3D)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede` 2026-09-08 — next named horizon rung is pose; 3D-in-center visor chrome **parked** (not this investigation)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_assembly_pose_revisit.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **Keep B0** (2026-09-08) · **CLOSED**  
**Parents (mandatory):**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — visualizar-3D **CLOSED**; pose is the next **named** product rung
- [investigation_contract_geometry_assembly_pose_b1plus.md](investigation_contract_geometry_assembly_pose_b1plus.md)
- [investigation_report_geometry_assembly_pose_b1plus.md](investigation_report_geometry_assembly_pose_b1plus.md) — lean **B0 Defer**; reversal criteria **§E**
- [investigation_review_geometry_assembly_pose_b1plus.md](investigation_review_geometry_assembly_pose_b1plus.md) — **PASS WITH NOTES**
- [implementation_contract_geometry_assembly_pose_b1plus_defer.md](implementation_contract_geometry_assembly_pose_b1plus_defer.md) — **B0 CLOSED** (doc-only)
- Stub [implementation_contract_geometry_assembly_pose_b1plus.md](implementation_contract_geometry_assembly_pose_b1plus.md) — **DEFERRED — DO NOT IMPLEMENT**
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**
- CSS 3D solids B1 **CLOSED** @ suite **2429** + smoke ACCEPT — [IC](implementation_contract_geometry_board_css3d_solids_b1.md) · [smoke](engineer_smoke_geometry_board_css3d_solids_b1.md)
- Click-inspect B1− **CLOSED** @ **2429** + smoke ACCEPT

**Type:** Investigation only — did anything shipped **after** B0 Defer **satisfy a named reversal criterion**, or is numeric pose still blocked?  
**Not** an Implementation Contract. **Do not implement.**  
**Not** `"cabe"` / fit. **Not** CAD/STEP/FEA. **Not** Conversation Engine. **Not** N-motor copies. **Not** moving the 3D pane (Engineer parked).

**Checkpoint base:** package **`0.3.8`** · suite **2429**

**Single objective (locked):**

> Re-check the **2026-09-07 B0 Defer** against live tree + the three reversal conditions in pose report **§E**. Decide whether the default lean is still **B0**, or whether new evidence (if any) justifies a **different** lean. CSS 3D solids and click-inspect are **visor**; they do not automatically create a reference frame.

**Product sentence this rung would enable (only if a later ★ Buy ≠ B0):**

```text
Sé a qué se declara montado y, si procede, con qué pose declarada respecto a un origen y ejes nombrados.
```

**Not:**

```text
El visor 3D ya coloca las piezas · la fila de sólidos es el drone · cabe · ensamblado verificado · el drag de cards es pose
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy / Defer / re-scope before any READY pose IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not add pose/offset/orientation/origin fields. Do not invent hole patterns, plate centers, or axis conventions. Do not treat `layoutSolidsRow` / card `x/y` / `mounted_on` as millimetre placement. Do not un-QUEUE fit. Do not recommend four motor/prop solids. Do not change 3D pane layout.**

---

## 0. Role split

```text
Engineer  → procede this revisit; 3D-in-center parked
Cursor    → this contract; review; READY pose IC only after ★
Claude    → investigation_report_geometry_assembly_pose_revisit.md
Engineer ★ → Buy lean / keep B0 / re-scope — never silent implement
```

---

## 1. Why this investigation exists now

The **product horizon** (locked 2026-09-08) names pose next:

```text
visualizar-3D (CLOSED) → place in space (pose) → later "cabe"
```

The **engineering lock** from 2026-09-07 still says pose is **B0 DEFERRED** until one of three reversal conditions holds. Those two statements are not a contradiction: the horizon names the rung; B0 says the rung is **not Buyable as schema** until evidence exists.

What shipped **after** the defer (do not re-investigate from zero — **cite** and **delta**):

| Slice | What it is | What it is not |
|---|---|---|
| Geometry-for-all B1 @ **2418** | More **text** envelopes | Not a body-frame convention |
| Remaining `mounted_on` @ **2429** | More **relations** | Not mm placement |
| Click-inspect B1− | Selection chrome | Not pose |
| CSS 3D solids B1 | Declared volume in a **presentation row** | Not pose; `layoutSolidsRow` forbids card `x/y` and `mountedOn` |

Wrong next moves:

```text
write x_mm on ComponentSpec because solids exist
place solids using mounted_on
treat Scene3D as the airframe
open the fit stub
copy the 2026-09-07 report without a live delta
```

Right question:

> Did **any** of §E’s three reversal conditions become true, or is B0 still the only honest lean?

---

## 2. Locked stances (inherit)

1. Parent pose report **§E B0 stands until reversed**. This revisit may **reaffirm** or **change the lean**; it may not ignore §E.  
2. Board card `{x,y,width,height}` / `localStorage` = **layout**, never pose SoT.  
3. `mounted_on` = assembly **relation** (guide), not fastener pose.  
4. CSS 3D `layoutSolidsRow` + gap in CSS px = **presentation**, same honesty class as card lanes.  
5. Disks stay **flat** (no `stator_height_mm` cylinder).  
6. One `ComponentSpec` = one card = one solid if `geometry` exists. `motor_count` is a **property**. Multiplicity is **out of this investigation**.  
7. No fit / `"cabe"` / collision / CAD. Fit stub stays QUEUED.  
8. If no named origin **and** no named axis convention exist, lean **B0**. Do not paper over with “assume plate center” or “put the row in the middle of the screen.”  
9. Continuity pose parsers are **out** of any first Buy (parent D10 still the default unless new evidence says otherwise).

---

## 3. Baseline to inventory (cite live tree)

Re-verify; do **not** rubber-stamp 2026-09-07 without opening the files. Prefer **delta**: “unchanged at file:line” or “changed: …”.

| Surface | Check |
|---|---|
| `ComponentSpec` / `state_schema.py` | Still **zero** pose / offset / orientation / origin fields? |
| Catalog seeds (Motor/Battery/ESC/FC/Frame/Prop) | Any **new** hole pattern, footprint anchor, or body-axis field since 2026-09-07? Full-seed grep, not anecdote. |
| Frame parts | Still no L×W usable as a geometric origin without invention? |
| `scene3dLayout.ts` + IC N1 | Confirm solids **cannot** read card `x/y` or `mountedOn` (decoy test U5 if still present). |
| `Scene3D.tsx` / `.sb-scene3d` | Own tilt/zoom; sibling of `.sb-viewport`; **not** inside `.sb-world`. |
| Projector `mountedOn` | Relation only; no mm. |
| Parent pose report **§E** | Quote the three reversal conditions **verbatim**, then score each **Met / Not met** with evidence. |

Do **not** re-run Geometry-for-all or glyph-fuel matrices except to say whether they added an **axis/anchor**.

---

## 4. Questions the report must answer

### A — Reversal scorecard (load-bearing)

Score **each** of the three 2026-09-07 §E conditions:

1. **SKU hole/anchor KNOW** — a cited manufacturer (or seed) mounting-hole pattern / footprint anchor for a live SKU. Stack 30.5 mm self-geometry, if it appears, is **orthogonal** (parent review N3) — do not conflate with airframe pose.  
2. **Jarvis body-frame convention** — an **explicit** named axis/origin convention in the product (not implied by CSS tilt `55°/−30°` or by a presentation row).  
3. **Explicit risk Buy** of scalar + prose without axis convention (parent contingency sketch) — only **Met** if this report finds Engineer already accepted that risk **in writing**. Engineer `procede` on **this investigation** is **not** that risk Buy.

If **all three are Not met**, default lean is **B0** unless you can name a **fourth** reversal with tree evidence. Inventing a fourth to escape B0 is a stop condition.

### B — What 3D visor changed (and did not)

1. Does a CSS box/disk at declared scale create a millimetre **placement** fact? (Expect: **no**.)  
2. Does sharing `selectedId` between solid and card create a reference frame? (Expect: **no**.)  
3. Could a later pose Buy **project** into `Scene3D` without making today’s row the SoT? Answer in one paragraph; **do not** design the camera.

### C — Honesty if anyone still wants a tiny Buy

Only if A shows a Met condition **or** a justified fourth reversal:

- Smallest durable bag (fields + origin + axes + `source`).  
- Optional vs required beside `mounted_on`.  
- Board: **text-only first** remains the default (parent D9). Moving 3D solids from numbers is a **later** visor Buy, not this lean’s rider.

If A is all Not met, **do not** sketch a schema as if it were recommended. Parent §6 contingency may be **cited**, not revived as a Buy.

### D — Buy options

Recommend **exactly one** default lean:

| Option | Meaning |
|---|---|
| **B0 — Keep defer** | Pose stub stays DEFERRED; no schema; no visor placement from numbers |
| **B1 — Optional declared translation** | Only if A/C are honest without invention |
| **B1+ — Translation + yaw** | Only if axes exist |
| **B0+risk** | Engineer-risk path (scalar + required prose, no axis) — **only** if you argue condition 3 is the recommendation, not a silent extra |
| **Reject numeric pose** | Permanent — **discouraged** unless you can show pose is impossible in principle (parent said it is not) |

State what would change the lean (update §E if the three conditions need a **wording** fix; do not drop them).

---

## 5. Non-goals (explicit)

- Implementation of pose, Continuity pose phrases, or 3D solid placement from numbers  
- Fit / `"cabe"` / un-QUEUEing the fit stub  
- N motors / N props as extra nodes  
- 3D pane layout (center / overlay / size) — **parked by Engineer**  
- Three.js / WebGL  
- Frame plate L×W invention  
- Motor cylinder from `diameter_mm` + `stator_height_mm`  
- Version bump · Conversation Engine · CAD/FEA  
- Re-opening Here3 / Pixhawk identity freeze

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean + one paragraph.  
2. **Delta since 2026-09-07** — table of shipped slices vs reference-frame impact.  
3. **Reversal scorecard** — §E 1/2/3 = Met / Not met + cite.  
4. **Answers B–D.**  
5. **Supersede or reaffirm** the 2026-09-07 B0 (must say which).  
6. **Risks if we Buy wrong** (especially “solids exist ⇒ pose”).  
7. **Later rungs** — `"cabe"` named, not bought.  
8. **Explicit non-goals honored.**

No Implementation Contract in the report. If lean ≠ B0, a **field-name sketch** is allowed (parent §6 style) — Cursor writes any IC after ★.

---

## 7. Done criteria

- [ ] Report at the path above  
- [ ] Scorecard complete; default lean stated; B0 allowed and preferred when evidence thin  
- [ ] 3D row explicitly **not** treated as pose  
- [ ] Fit stub still QUEUED; no code; no READY IC  
- [ ] Cursor investigation review next; Engineer ★ before any pose implementation IC

---

## 8. Stop conditions

Stop and ask before: treating CSS 3D or click-inspect as reversal; inventing plate center / hole pattern; opening fit; writing pose fields; or bundling 3D-pane chrome / N-motor copies into the lean.
