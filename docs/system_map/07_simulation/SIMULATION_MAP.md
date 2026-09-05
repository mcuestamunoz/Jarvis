# 07 — Simulation

**Purpose.** `CalculationBundle` → feasibility verdict (`can_fly`, `safety_margin_ratio`, warnings). Pure, no I/O, no LLM.

**Inbound:** C-070 (from Calculation). **Outbound:** C-071 (to State, persisted), C-080/C-081 (to Continuity).

## Key modules

| Path | Role |
|---|---|
| `simulation/simulator.py` | `FeasibilitySimulator.evaluate(calculations, autonomy_threshold) -> SimulationResult` (also referenced as `FlightSimulator` in some call sites — same class, see note below). All flight/energy physics live directly in this module. |
| `simulation/flight_model.py` | **Empty file (0 bytes), zero imports anywhere in the codebase — SYS-MAP-003 correction, see `MISMATCHES.md` M-003.** Was incorrectly listed as an active "flight-physics sub-model" in SYS-MAP-002; the physics actually lives in `simulator.py` directly. |
| `simulation/energy_model.py` | **Empty file (0 bytes), zero imports anywhere — same correction, M-003.** Was incorrectly listed as an active "energy/autonomy sub-model" in SYS-MAP-002. |
| `suggestions/suggestion_engine.py` | `SuggestionEngine` — margin/ratio-threshold-based suggestions, consumed by `SimulateAction` and by `ReasoningLayer` |
| `actions/simulate.py` | `SimulateAction` — the `ActionRouter`-registered action |

## Important functions (Level 2)

- `FeasibilitySimulator.evaluate(calculations, autonomy_threshold) -> SimulationResult` (`:18`) — the single entry point.
- `SuggestionEngine.generate_suggestions(simulation, calculations) -> list[Suggestion]` — threshold constants (`HIGH_MARGIN_THRESHOLD=1.8`, `LOW_MARGIN_THRESHOLD=1.3`, `HIGH_TW_RATIO_THRESHOLD=1.6`) are a **second, independent** margin-threshold table from `goal_planner._prioritize_strategies`' own `1.15`/`1.5` cutoffs — both are legitimate (different purposes: general suggestions vs. payload-goal strategy ordering). **Resolved (Claim Hygiene IC, 2026-09-04):** Continuity's H5 fix did not pick a third numeric cutoff — `project_continuity.margin_claim_weak` reads `simulator._resolve_quality`'s existing `"risky"` band plus the simulator's own `low_margin`/`high_actuator_load`/`low_force_to_weight_ratio` warning codes directly, so a fourth independent threshold was avoided for this one purpose. The `suggestion_engine`/`goal_planner` pair above remains its own, still-unharmonized fragmentation — flagged, not resolved.
- `SimulateAction.run(parameters) -> dict` (`actions/simulate.py`) — load → resolve calculations → `simulator.evaluate` → `SuggestionEngine.generate_suggestions` → `ReasoningLayer.build` → `record_action` → `save_state`.

## Local state touched

None held directly — same pattern as Calculation, persistence goes through `09_state`.

## LLM

NO.

## Known issues owned by this subsystem

None directly (this subsystem's own output is correct and complete) — **C-081** (Continuity not reading `safety_margin_ratio`/`quality`/`warnings` in the PASS branch) was a `08_continuity` issue, not a Simulation one, and is now **closed** (Claim Hygiene IC, 2026-09-04 — see `08_continuity/CONTINUITY_MAP.md`). Simulation's own output was never the problem; it already computed and exposed the margin correctly throughout.

## Tests

`tests/test_energy_params.py`, `tests/test_phase_layer.py` (phase inference reads sim results), suggestion-specific tests under `tests/` (see `suggestion_engine` usage).
