# Implementation Report — Mount standard assist B1 (`B1-mount-standard-assist`)

**IC:** [implementation_contract_mount_standard_assist_b1.md](implementation_contract_mount_standard_assist_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2747

---

## Files changed

- **`src/jarvis/core/mount_standard_assist.py`** (new) — pure, suggest-only module. `MountSuggestion` frozen dataclass (`subject`, `kind: "suggested"|"ambiguous"`, `target`, `example_phrase`, `reason`, `candidates`). `build_mount_standard_checklist(components) -> list[MountSuggestion]` computes undeclared, in-scope edges from the **current** `ProjectState.design_properties.components` dict — never a cached/smoke assumption. `format_mount_standard_checklist(...)` renders the locked Spanish copy. `is_mount_standard_assist_trigger(user_input)` gates the two locked trigger phrases. Calls no writer, imports no writer.
- **`src/jarvis/core/orchestrator.py`** — added `_try_handle_mount_standard_assist(self, user_input) -> dict | None`, mirroring `_try_handle_mounted_on_declare`'s structure exactly (gate → `_safe_active_project()` → build → format → return `{"status": "ok", ...}`; returns `None` when not a trigger, so the phrase falls through to normal routing unchanged). Wired into the IDLE dispatch chain immediately after the existing mount-declare bridge and before the catalog-refresh bridge (same file, ~line 998–1010), following the identical `if current_session.mode == OrchestratorMode.IDLE: result = self._try_handle_X(...); if result is not None: self._track_turn(...); return result` pattern every other IDLE bridge in this file uses.
- **`tests/test_mount_standard_assist_b1.py`** (new) — 16 tests.

No other file touched. No writer, no pose, no Scene3D, no plate/geometry file, no `workspace/` file.

## In-scope edges implemented (per IC §0 lock #2)

| Edge | Target rule |
|---|---|
| `propellers → motors` | fixed |
| `motors → frame_arm` | only suggested when `frame_arm` is itself a declared component; otherwise the edge is skipped entirely (no "add frame_arm" suggestion — that's a separate, out-of-scope vocabulary question) |
| `esc / flight_controller / battery / sensors → airframe` | single `frame_plate*` key when exactly one is declared; else bare `frame` when declared; else no suggestion at all. Two or more plates → `kind="ambiguous"` row listing the candidate keys, never a guess |

Per the IC's own §0 lock #3 ("prefer the single best target rule"), `sensors` is treated identically to the other three stack components (single-plate-or-frame), not specially routed to `esc` — the investigation's `sensors→esc` example was one project's particular choice, not a more "standard" target, so no differentiated rule was introduced for it.

A stack subject already carrying **any** `mounted_on` value (even one this rule wouldn't itself pick) is treated as declared and omitted — the checklist never proposes "correcting" an existing, presumably intentional, Engineer-declared relation. `frame_arm → plate`, connector/harness as subjects, and any pose/Δmm stay entirely absent from the builder — there is no code path that could produce them.

## UX design decision: retype-the-phrase (not number-pick)

IC §0 lock #5 allows either "confirm write" (typing a number replays the writer) or "user retypes the phrase; either OK if documented." I implemented **retype-the-phrase**: the assist only ever returns a read-only, numbered message. Confirmation happens by the user typing the shown (or an ambiguous row's completed) phrase in a later turn, which is picked up by the **existing, unmodified** `_try_handle_mounted_on_declare` bridge — zero new write path, zero new session-state, zero changes to `component_writers.py` or `mounted_on_declare_assist.py`. This is the thinnest implementation that satisfies the lock, and avoids introducing the heavier numbered-pick/session-state machinery used elsewhere (e.g. DEFINE_MISSING) for what is a stateless, one-shot discoverability read.

## Locked trigger phrases (IC §0 lock #5)

- `"montajes estándar"` (accent/case-insensitive)
- `"qué falta montar"` (accent/case-insensitive)

Normalized via the same `_normalize_help` (accent-strip + lowercase) used by every other IDLE phrase gate in this codebase (`motor_catalog_assist`, `catalog_refresh_assist`).

## Tests

Executed: `python -m pytest -q` → **2763 passed**, 0 failed (baseline 2747 + 16 new, all in the single new file). Ran the new file alone first (16 passed), then together with the two pre-existing `mounted_on`-declare test files (`test_continuity_mounted_on_declare_b1.py` + `test_connect_remaining_mounted_on_b1.py`, 43 passed combined, confirming zero regression) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_all_edges_undeclared_full_checklist` (full 6-edge fixture incl. `frame_arm`) + `test_t1_empty_project_no_suggestions` (explicit empty-project case) |
| T2 | `test_t2_5min_shaped_declared_edges_omitted` (prop→motors, esc→plate already declared → omitted, motors→arm still missing → still suggested) + `test_t2_stack_component_mounted_elsewhere_not_resuggested` (already-mounted-on-anything honesty guard) |
| T3 | `test_t3_no_frame_arm_skips_motor_arm_edge` |
| T4 | `test_t4_ambiguous_two_plates_no_silent_pick` (candidates listed, `target is None`) + `test_t4_ambiguous_subject_already_mounted_not_resuggested` |
| T5 | `test_t5_every_suggested_phrase_parses_as_set` (every suggested row's `example_phrase` run through the **real** `parse_mounted_on_declare`, asserted `SET` with matching subject/target) + `test_t5_ambiguous_candidate_phrase_parses_as_set_once_named` (each ambiguous row's candidate, once named in a phrase, parses as `SET`) |
| T6 | full suite green above; `pyproject.toml` still `0.4.1` (checked below) |

Additional coverage beyond the table: trigger-phrase recognition (`test_trigger_montajes_estandar`, `test_trigger_que_falta_montar`, `test_trigger_unrelated_phrase_is_false`) and four orchestrator IDLE integration tests — checklist lists missing mounts and never writes (`test_idle_checklist_lists_missing_mounts_never_writes`), checklist shrinks after a phrase is retyped and declared (`test_idle_checklist_shrinks_after_declaring_one`), empty-project honest message including the explicit "no es ASSEMBLY READY ni una pose" disclaimer (`test_idle_checklist_empty_project_honest_message`), and non-regression confirming a literal `"monta X en Y"` phrase still hits the pre-existing declare bridge first, not this new trigger (`test_non_regression_mount_declare_bridge_still_first`).

## Non-goals honored

- **No pose / Δmm**: the builder never reads or writes `declared_box_pose`; no coordinate, offset, or stacking rule appears anywhere in the module.
- **No plate L×W invention**: `_plate_target` only ever reads existing `is_frame_plate_key` membership — it never inspects geometry or invents a dimension.
- **No subject-vocabulary widening**: `frame_arm`, `power_connector`, `signal_harness` are never treated as mount subjects — the builder only ever emits `subject` values from the six keys already in `mounted_on_declare_assist._SUBJECT_PATTERNS`, and `frame_arm` only ever appears as a **target**, exactly as that module already locks. Confirmed by inspection — no new regex or alias table was added to the parse module itself (it was not touched at all).
- **No Board Situar layout, no Three.js**: no UI file touched.
- **No silent write**: `build_mount_standard_checklist`/`format_mount_standard_checklist` call no writer; `component_writers.py` was not imported by the new module and was not modified (confirmed via `git diff --stat component_writers.py` showing no change from this cycle's edits).
- **No version bump**: `pyproject.toml` still reads `version = "0.4.1"`.
- **No `workspace/` mutation**: `git status --short -- workspace/` is empty.
- **No test weakened**: the new file is entirely additive; both pre-existing `mounted_on`-related test files were re-run unmodified and still pass in full.

## Remaining risks / notes for review

- The "already mounted on anything is declared" honesty guard (for stack subjects) means a component intentionally mounted on a non-standard target (e.g. `sensors → esc`, seen in one live project) will never resurface in this checklist even though it differs from the rule's own "single best target." This is the intended, documented behavior (§5 of this report and the IC's own "discoverability, not new physics" framing), not an oversight — but it means the checklist cannot be used to detect a *sub-optimal* (as opposed to *missing*) mount.
- The retype-the-phrase UX means a user who only sees the numbered list still has to type the shown Spanish phrase verbatim (or a close enough paraphrase the existing parser already accepts) — there is no number-to-writer shortcut in this cycle. If Engineer smoke finds this friction unacceptable, wiring a numbered pick would be a small, additive follow-up (still reusing `set_component_mounted_on`), not a redesign.
- `motors → frame_arm` is entirely skipped (not even listed as "add frame_arm first") when `frame_arm` doesn't exist — per IC §0 lock #4/§4, `frame_arm`-as-subject and any BOM-structure suggestion are explicitly out of scope for this Buy.
