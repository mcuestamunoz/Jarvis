# Investigation Report — Disk-station fit / attest (`B0-disk-station-fit-attest`)

**IC:** `investigation_contract_disk_station_fit_attest_b0.md` (pasted 2026-09-15)
**Investigator:** Claude Code
**Date:** 2026-09-15
**Type:** Read-only. No code changed. No IC implied by this document.
**Checkpoint at investigation time:** package `0.4.1` · suite **2945 passed, 1 skipped** · UI **105**

---

## A. As-is code map

### A1 — Why motors/propellers get `n_a_disk` in `fit_relations_assist`

`src/jarvis/core/fit_relations_assist.py:59-62` hardcodes the mount-only relation set:

```python
_MOUNT_ONLY_RELATIONS: tuple[tuple[str, str], ...] = (
    ("motors", "frame_arm"),
    ("propellers", "motors"),
)
```

`_mount_only_relation_row` (`fit_relations_assist.py:221-237`) is unconditional — it never calls `screen_posed_envelope`, never calls `_geometry_from_spec`, never inspects the child's actual shape. Every row for these two pairs is forced to `status="n_a_disk"` with the fixed reason string `"sin screening de caja hoy (disco) — el montaje sí se puede declarar; verificación de disco es un Buy aparte"`, unconditionally, regardless of what geometry the live spec actually resolves to. This is a **locked design decision, not a runtime shape check** — even a motor with full box dims would still read `n_a_disk` today, because the code path that would compare geometry is never reached for these two pairs (contrast with `_plate_relation_row`, used for the box family, which does call `_geometry_from_spec`/`screen_posed_envelope`/`_attestation_is_valid`).

### A2 — What `screen_posed_envelope` returns for disk/cylinder children

`src/jarvis/core/pose_envelope_screening.py:63-115`. The function is box-only by construction:

- Origin: `origin_geometry.get("shape") != "box"` → `Screening(status="origin_unusable")` (line 83-84).
- Child: `child_geometry.get("shape") != "box"` → `Screening(status="child_not_box")` (line 86-88).

A disk or cylinder child (or origin) is refused at the shape check, before any axis/overlap math runs — the AABB math itself (lines 98-115) only ever reads `length_mm`/`width_mm`/`height_mm`, keys a disk/cylinder geometry dict does not have. So even if `fit_relations_assist` called this function for motors/propellers, it would correctly self-refuse (`child_not_box`), never crash and never silently coerce a disk into a box.

### A3 — How Visor places motor/prop stations: presentation vs. engineering frame

Two entirely separate mechanisms exist, and only one of them is an engineering claim:

- **Engineering frame** (`declared_box_pose`, `schemas/action_schema.py:157-176`): an explicit, writer-set `DeclaredBoxPose(origin_key, x_mm, y_mm, z_mm)` on a *specific* `ComponentSpec`. Set only by `component_writers.set_component_declared_box_pose` (`component_writers.py:295-352`), which validates the **origin** resolves to `shape=="box"` (raises `ValueError` otherwise, line 337-339) but does **not** validate the child's own shape — a disk/cylinder child can technically receive a `declared_box_pose` today (see A5 — this never happens in practice because no writer or IDLE grammar currently offers to declare one for motors/propellers). This field feeds `screen_posed_envelope` (engineering) and `_declared_box_pose_dto` (display), and is what `compute_fit_attestation_fingerprint` (`component_writers.py:366-379`) hashes.
- **Presentation frame** (`solidCopies`/`solidCopyOffsetsMm`, `workspace/spatial_board.py:411-478`, `682-767`): a **pure, re-derived-every-read** set of station points, computed from `frame.configuration=="quad_x"` + `frame.wheelbase_mm` (`_quad_x_wheelbase_mm`, lines 514-535) via `_quad_x_station_points` (lines 538-549) for motors/propellers/prop_adapter, or via the L-aware `_frame_arm_radial_offsets_mm` (lines 682-730) for `frame_arm` itself. **None of this is ever written to any `ComponentSpec` field** — it exists only in the DTO returned to the Board on each read, and is explicitly documented as presentation-only in three places (module docstrings at lines 411-412, 682-684, and `pose_envelope_screening.py`'s own header, lines 7-14, which states the CSS/pixel frame is a "purely presentational" convention that "would silently launder a rendering choice into an engineering verdict" if reused for a physical claim).

The practical consequence: today's arm-radial Visor renders 4 motors at plausible positions *every time the Board is opened*, purely from `wheelbase_mm` + `frame_arm.length_mm`, but **zero engineering claim backs that rendering** — no pose is stored, no fingerprint exists, nothing is screenable.

### A4 — Fit attestation fingerprint + `solidCopies` gate

`compute_fit_attestation_fingerprint` (`component_writers.py:366-379`) is a locked-order string join over `(origin_key, x_mm, y_mm, z_mm, child L/W/H, origin L/W/H)` — it unconditionally indexes `child_geometry["length_mm"]` etc. This means it is **only ever safe to call on a box/box pair**; a disk/cylinder geometry dict lacks those keys and would raise `KeyError` if this function were called on one. No current code path does this — `_attestation_is_valid` (`fit_relations_assist.py:109-127`) is only invoked from `_plate_relation_row`, never from `_mount_only_relation_row` — but it is a real latent landmine if any future code reused `compute_fit_attestation_fingerprint` for a disk pair without a new, disk-aware fingerprint function. **A B1 for disk-station attest must not reuse this fingerprint function as-is** — Locked stance #1 (new, distinctly-named helper) already anticipates this.

`set_component_declared_fit_attestation` (`component_writers.py:383-…`) requires `screen_posed_envelope(...).status == "overlap"` as a hard precondition (raises `ValueError` on any other status) — so today's writer is structurally incapable of attesting a disk pair even if a pose were somehow declared, since `screen_posed_envelope` would never return `"overlap"` for a non-box child.

The Board's singleton gate — "attest only when `solidCopies < 2`" — lives client-side in `ui/spatial-board/src/boardPoseDrag.ts:35`: `typeof node.solidCopies !== "number" || node.solidCopies < 2`. This is a UI convenience gate on the *pose-drag* affordance, reused by the attest button per `engineer_note_fit_attest_all_components.md`'s own description ("Board singleton (`solidCopies < 2`)") — it is not itself an engineering rule, but it is the existing precedent for "one seal per family regardless of N copies" that Locked stance #3 asks to preserve.

Separately, and more fundamentally: **`ComponentSpec` is already one BOM row per component family, regardless of `motor_count`.** `motors` is a single spec; `solidCopies=4` only controls how many *solids* the Visor draws for that one spec (`_solid_copies`, `spatial_board.py:411-458`). A `declared_fit_attestation` field lives on that one spec. This means "one station seal, not four independent seals" is not something a future Buy has to engineer — it falls out for free from the existing one-spec-per-family schema, exactly as it already does for the box family (a battery with `solidCopies` unset still gets exactly one `declared_fit_attestation`).

### A5 — Live Continuity pose census (read-only)

Checked all four `workspace/*/state.json` projects directly:

| Project | `motors.declared_box_pose` | `propellers.declared_box_pose` | `frame_arm.declared_box_pose` | `frame.configuration`/`wheelbase_mm` |
|---|---|---|---|---|
| `10-min-autonomía` | `None` | `None` | `None` | `quad_x` / `225.0` mm |
| `autonomía-de-5min` | `None` | `None` | `None` | `quad_x` / `225.0` mm |
| `dron-de-vigilancia-doméstico` | `None` | `None` | `None` | `quad_x` / `225.0` mm |
| `prueba` (throwaway) | `None` | `None` | (frame_arm absent) | absent |

**Zero live projects have any `declared_box_pose` on `motors`/`propellers`/`frame_arm`.** Confirms A3's conclusion is not just theoretical — no project has ever exercised the pose-on-a-disk path, because nothing in the product today offers to write one for these keys.

However, the **declared facts that would feed a station rule already exist** on the two real projects (`10-min-autonomía`, `dron-de-vigilancia-doméstico`):

- `motors`: `diameter_mm=28.5`, `height_mm=33.1` (cited body height, not `stator_height_mm`) → resolves to `cylinder` via `_geometry_from_spec`.
- `propellers`: `diameter_in=5.189`, `hub_thickness_mm=6.8` → resolves to `cylinder`.
- `frame_arm`: full box (`length_mm=80`, `width_mm=20`, `height_mm=5`, `thickness_mm=5`).
- `motors.mounted_on = "frame_arm"`; `propellers.mounted_on = "motors"` — both declared.
- `autonomía-de-5min` has weaker `frame_arm` facts (`thickness_mm` only, no `length_mm`) and no `motors.mounted_on` — it would not qualify for a radial station rule requiring arm length, today.

---

## B. Candidate evidence classes

| ID | Idea | Evidence class | Assessment |
|---|---|---|---|
| **D0** | Keep `n_a_disk` forever until MEASURE/CAD | Honest ceiling | **Must present, and is a legitimate close** if no evidence class below clears the "no lie" bar cheaply. Zero new code, zero new risk. Cost: the product want stated in the IC (a real seal on the strongest station pair) stays unmet. |
| **D1** | Declared **proxy box** at the station (Engineer-declares an L×W×H "stand-in" for the motor body / prop hub) + pose vs. arm/motor origin → reuse existing AABB + attest machinery unchanged | Same evidence class as the box path | Cheapest to *implement* (zero new geometry math) but **weakest honesty**: it asks the Engineer to invent a box for something that is not a box, and every future reader of that box has to remember it's a proxy, not the part. Also duplicates data already declared as Ø+height in a worse shape. Not recommended as the primary Buy — closest thing to "renaming a lie legible", which lock #7 in the parent IC (`n_a_disk` reason string) explicitly wants to avoid. |
| **D2** | **Radial station rule** — compare the arm's own declared `length_mm` (or a future declared "mount tip" offset) against the motor's station radius/offset from the frame's `wheelbase_mm`, as a 1D reach check, not a 3D AABB | New, narrowly-scoped, honestly-named deterministic rule with its own copy (never "overlap") | **Recommended primary candidate.** Every fact this rule needs already exists, cited, on 2 of 3 live projects today (A5): `frame.configuration=="quad_x"` + `wheelbase_mm`, `frame_arm.length_mm`, `motors.mounted_on=="frame_arm"`. The math is exactly `_frame_arm_radial_offsets_mm`'s own already-shipped `R = hypot(station.x, station.y)` / `L <= R` reach comparison (`spatial_board.py:682-730`) — today used only for *drawing* the arm's box at the right radial position, never as a pass/fail engineering verdict. A B1 would be: reuse that same radius math as a **new, disk-scoped screening status** (e.g. `station_reach_ok` / `station_reach_short` / `station_reach_over`), never named `overlap`/`no_overlap` (lock #1), gated the same fail-closed way (`origin_unusable`-equivalent when quad_x/wheelbase/arm length is missing) as `screen_posed_envelope` already is. |
| **D3** | Human attest **without** screen ("declaro estación OK") gated only on `mounted_on` + presence | Weaker than box attest — high lie risk | **Default OUT**, per the IC's own framing. `mounted_on` alone was already explicitly rejected as fit evidence for the box family (Locked stance #5, mirrored here) — there is no principled reason a disk pair should get a *weaker* bar than a box pair. Only worth reconsidering if D2 turns out to need a §0.1 bag no live project has (it doesn't — see C). |
| **D4** | Other | — | None identified beyond D0-D3 during this investigation. A pure diameter-vs-diameter "do these two circles overlap in plan view" check was considered and rejected: it would require assuming the propeller and motor share a common origin/axis, which is not currently a declared fact anywhere (no propeller-relative-to-motor offset exists, only `mounted_on`) — this would be inventing a spatial coincidence, not reading one. |

**Recommendation: D2 (radial station rule), scoped to `motors ↔ frame_arm` first — see C.** D0 is the honest fallback if the Engineer decides the reach-check's real engineering value (it proves nothing about vertical clearance, hub interference, or blade/frame contact — only that the arm reaches the frame's declared wheelbase radius) is too thin to be worth a Buy. This investigation does not judge that trade-off — it is a product decision, not a code one.

---

## C. First case scope

**Recommend `motors ↔ frame_arm`.**

Reasoning, from the live census (A5):
- `motors` has stronger, more complete declared facts today than the alternative first move would need: real cited `diameter_mm` + `height_mm` (not `stator_height_mm`), plus `mounted_on == "frame_arm"` declared, in 2 of 3 real projects.
- `frame_arm` already has a full box (`length_mm`/`width_mm`/`height_mm`) and is the one component in this pair whose reach math (`_frame_arm_radial_offsets_mm`) is **already implemented and shipped for the Visor** — a B1 would be extending an existing, tested radial calculation into an engineering verdict, not writing new spatial math from scratch.
- `propellers ↔ motors` is a *plausible second case* (propellers also have full cylinder facts and a declared `mounted_on` in all three live projects), but it has no equivalent to `frame_arm.length_mm`/wheelbase to compare against — a motor is not a box, so there is no existing "reach" quantity to reuse the way `_frame_arm_radial_offsets_mm` already provides for the arm case. It would need its own new evidence class (probably some declared axial standoff/prop-to-motor-face offset that does not exist as a fact anywhere today), making it strictly harder to ship honestly as a first Buy.

**§0.1 bag for a future IC:** the cited Ø/H facts already on `motors`/`propellers`/`frame_arm` (diameter_mm, height_mm, length_mm, width_mm, thickness_mm) are **already enough** for the D2 radial-reach comparison — no new Engineer-declared proxy box is needed. The only thing a future B1 needs to *decide* (not investigate further) is the exact tolerance/verdict shape for "reach OK" (e.g. is `L <= R` sufficient like the Visor's own placement math, or does it need a margin band) — that is a product/engineering judgment call for the IC's own §0, not a missing fact this investigation can resolve.

---

## D. Interaction with plate-box / estimated

Explicitly orthogonal, confirmed by code: `_is_estimated_temporary_box` (`pose_envelope_screening.py:49-54`, reused by `fit_relations_assist.py:28`) only ever inspects `length_mm`/`width_mm`/`height_mm` `PropertyValue.source` on a **box** spec. Neither `motors` nor `propellers` nor `frame_arm` carry `estimated_temporary` dims in any live project (A5's table shows all three as `declared`, not estimated) — the estimated-temporary plate hold blocks the **box family's** (`flight_controller`/`esc`/`battery`/`sensors`) fit attestation only, per `_plate_relation_row`'s own gate (`fit_relations_assist.py:175-188`), which the mount-only relations never touch. A disk-station Buy would ship independently of whether the plate-box hold ever clears.

---

## E. Explicitly out (confirmed, not touched by this investigation)

- Path N (disk-as-pose-origin) — not reopened; not needed by D2 (D2 compares a *radius*, never treats a disk as an origin/frame).
- No mm invented — D2's inputs are all already-cited facts (A5).
- No N seals — structurally already impossible to create per-copy seals; one `ComponentSpec` = one `declared_fit_attestation` field regardless of `motor_count`/`solidCopies` (A4).
- No cylinder-as-box — `screen_posed_envelope`/`compute_fit_attestation_fingerprint` are untouched by this investigation and by the D2 recommendation; D2 would live in a **new** module/function, never inside `pose_envelope_screening.py`.
- No `ASSEMBLY_READY` flip — not evaluated, not touched; `engineering_readiness.py` was not read as part of this investigation beyond confirming no other module already references `n_a_disk` (it does not — grepped repo-wide).
- No plate invent — D section confirms orthogonality.

---

## Summary for Cursor / Engineer

- **A** confirms `n_a_disk` is a hardcoded, unconditional stance (not a live shape check) and that no engineering pose has ever existed for a disk component in any project.
- **B** recommends **D2** (a new, narrowly-named radial-reach rule reusing the Visor's own already-shipped `_frame_arm_radial_offsets_mm` math) over D1 (proxy box, rejected as dishonest-by-indirection) and D3 (attest-without-screen, rejected as a double standard vs. the box family). D0 remains the correct close if the Engineer judges the reach-check's engineering value too thin.
- **C** recommends **`motors ↔ frame_arm`** as the first case — no new §0.1 bag needed, all facts already cited live.
- **D** confirms this work is fully orthogonal to the plate-box hold.
- **E** confirms nothing forbidden was touched or recommended.

No implementation performed. No files changed other than this report.
