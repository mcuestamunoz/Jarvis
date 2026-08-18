# Doc ↔ Code Mismatches

Per source-of-truth order (`README.md`), code wins. Entries below are recorded, not silently resolved.

## ⚠ DOCUMENTATION MISMATCH entries

### M-001 — "13 checkpoints" figure (stale)
```text
Prior documentation said:  _handle_user_text_inner has 13 checkpoints
                            (referenced in earlier architecture-audit conversation
                            history predating FN-011…023; not a file in this repo)
Code currently:             25 numbered checkpoints (01_runtime/RUNTIME_MAP.md),
                            counting nested ITERATE_INTERACTIVE / DEFINE_MISSING_
                            PARAMETERS sub-branches separately
Pointers:                   core/orchestrator.py:577-939 (_handle_user_text_inner)
Resolution:                 Re-derived fresh for SYS-MAP-001 (2026-08-10), carried
                            forward unchanged into this split (SYS-MAP-002). Every
                            one of FN-011 through FN-023 added at least one
                            checkpoint or nested branch — re-derive again after any
                            future FN that touches the top-level if-chain.
```

### M-002 — `design_layer_connection_map.md`'s CTA description
```text
Prior documentation said:  (implicitly, via the H1 sketch) the CTA/explore gap was
                            framed primarily as "session goal not persisted"
Code currently:             the CTA itself (_handle_engineering_intent) unconditionally
                            advertises "explora opciones" regardless of whether any
                            context to bind it to could ever exist — i.e. the CTA text
                            is dishonest independent of whether H1 is ever implemented
Pointers:                   core/orchestrator.py (_handle_engineering_intent CTA string)
Resolution:                 CLOSED (FN-024, 2026-08-10). Recorded as its own connection
                            (C-042, now 🟢) and its own design note (H2, now implemented,
                            below) — CTA honesty and context lifecycle turned out to be
                            the same fix in practice: a fresh active HandoffContext is
                            now always created immediately before the CTA is built, so
                            the existing CTA text became true by construction, no
                            separate conditional text was needed.
```

### M-003 — `semantic_intent_adapter.py` mischaracterized in `10_llm/LLM_MAP.md`
```text
Prior documentation said:  (SYS-MAP-002) SemanticIntentAdapter is "used by Iteration's
                            slot-filling (05_iteration), not by interpret()'s routing path"
Code currently:             it has two real callers, neither is "Iteration's slot-filling"
                            (that's the different, similarly-named core/semantic_interpreter.py).
                            (1) llm_client.py::_build_semantic_trace — logging only.
                            (2) orchestrator._semantic_preseed, called from handle()'s ITERATE
                            branch (:249) — decides whether the iterate wizard can skip to its
                            value-question step. Bounded (only adjusts starting step, never
                            bypasses confirmation or writes ProjectState), so no authority
                            violation — but the map's description of *where* it sits was wrong.
Pointers:                   core/orchestrator.py:249,2721 (_semantic_preseed),
                            llm/semantic_intent_adapter.py:106-121 (adapt() docstring)
Resolution:                 Fixed in 10_llm/LLM_MAP.md and 05_iteration/ITERATION_MAP.md
                            (SYS-MAP-003, 2026-08-10). No src/ change.
```

### M-004 — Nine empty scaffold modules, two mischaracterized as active in SYS-MAP-002
```text
Prior documentation said:  (SYS-MAP-002) 06_calculation/CALCULATION_MAP.md listed
                            tools/materials.py and tools/math_utils.py as "pure physics/data
                            helper functions consumed by the engine"; 07_simulation/
                            SIMULATION_MAP.md and README.md listed simulation/flight_model.py
                            and simulation/energy_model.py as active sub-models
Code currently:             both pairs are 0-byte empty files with zero imports anywhere in
                            src/ or tests/ (verified via `find src/jarvis -name "*.py" -size 0`
                            + per-file grep). All real physics for these concerns lives directly
                            in calculation_engine.py / simulator.py. Three more empty, unimported
                            modules exist and were never claimed as used by any map:
                            knowledge/{loader,parser,retriever}.py, utils/{helpers,validators}.py
                            (9 total, excluding legitimate empty __init__.py package markers)
Pointers:                   src/jarvis/tools/materials.py, tools/math_utils.py,
                            simulation/flight_model.py, simulation/energy_model.py,
                            knowledge/loader.py, knowledge/parser.py, knowledge/retriever.py,
                            utils/helpers.py, utils/validators.py — all 0 bytes
Resolution:                 Fixed in 06_calculation/CALCULATION_MAP.md, 07_simulation/
                            SIMULATION_MAP.md, README.md (SYS-MAP-003, 2026-08-10). Cataloged
                            for possible future cleanup in sys_map_003_hygiene_inventory.md
                            (HYG-008 through HYG-016) — no deletion in this cut (report-only
                            per contract §6). No src/ change.
```

### M-005 — C-040 presented without DEFINE_MISSING reachability caveat (SYS-MAP-004)
```text
Prior documentation said:  C-040 🟢 CONNECTED (FN-022) with evidence orchestrator.py:894-899;
                            ACQUISITION_MAP "Known issues: None"; AUTHORITY precedence table
                            implied Goal Plan reachable whenever classifiers fire
Code currently:             C-040 gate at orchestrator.py:931-936 only runs after all mode
                            branches return; DEFINE_MISSING + MISSING_COMPONENT_DEFINITION
                            UX-C (:796-802) returns first. Runtime comment already: "Runs
                            only in IDLE". ITERATE has C-052 preempt; DEFINE_MISSING does not.
                            Classifiers (F-1) are correct — turn never reaches the gate.
Pointers:                   CONNECTIONS.md C-040; orchestrator.py:796-802, :931-936;
                            .jes/artifacts/sys_map_004_routing_audit.md; finding G8
Resolution:                 Doc-only R1 (2026-08-15): C-040 Status/Evidence updated;
                            ACQUISITION_MAP known-issue pointer; AUTHORITY mode caveat.
                            Product preempt policy deferred to R3 → R4 (do not copy C-052).
```

### M-006 — Energy block label vs active param gap (G20, post-polish CLI)
```text
Prior documentation said:  (implicit via block labels) "Energía (batería)" means the user
                            should re-declare or confirm the battery component
Code currently:             composite energy block can be in_progress because motor_power_w
                            (or catalog motor bind) is stale after re-declaring motors at
                            IDLE, while battery component + battery_capacity_wh remain set.
                            build_startup_context proactive_question may say
                            "¿Definimos motor_power_w (energía) ahora?" but architecture
                            progress hint still uses block marketing label "Energía (batería)".
                            Bug 54 affirmative si correctly opens motor_power_w wizard — user
                            expectation mismatch, not wrong param wizard.
Pointers:                   orchestrator.build_startup_context (~3008-3114),
                            system_architecture_catalog BLOCK_TO_COMPONENTS["energy"],
                            .jes/artifacts/cli_findings_post_catalog_bind_v1.md G20/G20-B
Resolution:                 Registered follow-up (copy-only micro-fix). Not a polish-bundle
                            blocker. checkpoint-continuity-polish documents as known UX debt.
```

**Note on the design appendix below (observed during this verification pass, 2026-08-10):** `HANDOFF_CONTEXT_DESIGN.md`'s own status line and Decision Log now show **§5 CLOSED** (Hybrid Operation-Scoped Context) with an FN-024 (H1+H2) Implementation Contract already issued — this happened via an external Engineer/JES decision concurrent with this SYS-MAP-003 audit, not as part of this contract's own work (which is explicitly forbidden from touching H1–H5/FN-024). The "Open questions" section immediately below (§ Design-only appendix, "1. Lifecycle…" through "4. Explicit rejection…") still reads as if §5 is unresolved — it was **not** rewritten in this pass, since reconciling it would mean interpreting/restating an H1-adjacent decision, which SYS-MAP-003's scope excludes. Flagged here for Cursor/Engineer to reconcile in whatever pass formally absorbs the FN-024 outcome, so a future reader does not trust the stale "still open" framing over `HANDOFF_CONTEXT_DESIGN.md`'s own Decision Log.

No other mismatches were found between `docs/ARCHITECTURE.md`/`docs/PROJECT_CONTINUITY.md` and current code as of 2026-08-10 — the FN-by-FN log in `PROJECT_CONTINUITY.md` was cross-checked against this map's `CONNECTIONS.md` rows and found consistent (both were largely produced by the same closed-loop implement→test→document discipline, so this is expected, not a coincidence).

**2026-08-18 addendum:** CLI polish S1–S7 landed at `15aa503` (`checkpoint-continuity-polish`). System map subsystem files `02_intent`, `03_acquisition`, `08_continuity` updated for `list_motors`, force-motors, G9-B demotion, FN-013 pending sync. G20 energy-label mismatch recorded as M-006 above — not yet fixed in code.

---

## The FN-021 sticky-state lesson (why this matters for future handoff design)

FN-021 closed a real bug: `_set_pending_next_block()` did a bare `return` when `_next_pending_block()` was `None`, leaving `mode == DEFINE_MISSING_PARAMETERS` with stale `pending_missing_params`/`param_definition_reason` — so the *next unrelated turn*, regardless of what it was actually about, got answered with a leftover component-description prompt. The fix (`CONNECTIONS.md` C-037) was narrow and mode-gated: clear to IDLE only when the session was genuinely still sat inside the wizard that just finished.

**The general lesson, not specific to that one bug:** any piece of session state that means "the last thing we were talking about" is a liability unless every path that could make it stale explicitly clears it (or the read side is proven safe another way). FN-021's own report proved this by showing the *unmodified* non-final-block-chaining code path was untouched — i.e. the fix's blast radius was verified, not assumed.

This is the exact reason the design questions below (absorbed from the predecessor `docs/JARVIS_SYSTEM_MAP.md` §8) are marked **open, not decided** — a naive `last_engineering_goal` field, added without answering them, would very likely reproduce FN-021's bug shape in a new location (C-042/C-044's context, instead of C-037's wizard state).

---

## Design-only appendix — engineering state vs. handoff context (no implementation implied)

> **Living design authority for this topic:** [`HANDOFF_CONTEXT_DESIGN.md`](HANDOFF_CONTEXT_DESIGN.md) — **§5 CLOSED** (Hybrid Operation-Scoped Context, 2026-08-10). **FN-024 (H1+H2 / C-042), FN-025 (H3 / C-025+C-044), and FN-026 (H4 / C-043) are all DONE** — see `.jes/artifacts/implementation_report_fn024.md`, `.jes/artifacts/implementation_report_fn025.md`, and `.jes/artifacts/implementation_report_fn026.md`. **H1–H4 fully closed; only H5 (C-081) remains, design-only, deferred.**

This section is absorbed verbatim in substance from the predecessor single-file map (`docs/JARVIS_SYSTEM_MAP.md` §8/§9, itself absorbing `.jes/artifacts/design_layer_connection_map.md`'s H1–H5). Reviewed PASS WITH NOTES.

```text
Engineering Goal          ← may be persistent engineering meaning (optional future —
        │                    e.g. "this project's stated priority is stability"
        │                    surviving across sessions). Nothing in current code
        │                    does this; not proposed here either.
        ▼
Goal Plan (strategies/levers)     ← goal_planner.GOAL_STRATEGIES[goal_key], already
        │                            fully deterministic and stateless
        ▼
Plan / Handoff Context    ← IMPLEMENTED for the DSE consumer (FN-024, 2026-08-10),
        │                    the help+goal entry consumer (FN-025, 2026-08-12), AND
        │                    the Iterate lever consumer (FN-026, 2026-08-12),
        │                    schemas.action_schema.HandoffContext. Was C-042/C-043/
        │                    C-025/C-044's shared root cause — all four now closed.
        │                    Capability-scoped: which goal_key, which levers (now read
        │                    by H4), which DSE capability state — scoped to
        │                    "the conversation is still about the thing we just planned."
        │
        ├── valid context exists → "explora opciones" binds to the plan's goal_key ✅
        ├── "ayúdame" + named goal → enters/refreshes the same context ✅ (FN-025)
        ├── a named lever ∈ context.levers → preseeds Iterate's variable ✅ (FN-026)
        └── no valid context     → require explicit resolve ("optimiza para
                                    estabilidad") or ask ✅ (unchanged fallback)
```

### Open questions (design proposals only — not implementation recipes)

**1. Lifecycle: how long does handoff context live?** **RESOLVED (FN-024, Hybrid Operation-Scoped Context — see `HANDOFF_CONTEXT_DESIGN.md`'s Decision log).** Candidates that were considered, kept here for the historical record:
- *One turn only* — simplest, closes the exact CLI probe, but fragile to any intervening chat.
- *Until DSE actually runs* — mirrors `session.last_exploration_result`'s own shape (C-046): consumed-and-cleared by its own explicit next action. **Closest existing precedent in the codebase — this is the piece the Hybrid decision adopted for the DSE capability specifically.**
- *Until any mutation happens* (iterate, define_params, apply_exploration_result, component description save) — broader, but there are at least 4 mutation entry points to keep in sync, which is exactly the FN-021-class risk if one is missed.
- *Until Continuity's thread changes* (`_next_pending_block` state changes under it) — most "correct" in principle, most expensive to detect precisely.
- *Until project switch* — necessary in all cases, insufficient alone.

**2. Where does it live: runtime-only vs. `ProjectState`?** **RESOLVED (FN-024): runtime-only**, exactly as recommended below — `HandoffContext` lives on `InteractiveSessionState`, is excluded from `state_manager._PERSISTED_SESSION_FIELDS` (same tier as `last_exploration_result`, C-046), and is invalidated across a project boundary by a `project_id` match check at its one read site (`_handle_explore`) rather than by an active clear — proven via `tests/test_fn024_handoff_context_dse.py::test_handoff_context_inert_across_project_boundary`. Original recommendation, now implemented: runtime-only (`InteractiveSessionState`, not `design_properties`) — this is *conversational* context, not *engineering* fact; persisting it to `state.json` would make "goal of the moment" travel with the project file in a way that's almost certainly wrong. A future "persistent engineering priority" concept (the top box in the diagram) remains unimplemented and would need a **separate, explicitly-named field** with its own lifecycle.

**3. How to avoid a stale-handoff-context class of bug?** Whatever lifecycle is chosen, the fix must be symmetric with FN-021's own pattern: enumerate every mutation/turn-boundary entry point first (this map's `CONNECTIONS.md` is the checklist — start from C-050/C-054/C-046/C-013), and require a clear-or-justify at each one, the same way FN-021's report proved the untouched branch was safe by showing it, not asserting it. **FN-024 followed this discipline** — see its Implementation Report's blast-radius table for the per-path proof (project_status/analyze untouched, apply_exploration untouched, iterate path untouched, project switch proven inert via the `project_id` guard rather than an enumerated clear list).

**4. Explicit rejection of a naive sticky field.** This map does **not** recommend "just add `last_engineering_goal: str | None`, set it in `_handle_engineering_intent`, read it in `_handle_explore` when `goal_key is None`" as ready-to-implement, even though it would close C-042 in isolation. Without an answered lifecycle (question 1) and an explicit clear-on-mutation contract (question 3), it becomes a new instance of exactly the bug class FN-021 just closed. **FN-024 confirms this rejection was correct in practice** — it implemented `HandoffContext` as a small typed model with `goal_key`/`levers`/`dse_capability`/`iterate_capability`/`project_id`, not a bare string, specifically so a future H4 cut can consume `levers`/`iterate_capability` without needing a second field or a redesign.

### H1–H5 (absorbed, refined per Engineer notes)

| ID | Topic | Status | Refined statement |
|---|---|---|---|
| **H1** | Plan → DSE (closes C-042) | ✅ **IMPLEMENTED (FN-024, 2026-08-10)** | Bound via `schemas.action_schema.HandoffContext` — runtime-only (never in `_PERSISTED_SESSION_FIELDS`), project-scoped (`project_id` guard at every read, proven not assumed — see `tests/test_fn024_handoff_context_dse.py::test_handoff_context_inert_across_project_boundary`), capability-scoped (`dse_capability`/`iterate_capability` tracked independently — a successful DSE bind consumes `dse_capability` only, `goal_key`/`levers`/`iterate_capability` survive for H4). Lifecycle chosen: Hybrid Operation-Scoped Context per `HANDOFF_CONTEXT_DESIGN.md`'s Decision log. |
| **H2** | CTA honesty (M-002, closes part of C-042's symptom) | ✅ **IMPLEMENTED (FN-024)** | Closed as a *consequence* of H1, not a separate text change: `_handle_engineering_intent` unconditionally creates a fresh `dse_capability="active"` context immediately before building the CTA, so the existing `"... o 'explora opciones' ..."` phrasing is now true by construction every time it's shown — no conditional CTA logic was needed. |
| **H3** | Help + goal (closes C-025/C-044) | ✅ **IMPLEMENTED (FN-025, 2026-08-12)** | `IntentResolver.ANALYZE_PATTERNS` split into `ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS` (same union, zero change to `resolve_intent`'s own classification — GUIDANCE still wins first, unaffected). Orchestrator's `intent == "analyze"` branch checks whether the match came from the help half specifically (a real analytical verb always keeps its analyze routing); if so, `goal_planner.is_engineering_intention` (same authority as C-040, no second detector) decides: a detected goal routes into the existing `_handle_engineering_intent` (same plan, same `handoff_context` creation via C-105); no goal routes to `project_status`/Continuity, never an LLM-invented target. Option A chosen (orchestrator-side gate) over Option B (widening `resolve_intent` itself) — see C-025's `CONNECTIONS.md` entry for why. |
| **H4** | Lever → Iterate (closes C-043) | ✅ **IMPLEMENTED (FN-026, 2026-08-12)** | `orchestrator._preseed_variable_from_handoff` runs right before an `intent == "iterate"` request dispatches, guarded on `handoff.iterate_capability == "active"` and `handoff.project_id` matching the loaded project (same proof-at-read pattern as C-106, not an assumed clear). The pure helper `handoff_matching.match_plan_lever(user_input, handoff)` checks each lever's full string and its slash-separated tokens against the user text, accepting a candidate only if it also passes `iterate_domain._is_valid_variable` — so a compound lever's derived/non-settable token (e.g. `total_power_w`) is honestly skipped while its settable sibling (`motors`) still preseeds. Resolution reuses the exact `normalize_alias`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` chain `_apply_answer` already uses at step 1 — no parallel vocabulary. Never reads or touches `dse_capability`. |
| **H5** | Sim → Continuity, PASS + risky (addresses C-081) | 🟡 **Remains DESIGN, not a queued FN** | C-081 is `PARTIAL`/WEAK, not `BROKEN` — the fallback is honest, just uninformative. Open data-contract question: should `build_project_continuity` emit a new sentence reading `safety_margin_ratio` directly (cheap, consistent with `_prioritize_strategies`'s existing margin-reading pattern), or a structured "risk thread" field a future goal-thread mechanism (H1's context) could also consume? No position taken; do not implement an FN from this row until that data contract is written down as its own design note. |

**H1–H4 all closed (FN-024/FN-025/FN-026). H5 (C-081) is the sole remaining non-green row — design-only, deferred.**

**Forbidden across H1–H5 (unchanged):** Conversation Engine; Step D; inventing a parallel recommender to Continuity; Create→BOM. FN-024, FN-025, and FN-026 all confirmed none of these were touched (see their respective `.jes/artifacts/implementation_report_fn0*.md`).
