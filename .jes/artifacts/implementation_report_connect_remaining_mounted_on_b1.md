# Implementation Report — Conn B1 (`mounted_on` subject/target parse symmetry)

**IC:** [implementation_contract_connect_remaining_mounted_on_b1.md](implementation_contract_connect_remaining_mounted_on_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2418

---

## Files changed

- `src/jarvis/core/mounted_on_declare_assist.py` — **§3.1**: in `parse_mounted_on_declare`'s SET branch, subject resolution is now scoped to the text **before** the first `\ben\b` (`subject_segment = normalized[:en_match.start()] if en_match else normalized`; `subject = _resolve_subject(subject_segment)`) instead of the whole phrase — the exact mirror of the target-segment discipline the same branch already applied. The `en_match` computation was hoisted above subject resolution (previously computed only after) so both segments share the one match object. The CLEAR branch is untouched, per lock #2 ("CLEAR branch: leave as-is") — it has no target segment to collide with.
  - **§3.2**: new `_resolve_target_component_alias(normalized, components) -> str | None`, added as the last fallback inside `_resolve_target` (after exact-key, plate-label, arm/cage/standoff/frame-root, and bare-plate resolution all fail) — scans the target segment with the same `_SUBJECT_PATTERNS` table, in the same fixed priority order, and returns a canonical key **only when that key is already present in `components`**. Never invents a key absent from the project (verified by a dedicated test, below).

## Behavior changed

- `"helices montadas en los motores"` now resolves to `SET(component_key="propellers", target_key="motors")` — previously misresolved the subject to `"motors"` (since "motores" also matches the `motors` subject pattern, which outranks `propellers` in the fixed priority table) and then failed to find any target at all.
- `"sensor montado en el esc"` now resolves to `SET(component_key="sensors", target_key="esc")` — previously misresolved the subject to `"esc"` too, producing a same-key `SET(esc, esc)` that the writer correctly rejected as a self-mount, but with a confusing "esc no puede estar montado en sí mismo" message for a sentence that never said that.
- Verified live against the **real** demo project (`workspace/autonomía-de-10min-9ada1a1b0cca`, read-only — `git status --short workspace/` is clean): the exact phrase from the investigation's own evidence, `"helices montadas en los motores"`, now parses to `SET(propellers, motors)` against that project's real, live component set.
- No change to `_resolve_target`'s existing resolution order (exact key → plate label → arm/cage/standoff/frame root → bare plate) — the component-noun alias is strictly a **last-resort fallback**, confirmed by `test_t6c_non_regression_arm_target_unaffected_by_alias_fallback` (an arm-target phrase still resolves via the existing `_ARM_RE` path, never falls through to the alias).
- Frame parts (`frame_arm`/`frame_plate*`/`frame_cage`/`frame_standoff`) still have **zero subject-noun pattern** — confirmed unchanged; they remain target-only, per the investigation's own §4(C) recommendation and this IC's lock #5. No new vocabulary was added to `_SUBJECT_PATTERNS` itself — the alias fallback reuses the existing table verbatim.
- `set_component_mounted_on` (the writer) was not touched, not imported differently, and its self-mount/target-existence guards are unchanged — confirmed via `git diff --stat` showing zero lines changed in `component_writers.py`.

## Tests

Executed: `python -m pytest -q` → **2429 passed**, 0 failed (baseline 2418 + 11 new, all in the single new file `tests/test_connect_remaining_mounted_on_b1.py`). Ran the new file alone first (11 passed), then the two pre-existing `mounted_on`-related test files together (`test_geometry_assembly_espacial_b1.py` + `test_continuity_mounted_on_declare_b1.py`, 30 passed, confirming zero regression in the prior cycle's own coverage) before the full suite.

Test breakdown against §4: T1/T3 (the two collision phrases, both variants — "helices montadas en..." and "monta las helices en..." — now `SET(propellers, motors)`); T2 (sensor→esc, asserted `component_key != target_key` explicitly, never a self-mount); T4–T6 non-regression (literal-key phrasing, the 2+-plate ambiguity still refusing to guess, and the CLEAR phrase); plus two extra regression guards beyond the IC's own table — `test_t6b` (the pre-existing "esc can't resolve as its own target" case, now re-verified under segment-scoped subject resolution) and `test_t6c` (an arm-target phrase proving the new alias fallback never pre-empts the existing, more specific target-resolution steps) — and one dedicated honesty test (`test_target_alias_never_invents_a_key_absent_from_components`) proving the alias never fabricates a target for a component that isn't actually declared. T7 (orchestrator IDLE persistence for both fixed phrases, via `handle_user_text`, confirming the fix reaches all the way to a saved `ProjectState`).

## Non-goals honored

No frame-part subject vocabulary added — `_SUBJECT_PATTERNS` itself is unchanged; the alias fallback only ever resolves to a key already in that same table, reused, not extended. No auto-inference — every resolved target in every test still traces to an explicit noun the user typed matching an explicit, already-declared component; the alias never guesses among ambiguous candidates or fabricates a key. No writer change — `component_writers.py` untouched, confirmed via diff. No Board/UI file touched. No seed file touched. No pose/fit/Conversation-Engine/Here3-identity work opened. No package version bump (`pyproject.toml` still `0.3.8`). No test weakened — the new file is entirely additive; the two pre-existing `mounted_on` test files were re-run unmodified and still pass in full.

## Remaining risk / notes for review

- The component-noun alias fallback is scoped to `_SUBJECT_PATTERNS`'s existing six keys (`flight_controller`, `esc`, `motors`, `battery`, `sensors`, `propellers`). If a future cycle adds a new subject noun to that table, it becomes a valid target alias automatically too — this is the intended, symmetric behavior (the same table now serves both roles), not a side effect to guard against, but worth naming for whoever next edits that table.
- As anticipated by the investigation, this fix is narrow by design: it does not add any new way to *discover* that propellers/sensors are unmounted (no "qué falta por montar" status line — explicitly deferred as B1+, out of scope here). A user still has to know to type the mount phrase.
