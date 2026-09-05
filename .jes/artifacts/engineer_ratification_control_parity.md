# Engineer Ratification — Control parity (second knowledge thread)

**Date:** 2026-09-04  
**Authority:** Engineer  
**Decision:** After claim hygiene CLOSED, open **control parity** as the next
knowledge/block-parity thread.

**Prior closed:** claim hygiene B4 margin slice — suite **2160** ·
[implementation_review_claim_hygiene_assembly_ready.md](implementation_review_claim_hygiene_assembly_ready.md)

**Phase plan (Engineer):** claim hygiene → **control parity** → close
knowledge/block-parity phase → new feature cycle.

## Locked stance

1. **Investigation Contract required** — Know / Claim / Measure / Buy before any
   IC or `src/`.
2. A **sensor / FC catalog is not** the default Buy. Catalog may appear in the
   report only if Buy explicitly recommends it **after** claim language is locked
   — and even then as a separate later IC, not this investigation's deliverable.
3. **No control physics** (loop rates, PID, sensor fusion, failsafe models).
4. Claim hygiene residuals (N2 PhaseLayer, N4 weak-OP) are **not** this thread.

## Authorized next artifact

[investigation_contract_control_parity.md](investigation_contract_control_parity.md)

No Implementation Contract until investigation review + Engineer ★ on the
control claim matrix / Buy.
