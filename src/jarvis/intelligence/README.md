# `jarvis.intelligence` — Assistant platform home (scaffold + read-only retrieve + terminal canal)

**Buys:** [`B1-intelligence-scaffold`](../../../.jes/artifacts/implementation_contract_intelligence_scaffold_b1.md) (★ ACCEPT CLOSED @ `v0.6.1`) · [`B1-ontology-retrieve-r2`](../../../.jes/artifacts/implementation_contract_ontology_retrieve_r2_b1.md) (★ ACCEPT CLOSED @ `v0.6.2`) · [`B1-assistant-terminal-canal`](../../../.jes/artifacts/implementation_contract_assistant_terminal_canal_b1.md)
**Package:** `0.6.3` (tag `v0.6.3` on Engineer ACCEPT)
**Parent:** [`DC-assistant-placement`](../../../.jes/artifacts/design_contract_assistant_placement_b0.md) — ★ ACCEPT CLOSED

## Terminal canal (A3): `jarvis explain <query>`

`jarvis.intelligence.explain` wires a real CLI command (`jarvis explain
<query>` / `python -m jarvis.main explain <query>`) over A2 retrieve.
**Command-first, not chat**: resolves `query` as (1) frontmatter `id`,
(2) else exact `nombre`, (3) else a finite alias table
(`explain_aliases.EXPLAIN_ALIASES` — currently `c-rate`/`crate` →
`c-rate-de-bateria`, `op`/`operating point` →
`punto-de-operacion-vs-capacidad-intrinseca`, both verified `solid`
before seeding), else an honest miss (`No solid ontology note for: …`,
exit code 1 — never a fabricated note). On a hit, prints `nombre`, `id`,
repo-relative `path`, `[DEFINICION]`, `[INTUICION]`, an optional
`formula_citation` line, and — when `never_invents` is non-empty — an
explicit honesty line naming those craft quantities as catalog/Continuity's
job, never this explanation's. No LLM call, no embeddings/fuzzy rank
(the alias table is a fixed dict, not search), no `jarvis.core` import,
no `JarvisOrchestrator` construction, no `submit_command`.

## Retrieve (R2, read-only)

`jarvis.intelligence.ontology_retrieve` adds `retrieve_by_id(note_id)` /
`retrieve_by_nombre(nombre)` — exact lookup of one **`solid`** note in
`ontology/` by frontmatter `id` (or exact `nombre`), returning an
`OntologyCite`: `id`, `nombre`, `path`, `estado`, `jarvis_relevance`,
`never_invents`, `formula_citation`, and the extracted
`[DEFINICION]`/`[INTUICION]` body sections. A miss (unknown id, or a
note that is not `solid`) returns `None` — never a fabricated or
best-guess cite.

- **Read-only.** Every note is opened via `Path.read_text` only; this
  module contains no write API and never touches `library/`, the craft
  workspace, or `jarvis.core` (Continuity/orchestrator) state.
- **Exact lookup only.** No fuzzy matching, no embeddings, no vector
  search, no LLM ranking in this Buy.
- **Callers must respect `never_invents`.** Retrieve surfaces which
  craft quantities a note explicitly refuses to supply (`mass_g`,
  `power_w`, `thrust_gf`, `autonomy_min`, …) — it does not invent them
  either.
- **≠ terminal canal.** This is a library call, not a CLI/Board/Continuity
  prompt surface — wiring a canal is **A3**, a separate, later Buy.
- **≠ LLM answer synthesis.** No OpenAI/Anthropic/local LLM call
  anywhere in this module.
- Does **not** reuse or extend the empty `jarvis.knowledge.retriever`
  module — that surface stays untouched.

## What this package is

This is the **Assistant / intelligence column** home, per the placement
locked in `DC-assistant-placement` ★. It is where a future Assistant —
language/intent interpretation, skills, memory, reusable across
physical systems — will live, **separate from**:

- `jarvis.flight_software` — deterministic flight-control computation
- `jarvis.core` (Continuity/orchestrator) — craft engineering state machine
- MCU `native/` — firmware

## What this package is not (yet)

- **Scaffold ≠ Assistant shipped.** This package is importable and
  documented; retrieve exists as a library call (see above), but there
  is still no Assistant that decides, converses, or acts.
- **Retrieve ≠ RAG.** Exact `id`/`nombre` lookup only — no embeddings,
  no vector search, no ranking, no fuzzy match, no LLM in the loop.
  This package does not reuse the empty `jarvis.knowledge.retriever`
  module as a substitute retrieve surface.
- **Canal ≠ chat.** `jarvis explain` is one explicit subcommand, not a
  free-form "oye Jarvis" loop and not the `JarvisOrchestrator`
  chat/`--chat` path — those remain entirely separate code paths.
- **≠ voice.** No STT/TTS, no audio I/O.
- Does **not** call `jarvis.flight_software`, ESC, or any mixer.
- Does **not** decide or drive Continuity craft steps — no import of
  `jarvis.core` (orchestrator), no `submit_command`, no Safety gate
  traffic.
- Does **not** read or mutate `library/` or the craft workspace — vault
  reads are read-only (`Path.read_text` only, no write API anywhere in
  this package).

## Tip parent

Ontology explain epoch **CLOSED @ `v0.6.0`**
([close note](../../../.jes/artifacts/engineer_note_v0_6_0_ontology_epoch_close.md)).
Scaffold landed **`v0.6.1`**, retrieve landed **`v0.6.2`** (both ★
ACCEPT CLOSED). This canal Buy opens the next package/tag, `0.6.3` /
`v0.6.3`, on Engineer ACCEPT.

## Tests

- `tests/test_intelligence_scaffold_b1.py` (T1–T5): package imports
  cleanly, exists on disk under `src/jarvis/intelligence/`, never
  imports `jarvis.flight_software` or `jarvis.vehicle_profiles`, this
  README states the scaffold/not-retrieve honesty locks, and no source
  file in this package calls into Continuity/orchestrator (`jarvis.core`).
- `tests/test_ontology_retrieve_r2_b1.py` (T1–T7): retrieve works
  against the real vault (`c-rate-de-bateria`), returns a non-empty
  `definicion` and a non-empty `never_invents`, an unknown id returns
  `None` rather than raising or inventing a note, the package still has
  no forbidden imports, retrieve never writes the target note, and
  retrieve never imports/calls Continuity `submit_command` or writes
  craft state.
- `tests/test_assistant_terminal_canal_b1.py` (T1–T6): resolve yields a
  non-empty-`definicion` cite for `c-rate-de-bateria`, the seeded
  `c-rate`/`op` aliases resolve to the same note ids, an unknown query
  is an honest miss (`None` / exit 1, no invented note), formatted
  output includes the `never_invents` honesty line, `explain.py`/
  `explain_aliases.py` never import `jarvis.core` or call
  `submit_command`/construct `JarvisOrchestrator`, and neither module
  imports any LLM client — plus an actual `python -m jarvis.main
  explain …` subprocess smoke for both the hit and miss paths.
