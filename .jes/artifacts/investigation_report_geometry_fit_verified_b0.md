# Investigation Report — Fit VERIFIED (beyond AABB screening)

**IC:** [investigation_contract_geometry_fit_verified_b0.md](investigation_contract_geometry_fit_verified_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-10
**Checkpoint:** package `0.4.1` · suite 2669 · UI 80 · tag `v0.4.1` / `checkpoint-board-situar`

**Do not implement — this is a read-only report. No `src/`/`ui/`/`library/` edit made. No `workspace/` mutation. No version bump.**

---

## Executive summary

**Recommended: `B1-attest`** — a new, explicitly HUMAN-attributed "declared verified by the Engineer" mark on one already-screened posed pair, gated on `screening.status == "overlap"` and automatically invalidated the moment the pose or either box's geometry changes afterward (reusing the codebase's own already-shipped "divergence clears a stale label" pattern from `catalog_bind.py`, not a new mechanism). This is the smallest Buy that lets Jarvis honestly say the word "verified" — because the evidence is a human sign-off, not a stronger geometric proof, and the copy must say so explicitly, never bare "VERIFIED." **`B0` (never ship the word, keep screening forever) remains fully legitimate and arguably safer** — the live tree gives no evidence that a *better geometric* evidence class is available without CAD/MEASURE, and every stronger-geometry candidate (margin, multi-hop, mating faces) either doesn't actually change the evidence class or requires a genuinely large new declared-data concept. `ASSEMBLY_READY`/PASS stay **byte-identical** under the recommended Buy — confirmed via code inspection, `engineering_readiness.py` has zero references to pose/screening today.

---

## A. Screening as-is (evidence)

`pose_envelope_screening.py` is the ONE helper (`screen_posed_envelope`/`format_screening`), shared verbatim by the Board's `"sobres"` card field (`spatial_board.py:671-674`) and the IDLE `"cabe"` query (`orchestrator.py:2147-2204`) — confirmed no divergent copy exists between the two surfaces.

**What it proves:** for a child `ComponentSpec` with a complete `declared_box_pose` (all three axes present) whose `origin_key` resolves to another spec with `geometry: box`, and whose own geometry is also `box` — that the two axis-aligned bounding boxes, centered at declared-mm `(0,0,0)` for the origin and `(x_mm, y_mm, z_mm)` for the child, overlap in **every** axis (`pose_envelope_screening.py:92-95`, `abs(axis_values[i]) <= child_half[i] + origin_half[i]`).

**What it explicitly does NOT prove** (module docstring, `pose_envelope_screening.py:1-20`, and locked copy, `:99-125`):
- Not orientation/rotation — the AABB test is axis-aligned only, no rotation ever declared or checked.
- Not containment — "overlap" only means the two boxes' extents intersect somewhere in each axis; a child box could be 95% outside the origin and still register `overlap` if any sliver intersects in all three axes.
- Not collision with any THIRD sibling — pairwise only, single-level (never composes an origin chain).
- Not `mounted_on` — "never reads `mounted_on`" is stated verbatim in the module docstring (`:19-20`); a pose's own declared origin is the only relationship compared, independent of physical attachment.
- Every status string is suffixed `"— screening, no verificado"` (overlap/no_overlap) or an equivalent "Jarvis no verifica ensamblaje físico" phrasing (`origin_unusable`/`child_not_box`/`no_pose`) — the forbidden tokens (`"cabe"`, `"no cabe"`, `"VERIFIED"`, `"ensamblado"`, `"misfit geométrico"`) do not appear anywhere in `format_screening`'s six branches (confirmed by reading all of them, `:99-125`).

**Orthogonal, already-shipped LEVEL A mechanism** (do not merge, per the parent IC's own lock #7 and Structure A's own docstrings): `project_closure.frame_class_compatibility_state` (`project_closure.py:161-192`) and its Gap builder `engineering_readiness._frame_class_gaps` (`engineering_readiness.py:885-905`) compare propeller diameter vs. frame `size_class_inch` — a completely different, non-geometric, class-compatibility check. Its own docstring states verbatim: *"Class-compatibility screening (LEVEL A), never a geometric fit proof — forbidden copy (VERIFIED / "cabe" / "no cabe" / "misfit geométrico") is kept out of both the gap title and the evidence facts"* (`engineering_readiness.py:889-891`). This confirms the codebase already enforces the exact same honesty discipline on a second, unrelated surface — good precedent, zero connection to pose/AABB screening (grep confirms `engineering_readiness.py`/`project_closure.py` never import `pose_envelope_screening` or read `declared_box_pose` at all).

**`ASSEMBLY_READY` rollup** (`engineering_readiness.py:1199-1211`, `_derive_overall`) is driven entirely by Gap severity and per-subsystem `PASS`/`WARNING` verdicts — confirmed by direct read, it contains no reference to pose, screening, or geometry at all. Lock #9's default ("byte-identical unless Engineer ★ explicitly buys a change") is trivially satisfiable by any Buy that doesn't touch this file.

---

## B. Live complete posed box–box pairs

Read-only census (never mutated), post-Board-Situar:

| Project | Posed pairs (both boxes, all 3 axes) | `overlap` | `no_overlap` | Disks posed | Notes |
|---|---|---|---|---|---|
| `autonomía-de-5min` | **14**: `esc`, `battery`, `flight_controller`, `sensors`, `frame_plate_2..6` (5), `frame_cage`, `frame_standoff`, `power_connector`, `signal_harness`, `prop_adapter` | 6 | 8 | 0 | `frame_plate_2`'s offsets are non-round floats (`-0.99…, -1.35…, -3.21…`) — clearly Board-drag-authored, not CLI-typed; confirms Situar (C-113) is genuinely populating real pose data, not just a lab demo. |
| `autonomía-de-10min` | 1: `esc` vs `flight_controller` | 1 | 0 | 0 | Everything else on this project is still unposed. |

Zero disks carry a `declared_box_pose` on either project today — the writer's own box-origin gate plus "disk stays disk" hold without any special-casing needed here.

**A striking finding, directly relevant to any VERIFIED design:** on the live 5min project, **8 of 14** complete posed pairs already resolve to `no_overlap` — i.e., the Engineer has dragged pieces to positions that do not even mutually overlap in AABB space (e.g. `prop_adapter` at `(81, 81, 16)` vs. its origin plate, `power_connector`'s and `signal_harness`'s siblings differing only in overlap outcome despite identical-looking offsets). This confirms empirically that **nothing in the current write path gates on screening at all** — `set_component_declared_box_pose` (`component_writers.py:295-347`) checks only self-origin / undeclared-origin / non-box-origin, never overlap — a drag (or a typed `declara…`) can freely produce a position screening itself calls `no_overlap`, and it saves without complaint. Any VERIFIED design MUST treat `no_overlap` as a hard disqualifier, never something a human can "attest" past silently.

**Live UX consequence of the growing pose count:** `_try_handle_cabe_screening`'s bare-"cabe" fallback (`orchestrator.py:2181-2196`) lists every posed key and asks "¿Cuál componente?" once 2+ exist — with 14 posed keys today, a bare "cabe" on 5min now returns a 14-way disambiguation prompt. Not broken, but worth naming: the existing UX was designed for "one or two posed things," and Situar's own success is quietly stressing it. Out of scope for this investigation (not a VERIFIED design question), flagged for awareness only.

---

## C. Candidate meanings of VERIFIED (honest menu)

| ID | Evidence required | Code touched | Risk of lying | Lean |
|---|---|---|---|---|
| **V0** | None — screening stays the ceiling forever | None | Zero | **IN** (fully honest, zero-risk default) |
| **V1-attest** | An explicit Engineer action ("declaro verificado") on ONE already-`overlap`-screened pair, invalidated the instant pose/geometry changes | New attestation field + writer (mirrors `set_component_declared_box_pose`'s own discipline) + new IDLE phrase/Board button + new, distinctly-labeled copy | Low, IF invalidation is airtight and copy always says "declarado por el Engineer," never bare "VERIFIED" | **IN — recommended** |
| **V1-margin** | Engineer additionally declares a required clearance/inset (mm) beyond raw AABB overlap | Extends `pose_envelope_screening.py`'s comparison with a margin term | Low on its own, but does NOT change the evidence class — still numbers-vs-numbers, still no orientation/containment check | **OUT for the word "VERIFIED"** — a legitimate *stricter screening* rung, not a graduation |
| **V1-compose** | Multi-hop AABB across a chain of poses (child→origin→origin's-origin→…) in the DECLARED mm frame (never the visor's Y↔Z/omitted-axis-0 convention) | New composition helper in the engineering module (NOT `scene3dLayout.ts`) — cycle detection, partial-chain handling | Moderate — "walked more hops" can *read* as more rigorous to a user even though the underlying evidence (an AABB approximation) hasn't strengthened at all; a composition bug is subtle and could silently mis-locate a distant pair | **OUT for "VERIFIED"** — same evidence class, broader reach; a separate, differently-named screening extension if ever wanted, not a claim upgrade |
| **V1-faces** | Engineer additionally declares WHICH face of the child mates with WHICH face of the origin (+ optional flush/offset tolerance) | New schema concept (declared mating face/orientation), new writer, new UI to specify a face, updated screening math | Still declared-only (Jarvis trusts the Engineer's face claim, not a measurement) — but the closest analog to real tolerance-stack practice among the geometry-only options | **OUT for this Buy** — genuinely the most "engineering-honest" geometric option, but by far the largest new-concept lift; name as a possible LATER rung, not the minimum first Buy |
| **V-forbidden** | (n/a) | (n/a) | Certain | **OUT, explicitly.** Renaming `overlap`→"VERIFIED" is an empty rename (locked stance #1). Flipping `ASSEMBLY_READY`/PASS from AABB alone is forbidden (#9's default, and nothing in the live Gap/readiness code even reads pose today — §A). Any use of `scene3dLayout.ts`'s Y↔Z/omitted-axis-0 convention as engineering evidence is forbidden (#5) — that convention is presentation-only by the visor module's own docstring. Inventing a Rooster frame box to "verify against" is forbidden (#7; Plate L×W is still B0). |

**Why `V1-attest` and not a stronger-geometry candidate:** every stronger-geometry option (margin, multi-hop, mating faces) either (a) doesn't actually change what KIND of evidence Jarvis holds — it's still declared numbers compared by an AABB-shaped rule, so calling the result "VERIFIED" would overstate confidence exactly as much as today's screening already correctly declines to — or (b) requires a genuinely new declared-data concept (mating faces) that is a legitimate future rung but not a minimum Buy. `V1-attest` is the only candidate whose evidence class is *categorically different* from AABB screening (a human's own judgment, not a computed fact) and therefore the only one that can honestly carry a stronger word than "screening" — provided, and only provided, the copy makes that human-vs-machine distinction unmistakable every time it's shown.

---

## D. Recommended Buy: `B1-attest`

**Product sentence:** *"El Engineer puede marcar un par ya solapado (screening) como verificado por su propio criterio — Jarvis nunca lo deriva solo, y el sello se borra automáticamente si la pose o las cajas cambian después."*

**Sketch (name-only, NOT designed here, no code written):**
- A new field, e.g. `fit_attestation: FitAttestation | None` on `ComponentSpec` (or a small sibling record), holding: `attested: bool`, a **fingerprint** of `(child geometry L×W×H, origin geometry L×W×H, pose x/y/z, origin_key)` at attestation time, and a timestamp — mirroring, not inventing, the ALREADY-SHIPPED "divergence clears a stale label" pattern documented in `catalog_bind.py`'s own module docstring (*"the shared divergence check that clears `catalog_ref` when a later mutation moves a physical number away from what the bound SKU actually is"*, `catalog_bind.py:4-6`). Any subsequent write through `set_component_declared_box_pose` or `set_component_declared_box_envelope` (on either the child or the origin) that changes the fingerprinted values clears the attestation — same discipline, new field.
- A new writer (mirrors `set_component_declared_box_pose`'s own gate order): requires `screen_posed_envelope(...).status == "overlap"` — `no_overlap`/`pose_incomplete`/`origin_unusable`/`child_not_box`/`no_pose` all reject the attestation attempt outright, never a partial or silent grant. This closes the exact gap named in §B (8 of 14 live pairs are `no_overlap` today — none of those could ever be attested).
- A new, DISTINCT copy string, never reusing or mutating `format_screening`'s existing six branches: something like *"Declarado verificado por el Engineer el {fecha} — no es una comprobación geométrica de Jarvis."* — the word "VERIFIED"/"verificado" appears ONLY in this new, explicitly human-attributed sentence, never retroactively applied to the existing screening copy.
- A new IDLE phrase (e.g. `"declaro verificado el <sujeto>"`) and/or a Board button, both name-only here — reusing the SAME subject-noun resolution `_try_handle_cabe_screening` already uses (`mounted_on_declare_assist.resolve_component_subject_noun`), no new alias table.
- `ASSEMBLY_READY`/Gap Registry: **untouched** (default, per lock #9) — attestation is a Board/Continuity-visible fact only in this Buy; whether a later Buy ever feeds it into readiness is an explicit, separate future decision, not assumed here.

**Non-goals (this Buy):** no CAD/FEA/STEP, no clearance margin math, no multi-hop composition, no mating-face schema, no `ASSEMBLY_READY` change, no Rooster box, no version bump.

---

## E. Explicitly out

CAD · FEA · STEP-in-core · Conversation Engine · System Optimization · HD-* · inventing Rooster L×W (Plate L×W stays B0) · N≠4 standoffs / IDLE part count / sourced dims #4 (all named orthogonal in the parent IC) · re-implementing or reopening `pose_envelope_screening.py`'s existing AABB rule · implementing `implementation_contract_geometry_assembly_fit_compare.md` (confirmed still explicitly marked "QUEUED STUB — superseded... Do not implement this file," `:6`) · any change to `scene3dLayout.ts`'s own Y↔Z/omitted-axis convention · any code (none written — confirmed via `git status --short` showing no `src/`/`ui/`/`library/` diff introduced by this investigation).

---

## Incidental finding (unrelated to Fit VERIFIED, flagged for awareness only)

While confirming the live suite count, `python -m pytest -q` showed **1 pre-existing failure** unrelated to this investigation: `tests/test_geometry_prop_adapter_visor_x_b1.py::test_p6_library_and_version_untouched` asserts the literal string `'version = "0.4.0"'`, which no longer matches `pyproject.toml`'s current `0.4.1` (bumped by a later, unrelated cycle after that test was written). Not touched here — fixing a test file would be `src/`-adjacent edit work forbidden under this Investigation Contract's own "do not implement" mandate. Left for the next Implementation Contract's own scope, whatever it is.

---

## Done-when checklist

- [x] Report at the required path; answers A–E with live `file:line`/live-key citations
- [x] Single recommended Buy (`B1-attest`), with `B0` presented as a fully legitimate, not-strawman alternative
- [x] No `src/`/`ui/`/`library/` edits (confirmed via `git status --short`, empty)
- [x] No `workspace/` mutation (read-only throughout)
- [x] No version bump
- [x] Historical stub filename not implemented
