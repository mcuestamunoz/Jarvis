# Authority Map

> **ProjectState / Acquisition Target / Continuity own *what is next*. The LLM interprets and may narrate; it must never choose the next engineering target or goal.**

This is not a convention that could quietly be violated — it is enforced **structurally**, at a single choke point: `ActionPolicy.ALLOWED_ACTIONS` (`llm/action_policy.py:14-18`) is a 4-member closed set (`CREATE_PROJECT`, `ITERATE`, `CALCULATE`, `SIMULATE`). `ActionName` (the enum `ActionPolicy` validates against) has no member for "declare a component," "pick a goal," or "run this DSE grid" — those concepts do not exist as LLM-reachable actions in the schema. See `CONNECTIONS.md` C-102/C-103 for the exact validation call chain, and `10_llm/LLM_MAP.md` for the module-level detail.

## Decision → Authority → Forbidden usurper

| Decision | Authority (owns it) | Forbidden usurper | Verified? |
|---|---|---|---|
| What component/gap is missing? | `acquisition_target.py` + `orchestrator._next_pending_block`/`_block_progress_status` | LLM; a second inference engine | ✅ structural (ActionPolicy) |
| What is the single next useful step? | `project_continuity.build_project_continuity` → `next_useful_step` | LLM narrating a different gap | ✅ `project_continuity.py` has zero I/O and is never passed to the LLM as a decision input |
| Is a component key present/stub/declared/defined? | `project_closure.classify_component` (FN-020) | Any second completeness threshold | ✅ `orchestrator._component_is_low` is a thin wrapper over the same primitive (C-083) |
| What design goal is the user naming? | `goal_planner.detect_goal`/`is_engineering_intention` (FN-022) | LLM inventing a goal | ✅ `goal_planner.py` has zero I/O |
| Which configs to try (DSE)? | `DesignExplorer.explore(project_state, goal_key)` | LLM | ✅ docstring guarantee ("100% en memoria... no muta project_state") + no LLM import in `design_explorer.py` |
| Mutate a concrete parameter? | `IterateInteractiveSession`/`ParamDefinitionSession.answer` (value already given) | LLM inventing a variable/value | ✅ LLM's only reachable mutation actions are the 4 `ActionPolicy` verbs, all of which still resolve to deterministic Action objects, not LLM-chosen values |
| What component was declared and its properties? | `component_inference.infer_component[s]` → `component_writers.set_*` | Any other code path writing `design_properties.components` | ✅ `component_writers.py` is the only module that assigns `design_properties.components[key]` (grep-verified, no other write site in `src/`) |
| Orchestrator mode / session lifecycle? | `StateManager.set_runtime_session`/`clear_runtime_session` | A wizard leaving stale `pending_*` fields | ✅ (was violated pre-FN-021; closed, see `MISMATCHES.md`) |
| Physics results (calc/sim)? | `CalculationEngine.build`, `FeasibilitySimulator.evaluate` — pure functions | LLM; any hand-written override outside `component_resolver.PhysicalOverride` | ✅ both are pure functions over `current_parameters`, no LLM import |
| Narration / explanation in language? | `JarvisLLMInterface.analyze` | Choosing the gap, goal, or next step | ✅ `analyze()`'s return type is a plain string, never parsed back into a routing decision (unlike `interpret()`) |
| Motor catalog suggestions? | `motor_catalog_assist.py` (FN-005/009) | LLM inventing a SKU | ✅ deterministic search over `knowledge/library.py`, no LLM import |

## Precedent for "who owns next" (established pattern, reused throughout)

The codebase already has a repeated, working pattern for "deterministic layer decides the next question, LLM never consulted":

- **FN-004** — `pending_structural_change` (motor_count change confirmation)
- **Bug 54** — `pending_define_missing` ("¿Definimos X ahora?" → sí opens the wizard)
- **FN-005/009** — catalog-assist bridge (motor suggestions)
- **FN-014/015** — Acquisition Target mention/help-define gates
- **FN-021** — session hygiene (mode cleared to IDLE the instant there's nothing left to acquire)
- **FN-022** — Engineering Intent gate (goal plan before iterate/LLM)
- **FN-023** — next-step help routed to Continuity, not analyze

§8/§9 of `MISMATCHES.md` (absorbed from the predecessor map) extend this exact pattern to "engineering intent → plan → DSE/iterate" handoffs — which today do **not** yet have an authority of their own (C-042/C-043/C-044 are `🔴 BROKEN` precisely because no such authority exists).

## GUIDANCE / ANALYZE / ITERATE precedence (the mechanism behind several rows above)

`intent_resolver._resolve_strong_action_intent` checks pattern groups in a fixed order — this order **is** the authority for which of several possibly-overlapping intents wins:

```text
1. GUIDANCE_PATTERNS   (project_status — includes FN-023's next-step-help additions)
2. ANALYZE_PATTERNS    (bare "ayúdame" lives here — this is why C-025/C-044 are broken:
                        a goal word after "ayúdame" never reaches step 6 below)
3. CALCULATE_PATTERNS
4. SIMULATE_PATTERNS
5. DEFINE_PARAMS_PATTERNS (guarded: no numeric value present)
6. DISMISS_SUGGESTION_PATTERNS
7. APPLY_PATTERNS
8. EXPLORE_PATTERNS    (verb + goal/domain word; "aumentar"/"subir" deliberately excluded)
9. ITERATE_PATTERNS    (includes "aumentar"/"subir" — catches what EXPLORE didn't)
10. CREATE_PATTERNS
```

Only *after* this returns `None` does `resolve_intent` fall to `_looks_like_status_query`/`_looks_like_question`/`ambiguous`/`unknown`. The FN-022 engineering-intent gate (C-040) is **not** part of this ordered list — it is a separate check the orchestrator runs on the *result* (`intent ∈ {"iterate","unknown"}`), which is exactly why a phrase that resolves to `"analyze"` at step 2 never reaches it. This is the single most important fact for understanding Failures A/B/C's shared root shape.

Full code: `core/intent_resolver.py:461-506` (`_resolve_strong_action_intent`).
