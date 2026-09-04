# Implementation Report — CLI feasibility: calculated autonomy below target

**Contract:** [`implementation_contract_cli_feasibility_autonomy_below.md`](implementation_contract_cli_feasibility_autonomy_below.md)  
**Implementer:** Cursor (Engineer proceed 2026-09-02)  
**Base:** live tree after T1 catalog-assist (suite was 2103)  
**Status:** Complete. Full suite **2105 passed, 0 failed** (2103 + 2 new tests). Physics unchanged.

---

## 1. Mapped to IC

### §2.1 Situation

Helpers in `project_continuity.py`:

- `_autonomy_objective_undemonstrated` — parent uncalculated case **or** calculated-below.
- `_autonomy_calculated_below_target` — `current_autonomy_min < autonomy_target_min` **or** warning `autonomy_below_restriction`.

The existing §2.1 elif now calls the helper. Locked string unchanged:

```text
Comprobación de empuje: PASS. Candidato inicial — la autonomía del objetivo no está demostrada.
```

No-constraint and meets-or-exceeds still `"Diseño validado en simulación (PASS)…"`. Incomplete BOM still `"Física orientativa…"`.

### §2.2 Next step

When calculated-below:

1. Rank 2 (status warning / sim not pass): after T1 `_underspec_live`, before the generic `proactive_question` path — so architecture-complete CTA cannot win.
2. After architecture-pending ranks, before suggested-action / “puedes iterar” — covers `status_type == "nominal"` with the same numbers.

Locked next step verbatim. `next_useful_why` = `autonomy_below_restriction`. No SKUs, no `ayúdame a elegir`. T1 underspec copy still first in rank 2.

### §2.3 Evidence

Unchanged. Target + `(actual ~…)` already printed when current is set.

---

## 2. Files

```text
src/jarvis/core/project_continuity.py
tests/test_project_continuity.py
docs/IMPLEMENTATION_TASKS.md
.jes/state/engineering_state.json
.jes/artifacts/implementation_contract_cli_feasibility_autonomy_below.md
.jes/artifacts/engineer_ratification_cli_feasibility_autonomy_below.md
.jes/artifacts/implementation_report_cli_feasibility_autonomy_below.md
```

No `simulator.py`, `engineering_readiness.py`, orchestrator, CLI render of calc/sim numbers, catalog assist.

---

## 3. Tests

| Test | Result |
|---|---|
| `test_situation_thrust_feasibility_when_autonomy_calculated_below_target` | new — 15 vs 5.0 + warning, walk shape |
| `test_situation_still_diseno_validado_when_autonomy_meets_target` | new — 16 vs 15 still validated |
| `test_situation_thrust_feasibility_only_when_autonomy_unmet` | green (parent uncalculated) |
| `test_situation_still_diseno_validado_when_no_autonomy_constraint` | green |
| `tests/test_cli_feasibility_semantics.py` | 1/1 |
| `tests/test_cli_catalog_assist_t1.py` | 4/4 |
| Full suite | **2105** |

---

## 4. Physics / ERF

Unchanged. Sim can still `pass` with `autonomy_below_restriction`. Requirements INCOMPLETE + Continuity “candidato inicial” dual allowed (parent ★1).
