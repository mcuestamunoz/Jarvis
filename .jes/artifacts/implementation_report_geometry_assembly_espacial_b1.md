# Implementation Report — Geometry Assembly Espacial B1 (`mounted_on` relation-only)

**IC:** [implementation_contract_geometry_assembly_espacial_b1.md](implementation_contract_geometry_assembly_espacial_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2350

---

## Files changed

- `src/jarvis/schemas/action_schema.py` — **§3.1**: added `ComponentSpec.mounted_on: str | None = None`, additive, right after `parent_key`. Docstring states it is orthogonal to `parent_key` (frame BOM topology, always literal `"frame"`), names any key in `design_properties.components` (including ordinal frame-part keys like `frame_plate_1`), is always a declared relation (set only via the new writer, never inferred), and carries no pose/fit semantics. `extra="ignore"` was already on `ComponentSpec`; every existing/serialized project deserializes unchanged with `mounted_on=None`.
- `src/jarvis/core/component_writers.py` — **§3.2**: added `set_component_mounted_on(project_state, component_key, target_key) -> ProjectState`, placed right after `clear_frame_part_children` (grouped with the other frame/relation writers). Behavior exactly as locked:
  - `target_key=None` clears the relation — idempotent, returns `project_state` unchanged (same object, no spurious copy) when already `None`.
  - `target_key` set requires both `component_key` and `target_key` to exist in `components` and to differ — raises `ValueError` on a missing component, a missing/dangling target, or a self-mount, rather than storing a dangling reference.
  - Never touches `parent_key`, never inspects Board layout, never infers a target.
- `src/jarvis/workspace/spatial_board.py` — **§3.3 (N2)**: `_fields(spec)` appends `{"label": "montado en", "value": spec.mounted_on}` after the existing property/SKU fields, only when `spec.mounted_on` is truthy. No change to `_geometry_from_spec`, `_emit`, `place`/`place_slot`, `kind`, lane index, or `x`/`y` computation — `mounted_on` is purely an extra text field on whatever card the spec already produces. Module docstring extended with one paragraph naming this capability and its `parent_key` orthogonality, matching the file's existing per-capability documentation pattern.
- `tests/test_geometry_assembly_espacial_b1.py` (new file) — 14 tests covering all of §4: schema default/round-trip/orthogonality (3), writer set/reject-missing-target/reject-missing-component/reject-self-mount/clear/idempotent-clear (6), Board field-present/field-absent/kind-and-layout-unchanged (3), non-regression for `parent_key`/`clear_frame_part_children` (2).

## Behavior changed

- `ComponentSpec` gained one new optional field. Any project state without it behaves identically to before (`mounted_on=None`).
- A caller can now declare "component X is mounted on component/part Y" via `set_component_mounted_on`, which enforces that both keys exist and are distinct before storing the relation — no dangling references can be created through this writer.
- The Board now shows a plain `"montado en: <target key>"` text field on any component/part card whose spec has `mounted_on` set — confirmed via test that this does **not** change the card's `kind` (`"component"` stays `"component"`, only `parent_key` drives `"part"`), lane placement, or pixel `x`/`y`.
- `parent_key`'s own semantics, writers (`upsert_frame_part`, frame catalog bind), and consumers (`clear_frame_part_children`, BOM peer-exclusion, Board lane grouping) are byte-identical to before — confirmed via `git diff --stat` showing zero lines changed in any `parent_key`-related logic, and via a dedicated regression test proving `clear_frame_part_children` still filters strictly on `parent_key == "frame"` and leaves a `mounted_on`-bearing, non-frame-part component (`motors`) untouched.
- No UI (`ui/spatial-board/**`) file was changed — confirmed the existing `SpatialCard.tsx` renders `node.fields` generically (`node.fields.map(...)` into a `<dl>`, no hardcoded label set) and `types.ts`'s `SpatialNode.fields: {label: string; value: string}[]` already accommodates an arbitrary new label, exactly as the IC anticipated ("No UI React changes required if the generic fields renderer already displays arbitrary labels").

## §3.5 — Continuity / CLI copy (deferred, as explicitly permitted)

No orchestrator/CLI call site was added to invoke `set_component_mounted_on` from user free text or a wizard step. This IC ships the writer, the schema field, and the Board display only — reachable today via direct calls to `set_component_mounted_on` (e.g. from a script, a future orchestrator handler, or a test) but with no user-facing "declara que el FC está montado en la placa 1"-style entry point yet. This is named here explicitly per the IC's own §3.5 allowance ("If no user-facing set path ships, state that explicitly in the report"). No "ensamblado"/"cabe" copy was added anywhere — the only new user-visible string is the Board's own `"montado en"` field label, which states a declared relation and nothing more.

## Tests

Executed: `python -m pytest -q` → **2364 passed**, 0 failed (baseline 2350 + 14 new, all in the single new file `tests/test_geometry_assembly_espacial_b1.py`). Ran the new file alone first (14 passed) before the full suite. No existing test was modified or weakened.

## Non-goals honored

No position, orientation, offset, or face/side field added anywhere. No fit/clearance/intersection check. No Board canvas edge/line drawing (B2 deferred, per lock). No Board layout/`localStorage` ever read as physical truth (unchanged — still entirely client-side, still nothing in Python reads it). No inference of `mounted_on` from Board `x`/`y`, BOM co-membership, or cardinality-of-one — the writer has exactly one input path (an explicit `target_key` argument) and no heuristics. `parent_key` was not reused, widened, or reinterpreted — confirmed unchanged via `git diff --stat` (zero lines touched outside the new field/writer/Board-field addition) and via the two non-regression tests. No catalog seed, mount-pattern, or hole/offset data invented anywhere. No ESC mass, motor thrust H2/H3, Here3/Pixhawk, or HD-004 work reopened — confirmed no file under those areas touched. No package version bump (`pyproject.toml` still `0.3.8`). No test weakened — all 14 new tests are net-new assertions in a net-new file; zero existing test files were edited.

## Remaining risk / notes for review

- Since no writer call site exists yet outside direct invocation, `mounted_on` is currently reachable only programmatically (tests, or a future orchestrator/CLI IC) — this is the deferred §3.5 UX gap, not a defect in what shipped.
- The Board's honest-absence handling for a stale `mounted_on` target (a component deleted after being named as a mount target) was not specially hardened beyond "show the stored string as-is" (the IC's own default option, with the `"<key> (ausente)"` hardening explicitly marked optional/not required) — `_fields` shows whatever string is stored, including one that no longer resolves to a live component. This matches the IC's minimal-scope instruction; a future IC can add the honest-absence badge if the Engineer wants it.
