# Implementation Report — G24 Viable Selection + Honest CTA (IC C / Deferred Queue)

**Contract:** [`implementation_contract_g24_viable_selection_honest_cta.md`](implementation_contract_g24_viable_selection_honest_cta.md)
**Implementer:** Claude Code
**Base:** `v0.3.1` / `checkpoint-next-engineering-block` (`30c9aec`)
**Status:** Complete, all slices (G24C-1 … G24C-6) implemented, full suite green (**2025 passed**, +12 new), CLI probe **6/6 PASS**.

---

## 1. Slices delivered

| Slice | File | Change |
|---|---|---|
| G24C-1 | `src/jarvis/core/design_explorer.py` | New `_is_catalog_native_motor_candidate()` predicate + `_finalize_viable_list()` (★3a selection algorithm, §2.2 of the contract). `explore()`'s tail now calls `_finalize_viable_list(viable)` instead of the bare `viable.sort(...); viable[:MAX_VIABLE]`. |
| G24C-2/3 | `tests/test_g24_viable_selection.py` (new) | 11 tests: 3 for the predicate, 5 for the selection algorithm (synthetic candidates), 3 for the primary gate (real `explore()`, no G24-TF). |
| G24C-4 | `tests/test_g24_apply_by_index.py` (extended) | 1 new test proving G24-A composes with G24C's real output with zero hand-built list surgery. |
| G24C-5 | `src/jarvis/core/orchestrator.py`, `scripts/cli_probe_g24_viable_selection_honest_cta.py` (new) | Honest CTA appended to the explore success message; 6/6 PASS probe. |
| G24C-6 | this report | — |

**Not touched, confirmed by `git diff --stat -- src/`:** exactly 2 files changed (`design_explorer.py`, `orchestrator.py`). `intent_resolver.py` (G24-A), `component_writers.py`, `library.py`, `calculation_engine.py`, `electrical_compatibility.py`, `catalog_bind.py` (IC D territory), `action_schema.py`/`CatalogRef`, `pyproject.toml` — all untouched.

**`_score_candidate`'s function body: zero diff**, verified two ways: (1) `git diff` on `design_explorer.py` shows every `_score_candidate` occurrence in the diff is a comment/docstring *reference*, never inside the function's own lines; (2) `grep` for `def _score_candidate` in the diff returns no match at all — the function definition itself doesn't appear in the diff.

---

## 2. §2 locked semantics — implementation notes

### 2.1 Catalog-native candidate identification

`_is_catalog_native_motor_candidate()` implements the exact predicate from contract §2.1 verbatim (`components_delta.get("motors") is not None and catalog_ref is not None and catalog_ref.family == "motor"`) as a single, reusable function — called from both `_finalize_viable_list` (selection) and `orchestrator._handle_explore`'s new CTA logic (message), so "catalog-native" has exactly one definition across both consumers, per the contract's own single-authority spirit.

### 2.2 Viable-slot reservation algorithm

Implemented exactly as specified (§2.2 steps 1-6). One correctness detail found and fixed during implementation, not in the original contract text: **membership checks use object identity (`is`), not equality (`in`/`==`)**. `ExplorationCandidate` is a pydantic `BaseModel`, whose default `__eq__` compares field values — two distinct candidate objects could in principle carry identical field values (same delta, same score, same label), and a plain `in`/`==` check could then match the wrong object, potentially producing a duplicate entry when combined with the later `is not` filter. Fixed before any test was written by using `any(c is best_catalog for c in head)` and `c is not best_catalog` consistently throughout. Documented inline in the function.

**Properties verified directly (§2.2 "must hold in tests"):**
- `_score_candidate` never called from `_finalize_viable_list` — confirmed by reading the function body: it only calls `sorted()` on the already-scored input list.
- No candidate's `.score` is mutated — `test_finalize_viable_reserves_best_catalog_when_truncated` asserts every returned candidate's `.score` equals its pre-call value via an `id()`-keyed dict, not just a value comparison.
- At most one catalog-native slot reserved — `test_finalize_viable_only_reserves_best_of_multiple_catalog_candidates` (two catalog candidates present, only the higher-scoring one survives).

### 2.3 Goal-agnostic, no special-casing

`_finalize_viable_list` takes no `goal_key` parameter at all — it operates purely on the list of already-generated, already-scored candidates. Verified live and in `test_explore_reducir_masa_stays_empty_no_catalog_candidates_generated`: `reducir_masa` (not in `_CATALOG_MOTOR_GOAL_KEYS`, zero catalog candidates ever generated) produces `viable` identical in shape to pre-G24C behavior — the helper's `if not catalog_native: return ranked[:MAX_VIABLE]` branch is a complete no-op for this case.

### 2.4 Honest CTA

Added after the existing `"Di «aplica la mejor»..."` line in `orchestrator._handle_explore` (never removed, never reordered — G24-A's own CTA regression preserved verbatim). Two conditions implemented per the contract's table:

- `#1` abstract + catalog-native present at real index `N>1` → one line naming the index and the `"aplica la N"` phrasing.
- Zero catalog-native in the final `.viable` **but** at least one was generated (i.e., it existed in `.candidates` but never became flyable, so `_finalize_viable_list` correctly had nothing to reserve) → a distinct, honest "no catalog option ranked in the top N" line.
- Goals with **zero** catalog candidates generated at all (e.g. `reducir_masa`) → neither branch fires, no message — correctly silent, since there was never a catalog dimension to that goal to be honest about.
- `#1` catalog-native → no warning (contract: optional positive note not required for PASS; not added, keeping the diff minimal).

---

## 3. Live verification — the investigation's own repro, now fixed

Re-ran the exact three-goal repro from `investigation_report_deferred_queue_post_v031.md` §5.1:

```text
Before (v0.3.1 baseline):
  aumentar_payload:    viable=5, catalog_positions=[]
  mejorar_estabilidad: viable=5, catalog_positions=[]
  reducir_masa:        viable=5, catalog_positions=[]   (0 catalog candidates ever generated — correct)

After (this IC):
  aumentar_payload:    viable=5, catalog_positions=[5]   score=2.1063 (unchanged from pre-fix computation)
  mejorar_estabilidad: viable=5, catalog_positions=[5]   score=2.1063 (unchanged)
  reducir_masa:        viable=5, catalog_positions=[]    (unchanged — no-op, exactly as required)
```

Full end-to-end turn (`"optimiza para aumentar payload"` → `"aplica la 5"`) via `handle_user_text`, zero LLM calls, zero session hand-construction:

```text
Jarvis > ... 5. motors [emax_rs2205s_2300]: power_w=400.0, thrust_n=10.042, ... → score=2.106 (+0.123)
         Di «aplica la mejor» para aplicar la configuración #1 al proyecto.
         ⚠ La configuración #1 es abstracta (sin SKU de catálogo) — aplicarla puede perder el
         motor vinculado. La opción #5 sí usa un motor de catálogo: di «aplica la 5» para
         conservarlo.

User > aplica la 5
Jarvis > Aplicando configuración #5 de «maximizar carga útil»: ...
✓ catalog_ref preserved, sku=emax_rs2205s_2300
```

---

## 4. Tests added (12)

**`tests/test_g24_viable_selection.py`** (11 new):
- `test_is_catalog_native_true_for_catalog_bound_motor`, `..._false_for_abstract`, `..._false_for_freeform_motor_delta` — predicate coverage.
- `test_finalize_viable_reserves_best_catalog_when_truncated`, `..._noop_when_catalog_already_in_top5`, `..._noop_when_no_catalog_native`, `..._only_reserves_best_of_multiple_catalog_candidates`, `..._result_length_respects_short_input` — selection algorithm, synthetic candidates.
- `test_explore_bound_motor_includes_catalog_in_viable[aumentar_payload]`, `[mejorar_estabilidad]` (parametrized) — **primary gate**, real `explore()`.
- `test_explore_reducir_masa_stays_empty_no_catalog_candidates_generated` — no-op regression.

**`tests/test_g24_apply_by_index.py`** (1 new):
- `test_apply_by_index_on_real_viable_output_no_hand_built_reorder` — G24-A + G24C compose without G24-TF (contract G24C-4).

**Zero weakened tests.** No existing assertion in either file was changed.

---

## 5. Tests executed

```text
pytest tests/test_g24_viable_selection.py -v      → 11 passed (new file)
pytest tests/test_g24_apply_by_index.py -v        → 5 passed (4 pre-existing + 1 new)
pytest tests/ (full suite)                          → 2025 passed (2013 pre-existing + 12 new)
python scripts/cli_probe_g24_viable_selection_honest_cta.py → 6/6 PASS (step 6 = full cli_probe_g24_apply_by_index.py subprocess, 6/6)
python scripts/cli_probe_g24_apply_by_index.py               → 6/6 PASS (regression, unaffected)
```

---

## 6. `git diff --stat -- src/`

```text
src/jarvis/core/design_explorer.py | 54 +++++++++++++++++++++++++++++++++++---
src/jarvis/core/orchestrator.py    | 26 +++++++++++++++++-
2 files changed, 76 insertions(+), 4 deletions(-)
```

**Confirms the contract's hardest line: `_score_candidate`'s function body has zero diff** (§1 above, verified two independent ways).

---

## 7. Scope decisions disclosed

1. **Identity vs. equality fix (§2.2)** — not in the original contract text, found during implementation, disclosed above. Strictly a correctness hardening of the locked algorithm, not a deviation from it.
2. **"Zero catalog candidates generated at all" produces no CTA line, only "generated but none flyable" does.** The contract's own table lists these as two separate conditions with two different intents (one is about truncation, the other about a total absence of the catalog dimension for that goal) — implemented as written, verified live for `reducir_masa` (silent) vs. the hypothetical "generated but unflyable" case (covered by the `elif` branch's logic, though no live seed data was found this session that naturally produces a catalog-native-but-unflyable candidate to exercise it end-to-end; the branch's correctness was verified by code inspection against the same predicate used and tested elsewhere).
3. **No positive note added when `#1` is already catalog-native** — contract marks this explicitly optional ("not required for PASS"); omitted to keep the diff minimal, matching the CLAUDE.md discipline against unrequested scope.

---

## 8. Gate check (contract §6)

| Criterion | Result |
|---|---|
| Investigation §5.1 repro fixed: `aumentar_payload`/`mejorar_estabilidad` → ≥1 catalog-native in `.viable` | **PASS** |
| `_score_candidate` zero diff | **PASS** |
| G24-A probe 6/6 unchanged; new probe 6/6 | **PASS** |
| Full suite green | **PASS** — 2025/2025 |
| CTA present when `#1` abstract + catalog at `N>1` | **PASS** |
| `"aplica la N"` preserves `catalog_ref` on real explore output without G24-TF | **PASS** |
| No `_score_candidate` change | **PASS** |
| No scores mutated to force inclusion | **PASS** — `id()`-keyed test assertion |
| No G24-A regressions | **PASS** |
| No IC D (`.name`) changes | **PASS** — `catalog_bind.py` untouched |

**Ready for Cursor review.**

---

## 9. Queue

```text
IC C PASS (pending Cursor review)
  ↓
IC D (Frankenstein .name micro) — separate contract, already drafted
  (.jes/artifacts/implementation_contract_frankenstein_name_clear.md)
  ↓
Both PASS → Engineer checkpoint + 0.3.x version (★6)
```

No tag created, no push, no version bump — all explicitly out of scope for this contract, left for Engineer.
