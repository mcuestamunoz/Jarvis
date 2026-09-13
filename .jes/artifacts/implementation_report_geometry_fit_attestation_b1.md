# Implementation Report — Fit attestation B1 (Engineer-declared verified)

Status: Done
Parent: `implementation_contract_geometry_fit_attestation_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2669` → `2679` (2669 + 10 new) · UI `80` (unchanged)

## Summary

Added an optional, human-only sign-off (`declared_fit_attestation`) that an
Engineer can set on ONE already-`overlap`-screened posed box–box pair.
`pose_envelope_screening.py`'s own "screening, no verificado" copy is
completely untouched — this Buy adds a second, clearly-attributed fact
("Declarado verificado por el Engineer — no es una comprobación geométrica
de Jarvis.") alongside it, never a rename of it. The writer refuses
(`ValueError`) to set the field unless the pair's live screening status is
`overlap`; any later pose/geometry write that could have changed that
verdict clears the attestation automatically (same "divergence clears a
stale label" discipline `catalog_bind.py` already uses for `catalog_ref`).

## Files changed

- `src/jarvis/schemas/action_schema.py` — new `DeclaredFitAttestation`
  model (`attested_at: str`, `fingerprint: str`) and a new optional
  `ComponentSpec.declared_fit_attestation` field, default `None`.
- `src/jarvis/core/component_writers.py`:
  - `compute_fit_attestation_fingerprint(pose, child_geometry,
    origin_geometry)` — the one stable string over the locked tuple order
    (`origin_key, x_mm, y_mm, z_mm`, child L/W/H, origin L/W/H).
  - `set_component_declared_fit_attestation(project_state, component_key,
    attest)` — the single writer. `attest=True` requires
    `screen_posed_envelope(...).status == "overlap"` or raises
    `ValueError`; `attest=False` clears (idempotent no-op if already
    `None`).
  - `_cleared_fit_attestation` / `_clear_fit_attestations_after_geometry_
    change` — hooked into the END of the EXISTING
    `set_component_declared_box_pose` (clears the touched key's own
    attestation) and `set_component_declared_box_envelope` (clears the
    touched key's own attestation AND any sibling whose
    `declared_box_pose.origin_key` names it). Always-clear, per the IC's
    own explicit B1 allowance — never compares old vs. new values.
- `src/jarvis/core/orchestrator.py`:
  - `_DECLARO_VERIFICADO_RE` / `_QUITA_VERIFICACION_RE` gate regexes
    (mutually exclusive with the pose-declare grammar's own
    `declara(r)`+`mm`+`respecto` gate and with `_CABE_WORD_RE`).
  - `_try_handle_fit_attestation` — mirrors `_try_handle_cabe_screening`'s
    structure exactly: resolves the subject via the EXISTING
    `resolve_component_subject_noun` (no second alias table); a bare
    phrase with no named subject picks the sole eligible component
    (screened `overlap` for SET, currently attested for CLEAR) if exactly
    one exists, asks "¿Cuál componente?" if several, gives an honest
    "nothing eligible" message if none; calls the writer, surfaces its
    `ValueError` verbatim on refusal.
  - Wired into the IDLE dispatch chain right after the cabe bridge, before
    FN-005.
- `src/jarvis/workspace/spatial_board.py` — `_fields`: after the existing
  `sobres` field, when `spec.declared_fit_attestation` is present AND its
  fingerprint (recomputed live from the current pose + both boxes'
  geometry) matches the stored one, appends a `verificación` field with
  the human-attribution string. A stale/mismatched fingerprint is treated
  as absent — field omitted, `sobres` untouched.
- `src/jarvis/workspace/board_fit_attestation_bridge.py` (new) — thin CLI
  bridge, same shape as `board_pose_bridge.py`: load state → call the
  writer → save → reproject. No partial save on `ValueError`.
- `ui/spatial-board/vite-plugin-jarvis-projects.ts` — second POST route,
  `/api/projects/:id/fit-attestation`, bridged to the new Python module
  exactly like the existing `/pose` route is bridged to
  `board_pose_bridge`.
- `ui/spatial-board/src/projects.ts` — `postFitAttestation` client call,
  same error-surfacing discipline as `postDragPose`.
- `ui/spatial-board/src/Scene3D.tsx` — "Declarar verificado" / "Quitar
  verificación" buttons, shown only for the selected SINGLETON solid
  (same `isDraggableSolid` gate the drag path already uses — never a
  `solidCopies >= 2` station). On click, POSTs and calls the existing
  `onPoseCommitted` refetch callback (reused, not renamed — its contract
  was already "something changed, refetch nodes").
- `ui/spatial-board/src/spatial-board.css` — `.sb-scene3d__attest-toggle`
  style, sibling to the existing `.sb-scene3d__situar-toggle`.
- `tests/test_geometry_prop_adapter_visor_x_b1.py` — T9 pin fix: the
  stale `'version = "0.4.0"'` assertion updated to `'version = "0.4.1"'`
  (the IC's own explicit instruction).
- `tests/test_geometry_fit_attestation_b1.py` (new) — T0–T8, see below.

## Behavior changed

- New, additive-only: `ComponentSpec.declared_fit_attestation` (default
  `None`); existing/serialized projects deserialize unchanged.
- `set_component_declared_box_pose` and `set_component_declared_box_
  envelope` now also clear a stale `declared_fit_attestation` as a
  side effect on the components they touch (never elsewhere).
- New IDLE phrases ("declaro verificado el X" / "quito la verificación de
  X") recognized only when a subject resolves or exactly one eligible
  component exists; otherwise interactive or an honest refusal — never
  guesses, never opens the LLM.
- Board node `fields` gain an optional `verificación` entry after
  `sobres`. No machine DTO key added.
- Two new HTTP routes on the dev-server plugin (`/pose` sibling); no
  existing route's behavior changed.
- **Unchanged, verified explicitly**: `pose_envelope_screening.format_
  screening` strings (golden test T8), `_block_progress_status` (T6),
  `ASSEMBLY_READY`/`engineering_readiness`/`project_closure` (no edits —
  confirmed via `git diff --stat`, zero hits), package version (still
  `0.4.1`), `workspace/` (no mutation — confirmed via `git status --short
  -- workspace/`), the historical stub
  `implementation_contract_geometry_assembly_fit_compare.md` (not
  implemented).

## Tests

New file `tests/test_geometry_fit_attestation_b1.py` (10 tests, T0–T8 plus
one extra IDLE-refusal case T7b):
- T0 overlap → attest succeeds, fingerprint matches independent
  recomputation and is stable.
- T1 no_overlap → `ValueError`, no field set.
- T2 pose_incomplete → `ValueError`.
- T3 pose write changing Δmm on the child → attestation cleared.
- T4 envelope write on the child clears it; envelope write on its origin
  clears it; envelope write on an unrelated component does NOT.
- T5 Board `fields` show `verificación` when attested (and `sobres` still
  contains "no verificado"); a subsequent pose write leaves no stale
  `verificación` field.
- T6 `_block_progress_status` identical with/without an attestation
  present, across all four arch blocks.
- T7 IDLE `"declaro verificado el esc"` sets it and persists to disk;
  `"quito la verificación del esc"` clears it and persists — `_RefuseLLM`
  used throughout, LLM never called.
- T7b IDLE `"declaro verificado el esc"` against a `no_overlap` subject →
  `status: "error"`, honest message, no field set, LLM never called.
- T8 `format_screening(Screening(status="overlap"))` golden string
  unchanged.

`tests/test_geometry_prop_adapter_visor_x_b1.py::test_p6_library_and_
version_untouched` — pin fixed to `0.4.1` (T9).

Executed:
- `python -m pytest -q` → **2679 passed** (2669 baseline + 10 new).
- `npm run typecheck` (ui/spatial-board) → clean.
- `npm test` (ui/spatial-board) → **80 passed** (unchanged — no new pure
  logic module needed a dedicated unit test; the button/handler are
  integration glue over already-tested `postFitAttestation`/writer paths,
  same precedent `postDragPose`/`board_pose_bridge.py` set with no
  dedicated JS unit test of their own).
- Manual smoke of `board_fit_attestation_bridge.apply_fit_attestation`
  against a throwaway `state.json` (attest → field present; clear → field
  absent; unknown component → `ValueError`) — confirms the new HTTP
  route's Python side end-to-end without needing the dev server up.

## Non-goals honored

- `pose_envelope_screening.format_screening` strings unchanged (golden
  test).
- No `ASSEMBLY_READY`/new Gap/readiness rollup change —
  `engineering_readiness.py`/`project_closure.py` have zero diff.
- No CAD/FEA, no multi-hop chain, no margin, no mating-face logic.
- No second alias table — IDLE subject resolution reuses
  `resolve_component_subject_noun` verbatim.
- No version bump (`0.4.1` unchanged); only the pre-existing stale pin was
  fixed, per explicit IC instruction.
- Historical stub `implementation_contract_geometry_assembly_fit_
  compare.md` not implemented.
- Board/Scene3D control implemented (not deferred) — the C-113 POST
  pattern already existed and scoped cleanly to one sibling bridge module
  + one sibling route + one sibling client call + a singleton-gated button
  pair, so it was shipped rather than deferred.

## Remaining risks

- The Board button's eligibility check is a client-side text match on the
  `sobres` field value (`"se solapan"`) purely for UX (hide/show) — the
  writer's own `screen_posed_envelope` status check is the real gate, so a
  stale client render can only ever show a button that then gets an
  honest refusal, never a silent grant.
- `compute_fit_attestation_fingerprint` is a plain delimited string, not a
  cryptographic hash — adequate for an equality check against a later
  recomputation (not a security boundary), but a component key or origin
  key containing the `"|"` delimiter character would not by itself create
  a collision risk here since every field position is fixed, not
  concatenated ambiguously; noting this only because no test explicitly
  pins the exact delimiter format (only stability/equality is pinned, not
  the literal string), so this is free to change without breaking the
  contract if ever needed.
- No dedicated Vitest for the new `Scene3D.tsx` button wiring or the vite
  plugin's new route (mirrors the existing project's own precedent of
  leaving `postDragPose`/the `/pose` route similarly uncovered at the JS
  test layer) — covered instead by `npm run typecheck` + the Python-side
  bridge smoke test above.
