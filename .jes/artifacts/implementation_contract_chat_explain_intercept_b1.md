# Implementation Contract — Chat explain intercept (`B1-chat-explain-intercept`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.6`**

**Status:** **Parked** (Engineer 2026-09-28) — defer implementation; reopen when ready to intercept explain inside `--chat` without LLM.  
**Was:** ★ AUTHORIZED briefly after field note (Mac collapse via LLM). Tip parent remains **`v0.6.5`**.  
**Parents:**
- A6/R3 ★ CLOSED @ **`v0.6.5`** — Conceptos lines print `jarvis explain <id>`  
- Engineer field note 2026-09-28: typing that line **inside** `--chat` hits LLM → “No se pudo interpretar” + Mac collapse under local LLM load  
- Tip / package: **`v0.6.5` / `0.6.5`**

**Type:** **Global-command intercept** — recognize explain phrases in Continuity chat **before** LLM; return cite text without Ollama/OpenAI.  
**Opens:** **`0.6.6` / `v0.6.6`** on Engineer ACCEPT.  
**Cola:** **A7**

**Not:** RAG · voice · changing Continuity ranking · weakening ActionPolicy · full Conversation Engine.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-chat-explain-intercept`** — chat can run explain without LLM |
| 2 | Where | `JarvisOrchestrator._handle_global_commands` (same grain as escape / `nuevo`) — **before** any LLM path |
| 3 | Match | Strip; accept prefixes (casefold): `jarvis explain ` · `explain ` · optional bare ontology id **only if** also matching a known solid id or alias via existing `resolve_explain_query` — prefer explicit `explain` / `jarvis explain` prefixes for this Buy to avoid stealing craft phrases. **Minimum required:** `jarvis explain <query>` and `explain <query>` |
| 4 | Behavior | On match: call `resolve_explain_query` + `format_explain_cite` (A3). Return `status=ok`, `action=global_command` (or `explain`), `message=<formatted cite>`. Miss → honest message (same as CLI miss), **still no LLM** |
| 5 | No LLM | Zero Ollama/LLM calls on this path (test: intercept must not reach `llm_interface.interpret`) |
| 6 | Conceptos UX | Update Conceptos formatter / USER_GUIDE: clarify that inside chat you may type `explain <id>` (or `jarvis explain <id>`); outside chat use CLI subcommand |
| 7 | Continuity | Do not change `explain_topics` ranking; only chat ingress |
| 8 | Version | **`0.6.6`**; tag on ACCEPT |
| 9 | Docs | USER_GUIDE_EXPLAIN · intelligence README · ENTRY_MAP one-liner · PRIORIDAD A7 · ARCHITECTURE/PLATFORM pointers · CONNECTIONS note on C-114/C-115 chat ingress (extend C-114 detail or add C-116 if cleaner — prefer **extend C-114** “also reachable via global command in chat” unless a new edge is clearer) |

**Product sentence:**

```text
En --chat, "explain c-rate" / "jarvis explain …" responde la cita
sin llamar al LLM (evita colapso y el fallo de intención).
```

---

## 1. Tests

| ID | Assert |
|---|---|
| T1 | Input `jarvis explain c-rate` via `handle_user_text` (or `_handle_global_commands` + full path with LLM mocked to fail if called) returns message containing DEFINICION / C-rate |
| T2 | Input `explain imu` same path succeeds |
| T3 | Unknown `explain no-existe-xyz` → honest miss message · **LLM interpret not called** (mock assert) |
| T4 | Unrelated chat phrase still can reach existing paths (regression: e.g. escape / or a known Continuity command unchanged) |
| T5 | Orchestrator explain path does not require LLM client to be healthy |

---

## 2. Acceptance

- [ ] Chat intercept works · no LLM on explain lines  
- [ ] Conceptos / USER_GUIDE wording updated  
- [ ] Tests T1–T5 · report · docs · `0.6.6` · tag after ACCEPT  

---

## 3. Paste for Claude

```text
★ AUTHORIZED implementation — B1-chat-explain-intercept

IC: .jes/artifacts/implementation_contract_chat_explain_intercept_b1.md

In _handle_global_commands, intercept "jarvis explain <q>" and "explain <q>"
BEFORE any LLM. Use A3 resolve+format; miss = honest message, still no LLM.
Update Conceptos/USER_GUIDE: inside chat type explain <id>.
Tests T1–T5 (mock LLM must not be called on explain).
Bump pyproject to 0.6.6. Docs pointers. Report.
Parent tip v0.6.5. No ACCEPT claim.
```
