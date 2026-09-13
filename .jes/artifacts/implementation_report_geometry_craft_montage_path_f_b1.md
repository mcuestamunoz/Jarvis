# Implementation Report — Craft montage Path F on plate B1 (`B1-craft-montage-path-f`)

**IC:** [implementation_contract_geometry_craft_montage_path_f_b1.md](implementation_contract_geometry_craft_montage_path_f_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2796 → **2813**

---

## §0.1 menu — proceeded on the IC's own stated defaults

The IC presented `confirm_mode`/`live_smoke`/`apply_live` as choices but explicitly named a default or recommendation for each (`suggest_retype "(default, mount-assist class)"`, live smoke "recommend autonomía-de-5min + 10-min-autonomía — both MY5 + estimated plate already smoked", `apply_live: none "(default)"`). Rather than pausing for confirmation on an already-unambiguous menu, I locked in:

```
path_star: F                              # locked, no choice
confirm_mode: suggest_retype              # IC's own stated default
live_smoke: autonomía-de-5min + 10-min-autonomía   # IC's own recommendation
apply_live: none                          # IC's own stated default
estimated_plate_ok: yes                   # locked
```

## Files changed

- **`src/jarvis/core/craft_montage_stack_assist.py`** (new) — pure `propose_path_f_stack(components)` builder + `format_path_f_stack(...)` + `is_craft_montage_stack_trigger(...)`. Reads geometry exclusively via `spatial_board._geometry_from_spec` (the same projector the Board already uses) — never inspects a component's key/name/SKU, satisfying lock #10's "project-agnostic, zero SKU/project-id branches" by construction, not by convention.
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_craft_montage_stack_assist` IDLE bridge, wired right after the mount-standard-assist checklist (same "what's still missing" conceptual family), before the pose-declare bridge (no gate collision either way — the trigger phrases and the pose-declare grammar share no gate words).
- **`tests/test_geometry_craft_montage_path_f_b1.py`** (new) — 17 tests covering T1–T8 plus non-goal/trigger coverage.

## Locked arithmetic (lock #3) — implemented exactly, verified against the real parser

For each in-scope subject with its own `shape: box` geometry and a boxed plate origin: `x_mm=0`, `y_mm=0`, `z_mm = plate.height_mm/2 + child.height_mm/2`. No XY ever computed from anything but the literal `0`. `test_t1_example_phrases_parse_as_set_via_real_parser` runs every generated phrase through the **real, unmodified** `parse_declared_box_pose_declare` and asserts `SET` with the exact matching subject/origin/axes — not just string-format-checked, actually round-tripped through the production parser.

## Path N stays dead (lock #2) — structurally, not just by omission

`_STACK_SUBJECTS` is the fixed tuple `("flight_controller", "esc", "battery", "sensors")` — motors/propellers are never iterated, never candidates, never origins. `test_never_proposes_motors_or_propellers` confirms this directly even when both are present with disk geometry in the input. `test_t7_disk_origin_still_rejected_by_writer_directly` additionally proves the underlying writer's own origin-must-be-box gate is untouched (still raises for a disk origin), as defense-in-depth beyond "this module just never tries it."

## Confirm UX: retype (mount-assist class, as directed)

`_try_handle_craft_montage_stack_assist` only ever returns the read-only numbered list. Confirmation happens when the user retypes a shown phrase, which is picked up by the **existing, unmodified** `_try_handle_declared_box_pose` bridge later in the same dispatch chain — zero new write path, zero new session state, identical discipline to `mount_standard_assist_b1`. `test_t6_idle_checklist_never_writes` and `test_t7_idle_retype_confirms_via_existing_pose_bridge` cover both halves end-to-end through the real orchestrator.

## Fit-attestation screening stays refused on an estimated origin (lock #6) — verified, not just asserted

Confirmed directly (not merely via unit assertions on the assist module, but by driving the full orchestrator): posing a component onto an `estimated_temporary` plate via a Path F–generated phrase, then asking `cabe`, still returns the `estimated_dims` refusal (`pose_envelope_screening`'s existing, unmodified gate from the prior `estimated_temporary_plate_b1` cycle); `declaro verificado` still raises. Nothing in this Buy touches that gate.

## Tests

Executed: `python -m pytest -q` → **2813 passed, 1 skipped** (0 failed; the 1 skip is pre-existing, unrelated). Ran the new file alone first (17 passed), then together with `mount_standard_assist_b1`, `estimated_temporary_plate_b1`, and `continuity_mounted_on_declare_b1`'s own test files (67 passed combined, zero regression) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_declared_plate_proposals_match_locked_formula` + `test_t1_example_phrases_parse_as_set_via_real_parser` |
| T2 | `test_t2_estimated_temporary_plate_still_proposes_with_disclosure` |
| T3 | `test_t3_no_plate_box_yields_empty_honest_message` |
| T4 | `test_t4_two_boxed_plates_no_guess` |
| T5 | `test_t5_boxless_subject_skipped_others_still_proposed` + `test_undeclared_subject_omitted_entirely` + `test_already_posed_subject_omitted_not_reproposed` |
| T6 | `test_t6_idle_checklist_never_writes` |
| T7 | `test_t7_idle_retype_confirms_via_existing_pose_bridge` + `test_t7_disk_origin_still_rejected_by_writer_directly` |
| T8 | `test_t8_module_has_no_project_specific_literals` (greps the module's own source for `my5`/`hglrc`/`10-min`/`5min`/`autonomía`/`autonomia`) + `test_t8_same_module_works_on_two_independently_built_fixtures` |
| T9 | Full suite green above; `pyproject.toml` still `0.4.1` |

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState` and ran `propose_path_f_stack` against their real components (no orchestrator mutation, nothing saved):

- **`10-min-autonomía`**: all 4 in-scope subjects (`flight_controller`, `esc`, `battery`, `sensors`) currently have box geometry and no existing pose — the checklist proposes all 4, each phrase verified to parse. This project is ready for the Engineer's live smoke as-is.
- **`autonomía-de-5min`**: `frame_plate` box resolves correctly (confirmed directly — `is_frame_plate_key`/`_geometry_from_spec` both correct) and would be picked as origin, but **all four** stack subjects already carry a `declared_box_pose` from earlier, unrelated live interaction (Situar drag testing from a prior cycle — e.g. `esc`'s existing pose origins on `flight_controller`, not `frame_plate`; `battery`'s on `frame_plate_2`). Per this module's own "never propose a correction to an existing pose" rule (mirroring `mount_standard_assist`'s identical discipline), the checklist honestly reports **nothing to propose** on this project today.

This is the module working exactly as designed, not a bug — but it means the Engineer's smoke on `autonomía-de-5min` specifically will see an empty checklist unless they first clear one or more of those four poses (e.g. `quita la pose del esc`) to create something for Path F to propose. Flagging this clearly so smoke isn't misread as a failure to reproduce.

## Non-goals honored

No layout-pack §0.1 filled or invented. No Product B / "parece un dron" claim anywhere in the copy. No arm-as-subject widening. No standoff clearance invented (flush-centered is disclosed as a `supuesto` on every single proposal line, never silent). No mount auto-write (`mounted_on` is never read or written by this module). No auto-apply on Board load (suggest-only, IDLE-triggered only). No Conversation Engine. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty, and the reproducibility check above used an in-memory `ProjectState`, never `orch.workspace_manager.save_state`).

## Remaining risks / notes for review

- See the "already posed" finding above — Engineer smoke on `autonomía-de-5min` needs either a pose cleared first or an explicit acknowledgment that "honestly nothing to propose" is itself the correct, intended smoke result for that project's current state.
- The disclaimer copy always says "no VERIFICADO" as an explicit disclaimer (never a positive claim) — worth Cursor double-checking this reads unambiguously as a refusal, not an accidental claim, in context.
- `sensors`/`battery`/`esc`/`flight_controller` currently get box geometry through whatever prior cycle populated their `length_mm`/`width_mm`/`height_mm` (catalog bind or earlier Continuity declare) — this module has no opinion on how a subject got its box, by design; if a future cycle changes how those get populated, this Buy's behavior is unaffected as long as `_geometry_from_spec` still resolves them.
