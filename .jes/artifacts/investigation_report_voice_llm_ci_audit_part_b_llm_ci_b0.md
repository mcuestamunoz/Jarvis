# Investigation Report — Part B: LLM + Continuity Interpreter epoch (`INV-voice-llm-ci-audit`, CI-INV-0)

**Project:** Jarvis · **Date:** 2026-10-16 · **Investigator:** Claude Code (read-only)
**Contract:** [INV IC](investigation_contract_voice_llm_continuity_interpreter_audit_b0.md) · **Index:** [index](investigation_report_voice_llm_ci_audit_b0.md) · [Part A](investigation_report_voice_llm_ci_audit_part_a_voice_b0.md) · [Part C](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md)
**Tree audited:** tip `v0.8.6` + uncommitted CI-1/CI-1b (`0.8.7`). Live model during INV: `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` loaded in Ollama (`/api/ps`).
**Status:** Implemented — awaiting Cursor review. No ACCEPT claim. No `src/` edit.

---

## B1 — As-is LLM call graph

Entry points that construct a live `JarvisLLMInterface(client=OllamaClient())`: `--chat`/`--voice-only` (`main.py:1017`), `--voice-fixture` (`main.py:1318`), `--voice-audio` (`main.py:1336`), MCP (`adapters/mcp/session_manager.py:39`), demo (`main.py:768`). All funnel into `orchestrator.handle_user_text` → `_handle_user_text_inner` (`orchestrator.py:1580-1615`).

Order inside `_handle_user_text_inner` (deterministic first; LLM last):

```text
1  _handle_global_commands (escape · nuevo · explain intercept A7 · Continuity defer · twelve Skills)   orchestrator.py:1615   0 LLM
2  pending structural confirm / pending define-missing (FN-004, Bug 54)                               :1623-1645           0 LLM
3  IDLE catalog rebind (B2/B3)                                                                         :1661+               0 LLM
4  session-mode branches (iterate wizard, define-missing, create wizard …)
     ITERATE_INTERACTIVE: interim intent "analyze" → _handle_analyze                                    :2126   C-104
                         information/hybrid class guard  → _handle_analyze                               :2134   C-104
     DEFINE_MISSING:     _dm_intent "analyze" (not help-choose) → _handle_analyze                        :2221   C-104
5  IDLE intent dispatch (IntentResolver.resolve_intent)
     analyze + help-verb only → FN-025: is_engineering_intention → plan | project_status               :2440-2472  0 LLM
     analyze (real verb)  → _handle_analyze                                                             :2475   C-104
     ambiguous + project  → _handle_analyze                                                             :2480   C-104
     define_params (Bug 41/G18)                                                                          :2486+      0 LLM
     iterate/unknown + project → FN-022 is_engineering_intention → _handle_engineering_intent           :2537-2541  0 LLM
     create/iterate/calculate/simulate → resolve_action_request (deterministic C-019)                    :2544-2551  0 LLM
     dismiss_suggestion · explore_design_space · apply_exploration_result                               :2554-2574  0 LLM*
6  llm_interface.interpret(user_input, runtime_state)   ← LAST RESORT                                    :2576   C-100→C-103
     invalid_llm_output → status error "No se pudo interpretar la intención" (no _track_turn)            :2577-2582
     Bug 52: intent=="unknown" and LLM action=="iterate" → _handle_analyze                              :2586-2589  C-104
     else → self.handle(action_request)  (ActionRouter; 4 verbs)                                         :2590
   handle(ITERATE) → iterate wizard start with **self._semantic_preseed(...)                            :398    SemanticIntentAdapter
```

`*` `_handle_explore` falls back to `_handle_analyze` when no project / no bindable goal / unknown grid (`orchestrator.py:6929`, `6999`, `7006`).

`analyze` itself (`_handle_analyze`, `orchestrator.py:7468-7506`): `detect_goal` → `goal_context` into the prompt → `llm_interface.analyze(...)` (`llm_client.py:76-127`) → **if goal and not `is_explain_ask`** (CI-1b) prepend `format_goal_plan(...)` + `─── Evaluación contextual ───`.

C-100…C-104 (`docs/system_map/DIAGRAMS.md:224-228`) still match: C-100 = `:2576`, C-101 = `PromptBuilder.build_messages`, C-102 = `LLMResponseParser.validate_for_runtime` → `ActionPolicy.validate` (`response_parser.py:29-34`), C-103 = `:2590`, C-104 = the nine `_handle_analyze` call sites above.

Voice adds **no** LLM call site: `--voice-only` reaches the LLM only through the same chain (Part A A7).

## B2 — The two "semantic" modules

| | `llm/semantic_intent_adapter.py` (`SemanticIntentAdapter`) | `core/semantic_interpreter.py` |
|---|---|---|
| LLM | consumes LLM output (no call) | **no LLM** — regex/stem slot filler (`_OPERATION_MAP`, `semantic_interpreter.py:15+`) |
| Callers | `llm_client._build_semantic_trace` (logging only, `llm_client.py:129-155`); `orchestrator._semantic_preseed` (`orchestrator.py:8072-8100`, from `handle()` ITERATE `:398`) | `core/iterate_interactive_session.py` only |
| Role | turn an LLM `iterate` JSON into a seeded wizard start (step 2) or a derived-variable redirect | slot state for the iterate wizard (`update/decide/to_draft_patch`) |
| Relation to "Continuity Interpreter" | **none** — 4-verb residual helper; would be quarantined with `interpret` (CI-5) | **none** — wizard internals; CI-0 lock 11 forbids overloading the name |

Naming risk confirmed: three different things now carry "semantic/interpreter" (these two + CI product name). CI-0 lock 11 already fences it; no doc yet says so outside the DC.

## B3 — ActionPolicy fence

Structural fence **holds**: `ALLOWED_ACTIONS = {CREATE_PROJECT, ITERATE, CALCULATE, SIMULATE}` (`llm/action_policy.py:15-20`); session gating (`:65-88`); unknown iterate variable rejected (`:95-111`). Even the error fallback stays in-set (`llm_client.py:66-73`). No 5th verb, no component/goal/DSE verb reachable.

**But the fence constrains the verb, not the relevance.** Two leak classes (both are "valid output, wrong product turn"):

| # | Leak | Evidence | Severity |
|---|---|---|---|
| **B3-1** | **Gemma turns unclassified input into `create_project`.** Resolver intent `unknown` for `hablar`, `Gracias.`, `sistema`, `Que necesito para hacer una curva de consumo de los motores` (checked: `IntentResolver().resolve_intent`). With qwen these produced `action: null` → validation error → "No se pudo interpretar" (94 of 103 interpret errors in logs). With Gemma they **validate** as `create_project` (logs `20261015T103206`, `…103253`, `…140220` (`parameters.goal = "curva de consumo de motores"`), `20261016T092503`, `…095133`, `…144747`, `…144815`, `…150758`, `…150808`). Bug 52 guard only covers `iterate` (`orchestrator.py:2586`). Reproduced with a stub returning that JSON on a closed project: result `interactive` · "Vamos a definir el proyecto paso a paso." · session → `CREATE_PROJECT_INTERACTIVE`. On `--voice-only` any STT hallucination (T59 N2) now **opens the create-project wizard over the active project**. | **blocker for CI-1 ★ honesty** (regression introduced by the default-model change; not covered by CI-1/CI-1b smoke criteria) |
| **B3-2** | **Deterministic goal-plan prepend steers analyze** (CI-1 smoke). CI-1b removed bare `margen` + explain gate. Residual bare tokens still hit `detect_goal`: `empuje`, `thrust`, `estabilidad`, `autonomia`, `bateria` (`goal_planner.py:107-160`). Checked: `por que el empuje es bajo` → estabilidad, gate **False**; `en que consiste la autonomia` → autonomia, gate False; `como funciona la estabilidad` → estabilidad, gate False; `dime la autonomia` → autonomia, gate False. Those analyze turns still get the strategy wall. `goal_context` is still injected into the LLM prompt even when the prepend is gated (`orchestrator.py:7478`). | high (same class as the rejected smoke, different words) |

## B4 — CI-0 locks vs tip

| CI-0 lock | Tip | Status |
|---|---|---|
| 1 Primary role = CI (bridge + composer) | No CI code. LLM roles at tip = `interpret` (4-verb) + `analyze` (narrator) | **not started** (DC only) |
| 2 Layer 1 SoT; interpreter never ranks | Continuity ranking 0-LLM (`project_continuity.py`, `_explain_topics_for_continuity` called after ranking `:242-275`, `:662`) | ✅ satisfied (vacuously — no interpreter yet) |
| 3 Layer 2 may LLM-compose | Layer 2 deterministic only | **not started** |
| 4 Chat ∥ voice parallel spoken egress | `--chat` silent (`main.py:954-958`); `--voice-only` speaks | **contradicted by tip** (expected pre-CI-2; DC Open #2 unresolved) |
| 5 Ingress → existing contracts, claim-before-LLM | Deterministic chain first (B1); residual `interpret` still reaches `create_project` on nonsense (B3-1) | **partial** |
| 6 Egress = compose from computed fields; don't pick gap | not built; `analyze` composes from `context` + `reasoning_output` + `goal_context` — not Continuity fields | **partial / different shape** |
| 7 Ontology explains, never decides | R3 cite path 0-LLM, after ranking (B8) | ✅ satisfied |
| 8 ActionPolicy fence | holds (B3) | ✅ satisfied |
| 9 Quarantine `analyze` story / `interpret` measured | Both live; no quarantine marker; **measurement source polluted** (B7) | **partial / blocked** |
| 10 Gemma E4B runtime | `DEFAULT_OLLAMA_MODEL` = Gemma tag (`config.py:20-21`, in tree untagged) | **in tree untagged** (CI-1 REJECTED → CI-1b) |
| 11 Naming fence | code unchanged; docs don't yet mention CI outside `.jes/` + PRIORIDAD (B10) | ✅ code · **drift** docs |
| 12 Out-of-epoch list | nothing out-of-scope in tree | ✅ |

## B5 — CI-1 / CI-1b status honesty (tree as found)

| Item | State | Evidence |
|---|---|---|
| `DEFAULT_OLLAMA_MODEL` | `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL`, env override intact | `src/jarvis/config.py:20-21` |
| Package | `0.8.7` in `pyproject.toml`; **no `v0.8.7` tag**; last tag `v0.8.6` (`52e6892`) | `git tag`; `git status` (11 files modified, uncommitted) |
| CI-1 | Cursor PASS WITH NOTES · **Engineer ACCEPT REJECTED** (smoke `explicame el margen`) | `implementation_review_llm_gemma4_default_model_b1.md:10-16` |
| CI-1b | Implemented; Cursor review **exists**: PASS WITH NOTES, no ACCEPT | `implementation_review_llm_analyze_goal_smoke_hotfix_b1.md:10`, N1–N5 |
| CI-1b code | `is_explain_ask` + bare `margen` removal (`goal_planner.py`), gate (`orchestrator.py:7490-7491`), no prefill + no-echo system line (`prompt_builder.py:104-136`); tests `tests/test_llm_analyze_goal_smoke_hotfix_b1.py` | tree |
| Engineer re-smoke | **not run yet** as far as logs show: last `analyze` log is `20261016T091434` (`explicame el margen`, pre-CI-1b, still has `En resumen,` prefill echo). No post-CI-1b analyze log exists | `runtime/llm_logs/` |
| Smoke criteria unmet | (a) `explicame el margen` on-topic, no plan, no echo — **unverified live**; (b) **not in any smoke list:** unknown-intent → `create_project` hijack (B3-1) | — |
| Race note | CI-1b review landed while this INV ran (file mtime 16:52 local); audited tree is post-CI-1b code | file mtimes |

## B6 — Analyze / goal coupling

- **Coupling:** `_handle_analyze` (`orchestrator.py:7468-7506`) calls `detect_goal(user_input)` once and uses it twice: `goal_context` for the prompt (always) and the plan prepend (gated since CI-1b).
- **CI-1b changes:** bare `margen` out (`goal_planner.py` estabilidad list; 7 direction phrases added for FN-022), `is_explain_ask` finite regex, prefill `"En resumen,"` removed, system line "Nunca repitas…/Responde directamente…".
- **Residual risk (other short keywords):** B3-2 table. Same root as the rejected smoke: substring match on bare dimension words (`goal_planner.py:249-262`). F-1 already fixed this class for payload with dimension+direction (`goal_planner.py:176-246`); the other goals were explicitly left for "F-1b" (comment `goal_planner.py:181-184`).
- **Gemma-specific failure modes (log evidence):** (1) instruction echo — all three Gemma-era analyze logs begin `"En resumen, el usuario quiere que actúe como un asistente de ingeniería para…"` (`20261015T135747`, `…135851`, `20261016T091434`); CI-1b removed the prefill that seeded it — not yet re-measured; (2) eager valid JSON for nonsense (B3-1); (3) one `timed out` class in older logs (60 s default, `config.py`) — not seen on Gemma yet.
- **Voice coupling:** whatever `analyze` returns (plan + narration) is spoken verbatim on `--voice-only` (Part A A3-g1).

## B7 — Interpret quarantine readiness (measurement plan for CI-5 — no delete)

Log sample (`src/jarvis/runtime/llm_logs/`, gitignored, 158 files 2026-08-18 → 2026-10-16 after this INV's +2):

| Mode | ok | error | Notes |
|---|---|---|---|
| `interpret` | 30 | 103 | errors: 94 pydantic `action=None` (qwen), 4 `timed out`, 6 unknown-variable rejections (`flight_controller`, `esc`, `sensors`, `raw_user_input`, `power_connector`, `exit`) |
| `analyze` | 21 | 4 | — |

Useful interpret outcomes ≈ 17 `iterate` (12 `fallback_wizard`, 2 `preseed_step2`, 1 derived redirect), 4 `calculate`, 7 `create_project` (of which ≥ 6 are the `hablar` hijack).

**Measurement is invalid as-is:** **90 of 133 interpret logs are `hablar`**, and this INV proved the two pre-existing tests that type `hablar` into a real `run_chat()` generate them (+2 live Gemma calls, 28.9 s, per run of those two tests). 7 more are `[BLANK_AUDIO]` (pre-T59 live voice). So the corpus is dominated by test pollution + one retired word.

Proposed plan (input to a later CI-5 IC — nothing to implement now):
1. **Precondition:** suite never reaches a live LLM nor writes to `DEFAULT_LLM_LOG_ROOT` (stub `JarvisLLMInterface`/`OllamaClient` + `tmp_path` logger in `run_chat`-level tests). Without this, every suite run adds false `interpret` rows.
2. Tag each log row with the **resolver intent** and the **call site** (`:2576` vs Bug 52 vs analyze site) — today a row carries neither, so "would a deterministic path have claimed it?" can't be answered from logs.
3. Window: ≥ 2 weeks of Engineer daily use after (1); classify each `interpret` row: useful-verb / hijack / error / test.
4. CI-5 gate: near-zero useful rows **and** CI-3 ingress covers the useful ones.

## B8 — Ontology seam

- **Today (0-LLM):** chat `explain …` intercept → `assistant_task.handle_explain_intent` (`intelligence/assistant_task.py:318`, "Never calls an LLM"); R3: Continuity emits finite `explain_topics` **after** ranking (`project_continuity.py:242-275`, call `:662`), no `ontology/` read in that module; the CLI resolves cites via `intelligence/continuity_cite.cites_for_topics` (Conceptos lines, screen-only per T52).
- **R4 / CI-R4 (Later):** quote-only ontology cite inside an LLM compose (`JARVIS_KNOWLEDGE_VISION.md` §7 row (b) "R4 LLM cite: Later"). Nothing in tree.
- **Vault never decides Continuity:** confirmed — no `jarvis.intelligence` import in `project_continuity.py` (docstring `:262-266` + code).

## B9 — Chat ∥ voice parallel gap (input list for CI-2)

| Surface | `--chat` today | `--voice-only` today | CI-0 lock 4 target | Gap |
|---|---|---|---|---|
| Startup / `estado` walls | print full | print full + speak brief/FULL extract (0-LLM) | printed **and** spoken in both | `--chat` silent → **needs DC answer to Open #2** (always speak vs opt-in) |
| Coherence-footer turns (`Estado:/Siguiente paso:`) | print | speak as printed | Continuity-shaped → compose | not routed through Layer 2 at all |
| `analyze` turns | print | **speak LLM text verbatim** | fold into CI egress (CI-4) | unbounded, unclassified (A3-g1) |
| Wizard bodies / reprompts | print | speak as printed; reprompt **dropped** on `estado` (A3-g2) | "per later IC" | policy missing |
| Errors / Skills | print | speak as printed | — | none |

## B10 — Naming / docs drift

| # | Drift | Evidence |
|---|---|---|
| B10-1 | `LLM_MAP.md` still frames the subsystem as "bounded fallback + narrator", "Known issues: None", no Gemma, no CI epoch, no voice egress of `analyze` | `docs/system_map/10_llm/LLM_MAP.md:3,33-35` |
| B10-2 | `FASE_LLM.md` (HISTORICAL banner OK) still documents the `"En resumen,"` prefill that CI-1b removed | `docs/FASE_LLM.md:179` |
| B10-3 | "Continuity Interpreter" appears in `docs/` only in `IMPLEMENTATION_TASKS.md` | `grep -rl "Continuity Interpreter" docs` |
| B10-4 | PRIORIDAD / CI cola / state are mutually coherent (CI-1b PASS WITH NOTES → re-smoke; CI-INV-0 in progress) | `IMPLEMENTATION_TASKS.md:9`; cola lines 3, 25-28; `engineering_state.json` `cycle_intent` |
| B10-5 | Package drift: tree `0.8.7` vs tip tag `v0.8.6` — documented in PRIORIDAD ("package `0.8.7` untagged"); `src/jarvis.egg-info/PKG-INFO` stale | PRIORIDAD line 9; CI-1 review N3 |
| B10-6 | INV-anchors report §2.4 still says "Default model still `qwen2.5:14b`" | `investigation_report_llm_semantic_interpreter_anchors_b0.md:90` |

## Suite note (IC global method §2)

Full suite **not** re-run for this INV (docs-only; no `src/` change). Last full run on this tree: **4111 passed, 10 skipped** (CI-1b report §5). Targeted runs this INV: the two `hablar` tests (2 passed, 28.87 s — used as the B7 proof). Side effect disclosed: +2 files in the gitignored `src/jarvis/runtime/llm_logs/`.
