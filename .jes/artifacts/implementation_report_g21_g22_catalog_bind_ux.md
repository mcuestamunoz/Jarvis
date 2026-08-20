# Implementation Report — G21 + G22 Catalog Bind UX (pre–Impl C)

**Contract:** [`implementation_contract_g21_g22_catalog_bind_ux.md`](implementation_contract_g21_g22_catalog_bind_ux.md)
**Checkpoint base:** `checkpoint-g9a` (`ea3d47d`)
**Status:** Implemented, all 3 slices, 7 new tests added, full suite green (1892). **Not committed.**

---

## Slices completed

- [x] Slice 1 (G21) — component wizard + IDLE catalog bind
- [x] Slice 2 (G22) — KV fallback removed, single strict authority
- [x] Slice 3 — integration + probe

---

## Files changed

| File | What |
|---|---|
| `src/jarvis/core/orchestrator.py` | New `_offer_component_motor_catalog` / `_apply_component_motor_catalog_pick` helpers. `_handle_component_description`: motors help-choose/pick bridge inserted right after the ★2 refuse check, before `infer_components`. `_try_start_assisted_motor_help`: the bare `motor_power_w is not None: return None` dead-end replaced with a `catalog_ref` check — bound motors still no-op (unchanged); unbound freeform motors open the same component-wizard picker. |
| `src/jarvis/core/motor_catalog_assist.py` | `build_motor_catalog_suggestions` — removed the `find_motors_by_kv` fallback block. Strict search empty now means empty everywhere (Option A / ★2). |
| `src/jarvis/core/acquisition_brief.py` | `build_acquisition_brief` — third "Puedes:" bullet for `key == "motors"` only: `"decir 'ayúdame a elegir' para ver candidatos numerados del catálogo"`. |
| `tests/test_g21_g22_catalog_bind_ux.py` | New — 7 tests: 4 for G21 (component-wizard help-choose/pick, IDLE unbound re-bind, IDLE bound no-op regression guard), 2 for G22 (strict-empty parity, direct library-level check), 1 integration (bind via the new component-wizard path clears the G9-A gap). |

No changes to `bind_motor_from_catalog`, `set_motor_component`, `invalidate_diverged_catalog_refs`, `resolve_motor_catalog_surface`'s bound-SKU logic (G9-A), `iterate_interactive_session.py`'s own `find_motors_by_kv` call (separate, unrelated acquisition path — audited, left as-is per contract's "audit callers" instruction, not "remove the function").

---

## Design notes / minor implementer choices (within contract's stated latitude)

- `_apply_component_motor_catalog_pick`'s "advance to next expected key" logic (`still_missing` check, `_set_pending_next_block()`, `_append_arch_progress_hint`) mirrors the existing freeform-save tail in `_handle_component_description` line-for-line rather than calling it directly — the freeform tail is embedded inline in a much larger method and isn't itself factored into a reusable function; duplicating this ~15-line shape was judged cheaper and safer than extracting a new shared helper out of `_handle_component_description` for this IC's scope.
- The component-wizard pick helper writes via `set_motor_component` directly (the exact writer the numeric sub-mode's `_apply_catalog_motor_pick` also calls) — confirmed no parallel identity path, per ★4/Hard rule.

---

## CLI probe (Slice 3) — automated equivalent

The contract's two-step Engineer CLI probe was run as an automated script against the real orchestrator (not a manual paste — Engineer may still want to run the interactive CLI session separately to confirm the full multi-turn `create_project` → architecture-selection → `definir propulsion` dialogue, which this script bypasses by opening the component wizard directly, the same way this test suite's existing fixtures do for R3a/R3b/G9-A).

### Probe 1 — propulsion-first bind, no false gap after

```
'ayúdame a elegir' →
Candidatos del catálogo para este espacio de diseño:
  1. sunnysky_r2305_2500  →  7.5N, 28.0g, 2500KV, ~220W
  2. emax_rs2205_2300  →  8.0N, 30.0g, 2300KV, ~250W
  3. brotherhobby_avenger_2500  →  9.5N, 32.0g, 2500KV, ~280W
  4. brotherhobby_returner_r5_2700  →  10.0N, 31.0g, 2700KV, ~260W
  5. sunnysky_x2212_980  →  11.0N, 58.0g, 980KV, ~260W

'1' →
Motor elegido: sunnysky_r2305_2500 (~220W, 7.5N).

'estado' → startup_context.motor_catalog_gap: None
```

Scenario B holds through the new bind path — matches acceptance criteria 1–2.

### Probe 2 — strict-empty gap/list parity (thrust≈6.9N/motor, kv=2400, prop=10")

```
'estado' → startup_context.motor_catalog_gap:
  "Necesitas empuje ≥ 6.9 N/motor, ~2400KV, hélice ~10\"; no tengo un motor
   en el catálogo que cubra ese espacio."

'qué motores tenemos' →
  Motores del catálogo para este espacio de diseño:
    (sin candidatos para este espacio de diseño)
```

Both non-empty/empty agree (gap present, list empty) — the exact G22 contradiction (gap-empty-but-list-populated) no longer reproduces. Matches acceptance criterion 5.

---

## Test count / suite result

```
python -m pytest tests/test_g21_g22_catalog_bind_ux.py -v   # 7 passed
python -m pytest -q                                          # 1892 passed
```

1885 baseline (post-`checkpoint-g9a`) + 7 new = 1892. Zero weakened tests.

**Regression confirmation:** `tests/test_assisted_acquisition.py`, `tests/test_catalog_bind_v1.py`, and the G9-A suite (`tests/test_engineering_readiness_gaps.py`, `tests/test_g9a_catalog_ref_gap.py`) all pass unchanged as part of the full-suite run — none relied on the removed KV fallback.

---

## Deviations from the contract

None. All fix locations, decisions (★1–★6), and test names from the contract were implemented as specified, with one naming consolidation: G21 and G22 tests live in a single file `tests/test_g21_g22_catalog_bind_ux.py` (contract suggested `test_g21_catalog_bind_ux.py` for Slice 1 and didn't name a Slice 2 file) — kept together since both slices are one IC, one session, same root area, matching this repo's existing convention of one test file per IC (R3a/R3b/G9-A precedent).
