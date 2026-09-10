# Investigation Report — 4 motors + 4 hélices in space (product B, then remaining pieces)

**IC:** [investigation_contract_geometry_quadrotor_kit_in_space_b0.md](investigation_contract_geometry_quadrotor_kit_in_space_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint:** package `0.3.8` · suite 2540

**Do not implement — this is a read-only report. No `src/`/`ui/`/`library/` edit made. No `workspace/` mutation.**

---

## Executive summary

On both live projects, the bound motor SKU (`emax_rs2205_2300` — the sibling **without** the "s", confirmed via `default_library.get_motor(...)`) has `diameter_mm=None`: **zero motor geometry exists today**, so `_geometry_from_spec(motors)` is `None` and `_solid_copies` is `None` regardless of `motor_count` — there are currently **zero motor solids on either live project**, copies or otherwise. Propellers, by contrast, already have real geometry (Ø127mm disk, both projects) but never receive `solidCopies` by design (locked, tested non-goal from Motor visor copies B1). Three independent, already-cited blockers stand between today's tree and "N motors + N hélices in space": (1) no motor Ø on the live SKU, (2) `expandSolidCopies` deliberately strips `declaredBoxPose` on every copy (confirmed by reading the TS source directly) so N copies can only ever render as a flat row, never distinct stations, and (3) the pose writer itself (`set_component_declared_box_pose`) hard-rejects a disk origin at declare time — "hélices respecto a motors" cannot be declared today, full stop, not merely unprojected. Given this, a per-copy "stations" schema (B1-stations) would ship with **zero live effect** (still blocked by the missing motor Ø) and requires inventing a genuinely new architectural concept (an array of poses per spec) that no part of the codebase anticipates today. Relaxing the disk-origin gate (B1-disk-origin) reopens a deliberately-reasoned prior honesty decision (a disk has no in-plane heading to measure "along +X" against) and, even if done, only ever helps **one** hélice sit on **one** motor identity — not 4 stations. **Recommendation: `B1-copies-prop`** — extend the already-shipped `motor_count`-driven copy pattern to `propellers`, reusing the SAME quantity convention `_bom_quantity` already documents ("1 propeller per motor... no independent `propeller_count` field exists anywhere in this codebase") — a presentation-row, not millimetres, with **immediate live effect today** (4 propeller disks on the 5min project, 3 on the 10min project) and zero new schema, zero pose/writer change, zero motor-geometry dependency.

---

## A. As-is census (live tree, cited)

| Project | `motors` geometry | `motor_count` | `motors.solidCopies` | `propellers` geometry | `propellers.solidCopies` | Any pose declared | Any disk-origin pose possible |
|---|---|---|---|---|---|---|---|
| `autonomía-de-5min` | **None** (`emax_rs2205_2300`, `diameter_mm=None`) | 4 | `None` (blocked — no geometry) | disk, Ø127mm (`gf_5045x3`) | `None` (never emitted for propellers, by design) | zero | no — writer rejects disk origin at declare time |
| `autonomía-de-10min` | **None** (same SKU) | 3 | `None` | disk, Ø127mm (`gemfan_5045_hbn`) | `None` | zero (frame has `wheelbase_mm=230`/`configuration=quad_x` as **card text only**, no solid) | no |

Confirmed directly (`project_spatial_nodes_from_path`, read-only): both projects' `motors` node has `geometry: None`, `solidCopies: None`, `declaredBoxPose: None`; both `propellers` nodes have `geometry: {"shape": "disk", "diameter_mm": 127.0}`, `solidCopies: None`. Frame (`armattan_rooster_5in`) still has no `length_mm`/`width_mm`/`height_mm` on either project — Plate L×W B0 holds, unaffected here. Note the 5min project's frame properties additionally lack `wheelbase_mm`/`configuration` entirely (bound before Wheelbase-on-spec B1 shipped) — a pre-existing data-vintage difference, not something this investigation proposes touching.

---

## B. Why "the same as ESC–FC" does not scale

`"cabe"` B1-min screens exactly **one** already-posed child box against **one** already-posed-into box origin — a single, already-complete (if partial) relationship. "4 motors + 4 hélices in space" is a different shape of problem on three independent axes:

1. **Copies strip pose.** `expandSolidCopies` (confirmed by reading `ui/spatial-board/src/scene3dLayout.ts` directly) turns one `solidCopies: N` node into N presentation entries that share one `selectId` but explicitly **omit** `declaredBoxPose` on every copy ("A copied node's `declaredBoxPose` is deliberately stripped — composing pose onto N copies would stack them at the same point"). There is no way, today, for N copies of one identity to carry N distinct offsets — `layoutSolidsFromPose` falls back to a flat row for every one of them.
2. **One pose field, not an array.** `ComponentSpec.declared_box_pose: DeclaredBoxPose | None` is singular. Nothing in the schema, the writer, or the projector anticipates "N poses, one per copy index" — this would be a genuinely new architectural concept (confirmed: no `declared_box_poses`/`station`/`copy_offset` name exists anywhere in `src/` or `ui/spatial-board/src`), not a small extension of the existing field.
3. **Origin must be a box.** `set_component_declared_box_pose` (the one write path) raises `ValueError` for a disk origin, citing its own reasoning verbatim: "a disk (rotational symmetry, no in-plane heading — investigation report §A3)... is rejected, never silently accepted with an invented fallback origin." A hélice's pose "respecto a motors" is not merely unprojected today — it is **structurally impossible to declare**.

No frame prism exists to anchor any of this differently (Plate L×W B0), and `configuration=quad_x`/`wheelbase_mm=230` are card-text facts the Motor visor copies B1 Buy already explicitly locked **out** as a placement source ("not quad-X of 230").

---

## C. Honest Buys (ranked)

**Recommended: `B1-copies-prop`.**

- **What it is**: extend the existing `_solid_copies`-shaped gate to `propellers` — N presentation-row copies (never millimetre stations, never a new pose), N taken from the exact same convention `_bom_quantity` already documents and ships (`project_state.current_parameters["motor_count"]`, falling back to `motors.properties["motor_count"]` — "Propellers reuses this number as a documented convention... no independent `propeller_count` field exists anywhere in this codebase"). This is not inventing a new count source — it is applying an already-shipped one to a second (visor) surface.
- **Why it clears every locked stance**: N comes from the spec-linked convention, never a default 4 (confirmed live: 5min → 4, 10min → 3, both would render correctly, never coerced to 4). No pose is touched, stripped, or invented — propellers never had one and still won't. No frame prism, no cylinder (propellers stay disks), no disk-as-pose-origin change, no kit/adapter geometry. Still **one** `propellers` `ComponentSpec`/BOM node — copies are visor-only, click any copy → the one card (same guarantee the motors copy mechanism already proved).
- **Why it has live value today, unlike the alternatives**: propellers already have real geometry on both live projects (Ø127mm) — this Buy's happy path is immediately exercised, unlike a schema-only mechanism blocked by the motor-Ø wall. It ships an actual, visible change to what the Engineer asked for ("4 hélices" → 4 disks) using a pattern already reviewed, shipped, and tested once (Motor visor copies B1) for the sibling case.
- **What it deliberately does not solve**: motor solids stay invisible (the `emax_rs2205_2300` Ø gap is a separate, pre-existing wall this Buy does not touch or need to touch — seeding it is explicitly out of scope for a "kit in space" IC) and copies still sit in a plain row, not distinct stations (that remains B1-stations' problem, named below, not solved by this Buy).

**Also considered, not recommended this cycle:**

| ★ | Why not the first Buy |
|---|---|
| **B0** | Defensible on the sheer number of blockers, but strictly weaker than `B1-copies-prop`: that Buy already produces the honest, useful, in-scope subset of "the same as motors" without hitting any of the three named walls — recommending B0 here would leave real, immediately-available value on the table. |
| **B1-stations** | The architecturally "complete" answer, but requires inventing a genuinely new schema concept (a per-copy pose array/mechanism) that nothing today anticipates — a real architectural decision, not a small extension, and one CLAUDE.md's own discipline says needs explicit approval before an IC, not just Cursor review. Even fully built, it ships with **zero live effect** until the separate motor-Ø wall is also closed (out of scope here). Park for a dedicated future ★, not bundled into the propeller-copies step. |
| **B1-disk-origin** | Reopens a deliberately-reasoned, already-shipped honesty decision (no in-plane heading on a disk) without a new argument for why that reasoning no longer holds, and even if relaxed only ever yields **one** hélice on **one** motor identity — not 4 stations, not the Engineer's actual ask. Weakest of the four. |

**Explicitly parked, not this Buy**: remaining pieces (battery, sensors, kit hardware) — per lock #8, these wait for a separate ★ after motors+hélices is named and closed. Frame box, cylinder, `"cabe"` on disks, N BOM motor nodes.

---

## D. Out of scope (explicit)

Inventing Rooster L×W · a silent default of 4 motors/copies · a motor or propeller cylinder · Conversation Engine · widening `"cabe"` to every card · seeding `emax_rs2205_2300.diameter_mm` (or any other motor Ø) · a per-copy pose/stations mechanism (named as a future Buy, not built here) · relaxing the disk-origin pose gate · any `src/`/`ui/`/`library/` edit (none made — confirmed via `git status`, empty for all three) · a version bump (`pyproject.toml` unread/unchanged) · `workspace/` mutation (confirmed empty `git status --short -- workspace/`).

**Remaining pieces (battery, sensors, kit hardware, …) are explicitly a later ★, not folded into this recommendation.**
