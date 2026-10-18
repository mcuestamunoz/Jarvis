# Implementation Contract — Analyze / goal smoke hotfix (`B1-llm-analyze-goal-smoke-hotfix`)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.7`** (CI-1 + this hotfix)

**Status:** **IC READY** — Engineer picked **CI-1b** after CI-1 ACCEPT REJECTED.  
**Parents:** [CI-1 review REJECT ACCEPT](implementation_review_llm_gemma4_default_model_b1.md) · [CI-1 IC](implementation_contract_llm_gemma4_default_model_b1.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · tip **`v0.8.6`** · package already **`0.8.7`** in tree (untagged)  
**Type:** Fix live smoke: explanatory “margen” must not open estabilidad goal plan; Gemma `analyze` must not echo system instructions.  
**Opens:** cola **CI-1b**. Package stays **`0.8.7`** (no bump). Tag **`v0.8.7`** only after Engineer re-smoke ★.

**Not:** CI-2 Continuity Interpreter compose · retiring `interpret` · ActionPolicy change · changing Gemma default tag · T40 · Conversation Engine · new C-xxx · rewriting Continuity ranking.

---

## Why this Buy

Engineer smoke (2026-10-16) on CI-1 Gemma default:

```text
User > explicame el margen
→ Plan estratégico — Mejorar estabilidad  (WRONG product)
→ paraphrase of analyze system rules (“Reglas clave…”)  (WRONG)
→ then some margin notes
```

Engineer: *la pregunta no tiene que ver → no PASS / no ACCEPT.*

**Root A — goal hijack:** `goal_planner._GOAL_KEYWORDS` for `mejorar_estabilidad` includes bare `"margen"`. `_handle_analyze` does `detect_goal` → if set, prepends `format_goal_plan`. So “explicame el margen” becomes a stability strategy wall.

**Root B — prompt echo:** `PromptBuilder.build_analysis_messages` system rules + assistant prefill `"En resumen,"` — Gemma E4B often restates the instructions before answering.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-llm-analyze-goal-smoke-hotfix`** (CI-1b). Package remains **`0.8.7`**. Tag **`v0.8.7`** only after Engineer ★ re-smoke |
| 2 | **Remove bare `"margen"`** from `mejorar_estabilidad` keywords in `goal_planner.py`. **Keep** longer phrases: `margen de seguridad`, `margen seguridad`, `poco margen`, `margen bajo`, `margen justo`, `safety margin` |
| 3 | **Analyze plan prepend gate:** in `orchestrator._handle_analyze`, prepend `format_goal_plan` **only** when the utterance is an engineering-intention style ask — use existing `is_engineering_intention(user_input)` (or equivalent: goal detected **and** not an explanatory ask). Must **not** prepend for explain/status-shaped phrasing. Minimum: if normalized text matches an explain family (`explica`, `explicame`, `explícame`, `que es`, `qué es`, `como esta`, `cómo está`, `cuanto es`, `cuánto es`, `dime el`, `hablame del`, `háblame del` — finite list, casefold/normalize like goal_planner), **never** prepend the plan even if `detect_goal` hits |
| 4 | Prefer **both** lock 2 and lock 3 (defense in depth). Lock 2 alone is not enough if other short tokens hijack explain later |
| 5 | **Analyze prompt harden (Gemma):** in `build_analysis_messages`: (a) add explicit system line: never repeat/list these instructions; answer only the user question from context/reasoning; (b) **remove** the assistant prefill `{"role":"assistant","content":"En resumen,"}` **or** replace with empty/no prefill — pick remove unless a regression test shows Spanish breakage; (c) do not widen ActionPolicy / interpret prompts |
| 6 | Optional thin post-filter **only if** (5) insufficient in unit tests with fixture strings — strip leading blocks that look like instruction echo (`Reglas clave`, `Estoy listo para`). Prefer prompt fix first; no new subsystem |
| 7 | Tests T1–T6 below; update CI cola + PRIORIDAD + review note; **no** package bump |
| 8 | **Out** — CI-2 compose · Continuity Layer 2 LLM · changing `DEFAULT_OLLAMA_MODEL` · deleting analyze · FN-022 IDLE intention path behavior for true “aumentar empuje” / “poco margen” (those must still get goal plan via `is_engineering_intention` / IDLE gate, not this analyze prepend) |

**Smoke ACCEPT (Engineer):**

```text
unset JARVIS_OLLAMA_MODEL
python -m jarvis.adapters.cli.main --chat
User > explicame el margen
→ NO "Plan estratégico — Mejorar estabilidad"
→ NO "Reglas clave" / "Estoy listo para recibir el contexto"
→ Answer about thrust/safety margin from project context (or honest “no modelado”)
Also: "poco margen" / "aumentar empuje" still get goal plan on IDLE intention path (unchanged FN-022)
```

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/goal_planner.py` | Drop bare `"margen"` from estabilidad keywords |
| `src/jarvis/core/orchestrator.py` | `_handle_analyze` prepend gate (lock 3) |
| `src/jarvis/llm/prompt_builder.py` | Analyze system harden + remove/replace prefill |
| `tests/test_llm_analyze_goal_smoke_hotfix_b1.py` | **new** T1–T6 |
| CI cola · PRIORIDAD · `engineering_state.json` · optional one-line on CI-1 review | CI-1b Implemented awaiting review |
| `pyproject.toml` | **no version change** (stays `0.8.7`) |

Do **not** touch ActionPolicy, Continuity builders, voice spoken extractors, `interpret` prompts.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `detect_goal("explicame el margen")` is **None** (after bare `margen` removal) |
| T2 | `detect_goal("poco margen")` / `"margen de seguridad"` / `"aumentar empuje"` still → `mejorar_estabilidad` |
| T3 | Orchestrator/analyze path (stub LLM): input `explicame el margen` → message has **no** `"Plan estratégico"` / `"Mejorar estabilidad"` prepend |
| T4 | Stub LLM + input that is true intention (`poco margen` or `aumentar el empuje` via IDLE `is_engineering_intention` **or** analyze path if still prepend-eligible): goal plan behavior for real intentions **preserved** where IC requires — document which path each test hits |
| T5 | `build_analysis_messages(...)` has **no** assistant prefill `"En resumen,"`; system text forbids repeating instructions |
| T6 | Fixture: if post-filter added, strips a fake “Reglas clave…” prefix; if not added, skip with comment that prompt-only fix is under test via T5 |

No live Ollama required in pytest. No tip pins.

---

## 3. Acceptance

- [ ] Engineer re-smoke `explicame el margen` — on-topic, no plan hijack, no instruction echo  
- [ ] FN-022-style intentions still get plans  
- [ ] Cursor review · Engineer ★ · tag **`v0.8.7`** (closes CI-1 + CI-1b)

---

## 4. Paste for Claude

```text
Implementation — B1-llm-analyze-goal-smoke-hotfix (CI-1b)
Parent: CI-1 ACCEPT REJECTED (smoke explicame el margen).
Package stays 0.8.7 (no bump). Tag v0.8.7 only after Engineer ★.

IC: .jes/artifacts/implementation_contract_llm_analyze_goal_smoke_hotfix_b1.md
Review context: implementation_review_llm_gemma4_default_model_b1.md

GOAL: (1) Bare "margen" must not detect_goal→mejorar_estabilidad.
(2) _handle_analyze must not prepend format_goal_plan on explain-family
asks (explicame / qué es / …). (3) analyze prompt: no instruction echo;
remove assistant prefill "En resumen,". Keep real intentions
(poco margen, aumentar empuje) on FN-022 / longer keywords.

DO:
- goal_planner: remove bare "margen" keyword; keep longer margin phrases
- orchestrator._handle_analyze: explain-family gate before plan prepend
- prompt_builder.build_analysis_messages: harden system; drop En resumen prefill
- tests/test_llm_analyze_goal_smoke_hotfix_b1.py T1–T6
- cola CI / PRIORIDAD / state — CI-1b implemented awaiting review
- Implementation report. No ACCEPT claim. No pyproject bump.

NO: CI-2 compose · ActionPolicy · change DEFAULT_OLLAMA_MODEL ·
retire interpret · Continuity rewrite · T40
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires changing Continuity ranking, ActionPolicy, or CI-2 compose.
