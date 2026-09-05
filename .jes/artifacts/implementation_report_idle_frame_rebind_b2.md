# Implementation Report — IDLE frame rebind (B2)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_idle_frame_rebind_b2.md](implementation_contract_idle_frame_rebind_b2.md)
**Baseline:** Structure block CLOSED · suite 2229

---

## Files changed

- `src/jarvis/core/frame_catalog_assist.py` — new `is_frame_rebind_phrase(user_input) -> bool`. Requires the frame/chasis noun **and** either a change/define verb (`cambiar`/`cambia`/`definir`/`define`/`modificar`/`modifica`) or a help-choose soft phrase (`ayudame` + `elegir`/`escoger`). Reuses `motor_catalog_assist._normalize_help` for the same lowercase+diacritics-stripped normalization every other assist module uses — no new convention.
- `src/jarvis/core/component_writers.py` — new `clear_frame_part_children(project_state)`: removes every component with `parent_key == "frame"`, a no-op when none exist. Single legal mutation point for the "clear before re-pick" rule (IC §3.4).
- `src/jarvis/core/orchestrator.py` —
  - New IDLE dispatch block, checked **before** FN-005's bare help-choose chain: when `mode == IDLE` and `is_frame_rebind_phrase(user_input)`, sets session to `DEFINE_MISSING_PARAMETERS`/`pending_missing_params=["frame"]` and calls `_offer_component_frame_catalog` directly — bypassing both the FN-014 `_next_pending_block is None` gate and `_wants_catalog_help`'s bound-only restriction, for this one explicitly-named component only.
  - `_apply_component_frame_catalog_pick` now calls `clear_frame_part_children` after the root write and before upserting the new SKU's part children (IC §3.4 / G-N4 catalog half).
  - No changes to `_try_start_acquisition_from_mention`, `_continue_block_acquisition`, or any motor/propeller/battery dispatch — B3 not smuggled in.
- `tests/test_idle_frame_rebind_b2.py` (new) — see below.

No edits to `_structure_evidence`, `_derive_subsystem_verdict`, `_derive_overall` (`engineering_readiness.py` — zero diff, confirmed via `git diff --stat`), Continuity copy (`project_continuity.py` unchanged this turn), or any arms↔motors/coherence logic.

## Behavior changed

- `"cambiar frame"`, `"definir frame"`, `"ayúdame a elegir frame"` (and `"...chasis"`/`"modificar"` variants) now reopen the real, numbered frame catalog from IDLE, even when architecture is 4/4 and frame is already catalog-bound — confirmed live for all three locked phrases plus two additional variants (`"ayudame a escoger el chasis"`, `"modificar el chasis"`).
- Picking a SKU after this rebind entry binds `catalog_ref`/mass/material/class exactly as the original IC-3 apply path does (unchanged), and now **clears** any existing `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` children before upserting the new SKU's own parts — confirmed live: rebinding an Armattan-bound frame (4 children) to TBS (no part fields) leaves **zero** `frame_*` keys, not stale Armattan materials.
- **Confirmed unaffected (regression):** bare `"ayúdame a elegir"` (no frame/chasis token) still triages motor → propeller → battery exactly as before, including the T1 motor-underspec re-offer taking precedence — the new detector never fires without an explicit frame/chasis noun. `"cambiar batería"`, `"cambiar motores"`, `"definir motores"` never open the frame catalog.
- Free-text root-only rewrite (G-N1, external work already in the tree) is untouched — this IC only reaches the **catalog** re-pick path.

## Tests added

`tests/test_idle_frame_rebind_b2.py` (21 tests): phrase-detector true/false cases (10, parametrized), T1/T2/T3 IDLE dispatch opens the frame catalog for all three locked phrases, T3's frame-vs-motor distinction, T4 pick binds `catalog_ref` + all four part children, T5 rebind-to-TBS clears stale Armattan children, T6 bare help-choose regression, T7 other-family phrases never open frame catalog (parametrized ×3).

## Tests executed

- Targeted: `pytest tests/test_idle_frame_rebind_b2.py -q` → 21 passed.
- Full suite: `pytest -q` → **2250 passed** (2229 baseline + 21 new tests), zero failures, zero skipped, zero weakened.

## Residual (per IC §6, explicitly out)

- B3 (motors/propellers/battery rebind) — not implemented; no proven pattern existed to generalize (per the investigation), and this IC does not touch their dispatch.
- Display-name → SKU resolution (`"frame Armattan Quads Rooster 5\""` typed as free text) — still falls through to whatever wizard currently owns `expected_keys`, unchanged.
- Arms↔motors / configuration↔motor_count Continuity coherence notes — not added (locked as debt).
- Clearing orphans on a **free-text** root rewrite (the other G-N4 half) — still not cleared; only the catalog re-pick path clears children, per IC §3.4/§3.5.
