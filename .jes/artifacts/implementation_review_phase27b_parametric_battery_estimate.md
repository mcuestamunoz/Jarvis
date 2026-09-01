# Implementation Review — Phase 2.7-B Parametric / Estimative Battery Endurance Sweep

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES) — **independent code + test verification** (not report paraphrase)  
**Contract:** [implementation_contract_phase27b_parametric_battery_estimate.md](implementation_contract_phase27b_parametric_battery_estimate.md) **v0.2**  
**Report:** [implementation_report_phase27b_parametric_battery_estimate.md](implementation_report_phase27b_parametric_battery_estimate.md)  
**Base:** commit **`fc46938`** · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

## Verdict

**PASS WITH NOTES**

IC v0.2 is implemented in the right layers, with L1/L2 split intact. Paper numbers match Gate D. DSE / P26 / catalog / `P_battery` untouched. Notes are product-dormancy and probe-surface, not formula errors.

No checkpoint / tag unless Engineer asks.

---

## Review methodology (what was actually verified)

| Step | Action | Result |
|---|---|---|
| 1 | Full suite (reviewer re-run) | **2071 passed, 0 failed** |
| 2 | `tests/test_phase27b_loaded_endurance.py` | **13/13** |
| 3 | `scripts/cli_probe_phase27b_battery_endurance.py` | **4/4** |
| 4 | `scripts/cli_probe_phase25_hover_energy.py` | **4/4** — L1 Combo A still 1.3237 min |
| 5 | `git diff fc46938 -- src/` | **5 files only:** `electricity.py`, `calculation_engine.py`, `tool_schema.py`, `orchestrator.py`, `adapters/cli/main.py` |
| 6 | Forbidden paths | `design_explorer.py`, `electrical_compatibility.py`, `library/`, `simulation/` → **empty diff** |
| 7 | Independent Gate D arithmetic | 20 mΩ → 0.4301; 40 mΩ infeasible; optimistic 1.51875; Vcut=10 → 1.3235 nameplate cap |
| 8 | Defaults / I auto-fill | **No** Voc/R/I constants in L2 code; `motor_hover_current_a` not written into sweep |
| 9 | CLI forbidden copy | No `autonomía real`, `usable Wh`, `P_battery`, M3/IR ranking in `main.py` |

---

## Contract checklist (IC v0.2)

| Criterion | Verified | Evidence |
|---|---|---|
| Voltage-space branches (infeasible / nameplate_exhausted / voltage_cutoff) | **Pass** | `electricity.py` `v_full_loaded < v_cutoff` → infeasible; `v_empty_loaded > v_cutoff` → cap `C/I×60`; else interpolate; knife-edge `endurance_min=0` |
| `R < 0` refuse; `R == 0` allowed | **Pass** | tests `test_negative_resistance_refused`, `test_zero_resistance_allowed` |
| ★★13 scope mismatch refuse, no `× cells` | **Pass** | pack vs cell → `reason=scope_mismatch` |
| `ToolResult` `{tool_name, inputs, outputs}` only | **Pass** | `outputs.outcome` ∈ `{refused, infeasible, sustainable}` |
| Sweep `list[dict]`; refused point does not abort | **Pass** | `estimate_loaded_endurance_sweep`; `test_sweep_does_not_abort_on_refused_point` |
| Opt-in: no sweep → envelope/assumption `None`; L1 semantic unchanged | **Pass** | unit tests + probe Step 1/2 (L1 still 1.3237 **with** sweep present) |
| Envelope `source_type` **written** `"assumed"` | **Pass** | `calculation_engine.py` `row["source_type"] = "assumed"`; passthrough keys only if present on the point |
| Bundle: envelope + assumption JSON; **no** scalar `_min` | **Pass** | `tool_schema.py`; grep `battery_endurance_min` → 0 in `src/` |
| ★3 DSE does not read L2 | **Pass** | `git diff` empty; `_score_candidate` still `sim.autonomy_min`; static test greps source |
| CLI after hover; `ESTIMATIVO`; `INVIABLE`; refused ≠ INVIABLE | **Pass** | `main.py:335-354`; heading matches required phrase; `entrada inválida` for refuse |
| No `P_battery`; no catalog R/OCV; no `energy_model.py` revival | **Pass** | diffs + probe Step 4 |
| ★5 no “IR > M3” UX | **Pass** | CLI block has no M3 / ranking copy |

---

## Harmony with prior code

```text
L1  hover_energy_autonomy_min   = nameplate Wh / P_motor_input   (unchanged)
L2  battery_endurance_envelope  = caller sweep, ESTIMATIVE       (new, opt-in)
DSE scores sim.autonomy_min     = L1 path                        (unchanged)
```

`calculate_autonomy_min` body is unchanged. Hover path still interpolates OP and feeds W into that function. L2 is a sibling call after energy resolution in `build()`, gated on `parameters["battery_endurance_sweep"]`.

Phase 2.5 probe 4/4 confirms Combo A L1 was not relabeled or replaced.

---

## Notes (non-blocking)

### N1 — L2 is engine-ready, conversation-dark

Nothing in the product turn writes `battery_endurance_sweep` into `current_parameters`. That matches the IC (no default grid, ★2 no silent `I`). Consequence: a normal `estado` / calculate will **not** show the ESTIMATIVE block until a caller (test, probe, or a later IC) supplies the sweep. Not a miss of v0.2; Engineer should not expect the line to appear in CLI by itself.

### N2 — Probe Step 3 hits the renderer, not a full calculate→estado loop

Step 3 builds a synthetic ctx for `render_startup_context`. Orchestrator wiring (`_battery_endurance_from_calculations` in `build_startup_context`) is correct by inspection. Full-loop CLI with a persisted sweep is untested and unused until N1 has a writer.

### N3 — Malformed sweep JSON is treated as “no sweep”

Invalid JSON → `(None, None, [])`, same as missing. Honest and L1-safe. If a later writer persists sweep as a string, a parse error will be silent rather than `refused`. Acceptable for v1.

### N4 — Report vs review

Implementer report’s file set, counts (2071 / 13 / 4), and Gate D numbers **match** this review’s re-run. No contradiction found.

---

## Not done (correctly)

- Checkpoint / version bump  
- Catalog JSON / DSE / ERF-2 / P_battery  
- Default Voc 16.4/13.2 or default R/I in `electricity.py`

---

## Next (Engineer)

Implementation is **acceptable**. Optional: checkpoint when you want it frozen. Product visibility of L2 is a **separate** IC (who supplies the sweep). P26 / P27-A validated path stay frozen.
