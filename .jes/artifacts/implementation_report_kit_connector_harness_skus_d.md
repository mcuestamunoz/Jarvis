# Implementation Report — Kit SKUs D B1 (XT60 / JST-SH into existing holes)

**IC:** [implementation_contract_kit_connector_harness_skus_d.md](implementation_contract_kit_connector_harness_skus_d.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2523 · commit `3600b37`

---

## Re-fetch confirmation (live, 2026-09-09)

Re-fetched both cited pages before editing anything. Pololu (`https://www.pololu.com/product/2175/specs`): color "yellow", pin configuration "1x2", pin type "straight", item number 2175 — matches §3.2 exactly; the page's own prose sentence ("These high-current (60 A) XT60 connectors...") is confirmed to be prose, not a specs-table field, matching lock #6's own framing — `current_a` was **not** seeded. Pi Hut (`https://thepihut.com/products/jst-sh-cable-6-pin-pack-of-4`): 6 pins, 1.0mm pin spacing, 100mm/300mm cable length options, 26AWG, female JST-SH connectors on both ends, SKU CAB1009 — matches §3.2 exactly. Neither page states mass or dimensions. No STOP triggered.

## Files changed

- `src/jarvis/schemas/action_schema.py` — `CatalogRef.family` widened by exactly one member: `Literal["motor", "battery", "propeller", "esc", "frame", "kit_hardware"]`. `InteractiveSessionState.kit_hardware_suggestions: list[dict] = Field(default_factory=list)` added, same runtime-only tier as `frame_suggestions` (not added to `state_manager._PERSISTED_SESSION_FIELDS`, confirmed that allowlist needed no change).
- `library/kit_hardware/_datos.json` (**new folder**) — exactly two rows, `pololu_xt60_pair` (`kit_key: "power_connector"`) and `pihut_jst_sh_6pin_cab1009` (`kit_key: "signal_harness"`), each with only the cited fields from §3.2 and a `source_note` naming exactly what was/wasn't stated (including the N4 current_a exclusion and the N5 cable-length-is-not-a-box-axis note).
- `src/jarvis/knowledge/library.py` — new frozen `KitHardwareSpec` dataclass (identity + cited electrical fields, **no geometry field on the type at all** — confirmed by its own docstring and by T0's `hasattr` checks). `ComponentLibrary` gained `self._kit_hardware` cache, `_KIT_HARDWARE_KEYS = frozenset({"power_connector", "signal_harness"})`, `_kit_hardware_from_raw` (raises `ValueError` on any other `kit_key` — the loader rejects, never silently drops), `_load_kit_hardware`, `get_kit_hardware`, `list_kit_hardware(*, kit_key=None)` (filters so the connector wizard never lists the harness row and vice versa — confirmed T5), `has_kit_hardware`. **One** unified family, not two — per the Buy's own locked reasoning.
- `src/jarvis/core/catalog_bind.py` — new `bind_kit_hardware_from_catalog(sku, *, library=None, base=None)`. `suggested_key`/`component_type` come from the row's own `kit_key` (one function serves both holes). Projects only `pin_count`/`pitch_mm`/`wire_gauge_awg`/`color`/`pin_config` when cited — **never** `current_a` (lock #6), **never** any geometry key, **never** `cable_length_options_mm` as `length_mm` (confirmed T1/T2). `completeness` promoted to at least `"medium"`, matching the kit free-text relabel's own floor.
- `src/jarvis/core/kit_hardware_catalog_assist.py` (**new**, mirrors `frame_catalog_assist.py`) — one shared module for both kit holes (not two near-identical assist modules): `KitHardwareSuggestion`, `kit_hardware_spec_to_suggestion`, `build_kit_hardware_catalog_suggestions(kit_key, ...)` (filters by `kit_key`), `format_kit_hardware_catalog_suggestions`. Re-exports `is_help_choose_phrase`/`match_suggestion_by_input` from `motor_catalog_assist` unmodified (both already generic enough, confirmed by reading their implementations — `match_suggestion_by_input` only ever reads `s["idx"]`/`s.get("name")`, which `KitHardwareSuggestion` provides).
- `src/jarvis/core/project_closure.py` — `_bom_sku_resolved` gained one more `if family == "kit_hardware": return default_library.has_kit_hardware(sku)` branch, same shape as every other family.
- `src/jarvis/core/orchestrator.py`:
  - New `_KIT_HARDWARE_KEYS` module constant (`{"power_connector", "signal_harness"}`).
  - New `_offer_kit_hardware_catalog`/`_apply_kit_hardware_catalog_pick` methods — one shared pair for both holes (mirrors `_offer_component_frame_catalog`/`_apply_component_frame_catalog_pick`'s shape). The apply path writes via the **existing** `set_control_component` (no new physics writer) and never recomputes calculations — a kit hole was always display/BOM-only.
  - New help-choose/pick gate in `_handle_component_description`, inserted right after the frame block (before the "Affirmative" check, still well before `infer_components` is called) — gated on `expected_keys[0] in _KIT_HARDWARE_KEYS` (**never** `"esc" in expected_keys`, which is the unrelated `prop_adapter`/propulsion-specific gate).
  - All four existing `_offer_component_{motor,propeller,battery,frame}_catalog` functions now also clear `kit_hardware_suggestions: []` in their `model_copy(update={...})` calls (the ★4 cross-family clear rule extended to the new list).
- `src/jarvis/core/acquisition_target.py` — appended one short clause to `COMPONENT_PROMPTS["power_connector"]`/`["signal_harness"]`: `"Di 'ayúdame a elegir' para ver el catálogo."` — the free-text example (`'XT60'`) was kept, not removed. Aliases (`xt60`→`power_connector`, etc.) untouched.
- `tests/test_kit_connector_harness_skus_d.py` (**new**) — T0–T8 per the IC's own table.

## Behavior changed

- Once architecture is 4/4 and a kit hole's single-key wizard is open, `"ayúdame a elegir"` now lists exactly one catalog SKU (the one whose `kit_key` matches the active hole) and clears every peer suggestion list — verified live: the connector wizard's help-choose shows only "Pololu XT60 Connector Male-Female Pair, Yellow (PN 2175)"; the harness wizard's shows only "The Pi Hut JST-SH Cable - 6 Pin (PN CAB1009)" — neither ever lists the other's row.
- Picking `"1"` binds `catalog_ref={family: "kit_hardware", sku: "pololu_xt60_pair"}`, projects `color`/`pin_config` (no `current_a`, no geometry), removes the Board slot, and the wizard's own `still_missing` closes (single-key scope) — confirmed T6, and live: `"✓ Arquitectura completa (4/4)."` appears in the same turn's message.
- Free text (`"XT60"`) still saves with `catalog_ref is None` — confirmed T7 and live, unchanged from kit B1-min.
- `_geometry_from_spec` on both bound specs is `None` — confirmed T3; the type itself (`KitHardwareSpec`) has no geometry field to even accidentally populate.
- `robot`/other non-`dron`/`uav` projects: the kit IDLE bridge (`_try_start_kit_component_from_mention`) still returns `None` for a kit-key mention even though the library itself has rows for that `kit_key` — confirmed T8 (asserted directly at the dispatch method, mirroring the kit-B1-min cycle's own T11-style proof, since this exact phrase falls through to the LLM on a robot project via pre-existing, unrelated routing — not this test's subject).
- Architecture/PASS/hover/autonomy byte-identical — `BLOCK_TO_COMPONENTS`/`KIT_TO_COMPONENTS`/`engineering_readiness.py` all confirmed zero-diff via `git diff`.

## Tests

- `python -m pytest -q tests/test_kit_connector_harness_skus_d.py` → **9 passed** (T0–T8).
- `python -m pytest -q` (full suite) → **2532 passed**, 0 failed (baseline 2523 + 9 new).
- No existing test needed updating — contrary to the IC's own anticipation ("expect `_bom_sku_resolved` + suggestion-clear lists"), the full suite stayed green with zero pre-existing assertion touched; the four `_offer_component_*` functions' own tests never asserted an exhaustive/closed set of cleared session fields, so adding `kit_hardware_suggestions: []` to each was purely additive from their perspective.
- `git diff -- src/jarvis/core/system_architecture_catalog.py` (scoped to the `BLOCK_TO_COMPONENTS` dict body) — empty. `git diff --stat -- src/jarvis/core/engineering_readiness.py` — empty.
- `git status --short -- ui/ library/frames library/helices library/motores` — empty (only the new `library/kit_hardware/` folder was added).
- No version bump (`pyproject.toml` still `0.3.8`).
- Live demo (`autonomía-de-10min`) re-verified directly (read-only): `power_connector` card still shows empty `fields` (the free-text "XT60" declaration, `catalog_ref: None`, unchanged), `latest_results.simulation.safety_margin_ratio` unchanged. No `workspace/` mutation from this cycle.

## Non-goals honored

- No `prop_adapter` catalog row, no VTX/RX, no second connector aisle — the seed is exactly the two locked rows (confirmed T0: `{i.name for i in items} == {"pololu_xt60_pair", "pihut_jst_sh_6pin_cab1009"}`).
- No `current_a` seeded from Pololu's prose (lock #6) — confirmed T1: `"current_a" not in spec.properties`.
- No L×W×H/diameter ever projected — confirmed T1/T2/T3 directly, and by the `KitHardwareSpec` type itself having no such field to populate even by accident.
- `cable_length_options_mm` stays catalog-only, never `length_mm` — confirmed T2.
- Kit help-choose never opens inside the energy/propulsion composite wizard — the new gate is scoped to `expected_keys[0] in _KIT_HARDWARE_KEYS`, structurally distinct from the composite wizard's own `expected_keys` shapes (`["motors","propellers","esc"]`-style), and is positioned in the same single-key-only code region as the pre-existing kit relabel.
- N2 (`power_connector` mid-architecture nag) untouched — `project_continuity.py` has zero diff this cycle (confirmed via `git status`, not even listed as modified).
- `ComponentLibrary` remains the only JSON reader — no orchestrator code reads `library/kit_hardware/_datos.json` directly.
- No version bump; `BLOCK_TO_COMPONENTS`/`KIT_TO_COMPONENTS` values unchanged.

## Remaining risks / notes for review

- None identified beyond what the IC itself already flagged (N4/N5 honesty notes, both correctly threaded into the seed's own `source_note` fields for future review visibility).
