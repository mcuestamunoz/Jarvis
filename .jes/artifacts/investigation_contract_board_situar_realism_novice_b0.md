# Investigation Contract — Board Situar realism + novice situar path (B0)

**Project:** Jarvis  
**Date:** 2026-09-12  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_board_situar_realism_novice_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · [report](investigation_report_board_situar_realism_novice_b0.md) · [review](investigation_review_board_situar_realism_novice_b0.md) · await Engineer ★ **`B1-ux-situar`** (or **B0**)  
**Report:** [investigation_report_board_situar_realism_novice_b0.md](investigation_report_board_situar_realism_novice_b0.md)  
**Review:** [investigation_review_board_situar_realism_novice_b0.md](investigation_review_board_situar_realism_novice_b0.md)  
**Parents:**
- Feature: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md) ★ LOCKED  
- Mapping path: [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — product **A racimo** vs **B silueta**  
- Horizon: [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)  
- Progression: [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)  
- Relation rung CLOSED: [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — `mounted_on` = guide, **not** mm  
- Board drag → pose B1 **CLOSED** + ACCEPT — [IC](implementation_contract_board_drag_pose_b1.md) · smoke battery/FC/ESC **only**  
- Situar UX + free camera B1 **CLOSED** + ACCEPT — [IC UX](implementation_contract_board_situar_ux_b1.md) · [IC free-cam](implementation_contract_board_situar_free_camera_b1.md)  
- Nested-hit hotfix ACCEPT — [engineer_note_situar_nested_hit_select_card.md](engineer_note_situar_nested_hit_select_card.md)  
- Kit in space B0 CLOSED → propeller/motor copies path — [investigation quadrotor kit](investigation_contract_geometry_quadrotor_kit_in_space_b0.md)  
- Conn remaining mounts B1 CLOSED — Continuity declare, **no** auto-mount  
- Assembly kit template B1-min CLOSED — identity kit, **not** pose wizard  
- Plate L×W / #4g-A CAD **B0** — GEP-Racer part envelopes still absent unless Option B caliper  
- **Out of this investigation as auto-Buy:** HD-* · Conversation Engine · Three.js rewrite · STEP-in-core · invent Rooster/GEP plate L×W · N BOM clones · Fit VERIFIED reopen · autonomy/HD-005

**Type:** Deep **as-is vs product-need** investigation of the Spatial Board Situar surface.  
**Not** an IC. **Do not implement. Do not bump version. Do not invent millimetres. Do not mutate `workspace/`.**

**Checkpoint:** package **`0.4.1`** · suite ~**2742** · UI ~**83** · tag `v0.4.1` / `checkpoint-board-situar`

**Live smoke that triggered this (Engineer 2026-09-12 — `autonomía 15min` Board):**

```text
Situar: ON
· origin picker ("Fijar origen") required before drag; options feel
  unrelated to the selected component
· only ~3 solids "respond" to situar; rest ignore drag
· after fixing origin + dragging near another solid, the OTHER piece
  appears to jump far away
· overall: does not look like a drone; novice cannot know what mounts
  on what or where to place in mm
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → Board feels FATAL; wants realistic situar + novice path
Cursor    → this contract; review; IC only after ★ on Buy shape(s)
Claude    → investigation_report_board_situar_realism_novice_b0.md
```

---

## 1. Why this exists

Continuity spatial assembly is **shipped** as a feature: envelopes + `mounted_on` (guide) + `declared_box_pose` + Scene3D-from-pose + Situar drag → **same writers**. Expert walks on other projects (e.g. 5min/10min) can type Continuity poses and get a racimo.

The Engineer’s live 15min Board walk says the **product surface still fails** for the intended user:

1. **Broken / hostile UX** — origin picker, non-responsive solids, “other piece flies away”.  
2. **Not a drone** — exploded row / racimo ≠ readable airframe.  
3. **Novice gap** — `montado en` and Δmm were typed by someone who already knew the stack; a new user does not.

Wrong next step:

```text
· LLM invents poses / mounts / plate L×W
· Treat card localStorage x/y as millimetres
· Silent auto-mount from BOM co-membership
· Treat mounted_on as pose (mm)
· Three.js rewrite “because CSS 3D looks bad”
· N BOM motors so each disk can drag
· Rename situar ACCEPT smokes and claim done
· One mega-IC that mixes UX hotfix + silhouette + novice wizard
```

Right questions (all must be answered with evidence):

> **Q1 (broken vs honesty):** On the live tree, which Engineer symptoms are **bugs / UX defects** in shipped Situar, and which are **honest product limits** (singleton-only drag, box-only origin, copies strip pose, no frame prism, cluster chrome)?  
> **Q2 (realistic representation):** What does the Board need — minimum — to **look like** a quadrotor assembly without lying (product B silhouette vs A racimo)? What is still blocked by missing Class A envelopes (GEP plates/arms)?  
> **Q3 (Jarvis situates all):** How can Jarvis help situate **every** geometry-bearing identity (including motors/props with copies, frame parts, kit)? What already exists vs what is missing?  
> **Q4 (novice):** How does a novice learn / declare `mounted_on` and pose without being an Engineer who already walked Continuity? What Buys are honest (assist, kit defaults, cited layout packs) vs forbidden (invent mm)?

---

## 2. Locked stances

1. **ProjectState remains SoT.** Board is a visor + narrow mutation (C-113 pose POST). No parallel pose schema in the UI.  
2. **Same writers.** Pose/envelope/mount still go through Continuity writers (`set_component_declared_box_pose`, envelope, `set_component_mounted_on`).  
3. **`mounted_on` ≠ millimetres.** Relation is guide only; pose is separate. Do not collapse them.  
4. **No LLM-invented geometry or Δmm.** Cited / Engineer-typed / caliper only.  
5. **One BOM identity.** Visor copies ≠ N `ComponentSpec`. Do not recommend splitting motors/props into four BOM rows to “fix” drag.  
6. **Origin must be a box** today (writer + `layoutSolidsFromPose`). Disk-origin is a **named Buy or park**, not a silent loosen.  
7. **Assembly root** is `frame_plate` box at world 0 when present — do not invent a different silent root.  
8. **GEP / Rooster plate L×W** stay absent unless citation or Option B caliper — no invent prism for “looks like a frame.”  
9. **Disk stays disk.** No cylinder from Ø+height.  
10. **Prefer ranked Buys**, including **B0 leave gap**, and **split** UX-defect Buys from silhouette / novice Buys. Do not force one IC.  
11. **No Conversation Engine. No version bump in the investigation. No Three.js as the default Buy** — only if CSS 3D is proven unable to express a named, evidence-backed need.  
12. Read-only on `workspace/` — census only.

---

## 3. Baseline to inventory (cite live tree · `file:line`)

### 3.1 Situar / drag surface (smoke → code)

| Surface | Check |
|---|---|
| `ui/spatial-board/src/Scene3D.tsx` | Situar toggle; origin picker; `boxOriginCandidates`; when drag arms; nested-hit pane drag; hint copy |
| `ui/spatial-board/src/boardPoseDrag.ts` | `isDraggableSolid` (`solidCopies >= 2` gate); screen→mm; axes |
| `ui/spatial-board/src/Solid3D.tsx` | hit / select / drag start |
| `ui/spatial-board/src/scene3dLayout.ts` | `layoutSolidsRow` vs `layoutSolidsFromPose`; assembly root; multi-hop; **`clusterCenterPx` recentering** (candidate for “other jumps away”) |
| `ui/spatial-board/src/SpatialCard.tsx` + `useNodeGestures.ts` | 2D: grip-only drag vs body select (click-inspect lock) — separate from 3D situar but part of “board feels broken” |
| Vite plugin / `projects.ts` | POST pose path; error surfacing |
| Python bridge / `set_component_declared_box_pose` | Origin box gate; refuse messages |

### 3.2 What can appear / move on 15min

| Surface | Check |
|---|---|
| Live project `workspace/autonomía-15min-*/**/state.json` (read-only) | Per key: geometry yes/no · envelope source · `mounted_on` · `declared_box_pose` · `solidCopies` / offsets · frame parts |
| Projector `spatial_board.py` | Which keys become nodes; which get `geometry`; pose DTO omit rules |
| Catalog / sourced #4* stack | Which 15min SKUs have Class A boxes/disks vs declarative-only (harness, connector, mute plates) |

### 3.3 Product docs / prior Buys (do not re-litigate closed smokes; **map** them)

| Surface | Check |
|---|---|
| Continuity spatial assembly feature lock | In/out; “auto-pose without citation” OUT |
| Mapping path A vs B | What “realistic drone” means in locked vocabulary |
| Kit-in-space + motor/prop copies ICs | Why N disks exist but are **not** situar-draggable |
| Conn / Continuity mount assist | Phrases a novice can type today |
| Assembly kit template | What it does **not** situate |
| Engineer smokes (drag pose, situar UX, free-cam, nested-hit) | What was ACCEPT vs still scoped to battery/FC/ESC |

Do **not** mutate workspace. Optional: count posed vs unposed solids on 15min vs a previously walked 5min/10min demo for contrast.

---

## 4. Report sections (required)

### A. Symptom → classification matrix

For each Engineer symptom, classify as **BUG** (shipped behavior contradicts its own IC/smoke), **UX DEFECT** (allowed by locks but hostile), **HONEST LIMIT** (documented gate), or **MISSING CAPABILITY** (needs new ★ Buy). Cite code.

Must cover at least:

| Symptom | |
|---|---|
| Origin picker required + “Fijar origen” | |
| Origin options “don’t match” the component | |
| Only ~3 solids respond | |
| Other solid jumps far when dragging near it | |
| Scene does not look like a drone | |
| Novice does not know mounts / mm | |

### B. As-is situar census (15min + contrast)

Table: component key · has geometry · shape · copies · draggable? · has pose · has `mounted_on` · can be origin? · notes.

Name the exact set of situar-eligible identities and why motors/props/arms fail the gate.

### C. Why “near another component” can displace it

Evidence-backed mechanisms (pick what the tree proves):

- `clusterCenterPx` world recentering when bbox changes  
- Pose chain / multi-hop when origin is wrong or still on row slot  
- Preview vs commit mismatch  
- Selecting/dragging the wrong identity under nested-hit rules  
- Something else (prove it)

Separate **visual camera/cluster chrome** from **persisted pose mutation of a second key**.

### D. Realistic drone representation — needs vs lies

Answer in locked vocabulary (A racimo / B silueta):

1. What **minimum** additional facts (envelopes, stations, root plate box, arm X, …) are required for a readable airframe on **this** 15min stack (GEP-Racer)?  
2. What is blocked by **honest absence** (no plate L×W) vs what is blocked by **visor policy** (row, copies strip pose)?  
3. Ranked silhouette Buys — include **B0** “racimo is the product for now.”

### E. “Jarvis situates all components” — capability map

For each geometry-bearing family (box singleton, disk copies, frame parts, kit-without-geometry):

| Need | Exists today? | Gap type |
|---|---|---|
| Appear as solid | | |
| Select from card | | |
| Situar-drag | | |
| Persist pose | | |
| Default/suggested placement | | |

Recommend **how** “all” can be approached without N BOM clones and without inventing mm. Prefer deterministic assists + cited layout packs + Continuity grammar over a wizard personality.

### F. Novice path (mounted_on + pose)

1. What a novice can already do **today** with Continuity phrases (cite assist nouns).  
2. What the Board could honestly add without inventing (e.g. suggest **candidate origins** = boxes that are `mounted_on` targets / assembly root; never silent write).  
3. What must stay Engineer/citation (Δmm magnitudes, plate footprints).  
4. Ranked Buys for novice — include **B0** “Board stays expert situar; CLI Continuity remains the path.”

### G. Recommended Buy sequence (Engineer ★ menu)

Recommend **exactly one first IC** if any code is needed for the FATAL smoke, **plus** a short ordered cola for realism/novice. Allowed stars:

| ★ | Meaning |
|---|---|
| **`B0`** | No code — document honesty; expert Continuity only |
| **`B1-ux-situar`** | Thin UX/hotfix only (picker labels, cluster behavior, copy, eligibility affordances) — **no** new pose semantics |
| **`B1-origin-assist`** | Origin picker / Situar suggests targets from declared `mounted_on` + box roots — still user confirms; no silent pose |
| **`B1-copy-situar`** | Named mechanism so N-copy identities can be placed/stations without N BOM (only if evidence demands; may be B0 park) |
| **`B1-silhouette`** | Visor layout toward product B without inventing envelopes |
| **`B1-novice-pack`** | Deterministic cited/default **layout pack** for a known kit (must say citation authority) — or park as forbidden without citation |
| **`DEFER`** | Needs plate L×W / caliper / HD before any silhouette Buy |

Park explicitly: Conversation Engine · auto-pose from LLM · Three.js rewrite · Fit VERIFIED · autonomy.

### H. Out of scope (explicit)

Invent GEP plate L×W · disk AABB `"cabe"` · ASSEMBLY_READY from situar · weakening tests · reopening closed ACCEPT smokes as “failed” without new evidence · merging this into #4 sourced dims.

---

## 5. Non-negotiable report rules

- Cite `file:line` for every classification in §A and every mechanism in §C.  
- Do not propose inventing millimetres or mounts.  
- Do not treat prior Situar ACCEPT as proof the 15min novice walk is fine — reconcile **scoped smoke (battery/FC/ESC)** with **current FATAL**.  
- Prefer smallest first Buy that removes FATAL confusion; realism/novice may be cola.  
- End with a one-page **Engineer decision card**: symptom verdicts + recommended ★ + what stays B0.

---

## 6. Done means

Report exists at the output path; Cursor can review PASS/FAIL WITH NOTES; Engineer can ★ a Buy shape (or B0) without another discovery pass.
