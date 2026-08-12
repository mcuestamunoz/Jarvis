# 10 — LLM

**Purpose.** The bounded fallback (`interpret`) and narrator (`analyze`). This is the subsystem `AUTHORITY.md`'s core claim rests on — read that file first for *why* this boundary holds, this file for *how* it's implemented.

**Inbound:** C-100/C-104 (from Runtime). **Outbound:** C-103 (back into Runtime/ActionRouter, closed 4-verb set only).

## Key modules

| Path | Role |
|---|---|
| `llm/llm_client.py` | `JarvisLLMInterface` — `interpret`, `analyze`; `LLMClient` Protocol |
| `llm/prompt_builder.py` | `PromptBuilder.build_messages` |
| `llm/response_parser.py` | `LLMResponseParser` — `parse`, `validate_for_runtime` (delegates to `ActionPolicy`), `to_action_request` |
| `llm/action_policy.py` | `ActionPolicy` — **the structural authority boundary**: `ALLOWED_ACTIONS`, `ALLOWED_IN_SESSION`, `REQUIRES_INTERACTIVE_MODE`, `MIN_REQUIRED_FIELDS` |
| `llm/ollama_client.py` | `OllamaClient` — concrete `LLMClient` implementation (network call to the model backend) |
| `llm/semantic_intent_adapter.py` | `SemanticIntentAdapter.adapt(llm_output)` — **SYS-MAP-003 correction (M-003):** two real callers, neither is "Iteration's slot-filling" (that's the *different*, similarly-named `core/semantic_interpreter.py`, see `05_iteration`). (1) `llm_client.py::_build_semantic_trace` — logging only, does not affect routing. (2) `orchestrator._semantic_preseed`, called from `handle()`'s `ITERATE` branch (`:249`) — decides whether the iterate wizard can skip straight to its value-question step when the incoming `action_request` already names a valid, non-derived `variable` at high confidence. Bounded: only ever adjusts wizard *starting step*, never bypasses the wizard's own confirmation, never writes `ProjectState` itself. |

## Important functions (Level 2)

- `JarvisLLMInterface.interpret(user_input, runtime_state) -> dict` (`llm_client.py:34`) — `PromptBuilder.build_messages` → `LLMClient.complete` → `LLMResponseParser.parse` → `.validate_for_runtime` (→ `ActionPolicy.validate`) → `.to_action_request`. On any exception, returns a hardcoded `{"action": "simulate", "parameters": {"error": "invalid_llm_output", ...}}` fallback (not a crash) — this is itself evidence of the closed-action-set discipline: even the *error path* stays inside the 4-verb set.
- `JarvisLLMInterface.analyze(user_input, context, analyze_type, reasoning_output, conversation_history, goal_context) -> str` (`llm_client.py:76`) — pure narration; `goal_context` (from `get_goal_context_for_llm`, `04_engineering`) is passed in as *read-only reference material* the LLM may quote from, never as something it decides.
- `ActionPolicy.ALLOWED_ACTIONS` (`action_policy.py:15-19`) — `{CREATE_PROJECT, ITERATE, CALCULATE, SIMULATE}`. This 4-member closed set is **the** mechanism referenced throughout `AUTHORITY.md` and `CONNECTIONS.md`'s Forbidden Transitions box — there is no `ActionName` member for declaring a component, picking a goal, or configuring a DSE run, so `ActionPolicy.validate` structurally cannot let the LLM's output become one of those things.
- `LLMResponseParser.to_action_request(validated) -> dict` — the final shape handed to `orchestrator.handle` (C-103), identical in structure to what the deterministic `resolve_action_request` path (C-019) produces for the same 4 actions — i.e. the LLM and the deterministic resolver are interchangeable *inputs* to the same `ActionRouter`, which is exactly the intended narrowness.

## Local state touched

None — this subsystem is stateless per call (it reads `runtime_state`/`context` as input, never writes session or project state itself; any resulting mutation happens downstream, inside whatever `Action.run()` the returned `action_request` resolves to).

## LLM

YES — this is the LLM boundary itself.

## Known issues owned by this subsystem

None — the boundary holds as designed. The known-broken edges (C-025/C-042/C-043/C-044) are all cases of **other** subsystems failing to claim a turn before it falls here, not cases of this subsystem overreaching its own bounds.

## Tests

`tests/test_llm_integration.py`, `tests/test_llm_response_parser.py` (direct — `ActionPolicy`/`LLMResponseParser` boundary), plus indirect coverage throughout `tests/test_fn*.py` via `_StubLLM`/`_RefuseLLM` fixtures that assert 0-LLM-calls on deterministic paths.
