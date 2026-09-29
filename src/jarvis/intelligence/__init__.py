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

`B1-assistant-explain-task` (T0, package `0.6.8`) — per
`DC-assistant-first-task` (★ CLOSED) — adds the first on-disk Assistant
**Task** emission: `jarvis.intelligence.assistant_task` classifies an
`Intent` (`jarvis.capabilities.intent.Intent`) into a
`Task(required_capability_ids=["ontology.explain"])`, or refuses
honestly, for the single `explain_concept` kind. Fulfillment reuses A3's
`explain.py` unchanged. `jarvis.core.orchestrator`'s chat-explain branch
(A7) now calls this seam instead of holding its own parallel
resolve+format copy — the Assistant classifies/fulfills, the
orchestrator is ingress only. See `assistant_task`'s own module
docstring; not re-exported through this package's own `__all__` (same
convention as `explain`/`explain_maps`/`continuity_cite` — import the
submodule directly).

`B1-assistant-defer-continuity` (T1, package `0.6.9`) — per
`DC-assistant-defer-continuity` (★ CLOSED) — adds a **second** Task
kind to `assistant_task.py`: `defer_to_continuity`, requiring
`engineering.continuity`, classified from a finite, explicit phrase
table (`jarvis.config.CONTINUITY_DEFER_PHRASES`, hand-synced to
`IntentResolver.STATUS_PATTERNS`) and fulfilled entirely by `core/`'s
existing `_handle_project_status()` — this package still never
formats a Continuity body and still never imports
`jarvis.core.intent_resolver`/`jarvis.core.project_continuity`. An
explain-shaped line always wins over a Continuity-shaped one for the
same turn.
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
