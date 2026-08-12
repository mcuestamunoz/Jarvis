# 06 — Calculation

**Purpose.** `current_parameters` → physical results. Pure, no I/O, no LLM.

**Inbound:** C-050/C-054 (from Iteration), C-016 (from ActionRouter's `CalculateAction`). **Outbound:** C-070 (to Simulation).

## Key modules

| Path | Role |
|---|---|
| `core/calculation_engine.py` | `CalculationEngine.build(current_parameters) -> CalculationBundle` |
| `core/component_resolver.py` | `resolve_propulsion_parameters(components) -> PhysicalOverride` — declarative components → physical override, bridges D6/U2 |
| `tools/aerodynamics.py`, `tools/electricity.py`, `tools/mechanics.py` | Pure physics/data helper functions consumed by the engine and by `component_resolver` (verified importers) |
| `tools/materials.py`, `tools/math_utils.py` | **Empty files (0 bytes), zero imports anywhere — SYS-MAP-002 incorrectly listed these as consumed. Correction: SYS-MAP-003, `MISMATCHES.md` M-003.** |
| `actions/calculate.py` | `CalculateAction` — the `ActionRouter`-registered action; loads state, calls the engine, persists |

## Important functions (Level 2)

- `CalculationEngine.build(current_parameters) -> CalculationBundle` (`:34`) — the single entry point; everything downstream (Simulation, Continuity's `derive_physical_requirements`) reads its output, never recomputes physics itself.
- `component_resolver.resolve_propulsion_parameters(components) -> PhysicalOverride` (`:73`) — reconciles declarative component data (from `design_properties.components`) with `current_parameters`, respecting the documented invariant "user input beats component inference" (`system_architecture_catalog.py`).
- `CalculateAction.run(parameters) -> dict` (`actions/calculate.py`) — load → `CalculationEngine.build` → `save_calculation` (workspace artifact) → `record_action` → `save_state`.

## Local state touched

None held by this subsystem itself — it reads `ProjectState.current_parameters` and returns a `CalculationBundle`; persistence is the caller's (`CalculateAction`'s) responsibility, via `09_state`.

## LLM

NO — no LLM import anywhere in this subsystem.

## Known issues owned by this subsystem

None — this is one of the fully 🟢 subsystems (FLOW-005).

## Tests

`tests/test_energy_params.py`, `tests/test_u1_battery_mass.py`, `tests/test_u2_propeller_bridge.py`, plus calculation assertions embedded across most orchestrator-level tests (calc is exercised indirectly whenever a test drives simulate/iterate to completion).
