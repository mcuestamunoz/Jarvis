# Implementation Contract — Chat Skill-first software Skills (`B1-assistant-chat-skill-first-software`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Cursor** (Engineer: “ejecutalo tú”)  
**Reviewer:** Cursor forensic PASS WITH NOTES · Engineer ★ ACCEPT → tag **`v0.6.31`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES** · tag **`v0.6.31`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T21 ★ @ **`v0.6.30`**  
**Type:** First Skill-first chat slice — **software Skills only**.  
**Opens:** **`0.6.31` / `v0.6.31`**. **Cola:** **T22**

**Not:** vehicle/ops Skill-first · making vehicle Skills `available` · voice · SD-GO_TO · tip pins · rewriting Continuity ranking.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-software`** |
| 2 | **Explain path:** when chat would fulfill explain, user-facing cite/miss text MUST come from `run_skill("skill.explain_concept", query=…).message` on `outcome=="ok"` (same underlying ontology fulfill — no second cite brain). Prefer routing inside `handle_explain_intent` or the orch explain branch — one place only |
| 3 | **Status path:** when `try_defer_to_continuity_task` matches, chat MUST call `run_skill("skill.project_status", project_status_provider=…)` with a read-only Continuity snapshot provider (`build_startup_context` or equivalent — **not** a second ranker). On `skill_stub` / `safety_reject` / `unknown_skill`: do **not** silently fall back to Task-only fulfill. On `ok` or `no_project`: return the same `action=project_status` + `startup_context` product shape chat/CLI already use (including existing proactive_question session side effects from `_handle_project_status` or a shared helper) — Skill-first is the **gate + path**; Continuity display SoT stays honest |
| 4 | Optional small `skills_runtime` polish if needed so provider dict may carry fields the gate needs — **no** new Continuity ranking logic inside `capabilities/` |
| 5 | Vehicle / arm / ops / CHARGE / sim copper paths: **unchanged** this Buy (still Task-direct) |
| 6 | Tests: chat `explain …` → Skill path (message matches cite honesty); chat status phrase → `run_skill` invoked + same project_status shape; vehicle phrase still Task path; tip-pin / ESC fences green |
| 7 | Version **`0.6.31`**; PRIORIDAD · PLATFORM · CONNECTIONS note (**no new C-xxx** unless unavoidable) |
| 8 | Out: vehicle Skill-first · voice · inventing Skill availability · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `intelligence/assistant_task.py` and/or `core/orchestrator.py` | explain + defer fulfill via `run_skill` |
| `capabilities/skills_runtime.py` | optional tiny provider-contract polish |
| `tests/test_assistant_chat_skill_first_software_b1.py` | **new** |
| `pyproject.toml` | `0.6.31` |
| Docs | short |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `explain <known>` → ok message via Skill path (cite / DEFINICION honesty) |
| T2 | status phrase → `project_status` shape; `run_skill` exercised (spy/mock or observable) |
| T3 | `hold` / `charge` still Task-direct (not Skill-first) |
| T4 | AST/source: explain fulfill no longer calls `fulfill_ontology_explain` **bypassing** `run_skill` on the chat seam |
| T5 | No tip pins |

---

## 3. Acceptance

- [x] Explain + status chat go through `run_skill` · vehicle/ops unchanged · `0.6.31`  
- [x] Cursor review · Engineer ACCEPT · tag **`v0.6.31`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-software (T22)
Parent tip: T21 ★ ACCEPT CLOSED @ v0.6.30. Implement now → package 0.6.31.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_software_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED)

Chat Skill-first for software Skills only:
- explain → run_skill("skill.explain_concept", query=…) message is UX
- status/defer → run_skill("skill.project_status", provider=read-only Continuity
  snapshot); keep project_status/startup_context product shape + side effects
Vehicle/arm/ops/CHARGE stay Task-direct. No tip pins. No ACCEPT claim.
Not voice / not vehicle Skill-first / not SD-GO_TO.
```
