# Implementation Report — Geometry assembly fit B1-min (posed box–box screening)

**IC:** [implementation_contract_geometry_assembly_fit_cabe_b1.md](implementation_contract_geometry_assembly_fit_cabe_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2532

**This IC only — the 2026-09-07 stub (`implementation_contract_geometry_assembly_fit_compare.md`) was not implemented and was not edited into READY.**

---

## Files changed

- `src/jarvis/core/pose_envelope_screening.py` (**new**) — `Screening` (frozen dataclass: `status` + `missing_axes`), `screen_posed_envelope(child, components)`, `format_screening(screening)`. Statuses exactly as locked: `no_pose`, `origin_unusable`, `child_not_box`, `pose_incomplete`, `overlap`, `no_overlap`. AABB computed in the **declared mm frame** (origin box centered at `(0,0,0)`, child box centered at `(x_mm, y_mm, z_mm)` verbatim, half-extents from each box's own `length_mm/2, width_mm/2, height_mm/2`) — a new, backend-only Python function, never importing from `ui/`. `_geometry_from_spec` is imported **locally** inside the function (same circular-import-avoidance pattern `component_writers.py` already uses for this exact module pair, confirmed by reading it before writing this file).
- `src/jarvis/workspace/spatial_board.py` — one field appended to `_fields`, inside the **existing** pose-fields gate (`pose is not None and _declared_box_pose_dto(spec, components) is not None` — unchanged condition, not duplicated or loosened): `{"label": "sobres", "value": format_screening(screen_posed_envelope(spec, components))}`. No new `declaredBoxPose`/machine DTO key — confirmed T5 (`set(esc_node["declaredBoxPose"].keys()) == {"originKey", "xMm"}`, unchanged from before this IC).
- `src/jarvis/core/orchestrator.py` — new module constant `_CABE_WORD_RE = re.compile(r"\bcabe\b", re.IGNORECASE)` and new method `_try_handle_cabe_screening(user_input)`, dispatched in `_handle_user_text_inner` immediately after the existing pose declare/clear bridge (which already returns `None` for a bare "cabe" phrase — confirmed by inspection, it never matches the pose grammar's own `declara(r)`/`mm`/`respecto` gate) and before FN-005's help-choose chain — the same placement discipline every other deterministic IDLE bridge in this file already follows. Subject resolution reuses `mounted_on_declare_assist.resolve_component_subject_noun` (the same fc/esc/motor(es)/bateria/sensor(es)/helice(s) table already used elsewhere) — no second alias table, `"cabe"` not added to `COMPONENT_TERM_ALIASES`. A bare "cabe" with no named subject answers for the sole posed component when exactly one exists, otherwise asks which (never guesses); zero posed components → an honest "no pose declared yet" line, not a question.

## Behavior changed

- A `ComponentSpec` with a `declared_box_pose` whose origin resolves to a box now shows one more Board field, `"sobres"`, whose text is one of: an incomplete-pose notice naming the missing axis letters, an "se solapan"/"no se solapan" screening line (always suffixed "screening, no verificado"), or (if the child itself isn't a box) an honest non-box refusal — **never** a bare boolean, never `"cabe"`/`"no cabe"`/`"VERIFIED"`/`"ensamblado"`/`"misfit geométrico"` anywhere in any of these strings (confirmed by a dedicated `_no_forbidden` check run against every status's formatted text in the new test file).
- IDLE, a whole-word `"cabe"` phrase (`"cabe el esc"`, `"¿cabe?"`, `"cabe"`) now returns the same screening text deterministically, never reaching the LLM (confirmed live with a `_RefuseLLM` fixture) and never opening a wizard (`"status": "ok"`/`"action": "assembly_fit_screening"` for an answer, `"status": "interactive"`/`"action": "component_description_prompt"` only for the "which component?" disambiguation case — never `"component_description_saved"`, since nothing is written).
- **Missing axis is never treated as zero anywhere in this Buy** — `screen_posed_envelope` only ever reads `pose.x_mm`/`y_mm`/`z_mm` directly; a `None` value routes to `pose_incomplete` before any arithmetic runs. Verified directly against the live tree: `esc`'s real pose (`x_mm=5.0`, `y_mm`/`z_mm` absent) produces `"Pose incompleta (faltan y, z); no se compara — screening, no verificado."`, matching the IC's own smoke step 1 exactly, via a read-only check against the live `state.json` (no `workspace/` file touched — confirmed `git status --short -- workspace/` empty).
- Architecture/PASS/`ASSEMBLY_READY`/hover: byte-identical — `engineering_readiness.py` and `project_continuity.py` have **zero** diff this cycle (confirmed via `git status`, neither file even listed as modified); `_block_progress_status` reads only `BLOCK_TO_COMPONENTS`/params/component completeness, none of which this Buy touches. T6 directly proves a fixture whose only difference is a complete vs. incomplete `esc` pose produces the identical `_block_progress_status` result on every block.
- `mounted_on` is never read by the screening helper — confirmed by construction (the function only ever reads `child.declared_box_pose` and `components[origin_key]`'s geometry) and noted explicitly because the live `esc` row's own `mounted_on` (`"frame_plate"`) is a *different* key than its pose origin (`"flight_controller"`) — the two facts stay independent, exactly as the parent investigation flagged.

## Tests

- `python -m pytest -q tests/test_geometry_assembly_fit_cabe_b1.py` → **8 passed** (T0–T7; T8 is the git-diff check below, not a pytest test, per the IC's own note that it needs no in-test git parsing).
- `python -m pytest -q` (full suite) → **2540 passed**, 0 failed (baseline 2532 + 8 new).
- **T8 (`git diff` empty on `ui/`/`scene3dLayout.ts`)**: confirmed — `git status --short -- ui/` returns nothing at all this cycle; `scene3dLayout.ts` was never opened or imported by any file this IC touches.
- No version bump (`pyproject.toml` still `0.3.8`).
- Live re-check (read-only, no `workspace/` mutation): `project_spatial_nodes_from_path` against `autonomía-de-10min`'s real `state.json` produces the `"sobres"` field with the exact incomplete-pose text quoted above, matching the IC's own smoke script step 1.

## Non-goals honored

- **No `scene3dLayout.ts`/`ui/` import or port** — `pose_envelope_screening.py` has zero imports from `ui/`; confirmed via reading its own imports (`dataclasses`, `typing`, `jarvis.schemas.action_schema`, and a local `jarvis.workspace.spatial_board._geometry_from_spec` import) — no TS, no CSS, no pixel scale, no Y↔Z swap.
- **No `yMm ?? 0`/axis-default-to-zero anywhere** — confirmed by reading `screen_posed_envelope`'s own control flow: the `missing` check runs *before* any of `pose.x_mm`/`y_mm`/`z_mm` is used arithmetically; a `None` always short-circuits to `pose_incomplete`.
- **No forbidden token in any copy path** — `format_screening` covers all six statuses; every string was scanned by `_no_forbidden` in the test file (checks `"cabe"`, `"no cabe"`, `"VERIFIED"`, `"ensamblado"`, `"misfit geométrico"` as substrings, case-insensitive) across T0–T4 and T7's live orchestrator response.
- **No new Gap, no `ASSEMBLY_READY` touch** — `engineering_readiness.py` has zero diff (confirmed via `git status`); no `Gap`/`GapEvidence`/`gap_type` construct appears anywhere in the new code.
- **No Rooster L×W invented, `mounted_on` never used as compare origin** — confirmed by construction (the helper only reads `declared_box_pose`/`_geometry_from_spec`); no frame file touched.
- **No collision engine / origin-chain composition** — `screen_posed_envelope` reads exactly one child and its own direct pose origin, single level, never recursing into the origin's own pose (matching the existing pose-writer's own honesty scope, unchanged by this Buy).
- **`ComponentLibrary` unchanged**, `declared_box_pose_declare_assist.py` unchanged (pose writer stays REPLACE-not-merge, untouched) — confirmed via `git status`, neither file listed.
- **No new UI chrome** — the screening text lands on an existing Board `fields` array entry and an existing IDLE text-response shape; no new React component, no new CSS class, no new visual element.
- **Stub not unfrozen** — `implementation_contract_geometry_assembly_fit_compare.md` was read only to confirm its own gate text already named this investigation/IC chain; it was not edited.

## Remaining risks / notes for review

- None identified beyond what the parent investigation itself already flagged: the live tree's one real posed pair (`esc`/`flight_controller`) will keep showing "pose incompleta" until an Engineer or user declares the remaining two axes via the already-shipped pose IDLE grammar — this is the correct, intended behavior for today's data, not a gap in this implementation.
