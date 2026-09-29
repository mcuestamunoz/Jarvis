# Implementation Contract — Chat explain intercept (`B1-chat-explain-intercept`)

**Project:** Jarvis  
**Date:** 2026-09-28 (reopened / redrafted same day)  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.6`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-09-29) — Cursor review PASS WITH NOTES; package **`0.6.6`**. Git tag **`v0.6.6`** when commit lands.  
**Prior:** READY FOR ★ → Claude implemented → Cursor review → Engineer ACCEPT.  
**Parents:**
- A6/R3 ★ CLOSED @ **`v0.6.5`** — Conceptos lines print `jarvis explain <id>`
- Field note 2026-09-28: typing that line **inside** `--chat` hits LLM → “No se pudo interpretar” + Mac collapse under local LLM load
- Tip / package: **`v0.6.5` / `0.6.5`**
- Placement DC ★ CLOSED · USER_GUIDE_EXPLAIN · intelligence handoff post-A6

**Type:** **Global-command intercept** — recognize explain phrases in Continuity chat **before** LLM; return cite text without Ollama/OpenAI.  
**Opens:** **`0.6.6` / `v0.6.6`** on Engineer ACCEPT.  
**Cola:** **A7**

**Not:** RAG · voice / world · topic/maps expand · changing Continuity ranking · weakening ActionPolicy · Conversation Engine · craft autonomy · silicon.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-chat-explain-intercept`** — inside `--chat`, explain runs without LLM |
| 2 | Where | `JarvisOrchestrator._handle_global_commands` — same grain as escape / `nuevo`; **first** check in `handle_user_text` / `_handle_user_text_inner` already calls this **before** any LLM path. Extend that function; do not add a second intercept layer |
| 3 | Match (minimum) | After `strip`, casefold prefix match only: `jarvis explain ` and `explain ` (space required after prefix). Query = remainder stripped. **Do not** steal bare ontology ids / craft phrases in this Buy |
| 4 | Optional flags | Do **not** implement `--list` / `--rung` inside chat in this Buy (CLI remains the home for those). If user types `explain --list`, treat as query miss or honest “use terminal `jarvis explain --list`” — prefer one-line honest redirect, still **no LLM** |
| 5 | Behavior hit | `resolve_explain_query(query)` + `format_explain_cite(cite)` from `jarvis.intelligence.explain` (A3). Return `status=ok`, `action=global_command` (or `explain`), `message=<formatted cite>` |
| 6 | Behavior miss | Same honesty as CLI miss text (see `run_explain_cli` stderr string) in `message`; `status` may be `ok` or `error` as long as **no LLM** is called |
| 7 | No LLM | Zero Ollama/LLM calls on matched explain prefixes. Tests must assert `llm_interface.interpret` (or equivalent) is **not** called |
| 8 | Import direction | Orchestrator **may** import `jarvis.intelligence.explain` helpers. `jarvis.intelligence.*` must **not** import `jarvis.core` / orchestrator (AST / existing isolation discipline) |
| 9 | Conceptos UX | Update pointer copy so chat users know they can type `explain <id>` (or `jarvis explain <id>`) **in chat**; terminal CLI unchanged. Touch: `format_continuity_cite_lines` and/or `_render_concept_lines` docs + USER_GUIDE §7 |
| 10 | Continuity | Do **not** change `explain_topics` ranking / `_explain_topics_for_continuity` logic — ingress only |
| 11 | Version | Bump `pyproject` / package to **`0.6.6`**; git tag **`v0.6.6`** only after Engineer ACCEPT |
| 12 | Docs | USER_GUIDE_EXPLAIN (§7 + limits) · `src/jarvis/intelligence/README.md` · ENTRY_MAP one-liner · PRIORIDAD A7 CLOSED after ACCEPT · CONNECTIONS: **extend C-114** (“also reachable via global command in `--chat`”) — prefer extend over new C-116 unless review finds a cleaner edge |

**Product sentence:**

```text
En --chat, "explain c-rate" / "jarvis explain …" responde la cita
sin llamar al LLM (evita colapso y el fallo de intención).
```

---

## 1. Files (expected touch set)

| Area | Path | Change |
|---|---|---|
| Orchestrator | `src/jarvis/core/orchestrator.py` | Explain branch in `_handle_global_commands` |
| Conceptos copy | `src/jarvis/intelligence/continuity_cite.py` and/or `src/jarvis/adapters/cli/main.py` | Pointer text mentions chat `explain <id>` |
| Tests | `tests/test_chat_explain_intercept_b1.py` (new) | T1–T5 |
| Version | `pyproject.toml` | `0.6.6` |
| Docs | `docs/USER_GUIDE_EXPLAIN.md`, intelligence README, ENTRY_MAP, CONNECTIONS C-114, PRIORIDAD | As §0 rows 9/12 |

Do **not** relocate retrieve into `knowledge/retriever.py`. Do not teach Continuity to read `ontology/`.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `handle_user_text("jarvis explain c-rate", llm)` → message contains DEFINICION / C-rate (or cite body); LLM interpret **not** called |
| T2 | `handle_user_text("explain imu", llm)` succeeds same path |
| T3 | `handle_user_text("explain no-existe-xyz", llm)` → honest miss · LLM interpret **not** called |
| T4 | Unrelated global / Continuity path unchanged (e.g. escape word or `nuevo` still works; a non-explain phrase is **not** swallowed by the intercept) |
| T5 | Explain path works even if LLM client is unhealthy / interpret would raise if called |
| T6 | AST or import check: `jarvis.intelligence.explain` (and continuity_cite) still do not import `jarvis.core` |

---

## 3. Acceptance

- [ ] Chat intercept works · no LLM on explain-prefix lines  
- [ ] Conceptos / USER_GUIDE wording updated for in-chat `explain`  
- [ ] Tests T1–T6 · implementation report · docs · package `0.6.6`  
- [ ] Cursor independent review PASS · Engineer ACCEPT · tag **`v0.6.6`**

---

## 4. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-chat-explain-intercept (A7)

IC: .jes/artifacts/implementation_contract_chat_explain_intercept_b1.md

In JarvisOrchestrator._handle_global_commands, intercept prefixes
"jarvis explain " and "explain " (casefold, strip) BEFORE any LLM.
Call resolve_explain_query + format_explain_cite (A3). Miss = honest
message, still no LLM. No --list/--rung in chat this Buy.
Update Conceptos pointer + USER_GUIDE: inside chat type explain <id>.
Tests T1–T6 (mock LLM must not be called on explain).
Bump pyproject to 0.6.6. Docs: intelligence README, ENTRY_MAP,
extend CONNECTIONS C-114. Report. Parent tip v0.6.5. No ACCEPT claim.
```

---

## 5. Engineer gate

Reply **★** (or “procede / implementa”) to authorize Claude.  
Until then: **no `src/` edits** for this Buy (Cursor role lock).
