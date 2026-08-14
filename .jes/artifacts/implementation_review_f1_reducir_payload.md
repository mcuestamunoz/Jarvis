# Implementation Review — F-1 (Vehicle-Agnostic Payload Direction)

**Date:** 2026-08-14  
**Reviewer:** Cursor (JES)  
**Contract:** `.jes/artifacts/implementation_contract_f1_reducir_payload.md`  
**Report:** `.jes/artifacts/implementation_report_f1_reducir_payload.md`  
**Base:** `checkpoint-catalog-impl-b`

## Verdict

**PASS WITH NOTES**

F-1 closes the semantic inversion at the goal-planning layer. Payload detection is direction-aware, vehicle-agnostic, and wired through the existing Goal Plan → HandoffContext → DSE machinery without a parallel architecture or catalog/H4 scope creep.

## Checklist (contract acceptance)

| Criterion | Result |
|---|---|
| `"reducir payload"` → `reducir_payload` | **Pass** (spot-check + 51 tests) |
| `"reducir carga útil"` → `reducir_payload` | **Pass** |
| Positive payload phrases → `aumentar_payload` | **Pass** (regressions green) |
| Numeric payload → iterate path | **Pass** (`"reducir payload a 2kg"` → `None`) |
| Vehicle-agnostic detection | **Pass** (pure text; dron/robot/rover E2E) |
| `reducir_payload` Goal Plan | **Pass** (3 strategies, neutral wording) |
| DSE symmetric grid + lower candidates | **Pass** (factors < 1.0; probe 2.0/2.8 vs 4.0 baseline) |
| `aumentar_payload` DSE unchanged | **Pass** |
| H1–H4 regressions | **Pass** (FN-022/024/025/026 subset green) |
| Full suite | **Pass** — **1681** (reviewer re-run) |
| No catalog/H5/BOM/material | **Pass** |
| `motor_count` architecture-conditional | **Pass** (catalog present; never promoted without data) |
| No global `goal_planner` rewrite | **Pass** (payload only; other 3 goals untouched) |

## Code review highlights

**Root cause fix — correct layer.** Bare `"payload"` removed from `_GOAL_KEYWORDS`. `_detect_payload_goal` runs first with explicit direction via `_direction_of` and phrase tables — not a one-off `if "reducir" and "payload"` bypass.

**Symmetry — correct machinery.** `reducir_payload` uses same `GOAL_STRATEGIES`, `EXPLORATION_GRIDS`, `_score_candidate`, `_GOAL_EXPLORE_DOMAIN`, Handoff bind — no `intent_resolver.py` change needed (generic `EXPLORATION_GRIDS` membership).

**Engineer lock — honored.** Motor/actuator strategy stays in catalog; `_prioritize_strategies` pushes it last when `motor_count` absent from `sim_context` (always today). Does not invent `motor_count`.

**Scope discipline — clean.** 4 production files touched meaningfully; 51 focused tests; zero catalog/bind/orchestrator refactor beyond domain map entry.

## Notes (non-blocking)

1. **Undirected bare `"payload"`** still resolves to `aumentar_payload` when no decrease word is present (documented intentional default for pre-F-1 compat). Contract text said bare `"payload"` should not *alone* evidence increase — implementation interprets this as “must not substring-match increase without direction check,” not “return None for bare payload.” Acceptable for F-1; tighten in a follow-up if Engineer wants ambiguous bare dimension → Continuity/ask instead of default increase.

2. **Explicit explore phrases** for `reducir_payload` (e.g. `"optimiza para reducir payload"`) remain untested — Handoff-bound `"explora opciones"` path is the one that matters and is proven.

3. **H4 lever preseed via NL** for `payload_kg` still blocked by pre-existing FN-022 substring collision (`"payload"` in `payload_kg`) — same class as FN-026/thrust note; direct `match_plan_lever` test is sufficient for F-1.

4. **CLI probe was orchestrator-simulated**, not live `jarvis --chat`. Recommend Engineer runs the 4-line CLI script from contract before checkpoint commit — expected to pass given E2E tests.

## Regression verification (reviewer)

```
pytest tests/test_f1_reducir_payload.py tests/test_goal_planner.py \
       tests/test_fn022_engineering_intent.py tests/test_fn024_handoff_context_dse.py \
       tests/test_fn025_help_goal_intent.py tests/test_fn026_lever_iterate_preseed.py \
       tests/test_design_explorer.py -q     → 194 passed
pytest -q                                 → 1681 passed
```

## Queue

```text
F-1 PASS WITH NOTES
        ↓
Engineer CLI aggressive probe (live jarvis --chat)
        ↓
Update cli_findings F-1 → 🟢
        ↓
commit + tag (when Engineer asks)
        ↓
UX catálogo batería/hélice → Impl C
```
