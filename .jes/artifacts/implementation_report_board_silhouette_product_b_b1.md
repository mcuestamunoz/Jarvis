# Implementation Report — Silhouette Product B B1 (`B1-silhouette-product-b`) · Path S1

**IC:** [implementation_contract_board_silhouette_product_b_b1.md](implementation_contract_board_silhouette_product_b_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2830 → **2844** (14 new tests)

---

## §0.1 filled bag applied

Implemented against the locked Path S1 (`code_star: checklist_idle`). The smoke target project (`10-min-autonomía`, `7e400f0a4983`) was used for the live reproducibility check below — read-only, no `workspace/` write.

## Verdict rules implemented exactly as locked

`assess_silhouette(components)` (`src/jarvis/core/silhouette_product_b_assist.py`):

```text
no boxed plate (or 2+, ambiguous)              -> racimo
boxed plate, stack/mounts incomplete           -> racimo (not yet)
boxed plate, stack+mounts OK, plate estimated  -> silueta estimada (B*)
boxed plate, stack+mounts OK, plate declared   -> silueta (B)
```

`stack+mounts OK` is evaluated only over subjects that are **present** in the project **and already have their own declared box** (`_stack_present_subjects`) — a project that never declared a sensor, or declared one with no box, is never asked to pose/mount it (mirrors `craft_montage_stack_assist`'s "skip, don't demand" honesty). Visor X/wheelbase and pose-cycle are separate, **warn-only** rows (`status: "n/a"` or `"ok"`) that never demote an otherwise-earned B*/B verdict, per the IC's own explicit note ("X already shipped on 10min; warn-only avoids false racimo").

## Row 6 (pose cycle) — no invented detection

I searched the codebase (Continuity, pose, envelope-screening modules) for any existing "pose cycle" / "sibling cycle" honesty check and found **none exists anywhere today**. Per the IC's own allowance ("reuse Continuity honesty if a cheap check exists; **else skip with `n/a`**"), row 6 always reports `n/a` with an honest reason string — no new detection logic was invented, no new subsystem introduced.

## Row 5 (Visor X/wheelbase) — reused the existing gate, not duplicated

Reused `spatial_board._quad_x_wheelbase_mm(components)` (the exact frame `configuration == "quad_x"` + `wheelbase_mm` gate the Board's own motor/propeller X-station rendering already uses) rather than inventing a second, parallel wheelbase check. `None` → row `n/a`; a value → row `ok`. This is a private helper, imported the same way `_geometry_from_spec` is already imported by every sibling assist module this session.

## No duplicated arithmetic/vocabulary — reused sibling helpers directly

`silhouette_product_b_assist.py` imports `_plate_box_origin`, `_is_estimated_temporary_box`, and `_STACK_SUBJECTS` directly from `craft_montage_stack_assist.py` (same private-import pattern already established for `_geometry_from_spec` across every assist module this session) instead of re-deriving "which plate is the unambiguous boxed one" or "is any box dim estimated" a second time. Every suggested phrase (`"apilar en placa"`, `"montajes estándar"`, `"declara frame_plate estimada L x W mm"`) is a literal, unmodified trigger/example already owned by an existing sibling assist — this module never widens or re-implements any of that vocabulary.

## Files changed

- **`src/jarvis/core/silhouette_product_b_assist.py`** (new) — `SilhouetteRow`, `SilhouetteAssessment`, `assess_silhouette(components)`, `format_silhouette_checklist(assessment)`, `is_silhouette_assist_trigger(user_input)`.
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_silhouette_product_b_assist` IDLE bridge, wired right after the layout-pack checklist bridge (same conceptual "what's missing" family).
- **`tests/test_geometry_silhouette_product_b_b1.py`** (new) — 14 tests covering T1–T6 plus the warn-only-row and no-project-literal checks.

No other file was touched. No writer was added or modified. No existing sibling module's public behavior changed.

## Trigger family (IC §0 lock #3)

`_TRIGGER_RE = re.compile(r"\bsilueta\b|parece\s+un\s+dron|\bproduct\s+b\b")`, matched against `_normalize_help` output (same accent/case-fold every other IDLE gate in this codebase uses). Covers `silueta`, `parece un dron`, `¿parece un dron?` (the leading `¿` is inert to a `.search`, never stripped or required), and `product b` (case-insensitive). Verified this family never fires on `montajes estándar`, `layout pack`, or `apilar en placa` (T5).

## Tests

Executed: `python -m pytest -q` → **2844 passed, 1 skipped** (0 failed; the 1 skip is pre-existing, unrelated). Ran the new file alone first (14 passed) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_no_plate_box_yields_racimo`, `test_t1_ambiguous_two_plates_still_racimo_never_guessed` |
| T2 | `test_t2_estimated_plate_full_stack_yields_silueta_estimada` |
| T3 | `test_t3_declared_plate_full_stack_yields_silueta_no_star` |
| T4 | `test_t4_missing_esc_pose_yields_racimo_with_existing_assist_suggestion`, `test_t4_missing_mount_only_yields_racimo_with_mount_suggestion`, `test_t4_absent_subject_never_demanded`, `test_t4_boxless_subject_never_demanded_either` |
| T5 | `test_t5_trigger_phrases_resolve`, `test_t5_unrelated_phrases_do_not_trigger` |
| T6 | `test_t6_idle_checklist_never_writes`, `test_t6_idle_full_stack_reports_silhouette_and_never_writes` |
| T7 | Full suite green above; `pyproject.toml` still `0.4.1` |

Additional coverage: warn-only Visor X/pose-cycle rows never demote an earned verdict (`test_visor_x_and_pose_cycle_rows_are_warn_only`); no project-specific literal in the module (`test_module_has_no_project_specific_literals`, mirroring the sibling modules' own T8-style check).

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **`10-min-autonomía`**: verdict **racimo** — `esc` currently has no `mounted_on` (cleared during an earlier live smoke), so the stack is not yet mount-complete; every other row is `ok`, plate is correctly flagged `estimated_temporary`. This exactly matches the IC's own §3 smoke expectation ("expect silueta estimada (B*) **after remount esc if still cleared**") — the checklist message correctly names `montaje_esc` as the one missing row and suggests the existing `"montajes estándar"` phrase.
- **`autonomía-de-5min`**: verdict **silueta estimada (B\*)** — all four stack subjects already posed and mounted, plate `estimated_temporary`. Message ends with the "nada crítico pendiente... sustituye L×W... para quitar el *" reminder, exactly as the IC's own tuning target describes.

## Non-goals honored

No Three.js/Scene3D (S2) work. No new writer. No plate L×W seeded into the library. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty; the live-project reproducibility check used in-memory `ProjectState` objects only). No arm-radial-to-plate row. No mount key-tip FN. No HD-005. Never prints "VERIFICADO" / "CAD medido del kit" — confirmed by `test_t2_estimated_plate_full_stack_yields_silueta_estimada`'s explicit `"medido" not in message.lower()` / `"verificado" not in message.lower()` assertions.

## Remaining risks / notes for review

- Row 5 (Visor X/wheelbase) is warn-only by explicit IC instruction; a project with a non-`quad_x` frame or no `wheelbase_mm` will show `n/a` there forever even once it's otherwise a fully-posed, fully-mounted silhouette — this is the locked behavior, not a gap, but worth Cursor's explicit confirmation since it's the first "structurally can't ever go green for this frame shape" row in this checklist family.
- Row 6 (pose cycle) is permanently `n/a` today since no such check exists anywhere in the codebase — if a future Buy adds one, this module's row should be updated to consume it rather than left stale.
- The verdict enum's Spanish copy (`racimo (A)` / `silueta estimada (B*)` / `silueta (B)`) is new UI vocabulary for this checklist family, distinct from the `✓`/`✗`/`·`/`*` per-row markers introduced by sibling checklists — worth Cursor confirming the two markers (`*` for the estimated-authority row vs. `(B*)` in the verdict line) read unambiguously together.
