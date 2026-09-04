# Engineer Ratification — CLI fail-routing coherence

**Date:** 2026-09-03  
**Authority:** Engineer  
**Decisions:** investigation `Procede`; IC `Procede` (same day, after JES closed R1–R5)

**Investigation contract:** [investigation_contract_cli_fail_routing_coherence.md](investigation_contract_cli_fail_routing_coherence.md)  
**Walk:** [engineer_cli_walk_fail_routing_coherence.md](engineer_cli_walk_fail_routing_coherence.md)  
**Revision:** [investigation_revision_cli_fail_routing_coherence.md](investigation_revision_cli_fail_routing_coherence.md)  
**IC:** [implementation_contract_cli_fail_routing_coherence.md](implementation_contract_cli_fail_routing_coherence.md)

## Investigation (earlier this day)

Authorized tracing of the failed CLI walk. Did **not** authorize production-code changes, a broad `orchestrator.py` refactor, D8 policy, or absorbing the core audit wholesale.

## Implementation (this turn)

Implement Shape A routing/copy only:

- frame class prompt in the **active wizard** (not only IDLE startup);
- Continuity must not claim thrust PASS when `can_fly` is not True;
- do not recommend `optimizar o simular` as the next action on sim FAIL;
- do not render FAIL as WARNING when Continuity already named the fail.

## Explicitly not this IC

- D8 / catalog ranking / range-only vs nominal (C-A1 — later investigation);
- reopening `ayúdame a elegir` motor picker for a D8-admitted SKU;
- new `status_type` enum;
- `orchestrator.py` split;
- ERF / simulator physics.

Claude implements the IC. JES reviews the report. No `src/` from JES.
