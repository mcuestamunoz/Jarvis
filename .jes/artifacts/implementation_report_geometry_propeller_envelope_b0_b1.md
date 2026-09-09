# Implementation Report — Propeller B0 honesty + B1 cited bag (`gf_5045x3` only)

**IC:** [implementation_contract_geometry_propeller_envelope_b0_b1.md](implementation_contract_geometry_propeller_envelope_b0_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2480

---

## Files changed

- `library/helices/_datos.json` — **B0**: removed the `mass_g` key from every unsourced propeller row (`gemfan_5030`, `gemfan_6040`, `dal_7040`, `apc_8x4_5`, `apc_10x4_5`, `apc_11x5_5`, `tmotor_12x4`, `tmotor_13x4_4`, `tmotor_15x5`, `tmotor_16x5_4`, `tmotor_17x5_8`, `tmotor_18x6_1`, `tmotor_22x6_7`, `tmotor_24x7_2`) — all 14 confirmed by grep before/after. `gemfan_5045_hbn`: `identity_status` → `"partially_verified"` (was `"verified"`), added `source_note` quoting the Oscar Liang thrust-test article verbatim and explicitly stating no propeller physical fact beyond diameter/pitch is known — `source_url` kept (identity-of-use evidence, not a physical ficha). `tmotor_22x6_7`: SKU key and `pitch_in` (`6.7`) left untouched; added `source_note` naming the identity debt (current T-Motor catalog lists "P22x6.6") without renaming anything. `gf_5045x3` — **B1**: added `identity_status: "verified"`, `blade_count: 3`, `material: "ABS"`, `hub_diameter_mm: 5`, `hub_thickness_mm: 9.5`, and a `source_note` quoting the re-fetched EMAX shop listing verbatim; `mass_g`/`diameter_in`/`pitch_in`/`part_number` unchanged (the primary page confirms them, does not contradict — see "Re-fetch note" below).
- `src/jarvis/knowledge/library.py` — **§3.4**: added `PropellerSpec.blade_count/material/hub_diameter_mm/hub_thickness_mm/mass_tolerance_g/shaft_bore_mm/source_note`, all `None`-default and independently optional (matching every other optional-dim field's pattern in this file). Parsed in `_propeller_from_raw` exactly like the existing optionals (`int(...)`/`float(...)`/`data.get(...)` guarded by `is not None`). `source_note` docstring states explicitly it is catalog provenance, never a Board property.
- `src/jarvis/core/catalog_bind.py` — **§3.6**: extended `bind_propeller_from_catalog` to project each new bag field as a `PropertyValue` (confidence `0.9`, `source="declared"`) when not `None` — `blade_count`/`material` with no `unit` (matching `PropertyValue.unit: str | None = None`'s default), `hub_diameter_mm`/`hub_thickness_mm`/`shaft_bore_mm` with `unit="mm"`, `mass_tolerance_g` with `unit="g"`. `source_note` is deliberately **not** projected — it stays catalog-only metadata, read directly off `PropellerSpec` if ever needed, never a `ComponentSpec.properties` key.
- `tests/test_geometry_propeller_envelope_b0_b1.py` (**new**) — T1–T9 per the IC's own table.
- `tests/test_catalog_foundation_v1.py` — renamed `test_gemfan_5045_hbn_verified_identity` → `test_gemfan_5045_hbn_partially_verified_identity`, asserting `identity_status == "partially_verified"` (the required correction the IC calls out explicitly as "not a weaken"). `test_gf_5045x3_curated_identity_and_mass` and `test_hq_5045_bn_partially_verified_identity` left unmodified — both already pass unchanged.

## Re-fetch note (`gf_5045x3`'s primary page, checked live 2026-09-09)

Re-fetched `https://shop.emaxmodel.com/collections/all/products/2-pairs-5045-3-blade-propeller-abs-cw-ccw-for-mini-quadcopter` live (not reused from the parent investigation). It states, verbatim: Material "ABS", "3" blades, "4.5 grams per prop", hub diameter "5mm", hub thickness "9.5mm", diameter "5\"", pitch "4.5\"", pack "2xCW and 2xCCW propellers (1 FULL SETS per pack)", and its own "Product Code: 0106003102" — no shaft bore/hole and no weight tolerance stated (both correctly omitted, not invented). All physical values seeded (`blade_count`, `material`, `hub_diameter_mm`, `hub_thickness_mm`) match this quote exactly, and the existing `mass_g`/`diameter_in`/`pitch_in` are confirmed, not contradicted. One discrepancy noted but **not** treated as a STOP-triggering contradiction: the page's own "Product Code" (`0106003102`) does not match the row's pre-existing `part_number` (`PMAB5045-3`), which this page does not state at all (searched for the literal string — absent). Per the IC's lock ("keep part_number PMAB5045-3 ... unless the primary page contradicts"), a *different, unstated-elsewhere* code is not the same as the page contradicting the existing number for the same physical fact — `part_number` was left as-is, and the discrepancy is documented verbatim in the row's own new `source_note` for future review rather than silently resolved either way.

## Behavior changed

- Every previously-unsourced propeller (14 rows) no longer publishes a `mass_g` — `default_library.get_propeller(...).mass_g is None` for all of them; `bind_propeller_from_catalog` correctly omits the `mass_g` property key for these SKUs (its existing `if spec.mass_g is not None:` guard required no code change — the row simply has nothing to project now). Confirmed via T9: across `list_propellers()`, exactly one propeller (`gf_5045x3`) has `mass_g is not None`.
- `gemfan_5045_hbn.identity_status` is now `"partially_verified"`, matching the same evidence-quality class already honestly labeled on `hq_5045_bn`. No physical bag field was added to this row — it still has no `mass_g`/hub/`blade_count`.
- `tmotor_22x6_7` is unchanged in every observable respect (SKU key, `pitch_in == 6.7`, no mass) except for the new `source_note` documenting its own identity debt.
- `gf_5045x3` now carries a real cited bag (`blade_count`, `material`, `hub_diameter_mm`, `hub_thickness_mm`) that `bind_propeller_from_catalog` projects onto a bound `ComponentSpec`'s `properties`, which `_fields`' existing generic property loop then shows on the Board card as plain text — verified by T4/T7, no `_fields`/`_geometry_from_spec` code change needed.
- `_geometry_from_spec` is untouched (confirmed via `git diff`, zero lines changed): a propeller with `diameter_in` + any hub field still resolves to `{"shape": "disk", "diameter_mm": ...}`, never a box or cylinder — T7 is a direct regression proof (`diameter_in=5` + `hub_thickness_mm=9.5` → disk Ø 127mm, hub shown only as an ordinary text field).
- Live demo (`autonomía-de-10min`, propellers bound to `gemfan_5045_hbn`) confirmed unchanged: still Ø 127mm disk, still no `mass_g`/hub fields — checked via a read-only Python snippet against the live `state.json` (`git status --short -- workspace/` empty).

## Tests

- `python -m pytest -q tests/test_geometry_propeller_envelope_b0_b1.py tests/test_catalog_foundation_v1.py` → **69 passed** (9 new + the full foundation file, including the renamed HBN test).
- `python -m pytest -q` (full suite) → **2489 passed**, 0 failed (baseline 2480 + 9 new). No existing test weakened — the one foundation-test change is the IC's own required correction (asserting the new, more honest `identity_status`), not a loosened assertion; every other propeller/catalog test file re-run unmodified and green.
- `git status --short -- ui/` shows only the two prior cycles' changes (Motor visor copies B1, unrelated to this IC) — this IC touched zero `ui/` files, satisfying "UI empty diff this cycle."
- Live census re-verified directly against `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` via `project_spatial_nodes_from_path` (read-only, never a test, never a mutation): propellers card unchanged.

## Non-goals honored

- No hub/mass/blade seeded on `gemfan_5045_hbn`, `hq_5045_bn`, `gemfan_5030`, `gemfan_6040`, `dal_7040`, any `apc_*`, or any other `tmotor_*` besides the identity-debt note on `tmotor_22x6_7` — confirmed by grep: none of these rows carry any of the new bag keys.
- `tmotor_22x6_7`'s SKU key and `pitch_in` (`6.7`) were not renamed/changed — confirmed by T8.
- No Lemon FPV page fetched or cited — the EMAX shop page (already the row's existing `source_url`) fully stated the locked bag fields, so no replacement source was needed and the "if EMAX and Lemon disagree, STOP" branch never triggered.
- No `diameter_mm`, nested schema, RPM, thrust_limit, temperature, POPO, `prop_type`, or rotation field added anywhere — the only new keys are exactly the seven named in §3.4.
- `_geometry_from_spec`/`Solid3D`/disk `z` untouched — confirmed via `git diff`, empty for `Solid3D.tsx`/`scene3dScale.ts`; `_geometry_from_spec` itself has zero new lines this cycle.
- No `motor_power_w` invented; fit stub not un-queued; no version bump (`pyproject.toml` still `0.3.8`).
- No live `workspace/` mutation from tests — the new test file builds synthetic fixtures (T7) and reads only `default_library`/`bind_propeller_from_catalog` (T1–T6, T8–T9), never touching `workspace/`.

## Remaining risks / notes for review

- The `gf_5045x3` part-number/product-code discrepancy noted above (`PMAB5045-3` vs. the page's own `0106003102`) is flagged in the row's `source_note` for Engineer/Cursor visibility but not resolved either direction this cycle — resolving it (confirming which code is the real manufacturer part number, or whether both legitimately coexist as shop-code vs. mfr-code) is a natural small follow-up, not blocking this Buy.
- `source_note` is intentionally not exposed on the Board card (matches Motor/Battery/ESC precedent) — an Engineer wanting to see the citation text today would need to read the catalog JSON directly; no UI surface for it exists yet, consistent with every other family's `source_note`.
