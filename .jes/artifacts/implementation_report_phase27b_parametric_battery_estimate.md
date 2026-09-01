# Implementation Report — Phase 2.7-B Parametric / Estimative Battery Endurance Sweep

**Contract:** [`implementation_contract_phase27b_parametric_battery_estimate.md`](implementation_contract_phase27b_parametric_battery_estimate.md) (v0.2)
**Implementer:** Claude Code
**Base:** commit `fc46938` / tag `v0.3.5` / `checkpoint-phase25-hover-energy`
**Status:** Complete. Full suite **2071 passed, 0 failed** (2058 baseline + 13 new tests). New probe **4/4 PASS**. `cli_probe_phase25_hover_energy.py` **4/4 PASS**, `cli_probe_minimum_universe_combo.py` **3/3 PASS** — zero regression.

---

## 1. Files touched — matches §7 acceptance exactly

```text
src/jarvis/tools/electricity.py       | 146 ++++++++++++++++++++++++++++++++++
src/jarvis/core/calculation_engine.py |  61 +++++++++++++-
src/jarvis/core/orchestrator.py       |  26 ++++++
src/jarvis/adapters/cli/main.py       |  27 +++++++
src/jarvis/schemas/tool_schema.py     |   7 ++
tests/test_phase27b_loaded_endurance.py    (new, 13 tests)
scripts/cli_probe_phase27b_battery_endurance.py  (new, 4 steps)
```

**Not touched** (§7/§6 non-goals, confirmed): `library/baterias/_datos.json`, `library.py`, `electrical_compatibility.py`, `design_explorer.py` (a dedicated test statically greps its source for `battery_endurance` and asserts zero references), `simulation/energy_model.py`/`flight_model.py` (left empty, not revived).

---

## 2. What was implemented, mapped to the IC's locked sections

### §2 Physics — voltage-space evaluation, exactly as specified

`tools/electricity.py::estimate_loaded_endurance()` implements the three-branch order from §2 literally:

1. `V_full_loaded = V_oc_full − I×R`; if `< V_cutoff` → **infeasible** (diagnostic `soc_at_cutoff` may exceed 1, `endurance_min=None`, `stopping_condition=None`).
2. Else `V_empty_loaded = V_oc_empty − I×R`; if `> V_cutoff` → **sustainable**, `stopping_condition="nameplate_exhausted"`, `endurance_min = capacity_ah/i_load_a×60` (capped at the nameplate coulomb budget by construction — the branch condition itself guarantees cutoff is never reached inside `SOC∈[0,1]`).
3. Else → **sustainable**, `stopping_condition="voltage_cutoff"`, `SOC_cutoff` solved directly, `endurance_min = capacity_ah×(1−SOC_cutoff)/i_load_a×60`. The knife-edge case (`V_full_loaded == V_cutoff` exactly) falls into this branch and correctly evaluates to `SOC_cutoff=1.0`, `endurance_min=0.0` — verified live and by a dedicated test.

All seven §5.1 numeric test cases were hand-derived from this exact formula **before** writing any code, then verified to match after implementation — no discrepancies.

### §3 API — `ToolResult`-shaped, no invented schema

- `estimate_loaded_endurance(**kwargs) -> ToolResult`: uses the repo's real `ToolResult` (`{tool_name, inputs, outputs}` only, per `schemas/tool_schema.py`) — status lives in `outputs["outcome"] ∈ {refused, infeasible, sustainable}`, never a fictional `success`/`error` field.
- Validation order: non-finite/wrong-type inputs → `invalid_input`; scope not in `{pack, cell}` or `r_internal_scope != voltage_scope` → `scope_mismatch`; `i_load_a<=0`, `capacity_ah<=0`, `r_internal_ohm<0`, or `v_oc_full_v<=v_oc_empty_v` → `invalid_input`. **`r_internal_ohm==0` is valid** (tested explicitly).
- `estimate_loaded_endurance_sweep(points: list[dict[str, Any]]) -> list[ToolResult]`: no built-in grid, no dataclass/TypedDict, one point in → one `ToolResult` out, a refused point does not abort the rest (tested).
- `CalculationEngine.build()`: reads `parameters["battery_endurance_sweep"]` (missing/`None`/`[]`/`"[]"` → both bundle fields `None`, verified for all three forms). Envelope rows are **plain dicts** — `ToolResult.inputs` merged with `.outputs`, `source_type` **written** as `"assumed"` (never read off the caller's point), plus optional passthrough (`i_load_label`, `capacity_source`, `capacity_source_ref`) copied only when present on the *original* caller point dict, never invented. Every point's `ToolResult` is also appended to `tool_results` for auditability, matching this file's existing convention for every other intermediate calculation.
- `battery_endurance_assumption` JSON string: `sort_keys=True`, contains `model_class`, `source_type`, the required `ESTIMATIVE` label text, the `ocv_note`, and `n_points` — matches §3.3's schema exactly.

### §3.4 Schema

`CalculationBundle` gains `battery_endurance_envelope: list[dict[str, Any]] | None = None` and `battery_endurance_assumption: str | None = None`. No `battery_endurance_min` scalar (explicitly forbidden, §6) — the envelope is always list-shaped, even for a single point.

### §4 Presentation

- `orchestrator.py`: new `_battery_endurance_from_calculations()` helper mirrors `_hover_energy_from_calculations()`'s pattern exactly — reads from `latest_results["calculations"]` (not `current_parameters`, same architectural choice Phase 2.5/2.6 made and this report follows), returns `None` whenever no envelope exists. New `"battery_endurance"` ctx key in `build_startup_context()`, separate from `"hover_energy"`.
- `adapters/cli/main.py`: new block, positioned **after** the "Energía hover (evidencia)" line, **never** on the same line. Heading is exactly `"Autonomía estimada (ESTIMATIVO — no validado, no es tiempo de vuelo):"` — contains the required `ESTIMATIVO` token and the "not flight time" disclaimer in the same line, as the IC's §4.2 required. Each row states `R=<mΩ> <scope> (asumido) · I=<A> (hipótesis) · Vcut=<V> <scope>` before the outcome — `sustainable` rows show the minute figure (plus a `nameplate_exhausted` note when applicable), `infeasible` rows show `INVIABLE`, `refused` rows show `entrada inválida (<reason>)` (distinct from `INVIABLE`, per §4.2's "refused points... not as INVIABLE"). Never renders the forbidden phrase `"autonomía real"` — verified live by the probe's Step 3.

---

## 3. Live verification (this session)

```text
No sweep:        hover_energy_autonomy_min=1.3237 (Combo A, payload_kg=1.718) — bit-identical to Phase 2.5
                  battery_endurance_envelope=None, battery_endurance_assumption=None

With 2-point sweep (R=20mΩ / R=40mΩ, both pack/pack, I=68A, Vcut=14.0V, labeled i_load_label):
                  row[0]: outcome=sustainable, endurance_min=0.4301, source_type=assumed
                  row[1]: outcome=infeasible,  endurance_min=None,   source_type=assumed
                  hover_energy_autonomy_min still 1.3237 — UNCHANGED by the sweep's presence

CLI render:       contains "ESTIMATIVO" and "INVIABLE"; does NOT contain "autonomía real"
Bundle dump:      no key containing "p_battery" (case-insensitive) — Phase 2.6 boundary intact
```

All four numbers match the investigation report's own Gate D computation exactly (same formula, same inputs).

---

## 4. Tests added (13, all passing)

`tests/test_phase27b_loaded_endurance.py`:
`test_scope_mismatch_refused`, `test_negative_resistance_refused`, `test_zero_resistance_allowed`, `test_sustainable_voltage_cutoff_matches_investigation_numbers`, `test_higher_resistance_is_infeasible`, `test_optimistic_point_matches_investigation_numbers`, `test_nameplate_exhausted_never_exceeds_coulomb_budget`, `test_knife_edge_zero_minutes_at_soc_one`, `test_build_without_sweep_leaves_l1_unaffected`, `test_build_with_empty_or_null_sweep_leaves_l1_unaffected`, `test_build_with_two_point_sweep_populates_envelope`, `test_sweep_does_not_abort_on_refused_point`, `test_design_explorer_never_references_battery_endurance` — this last one statically greps `design_explorer.py`'s source for the string `battery_endurance` (zero hits), directly enforcing ★3.

L1-unaffected assertions use **semantic equality** (`test.autonomy_min == control.autonomy_min`, `test.hover_energy_autonomy_min == control.hover_energy_autonomy_min`) against a separately-built control bundle, per v0.2's changelog item 7 — not `model_dump()` byte identity (the new `None`-valued keys are expected and fine).

`scripts/cli_probe_phase27b_battery_endurance.py`: 4 steps, matching §5.2 exactly.

---

## 5. Deviations from the letter of the IC (none material)

None. Every numeric branch, validation rule, refuse/infeasible/sustainable distinction, opt-in gating, scope-mismatch rule, and presentation requirement was implemented literally as specified in v0.2. The one place requiring judgment — where to source `has_project`/`project_slug` for the probe's CLI-render step, since `render_startup_context()` requires them and the IC's own example ctx doesn't list them — was resolved by adding the two keys `render_startup_context` actually requires (discovered by reading its source), not by inventing extra product behavior.

---

## 6. Verification checklist (§7)

| # | Check | Result |
|---|---|---|
| 1 | Suite green including new tests | ✅ 2071/2071 |
| 2 | Probe 4/4 | ✅ |
| 3 | `git diff` touch set | ✅ exactly `electricity.py`, `tool_schema.py`, `calculation_engine.py`, `orchestrator.py`, `adapters/cli/main.py`, tests, probe — no library JSON, no DSE |
| 4 | L1 Combo A still ≈1.32 min without sweep | ✅ `1.3237`, semantic-unchanged |

**No version bump, no checkpoint, no tag** — per the IC, gated on Cursor review / Engineer request.
