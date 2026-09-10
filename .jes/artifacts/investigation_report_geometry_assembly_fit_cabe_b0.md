# Investigation Report — `"cabe"` / fit vs spatial situation (mapping rung 5)

**IC:** [investigation_contract_geometry_assembly_fit_cabe_b0.md](investigation_contract_geometry_assembly_fit_cabe_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint:** package `0.3.8` · suite 2532

**Do not implement — this is a read-only report. No `src/`/`ui/`/`library/` edit made. No `workspace/` mutation.**

---

## Executive summary

The live tree has exactly **one** identity pair with a declared box-local pose at all: `esc` (a real 50×21.6×12mm box, catalog-bound to `hobbywing_xrotor_40a_6s`) posed relative to `flight_controller` (a real 44×84×12mm box, freeform-declared "pixhawk_4") on `autonomía-de-10min` — confirmed by reading the live `state.json` directly, not assumed. That pose is **deliberately incomplete**: only `x_mm=5.0` is declared; `y_mm`/`z_mm` are absent (both from the raw JSON and from the projected `declaredBoxPose` DTO the Board actually receives — confirmed by running `project_spatial_nodes` against the live file). `autonomía-de-5min` has **zero** poses at all. The Rooster frame (`armattan_rooster_5in`) still has no box on either project, confirming Plate L×W B0 holds. This means: a "compare" mechanic exercised against the live tree today would, correctly and by design, produce **zero** screening facts — only an honest "pose incomplete, no screening possible" outcome on the one real pair. That is not a bug to fix with an invented `y_mm`/`z_mm`; it is exactly what fail-closed honesty requires. Given a real (if incomplete) pair already exists, the gap is closeable by the same user through the already-shipped pose IDLE grammar (no new engineering needed), and the mechanic itself composes entirely from already-shipped primitives (`_geometry_from_spec`, `ComponentSpec.declared_box_pose`'s raw mm fields) without inventing any new geometric concept — **recommendation: B1-min**, named pair `esc` (child) vs `flight_controller` (origin), mechanic: axis-aligned-box overlap computed in the pose's own declared mm frame (never the CSS/pixel frame `scene3dLayout.ts` uses for rendering), fail-closed on any missing axis, copy restricted to the same screening-only vocabulary `GAP-FRAME-PROP-SIZE` already established and never touching `ASSEMBLY_READY`/PASS.

---

## A. Spatial situation as-is (live tree, cited)

### `autonomía-de-5min`

| Key | Envelope | `mounted_on` | `declared_box_pose` | Board solid |
|---|---|---|---|---|
| `motors` | none | `frame_arm` | — | no |
| `propellers` | disk (Ø) | `motors` | — | yes (disk) |
| `esc` | none | `frame_plate` | — | no |
| `battery` | none | `frame_plate_2` | — | no |
| `flight_controller` | **box** 44×84×12 | `frame_plate` | — | yes (box) |
| `sensors` | none | `frame` | — | no |
| `frame`/`frame_*` parts | none | — | — | no |
| kit keys (`power_connector`/`signal_harness`/`prop_adapter`) | none | — | — | no |

**Zero** poses declared. **Zero** posed pairs of any kind.

### `autonomía-de-10min`

| Key | Envelope | `mounted_on` | `declared_box_pose` | Board solid |
|---|---|---|---|---|
| `motors` | none | — | — | no |
| `propellers` | disk (Ø) | `motors` | — | yes (disk) |
| `esc` | **box** 50×21.6×12 (catalog `hobbywing_xrotor_40a_6s`) | `frame_plate` | `{origin_key: "flight_controller", x_mm: 5.0}` — **y_mm/z_mm absent** | yes (box) |
| `flight_controller` | **box** 44×84×12 (freeform "pixhawk_4") | `frame_plate` | — | yes (box) |
| `battery`, `sensors`, `frame`, `frame_*` parts, kit keys | none | various | — | no |

**One** declared pose exists: `esc → flight_controller`. Both ends are real boxes (confirmed `_geometry_from_spec`-eligible — both have the full `length_mm`/`width_mm`/`height_mm` triple). The pose is genuinely **incomplete**: re-running `project_spatial_nodes` against the live file confirms the Board's own `declaredBoxPose` DTO for `esc` is `{"originKey": "flight_controller", "xMm": 5.0}` — `yMm`/`zMm` keys are not present at all (not even `null`), matching `_declared_box_pose_dto`'s own "only emit axes that are not `None`" contract.

**Count of posed box–box pairs with a screening-usable (complete) pose: zero.** Count of posed box–box pairs with *any* declared pose at all: **one** (incomplete). This distinction matters — the IC's own §A framing ("if zero, that is evidence for B0") is about *complete* pairs; the live tree has one *partial* pair, which is meaningfully different from having no relationship declared at all: the gap here is "the same user hasn't finished a fact they already started," not "no page/mechanism exists to source it" (contrast with Plate L×W's hard sourcing wall).

**Cross-check, not a conflation**: `esc.mounted_on == "frame_plate"` (a structural part with no envelope) while `esc`'s pose origin is `flight_controller` — a *different* component. These are two independent, already-orthogonal facts in the schema (mount = physical attachment point; pose = declared measurement reference) and any compare mechanic must keep them separate — screening `esc` against `flight_controller`'s box is a statement about the *declared pose relationship* only, never an implicit claim that `esc` is mounted to or physically adjacent to the flight controller.

**Rooster frame**: confirmed still has no `length_mm`/`width_mm`/`height_mm` on either live project — Plate L×W B0 holds, unaffected by this investigation.

---

## B. What "comparar" could mean without CAD

| Mechanic | Inputs | Honest output | Forbidden output |
|---|---|---|---|
| **AABB overlap of two posed boxes, in the pose's own declared mm frame** | Child's `_geometry_from_spec` box (L/W/H) + child's `declared_box_pose` (all three of `x_mm`/`y_mm`/`z_mm` present) + origin's `_geometry_from_spec` box (L/W/H, resolved via the same box-check `_declared_box_pose_dto` already enforces) | A screening fact: "en los ejes declarados, los sobres [no] se solapan" — plus, when incomplete, an equally honest "pose incompleta en {axis}; no se puede comparar" | `"cabe"`/`"no cabe"`/`VERIFIED`/`"ensamblado"`/`"misfit geométrico"` |
| **Axis-count coverage note (no geometry math)** | Same `declared_box_pose`, just checks `x_mm is not None and y_mm is not None and z_mm is not None` | "Pose declarada en 1/3 ejes — falta y, z para comparar" (a pure presence count, zero mm arithmetic) | Any "fits"/"safe"/"clearance OK" framing |
| **Refuse-only (no compute at all)** | Any `expected_keys`/CLI phrase asking "¿cabe?" | A deterministic refusal naming *why* ("Jarvis no verifica ensamblaje físico; puedo comparar sobres declarados si ambos tienen pose completa") | Silently answering yes/no |

Disk–box or any cylinder mechanic is **not** proposed — the live tree's only disk (`propellers`) has no pose at all, and Locked Stance #6 forbids treating Ø+height as a cylinder regardless.

---

## C. Honest Buys (ranked)

**Recommended: `B1-min`.**

- **Named pair**: `esc` (child) vs `flight_controller` (origin) — the one real, live identity pair with a declared pose relationship, both ends already-sourced/declared boxes.
- **Mechanic**: axis-aligned box overlap, computed in the pose's own **declared mm frame** (child box centered at `(x_mm, y_mm, z_mm)` relative to the origin box centered at `(0,0,0)`, each box's half-extents from its own `length_mm/2, width_mm/2, height_mm/2`) — a pure, new, backend-only (Python) function. **Must not** reuse `scene3dLayout.ts`'s `layoutSolidsFromPose`/`solidWrapperPx`: that code operates in **CSS pixels**, applies the locked **Y↔Z axis swap** for rendering, and is explicitly presentation-only per its own docstrings — reusing it for a physics claim would silently launder a rendering convention into an engineering verdict, exactly the kind of error this investigation exists to prevent.
- **Fail-closed exactly where the live data already requires it**: `x_mm`/`y_mm`/`z_mm` must all be present (today's live pair has only `x_mm` — it would correctly and immediately produce "pose incompleta" text, not a screening fact, when this Buy first ships). Same fail-closed rule as the existing pose DTO gate for a non-box or vanished origin.
- **Severity/copy discipline**: mirror `GAP-FRAME-PROP-SIZE` exactly — MEDIUM at most, screening-only vocabulary, never `ASSEMBLY_READY`/Structure/Propulsion PASS, never a new `can_fly=False`, surfaced via an existing text surface (Board field or Continuity line) — no new UI chrome, per lock #9 (the IC that eventually implements this decides exactly where the text lands).
- **Why B1-min over B0**: unlike Plate L×W (a hard sourcing wall — no page anywhere states the Rooster's footprint), this gap is a single user action away from being closeable (declaring the two missing axes via the already-shipped pose IDLE grammar) and the mechanic itself invents no new geometric primitive — it is a direct, minimal composition of `_geometry_from_spec` + the schema's own raw `declared_box_pose` fields, exactly the kind of "ship the honest mechanism now, correctly idle on today's incomplete data" pattern this project has repeatedly and successfully used (Scene3D-from-pose B1, prop adapter ask B1, kit SKUs D — all shipped mechanisms whose live "happy path" wasn't yet exercised by existing project data, validated instead by synthetic fixtures).
- **Why not B1-copy alone**: a bare refusal is strictly less useful than B1-min once B1-min's own fail-closed path already produces the *same* honest "cannot compare" outcome for today's live data — B1-copy would be redundant with B1-min's own honest-absence branch, not a smaller step.

**Parked (named, not this Buy):** clearance-margin-in-mm ("least N mm of clearance"), a Continuity HIGH-severity fit gap, "does the assembly fit inside the frame's silhouette" (blocked on Plate L×W B0 regardless).

---

## D. Twin / non-goals

- **Not treating the queued stub as READY**: `implementation_contract_geometry_assembly_fit_compare.md` (2026-09-07) is confirmed, by its own current text, to already name this very investigation as its gate ("Fresh investigation: investigation_contract_geometry_assembly_fit_cabe_b0.md... Do not implement intersection, clearance, 'cabe', or fit badges under this filename until that investigation is REVIEWED and a superseding READY IC replaces this stub"). It was written when pose was still deferred (its own parent line: "pose B0 DEFERRED") — that premise is now false (pose shipped, Scene3D-from-pose shipped), but the stub's own gate text already anticipated exactly this report and remains correctly un-unfrozen; a **new** IC (not an edit to this stub file) would be required to proceed.
- **Frame class compatibility (`GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE`) is not this Buy** — confirmed by reading `_frame_class_gaps` directly: it compares `propeller_diameter_in` against a declared `size_class_inch` *convention*, never a geometric envelope, never a pose. This report's B1-min recommendation is additive to it, never a replacement or relabeling.
- **Kit SKUs (`power_connector`/`signal_harness`/`prop_adapter`) have no geometry** — confirmed live: none of the three has an `envelope` or a pose on either demo project; out of scope, unaffected.
- **No card-lane/CSS overlap mechanic proposed anywhere in this report** — every mechanic in §B reads `declared_box_pose`'s raw mm fields and `_geometry_from_spec`'s mm dimensions directly; none reads Board `x`/`y`, `localStorage`, or any `scene3dLayout.ts` pixel value.
- **No version bump, no `library/` edit, no `workspace/` mutation** — confirmed via `git status --short`, empty for all three this cycle.

---

## Explicitly not this investigation

Implementing the AABB compare (no code written — confirmed via `git diff`, empty) · seeding Rooster L×W · relabeling `GAP-FRAME-PROP-SIZE` as fit · FEA/STEP/cylinder · a GetFPV crawl · Conversation Engine · a version bump · un-freezing the 2026-09-07 stub as-is.
