# Implementation Review — G21 + G22 Catalog Bind UX

**Contract:** `implementation_contract_g21_g22_catalog_bind_ux.md`  
**Report:** `implementation_report_g21_g22_catalog_bind_ux.md`  
**Reviewer:** Cursor  
**Date:** 2026-08-20  
**Verdict:** **PASS**

---

## Checklist (contract §6)

| # | Criterion | Result |
|---|---|---|
| 1 | Component wizard help-choose runs **before** `infer_components` / Brief re-show | ✅ `_handle_component_description` G21 bridge at ~2533–2552, after refuse check, before infer |
| 2 | Pick sets `catalog_ref` via `bind_motor_from_catalog` | ✅ `_apply_component_motor_catalog_pick` → `bind_motor_from_catalog` + `set_motor_component` |
| 3 | IDLE: unbound → picker; bound → no spurious picker | ✅ `_try_start_assisted_motor_help` ~1351–1372; regression test present |
| 4 | KV fallback removed from `build_motor_catalog_suggestions` | ✅ ~241–251; comment documents G22 |
| 5 | Gap + list agree on strict-empty fixture | ✅ `test_g22_*` pair |
| 6 | G9-A tests green; no Impl C work | ✅ 76 targeted + 1892 full suite; no DSE/catalog-aware changes |
| 7 | Full suite green | ✅ **1892 passed** (independent run) |

---

## Acceptance criteria (contract §4)

| # | Criterion | Result |
|---|---|---|
| 1 | `definir propulsion` → `ayúdame a elegir` → numbered list | ✅ tested + scripted probe in report |
| 2 | Pick `1` → `catalog_ref` + wizard continues | ✅ `test_g21_component_wizard_pick_sets_catalog_ref` |
| 3 | IDLE unbound freeform → picker, not `estado` | ✅ `test_g21_idle_help_choose_when_power_set_unbound_motor` |
| 4 | IDLE bound → no false re-bind | ✅ `test_g21_idle_help_choose_noop_when_catalog_ref_set` |
| 5 | Strict empty → gap/list agree | ✅ probe 2 + G22 tests |
| 6 | G9-A + new tests pass | ✅ |
| 7 | Full suite green | ✅ |

---

## Code review notes

### Strengths

- **Single bind path preserved:** Component-wizard pick reuses Impl B writers; no parallel identity logic.
- **Correct ordering:** Help-choose/pick bridge precedes `infer_components`, so `"1"` is never parsed as freeform motor text.
- **IDLE dead-end fixed precisely:** Only the `motor_power_w set + catalog_ref None` branch opens picker; bound motors still no-op.
- **G22 authority unified:** Removing KV fallback is the right fix (not softening the gap).
- **Tests are behavioral:** 7 tests cover wizard list, pick+bind+advance, IDLE paths, strict-empty parity, and G9-A Scenario B through the **new** entry path.

### Non-blocking observations (pre-existing patterns, not regressions)

1. **`pending_missing_params` not trimmed after catalog pick** — `_apply_component_motor_catalog_pick` mirrors the freeform-save tail: `still_missing` is computed from on-disk components for the follow-up message, but session still lists `"motors"` in `expected_keys`. Harmless today (next propellers input works; re-`ayúdame a elegir` could re-offer catalog while motors already bound). Same shape as freeform save; out of IC scope.

2. **No `apply_and_recalculate` after component catalog pick** — same as freeform component save in `_handle_component_description`; integration test reads readiness directly from saved state. Acceptable.

3. **`find_motors_by_kv` retained in library + iterate wizard** — contract-correct (audit callers, don't delete API).

4. **CLI probe scripted, not full interactive create→arch dialogue** — contract allows Engineer to re-run manually; scripted equivalent matches acceptance criteria.

---

## Deviations

**None.** File naming (`test_g21_g22_catalog_bind_ux.py`) is reasonable consolidation.

---

## Residual risks / follow-ups (out of scope)

- **G23:** `ayúdame a definir` bullet in Brief still advertises "repetir esta guía" — discussed with Engineer, not part of this IC.
- **Manual CLI smoke:** Full `create_project` → architecture → `definir propulsion` → bind → `estado` recommended once before Impl C IC (Engineer session).

---

## Recommendation

**Approve for commit/tag** (`checkpoint-g21-g22` or similar) when Engineer confirms. Gate for Impl C investigation is **open** pending optional manual CLI smoke.

---

**End of review.**
