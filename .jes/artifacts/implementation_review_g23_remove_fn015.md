# Implementation Review — G23 Eliminate FN-015 Feature

**Contract:** `implementation_contract_g23_remove_fn015.md`  
**Report:** `implementation_report_g23_remove_fn015.md`  
**Reviewer:** Cursor  
**Date:** 2026-08-20  
**Verdict:** **PASS** (one documented deviation accepted; one minor doc nit)

---

## Checklist (contract §6)

| # | Criterion | Result |
|---|---|---|
| 1 | Brief bullet gone for all keys | ✅ motors + battery tested; `repetir esta guía` absent |
| 2 | IDLE FN-015 bridge deleted; no stealth reimplementation | ✅ `_try_help_define_pending_idle` / `_help_current_pending_acquisition` zero hits in `src/`/`tests/` |
| 3 | DEFINE_MISSING: no Brief replay, no catalog via definir | ✅ `_define_missing_confusion_reask` — one-line `question` only |
| 4 | Detector renamed; FN-015 product naming gone from live API | ✅ `is_define_missing_confusion_phrase`; comments honest about removal |
| 5 | C-032 REMOVED; living maps cleaned | ✅ CONNECTIONS/DIAGRAMS/RUNTIME/ACQUISITION updated |
| 6 | Historical artifacts SUPERSEDED | ✅ `implementation_contract_fn015.md`, `cycle_close_fn015.md` bannered |
| 7 | G21 choose path green; full suite green | ✅ 1894 passed (independent run) |

---

## Acceptance criteria (contract §4)

All 9 criteria met per report + independent verification.

---

## Deviation review (contract ★3 IDLE mechanism)

**Claimed:** Adding confusion phrases to `GUIDANCE_PATTERNS` would collide with Bug-56 `project_status` intercept inside `DEFINE_MISSING`, replacing the mandated short re-ask with a full Continuity dump mid-wizard.

**Assessment:** **Accepted.** The orchestrator's DEFINE_MISSING branch resolves intent for `project_status` before the confusion gate; a global GUIDANCE match would indeed fire in the wrong mode. The narrow IDLE-only check (`is_define_missing_confusion_phrase` → `_handle_project_status()`) satisfies ★3's *requirement* (Continuity authority, no wizard, 0 LLM) without cross-mode regression. Well documented inline (~817–831) and in the report §4.

This is a **correct implementation choice**, not scope creep.

---

## Code review

### Deleted (confirmed)

- `tests/test_fn015_pending_help.py`
- `_try_help_define_pending_idle`
- `_help_current_pending_acquisition`

### Survives (by design — hygiene, not feature)

- `is_define_missing_confusion_phrase` — narrow detector, honest docstring
- `_define_missing_confusion_reask` — single-line re-ask, no session mutation, no catalog

### Product surface

- Brief: only `ayúdame a elegir` on motors (G21); no `definir` CTA
- IDLE: `project_status`, not wizard auto-open
- Numeric wizard: `ayúdame a definir` no longer opens catalog (G21/FN-005 owns `elegir`)

---

## Tests

| File | Count | Notes |
|---|---|---|
| `tests/test_g23_fn015_removed.py` | 11 | Covers Brief, in-wizard re-ask, no catalog, IDLE status, G21/FN-013/analyze regressions |
| Deleted `test_fn015_pending_help.py` | −9 | Correct — tested removed behavior |

1894 = 1892 (G21/G22 baseline) − 9 + 11. Math checks out.

---

## Doc purge

Living docs updated as specified. Historical FN-015 artifacts bannered, not deleted.

### Minor doc nit (non-blocking)

`docs/system_map/CONNECTIONS.md` C-037 Evidence line still lists `_help_current_pending_acquisition` as a caller of `build_acquisition_brief` — method no longer exists. Should be purged in a follow-up doc touch (or same commit).

`docs/PROJECT_CONTINUITY.md` deferred notes under FN-016 still mention "FN-015 also declines" in historical context — acceptable as closed-cycle record, but could confuse skimmers; optional cleanup.

---

## Stacked working tree (Engineer note)

Three logical cycles uncommitted in same tree:

1. **G21/G22** — catalog bind UX (review PASS)
2. **G23** — FN-015 removal (this review PASS)

**Recommended commit sequence:**

```text
commit 1: G21/G22  → tag checkpoint-g21-g22 (or checkpoint-pre-impl-c-partial)
commit 2: G23      → tag checkpoint-g23 (or fold into one tag if Engineer prefers single cut)
```

Or single commit if Engineer wants one checkpoint before CLI probe — but separate commits preserve bisect clarity.

---

## Recommendation

**Approve for commit.** Gate for CLI probe + Impl C IC is open after checkpoint.

Optional pre-commit: fix C-037 Evidence line stale symbol (30-second doc fix).

---

**End of review.**
