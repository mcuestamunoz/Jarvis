# Investigation Report — Drone default layout / main-plate assembly root (B0)

Status: Investigation complete — no code changed, no version bump, `workspace/` read-only
Parent: `investigation_contract_board_drone_default_layout_b0.md`
Checkpoint: package `0.4.1` (unchanged) · suite `2747` (unchanged) · UI `99` (unchanged)

## Summary up front

The product sentence under evaluation — *"Jarvis treats the main plate box
as the assembly origin and situates components by dimension per a minimum
drone standard"* — is **currently dishonest to claim as shipped**, but not
because the standard graph is unbuildable. Two independent, separable
findings:

1. **The assembly root has never activated on any live project**, on any
   date this investigation checked (`5min`, `10min`, `15min` — all three,
   fresh read). Not a bug: `frame_plate` genuinely has no cited L×W
   anywhere (the already-closed `#4g-A` CAD gap), so the root-activation
   code — which already exists and needs zero new code — has nothing to
   turn on. Confirmed live, right now, a **cyclic pose chain** exists on
   `autonomía-15min` (`esc`→`battery`→`flight_controller`→`esc`) — a
   direct, concrete illustration of what happens when three boxes pose
   relative to EACH OTHER with no fixed anchor: there is no well-defined
   "true" position for any of them, only whatever order the layout
   algorithm's cycle-guard happens to resolve.
2. **The standard graph is partially, not fully, expressible today** —
   and better than a first skim suggests. `prop→motor` and `motor→arm` are
   ALREADY declarable via the existing `mounted_on` grammar (verified by
   reading the actual resolver code, not assumed). `arm→plate` and
   anything involving the kit-hardware family (`power_connector`/
   `signal_harness`) are genuinely not expressible — no invented gap, a
   real one.

Recommended first Buy (§D): **`B1-mount-standard-assist`** — it needs no
new data, touches no pose math, and closes the one part of "novice doesn't
know what mounts on what" that's solvable today. `B1-plate-box` is
`DEFER` — it is not a code gap, it's the same data gap `#4g-A` already
closed B0.

---

## A. Assembly-root census

`ASSEMBLY_ROOT_ID = "frame_plate"` (`ui/spatial-board/src/scene3dLayout.
ts:35`); root activates only when `item.id === ASSEMBLY_ROOT_ID &&
item.geometry.shape === "box"` (`scene3dLayout.ts:66-67`). When it does
not activate, every item falls back to a plain row slot
(`layoutSolidsFromPose`'s own fallback, `scene3dLayout.ts:99-101` for the
non-posed case and `:134-136` for the posed-but-origin-not-a-box case) or,
if it declares a pose to a boxed non-root origin, a **composed chain**
relative to that origin (`resolveComposedCenter`, `scene3dLayout.ts:
90-111`) — never relative to world 0 unless that chain eventually resolves
back to the (inactive) root.

Fresh read (this investigation, read-only) of all three live projects:

| Project | `frame_plate` geometry | Root active? | Consequence |
|---|---|---|---|
| `autonomía-de-5min` | `None` (thickness only — no citation) | **No** | All 9 solids sit at row slots or in a pose chain anchored to whichever box was posed first (`esc`→`flight_controller`), never to world 0 |
| `autonomía-de-10min` | `None` | **No** | Same — `esc`→`flight_controller` chain, rest at row slots |
| `autonomía-15min` | `None` | **No** | Same mechanism, but the pose graph has drifted into a **cycle**: `esc`→`battery`, `battery`→`flight_controller`, `flight_controller`→`esc` (fresh read, this investigation). `resolveComposedCenter`'s own cycle guard (`scene3dLayout.ts:92`, `if (visiting.has(id)) return rowSlotCenter(id)`) prevents an infinite loop, but there is no principled "correct" position for any of the three — whichever one the traversal order happens to hit first gets treated as the fixed point. This is not a bug (the code does exactly what it says), but it is a direct, live demonstration of why "situate by dragging relative to a sibling, with no fixed anchor" degrades: three honest, individually-correct pose declarations combine into a graph with no ground truth. |

None of the three projects can reach root-anchored placement today, on any
version of `scene3dLayout.ts` currently shipped, because none has ever
cited or declared a `frame_plate` L×W. This is the SAME gap `#4g-A`
already investigated and closed B0 for the GEP-Racer catalog row
specifically (`investigation_report_geometry_gep_racer_part_cad_b0.md` —
no authentic OEM CAD found; Engineer confirmed no private pack) — this
investigation does not reopen that search, only confirms its downstream
consequence for the assembly root.

## B. Standard drone graph vs Jarvis keys

Read directly from `src/jarvis/core/mounted_on_declare_assist.py` (the
one module both the CLI and Board edges/mount data derive from — no
second alias table anywhere in the codebase). Two separate noun tables
matter: `_SUBJECT_PATTERNS` (`mounted_on_declare_assist.py:63-70` — fixed:
`flight_controller`, `esc`, `motors`, `battery`, `sensors`, `propellers`)
and target resolution (`_resolve_target`, `:121-169`), which tries, in
order: an **exact literal key match** (`_exact_key_match`, `:88-96` — any
declared component key, verbatim), a plate **label** match, the frame-part
noun patterns (`_ARM_RE`/`_CAGE_RE`/`_STANDOFF_RE`/`_FRAME_ROOT_RE`/
`_PLATE_BARE_RE`, `:74-78`), and finally — the one non-obvious escape
hatch — a re-use of the SAME `_SUBJECT_PATTERNS` table as target aliases
too (`_resolve_target_component_alias`, `:172-176`, explicitly documented
as "what lets 'hélices montadas en los motores' resolve a target at all").

| Relation (Engineer) | `mounted_on` expressible today? | Already declared? |
|---|---|---|
| prop **on** motor | **Yes** — `propellers` is a valid subject; `motors` resolves as a target via the subject-alias reuse (`:172-176`) | `5min`: yes (`propellers`→`motors`). `10min`: yes (Conn smoke, `engineer_smoke_connect_remaining_mounted_on_b1.md`). `15min`: no |
| motor **on** arm | **Yes** — `motors` is a valid subject; `frame_arm` resolves via `_ARM_RE` (`:74`, `:138-139`) | `10min`: yes (`motors`→`frame_arm`, per the same Conn smoke's "already declared" table). `5min`/`15min`: no |
| arm **on** main plate | **No** — `frame_arm` is never a valid SUBJECT noun (absent from `_SUBJECT_PATTERNS`; the alias-reuse tier at `:172-176` only ever supplies target-side aliases, never widens subject resolution, which stays `_resolve_subject`-only, `:81-85`). A phrase like "el brazo montado en la placa" resolves `subject=None` and the whole parse falls through to `_NONE` (`:186-188`/`:210-211`) | Not applicable — cannot be declared via this grammar at all today |
| battery / esc / fc / gps **on/in** frame | **Yes**, all four — each of `battery`/`esc`/`flight_controller`/`sensors` is a valid subject; the bare frame root resolves via `_FRAME_ROOT_RE` (`:77`, `:144-145`) | `5min`: `esc`/`flight_controller`→`frame_plate` (a specific plate, not bare `frame`), `battery`→`frame_plate_2`, `sensors`→`frame`. `10min`: `esc`/`flight_controller`→`frame_plate`, `battery`→`frame` (per Conn smoke), `sensors`→`esc` (declared in that same smoke walk — not the frame at all). `15min`: none declared (pose-chain-only project, §A) |
| connector / harness **on/in** frame | **No** — `power_connector`/`signal_harness` never appear in `_SUBJECT_PATTERNS`; there is no exact-key-match fallback on the SUBJECT side (only `_resolve_target`, `:88-96`, has one, and only for targets) | Not applicable |

`parent_key` (Structure B Parts Graph composition — every `frame_*` part
already carries `parent_key: "frame"`) is a **separate, orthogonal** fact
from `mounted_on` — it says "this part belongs to the frame kit's BOM,"
never "this part sits spatially on the plate." The two are never merged
anywhere in the codebase (confirmed by the same read); a future Buy must
not conflate them.

**Net finding**: two of six named relations are fully expressible and
already partly declared on real projects; two are fully expressible but
under-declared (data-entry gap, not a code gap); two (`arm`-as-subject,
kit-hardware-as-subject) are genuine, real gaps in the noun vocabulary —
not previously identified anywhere in this codebase's own documentation.

## C. "By dimension" — honest math vs invention

No rule of any kind exists today for deriving a Δmm pose from envelopes
alone — `set_component_declared_box_pose` (`src/jarvis/core/component_
writers.py:295`) only ever writes a pose it is explicitly handed
(Engineer-typed or Board-dragged); nothing in the writer, the Continuity
parse layer, or the projector ever computes one from L×W×H.

Two candidate rules exist that COULD be computed from already-declared
envelopes with zero new millimetre citations, evaluated honestly:

- **"Touching stack" for X mounted-on Y** (e.g. `battery` on `frame_
  plate`): `z_mm = Y.height_mm/2 + X.height_mm/2`, `x_mm = y_mm = 0`
  (centered). This uses only heights the project already declares — no
  external citation needed for the ARITHMETIC. But the ASSUMPTION behind
  it (centered, flush, no gap) is not derived from any fact Jarvis holds —
  real assemblies commonly have standoffs, screws, wiring clearance, or a
  deliberate off-center placement for CG balance that this formula cannot
  know about. This is squarely the Feature lock's own "auto-pose without
  citation" boundary
  (`engineer_lock_continuity_spatial_assembly_feature.md:64`, "Out (still):
  ... auto-pose without citation"), even though the inputs are already
  declared — the OUTPUT would be a NEW physical claim (a specific Δmm)
  Jarvis has no evidence for. **Never implement silently; only as an
  explicit, named `B1-stack-rule` the Engineer separately ★'s.**
- **"Centered on motor shaft" for prop-on-motor**: `x_mm = y_mm = 0`,
  `z_mm = motor.height_mm` (or similar). This is a stronger, near-universal
  physical convention (propellers are built to center on a motor's own
  rotational axis) than generic stacking, but it is still an assumption
  Jarvis is asserting rather than citing — same "never silent" rule
  applies.
- **`arm` on `main plate`**: cannot even reach this stage. `frame_arm` has
  no L×W on the current GEP-Racer catalog row at all (thickness-only,
  same `#4g-A` gap) — there is no envelope to compute FROM, independent of
  whether a stacking rule ever gets ★'d.

Any stacking/centering rule, if the Engineer wants one, must be its own
named Buy (`B1-stack-rule`) with the assumption spelled out in the
Continuity/Board copy exactly the way `pose_envelope_screening.py`
already discloses its own AABB-only limits — never presented as a
verified physical fact.

## D. Honest Buys (ranked)

**Recommended first IC: `B1-mount-standard-assist`.**

Rationale: it is the only item on the Engineer's own list that needs
**zero new data** — it works entirely within what §B already proved
expressible today (prop→motor, motor→arm, the four component→frame
relations) — and it directly answers "novice doesn't know what mounts on
what" without touching pose math, envelopes, or the still-blocked plate
root. A deterministic checklist/suggest surface (mirroring the existing
`motor_catalog_assist.py`/`propeller_catalog_assist.py`/`catalog_rebind_
assist.py` pattern already used throughout this codebase for "suggest,
never silently write") that, for a given project, lists which of the
expressible standard-graph relations are still undeclared and offers the
exact Continuity phrase to type — user still types/confirms, never an
auto-write.

| ★ | Meaning | Verdict here |
|---|---|---|
| `B0` | Leave racimo; teach Continuity manually | Valid fallback if the Engineer wants zero further code this cycle |
| **`B1-mount-standard-assist`** | Deterministic suggest for the already-expressible standard graph | **Recommended first** — no data blocker, no pose-math risk |
| `B1-plate-box` | Unlock main-plate root via cited/caliper L×W | **`DEFER`** — this is `#4g-A`'s own already-closed-B0 gap, not new code; only a new citation or an Engineer caliper measurement unblocks it |
| `B1-stack-rule` | Explicit envelope-only stacking/centering rule | Rank AFTER plate-box (mostly moot without a boxed root to stack against, except prop-on-motor which is independent) — needs its own ★ and its own honesty-copy design (§C) |
| `B1-layout-pack-cited` | Named kit layout pack with disclosed authority | Rank last — needs either a real citation or an Engineer-measured table; nothing here to seed one today |

Parked (per the IC's own lock, not re-litigated here): LLM auto-pose,
inventing plate L×W from wheelbase/body footprint, Three.js, N BOM
clones, reopening Situar experience B1 as if it were a layout Buy (it is
an ergonomics product, evaluated and shipped separately — §5 of this
report's own rules).

## E. Ordered cola after the first Buy

1. `B1-mount-standard-assist` (this report's recommendation — no data
   blocker).
2. Plate data (citation or Engineer Option B caliper) — reopens
   `B1-plate-box`, which is pure activation of already-shipped code
   (`ASSEMBLY_ROOT_ID` gate) once `frame_plate` has a real L×W.
3. `B1-stack-rule` (envelope-only stacking, explicitly labeled) — once a
   boxed root exists, or scoped narrowly to prop-on-motor first.
4. `B1-layout-pack-cited` — a named kit's disclosed-authority layout, only
   if/when a real citation or Engineer-measured table exists.
5. Silhouette polish (Product B) — unchanged from the prior investigation
   (`investigation_report_board_situar_realism_novice_b0.md`), still
   downstream of the same plate/arm/standoff data gap.

## F. Out of scope (explicit, honored)

This investigation did not: invent GEP `frame_plate`/`frame_arm` L×W,
treat the 175×173mm body footprint as a plate box, propose or implement
any auto-pose/stacking code, reopen Fit VERIFIED, touch autonomy/HD-005,
or treat Situar experience B1 as an unfinished layout feature (it is a
separate, already-shipped ergonomics product — evaluated on its own terms
in the prior investigation and IC). No file under `src/`, `tests/`, `ui/`,
or `library/` was modified. No `workspace/` file was modified — every read
in §A/§B was via `project_spatial_nodes`/direct file reads, never a write
(confirmed via `git status --short -- workspace/`, empty). No version
bump.

---

## G. Engineer decision card (one page)

| Question | Answer |
|---|---|
| Is "main plate as assembly origin" shipped/working today? | **No, on any live project** — not a bug, `frame_plate` has no cited L×W anywhere (same gap `#4g-A` already closed B0). Code that would activate it (`ASSEMBLY_ROOT_ID`) already exists and needs no changes. |
| Is the standard drone graph (props→motors→arms→plate; stack→frame) expressible via Continuity today? | **Partially — better than assumed.** prop→motor and motor→arm ARE already declarable (verified in code); arm→plate and connector/harness→frame are genuine gaps in the subject-noun vocabulary. |
| Can Jarvis honestly place things "by dimension" without inventing? | **Not yet, for anything requiring a NEW Δmm** — any stacking/centering rule is a real physical assumption, not a citation, and must be its own explicit ★'d Buy, clearly disclosed in copy, never silent. |
| What's the smallest Buy that helps today? | **`B1-mount-standard-assist`** — needs no new data, suggests only what's already provably expressible, user still confirms every write. |
| What stays `B0`/`DEFER`? | `B1-plate-box` (data-blocked, not code-blocked — `DEFER`), `B1-stack-rule` and `B1-layout-pack-cited` (rank after plate data, or scope prop-on-motor narrowly if pursued sooner), full silhouette (unchanged `DEFER` from the prior investigation). |
