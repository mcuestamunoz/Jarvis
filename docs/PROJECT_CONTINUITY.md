# Project Continuity → Project Coherence

**Validated:** 2026-08-06 — workspace experiment + live CLI field notes
(`inspección-de-puentes-…`, `transportar-cámara-800g-…`).

**Updated:** 2026-08-18 — CLI polish checkpoint `checkpoint-continuity-polish` (`15aa503`). Living CLI findings: [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](../.jes/artifacts/cli_findings_post_catalog_bind_v1.md).

## Scope and related documents

This file documents the **Continuity / Project Coherence product contract** and the **FN field-note register** (acquisition fluency, session hygiene, G9-B, etc.). It is **not** the authority for Engineering Readiness rollup or Assembly Ready policy.

| Topic | Authority |
|---|---|
| Situation / Evidence / Next useful step | `project_continuity.build_project_continuity` (this doc) |
| Gap registry + `ASSEMBLY READY` rollup + snapshots A/B | [`ENGINEERING_READINESS_VISION.md`](./ENGINEERING_READINESS_VISION.md) **§11** |
| As-is wiring | [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`system_map/`](./system_map/README.md) |

Continuity may **consume** `readiness=` for catalog-gap ranking (C-108, partial) but does not define readiness rules. Do not duplicate §11 family matrix or closure snapshots here.

## Product contract (A')

Whenever the engineer **reopens** a project, Jarvis must answer:

1. **Situation** — Where am I?
2. **Evidence** — Why am I there?
3. **Next useful step** — One concrete technical action

Decisions come and go. The **project** is the stable unit.

## Deeper discovery: Project Coherence

Continuity at **startup** is not enough. After the first user turn, Jarvis often becomes a set of **operations** (analyze / iterate / define) and the project disappears from the reply.

The real property is not “conversational continuity”. It is:

> **Project Coherence** — every response must still make sense as coming from *this* engineering project. The project remains the protagonist.

```text
User
  → Project context
  → Operation (may run)
  → Project context updated
  → Response (still about the project)
```

Not:

```text
User → Operation → Response
```

### Continuity Rule (document this)

After every **relevant** operation, Jarvis must answer — implicitly or explicitly:

1. **What just changed in the project?**
2. **What is the project state now?**
3. **What is the single most useful next technical decision?**

Not always as three visible sections. But that information must exist in the response.

### Field-note metric

If you feel: *“I’m talking to an operation, not to Jarvis / not to my project”* — that is a field note. Collect 10–15 before designing a large response layer.

**Do not build a Conversation Engine yet.** Discover the shape from CLI use.

## Experiment notes (abridged)

| Need | Jarvis said | Human engineer expectation |
|------|-------------|----------------------------|
| Where am I / summary | Phase “completado” + sim OK **and** competing nexts | One situation + one next |
| “dame detalles” | Analyze / “impacto” | Project narrative (resolved / pending / why) |
| motor_count=6 vs “faltan motores” | Conflicting evidence | One coherent story |
| “define 4 motores” with 6 set | Silent execute | Conscious substitute + impact on project |

**Synthesis:** Engineers stop asking for more physics and start asking for better accompaniment. That means the calc/sim core is starting to be good enough; the next gains are in **project-first behaviour**.

## Field notes FN-001…004 — closed

| ID | Fix | Status |
|----|-----|--------|
| FN-001 | No auto-start `define_missing_params` on load when `missing_params` empty / Continuity already has next | ✅ |
| FN-002 | Continuity-first status render (hide noisy “Fase: completado” / competing suggestions) | ✅ |
| FN-003 | “dame detalles” / “cuéntame el proyecto” → `project_status` | ✅ |
| FN-004 | Confirm Sí/No before substituting defined `motor_count` (define + component intercept `"4 motores"` + iterate) | ✅ |
| Evidencia | BOM gap “número de motores” suppressed when `motor_count` in params | ✅ |
| P4 | After iterate/define/calc/sim `ok`: Continuity footer (estado + next) | ✅ |

## Field note FN-005 — Assisted Acquisition (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-005 | Wizard asks `motor_power_w`; “ayúdame a elegir” → LLM analyze | Human 3-path prompt + D8 catalog picker in DEFINE; Continuity next aligned | ✅ |

**Surface:** `motor_catalog_assist` + `param_question` / DEFINE wizard. Choosing a catalog motor writes `motor_power_w` ← `max_watts` (catalog nominal, not a flight curve) and enriches `components["motors"]`.

## Field note FN-006 — Assisted Acquisition hygiene (closed)

Localized, behavior-preserving cleanup after FN-005:

- `_answer_assisted_motor` isolates the assisted branch from the generic parameter flow.
- `offer_catalog_help()` is the public session entry point; IDLE no longer re-enters through a magic user string.
- `MotorSuggestion` and `_format_candidate_line` centralize the local candidate contract and rendering.
- Review verdict: **PASS WITH NOTES** — 160 focused/related tests and 1428 full-suite tests reported green.

### Recorded MINOR notes

1. `_question_for_param(..., suggestions=...)` still uses `list[dict] | None` instead of propagating `MotorSuggestion`.
2. `test_offer_catalog_help_is_public_session_entry_point` asserts the private worker `_offer_catalog_help`; future tests should verify only the public API and observable result.

These notes are non-blocking and do not reopen FN-006.

## Field note FN-007 — Catalog pick physical coherence (closed)

A catalog motor selection now preserves the declared `motor_count` and replaces
stale thrust with the selected motor's declared `thrust_n` through the existing
propulsion resolver. The catalog component exposes `output_magnitude="thrust_n"`,
so power, thrust, KV, weight, and actuator count remain coherent after recalculation.

Review verdict: **PASS WITH NOTES** — 49 focused tests and 1431 full-suite tests
reported green. The non-blocking note is that the end-to-end fixture reproduces
the corruption mechanism but not the field note's exact ≈7.03 N/motor value.

## Field note FN-023 — Generic next-step help → Continuity/`project_status` (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-023 | `"ayúdame con el siguiente paso"` resolved to `intent="analyze"` (`ANALYZE_PATTERNS`' bare `\bayudame\b` wins in `_resolve_strong_action_intent`, checked before `_looks_like_status_query` ever runs) → LLM → could invent an unrelated gap (e.g. `battery_capacity_wh`) instead of reading project state, even though Continuity already knew the real pending target (e.g. propellers) | Three new `GUIDANCE_PATTERNS` entries in `intent_resolver.py` (checked before `ANALYZE_PATTERNS`) route `"ayúdame con el siguiente paso"` / `"ayúdame con el siguiente"` / `"ayúdame a seguir"` to `intent="project_status"` — no new recommender: `orchestrator._handle_project_status()` already answers `project_status` via `build_startup_context()`'s existing Continuity block, 0 LLM. **No orchestrator.py change was needed** — the existing `if intent == "project_status": ...` dispatch (IDLE tail) and the existing `DEFINE_MISSING_PARAMETERS` soft-interrupt (`_dm_intent == "project_status"`, Bug 56) both already exist and pick this up automatically once `resolve_intent` returns the right value | ✅ |

Generic by construction: the new patterns match on `"ayudame"` + navigation words only, never a block/component/value name — those stay FN-005/011/014/015's territory (all of which run *before* `resolve_intent` is ever called in the orchestrator pipeline, so they are provably unaffected). Proven with **two different pending gaps**: a propulsion/propellers fixture and a structure/frame fixture both correctly surface their own `next_architecture_label` and `next_useful_step` — never `battery_capacity_wh`.

Review: suite **1558** (1550 pre-FN-023 baseline + 8 new). Verified mid-`DEFINE_MISSING` (the wizard's own pending target and Continuity's next-gap read agree by construction — both are computed from the same on-disk `design_properties`, independent of runtime session mode) — session mode is preserved (`DEFINE_MISSING_PARAMETERS` unchanged), 0 LLM, no invented gap. FN-005 (`ayúdame a elegir`), FN-011/014 (`ayúdame a declarar propulsión`), FN-015 (`ayúdame a definir`), FN-022 (`Aumentar el empuje` on closed architecture), real `analiza...` verbs, and bare `"siguiente paso"` all verified unstolen/unchanged.

No Conversation Engine, no Step D, no parallel recommender, no Create→BOM, no Continuity formula rewrite, no change to FN-020 coherence rules, no auto-DSE.

## Field note FN-022 — Engineering Intent → deterministic goal plan (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-022 | A bare engineering intention with no target value ("Aumentar el empuje", "más thrust") resolved to `intent="iterate"` (`ITERATE_PATTERNS` claims `aumentar`/`subir` before any goal layer) and opened the iterate wizard, or fell to the LLM — instead of the deterministic strategy plan already sitting in `goal_planner.GOAL_STRATEGIES`/`format_goal_plan`. Root gaps: `_GOAL_KEYWORDS` had no thrust/empuje/margen vocabulary at all, and the plan was only ever shown inside the LLM `analyze` path, never as a deterministic IDLE first response | `goal_planner._GOAL_KEYWORDS` extended for **all 4 goals** (not thrust-only — payload/autonomía/masa gaps filled too); new `goal_planner.is_engineering_intention(text) -> goal_key \| None` (`detect_goal` + a conservative "any digit present ⇒ defer to iterate" guard, `looks_like_numeric_mutate`). One new orchestrator IDLE-tail gate — `intent in ("iterate", "unknown")` and a goal is detected → new `_handle_engineering_intent(goal_key)` (reuses `format_goal_plan` + the same `sim_context` wiring `_handle_analyze` already uses, 0 LLM) — inserted immediately before the existing iterate dispatch, after every more specific route (`project_status`/`analyze`/`define_params`/`dismiss_suggestion`, and `explore_design_space`/`apply_exploration_result` which return earlier and are untouched) | ✅ |

**Primary mapping decision (documented per contract, not hidden in code):** "aumentar empuje"/"más thrust" → `mejorar_estabilidad`, because that goal's strategies already lead with the thrust/margin lever (`per_motor_max_thrust_n / motors`, `safety_factor`) — no fifth goal was created. Bare `"margen"` was also added under the same goal (previously only `"margen de seguridad"`/`"margen seguridad"` matched).

Review: suite **1550** (1533 pre-FN-022 baseline + 17 new: 9 in `test_fn022_engineering_intent.py`, 8 in `test_goal_planner.py`). Verified empirically across multiple goals, not just the probe: `"Reducir la masa"`/`"Mejorar la autonomía"`/`"mejorar estabilidad"`/`"optimiza para estabilidad"` all **already** correctly routed to `explore_design_space` before this cut (their verbs — `reducir`/`mejora`/`optimiza` — were never excluded from `EXPLORE_PATTERNS`, unlike `aumentar`/`subir`) and remain unchanged; only the `aumentar`/`subir`-verb gap was actually broken and is what this cut closes. Numeric-valued phrases (`"sube el empuje a 15N"`, `"aumentar payload a 3kg"`) still correctly reach `define_params`/iterate — unintercepted, verified the parameter was actually applied. Mid-`DEFINE_MISSING` acquisition is unaffected by construction (the new gate sits in the IDLE-only tail of `_handle_user_text_inner`, never reached while a wizard mode branch above already returned) — verified explicitly. FN-021 regression: one of FN-021's own test assertions (`"Aumentar el empuje"` → `iterate_interactive`) was updated to accept the now-better `engineering_intent` outcome, since the property FN-021 actually guards (no stale component prompt) still holds — documented inline in the test.

No Conversation Engine, no Step D, no `intent_resolver.py` change (the gate lives entirely in `orchestrator.py`/`goal_planner.py`), no auto-running DSE on the first intention turn (explore only via the existing, separate `explore_design_space` intent), no "ayúdame con el siguiente paso" → Continuity bridge.

## Field note FN-021 — Session hygiene: architecture-complete returns to IDLE (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-021 | On acquisition completion, when `_next_pending_block()` is `None` (nothing left to acquire, for **any** block type/reason), `_set_pending_next_block()` did a bare `return` — leaving `mode=DEFINE_MISSING_PARAMETERS` with stale `pending_missing_params`/`param_definition_reason`. Since the `DEFINE_MISSING` branch in `_handle_user_text_inner` runs before iterate/analyze, the **next unrelated turn** (any phrase, any intent) got answered with a leftover `component_description_prompt` for whichever key happened to be pending last. Probe: `"Aumentar el empuje"` after architecture 4/4 → still asked for the flight controller | `_set_pending_next_block()`: when `pending is None` **and** the runtime session is still in `DEFINE_MISSING_PARAMETERS` mode, call the existing `state_manager.clear_runtime_session()` (no new clearer invented) instead of returning silently. Gated on mode, not on any block/key name — callers that only pre-load from IDLE (Bug54/FN-011/FN-014/FN-015 bridges) are never inside `DEFINE_MISSING_PARAMETERS` when they call this, so the gate is a true no-op for them, unchanged | ✅ |

Generic by construction: the trigger is "no next architecture block", never a specific block/component/field — the fix is a single 2-line addition inside the pre-existing "no next block" branch, with zero new conditionals on block type or key name. The field-evidence scenario (control block, `"Aumentar el empuje"`) is used only as one of four tests — an acceptance probe, not the design center; the primary proof (`test_last_architecture_gap_clears_to_idle`) uses a minimal single-block fixture with no domain-specific branching at all.

Review: suite **1533** (1529 pre-FN-021 baseline + 4 new tests, exact). Verified both by direct smoke (reproducing the exact field sequence: control block completes last → `mode` was `DEFINE_MISSING_PARAMETERS` before the fix, `IDLE` after → `"Aumentar el empuje"` now correctly enters `iterate_interactive` instead of returning a `flight_controller` prompt) and by the test file. Non-final block completion still correctly pre-loads the next block's `pending_missing_params`/`pending_define_missing` (Bug54/FN-011 chaining untouched — that code path was not modified, only the `pending is None` branch was). FN-016 `atrás` still clears to IDLE. The numeric-param wizard path (`ParamDefinitionSession.answer()`) was already self-clearing on its own completion (`clear_runtime_session()` at its own "all params answered" branch) — the bug was specific to `_handle_component_description`'s completion path, which never cleared on its own and relied entirely on `_set_pending_next_block()`.

No Engineering Intent → goal_planner/DSE bridge, no "ayúdame con el siguiente paso" → Continuity, no Create→BOM handoff, no Conversation Engine, no Step D, no `intent_resolver.py` change.

## Field note FN-019 — Bare propeller size ("10x4.5") unblocked (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-019 | Field-blocking loop: propellers pending → Brief/`COMPONENT_PROMPTS` advertise `'10x4.5'` as the example, but bare `10x4.5` (no `"hélices"` keyword) never matched `aerial_registry`'s propeller rule (keyword-gated) → `generic_component` → FN-017/018 correctly refuse the write and re-show the same Brief → user loops forever on their own advertised example | New `component_inference.py::infer_component_for_key(raw_name, suggested_key, ...)` — forces inference against a specific rule's `property_extractor`/`completeness_evaluator` (same `extract_propeller_properties`, no new regex), bypassing keyword matching. Refactored `infer_component` to share the extraction step via a new `_spec_from_rule` helper (no duplication). Wired into `orchestrator._handle_component_description`, gated strictly: fires only when `"propellers" in expected_keys` **and** every spec `infer_components` found is still `generic_component` — never overrides a real match for another component | ✅ |

Review: suite **1527** (1520 pre-FN-019 baseline + 7 new tests, exact). Acceptance A–G verified both by direct smoke (shown in the implementation report) and by the new test file: bare `10x4.5` and spaced `10 x 4.5` save propellers (completeness `high`); `hélices 10x4.5` keyword path unaffected; bare `5` (no pitch) still re-prompts, never writes; frame pending + `10x4.5` is **not** stolen (frame's own material/masa path fires, propellers stays unset) — confirming the `expected_keys`-gate is the correct scope boundary, not a global aerial-registry change; Brief/FN-015 help still 0 LLM; `"plastico 450g"` still refused (no generic write). FN-011/013/014/015/016/017/018/020 regressions (100 tests total across those files + this one) verified green.

No `COMPONENT_PROMPTS`/Brief copy change was needed — the fix makes the already-advertised `'10x4.5'` example actually work, per the contract's stated preference. No Step D, no Conversation Engine, no change to `aerial.py`'s registry (kept the gate in the orchestrator, scoped to acquisition context, per the contract's explicit caution against a global text-pattern match).

## Field note FN-020 — Completeness coherence: architecture ↔ BOM ↔ Continuity (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-020 | Two disagreeing completeness thresholds for the same `ComponentSpec`: `_block_progress_status`/`_component_is_low` treated any non-`low` completeness as architecture-present (`4/4`), while `build_component_bom` routed any `medium` completeness into `incomplete` regardless of missing_fields — so Continuity could say `"Física orientativa en PASS, pero el sistema aún tiene gaps de componentes."` and `next_useful_step: "Completa battery…"` in the same turn as `Arquitectura: 4/4`. Live evidence: `construir-dron-6ac77f21daf5` — `battery`/`sensors` at `completeness=medium` with real measurable properties (`battery_capacity_wh`/`gps_model`) | New `project_closure.py::classify_component(key, spec, project_state) -> "missing"/"stub"/"declared"/"defined"` — single classifier, built on a shared `component_presence_tier(spec) -> "stub"/"present"` primitive and a shared `_measurable_and_missing_fields` (reuses `_MEASURABLE` + the existing motor_count-in-current_parameters rule, no forked copy). `build_component_bom` now routes its 4 buckets (unchanged shape: `defined`/`incomplete`/`missing`/`declarative`) through the classifier — `incomplete` means genuinely `stub` only now, never merely-`medium`-but-measurable (that lands in `declarative`). `orchestrator._component_is_low` is now a thin wrapper over `component_presence_tier` — provably the same primitive, behavior unchanged (`completeness == "low"`) | ✅ |

**Continuity required no code changes.** Tracing the live-project shape through `project_continuity.py`'s existing situation/evidence/next-step logic showed the contradiction lived entirely in `build_component_bom`'s bucket routing — Continuity already treats `bom["incomplete"]`/`bom["missing"]` (never `declarative`) as the strong-gap signal. Once those buckets stop misclassifying medium+measurable components, Continuity's own rules already produce the coherent result: no `"gaps de componentes"` situation, no `"Completa battery…"` next step, falls straight to `"Diseño validado en simulación (PASS)..."` when architecture is closed and nothing is genuinely `stub`/`missing`.

**Discovered and fixed within this same cut, prominently documented (not scope creep, not on the contract's file allowlist):** `tests/test_project_closure_v1.py::test_bom_kv_motor_is_incomplete_not_declarative` pinned the exact dual-threshold contradiction this contract removes (a `medium` + measurable + `missing_fields=[]` motor asserted as `"incomplete"`, not `"declarative"`) — identical shape to the live battery/sensors bug. Renamed to `test_bom_kv_motor_is_declared_not_stub` and updated to assert the new, coherent classification, with the rationale documented in the test docstring. Same precedent as FN-016/017: a discovery that directly blocks the contract's own acceptance criteria, fixed in-cut with clear documentation rather than left silently broken or treated as out-of-scope.

Review: suite **1520** (1514 pre-FN-020 baseline + 6 new tests, same total test count as the renamed test — no net addition from that file). `test_project_closure_v1.py`, `test_project_continuity.py`, `test_project_coherence.py`, `test_architecture_progress.py` (67 tests) verified green. Real `stub`/`missing` components still produce strong gap language (Continuity evidence + next_useful_step); propulsion with a genuinely missing `propellers` key is unaffected (still not `4/4`, still points at propulsion).

No FN-019 (bare `10x4.5`), no Create→BOM handoff, no Step D. `_BLOCK_COMPONENT_HINTS` copy untouched (deferred, per contract).

## Field note FN-018 — Thin Acquisition Brief + component-question harmonization (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-018 | (C0) `_try_reprompt_active_block_declaration` (FN-013's "definir propulsión" re-prompt) was the one remaining path still calling `_question_for_param` unconditionally, showing `¿Cuál es el valor de propellers?` even for a component key. (C1) Opening/re-prompting/help for a component-definition target showed only a bare one-line prompt (COMPONENT_PROMPTS, FN-017), with no "what/why/what Jarvis already knows" context | New `core/acquisition_brief.py::build_acquisition_brief(key, project_state) -> {message, question}` — composes a static per-key blurb (propellers/motors/battery/frame), a deterministic "already declared" fact from sibling components in the same architecture block (`BLOCK_TO_COMPONENTS`), and an optional thrust-per-motor "why" line (reuses `project_closure.derive_physical_requirements`, propellers/motors only, no new calculation) around the existing `COMPONENT_PROMPTS[key]` question; degrades to `{"message": "", "question": COMPONENT_PROMPTS[key]}` for any other component key (identical to FN-017). Wired into 4 entry points: `ParamDefinitionSession.start()` (Phase A open), `_try_reprompt_active_block_declaration` (FN-013 — **the C0 fix**), `_help_current_pending_acquisition` (FN-015), `_handle_component_description`'s low-completeness `elif expected_keys` branch (frame's own fine-grained material/masa branch is untouched) | ✅ |

Review: suite **1514** (1506 pre-FN-018 baseline + 8 new tests, exact). Field-note path verified via manual smoke: both Phase A open and the FN-013 reprompt now show the full hélices Brief (blurb + "Motores ya declarado(s); gap activo = propellers" + options), never `¿Cuál es el valor de propellers?`. FN-011/013/014/015/016/017 regressions (61 tests total across those six files) verified green. Frame's fine-grained material/masa probe verified unbroken and never shows propeller text.

No new subsystem: `acquisition_brief.py` is a single pure function plus two small static dicts, no session/dialogue state, no LLM. No Step D (Guided Engineering subsystem), no Conversation Engine, no `intent_resolver.py` change. Bare `"10x4.5"` registry gap remains deferred (out of this contract's scope; not attempted).

## Field note FN-017 — Component acquisition plumbing (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-017 | (a) `pending_missing_params` stayed `[]` on a live component wizard — `ParamDefinitionSession.start()` never carried it onto the session it builds. (b) Low-completeness follow-up always asked "Indica material y masa..." (frame copy) regardless of which component was actually pending. (c) A description matching only `generic_component` (e.g. "plastico 450g") was silently written as a placeholder with no physical meaning. (d) Opening question for a component wizard used the generic `¿Cuál es el valor de X?` instead of a concrete prompt. (e) IDLE `"declarar motores"` on an aerial project with motors done/propellers still pending fell through to an unrelated **ground**-domain transmission-torque wizard instead of continuing propulsion | (a) `start()` now sets `pending_missing_params`/`pending_missing_reason` from the same list when `reason == MISSING_COMPONENT_DEFINITION` (additive — Bug54's non-component callers unaffected). (b) `_handle_component_description`'s low-completeness branch is key-aware: frame keeps its fine-grained material/masa probe (only when frame is actually pending or inferred), every other `expected_keys[0]` gets `acquisition_target.COMPONENT_PROMPTS[key]`. (c) `processable` filter excludes `generic_component` matches whenever `expected_keys` is set, falling through to the targeted re-prompt instead of writing. (d) `start()`'s opening question uses `COMPONENT_PROMPTS[first]` for component-definition reasons. (e) New `orchestrator._continue_block_acquisition()` helper (dedupes the existing Bug54/FN-011/FN-013 bridge tail) — `_try_start_acquisition_from_mention` calls it when a component mention resolves to the right block but an already-satisfied component, continuing the block's real remaining gap instead of falling through to `define_params`/`intent_resolver` | ✅ |

`COMPONENT_PROMPTS` (formerly `orchestrator._COMPONENT_PROMPTS`) moved to `acquisition_target.py` as the single source of truth — both `orchestrator.py` and `param_definition_session.py` import it (no circular import: `acquisition_target.py` has no dependency on either). `orchestrator._COMPONENT_PROMPTS` kept as a local alias so no other in-file reference needed changing.

Review: suite **1506** (1496 pre-FN-017 baseline + 10 new tests, exact). Field-note path (reproduced end-to-end via the exact reported CLI sequence): **0 generic_component writes**, propellers hint shown for every unclear/wrong-target input while propellers is pending, `"hélices 10x4.5"` still saves correctly, `"declarar motores"` on the aerial fixture opens the propellers wizard (no `per_actuator_torque_nm`/torque copy anywhere in the response). FN-011/013/014/015/016 regressions (43 tests) verified green. Frame's material/masa fine-grained probe verified unbroken (`test_frame_pending_still_asks_material_masa`).

Deferred (not implemented — out of contract scope): bare `"10x4.5"` (no "hélices" keyword) is still not recognized by the aerial component registry — pre-existing, unrelated to plumbing; the FN-017 tests use the proven `"hélices 10x4.5"` fixture phrase, same precedent as FN-016. No Acquisition Brief (Step C), no Guided Engineering subsystem (Step D), no Conversation Engine, no `intent_resolver.py` change (B6 lives entirely in `orchestrator.py`).

## Field note FN-016 — Navigation words + component-key parse safety (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-016 | `"atrás"/"volver"` during `DEFINE_MISSING` fell into value-parse ("No reconozco … como valor"); a component key (e.g. `propellers`) could receive a bare float positionally, corrupting `current_parameters["propellers"]=10.0` | `config.NAVIGATION_BACK_WORDS` + `acquisition_target.is_navigation_back_phrase` (exact-match, scoped to acquisition wizards, NOT global `ESCAPE_WORDS`) → clean cancel. `param_definition_session._ACQUISITION_COMPONENT_KEYS` (single source: `BLOCK_TO_COMPONENTS`) guards `answer()`'s float parser, both at `pending[0]` and inside the positional-zip loop | ✅ |

**Discovered and fixed within this same cut** (justified by the contract's own acceptance criterion D, not scope creep): the pre-existing `UX-C` intercept in `orchestrator.py` checked `pending_missing_reason`, a field that `ParamDefinitionSession.start()` never carries onto the session it builds — meaning a real component description given right after opening Phase A acquisition (via Bug54's own `"¿Definimos X ahora?"` → `"sí"` flow, **not** specific to FN-011/013/014) never reached `_handle_component_description` and silently corrupted state instead. Fixed additively (`OR` with `param_definition_reason`, the field actually populated on a live wizard) — narrows nothing, only widens when the intercept correctly fires. Locked in by `test_component_description_works_via_original_bug54_confirmation`.

Review: suite **1496** (1485 pre-FN-016 baseline + 11 new tests, exact). Field-note path: **0 LLM** on navigation words, `collected_params` never receives a component-key float. FN-005/011/013/014/015 regressions verified green.

### Deferred notes (Corte 4 — copy, not implemented here)

1. `¿Cuál es el valor de X?` generic first-turn copy for component keys remains — deferred to Corte 4 unless it still hurts after FN-016.
2. Wrong-named-block-while-wizard-open LLM leak (FN-011/013/015 residual) remains unfixed.

## Field note FN-015 — REMOVED (G23)

FN-015 ("ayúdame a definir" as a generic acquisition-help feature — Brief
replay in-wizard, IDLE auto-open of `DEFINE_MISSING`) was **deleted in
full** by G23 (`.jes/artifacts/implementation_contract_g23_remove_fn015.md`):
zero product value (re-showed a Brief already on screen), and its IDLE
bridge duplicated Continuity/FN-011/014/023. It is not a live user-facing
verb — do not teach or reference it as one.

What survives: the original anti-LLM bug the feature was built on top of
was real, so a narrow confusion-phrase gate remains — inside
`DEFINE_MISSING` it returns a one-line re-ask of the current pending item
(no Brief, no catalog offer); at IDLE it resolves to `project_status`
(same authority as FN-023), never opening a wizard. See G23's report for
details.

### Deferred notes (FN-016 — next contract, not implemented here)

1. A named-but-wrong block phrase said *while already inside* `DEFINE_MISSING` for a different block (e.g. `"ayúdame a definir batería"` while propulsion is open) still reaches the LLM — FN-013 declines it (not the active block) and FN-015 also declines it (has a resolvable block, so it is not "bare" help). Deliberately out of scope; same class as the FN-011 "wizard-active" observation.
2. `"atrás"` / navigation vocabulary — unchanged, still FN-016 territory.

## Field note FN-014 — Acquisition Target Authority: IDLE gate for block ∪ component mentions (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-014 | `"definir propellers"` (component key, not a block alias) while IDLE → ITERATE_INTERACTIVE generic declarative flow, not acquisition | New `core/acquisition_target.py::resolve_acquisition_mention` (block ∪ component, verb-gated same as FN-011) + `orchestrator._try_start_acquisition_from_mention` — same Bug54/FN-011/FN-013 bridge, wrong-block mentions get a deterministic message instead of a silent jump | ✅ |

Review: suite **1476** (1456 pre-FN-014 baseline + FN-012/013 tests already merged + 11 new FN-014 tests). Field-note IDLE path: **0 LLM**. FN-011 (7) and FN-013 (5) regressions verified green after the refactor. One regression was caught and fixed during implementation itself (see report): the new gate initially claimed free-text component descriptions containing a block-alias word with no acquisition verb (e.g. `"estructura de fibra de carbono"`), which belongs to the global component intercept, not this gate — fixed by requiring the same declare/complete verb FN-011 already required, reusing `IntentResolver.DECLARE_BLOCK_VERB_PATTERNS` (no duplicated vocabulary, no change to `intent_resolver.py`).

### Deferred notes (FN-015 / FN-016 — next contracts, not implemented here)

1. `"ayúdame a definir"` (no block/component named) while DEFINE_MISSING is already active still reaches `analyze`/LLM — FN-014 only widened WHAT can be named (block ∪ component), not the bare-request case.
2. `"atrás"` / navigation words with no dedicated vocabulary — can still be mis-absorbed as a value inside `ParamDefinitionSession.answer`'s bidirectional keyword+number parser in Phase-B (param-driven) states.

## Field note FN-013 — Active block declaration inside DEFINE_MISSING (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-013 | `"definir propulsión"` during DEFINE_MISSING → treated as param value | Re-prompt current pending when named block == active; no restart / no LLM | ✅ |

## Field note FN-012 — Runtime snapshot draftless wizard (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-012 | Reopen restores `create_project_interactive` without `project_draft` → every turn errors | Sanitize draftless wizard modes to IDLE on persist + restore | ✅ |

## Field note FN-011 — Declare active block without LLM (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-011 | `"ayúdame a declarar propulsión"` → analyze/LLM | IDLE: verb+block alias → only if block == `_next_pending_block` → Bug 54 bridge | ✅ |

Review: **PASS WITH NOTES**. Suite **1456**. Field-note IDLE path: **0 LLM**.

### Deferred notes

1. Same `ayudame`→analyze leak while already in `DEFINE_MISSING_PARAMETERS` — needs re-prompt of current pending, not session rebuild.
2. Pre-existing generic first question for component keys (`¿Cuál es el valor de motors?`) — copy, not routing; shared with Bug 54 bridge.

## Field notes FN-008 / FN-009 / FN-010 — Guided Propulsion Acquisition (closed)

| ID | Scope | Status |
|----|-------|--------|
| FN-010 | Fallback `objective` → `parsed_constraints` when restrictions are empty placeholders | ✅ |
| FN-008 | `detallado` applies 0.6/1.2 hypotheses automatically; humanized confirmation | ✅ |
| FN-009 | Assisted thrust acquisition + IDLE propulsion-before-energy + honest catalog gap | ✅ |

`_offer_catalog_help` copy is pending-aware (N for thrust, W for power). Closed with review **PASS**.

### Pending debt (copy only — `_answer_assisted_motor`)

Non-blocking. Same W-vs-N mismatch still reachable on **error paths** when
`pending[0] == "per_motor_max_thrust_n"`:

1. **Catalog miss** — `"No encuentro el motor… indica W (ej: 350)…"`.
2. **Unrecognized value** — `"No reconozco ese valor como potencia en W…"`.

Do **not** invent SKUs or change matching to clear these; only condition the copy
on the pending assisted param (same pattern as `_offer_catalog_help`). Tracked in
[IMPLEMENTATION_TASKS.md](IMPLEMENTATION_TASKS.md) under Guided Propulsion Acquisition.

## Success criterion

> Can Jarvis look at a two-week-old project *and* survive a multi-turn session without the project vanishing behind operations?

## Not building yet

- Conversation Engine / dialogue framework
- Engineering Decision as a first-class entity
- Purchase / assembly / firmware modules
- Symptom diagnostic as a separate product slice

## Surface today

`build_startup_context` / `project_status` / CLI expose a `continuity` block (situation / evidence / one next step).

After relevant `ok` ops, `attach_project_coherence` + CLI `render_response` append the same Continuity Rule (cambio / estado / siguiente paso). Further field notes still welcome before any larger response layer.

## CLI polish checkpoint (2026-08-18)

Tag **`checkpoint-continuity-polish`** — Continuity + G10 + polish S1–S7. Key Continuity-facing changes:

| Slice | Behavior |
|---|---|
| **S1 G9-B** | When sim PASS and declared `per_motor_max_thrust_n >=` physics floor, catalog BOM gap stays in **evidence** but no longer wins `next_useful_step` with imperative "Declara empuje ≥ X". |
| **S7 G19** | PASS branch and reasoning labels bridge to **`list_motors`** and **`explora opciones`** (existing DSE path). |
| **G20 (closed)** | Closed in `d224dc1`: composite energy in-progress labels now reflect the active sub-gap (`motor_power_w` vs battery), aligning progress hint and follow-up wizard expectation. |

Full register and queue: `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` · roadmap: `docs/IMPLEMENTATION_TASKS.md`.
