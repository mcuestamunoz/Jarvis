# `jarvis.intelligence` — Assistant platform home (scaffold + read-only retrieve + terminal canal + explain maps + Continuity cite + chat intercept + topics expand + Assistant Task seam + Continuity defer)

**Buys:** [`B1-intelligence-scaffold`](../../../.jes/artifacts/implementation_contract_intelligence_scaffold_b1.md) (★ ACCEPT CLOSED @ `v0.6.1`) · [`B1-ontology-retrieve-r2`](../../../.jes/artifacts/implementation_contract_ontology_retrieve_r2_b1.md) (★ ACCEPT CLOSED @ `v0.6.2`) · [`B1-assistant-terminal-canal`](../../../.jes/artifacts/implementation_contract_assistant_terminal_canal_b1.md) (★ ACCEPT CLOSED @ `v0.6.3`) · [`B1-explain-maps-expand`](../../../.jes/artifacts/implementation_contract_explain_maps_expand_b1.md) (★ ACCEPT CLOSED @ `v0.6.4`) · [`B1-continuity-explain-cite-r3`](../../../.jes/artifacts/implementation_contract_continuity_explain_cite_r3_b1.md) (★ ACCEPT CLOSED @ `v0.6.5`) · [`B1-chat-explain-intercept`](../../../.jes/artifacts/implementation_contract_chat_explain_intercept_b1.md) (★ ACCEPT CLOSED @ `v0.6.6`) · [`B1-continuity-explain-topics-expand`](../../../.jes/artifacts/implementation_contract_continuity_explain_topics_expand_b1.md) (★ ACCEPT CLOSED @ `v0.6.7`) · [`B1-assistant-explain-task`](../../../.jes/artifacts/implementation_contract_assistant_explain_task_b1.md) (★ ACCEPT CLOSED @ `v0.6.8`) · [`B1-assistant-defer-continuity`](../../../.jes/artifacts/implementation_contract_assistant_defer_continuity_b1.md)
**Package:** `0.6.9` (tag `v0.6.9` on Engineer ACCEPT)
**Parent:** [`DC-assistant-placement`](../../../.jes/artifacts/design_contract_assistant_placement_b0.md) · [`DC-assistant-first-task`](../../../.jes/artifacts/design_contract_assistant_first_task_b0.md) · [`DC-assistant-defer-continuity`](../../../.jes/artifacts/design_contract_assistant_defer_continuity_b0.md) — all ★ ACCEPT CLOSED

## Continuity defer seam (T1): second Task kind, fulfilled entirely by `core/`

`B1-assistant-defer-continuity` adds `defer_to_continuity`, the
**second** Assistant Task kind (`DC-assistant-defer-continuity`, ★
CLOSED). Classify, don't decide:

```text
Intent (raw_text)
   ↓
try_defer_to_continuity_task  →  Task(required_capability_ids=["engineering.continuity"]) | None
   ↓ (if Task)
core/orchestrator._handle_project_status()   ← existing, already-LLM-free; unchanged
```

- **`CAPABILITY_ENGINEERING_CONTINUITY = "engineering.continuity"`**, **`TASK_KIND_DEFER_TO_CONTINUITY = "defer_to_continuity"`** — finite strings, same grain as T0's `ontology.explain`.
- **Phrase table is a hand-copy, not an import.** `jarvis.config.CONTINUITY_DEFER_PHRASES` is a manually-synced copy of `IntentResolver.STATUS_PATTERNS`' own string values as of tip `v0.6.8` — `assistant_task.py` never imports `jarvis.core.intent_resolver` (or `jarvis.core.project_continuity`); only the finite phrase *strings* cross that boundary, copied by hand into a leaf config module. A sync test (`tests/test_assistant_defer_continuity_b1.py` T5) asserts every `STATUS_PATTERNS` entry is present in the copy, so the two tables can't silently drift.
- **Exact-phrase match, deliberately narrower than `IntentResolver`'s own matching.** `IntentResolver._looks_like_status_query` does a word-boundary *substring search* over an entire sentence; `try_defer_to_continuity_task` requires the **whole** normalized `raw_text` to equal one table entry. A status-shaped sentence that isn't an exact match still reaches the existing, unaffected Continuity/status path further down `_handle_user_text_inner` — this seam only adds an earlier, zero-LLM fast path for a strict subset, it narrows nothing that already worked.
- **Explain always wins.** A line that is both explain-shaped and would otherwise match a status phrase (e.g. `"explain estado"`) resolves as `explain_concept` — checked twice: the orchestrator's own call order (explain branch runs first and returns), and `try_defer_to_continuity_task`'s own internal guard (refuses any explain-shaped `intent.raw_text` outright, so direct/test callers get the same precedence without relying on call order).
- **`jarvis.intelligence` never formats a Continuity body.** On a Task, the orchestrator calls the exact same `_handle_project_status()` every other Continuity-status call site already uses — same dict shape, same UX, same `build_startup_context` under the hood. No second "fake Continuity" formatter anywhere in this package.
- **Wizard soft-interrupts intentionally left alone.** Existing branches that already call `_handle_project_status()` directly (6+ call sites) are unmodified this Buy — only the `_handle_global_commands` global-command path is wired to classify through the Assistant (IC §0 row 9's explicit, narrower mandatory-wire scope).
- Fences unchanged: `assistant_task.py` still never imports `jarvis.core`/`jarvis.flight_software`/`jarvis.vehicle_profiles` (now also explicitly never `jarvis.core.intent_resolver`); `project_continuity.py` still never imports `jarvis.intelligence`.

## Assistant Task seam (T0, ★ ACCEPT CLOSED @ `v0.6.8`): the Assistant classifies, never a second brain

`B1-assistant-explain-task` is the first on-disk `Task` emission per
`DC-assistant-first-task` (★ CLOSED): `jarvis.intelligence.assistant_task`
classifies an `Intent` (`jarvis.capabilities.intent.Intent`, reused
as-is — no forked type) into a `Task` requiring one capability string,
or refuses honestly. This Buy shipped exactly one kind (a second,
`defer_to_continuity`, landed with T1 — see above):

```text
Intent (raw_text)
   ↓
try_explain_concept_task  →  Task(required_capability_ids=["ontology.explain"]) | None
   ↓ (if Task)
fulfill_ontology_explain  →  A3 cite text (or honest miss / --list|--rung redirect)
```

- **`CAPABILITY_ONTOLOGY_EXPLAIN = "ontology.explain"`**, **`TASK_KIND_EXPLAIN_CONCEPT = "explain_concept"`** — finite strings, not a capability-registry product (C1's registry stays empty; this is not that Buy).
- **Match grain is identical to A7**: `_extract_explain_query` reuses `jarvis.config.CHAT_EXPLAIN_PREFIXES` — one shared prefix table, not a second copy. No bare-id/craft-phrase steal.
- **`--list`/`--rung` get no Task** — explain-shaped but nothing is actually being explained, so claiming `ontology.explain` would be a fake capability claim (IC §0 row 6). `fulfill_ontology_explain` still gives the same honest terminal-redirect A7 always did; still zero LLM.
- **A7's orchestrator branch now calls this seam** (`handle_explain_intent`) instead of holding its own parallel resolve+format copy — `_handle_chat_explain` (the old A7-only method) is gone; `_handle_global_commands` builds a `TerminalIntentAdapter`-parsed `Intent` and asks the Assistant. Zero user-visible behavior change, zero LLM change — re-proven by re-running every A7 test unmodified against the new path.
- **`jarvis explain` (CLI, A3)** was deliberately left calling `resolve_explain_query`/`format_explain_cite` directly rather than routed through `fulfill_ontology_explain` — both already call the identical two underlying functions, so cite-text drift is structurally impossible either way, and the CLI's own exit-code/stderr contract (miss → stderr + exit 1, tested since A3) would have needed re-deriving hit/miss a second time to preserve if routed through the string-only `fulfill_ontology_explain` — a redundant indirection for zero benefit. IC §0 row 8 allows this ("either OK if cite text stays identical").
- Fences unchanged from every prior Buy: `assistant_task.py` never imports `jarvis.core`/`jarvis.flight_software`/`jarvis.vehicle_profiles`; `project_continuity.py` still never imports `jarvis.intelligence`.

## Topics expand (A8, ★ ACCEPT CLOSED @ `v0.6.7`): `current` now tags on a real signal

`B1-continuity-explain-topics-expand` wires the `current` row of
`CONTINUITY_TOPIC_MAP` — seeded since R3 but deliberately left untagged
because no distinguished signal existed then — to a real one:
`project_continuity._explain_topics_for_continuity` gained an
`op_current_present: bool` kwarg, set at the same post-ranking call
site as every other topic input from
`current_parameters["motor_op_current_a"] is not None` (the identical
field the CLI's own "OP eléctrico" line already surfaces via
`_motor_op_electrical_from_params`). **Not** tagged from watts-recovery
activity or a generic `energy_model_note` alone — only from that one
distinguished field. Same fence, same call-site discipline as R3: still
computed strictly after `next_useful_step`/`next_useful_why`, still
zero new `project_state` reads beyond that one field, still zero
`jarvis.intelligence` import in `project_continuity.py`.

## Chat intercept (A7, ★ ACCEPT CLOSED @ `v0.6.6`; refactored onto the Assistant Task seam by T0): `explain` works inside `--chat`, no LLM

`B1-chat-explain-intercept` extends
`JarvisOrchestrator._handle_global_commands` (`core/orchestrator.py`) —
the **same** intercept point escape words and `nuevo` already use, run
as the very first check in `_handle_user_text_inner`, strictly before
any LLM call. A line starting with `jarvis explain ` or `explain `
(exact prefix + required space, casefold) never reaches the LLM on that
turn. **As of T0**, the mechanism is: a cheap local prefix probe (same
`CHAT_EXPLAIN_PREFIXES` table), then `TerminalIntentAdapter.parse(...)`
→ `assistant_task.handle_explain_intent(intent)` — see "Assistant Task
seam" above for the classify/fulfill detail. The orchestrator no longer
holds its own copy of the resolve+format logic (the old
`_handle_chat_explain` method is gone). A `--list`/`--rung` line inside
chat still gets an honest one-line redirect to the terminal (still zero
LLM calls, still no Task emitted for it) — those stay terminal-only.

**Import direction, explicitly scoped:** `jarvis.core.orchestrator` now
imports `jarvis.capabilities.intent.TerminalIntentAdapter` and
`jarvis.intelligence.assistant_task.handle_explain_intent` (both local
imports, inside `_handle_global_commands` only) — the *orchestrator's*
global-command layer, not `project_continuity.py`, which still never
imports anything from `jarvis.intelligence` and still never reads
`ontology/` (that fence, from R3, is unchanged — see below). The
direction stays one-way: `jarvis.intelligence.*` still must not import
`jarvis.core`/`orchestrator` (AST-enforced, same as every prior Buy).

## Continuity cite seam (A6/R3, extended by A8): `continuity_cite.py`

`jarvis.intelligence.continuity_cite` adds `CONTINUITY_TOPIC_MAP` (a
finite `dict[str, list[str]]`, 5 seed topics: `c_rate`,
`operating_point`, `motor`, `current`, `thrust_stand` — all five now
actually tagged by Continuity as of A8; `current` was seeded-but-unused
from R3 until then) and
`cites_for_topics(topics) -> list[OntologyCite]` — exact topic → solid
id(s) → A2 `retrieve_by_id` resolve. Unknown topics are skipped
silently (never invented). `format_continuity_cite_lines(cites)` is the
thin CLI formatter used by `adapters/cli/main.py`'s optional
**"Conceptos"** block.

**The fence (locked, test-enforced):**
- `jarvis.core.project_continuity` **never imports this module** and
  **never reads `ontology/`.** It only computes a finite list of topic
  *tags* (`explain_topics`, via its own pure `_explain_topics_for_
  continuity` helper) from signals it already had for
  `situation`/`next_useful_step` — resolving those tags to cites is
  this module's job, called only from the CLI layer, the same seam
  `jarvis explain` itself uses.
- Topics are computed **after** `next_useful_step`/`next_useful_why`
  are finalized — they never feed back into Continuity's own ranking.
  Continuity decides the craft step; the vault never does.
- The CLI never dumps `[DEFINICION]`/`[INTUICION]` into `estado` — only
  `id` + a `jarvis explain <id>` pointer. Full text stays behind the
  explicit `jarvis explain` command (A3).
- `continuity_cite.py` itself never imports `jarvis.core` and never
  calls `submit_command` (AST-enforced, same as every other module in
  this package).

## Explain maps (A5): `--list` / `--rung KEY`

`jarvis.intelligence.explain_maps` adds two **static** dicts (not a
registry read from `flight_software` or anywhere else):
`FS_EXPLAIN_MAP` (keys `C3`/`C7`/`C10`/`C39`/`C42`) and
`HD_EXPLAIN_MAP` (keys `HD-001`/`HD-005`), each mapping a product key to
a list of ontology ids, mirroring `docs/ONTOLOGY_CROSSWALKS.md` §1/§2
verbatim for the seeded keys. `ids_for_rung(key)` does a case-normalized
lookup across both (`C7`/`c7`, `HD-001`/`hd-001` all resolve the same)
and returns `None` on a miss.

`jarvis explain --list` prints every solid vault id
(`ontology_retrieve.list_solid_ids`) plus every known alias → id line —
read-only vault scan, no ranking. `jarvis explain --rung KEY` prints the
mapped ids (+ `nombre` when retrievable) — deliberately **not** the full
`[DEFINICION]`/`[INTUICION]` bodies, to stay scannable; use the
positional query path for those. `--list`/`--rung`/the positional query
are mutually exclusive (argparse group) and the positional query's own
resolve order is unchanged from A3.

**Namespace honesty:** `FS_EXPLAIN_MAP`/`HD_EXPLAIN_MAP` keys are
product-doc shorthand for bridging to ontology ids — never `jarvis.core`
parameter ids, and never read from `flight_software` dynamically.

`explain_aliases.EXPLAIN_ALIASES` was expanded from the original 4 A3
seeds to 29 entries — one short alias for every remaining solid spine
id (`imu`, `gyro`/`giroscopio`, `accel`/`acelerometro`, `motor-dc`,
`motores`, `actuadores`, `dinamica`/`dynamics`, `vectores`/`vectors`,
`magnetismo`/`mag`, `corriente`, `banco`/`thrust stand`, `control
clasico`/`pid`, `control robotico`, `navegacion`/`nav`, `momento`,
`sensores movimiento`), every target independently verified `estado:
solid` against the real vault before being seeded.

## Terminal canal (A3): `jarvis explain <query>`

`jarvis.intelligence.explain` wires a real CLI command (`jarvis explain
<query>` / `python -m jarvis.main explain <query>`) over A2 retrieve.
**Command-first, not chat**: resolves `query` as (1) frontmatter `id`,
(2) else exact `nombre`, (3) else the finite alias table
(`explain_aliases.EXPLAIN_ALIASES`, now 29 entries — see "Explain maps"
above), else an honest miss (`No solid ontology note for: …`, exit code
1 — never a fabricated note). On a hit, prints `nombre`, `id`,
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
- `list_solid_ids()` (added for `--list`) is the same read-only scan
  pattern as `retrieve_by_id`/`retrieve_by_nombre` — no write, no new
  vault-access surface.

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
Scaffold landed **`v0.6.1`**, retrieve landed **`v0.6.2`**, terminal
canal landed **`v0.6.3`**, explain maps landed **`v0.6.4`**, Continuity
cite landed **`v0.6.5`**, chat intercept landed **`v0.6.6`**, topics
expand landed **`v0.6.7`**, Assistant Task (explain) landed **`v0.6.8`**
(all ★ ACCEPT CLOSED). This Continuity-defer Buy opens the next
package/tag, `0.6.9` / `v0.6.9`, on Engineer ACCEPT.

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
- `tests/test_explain_maps_expand_b1.py` (T1–T6): `imu`/`gyro` aliases
  resolve to solid cites, `ids_for_rung("C7")` contains `imu` and
  `giroscopio` (case-normalized), `ids_for_rung("HD-001")` contains
  `c-rate-de-bateria`, an unknown rung/HD key is an honest miss,
  `--list` output mentions `c-rate-de-bateria` and a known alias line
  and matches the real solid-id scan exactly, `explain_maps.py`/
  `explain_aliases.py` have no Continuity/LLM imports and no write API,
  every id referenced by the new maps/aliases is cross-checked against
  the real solid-id scan, the A3 query path is unchanged, and a
  subprocess smoke covers `--list`, `--rung C7`, and the
  `--list`+query mutual-exclusion error.
- `tests/test_continuity_explain_cite_r3_b1.py` (T1–T6): topic `c_rate`
  resolves to `c-rate-de-bateria` with non-empty `definicion`; two
  Continuity fixtures (motor-catalog-gap, autonomy-target) tag the
  expected topics (`["motor"]`, `["c_rate", "operating_point"]`) while
  producing the exact same `next_useful_step`/`next_useful_why` text as
  before this Buy (golden-string regression, captured from the code
  pre-edit); `project_continuity.py` never imports `jarvis.intelligence`
  (AST); `continuity_cite.py` never imports `jarvis.core` (AST); the
  rendered "Conceptos" block mentions `c-rate-de-bateria` and
  `jarvis explain`; an unknown topic never crashes and resolves to no
  cite.
- `tests/test_chat_explain_intercept_b1.py` (T1–T6): `orchestrator.
  handle_user_text("jarvis explain c-rate", llm)` and `"explain imu"`
  both resolve via A3, with an LLM interface whose `interpret`/
  `analyze`/`complete` all raise `AssertionError` if called — proving
  zero LLM calls on the matched path; an unknown query is an honest
  miss, still with the exploding LLM; unrelated global commands
  (escape word, an unmatched `explica esto`/`no explain plz` phrase)
  are unaffected by the new intercept; `explain --list` inside chat
  redirects to the terminal rather than attempting the search there;
  and every `jarvis.intelligence` module still has zero `jarvis.core`
  imports (AST).
- `tests/test_continuity_explain_topics_expand_b1.py` (T1–T5):
  `motor_op_current_a` present tags `"current"` and resolves via
  `cites_for_topics` to the solid `corriente-y-circuitos` cite; absent
  (or explicitly `None`) never tags it; a generic `energy_model_note`
  or a `motor_catalog_gap` fixture alone still never tags `current`
  (only `c_rate`/`operating_point` or `motor`, per the IC's own
  "forbidden" list); the R3 golden `next_useful_step`/`next_useful_why`
  strings stay byte-identical; `project_continuity.py`/`continuity_cite.py`
  fences hold (AST); `cites_for_topics(["current"])` returns a cite with
  non-empty `definicion`.
- `tests/test_assistant_explain_task_b1.py` (T1–T7): an explain-shaped
  `Intent` (either A7 prefix) yields a `Task` with `required_capability_ids
  == ["ontology.explain"]` and records `task_kind`/`explain_query` on
  `intent.metadata`; a non-explain Intent (including near-miss phrases
  like `"explica esto por favor"`) yields no Task; `fulfill_ontology_explain`
  returns the A3 cite body on a hit and the honest-miss string on a miss,
  never raising; `--list`/`--rung` get the terminal redirect via fulfill
  with **no** Task emitted; the full `handle_user_text` path re-proves
  the A7 exploding-LLM regression (hit/miss/`--list` all zero-LLM) through
  the new seam; `assistant_task.py` has zero `jarvis.core`/
  `jarvis.flight_software`/`jarvis.vehicle_profiles` imports and
  `project_continuity.py` still has zero `jarvis.intelligence` import
  (AST, both directions).
- `tests/test_assistant_defer_continuity_b1.py` (T1–T7): status phrases
  (`estado`, `resumen`, `siguiente paso`, `que falta`) yield a `Task`
  with `required_capability_ids == ["engineering.continuity"]`; a
  non-status craft line yields no Task; an explain-shaped line (even
  one whose remainder looks like a status phrase, e.g. `"explain
  estado"`) never gets a Continuity Task either; the full
  `handle_user_text` path resolves `"estado"`/`"resumen"`/`"ESTADO"`
  to `action == "project_status"` with zero LLM calls while explain
  stays unaffected; every `IntentResolver.STATUS_PATTERNS` entry is
  present in `CONTINUITY_DEFER_PHRASES` (sync); `assistant_task.py`
  has zero `jarvis.core`/`jarvis.core.intent_resolver`/`jarvis.
  flight_software`/`jarvis.vehicle_profiles` imports and
  `project_continuity.py` still has zero `jarvis.intelligence` import
  (AST, both directions).
