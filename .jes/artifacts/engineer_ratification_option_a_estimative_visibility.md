# Engineer Ratification — Option A: Show ESTIMATIVO in chat

**Date:** 2026-09-01  
**Authority:** Engineer (“ratifico” ★1–★5 as tabled)  
**Contract:** [implementation_contract_option_a_estimative_visibility.md](implementation_contract_option_a_estimative_visibility.md)  
**Baseline:** P27-B on `main` (`0a32b89`) · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

---

## Ratification status

**LOCKED.** Product writer for the existing P27-B L2 sweep may ship.  
P27-A validated loaded autonomy remains **NO IC**. `PHASE26_P_BATTERY_BOUNDARY` and `PHASE27_LOADED_BATTERY_BOUNDARY` stay frozen. Hardware debt (HD-001/002/003) is parallel and unchanged.

Engineer also authorized **this-session implementation** of this IC only (bounded product writer, not a new physics slice).

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | **Auto** on user `calcular` / physical `iterate`. No new chat verb. Grid lives in the writer, not in `electricity.py`. |
| **★2** | **4S only** (`battery_cell_count == 4`). Other S-count: omit ESTIMATIVO. |
| **★3** | **Ephemeral two-pass.** Never persist `battery_endurance_sweep` in `current_parameters`. |
| **★4** | **I_load = motors × motor_hover_current_a**, labeled n×I_hover — not pack draw, not `P_battery`. Live I, not hardcoded 68 A. |
| **★5** | **DSE must not call the writer.** |

---

## Next

Implement [implementation_contract_option_a_estimative_visibility.md](implementation_contract_option_a_estimative_visibility.md).
