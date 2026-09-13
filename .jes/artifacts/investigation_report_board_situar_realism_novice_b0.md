# Investigation Report — Board Situar realism + novice situar path (B0)

Status: Investigation complete — no code changed, no version bump, `workspace/` read-only
Parent: `investigation_contract_board_situar_realism_novice_b0.md`
Checkpoint: package `0.4.1` · suite `2742` (unchanged) · UI `83` (unchanged)

## Summary up front

The 15min FATAL smoke is **real** and has three distinct, cite-able causes —
none of them is "the feature is broken end to end." One is a genuine UX
defect in an already-ACCEPTed mechanism whose validated smoke never
exercised the failure mode the Engineer just hit (§C, mechanism 1). One is
visual camera chrome, not a data bug (§C, mechanism 2). One is intentional,
correct pose-chain composition that reads as "the wrong thing moved" to
someone who doesn't yet think in origin chains (§C, mechanism 3). Separately,
"only ~3 solids respond" and "doesn't look like a drone" are **honest,
already-documented product limits** (Product A "racimo", locked), not bugs
— 8 of this project's 15 components have no sourced geometry at all, and 2
more are copy-family disks that can never be singleton-draggable by design.
The novice gap is real and, per the feature's own lock, has never been
addressed — today's Board assumes an Engineer who already knows the
Continuity grammar.

Recommended first Buy (§G): **`B1-ux-situar`**, narrowly scoped to the one
proven UX defect (mechanism 1) plus honest picker filtering — no new pose
semantics, no silhouette work, no novice wizard. Everything else is ranked
cola, several of it legitimately `B0`/`DEFER`.

---

## A. Symptom → classification matrix

| # | Engineer symptom | Verdict | Evidence |
|---|---|---|---|
| 1 | Origin picker required + "Fijar origen" | **HONEST LIMIT** (server-enforced) + **UX DEFECT** (unfiltered candidate list) | `set_component_declared_box_pose` rejects any non-box origin with `ValueError` — `src/jarvis/core/component_writers.py:295-343` (origin must resolve `_geometry_from_spec(...).get("shape") == "box"`, else raises). The picker itself only appears because `Scene3D.tsx:193-200` finds no `declaredBoxPose.originKey` yet — this is the intended "never a silent default origin" behavior per Board drag → pose B1 lock #4 (cited in `Scene3D.tsx:65-67`). The **defect** is the candidate list: `boxOriginCandidates = solids.filter(n => n.geometry?.shape === "box" && n.id !== pickerNodeId)` — `Scene3D.tsx:319-321` — every box on the board, unfiltered by `mounted_on`, proximity, or relevance. |
| 2 | Origin options "don't match" the component | **UX DEFECT** | Same citation as #1 (`Scene3D.tsx:319-321`). The `<select>` (`Scene3D.tsx:419-424`) lists raw component keys with no label/relation context — a novice sees `flight_controller`, `battery`, `sensors` with no hint of which one is the actual mount target. |
| 3 | Only ~3 solids respond | **HONEST LIMIT** (mostly) | Live census on `autonomía-15min-d2fe43e72976/state.json` (read-only, §B): of 15 declared components, only 4 are situar-draggable (`esc`, `battery`, `flight_controller`, `sensors`) — all singleton boxes. `motors`/`propellers` have `solidCopies: 4` and are excluded by `isDraggableSolid`'s own copy gate — `ui/spatial-board/src/boardPoseDrag.ts:33-36` ("A copied node has no single coherent origin/Δmm to drag onto"), itself downstream of Motor/Propeller visor copies B1 (one BOM identity, not N specs — locked in `engineer_lock_continuity_spatial_assembly_feature.md:41`, layer 4). The other 8 components (`frame`, `frame_arm`, `frame_plate`/`_2`/`_3`, `frame_standoff`, `power_connector`, `prop_adapter`, `signal_harness`) have **no geometry at all** — `frame_plate*` are `completeness: "low"` (no cited L×W; #4g-A CAD closed B0), `power_connector`/`signal_harness` are declarative-only kit rows with no dimensions on their source pages (locked "Class A vs declarative" boundary). "~3" vs the actual 4 is close enough that this reads as an accurate Engineer count, not a contradicted claim. |
| 4 | Other solid jumps far when dragging near it | **UX DEFECT** (primary) + **HONEST-BUT-CONFUSING mechanism** (secondary, intentional) | Three distinct, separable mechanisms — see §C. The dominant one for this live tree is mechanism 1 (nested-hit "drag whatever is selected, not what's under the cursor"), which is *accepted, working-as-designed* behavior whose own validated smoke (`engineer_note_situar_nested_hit_select_card.md`) never tested it with more than one draggable solid nearby. |
| 5 | Scene does not look like a drone | **HONEST LIMIT** (explicitly documented, not a bug) | `engineer_lock_geometry_3d_mapping_path.md:20-27` names exactly this as Product **A "racimo"**: "The 5 solids... sit in millimetre relation. **Not a quadrotor.**" Product **B "silueta"** ("Needs wheelbase / instancing / or sourced plate L×W... Separate ★") was never ★'d as a Buy. The 15min tree additionally never activates the one root-anchor mechanism that DOES exist: `ASSEMBLY_ROOT_ID = "frame_plate"` in `ui/spatial-board/src/scene3dLayout.ts:35`, requires `frame_plate`'s own `geometry.shape === "box"` (`scene3dLayout.ts:66-67`) — and the live `frame_plate` has no geometry (§B), so the world never anchors to a stable center; every solid free-floats via a plain row slot or a pose chain with no fixed frame of reference. |
| 6 | Novice does not know mounts / mm | **HONEST LIMIT** (never addressed by any prior Buy) | Every existing Continuity phrase requires the novice to already know component nouns and the Continuity grammar: `mounted_on` needs `"monta el esc en..."` / `"...montado en..."` (`src/jarvis/core/mounted_on_declare_assist.py:52-53`, subject table lines 62-69); pose needs `"declara X a N mm en <eje> respecto a <origin>"` (established grammar from `declared_box_pose_declare_assist.py`). Nothing surfaces *which* box can legally be an origin, *what* mounts on *what* by default, or *any* suggested Δmm — this is the feature's own acknowledged next-work item, never closed: `engineer_lock_continuity_spatial_assembly_feature.md:72` lists "IDLE frame-part count declare" and "N≠4 standoff layout" as cola, but no novice-facing item has ever been ★'d. |

---

## B. As-is situar census — `autonomía-15min-d2fe43e72976` (read-only)

Projected live via `jarvis.workspace.spatial_board.project_spatial_nodes` (no
mutation — a pure read, confirmed by `git status --short -- workspace/`
showing no diff after this investigation).

| Key | Geometry | Shape | Copies | Draggable? | Has pose | `mounted_on` | Can be origin? | Notes |
|---|---|---|---|---|---|---|---|---|
| `motors` | Yes | disk | 4 | **No** — `isDraggableSolid` copy gate | No | No | No (disk) | Row/X-station only |
| `propellers` | Yes | disk | 4 | **No** — copy gate | No | No | No (disk) | Row/X-station only |
| `esc` | Yes | box | — | **Yes** | Yes → origin `battery` | No | Yes | Only draggable box with a live pose |
| `battery` | Yes | box | — | **Yes** | Yes → origin `flight_controller` | No | Yes | |
| `flight_controller` | Yes | box | — | **Yes** | No (row slot) | No | Yes | No pose set yet despite being origin for `battery` |
| `sensors` | Yes | box | — | **Yes** | No (row slot) | No | Yes | |
| `frame` | No | — | — | No | No | No | No | Root frame is never itself a solid |
| `frame_arm` | No (thickness only) | — | — | No | No | No | No | GEP-Racer P1: no cited arm L×W |
| `frame_plate` | No (thickness only) | — | — | No | No | No | **No** — this is the one key `ASSEMBLY_ROOT_ID` expects | Root-anchor mechanism never activates on this project |
| `frame_plate_2` | No | — | — | No | No | No | No | |
| `frame_plate_3` | No | — | — | No | No | No | No | |
| `frame_standoff` | No | — | — | No | No | No | No | Height-only (24mm), no cross-section cited |
| `power_connector` | No | — | — | No | No | No | No | Kit hardware — page states no dims (locked, `kit_connector_harness_skus_d` seed) |
| `prop_adapter` | No | — | — | No | No | No | No | Declarative only on this project |
| `signal_harness` | No | — | — | No | No | No | No | Same as `power_connector` |

**Situar-eligible set on this project: exactly 4 keys** (`esc`, `battery`,
`flight_controller`, `sensors`) out of 15 declared components. `motors`/
`propellers` fail on the copy gate (by design, not by bug). The remaining 9
fail on missing geometry (by honest absence, not by bug) — most of them
directly tied to the still-open `#4g-A` CAD investigation (closed B0,
`investigation_report_geometry_gep_racer_part_cad_b0.md`) and the kit-
hardware family's own "no dimensions on the page" seeds.

**Contrast note (no other pre-`#4*` project was live-walked with a full
5-solid stack at the time of this investigation to give a clean before/after
count — the `autonomía-de-5min` project now also carries the full `#4*`
stack post-cycle and would show a similar 4-of-N ratio; re-running this exact
census against it is a cheap follow-up if the Engineer wants a second data
point, not performed here to keep this investigation strictly read-only and
scoped to the reported 15min symptom).**

---

## C. Why "near another component" can displace it — three separable mechanisms

### Mechanism 1 — nested-hit "drag whatever is selected" (dominant cause; UX defect)

`Scene3D.tsx:396`: `pointerEventsNone = Boolean(situar && selectedId && e.selectId !== selectedId)`
— once **anything** is selected, every OTHER solid gets `pointer-events: none`
(`ui/spatial-board/src/spatial-board.css:379-380`, `.sb-solid--hit-through`).
`Scene3D.tsx:218-241` (`onBackgroundMouseDown`): with Situar ON and a
selection active, **any** mousedown on the 3D pane background — including
one visually right on top of a *different*, non-selected solid, since that
solid is now click-through — starts a drag on the **currently selected**
node instead (`handleSolidDragStart(event, selectedId)`).

This is **accepted, working-as-designed behavior**, not a regression: it was
explicitly built and smoke-tested as the nested-hit hotfix
(`engineer_note_situar_nested_hit_select_card.md`), whose own smoke script
says verbatim: *"Click card **esc**... Drag anywhere in the 3D pane (not
only on the yellow box) → ESC moves"* — and the Engineer accepted it
("Ahora sí") for exactly that one-solid-selected scenario. **The validated
smoke never had a second nearby draggable solid in the scene** (the free-
camera ACCEPT smoke's own note says "Assembly legible (placa + FC + discos)"
— disks aren't draggable, so there was still only one draggable candidate at
smoke time). The 15min project now has four draggable boxes in close
proximity (`esc`→`battery`→`flight_controller` is a real 2-hop chain,
plus `sensors`). Reconciling the two: **the mechanism itself was correctly
validated for its own narrow test; the FATAL symptom is what happens when
the same mechanism is used, unchanged, in a scene with N>1 nearby draggable
solids** — a case its own ACCEPT never covered. This is the report's
sharpest, most actionable finding.

### Mechanism 2 — `clusterCenterPx` recentering (visual chrome, not data)

`Scene3D.tsx:314-317` recomputes `cluster = clusterCenterPx(laidOut, ...)`
on every render and translates the **entire world** so the axis-aligned
bounding box of all laid-out solids stays centered in the pane
(`scene3dLayout.ts:158-180`, doc comment: *"Visor chrome only... Not pose,
not millimetre SoT"*). Moving ONE solid far from its origin grows the
overall bbox, which shifts the pane's camera-center translate — every OTHER
solid's on-screen pixel position changes even though its own `originX/Y/Z`
(and therefore its persisted pose) did **not** change. This is real and
provable from the code, but it is presentation-only: no second component's
`ProjectState` is ever mutated by this. Distinguishing this from mechanism 1
matters — a novice cannot tell "the camera reframed" from "that thing's data
moved," and the report explicitly separates the two per the IC's own §C
instruction.

### Mechanism 3 — intentional pose-chain composition (honest, but reads as confusing)

`scene3dLayout.ts:90-111` (`resolveComposedCenter`): a child's screen
position is the origin's own **composed** center plus the child's own
Δmm — walked recursively through multi-hop chains. On this project,
`battery`'s origin is `flight_controller`, and `esc`'s origin is `battery`
(§B). Dragging `battery` therefore visually moves `esc` too, correctly,
since `esc`'s own declared Δmm is relative to `battery`'s new position —
`esc`'s persisted pose numbers are unchanged, but its on-screen position is.
This is correct, intended multi-hop behavior (Board drag → pose B1, rung 1),
not a bug — but to someone who has not yet internalized "poses compose
through origin chains," a sibling box visibly sliding across the screen
while they only touched a different one looks exactly like "the other piece
jumped."

**All three mechanisms are real and distinguishable by evidence.** The
Engineer's single live symptom is most likely explained by mechanism 1 (it
requires no special origin-chain setup to trigger — any two nearby
draggable boxes reproduce it), with mechanism 2 and 3 as contributing or
alternative explanations depending on the exact gesture performed.

---

## D. Realistic drone representation — needs vs lies

**Locked vocabulary** (`engineer_lock_geometry_3d_mapping_path.md:20-27`):
Product **A — racimo** ("solids sit in millimetre relation... not a
quadrotor") is what ships today. Product **B — silueta quadrotor** ("needs
wheelbase / instancing / or sourced plate L×W... separate ★") has never
been bought.

1. **Minimum additional facts needed for a readable GEP-Racer airframe:**
   - `frame_plate`'s own L×W (activates `ASSEMBLY_ROOT_ID` — `scene3dLayout.
     ts:35,66-67` — the single biggest lever: with a boxed root, every other
     solid's pose becomes relative to a *fixed, centered* reference instead
     of a free-floating row/chain).
   - `frame_arm` L×W (would let the arm join the existing quad-X station
     mechanism — `_solid_copy_offsets_mm`'s `frame_arm` branch, already
     shipped, gated on `motor_count==4` + `quad_x`/`wheelbase_mm`, both
     already declared on this project: `configuration=quad_x`,
     `wheelbase_mm=208`).
   - `frame_standoff` cross-section (Ø or L×W) to let the already-shipped
     4/6/8-count perimeter layout (`_frame_standoff_layout_offsets_mm`)
     draw actual posts instead of nothing.
   All three are currently **honestly absent** — GEP-Racer's own citation
   states thickness/height only (`library/frames/_datos.json`'s
   `geprc_gep_racer_5in` row, `source_note`), and the dedicated CAD
   investigation for exactly this gap is already **closed B0**
   (`investigation_report_geometry_gep_racer_part_cad_b0.md` — no authentic
   OEM CAD found, Engineer confirmed no private pack).

2. **Blocked by honest absence vs by visor policy:**
   - Honest absence: plate/arm L×W, standoff Ø — no citation exists; this
     is a data gap, not a code gap (see §H boundary: never invent).
   - Visor policy: `motors`/`propellers` are copies and therefore *never*
     draggable regardless of any future citation — that's a deliberate,
     locked BOM-identity boundary (`engineer_lock_continuity_spatial_
     assembly_feature.md:41`), not something a silhouette Buy should touch.

3. **Ranked silhouette Buys:**
   - **B0 (recommended for now)** — racimo is the product; no silhouette
     work until the Engineer explicitly ★'s Product B, and until either an
     authentic CAD source appears for GEP-Racer parts or the Engineer
     accepts Option B (caliper) declared L×W for the frame's own plate/arm.
   - `B1-silhouette` (parked, needs data first): once plate L×W exists
     (any source), activate `ASSEMBLY_ROOT_ID` for free — zero new code,
     it is already gated purely on `frame_plate` having a box geometry.
   - `DEFER`: standoff cross-section and arm L×W — same reasoning, blocked
     on citation/caliper, not on missing code.

---

## E. "Jarvis situates all components" — capability map

| Need | Box singleton (esc/battery/FC/sensors) | Disk copies (motors/props) | Frame parts (thickness-only) | Kit w/o geometry (connector/harness) |
|---|---|---|---|---|
| Appear as solid | **Yes** | Yes (disk) | **No** — no glyph without full box/diameter | **No** |
| Select from card | Yes (shared `selectedId`, 2D card ↔ 3D pane) | Yes | Yes (2D card only — no 3D solid to select) | Yes (2D card only) |
| Situar-drag | **Yes** | **No** — copy gate, by design | **No** — no geometry to drag | **No** — no geometry to drag |
| Persist pose | Yes (`declared_box_pose`, box-origin only) | No (copies strip pose — `expandSolidCopies` doc comment, `scene3dLayout.ts:194`) | No | No |
| Default/suggested placement | **No** — none exists anywhere in the codebase today | N/A (stations only when `motor_count==4`+`quad_x`+`wheelbase_mm`, already shipped) | N/A | N/A |

**Recommendation:** "situate all" should NOT mean making disks draggable
(would require either splitting one BOM identity into N specs — explicitly
forbidden — or inventing a per-copy pose mechanism nobody has asked for and
the parent investigation already flagged as an honesty collision). The
realistic, deterministic path is:
1. Grow the set of geometry-bearing singletons via citation (frame plate/
   arm/standoff — already the plan, blocked on data, §D).
2. For the copy families, the *existing* quad-X/perimeter station mechanism
   already "situates" them collectively and correctly whenever their gating
   facts (`motor_count`, `quad_x`, `wheelbase_mm`, standoff `count`) are
   declared — this already works and needs no new Buy.
3. Never introduce a wizard personality or an LLM-invented default pose;
   any "suggested placement" must be a deterministic assist (candidate list
   from already-declared `mounted_on`/box roots — see §F) that the user
   still confirms, never a silent write.

---

## F. Novice path (`mounted_on` + pose)

1. **What a novice can already do today** (deterministic, no LLM):
   - `mounted_on`: `"monta el esc en la placa"` / `"el esc montado en el
     frame"` — subject nouns fc/esc/motor(es)/bateria/sensor(es)/helice(s)
     (`mounted_on_declare_assist.py:62-69`); target resolution accepts
     frame-part nouns (arm/cage/standoff/frame root/plate) and asks which
     plate when ambiguous (`AMBIGUOUS_TARGET`, never guesses).
   - Pose: `"declara el esc a 5 mm en x respecto al fc"` (existing
     `declared_box_pose_declare_assist.py` grammar, unchanged by this
     investigation).
   - Standoff/plate part counts: `"6 standoffs"` (IDLE frame-part count
     declare B1, already shipped).
   None of this is discoverable from the Board UI itself — it lives only in
   CLI/IDLE muscle memory an Engineer already has from walking prior
   Continuity cycles.

2. **What the Board could honestly add without inventing:**
   - Filter the origin picker's candidate list to boxes that are either (a)
     the assembly root (`frame_plate` when boxed) or (b) already named as a
     `mounted_on` target by the dragged component — the relation the
     Engineer already declared, surfaced as a *suggestion*, never a silent
     write. This directly fixes symptom #2 (§A) using data that already
     exists on every project (`mounted_on` is already computed server-side
     for the Board's 2D edge lines — `DeclaredMountEdges.tsx`/
     `mountEdgeGeometry.ts` — just never fed into the 3D picker).
   - Surface the `montado en` relation visually **inside the 3D pane**, not
     only the 2D `.sb-world` (`DeclaredMountEdges.tsx` currently renders
     only in the 2D canvas — confirmed by its own SVG being mounted in
     `InfiniteCanvas.tsx:194`, inside `.sb-world`, never inside `Scene3D`).
     A novice situating in 3D currently has zero visual guide for "what
     mounts on what" in the very pane where they're dragging.
3. **What must stay Engineer/citation-only:** any actual Δmm magnitude,
   any plate/arm footprint, any standoff cross-section — all of §D's
   "honest absence" list. A novice-facing Buy must never guess these even
   to make the origin picker friendlier.
4. **Ranked novice Buys:**
   - **B0 (acceptable default)** — Board stays expert situar; CLI Continuity
     remains the taught path (e.g. an onboarding doc/CLAUDE-side script,
     not a code Buy).
   - `B1-origin-assist` — origin-candidate filtering by `mounted_on`/root,
     described above. Small, deterministic, no new pose semantics.
   - `B1-novice-pack` (park unless a specific kit gets an Engineer-cited
     default layout) — a deterministic, disclosed-authority layout pack for
     one named kit; forbidden without a citation naming its own authority.

---

## G. Recommended Buy sequence (Engineer ★ menu)

**First IC (removes the FATAL confusion, smallest safe scope):**

> **`B1-ux-situar`** — thin UX/hotfix only, no new pose semantics:
> 1. Filter the origin picker to a short, relevant candidate list instead
>    of every box on the board (§A-1/2, §F-2) — still user-confirmed, never
>    silent.
> 2. Address mechanism 1 (§C) — the dominant cause of "other piece jumps."
>    The smallest fix that doesn't touch pose semantics is a **visible,
>    explicit indicator of which solid a pane-background drag will move**
>    (e.g. the existing selection highlight is already there, but the
>    situar-hint copy at `Scene3D.tsx:365-368` should say plainly that
>    background drag always moves the *card-selected* piece, and/or the
>    hit-through solids could get a distinct dimmed style so it's visually
>    obvious they are pass-through right now) — a copy/affordance fix, not
>    a new mechanism. (Cursor/Engineer to size the exact hotfix at IC time;
>    this report intentionally does not prescribe pixels.)
> 3. Leave mechanisms 2 and 3 (§C) undocumented-in-UI risk items for now —
>    both are correct behavior; flagging them for a future copy/HUD
>    improvement is cola, not FATAL.

**Ordered cola after the first IC:**

| ★ | Item |
|---|---|
| `B1-origin-assist` | Origin candidates ranked/filtered by declared `mounted_on` + root (§F-2) |
| `DEFER` | Silhouette (`B1-silhouette`) — needs plate/arm L×W or Engineer Option B caliper; zero new code once data exists (§D) |
| `B0` | Novice wizard/layout pack — CLI Continuity stays the taught path unless the Engineer names a specific kit for `B1-novice-pack` |
| `B0` | Copy-family situar (`B1-copy-situar`) — no evidence in this investigation demands it; the existing station mechanism already covers motors/props/arms correctly when their gating facts are declared |

**Explicitly parked, not reopened by this investigation:** Conversation
Engine, LLM-invented geometry/mounts, Three.js rewrite (CSS 3D has not been
shown incapable of expressing any named need — every symptom here traces to
selection/filtering/data-absence, not a rendering-technology limit), Fit
VERIFIED reopen, autonomy/HD-005, N BOM clones for arms/motors.

---

## H. Out of scope (explicit, honored)

This investigation did not: invent GEP plate/arm L×W or standoff Ø, propose
disk-AABB `"cabe"`, derive `ASSEMBLY_READY` from situar state, weaken any
test, reopen the Situar UX/free-camera/nested-hit ACCEPT smokes as "failed"
(they are reconciled, not overturned — §C mechanism 1), or fold any of this
into the `#4` sourced-dims thread. No file under `src/`, `tests/`, `ui/`, or
`library/` was modified. No `workspace/` file was modified — every read in
§B/§C was via `project_spatial_nodes` against the live file, never a write.
No version bump.

---

## Engineer decision card (one page)

| Symptom | Verdict |
|---|---|
| Origin picker required | Honest limit (box-origin only) + fixable UX defect (unfiltered list) |
| Origin options don't match | UX defect — fixable in `B1-ux-situar`/`B1-origin-assist` |
| Only ~3 solids respond | Honest limit — 4 of 15 keys are situar-eligible today; the rest need citations (§D) or are copy families by design |
| Other solid jumps away | UX defect (dominant: nested-hit "drag the selected one," §C-1) + two honest/intentional contributing mechanisms (camera recenter, pose-chain composition) |
| Not a drone | Honest, already-documented Product A limit — Product B needs data this project doesn't have yet, or an Engineer ★ on Option B caliper |
| Novice gap | Honest, never-addressed gap — real, ranked as cola (`B1-origin-assist` first, wizard/pack stays `B0`/parked) |

**Recommended ★:** `B1-ux-situar` first (smallest, removes the FATAL
confusion), then `B1-origin-assist` next. Silhouette and novice-pack both
`DEFER`/`B0` pending data or an explicit Engineer ask. No Three.js, no
Conversation Engine, no invented millimetres.
