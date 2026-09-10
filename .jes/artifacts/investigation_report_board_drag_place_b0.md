# Investigation Report — Board drag / resize → Continuity writers

**IC:** [investigation_contract_board_drag_place_b0.md](investigation_contract_board_drag_place_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-10
**Checkpoint:** package `0.4.0` · suite 2652 · tag `v0.4.0` / `checkpoint-continuity-spatial-assembly`

**Do not implement — this is a read-only report. No `src/`/`ui/`/`library/` edit made. No `workspace/` mutation. No version bump.**

---

## Executive summary

**Recommended lean: `B1` — pose-only drag, restricted to singleton solids (no `solidCopies`), via a new canonical top-down (untilted) drag mode on the existing Scene3D pane, committed through a new minimal POST bridge that calls `set_component_declared_box_pose` + `save_state` — resize deferred to a later `B1+`.**

The live tree confirms every locked stance empirically: the Board's HTTP surface is GET-only with exactly two routes (`vite-plugin-jarvis-projects.ts:131,136,143`), the 2D card drag/resize persists only to `localStorage` in a pixel-space `CanvasTransform` that has no millimetre calibration anywhere (`useBoardNodes.ts:23-29`, `transform.ts`), and Scene3D's own mouse gesture rotates the whole camera (`Scene3D.tsx:44-66`) rather than moving any individual solid — there is no drag-a-solid code path today at all, in either pane. The only existing millimetre math is one-directional (`mmToPx`, `scene3dScale.ts:14`) with no inverse anywhere in the codebase. A coherent first Buy is therefore genuinely new wiring, not a small extension — but it is boundable: singleton-only scoping avoids the one truly hard question (per-copy drag onto four shared-identity station copies, which today's own live data already shows drifting into an "orphan FR pose" honesty gap — see §C), and a top-down canonical view avoids inventing 3D ray-plane unprojection math for a tilted camera. `B0` remains fully defensible — it is the safer choice if the new mutation surface itself (breaking today's clean GET-only invariant) is judged too significant a step to fold into a "thin" IC.

---

## A. Gestures as-is

| Surface | Gesture | Units | Persistence | Engineering effect |
|---|---|---|---|---|
| 2D card (`.sb-card`, via `useNodeGestures.ts`) | Drag (mousedown→move→up, `startDrag`/`onMove`/`onUp`, `useNodeGestures.ts:42-106,113-131`) | `CanvasTransform` "world" px (`screenToWorldDelta`, `transform.ts:34-39`) — a pan/zoom pixel frame, no mm calibration (`zoom`/`panX`/`panY` only, `transform.ts:16-30`) | `localStorage`, key `${LAYOUT_KEY}.${projectId}` (`useBoardNodes.ts:8-9,23-29`, written via `commit` → `persist` at `useBoardNodes.ts:72-81`) | **None.** `SpatialRect.x/y/width/height` is explicitly documented as "the card's on-canvas pixel layout (drag/resize state) — never physical mm" (`types.ts:20-21`). Never reaches `ProjectState`. |
| 2D card (`useNodeGestures.ts:133-154`) | Resize (4 corner handles, `startResize`) | Same px world frame, clamped to `CARD.minWidth`/`minHeight` (`useNodeGestures.ts:82-83`) | Same `localStorage` overlay | **None** — same reasoning. |
| Scene3D pane (`Scene3D.tsx:44-66`) | "Drag" on background mousedown/move | CSS degrees (`rotateX`/`rotateY`, `Scene3D.tsx:49-52`) applied to the WHOLE `.sb-scene3d__world` div (`Scene3D.tsx:100-106`) | React state only (`tilt`, `Scene3D.tsx:36`) — not even `localStorage` | **None.** This is camera orbit, not solid movement — confirmed by reading the handler: it only ever calls `setTilt`, never touches any `SolidLayout`/`originX/Y/Z`, never calls `onSelect` or any writer. |
| Scene3D pane wheel (`Scene3D.tsx:68-72`) | Zoom | Unitless scale factor | React state (`zoom`) | None. |
| `Solid3D` mousedown (`Solid3D.tsx:26-29`) | Click | n/a | Calls `onSelect(id)` only — `event.stopPropagation()`, no coordinate read at all | **None** — pure selection, not movement. `id` passed is `e.selectId` (`Scene3D.tsx:113`), the shared BOM key for every station copy, not a per-copy id. |
| IDLE text (`declara … mm …`) | Typed phrase | Declared mm (Engineer-typed) | `ProjectState.components[key].declared_box_pose` / properties, via writer + `workspace_manager.save_state` (§B) | **Full** — this is the only gesture today that reaches `ProjectState`. |

No drag-a-3D-solid code path exists anywhere in `ui/spatial-board/src` — confirmed by reading every `on*Down`/`useNodeGestures`/`Scene3D` handler in the package; `grep -rn "onMouseDown\|onDrag"` across the directory turns up only the two gestures tabulated above plus `Solid3D`'s click-only handler.

---

## B. Writer + save path as-is

**How CLI `declara…` reaches disk today** (orchestrator.py):

```text
IDLE user_input
  → _try_handle_declared_box_pose / _try_handle_declared_box_envelope   (orchestrator.py:1950, 2049)
  → parse_declared_box_pose_declare / parse_declared_envelope_declare   (pure parse, no I/O)
  → component_writers.set_component_declared_box_pose / _envelope       (component_writers.py:295, 364)
      — pure function: takes ProjectState, returns a NEW ProjectState, no disk I/O itself
  → self.workspace_manager.save_state(updated_state)                    (orchestrator.py:2023, 2129)
      → write_json(Path(state.workspace_path) / "state.json", ...)      (workspace_manager.py:82-83)
```

`state.workspace_path` is a field already carried on `ProjectState` (set once at project creation, `self.root / f"{slug}-{project_id}"`, `workspace_manager.py:47`) — `save_state` needs nothing beyond the `ProjectState` object itself. There is no HTTP layer, no auth, no queue anywhere in this chain: it is synchronous, local-process Python.

**What a board commit would have to call.** The Vite dev server (`ui/spatial-board/vite-plugin-jarvis-projects.ts`) is a *separate Node process* from the Python CLI/orchestrator. Its only existing bridge into Python is one read-only `spawnSync` call to `python -m jarvis.workspace.spatial_board <state.json>` (`vite-plugin-jarvis-projects.ts:97-118`) — a one-shot subprocess that prints a JSON projection and exits. There is no in-process Python object (no live `JarvisOrchestrator`, no live `WorkspaceManager`) the Node server could call a writer on directly.

**Gaps a mutation path would have to name explicitly** (per locked stance #4 — never smuggled as "refresh"):
1. **HTTP.** The middleware itself gates on `req.method !== "GET"` and calls `next()` for anything else (`vite-plugin-jarvis-projects.ts:130-134`) — a POST handler is new code, not a flag flip.
2. **Bridge process.** A POST would need its own `spawnSync`/`spawn` into a small Python entry point that (a) loads the target `state.json` into a `ProjectState`, (b) calls `set_component_declared_box_pose`/`_envelope` directly (bypassing the full LLM-backed orchestrator entirely, since Continuity parsing/writing is already pure/deterministic and needs no LLM), (c) calls `workspace_manager.save_state` (or an equivalent direct `write_json`), (d) returns the new projected nodes so the Board can refresh without a full reload.
3. **Auth/project id.** Today's GET routes resolve `projectId` → `state.json` path via a directory-suffix scan (`statePathFor`, `vite-plugin-jarvis-projects.ts:70-80`) with no ownership check — this is fine for a local dev tool reading its own workspace, but a write path inherits the same "no auth" posture, which is worth naming rather than silently carrying over.
4. **Concurrency.** Nothing today guards against the CLI and the Board writing `state.json` at the same moment — not a new risk this Buy introduces (the CLI already has this same read-modify-write race with itself across terminals), but it becomes reachable from two different processes/languages instead of one.

---

## C. Honesty collisions

1. **Card-px drag, if wired naively, lies about units.** The 2D canvas world (`CanvasTransform`) has no `pxPerMm` anywhere — it is a pure pan/zoom presentation frame (`transform.ts`). Committing a `dx`/`dy` from `screenToWorldDelta` straight into a `declared_box_pose`'s `x_mm`/`y_mm` would silently rescale "how far the mouse moved on screen, at whatever zoom level" into "millimetres" — exactly the B2 lean's default-reject condition (§3/§4D), confirmed here by reading the code rather than assumed.
2. **Scene3D tilt, if mistaken for pose, lies about intent.** `Scene3D.tsx`'s background-drag only ever mutates `tilt.rotateX/rotateY` (camera orbit) — it has no per-solid target at all. Any future gesture that moves an *individual* solid must be a genuinely new handler on `Solid3D`, not an extension of the existing background handler, and must not consume the same mousedown that currently starts a camera orbit.
3. **Station copies vs. subject drag — the sharpest real collision.** `expandSolidCopies` (`scene3dLayout.ts:212`) turns one `solidCopies: N` node into N presentation entries sharing one `selectId` and deliberately **strips** `declaredBoxPose` on every copy. Confirmed live on `autonomía-de-5min`: `prop_adapter` and `frame_standoff` both already carry a single stale `declaredBoxPose` (an "FR-corner" pose from before their own visor-copies IC landed) *alongside* `solidCopies: 4` — the 3D visor correctly ignores that stale pose on all four rendered copies (the strip already works), but the **card's own text field still shows it** (`_fields`/`_declared_box_pose_dto` don't know about `solidCopies` at all). This means: today, a component with `solidCopies >= 2` has **no coherent single-origin pose to drag** — all four rendered copies share one `selectId`, so a click/drag on any one of them would necessarily write to the *same* `declared_box_pose`, which cannot represent "this copy is at FR, that one at FL" without a genuinely new per-copy pose mechanism (explicitly forbidden — locked stance #6, and every visor-copies IC this session: "never N sibling specs," "copies follow projector rules"). A drag Buy that ignores this will either (a) silently let the Engineer "pose" a station copy in a way that does nothing visible (stripped on render) — a dishonest gesture — or (b) require deciding this multiplicity question as part of the Buy, which is out of this investigation's scope per its own parents. **The clean way to avoid inventing that decision here is to scope any drag Buy to singleton solids only** (no `solidCopies` key present) — precisely how `frame_plate`/`frame_plate_2`/`battery`/`flight_controller`/`esc` already behave today.
4. **Origin choice is not free.** Every write still goes through `set_component_declared_box_pose`'s existing box-origin gate (`component_writers.py:330-343`) — a drag onto a disk or a shapeless part must fail exactly as `declara…` already fails, never silently pick a fallback origin. A drag UI needs an explicit origin choice (which box the Δmm is measured against) *before* the gesture can compute a delta at all — this is itself real product surface (an origin picker), not a detail to wave away.

---

## D. Buy ladder

| Lean | Verdict | Why |
|---|---|---|
| **B0 — Defer** | **Fully defensible fallback.** | Keep typing-only. The write-path (§B gaps 1-2) and the multiplicity question (§C.3) are real, non-trivial pieces of new surface — a legitimate call is "not ready for even a thin IC yet." Document reason: no HTTP mutation route exists at all today (a genuinely new architectural surface, not a flag), and the one hard product question (drag vs. station copies) has no existing precedent to lean on. |
| **B1 — Pose-only** ★ recommended | **Minimum honest first Buy.** | Drag a **singleton solid only** (no `solidCopies`) in a **new canonical top-down (untilted) Scene3D mode** — reusing the existing `mmToPx`/`layoutSolidsFromPose` math via one new inverse (`pxToMm`, trivial to derive: `mm = px / pxPerMm`, valid only when `rotateX=rotateY=0` and the existing `translate`/`scale` are the only active transforms — no perspective, no 3D unprojection needed). On drop: origin = the solid's already-declared `mounted_on`/`declared_box_pose.originKey` if present, else the drag is disabled until the Engineer picks one (name-only in §E) → `set_component_declared_box_pose` via a new minimal POST bridge (§B gap 2) → `save_state`. Resize explicitly **out** (kept for `B1+`). |
| **B1+ — Pose + envelope** | **Real, but not the first slice.** | Adds resize handles → `set_component_declared_box_envelope` for the already-allowlisted keys. Doubles the Buy's blast radius (two gesture surfaces, arguably two POST shapes) in one step — the concept note's own "suggested next step" already names this as a *second* IC ("drag solid → pose write only (resize later)"), which this investigation agrees with. |
| **B2 — Card-px → pose** | **Rejected by the IC's own default.** | The 2D card canvas has no calibrated mm plane anywhere (§A, §C.1) — confirmed by reading `transform.ts`/`useNodeGestures.ts` directly, not assumed. Per §4's own instruction ("default reject unless you prove a calibrated mm plane already exists"), this lean fails on the evidence. |

**State blast radius for B1** (if ★'d):
- New files: none required conceptually beyond a small bridge script (e.g. `src/jarvis/cli_board_bridge.py` or similar) — name only, not designed here.
- Changed files: `vite-plugin-jarvis-projects.ts` (new POST route), `Scene3D.tsx` (new canonical/top-down mode + a per-solid drag handler on `Solid3D`), `scene3dLayout.ts`/`scene3dScale.ts` (new `pxToMm`), a new fetch helper alongside `projects.ts`.
- New tests: bridge script (writer call + save, Python-side, same style as existing orchestrator tests), `pxToMm` round-trip (UI-side, mirroring `scene3dLayout.test.ts`'s existing style).
- `docs/system_map/CONNECTIONS.md`: the absence row at line 970 ("Board drag/resize → pose/envelope writers — NOT IMPLEMENTED") would need to flip to an actual `C-xxx` entry, or be narrowed to "resize" only if `B1` ships pose-only first.
- **Named out, explicitly:** snap-to-grid, an undo stack, multi-select drag, a CAD mate/auto-fit solver, flipping `"cabe"` screening to `"VERIFIED"`, and (again) any per-copy pose mechanism for `solidCopies >= 2` nodes.

---

## E. Contingency sketch (name-only — NOT an IC)

If `B1` is ★'d:

- **Gesture surface:** a new mousedown/move/up handler on `Solid3D`, gated to fire only when `node.solidCopies` is absent and Scene3D is in its new top-down mode (tilt reset to `0,0` for the duration of the drag, or a dedicated "situar" toggle that locks tilt).
- **Δmm computation vs. which origin:** the dragged solid's own already-declared origin (`declared_box_pose.originKey` if a pose already exists; otherwise the Engineer must pick one via a small origin selector before the drag is armed — never invented, never defaulted to the assembly root silently).
- **Write endpoint shape:** `POST /api/projects/:id/pose` (or similar), body `{component_key, origin_key, x_mm?, y_mm?, z_mm?}`, mirroring `set_component_declared_box_pose`'s own signature 1:1 — no new fields invented.
- **Poll/reload after save:** the existing `fetchProjectNodes` (`projects.ts:23`) re-run after a successful POST — no new polling loop needed, since the Board already re-fetches nodes on project switch.
- **Copy-select behavior:** unchanged — clicking a station copy still selects the shared card; the new drag handler simply never arms for those nodes.

---

## F. Explicit non-goals

Card-pixel-as-millimetre (B2, rejected on evidence) · per-copy pose for `solidCopies >= 2` (multiplicity mechanism, not this Buy) · resize/envelope drag (`B1+`, later) · CAD mate solver / auto-fit `"VERIFIED"` · Conversation Engine inventing drop coordinates · `standoff_count` generalist declare · plate label noun fix · sourced dims (#4) · any version bump · any `workspace/` mutation (none made — confirmed via `git status --short -- workspace/`, empty).

---

## Done-when checklist

- [x] All §4 sections present with live `file:line` citations
- [x] One executive lean (`B1`, pose-only, singleton-scoped) + one-sentence recommendation
- [x] `B0` evaluated honestly as a fully defensible fallback, not a straw man
- [x] No code, no version bump, no IC authored in this report
- [x] Engineer can ★ Buy / Defer without guessing the write path — §B and §D name every missing piece explicitly
