# Implementation Report — Catalog Foundation v1 (Impl A)

## Summary

`ComponentLibrary` (`knowledge/library.py`, still the single JSON reader) now also loads batteries and propellers, alongside enriched (optional) motor fields. `ComponentSpec` gained an additive, optional `catalog_ref: CatalogRef | None` identity placeholder — set by nothing in production code, exactly as locked. No calc, DSE, Continuity, or Bind-write-path behavior changed. Full suite: **1616 passed** (1591 baseline + 25 new), zero failures, zero regressions.

## Existing architecture inspected

- `knowledge/library.py` — confirmed single reader; `_load_motors`/`get_motor`/`find_motors_by_kv`/`find_motors_for_requirements` (D8) read in full before touching anything.
- `library/motores/_datos.json` — **20 SKUs, 3 `is_generic`** (correcting the audit report's earlier 18/2 count, per Cursor's review note — cosmetic, non-material).
- `schemas/action_schema.py::ComponentSpec`/`PropertyValue` — confirmed no existing identity field, `extra="ignore"` on `ComponentSpec` (safe for an additive field).
- `iterate_interactive_session.py:1390-1424` (`_handle_motor_suggestion_selection`) — reconfirmed the audit's central finding: copies `thrust_n`+`weight_g` only, discards SKU name.
- `param_definition_session.py:179-206` (`_make_motor_spec_from_catalog`) — reconfirmed Cursor's spot-check: sets `ComponentSpec.name` to the SKU name but has no `catalog_ref`/`source="catalog"` either. Neither path is touched in this cut (Impl B territory).
- `tests/test_component_library.py` — existing motor test conventions (real-library integration style, `pytest.raises(KeyError, match=...)`) — followed for the new battery/propeller tests.

## Catalog schema (Motors / Batteries / Propellers)

**`MotorSpec`** (enriched, all new fields optional with safe defaults — every existing row still loads unchanged): `manufacturer`, `model`, `max_current_a`, `voltage_min`, `voltage_max`, `compatible_prop_ids: tuple[str, ...] = ()`, `operating_points: tuple[dict, ...] = ()` (zero consumer code reads this), `source_url`.

**`BatterySpec`** (new): required `chemistry`, `energy_wh`, `mass_g` (canonical mass unit — **grams**, matching `MotorSpec.weight_g`'s convention, documented here per the contract's "pick one and document" instruction). Voltage identity: `cells` and/or `nominal_voltage` — **enforced at load time** (`_battery_from_raw` raises `ValueError` if a JSON row has neither, and if `chemistry`/`energy_wh`/`mass_g` are missing) since a frozen dataclass can't express "at least one of two fields" at the type level. Optional: `capacity_mah`, `max_continuous_current_a`, `c_rating`, `design_space`, `operating_points`.

**`PropellerSpec`** (new): required `diameter_in`, `pitch_in` (same load-time enforcement pattern). Optional: `mass_g`, `ct`, `cp`, `compatible_kv_band: tuple[int, int] | None`, `tags: tuple[str, ...] = ()`, `operating_points`.

## Canonical API

Extended the existing `ComponentLibrary` class — no second library architecture:

```
get_battery(id) / list_batteries() / has_battery(id)
get_propeller(id) / list_propellers() / has_propeller(id)
find_batteries(*, min_energy_wh=None, chemistry=None)     # plain threshold/equality filters
find_propellers(*, diameter_in=None, tolerance=1.0)        # plain distance filter
match_motor_propeller(motor_id, prop_id) -> bool
```

`match_motor_propeller` follows Design §5 exactly: (1) explicit `motor.compatible_prop_ids` membership wins outright — even overriding what `compatible_prop_inch` would otherwise suggest (verified by test, see below); (2) else `compatible_prop_inch` vs the propeller's `diameter_in` within 1.0" (the same tolerance `find_motors_for_requirements` already uses for its own reverse lookup — no new tolerance invented); (3) neither present → `False`, never fabricated `True`.

No design-space matching for batteries/propellers in Impl A (Design §2.3 explicitly allows "minimal deterministic filters"; D8-style banded matching stays motor-only, unchanged).

## `ComponentSpec.catalog_ref` (schema only — writers untouched)

```python
class CatalogRef(BaseModel):
    family: Literal["motor", "battery", "propeller"]
    sku: str

ComponentSpec.catalog_ref: CatalogRef | None = None
```

Confirmed via `grep -rn "catalog_ref" src/jarvis/` that the only two references are the schema definition itself — no writer (`component_writers.py`), no assisted-pick path (`iterate_interactive_session.py`, `param_definition_session.py`), no orchestrator code sets it. Round-trip (`model_dump()` → `model_validate()`) verified by test.

## Data seed (counts + LiPo-first note)

- **Batteries:** 10 rows, `library/baterias/_datos.json`, **chemistry: `"lipo"` for all** (Design §4.3/10 "LiPo-first"). Capacity spans 850 mAh (2S handheld-scale) to 22,000 mAh (6S heavy-lift) plus one 12S high-voltage pack, so `find_batteries`/mass ranges have real spread to exercise. Every row: real-ish `energy_wh` = `capacity_mah/1000 × cells × 3.7`, `mass_g` derived at a plausible 130–160 Wh/kg LiPo density (varied per pack, not a repeated constant — deliberately avoids just re-encoding the existing 150 Wh/kg heuristic as fake "real" data).
- **Propellers:** 14 rows, `library/helices/_datos.json`, diameters 5"–24" chosen to align with every `compatible_prop_inch` value already present across the 20 motor SKUs, so `match_motor_propeller`'s fallback path has real, non-synthetic hits to exercise (verified: `sunnysky_x2216_11` ↔ `apc_10x4_5` → `True`).
- **Motors:** unchanged rows; only new *optional* fields were added to the dataclass/loader, none to the existing JSON — the contract's "do not arbitrarily rewrite valid existing numeric rows" is satisfied by construction (nothing in `library/motores/_datos.json` was touched).

## Matching / gap behavior

- Unknown SKU (any family) → `has_*` returns `False`, `get_*` raises `KeyError` naming the unknown id and listing available options — same shape as the existing motor behavior, extended verbatim to batteries/propellers (test: `test_unknown_sku_never_fabricated`).
- `match_motor_propeller` never returns `True` without either an explicit id match or a diameter-band hit — both the explicit-wins-over-diameter case and the honest-`False` case are tested.
- D8's own `find_motors_for_requirements`/`find_motors_by_kv` behavior is unchanged (regression-tested).

## Files changed

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `MotorSpec` enrichment fields; new `BatterySpec`/`PropellerSpec`; new loaders + `get_*`/`list_*`/`has_*`/`find_*`; `match_motor_propeller`. |
| `src/jarvis/schemas/action_schema.py` | New `CatalogRef` model; `ComponentSpec.catalog_ref: CatalogRef \| None = None` (additive). |
| `library/baterias/_datos.json` (new) | 10 LiPo battery SKUs. |
| `library/helices/_datos.json` (new) | 14 propeller SKUs. |
| `tests/test_catalog_foundation_v1.py` (new) | 25 tests — see below. |

`library/motores/_datos.json` and `library/materiales/_datos.json` — **not touched**.

## Tests run

```
pytest tests/test_catalog_foundation_v1.py -v                                    → 25 passed
pytest tests/test_component_library.py tests/test_motor_component.py \
       tests/test_iterate_session.py tests/test_orchestrator.py \
       tests/test_project_closure_v1.py tests/test_design_explorer.py \
       tests/test_fn022_engineering_intent.py tests/test_fn024_handoff_context_dse.py \
       tests/test_fn025_help_goal_intent.py tests/test_fn026_lever_iterate_preseed.py \
       tests/test_catalog_foundation_v1.py -q                                     → 315 passed
pytest -q (full suite)                                                            → 1616 passed (1591 baseline + 25 new)
```

## Regression results

Zero failures, zero changed outcomes anywhere. `git status --short -- src/ library/` confirms exactly the two intended `src/` files modified and two new `library/` directories added — `library/motores/_datos.json` and `library/materiales/_datos.json` are untouched. The single-JSON-reader guard test (`test_single_json_reader_guard`) programmatically confirms no file outside `knowledge/library.py` constructs a `_datos.json` path (regex matches the actual `Path / "_datos.json"` join idiom, not prose mentions — an earlier naive substring version false-flagged two docstring/error-message mentions and was corrected before landing).

## System Map impact (proposed only — no ID allocation)

Per audit `PROPOSED-CAT-001` ("library JSON → ComponentLibrary API") — this cut is exactly that edge, generalized from motors to three families. No other `PROPOSED-CAT-*` edge is touched: `PROPOSED-CAT-002` (assist → Continuity gap) is explicitly out of scope (5A: `motor_catalog_assist` left as-is, no battery/propeller Continuity gaps); `PROPOSED-CAT-003` (assisted pick → `ComponentSpec` identity) and the mass-in-calc edges are Impl B; `PROPOSED-CAT-004` (DSE ↔ catalog) is Impl C. No IDs allocated into `CONNECTIONS.md` — left for Cursor per contract §6.

## Blast radius

| Path | Expected effect | Evidence |
|---|---|---|
| Existing motor load/D8 matching | Unchanged | `test_get_motor_exact_name_still_works`, `test_find_motors_for_requirements_still_works`, full `test_component_library.py` green |
| `motor_catalog_assist`/Continuity motor gap | Unchanged — module untouched | full orchestrator/iterate regression suite green |
| Calc/sim numeric output | Unchanged — `calculation_engine.py`/`simulation/` untouched | full suite green, no changed test expectations anywhere |
| FN-022…026 / H1–H4 | Unchanged | dedicated regression run green (`test_fn022`…`test_fn026`) |
| Existing `ComponentSpec` construction in tests | Unchanged — new field defaults to `None`, `extra="ignore"` already tolerant | full suite green, zero test file edits needed anywhere outside the new test file |
| New battery/propeller families | Load correctly, honest not-found, no fabricated matches | `test_catalog_foundation_v1.py`, all 25 tests |
| Second JSON reader | None introduced | `test_single_json_reader_guard` |

## Explicitly deferred

- **Impl B** — Bind write path (assisted pick / DEFINE_MISSING confirm → `catalog_ref` + projected properties), fixing the iterate SKU-identity discard, motor-mass-in-calc (opt-in, SKU-bound only per 2A), battery-mass-from-SKU overriding the 150 Wh/kg heuristic (per 4A), BOM/Continuity catalog-bound vs declared-only distinction, `catalog_ref` invalidation on DSE-continuous-divergence.
- **Impl C** — Catalog-aware DSE. Not started; forbidden until B is stable per Design §6.
- **Impl D** — Create→BOM / SKU BOM.
- **H5 / C-081** — untouched.
- **ESC / frame SKU catalogs** — not built.
- **Material ES/EN alias micro-fix (3A)** — untouched, tracked separately per Design §11.
- **Continuity gap redesign for battery/propeller** — untouched (5A: kept out of Impl A).
- **`motor_catalog_assist` generalization** — untouched (5A: kept as-is; battery/propeller got thin `ComponentLibrary` methods only, no sibling assist modules).

## Risks / limitations

- Battery/propeller seed data is **plausible, not manufacturer-sourced** — same limitation the audit flagged for motors (finding F6). No `source_url`/datasheet field was populated on any new seed row (field exists, unused in seed) — acceptable for Impl A's "prove architecture, not market coverage" goal (Design §10), but real sourcing is a pre-Impl-D concern worth tracking.
- The battery loader's "at least one of `cells`/`nominal_voltage`" and both loaders' "required field present" checks raise `ValueError` at load time rather than the `KeyError`-with-available-list style `get_motor`/`get_battery`/`get_propeller` use for *unknown* ids. This is deliberate — a malformed catalog row is a data-authoring bug (fail loud, fail at load), not a "not found" user-facing case (fail gracefully) — but it's a second error-handling shape in the same module worth a note for whoever writes Impl B's contract.
- `operating_points` on all three families is typed as `tuple[dict[str, Any], ...]` — permissive on purpose (Design: "no consumer code," so no schema was locked in for its internal shape yet). Impl B/C will need to define that shape for real before writing any interpolation code.
