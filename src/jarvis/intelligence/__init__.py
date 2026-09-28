"""Assistant / intelligence platform column — scaffold only.

`B1-intelligence-scaffold` opens this package as the disk home for the
Assistant column locked by `DC-assistant-placement` (★ ACCEPT CLOSED):
Assistant lives in `jarvis.intelligence`, never inside `jarvis.core`
(Continuity), `jarvis.flight_software`, or MCU `native/`.

Scaffold @ `0.6.1` != Assistant shipped. This package does not read
`ontology/`, does not expose a cite API, does not call an LLM, and does
not import `jarvis.flight_software` or `jarvis.vehicle_profiles`
(test-enforced — see `tests/test_intelligence_scaffold_b1.py`). It does
not call into `jarvis.core` (Continuity/orchestrator) and produces no
Intent, no `submit_command`, no Safety gate traffic. Retrieve over the
ontology vault is a separate, later Buy (`B1-ontology-retrieve-r2`,
blocked on this Buy's Engineer ACCEPT) — this package deliberately does
not reuse `jarvis.knowledge.retriever` (also empty today) as its own
retrieve surface.

See `src/jarvis/intelligence/README.md` for the full honesty locks and
`.jes/artifacts/implementation_contract_intelligence_scaffold_b1.md`
for the authorizing Buy.

`B1-ontology-retrieve-r2` (package `0.6.2`) adds read-only retrieve:
`retrieve_by_id`/`retrieve_by_nombre` in `jarvis.intelligence.ontology_retrieve`
look up one `solid` note by frontmatter `id` (or exact `nombre`) and
return a small `OntologyCite` — identity/path/state metadata,
`never_invents`, and the extracted `[DEFINICION]`/`[INTUICION]`
sections. Exact lookup only: no fuzzy match, no embeddings, no LLM
ranking, no number synthesis. Still no CLI/Board/Continuity canal
(that is **A3**), still no LLM call, still no write path anywhere in
this package. See `ontology_retrieve`'s own module docstring.
"""

SCAFFOLD_STATUS = "stub"
RETRIEVE_STATUS = "r2"

from jarvis.intelligence.ontology_retrieve import (  # noqa: E402
    OntologyCite,
    retrieve_by_id,
    retrieve_by_nombre,
)

__all__ = [
    "SCAFFOLD_STATUS",
    "RETRIEVE_STATUS",
    "OntologyCite",
    "retrieve_by_id",
    "retrieve_by_nombre",
]
