# Implementation Contract — CLI catalog-assist watts recovery

**Project:** Jarvis  
**Date:** 2026-09-02  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor  
**Reviewer:** Cursor against this IC after the edit

**Status:** RATIFIED ★ (Engineer “bien ratifico”, 2026-09-02). Implement this file only.

**Type:** T1-shaped wiring, **new trigger**. Same G22 list + pick. **Not** T1+2. **Not** Tier 3. **Not** Option B / `ASSEMBLY_READY`. **Not** inventing `motor_power_w`.

**Walk fixture (tmp tests only):** `autonomia-15min` shape — `emax_rs2205s_2300` (no `max_watts`) + catalog propeller + 4S Wh + `autonomy_min` constraint, sim **pass**, `calculations.autonomy_min is None`. Do not mutate Engineer `workspace/`.

---

## 0. You

- Edit only files in §5.
- Reuse `build_motor_catalog_suggestions` + `_offer_component_motor_catalog` / pick. **No** new ranker. **No** drop-KV/prop (T1+2 stays underspec-only).
- Do not change `_derive_overall`, Energy PASS, Block Closure formula, G21 covering-with-watts, G18 `definir motor` list.
- Do not invent W, minutes, or SKUs.
- Full suite green.

---

## 1. Intent

After binding a catalog motor that **does not declare nameplate W**, with an autonomy objective and **no calculated minutes**, Jarvis must:

- keep saying the 15 min is not demonstrated (situation already shipped);
- **not** stop at “No declares motor_power_w”;
- tell the user **why** there is no number (this SKU has no W);
- offer `ayúdame a elegir` and a numbered G22 list of motors that **do** declare `max_watts`, so L0 can run again.

Picking a W-SKU may still miss the 15 min target (e.g. ~5 min). That is recovery of evidence, not meeting the requirement.

IDLE covering **with** nameplate W stays G21 (no motor picker).

---

## 2. Locked behavior

### 2.1 Predicate (single authority)

Add next to `bound_motor_sku_is_underspec` (prefer `engineering_readiness.py`):

```text
bound_motor_needs_watts_recovery(project_state) -> bool
```

True **iff all** of:

1. `bound_motor_sku_is_underspec` is **False** (T1/T1+2 own underspec);
2. `catalog_bound_motor_lacks_nameplate_watts(design_properties)` is True;
3. `derive_physical_requirements(...).autonomy_target_min` is set;
4. `calculations.autonomy_min` is None **or** `simulation.energy_status == "missing_energy_parameters"`.

False if no autonomy constraint, or minutes exist, or SKU has `max_watts`.

### 2.2 List — G22 then keep only nameplate W

New helper in `motor_catalog_assist.py` (name free), e.g. `build_nameplate_watts_motor_suggestions`:

- Call `build_motor_catalog_suggestions` (limit 10 is OK, then truncate);
- keep rows whose `max_watts is not None`;
- reindex `1..n`, cap 5.

**Do not** call `build_underspec_motor_offer` (no relaxed section).

Empty after filter: honest sentence, locked:

```text
Este motor no declara vatios, por eso no hay autonomía. No hay otro motor en el catálogo con KV/hélice actuales que declare W. No inventes motor_power_w.
```

Non-empty list header (one line before existing G22 lines):

```text
Este motor no declara vatios, por eso no hay autonomía. Solo candidatos con W de placa:
```

Then existing `format_motor_catalog_suggestions` body (or equivalent). Trailing: `Elige un número…` plus `Elegir no garantiza cumplir el objetivo de autonomía.`

### 2.3 IDLE — `_try_start_assisted_motor_help`

Today: catalog-bound + **not** underspec → `return None`.

Replace the dead-end with:

| Bound | Underspec | Watts recovery (§2.1) | Behavior |
|---|---|---|---|
| no | — | — | unchanged |
| yes | True | — | T1/T1+2 offer (unchanged) |
| yes | False | **True** | Open COMPONENT motors + offer **§2.2 list** (not full G22, not T1+2) |
| yes | False | False | `return None` (G21) |

Do **not** open the numeric `motor_power_w` wizard.

### 2.4 Continuity next_step

When §2.1 is true (sim may be **pass**), **before** the suggested-action / “No declares motor_power_w” rank:

If §2.2 names non-empty:

```text
Este motor de catálogo no declara vatios, por eso no hay autonomía. Candidatos que sí declaran W: {names}. Di 'ayúdame a elegir'. No inventes motor_power_w.
```

`names` = up to 5 from the helper.

If empty: the empty sentence in §2.2.

`next_useful_why`: reuse the existing “Inventar W usaría (Wh/W)×60…” sense (may be verbatim).

Situation string **unchanged** (feasibility / uncalculated autonomy).

T1 underspec rank-2 **stays first** when underspec is live.

### 2.5 Out of this IC

`_offer_component_motor_catalog` default (G18 `definir motor`, unbound, T1 underspec) **unchanged** — may still show `emax_rs2205s_2300`. Only the IDLE watts-recovery call uses §2.2.

ReasoningLayer locked “No declares motor_power_w…” insight may stay; Continuity must not leave that as the **only** next step when §2.1 is true.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_cli_catalog_assist_watts_recovery.py` **new** | emax no-W + prop catalog + 4S + autonomy constraint + calc/sim → IDLE `ayúdame a elegir` is a numbered list, contains a W-SKU (e.g. `sunnysky_r2305_2500`), **does not** contain `emax_rs2205s_2300`, **not** a bare `estado`. Covering `r2305` (has W) IDLE still no motor picker. Continuity next_step has `ayúdame a elegir` + W name, not only `No declares motor_power_w`. |
| `tests/test_cli_catalog_assist_t1.py` | Underspec IDLE / G18 covering motors-only stay green. |
| `tests/test_g21_g22_catalog_bind_ux.py` | G21 covering-with-identity / G22 empty-strict green. |

Optional probe. Do not weaken `test_reasoning_missing_energy_catalog_bound_motor_no_watts_label` (emax still must not ask to invent W).

---

## 4. Non-goals

```text
T1+2 filter relax
Tier 3 joint combo
Invent motor_power_w / hover minutes
_derive_overall / ASSEMBLY_READY / Energy PASS / Option B
Block Closure rollup
Battery picker
G18 definir-motor list contents
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/engineering_readiness.py` | Predicate §2.1 |
| `src/jarvis/core/motor_catalog_assist.py` | Helper + format |
| `src/jarvis/core/orchestrator.py` | IDLE branch; offer call with §2.2 list |
| `src/jarvis/core/project_continuity.py` | Next step §2.4 |
| `tests/test_cli_catalog_assist_watts_recovery.py` | New |
| `docs/IMPLEMENTATION_TASKS.md` | Sync |
| `.jes/state/engineering_state.json` | Sync |

---

## 6. Acceptance

- emax walk: IDLE list of W-motors, not `estado`; Continuity names recovery + help-choose.
- r2305 covering: G21 noop.
- T1 underspec unchanged.
- `calcular` still `autonomy_min is None` until a W-SKU is picked.
- Suite green.

---

## 7. After you finish

Write `implementation_report_cli_catalog_assist_watts_recovery.md`.
