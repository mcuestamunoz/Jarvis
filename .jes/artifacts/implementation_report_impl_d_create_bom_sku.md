# Implementation Report — Impl D Create → BOM / SKU BOM

**Contract:** [`implementation_contract_impl_d_create_bom_sku.md`](implementation_contract_impl_d_create_bom_sku.md)
**Checkpoint base:** `checkpoint-impl-c` (`c99fec6`)
**Status:** Implemented — D1, D2, D3, and D4 (★6 gate passed — presentation-local). 6 new tests + CLI probe (4/4), full suite green (1923 passed). **Not committed.**

---

## 1. Files changed

| File | What |
|---|---|
| `src/jarvis/core/project_closure.py` | D1: three new private helpers (`_bom_catalog_ref_dict`, `_bom_sku_resolved`, `_bom_quantity`); `_entry()` (inside `build_component_bom`) gains `catalog_ref`/`sku_resolved`/`quantity` — all additive, existing keys unchanged. D2: two new private helpers (`_bom_identity_suffix`, `_bom_quantity_suffix`); `format_bom_lines` uses them to append `[sku]`/`(SKU sin resolver)`/`qty=N` when applicable — unchanged output shape when no catalog identity exists. |
| `src/jarvis/adapters/cli/main.py` | D4: one boolean condition in `render_startup_context` — `if bom_lines and not continuity.get("evidence")` → `if bom_lines`. Presentation-only; no other line touched. `req_lines`'s sibling gate deliberately left as-is. |
| `tests/test_impl_d_sku_bom.py` | New — 6 tests (contract §4.1's full list). |
| `scripts/cli_probe_impl_d_sku_bom.py` | New — CLI probe, 4/4 PASS. |

No changes to `project_continuity.py`, `catalog_bind.py`, `engineering_readiness.py`, `component_writers.py`, or any G5/G9-A surface. Confirmed via `git diff --stat -- src/`: only the two files above.

---

## 2. Behavior changed (and explicitly what did not)

**Changed:**
- `build_component_bom`'s entries (in `defined`/`incomplete`/`declarative` buckets — `missing` stays a bare key list, unchanged) now carry `catalog_ref`, `sku_resolved`, `quantity`.
- `format_bom_lines` shows `[sku]` only when `sku_resolved` is `True`, `(SKU sin resolver)` when `catalog_ref` is set but unresolved (Scenario C), nothing extra when `catalog_ref is None` (Scenarios A/D) — and `qty=N` when a quantity is known.
- CLI `estado`'s "Componentes / gaps:" section now renders whenever there are BOM lines, regardless of whether Continuity has evidence text queued.

**Explicitly unchanged (verified, not merely assumed):**
- BOM bucket routing (`defined`/`incomplete`/`missing`/`declarative`) — untouched, still driven entirely by `classify_component`.
- `GAP-BOM-MISSING-COMPONENT` / `GAP-BOM-INCOMPLETE-COMPONENT` generation — both gap functions read only bucket membership (`bom["missing"]`/`bom["incomplete"]`), never the new fields; confirmed by `test_gap_bom_missing_and_incomplete_unaffected_by_new_fields`.
- No new gap type exists anywhere in `engineering_readiness.py` — confirmed by grep and by the probe's own explicit assertion (`"GAP-BOM-SKU-UNRESOLVED" not in gap_types`).
- `_bom_evidence`'s existing `catalog_bound` field and `_derive_subsystem_verdict` — zero lines touched; ASSEMBLY_READY logic identical.
- `project_continuity.py` — zero lines touched; `next_useful_step` ranking, `evidence` list construction, and the sibling `req_lines` suppression gate in `main.py` are all byte-identical to before.
- `catalog_bind.py` / G5 invalidate-then-sync order — zero lines touched. `invalidate_diverged_catalog_refs` still clears `catalog_ref` without touching `.name` — Impl D does not "fix" that at the source; it makes the *display* honest instead, exactly as scoped.

---

## 3. ★1–★6 — how implemented / D4 shipped or STOP'd

- **★1 (Option A, no parallel authority):** implemented exactly — all new logic lives inside the existing `build_component_bom`/`format_bom_lines` pair in `project_closure.py`. No `build_sku_bom` or any second function was created.
- **★2 (motors + battery, family-agnostic schema):** implemented — `_bom_sku_resolved` branches on `catalog_ref["family"]` (`"motor"` → `has_motor`, `"battery"` → `has_battery`, anything else → `False`). The schema itself (`catalog_ref`/`sku_resolved`/`quantity` on every entry) is identical for every key; propeller/ESC/frame/FC entries simply always get `catalog_ref=None`, `sku_resolved=False` today because no bind path ever sets `catalog_ref` on them — no special-casing needed, no family allowlist to maintain.
- **★3 (Create-handoff deferred):** `project_continuity.py` untouched, confirmed by `git diff --stat`.
- **★4 (no new gap type):** confirmed — no new `Gap`/gap-type constant added anywhere; probe and test both assert `"GAP-BOM-SKU-UNRESOLVED" not in gap_types`.
- **★5 (`catalog_bound` disconnected):** `engineering_readiness.py` untouched, confirmed by `git diff --stat`.
- **★6 (D4 conditional):** **shipped.** The change is a single boolean condition inside `render_startup_context`, touching no Continuity file, no ranking, no evidence-block construction. Verified it stays presentation-local: the diff is 4 lines (1 code line + 3 comment lines) in one CLI-adapter function. No STOP was needed.

---

## 4. Tests added + commands run + results

`tests/test_impl_d_sku_bom.py` — 6 tests, matching contract §4.1 exactly:

1. `test_bound_motor_entry_has_resolved_catalog_ref_and_quantity` — real `bind_motor_from_catalog` output → `catalog_ref`, `sku_resolved=True`, `quantity=6`, formatted line contains `[sku]` and `qty=6`.
2. `test_unbound_freeform_motor_entry_has_no_catalog_identity` — freeform `ComponentSpec` → `catalog_ref=None`, `sku_resolved=False`, no bracket in the formatted line.
3. `test_frankenstein_entry_after_g5_divergence_is_not_resolved` — real orchestrator project, real `bind_motor_from_catalog` + `set_motor_component`, real `catalog_bind.invalidate_diverged_catalog_refs` (the actual G5 function, not a mock) → confirms `.name` stays the old SKU string while `catalog_ref` clears, and the BOM entry/formatted line never presents it as resolved.
4. `test_architecture_complete_bound_motor_still_bom_pass_no_new_gap_type` — full 6-key architecture (motors bound + propellers/esc/battery/frame/flight_controller/sensors declared) → `bom["missing"] == []`, `bom["incomplete"] == []`, motors entry `sku_resolved=True`, and `build_engineering_readiness` produces no new gap type and no `GAP-BOM-*` gaps (architecture genuinely complete).
5. `test_gap_bom_missing_and_incomplete_unaffected_by_new_fields` — direct call to `_bom_missing_gaps`/`_bom_incomplete_gaps` on a bucket set that includes the new fields → gap objects unaffected; only the bucket-entry dicts (not the gaps) carry `catalog_ref`/`sku_resolved`.
6. `test_battery_catalog_ref_entry_shape_matches_motors_pattern` — `bind_battery_from_catalog` (Impl C's test-only path, no live acquisition UX, per ★2) against a real library battery SKU → identical entry shape to motors, `sku_resolved` via `has_battery`.

```
python -m pytest tests/test_impl_d_sku_bom.py -v
# 6 passed

python -m pytest tests/test_impl_d_sku_bom.py tests/test_project_closure_v1.py \
  tests/test_fn020_completeness_coherence.py tests/test_project_coherence.py \
  tests/test_erf2_architecture.py tests/test_engineering_readiness_continuity.py -v
# 52 passed (contract §4.2's named regression suites, zero modified assertions)

python -m pytest -q
# 1923 passed
```

1917 baseline (post-`checkpoint-impl-c`) + 6 new = 1923. Zero weakened tests — no existing assertion was loosened, removed, or needed updating (every named regression file passed byte-for-byte unchanged, since all Impl D fields are additive and no existing test pins the exact `format_bom_lines` string for a catalog-bound entry).

---

## 5. CLI probe result

`scripts/cli_probe_impl_d_sku_bom.py` — 4/4 PASS:

1. Bind `sunnysky_r2305_2500` via the real component-wizard "ayúdame a elegir" → pick `1` flow (G21, unmodified).
2. With an autonomy constraint set (so `energy_model_honesty_note` fires → Continuity `evidence` is non-empty — the exact pre-D4 suppression trigger): `estado`'s BOM line reads `[sunnysky_r2305_2500] qty=6`, **and** `render_startup_context`'s output actually contains "Componentes / gaps:" — proving D4 closes the visibility gap the investigation flagged.
3. Force a real G5 divergence via `catalog_bind.invalidate_diverged_catalog_refs` (not a mock) → `catalog_ref` clears, `.name` stays `"sunnysky_r2305_2500"` → the next `estado`'s motor line reads `✓ motors: sunnysky_r2305_2500 qty=6 (high)` — **no `[sunnysky_r2305_2500]` bracket** despite the name looking identical to the resolved case. This is the concrete, end-to-end proof of Scenario D honesty.
4. `build_engineering_readiness` on the diverged state confirms `"GAP-BOM-SKU-UNRESOLVED"` was never introduced (★4).

---

## 6. Remaining risks / deferred

- **Create-handoff (sense B, ★3):** still not implemented, as ratified. No Continuity CTA exists for "architecture complete, SKU unresolved."
- **`req_lines`'s sibling suppression gate** (`if req_lines and not continuity.get("evidence")` in `render_startup_context`, immediately above the BOM gate this IC fixed): deliberately left untouched per §5.2 of the contract — same class of bug, explicitly out of ★6's scope. Flagged again here for visibility.
- **`catalog_bound` → ERF verdict wiring (★5):** the existing `_bom_evidence`/`_propulsion_evidence`/etc. `catalog_bound` field remains write-only (computed, never read by verdict derivation). A project can still be `ASSEMBLY_READY` with zero SKUs resolved — unchanged from before this IC, by design (★5).
- **Scenario C re-validation cost:** `_bom_sku_resolved` calls `default_library.has_motor`/`has_battery` on every `build_component_bom` call for every catalog-bound entry — an in-memory dict lookup against the already-loaded library (no I/O per call after first load), consistent with every other live-re-check pattern this codebase already uses (G9-A's own `resolve_motor_catalog_surface` does the same). No new performance concern identified.
