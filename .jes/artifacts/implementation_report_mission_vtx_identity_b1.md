# Implementation Report — VTX identity + first catalog seed (`B1-mission-vtx-identity`)

**IC:** [implementation_contract_mission_vtx_identity_b1.md](implementation_contract_mission_vtx_identity_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-18
**Baseline:** package `0.4.1` (unchanged, no version bump) · suite **3165 passed, 1 skipped** (≥3134 checkpoint met) · UI **105 passed** (unaffected — no UI files touched)

---

## §0.2 fork — followed cameras' full fluid path, not a half-land

VTX gets its own key (`vtx`), its own block (`video_link`), its own library family (`library/vtx/`), and the complete ESC/camera-shaped lifecycle in this Buy: load → list → pick → **bind** → `catalog_ref` + high → mass mirror → `cambiar vtx` → `actualiza el vtx`. Never folded into `radio_module` (a VTX is the video link; a radio like ELRS is the control link — deliberately separate physical objects) and never folded into `cameras`/`perception` (which stays `["cameras"]` only, per lock #4 — no forced VTX stub on a camera-only project).

## File tree + SKU census

```
library/vtx/_datos.json   — hglrc_zeus_800 (§0.1 cite, locked verbatim)
```

## Architecture (`src/jarvis/core/system_architecture_catalog.py`)

New block `"video_link"` (`BLOCK_TYPE["video_link"] = "component"`, `BLOCK_TO_COMPONENTS["video_link"] = ["vtx"]`). `BLOCK_ALIASES` gained `vtx`/`video`/`vídeo`/`enlace de video`/`enlace de vídeo`/`transmisor de video`/`transmisor de vídeo`/`fpv vtx` → `"video_link"` — bare `video`/`vídeo` deliberately included **only** here (the explicit "add a block" step, a lower-ambiguity context) and never in the component-identity keyword set below.

## Identity (`src/jarvis/domains/aerial.py`)

`VTX_KEYWORDS`, `VTX_MODEL_MAP = {"hglrc": "hglrc"}` (only the cited brand — never invented beyond the seed), `extract_vtx_properties`, `_vtx_completeness`, and a new `ComponentRule` (`component_type="video_link"`, `suggested_key="vtx"`) registered in `aerial_registry` right after the radio rule. `VTX_KEYWORDS` deliberately excludes bare `"video"`/`"vídeo"` (too generic for free text) **and any `"fpv"`-containing phrase**.

**Bug caught by my own test suite, fixed before shipping:** I initially included `"fpv vtx"` in `VTX_KEYWORDS`, reasoning the qualified phrase was "unambiguous." It isn't — `ComponentRuleRegistry.match()` is first-match-wins by registration order (`component_rules.py`), and the cameras rule (registered before vtx) already carries bare `"fpv"` in `CAMERA_KEYWORDS`. Any phrase containing `"fpv"` — including `"fpv vtx"` — resolves to `cameras` regardless of what else it contains, making a `"fpv vtx"` alias a dead, misleading promise. Removed it; `test_t9_bare_fpv_still_resolves_camera_not_vtx` now pins the actual (narrower) reachable set, and the code comment explains why.

## `ComponentLibrary` extension (`src/jarvis/knowledge/library.py`)

`VtxSpec` (`name`, `manufacturer`, `model`, `identity_status`, `source_url`, `source_note`, `length_mm`/`width_mm`/`height_mm`, `mass_g`) — **deliberately no `power_w` field at all** (lock #12): a VTX's cited spec is RF output in milliwatts, a physically different quantity from electrical DC draw; there is no honest number to carry on this dataclass this Buy. `_load_vtx`/`get_vtx`/`list_vtx`/`has_vtx` mirror `_load_cameras`/etc. byte-for-byte.

## Schema (`src/jarvis/schemas/action_schema.py`)

`CatalogRef.family` widened to include `"vtx"`. New runtime-only `vtx_suggestions: list[dict]` session field, same tier as `camera_suggestions`.

## Bind (`src/jarvis/core/catalog_bind.py`)

`bind_vtx_from_catalog(sku, *, library=None, base=None)` — same shape as `bind_camera_from_catalog`, projecting L×W×H + `mass_g` only. Reuses the exact preserve-manual-mass-on-same-SKU-refresh discipline the camera post-review fix established, generalized to a small `_VTX_MANUALLY_OVERRIDABLE_KEYS = frozenset({"mass_g"})` (mass-only — no `power_w` key exists to ever preserve).

## Mass mirror widening (`src/jarvis/core/component_writers.py`)

`_MISSION_MASS_KEYS` widened to `("cameras", "radio_module", "vtx")` (lock #11). **Power stays separate, not shared** (lock #12's own "prefer mass-only unless trivial" guidance): a new `_MISSION_POWER_KEYS = ("cameras", "radio_module")` constant now backs `set_mission_component_power`'s validation and sum loop — `vtx` is deliberately never in it, so `set_mission_component_power(state, "vtx", ...)` still raises `ValueError` (verified: `test_t7_mission_component_power_refuses_vtx_key`). `refresh_component_from_catalog`'s mirror-on-refresh block now guards the mass mirror by `_MISSION_MASS_KEYS` and the power mirror by `_MISSION_POWER_KEYS` **independently** (two separate `if` blocks, not one shared gate) — a VTX refresh re-mirrors mass but never touches `mission_accessory_power_w`. `_REFRESH_BINDERS["vtx"] = bind_vtx_from_catalog` registered for `actualiza el vtx`.

## Assist + orchestrator wiring (`src/jarvis/core/vtx_catalog_assist.py` new, `orchestrator.py`)

`vtx_catalog_assist.py` mirrors `camera_catalog_assist.py` (no `power_w` column, since VTX never carries one). `_offer_component_vtx_catalog`/`_apply_component_vtx_catalog_pick` mirror the camera pair — apply calls `set_mission_component_mass` only, never `set_mission_component_power`. Singleton head-key routing gate `expected_keys[0] == "vtx"` added right after the camera gate (same `_wants_catalog_help`-based shape — `"video_link"` is a singleton block like `"perception"`, so one gate covers both first-time acquisition and the `cambiar vtx` reopen). IDLE rebind dispatch gained an `elif _rebind_key == "vtx":` branch. `vtx_suggestions: []` added to every peer-suggestion-clear dict (motor/propeller/battery/frame/kit-hardware/ESC/camera offers, `_control_identity_peer_clear`), and the camera offer now also clears `vtx_suggestions` (and vice versa) — offering either family's list retires a pending pick of the other.

## Rebind / refresh triggers

- `catalog_rebind_assist.py`: `"vtx"` added to `CatalogRebindKey`/`_FAMILY_NOUN_PATTERNS` (narrow `\bvtx\b` — matching only the IC's own locked examples, not the broader `VTX_KEYWORDS` identity set, same discipline every other family's rebind noun already uses) and `_PURE_PHRASE_STRIP_RE`.
- `catalog_refresh_assist.py`: same narrow `vtx` noun added to `_SUBJECT_PATTERNS`.

## Continuity (`src/jarvis/core/reasoning_layer.py`)

New `_mission_vtx_suggestion(components)` wired into `_mission_aware_high_margin_suggestion`'s waterfall **after** the camera/radio power step and **before** the final margin-review fallback — the IC's own locked default slot (§0.2: "after camera power / before soft margin"). Because it sits after every earlier camera/radio step in the same waterfall (which already return first when incomplete), reaching this step already implies "mission intent + cameras present" per lock #15 — no extra guard needed. Fires `"Declara VTX (enlace de vídeo)"` (`action_type="declare_mission_vtx"`) only while `vtx` is absent or low; clears once `vtx` reaches non-low completeness (verified T8).

## BOM (`src/jarvis/core/project_closure.py`)

`_bom_sku_resolved` gained a `family == "vtx"` branch calling `default_library.has_vtx(sku)` — same class as the concurrent `B1-bom-sku-resolved-cameras` fix, extended the same turn the family/bind landed (never a deferred half-land, per lock #10's own precedent).

## Regressions found and fixed

1. **Two hardcoded registry-length tests** (`tests/test_aerial_domain.py::test_aerial_registry_has_four_rules`, `tests/test_control_component.py::test_aerial_registry_has_seven_rules`) — both asserted `len(aerial_registry) == 13`; bumped to `14` (the new vtx rule), comments updated to name the added rule.
2. **Five terminal-margin-review tests** across `test_mission_mass_energy_b1.py`, `test_mission_continuity_mount_endurance_b1.py` (one shared fixture, `_mission_components()`), `test_continuity_mission_intent_b1.py` (×2), and `test_mission_power_w_b1.py` — all previously reached `"Revisar margen vs carga de misión"` without a `vtx` component declared. Same category of regression the mount+endurance and power Buys each caused (and fixed) when they extended this exact ladder — fixtures updated to include a fully-defined `vtx` component so they keep reaching the same terminal state they always tested for; no assertion weakened.

## Tests

`tests/test_mission_vtx_identity_b1.py` (new, 31 tests) — T1–T12 per IC §2, plus extras: the fpv/VTX_KEYWORDS collision regression, a composite-wizard non-steal test (T9), and the BOM/`has_vtx` display test (T10). Full suite: 3165 passed, 1 skipped.

## Forbidden items — confirmed NOT done

No RF mW → `power_w` invention (`VtxSpec` has no `power_w` field at all; `set_mission_component_power` fail-closed refuses the `vtx` key — verified). No half-land (pick always binds with `catalog_ref`+high+mass mirror; rebind/refresh wired same turn). No invented mm/g beyond the §0.1 cite. No fold into `radio_module`/`cameras` (separate key, separate block, separate library family). No Conversation Engine, no LLM, no version bump. No workspace mutation — tests-only, per lock #18.

## Remaining risks / named debt

- **Engineer smoke (§3) not run by this implementer** — per the IC's own handoff, left for the Engineer.
- VTX mount/pose Continuity (an analogous `_mission_mount_suggestion` step for `vtx`) is explicitly out of scope (IC §4, "Mount Continuity for vtx | Follow-on") — a VTX can still be mounted/posed manually via the existing generic mount/pose commands, just without a Continuity nudge.
- Only one SKU exists (same maturity level cameras had at its own first-seed cut).
- If a future VTX row ever cites real mA (not just RF mW), a follow-on Buy would need to add a genuine DC-draw field to `VtxSpec` and wire it through `_MISSION_POWER_KEYS` — deliberately not anticipated here per lock #12.
