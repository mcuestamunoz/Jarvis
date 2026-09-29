# 00 — Entry

**Purpose.** The CLI/MCP surface, the spatial board visor launcher, and the seam where two independent dispatch mechanisms meet the same orchestrator. The visor does **not** call `handle` / `handle_user_text`.

**Inbound:** C-001 (user → CLI). **Outbound:** C-002 (→ `handle_user_text`), C-003 (→ `handle`), C-114 (`explain` subcommand → `jarvis.intelligence` — a *sibling* CLI entry point that does **not** route through `handle_user_text`/`handle`; since A7, **also** reachable inside `--chat` via `_handle_global_commands`'s `jarvis explain `/`explain ` prefix intercept — same C-114 edge, before any LLM call), C-115 (Continuity `explain_topics` → `_render_concept_lines` → `jarvis.intelligence.continuity_cite` — reached from inside `render_startup_context`/`render_response`, not a separate subcommand).

## Key modules

| Path | Role |
|---|---|
| `adapters/cli/main.py` | Terminal loop; renders results (`render_response`, `render_startup_context`); also hosts the `explain` subparser dispatch (below) |
| `adapters/mcp/server.py` | MCP tool server exposing Jarvis actions |
| `adapters/mcp/session_manager.py` | MCP-side session bookkeeping |
| `adapters/cli/board.py` (`jarvis board`) + `workspace/spatial_board.py` | Spatial board launcher + read-only projector (`ProjectState` → cards/`slot`; `geometry`, `declaredBoxPose`, `solidCopies`/`solidCopyOffsetsMm` — quad-X radial L-aware arms + Main Plate corner stations). Mutation = CLI/writers/Continuity — not the visor. Card layout overlay = browser `localStorage` (not pose). **Continuity spatial assembly @ v0.4.0** + craft-montage / mission-payload / user-guide @ v0.4.1 + Fase M mission craft ladder (cameras + VTX catalog families) @ v0.4.2 (suite **3166**) — feature locks under `.jes/artifacts/engineer_lock_*`. Scene3D situar mutation = **C-113** only. Taller CSS visor faces (cuboid + cylinder) @ `v0.5.35` — a rendering fix (each face/cap now centers before rotate+`translateZ`) so a thin plate/short cylinder draws as one solid instead of exploding; still **C-094**/**C-113** class (presentation-only, no new writer, no new C-xxx). |
| `adapters/cli/main.py` (`explain` subparser) + `intelligence/{explain,explain_aliases,explain_maps,ontology_retrieve}.py` | `jarvis explain <query \| --list \| --rung KEY>` — a second, independent CLI subcommand launcher, same grain as `board`: parses argv, then calls straight into `jarvis.intelligence` (read-only ontology cite lookup), never through `orchestrator.handle`/`handle_user_text`. Assistant A1–A5 (`v0.6.1`→package `0.6.4`). **C-114** only; no writer, no Continuity call. See `docs/USER_GUIDE_EXPLAIN.md`. |
| `core/orchestrator.py::_handle_global_commands`/`_handle_chat_explain` | A7 (`B1-chat-explain-intercept`, package `0.6.6`) — the **same** global-command intercept escape words/`nuevo` already use (first check in `_handle_user_text_inner`, strictly before any LLM call) now also matches `jarvis explain `/`explain ` (exact prefix + required space) and resolves via the same A3 `resolve_explain_query`/`format_explain_cite` `intelligence/explain.py` calls use — a query hit or an honest miss, zero LLM either way. `--list`/`--rung` inside chat get a terminal redirect, not a search. Still **C-114** (same edge, new ingress); `jarvis.intelligence.*` still never imports `jarvis.core` back. |
| `adapters/cli/main.py::_render_concept_lines` + `intelligence/continuity_cite.py` | R3 (`B1-continuity-explain-cite-r3`, package `0.6.5`) — **not** a subcommand: a helper called from inside `render_startup_context`/`render_response` when Continuity's `explain_topics` is non-empty. Resolves topic tags to solid cites via the same read-only `intelligence` seam as `explain`. **C-115** only; Continuity itself (`core/project_continuity.py`) never imports `jarvis.intelligence` — see `08_continuity/CONTINUITY_MAP.md`. Since A7, the block's own header text also tells the user they can type the pointer command right there in chat. |

## Important functions

- `adapters/cli/main.py::render_response(result)` — the one place CLI action-result formatting happens. Option A: if `calculations.battery_endurance_envelope` is present, appends the same ESTIMATIVO block as `estado` (`_render_estimative_endurance_lines`). Note it has a **dead branch** for `action == "define_missing_params"` at status other than `"interactive"` (unreachable because the generic `status == "interactive"` check above it already returns first) — harmless, not fixed here, flagged for a future cleanup pass.
- `adapters/cli/main.py::render_startup_context(ctx)` — `estado` / session startup; hover L1 line then ESTIMATIVO when envelope is on `latest_results`. Prints an optional **"Conceptos (ontology):"** block right after "Siguiente paso"/"Por qué" (R3, C-115) when `continuity["explain_topics"]` is non-empty **and** at least one topic resolves to a solid cite — one `id` + `jarvis explain <id>` pointer per line, never the note body. Same block is mirrored in `render_response`'s coherence footer (`_render_concept_lines`, shared helper).
- `orchestrator.handle_user_text(user_input, llm_interface)` (`core/orchestrator.py:559`) — public wrapper, persists a runtime snapshot after every turn.
- `orchestrator.handle(request)` (`core/orchestrator.py:199`) — the structured-action entry, used directly by MCP and by `_handle_user_text_inner`'s own handoff for a subset of intents (C-016).

## The dual-dispatch seam (documented here in detail; see `JARVIS_SYSTEM_MAP.md` for the headline)

```text
handle_user_text(text, llm)                    handle(request)
        │                                              │
        ▼                                              ▼
_handle_user_text_inner                    interactive-session short-circuit
  ~25-checkpoint if-chain                   (CREATE_PROJECT / ITERATE only)
        │                                              │
        │  intent ∈ {create_project,                   │
        │  iterate, calculate, simulate}                │
        └──────────────────►  self.handle(action_request) ──► ActionRouter.resolve
        │                                              │
        │  every other intent                          ▼
        ▼                                    CreateProjectAction / IterateAction /
  own dedicated handler                      CalculateAction / SimulateAction .run
  (analyze, project_status, define_params,
   explore_design_space, apply_exploration_result,
   dismiss_suggestion, engineering_intent)
```

**Implication for future work:** a new action type reachable from natural language must be wired into `_handle_user_text_inner`'s if-chain regardless of whether it also goes through `ActionRouter`. A new action type reachable only structurally (MCP) only needs `ActionRouter` + `handle()`. These are not currently unifiable without a refactor, which is explicitly out of scope for this map (documented, not fixed, per contract).

## Local state touched

CLI/MCP: none directly — those adapters forward to the orchestrator.  
`jarvis board`: launches Vite; visor layout overlay lives in browser `localStorage` (not `ProjectState`). Projector is read-only.  
`jarvis explain`: none — reads `ontology/*.md` via `Path.read_text` only (no write API anywhere in `jarvis.intelligence`); touches no `ProjectState`, no `library/`, no browser storage. Same holds for the A7 in-chat intercept — it calls the identical read-only `explain.py` functions, no new state touched.  
Conceptos block (R3): none — same read-only `ontology/` path as `jarvis explain`, reached from `render_startup_context`/`render_response` instead of the `explain` subcommand; `project_continuity.py` itself touches nothing new (additive `explain_topics` tag only, no new `ProjectState` read).

## Tests

`tests/test_main_cli.py` (CLI rendering), `tests/test_cli_board.py` (launcher), `tests/test_spatial_board_projector.py` (cards + B3 slots). MCP-specific tests under the same `tests/` tree if present (not enumerated here — see `find tests -iname "*mcp*"`).  
`explain`: `tests/test_intelligence_scaffold_b1.py`, `tests/test_ontology_retrieve_r2_b1.py`, `tests/test_assistant_terminal_canal_b1.py`, `tests/test_explain_maps_expand_b1.py`.  
Conceptos / Continuity cite (R3): `tests/test_continuity_explain_cite_r3_b1.py`, `tests/test_project_continuity.py` (unchanged, re-run as regression proof).  
Chat explain intercept (A7): `tests/test_chat_explain_intercept_b1.py` — asserts zero LLM calls via an exploding mock `llm_interface`.
