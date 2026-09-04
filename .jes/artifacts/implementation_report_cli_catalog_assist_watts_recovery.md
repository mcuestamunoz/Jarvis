# Implementation Report — CLI catalog-assist watts recovery

**Contract:** [`implementation_contract_cli_catalog_assist_watts_recovery.md`](implementation_contract_cli_catalog_assist_watts_recovery.md)  
**★:** [`engineer_ratification_cli_catalog_assist_watts_recovery.md`](engineer_ratification_cli_catalog_assist_watts_recovery.md)  
**Implementer:** Cursor (Engineer “bien ratifico”, 2026-09-02)  
**Base:** live tree after T1+2 + G18 covering motors-only help-choose (suite was 2111)  
**Status:** Complete. Full suite **2114 passed, 0 failed** (2111 + 3 new).

---

## 1. Mapped to IC

### §2.1 Predicate

`bound_motor_needs_watts_recovery` in `engineering_readiness.py`:

- `catalog_bound_motor_lacks_nameplate_watts`
- `autonomy_target_min` set
- `calculations.autonomy_min is None` **or** `energy_status == missing_energy_parameters`

**Hygiene vs IC bullet 1:** the predicate does **not** call `bound_motor_sku_is_underspec` (that would `resolve_motor_catalog_surface` a second time on every Continuity/`estado` path and fail G9-A `test_startup_context_invokes_catalog_resolver_once`). Underspec stays exclusive via:

- IDLE: underspec branch **before** watts recovery
- Continuity: T1 rank-2 (sim not pass) **before** the watts-recovery `elif`

### §2.2 List

`build_nameplate_watts_motor_suggestions` → G22 `build_motor_catalog_suggestions` (limit 10), keep `max_watts is not None`, reindex, cap 5. No `build_underspec_motor_offer`.

`format_watts_recovery_catalog`: locked header / empty sentence / trailing “Elegir no garantiza cumplir el objetivo de autonomía.”

### §2.3 IDLE

`_try_start_assisted_motor_help`: bound + underspec → T1+2 offer; bound + watts recovery → `_offer_component_motor_catalog(..., watts_recovery=True)`; covering with W → `None` (G21).

`_offer_component_motor_catalog` default (`watts_recovery=False`) unchanged — G18 `definir motor` may still list `emax_rs2205s_2300`.

### §2.4 Continuity

`_watts_recovery_next_step` before suggested-action / “No declares motor_power_w”. Names up to 5 W-SKUs + `ayúdame a elegir`. Why: invent-W sentence. Situation unchanged.

---

## 2. Files

```text
src/jarvis/core/engineering_readiness.py
src/jarvis/core/motor_catalog_assist.py
src/jarvis/core/orchestrator.py
src/jarvis/core/project_continuity.py
tests/test_cli_catalog_assist_watts_recovery.py
docs/IMPLEMENTATION_TASKS.md
.jes/state/engineering_state.json
```

---

## 3. Tests

| Test | Result |
|---|---|
| `tests/test_cli_catalog_assist_watts_recovery.py` | 3/3 |
| `tests/test_cli_catalog_assist_t1.py` | green |
| `tests/test_g21_g22_catalog_bind_ux.py` | green (G21 covering; emax-without-autonomy still opens propellers, not `motor_power_w`) |
| `tests/test_g9a_catalog_ref_gap.py` | green after predicate hygiene |
| Full suite | **2114** |

---

## 4. Physics / ERF / G22

Unchanged. No invent W. `_derive_overall` / Energy PASS / Block Closure / T1+2 / G18 list contents not edited for product behavior.

---

## 5. Notes for reviewer

G9-A forced dropping underspec from the **predicate**. Behavior of the IC table in §2.3 is still the exclusivity rule. Do not put `resolve_motor_catalog_surface` back into Continuity’s watts helper.
