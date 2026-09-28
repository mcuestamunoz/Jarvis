# `jarvis.intelligence` — Assistant platform home (scaffold)

**Buy:** [`B1-intelligence-scaffold`](../../../.jes/artifacts/implementation_contract_intelligence_scaffold_b1.md)
**Package:** `0.6.1` (tag `v0.6.1` on Engineer ACCEPT)
**Parent:** [`DC-assistant-placement`](../../../.jes/artifacts/design_contract_assistant_placement_b0.md) — ★ ACCEPT CLOSED

## What this package is

This is the **Assistant / intelligence column** home, per the placement
locked in `DC-assistant-placement` ★. It is where a future Assistant —
language/intent interpretation, skills, memory, reusable across
physical systems — will live, **separate from**:

- `jarvis.flight_software` — deterministic flight-control computation
- `jarvis.core` (Continuity/orchestrator) — craft engineering state machine
- MCU `native/` — firmware

## What this package is not (yet)

- **Scaffold ≠ Assistant shipped.** Today this package is importable
  and documented; it does nothing.
- **≠ ontology retrieve.** Reading `ontology/` vault notes, a cite API,
  or RAG over the spine is a separate, later Buy (**A2**,
  `B1-ontology-retrieve-r2`), blocked on this Buy's Engineer ACCEPT.
  The ontology vault **explains**; it does not ship here, and this
  package does not reuse the empty `jarvis.knowledge.retriever` module
  as a substitute retrieve surface.
- **≠ voice.** No STT/TTS, no audio I/O.
- Does **not** call `jarvis.flight_software`, ESC, or any mixer.
- Does **not** decide or drive Continuity craft steps — no import of
  `jarvis.core` (orchestrator), no `submit_command`, no Safety gate
  traffic.
- Does **not** read or mutate `library/` or the craft workspace.

## Tip parent

Ontology explain epoch **CLOSED @ `v0.6.0`**
([close note](../../../.jes/artifacts/engineer_note_v0_6_0_ontology_epoch_close.md)).
This scaffold opens the next package/tag, `0.6.1` / `v0.6.1`, on
Engineer ACCEPT.

## Tests

`tests/test_intelligence_scaffold_b1.py` (T1–T5) enforces: the package
imports cleanly, exists on disk under `src/jarvis/intelligence/`, never
imports `jarvis.flight_software` or `jarvis.vehicle_profiles`, this
README states the scaffold/not-retrieve honesty locks, and no source
file in this package calls into Continuity/orchestrator (`jarvis.core`).
