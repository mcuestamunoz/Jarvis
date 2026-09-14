# Implementation Report — Relocate FC + GPS envelopes into `library/` (`B1-library-fc-sensors`)

**IC:** [implementation_contract_library_fc_sensors_b1.md](implementation_contract_library_fc_sensors_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-14
**Baseline:** package `0.4.1` · suite 2892 → **2911** (19 new tests)

---

## Explicit supersession of the #4b "no `library/fc|sensors`" lock

`implementation_contract_geometry_sourced_fc_gps_b1.md`'s own original lock ("no `library/fc/`, no `library/sensors/`, no bind, no `catalog_ref`" — a deliberate free-text/Structure-style pattern chosen at the time) is **superseded** by this Buy per the Engineer's 2026-09-14 architecture-failure finding: physical catalog facts must live under repo-root `library/` with every other family, never as module-level dicts inside `src/jarvis/domains/aerial.py`. That prior IC's own test file (`test_geometry_sourced_fc_gps_b1.py`) has been updated in place with an explicit note recording this supersession rather than being silently rewritten.

## File tree + SKU census

```
library/fc/_datos.json        — pixhawk_4, speedybee_f405_v4
library/sensors/_datos.json   — holybro_m10
```

Both created fresh this cycle; `library/motores/`, `library/esc/`, etc. untouched. Dims, `source_url`, and `source_note` text are copied **verbatim** from the deleted `FLIGHT_CONTROLLER_DIMENSIONS`/`GPS_DIMENSIONS` dicts — the only structural change is the plural `source_urls` tuple (an `aerial.py`-local convention no other `library/` family uses) collapsing to the singular `source_url` convention every other catalog family already uses, with the second/corroborating URL preserved by appending it verbatim to the end of `source_note` (never dropped, never reworded). `manufacturer`/`model`/`identity_status` fields — required by the ESC-mirroring `FcSpec`/`SensorSpec` shape but absent from the original ad-hoc dicts — were added from facts already evident in the existing citations (e.g. the Holybro-branded source URLs), never a new physical claim.

## `ComponentLibrary` extensions

New `FcSpec`/`SensorSpec` frozen dataclasses (identical field shape to `EscSpec`'s own box-envelope convention: `name`, `manufacturer`, `model`, `identity_status`, `source_url`, `source_note`, `length_mm`/`width_mm`/`height_mm`), each with its own `_load_*`/`get_*`/`list_*`/`has_*` methods mirroring `_load_escs`/`get_esc`/`list_escs`/`has_esc` byte-for-byte in structure (same missing-file-returns-empty-dict fallback, same `KeyError` message shape). `ComponentLibrary.__init__` gained `self._fcs`/`self._sensors` cache slots.

## `aerial.py` after the move

`FLIGHT_CONTROLLER_DIMENSIONS` and `GPS_DIMENSIONS` are **deleted** — confirmed by `hasattr` and a full source-grep test (`test_l3_...`). `FLIGHT_CONTROLLER_MAP`/`GPS_MAP` (alias→canonical-id language maps) remain, per lock #6. `extract_flight_controller_properties`/`extract_sensor_properties` now resolve dims via `default_library.get_fc(...)`/`get_sensor(...)` (wrapped in `try/except KeyError`, mirroring the original `dict.get()` → `None` semantics exactly) instead of a local dict lookup — confirmed byte-identical output for every existing alias (Pixhawk 4, SpeedyBee F405 V4, Holybro M10, bare "m10", bare "ardupilot").

## `control_identity_catalog_assist.py` rewire

`build_flight_controller_identity_suggestions`/`build_sensor_identity_suggestions` now iterate `default_library.list_fcs()`/`list_sensors()` instead of the deleted dicts, filtering to rows with a full cited box (matching the module's own "con caja citada" header claim — a defensive addition against a future partial-data row, since every row today already has full dims). The pick-application UX (`_apply_control_identity_catalog_pick` in `orchestrator.py`, untouched) still routes through the **same free-text extractor path** — no new `catalog_ref` bind wired into this specific flow, per lock #8's explicit "declare/pick phrases stay the ones extractors already understand."

## New catalog-bind capability (additive, not wired into a new trigger)

`catalog_bind.bind_flight_controller_from_catalog`/`bind_sensor_from_catalog` (new) mirror `bind_esc_from_catalog`'s exact shape (`library=None, base=None` signature, `base` preserves `declared_box_pose`/`mounted_on` across a rebind — confirmed by `test_l7_bind_preserves_base_pose_and_mount`). `CatalogRef.family`'s `Literal` was widened to include `"flight_controller"`/`"sensors"` (a core-contract change, but one this ★'d IC explicitly specifies in lock #7 — not an unrequested schema change).

**Naming choice (lock #7, "pick one pair, document, stay consistent"):** I chose `"flight_controller"`/`"sensors"` over the shorter `"fc"`/`"sensor"` alternative, matching these two families' own existing `suggested_key`/`component_type` string (`"flight_controller"`, `"sensors"`) used everywhere else in the codebase (`mounted_on_declare_assist`'s subject table, `_STACK_SUBJECTS`, `aerial_registry`'s own `ComponentRule` definitions) — consistency with the established vocabulary won over brevity.

**These bind functions are not wired into a new orchestrator IDLE trigger this cycle.** No existing "cambiar controladora `<sku>`"/"cambiar GPS `<sku>`" rebind flow exists in this codebase today (confirmed: no such trigger phrase anywhere in `orchestrator.py`), and lock #9 explicitly forbids inventing a new acquisition architecture. Building one was outside this Buy's own literal test list (L1–L8 test the bind FUNCTIONS directly, not a new IDLE phrase) and outside "P0 architecture correction" scope — flagging this explicitly for Cursor, since lock #3's "wire writers/orchestrator pick paths as ESC already is" could be read more expansively. `catalog_refresh_assist.py`'s own stale comment ("FC has no CatalogRef.family/bind path at all") was corrected to note the bind now exists but the refresh trigger still deliberately excludes both families for the same minimal-surface reason.

## Files changed

- **`library/fc/_datos.json`**, **`library/sensors/_datos.json`** (new).
- **`src/jarvis/knowledge/library.py`** — `FcSpec`/`SensorSpec` + loaders/getters/listers.
- **`src/jarvis/domains/aerial.py`** — `FLIGHT_CONTROLLER_DIMENSIONS`/`GPS_DIMENSIONS` deleted; extractors rewired to `ComponentLibrary`; stale comments updated.
- **`src/jarvis/core/catalog_bind.py`** — `bind_flight_controller_from_catalog`/`bind_sensor_from_catalog` (new).
- **`src/jarvis/core/control_identity_catalog_assist.py`** — rewired off `aerial` dimension dicts onto `list_fcs`/`list_sensors`.
- **`src/jarvis/core/catalog_refresh_assist.py`** — comment-only correction (no behavior change).
- **`src/jarvis/schemas/action_schema.py`** — `CatalogRef.family` widened per lock #7.
- **`docs/system_map/09_state/STATE_MAP.md`** — one line corrected (the doc's own `FLIGHT_CONTROLLER_DIMENSIONS` architecture claim was now false; this system-map file documents current architecture, not dated history, so it was fixed alongside the code that made it stale).
- **`tests/test_geometry_sourced_fc_gps_b1.py`** — supersession note added; the one direct `GPS_DIMENSIONS` import/read replaced with `default_library.get_sensor(...)`.
- **`tests/test_geometry_declared_sensors_kit_envelope_b1.py`** — `test_p10_...`'s "no sensor seed ever gains dims" guard updated with a named, documented exception for `holybro_m10` (a real migrated citation, not an invention) — every OTHER sensor SKU is still guarded exactly as before.
- **`tests/test_library_fc_sensors_b1.py`** (new) — 19 tests, L1–L7 plus projector/library-file-existence regressions.

No `workspace/` mutation (Path D, the optional live-project rewrite, was **not** taken — the default "no workspace edit" per the IC's own type line). No version bump.

## Confirmation: extractors no longer own physical SoT

`test_l3_no_dimensions_dicts_in_aerial_module` (attribute check) and `test_l3_no_dimension_source_in_aerial_module_source` (full source-grep via `inspect.getsource`) both confirm zero trace of the deleted dicts anywhere in `aerial.py`'s compiled module or source text.

## Tests

Executed: `python -m pytest -q` → **2911 passed, 1 skipped** (0 failed). Ran the new file alone first (19 passed) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| L1 | `test_l1_get_fc_speedybee_and_pixhawk`, `test_l1_get_fc_unknown_raises_key_error` |
| L2 | `test_l2_get_sensor_holybro_m10` |
| L3 | `test_l3_no_dimensions_dicts_in_aerial_module`, `test_l3_no_dimension_source_in_aerial_module_source` |
| L4 | `test_l4_extract_flight_controller_speedybee_unchanged`, `test_l4_extract_flight_controller_pixhawk4_unchanged`, `test_l4_bare_unmapped_model_no_dims` |
| L5 | `test_l5_extract_sensor_holybro_m10_unchanged`, `test_l5_bare_m10_still_no_dims` |
| L6 | `test_l6_fc_suggestions_come_from_library_not_aerial_dict`, `test_l6_sensor_suggestions_come_from_library`, `test_l6_module_no_longer_imports_dimension_dicts` |
| L7 | `test_l7_bind_flight_controller_projects_catalog_ref_and_box`, `test_l7_bind_sensor_projects_catalog_ref_and_box`, `test_l7_bind_preserves_base_pose_and_mount`, `test_l7_bind_unknown_sku_raises_key_error` |
| L8 | Full suite green above; `pyproject.toml` still `0.4.1`; no `ui/` file touched this cycle (backend/catalog-only) |

Additional coverage: `test_geometry_sourced_fc_gps_b1.py`'s own T1–T5 re-verified green unchanged (proves this migration is invisible to the extractor's own pre-existing regression suite); `test_projector_emits_box_for_bound_fc_and_sensor` (a bound catalog spec still projects a `box`, same as the free-text path).

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **`10-min-autonomía`** (the IC's own §0.3 smoke target): `flight_controller` geometry `{box, 41.6, 39.4, 7.8}` (SpeedyBee F405 V4) and `sensors` geometry `{box, 50.0, 50.0, 14.4}` (Holybro M10) — **byte-identical** to pre-migration values, confirming the live cards are unaffected.
- **`autonomía-de-5min`**: `flight_controller` geometry `{box, 44.0, 84.0, 12.0}` (Pixhawk 4) — also unchanged. `sensors` geometry there is `{box, 40.0, 40.0, 12.0}`, which does **not** match any GPS_MAP/library row at all — that project's sensor box was set via the separate, unrelated `declared_envelope_declare_assist` free-text writer (`declara el sensor 40x40x12mm`), never touched by this Buy, confirming this migration didn't interfere with that orthogonal path either.

## Non-goals honored

No invented mm (every FC/sensor dimension traces to the exact same source citation as before, just relocated). No antenna fold-in (the M10's 25×25×4mm antenna disclosure in `source_note` is preserved verbatim). No bare `ublox_m10`/generic `m10` dims seeded (that row still has no `library/sensors/` entry — confirmed by `test_l5_bare_m10_still_no_dims`). No duplicate SoT left in `src/` (the dicts are deleted, not just unused). No new Conversation Engine / new acquisition architecture (the bind functions are additive plumbing, not wired to a new trigger — see the flagged note above). No version bump. No `workspace/` mutation.

## Remaining risks / notes for review

- **Bind functions not yet wired to a live IDLE trigger** (see the dedicated note above) — Cursor should confirm this reading of lock #3 is the intended minimal scope, or specify the exact trigger phrase/flow wanted if not.
- `CatalogRef.family`'s `Literal` widening touches a schema every catalog-bound `ComponentSpec` in the system already relies on — I re-ran the FULL suite (not just this Buy's own new tests) specifically to catch any place that might have exhaustively matched on the old, narrower `Literal` set; none did (0 unrelated failures).
- The `source_urls` → `source_url` + appended-note collapse is a structural change to how these two specific citations are represented (not their content) — flagged explicitly above so a future reader never mistakes the shape change for a content edit.
