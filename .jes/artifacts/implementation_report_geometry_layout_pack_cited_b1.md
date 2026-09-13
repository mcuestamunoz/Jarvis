# Implementation Report — Cited kit layout pack B1 (`B1-layout-pack-cited`)

**IC:** [implementation_contract_geometry_layout_pack_cited_b1.md](implementation_contract_geometry_layout_pack_cited_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2813 → **2830** (16 new layout-pack tests + 1 new craft-montage N1-regression test)

---

## §0.1 filled bag applied

`pack_id: hglrc_my5_flush_stack_b1` registered exactly as disclosed: `kit_frame_sku: hglrc_my5_5in`, `origin_key: frame_plate`, `requires_plate_box: yes`, 4 rows (`flight_controller`/`esc`/`battery`/`sensors`), authority string = "Engineer-confirmed Path F flush (supuesto) on estimated_temporary plate — smoke 2026-09-13, proyecto 10-min-autonomía" verbatim. The explicit exclusion list (motors/propellers, `frame_arm`, `frame_plate_2/3`, kit connectors) is enforced structurally — the pack registry's `rows` tuple simply never names them, and a dedicated test (`test_pack_never_names_motors_or_propellers_or_frame_arm`) proves the loop can't accidentally surface them even when present in the input.

## Honesty lock honored: formula-at-propose-time, not the bag's frozen floats

Per the IC's own instruction ("Prefer formula-at-propose-time... use §0.1 floats as test fixture expectations"), `propose_layout_pack` **never reads a z value out of the registry** — it recomputes `z = plate.height_mm/2 + child.height_mm/2` fresh from whatever boxes are live on the current project, every time. The bag's own worked-example numbers (4.9/5.0/15.5/8.2) are used **only** as the regression-fixture expectation in `test_t1_proposals_match_bag_worked_example_z_values` — proven independently in `test_t1_z_recomputed_live_not_frozen_bag_value`, which gives a different real ESC height and asserts a **different**, correctly-recomputed z, never the bag's frozen 5.0.

## Small, localized shared-helper extraction (not a large refactor)

Per lock #5 and the IC's own "same arithmetic as B1-craft-montage-path-f" instruction, I extracted the one-line flush-centered formula out of `craft_montage_stack_assist.propose_path_f_stack`'s inline body into a new public function, `flush_centered_z_mm(origin_geometry, child_geometry)`, and updated that call site to use it. This is the smallest safe scope for reuse (one arithmetic line, behavior-preserving — confirmed by re-running `test_geometry_craft_montage_path_f_b1.py`'s full 17 tests unchanged before writing any new code) — not a restructuring of that module's public shape, its dispatch, or any other function.

## Files changed

- **`src/jarvis/core/craft_montage_stack_assist.py`** — new public `flush_centered_z_mm(...)` helper; `propose_path_f_stack` now calls it instead of the inline formula (zero behavior change, re-verified). **Also**: applied the identical N1 fix described below back to this sibling module — `StackProposal` gained the same `kind == "done"` case (an already-posed subject now gets an explicit "✓ ya tiene pose declarada" row instead of silently vanishing), and `format_path_f_stack`'s empty-list message no longer risks the false "no hay una placa con caja" claim Cursor's review flagged as N1 on that Buy's own report. This is the same bug class as the one this cycle's own reproducibility check surfaced independently (see below) — fixing it in both modules in the same sitting avoided leaving a known, already-flagged defect unaddressed for a separate cycle. `tests/test_geometry_craft_montage_path_f_b1.py` gained 1 new test for this (`test_empty_list_means_no_plate_box_never_everything_done`) and one existing test's assertions were updated to match the corrected "done" semantics.
- **`src/jarvis/core/layout_pack_assist.py`** (new) — the `_PACKS` registry (currently one pack), `LayoutPackRow` (three kinds: `proposed` / `skipped` / **`done`** — see bug fix below), `propose_layout_pack(pack_id, components)`, `format_layout_pack(...)`, `resolve_layout_pack_trigger(...)`, `list_pack_ids()`.
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_layout_pack_assist` IDLE bridge, wired right after the Path F checklist bridge (same conceptual family), before the pose-declare/mount-declare bridges it hands confirmation off to.
- **`tests/test_geometry_layout_pack_cited_b1.py`** (new) — 16 tests covering T1–T4 plus trigger/exclusion/already-done coverage.

## A real bug found and fixed during the reproducibility check (not just a purge-style redirect)

Checking this Buy against both live projects (read-only — see below) surfaced a genuine defect in my own first draft: `autonomía-de-5min`'s four stack subjects **already have both a pose and a mount declared** (from the earlier Path F / mount-standard-assist live smoke and prior Situar-drag testing) — so `propose_layout_pack` correctly produced an empty proposal list for that reason, but `format_layout_pack`'s empty-list branch unconditionally said *"falta la caja de la placa de origen"* (missing plate box) — the **wrong** reason, since the plate box was present and fine. An empty list meant two different things (prerequisite unmet vs. everything already succeeded) and the copy silently assumed only the first. Fixed by adding a third `LayoutPackRow.kind == "done"` — a fully-declared subject now gets an explicit, honest "✓ ya tiene pose y montaje declarados" line instead of vanishing into an ambiguous empty list; a **genuinely** empty list now only ever means the plate-box prerequisite itself was unmet. Added `test_empty_list_means_prereq_unmet_never_everything_done` to lock this distinction in permanently, and re-verified the fix directly against `autonomía-de-5min`'s real data (see below).

## Fit-attestation / Path N gates untouched

`test_t4_disk_origin_still_rejected_by_writer_directly` re-confirms `set_component_declared_box_pose`'s disk-origin gate is unweakened (this pack's `origin_key` is always the hardcoded `frame_plate`, never a disk, but the writer's own defense is re-checked directly regardless, same discipline as `B1-craft-montage-path-f`'s own T7).

## Tests

Executed: `python -m pytest -q` → **2830 passed, 1 skipped** (0 failed; the 1 skip is pre-existing, unrelated). Ran the new file alone first (16 passed), then together with `test_geometry_craft_montage_path_f_b1.py` (34 passed combined, confirming the shared-helper extraction and the back-ported N1 fix didn't regress the sibling module) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_proposals_match_bag_worked_example_z_values`, `test_t1_pose_and_mount_phrases_parse_via_real_parsers` (both phrases round-tripped through the real, unmodified pose-declare and mount-declare parsers), `test_t1_z_recomputed_live_not_frozen_bag_value` |
| T2 | `test_t2_idle_pack_checklist_never_writes` |
| T3 | `test_t3_no_plate_box_yields_empty_honest_message`, `test_t3_idle_no_plate_box_honest_message` |
| T4 | `test_t4_disk_origin_still_rejected_by_writer_directly` |
| T5 | Full suite green above; `pyproject.toml` still `0.4.1` |

Additional coverage: unknown pack id, trigger resolution (bare vs named), the motors/propellers/frame_arm exclusion, already-posed-but-not-mounted (offers only the missing half), boxless-subject skip, and the "done" vs "empty" distinction from the bug fix above.

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **`10-min-autonomía`**: `flight_controller` and `sensors` still need a mount phrase (their pose was already confirmed during the prior Path F smoke); `esc` and `battery` show as `done` (both already fully declared). Matches that project's known history exactly.
- **`autonomía-de-5min`**: all four subjects show as `done` — every one already has both a pose and a mount from earlier, unrelated live testing. Before the bug fix above, this rendered as a false "missing plate box" message; after the fix, it correctly shows four "✓ ya tiene pose y montaje declarados" lines and the honest "nada pendiente" footer.

Also re-ran `craft_montage_stack_assist.propose_path_f_stack`/`format_path_f_stack` directly against both live files after back-porting the N1 fix there: both projects now correctly show all 4 subjects as "✓ ya tiene pose declarada" with the honest "nada pendiente" footer, instead of the previous false "no hay una placa con caja declarada" message for `autonomía-de-5min` (`10-min-autonomía` had reached the same fully-posed state independently, from the Engineer's own live smoke since the Path F cycle landed).

## Non-goals honored

No XY ever computed from anything but the literal `0`. No invention from GEP/MY5 body dimensions. No LLM. No "typical freestyle" row without a citation. No arm-as-subject / radial-beam-to-plate row (explicitly excluded, tested). No Product B claim. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty; the live-project reproducibility check used in-memory `ProjectState` objects only).

## Remaining risks / notes for review

- The registry (`_PACKS`) is a plain Python dict today, per the IC's own "code or JSON — numbers only from bag/formula" allowance — if a second pack is added later, `resolve_layout_pack_trigger`'s bare "layout pack" branch (`packs[0] if len(packs) == 1 else None`) will need a real disambiguation/listing path; not built now since only one pack exists and speculative branching for a hypothetical second pack isn't justified yet.
- The "done" row's checkmark (`✓`) is new UI vocabulary for this family of checklists (mount-standard-assist and craft-montage-stack use `·` for skipped only, no "done" concept existed there since neither combines two writers per subject) — worth Cursor confirming this reads clearly in context, since it's the first assist in this family to report a fully-complete subject explicitly rather than just omitting it.
