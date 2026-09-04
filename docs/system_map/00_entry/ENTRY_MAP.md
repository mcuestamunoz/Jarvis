# 00 — Entry

**Purpose.** The CLI/MCP surface, and the seam where two independent dispatch mechanisms meet the same orchestrator.

**Inbound:** C-001 (user → CLI). **Outbound:** C-002 (→ `handle_user_text`), C-003 (→ `handle`).

## Key modules

| Path | Role |
|---|---|
| `adapters/cli/main.py` | Terminal loop; renders results (`render_response`, `render_startup_context`) |
| `adapters/mcp/server.py` | MCP tool server exposing Jarvis actions |
| `adapters/mcp/session_manager.py` | MCP-side session bookkeeping |

## Important functions

- `adapters/cli/main.py::render_response(result)` — the one place CLI action-result formatting happens. Option A: if `calculations.battery_endurance_envelope` is present, appends the same ESTIMATIVO block as `estado` (`_render_estimative_endurance_lines`). Note it has a **dead branch** for `action == "define_missing_params"` at status other than `"interactive"` (unreachable because the generic `status == "interactive"` check above it already returns first) — harmless, not fixed here, flagged for a future cleanup pass.
- `adapters/cli/main.py::render_startup_context(ctx)` — `estado` / session startup; hover L1 line then ESTIMATIVO when envelope is on `latest_results`.
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

None directly — this layer only forwards to the orchestrator.

## Tests

`tests/test_main_cli.py` (CLI rendering), MCP-specific tests under the same `tests/` tree if present (not enumerated here — see `find tests -iname "*mcp*"`).
