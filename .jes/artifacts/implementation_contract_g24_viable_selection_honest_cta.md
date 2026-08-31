# Implementation Contract — G24 Viable Selection + Honest CTA (IC C / Deferred Queue)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** DSE explore UX — ensure at least one **catalog-native motor candidate** survives into `ExplorationResult.viable[]` when Impl C generated one, plus **honest explore CTA** copy. Completes the G24 arc started by G24-A (apply-by-index). **Does not** rewrite `_score_candidate`.

**Investigation:** [`.jes/artifacts/investigation_report_deferred_queue_post_v031.md`](investigation_report_deferred_queue_post_v031.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_deferred_queue_post_v031.md`](investigation_review_deferred_queue_post_v031.md) — **PASS WITH NOTES**  
**Checkpoint base:** tag **`v0.3.1`** / **`checkpoint-next-engineering-block`** · commit `30c9aec`

**Arc position:** IC **C** (primary). IC **D** (frankenstein `.name` micro) is a **separate contract** — may land in the same checkpoint window but **not** in this diff's scope.

**Workflow:** Claude implements **G24C-1 → G24C-6** + report → Cursor review → CLI probe → checkpoint if Engineer asks. **No version bump in this IC alone** (Engineer ★6: version after C+D PASS).

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | **C primary** — G24 viable selection + honest CTA. |
| **★2** | **A (Validation Case) defer.** |
| **★3** | **Option (a) — viable-slot reservation.** **`_score_candidate` formula: zero diff.** Option (b) scoring rewrite: **out of scope.** |
| **★4** | **B (H5) defer.** |
| **★5** | **D micro-IC parallel** — separate contract, not this IC. |
| **★6** | Version bump **after C+D PASS** — not in this diff. |

**Problem statement (live on v0.3.1, reproduced in investigation §5.1):**

```text
Impl C generates 4 catalog-native motor candidates
        ↓
global sort by _score_candidate (unchanged)
        ↓
viable[:MAX_VIABLE]   (MAX_VIABLE = 5)
        ↓
0 catalog rows in the list the user sees
        ↓
G24-A apply-by-index has nothing to select
```

**Product contract (Engineer, locked):**

> When Impl C generated at least one flyable catalog-native motor candidate, **at least one** must appear in the returned `viable[]` list shown to the user — without changing any candidate's score.

---

## 1. Problem / intent

### 1.1 Today

`DesignExplorer.explore()` (`design_explorer.py:638-647`):

```python
viable.sort(key=lambda c: c.score, reverse=True)
...
viable=viable[:MAX_VIABLE],
```

Catalog-native candidates compete on equal footing with unconstrained abstract param deltas. When ≥5 abstract candidates outscore every catalog row (common with bound motor + declared thrust), **all catalog rows are truncated out** before the orchestrator message or G24-A apply path run.

G24-A (`aplica la N`) is **correct and frozen** — it cannot apply a row that was never listed.

### 1.2 Target

After explore on a catalog-eligible goal with generated catalog candidates:

1. **Selection:** best-scoring **catalog-native motor** candidate (if any flyable) is **guaranteed** in `viable[]` (length still ≤ `MAX_VIABLE`).
2. **Scores:** every candidate keeps the **same `score` value** as today — only **membership/order** of the truncated list may change.
3. **CTA:** explore message honestly guides the user:
   - when `#1` is abstract and a catalog row exists at index `N>1` → point to `aplica la N`;
   - when **no** catalog-native row survived selection (e.g. zero generated) → say so explicitly — never a dangling CTA.

---

## 2. Locked semantics (non-negotiable)

### 2.1 Catalog-native candidate (identification)

A candidate is **catalog-native motor** when:

```text
candidate.components_delta.get("motors") is not None
AND candidate.components_delta["motors"].catalog_ref is not None
AND candidate.components_delta["motors"].catalog_ref.family == "motor"
```

Params-only candidates (`components_delta == {}`) are **never** catalog-native.

### 2.2 Viable-slot reservation algorithm (★3a)

Implement **`_finalize_viable_list(viable: list[ExplorationCandidate]) -> list[ExplorationCandidate]`** in `design_explorer.py` — single authority, called once at the end of `explore()` **instead of** bare `viable[:MAX_VIABLE]`.

**Steps (locked):**

1. **Sort** `viable` by `score` descending — same key as today; **do not recompute scores**.
2. **Filter** catalog-native motor candidates from the sorted list; if empty → return `sorted[:MAX_VIABLE]` (unchanged behavior when no catalog rows).
3. Let **`best_catalog`** = first entry in that filter (highest score among catalog-native).
4. Let **`head`** = `sorted[:MAX_VIABLE]`.
5. If **`best_catalog` already in `head`** → return `head` unchanged.
6. Else **reserve one slot:**
   - `others = [c for c in sorted if c is not best_catalog][:MAX_VIABLE - 1]`
   - return `others + [best_catalog]` (length exactly `MAX_VIABLE` when `len(sorted) >= MAX_VIABLE`).

**Properties (must hold in tests):**

- `_score_candidate` is never called from this helper.
- No candidate's `.score` field is mutated.
- At most **one** catalog-native slot is reserved (the best-scoring catalog-native only).
- If multiple catalog-native candidates exist, only `best_catalog` is guaranteed; others may remain truncated.

### 2.3 Goals / catalog branch scope

Reservation runs for **all goals** where catalog-native candidates can appear in `viable` (today: `_CATALOG_MOTOR_GOAL_KEYS` — `aumentar_payload`, `mejorar_estabilidad`). Do **not** special-case only those keys inside `_finalize_viable_list` — the helper is goal-agnostic; if no catalog-native in `viable`, it is a no-op.

When **`reducir_masa`** (or any goal) generates **zero** catalog candidates, behavior stays identical to today.

### 2.4 Honest CTA (`orchestrator._handle_explore`)

Extend the explore success message (`orchestrator.py` ~3487-3508) **without removing**:

- numbered list `1.` … `N.`
- `"Di «aplica la mejor» para aplicar la configuración #1 al proyecto."` (G24-A regression)

**Add** (Spanish, deterministic — no LLM):

| Condition | Minimum message intent |
|---|---|
| `#1` is **not** catalog-native **and** some `viable[k]` is catalog-native (`k>1`) | One line: `#1` is abstract/params-only; applying it may drop bound SKU — use `aplica la {k}` to apply the catalog option at `{k}`. |
| No catalog-native in `viable` **but** `len(exploration.candidates)` includes catalog-native that failed `can_fly` or were truncated before reservation | Optional honesty: no catalog option in top `{MAX_VIABLE}` — investigate constraints (keep brief). |
| `#1` is catalog-native | No warning needed (optional positive note OK, not required for PASS). |

Exact wording is implementer choice; **must** mention apply-by-index when a catalog row is listed at `N>1`.

### 2.5 Frozen behaviors (regression locks)

| Behavior | Lock |
|---|---|
| `_score_candidate` body | **Zero diff** |
| G24-A `resolve_apply_exploration_index` / `_handle_apply_exploration(index=…)` | **Unchanged** |
| `"aplica la mejor"` → `viable[0]` after selection | **Unchanged** |
| P2-2 `motor_op_*` / `motor_power_w` semantics | **Unchanged** |
| G5 `invalidate_diverged_catalog_refs` | **Unchanged** |
| Impl C catalog **generation** (`_build_catalog_motor_candidates_for_goal`) | **Unchanged** — selection only |

---

## 3. Implementation slices (G24C-1 … G24C-6)

Execute **in order**. Suite green after each slice.

### G24C-1 — `_finalize_viable_list` (`design_explorer.py`)

- Add helper per §2.2.
- Replace `viable=viable[:MAX_VIABLE]` with `viable=_finalize_viable_list(viable)`.
- Docstring cites ★3(a) and G24 investigation §5.1.

### G24C-2 — Unit tests for selection helper (`tests/test_g24_viable_selection.py` — new)

Minimum:

1. **`test_finalize_viable_reserves_best_catalog_when_truncated`** — synthetic `ExplorationCandidate` list: 5 abstract + 1 catalog with lower score; assert catalog in result, length ≤ 5, scores unchanged.
2. **`test_finalize_viable_noop_when_catalog_already_in_top5`**
3. **`test_finalize_viable_noop_when_no_catalog_native`**

### G24C-3 — Integration test (primary gate)

**`test_explore_bound_motor_includes_catalog_in_viable_aumentar_payload`** — real orchestrator/`design_explorer.explore()`:

- Fixture: bound motor + declared thrust (investigation §5.1 / `test_g24_apply_by_index._project_with_bound_motor` pattern).
- Goals: **`aumentar_payload`** and **`mejorar_estabilidad`** — assert `≥1` catalog-native in `exploration.viable` (today: **0**).
- **No session patch / G24-TF** — real explore output only.

### G24C-4 — G24-A end-to-end without G24-TF

Extend `tests/test_g24_apply_by_index.py` or new test:

- Same bound-motor fixture → explore → find index `N` of first catalog-native in **real** `viable` → `"aplica la N"` → `catalog_ref` preserved.
- Proves G24-A + G24C compose without hand-built `viable` reorder.

### G24C-5 — CTA + CLI probe (`orchestrator.py` + `scripts/cli_probe_g24_viable_selection_honest_cta.py`)

Probe steps (deterministic, `_RefuseLLM`):

| Step | Pass criterion |
|---|---|
| 1 | Bound motor + thrust; `"optimiza para aumentar payload"` |
| 2 | `≥1` catalog-native row in printed list (parse session `last_exploration_result.viable` or message) |
| 3 | Message includes honest CTA when `#1` abstract and catalog at `N>1` |
| 4 | `"aplica la N"` preserves `catalog_ref` (real index from step 2) |
| 5 | `"aplica la mejor"` still applies `#1` (G24-A regression) |
| 6 | `cli_probe_g24_apply_by_index.py` still **6/6** (subprocess OK) |

Target: **6/6 PASS**.

### G24C-6 — Implementation report

`.jes/artifacts/implementation_report_g24_viable_selection_honest_cta.md` — slices, tests, probe, explicit **`git diff` confirms zero `_score_candidate` changes**.

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/core/design_explorer.py` | G24C-1 |
| `src/jarvis/core/orchestrator.py` | G24C-5 CTA only |
| `tests/test_g24_viable_selection.py` | G24C-2, G24C-3 (new) |
| `tests/test_g24_apply_by_index.py` | G24C-4 (extend) |
| `scripts/cli_probe_g24_viable_selection_honest_cta.py` | G24C-5 (new) |

**Must NOT change:**

- `_score_candidate` function body or Impl C ★6 scoring policy docs (except adding a cross-ref comment in `_finalize_viable_list` is OK)
- `intent_resolver.py` / G24-A apply-by-index
- `component_writers.py`, `library.py`, `calculation_engine.py`, `electrical_compatibility.py`
- H5 / `CatalogRef` / ESC
- IC D (`catalog_bind.py` `.name`) — separate contract
- `pyproject.toml` version

---

## 5. Explicit non-goals (this IC)

- **G24-B (b):** `_score_candidate` formula rewrite, cost/feasibility terms, catalog preference inside scoring
- Changing which catalog SKUs Impl C **generates**
- Auto-apply catalog row without user verb
- Validation Case, H5, P2-1/P2-2 reopening
- Frankenstein `.name` (IC D)
- Version bump / tag

---

## 6. Acceptance (Cursor review)

**PASS** if:

- Investigation §5.1 repro fixed: `aumentar_payload` / `mejorar_estabilidad` → **≥1** catalog-native in `.viable`
- `_score_candidate` **zero diff**
- G24-A probe **6/6** unchanged; new probe **6/6**
- Full suite green
- CTA present when `#1` abstract + catalog at `N>1`
- `"aplica la N"` preserves `catalog_ref` on real explore output **without G24-TF**

**FAIL** if:

- Any `_score_candidate` change
- Scores mutated to force catalog inclusion
- G24-A regressions
- Mega-IC includes IC D `.name` changes

---

## 7. Queue after IC C

```text
IC C PASS + probe 6/6
  ↓
IC D (Frankenstein .name micro) — separate contract
  ↓
Both PASS → Engineer checkpoint + 0.3.x version (★6)
```

---

**End of contract.**
