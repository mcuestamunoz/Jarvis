# Implementation Report — Estimated-temporary ESC height (Skystars KO50A II) B1

**IC:** [implementation_contract_geometry_estimated_temporary_esc_skystars_b1.md](implementation_contract_geometry_estimated_temporary_esc_skystars_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-14
**Baseline:** package `0.4.1` · suite 2911 → **2929** (18 new tests)

---

## §0.1 bag — filled after clarification, not invented

The IC's own §0.1 arrived with `height_mm: ?` (empty) and the IC's own Status line pre-announced a B0 hold for exactly that reason (same discipline as the original plate-box cycle). I stopped before shipping anything on the empty bag and asked the user directly. The Engineer then supplied the bag explicitly in conversation:

```
height_mm: 8
projects: 10-min-autonomía
```

No value was invented by me at any point — I offered `speedybee_bls_60a_30x30_4in1`'s own cited **8.0mm** height purely as reference context (a same-topology 4-in-1 ESC already in the catalog) before asking, and the Engineer independently chose to use that same number as their own estimate — an explicit Engineer decision, not an agent default (the IC's own §0.1 "forbidden_copy" note is about the agent silently reusing that number; it was reused here only because the Engineer said so, after being shown it as one data point).

## Catalog SoT rule honored (lock #3)

`library/esc/_datos.json`'s `skystars_ko50a_ii_bls` row is **untouched** — still no `height_mm` key. Confirmed via `test_t8_catalog_json_still_omits_height_mm_for_skystars` and a direct `git status`-equivalent check in the test itself.

## New additive writer (lock #6) — `set_estimated_temporary_esc_height`

`component_writers.set_estimated_temporary_esc_height(project_state, component_key, height_mm)` — a **separate** function from `set_estimated_temporary_plate_envelope`, not a broadened plate allowlist. Scoped to the literal `"esc"` key (ESC has no ordinal siblings the way `frame_plate*` does). Requires the ESC to **already** carry cited `length_mm`/`width_mm` (any source) — raises `ValueError` otherwise, since this writer's whole contract is completing a hybrid box, never seeding a lone axis onto an otherwise-boxless ESC. Writes only `height_mm`, `source="estimated_temporary"`, `confidence=0.3` (identical confidence convention to the plate writer) — every other property (`mass_g`, `current_a`, `catalog_ref`, `mounted_on`, `declared_box_pose`) survives untouched. Reuses `_clear_fit_attestations_after_geometry_change`.

## Continuity grammar (lock #7)

New `estimated_temporary_esc_assist.py`, mirroring `estimated_temporary_plate_assist.py`'s gate shape (declara + provisional keyword) but for a single axis instead of a L×W×H triple. Locked trigger family: **`declara el esc estimado/temporal/provisional <N> mm`** (also accepts phrasing like `declara la altura del esc estimada <N> mm` — the gate only requires the ESC subject noun + provisional keyword + one `<N> mm` number anywhere in the phrase, not fixed word order). Subject resolution reuses `mounted_on_declare_assist.resolve_component_subject_noun`'s existing table, scoped to `"esc"` specifically — a plate/battery/etc. provisional phrase correctly falls through to `NONE` (proven by `test_t7_none_for_other_subjects`), so it never steals from `estimated_temporary_plate_assist`'s own bridge, and vice versa (plate's own module already deferred to `NONE` for a non-plate subject before this Buy — confirmed unchanged).

Orchestrator bridge `_try_handle_estimated_temporary_esc_height_declare` wired immediately after the plate's own provisional bridge (same conceptual family), before the plain declared-envelope bridge.

## Gates — confirmed unchanged with ZERO code changes (lock #9)

`screen_posed_envelope`, `set_component_declared_fit_attestation`, and `fit_relations_assist.assess_fit_relations` all **already** treat any `estimated_temporary` box dimension as `estimated_dims`/refused — none of the three needed a single line changed. Confirmed directly: T4 (screening → `estimated_dims`), T5 (attestation SET → `ValueError`, never grants), T6 (fit-relations row → `estimated_dims`, `ready_count`/`attested_count` both 0).

## Disclosure copy (lock #10)

```
Declarado (ESTIMATED_TEMPORARY): esc H 8 mm (source=estimated_temporary).
ESC · H ESTIMADA TEMPORAL · L×W citada (41×46) · evidencia H: ninguna
ficha de esta revisión · sustituir al citar/medir H: SÍ. Jarvis no valida
"cabe" ni "declaro verificado" con esta altura.
```

L×W in the disclosure is read live from the component's own current properties (never hardcoded), so the same message stays correct if this writer is ever reused for a different ESC with different cited L×W.

## Replace path (lock #11) — confirmed working with ZERO new code

`refresh_component_from_catalog` already handles both halves correctly via `bind_esc_from_catalog`'s existing `base=` merge semantics:
- While the catalog still lacks `height_mm` for this SKU, a refresh **preserves** the estimated value untouched (`test_replace_path_refresh_preserves_estimate_while_catalog_still_lacks_h`).
- The moment the catalog SKU gains a real `height_mm` (simulated via `monkeypatch.setitem` on the library's own cache, never touching disk), a refresh **overwrites** the estimate with the new `declared` value (`test_replace_path_refresh_overwrites_estimate_once_catalog_cites_h`).

No new code was needed for lock #11 — both behaviors already fall out of the existing bind/refresh machinery.

## §0.2 (FC bag) — not taken

The Engineer's clarification only filled §0.1 (ESC height); §0.2 (an optional estimated FC box for `skystars_f4_v4`) was never filled and is explicitly optional in the IC ("only if Engineer wants FC solid this ★"). Left untouched — `skystars_f4_v4` stays identity-only, per lock #12's own default. No T9 tests apply.

## A real finding during live apply: stale property leak on ESC rebind (flagged, not fixed here)

Applying this live to `10-min-autonomía` required first rebinding the project's ESC from its current SKU (`speedybee_bls_60a_30x30_4in1`, which already has a full, correctly-cited `height_mm=8.0`) to `skystars_ko50a_ii_bls`, using the existing `bind_esc_from_catalog(sku, base=old_spec)` seam (per this IC's own parent reference — "ESC visor rebind B1 CLOSED"). Testing this rebind step in isolation surfaced a real, **pre-existing** (not introduced by this Buy) correctness gap: `bind_esc_from_catalog`'s `base=` merge (`{**base.properties, **projected}`) only overwrites a property key when the **new** SKU's catalog row actually defines it. Since Skystars has no `height_mm`, a bare rebind (rebind alone, with no follow-up write) left the **old SpeedyBee `height_mm=8.0` sitting there marked `source="declared"`** — a stale fact from a physically different ESC, silently surviving under a `declared` label that now (falsely) implies it's a cited Skystars fact.

This never reached the live project file: my own sequence always ran the new `set_estimated_temporary_esc_height` write **immediately** after the rebind in the same operation, which unconditionally overwrites `height_mm` regardless of what the rebind left there — the final persisted state is correct (verified property-by-property below). But the underlying gap in `bind_esc_from_catalog`'s general rebind semantics is real and not scoped to this Buy to fix (it would affect ANY ESC-to-ESC rebind where the new SKU's catalog row omits a property the old one had, not just this height_mm case) — flagging it explicitly for Cursor/Engineer as a named, out-of-scope debt rather than silently discovering and hiding it.

## Files changed

- **`src/jarvis/core/component_writers.py`** — new `set_estimated_temporary_esc_height`.
- **`src/jarvis/core/estimated_temporary_esc_assist.py`** (new) — `EstimatedEscHeightDeclareResult`, `parse_estimated_temporary_esc_height_declare`.
- **`src/jarvis/core/orchestrator.py`** — new `_try_handle_estimated_temporary_esc_height_declare` IDLE bridge.
- **`tests/test_geometry_estimated_temporary_esc_skystars_b1.py`** (new) — 18 tests, T1–T8 plus the replace-path and IDLE-non-mutation regressions.
- **`workspace/10-min-autonomía-7e400f0a4983/state.json`** — live apply (Path D, per lock #14 and the Engineer's own explicit `projects: 10-min-autonomía` instruction): ESC rebound from `speedybee_bls_60a_30x30_4in1` to `skystars_ko50a_ii_bls` (pose/mount preserved, fit attestation was already `None`), `height_mm=8.0` set `source=estimated_temporary`. This directory is git-ignored (`workspace/` in `.gitignore`) — verified directly via the file's own JSON content, not `git diff`.

## Tests

Executed: `python -m pytest -q` → **2929 passed, 1 skipped** (0 failed). Ran the new file alone first (18 passed) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_catalog_row_has_lw_mass_no_height` |
| T2 | `test_t2_bound_esc_no_full_box_yet` |
| T3 | `test_t3_estimated_height_yields_hybrid_box`, `test_t3_writer_requires_esc_key`, `test_t3_writer_requires_prior_lw`, `test_t3_writer_rejects_non_positive_height` |
| T4 | `test_t4_screening_refuses_estimated_dims` |
| T5 | `test_t5_fit_attestation_refuses_estimated_esc` |
| T6 | `test_t6_fit_relations_row_is_estimated_dims` |
| T7 | `test_t7_trigger_and_parse`, `test_t7_incomplete_without_number`, `test_t7_none_for_other_subjects`, `test_t7_idle_disclosure_copy_includes_estimada_temporal_and_replace_signal` |
| T8 | Full suite green above; `pyproject.toml` still `0.4.1`; `test_t8_catalog_json_still_omits_height_mm_for_skystars` |
| T9 | Not applicable — §0.2 not taken |

Additional coverage: the replace-path pair described above; `test_idle_unrelated_phrase_falls_through` (no mutation on an unrelated trigger); `test_projector_regression_full_suite_local_geometry_unaffected` (a non-Skystars boxless ESC is untouched by this Buy).

## Live smoke evidence (`10-min-autonomía`, post-apply)

- Board: `esc` geometry now `{shape: box, length_mm: 41.0, width_mm: 46.0, height_mm: 8.0}` — a full box, was previously a full box too (SpeedyBee) but is now honestly Skystars + estimated H rather than a different SKU's fully-declared box.
- `screen_posed_envelope(esc, ...)` → `estimated_dims` (refuses to compare).
- `relaciones` checklist → `esc` row `estimated_dims`, `0 listas para declarar verificado`.
- `parece un dron` → unaffected (`silueta_estimada (B*)`, unchanged) — the silhouette checklist never inspects ESC's own estimated flag, only the plate's; this is expected, pre-existing scope, not a gap this Buy introduces.
- `library/esc/_datos.json` re-confirmed unchanged on disk after the live apply.

## Non-goals honored

No `height_mm` seeded into `library/esc/_datos.json` (confirmed). No invented number — the Engineer explicitly chose 8mm after being shown, not defaulted to, the SpeedyBee reference. No SKU-mismatched "declared" claim survives in the FINAL persisted state (see the stale-leak finding above — caught and neutralized by this Buy's own writer sequence, not silently shipped). No plate-box work. No Path N. No version bump. `library/fc/` untouched (§0.2 not taken).

## Remaining risks / notes for review

- **`bind_esc_from_catalog`'s stale-property-leak on a cross-SKU rebind** (detailed above) is a real, pre-existing gap outside this Buy's own scope — any FUTURE ESC-to-ESC "cambiar esc" rebind where the new SKU's catalog row omits a property the OLD SKU had would silently keep the old value labeled `declared`. Flagging for a separate, dedicated ★ (likely scoped to `bind_esc_from_catalog`/`ESC visor rebind B1`'s own review, not this estimated-height Buy).
- The live apply to `10-min-autonomía` is a real project mutation (ESC identity switch + a new estimated axis) — I confirmed the sequencing produces a fully correct final state, but this is a heavier live change than a single-property write; flagging explicitly per this session's own risk-communication norm even though it was explicitly requested (`projects: 10-min-autonomía`).
- `autonomía-de-5min` was **not** touched (the Engineer named only `10-min-autonomía`) — its ESC (if any Skystars-bound) remains whatever it already was.
