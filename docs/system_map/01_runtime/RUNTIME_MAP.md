# 01 — Runtime

**Purpose.** The turn dispatcher: `_handle_user_text_inner`'s checkpoint chain, plus `ActionRouter`'s structured-action backend.

**Inbound:** C-002/C-003 (from Entry). **Outbound:** virtually everything — C-020 (Intent), C-030-C-038 (Acquisition), C-040 (Engineering), C-050 (Iteration), C-092 (State), C-100/C-104 (LLM).

## The 25-checkpoint order (current `main`, re-derived 2026-08-10)

| # | Checkpoint | Anchor | C-xxx |
|---|---|---|---|
| 1 | Global commands (escape words, `n`/`nuevo`) | `_handle_global_commands` | C-010 |
| 2 | FN-004 structural-confirm consume | `pending_structural_change` | C-011 |
| 3 | Bug 54 pending_define_missing consume | `pending_define_missing` | C-012 |
| 4 | FN-005 "ayúdame a elegir" (IDLE) | `_try_start_assisted_motor_help` | C-030 |
| 5 | FN-014 acquisition mention (IDLE) | `_try_start_acquisition_from_mention` | C-031 |
| 6 | FN-015 bare help-define (IDLE) | `_try_help_define_pending_idle` | C-032 |
| 7 | Global component intercept (any mode) | `_interceptable_component_specs` | C-013 |
| 8 | Mode: `CREATE_PROJECT_INTERACTIVE` | `self.handle({"action": CREATE_PROJECT, ...})` | C-014, C-016 |
| 9 | Mode: `ITERATE_INTERACTIVE` (nested, see below) | — | C-014, C-050-C-054 |
| 10 | Mode: `DEFINE_MISSING_PARAMETERS` (nested, see below) | — | C-014, C-033, C-034 |
| 11 | Mode: `SYSTEM_DEFINITION` | `system_definition_session.answer` + auto-bridge | C-014 |
| 12 | Parameter ingestion layer | `try_ingest` | C-015 |
| 13 | `intent = resolve_intent(user_input)` | — | C-020 |
| 14 | `intent == "project_status"` | `_handle_project_status` | C-021, C-035 |
| 15 | `intent == "analyze"` — nested: FN-025 (H3) help-verb + goal check first | `is_engineering_intention` → `_handle_engineering_intent`, or `_handle_project_status` (bare help, no goal), else `_handle_analyze` | C-022, C-025/C-044 |
| 16 | `intent == "ambiguous"` | analyze or start create_project | — |
| 17 | `intent == "define_params"` | bridge to `start_define_missing_params` | C-023 |
| 18 | **FN-022 engineering-intention gate** | `is_engineering_intention` → `_handle_engineering_intent` | C-040 |
| 19 | `intent ∈ {create_project, iterate, calculate, simulate}` | `resolve_action_request` → `self.handle` | C-016 |
| 20 | `intent == "dismiss_suggestion"` | `_handle_dismiss_suggestion` | C-024 |
| 21 | `intent == "explore_design_space"` | `resolve_explore_goal` → `_handle_explore` | C-042, C-045 |
| 22 | `intent == "apply_exploration_result"` | `_handle_apply_exploration` | C-046 |
| 23 | LLM fallback | `llm_interface.interpret` | C-100 |
| 24 | Bug 52 guard (`unknown` + LLM said `iterate` → analyze) | — | — |
| 25 | Final dispatch | `self.handle(action_request)` | C-103 |

### Nested — `ITERATE_INTERACTIVE`
```text
resolve_intent → "project_status"/"analyze" → soft-interrupt (wizard_reprompt attached)   C-051
classify_input_intent ∈ {information, hybrid} → soft-interrupt                             C-051
_should_preempt_iterate_wizard → clear + re-dispatch as IDLE                                C-052
else → self.handle(ITERATE)                                                                 C-050
```

### Nested — `DEFINE_MISSING_PARAMETERS`
```text
resolve_intent → "project_status" → _handle_project_status (mode preserved)                 C-035
FN-013 _try_reprompt_active_block_declaration                                                C-033
FN-015 is_help_define_pending_phrase → _help_current_pending_acquisition                     C-032
"analyze" (not help-choose) → _handle_analyze
"calculate"/"simulate" → self.handle(...)
FN-016 is_navigation_back_phrase → clear_runtime_session, cancelled                          C-034
UX-C: pending_missing_reason/param_definition_reason == MISSING_COMPONENT_DEFINITION
  → _handle_component_description                                                            C-013
battery component-intent intercept → synthesize session → _handle_component_description
else → param_definition_session.answer → _append_arch_progress_hint + _set_pending_next_block  C-037
```

## Key modules

| Path | Role |
|---|---|
| `core/orchestrator.py` | `JarvisOrchestrator` — the hub; ~2700+ lines, every checkpoint above lives here |
| `core/action_router.py` | `ActionRouter` — 4-action closed-set backend |
| `actions/*.py` | `CreateProjectAction`, `IterateAction`, `CalculateAction`, `SimulateAction` — the `.run()` targets |

## Local state touched

`InteractiveSessionState` (all fields — this is the layer that owns reading/writing session mode and every `pending_*` field). Full field list: `09_state/STATE_MAP.md`.

## Tests

`tests/test_orchestrator.py` (broad), `tests/test_fn011_propulsion_declare_routing.py` through `tests/test_fn023_next_step_help.py` (each FN's own checkpoint), `tests/test_main_cli.py`.
