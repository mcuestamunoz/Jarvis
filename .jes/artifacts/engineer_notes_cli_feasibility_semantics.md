# Engineer Interface notes — CLI feasibility semantics

**Not an investigation report.** Cursor wrote these after the field session.  
**Official report:** Claude Code must write [investigation_report_cli_feasibility_semantics.md](investigation_report_cli_feasibility_semantics.md) per the contract.

**Contract:** [investigation_contract_cli_feasibility_semantics.md](investigation_contract_cli_feasibility_semantics.md)

Claude: treat every claim below as a **hypothesis**. Verify or refute with file:line. Do not paste this document as the report.

---

## Hypotheses (unverified until Claude’s report)

1. Calc/sim on `workspace/autonomía-de-5min-c09442c25db0` has `autonomy_min: null`, `energy_status: missing_energy_parameters`, `hover_energy_autonomy_min: null` — physically honest for this SKU/HOLD/fallback; the failure is **claim language**.

2. Continuity situation upgrades from “Física orientativa en PASS” to “Diseño validado en simulación (PASS)” when BOM gaps clear, **not** when energy/hover evidence appears. Source to check: `project_continuity.py` situation block.

3. FN-005 `catalog_bound_motor_covers_power_w` does **not** fire after motors are BOM-complete. Post-4/4 CTA “Declarar motor_power_w” is hypothesized to win via **ReasoningLayer** `missing_energy_parameters` → Continuity `suggested_action` branch when sim PASS and BOM complete.

4. `MISSING_ENERGY_PARAMETERS` still lists `motor_power_w`; `param_present_for_architecture` covers W for architecture progress when SKU-bound, but `missing_params_for_reason` does not — dual contract.

5. `energy_model_honesty_note` always emits L0 `(Wh/W)×60` when `autonomy_min` constraint exists, even if L0/L1/L2 did not run.

6. Hover/ESTIMATIVO CLI blocks are omitted (not a named negative) when `hover_energy_resolution` is null.

7. CLI suffix `" (sin hélice de catálogo)"` keys on `resolution_type == fallback_operating_point`, not BOM `catalog_ref`.

8. Option A (copy/ranking only, ERF untouched) is the slice that matches product constraints C1–C5. Option B (Energy PASS) and C (persisted ladder) should be rejected **unless** Claude’s evidence forces a stop-and-rewrite of C1.

---

Cursor does not implement this slice. After Claude’s report + Cursor review + Engineer ★, Cursor writes an Implementation Contract **for Claude**.
