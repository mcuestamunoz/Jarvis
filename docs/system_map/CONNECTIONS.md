# Connections Registry

Every directed edge in Jarvis that carries control, data, and/or state, as a first-class entity. Subsystem maps **reference** these by ID; they do not redefine them. IDs are stable within this map version (SYS-MAP-002); do not renumber on future edits — append new IDs, deprecate old ones in place with a note.

## Document structure (count correctly)

```text
CONNECTIONS.md
│
├── Canonical registry  ← THIS SECTION ONLY defines the connection count
│   └── 65 unique C-xxx  (ID space sparse through C-112)
│         63 🟢 connected · 1 ⛔ removed (C-032) · 2 🟡 partial
│
├── Derived / detail views  ← may repeat C-xxx for readability
│   └── "Detail — NN …" sections below; NOT additional connections
│
└── Forbidden transitions  ← 10 structural absences; NOT C-xxx registry edges
```

**FN-024 (2026-08-10):** C-042 flipped 🔴→🟢 (Plan→DSE now binds through a Handoff Context — see `HANDOFF_CONTEXT_DESIGN.md`); two new connections added, **C-105** (`_handle_engineering_intent` → create/replace context) and **C-106** (bound context → `_handle_explore` goal bind). Registry count moved **57 → 59**.

**FN-025 (2026-08-12):** C-025/C-044 flipped 🔴→🟢 (help + named goal now reaches the same Goal Plan path as FN-022/024, via `IntentResolver.ANALYZE_HELP_PATTERNS`/`ANALYZE_VERB_PATTERNS`). C-043 (H4) was the only remaining 🔴 in the registry — not touched by that cut.

**FN-026 (2026-08-12):** C-043 flipped 🔴→🟢 (a Goal Plan lever named by the user now preseeds the Iterate wizard's `variable` slot, via `handoff_matching.match_plan_lever` reading the active `handoff_context.levers` — C-105 stays the sole writer). **Registry was 58🟢 · 0🔴 · 1🟡 — H1–H4 all closed, only C-081 (H5, design-only, deferred) remained non-green.**

**ERF-1 (2026-08-18):** Four new connections added — **C-107** (authorities → `build_engineering_readiness`), **C-108** (readiness → Continuity catalog-gap ranking, 🟡 PARTIAL), **C-109** (startup context exposes `"readiness"`), **C-110** (CLI renders `ENGINEERING READINESS` block). Registry count moved **59 → 63**; **62🟢 · 0🔴 · 2🟡** (C-081 + C-108). Two forbidden absences added (Continuity→Readiness; persist `readiness.json`). Report: [`.jes/artifacts/implementation_report_erf1.md`](../../.jes/artifacts/implementation_report_erf1.md).

**ERF-2 (2026-08-19):** Two new connections added — **C-111** (`electrical_compatibility` pure checks → `build_engineering_readiness` gap generation), **C-112** (ESC acquisition routing in `orchestrator._handle_component_description` — out-of-scope explicit save). C-107 updated (9 subsystems, `electronics` added). C-110 updated (9 readiness lines). Registry count moved **63 → 65**; **64🟢 · 0🔴 · 2🟡** (C-081 + C-108). Report: [`.jes/artifacts/implementation_report_erf2.md`](../../.jes/artifacts/implementation_report_erf2.md).

**G23 (2026-08-20):** **C-032** flipped 🟢→⛔ **REMOVED** — FN-015 pending-help feature deleted in full (Brief replay, IDLE wizard auto-open). Replacement is **not** a new C-xxx: `is_define_missing_confusion_phrase` + `_define_missing_confusion_reask` (anti-LLM gate only; short re-ask in `DEFINE_MISSING`, `project_status` at IDLE). **C-038** callers updated (FN-015's `_help_current_pending_acquisition` removed). Registry: **63🟢 · 1⛔ · 2🟡** (C-032 removed; C-081 + C-108 partial). Report: [`.jes/artifacts/implementation_report_g23_remove_fn015.md`](../../.jes/artifacts/implementation_report_g23_remove_fn015.md).

**Motor OP Voltage Coherence (2026-09-01, v0.3.4):** No registry change. **C-030** / **C-091** detail updated: battery catalog bind still routes through `set_battery_component` only at the orchestrator layer, but that writer now **conditionally** re-calls `set_motor_component` when stored `propulsion_resolution` was never `voltage_validated` or is validated at an incompatible pack voltage — preserving the P2-2/IC2 lock when already validated at the same voltage. `library.resolve_operating_point` exact match now requires `voltage_v is not None`. Report: [`.jes/artifacts/implementation_report_motor_op_voltage_coherence.md`](../../.jes/artifacts/implementation_report_motor_op_voltage_coherence.md).

**Do not count** leading `| C-xxx |` table cells across the whole file as the registry size — several IDs are re-listed in derived summary tables. The only authoritative count is the length of **Canonical registry** below.

Visual companions (`DIAGRAMS.md`, `jarvis-system-map.canvas.tsx`) must mirror this registry; if they diverge, **this file wins**.

## Status taxonomy

```text
🟢 CONNECTED       — explicit path in code; works for intended use
🟡 PARTIAL         — implicit, incomplete, or only some payloads handled
🔴 BROKEN          — path claims to work but fails / falls to wrong layer (CLI evidence)
⚪ NOT IMPLEMENTED — designed/discussed but no code path exists
⚠ SUSPECT          — LLM or the wrong layer appears to decide (authority smell)
```

## Canonical registry

**65 unique edges.** Append new IDs here first; then add a Detail section. Derived tables elsewhere in this file must not be treated as new edges.

| ID | From | To | Status |
|---|---|---|---|
| C-001 | User | CLI adapter | 🟢 |
| C-002 | CLI/MCP adapter | `orchestrator.handle_user_text` | 🟢 |
| C-003 | CLI/MCP adapter (structured) | `orchestrator.handle` | 🟢 |
| C-010 | Runtime | Global commands intercept | 🟢 |
| C-011 | Runtime | FN-004 structural-confirm consume | 🟢 |
| C-012 | Runtime | Bug 54 pending_define_missing consume | 🟢 |
| C-013 | Runtime | Global component intercept (any mode) | 🟢 |
| C-014 | Runtime | Mode-branch dispatch | 🟢 |
| C-015 | Runtime | Parameter ingestion layer | 🟢 |
| C-016 | `orchestrator.handle` | `ActionRouter.resolve` → `Action.run` | 🟢 (dual-dispatch seam, documented not fixed) |
| C-020 | Runtime | `IntentResolver.resolve_intent` | 🟢 |
| C-021 | Intent (`project_status`) | `_handle_project_status` | 🟢 |
| C-022 | Intent (`analyze`) | `_handle_analyze` | 🟢 |
| C-023 | Intent (`define_params`) | `start_define_missing_params` bridge | 🟢 |
| C-024 | Intent (`dismiss_suggestion`) | `_handle_dismiss_suggestion` | 🟢 |
| C-025 | "ayúdame" + named goal | Intent → engineering_intent (was analyze) | 🟢 (FN-025) |
| C-030 | Runtime (IDLE) | FN-005 assisted motor help | 🟢 |
| C-031 | Runtime (IDLE) | FN-014 acquisition mention → wizard open | 🟢 |
| C-032 | ~~Runtime (IDLE) FN-015 pending-help~~ | REMOVED (G23) | ⛔ |
| C-033 | Runtime (DEFINE_MISSING) | FN-013 reprompt active block | 🟢 |
| C-034 | Runtime (DEFINE_MISSING) | FN-016 navigation cancel | 🟢 |
| C-035 | Intent (`project_status`, FN-023 phrasing) | `_handle_project_status` (Continuity) | 🟢 |
| C-036 | Continuity | Acquisition (`_next_pending_block` shared read) | 🟢 |
| C-037 | Acquisition wizard completion | `_set_pending_next_block` → next block or IDLE | 🟢 (FN-021 invariant) |
| C-038 | Acquisition wizard open | `acquisition_brief.build_acquisition_brief` | 🟢 |
| C-040 | Intent (`iterate`/`unknown`) | `is_engineering_intention` → `_handle_engineering_intent` | 🟢 (IDLE / via C-052; **not** mid DEFINE_MISSING — G8 / SYS-MAP-004) |
| C-041 | `_handle_engineering_intent` | `goal_planner.format_goal_plan` | 🟢 |
| C-042 | Goal Plan CTA (`"explora opciones"`) | DSE (goal binding) | 🟢 (FN-024 — binds via `handoff_context`, see C-105/C-106) |
| C-043 | Goal Plan lever (e.g. `safety_factor`) | Iterate wizard preseed | 🟢 (FN-026 — via `handoff_matching.match_plan_lever`) |
| C-044 | "ayúdame" + named goal | Plan/Explore | 🟢 (= C-025, cross-ref; H3 — FN-025) |
| C-045 | Intent (`explore_design_space`) | `_handle_explore` → `DesignExplorer.explore` | 🟢 (when `goal_key` is resolved, explicitly or via C-106 bind) |
| C-046 | `_handle_explore` result | `_handle_apply_exploration` (via `session.last_exploration_result`) | 🟢 |
| C-105 | `_handle_engineering_intent` (successful plan) | Create/replace `session.handoff_context` | 🟢 (FN-024, new) |
| C-106 | Active `handoff_context` (`dse_capability="active"`, matching `project_id`) | `_handle_explore` goal bind | 🟢 (FN-024, new) |
| C-050 | `orchestrator.handle` (ITERATE) | `IterateInteractiveSession.start`/`answer` | 🟢 |
| C-051 | ITERATE_INTERACTIVE | Bug 7 soft-interrupt (`project_status`/`analyze`) | 🟢 |
| C-052 | ITERATE_INTERACTIVE | Calibration preempt → re-dispatch as IDLE | 🟢 |
| C-053 | `IterateInteractiveSession.answer` | `semantic_interpreter` slot filling | 🟢 |
| C-054 | Iterate final confirm | `MutationEngine` / `apply_and_recalculate` | 🟢 |
| C-060 | `current_parameters` | `CalculationEngine.build` | 🟢 |
| C-061 | `component_resolver.resolve_propulsion_parameters` | Calculation input override | 🟢 |
| C-070 | `CalculationBundle` | `FeasibilitySimulator.evaluate` | 🟢 |
| C-071 | `SimulationResult` | `state_manager.record_action` → persisted `latest_results` | 🟢 |
| C-080 | ProjectState + BOM + requirements | `project_continuity.build_project_continuity` | 🟢 |
| C-081 | Sim (`safety_margin_ratio`) | Continuity `next_useful_step` (PASS+risky thread) | 🟡 PARTIAL (WEAK) |
| C-082 | `classify_component` | BOM buckets (`build_component_bom`) + `sku_resolved` display | 🟢 (FN-020, IC 3 propeller branch) |
| C-083 | `classify_component` (via `component_presence_tier`) | `_block_progress_status` (architecture presence) | 🟢 (FN-020, same classifier as C-082) |
| C-084 | ProjectState | `PhaseLayer.infer` | 🟢 |
| C-085 | Context (incl. C-084) | `ReasoningLayer.build` | 🟢 |
| C-090 | Free text | `component_inference.infer_component[s]` → `ComponentSpec` | 🟢 (pure) |
| C-091 | `ComponentSpec` | `component_writers.set_*` → `design_properties.components[key]` | 🟢 (single write point) |
| C-092 | Any orchestrator checkpoint | `StateManager.set_runtime_session` / `clear_runtime_session` | 🟢 |
| C-093 | `ProjectState` | `WorkspaceManager.save_state` → `state.json` | 🟢 |
| C-094 | `ProjectState` | `WorkspaceManager.render_views` → `estado_actual.md`/`sistema.md` | 🟢 |
| C-100 | `orchestrator` | `llm_interface.interpret` → `PromptBuilder.build_messages` | 🟢 |
| C-101 | `PromptBuilder` messages | `LLMClient.complete` (Ollama) | 🟢 |
| C-102 | Raw LLM response | `LLMResponseParser.parse/validate_for_runtime` (`ActionPolicy`) | 🟢 |
| C-103 | Validated `action_request` | `orchestrator.handle` (closed 4-verb set) | 🟢 |
| C-104 | `orchestrator` | `llm_interface.analyze` → narration string | 🟢 |
| C-107 | `ProjectState` + closure/arch/sim/electrical authorities | `engineering_readiness.build_engineering_readiness` (9 subsystems, ERF-2; IC 1 requirements explicit-none) | 🟢 (ERF-1, updated ERF-2 + IC 1) |
| C-108 | `EngineeringReadinessResult` | `project_continuity.build_project_continuity(readiness=…)` — catalog-gap ranking only | 🟡 PARTIAL (ERF-1) |
| C-109 | `orchestrator.build_startup_context` | startup context `"readiness"` field | 🟢 (ERF-1) |
| C-110 | CLI `render_startup_context` | `ENGINEERING READINESS` block (9 lines, ERF-2) | 🟢 (ERF-1, updated ERF-2) |
| C-111 | `electrical_compatibility` checks | `engineering_readiness` gap generation (4 electrical gap types) | 🟢 (ERF-2) |
| C-112 | `orchestrator._handle_component_description` | ESC out-of-scope explicit save (`OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS`) | 🟢 (ERF-2, FN-ESC) |

## Forbidden transitions (not registry edges)

**10** normative absences — listed even where no code path exists, so a future change can be checked against them. **Do not add these to the 63.** They have no `C-xxx` IDs.

```text
LLM → acquisition target            NOT IMPLEMENTED — ActionPolicy.ALLOWED_ACTIONS has no such action (structurally impossible today)
LLM → goal selection                NOT IMPLEMENTED — same
LLM → DSE configuration choice      NOT IMPLEMENTED — same
Continuity → mutate ProjectState    NOT IMPLEMENTED — project_continuity.py has zero writes/I-O
Continuity → engineering_readiness  NOT IMPLEMENTED — circularity forbidden (ERF-1 ★7); Readiness composes authorities, never Continuity output
engineering_readiness → persist readiness.json  NOT IMPLEMENTED — derived-on-read only (ERF-1); no parallel persisted readiness state
DSE → silent mutate without apply   NOT IMPLEMENTED — DesignExplorer docstring guarantee + C-046 is the only apply path, and it is a distinct, explicit user turn
Goal Planner → write physical params NOT IMPLEMENTED — goal_planner.py has zero writes/I-O
Component Inference → write direct  NOT IMPLEMENTED — only component_writers.py (C-091) may write components[key]
Analyze (LLM) → choose next gap     NOT IMPLEMENTED — analyze()'s return is a message string only, never parsed as routing
```

None of these are currently violated in code (all `NOT IMPLEMENTED`, i.e. structurally absent, which is the desired state — see `AUTHORITY.md` for the mechanism). They are listed here as a checklist for future FN reviews, not because a violation was found.

---

## Derived detail (may repeat C-xxx)

Sections below expand evidence for canonical IDs. Summary tables that re-list IDs (e.g. C-021…024, C-084/085, C-093/094) are **derived views**, not additional connections.

## Detail — 00 Entry

### C-001 — User → CLI adapter
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | terminal stdin loop |
| Symbols | `adapters/cli/main.py` main loop |
| Payload | raw text line |
| Authority | n/a (input boundary) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `src/jarvis/adapters/cli/main.py` |

### C-002 — CLI/MCP adapter → `orchestrator.handle_user_text`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct method call |
| Symbols | `JarvisOrchestrator.handle_user_text(user_input, llm_interface)` |
| Payload | `user_input: str`, `llm_interface` |
| Authority | Orchestrator (routing owner from here down) |
| Mutation | Indirect (delegates) |
| LLM | INDIRECT (passed through, only invoked deep in the chain — C-100/C-104) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:559` (`handle_user_text`), `:577` (`_handle_user_text_inner`) |

### C-003 — CLI/MCP adapter (structured) → `orchestrator.handle`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct method call, `ActionRequest` |
| Symbols | `JarvisOrchestrator.handle(request)` |
| Payload | `ActionRequest` (`action`, `parameters`) |
| Authority | Orchestrator / `ActionRouter` |
| Mutation | Indirect (delegates to Action objects) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:199` |

---

## Detail — 01 Runtime

### C-010 — Runtime → Global commands intercept
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | function call, first line of `_handle_user_text_inner` |
| Symbols | `_handle_global_commands` |
| Payload | `user_input` |
| Authority | escape-word table (`config.ESCAPE_WORDS`) |
| Mutation | YES (may `clear_runtime_session`) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:579` |

### C-011 — Runtime → FN-004 structural-confirm consume
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | session-field check (`pending_structural_change`) |
| Symbols | `_consume_structural_confirm` |
| Payload | sí/no answer |
| Authority | session state (FN-004) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:587` |

### C-012 — Runtime → Bug 54 pending_define_missing consume
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | session-field check + affirmative-phrase match |
| Symbols | `_is_affirmative`, `start_define_missing_params` |
| Payload | sí/no answer |
| Authority | session state (Bug 54) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:596` |

### C-013 — Runtime → Global component intercept (any mode)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | free-text component detection, mode-independent |
| Symbols | `_interceptable_component_specs`, `_should_intercept_component`, `_handle_component_description` |
| Payload | inferred `ComponentSpec[]` |
| Authority | `component_inference` (C-090) |
| Mutation | YES (via C-091) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:330` (`_interceptable_component_specs`), `:368` (`_should_intercept_component`), `:646` (call site) |

### C-014 — Runtime → Mode-branch dispatch
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `if current_session.mode == OrchestratorMode.X` chain |
| Symbols | `OrchestratorMode` (5 values) |
| Payload | — |
| Authority | `StateManager` session mode |
| Mutation | Indirect |
| LLM | INDIRECT (ITERATE_INTERACTIVE's Bug 7 soft-interrupt can reach `analyze`) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:660-830` |

### C-015 — Runtime → Parameter ingestion layer
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct param input recognized before intent resolution |
| Symbols | `param_definition_session.try_ingest` |
| Payload | e.g. "4 motores" |
| Authority | `ParamDefinitionSession` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:840` |

### C-016 — `orchestrator.handle` → `ActionRouter.resolve` → `Action.run` (dual-dispatch seam)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | dict lookup + method call |
| Symbols | `ActionRouter.resolve(ActionName)`, `CreateProjectAction/IterateAction/CalculateAction/SimulateAction.run` |
| Payload | `parameters: dict` |
| Authority | `ActionRouter.ALLOWED` (4-action closed set — same set `ActionPolicy` enforces for the LLM) |
| Mutation | YES (varies by action) |
| LLM | NO (this is the *target* of both LLM's `action_request` and the orchestrator's own resolved-intent handoff — see C-019/C-103) |
| Status | 🟢 CONNECTED — but reached from **two** independent call sites (`orchestrator.handle` directly, and `_handle_user_text_inner`'s `intent in {...}` branch calling `self.handle(...)`), which is the documented dual-dispatch seam. Not a bug; a structural note. |
| Evidence | `core/orchestrator.py:257` (`handle`'s own dispatch), `:901-904` (`_handle_user_text_inner`'s handoff into `handle`), `core/action_router.py` |

---

## Detail — 02 Intent

### C-020 — Runtime → `IntentResolver.resolve_intent`
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | function call |
| Symbols | `IntentResolver.resolve_intent(user_input) -> IntentType` |
| Payload | `user_input: str` → one of 13 `IntentType` values |
| Authority | `IntentResolver` (regex tables, GUIDANCE before ANALYZE before ITERATE, see `AUTHORITY.md`) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:845`, `core/intent_resolver.py:280` |

### C-021 / C-022 / C-023 / C-024 — Intent → dedicated handler
> Derived summary — IDs already in Canonical registry (not +4 edges).

| ID | Intent | Handler | Status |
|---|---|---|---|
| C-021 | `project_status` | `_handle_project_status` (0 LLM, Continuity-backed) | 🟢 |
| C-022 | `analyze` | `_handle_analyze` (LLM narration) | 🟢 |
| C-023 | `define_params` | `start_define_missing_params` bridge | 🟢 |
| C-024 | `dismiss_suggestion` | `_handle_dismiss_suggestion` | 🟢 |

Evidence: `core/orchestrator.py:846,850,864,906`.

### C-025 — "ayúdame" + named goal → Intent → `analyze` 🟢 CONNECTED (FN-025)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `intent == "analyze"` is now split at the orchestrator: `IntentResolver.ANALYZE_PATTERNS` was split into `ANALYZE_VERB_PATTERNS` (analiza/evalúa/revisa/...) and `ANALYZE_HELP_PATTERNS` (ayúdame/oriéntame/...), same union, zero change to `resolve_intent`'s own classification. When the match came from the help group only (not the verb group), the orchestrator checks `goal_planner.is_engineering_intention` before falling to `_handle_analyze` |
| Symbols | `intent_resolver.ANALYZE_VERB_PATTERNS`, `ANALYZE_HELP_PATTERNS` (new, FN-025), `orchestrator`'s `intent == "analyze"` branch, `goal_planner.is_engineering_intention`, `orchestrator._handle_engineering_intent` (reused, unchanged, same as C-040) |
| Payload | e.g. `"ayudame a mejorar la estabilidad"` → `goal_key="mejorar_estabilidad"` |
| Authority | `goal_planner.is_engineering_intention` — the exact same authority C-040/FN-022 already uses; no second goal detector |
| Mutation | YES (session) — routes into `_handle_engineering_intent`, which creates/replaces `handoff_context` via the existing C-105, same as any other engineering-intent entry |
| LLM | NO for help+goal (routes to the plan) and for bare help with no goal (routes to `project_status`). Still YES for genuine analytical verbs (`"analiza el margen..."`) and for help+verb combinations where a real analyze verb is also present (verb wins, unaffected) — this gate never claims those. |
| Status | 🟢 CONNECTED (FN-025, 2026-08-12) |
| Evidence | `core/intent_resolver.py` (`ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS`), `core/orchestrator.py`'s `intent == "analyze"` branch, `tests/test_fn025_help_goal_intent.py` (T1–T8 + 2 regressions). Verified live: `"ayudame a mejorar la estabilidad"` → `action="engineering_intent"`, `goal_key="mejorar_estabilidad"`, `handoff_context` created; `"ayudame con el siguiente paso"` (FN-023) and `"analiza el margen de seguridad"` both unaffected. Same underlying fix as C-044 (cross-ref, one finding, one fix). |

---

## Detail — 03 Acquisition

### C-030 — Runtime (IDLE + DEFINE_MISSING) → catalog pick UX (motor / propeller / battery)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | phrase match + numbered list + pick index |
| Symbols | `is_help_choose_phrase`, `_try_start_assisted_motor_help`; `_offer/_apply_component_{motor,propeller,battery}_catalog*`; `catalog_bind.bind_*_from_catalog` → `component_writers.set_*` |
| Payload | `"ayúdame a elegir"`, pick `N` |
| Authority | `motor_catalog_assist.py`, `battery_catalog_assist.py`, `catalog_bind.py`, orchestrator pick handlers |
| Mutation | YES (bind + component writer). Battery pick calls `set_battery_component` only at orchestrator layer; that writer **conditionally** re-calls `set_motor_component` when OP was never voltage-validated or pack voltage changed beyond `_OP_VOLTAGE_EPSILON_V` (v0.3.4 MOP-2). Unconditional motor re-call on every battery bind remains forbidden (P2-2/IC2 lock). |
| LLM | NO |
| Status | 🟢 CONNECTED (G21 motor; v0.3.0 propeller; IC 2 battery + G27 hardening; v0.3.4 MOP-2 conditional OP re-resolve) |
| Evidence | `core/orchestrator.py`, `core/motor_catalog_assist.py`, `core/battery_catalog_assist.py`, `core/catalog_bind.py`, `core/component_writers.py` (`set_battery_component` tail), `tests/test_propeller_catalog_bind_ux.py`, `tests/test_battery_catalog_bind_ux.py`, `tests/test_dse_motor_op_dual_truth.py` |

### C-031 — Runtime (IDLE) → FN-014 acquisition mention → wizard open
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | mention resolution + Bug54 bridge |
| Symbols | `_try_start_acquisition_from_mention`, `acquisition_target.resolve_acquisition_mention`, `_continue_block_acquisition` |
| Payload | "declarar/definir/completar X" (block or component) |
| Authority | `acquisition_target.py` + `_next_pending_block` |
| Mutation | YES (session `pending_*`) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:630-634`, `core/acquisition_target.py` (FN-011/013/014) |

### C-032 — REMOVED (G23)

The FN-015 pending-help feature this connection described (IDLE bare-help
phrase → auto-open `DEFINE_MISSING` wizard → deterministic help / Brief
replay) was **deleted in full** by G23
(`.jes/artifacts/implementation_contract_g23_remove_fn015.md`) — zero
product value; duplicated Continuity/FN-011/014/023.

**Deleted symbols:** `_try_help_define_pending_idle`, `_help_current_pending_acquisition`, `is_help_define_pending_phrase` (product framing).

**Replacement (not a new C-xxx — Runtime-internal anti-LLM gate only):**

| Mode | Mechanism | Symbols |
|---|---|---|
| IDLE | confusion phrase → Continuity, no wizard | `is_define_missing_confusion_phrase` → `_handle_project_status` (`orchestrator.py:~832-838`) |
| DEFINE_MISSING | confusion phrase → one-line re-ask, no Brief/catalog | `is_define_missing_confusion_phrase` → `_define_missing_confusion_reask` (`orchestrator.py:~972-976`, method ~1614-1652) |

**Why not folded into C-035 `GUIDANCE_PATTERNS`:** that table is resolved globally; mid-wizard it would collide with Bug-56's `project_status` intercept and dump full Continuity instead of the short re-ask (G23 report §4).

| Field | Value |
|---|---|
| Status | ⛔ REMOVED |

### C-033 — Runtime (DEFINE_MISSING) → FN-013 reprompt active block
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | in-wizard re-prompt, no restart |
| Symbols | `_try_reprompt_active_block_declaration`, `resolve_declare_block_request` |
| Payload | "definir/declarar X" while X's wizard is already open |
| Authority | `intent_resolver.resolve_declare_block_request` + `acquisition_brief` (FN-018) |
| Mutation | NO (re-reads, doesn't reset `collected_params`) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:~957-960` (FN-013 reprompt gate), `~1550-1612` (`_try_reprompt_active_block_declaration`) |

### C-034 — Runtime (DEFINE_MISSING) → FN-016 navigation cancel
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | exact-match navigation word → clean cancel |
| Symbols | `is_navigation_back_phrase`, `clear_runtime_session` |
| Payload | "atrás"/"volver"/"vuelve" |
| Authority | `acquisition_target.py` (scoped, not global `ESCAPE_WORDS`) |
| Mutation | YES (clears session) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:770-778` |

### C-035 — Intent (`project_status`, FN-023 phrasing) → `_handle_project_status`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `GUIDANCE_PATTERNS` (checked before `ANALYZE_PATTERNS`) |
| Symbols | `intent_resolver.GUIDANCE_PATTERNS` (FN-023's 3 additions), `_handle_project_status` |
| Payload | "ayúdame con el siguiente paso"; also bare `"ayúdame a definir"` / confusion phrases at **IDLE only** (G23 — dedicated check, **not** `GUIDANCE_PATTERNS`; see C-032 replacement) |
| Authority | Continuity (via `build_startup_context`) |
| Mutation | NO (read-only; may set Bug54 `pending_define_missing` as an existing side effect, IDLE only) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-023; G23 IDLE confusion phrases share this authority) |
| Evidence | `core/intent_resolver.py` (GUIDANCE_PATTERNS FN-023 block), `core/orchestrator.py:~832-838` (G23 IDLE confusion → `_handle_project_status`), `~972-976` (DEFINE_MISSING confusion re-ask — **not** this connection); mid-wizard `"siguiente paso"` family still via C-014's `_dm_intent == "project_status"` (Bug 56) |

### C-036 — Continuity → Acquisition (`_next_pending_block` shared read)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | both read the same underlying computation |
| Symbols | `orchestrator._next_pending_block`, `_block_progress_status`, consumed by both `_try_start_acquisition_from_mention` (Acquisition) and `build_startup_context`'s `arch_progress`/`next_architecture_label` (Continuity) |
| Payload | `(block_key, status)` or `None` |
| Authority | `_block_progress_status` (via `classify_component`, FN-020) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — this shared-source property is *why* C-082/C-083 (FN-020) closed the old architecture-vs-BOM contradiction |
| Evidence | `core/orchestrator.py:1438-1463` (`_next_pending_block`, `_architecture_progress_str`) |

### C-037 — Acquisition wizard completion → `_set_pending_next_block` → next block or IDLE
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | post-completion hook, gated on `_next_pending_block` result and current mode |
| Symbols | `_set_pending_next_block`, `StateManager.clear_runtime_session` |
| Payload | — |
| Authority | Orchestrator (FN-021 invariant) |
| Mutation | YES (session) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-021 closed the "stays in DEFINE_MISSING forever" bug) |
| Evidence | `core/orchestrator.py:1366-1437`, `tests/test_fn021_session_hygiene.py` |

### C-038 — Acquisition wizard open → `acquisition_brief.build_acquisition_brief`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, composes blurb + known facts + why-line |
| Symbols | `build_acquisition_brief(key, project_state)` |
| Payload | `{"message": str, "question": str}` |
| Authority | `acquisition_brief.py` (FN-018), reuses `COMPONENT_PROMPTS` (`acquisition_target.py`) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/acquisition_brief.py::build_acquisition_brief`. **Live callers only** (G23 removed FN-015 help path): `param_definition_session.start` (wizard open), `orchestrator._try_reprompt_active_block_declaration` (FN-013 reprompt), `orchestrator._handle_component_description` (low-completeness re-prompt). **Not** called from confusion re-ask (`_define_missing_confusion_reask` returns one-line `question` only). Motors Brief advertises `ayúdame a elegir` (G21); no `ayúdame a definir` bullet. |

---

## Detail — 04 Engineering

### C-040 — Intent (`iterate`/`unknown`) → `is_engineering_intention` → `_handle_engineering_intent`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | goal detection + numeric-mutate guard, gated to two intent values only |
| Symbols | `goal_planner.is_engineering_intention`, `orchestrator._handle_engineering_intent` |
| Payload | e.g. "aumentar el empuje" → `goal_key="mejorar_estabilidad"`; "reducir payload" → `goal_key="reducir_payload"` (F-1) |
| Authority | `goal_planner.py` (FN-022) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-022) — **reachability is mode-gated** (SYS-MAP-004 / G8). Reachable from **IDLE**, and from **ITERATE_INTERACTIVE** via C-052 preempt-and-redispatch. **Not reachable from `DEFINE_MISSING_PARAMETERS`** while `param_definition_reason`/`pending_missing_reason` == `MISSING_COMPONENT_DEFINITION`: UX-C (`_handle_component_description`) intercepts unconditionally and returns before this gate. The runtime comment at the gate already states it runs only in IDLE; earlier map rows omitted that caveat (map overclaim by omission — not a broken connection when IDLE). |
| Evidence | `core/orchestrator.py:931-936` (C-040 gate; FN-025 also calls `is_engineering_intention` earlier at ~`:880` inside the analyze branch); `core/goal_planner.py`; contrast C-052. Finding: G8 in `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`; audit `.jes/artifacts/sys_map_004_routing_audit.md`. |

### C-041 — `_handle_engineering_intent` → `goal_planner.format_goal_plan`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, deterministic template over `GOAL_STRATEGIES` |
| Symbols | `format_goal_plan(goal_key, sim_context)`, `_prioritize_strategies` |
| Payload | plan text (numbered strategies + levers) |
| Authority | `goal_planner.GOAL_STRATEGIES` |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:2245-2263` (`_handle_engineering_intent`) |

### C-042 — Goal Plan CTA (`"explora opciones"`) → DSE (goal binding) 🟢 CONNECTED (FN-024)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | bare `"explora opciones"` (`goal_key is None`) binds through `session.handoff_context` — see C-105 (create) / C-106 (bind) — when the context belongs to the current project (`project_id` match) and `dse_capability == "active"` |
| Symbols | `orchestrator._handle_explore`, `schemas.action_schema.HandoffContext` |
| Payload | `handoff_context.goal_key` (never invented — reused from the plan `_handle_engineering_intent` already showed) |
| Authority | `HandoffContext` created by `_handle_engineering_intent` (C-105); `_handle_explore` only reads it, never invents a goal |
| Mutation | YES (session only) — successful bind+explore sets `dse_capability = "consumed"`; `goal_key`/`levers`/`iterate_capability` untouched |
| LLM | NO for the bound case. A second bare `"explora opciones"` after consumption gets a deterministic 0-LLM message (not analyze — see `05_iteration`/`04_engineering` maps). Falls to `_handle_analyze` only when no bindable context exists at all (no context, wrong project, or unknown goal) — same honest fallback as before FN-024. |
| Status | 🟢 CONNECTED (FN-024, 2026-08-10) |
| Evidence | `core/orchestrator.py::_handle_explore` (bind logic), `::_handle_engineering_intent` (C-105, context creation), `tests/test_fn024_handoff_context_dse.py` (T1–T9). Verified live: plan for `mejorar_estabilidad` → `"explora opciones"` → `action="explore_design_space"`, `goal_key="mejorar_estabilidad"`, 0 LLM. Design authority: `HANDOFF_CONTEXT_DESIGN.md` Decision log (Hybrid Operation-Scoped Context). H2 (CTA honesty, M-002) closed as a consequence — the CTA's `'explora opciones'` promise is now true by construction (a fresh active context is always created immediately before the CTA is built). |

### C-043 — Goal Plan lever (e.g. `safety_factor`) → Iterate preseed 🟢 CONNECTED (FN-026)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `orchestrator._preseed_variable_from_handoff` runs right before an `intent == "iterate"` action request is dispatched to `self.handle(...)`. It reads the active `handoff_context` (C-105, never a second store), guards on `handoff.iterate_capability == "active"` and `handoff.project_id == project_state.project_id`, then calls the pure helper `handoff_matching.match_plan_lever(user_input, handoff)`, which checks each lever's full string and its slash-separated tokens against the normalized user text and resolves a hit to a canonical variable via the exact same `normalize_alias`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` chain `iterate_interactive_session._apply_answer` already uses at step 1 — no parallel vocabulary. |
| Symbols | `orchestrator._preseed_variable_from_handoff`, `handoff_matching.match_plan_lever`, `iterate_domain._is_valid_variable`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` |
| Payload | "incrementa safety_factor" (after a `mejorar_estabilidad` plan) → confirm → `iteration_draft.variable == "safety_factor"`, wizard jumps straight to step 2 — step 1 ("¿Qué quieres modificar?") never asked |
| Authority | `GOAL_STRATEGIES[goal_key][i]["lever"]` membership (via `handoff_context.levers`) — exactly the H4 design in `MISMATCHES.md`/`HANDOFF_CONTEXT_DESIGN.md` |
| Mutation | YES (session only — `iteration_draft.variable` seeded at wizard start); never touches `dse_capability` or wipes the context |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-026, 2026-08-12) |
| Evidence | `core/handoff_matching.py::match_plan_lever`, `core/orchestrator.py::_preseed_variable_from_handoff`, `tests/test_fn026_lever_iterate_preseed.py` (T1–T8), `tests/test_fn025_help_goal_intent.py::test_iterate_lever_preseed_now_implemented` (regression flipped from the pre-FN-026 pin). A compound lever like `"per_motor_max_thrust_n / motors"` (aumentar_payload) or `"total_power_w / motors"` (mejorar_autonomia) only preseeds from its settable sibling token (`motors`) — a derived/computed token (`total_power_w`) fails `_is_valid_variable` and is honestly skipped, same as if the user had typed it at step 1 manually. |

### C-044 — "ayúdame" + named goal → Plan/Explore (cross-ref C-025) 🟢 CONNECTED (FN-025)
Same underlying phrase and root cause as **C-025** — listed under both Intent and Engineering because the fix could plausibly live in either layer. **FN-025 chose Option A** (orchestrator-side gate, per the contract's preferred option): the fix lives in `orchestrator.py`'s `intent == "analyze"` branch, reusing `intent_resolver.py`'s new `ANALYZE_HELP_PATTERNS`/`ANALYZE_VERB_PATTERNS` split — not a `GUIDANCE_PATTERNS` extension (Option B was considered and rejected: it would have required teaching `resolve_intent` itself to reach into `goal_planner`, blurring intent classification with goal detection). Full evidence at C-025 (do not treat as two separate findings when counting BROKEN edges — now zero, both closed by the one fix).

### C-045 — Intent (`explore_design_space`) → `_handle_explore` → `DesignExplorer.explore`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct call, in-memory only |
| Symbols | `_handle_explore`, `DesignExplorer.explore(project_state, goal_key)`, `EXPLORATION_GRIDS` |
| Payload | `ExplorationResult` (candidates, viable, baseline_simulation) |
| Authority | `design_explorer.py` |
| Mutation | NO ("100% en memoria: no escribe en disco, no muta project_state") |
| LLM | NO — **when `goal_key` is resolved** either explicitly from text or via a C-106 bind. Falls to `_handle_analyze` only when no `goal_key` and no bindable context exist. |
| Status | 🟢 CONNECTED (`goal_key` now resolves either from explicit text or, since FN-024, from a bound `handoff_context` — see C-042/C-106) |
| Evidence | `core/orchestrator.py:912-917,1981-2046`, `core/design_explorer.py` |

### C-046 — `_handle_explore` result → `_handle_apply_exploration`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | runtime-session field carries the result across turns |
| Symbols | `session.last_exploration_result`, `_handle_apply_exploration` |
| Payload | best viable candidate's delta |
| Authority | Orchestrator (DSE v1.1) |
| Mutation | YES — this is the one DSE-adjacent path that **does** write `ProjectState`, and only on an explicit "aplica" turn |
| LLM | NO |
| Status | 🟢 CONNECTED — **this is the existing precedent** the `MISMATCHES.md` design appendix points to for how a future Plan/Handoff Context (H1) should be shaped: runtime-only, consumed-and-cleared by its own explicit next action |
| Evidence | `core/orchestrator.py:919-923,2047-2090`, `schemas/action_schema.py` (`InteractiveSessionState.last_exploration_result`) |

### C-105 — `_handle_engineering_intent` (successful plan) → create/replace `handoff_context` (FN-024, new)
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | unconditional create-or-replace, every successful `_handle_engineering_intent(goal_key)` call builds a fresh `HandoffContext` and overwrites any previous one via `session.model_copy(update={"handoff_context": ...})` |
| Symbols | `orchestrator._handle_engineering_intent`, `schemas.action_schema.HandoffContext` |
| Payload | `HandoffContext(goal_key, levers=[s["lever"] for s in GOAL_STRATEGIES[goal_key]], origin="engineering_intent", dse_capability="active", iterate_capability="active", project_id=project_state.project_id)` |
| Authority | `goal_planner.GOAL_STRATEGIES` (levers), `_handle_engineering_intent`'s own `goal_key` (already resolved deterministically by C-040, never invented here) |
| Mutation | YES (session only — never `ProjectState`, never disk) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-024, new) |
| Evidence | `core/orchestrator.py::_handle_engineering_intent`, `tests/test_fn024_handoff_context_dse.py::test_plan_creates_active_handoff_context`, `::test_new_engineering_intent_replaces_context` |

### C-106 — Active `handoff_context` → `_handle_explore` goal bind (FN-024, new)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | read-only lookup at the top of `_handle_explore`, gated on `handoff.project_id == project_state.project_id` (project-boundary proof, not an assumed clear — see `HANDOFF_CONTEXT_DESIGN.md`) and `handoff.dse_capability == "active"` |
| Symbols | `orchestrator._handle_explore`, `StateManager.get_runtime_session().handoff_context` |
| Payload | `handoff_context.goal_key` read into the local `goal_key` used by the rest of `_handle_explore` — from that point on, indistinguishable from an explicitly-resolved `goal_key` (C-045) except for the capability-consumption side effect on success |
| Authority | Same as C-105 — this connection only *reads*, `_handle_engineering_intent` (C-105) is the sole writer |
| Mutation | YES (session only) — successful bind + explore sets `dse_capability = "consumed"`, nothing else changes |
| LLM | NO — a bind either succeeds deterministically or falls through to the pre-existing `_handle_analyze` fallback (C-042) / the deterministic "already explored" message (§4.3) |
| Status | 🟢 CONNECTED (FN-024, new) |
| Evidence | `core/orchestrator.py::_handle_explore` (bind block), `tests/test_fn024_handoff_context_dse.py::test_bare_explore_binds_context_and_consumes_dse_capability_only`, `::test_handoff_context_inert_across_project_boundary` |

---

## Detail — 05 Iteration

### C-050 — `orchestrator.handle` (ITERATE) → `IterateInteractiveSession.start`/`answer`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | interactive-session short-circuit inside `handle()`, or mode-branch inside `_handle_user_text_inner` |
| Symbols | `IterateInteractiveSession.start`, `.answer` |
| Payload | seed parameters, then multi-turn free text |
| Authority | `iterate_interactive_session.py` |
| Mutation | YES (via `apply_and_recalculate`/`record_action` at final confirm) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:220-255,669-721`, `core/iterate_interactive_session.py:88,130` |

### C-051 — ITERATE_INTERACTIVE → Bug 7 soft-interrupt
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | interim intent check, wizard stays open (`wizard_reprompt` attached) |
| Symbols | `resolve_intent` (interim), `_handle_project_status`/`_handle_analyze` |
| Payload | "¿cómo va el proyecto?" mid-wizard |
| Authority | Same as C-021/C-022, scoped to not close the wizard |
| Mutation | NO |
| LLM | INDIRECT (analyze branch) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:672-685` |

### C-052 — ITERATE_INTERACTIVE → Calibration preempt
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | pattern-based preempt check, clears session, re-dispatches as IDLE |
| Symbols | `_should_preempt_iterate_wizard`, `clear_runtime_session` |
| Payload | a new strong-intent/component phrase mid-wizard |
| Authority | Orchestrator (2026-08-05 calibration) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:405-459` (`_should_preempt_iterate_wizard`), `:693-707` (call site) |

### C-053 — `IterateInteractiveSession.answer` → `semantic_interpreter` slot filling
| Field | Value |
|---|---|
| Kind | DATA, STATE |
| Mechanism | `SemanticState` slot extraction/merge |
| Symbols | `semantic_interpreter.update/decide/extract_entities`, `SemanticState` |
| Payload | operation/variable/value slots |
| Authority | `semantic_interpreter.py` |
| Mutation | YES (session `semantic_state`) |
| LLM | NO |
| Status | 🟢 CONNECTED — since FN-026, this is also the mechanism C-043 feeds: `_preseed_variable_from_handoff` writes `iteration_draft.variable` directly on `.start()`, upstream of this slot-filling loop |
| Evidence | `core/semantic_interpreter.py`, `core/iterate_interactive_session.py:1108-1224` |

### C-054 — Iterate final confirm → `MutationEngine`/`apply_and_recalculate`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | direct call chain |
| Symbols | `MutationEngine`, `param_definition_session.apply_and_recalculate`, `state_manager.record_action` |
| Payload | resolved parameter delta |
| Authority | `mutation_engine.py` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/mutation_engine.py`, `core/param_definition_session.py:715` |

---

## Detail — 06 Calculation / 07 Simulation

### C-060 — `current_parameters` → `CalculationEngine.build`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function |
| Symbols | `CalculationEngine.build(current_parameters) -> CalculationBundle` |
| Payload | `current_parameters: dict` |
| Authority | `calculation_engine.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/calculation_engine.py:34`, `actions/calculate.py` |

### C-061 — `component_resolver.resolve_propulsion_parameters` → calculation input override
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, declarative components → physical override |
| Symbols | `resolve_propulsion_parameters(components) -> PhysicalOverride` |
| Payload | `PhysicalOverride` |
| Authority | `component_resolver.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_resolver.py:73` |

### C-070 — `CalculationBundle` → `FeasibilitySimulator.evaluate`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function |
| Symbols | `FeasibilitySimulator.evaluate(calculations, autonomy_threshold) -> SimulationResult` |
| Payload | `CalculationBundle` → `SimulationResult` |
| Authority | `simulation/simulator.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `simulation/simulator.py:18`, `actions/simulate.py` |

### C-071 — `SimulationResult` → `state_manager.record_action` → persisted `latest_results`
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | direct call, immutable `model_copy` |
| Symbols | `StateManager.record_action`, `WorkspaceManager.save_state` |
| Payload | `HistoryEntry` + `latest_results` dict |
| Authority | `state_manager.py` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/state_manager.py:195-215`, `actions/calculate.py`, `actions/simulate.py` |

---

## Detail — 08 Continuity

### C-080 — ProjectState + BOM + requirements → `build_project_continuity`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, recomputed every call |
| Symbols | `project_continuity.build_project_continuity` |
| Payload | `{situation, evidence, next_useful_step, next_useful_why}` |
| Authority | `project_continuity.py` |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/project_continuity.py:10` |

### C-081 — Sim (`safety_margin_ratio`) → Continuity `next_useful_step` 🟡 PARTIAL (WEAK)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `sim_status == "pass"` branch does not read `safety_margin_ratio` at all |
| Symbols | `build_project_continuity`'s `elif sim_status == "pass": next_step = "Diseño en PASS..."` |
| Payload | margin value is available (`sim.get("safety_margin_ratio")`) but unused in this branch |
| Authority | Continuity is still the sole decider — just under-informed |
| Mutation | NO |
| LLM | NO |
| Status | 🟡 PARTIAL — not `BROKEN` (never wrong, never claims something false) but degrades to a generic fallback identical for margin=1.08 and margin=3.0. Verified via direct `build_project_continuity` call with `safety_margin_ratio=1.08`, architecture 4/4, no incomplete/missing components. |
| Evidence | `core/project_continuity.py` (the `elif sim_status == "pass":` branch, no margin read). Failure D of the predecessor map; H5 (design-only, `MISMATCHES.md`) is the open question, not yet a queued FN. |

### C-107 — Authorities → `build_engineering_readiness` 🟢 (ERF-1, updated ERF-2)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure projection over `ProjectState` + existing authority helpers + `electrical_compatibility` (ERF-2, C-111) |
| Symbols | `engineering_readiness.build_engineering_readiness` |
| Payload | `EngineeringReadinessResult` — gap registry (primary), nine subsystem lines (ERF-2: +`electronics`), `overall`, `top_gap`. ERF-2 adds 4 electrical gap types and `INCOMPATIBLE` verdicts (★3 gate). **IC 1:** `requirements.defined` via `requirements_declared()` (numeric `parsed_constraints` or explicit-none `restrictions`). Product contract: `ENGINEERING_READINESS_VISION.md` §11. |
| Authority | `engineering_readiness.py` — authoritative over **gap aggregation and assembly-ready rollup**, not over physics/BOM/sim truth |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/engineering_readiness.py`, `core/electrical_compatibility.py`, `tests/test_engineering_readiness_*.py`, `tests/test_engineering_readiness_erf2_*.py` |

### C-108 — Readiness → Continuity (catalog-gap ranking only) 🟡 PARTIAL (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | optional kw-only `readiness=` on `build_project_continuity`; gates catalog-gap branches via `readiness.top_gap.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"` and `subsystems["catalog"].warning_type` (G9-B demotion) |
| Symbols | `project_continuity.build_project_continuity(..., readiness=readiness)` |
| Payload | affects only the two motor-catalog-gap `next_useful_step` branches; all other ranking (blocking, FN-005, BOM, arch, optimization, fallback) remains Continuity's legacy chain |
| Authority | Gap ordering from C-107; human next-step copy still from Continuity |
| Mutation | NO |
| LLM | NO |
| Status | 🟡 PARTIAL — intentional ERF-1 scope cut; full handoff deferred (Slice 4b). See `.jes/artifacts/implementation_report_erf1.md` "Scope decision". |
| Evidence | `core/project_continuity.py`, `core/orchestrator.py` (`build_startup_context`), `tests/test_engineering_readiness_continuity.py` |

### C-109 — `build_startup_context` → `"readiness"` field 🟢 (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `readiness = build_engineering_readiness(project_state)` then `dataclasses.asdict(readiness)` in return dict |
| Symbols | `orchestrator.build_startup_context` |
| Payload | full readiness snapshot (derived on read, not persisted) |
| Authority | C-107 |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py`, `tests/test_engineering_readiness_cli.py` |

### C-110 — CLI → `ENGINEERING READINESS` render block 🟢 (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA (presentation) |
| Mechanism | `_render_readiness_block` in `render_startup_context` |
| Symbols | `adapters/cli/main.py::_render_readiness_block` |
| Payload | 9 subsystem verdict lines (ERF-2), `PROJECT STATUS`, up to 3 `TOP GAPS` |
| Authority | display only — reads C-109 payload, no new domain logic |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED (ERF-1, updated ERF-2 — 8→9 lines) |
| Evidence | `adapters/cli/main.py`, `tests/test_engineering_readiness_cli.py` |

### C-111 — `electrical_compatibility` → `engineering_readiness` gap generation 🟢 (ERF-2)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `build_engineering_readiness` calls `check_esc_presence`, `check_esc_vs_motor`, `check_battery_discharge`, library `match_motor_propeller` |
| Symbols | `electrical_compatibility.check_esc_presence`, `.check_esc_vs_motor`, `.check_battery_discharge`; `library.match_motor_propeller` |
| Payload | per-check boolean/numeric facts → 4 gap types (`GAP-ESC-MISSING`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`) |
| Authority | `electrical_compatibility.py` — pure facts; `engineering_readiness.py` aggregates into gaps |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/electrical_compatibility.py`, `core/engineering_readiness.py`, `tests/test_electrical_compatibility.py`, `tests/test_engineering_readiness_erf2_gaps.py` |

### C-112 — ESC acquisition routing (out-of-scope explicit save) 🟢 (ERF-2, FN-ESC)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `_handle_component_description` checks `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS` + `user_explicitly_named_component()` |
| Symbols | `orchestrator._handle_component_description`, `acquisition_target.COMPONENT_TERM_ALIASES["esc"]`, `COMPONENT_PROMPTS["esc"]` |
| Payload | user text `"esc 30a"` → ESC saved even when wizard expects different key (e.g. `motors`) |
| Authority | `acquisition_target.py` (aliases), `orchestrator.py` (narrow save gate) |
| Mutation | YES (via C-091, component_writers) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py`, `core/acquisition_target.py`, `tests/test_fn_esc_acquisition.py` |

### C-082 — `classify_component` → BOM buckets
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure classifier, routes into 4 buckets; each entry adds `catalog_ref`, `sku_resolved`, `quantity` |
| Symbols | `project_closure.classify_component`, `build_component_bom`, `_bom_sku_resolved`, `format_bom_lines` |
| Payload | `"missing"/"stub"/"declared"/"defined"` → `{defined, incomplete, missing, declarative}`; `[sku]` suffix when `sku_resolved` (motor/battery/**propeller** via `has_*` re-check — IC 3) |
| Authority | `project_closure.py` (FN-020, Impl D, IC 3 display fix) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — `sku_resolved` is **display-only** (C-094 views); never consumed by C-107 gap/verdict derivation |
| Evidence | `core/project_closure.py`, `tests/test_impl_d_sku_bom.py` |

### C-083 — `classify_component` (via `component_presence_tier`) → `_block_progress_status`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | thin wrapper — same primitive as C-082, not a second threshold |
| Symbols | `orchestrator._component_is_low` → `project_closure.component_presence_tier` |
| Payload | `"stub"/"present"` |
| Authority | `project_closure.py` (FN-020) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — **this is the connection whose absence was the FN-020 bug**: before FN-020, architecture progress and BOM used two independently-defined thresholds that could disagree; now both read the same primitive |
| Evidence | `core/orchestrator.py` (`_component_is_low`), `core/project_closure.py` (`component_presence_tier`) |

### C-084 / C-085 — Phase / Reasoning
> Derived summary — IDs already in Canonical registry (not +2 edges).

| ID | From | To | Status | Evidence |
|---|---|---|---|---|
| C-084 | ProjectState | `PhaseLayer.infer` | 🟢 | `core/phase_layer.py:28` |
| C-085 | Context (incl. phase, signals) | `ReasoningLayer.build` → insights/suggested_actions | 🟢 | `core/reasoning_layer.py:28` |

---

## Detail — 09 State

### C-090 — Free text → `component_inference.infer_component[s]`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, domain-registry keyword match + property extraction |
| Symbols | `infer_component`, `infer_components`, `infer_component_for_key` (FN-019), `ComponentRuleRegistry.match` |
| Payload | free text → `ComponentSpec` |
| Authority | `component_inference.py` + `domains/{aerial,ground}.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_inference.py`, `core/component_rules.py` |

### C-091 — `ComponentSpec` → `component_writers.set_*` (single write point)
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | direct call, atomic write to `components[key]` + mirrored `current_parameters` |
| Symbols | `set_frame_material`, `set_control_component`, `set_battery_component`, `set_motor_component`, `set_propeller_component`, `apply_components_delta` |
| Payload | `ComponentSpec` → `ProjectState` update |
| Authority | `component_writers.py` — **the only** legal writer of `design_properties.components` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_writers.py`, `tests/test_d4_param_gatekeeper.py` (locks the mirrored-param invariant) |

### C-092 — Any orchestrator checkpoint → `StateManager.set_runtime_session`/`clear_runtime_session`
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | whole-session `model_copy(update={...})`, or full reset to a fresh IDLE `InteractiveSessionState` |
| Symbols | `StateManager.set_runtime_session`, `clear_runtime_session` |
| Payload | `InteractiveSessionState` fields (`mode`, `pending_*`, `last_exploration_result`, etc. — full field list in `09_state/STATE_MAP.md`) |
| Authority | `state_manager.py` |
| Mutation | YES (session, not disk, though snapshotted — see C-093) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/state_manager.py:98-114` |

### C-093 / C-094 — ProjectState → disk
> Derived summary — IDs already in Canonical registry (not +2 edges).

| ID | To | Symbols | Status | Evidence |
|---|---|---|---|---|
| C-093 | `state.json` | `WorkspaceManager.save_state` | 🟢 | `workspace/workspace_manager.py:82` |
| C-094 | `estado_actual.md`/`sistema.md` | `WorkspaceManager.render_views` (uses `project_closure`'s BOM) | 🟢 | `workspace/workspace_manager.py:115`, `workspace/render_views.py` |

---

## Detail — 10 LLM

### C-100 — `orchestrator` → `llm_interface.interpret` → `PromptBuilder.build_messages`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct call |
| Symbols | `JarvisLLMInterface.interpret`, `PromptBuilder.build_messages` |
| Payload | `user_input`, `runtime_state` → `messages: list[dict]` |
| Authority | `llm/prompt_builder.py` |
| Mutation | NO |
| LLM | YES (this is the boundary itself) |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:34-35` |

### C-101 — `PromptBuilder` messages → `LLMClient.complete`
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | network call to the model backend |
| Symbols | `LLMClient.complete(messages, json_mode=True)`, implemented by `OllamaClient` |
| Payload | messages → raw JSON string |
| Authority | the model itself (outside this codebase) |
| Mutation | NO |
| LLM | YES |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:38`, `llm/ollama_client.py` |

### C-102 — Raw LLM response → `LLMResponseParser.parse/validate_for_runtime`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | JSON parse → schema validation → **`ActionPolicy.validate`** |
| Symbols | `LLMResponseParser.parse`, `.validate_for_runtime`, `ActionPolicy.validate`, `ActionPolicy.ALLOWED_ACTIONS` |
| Payload | raw JSON → validated `LLMActionRequest` |
| Authority | **`ActionPolicy`** — this is the structural enforcement point for "LLM must not choose the next engineering target" (see `AUTHORITY.md`) |
| Mutation | NO |
| LLM | YES (validating its output, not itself deciding) |
| Status | 🟢 CONNECTED |
| Evidence | `llm/response_parser.py:17-18`, `llm/action_policy.py:14-38` |

### C-103 — Validated `action_request` → `orchestrator.handle` (closed 4-verb set)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `to_action_request` → `self.handle(action_request)` |
| Symbols | `LLMResponseParser.to_action_request`, `orchestrator.handle` |
| Payload | `{"action": one of 4, "parameters": {...}}` |
| Authority | Same closed set as C-016 |
| Mutation | YES (delegates to the resolved Action) |
| LLM | INDIRECT (this is the LLM's output being consumed, not the LLM itself acting) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:925,939` |

### C-104 — `orchestrator` → `llm_interface.analyze` → narration string
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, return value is text only |
| Symbols | `JarvisLLMInterface.analyze` |
| Payload | `user_input`, `context`, `goal_context` (optional, from `get_goal_context_for_llm`) → message string |
| Authority | n/a — narration is not a decision |
| Mutation | NO |
| LLM | YES |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:76`, `core/orchestrator.py:2194-2253` (`_handle_analyze`) |

---

## Suspected missing edges (flagged, not fabricated)

These are gaps observed while building this registry — not claimed as connections, and not implemented anywhere. Listed so a future contributor doesn't have to rediscover them from scratch.

- **Plan/Handoff Context → DSE consumer** — **IMPLEMENTED (FN-024, C-105/C-106)**, closing C-042. **Help+Goal routing (H3/C-025/C-044)** — **IMPLEMENTED (FN-025)**, closing both. **Plan/Handoff Context → Iterate consumer (H4/C-043)** — **IMPLEMENTED (FN-026)**, via `handoff_matching.match_plan_lever` + `orchestrator._preseed_variable_from_handoff`. H1–H4 all closed; only H5 (C-081, below) remains. See `MISMATCHES.md` design appendix.
- **Continuity → margin/goal "thread"** — `⚪ NOT IMPLEMENTED` in the sense that no data surface currently carries "we are worried about margin" across turns; C-081 is the read-side symptom.
- **`ActionRouter` entry for `analyze`/`project_status`/`explore_design_space`/etc.** — `⚪ NOT IMPLEMENTED` by design (§1.4 dual-dispatch note) — these intents never touch `ActionRouter` at all, which is why the seam exists. Not a bug, listed for completeness.
