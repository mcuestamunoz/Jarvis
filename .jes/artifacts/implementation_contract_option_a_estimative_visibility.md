# Implementation Contract — Option A: Show ESTIMATIVO in chat

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** RATIFIED ★1–★5 (2026-09-01). Implementer: this session (Engineer-authorized one-off).

**Type:** Product writer for the existing P27-B L2 sweep. **Not** new physics. **Not** T1/T2. **Not** `P_battery`. **Not** DSE. **Not** L1 change.

**Evidence (no new investigation):**
- [implementation_review_phase27b_parametric_battery_estimate.md](implementation_review_phase27b_parametric_battery_estimate.md) **N1** — engine-ready, conversation-dark
- [implementation_contract_phase27b_parametric_battery_estimate.md](implementation_contract_phase27b_parametric_battery_estimate.md) **v0.2** — formula + CLI renderer already shipped (`0a32b89`)
- Engineer queue 2026-09-01: **Opción A** = show the estimative in chat

**Checkpoint base:** `main` after P27-B (`0a32b89`). P26 / P27-A boundaries stay frozen.

**Parallel, not this IC:** [docs/HARDWARE_DEBT.md](../../docs/HARDWARE_DEBT.md) (HD-001/002/003).

---

## 0. Engineer ★ (to lock)

| ★ | Proposed lock | Why |
|---|---|---|
| **★1** | **Auto on user calculate / iterate** — no new chat command, no wizard | “Mostrar el estimativo” is visibility, not a second verb. `electricity.py` stays grid-free; the **writer** owns the product grid. |
| **★2** | **4S only** (`battery_cell_count == 4`). Other S-count → omit the block (honest gap) | Gate D polyline is 4S (16.4 / 13.2 / Vcut 14.0). Do not invent 6S OCV/R in this cut. |
| **★3** | **Ephemeral two-pass.** Do **not** persist `battery_endurance_sweep` in `current_parameters` | A stored sweep looks like SKU data. Rebuild from live hover current each time. |
| **★4** | **I_load = `motors × motor_hover_current_a`**, labeled `n×I_hover` — **not** pack draw, **not** `P_battery` | P27-B ★2 + P27-A I1 (rejected unlabeled I1). Live I, not hardcoded 68 A. |
| **★5** | **DSE / `design_explorer.py` must not call the writer** | P27-B ★3. Explore/apply stay L1-only. |

**If Engineer wants a command instead of auto-on-calculate:** stop and rewrite ★1 before Claude starts.

---

## 1. Intent

After a normal `calcular` (and a physical `iterate` that rebuilds calculations) on a **4S + hover-applicable** project, `estado` shows the existing CLI block:

```text
Autonomía estimada (ESTIMATIVO — no validado, no es tiempo de vuelo):
  …
```

without anyone injecting a sweep by hand. L1 `hover_energy_autonomy_min` stays the evidence line. L2 stays labeled assumed.

**Today:** `CalculateAction` calls `engine.build(current_parameters)` with no sweep → envelope `None` → CLI omits the block.

---

## 2. Product grid (writer only — never `electricity.py`)

When **all** of these hold, after pass 1 of `build()`:

- `battery_cell_count == 4`
- `battery_capacity_wh` present and `> 0`
- bundle `motor_hover_current_a` is a finite `> 0`
- `motors` (or bundle `motors`) is an integer `>= 1`
- pass-1 `hover_energy_autonomy_min` is not `None` (hover actually resolved)

emit **exactly two** points, pack/pack:

| Field | Value | Provenance on the point |
|---|---|---|
| `v_oc_full_v` | `16.4` | paper hypothesis 4.1 V/cell × 4 — **not SKU** |
| `v_oc_empty_v` | `13.2` | paper hypothesis 3.3 V/cell × 4 — **not SKU** |
| `v_cutoff_v` | `14.0` | assumed 3.5 V/cell × 4 — **not SKU** |
| `r_internal_ohm` | `0.020` then `0.040` | Gate D paper pack R — **not SKU** |
| `i_load_a` | `motors * motor_hover_current_a` (float, live) | ★4 |
| `capacity_ah` | `battery_capacity_wh / (4 * 3.7)` | nameplate coulomb budget used by L1’s Wh; Combo A → 1.5 |
| `r_internal_scope` | `"pack"` | |
| `voltage_scope` | `"pack"` | |
| `i_load_label` | `"n×motor_hover_current_a (hipótesis de corriente de motor — NO es I_pack, NO P_battery)"` | required |
| `capacity_source` | `"catalog_nameplate"` | passthrough; engine copies it |

If any gate fails → **no sweep**, pass-1 bundle is the result (L1-only, same as today).

**Forbidden in this grid:** silent 68 A, Voc/R constants inside `tools/electricity.py`, treating I as pack current, 6S scaling, catalog JSON R/OCV.

---

## 3. Placement

### 3.1 New helper (not a subsystem)

`src/jarvis/core/endurance_sweep_writer.py`

```text
build_product_endurance_sweep(parameters, bundle) -> list[dict] | None
build_with_estimative_sweep(engine, parameters) -> CalculationBundle
```

- Pure. No I/O. No ProjectState writes.
- `build_with_estimative_sweep`: `first = engine.build(parameters)`; if sweep is `None`, return `first`; else `engine.build({**parameters, "battery_endurance_sweep": sweep})` with a **copy** of the dict. Do not mutate the caller’s `current_parameters` object in place if it is the live state dict — copy first.
- `CalculationEngine.build` **unchanged** (still opt-in only).

### 3.2 Call the wrapper

| Call site | Change |
|---|---|
| `actions/calculate.py` | `build_with_estimative_sweep` instead of `engine.build` |
| `actions/iterate.py` | same, on the physical rebuild that writes `latest_results["calculations"]` |
| `actions/simulate.py` `_resolve_calculations` | when it **rebuilds** (no stored calc), use the wrapper |

**Do not** call the wrapper from:

- `design_explorer.py`
- DSE apply in `orchestrator.py` (`build(canonical_params)` stays bare)
- `actions/create_project.py`
- `param_definition_session.py`
- inferred-component rebuilds in `orchestrator.py`

### 3.3 Persistence

- Save the **second** bundle (with envelope) in `latest_results["calculations"]` / history, as today.
- **Never** write `battery_endurance_sweep` into `current_parameters` on disk.
- `estado` already reads envelope from `latest_results` — no orchestrator ctx change required.

### 3.4 CLI (small honesty pass)

Existing heading **must stay** (P27-B §4.2). If a row has `i_load_label`, surface that it is `n×I_hover` / not pack draw (short; do not drop `ESTIMATIVO`). No new heading. Forbidden phrases unchanged: `autonomía real`, `usable Wh`, `P_battery`.

**Addendum (Engineer 2026-09-01):** the same block must appear on the **`calcular` / physical `iterate` CLI reply** (`render_response`), not only on `estado`. Share one helper; do not fork wording. The L1 `Cálculos: … autonomía=` line may remain (it is `autonomy_min` / hover energy, not relabeled as ESTIMATIVO).

### 3.5 Untouched

`tools/electricity.py`, `design_explorer.py`, `library/`, `electrical_compatibility.py`, catalog JSON, DSE scoring, version bump.

---

## 4. Tests + probe

### 4.1 `tests/test_option_a_estimative_visibility.py`

| Case | Expect |
|---|---|
| Combo A bind → `CalculateAction.run` (no sweep in params) | envelope len=2; `source_type=="assumed"`; one `sustainable`, one `infeasible`; L1 ≈ 1.3237; `current_parameters` has **no** `battery_endurance_sweep` |
| Same, `battery_cell_count=6` (or unset) | envelope `None`; L1 still computed if hover exists |
| `design_explorer.py` import/grep | no `endurance_sweep_writer` / `build_with_estimative_sweep` / `battery_endurance_sweep` writes |
| Writer skipped when `motor_hover_current_a` missing on pass 1 | envelope `None` |

Reuse Combo A fixture pattern from `tests/test_phase27b_loaded_endurance.py` / P25 probes. Do **not** assert Gate D’s 0.4301 against live I (I is ~68.04 A, not 68.0). Assert outcomes + L1 + no persisted sweep.

### 4.2 `scripts/cli_probe_option_a_estimative_visibility.py`

1. Combo A bind (same as P27-B probe) → orchestrator/CLI **calculate** with **no** injected sweep.  
2. `render_startup_context` contains `ESTIMATIVO` and `INVIABLE`, does **not** contain `autonomía real`.  
3. L1 line still present ≈ 1.32 min.  
4. Loaded state JSON: `current_parameters` lacks `battery_endurance_sweep`.  
5. Existing `scripts/cli_probe_phase27b_battery_endurance.py` still **4/4** (manual sweep path unchanged).

---

## 5. Non-goals

```text
P_battery / ESC η / HD-001 M3 / HD-002 / HD-003
Validated loaded autonomy (P27-A)
Default Voc/R/I in electricity.py
Persisted sweep / user-editable R wizard
6S or generic N-S OCV
DSE reading L2
New chat verb (“estima”)
Relabel hover_energy_autonomy_min
Version bump / checkpoint (unless Engineer asks after review)
```

---

## 6. Files

| File | Role |
|---|---|
| `src/jarvis/core/endurance_sweep_writer.py` | **New** — product grid + two-pass wrapper |
| `src/jarvis/actions/calculate.py` | Use wrapper |
| `src/jarvis/actions/iterate.py` | Use wrapper on calc rebuild |
| `src/jarvis/actions/simulate.py` | Use wrapper on rebuild-only path |
| `src/jarvis/adapters/cli/main.py` | Optional: show `i_load_label` honesty |
| `tests/test_option_a_estimative_visibility.py` | **New** |
| `scripts/cli_probe_option_a_estimative_visibility.py` | **New** |
| `docs/IMPLEMENTATION_TASKS.md` | Mark in progress / done |
| `.jes/state/engineering_state.json` | Sync |

---

## 7. Acceptance (reviewer)

- Combo A `calcular` **reply** and `estado` show ESTIMATIVO without a hand-built sweep.  
- L1 unchanged vs P25 (1.3237).  
- No `battery_endurance_sweep` in saved parameters.  
- DSE code does not import the writer.  
- `electricity.py` formula/defaults byte-stable vs P27-B (no product grid there).  
- Suite green + both probes (P27-B + Option A).

---

## 8. After ★

Claude implements this file only. Cursor reviews against this IC, not against a new physics story.
