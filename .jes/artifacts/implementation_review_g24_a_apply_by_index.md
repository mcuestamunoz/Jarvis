# Implementation Review — G24-A DSE Apply By Index (IC 1)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_g24_a_apply_by_index.md`](implementation_contract_g24_a_apply_by_index.md)  
**Report:** [`.jes/artifacts/implementation_report_g24_a_apply_by_index.md`](implementation_report_g24_a_apply_by_index.md)  
**Base:** tag `checkpoint-closure-policy` · docs hygiene `73bd9fa`

## Verdict

**PASS WITH NOTES**

All G24-1…G24-6 contract gates met. Hardest constraint verified independently: **zero diff** on `design_explorer.py`. Primary gate (apply-by-index preserves `catalog_ref` when catalog row is not `#1`) passes via G24-TF + live probe.

**Defect-first review:** No open findings that block checkpoint or IC 2 contract drafting (IC 2 still gated on Engineer P2-2 semantics lock).

---

## Contract checklist (§6)

| Criterion | Result |
|---|---|
| `"aplica la N"` / `"aplica #N"` applies exact row for N in `1…len(viable)` | **Pass** — tests + probe steps 4, 6 |
| `"aplica la mejor"` and unqualified apply → `viable[0]` | **Pass** — mock + probe step 5 |
| Out-of-range index → error, no state mutation | **Pass** — mock + integration + probe step 6 |
| G24-TF gate: catalog at index > 1 → `catalog_ref` preserved | **Pass** — `test_apply_by_index_preserves_catalog_ref_when_catalog_not_at_one` |
| Regression: abstract `#1` via `"aplica la mejor"` still clears `catalog_ref` (G5) | **Pass** — probe step 5 |
| Full suite green; probe 6/6 | **Pass** — **2001/2001**, **6/6** |
| Zero `design_explorer.py` scoring/generation diff | **Pass** — `git diff --stat` confirms |
| No weakened tests without disclosure | **Pass** — append-only; zero existing assertion edits |
| Scope: no P2-2 / H5 / version bump | **Pass** |

---

## Independent verification

```text
pytest tests/test_g24_apply_by_index.py              → 4 passed
pytest tests/test_design_explorer.py (ApplyPatterns + HandleApply) → 24 passed
pytest tests/ (full)                                 → 2001 passed
cli_probe_g24_apply_by_index.py                      → 6/6 PASS
cli_probe_requirements_closure.py                    → 5/5 PASS (Closure regression)
cli_probe_closure_policy_propeller_sku.py            → 4/4 PASS (Closure regression)

git diff --stat HEAD -- src/jarvis/core/design_explorer.py → (empty)
```

---

## Code review highlights

**G24-1 — minimal intent surface.** `resolve_apply_exploration_index` is a separate extraction step; existing `APPLY_PATTERNS` unchanged (correct — `"aplica la 5"` already matched `apply_exploration_result` on baseline). Ordinal map + numeric regex cover contract §2.2 minimum set.

**G24-2 — selection-only change.** `_handle_apply_exploration(*, index: int = 1)` adds bounds check then `viable[index - 1]`. All 12 pre-existing no-arg call sites remain byte-identical via default. G5 invalidate + component-driven apply paths untouched downstream of `best` selection.

**Regression lock honored.** `"aplica la mejor"` on bound-motor explore still applies abstract `#1` and G5 still clears identity — deliberately unfixed; G24-A adds escape hatch only when user names another index.

**Scope discipline.** Touch set matches contract §4: `intent_resolver.py`, `orchestrator.py`, tests, probe only.

---

## Disclosed additions — accepted

1. **`applied_index` in result dict** — additive, used by tests/probe; no existing consumer breakage. Acceptable.

2. **Success message branches on `index == 1`** — index 1 keeps prior copy; higher indices get `"Aplicando configuración #N..."`. Minimal, not explore-CTA redesign (G24-C still deferred).

3. **Index ≤ 0 via resolver → unqualified (default 1)** — matches contract §2.3 recommended choice; orchestrator also guards `index < 1` independently.

---

## Notes (non-blocking)

### Note 1 — G24-TF is test/probe fixture only

On baseline, bound-motor explore often produces **zero** catalog rows in natural `.viable`. G24-TF appends a real generated catalog candidate at a known index without re-scoring — contract-permitted and correctly scoped to tests/probe, not production ranking changes.

### Note 2 — Catalog rows not in `.viable` remain unreachable

G24-A fixes apply selection, not ranking visibility. When Impl C excludes catalog from top-5 entirely, user still cannot apply that SKU until G24-B (deferred) or a different explore shape. Investigation scope boundary preserved — not an IC 1 defect.

### Note 3 — Frankenstein `.name` after G5 clear

Still open, out of scope. `"aplica la mejor"` on abstract `#1` can leave stale `.name` with `catalog_ref=None` — unchanged from pre-G24-A.

### Note 4 — Checkpoint / version

Engineer may tag `checkpoint-g24-apply-by-index` when ready. **No version bump** in this diff (correct per ★5). IC 2 (P2-2 bridge) requires **Engineer semantics lock** on `motor_power_w` (catalog rating) vs `resolved_op.power_w` (observed OP power) before contract draft — investigation review Note 3.

---

## Next step

```text
IC 1 PASS WITH NOTES
  ↓
Engineer: optional checkpoint + commit
  ↓
Engineer ★: P2-2 field semantics (overwrite vs new keys)
  ↓
Cursor: implementation_contract_p2_2_operating_point_bridge.md (IC 2)
  ↓
Version decision (★5) — after IC PASS(es), not before
```

---

**End of review.**
