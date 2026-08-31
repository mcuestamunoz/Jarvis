# Implementation Report — Frankenstein `.name` Clear (IC D / Micro)

**Contract:** [`implementation_contract_frankenstein_name_clear.md`](implementation_contract_frankenstein_name_clear.md)
**Implementer:** Claude Code
**Base:** `v0.3.1` (`30c9aec`) — working tree also carries IC C (G24 Viable Selection), per that IC's own report
**Status:** Complete, all slices (G24D-1 … G24D-5) implemented, full suite green (**2028 passed**, +3 new), CLI probe **5/5 PASS**.

---

## 1. Slices delivered

| Slice | File | Change |
|---|---|---|
| G24D-1 | `src/jarvis/core/catalog_bind.py` | New module-level constant `_DIVERGED_MOTOR_NAME = "motor (parámetros divergentes)"`; the motor divergence branch of `invalidate_diverged_catalog_refs` now sets `.name` to this constant in the same `model_copy` call that clears `catalog_ref`. Docstring updated to describe the new behavior. |
| G24D-2 | `tests/test_impl_d_sku_bom.py` (updated + extended), `tests/test_g24_apply_by_index.py` (updated) | 3 new tests + 2 disclosed assertion changes (§3). |
| G24D-3 | (folded into G24D-2's unit-level tests — see §3) | — |
| G24D-4 | `scripts/cli_probe_frankenstein_name_clear.py` (new) | 5/5 PASS. |
| G24D-5 | this report | — |

**Touch set matches the contract's table exactly** (`git diff --stat`): `catalog_bind.py` is the only `src/` file changed by this IC. `design_explorer.py`/`orchestrator.py` in the working tree are IC C's carried-forward diff (already reviewed under that IC's own report) — **zero additional lines in either from this IC**.

---

## 2. §2 locked semantics — implementation notes

### 2.1/2.2 Scope of the rename

Implemented exactly where the contract locks it: inside the existing motor-divergence `if` block, in the same `model_copy` call that already sets `catalog_ref: None` — no new branch, no new condition, no change to the divergence epsilon/comparison logic. Verified both directions live and in tests:

- **No divergence** → `invalidate_diverged_catalog_refs` returns the exact same `components` object (`is` check, not just equality) — `test_motor_name_unchanged_when_catalog_ref_preserved`.
- **Battery-only divergence** → the motor entry is untouched (`is` check against the original spec object) even when the battery branch fires in the same call — `test_battery_divergence_does_not_rename_motor`.

### 2.3 Identity/readiness unchanged

`catalog_ref is None`, `_bom_sku_resolved` → `sku_resolved=False`, `classify_component`/readiness verdicts, and G5's **decision** of *when* to invalidate are all untouched — confirmed by the full suite (every `engineering_readiness_*`/`requirements_closure`/`battery_catalog_bind_ux`/`closure_policy_propeller_sku`/P2-1/P2-2/G24-A/G24C test and probe green, unmodified assertions in all of those files).

### 2.4 Label string

`_DIVERGED_MOTOR_NAME = "motor (parámetros divergentes)"` — contains spaces, parentheses, and an accented character, structurally incompatible with this codebase's snake_case SKU naming convention (`sunnysky_r2305_2500`, `brotherhobby_avenger_2500`, etc.). Verified live and in `test_frankenstein_motor_name_is_never_a_real_sku`: `default_library.has_motor(_DIVERGED_MOTOR_NAME)` is `False`.

---

## 3. Disclosed assertion changes (required by contract §G24D-2/§6)

Both are the exact class of change the contract itself anticipated and pre-authorized ("existing test today encodes stale behavior... disclose in report is required").

1. **`tests/test_impl_d_sku_bom.py::test_frankenstein_entry_after_g5_divergence_is_not_resolved`** — was `assert frankenstein.name == _SKU  # .name untouched — still looks like a SKU`. Now `assert frankenstein.name != _SKU` + `assert not default_library.has_motor(frankenstein.name)`, plus a new assertion that the old SKU string doesn't appear in the rendered BOM line at all (previously only the bracketed `[sku]` form was checked). This test's own docstring explicitly described the pre-IC-D behavior as the thing being tested — updated to describe the post-IC-D honest behavior instead.

2. **`tests/test_g24_apply_by_index.py::test_bound_motor_aplica_la_mejor_clears_catalog_ref`** — a test written during IC C (this session, same arc) that also asserted `motors.name == _BOUND_SKU` in its "identity cleared" branch. **Not listed in this contract's touch table**, but its assertion directly encoded the stale-name behavior IC D exists to fix, so leaving it failing was not an option — updated to `assert motors.name != _BOUND_SKU`, disclosed here as a necessary side-effect fix rather than a contract-scoped change.

**Zero other test files required changes** — confirmed by running the full suite before and after: exactly these 2 failures appeared, both expected, both now fixed.

---

## 4. A scoping nuance found while building the probe (worth flagging, not a defect)

The CLI probe's step 4 (contract: *"estado/format_bom_lines motor line does not display the old SKU as name"*) initially checked the **entire** rendered `estado` output for the old SKU string, which failed — not because the fix is incomplete, but because Continuity's own `"• Catálogo: candidatos {sku}, ..."` evidence line (`resolve_motor_catalog_surface`, a completely separate, unrelated code path) legitimately re-suggests the same SKU as a **fresh pick candidate** for the now-diverged design space. That's correct, intentional behavior — the contract's own §5 non-goals explicitly excludes "Fixing Continuity catalog-gap suggestions (separate debt)." Narrowed the probe's step 4 to check only the motor component's own identity line (in both the direct BOM projection and the `estado`-rendered "Componentes / gaps" section), which is what the contract actually asks for. No source code change was needed for this — it was a probe-assertion-scope correction, not a fix.

---

## 5. Live verification — the investigation's own §6.1 repro, now honest

```text
Before (investigation baseline):
  catalog_ref: None
  name:        sunnysky_r2305_2500          (stale)
  BOM line:    ✓ motors: sunnysky_r2305_2500 qty=6 (high)

After (this IC):
  catalog_ref: None                          (unchanged)
  name:        motor (parámetros divergentes)
  BOM line:    ✓ motors: motor (parámetros divergentes) qty=6 (high)
  estado's own Continuity "Catálogo" line: unaffected (§4), still correctly
    lists sunnysky_r2305_2500 as a fresh catalog candidate for the (now
    higher-thrust) design space — a different, correct claim, not the
    stale-identity bug.
```

---

## 6. Tests added (3) + updated (2)

**New (`tests/test_impl_d_sku_bom.py`):**
1. `test_frankenstein_motor_name_is_never_a_real_sku`
2. `test_motor_name_unchanged_when_catalog_ref_preserved`
3. `test_battery_divergence_does_not_rename_motor`

**Updated (disclosed, §3):**
1. `test_impl_d_sku_bom.py::test_frankenstein_entry_after_g5_divergence_is_not_resolved`
2. `test_g24_apply_by_index.py::test_bound_motor_aplica_la_mejor_clears_catalog_ref`

---

## 7. Tests executed

```text
pytest tests/test_impl_d_sku_bom.py -v      → 12 passed (9 pre-existing + 3 new)
pytest tests/ (full suite)                    → 2028 passed (2025 pre-existing + 3 new)
python scripts/cli_probe_frankenstein_name_clear.py → 5/5 PASS
python scripts/cli_probe_g24_apply_by_index.py        → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_g24_viable_selection_honest_cta.py → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_p2_2_operating_point_bridge.py      → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_requirements_closure.py              → 5/5 PASS (regression, unaffected)
python scripts/cli_probe_battery_catalog_bind_ux.py            → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_closure_policy_propeller_sku.py        → 4/4 + 1 optional PASS (regression, unaffected)
```

---

## 8. `git diff --stat`

```text
src/jarvis/core/catalog_bind.py    | 22 +++++++++++--   (this IC — only src/ file)
src/jarvis/core/design_explorer.py | 54 ++++++++...      (IC C, carried forward, untouched by this IC)
src/jarvis/core/orchestrator.py    | 26 +++++++++...      (IC C, carried forward, untouched by this IC)
tests/test_g24_apply_by_index.py   | 44 ++++++++...        (IC C's new test + this IC's 1 disclosed fix)
tests/test_impl_d_sku_bom.py       | 63 +++++++++...        (this IC — 1 disclosed fix + 3 new tests)
```

`src/jarvis/core/catalog_bind.py`'s own diff (§ above, reproduced in full in this report) confirms: the divergence **conditions** (the `if` comparing `old_value`/`new_value` against `epsilon`) are byte-identical — only the `model_copy(update={...})` payload gained one additional key.

---

## 9. Gate check (contract §6)

| Criterion | Result |
|---|---|
| §6.1 repro: post-divergence `.name` honest; BOM/estado motor line no longer shows stale SKU | **PASS** |
| G5 semantics preserved: `catalog_ref` cleared same as before; `sku_resolved=False` | **PASS** |
| Existing frankenstein BOM test updated with disclosed assertion change | **PASS** — §3 (2 disclosed changes, one beyond the contract's own touch table, still disclosed) |
| Probe 5/5; full suite green | **PASS** — 2028/2028, 5/5 |
| Zero changes outside touch set | **PASS** — only `catalog_bind.py` in `src/` |
| G5 invalidate conditions unchanged | **PASS** |
| Readiness/BOM `[sku]` rules not weakened | **PASS** — `_bom_sku_resolved`/`format_bom_lines` untouched |
| Not bundled with IC C in one undifferentiated diff | **PASS** — this diff touches only `catalog_bind.py` + tests; IC C's `design_explorer.py`/`orchestrator.py` diff is separate and pre-existing in the working tree |

**Ready for Cursor review.**

---

## 10. Queue

```text
IC D PASS (pending Cursor review, may parallel IC C's own review)
  ↓
Combined checkpoint with IC C → 0.3.x version (Engineer ★6)
```

No tag created, no push, no version bump — left for Engineer.
