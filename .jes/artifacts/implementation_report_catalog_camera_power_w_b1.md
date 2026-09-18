# Implementation Report — Catalog camera `power_w` from cite (`B1-catalog-camera-power-w`)

**IC:** [implementation_contract_catalog_camera_power_w_b1.md](implementation_contract_catalog_camera_power_w_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-18
**Baseline:** package `0.4.1` (unchanged, no version bump) · suite **3134 passed, 1 skipped** (≥3122 checkpoint met) · UI unaffected (no UI files touched)

---

## Cite arithmetic (lock #2, verbatim)

RunCam Phoenix 2's own `source_note` (from `B1-library-cameras-seed`) already carried, as citation-only text: `Current 200mA@5V / 85mA@12V`. Engineer-locked formula **P = I × V**:

- `200 mA @ 5 V` → `0.200 A × 5 V = 1.0 W`
- `85 mA @ 12 V` → `0.085 A × 12 V = 1.02 W` (agrees within 2%, corroborating the 5 V point rather than contradicting it)

**Locked project value: `power_w = 1.0`** (the 5 V rail point). Written as a structured JSON field on the seed row, not derived at runtime from the `source_note` string — the loader (`CameraSpec.power_w`) reads the field directly; nothing in `library.py` or `catalog_bind.py` parses `source_note` for mA/V text.

## Seed + loader

`library/cameras/_datos.json` → `runcam_phoenix_2` gained `"power_w": 1.0` and one appended `source_note` sentence recording the arithmetic and the ★ date. `CameraSpec.power_w: float | None = None` (new optional field); `_camera_from_raw` reads `data.get("power_w")` the same way every other optional numeric field on this dataclass is read.

## Bind (`src/jarvis/core/catalog_bind.py`)

`_CAMERA_CATALOG_PROJECTED_KEYS` extended with `"power_w"`. `bind_camera_from_catalog` projects `PropertyValue(value=spec.power_w, unit="W", confidence=0.9, source="declared")` whenever the row states one (Phoenix 2 today; any future powerless row simply doesn't get the key, same as `mass_g`'s own conditional).

**Preserve-manual discipline (lock #6) — generalized, not duplicated.** The mass-preservation fix from `B1-library-cameras-seed`'s own post-review pass (same-SKU refresh must never clobber a manually-declared value with the SAME `"declared"`/0.9 confidence tag) previously lived as `mass_g`-only inline logic. This Buy factored it into a named constant, `_CAMERA_MANUALLY_OVERRIDABLE_KEYS = frozenset({"mass_g", "power_w"})`, and a small loop that pops any of those keys out of `projected` when `sku_changed` is `False` and `base` already carries a non-null value for that key. `power_w` gets the exact same treatment `mass_g` already had — no new discipline invented, the existing one extended to a second field. Verified directly (`test_t5_manual_power_override_preserved_on_refresh`, `test_t5_rebind_preserves_pose_and_manual_power_together`): a manually-declared `power_w=2.0` survives both a same-SKU refresh and a same-SKU re-pick, while pose/mount survive alongside it.

## Energy mirror

- **Orchestrator pick** (`_apply_component_camera_catalog_pick`): now calls both `set_mission_component_mass` and `set_mission_component_power` after binding — projecting the bare property was never enough (lock #7), same as the mass mirror already required.
- **Refresh** (`component_writers.refresh_component_from_catalog`): the existing mission-mass re-mirror block (added post-review in the previous Buy) now also re-mirrors `power_w` → `mission_accessory_power_w` for the same `component_key in _MISSION_MASS_KEYS` branch — one shared block, two mirrors, since a refresh can change (or, per the preserve discipline above, deliberately NOT change) either field.

## Continuity (lock #8) — no new code needed

`reasoning_layer._mission_power_suggestion` (from `B1-mission-power-w`) already gates purely on property presence (`"power_w" not in (camera.get("properties") or {})`), not on provenance. Once the catalog bind projects `power_w`, that check naturally sees it as satisfied — verified by `test_t6_bound_catalog_camera_with_power_clears_cta` (no CTA when camera carries catalog power) and `test_t7_radio_power_still_cta_when_camera_power_present` (radio's own hole still surfaces, camera before radio unchanged).

## Free-text boundary (lock #9)

`extract_camera_properties`/`aerial.py`'s `ComponentRule` for cameras are untouched — `cámara RunCam` still resolves to `completeness="medium"`, no `catalog_ref`, no `power_w` (verified: `test_t4_free_text_runcam_still_no_power_w`).

## Catalog list display (additive, not locked but low-risk)

`camera_catalog_assist.py`'s `CameraSuggestion`/`camera_spec_to_suggestion`/`_format_candidate_line` extended to surface `power_w` in the numbered pick list (`"1. RunCam Phoenix 2, 19×19×19 mm, 9 g, 1 W"`), mirroring how `mass_g` was already shown. Not required by any lock, but a natural minimal consistency addition — the list already showed every other cited number.

## Regressions found and fixed

1. **`tests/test_mission_power_w_b1.py::test_never_invent_watts_from_identity_alone`** — this test, from the immediately-prior Buy (`B1-mission-power-w`), asserted `bind_camera_from_catalog("runcam_phoenix_2")` carried no `power_w` at all. That boundary is *deliberately* superseded by this Buy (the whole point is to add exactly that projection). Updated the test with an explicit "SUPERSEDED boundary" docstring note (same pattern `B1-library-fc-sensors`'s report used for its own prior-IC supersession) and changed the assertion to confirm `power_w == 1.0`. Added a new test, `test_row_without_power_w_field_still_invents_nothing`, to keep the *actual* surviving boundary covered: a camera row with no explicit JSON `power_w` field still gets nothing projected, never parsed from its own `source_note` mA text.

2. **`tests/test_bom_sku_resolved_cameras_b1.py::test_t2_bom_suffix_shows_bracket_sku_not_sin_resolver`** (a different, concurrently-landed Buy, `B1-bom-sku-resolved-cameras`, implemented directly by Cursor) — `project_closure.py`'s `_MEASURABLE` set already includes `"power_w"` (added for motors/ESCs generally, predates this Buy). A freshly-bound Phoenix 2 now carries a measurable `power_w` for the first time, so `classify_component` promotes it from `"declared"` to `"defined"` (completeness=high + measurable + no missing_fields = a strict close) — a genuine, correct behavior change: a camera with real physical mass **and** power data should read as more fully defined than one with only a box envelope. Fixed by having the test look the entry up across `defined + declarative + incomplete` rather than assuming `"declarative"` — the test's actual concern (SKU-suffix formatting) is bucket-independent; no assertion was weakened.

## Tests

- `tests/test_catalog_camera_power_w_b1.py` (new, 11 tests) — T1–T8 per IC §2, plus one extra confirming the catalog list surfaces the cited watts.
- `tests/test_mission_power_w_b1.py` — one test updated (supersession note), one test added (surviving no-field boundary).
- `tests/test_bom_sku_resolved_cameras_b1.py` — one test's bucket lookup widened (not weakened).

Full suite: **3134 passed, 1 skipped**.

## Forbidden items — confirmed NOT done

No runtime scrape of `source_note` (the loader reads a structured JSON field only — grepped: no regex over `source_note` exists anywhere in `library.py`/`catalog_bind.py`). No inventing `power_w` without the JSON field (verified by the new no-field-no-invention test). No radio catalog `power_w` (radio still has no catalog family at all — declare-only, unchanged). No VTX, no Conversation Engine, no version bump, no LLM, no claim of validated flight (the orchestrator's power-declare confirmation message already carried that disclaimer from M3, untouched here). No workspace mutation by this implementer — tests-only, per lock #12 (Path D live rebind is optional and left to the Engineer's own smoke pass).

## Remaining risks / named debt

- **Engineer smoke (§3) not run by this implementer** — per the IC's own handoff and lock #12 ("Live: default tests-only"), the live `dron-de-vigilancia-doméstico` `actualiza la cámara`/`cambiar cámara` re-pick (to pick up the new catalog `power_w` on the already-bound live project) is left for the Engineer.
- Voltage-rail auto-select (5 V vs 12 V, depending on the craft's actual rail) remains out of scope (IC §4) — the locked value is always the 5 V point regardless of what the live project's rail voltage is.
- Radio has no catalog family yet, so its own power hole stays declare-only; a future radio catalog Buy would need the same preserve-manual + mirror-on-bind/refresh discipline this Buy generalized for cameras.
