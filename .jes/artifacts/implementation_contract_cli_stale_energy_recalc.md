# Implementation Contract — CLI Continuity: recalc after watts-recovery pick

**Project:** Jarvis  
**Date:** 2026-09-02  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** JES / Cursor against this IC after Claude reports

**Status:** RATIFIED (Engineer “procede”, 2026-09-02). **Claude implements this file only. JES does not edit `src/`.**

**Type:** Claim-language / ranking. **Not** auto-`calcular`. **Not** new physics. **Not** ERF / Option B. **Not** T1+2 / Tier 3. **Not** inventing `motor_power_w`.

**Walk (2026-09-02, `autonomia-15min`):** emax no-W → watts recovery list → pick `#1 sunnysky_r2305_2500` (~220 W). **Before** `calcular`, Continuity said `Declarar battery_capacity_wh, motor_power_w` though Wh and W were already in the project. After `calcular`, 5.0 vs 15 and autonomy-below were correct.

**Cause:** `latest_results.simulation.energy_status` stays `missing_energy_parameters` until the user recalculates. ReasoningLayer keys off that stale flag. `_detect_missing_energy_params` is **empty** (both params present) and the fallback still labels `battery_capacity_wh, motor_power_w`. Watts recovery is off (SKU now has W). Autonomy-below is off (no minutes yet). `suggested_action` wins. Same turn: `_append_arch_progress_hint` adds `puedes optimizar o simular`.

---

## 0. You

- Edit only files in §5.
- Do **not** call calculate/simulate inside the pick path.
- Do not change `_derive_overall`, Energy PASS, Block Closure, G22, T1+2, watts-recovery list/IDLE, G21 covering-with-W.
- Do not invent W, minutes, or SKUs.
- Full suite green. Zero weakened tests.
- After you finish: write `implementation_report_cli_stale_energy_recalc.md`.

---

## 1. Intent

After binding a catalog motor that **declares nameplate W**, with battery Wh already set, an autonomy objective, and **no new minutes yet** (stale `energy_status` / `autonomy_min is None`):

- Situation stays the locked thrust-feasibility sentence (autonomy not demonstrated).
- Next step is **recalculate**, not “declare W/Wh”, not watts-recovery list, not iterate/optimizar.
- ReasoningLayer must not emit `Declarar battery_capacity_wh, motor_power_w` when those params are already present.
- The pick message must not say `puedes optimizar o simular` in this state.

After `calcular`/`simular`, existing autonomy-below (5 vs 15) **unchanged**.

---

## 2. Locked behavior

### 2.1 Continuity rank — `_await_autonomy_recalc_next_step` (name free)

In `project_continuity.py`, **after** `_watts_recovery_next_step` and **before** `suggested_action`:

True **iff all** of:

1. `derive_physical_requirements` / `req.autonomy_target_min` is set (same source Continuity already uses for autonomy-below).
2. Minutes are absent or stale: `calculations.autonomy_min is None` **or** `simulation.energy_status == "missing_energy_parameters"`.
3. Nameplate W is now present: `catalog_bound_motor_lacks_nameplate_watts(design_properties)` is **False**, **and** `current_parameters.motor_power_w` is not None.
4. `current_parameters.battery_capacity_wh` is not None.
5. `_watts_recovery_next_step` is None (do not steal emax no-W).

False if no autonomy target, or minutes already exist **and** energy_status is not missing, or SKU still lacks W.

Locked next_step (verbatim):

```text
El motor vinculado declara vatios de placa. Di 'calcular' y 'simular' para actualizar la autonomía. No declares motor_power_w a mano.
```

`next_useful_why` (verbatim):

```text
Los W ya están en el proyecto; el último cálculo es anterior al cambio de motor.
```

Situation string **unchanged** (feasibility / uncalculated autonomy).

Rank order (first match still wins): underspec rank-2 → … → autonomy-below (calculated) → watts recovery (no W) → **this rank** → suggested_action.

Do **not** call `resolve_motor_catalog_surface` here (G9-A). Reuse `catalog_bound_motor_lacks_nameplate_watts` only.

### 2.2 ReasoningLayer — empty missing list is not “declare both”

In `_collect_suggested_actions` and the matching **insight** under `missing_energy_parameters`:

If `_catalog_bound_motor_lacks_watts` is False **and** `_detect_missing_energy_params` is **empty**:

- Do **not** emit `Declarar battery_capacity_wh, motor_power_w…`
- Do **not** emit the insight `faltan parámetros de energía: battery_capacity_wh, motor_power_w`
- Do **not** use the `else "battery_capacity_wh, motor_power_w"` fallback when `missing_e` is empty

If `missing_e` is non-empty (e.g. battery Wh actually absent), keep today’s declare-those-params path.

Emax no-W locked CTA (`No declares motor_power_w a mano…`) **unchanged**.

Optional same-file: the energy **tradeoff** that always lists both energy params when the stale signal is true — skip it when `missing_e` is empty. Do not add a new tradeoff module.

### 2.3 Pick hint — `_append_arch_progress_hint`

When architecture is complete **and** `_autonomy_objective_undemonstrated` is true for the active project, **do not** append:

```text
✓ Arquitectura completa (…) — puedes optimizar o simular.
```

Omit the hint on that turn (Continuity footer owns the next step). Other 4/4 saves without an autonomy-undemonstrated state keep today’s hint.

Do not open a wizard. Do not change pick bind (`set_motor_component`).

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_cli_stale_energy_recalc.py` **new** | Watts-recovery fixture: emax + prop + 4S + autonomy 15 + calc/sim → pick `sunnysky_r2305_2500` (do **not** calcular). Continuity `next_useful_step` contains `calcular` and `simular`, contains `No declares motor_power_w a mano`, does **not** contain `Declarar battery_capacity_wh`. Situation still `Candidato inicial` / not `Diseño validado`. Pick `message` does **not** contain `puedes optimizar o simular`. |
| same or `tests/test_cli_catalog_assist_watts_recovery.py` | **Before** pick, emax Continuity still names W-SKUs + `ayúdame a elegir` (watts recovery not stolen). |
| `tests/test_project_continuity.py` | After calc with 5.0 vs 15 + warning: autonomy-below next_step **unchanged** (not this recalc string). |
| `tests/test_energy_params.py` | `test_reasoning_missing_energy_catalog_bound_motor_no_watts_label` stays green. New: r2305 + `motor_power_w` set + Wh set + stale `energy_status=missing_energy_parameters` → no `Declarar battery_capacity_wh` in suggested labels. |

Do not mutate Engineer `workspace/`.

---

## 4. Non-goals

```text
Auto calcular / simular on pick
_derive_overall / ASSEMBLY_READY / Option B
T1+2 / Tier 3 / G22 filter change
Invent motor_power_w
Block Closure rollup
G18 definir-motor list
Invalidating latest_results without user calcular
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/project_continuity.py` | Rank §2.1 |
| `src/jarvis/core/reasoning_layer.py` | Guard §2.2 (suggestions + insight; tradeoff optional) |
| `src/jarvis/core/orchestrator.py` | `_append_arch_progress_hint` §2.3 only |
| `tests/test_cli_stale_energy_recalc.py` | New |
| `tests/test_energy_params.py` | ReasoningLayer stale-signal guard |
| `docs/IMPLEMENTATION_TASKS.md` | Sync after report |
| `.jes/state/engineering_state.json` | Sync after report |

---

## 6. Acceptance

- Walk turn after pick `#1` r2305, before `calcular`: next step is recalc, not declare W/Wh, not optimizar.
- Emax (no pick): watts recovery Continuity/IDLE unchanged.
- After `calcular` 5 vs 15: autonomy-below unchanged.
- Suite green.

---

## 7. After you finish

Write `.jes/artifacts/implementation_report_cli_stale_energy_recalc.md` (files, tests run, physics unchanged). Stop. JES reviews.
