# Understanding — Guided Propulsion Acquisition

**Date:** 2026-08-08  
**Cycle:** FN-010 / FN-008 / FN-009 (closed)

## Problem cluster

Live CLI create of “levantar 3,5 kg con autonomía 40 min” exposed three coupled gaps:

1. Mission autonomy lived only in free-text `objective`; `restrictions = ninguno` wiped `parsed_constraints`.
2. Detailed create asked for internal physics knobs (`structure_mass_factor`, `safety_factor`) with broken Enter defaults.
3. After motors were declared, pending `per_motor_max_thrust_n` was treated as a raw user number; “ayúdame a elegir el motor” did not enter assisted acquisition.

## Design stance (unchanged)

- Deterministic writers / resolvers own physics.
- Catalog assist proposes; user confirms; no invented SKUs.
- Continuity stays honest about provisional thrust until battery mass enters.

## Non-goals

- Conversation Engine
- Full propulsion sizing solver
- Orchestrator structural refactor
