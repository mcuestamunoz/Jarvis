# Implementation Report — Option A: Show ESTIMATIVO in chat

**Contract:** [`implementation_contract_option_a_estimative_visibility.md`](implementation_contract_option_a_estimative_visibility.md)  
**★:** [`engineer_ratification_option_a_estimative_visibility.md`](engineer_ratification_option_a_estimative_visibility.md)  
**Implementer:** Cursor (Engineer-authorized one-off, 2026-09-01)  
**Base:** P27-B on `main` (`0a32b89`)  
**Status:** Complete. Full suite **2075 passed, 0 failed** (2071 baseline + 4 new). Option A probe **4/4**. P27-B probe **4/4**. P25 probe **4/4**.

---

## 1. Files

```text
src/jarvis/core/endurance_sweep_writer.py          (new)
src/jarvis/actions/calculate.py
src/jarvis/actions/iterate.py
src/jarvis/actions/simulate.py
src/jarvis/adapters/cli/main.py                    (i_load_label honesty)
src/jarvis/core/orchestrator.py                    (comment only)
tests/test_option_a_estimative_visibility.py       (new, 4 tests)
scripts/cli_probe_option_a_estimative_visibility.py (new, 4 steps)
```

**Not touched:** `tools/electricity.py`, `design_explorer.py`, `library/`, `electrical_compatibility.py`, catalog JSON, DSE apply path (`orchestrator.py` still calls `engine.build` bare).

---

## 2. Mapping to IC

| Lock | What shipped |
|---|---|
| ★1 | `CalculateAction` / physical `IterateAction` / simulate rebuild use `build_with_estimative_sweep`. No new chat verb. |
| ★2 | Writer returns `None` unless `battery_cell_count == 4`. |
| ★3 | Two-pass on a **copy**. `current_parameters` never gains `battery_endurance_sweep`. |
| ★4 | `i_load_a = motors × motor_hover_current_a` (live). Label copied onto each point. CLI shows `n×I_hover, no es I_pack` when label present. |
| ★5 | `design_explorer.py` has no writer import (tested). DSE apply unchanged. |

`CalculationEngine.build` remains opt-in. Product grid constants live only in `endurance_sweep_writer.py`.

---

## 3. Live Combo A (payload 1.718 kg)

```text
calcular (no injected sweep)
  hover_energy_autonomy_min ≈ 1.3237
  envelope: 2 rows, assumed, one sustainable + one infeasible
  estado: ESTIMATIVO + INVIABLE + L1 line
  saved current_parameters: no battery_endurance_sweep
```

---

## 4. Tests

- `test_combo_a_calculate_shows_envelope_without_persisting_sweep`
- `test_six_s_omits_envelope`
- `test_writer_skips_when_hover_current_missing`
- `test_design_explorer_does_not_call_writer`

---

## 5. Non-goals (held)

No `P_battery`, no 6S OCV, no persisted sweep, no version bump, no HD-* close.
