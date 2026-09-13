# Implementation Report — Envelope stack rule B1 · B0 hold (`B1-stack-rule`)

**IC:** [implementation_contract_geometry_stack_rule_b1.md](implementation_contract_geometry_stack_rule_b1.md)
**Implementer:** Claude Code (doc-only — no code path opened)
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2763

---

## Outcome: B0 hold — Path N is schema-level impossible; Path F stays data-gated

Engineer ★'d **Path N only** (`propellers` posed on `motors`, confirm-by-retype). Before writing any module, I verified the writer/parser chain lock #6 mandates reusing (`set_component_declared_box_pose`, "no new pose schema") against the actual data model, and found Path N cannot ever be confirmed — not a missing-data gap like plate-box, a **structural** one:

1. **Neither side of the pair can ever be a box.** `_geometry_from_spec` (`src/jarvis/workspace/spatial_board.py:270-319`) requires the full `length_mm`/`width_mm`/`height_mm` triple for `shape: "box"`; a bare diameter always resolves to `"disk"`. `MotorSpec` (`src/jarvis/knowledge/library.py:37-83`) carries only `diameter_mm`/`stator_diameter_mm`/`stator_height_mm`/`height_mm` (an axial-height fact, explicitly documented at line 82 as never combining with `diameter_mm` into a box). `PropellerSpec` (`library.py:305-333`) carries only `diameter_in`. Neither type has ever had an `length_mm`/`width_mm` field — this isn't an uncited-yet fact, it's absent from the schema itself.
2. **The Continuity envelope-declare grammar deliberately forbids it too**, independent of catalog data: `declared_envelope_declare_assist._resolve_subject`'s own docstring (`src/jarvis/core/declared_envelope_declare_assist.py:282-305`) states its subject set is "never frame root/motors/esc/fc/propellers" — a user cannot manually declare a box for `motors` or `propellers` through the existing IDLE grammar even if they wanted to.
3. **The writer enforces this as a hard gate, not a soft default.** `set_component_declared_box_pose` (`src/jarvis/core/component_writers.py:295-345`) raises `ValueError` for any pose whose `origin_key` doesn't resolve to `shape == "box"` via `_geometry_from_spec` — a disk origin is rejected unconditionally (line 334-338).

Net effect: a "propeller posed on motors, N mm en Z respecto a los motores" phrase can be *displayed*, but retyping it to confirm — the exact UX lock #4 calls for — would **always** raise that `ValueError` and surface as an error, for every project, forever, regardless of how complete anyone's catalog citations become. Suggesting a phrase that can never successfully write would be a dishonest UX, not a suggest-only assist.

Asked directly, given Path N's blocker plus Path F's pre-existing data gate (plate-box B0 hold — [report](implementation_report_geometry_plate_box_b1.md)), the Engineer chose to **B0-hold the whole Buy** rather than ship an informational-only, never-confirmable sliver of Path N.

## Files changed

None in `src/`, `tests/`, `ui/`, `library/`, or `workspace/`.

- `.jes/artifacts/implementation_report_geometry_stack_rule_b1.md` (this file)
- `docs/IMPLEMENTATION_TASKS.md` — `B1-stack-rule` marked **B0 HOLD**, cola advanced
- `.jes/state/engineering_state.json` — tracking fields synced to the hold

## Behavior changed

**None.** No `stack_rule_assist.py` module was written; no new IDLE trigger exists; `set_component_declared_box_pose`, `_geometry_from_spec`, and `declared_envelope_declare_assist` were read but not modified.

## Tests

Not run for this cycle's own change (doc-only, nothing to regress). Confirmed empty code footprint: `git status --short -- src/ tests/ ui/ workspace/` returns nothing for this cycle. The existing suite (2763) was not re-run since nothing in scope for this IC could affect it.

## Non-goals honored

No new pose schema, no writer-gate weakening to force a disk origin through, no plate/arm L×W invention, no layout pack, no subject-vocabulary widen (motors/propellers were confirmed to stay non-subjects for envelope declare, exactly as already locked — this cycle's finding is that this exclusion is *why* Path N fails, not a reason to lift it). No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation.

## Remaining risks / notes for review

- **Path N cannot be revived by better data alone.** Unlike plate-box (blocked on a citation that could arrive tomorrow), Path N is blocked by the absence of L×W fields on `MotorSpec`/`PropellerSpec` and by `declared_envelope_declare_assist`'s deliberate subject exclusion. Reviving it would require either (a) a new geometry representation for rotationally-symmetric parts as pose origins — a genuine architecture change, out of scope for any "B1" suggest-assist — or (b) redefining Path N's origin to something other than the motor itself (e.g. a boxed mount point), which isn't what the IC specifies and wasn't asked for here.
- **Path F remains the only viable path forward for this Buy**, and it was already known to be blocked on plate-box data before this cycle. Once a filled §0.1 bag lands for `B1-plate-box` and that Buy closes, `B1-stack-rule` Path F (stack subjects centered on the now-boxed `frame_plate`) becomes newly implementable — worth re-opening this IC (or a successor) at that point rather than before.
- This finding should probably be folded back into the parent investigation's own record (`investigation_report_board_drone_default_layout_b0.md` §C) so a future reader doesn't re-propose prop-on-motor pose as a "narrow, implementable now" path — flagging for Cursor's review rather than editing that closed investigation report myself.
