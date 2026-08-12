# 05 — Iteration

**Purpose.** Free-text → concrete parameter mutation, via a multi-step confirmation wizard. Also hosts the new-project wizard (`interactive_session.py`), which follows the same "draft + step + confirm" shape.

**Inbound:** C-050 (from Runtime). **Outbound:** C-060 (to Calculation, via `apply_and_recalculate`/`MutationEngine`), C-091 (component-shaped mutations go through the same writers).

## Key modules

| Path | Role |
|---|---|
| `core/iterate_interactive_session.py` | `IterateInteractiveSession` — the wizard itself (~1350 lines: draft building, impact estimate, conflict detection, semantic preseed, pending-entity selection) |
| `core/iterate_domain.py` | Stateless validators/normalizers used by the session (`_is_valid_variable`, `_fuzzy_normalize_variable`, …) |
| `core/mutation_engine.py` | `MutationEngine`, `apply_mutation` — free text → parameter delta resolution |
| `core/semantic_interpreter.py` | `SemanticState` slot-filling (`update`, `decide`, `extract_entities`, `to_draft_patch`) — shared machinery, also used by `interactive_session.py` |
| `core/interactive_session.py` | `CreateProjectInteractiveSession` — new-project wizard, same draft/step/confirm shape, not otherwise related to mutation |

## Important functions (Level 2)

- `IterateInteractiveSession.start(seed_parameters) -> dict` (`:88`) — builds the initial `IterationDraft`.
- `IterateInteractiveSession.answer(session, user_input) -> dict` (`:130`) — the main turn handler; ~380 lines covering objective confirmation, apply/final-confirmation, conflict resolution, pending-entity selection.
- `_seed_semantic_from_state` / `_seed_semantic_from_draft` (`:1108`, `:1127`) — **this is the exact mechanism C-043 is broken inside of.** It seeds `SemanticState.slots` from whatever the draft already has (`objective`, `operation`) but nothing currently writes a plan-lever name into the `variable` slot specifically — so a user who names a real lever (`"safety_factor"`) still gets `missing_slots == ["variable"]`.
- `_missing_slot_question(slot_name)` (`:1155`) — produces `"¿Qué quieres modificar? ..."` whenever `variable` is still unfilled; this is the honest fallback that fires today regardless of whether the user already named the lever in free text.
- `semantic_interpreter.extract_entities(text) -> list[str]` (`:142`) — generic entity extraction; does not currently cross-reference `goal_planner.GOAL_STRATEGIES`' lever vocabulary at all (confirmed: no import of `goal_planner` anywhere in `iterate_interactive_session.py` or `semantic_interpreter.py`).
- **SYS-MAP-003 addition (M-003):** a *second*, easily-confused, similarly-named module also touches wizard start-up: `llm/semantic_intent_adapter.py::SemanticIntentAdapter` (`10_llm`). `orchestrator._semantic_preseed` calls it from `handle()`'s `ITERATE` branch, before `IterateInteractiveSession.start` runs, to decide whether the wizard can skip its variable-selection step. It is a *different* mechanism from `semantic_interpreter.py`'s in-wizard slot filling above — do not conflate the two when tracing why a wizard opened at a given step.
- `mutation_engine.apply_mutation` (`:404`) — resolves a free-text mutation phrase into a concrete parameter delta once `variable`+`operation`(+`value`) are known.

## Local state touched

`InteractiveSessionState.iteration_draft`, `.semantic_state`, `.pending_entities`, `.motor_suggestions` (motor-specific sub-flow).

## LLM

NO — the wizard itself never calls the LLM directly. It is *reachable* from an LLM-classified `"iterate"` action_request (C-103), but the wizard's own turn-by-turn logic is fully deterministic.

## Known issues owned by this subsystem

- **C-043** 🔴 (shared with `04_engineering`) — a plan's lever name is not preseeded into `variable`. Fix (H4, design-only) requires the lever to be a member of the *current plan's* strategy levers, which means this subsystem would need to receive that plan/handoff context from Engineering — it cannot derive it alone from generic NLP matching without risking false positives on unrelated free text.

## Tests

`tests/test_iterate_session.py`, `tests/test_design_utils.py`, `tests/test_u1_battery_mass.py`, `tests/test_u2_propeller_bridge.py` (iterate-adjacent bridges).
