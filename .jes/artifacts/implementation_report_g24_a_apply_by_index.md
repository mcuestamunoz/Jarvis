# Implementation Report — G24-A DSE Apply By Index (IC 1 / Next Engineering Block)

**Contract:** [`implementation_contract_g24_a_apply_by_index.md`](implementation_contract_g24_a_apply_by_index.md)
**Implementer:** Claude Code
**Base:** `checkpoint-closure-policy` / doc hygiene `73bd9fa`
**Status:** Complete, all slices (G24-1 … G24-6) implemented, full suite green (**2001 passed**, +25 new), CLI probe **6/6 PASS**.

---

## 1. Slices delivered

| Slice | File | Change |
|---|---|---|
| G24-1 | `src/jarvis/core/intent_resolver.py` | New `IntentResolver.resolve_apply_exploration_index(user_input) -> int \| None` — extracts a 1-based index from an apply phrase, or `None` for unqualified apply. |
| G24-2 | `src/jarvis/core/orchestrator.py` | `_handle_apply_exploration(self, *, index: int = 1)` — bounds-checked `viable[index - 1]`; apply-branch call site passes `resolve_apply_exploration_index(...) or 1`; success message/return dict note the applied index. |
| G24-3/4 | `tests/test_g24_apply_by_index.py` (new), `tests/test_design_explorer.py` (extended) | 25 new tests (4 + 21). |
| G24-5 | `scripts/cli_probe_g24_apply_by_index.py` (new) | 6/6 PASS, real production wiring, no LLM. |
| G24-6 | this report | — |

**Not touched, confirmed by `git diff --stat`:** `design_explorer.py` (zero diff — the contract's hardest constraint), `catalog_bind.py`, `component_writers.py`, `library.py`, `engineering_readiness.py`, `electrical_compatibility.py`, `action_schema.py`, `pyproject.toml`.

---

## 2. §2 locked semantics — implementation notes

### 2.1 Indexing

`resolve_apply_exploration_index` returns 1-based indices or `None`; the orchestrator call site defaults `None` to `1` (`... or 1`), and `_handle_apply_exploration` converts to the internal 0-based `viable[index - 1]`. Confirmed unchanged for every pre-existing unqualified call site (`grep` found 12 call sites across 6 test files, all calling `_handle_apply_exploration()` with no arguments — the new `index: int = 1` keyword-only default makes every one of them byte-identical to before).

### 2.2 Recognized phrases

Implemented via one regex (`_APPLY_INDEX_RE`) plus a small ordinal map, covering every pattern class in the contract's table (`"aplica la N"`, `"aplica #N"`, `"aplica el N"`, `"aplica la opción N"`, `"aplica la quinta"`), live-verified against all listed examples plus the two negative cases (`"aplica la mejor"`, `"aplica la optima"` → `None`). **Important pre-existing fact confirmed before writing any code:** `APPLY_PATTERNS`'s first pattern (`r"\bapl(?:ica|icar)\b"`) already matches any input containing "aplica"/"aplicar" as a whole word — so `"aplica la 5"` already resolves to intent `"apply_exploration_result"` on `73bd9fa`, unmodified. G24-1 therefore did **not** touch `APPLY_PATTERNS` or `resolve_intent` at all — it only adds the separate index-extraction step, exactly matching the contract's "wire into apply path" instruction without needing new intent-matching patterns.

### 2.3 Bounds and errors

Implemented the contract's recommended choice explicitly: **index < 1 or unparseable → treated as unqualified (falls back to default 1)**, resolved entirely inside `resolve_apply_exploration_index` (e.g. `"aplica #0"` → `None` → caller defaults to `1`). **Index > `len(viable)` → error, no state mutation** — implemented as an orchestrator-level bounds check (`_handle_apply_exploration`) since only the orchestrator knows `len(exploration.viable)`; the intent resolver has no access to it. Verified no state mutation on out-of-range: both a mock-based unit test and a real-orchestrator integration test assert `current_parameters`/`components` are unchanged after `"aplica la 99"`.

### 2.4 Regression locks

- `_score_candidate` / `EXPLORATION_GRIDS` / `explore()`: **zero diff**, confirmed by `git diff --stat` showing no `design_explorer.py` entry at all.
- `"aplica la mejor"` → `viable[0]`: confirmed byte-identical via `test_default_index_applies_viable_zero` (mock-level) and the CLI probe's step 5 (real turn).
- G5 `invalidate_diverged_catalog_refs` on an abstract apply: confirmed **still fires** exactly as before — `test_bound_motor_aplica_la_mejor_clears_catalog_ref` and probe step 5 both show `"aplica la mejor"` on an abstract `#1` still clearing `catalog_ref`, which is the **documented, unfixed** G5 behavior this IC deliberately leaves alone.
- Component-driven apply (`apply_components_delta`) path: untouched — `best = exploration.viable[index - 1]` is the only line that changed upstream of the existing `if best.components_delta:` branch, which is otherwise byte-identical.

---

## 3. Live verification — the exact bug from the investigation, now fixable

Reproduced the G24 scenario from the investigation report (§4.2) once more, then applied the fix:

```text
Setup: brotherhobby_avenger_2500 catalog-bound, thrust already declared.
"optimiza para aumentar payload" -> 5 abstract candidates in viable[0..4],
                                     no catalog candidate ranks into the top 5
                                     (consistent with the investigation's own
                                     finding that ranking can exclude catalog
                                     rows entirely when thrust is declared).

G24-TF: a real, unmodified catalog candidate (sunnysky_r2305_2500) — already
generated by Impl C's Strategy 3, never re-scored — placed at viable index 5
(1-based), viable[0] stays a genuine abstract candidate from the same
exploration.

"aplica la 5"  -> status=ok, applied_index=5
                  catalog_ref = {family: motor, sku: sunnysky_r2305_2500}
                  -- preserved, exactly the capability this IC adds.

"aplica la mejor" on a fresh exploration -> status=ok, applied_index=1
                  catalog_ref cleared (G5) -- unchanged, as designed.

"aplica la 99" -> status=error, "No hay una configuración #99. Elige un
                  número entre 1 y 5, o di «aplica la mejor»." -- no state
                  mutation.
```

---

## 4. Tests added (25)

**`tests/test_design_explorer.py`** (21 new, extending existing classes per the contract's preference):
- `TestApplyExplorationIndex` (new class, 11 tests): parametrized coverage of every indexed phrase class + every unqualified/non-positive case + an intent-classification sanity check.
- `TestHandleApplyExploration` (extended, 3 new tests): default-index-applies-viable-zero, out-of-range-no-mutation, index-zero/negative-no-mutation — all at the existing mock-stub level this class already uses.

**`tests/test_g24_apply_by_index.py`** (4 new, real orchestrator, no LLM):
1. `test_apply_by_index_preserves_catalog_ref_when_catalog_not_at_one` — **the primary gate**, G24-TF fixture, real `explore()`, real `handle_user_text("aplica la N", ...)`.
2. `test_hash_index_phrasing_also_works` — `"aplica #N"` end-to-end.
3. `test_bound_motor_aplica_la_mejor_clears_catalog_ref` — regression documentation (G5 unchanged).
4. `test_apply_index_out_of_range_via_real_turn_errors_no_mutation` — real-turn version of the bounds check.

**Zero weakened tests.** No existing test file assertion was modified — `test_design_explorer.py` and no other pre-existing file had any line changed, only new test classes/methods appended.

---

## 5. Tests executed

```text
pytest tests/test_design_explorer.py -v          → 83 passed (62 pre-existing + 21 new)
pytest tests/test_g24_apply_by_index.py -v       → 4 passed (new file)
pytest tests/ (full suite)                        → 2001 passed (1976 pre-existing + 25 new)
python scripts/cli_probe_g24_apply_by_index.py    → 6/6 PASS
```

---

## 6. `git diff --stat`

```text
src/jarvis/core/intent_resolver.py |  52 +++++++++++++++++++++
src/jarvis/core/orchestrator.py    |  44 +++++++++++++----
tests/test_design_explorer.py      |  83 +++++++++++++++++++++++++++++++
3 files changed (+ 1 new test file, + 1 new probe script)
```

**Confirms the contract's hardest acceptance line: zero `design_explorer.py` diff.**

---

## 7. Scope decisions disclosed

1. **Index-zero/negative treated as "unqualified," not a distinct error** — per §2.3's explicit "pick one" instruction. Documented in `resolve_apply_exploration_index`'s own docstring and covered by `test_unqualified_or_nonpositive_apply_returns_none`. A defense-in-depth orchestrator-level test (`test_apply_index_zero_or_negative_returns_error_no_mutation`) also confirms that if index `0` ever reached `_handle_apply_exploration` directly (bypassing the resolver, e.g. a future caller bug), the bounds check there still refuses cleanly — the resolver's own choice doesn't weaken the orchestrator's independent guard.
2. **`applied_index` added to the result dict** — small, additive field (not in the contract's explicit spec) used by the new tests/probe to assert which row was applied without parsing the message string. Does not change any existing consumer's behavior (an additive dict key).
3. **Success message minimally branches on `index == 1`** — `"Aplicando mejor configuración..."` (byte-identical to before) vs. `"Aplicando configuración #{index}..."` for any other index. No other copy/CTA text touched, per §2.4's explicit "out of scope: Explore result copy... do not redesign CTA text in this IC."
4. **G24-TF construction detail:** per contract, the fixture must place the catalog candidate at index > 1 "without touching `_score_candidate` or mutating scores." Implemented by taking `exploration.candidates` (already scored by the real `explore()` call) and appending the chosen catalog candidate to a truncated slice of the real `exploration.viable` list — every score value in the resulting list is exactly what `explore()` computed; only list *membership/order* was constructed by the test, never a score.

---

## 8. Gate check (contract §6)

| Criterion | Result |
|---|---|
| `"aplica la N"`/`"aplica #N"` applies that exact row for N in 1..len(viable) | **PASS** |
| `"aplica la mejor"` and all existing unqualified phrases still select `viable[0]` | **PASS** |
| Out-of-range index → error, no state corruption | **PASS** |
| G24-TF gate test: catalog row at index 5 applied → `catalog_ref` preserved | **PASS** |
| G24 regression: `"aplica la mejor"` on abstract `#1` still clears `catalog_ref` (G5) | **PASS** |
| Full suite green; probe 6/6 | **PASS** — 2001/2001, 6/6 |
| `git diff` confirms zero `design_explorer.py` scoring/generation changes | **PASS** |
| No weakened tests without disclosure | **PASS** — zero existing assertions modified |

**Ready for Cursor review.**

---

## 9. Queue

```text
IC 1 (G24-A) PASS (pending Cursor review)
  ↓
Engineer optional checkpoint (checkpoint-g24-apply-by-index)
  ↓
Engineer semantics lock for P2-2 (motor_power_w vs resolved OP power — investigation review Note 3)
  ↓
Cursor: implementation_contract_p2_2_operating_point_bridge.md (IC 2)
  ↓
Version decision (★5) — after IC PASS(es), not before
```

No tag created, no push, no version bump — all explicitly out of scope for this contract, left for Engineer.
