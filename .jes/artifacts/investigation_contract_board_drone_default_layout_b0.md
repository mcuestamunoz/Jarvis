# Investigation Contract — Drone default layout / main-plate assembly root (B0)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_board_drone_default_layout_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · [report](investigation_report_board_drone_default_layout_b0.md) · [review](investigation_review_board_drone_default_layout_b0.md) · await Engineer ★ **`B1-mount-standard-assist`** (or **B0**)  
**Report:** [investigation_report_board_drone_default_layout_b0.md](investigation_report_board_drone_default_layout_b0.md)  
**Review:** [investigation_review_board_drone_default_layout_b0.md](investigation_review_board_drone_default_layout_b0.md)  
**Parents:**
- Engineer ask (2026-09-12→13): after Situar experience still “malísima”, go beyond UX — **standard drone structure** (props→motors→arms→main plate; battery/ESC/FC/GPS/connector inside/on frame) and ask whether Jarvis can fix **main frame box as assembly start** and situate components by dimension  
- Feature: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md) ★ — envelopes · `mounted_on` (guide) · pose · visor copies; **auto-pose without citation OUT**  
- Mapping path: [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — Product **A racimo** vs **B silueta**  
- Assembly root already coded: `ASSEMBLY_ROOT_ID = "frame_plate"` when that solid is a **box** (`scene3dLayout.ts`)  
- Relation CLOSED: [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md)  
- Conn / Continuity mount assist CLOSED — declare mounts, **no** silent auto-mount  
- Assembly kit template B1-min CLOSED — **identity** kit holes, **not** pose wizard  
- Situar experience B1 LANDING — [IC](implementation_contract_board_situar_experience_b1.md) (ergonomics only; does **not** invent layout)  
- Plate L×W: #4g-A CAD **CLOSED B0** — GEP part envelopes absent unless Option B caliper / new citation  
- Quad-X / wheelbase stations / standoff perimeter — already shipped for copies when facts exist  
- **Out as auto-Buy:** Conversation Engine · LLM invent Δmm/mounts/plate L×W · Three.js rewrite · N BOM clones · Fit VERIFIED reopen · HD-005 · STEP-in-core · treating body 175×173 as plate footprint without ★

**Type:** Product-path investigation — **default drone assembly layout** vs what Continuity + visor already do.  
**Not** an IC. **Do not implement. Do not bump version. Do not invent millimetres. Do not mutate `workspace/`.**

**Checkpoint:** package **`0.4.1`** · suite ~**2747** · UI ~**99**

**Engineer product sentence to evaluate (honest / dishonest):**

```text
Jarvis trata la caja principal del frame como origen de montaje y sitúa
los componentes en el espacio según su dimensión y un estándar mínimo
de dron (hélices→motores→brazos→placa; stack/battery/GPS respecto a placa).
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → wants standard-drone situar from main plate, not endless drag UX
Cursor    → this contract; review; IC only after ★ on Buy shape(s)
Claude    → investigation_report_board_drone_default_layout_b0.md
```

---

## 1. Why this exists

Block-by-block project creation already mirrors “define components.” The Engineer now wants the **spatial** analogue: a **minimum airframe standard** so a novice does not hand-place every Δmm.

Situar experience B1 improves picking/dragging; it does **not** answer “where should the stack sit relative to the main plate.”

Wrong next step:

```text
· LLM invents poses / plate L×W / “typical 30×30 stack height”
· Silent mounted_on from BOM co-membership
· Treat mounted_on as millimetres
· Pretend body footprint 175×173 is the Main Plate box without ★
· Mega-wizard Conversation Engine
· Collapse Product A/B without naming the data gate
· Reopen Situar experience IC as if layout were an ergonomics bug
```

Right questions:

> **Q1 (as-is root):** On the live tree, what exactly activates assembly root today? What blocks `frame_plate` on 15min/5min GEP (and Rooster demos if still relevant)?  
> **Q2 (standard graph):** Map the Engineer’s minimum drone graph (props→motors→arms→main plate; battery/ESC/FC/GPS/connector/harness) onto existing keys (`mounted_on`, `parent_key`, pose origin, stations). What is already expressible vs missing?  
> **Q3 (dimensions vs positions):** Which facts are **envelope-only** (L×W×H / Ø) vs which need **pose defaults**? Where can “by dimension” honestly mean stacking offsets from envelopes alone vs where a cited/declared Δmm pack is required?  
> **Q4 (authority):** What Buy shapes keep Continuity SoT without inventing mm — plate data (caliper/cite), suggest-only mount+pose assist, cited kit layout pack, B0 leave racimo?  
> **Q5 (first Buy):** Rank one **first** IC (or B0/DEFER) that maximally unblocks “main plate as start” without lying.

---

## 2. Locked stances

1. **ProjectState / Continuity writers remain SoT.** No parallel pose schema in the UI.  
2. **`mounted_on` ≠ millimetres.** Relation guide only.  
3. **No LLM-invented geometry or Δmm.** Cited / Engineer-typed / caliper only.  
4. **Origin must be a box** today (writer + visor). Disk-origin stays named Buy or park.  
5. **Assembly root key is `frame_plate`** when boxed — do not silently pick `frame_plate_2` / body footprint as root without ★.  
6. **GEP/Rooster plate L×W** stay absent until citation or Option B caliper ★ — no invent from wheelbase/body.  
7. **One BOM identity** — visor copies/stations, not N motor specs.  
8. **Prefer ranked Buys** including **B0** and **DEFER** (data-first). Split **plate envelope** from **layout pack** from **Situar UX** (already shipping).  
9. **No Conversation Engine. No version bump. No Three.js as default Buy.**  
10. Read-only on `workspace/`.

---

## 3. Baseline to inventory (cite live tree · `file:line`)

| Surface | Check |
|---|---|
| `scene3dLayout.ts` `ASSEMBLY_ROOT_ID` / `layoutSolidsFromPose` | When root activates; what happens when `frame_plate` has no box |
| `component_writers.set_component_declared_box_pose` | Box-origin gate |
| `mounted_on_declare_assist` + Conn smoke | Which standard edges already declare |
| `_solid_copy_offsets_mm` / arm / prop / standoff stations | What “around the plate” already exists without per-piece Situar |
| Kit template / Continuity subjects | Kit holes vs spatial layout |
| Live `autonomía-15min` + `autonomía-de-5min` (read-only) | Per key: geometry · `mounted_on` · pose · plate box yes/no |
| GEP catalog row + #4g-A B0 | What plate/arm/standoff dims are honestly absent |
| Feature lock §Out | Quote auto-pose-without-citation boundary |

---

## 4. Report sections (required)

### A. Assembly-root census

Table: project · `frame_plate` geometry · root active? · consequence for Scene3D (row vs world-0).

### B. Standard drone graph vs Jarvis keys

Engineer’s list → matrix:

| Relation (Engineer) | Continuity `mounted_on` today? | Pose / station today? | Gap |
|---|---|---|---|
| prop on motor | | | |
| motor on arm | | | |
| arm on main plate | | | |
| battery / esc / fc / gps / connector / harness on/in frame | | | |

Separate `parent_key` (structure parts) from `mounted_on` (assembly relation).

### C. “By dimension” — honest math vs invention

For stack-on-plate and prop-on-motor: what offsets (if any) are **determined** by envelopes alone (e.g. half-height stacking along +Z with explicit rule ★) vs what still needs a **cited/declared** Δmm. Name any rule as a **Buy requiring Engineer ★**, never as silent default in the report recommendation without labeling it.

### D. Honest Buys (ranked)

Recommend **exactly one** as the **first** IC (or B0):

| ★ | Meaning |
|---|---|
| **`B0`** | Leave racimo; teach Continuity; Situar stays manual |
| **`B1-plate-box`** | Unlock main-plate root via **cited or Option B caliper** L×W on `frame_plate` only — no layout pack |
| **`B1-mount-standard-assist`** | Deterministic suggest Continuity phrases / mount checklist for the standard graph — **user confirms**; no auto-write mm |
| **`B1-layout-pack-cited`** | Named kit layout pack with **disclosed authority** (citation or Engineer-measured table) writing poses via **existing** writers after confirm |
| **`B1-stack-rule`** | Explicit ★ stacking rule from envelopes (e.g. center-on-plate + Z from heights) — only if evidence shows it is honest and scoped |
| **`DEFER`** | Needs plate box and/or citation before any layout Buy |

Park: LLM auto-pose · invent plate from body · Three.js · N BOM · reopening Situar experience as layout.

### E. Ordered cola after the first Buy

Short table: plate data → mounts → layout pack / stack rule → silhouette polish.

### F. Out of scope (explicit)

Invent GEP L×W · wheelbase-as-plate · Conversation Engine · Fit VERIFIED · autonomy.

### G. Engineer decision card (one page)

Symptom (“want main plate as start + standard situar”) → verdict on honesty → recommended ★ → what stays B0.

---

## 5. Non-negotiable report rules

- Cite `file:line` for root activation and writer gates.  
- Live census read-only.  
- Do not propose inventing mm.  
- Do not treat Situar experience B1 as unfinished layout — separate products.  
- End with a decision card usable for ★ without another discovery pass.

---

## 6. Done means

Report at the output path; Cursor can review; Engineer can ★ a Buy (or B0/DEFER) without re-litigating Continuity locks.
