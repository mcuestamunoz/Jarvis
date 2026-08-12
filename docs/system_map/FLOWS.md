# Reference Flows

User-visible journeys, step by step, each tied to `C-xxx` connection IDs. These are not exhaustive test cases — they are the reference paths a reader should be able to recognize their own CLI session against.

---

## FLOW-001 — Architecture acquisition

**User-visible steps:**
1. `"ayúdame a declarar propulsión"` (or any block) → wizard opens, asks for the first missing component.
2. Component description ("hélices 10x4.5") → saved, next component or block preseeded.
3. Last gap in the whole architecture closes → session returns to IDLE (no stale wizard).

**Modules/functions:** `acquisition_target.resolve_acquisition_mention` → `orchestrator._try_start_acquisition_from_mention`/`_continue_block_acquisition` → `param_definition_session.start` (uses `acquisition_brief.build_acquisition_brief`) → `orchestrator._handle_component_description` → `component_inference.infer_component[s]` → `component_writers.set_*` → `orchestrator._set_pending_next_block`.

**Connections:** C-031, C-038, C-013, C-090, C-091, C-037, C-036.

**Notes:** Fully 🟢. This is the flow FN-011 through FN-021 closed, in order. FN-021's invariant (C-037) is what guarantees step 3 above — verified in `tests/test_fn021_session_hygiene.py`.

---

## FLOW-002 — Engineering intention (`"aumentar empuje"` → goal_plan)

**User-visible steps:**
1. User states an intention with no concrete value: `"aumentar el empuje"`.
2. Jarvis shows a deterministic strategy plan (numbered levers) + a CTA, 0 LLM.
3. Iterate wizard does **not** open; LLM is **not** called.

**Modules/functions:** `intent_resolver.resolve_intent` (→ `"iterate"`) → `orchestrator`'s FN-022 gate → `goal_planner.is_engineering_intention` → `goal_planner.detect_goal` + `looks_like_numeric_mutate` → `orchestrator._handle_engineering_intent` → `goal_planner.format_goal_plan` (+ `_prioritize_strategies` using last sim context).

**Connections:** C-020, C-040, C-041.

**Notes:** 🟢 (FN-022). Primary mapping: "aumentar empuje"/"más thrust" → `mejorar_estabilidad` (documented in `04_engineering/ENGINEERING_MAP.md`). The CTA text this flow ends on is what FLOW-003 picks up — since FN-024, that handoff now works.

### FLOW-002b — Help + named goal entry (`"ayúdame a mejorar la estabilidad"` → goal_plan, fixed by FN-025)

A second, equally valid entry point into this same flow. **Pre-FN-025:** `resolve_intent("ayudame a mejorar la estabilidad") == "analyze"` (the help-verb half of `ANALYZE_PATTERNS` won before the FN-022 gate — which only fires for `intent ∈ {"iterate","unknown"}` — ever saw the turn) → LLM narrated instead of the plan being shown. This was C-025/C-044.

**Since FN-025:** inside the `intent == "analyze"` branch, the orchestrator checks whether the match came from `ANALYZE_HELP_PATTERNS` specifically (not `ANALYZE_VERB_PATTERNS` — a real analytical verb like `"analiza"`/`"evalúa"`/`"revisa"` always keeps its analyze routing, even combined with a help word). If so, it calls the exact same `goal_planner.is_engineering_intention` → `orchestrator._handle_engineering_intent` chain FLOW-002 already uses — same plan, same `handoff_context` creation (C-105), same CTA. A help phrase with **no** detectable goal (bare `"ayúdame"`) routes to `project_status`/Continuity instead — never an LLM-invented goal. FN-023's own next-step-help patterns (`"ayúdame con el siguiente paso"`) are checked earlier in `resolve_intent` (GUIDANCE, before ANALYZE) and never reach this branch at all — unaffected by construction, see FLOW-006.

**Connections:** C-025/C-044 (🟢, fixed FN-025), C-040/C-041 (reused, unchanged), C-105 (reused, unchanged).

---

## FLOW-003 — Explore design space (incl. `"explora opciones"` after a plan — fixed by FN-024)

**User-visible steps (working sub-case, unchanged):**
1. `"optimiza para estabilidad"` (verb + explicit domain) → DSE runs immediately, reports viable candidates or an honest "no viable configuration" message.

**User-visible steps (bound sub-case — continuation of FLOW-002, fixed by FN-024):**
1. FLOW-002 just showed a plan for `mejorar_estabilidad` and a CTA saying `"... o 'explora opciones' ..."`; this also created an active `handoff_context` (C-105).
2. User types exactly that: `"explora opciones"`.
3. **Result (since FN-024):** `_handle_explore` finds `goal_key is None`, reads the active `handoff_context`, confirms it belongs to the current project and `dse_capability == "active"`, binds `goal_key = "mejorar_estabilidad"` (C-106) — DSE runs for the goal just discussed, 0 LLM. `dse_capability` becomes `"consumed"`; `goal_key`/`levers`/`iterate_capability` are left untouched for a future H4 consumer.
4. A **second** bare `"explora opciones"` in the same operation (capability already consumed) gets a deterministic "ya exploré opciones para «X»..." message — not a silent re-bind, not an LLM call.
5. **Pre-FN-024 behavior (historical, for reference):** `resolve_explore_goal("explora opciones")` returns `None` (no domain word in the bare phrase) → with no context mechanism, `_handle_explore` fell straight to `_handle_analyze` → LLM narrated something generic. This is what C-042 being `🔴 BROKEN` meant.

**Modules/functions:** `intent_resolver.resolve_intent` (→ `"explore_design_space"`) → `intent_resolver.resolve_explore_goal` (= `goal_planner.detect_goal`, still tried first) → `orchestrator._handle_explore` → (explicit domain) `DesignExplorer.explore` directly / (bare phrase) bind via `session.handoff_context` (C-106) → `DesignExplorer.explore`, or the deterministic "already explored" message, or (no bindable context at all) `orchestrator._handle_analyze` → LLM.

**Connections:** C-045 (🟢), **C-042 (🟢, fixed FN-024)**, **C-105/C-106 (🟢, new)**.

**Notes:** This was the headline broken edge (predecessor map's Failure A) — **fixed by FN-024**. See `MISMATCHES.md`'s H1/H2 rows for the implemented design (Hybrid Operation-Scoped `HandoffContext`) and why a naive sticky-string fix was rejected in favor of it.

---

## FLOW-004 — Concrete mutation / iterate

**User-visible steps (working case):**
1. `"cambia el material a fibra de carbono"` → wizard confirms, applies, recalculates.

**User-visible steps (broken case — named lever from a plan):**
1. FLOW-002 just showed a plan whose top strategy names lever `safety_factor`.
2. User: `"incrementa safety_factor"` → `"sí"` (confirms the objective).
3. **Expected:** wizard recognizes `safety_factor` as the target variable, asks for the operation/value directly.
4. **Actual:** `iteration_draft.variable` is `None`, `semantic_state.missing_slots == ["variable"]`, wizard re-asks `"¿Qué quieres modificar?"` — the lever name the user already typed is discarded (captured only as free-text `objective`).

**Modules/functions:** `orchestrator.handle`(ITERATE) / mode-branch → `IterateInteractiveSession.start`/`answer` → `semantic_interpreter.extract_entities`/`update` → `MutationEngine`/`apply_and_recalculate`.

**Connections:** C-050, C-053 (🟢 the slot-filling mechanism itself works), **C-043 (🔴 broken — nothing feeds a plan lever into it)**.

**Notes:** Predecessor map's Failure C. The fix (H4, design-only) must gate on "lever ∈ current plan's own strategy levers," not generic free-text matching — see `MISMATCHES.md`.

---

## FLOW-005 — Calculate / simulate

**User-visible steps:**
1. `"calcula"` / `"simula"` (or implicit via iterate's final confirm) → physics recomputed, results persisted.

**Modules/functions:** `orchestrator.handle`(CALCULATE/SIMULATE) → `ActionRouter.resolve` → `CalculateAction.run`/`SimulateAction.run` → `CalculationEngine.build` → `FeasibilitySimulator.evaluate` → `StateManager.record_action` → `WorkspaceManager.save_state`.

**Connections:** C-016, C-060, C-061, C-070, C-071, C-093.

**Notes:** Fully 🟢, pure physics chain, no LLM anywhere in this flow.

---

## FLOW-006 — Continuity / `project_status` / next-step help

**User-visible steps:**
1. `"siguiente paso"` (bare) or `"ayúdame con el siguiente paso"` → Continuity's `situation`/`evidence`/`next_useful_step`, 0 LLM, correctly reflects whatever the real pending gap is (verified with two different fixtures — propulsion vs structure — in FN-023's own test suite).
2. Same phrase mid-wizard (`DEFINE_MISSING_PARAMETERS`) → same Continuity answer, wizard mode preserved (not reset, not advanced past the user).

**Modules/functions:** `intent_resolver.resolve_intent` (GUIDANCE_PATTERNS, FN-023 additions) → `orchestrator._handle_project_status` → `orchestrator.build_startup_context` → `project_continuity.build_project_continuity` (reads `project_closure.build_component_bom`, `derive_physical_requirements`, `_next_pending_block`).

**Connections:** C-035, C-080, C-036, C-082.

**Notes:** 🟢 (FN-023). This flow is the one that made the "ayúdame + next-step orientation" case work; it deliberately does **not** cover "ayúdame + a named goal" — that's FLOW-002b's territory (C-025/C-044, fixed separately by FN-025). The two are distinguished at the `resolve_intent` level: GUIDANCE (this flow, checked first) vs. the `ANALYZE_HELP_PATTERNS` half of ANALYZE (FLOW-002b, checked second) — never confused, never claiming each other's phrasing.

---

## FLOW-007 — LLM fallback / analyze

**User-visible steps:**
1. Input that matches no deterministic pattern at all → `llm_interface.interpret` → validated against the closed 4-action set → dispatched like any other structured action.
2. `"analiza el margen de seguridad"` (or any real analyze verb) → `llm_interface.analyze` → narration, optionally wrapped around a deterministic `format_goal_plan` block when a goal is also detected.

**Modules/functions:** `orchestrator._handle_user_text_inner` (bottom of the chain) → `llm_interface.interpret`/`analyze` → `PromptBuilder` → `LLMClient.complete` → `LLMResponseParser`/`ActionPolicy` (interpret path only).

**Connections:** C-022, C-100, C-101, C-102, C-103, C-104.

**Notes:** 🟢 by construction — this is the *correctly narrow* fallback. The original bugs (Failures A/B, now closed by FN-024/FN-025) were never that this flow exists; it's that turns which *should* have been claimed by a more specific deterministic layer (C-042, C-025/C-044) fell all the way down to here instead. **C-043 (H4, lever → iterate preseed) is the one remaining case of this shape** — a named lever still isn't claimed by a more specific layer before reaching the iterate wizard's own generic fallback (not this LLM flow, but the same underlying pattern).
