# Implementation Report — Estimated-temporary plate envelope B1 (`B1-estimated-temporary-plate`)

**IC:** [implementation_contract_geometry_estimated_temporary_plate_b1.md](implementation_contract_geometry_estimated_temporary_plate_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2763 (+ concurrent unrelated in-flight work in this tree; full suite green at 2785 after this cycle's 18 new tests)

---

## §0.1 bag received

```
length_mm: 120
width_mm: 55
height_mm: use thickness
projects: autonomía-de-5min
```

Neither `120` nor `55` matches a rejected source (GEP `175×173`, MY5 `225×200`, or `208` wheelbase) — verified against this Buy's own rejection table before writing anything.

## Files changed

- **`src/jarvis/schemas/action_schema.py`** — `PropertyValue.source` gains the literal `"estimated_temporary"` (minimal extension, lock #3 — not the full five-tier taxonomy).
- **`src/jarvis/core/component_writers.py`** — new `set_estimated_temporary_plate_envelope(project_state, component_key, length_mm, width_mm, height_mm)`: rejects any non-`is_frame_plate_key` component (`ValueError`), requires all three axes finite and `> 0`, writes them with `source="estimated_temporary"` and a fixed low `confidence=0.3` (vs. `declared`'s `0.9`), preserves every other property, and reuses the existing `_clear_fit_attestations_after_geometry_change` helper (renamed its docstring to note the new caller — no behavior change to that helper itself).
- **`src/jarvis/core/estimated_temporary_plate_assist.py`** (new) — pure parser `parse_estimated_temporary_plate_declare`: gate requires `declara` + a provisional keyword (`estimada`/`estimado`/`temporal`/`provisional`) + an A×B[×C] mm shape, resolved subject restricted to `resolve_plate_subject_noun` (the exact same plate-noun table the existing declared-envelope grammar uses — no second table). A provisional phrase naming a different **known** subject (battery/sensors/esc/fc/motors/propellers) returns `NONE` (defers entirely) rather than a confusing "which plate?" prompt — see finding below.
- **`src/jarvis/core/pose_envelope_screening.py`** — new `ScreeningStatus` member `"estimated_dims"`; `_is_estimated_temporary_box(spec)` helper; `screen_posed_envelope` now checks both origin and child for an `estimated_temporary` dim (right after confirming both are boxes, before any axis/overlap math) and returns `"estimated_dims"` instead of computing overlap; `format_screening` gains the matching honest-refusal copy.
- **`src/jarvis/workspace/spatial_board.py`** — `_fields` gains a mandatory `"geometría"` disclosure row (`"ESTIMADA TEMPORAL · evidencia: ninguna · sustituir al llegar el frame: SÍ"`) whenever any of a spec's `length_mm`/`width_mm`/`height_mm` carries `source="estimated_temporary"` — satisfies lock #8's "Continuity message + projector fields note" fallback (no Three.js/badge work).
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_estimated_temporary_plate_declare` IDLE bridge, wired **before** the existing `_try_handle_declared_box_envelope` bridge (its gate is a strict superset — dims shape + provisional keyword — so a provisional phrase must never be silently claimed as ordinary `declared` by the next bridge in the chain).
- **`tests/test_geometry_estimated_temporary_plate_b1.py`** (new) — 18 tests.

No `library/` file touched (T7's own check). No `workspace/` mutation (confirmed below).

## Gates implemented (IC §0 lock #7)

| Gate | Mechanism |
|---|---|
| (a) `cabe` refuses | `screen_posed_envelope` returns `"estimated_dims"` before any overlap math when either box in the pair carries an estimated dim; `format_screening` never emits "cabe"/"no cabe"/"VERIFIED" for it |
| (b) fit-attestation SET refuses | **Free consequence of (a)** — `set_component_declared_fit_attestation` already hard-requires `screening.status == "overlap"`; since `"estimated_dims"` is never `"overlap"`, the existing writer refuses without any change to that writer itself. Verified directly (`test_t4_fit_attestation_set_refuses_with_estimated_dims`) |
| (c) never seeded into `library/` | The new writer only ever touches `ProjectState.design_properties.components` — it has no path into `library/**/_datos.json`, and no catalog bind/seed function was touched |
| (d) copy never claims "cabe porque la placa mide X" | Both the declare-success message and the `cabe` refusal explicitly name `ESTIMATED_TEMPORARY`/"no se compara" — never a fit claim |

## Replace path (IC §0 lock #9)

The **existing, untouched** `set_component_declared_box_envelope` and its IDLE bridge (`"quita el sobre de X"` / a plain `"declara ... mm"`) already unconditionally overwrite or pop `length_mm`/`width_mm`/`height_mm` regardless of their prior `source` — so a later measured `declared` write, or a plain clear, transparently supersedes an estimated one with **zero new code**. Verified directly: `test_t6_measured_declare_overwrites_estimated_source`, `test_t6_clear_pops_estimated_dims_same_as_declared`, `test_t6_fit_attestation_clears_when_estimated_dims_written` (the shared `_clear_fit_attestations_after_geometry_change` helper pops a sibling's stale attestation on an estimated write exactly as it already did for a declared one).

## A design finding worth flagging (fixed, not just noted)

The IC's own gate ("declara" + provisional keyword + dims) doesn't, on its own, distinguish "no plate named" from "a *different* known subject named" — `resolve_plate_subject_noun` returns `None` for both. A first draft made **both** cases `INCOMPLETE`, meaning `"declara la batería estimada 80 x 34 x 22 mm"` (a battery phrase, provisional adjective included) would have produced *"Indica qué placa..."* — a confusing answer to a battery question. Fixed by checking `resolve_component_subject_noun` first: if the phrase names one of the six subjects this Buy's own lock #2 excludes (battery/sensors/esc/fc/motors/propellers), the parser returns `NONE` and the phrase falls through entirely to the plain declared-envelope bridge (which applies it as ordinary `source="declared"`, silently dropping the unsupported "estimada" adjective — acceptable since provisional support for these families is explicit follow-on scope, not a promise this Buy makes). Covered by `test_parse_battery_provisional_defers_not_incomplete`.

## Tests

Executed: `python -m pytest -q` → **2785 passed**, 0 failed (this cycle's own file: 18/18; full suite includes unrelated concurrent in-flight work already present in this tree — `library/frames/_datos.json` and a `hglrc_my5` IC/test file neither authored nor touched by this cycle). Ran the new file alone first (18 passed), then together with the three pre-existing envelope/fit-attestation files (`test_geometry_declared_battery_plate_envelope_b1.py`, `test_geometry_declared_sensors_kit_envelope_b1.py`, `test_geometry_fit_attestation_b1.py` — 48 passed combined, zero regression) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_idle_provisional_declare_sets_estimated_source` — L/W/H all `estimated_temporary`, height from cited `thickness_mm`, projector geometry resolves `shape: box` (root-capable — the exact same gate `scene3dLayout.ts` reads) |
| T2 | `test_t2_plain_declare_still_declared_source` + `test_parse_plain_declare_no_provisional_keyword_is_none` |
| T3 | `test_t3_cabe_refuses_estimated_origin` (IDLE) + `test_screen_posed_envelope_estimated_dims_status_direct` (unit) |
| T4 | `test_t4_fit_attestation_set_refuses_with_estimated_dims` (writer raises `ValueError`; IDLE bridge surfaces it as `status: error`; no attestation stored) |
| T5 | `test_t5_success_copy_discloses_estimated_temporary` (message text + projector `"geometría"` field) |
| T6 | `test_t6_measured_declare_overwrites_estimated_source`, `test_t6_clear_pops_estimated_dims_same_as_declared`, `test_t6_fit_attestation_clears_when_estimated_dims_written` |
| T7 | Full suite green above; `pyproject.toml` still `0.4.1`; `git status --short -- library/` shows only the pre-existing unrelated `hglrc_my5` diff — nothing from this cycle |

Additional coverage beyond the table: parser unit tests (exact-key match, `temporal` keyword, ambiguous 2-plate, no-subject `INCOMPLETE`, the battery-defers-to-NONE finding above), writer rejection tests (non-plate key, non-positive dims), and a non-regression test confirming `set_component_declared_box_envelope` and its plate-labeling behavior are byte-for-byte unaffected.

## Non-goals honored

No full evidence taxonomy (only the one new literal). No estimated dims for any non-plate family — the writer's `is_frame_plate_key`-only gate and the parser's battery/sensors/etc. defer-to-`NONE` behavior both enforce this from two independent directions. No auto-pose, no stack-rule, no layout-pack invent. No quiet upgrade to `verified` — `declaro verificado` is refused, not silently granted. No body-footprint numbers (`175×173`/`225×200`/wheelbase `208`) anywhere in code, tests, or the applied bag. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation — confirmed via `git status --short -- workspace/` (empty); the Engineer's own live smoke on `autonomía-de-5min` (typing `"declara frame_plate estimada 120 x 55 mm"`, per lock #10's live-project pick) is what will actually apply this to that project, matching every prior cycle's own Path-C precedent (Claude implements + tests, Engineer types the phrase live).

## Remaining risks / notes for review

- **Live-apply interpretation.** The bag named `autonomía-de-5min` as the target project, and lock #10 allows Claude to pick "project(s) or tests-only." I interpreted this as *which project the Engineer's own smoke (§3) should target*, not an instruction for this cycle to script-mutate that project's `workspace/` file directly — matching the "Not... silent `workspace/` mutation unless ★ apply-live" language and every prior Path-C precedent this session (`mount_standard_assist_b1`, `plate_box_b1`) where Claude never wrote to `workspace/` even for a named live project. If the Engineer actually wanted Claude to apply it directly, that's a one-line follow-up: type the exact same phrase (`"declara frame_plate estimada 120 x 55 mm"`) into that live project's session.
- **`frame_plate` must already have a cited `thickness_mm`** for the two-number phrase to succeed (height falls back to it, per §0.1's own "use thickness" instruction) — if `autonomía-de-5min`'s `frame_plate` lacks one, the Engineer's live smoke will get an honest `ValueError` ("'height_mm' debe ser un número finito mayor que 0...") rather than a silent invented height. Worth confirming that project's `thickness_mm` before smoking, or typing the explicit triple (`"declara frame_plate estimada 120 x 55 x 3 mm"`) instead.
- The disclosure field is unconditional (any `estimated_temporary` dim on any component), not plate-specific in the projector — harmless today since the writer only ever produces this source on plates, but worth remembering if this literal is ever reused by a future Buy for a different family.
- `"geometría"` disclosure text uses the generic word "PLACA" was dropped from the Board field version (kept only in the Continuity message) to avoid hardcoding a family assumption into the shared `_fields` helper; the Continuity declare-success message does say "PLACA" explicitly, matching lock #8's example copy.
