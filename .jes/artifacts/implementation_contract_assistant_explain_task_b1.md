# Implementation Contract — Assistant explain Task (`B1-assistant-explain-task`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.8`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-29) — Cursor review PASS; package/tag **`0.6.8` / `v0.6.8`**.  
**Parents:**
- [`design_contract_assistant_first_task_b0.md`](design_contract_assistant_first_task_b0.md) — ★ **ACCEPT CLOSED** 2026-09-29 (ratified as drafted)
- A7 ★ CLOSED @ **`v0.6.6`** — chat explain intercept (behavior must not regress)
- A0–A8 cite/topic path ★ CLOSED @ tip **`v0.6.7`**
- C2: `jarvis.capabilities.intent.Intent` / `Task`

**Type:** **Assistant Task seam** — `Intent` → emit `Task(explain_concept)` → fulfill via `ontology.explain` (A3 cite). Refactor A7 to call this path.  
**Opens:** **`0.6.8` / `v0.6.8`** on Engineer ACCEPT.  
**Cola:** **T0**

**Not:** `defer_to_continuity` · vehicle verbs · world/voice · Conversation Engine · Continuity ranking · capability registry product fill · R4 · maps/topic expand · N1 casefold.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-assistant-explain-task`** — first Assistant Task emission on disk |
| 2 | Module | New `src/jarvis/intelligence/assistant_task.py` (name fixed unless collision — keep this name) |
| 3 | API (normative) | See §1 — `try_explain_concept_task` + `fulfill_ontology_explain` (or equivalent names in §1; do not invent a third public entry without need) |
| 4 | Task shape | Use **`jarvis.capabilities.intent.Task`** as-is. Set `required_capability_ids=["ontology.explain"]`. Record kind in `Intent.metadata` (e.g. `task_kind=explain_concept`) and/or Task-side convention documented in module docstring — **no forked Task subclass** |
| 5 | Match grain | Same prefixes as A7 / `CHAT_EXPLAIN_PREFIXES`: `jarvis explain ` and `explain ` (casefold, strip, required trailing space). Query = remainder. **No** bare-id steal |
| 6 | `--list` / `--rung` | Keep A7 honesty: redirect-to-terminal message, **still no LLM**, still **no** Task required (or emit Task then fulfill with same redirect — prefer **no Task** for flag-only lines to avoid fake capability claims) |
| 7 | A7 refactor | `_handle_chat_explain` / global-command explain branch **must** call the intelligence Assistant path (build Intent via `TerminalIntentAdapter.parse` or equivalent → try Task → fulfill). Orchestrator must **not** keep a parallel resolve+format copy as the primary brain |
| 8 | CLI `jarvis explain` | May keep calling A3 directly **or** go through fulfill helper — either OK if cite text stays identical; prefer sharing `fulfill_ontology_explain` to avoid drift |
| 9 | Refuse | Non-explain Intent → Assistant returns `None` / no Task; caller falls through unchanged |
| 10 | Fences | `intelligence` may import `capabilities.intent`. Must **not** import `flight_software` / `vehicle_profiles` / Continuity ranking. `project_continuity.py` **unchanged** (zero ranking import of intelligence) |
| 11 | Version | Bump **`0.6.8`**; tag only after ACCEPT |
| 12 | Docs | intelligence README · USER_GUIDE_EXPLAIN one pointer · ENTRY_MAP / CONNECTIONS: note Assistant Task seam (extend C-114 or add thin C-117 — **prefer extend C-114** “fulfill also via Assistant Task” unless a new edge is clearer) · PRIORIDAD T0 |

**Product sentence:**

```text
explain en chat/terminal pasa por Assistant → Task(explain_concept)
→ ontology.explain → misma cita A3; cero LLM; sin segundo cerebro.
```

---

## 1. Normative API (`assistant_task.py`)

```python
CAPABILITY_ONTOLOGY_EXPLAIN = "ontology.explain"
TASK_KIND_EXPLAIN_CONCEPT = "explain_concept"

def try_explain_concept_task(intent: Intent) -> Task | None:
    """If intent.raw_text is explain-shaped (A7 prefixes), return Task
    with required_capability_ids=[CAPABILITY_ONTOLOGY_EXPLAIN] and
    intent metadata / docstring marking TASK_KIND_EXPLAIN_CONCEPT.
    Else return None. Never calls LLM. Never reads Continuity ranking.
    """

def fulfill_ontology_explain(query: str, *, ontology_root: Path | None = None) -> str:
    """Provider for ontology.explain: A3 resolve+format, or the same
    honest miss / --list|--rung redirect strings A7 already uses.
    Returns message body string only (caller wraps status/action).
    """
```

Helpers to parse prefix→query may live in this module or reuse `CHAT_EXPLAIN_PREFIXES` from `jarvis.config` (preferred — single prefix table).

Optional thin:

```python
def handle_explain_intent(intent: Intent, *, ontology_root: Path | None = None) -> str | None:
    """try_explain_concept_task; if Task, fulfill with extracted query; else None."""
```

Orchestrator A7 path should use this (or try+fulfill explicitly).

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Assistant | `src/jarvis/intelligence/assistant_task.py` | **New** — §1 |
| Package export | `src/jarvis/intelligence/__init__.py` / README | Export or document public helpers |
| A7 wire | `src/jarvis/core/orchestrator.py` | Explain branch calls Assistant path; drop duplicate primary resolve logic |
| Tests | `tests/test_assistant_explain_task_b1.py` (**new**) | T1–T7 |
| Regression | Keep A7 tests green (adapt imports if needed — **do not weaken** exploding-LLM asserts) |
| Version | `pyproject.toml` | `0.6.8` |
| Docs | README · USER_GUIDE · ENTRY_MAP · CONNECTIONS · PRIORIDAD | §0.12 |

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | Explain-shaped Intent (`explain c-rate` / `jarvis explain c-rate`) → `Task` with `ontology.explain` in `required_capability_ids` |
| T2 | Non-explain Intent (`quiero diseñar un dron`) → `None` Task |
| T3 | `fulfill_ontology_explain("c-rate")` contains DEFINICION / C-rate cite body |
| T4 | Unknown query → honest miss string (A7/CLI equivalent); no raise |
| T5 | `handle_user_text("explain imu", exploding_llm)` still works; LLM not called (A7 regression via Assistant path) |
| T6 | AST: `assistant_task.py` does not import `jarvis.core` / `flight_software` / `vehicle_profiles`; `project_continuity.py` still does not import `jarvis.intelligence` |
| T7 | `pyproject` reads `0.6.8` |

Bump prior version-checkpoint tests forward per established pattern.

---

## 4. Acceptance

- [ ] `assistant_task.py` emits `explain_concept` Task / refuses honestly  
- [ ] A7 chat path routes through Assistant; no LLM; no UX regression on prefixes  
- [ ] Fences AST held · Continuity untouched for ranking  
- [ ] Tests T1–T7 · report · docs · package `0.6.8`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.8`**

---

## 5. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-assistant-explain-task (T0)

IC: .jes/artifacts/implementation_contract_assistant_explain_task_b1.md
DC: .jes/artifacts/design_contract_assistant_first_task_b0.md (★ CLOSED)

Add jarvis.intelligence.assistant_task with try_explain_concept_task +
fulfill_ontology_explain (reuse CHAT_EXPLAIN_PREFIXES / A3 cite).
Task uses capabilities.intent.Task; required_capability_ids=["ontology.explain"].
Refactor orchestrator A7 explain branch to call this path (no parallel brain).
--list/--rung: honest terminal redirect, no LLM, prefer no fake Task.
Tests T1–T7; keep A7 exploding-LLM coverage. Bump pyproject to 0.6.8.
Docs: intelligence README, USER_GUIDE pointer, extend C-114, PRIORIDAD.
Report. Parent tip v0.6.7. No ACCEPT claim.
```

---

## 6. Engineer gate

Reply **★** (or “procede / implementa”) to authorize Claude.  
Until then: **no `src/` for this Buy.**
