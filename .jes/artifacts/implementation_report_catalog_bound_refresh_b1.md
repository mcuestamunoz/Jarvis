# Implementation Report — Refresh Catalog-bound Component from Seed B1

**IC:** [implementation_contract_catalog_bound_refresh_b1.md](implementation_contract_catalog_bound_refresh_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2385

---

## Files changed

- `src/jarvis/core/component_writers.py` — **§3.1**: added `refresh_component_from_catalog(project_state, component_key) -> ProjectState`, dispatching on `spec.catalog_ref.family` to the matching `bind_{motor,battery,propeller,esc,frame}_from_catalog(sku, base=spec)` (imported at module level — confirmed no circular import). Raises `ValueError` (never a silent no-op) when the key is undeclared, when `catalog_ref` is `None`, or for an unrecognized family. Also added `diff_refreshed_properties(old_spec, new_spec) -> dict[str, tuple[old, new]]`, a pure helper (never called by the writer itself) used only by the orchestrator to build honest confirmation copy.
- `src/jarvis/core/catalog_refresh_assist.py` (**new**) — pure parser mirroring `mounted_on_declare_assist`'s thinness. `resolve_catalog_refresh_component(user_input) -> str | None`: gate is `actualiza(r)`/`refresca(r)` (word-boundary, so "actualizar" alone with no recognized subject noun correctly returns `None`); subject resolution covers exactly the 5 locked families — `esc`, `motors` (motor/motores), `battery` (bateria/batteries/battery), `frame` (frame/chasis), `propellers` (helice/helices/propeller/propellers) — deliberately **excluding** `flight_controller`, since FC has no `CatalogRef.family`/bind path at all (confirmed during the investigation).
- `src/jarvis/core/orchestrator.py` — **§3.3**: added `_try_handle_catalog_refresh(self, user_input) -> dict | None`, placed directly after `_try_handle_mounted_on_declare` (same file region, same pattern), and dispatched in `_handle_user_text_inner` immediately after the mount-declare IDLE bridge and before FN-005's help-choose chain. Behavior exactly as locked:
  - `None` from the parser → returns `None`, falls through unchanged (T6/T6b non-regression).
  - Subject key not present in the project's `components` → honest `{"status": "error", ...}`, writer never called.
  - `ValueError` from the writer (no `catalog_ref`, unrecognized family) → surfaced as `{"status": "error", ...}` with the writer's own message.
  - Success → saves state and returns `{"status": "ok", "action": "component_description_saved", "message": ...}` built from `diff_refreshed_properties`: when something changed, `"Actualizado desde catálogo (<sku>): <field> <old> → <new>, ..."`; when nothing changed, `"Ya coincidía con el catálogo (<sku>) — sin cambios."`; appends `" Montaje declarado sin cambios."` only when `mounted_on` survives (never claims a montado relation that isn't there).

## Behavior changed

- IDLE, active-project chat input matching `actualiza`/`refresca` + a recognized family noun now re-projects that component's physicals from the **current** catalog seed, via the existing `bind_*_from_catalog(sku, base=spec)` merge — proven both in synthetic tests and against the **actual** stale demo project (`workspace/autonomía-de-10min-9ada1a1b0cca`, dry-run only, not persisted by this implementation): `esc.properties["mass_g"]` goes `26.0 → 15.0` while `mounted_on="frame_plate"`, `catalog_ref`, and every other property survive untouched.
- No property change → an honest "already matches" message, never a false diff.
- A subject not yet declared, or a declared-but-not-catalog-bound component, gets an honest error and makes no write.
- No other IDLE phrase's routing changed — confirmed by T6 (`"cambiar frame"` still opens the frame catalog) and T6b (`"quita el montaje del esc"` still clears the mount relation via the pre-existing, untouched `mounted_on_declare_assist`/`set_component_mounted_on` path).
- Frame refresh preserves `frame_plate`/`frame_arm`/etc. children **by construction, with zero special-casing**: `refresh_component_from_catalog` only ever touches `components[component_key]` (a single dict key) — it never reaches into sibling entries, so a frame refresh cannot clear or touch frame-part children the way a catalog **re-pick** (`clear_frame_part_children` + `frame_part_specs_from_catalog`) deliberately does. This was the IC's own §3.1.6 concern ("do not clear frame children unless an existing bind path already does") — confirmed unnecessary to worry about, since the writer's scope is structurally single-key.

## Tests

Executed: `python -m pytest -q` → **2403 passed**, 0 failed (baseline 2385 + 18 new, all in the single new file `tests/test_catalog_bound_refresh_b1.py`). Ran the new file alone first (18 passed) before the full suite. No existing test was modified or weakened.

Test breakdown against §4: T1 (mass fixed + `mounted_on` preserved) plus T1b (a companion proving `diff_refreshed_properties` reports exactly the one changed field, nothing else); T2 (no `catalog_ref` → `ValueError`, verified the original spec's properties are untouched afterward); T3 (missing key → `ValueError`); T4 (6 parse-SET cases across all 5 families + 3 parse-NONE cases, parametrized); T5 (orchestrator happy path: persisted 15g, message contains both old/new values and the "montaje sin cambios" line, and is free of every forbidden token) plus T5b (idempotent second refresh reports "sin cambios") and T5c (missing subject → honest error); T6 (non-regression: `"cambiar frame"`) plus T6b (non-regression: `mounted_on` clear phrase still works end-to-end).

## Non-goals honored

No ESC picker UX built — this is a same-SKU refresh, never a re-pick among candidates. No auto-refresh on Board load/read/save — confirmed via `git diff --stat`, zero changes to `spatial_board.py` or any projector path; the writer is only ever invoked from the new IDLE dispatch. No "fix" attempted via `set_control_component`/free text — that path is untouched and remains the destructive non-option the investigation identified. No seed value changed (`git diff --stat` shows zero `library/**` changes). `bind_*_from_catalog`'s own merge semantics were called exactly as-is, never modified. No FC/Here3/Pixhawk file touched — confirmed, and the parser deliberately excludes `flight_controller` as a resolvable subject. No fit/pose/Fase 2/Fase 3 work opened. No package version bump (`pyproject.toml` still `0.3.8`). No test weakened — the new file is entirely additive; zero existing test files were edited.

## Remaining risk / notes for review

- The real demo project (`workspace/autonomía-de-10min-9ada1a1b0cca`) was **not** modified by this implementation — I only dry-ran the refresh against its live `state.json` to confirm the mechanism works on the actual stale data (see "Behavior changed" above), then discarded the result (`git status --short workspace/` is clean). Per the IC's own done-criteria, the Engineer smoke ("refresh demo ESC → Board 15 g") is the step that should actually run `"actualiza el esc desde catálogo"` against that live project through the real product surface, not something this implementation should do on its own initiative.
- `diff_refreshed_properties` is a simple value-equality diff (`old_val != new_val`) — it does not attempt unit-aware or float-tolerance comparison. For every seed value in the catalog today this is exact (no floating-point drift observed in testing), but a future seed edit that changes a value by a sub-epsilon rounding artifact could theoretically show as "changed" when it's not meaningfully different. Not a concern for this cycle's evidence (the ESC case is a clean integer-vs-integer 26→15), flagged for awareness only.
