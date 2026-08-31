# Implementation Contract — G24-A DSE Apply By Index (IC 1 / Next Engineering Block)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** DSE apply UX — user can **explicitly select any row of `exploration.viable[]`** and apply it. Preserves catalog identity when a catalog candidate is listed below `#1`. **Does not** change ranking, scoring, or `"aplica la mejor"` semantics.

**Investigation:** [`.jes/artifacts/investigation_report_next_engineering_block.md`](investigation_report_next_engineering_block.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_next_engineering_block.md`](investigation_review_next_engineering_block.md) — **PASS WITH NOTES**  
**Prior finding:** [`.jes/artifacts/cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md`](cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md)  
**Checkpoint base:** tag **`checkpoint-closure-policy`** · docs hygiene **`73bd9fa`**

**Arc position:** IC **1 of 2** (Next Engineering Block). IC 2 = P2-2 operating-point electrical bridge (separate contract — **not this cut**). **H5 deferred.**

**Workflow:** Claude implements **G24-1 → G24-6 in order** + report → Cursor review → CLI probe → checkpoint if Engineer asks. **No version bump in this IC.**

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | **G24-A RATIFIED** — primary next IC. |
| **★2** | **Apply-by-index ONLY (Option A).** No ranking tiebreak, no catalog preference in `_score_candidate`, no `EXPLORATION_GRIDS` change, no redesign of `"aplica la mejor"`. |
| **★3** | **P2-2 bridge SECOND** — out of scope here; separate IC after G24-A PASS. |
| **★4** | **H5 DEFER** — out of scope; no schema lock 1A reopening. |
| **★5** | **Version bump AFTER chosen IC PASS** — not in this diff. |

**Product contract (Engineer, locked):**

> The user can explicitly select any row of `viable[]` and apply it.  
> `"aplica la mejor"` remains exactly `viable[0]`.

**IC 1 gate (Engineer, locked):**

> Adds apply capability **without reinterpretation** of existing explore ranking or G5 invalidate semantics. Zero `_score_candidate` / `EXPLORATION_GRIDS` diff.

---

## 1. Problem / intent

### 1.1 Today

After `optimiza para <goal>`, the CLI lists up to five viable candidates (`orchestrator._handle_explore`, lines ~3482–3488). The only apply path is:

```3576:3576:src/jarvis/core/orchestrator.py
        best = exploration.viable[0]
```

`intent_resolver.py` `APPLY_PATTERNS` resolve to `apply_exploration_result` with **no index** — `_handle_apply_exploration()` always takes `#1`.

**G24 failure mode (live, baseline `73bd9fa`):**

1. User already bound a catalog motor (`catalog_ref` set).
2. Explore returns abstract params-only candidates at `#1…#4` (common when thrust is declared — abstract grid scales without cost).
3. User runs `"aplica la mejor"` → applies abstract `#1` → G5 `invalidate_diverged_catalog_refs` clears `catalog_ref` while `.name` may stay stale.

When a catalog candidate **does** appear in the list at `#2…#5`, the user still cannot reach it — there is no `"aplica la N"`.

**Scope boundary:** G24-A fixes **apply selection** only. It does **not** guarantee catalog rows enter `.viable` when ranking excludes them (that would be G24-B — explicitly deferred).

### 1.2 Target

```text
User > optimiza para aumentar payload
Jarvis > … 1. abstract …  5. motors [sku]: …

User > aplica la 5
  → applies exploration.viable[4]  (1-based UI → 0-based internal)
  → if row is catalog-native (components_delta.motors.catalog_ref): catalog_ref preserved
  → calculate + simulate + save (same pipeline as today)

User > aplica la mejor
  → unchanged: exploration.viable[0]
  → abstract #1 still clears catalog_ref via G5 (existing behavior — regression, not fixed here)
```

---

## 2. Locked semantics (non-negotiable)

### 2.1 Indexing

| Surface | Rule |
|---|---|
| **User-facing index** | **1-based**, matching explore list numbering (`1.` … `5.`). |
| **Internal selection** | `viable[index - 1]` after validation. |
| **Default (no index)** | Index **1** — identical to today's `viable[0]`. |

### 2.2 Recognized apply phrases (minimum set)

Implement **`IntentResolver.resolve_apply_exploration_index(user_input) -> int | None`**:

- Returns **`None`** → default index **1** (preserve all existing unqualified apply phrases).
- Returns **`int` N** (N ≥ 1) when input matches an **indexed** apply phrase.

**Minimum indexed patterns (normalize text first — same `_normalize_text` as existing resolver):**

| Pattern class | Examples |
|---|---|
| `aplica la N` | `"aplica la 5"`, `"aplicar la 3"` |
| `aplica #N` | `"aplica #5"`, `"aplica #2"` |
| `aplica el N` / `aplica la opción N` | `"aplica el 4"`, `"aplica la opcion 2"` |
| Ordinal (optional but recommended) | `"aplica la quinta"`, `"aplica la 5-ésima"` — map 1–5 only |

**Must NOT match as indexed apply:**

- `"aplica la mejor"`, `"aplica la optima"` — these stay **unqualified** → index 1.
- `"optimiza para …"` — still `explore_design_space`.
- Bare `"aplica"` without a number — unqualified → index 1 (existing behavior).

**Resolution order (locked):** check **indexed apply patterns first**; only if no index captured, fall through to existing `APPLY_PATTERNS` → `apply_exploration_result`.

### 2.3 Bounds and errors

| Case | Behavior |
|---|---|
| No `last_exploration_result` | Same error as today. |
| `viable` empty | Same error as today. |
| Index **N > len(viable)** | **Error** — informative message listing valid range `1…len(viable)`; **no state mutation**. |
| Index **N < 1** or non-integer | Treat as unqualified apply (index 1) **or** error — **pick one in report**; recommended: error if explicit `#0` / negative, else unqualified. |

### 2.4 Unchanged behaviors (regression locks)

| Behavior | Lock |
|---|---|
| `_score_candidate` / `EXPLORATION_GRIDS` / explore generation | **Zero diff** |
| `"aplica la mejor"` → `viable[0]` | **Byte-identical selection** |
| G5 `invalidate_diverged_catalog_refs` on params-only apply | **Unchanged** — still runs when applied row is params-only |
| Component-driven apply (`components_delta`) | **Unchanged** — `apply_components_delta` path |
| Explore result copy (`Di «aplica la mejor»…`) | **Out of scope** (G24-C deferred) — do not redesign CTA text in this IC |

---

## 3. Implementation slices (G24-1 … G24-6)

Execute **in order**. Each slice should leave the suite green.

### G24-1 — Index resolver (`intent_resolver.py`)

- Add `resolve_apply_exploration_index(user_input) -> int | None` per §2.2.
- Wire into `resolve_intent` / apply path: indexed apply still resolves to `"apply_exploration_result"`.
- Unit tests in `tests/test_design_explorer.py` `TestApplyPatterns` (or new `tests/test_g24_apply_by_index.py`):
  - `"aplica la 5"` → intent `apply_exploration_result`, index 5.
  - `"aplica #3"` → index 3.
  - `"aplica la mejor"` → index `None` (default 1).
  - `"aplica"` → index `None`.
  - `"optimiza para autonomia"` → not apply.

### G24-2 — Orchestrator apply index (`orchestrator.py`)

- Change signature: `_handle_apply_exploration(self, *, index: int = 1) -> dict`.
- Replace `best = exploration.viable[0]` with bounds-checked `best = exploration.viable[index - 1]`.
- `handle_user_text` apply branch: pass `index=resolver.resolve_apply_exploration_index(user_input) or 1`.
- Success message should mention applied row number (e.g. `"Configuración #5 aplicada"`) — minimal, no CTA redesign.

### G24-3 — Apply-by-index integration test (primary gate)

**New test** (prefer `tests/test_g24_apply_by_index.py`):

`test_apply_by_index_preserves_catalog_ref_when_catalog_not_at_one`

**Fixture (G24-TF — locked, does not touch `design_explorer` scoring):**

1. Real orchestrator project via `_project_with_bound_motor` pattern (`tests/test_impl_c_catalog_aware_dse.py`) — catalog motor + declared thrust (G24 bug context).
2. Real `explore(ps, "aumentar_payload")` — persist to `session.last_exploration_result`.
3. Locate first catalog-native candidate in `exploration.candidates` (`components_delta.motors.catalog_ref` set).
4. **Test-only session patch (permitted):** ensure that catalog candidate appears in `exploration.viable` at **index 5 (1-based)** without moving it to index 1:
   - Replace `viable[4]` with the catalog candidate **or** append and truncate to 5 — catalog row must remain at **N > 1** while `viable[0]` stays abstract/params-only.
   - **Do not** call `_score_candidate` or mutate scores.
5. `"aplica la 5"` through `handle_user_text` → `status == "ok"`.
6. Assert `design_properties.components["motors"].catalog_ref.sku == picked_sku`.
7. Assert `catalog_ref` is **not** `None`.

**Why G24-TF is allowed:** On baseline `73bd9fa`, bound-motor explore often produces **zero** catalog rows in `.viable` (investigation §4.2). The production bug is visible when a catalog row **is listed** but not at `#1`; G24-TF reproduces that list shape using real generated catalog candidates without reordering to `#0`.

### G24-4 — Regression tests

Minimum:

1. **`test_aplica_la_mejor_still_applies_viable_zero`** — unqualified apply → `viable[0]` (existing mock/stub tests in `test_design_explorer.py` updated for index param if needed).
2. **`test_apply_index_out_of_range_errors`** — `"aplica la 99"` → error, project unchanged.
3. **`test_bound_motor_aplica_la_mejor_clears_catalog_ref`** — bound motor + G24-TF explore (abstract `#1`) + `"aplica la mejor"` → `catalog_ref is None` (documents existing G5 path; **not** fixed by G24-A).
4. **Existing Impl C / G5 tests** — full suite green; **zero weakened assertions** without disclosure.

**Do not remove** the workaround comment in `test_full_explore_apply_path_with_real_catalog_candidate` yet — optional follow-up cleanup after G24-A lands (not required for PASS).

### G24-5 — CLI probe (`scripts/cli_probe_g24_apply_by_index.py`)

Deterministic probe — **no LLM**, `_RefuseLLM` pattern.

| Step | Action | Pass criterion |
|---|---|---|
| 1 | Create project + bound motor (thrust declared) via real bind path | `catalog_ref` set |
| 2 | `"optimiza para aumentar payload"` | Exploration persisted |
| 3 | G24-TF: place real catalog candidate at viable index **5**, abstract at **1** | Session patched; no scorer calls |
| 4 | `"aplica la 5"` | `catalog_ref.sku` matches applied catalog row |
| 5 | Fresh explore on same project → `"aplica la mejor"` | Applies `#1`; if params-only, `catalog_ref` cleared (**regression**, expected) |
| 6 | `"aplica la 99"` | Error; no crash |

Target: **6/6 PASS**.

### G24-6 — Implementation report

`.jes/artifacts/implementation_report_g24_a_apply_by_index.md` — slices done, tests/probe counts, any assertion changes disclosed, explicit confirmation **no** `_score_candidate` diff.

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/core/intent_resolver.py` | G24-1 |
| `src/jarvis/core/orchestrator.py` | G24-2 only (`_handle_apply_exploration`, apply branch in `handle_user_text`) |
| `tests/test_g24_apply_by_index.py` | G24-3, G24-4 (new) |
| `tests/test_design_explorer.py` | G24-1, G24-4 (extend `TestApplyPatterns` / apply stubs if needed) |
| `scripts/cli_probe_g24_apply_by_index.py` | G24-5 (new) |

**Must NOT change:**

- `design_explorer.py` — `_score_candidate`, `EXPLORATION_GRIDS`, `explore()` generation logic
- `catalog_bind.py` — G5 invalidate semantics (unless a one-line comment only)
- `component_writers.py`, `library.py`, `resolve_operating_point`, `engineering_readiness.py`
- P2-2 bridge / `electrical_compatibility.py`
- H5 / `CatalogRef` / `action_schema.py`
- Closure probes' fixtures; existing closure behavior
- `pyproject.toml` version
- Explore CTA copy redesign (G24-C)

---

## 5. Explicit non-goals (this IC)

- **G24-B** — ranking tiebreak / catalog preference in scoring  
- **G24-C** — honest CTA-only / explore message redesign  
- **P2-2** — operating-point `power_w` / `current_a` bridge (IC 2 — requires Engineer semantics lock on `motor_power_w` vs resolved OP power **before** that IC)  
- **H5** — ESC catalog family  
- Frankenstein `.name` cleanup after G5 invalidate  
- Auto-refresh calc/sim after apply  
- Conversation Engine / LLM apply interpretation  
- Version bump / checkpoint tag — Engineer call after review PASS  

---

## 6. Acceptance (Cursor review)

**PASS** if:

- User can `"aplica la N"` / `"aplica #N"` for N in `1…len(viable)` and apply that exact row  
- `"aplica la mejor"` and all existing unqualified apply phrases still select `viable[0]`  
- Out-of-range index → error, no state corruption  
- G24-TF gate test: catalog row at index **5** applied → `catalog_ref` preserved  
- G24 regression: `"aplica la mejor"` on abstract `#1` still clears `catalog_ref` when params diverge (G5)  
- Full suite green; probe **6/6**  
- Git diff confirms **zero** changes under `design_explorer.py` scoring/generation logic  
- No weakened tests without disclosure  

**FAIL** if:

- Any `_score_candidate` / ranking / grid change  
- Indexed apply changes default `"aplica la mejor"` behavior  
- Catalog rows not in `.viable` magically become applicable (must not bypass viable list)  
- P2-2 / H5 / Closure / P2-1 paths touched  
- Version bumped in this diff  

---

## 7. Queue after IC 1

```text
IC 1 PASS + CLI probe 6/6
  ↓
Engineer optional checkpoint (e.g. checkpoint-g24-apply-by-index)
  ↓
Engineer semantics lock for P2-2 (motor_power_w vs resolved OP power — see investigation review Note 3)
  ↓
Cursor: implementation_contract_p2_2_operating_point_bridge.md  (IC 2)
  ↓
Version decision (★5) — after IC PASS(es), not before
```

---

**End of contract.**
