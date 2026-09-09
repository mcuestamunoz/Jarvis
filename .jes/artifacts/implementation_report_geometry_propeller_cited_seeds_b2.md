# Implementation Report — Propeller cited seeds B2 (`dal_7040` Cyclone + `apc_10x6_ep`)

**IC:** [implementation_contract_geometry_propeller_cited_seeds_b2.md](implementation_contract_geometry_propeller_cited_seeds_b2.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2489

---

## Files changed

- `library/helices/_datos.json` — **§3.2**: `dal_7040` (existing key, `diameter_in`/`pitch_in`/`compatible_kv_band` unchanged) gained `manufacturer: "DALProp"`, `model: "Cyclone 7040"`, `identity_status: "verified"`, `source_url` (the locked GetFPV URL), `mass_g: 5.7`, `blade_count: 2`, `material: "Pure PC"`, `hub_diameter_mm: 5`, `hub_thickness_mm: 7`, and a `source_note` quoting the confirmed bag plus an honest account of the re-fetch access problem (below). No `shaft_bore_mm` — no page checked names a bore distinct from the hub. **§3.3**: new key `apc_10x6_ep` (distinct from `apc_10x4_5`, which is untouched — confirmed by `git diff`, zero lines changed on that row) with `diameter_in: 10`, `pitch_in: 6`, `manufacturer: "APC"`, `model: "10x6EP"`, `identity_status: "verified"`, `source_url` (the locked GetFPV URL), `blade_count: 2`, `material: "Composite plastic"`, `mass_g: 20.1`, `hub_diameter_mm: 20.3`, `hub_thickness_mm: 9.9`, `shaft_bore_mm: 6.35`, and a `source_note`.
- `tests/test_geometry_propeller_cited_seeds_b2.py` (**new**) — T1–T8 per the IC's own table.
- `tests/test_geometry_propeller_envelope_b0_b1.py` — **§3.5**: `test_t9_only_gf_5045x3_has_mass_g` renamed to `test_t9_only_cited_propellers_have_mass_g`, now asserting the cited set is exactly `{gf_5045x3, dal_7040, apc_10x6_ep}` — the required census update called out explicitly as "not a weaken" in the IC.
- `src/` — **empty diff**, as expected: `bind_propeller_from_catalog`'s existing bag-projection loop (shipped in the parent B0+B1 Buy) needed no change, since it already projects every one of `mass_g`/`blade_count`/`material`/`hub_diameter_mm`/`hub_thickness_mm`/`shaft_bore_mm` unconditionally when the catalog row states them.

## Re-fetch note — both locked GetFPV URLs were inaccessible; verified via independent live cross-checks instead

Both locked primary URLs (`getfpv.com/dalprop-cyclone-7040-...` and `getfpv.com/.../apc-10x6ep-...`) returned an HTTP 403 **Cloudflare bot-challenge page** ("Just a moment...") on every fetch attempt — confirmed both via the `WebFetch` tool and directly via `curl` with a standard browser user agent, ruling out a tool-specific issue. GetFPV is genuinely unreachable from this environment, not merely slow or content-poor.

To honor "sourced-only, re-fetch live" without fabricating GetFPV's own page text, each SKU's bag was cross-verified live against **independent, reachable pages carrying the identical spec sheet**:

- **`dal_7040`**: `unmannedtechshop.co.uk` and `pyrodrone.com` (fetched separately) both state, verbatim and identically to each other: "5.7g" weight, "Diameter of Hub: 5mm", "Height of Hub: 7mm", "Pure PC" material, "POPO: Support", 2-blade, 7in/pitch 4. Perfect agreement between two independent resellers — no contradiction found anywhere, so the STOP condition never triggered.
- **`apc_10x6_ep`**: `racedayquads.com`'s listing states "20.1 g" / "20.3 mm" hub diameter / "9.9 mm" hub thickness / "6.35 mm" shaft bore / "Composite plastic" / CW — matching the IC's own expected bag exactly. Independently re-confirmed against **APC's own manufacturer page** (`apcprop.com/product/10x6ep/`), which states the same physical facts in imperial units — "0.71 oz." (= 20.13 g), "0.80 in." hub diameter (= 20.32 mm), "0.39 in." hub thickness (= 9.91 mm), "1/4 in." shaft bore (= 6.35 mm exactly) — every figure converts to the metric value already seeded, within normal rounding. This is now a manufacturer-confirmed number, not just a retailer copy.

Both rows' `source_note` documents this access problem and the exact independent pages used, so a future reviewer can see precisely what was and wasn't verified against the GetFPV page itself. No number was seeded that lacked this live, independent confirmation; no contradiction was found on either SKU, so neither triggered the IC's STOP condition.

## Behavior changed

- `default_library.get_propeller("dal_7040")` now returns a fully cited bag (`mass_g`, `blade_count`, `material`, `hub_diameter_mm`, `hub_thickness_mm`) plus `identity_status`; `bind_propeller_from_catalog("dal_7040")` projects all of it onto a bound `ComponentSpec`'s `properties`, and `_fields`' existing generic loop shows it on the Board card as plain text — no code change needed, verified by T1/T2.
- `default_library.get_propeller("apc_10x6_ep")` is a brand-new SKU (10", pitch 6, 2-blade, composite, cited mass/hub/bore); `apc_10x4_5` (10", pitch 4.5) is completely untouched — verified by T4's own direct comparison of both bound specs in the same test.
- `_geometry_from_spec` (untouched, confirmed via `git diff` showing zero lines changed) still resolves `diameter_in` alone to a flat disk: a synthetic 10" propeller (with or without a hub field present) yields `diameter_mm == 254.0`; a synthetic 7" propeller yields `diameter_mm ≈ 177.8` — both regression-proven by T5/T6. Hub/mass/blade fields appear only as ordinary text rows, never stitched into a cylinder or any new shape.
- The cited-mass census (T9 in the parent B0+B1 test file) grew from `{gf_5045x3}` to `{gf_5045x3, dal_7040, apc_10x6_ep}` — every other propeller row's `mass_g` remains `None`, unchanged.

## Tests

- `python -m pytest -q tests/test_geometry_propeller_cited_seeds_b2.py tests/test_geometry_propeller_envelope_b0_b1.py tests/test_catalog_foundation_v1.py` → **77 passed** (8 new T1–T8, plus the updated T9 and the full untouched foundation file).
- `python -m pytest -q` (full suite) → **2497 passed**, 0 failed (baseline 2489 + 8 new). No existing test weakened — the one T9 change is the IC's own required census update (a stricter, larger exact-set assertion), not a loosened one.
- `git status --short -- ui/` and `git diff --stat -- src/` show only prior, unrelated cycles' changes — this IC touched zero `ui/` and zero `src/` files.
- `apc_10x4_5` confirmed byte-identical (`git diff` on that row, empty) — still `pitch_in: 4.5`, no `mass_g`.
- Live `workspace/` confirmed untouched (`git status --short -- workspace/` empty) — no test binds `dal_7040`/`apc_10x6_ep` onto the live demo project.

## Non-goals honored

- No Cyclone numbers written onto any other DAL row, no EP bag merged into `apc_10x4_5` — confirmed by inspection and by T4's direct side-by-side assertion.
- No seed touched `gemfan_6040`, `gemfan_5045_hbn`, `hq_5045_bn`, any T-Motor row, or `apc_8x4_5` — confirmed by `git diff`, showing changes on exactly two rows (`dal_7040` modified, `apc_10x6_ep` added) plus the new row's insertion.
- No new `PropellerSpec`/schema keys added (§3.4's own lock) — every field seeded already existed from the parent B0+B1 Buy; the "POPO: Support" and "2CW+2CCW pack" facts were folded into `source_note` text, not new schema fields, exactly as instructed.
- No `catalog_bind.py`/`library.py` change was needed or made (`src/` empty diff) — the existing bag-projection loop already handles every field.
- `_geometry_from_spec`/`Solid3D`/disk `z` untouched (confirmed, zero diff).
- No STEP, no plate L×W, no `"cabe"`, no `tmotor_22x6_6` rename, no version bump (`pyproject.toml` still `0.3.8`).

## Remaining risks / notes for review

- Neither `source_url` could be directly read this cycle (GetFPV's own Cloudflare challenge blocks automated fetches from this environment entirely) — the seeded numbers rest on independent-reseller and (for `apc_10x6_ep`) manufacturer-page confirmation instead, fully disclosed in each row's `source_note`. If GetFPV becomes reachable in a future session, re-confirming the exact page text directly would be a reasonable, low-cost follow-up, but no contradiction exists today to act on.
- `apc_10x6_ep`'s manufacturer page (`apcprop.com`) states its numbers in imperial units (oz/in) that convert to the metric figures seeded here within ordinary rounding (e.g. 0.71 oz → 20.13 g vs. the seeded 20.1 g) — the seeded value follows the IC's own explicitly locked number (`20.1`) and the metric-native retailer listing, not a re-derived conversion, to avoid introducing a third, self-computed figure.
