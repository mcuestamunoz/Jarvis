# 02 — Intent

**Purpose.** Regex-based classification of raw user text into one of 13 `IntentType` values. The single deterministic classifier everything else in Runtime branches on (C-020).

**Inbound:** C-020 (from Runtime). **Outbound:** C-021…C-025 (routing decisions back into Runtime handlers), plus catalog list handlers (`list_materials`, `list_motors`).

## Key modules

| Path | Role |
|---|---|
| `core/intent_resolver.py` | `IntentResolver` — the entire subsystem is this one class |

## Important functions

- `resolve_intent(user_input) -> IntentType` (`:280`) — top-level entry: `_resolve_strong_action_intent` first, then `_looks_like_status_query`, `_looks_like_question`, `DOMAIN_HINT_PATTERNS` (→ `"ambiguous"`), else `"unknown"`.
- `_resolve_strong_action_intent(normalized) -> IntentType | None` (`:461`) — the ordered pattern-group chain; **this ordering is the de facto authority** for GUIDANCE vs ANALYZE vs ITERATE vs EXPLORE precedence (full order in `AUTHORITY.md`).
- `resolve_declare_block_request(user_input) -> str | None` (`:300`) — FN-011, reused by Acquisition (C-031, C-033).
- `resolve_explore_goal(user_input) -> str | None` (`:317`) — thin wrapper over `goal_planner.detect_goal`, used by C-042/C-045.
- `classify_input_intent(user_input) -> "information"|"action"|"hybrid"` (`:508`) — used only by ITERATE_INTERACTIVE's soft-interrupt (C-051), not by the main dispatch chain.

## Pattern groups (constants, not functions — see `AUTHORITY.md` for the precedence order they're checked in)

`GUIDANCE_PATTERNS` (includes FN-023's 3 next-step-help additions), `ANALYZE_PATTERNS` (FN-025: now `ANALYZE_VERB_PATTERNS + ANALYZE_HELP_PATTERNS`, same union, same classification behavior — bare `\bayudame\b` lives in the HELP half, which `orchestrator.py` checks separately after `resolve_intent` returns `"analyze"`, see C-025), `CALCULATE_PATTERNS`, `SIMULATE_PATTERNS`, `DEFINE_PARAMS_PATTERNS`, `DISMISS_SUGGESTION_PATTERNS`, `APPLY_PATTERNS`, `EXPLORE_PATTERNS` (verb + goal/domain word; `aumentar`/`subir` deliberately excluded, comment in source), `ITERATE_PATTERNS`, `CREATE_PATTERNS`, **`LIST_MATERIALS_PATTERNS`** (G10 ★8 → `"list_materials"`), **`LIST_MOTORS_PATTERNS`** (polish S2/G16 → `"list_motors"`, checked before ANALYZE), `STATUS_PATTERNS` (checked only after all of the above return `None`).

## Local state touched

None — `IntentResolver` is stateless; every method is a pure function of its text argument (and, for `resolve_explore_goal`, a delegated pure call into `goal_planner`).

## LLM

NO — zero LLM involvement anywhere in this module.

## Known broken edges owned by this subsystem

- **G18 (closed S3, 2026-08-18):** terrestrial `DEFINE_PARAMS_PATTERNS` for `definir motores` no longer wins on aerial projects — orchestrator gate redirects to motors acquisition. IntentResolver unchanged (stateless).
- ~~C-025 — "ayúdame" + named goal → `"analyze"`~~ **fixed (FN-025)**: `ANALYZE_PATTERNS` was split into `ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS` (this module, zero change to `resolve_intent`'s own output) so `orchestrator.py` can distinguish the two groups and route help+goal into the Goal Plan path before falling to analyze. See `AUTHORITY.md`'s precedence table and `MISMATCHES.md`'s H3.

## Tests

`tests/test_orchestrator.py` (intent resolution is exercised indirectly through most orchestrator tests), **`tests/test_cli_polish.py`** (G16 list_motors, G18 aerial gate), plus targeted FN-014/015/016/022/023 test files which each pin specific `resolve_intent`/pattern behavior.
