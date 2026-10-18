# Implementation Contract — Interpret unknown-intent wizard guard (`B1-llm-interpret-unknown-guard`)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.7`** (CI-1 + CI-1b + this Buy)

**Status:** **IC READY** — opened after [CI-INV-0 review ★ findings](investigation_review_voice_llm_ci_audit_b0.md) (G-01 blocker).  
**Parents:** [CI-INV-0 Part C §C3](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · Bug 52 guard (`orchestrator.py` ~2586) · tip **`v0.8.6`** · package **`0.8.7`** untagged  
**Type:** Guard — when the deterministic resolver says `unknown`, residual `interpret` must **not** open wizards / mutate via ActionPolicy verbs.  
**Opens:** cola **CI-1c**. Package stays **`0.8.7`** (no bump). Tag **`v0.8.7`** only after Engineer ★ (CI-1b smoke + this Buy + probes).

**Not:** CI-2 Continuity compose · CI-3 full ingress design · retiring `interpret` · ActionPolicy widen/narrow · changing Gemma default · G-03 test-Ollama isolation (separate Buy) · G-02 keyword hygiene · T40 · Conversation Engine.

---

## Why this Buy

CI-INV-0 + Cursor repro: with Gemma default, unclassified input (`hablar`, `Gracias.`, free questions) often returns valid `create_project`. Bug 52 only redirects `unknown` + `iterate` → `_handle_analyze`. Result: **create-project wizard opens over the active project** (`CREATE_PROJECT_INTERACTIVE`, copy “Vamos a definir el proyecto paso a paso.”). Voice STT hallucinations hit the same path. CI-1/CI-1b smoke never exercised it.

Maps to CI-0 locks **5** (claim-before-LLM) and **9** (quarantine `interpret` — keep path, stop harmful fallthrough).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-llm-interpret-unknown-guard`** (CI-1c). Package remains **`0.8.7`**. Tag **`v0.8.7`** only after Engineer ★ that covers CI-1b analyze smoke **and** this guard |
| 2 | In `handle_user_text` residual LLM branch (after `llm_interface.interpret`, same site as Bug 52): when resolver **`intent == "unknown"`** and `action_request["action"]` is any of **`create_project`**, **`calculate`**, **`simulate`**, or **`iterate`**, **do not** `self.handle(action_request)`. Route like Bug 52: **`_handle_analyze(user_input, llm_interface)`** (honest non-mutating contextual answer). Prefer one shared condition (all four verbs) over only `create_project` — same hallucination class |
| 3 | Keep existing Bug 52 `iterate` behaviour (analyze). Extending the set must remain behaviour-compatible for `iterate` |
| 4 | **Do not** change ActionPolicy, prompt schemas, or `interpret` JSON shape. Fence stays; ingress guard is orchestrator-side |
| 5 | When `invalid_llm_output` / `action: null` already returns the existing error message path — leave that path alone |
| 6 | Session must **stay IDLE** (or prior mode) after the guarded turn — never enter `CREATE_PROJECT_INTERACTIVE` from this fallthrough on an active project |
| 7 | Tests T1–T5 below; update CI cola + PRIORIDAD + state; **no** package bump; no spoken-map change (no new egress surface) |
| 8 | **Out** — CI-2 compose · delete `interpret` · stubbing live Ollama in voice `run_chat` tests (G-03) · goal_planner keyword F-1b · changing `DEFAULT_OLLAMA_MODEL` |

**Smoke ACCEPT (Engineer)** — with active project, unset `JARVIS_OLLAMA_MODEL`:

```text
python -m jarvis.adapters.cli.main --chat
User > hablar
→ NO "Vamos a definir el proyecto paso a paso."
→ NO create-project wizard / mode change
→ analyze-shaped or honest contextual reply (or invalid_llm_output if model refuses)
User > gracias
→ same: no create wizard
User > explicame el margen
→ still CI-1b criteria (no estabilidad plan wall, no instruction echo)
Also: real create ("nuevo proyecto" / intentional create intent) still works via deterministic path
```

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | Extend Bug 52 guard (~2586) per lock 2 — one clear condition + short comment citing CI-1c / CI-INV-0 G-01 |
| `tests/test_llm_interpret_unknown_guard_b1.py` | **new** T1–T5 |
| CI cola · PRIORIDAD · `engineering_state.json` | CI-1c Implemented awaiting review |
| `pyproject.toml` | **no version change** |

Do **not** touch ActionPolicy, Continuity builders, voice adapters, `prompt_builder`, `goal_planner`, `DEFAULT_OLLAMA_MODEL`.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Closed project + stub `interpret` → `create_project`: inputs `hablar`, `Gracias.` → result does **not** enter create wizard; message must **not** contain `Vamos a definir el proyecto paso a paso.`; session mode stays **IDLE** (or not `CREATE_PROJECT_INTERACTIVE`) |
| T2 | Same stub pattern for `calculate` and `simulate` actions under `unknown` → no `self.handle` mutation; routes to analyze (stub `analyze` return visible) |
| T3 | Stub `iterate` under `unknown` still hits analyze (Bug 52 regression) |
| T4 | Deterministic create still works: resolver/`nuevo`-style path (or `handle({"action":"create_project",...})` / documented intent that is **not** `unknown`) still can start create interactive — document which path the test hits |
| T5 | `invalid_llm_output` stub still returns existing error message path (no wizard) |

No live Ollama. No tip pins.

---

## 3. Acceptance

- [ ] Engineer smoke: `hablar` / `gracias` / `explicame el margen` per §0  
- [ ] Intentional create still works  
- [ ] Cursor review · Engineer ★ · tag **`v0.8.7`** (closes CI-1 + CI-1b + CI-1c)

---

## 4. Paste for Claude

```text
Implementation — B1-llm-interpret-unknown-guard (CI-1c)
Parent: CI-INV-0 G-01 blocker · CI-1b PASS WITH NOTES.
Package stays 0.8.7 (no bump). Tag v0.8.7 only after Engineer ★.

IC: .jes/artifacts/implementation_contract_llm_interpret_unknown_guard_b1.md
Review context: investigation_review_voice_llm_ci_audit_b0.md

GOAL: When resolver intent is "unknown", residual interpret must NOT
open create_project (or calculate/simulate/iterate) via self.handle.
Extend Bug 52 (orchestrator ~2586) to all four ActionPolicy verbs →
_handle_analyze. Session must stay out of CREATE_PROJECT_INTERACTIVE.
Keep deterministic create path. No ActionPolicy / prompt / DEFAULT change.

DO:
- orchestrator.py: extend unknown-intent guard (one condition, cite CI-1c)
- tests/test_llm_interpret_unknown_guard_b1.py T1–T5 (stub LLM)
- cola CI / PRIORIDAD / state — CI-1c implemented awaiting review
- Implementation report. No ACCEPT claim. No pyproject bump.

NO: CI-2 · delete interpret · G-03 Ollama test isolation · goal keywords ·
Continuity · T40 · Conversation Engine
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires ActionPolicy changes, Continuity ranking, or CI-2 compose.
