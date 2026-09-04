# Implementation Contract — CLI feasibility vs readiness semantics

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** RATIFIED ★1–★5 (2026-09-01). **You are Claude Code.** Implement this file only. Cursor reviews; Cursor does not implement.

**Type:** Claim-language / Continuity + CLI copy. **Not** new physics. **Not** ERF §11. **Not** a fidelity ladder.

**Evidence:**
- [investigation_report_cli_feasibility_semantics.md](investigation_report_cli_feasibility_semantics.md)
- [investigation_review_cli_feasibility_semantics.md](investigation_review_cli_feasibility_semantics.md) — **PASS WITH NOTES**
- [engineer_ratification_cli_feasibility_semantics.md](engineer_ratification_cli_feasibility_semantics.md) — ★1–★5 locked

**Checkpoint base:** tag **`v0.3.5`** / `fc46938` plus current tree (P27-B / ESTIMATIVO already shipped). Do not revert those.

---

## 0. You (Claude)

- Edit only files listed in §6.
- Do not change `engineering_readiness.py` evidence/verdict/`ASSEMBLY_READY`.
- Do not change `resolve_operating_point`, HOLD rows, `fallback_only`, voltage epsilon, catalog JSON, `missing_params_for_reason` **globally** (calc still correctly lacks W).
- Do not invent `motor_power_w`, hover watts, ESC η, pack R, minutes.
- Do not bump `pyproject.toml` unless the Engineer asks after review.
- Full suite green. Zero weakened tests.

---

## 1. Intent (field fixture)

`workspace/autonomía-de-5min-c09442c25db0` after 4/4 + `calcular`/`simular`/`estado` must no longer say:

```text
Diseño validado en simulación (PASS)
Declarar motor_power_w …
(sin hélice de catálogo)          # while hq_5045_bn is BOM-bound
```

and must say, in substance:

```text
thrust feasibility PASS
autonomy objective unmet / not calculated
do not invent motor_power_w for this SKU
fallback OP is not the BOM propeller combo
```

ERF may still print `ASSEMBLY READY`. That dual is **allowed** (★1).

---

## 2. Locked copy (do not freelance)

### 2.1 Continuity `situation` — `project_continuity.py`

**Only** when `sim_status == "pass"` **and** `parsed_constraints.autonomy_min` is set **and** calculated autonomy is absent (`latest_results.calculations.autonomy_min` is None **or** `simulation.energy_status == "missing_energy_parameters"`):

```text
Comprobación de empuje: PASS. Candidato inicial — la autonomía del objetivo no está demostrada.
```

Replace the current `"Diseño validado en simulación (PASS). …"` **in that branch only**.

Keep `"Física orientativa en PASS…"` for incomplete/missing BOM.

When there is **no** autonomy constraint, or when `autonomy_min` **was** computed, leave the existing PASS situation string unchanged.

### 2.2 Continuity evidence — autonomy target without current

When `autonomy_target_min` is set and `current_autonomy_min` is None, the evidence line must not look like a silent target. Append an explicit clause, e.g.:

```text
Autonomía objetivo: 5 min — no calculada (sin evidencia de potencia de hover usable)
```

Do **not** write `(actual ~…)`. Do **not** print a fake minute.

### 2.3 ReasoningLayer CTA — `_collect_suggested_actions` energy branch

**Do not** change `missing_params_for_reason`. Gate the **label**.

When `signals["missing_energy_parameters"]`:

| Condition | Label (locked) | Reason (locked sense) |
|---|---|---|
| `catalog_bound_motor_covers_power_w(design_properties)` is True (battery Wh may already be set) | `No declares motor_power_w a mano — este motor de catálogo no declara vatios` | Inventar W usaría `(Wh/W)×60` como si fuera vuelo. No hay autonomía de hover calculable con la evidencia actual. |
| Motor **not** catalog-bound, `motor_power_w` actually missing | Keep today’s `Declarar motor_power_w…` | Unchanged unbound path |

Pass `design_properties` into the layer context if it is not already there (`build()` already has `design_properties` on context in several tests — use it). Do **not** fall through to the default `param_list = "battery_capacity_wh, motor_power_w"` when `missing_e` is empty because the motor is SKU-bound.

Also fix the **insight** for the same signal (`_build_insights` missing-energy block): when catalog-bound, do not tell the user to “define `motor_power_w`”. Same honest gap, no W wizard.

Continuity rank-6 will forward the new label when BOM is complete. That is intended.

### 2.4 Orchestrator proactive — `build_startup_context` ~4115

When `catalog_bound_motor_covers_power_w` is True, **remove `motor_power_w` from `missing_params`** for this energy branch. If nothing remains, do **not** set `proactive_question` / `param_definition_reason` for energy. Unbound motors keep `"¿Definimos motor_power_w (energía) ahora?"`.

Reuse the existing helper from `project_closure.py`. No second predicate.

### 2.5 Honesty note — `energy_model_honesty_note`

| Case | Behavior |
|---|---|
| No `autonomy_min` constraint | `None` (today) |
| Constraint set **and** `calculations.autonomy_min` is not None | Keep today’s L0 `(Wh/W)×60` sentence |
| Constraint set **and** autonomy not calculated | **Different** sentence, e.g. `Autonomía no calculada: no hay potencia de hover usable ni W de placa. No inventes motor_power_w.` Do **not** imply a number exists to interpret. |

You may read `latest_results` from `project_state` (already passed in). Update `tests/test_project_closure_v1.py` `test_energy_honesty_only_when_autonomy_constrained` accordingly (add the null-autonomy case; keep “no constraint → None”).

### 2.6 `calcular` / `simular` autonomy line — `adapters/cli/main.py`

When `autonomy_min is None`, do **not** stay fully silent if an energy gap is visible:

**Calculate:** if `tool_results` contains `tool_name == "missing_energy_parameters"` **or** (if present) latest `energy_status`, append a clause such as:

```text
, autonomía=no calculada (sin evidencia de potencia — no es tiempo de vuelo)
```

**Simulate:** same using `simulation.energy_status == "missing_energy_parameters"` and/or `autonomy_min is None` with that energy_status.

**Forbidden phrases:** `fuera del rango del dataset`, `unverifiable` (those are Phase 2.5 hover-unverifiable, ★5), `autonomía real`, a numeric minute.

Do not assume `energy_status` exists on the calculate payload. Prefer `tool_results`.

Do **not** add a fake `hover_energy` block on `estado` when `_hover_energy_from_calculations` is None (honest absence stays).

### 2.7 Propulsion suffix — `render_startup_context`

`resolution_type == "fallback_operating_point"`:

| BOM | Suffix |
|---|---|
| No propellers `catalog_ref` (motor-only bind) | keep ` (sin hélice de catálogo)` |
| Propellers entry has `catalog_ref` (family propeller) | **replace** with ` (fallback de fabricante — combo exacto no usable)` |

Read BOM from `ctx["component_bom"]` (already in startup context). Do not infer from `.name`. Do not change `propulsion_resolution` JSON or the resolver.

Keep `test_estado_renders_honest_evidence_label` motor-only assertion. **Add** a second test: bind `hq_5045_bn` (or any propeller `catalog_ref`) → rendered must **not** contain `sin hélice de catálogo`, must contain the fallback-de-fabricante suffix (or equivalent locked string above).

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_project_continuity.py` | Closed BOM + sim PASS + `energy_status=missing_energy_parameters` + `parsed_constraints.autonomy_min` → situation contains `Comprobación de empuje` / `Candidato inicial`, **not** `Diseño validado`. Loose `"PASS" in situation` tests must still pass. |
| `tests/test_energy_params.py` | New: catalog-bound motors in `design_properties` + missing energy signal → suggested label must **not** contain `Declarar motor_power_w`. Unbound path still does. Orchestrator: catalog-bound emax without W + battery Wh → `proactive_question` must **not** ask to define `motor_power_w`. |
| `tests/test_g21_g22_catalog_bind_ux.py` | Existing bound-without-watts / propeller fall-through must stay green. |
| `tests/test_phase2_lookup_operating_point.py` | Keep motor-only suffix test; add propeller-bound suffix test (§2.7). |
| `tests/test_project_closure_v1.py` | Honesty note: constraint + no calc autonomy → new wording; constraint + autonomy present → old L0; no constraint → None. |
| `tests/test_cli_feasibility_semantics.py` **new** (or fold into continuity tests) | Fixture sketch from the investigation: catalog `emax_rs2205s_2300` (no W) + propeller `catalog_ref` + 4S Wh + sim PASS + `autonomy_min` None → (a) next step does not ask to invent W, (b) situation not `Diseño validado`, (c) calculate/sim render has named-negative autonomía, (d) suffix not `sin hélice de catálogo`. |

Optional probe: `scripts/cli_probe_cli_feasibility_semantics.py` driving the same combo via orchestrator (pattern of `cli_probe_option_a_estimative_visibility.py`). Not a substitute for the unit fixture.

Do **not** weaken `test_energy_params.py` engine tests that still expect `energy_status == missing_energy_parameters` when W is absent — that remains physically true.

---

## 4. Non-goals

```text
engineering_readiness.py / ASSEMBLY_READY / _energy_evidence   (Option B)
missing_params_for_reason global semantics
P27-A / P26 / P_battery / ESC η / HD-001/002/003
resolve_operating_point / HOLD / fallback_only / voltage epsilon
DSE / Structure v1+ / Block Closure / H5 / C-081
Conversation Engine / new chat verb
Invented motor_power_w / hover minutes
Relabel hover_energy_autonomy_min
estado fake hover unverifiable line when resolution is null
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/project_continuity.py` | Situation + evidence autonomy line |
| `src/jarvis/core/reasoning_layer.py` | Energy CTA + insight, catalog-aware |
| `src/jarvis/core/orchestrator.py` | Energy proactive gate (~4115) |
| `src/jarvis/core/project_closure.py` | `energy_model_honesty_note` |
| `src/jarvis/adapters/cli/main.py` | calcular/simular named negative; fallback suffix |
| `tests/test_project_continuity.py` | Situation |
| `tests/test_energy_params.py` | CTA + proactive |
| `tests/test_phase2_lookup_operating_point.py` | Suffix second case |
| `tests/test_project_closure_v1.py` | Honesty note |
| `tests/test_cli_feasibility_semantics.py` | New end-to-end unit of the field case |
| `scripts/cli_probe_cli_feasibility_semantics.py` | Optional |
| `docs/IMPLEMENTATION_TASKS.md` | In progress / done when you finish |
| `.jes/state/engineering_state.json` | Sync |

---

## 6. Acceptance (reviewer)

- Field-equivalent state: no `Diseño validado`, no `Declarar motor_power_w`, no `sin hélice de catálogo` with propeller bound.
- Unbound motor + missing W: still asked to declare W / choose catalog.
- Motor-only fallback suffix unchanged.
- `energy_status` / calc `autonomy_min` still null (physics unchanged).
- ERF Energy PASS / ASSEMBLY READY **unchanged** for the same fixture.
- Suite green. `test_g21_g22_catalog_bind_ux.py` green.
- No `src/` outside §5.

---

## 7. After you finish

Write `implementation_report_cli_feasibility_semantics.md` (files, tests run, physics unchanged). Cursor reviews against **this** IC.
