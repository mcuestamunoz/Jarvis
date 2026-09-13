# Implementation Report — Fit relations checklist B1 (`B1-fit-relations-checklist`)

**IC:** [implementation_contract_geometry_fit_relations_checklist_b1.md](implementation_contract_geometry_fit_relations_checklist_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2858 → **2873** (15 new tests)

---

## Part A — silhouette footer scoped to "este checklist"

`format_silhouette_checklist`'s two closing lines (verdicts `silueta_estimada`/`silueta`) now read "Silueta: sin bloqueos críticos **dentro de este checklist** — ..." instead of the bare "Nada crítico pendiente..." — the exact copy lock #9 specifies. No new triggers, no other copy touched; the estimated-plate reminder ("sustituye L×W por una medida real...") is unchanged.

## Part B — fit relations module (`fit_relations_assist.py`)

### Reuse, not new arithmetic (IC's own repeated instruction)

- **Plate pick**: `craft_montage_stack_assist._plate_box_origin` (single unambiguous boxed `frame_plate*` / a candidates tuple when 2+ / `None` when zero) — the exact same honesty already validated by Path F and the silhouette checklist. `_is_estimated_temporary_box` is reused from the same module for both the child's and the plate's own estimated check.
- **Screening**: `pose_envelope_screening.screen_posed_envelope`/`format_screening` — called directly once a relation has passed the box/estimated/pose gates; its own message text becomes the row's `reason` verbatim, so the "screening, no verificado" honesty language is never re-typed or paraphrased.
- **Mount status**: `mount_standard_assist.build_mount_standard_checklist(components)` is called once per assessment; its output is indexed by subject and reused as the `mount_warning` annotation for every one of the six relations (plate family AND the two disk mount edges) — this avoids re-deriving "which plate/frame the mount target should be" a second time, since that module already gets the plate/frame/ambiguous logic right.
- **Attestation validity**: mirrors (does not import, since the check lives inline in `spatial_board.py`'s own projector) the exact same "recompute the fingerprint fresh, never trust the stored seal" re-verification `_fields` already performs — `compute_fit_attestation_fingerprint` from `component_writers.py`.

### Per-relation status ladder (IC §0 lock #7)

For the four plate-family relations (`flight_controller`/`esc`/`battery`/`sensors` → the resolved plate), in order: `missing_origin` (no `frame_plate*` key at all) → `no_box_origin` (a plate key exists but isn't boxed yet) → `ambiguous_plate` (2+ boxed plates, never guessed) → `no_box_child` (the child itself has no box) → `estimated_dims` (either box carries `estimated_temporary` — checked independently of pose, so an unposed child on an estimated plate is flagged immediately rather than waiting for a pose to exist) → `no_pose` → `attested` (valid fingerprint) → `screen_overlap` / `screen_no_overlap` / `screen_pose_incomplete`. For the two mount-only relations (`motors`→`frame_arm`, `propellers`→`motors`): `missing_origin` if the target key is absent, else always the honest `n_a_disk` — these are disk pairs and this Buy explicitly never screens them (disk-station attest is a separate, out-of-scope Buy per lock #1).

`mount_warning` is a **second, independent** field on every row (IC's own "optional warn row... does not block screening") — a relation can be `screen_overlap`-ready or `attested` and still carry a `mount_warning` if `mounted_on` happens to be unset, and a `n_a_disk` relation shows its mount warning too when applicable (R5).

### `no_box_child` honesty for FC/ESC (a finding, not an assumption)

I checked `declared_envelope_declare_assist.py`'s own documented scope before writing a suggest phrase for a boxless FC/ESC: that module's own docstring locks its subject table to `battery`/`sensors`/any `frame_plate*`/two kit keys — **"Never `frame` root, arms, cage, standoff, motors, ESC, FC, or propellers."** There is no working single-phrase "declare this box" command for FC/ESC in this codebase today (their boxes arrive via catalog bind, a separate multi-turn flow) — I verified this empirically (`declara el esc ...`/`declara la controladora ...` both parse to `NONE`/`INCOMPLETE` with no resolved subject). Rather than inventing a phrase that doesn't actually work, `no_box_child` for `flight_controller`/`esc` carries **no `suggest`**, only an honest reason noting the box normally arrives via catalog/SKU — mirroring `craft_montage_stack_assist`'s own precedent (`kind="skipped"` boxless rows there also carry no suggest). `battery`/`sensors` DO get a working suggest (`declara <noun> L x W x H mm`, verified to `SET`).

### Attest suggestion — verified against the real live grammar (R3)

The suggested attest phrase (`declaro {verificado|verificada} <noun>`) picks the grammatical gender from whether the noun's article is "la " (feminine) — this is cosmetic only: the real trigger regex (`orchestrator._DECLARO_VERIFICADO_RE = r"\bdeclaro\s+verificad[oa]\b"`) accepts either gender, and subject resolution (`resolve_component_subject_noun`) scans the whole phrase for a recognized noun regardless of the verb's own gender. I verified all four plate-family suggest phrases round-trip correctly through both the trigger regex and `resolve_component_subject_noun` (test `test_r3_declared_plate_overlap_ready_with_real_attest_phrase`, plus manual verification for esc/battery/sensors during development).

## Files changed

- **`src/jarvis/core/silhouette_product_b_assist.py`** — Part A footer copy change only (2 lines).
- **`src/jarvis/core/fit_relations_assist.py`** (new) — `FitRelationRow`, `FitRelationsAssessment`, `assess_fit_relations(components)`, `format_fit_relations_checklist(assessment)`, `is_fit_relations_assist_trigger(user_input)`.
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_fit_relations_assist` IDLE bridge, wired right after the silhouette checklist bridge (same conceptual family).
- **`tests/test_geometry_fit_relations_checklist_b1.py`** (new) — 15 tests covering A1 + R1–R7 plus a no-project-literal check.

No writer was added or modified. No existing sibling module's public behavior changed beyond the two Part A lines.

## Trigger family (IC §0 lock #3)

`_TRIGGER_RE = re.compile(r"\brelaciones\b|\bfit\b|que\s+falta\s+verificar|verificaciones\s+de\s+encaje")`, matched against `_normalize_help` output. Verified this never fires on `silueta`, `parece un dron`, `montajes estándar`, `layout pack`, or `apilar en placa` (R6).

## Tests

Executed: `python -m pytest -q` → **2873 passed, 1 skipped** (0 failed). Ran the new file alone first (15 passed) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| A1 | `test_a1_silhouette_estimada_footer_scoped_to_checklist`, `test_a1_silhouette_declared_footer_also_scoped` |
| R1 | `test_r1_no_plate_box_blocks_plate_relations`, `test_r1_zero_plate_key_declared_is_missing_origin` |
| R2 | `test_r2_estimated_plate_blocks_attest_even_when_posed` |
| R3 | `test_r3_declared_plate_overlap_ready_with_real_attest_phrase` |
| R4 | `test_r4_valid_attestation_shows_attested`, `test_r4_stale_fingerprint_never_shows_attested` (extra: proves a pose change after attest is never shown as still-attested) |
| R5 | `test_r5_motors_propellers_are_n_a_disk_with_mount_warning`, `test_r5_mount_warning_absent_once_mounted`, `test_r5_missing_arm_is_missing_origin_for_motors_relation` |
| R6 | `test_r6_trigger_phrases_resolve`, `test_r6_sibling_triggers_never_stolen` |
| R7 | `test_r7_idle_checklist_never_writes_or_attests` |
| T | Full suite green above; `pyproject.toml` still `0.4.1` |

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **Both `10-min-autonomía` and `autonomía-de-5min`**: all four plate-family relations correctly show `estimated_dims` (blocked) since both projects' `frame_plate` is still `estimated_temporary` today — **0 listas para declarar verificado**, honestly reflecting that no relation can be attested until the plate is measured, exactly matching the estimated-plate gate (R2's own scenario, confirmed against real data, not just the synthetic fixture). Motors/propellers correctly show `n_a_disk`; `10-min-autonomía`'s motors already has a mount declared (no warning shown) while `autonomía-de-5min`'s does not (warning shown, suggesting the real "motor montado en el brazo" phrase) — the mount-warning annotation's presence/absence tracks real per-project state exactly as designed.

## Non-goals honored

No new geometry formula (screening math is 100% delegated to the existing `screen_posed_envelope`). No auto-attest (the writer is never called — confirmed by `test_r7_...`). No weakening of the `overlap`-only attest gate. No renaming of "screening, no verificado" copy. No `ASSEMBLY_READY`/project-green claim anywhere in the checklist copy (`"esto no es ASSEMBLY READY ni el estado del proyecto"` is printed on every non-empty result). No disk-station attestation. No visual recognition. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty).

## Remaining risks / notes for review

- **Verdict bucket count differs slightly from the IC's own illustrative example.** Lock #8 showed `"relaciones: N listas para declarar · M bloqueadas · K n/a"` (three buckets); I added a fourth, `attested`, so a relation that's already sealed is never folded into either "listas" (misleadingly implying it still needs an action) or "bloqueadas" (factually wrong — it's done). Given this session's own repeated "done vs. pending must never be conflated" finding (layout-pack-cited's N1, back-ported to craft-montage), I judged this the more honest choice, not a deviation from the lock's intent — flagging for Cursor's explicit confirmation since the IC's own copy example didn't show four buckets.
- **`ambiguous_plate` rows are emitted per-child** (one row per present plate-family subject, all sharing the same `candidates`) rather than a single collapsed row for the whole family the way `craft_montage_stack_assist`'s own ambiguous handling does. I chose this for a uniform one-row-per-relation data shape (simpler counts/formatting), not because collapsing would be wrong — no test exercises the 2-plate scenario end-to-end for this module since the IC's own R-list didn't ask for it, so this is a design note rather than a gap.
- `no_box_child` gives no `suggest` for `flight_controller`/`esc` (see finding above) — this is an honest reflection of the current codebase, not a placeholder; if a future Buy adds a manual FC/ESC envelope-declare path, this module should pick it up automatically once such a phrase exists to reuse.
