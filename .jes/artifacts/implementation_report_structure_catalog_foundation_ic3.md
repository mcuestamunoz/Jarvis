# Implementation Report — Structure Catalog Foundation IC-3 (assist)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_catalog_foundation_ic3.md](implementation_contract_structure_catalog_foundation_ic3.md)
**Baseline:** IC-1 + IC-2 landed · suite closed at 2188

---

## Files changed

- `src/jarvis/core/frame_catalog_assist.py` — **new**, mirrors `battery_catalog_assist.py` exactly: `FrameSuggestion` TypedDict, `build_frame_catalog_suggestions` (full unfiltered `list_frames()`, no ranking), `format_frame_catalog_suggestions` (numbered list showing manufacturer/model, size class, mass, material), `is_help_choose_phrase`/`match_suggestion_by_input` re-exported (not duplicated) from `motor_catalog_assist`.
- `src/jarvis/schemas/action_schema.py` — `InteractiveSessionState.frame_suggestions: list[dict] = []`, same tier as `motor_suggestions`/`propeller_suggestions`/`battery_suggestions`.
- `src/jarvis/core/orchestrator.py` — new `_offer_component_frame_catalog`/`_apply_component_frame_catalog_pick` (mirror the battery pair exactly: offer clears the three peer suggestion lists, apply calls `bind_frame_from_catalog` + `set_frame_material(..., catalog_ref=, component_name=)`, no recalculation, same as battery/propeller); new frame help-choose/pick gate block in `_handle_component_description`, inserted right after the battery block, using the same `_wants_catalog_help` predicate (already generic — no new incompleteness theory); the three existing motor/propeller/battery offer methods now also clear `frame_suggestions` (cross-family symmetry).
- `src/jarvis/core/acquisition_brief.py` — `"frame"` added to the `("motors", "propellers", "battery")` tuple that advertises "ayúdame a elegir"; stale comment ("frame... still has no bind path") corrected.
- `tests/test_frame_catalog_bind_ux.py` — **new**, 7 tests covering all of §4.
- `tests/test_cli_fail_routing_coherence.py` — one pre-existing test (`test_frame_wizard_ayudame_a_elegir_asks_size_class_from_persisted_state`) asserted the **old** behavior (that "ayúdame a elegir" for a pending frame fell through to the generic missing-datum prompt). That premise is exactly what this IC intentionally supersedes. Renamed it to `test_frame_wizard_unrecognized_reply_asks_size_class_from_persisted_state` and swapped its trigger phrase to a neutral one (`"continuar"`) that preserves its real, original subject (an unrecognized follow-up still re-derives the missing-datum prompt from persisted state) — not weakened, just no longer exercised via a phrase that now has a different, intended meaning. Added a new `test_frame_wizard_ayudame_a_elegir_opens_frame_catalog` asserting the new, correct behavior.
- `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` — one status-table row (IC-3 landed) plus removing "frame catalog **assist**" from the "still deferred" line.

No edits to `engineering_readiness.py` (verdict/gap logic), `project_continuity.py` (Continuity claim-copy strings — the Structure Foundations situation gate and BOM suffix from the prior IC are unchanged and untouched here), `library/frames/_datos.json` (seed unchanged), `frame_class_compatibility_state`, or any DSE/ranking module. `state_manager.py` was touched only for a documentation comment during drafting and then **reverted** to stay strictly within the IC's file allowlist — the actual persistence behavior (`frame_suggestions` excluded from `_PERSISTED_SESSION_FIELDS`) needed no code change since the field was simply never added to that allowlist.

## Behavior changed

- A pending/unbound `frame` component now responds to "ayúdame a elegir" (and the other `HELP_CHOOSE_PHRASES`) by listing the real IC-1 seed catalog, numbered, with manufacturer/model/size-class/mass/material.
- Picking a number binds the SKU: `components["frame"].catalog_ref` is set, `structure_mass_override_kg` mirrors the SKU's real mass (same single writer path as free text — confirmed unchanged), and BOM's `sku_resolved` correctly reports `True` for a live SKU.
- Acquisition Brief now advertises the catalog CTA for frame the same way it already does for motors/propellers/battery.
- **Confirmed by CLI walk** (not just unit tests): binding a frame whose declared class is smaller than the project's declared propeller diameter still fires `GAP-FRAME-PROP-SIZE` and the Structure Foundations IC's BOM suffix (`— clase incompatible nivel A`) — the new bind path composes with the existing claim-hygiene work with zero special-casing. `PROJECT STATUS` never claims readiness from a catalog pick alone.
- Free-text frame declaration is completely unaffected (regression-tested): describing a frame in plain text still works exactly as before, `catalog_ref` stays `None`.
- A TBS seed row with no stated material binds without inventing one; completeness stays honestly `"medium"`.

## Tests added/updated

- `tests/test_frame_catalog_bind_ux.py` (new): suggestion builder/formatter, offer path (populates + clears peers), apply path (catalog_ref + mass mirror + sku_resolved), TBS-no-material honesty, free-text regression, LEVEL A composition smoke.
- `tests/test_cli_fail_routing_coherence.py`: one test renamed/retargeted (see above, not weakened — same real assertion, neutral trigger phrase) + one new test for the now-intended "ayúdame a elegir opens the catalog" behavior.

## Tests executed

- Targeted: `pytest tests/test_frame_catalog_bind_ux.py tests/test_cli_fail_routing_coherence.py -q` → 15 passed.
- Full suite: `pytest -q` → **2197 passed**, zero failures, zero skipped.
- **CLI walk** (per §6.5): `ayúdame a elegir` → real numbered list → pick `1` (Armattan Rooster 5″) → `estado` shows `✓ frame: armattan_rooster_5in [armattan_rooster_5in] ... (high — clase incompatible nivel A)`, `GAP-FRAME-PROP-SIZE` in TOP GAPS, `PROJECT STATUS: NOT ASSEMBLY READY` — full chain verified honest end to end, transcript in the session record.

## Residual

- IC-3 does not touch `catalog_bound`'s reachability into any verdict — unchanged, unproposed.
- Frame ranking / "best frame for my thrust" remains out, as instructed.
- Continuity's situation/next-step copy was not touched — the acquisition brief + COMPONENT wizard path is the surface this IC uses, per §2.5's instruction not to expand Continuity scope.
