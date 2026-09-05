# Implementation Report — Claim hygiene under ASSEMBLY READY

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_claim_hygiene_assembly_ready.md](implementation_contract_claim_hygiene_assembly_ready.md)
**Baseline:** tag `v0.3.6` / commit `f70b278` · suite closed at 2150

---

## Files changed

- `src/jarvis/core/project_continuity.py` — new `margin_claim_weak(sim)` predicate + `_MARGIN_WEAK_WARNING_CODES` / `_MARGIN_WEAK_SITUATION` constants; new situation branch inserted between the autonomy-undemonstrated guard and the plain `elif sim_status == "pass":` branch (§2.1).
- `src/jarvis/core/orchestrator.py` — `build_startup_context` now imports `margin_claim_weak` and adds one thin `"margin_claim_weak"` boolean to its return dict, computed once from the already-bound `simulation` dict (§2.4 preferred option).
- `src/jarvis/adapters/cli/main.py` — `_humanize_next_useful_why` helper (WARNING_SHORT → WARNING_MESSAGES → verbatim) applied to the `Por qué:` line in `render_startup_context` (§2.3); `_render_readiness_block` takes a new `margin_claim_weak` kwarg (default `False`, backward compatible) and appends the locked `NOTE:` line only when `overall == "ASSEMBLY_READY"` and the flag is true (§2.4); its caller now passes `ctx.get("margin_claim_weak")`.
- `tests/test_project_continuity.py`, `tests/test_engineering_readiness_cli.py`, `tests/test_engineering_readiness_subsystems.py` — new tests (below).

No edits to `simulator.py`, `engineering_readiness.py`'s gap catalog / `_derive_subsystem_verdict` / `_derive_overall`, catalog JSON, or `prop_energy_block_closure` wiring.

## Behavior changed

- **Continuity situation:** PASS + `quality=="risky"` or an active `low_margin`/`high_actuator_load`/`low_force_to_weight_ratio` warning now reads *"Comprobación de empuje: PASS. Margen ajustado — el diseño no está validado con reserva cómoda."* instead of *"Diseño validado en simulación (PASS)..."*. PASS + good/acceptable with no such warning is byte-identical to before (verified by regression test and the untouched autonomy branches).
- **CLI `Por qué:` line:** known warning codes (e.g. `low_margin`) now render as their short human label (`margen ajustado`) instead of the raw code; unrecognized strings render verbatim, unchanged.
- **CLI readiness block:** `PROJECT STATUS: ASSEMBLY READY` now gets one additional `NOTE: margen ajustado — ASSEMBLY READY no implica reserva cómoda.` line when the backing simulation is margin-weak. `NOT ASSEMBLY READY` output and PASS-without-warning `ASSEMBLY READY` output are unchanged.
- **Not changed:** `ASSEMBLY_READY`/`NOT_ASSEMBLY_READY` eligibility, all 9 subsystem verdicts, gap types, `autonomy_below_restriction` handling, PhaseLayer suppression (FN-002 stays), `prop_energy_block_closure` wiring.

## Tests added/updated

- `test_project_continuity.py`: `test_situation_margin_weak_never_says_diseno_validado`, `test_situation_high_actuator_load_never_says_diseno_validado`, `test_situation_diseno_validado_unchanged_for_pass_good_no_warnings`.
- `test_engineering_readiness_cli.py`: `test_cli_note_shown_when_assembly_ready_and_margin_claim_weak`, `test_cli_note_absent_when_assembly_ready_and_margin_not_weak`, `test_cli_note_absent_when_margin_claim_weak_key_missing`, `test_cli_note_absent_when_not_assembly_ready_even_if_margin_weak`, `test_cli_humanizes_next_useful_why_for_known_warning_code`, `test_cli_leaves_unknown_next_useful_why_verbatim`.
- `test_engineering_readiness_subsystems.py`: `test_assembly_ready_true_when_pass_but_quality_risky` (ERF regression smoke — confirms this IC does not flip `ASSEMBLY_READY`).

## Tests executed

- Targeted: `pytest tests/test_project_continuity.py tests/test_engineering_readiness_cli.py tests/test_engineering_readiness_subsystems.py tests/test_engineering_readiness_continuity.py -q` → 41 passed.
- Full suite: `pytest -q` → **2160 passed** (2150 baseline + 10 new tests), zero failures, zero skipped, zero weakened.

## Residual risks / documented debt

- **N2 (per investigation review):** `PhaseLayer.infer` still independently computes `phase == "physical_validation"` for `quality in ("fail","risky")`, and `render_startup_context` still suppresses the phase line whenever `continuity.situation` is present (FN-002, unchanged). The fixed situation string now agrees in substance with PhaseLayer's verdict, but the two authorities remain structurally separate — left as documented debt for a later thread, per N2.
- **N4 / B4 second half:** `prop_energy_block_closure` ("evidencia débil") is still not wired into Continuity's situation branch — a project can show the fixed margin-honest situation while a separate `BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia débil` line renders independently below it. Named as a separate follow-up IC, not bundled here (per B4 split).
- Four independent "low margin" threshold constants (`simulator.py:13`, `reasoning_layer.py:19`, `suggestion_engine.py:7`, inline literals in `goal_planner.py`) remain unharmonized — cited, not touched, per locked constraints.
