# Implementation Report — First `library/cameras` seed (`B1-library-cameras-seed`)

**IC:** [implementation_contract_library_cameras_seed_b1.md](implementation_contract_library_cameras_seed_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-18
**Baseline:** package `0.4.1` (unchanged, no version bump per lock #16) · suite **3102 passed, 1 skipped** (≥3068 checkpoint met) · UI **105 passed** (unaffected — no UI files touched)

---

## Post-review fix — manually-declared mass survives a same-SKU refresh

`/code-review medium` (2026-09-18) found that `bind_camera_from_catalog(sku, base=spec)` always let the catalog's own `mass_g` overwrite whatever was in `base.properties["mass_g"]`, even on a same-SKU refresh. Unlike L×W×H, camera `mass_g` has a **second, independent write path** — `mission_mass_declare_assist` → `set_mission_component_mass` (`"cámara 28 g"`) — that carries the **same** confidence/source tag (`"declared"`, 0.9) as a catalog projection, not a lower-confidence `estimated_temporary` one. So a user who corrected the catalog's cited mass with a real measurement, then ran `actualiza la cámara`, would silently lose that correction with no warning — indistinguishable from data loss.

Fix (`src/jarvis/core/catalog_bind.py`, `bind_camera_from_catalog`): on a same-SKU call (`base.catalog_ref.sku == sku`) where `base` already carries a `mass_g` value, the catalog's own `mass_g` is dropped from `projected` before the merge — the existing value survives untouched. Catalog `mass_g` still applies on every genuine first bind and on a rebind to a **different** SKU (a real SKU change legitimately means a new physical mass). L×W×H are unaffected — they have no competing manual-declare grammar, so the original "catalog truth always wins on refresh" behavior (same precedent `set_estimated_temporary_esc_height` documents) is unchanged for them.

Two new regression tests added: `test_same_sku_refresh_preserves_manually_declared_mass` (refresh + same-SKU re-pick both preserve a manual mass) and `test_different_sku_rebind_still_projects_new_catalog_mass` (a genuine SKU change still projects the new row's own mass, confirming the fix didn't overcorrect). Full suite: 3102 passed, 1 skipped.

---

## §0.2 fork — followed the ESC pattern, not the FC/sensors mistake

The pick path for cameras calls `bind_camera_from_catalog` directly (ESC-shaped), never a free-text-only apply. A numbered pick always leaves `catalog_ref` set, `completeness="high"`, and the cited dims + `mass_g` projected — there is no half-wired state where a camera shows as "picked" but carries no `catalog_ref`. Rebind (`cambiar cámara`) and refresh (`actualiza la cámara`) are wired in **this** Buy, not deferred.

## File tree + SKU census

```
library/cameras/_datos.json   — runcam_phoenix_2 (§0.1 cite, locked verbatim)
```

## `ComponentLibrary` extension (`src/jarvis/knowledge/library.py`)

New `CameraSpec` frozen dataclass: same box-envelope shape as `FcSpec`/`SensorSpec` (`name`, `manufacturer`, `model`, `identity_status`, `source_url`, `source_note`, `length_mm`/`width_mm`/`height_mm`) **plus** an optional `mass_g` (lock #4) — the one field this family carries that FC/sensors don't. `_load_cameras`/`get_camera`/`list_cameras`/`has_camera` mirror `_load_sensors`/`get_sensor`/`list_sensors`/`has_sensor` byte-for-byte (same missing-file → empty-dict fallback, same `KeyError` message shape). `ComponentLibrary.__init__` gained a `self._cameras` cache slot.

## Schema (`src/jarvis/schemas/action_schema.py`)

`CatalogRef.family` widened to include `"cameras"` (lock #5). New runtime-only `camera_suggestions: list[dict]` session field, same tier as `esc_suggestions`/`flight_controller_suggestions`/`sensor_suggestions` (not in `state_manager._PERSISTED_SESSION_FIELDS`).

## Bind (`src/jarvis/core/catalog_bind.py`)

`bind_camera_from_catalog(sku, *, library=None, base=None)` — ESC-shaped signature and merge discipline: projects cited `length_mm`/`width_mm`/`height_mm`/`mass_g` (only the keys the row actually states), `suggested_key="cameras"`, `completeness="high"`, `catalog_ref=CatalogRef(family="cameras", sku=sku)`. `component_type="perception"` — matched to `aerial.py`'s existing free-text `ComponentRule` for cameras (which uses the block name `"perception"` as `component_type` with `suggested_key="cameras"`) so a catalog bind and a free-text declare never disagree on this component's own type label. Uses the shared `_merge_base_properties_dropping_stale_catalog_keys` with `_CAMERA_CATALOG_PROJECTED_KEYS = {length_mm, width_mm, height_mm, mass_g}` (lock #6) — a rebind to a SKU that doesn't state `mass_g` drops the stale value from the old SKU rather than leaking it (T6, synthetic two-row library test).

Mass mirroring is explicitly **not** this function's job — it only projects `properties["mass_g"]`; the caller (orchestrator apply-pick, and `refresh_component_from_catalog`) is responsible for calling `component_writers.set_mission_component_mass` afterward (lock #8), same division of labor `bind_battery_from_catalog` already has with the legacy `battery_mass_kg` param mirror.

## Refresh (`src/jarvis/core/component_writers.py`)

`_REFRESH_BINDERS["cameras"] = bind_camera_from_catalog` (lock #12). `refresh_component_from_catalog` now also re-mirrors `mission_payload_mass_kg` via `set_mission_component_mass` whenever the refreshed `component_key` is one of `_MISSION_MASS_KEYS` (`cameras`/`radio_module`) — the catalog seed is the only place that number could change on a refresh, and no other line in that writer touches `current_parameters`. This lives inside the writer itself (not the orchestrator caller), so `actualiza la cámara` can never forget the mirror regardless of call site.

## Assist (`src/jarvis/core/camera_catalog_assist.py`, new)

`build_camera_catalog_suggestions`/`format_camera_catalog_suggestions`/`camera_spec_to_suggestion` — thin glue over `list_cameras()`, no ranking, mirrors `esc_catalog_assist.py`'s shape exactly. Reuses (not duplicates) `is_help_choose_phrase`/`match_suggestion_by_input` from `motor_catalog_assist` (★2 discipline).

## Rebind / refresh triggers

- `catalog_rebind_assist.py`: `"cameras"` added to `CatalogRebindKey`, `_FAMILY_NOUN_PATTERNS` (`camara|camaras|camera|cameras` — accent-stripped, matching `_normalize_help`'s own normalization; deliberately **excludes** the broader `fpv`/`vision` identity-declare-only aliases, per Engineer note), and `_PURE_PHRASE_STRIP_RE`.
- `catalog_refresh_assist.py`: same noun set added to `_SUBJECT_PATTERNS`.

## Orchestrator wiring (`src/jarvis/core/orchestrator.py`)

- `_offer_component_camera_catalog` / `_apply_component_camera_catalog_pick` — mirror `_offer_component_esc_catalog`/`_apply_component_esc_catalog_pick`; apply calls `bind_camera_from_catalog(sku, base=existing)`, writes via the existing `set_control_component`, then calls `set_mission_component_mass(updated_state, "cameras", mass_value)` before saving (lock #8) and clears every peer suggestion list.
- Singleton head-key routing gate `expected_keys[0] == "cameras"` (FC/sensors-shaped gate — `_wants_catalog_help` OR an explicit help-choose phrase) placed after the sensors gate: `"perception"` is already a singleton architecture block (`["cameras"]`, `system_architecture_catalog.py`), so this one gate covers **both** first-time acquisition and the `cambiar cámara` reopen (rebind sets `pending_missing_params=["cameras"]`) — no second wizard shape needed (lock #10).
- IDLE rebind dispatch (`resolve_idle_catalog_rebind`) gained an `elif _rebind_key == "cameras":` branch calling the same offer (lock #11 — not deferred).
- `camera_suggestions: []` added to every peer-suggestion-clear dict (motor/propeller/battery/frame/kit-hardware/ESC offers, `_control_identity_peer_clear` used by FC/sensors offers) so offering any other family's list retires a pending camera pick, and vice versa (★4 cross-family rule, unchanged for every existing family).

## Mount / pose preservation (lock #14)

No new code needed: `mounted_on_declare_assist.py`'s subject table already carries a `"cameras"` entry (from `B1-mission-continuity-mount-endurance`), and `bind_camera_from_catalog(..., base=spec)` preserves `mounted_on`/`declared_box_pose` by construction (same `model_copy` merge every other bind uses) — confirmed by E4.

## USER_GUIDE_CRAFT_MONTAGE.md

Removed the "No hay `library/cameras`" callout (replaced with an accurate note pointing at §3's catalog pick). §3.1/§3.2 extended to list cameras among the catalog families, documented `ayúdame a elegir cámara`, `cambiar cámara`, and `actualiza la cámara` (new paragraph — the refresh trigger wasn't documented for any family before this pass, added generically for all catalogued families since it was simply missing, not a scope expansion of behavior).

## Tests — `tests/test_library_cameras_seed_b1.py` (new, 23 tests, all green)

T1–T8 + E1–E6 per IC §2, plus a synthetic two-row library for T6 (omit-key hygiene) and a direct `component_writers.refresh_component_from_catalog` unit test for the mass-mirror-on-refresh path. T7 additionally re-runs the FC/ESC/GPS rebind+refresh resolvers parametrized alongside cameras to confirm no cross-family regression (full-suite T7/T12 confirmed separately: `tests/test_library_fc_sensors_b1.py`, `tests/test_catalog_hygiene_mission_suggestions_b1.py`, `tests/test_geometry_esc_visor_rebind_b1.py`, `tests/test_mission_mass_energy_b1.py`, `tests/test_mission_continuity_mount_endurance_b1.py`, `tests/test_component_library.py`, `tests/test_d4_param_gatekeeper.py` — 91 tests, all green).

## Forbidden items — confirmed NOT done

No multi-SKU dump (one row only). No invented mm/g (all four numbers trace to the §0.1 cite). No bare "RunCam"→Phoenix auto-bind (`extract_camera_properties`/`CAMERA_MODEL_MAP` untouched — free-text `cámara RunCam` still resolves to `model="runcam"`, `completeness="medium"`, no `catalog_ref`, no seed dims — T3). No fold into `sensors` (separate `library/cameras/` family, separate `CameraSpec`). No Conversation Engine, no LLM, no version bump. No workspace/vigilancia mutation (★ Path D declined — default tests-only, per lock #17).

## Remaining risks / named debt

- `power_w` from the cited 200mA@5V/85mA@12V current draw is explicitly out of scope (M3, per §4 of the IC) — `source_note` carries the citation for a future Buy, never projected as a property this cycle.
- Only one SKU exists; `build_camera_catalog_suggestions`'s `limit=10` and the offer/apply plumbing are unexercised at >1 row scale beyond the synthetic T6 library (same maturity level ESC/FC/sensors had at their own first-seed cut).
- `mounted_on` for cameras was wired by a prior Buy (`B1-mission-continuity-mount-endurance`) and is exercised here only indirectly (E4 checks bind-level preservation, not a live mount-CTA flow) — no new risk introduced, just noting the boundary between the two Buys per that review's N3.
