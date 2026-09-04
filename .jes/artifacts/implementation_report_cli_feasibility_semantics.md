# Implementation Report — CLI Feasibility vs Readiness Semantics

**Contract:** [`implementation_contract_cli_feasibility_semantics.md`](implementation_contract_cli_feasibility_semantics.md)
**Implementer:** Claude Code
**Base:** tag `v0.3.5` / `fc46938` plus current tree (Phase 2.7-B, Option A already shipped)
**Status:** Complete, all §2 items implemented. Full suite **2087 passed, 0 failed** (2080 baseline + 7 new tests). New probe **4/4 PASS**. Zero regression across `cli_probe_phase25_hover_energy.py` (4/4), `cli_probe_minimum_universe_combo.py` (3/3), `cli_probe_phase27b_battery_endurance.py` (4/4), `cli_probe_option_a_estimative_visibility.py` (5/5).

---

## 1. What was implemented, mapped to the IC's locked copy sections

### §2.1 — Continuity situation (`project_continuity.py:101-112`)

New elif inserted between the existing "architecture pending" and "sim PASS" branches — fires **only** when `sim_status=="pass"` AND `req.get("autonomy_target_min") is not None` AND (`calc.get("autonomy_min") is None` OR `sim.get("energy_status")=="missing_energy_parameters"`):

```text
"Comprobación de empuje: PASS. Candidato inicial — la autonomía del objetivo no está demostrada."
```

Every other path to `"Diseño validado en simulación (PASS)..."` is byte-identical to before — verified by a new test (`test_situation_still_diseno_validado_when_no_autonomy_constraint`) confirming the original string still fires when there's no autonomy constraint.

### §2.2 — Continuity evidence (`project_continuity.py:130-136`)

When `req.get("current_autonomy_min")` is `None`, the "Autonomía objetivo: X min" evidence line now appends `" — no calculada (sin evidencia de potencia de hover usable)"` instead of silently omitting the `(actual ~...)` clause. Locked wording used verbatim.

### §2.3 — ReasoningLayer CTA + insight (`reasoning_layer.py`)

New `ReasoningLayer._catalog_bound_motor_lacks_watts(context)` static helper calls `project_closure.catalog_bound_motor_covers_power_w(context.get("design_properties"))`. Both `_collect_suggested_actions`'s `missing_energy_parameters` branch and `_build_insights`'s matching block now check this first:

- **True** (catalog-bound, no nameplate W): label `"No declares motor_power_w a mano — este motor de catálogo no declara vatios"`, reason `"Inventar W usaría (Wh/W)×60 como si fuera vuelo. No hay autonomía de hover calculable con la evidencia actual."` — locked copy, verbatim.
- **False** (genuinely unbound/unspecified motor): unchanged `"Declarar {param_list} en parámetros del proyecto"` path — verified unchanged by `test_reasoning_missing_energy_unbound_motor_still_asks_to_declare`.

**Dependency resolved:** `context["design_properties"]` is already populated by `orchestrator._build_analyze_context` (`.model_dump()`, a plain dict) — `ReasoningLayer` already reads it dict-style elsewhere (`_extract_signals`, `_component_entries`). `catalog_bound_motor_covers_power_w` (its only other caller: `param_present_for_architecture`, called with the *live* `DesignProperties` object) needed to accept **both** shapes. Made it dual-mode (`isinstance(design_properties, dict)` branch vs. the original `getattr`-based object branch) — same predicate, same function, no second helper, no behavior change for existing object-mode callers (verified: full suite green, including every existing `catalog_bound_motor_covers_power_w`/`param_present_for_architecture` test).

### §2.4 — Orchestrator proactive gate (`orchestrator.py:4115-4139`)

After computing `missing_params = missing_params_for_reason(MISSING_ENERGY_PARAMETERS, params)`, filters out `"motor_power_w"` when `catalog_bound_motor_covers_power_w(_dp)` is True (`_dp` is the live `design_properties` object already local to this branch — object-mode, no dict-shape concern here). If the filtered list is empty, `proactive_question`/`param_definition_reason` are never set for this branch (unchanged `if missing_params:` guard achieves this without new control flow). Unbound motors keep asking, unaffected — `_energy_missing_comps`/battery-only-missing cases unaffected (filter only ever removes `motor_power_w`, never `battery_capacity_wh`).

### §2.5 — `energy_model_honesty_note` (`project_closure.py:390-411`)

Now reads `latest_results.calculations.autonomy_min` in addition to the existing `parsed_constraints.autonomy_min` check:

| Case | Behavior |
|---|---|
| No constraint | `None` (unchanged) |
| Constraint set, `calculations.autonomy_min` present | Original L0 `(Wh/W)×60` sentence (unchanged) |
| Constraint set, `calculations.autonomy_min` absent | New: `"Autonomía no calculada: no hay potencia de hover usable ni W de placa. No inventes motor_power_w."` |

`tests/test_project_closure_v1.py::test_energy_honesty_only_when_autonomy_constrained` updated to cover all three cases explicitly (previously only tested the first two, and the constraint-set case happened to always hit the *new* branch's precondition — that's the one pre-existing test this IC's changes broke, fixed here, not weakened: the old assertion `"Wh" in note or "simplificado" in note.lower()` is now scoped to the case where it's actually true).

### §2.6 — `calcular`/`simular` autonomy line (`adapters/cli/main.py:442-451,463-473`)

Both lines now branch three ways instead of two:
- `autonomy_min is not None` → unchanged numeric string.
- `autonomy_min is None` and an energy gap is visible (`calculate`: any `tool_results` entry with `tool_name=="missing_energy_parameters"`; `simulate`: `simulation.energy_status=="missing_energy_parameters"`) → `", autonomía=no calculada (sin evidencia de potencia — no es tiempo de vuelo)"` — locked wording, verbatim, no forbidden phrases (`fuera del rango del dataset`, `unverifiable`, `autonomía real`, no numeric minute).
- Neither → `""` (unchanged silent case for genuinely unrelated missing-parameter situations, e.g. blocking physics).

`estado`'s `hover_energy` block is untouched — still absent (not a fake line) whenever `_hover_energy_from_calculations` is `None`, per §2.6's explicit instruction.

### §2.7 — Propulsion fallback suffix (`adapters/cli/main.py:310-328`)

When `resolution_type=="fallback_operating_point"`, now checks `ctx["component_bom"]` (already present in startup context, no new field) across its `defined`/`incomplete`/`declarative` buckets for a `propellers` entry with a non-null `catalog_ref`:

- Propeller catalog-bound → `" (fallback de fabricante — combo exacto no usable)"` (new, locked wording).
- No propeller catalog-bound (motor-only bind, the original case) → `" (sin hélice de catálogo)"` (unchanged) — verified unchanged by the existing `test_estado_renders_honest_evidence_label`.

`propulsion_resolution` JSON and the resolver itself are untouched (C4/§4 respected) — this is a BOM lookup added at render time only.

---

## 2. Files touched — matches §5/§6 exactly

```text
src/jarvis/core/project_continuity.py    situation branch + evidence clause (§2.1/§2.2)
src/jarvis/core/reasoning_layer.py       catalog-aware CTA + insight (§2.3)
src/jarvis/core/orchestrator.py          proactive gate (§2.4)
src/jarvis/core/project_closure.py       dual-mode catalog_bound_motor_covers_power_w (§2.3 dependency) + energy_model_honesty_note (§2.5)
src/jarvis/adapters/cli/main.py          calcular/simular named negative (§2.6) + fallback suffix (§2.7)
tests/test_project_continuity.py         +2 tests (§2.1/§2.2 fixture + no-constraint-unchanged guard)
tests/test_energy_params.py              +3 tests (ReasoningLayer catalog-bound/unbound CTA, orchestrator proactive)
tests/test_phase2_lookup_operating_point.py  +1 test (propeller-bound suffix case)
tests/test_project_closure_v1.py         1 test updated (3-case honesty note coverage)
tests/test_cli_feasibility_semantics.py  new — end-to-end field-fixture reproduction
scripts/cli_probe_cli_feasibility_semantics.py  new — optional probe, same fixture
docs/IMPLEMENTATION_TASKS.md             synced
.jes/state/engineering_state.json        synced
```

**Not touched** (§4 non-goals, confirmed): `engineering_readiness.py`, `resolve_operating_point`/HOLD/`fallback_only`/voltage epsilon, any catalog JSON, `missing_params_for_reason`'s global semantics, `design_explorer.py`, `library.py`.

---

## 3. Live verification — field-fixture equivalent (this session)

`tests/test_cli_feasibility_semantics.py::test_field_fixture_claim_language` and `scripts/cli_probe_cli_feasibility_semantics.py` both reproduce the exact fixture shape (`emax_rs2205s_2300` no-watts + `hq_5045_bn` catalog propeller + 4S battery + `autonomy_min=5` constraint) through the real orchestrator and confirm, in one run:

```text
calcular:  calculations.autonomy_min = None (physics unchanged)
           rendered: "...autonomía=no calculada (sin evidencia de potencia — no es tiempo de vuelo)"
simular:   simulation.status = "pass" (thrust feasibility unchanged), autonomy_min = None
           rendered: same named-negative clause
estado:    "Declarar motor_power_w" absent from rendered text and from proactive_question
           continuity.situation = "Comprobación de empuje: PASS. Candidato inicial..." (not "Diseño validado")
           "(sin hélice de catálogo)" absent; "(fallback de fabricante — combo exacto no usable)" present
           readiness.subsystems.energy.verdict == "PASS"  (ERF §11 untouched, confirmed live — not just asserted)
```

The last line is the direct, live confirmation that ★1's "dual is allowed" holds: `ASSEMBLY READY`-adjacent Energy verdict is exactly as it was before this IC — only the *claim language* around it changed.

---

## 4. Tests

**Added (7):**
- `test_situation_thrust_feasibility_only_when_autonomy_unmet`, `test_situation_still_diseno_validado_when_no_autonomy_constraint` (`test_project_continuity.py`)
- `test_reasoning_missing_energy_catalog_bound_motor_no_watts_label`, `test_reasoning_missing_energy_unbound_motor_still_asks_to_declare`, `test_build_startup_context_catalog_bound_motor_no_watts_no_proactive` (`test_energy_params.py`)
- `test_estado_fallback_suffix_when_propeller_catalog_bound` (`test_phase2_lookup_operating_point.py`)
- `test_field_fixture_claim_language` (`test_cli_feasibility_semantics.py`, new file)

**Updated (1, disclosed):** `test_project_closure_v1.py::test_energy_honesty_only_when_autonomy_constrained` — extended from 2 cases to 3 (no constraint / constraint+calculated / constraint+uncalculated), not weakened — the original assertion is preserved exactly, scoped to the case where it's actually true.

**Zero weakened tests** — every existing assertion that changed was either (a) scoped more precisely to the case it was actually testing, or (b) left untouched and still passing (`test_g21_g22_catalog_bind_ux.py`, `test_estado_renders_honest_evidence_label`, all `catalog_bound_motor_covers_power_w`/`param_present_for_architecture` object-mode callers).

---

## 5. Verification checklist (§6 acceptance)

| # | Check | Result |
|---|---|---|
| 1 | Field-equivalent state: no `Diseño validado`, no `Declarar motor_power_w`, no `sin hélice de catálogo` with propeller bound | ✅ live-verified (§3) |
| 2 | Unbound motor + missing W: still asked to declare W / choose catalog | ✅ `test_reasoning_missing_energy_unbound_motor_still_asks_to_declare`, existing `test_build_startup_context_nominal_has_energy_proactive` unchanged |
| 3 | Motor-only fallback suffix unchanged | ✅ `test_estado_renders_honest_evidence_label` unchanged and passing |
| 4 | `energy_status`/calc `autonomy_min` still null (physics unchanged) | ✅ asserted live in §3, no calc/sim engine touched |
| 5 | ERF Energy PASS / ASSEMBLY READY unchanged for the same fixture | ✅ asserted live in §3 (`readiness.subsystems.energy.verdict == "PASS"`) |
| 6 | Suite green | ✅ 2087/2087 |
| 7 | `test_g21_g22_catalog_bind_ux.py` green | ✅ unchanged, passing |
| 8 | No `src/` outside §5 | ✅ confirmed via `git status` — exactly the 5 files listed |

**No version bump, no checkpoint, no tag** — per the IC, pending Cursor review.
