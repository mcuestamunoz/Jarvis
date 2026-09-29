# Implementation Contract — Assistant defer-to-Continuity Task (`B1-assistant-defer-continuity`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.9`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-29) — Cursor review PASS; package/tag **`0.6.9` / `v0.6.9`**.
**Parents:**
- [`design_contract_assistant_defer_continuity_b0.md`](design_contract_assistant_defer_continuity_b0.md) — ★ **ACCEPT CLOSED** 2026-09-29 (Engineer: redacta IC)
- T0 [`B1-assistant-explain-task`](implementation_contract_assistant_explain_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.8`**
- `IntentResolver.STATUS_PATTERNS` — existing Continuity/status vocabulary (seed source)
- `_handle_project_status` — existing Continuity fulfill (no LLM)

**Type:** **Second Assistant Task kind** — classify continuity/status phrases → `Task(defer_to_continuity)` → core fulfills via Continuity/`project_status`.  
**Opens:** **`0.6.9` / `v0.6.9`** on Engineer ACCEPT.  
**Cola:** **T1**

**Not:** vehicle verbs · world/voice · R4 · Continuity ranking changes · Conceptos/topic expand · rewriting Continuity copy · migrating every wizard soft-interrupt call site (see §0.9).

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-assistant-defer-continuity`** |
| 2 | Kind / capability | `task_kind=defer_to_continuity` · `required_capability_ids=["engineering.continuity"]` |
| 3 | Schema | Reuse `jarvis.capabilities.intent.Task` — no fork |
| 4 | Classify API | Extend `jarvis.intelligence.assistant_task` with `try_defer_to_continuity_task(intent) -> Task \| None` (name fixed). Optional thin `handle_continuity_defer_intent` **only if** needed; prefer classify-only in intelligence + fulfill in core |
| 5 | Phrase table | Finite exact-match set **`CONTINUITY_DEFER_PHRASES`** in `jarvis.config` (preferred) or `assistant_task` module. **Seed = full `IntentResolver.STATUS_PATTERNS` tuple as of tip `v0.6.8`** (copy values into the new frozenset/tuple). Match after a **minimal normalize** (strip + casefold + accent-strip equivalent to IntentResolver’s status check — implement locally or share a tiny pure helper **not** under Continuity ranking; intelligence must **not** import `jarvis.core.intent_resolver` / `project_continuity`) |
| 6 | Sync test | Test asserts every `IntentResolver.STATUS_PATTERNS` entry is covered by `CONTINUITY_DEFER_PHRASES` (tests **may** import both) so the tables cannot silently drift |
| 7 | Explain precedence | If explain-shaped (T0 / `CHAT_EXPLAIN_PREFIXES`), do **not** emit Continuity Task. Global-command order: escape → nuevo → **explain** → **continuity defer** → fallthrough |
| 8 | Fulfill | On Continuity Task: orchestrator calls existing **`_handle_project_status()`** (same dict/UX as today). Intelligence does **not** format Continuity bodies |
| 9 | Wizard soft-interrupts | Existing branches that already call `_handle_project_status` **may stay** direct this Buy (no mandatory refactor of every soft-interrupt). Mandatory wire: **`_handle_global_commands`** path for continuity-shaped lines → Assistant classify → `_handle_project_status` |
| 10 | LLM | Zero LLM on matched defer path |
| 11 | Fences | `assistant_task` may import `capabilities.intent` + `config`. Must not import `flight_software` / `vehicle_profiles` / `project_continuity` / `intent_resolver`. `project_continuity.py` zero ranking-import of intelligence |
| 12 | Version / docs | Bump **`0.6.9`**; intelligence README · USER_GUIDE one pointer · extend CONNECTIONS (prefer note on C-010 / Continuity ingress or thin extend — **no** new Conversation Engine). PRIORIDAD T1 |

**Product sentence:**

```text
"estado" / STATUS_PATTERNS → Assistant Task(defer_to_continuity)
→ engineering.continuity → _handle_project_status (Continuity), cero LLM.
```

---

## 1. Normative API (additions to `assistant_task.py`)

```python
CAPABILITY_ENGINEERING_CONTINUITY = "engineering.continuity"
TASK_KIND_DEFER_TO_CONTINUITY = "defer_to_continuity"

def try_defer_to_continuity_task(intent: Intent) -> Task | None:
    """If normalized intent.raw_text is in CONTINUITY_DEFER_PHRASES
    (and not explain-shaped), return Task with
    required_capability_ids=[CAPABILITY_ENGINEERING_CONTINUITY] and
    metadata task_kind=defer_to_continuity. Else None.
    Never calls LLM. Never imports Continuity ranking.
    """
```

Orchestrator (sketch):

```python
# after explain branch in _handle_global_commands:
intent = TerminalIntentAdapter.parse(stripped)
if try_defer_to_continuity_task(intent) is not None:
    return self._handle_project_status()
```

(Exact structure may use a cheap phrase probe before constructing Intent — same grain as T0 prefix probe — but **classify decision** must live in `try_defer_to_continuity_task`, not a second phrase brain in orchestrator.)

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Phrases | `src/jarvis/config.py` (preferred) | `CONTINUITY_DEFER_PHRASES` seeded from STATUS_PATTERNS |
| Assistant | `src/jarvis/intelligence/assistant_task.py` | `try_defer_to_continuity_task` + normalize helper |
| Wire | `src/jarvis/core/orchestrator.py` | Global-command continuity defer → Task → `_handle_project_status` |
| Tests | `tests/test_assistant_defer_continuity_b1.py` (**new**) | T1–T7 |
| Version | `pyproject.toml` | `0.6.9` |
| Docs | README · USER_GUIDE · CONNECTIONS/ENTRY_MAP · PRIORIDAD | §0.12 |

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | Intent `estado` (and ≥1 other STATUS phrase) → Task with `engineering.continuity` |
| T2 | Non-status craft line → `None` Task |
| T3 | Explain-shaped line → `try_defer_to_continuity_task` is `None` (explain wins / no double Task) |
| T4 | `handle_user_text("estado", exploding_llm)` → `action=project_status` (or equivalent Continuity payload); LLM not called |
| T5 | Every `IntentResolver.STATUS_PATTERNS` string ∈ `CONTINUITY_DEFER_PHRASES` (sync) |
| T6 | AST: `assistant_task.py` still forbids `jarvis.core` / FS / vehicle_profiles; `project_continuity` still no intelligence import |
| T7 | `pyproject` reads `0.6.9` |

Keep T0/A7 suites green; bump stale version checkpoints forward.

---

## 4. Acceptance

- [ ] Classify + Task emission for STATUS phrases  
- [ ] Fulfill via `_handle_project_status`; zero LLM  
- [ ] Explain precedence held · fences held · phrase sync test  
- [ ] Tests T1–T7 · report · docs · package `0.6.9`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.9`**

---

## 5. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-assistant-defer-continuity (T1)

IC: .jes/artifacts/implementation_contract_assistant_defer_continuity_b1.md
DC: .jes/artifacts/design_contract_assistant_defer_continuity_b0.md (★ CLOSED)

Add CONTINUITY_DEFER_PHRASES (seed = IntentResolver.STATUS_PATTERNS @ v0.6.8)
and try_defer_to_continuity_task in assistant_task.py.
Task: required_capability_ids=["engineering.continuity"], kind defer_to_continuity.
Wire _handle_global_commands: after explain branch, if Task → _handle_project_status().
Explain-shaped lines must not emit Continuity Task. Zero LLM on defer path.
intelligence must not import intent_resolver/project_continuity.
Wizard soft-interrupts may stay direct this Buy.
Tests T1–T7 (include STATUS_PATTERNS sync). Bump pyproject to 0.6.9.
Docs + PRIORIDAD. Report. Parent tip v0.6.8. No ACCEPT claim.
```

---

## 6. Engineer gate

Reply **★** (or “procede / implementa”) to authorize Claude.  
Until then: **no `src/` for this Buy.**
