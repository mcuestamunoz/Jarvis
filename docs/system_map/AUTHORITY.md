# Authority Map

> **ProjectState / Acquisition Target / Continuity own *what is next*. The LLM interprets and may narrate; it must never choose the next engineering target or goal.**

This is not a convention that could quietly be violated — it is enforced **structurally**, at a single choke point: `ActionPolicy.ALLOWED_ACTIONS` (`llm/action_policy.py:14-18`) is a 4-member closed set (`CREATE_PROJECT`, `ITERATE`, `CALCULATE`, `SIMULATE`). `ActionName` (the enum `ActionPolicy` validates against) has no member for "declare a component," "pick a goal," or "run this DSE grid" — those concepts do not exist as LLM-reachable actions in the schema. See `CONNECTIONS.md` C-102/C-103 for the exact validation call chain, and `10_llm/LLM_MAP.md` for the module-level detail.

## Decision → Authority → Forbidden usurper

| Decision | Authority (owns it) | Forbidden usurper | Verified? |
|---|---|---|---|
| What component/gap is missing? | `acquisition_target.py` + `orchestrator._next_pending_block`/`_block_progress_status` | LLM; a second inference engine | ✅ structural (ActionPolicy) |
| Which gaps exist + assembly-ready rollup (9 subsystem lines)? | `engineering_readiness.build_engineering_readiness` (ERF-1/ERF-2) — composes closure/BOM/sim/arch/electrical authorities; **not** primary physics/BOM/sim truth. ERF-2 adds `INCOMPATIBLE` verdicts + `electrical_compatibility.py` | Continuity re-deriving gaps ad hoc; LLM gap inference | ✅ pure projection, no Continuity import (`engineering_readiness.py`, `electrical_compatibility.py`) |
| What is the single next useful step? | `project_continuity.build_project_continuity` → `next_useful_step` | LLM narrating a different gap | ✅ `project_continuity.py` has zero I/O and is never passed to the LLM as a decision input |
| Is a component key present/stub/declared/defined? | `project_closure.classify_component` (FN-020) | Any second completeness threshold | ✅ `orchestrator._component_is_low` is a thin wrapper over the same primitive (C-083) |
| What design goal is the user naming? | `goal_planner.detect_goal`/`is_engineering_intention` (FN-022, reused unchanged by FN-025 for help-phrased goals) | LLM inventing a goal | ✅ `goal_planner.py` has zero I/O |
| Which configs to try (DSE)? | `DesignExplorer.explore(project_state, goal_key)` | LLM | ✅ docstring guarantee ("100% en memoria... no muta project_state") + no LLM import in `design_explorer.py` |
| Mutate a concrete parameter? | `IterateInteractiveSession`/`ParamDefinitionSession.answer` (value already given) | LLM inventing a variable/value | ✅ LLM's only reachable mutation actions are the 4 `ActionPolicy` verbs, all of which still resolve to deterministic Action objects, not LLM-chosen values |
| What component was declared and its properties? | `component_inference.infer_component[s]` → `component_writers.set_*` | Any other code path writing `design_properties.components` | ✅ `component_writers.py` is the only module that assigns `design_properties.components[key]` (grep-verified, no other write site in `src/`) |
| Orchestrator mode / session lifecycle? | `StateManager.set_runtime_session`/`clear_runtime_session` | A wizard leaving stale `pending_*` fields | ✅ (was violated pre-FN-021; closed, see `MISMATCHES.md`) |
| Physics results (calc/sim)? | `CalculationEngine.build`, `FeasibilitySimulator.evaluate` — pure functions | LLM; any hand-written override outside `component_resolver.PhysicalOverride` | ✅ both are pure functions over `current_parameters`, no LLM import |
| Narration / explanation in language? | `JarvisLLMInterface.analyze` | Choosing the gap, goal, or next step | ✅ `analyze()`'s return type is a plain string, never parsed back into a routing decision (unlike `interpret()`) |
| Motor catalog suggestions? | `motor_catalog_assist.py` (FN-005/009) | LLM inventing a SKU | ✅ deterministic search over `knowledge/library.py`, no LLM import |

**ERF-1 nuance (2026-08-18):** Continuity remains the sole authority for **human next-step copy**, but the **catalog-gap ranking decision** (genuine gap vs G9-B demoted PASS branch) is now sourced from `engineering_readiness` when `readiness=` is supplied (C-108, 🟡 PARTIAL — catalog branches only; blocking/FN-005/BOM/arch/optimization/fallback unchanged until Slice 4b). Gap registry ordering lives in C-107, not Continuity.

## Precedent for "who owns next" (established pattern, reused throughout)

The codebase already has a repeated, working pattern for "deterministic layer decides the next question, LLM never consulted":

- **FN-004** — `pending_structural_change` (motor_count change confirmation)
- **Bug 54** — `pending_define_missing` ("¿Definimos X ahora?" → sí opens the wizard)
- **FN-005/009** — catalog-assist bridge (motor suggestions)
- **FN-014/015** — Acquisition Target mention/help-define gates
- **FN-021** — session hygiene (mode cleared to IDLE the instant there's nothing left to acquire)
- **FN-022** — Engineering Intent gate (goal plan before iterate/LLM)
- **FN-023** — next-step help routed to Continuity, not analyze

§8/§9 of `MISMATCHES.md` (absorbed from the predecessor map) extend this exact pattern to "engineering intent → plan → DSE/iterate" handoffs. All three (C-042 via FN-024, C-025/C-044 via FN-025, C-043 via FN-026) now have that authority — `handoff_context.levers` membership (via `handoff_matching.match_plan_lever`) is the sole source for the iterate preseed, never a generic NLP guess.

## GUIDANCE / ANALYZE / ITERATE precedence (the mechanism behind several rows above)

`intent_resolver._resolve_strong_action_intent` checks pattern groups in a fixed order — this order **is** the authority for which of several possibly-overlapping intents wins:

```text
1. GUIDANCE_PATTERNS   (project_status — includes FN-023's next-step-help additions)
2. ANALYZE_PATTERNS    (= ANALYZE_VERB_PATTERNS + ANALYZE_HELP_PATTERNS, FN-025 split —
                        same union, same classification as before; bare "ayúdame" lives
                        in the HELP half)
3. CALCULATE_PATTERNS
4. SIMULATE_PATTERNS
5. DEFINE_PARAMS_PATTERNS (guarded: no numeric value present)
6. DISMISS_SUGGESTION_PATTERNS
7. APPLY_PATTERNS
8. EXPLORE_PATTERNS    (verb + goal/domain word; "aumentar"/"subir" deliberately excluded)
9. ITERATE_PATTERNS    (includes "aumentar"/"subir" — catches what EXPLORE didn't)
10. CREATE_PATTERNS
```

Only *after* this returns `None` does `resolve_intent` fall to `_looks_like_status_query`/`_looks_like_question`/`ambiguous`/`unknown`. Two authority checks now sit **downstream** of this ordered list, both in `orchestrator.py`, both reusing `goal_planner.is_engineering_intention` (never a second goal detector):

- **C-040 (FN-022)** — a separate check on the *result* `intent ∈ {"iterate","unknown"}`.
- **C-025/C-044 (FN-025)** — a separate check inside the `intent == "analyze"` branch, gated on the match having come from `ANALYZE_HELP_PATTERNS` specifically (not `ANALYZE_VERB_PATTERNS` — a real analytical verb always keeps its analyze routing, even combined with a help word, e.g. `"ayúdame, analiza el margen"`). A detected goal routes into the same `_handle_engineering_intent` C-040 uses; no detected goal (bare help) routes to `project_status`/Continuity, never an LLM-invented goal.

**Mode caveat (SYS-MAP-004 / G8):** this whole apparatus (ordered list + C-040/C-025 refinements) only runs when no earlier **mode branch** has already returned. In particular, an open `DEFINE_MISSING_PARAMETERS` session with `MISSING_COMPONENT_DEFINITION` handles the turn inside Acquisition's UX-C intercept and never reaches C-040 — unlike `ITERATE_INTERACTIVE`, which has C-052 preempt-and-redispatch. Classifiers may still be correct; the Goal Plan is simply unreachable until IDLE (or a future R3/R4 preempt policy).

Precedence is still fully determined by the ordered list above — these two checks only refine what happens *after* a phrase already resolved to `"iterate"`/`"unknown"`/`"analyze"`; they never reorder or bypass GUIDANCE, which is why FN-023's next-step-help patterns (step 1) are untouched by either.

Full code: `core/intent_resolver.py:461-506` (`_resolve_strong_action_intent`), `core/orchestrator.py`'s `intent == "analyze"` and `intent in ("iterate", "unknown")` branches.
