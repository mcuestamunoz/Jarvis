# Investigation Report — CLI Feasibility vs Readiness Semantics

**Contract:** `.jes/artifacts/investigation_contract_cli_feasibility_semantics.md`
**Seed notes (hypotheses, not proof):** `.jes/artifacts/engineer_notes_cli_feasibility_semantics.md`
**Investigator:** Claude Code
**Baseline:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` (`fc46938`) — working tree currently carries later uncommitted work (Phase 2.7-B, Option A estimative visibility) on top of that checkpoint; the field fixture below was generated against that live state, so this report investigates the code as it stands today, not a `git checkout` back to `fc46938`. No `src/`/test file is touched by this investigation (§ sign-off).
**Date:** 2026-09-01

---

## Executive summary

The fixture (`workspace/autonomía-de-5min-c09442c25db0`) is **physically honest at every individual field** — `autonomy_min: null`, `hover_energy_autonomy_min: null`, `energy_status: missing_energy_parameters` are all correct given `emax_rs2205s_2300` (catalog-bound, no nameplate `max_watts`, confirmed in `state.json`). The problem is entirely in **claim language that aggregates across those fields without checking them**: four independent, verified findings, each traced to an exact file:line, each avoidable inside the existing C1-C5 constraints.

1. **Situation string overclaims.** `"Diseño validado en simulación (PASS)"` fires purely from `sim_status=="pass"` + empty BOM gaps + no pending architecture — it has **zero reference** to `energy_status`/`autonomy_min` anywhere in its predicate (`project_continuity.py:83-104`). Confirms hypothesis #2, precisely.
2. **The CTA is catalog-blind by construction, not by oversight.** `"Declarar motor_power_w"` is produced by `ReasoningLayer._collect_suggested_actions` (`reasoning_layer.py:235-248`), which calls `_detect_missing_energy_params` → `missing_params_for_reason(MISSING_ENERGY_PARAMETERS, params)` (`parameter_requirements.py:333-334`) — a raw `params.get(param) is None` check with **no** catalog awareness. A parallel, catalog-aware predicate (`catalog_bound_motor_covers_power_w`, `project_closure.py:44-58`) exists and is correctly used elsewhere (`param_present_for_architecture`, same file, L61-69) — but `ReasoningLayer` never calls it. This is Hypothesis #3/#4's "dual contract," confirmed as two real, independently-tested functions answering the same question differently for two different UI surfaces.
3. **Silent omission, and inconsistent with a pattern the codebase already has.** `calcular`/`simular`'s own response text (`adapters/cli/main.py:442-443,463-464`) fully omits any autonomy mention when null — no reason, no reference to the `parsed_constraints.autonomy_min=5.0` the user explicitly set. The **hover_energy block two hundred lines away in the same file already renders a named negative** when unverifiable (`:349-356`) — the newer Phase 2.5 code established the honest pattern; the older calc/sim line never adopted it.
4. **The propulsion suffix is a verified, concrete claim-language bug**, not a stylistic nitpick. `" (sin hélice de catálogo)"` fires on `resolution_type=="fallback_operating_point"` alone (`main.py:316-317`) — but the fixture has a **catalog-bound propeller** (`propellers.catalog_ref.sku == "hq_5045_bn"`, confirmed in `state.json`) whose OP row simply has no `propeller_sku` on the fallback record it fell back to. The line tells the user "you have no catalog propeller" while the BOM, two blocks earlier in the same `estado` output, shows one bound.

**Recommendation: Option A** (presentation + ranking only, ERF untouched) — see §5. **C1 was not broken by this investigation's evidence** — no stop-and-rewrite needed.

---

## 1. Baseline / fixture confirmation

`workspace/autonomía-de-5min-c09442c25db0/state.json`, live-read this session:

| Field | Value |
|---|---|
| `latest_results.calculations.autonomy_min` | `null` |
| `latest_results.calculations.hover_energy_autonomy_min` / `motor_hover_power_w` / `t_hover_motor_n` | all `null` |
| `latest_results.simulation.status` / `quality` / `safety_margin_ratio` | `pass` / `acceptable` / `1.2828` |
| `latest_results.simulation.energy_status` | `missing_energy_parameters` |
| `current_parameters` | has `battery_capacity_wh=148.0`; **no `motor_power_w` key at all** |
| `current_parameters.propulsion_resolution` | `{"resolution_type":"fallback_operating_point","fallback_only":true,"motor_sku":"emax_rs2205s_2300","propeller_sku":null,"thrust_n":10.042,"resolved_at_voltage_v":14.8,"source_type":"manufacturer_test",...}` |
| `design_properties.components.motors` | `catalog_ref={family:motor, sku:emax_rs2205s_2300}`, completeness `high` |
| `design_properties.components.propellers` | `catalog_ref={family:propeller, sku:hq_5045_bn}`, completeness `high` |
| `design_properties.components.battery` | `catalog_ref={family:battery, sku:lipo_4s_10000mah}`, 148 Wh |
| `parsed_constraints.autonomy_min` | `5.0` |

Every number in the contract's "Observed in chat" block is confirmed present, byte-for-byte, in the persisted state. Baseline suite: **2080 passed** (working tree, current HEAD + uncommitted work).

---

## 2. Gate 3.1 — Situation strings (as-is claim graph)

`project_continuity.py:build_project_continuity`, situation block (`:83-104`):

```text
status_type=="blocking"                          → "Diseño bloqueado..."
status_type=="no_data"                            → "Proyecto abierto sin simulación útil todavía."
sim_status and sim_status != "pass"                → "Última simulación: {sim_status}..."
incomplete or missing (BOM)                        → "Física orientativa en PASS..." (if can_fly/pass)
                                                       "Proyecto en progreso..." (otherwise)
architecture_progress and next_architecture_label  → "Arquitectura X: pendiente Y."
sim_status == "pass"                               → "Diseño validado en simulación (PASS)..."
else                                                → "Proyecto activo; revisa evidencia..."
```

**Exact predicate that upgrades orientativa → validado, traced for this fixture:**
- `status_type` — computed in `orchestrator.build_startup_context` (`:4001-4014`) from `ReasoningLayer` signals: `missing_physics_parameters` is False (physics_status is `valid`, not `missing_parameters` — energy is a *separate* signal), `has_warnings` is False (`warnings: []`), `has_simulation` is True → **`status_type = "nominal"`**. Confirmed live-read from the persisted `simulation` block above.
- `sim_status` = `"pass"` → third elif (`sim_status != "pass"`) is False.
- `incomplete or missing` — the BOM classifier (`project_closure.classify_component`, per this session's own earlier code review of the same predicate) routes `flight_controller`/`sensors` (completeness `medium`, real declared values) and `esc` (freeform, high) into the `declarative`/`defined` buckets, not `incomplete`. With every component catalog-bound-`high` or freeform-declared with real data, **`incomplete` and `missing` are both empty for this fixture** — the fourth elif is False.
- Architecture 4/4 (confirmed by the contract's own chat transcript) → `next_architecture_label` is falsy → fifth elif is False.
- Falls to `sim_status == "pass"` → **`situation = "Diseño validado en simulación (PASS). Proyecto vivo — listo para el siguiente paso útil."`**

**Answer to the contract's question ("BOM-complete heuristic, or stronger physics?"):** confirmed BOM-complete heuristic. The predicate chain never reads `energy_status`, `autonomy_min`, or `hover_energy_autonomy_min` — hypothesis #2 verified exactly as stated, with the precise elif chain cited above (the seed note only named "when BOM gaps clear," not the full architecture/sim_status interaction — now traced completely).

---

## 3. Gate 3.2 — CTA `motor_power_w` after architecture 4/4

**Which surface won, verified on the fixture:**

| Surface | Finding |
|---|---|
| `Continuity` rank branch (`project_continuity.py:183-208`, labeled "FN-005/P4: align Continuity with assisted energy/motor acquisition") | **Did not fire.** Its guard requires `motors` to appear in `incomplete`/`missing`, or `motor_catalog_matches` to be non-empty (`:186-189`). `motors` is catalog-bound `high` in this fixture (not incomplete/missing), and no catalog matches are being offered (motor already bound) — guard is False. |
| `ReasoningLayer` (`reasoning_layer.py:235-248`) | **This is the actual producer.** `signals["missing_energy_parameters"]` is `simulation.get("energy_status") == MISSING_ENERGY_PARAMETERS` (`:74`) — True for this fixture, independent of catalog state. `_collect_suggested_actions` returns `ReasoningSuggestion(label=f"Declarar {param_list} en parámetros del proyecto", priority=0.95)` where `param_list = self._detect_missing_energy_params(context)` → `missing_params_for_reason(MISSING_ENERGY_PARAMETERS, params)` (`parameter_requirements.py:333-334`) → filters `("battery_capacity_wh","motor_power_w")` against `params.get(x) is None` → only `motor_power_w` is missing (battery is present) → **label is literally `"Declarar motor_power_w en parámetros del proyecto"`.** |
| `Continuity`'s generic fallback (`project_continuity.py:226-228`) | **This is the bridge that surfaces it.** `elif suggested_action and sim_status=="pass" and not incomplete and not missing: next_step = suggested_action.get("label")`. Since `incomplete`/`missing` are both empty (§2) and `sim_status=="pass"`, and no higher-priority branch (blocking/warning/catalog-gap/motor-BOM-incomplete/missing/incomplete/architecture) fired, this is the branch that actually reaches the CLI as the observed "Declarar motor_power_w" CTA. |
| `param_present_for_architecture` (`project_closure.py:61-69`) | **Correctly catalog-aware, but irrelevant to this CTA.** It special-cases `motor_power_w` via `catalog_bound_motor_covers_power_w` — used only for architecture-progress display, never consulted by the ReasoningLayer path above. |

**Answer:** ReasoningLayer wins, via Continuity's rank-6 fallback. **Confirms and sharpens Hypothesis #3/#4 exactly**: it is a real dual contract — `param_present_for_architecture` (catalog-aware) and `missing_params_for_reason`/`_detect_missing_energy_params` (catalog-blind) answer "is `motor_power_w` satisfied?" differently, and the CTA-producing path uses the blind one. `catalog_bound_motor_covers_power_w` exists specifically to prevent asking the user to invent W for a verified-no-nameplate SKU (its own docstring, `project_closure.py:44-51`, names `emax_rs2205s_2300` as the exact motivating case) — but `ReasoningLayer._collect_suggested_actions` never calls it.

---

## 4. Gate 3.3 — Silent autonomy

`adapters/cli/main.py`, `render_response` (the generic `calcular`/`simular` text, distinct from `estado`'s `render_startup_context`):

- Calculate action line (`:442-443`): `autonomy_str = f", autonomía={round(autonomy_min,1)} min" if autonomy_min is not None else ""` — **fully silent** when null; no reason class, no reference to `energy_status`.
- Simulate action line (`:463-464`): identical pattern.
- The one existing autonomy-related warning, `autonomy_below_restriction` (`:472-478`), only fires when a numeric `autonomy_min` **was** computed and fell below the restriction — it has no branch for "restriction set, autonomy uncomputable." For this fixture, `parsed_constraints.autonomy_min=5.0` is a real, user-set target, and **neither `calcular` nor `simular` output says anything about it being unverifiable** — not a wrong number, an absent acknowledgment of the central ask.

**Contrast, same file:** the hover_energy block (`:349-356`, Phase 2.5) already renders a named negative for the equivalent situation — `"Energía hover (evidencia): unverifiable · fuera del rango del dataset ({selection_reason}) · sin hover_energy_autonomy_min"` — when `source_type=="unverifiable"`. That pattern already exists and works; the older calc/sim line simply never adopted it.

**Answer to the contract's question:** today it is an **honest omission with no named negative** — confirmed, not merely hypothesized (Hypothesis #6 confirmed). The smallest addition that does not invent minutes: when `calculations.autonomy_min is None` and `simulation.energy_status == "missing_energy_parameters"` (a field that already exists on the sim result, no new computation), append a short reason clause to the existing line — mirroring the already-proven hover_energy phrasing, not a new mechanism.

---

## 5. Gate 3.4 — Propulsion evidence suffix

`adapters/cli/main.py:310-322` (already quoted in the executive summary). The suffix is keyed on `resolution_type == "fallback_operating_point"` (`:316`) — a property of **which OP row the resolver matched**, not of BOM identity.

Two independent signals exist for "does the BOM show a catalog propeller":
- `propulsion_resolution.propeller_sku` (from the OP row itself) — `null` in this fixture, because the fallback row (`emax_rs2205s_2300`'s headline row) simply carries no propeller association on file.
- `design_properties.components.propellers.catalog_ref.sku` (BOM identity) — `"hq_5045_bn"` in this fixture, a real bound propeller.

The suffix reads today's `resolution_type` (resolver identity) and says **"sin hélice de catálogo"** even though BOM identity (the thing a user actually cares about — "did I pick a propeller") says otherwise. **Verified false for this exact fixture, not a hypothetical.**

**Recommendation (one sentence, per the contract's ask):** key the suffix on whether a catalog propeller is actually bound (BOM `propellers.catalog_ref` presence — already available in the same `build_startup_context` call, no new field), not on the resolver's own row-level `propeller_sku`; keep the underlying `fallback_operating_point`/`manufacturer_test`/etc. resolution-type label exactly as-is (★6 resolver contract, untouched) — this is copy-only, **not** a resolver policy change (C4 respected).

---

## 6. Gate 3.5 — Options for a future IC

**Recommendation: Option A.** Presentation + ranking only; `ASSEMBLY_READY`/ERF §11 untouched.

**File list for the future IC (not a patch — scope pointer only):**

| File | What Option A would touch |
|---|---|
| `src/jarvis/core/project_continuity.py` | Situation predicate (§2): add an energy-caveat clause to the `sim_status=="pass"` branch when `energy_status` isn't a real PASS. `next_useful_step`'s rank-6 fallback: nothing structural changes, but the label it forwards changes (see ReasoningLayer row). |
| `src/jarvis/core/reasoning_layer.py` | `_collect_suggested_actions`'s `missing_energy_parameters` branch (§3): consult `catalog_bound_motor_covers_power_w` before phrasing the CTA as "declarar motor_power_w" — when the motor is catalog-bound and genuinely lacks nameplate wattage, the CTA needs different wording (e.g. point at the honest gap — no autonomy claim possible for this SKU — rather than ask the user to invent a number). |
| `src/jarvis/core/project_closure.py` | `energy_model_honesty_note` (§7 below) — gate its firing, or adjust wording, so it doesn't imply a model ran when it didn't. |
| `src/jarvis/adapters/cli/main.py` | `calcular`/`simular` autonomy line (§4): add named-negative clause when `autonomy_min is None` and `energy_status=="missing_energy_parameters"`. Propulsion suffix (§5): re-key on BOM `catalog_ref`, not `resolution_type`. |
| `src/jarvis/core/orchestrator.py` | `build_startup_context`: no new fields needed — `energy_status`, `propulsion_resolution`, and BOM `catalog_ref` are all already threaded into ctx; Option A is copy/logic changes over existing data, not new plumbing. |

**Option B rejected for this report (not implemented, not authored as an IC target) — evidence recorded for the Engineer's future call, not adopted here:** `_energy_evidence` (`engineering_readiness.py:943-952`) computes `calculated = battery_capacity_wh is not None or autonomy_min is not None` — for this fixture, `battery_capacity_wh=148.0` alone satisfies `calculated=True`, and `validated = ctx.sim_status=="pass"` (the same global-sim boolean this session's earlier Phase 2.5 investigation already found is shared, uncritically, across 8 of 9 subsystems) is also True — so **Energy subsystem verdict is PASS today, independent of `autonomy_min` being null.** This is real, verified evidence that "SIMULATION PASS ≠ ENERGY MODEL CLOSED" (the product framing block) is *already true in code*, not just a slogan. Changing this would directly touch `ASSEMBLY_READY`'s own rollup (ERF §11) — **this is a C1 violation by definition, and I am not proposing it be done in this slice.** No stop-and-rewrite is triggered because Option A does not require touching this function — flagging Option B's exact mechanism only so a future, explicitly-authorized ERF revision doesn't have to re-derive it.

**Option C rejected:** no new persisted field is needed for any of §2-§5's fixes — every recommended change reads data that already exists on `ProjectState`/`latest_results` (C3 respected).

---

## 7. Additional finding (not in the contract's gate list, surfaced because it's adjacent and cheap to fix): `energy_model_honesty_note`

`project_closure.py:390-400` fires unconditionally whenever `parsed_constraints.autonomy_min is not None` — regardless of whether any energy calculation ever ran:

```python
if constraints.get("autonomy_min") is None:
    return None
return "Modelo energético simplificado: autonomía ≈ (Wh / W) × 60 — sin curva de descarga ni C-rating. Úsalo como orientación, no como certificación."
```

For this fixture, the note would render (`parsed_constraints.autonomy_min=5.0`) even though **zero energy calculation occurred** (`motor_power_w` is absent, `autonomy_min` is null) — the note's wording ("Úsalo como orientación") presumes a number exists to interpret. Confirms Hypothesis #5. Recommend (Option A scope, listed in §6's file table) gating this note on `calculations.autonomy_min is not None`, or rewording the null-autonomy case separately — a one-line, low-risk addition.

---

## 8. Gate 3.6 — Tests / probe risk

**Existing tests that pin the strings/predicates in scope (verified by grep, this session):**

| Behavior | Test file(s) | Risk shape |
|---|---|---|
| Situation string content (`build_project_continuity`'s own output) | `tests/test_project_continuity.py:57` | **Loose assertion** — `"PASS" in cont["situation"] or "gaps" in cont["situation"].lower()`, not an exact match. Adding an energy caveat clause to the PASS branch is low-risk against this specific test (it only checks for the substring "PASS", which would still be present). |
| `render_startup_context`'s rendering of a *given* situation dict | `tests/test_project_continuity.py:88-104` (`test_render_leads_with_continuity_block`) | Feeds a hand-built ctx dict — tests the *renderer*, not the *string producer*. Unaffected by changing `project_continuity.py`'s own predicate. |
| `motor_power_w`/`missing_energy_parameters` CTA and energy-param wiring | `tests/test_energy_params.py`, `tests/test_goal_planner.py`, `tests/test_system_definition_session.py`, `tests/test_composite_wizard_flow.py`, `tests/test_frame_component.py`, `tests/test_intent_resolver.py`, `tests/test_d4_param_gatekeeper.py` | Broad grep hits on the `motor_power_w` string generally — a future IC must audit each individually before touching `ReasoningLayer`'s CTA wording; not all of these necessarily assert the exact label text, but they're the search surface to check. |
| Propulsion evidence suffix / `fallback_operating_point` rendering | `tests/test_battery_catalog_bind_ux.py`, `tests/test_phase2_lookup_operating_point.py`, `tests/test_dse_motor_op_dual_truth.py`, `tests/test_requirements_closure.py`, `tests/test_propeller_catalog_bind_ux.py` | These assert on `resolution_type`/`fallback_operating_point` *values*, mostly at the resolver/bridge level (`propulsion_resolution` dict), not necessarily the CLI suffix string itself — a future IC must check whether any of them assert the literal `" (sin hélice de catálogo)"` text (this investigation did not find one in `estado`-rendering test form; the closest hits are on the underlying resolution data, not the rendered suffix). |
| `energy_model_honesty_note` | `tests/test_project_closure_v1.py` | Direct test of the function; a gating change must update whatever fixture currently expects it to always fire on `autonomy_min` constraint presence. |

**Suggested unit fixture for a future IC** (sketch only, not written here per the sign-off below): catalog-bind `emax_rs2205s_2300` (no `max_watts`) + `hq_5045_bn` propeller + a 4S battery with `battery_capacity_wh` set, run `calcular`/`simular` to real `sim.status=="pass"`/`autonomy_min=None`, then assert: (a) the CTA text does **not** ask the user to invent W (must not say "Declarar motor_power_w" verbatim once fixed — must reflect the catalog-bound-no-nameplate case), (b) the situation string does **not** say "Diseño validado" unconditionally without an energy caveat, (c) `calcular`/`simular` output names the missing-energy reason instead of silently omitting autonomy, (d) the propulsion suffix does not claim "sin hélice de catálogo" when `propellers.catalog_ref` is set. This mirrors the existing fixture almost exactly — a probe script driving this exact combo (mirroring `cli_probe_phase25_hover_energy.py`'s pattern) would be the natural regression lock for whichever IC implements Option A.

**ERF §11 impact: none**, confirmed — Option A does not touch `engineering_readiness.py`'s evidence/verdict functions (Option B's row in §6 is the only path that would, and it is explicitly not recommended here).

---

## Sign-off

No `src/` or test files were touched by this investigation. Only this report was written, plus the read-only fixture inspection (`workspace/autonomía-de-5min-c09442c25db0/state.json`, unmodified) and code reads cited above. `pyproject.toml` untouched, no version bump.
