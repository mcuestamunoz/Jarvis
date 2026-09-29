# Design Contract — Assistant defer-to-Continuity Task (`DC-assistant-defer-continuity`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **design contract only**  
**Implementer:** none for this DC — disk behavior is a **later IC** after Engineer ★  
**Reviewer:** Engineer ★ (ratify / amend)

**Status:** **READY FOR ★**  
**Type:** Design / Architecture Lock — **second Task kind**: craft/status asks → Continuity Engineer, without moving ranking into `intelligence/`.  
**Not** an Implementation Contract. **Not** voice/world/GO_TO. **Not** Conversation Engine.

**Parents:**
- [`design_contract_assistant_first_task_b0.md`](design_contract_assistant_first_task_b0.md) (**★ CLOSED**) — first kind `explain_concept`; deferred Continuity kind named here
- T0 [`B1-assistant-explain-task`](implementation_contract_assistant_explain_task_b1.md) (**★ ACCEPT CLOSED** @ **`v0.6.8`**) — Intent→Task→provider seam on disk
- C0 / placement — Continuity stays in `core/`; Assistant issues tasks
- Engineer 2026-09-29: ACCEPT T0 + proceed natural next = Continuity defer

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | Second Task kind: **`defer_to_continuity`** (name fixed unless ★ amends) |
| 2 | Capability id | **`engineering.continuity`** (finite string; registry product fill still later) |
| 3 | Schema | Reuse **`jarvis.capabilities.intent.Task`** — same as T0; no fork |
| 4 | Who classifies | **`jarvis.intelligence`** emits Task (or refuses). Extend `assistant_task.py` (or sibling) — do **not** create a second Assistant brain in orchestrator |
| 5 | Who fulfills | **`core/`** — existing Continuity / `project_status` / estado surface (`_handle_project_status` or equivalent). Intelligence **must not** reimplement ranking or import `project_continuity` to *decide* `next_useful_step` |
| 6 | Match grain | **Finite, explicit** status/continuity phrases only (IC lists the table). Minimum seed aligned with today’s soft-interrupt / estado vocabulary (e.g. `estado`, `status`, `project_status` / Spanish equivalents already owned by Continuity ingress). **No** stealing arbitrary craft design chat into this Task |
| 7 | Explain precedence | If a line is explain-shaped (T0 prefixes), **`explain_concept` wins** — never also emit Continuity Task for the same turn |
| 8 | LLM | Zero LLM on matched Continuity-defer path (same honesty as T0 explain path) |
| 9 | Ranking fence | `project_continuity.py` still never imports `intelligence` for ranking. Topics/Conceptos unchanged by this DC |
| 10 | Out | Vehicle verbs · world · voice · multi-step plans · R4 · rewriting Continuity copy |
| 11 | Next code | After this DC ★ → IC **`B1-assistant-defer-continuity`** (cola **T1**) → package bump on that IC’s ACCEPT |

**Product sentence:**

```text
El Assistant reconoce “estado / status…” y emite Task(defer_to_continuity)
que exige engineering.continuity; core cumple con Continuity existente —
sin que intelligence decida el siguiente paso del craft.
```

---

## 1. Seam shape

```text
Intent  (terminal / chat line)
   ↓
Assistant classify
   ├─ explain-shaped?     → Task(explain_concept) → ontology.explain     [T0]
   ├─ continuity-shaped?  → Task(defer_to_continuity) → engineering.continuity
   │                              ↓ fulfill in core (_handle_project_status / Continuity render)
   └─ else                → None → today’s craft/LLM paths unchanged
```

---

## 2. Fulfill contract (normative)

| Step | Owner | Lock |
|---|---|---|
| Classify phrase → Task | `intelligence` | Returns `Task` with `required_capability_ids=["engineering.continuity"]` + metadata `task_kind=defer_to_continuity` |
| Fulfill | `core` orchestrator (or thin core helper) | Calls **existing** Continuity/project_status path; message/UX must stay Continuity’s (no second “fake Continuity” formatter in intelligence) |
| Import direction | — | Orchestrator may call intelligence to classify. Intelligence must **not** import Continuity ranking modules. Core may fulfill without intelligence importing `project_continuity` |

---

## 3. Explicit non-goals

- Teaching Continuity new ranking rules  
- Replacing LLM craft interpretation for free-form design turns  
- `defer_to_continuity` for every sentence that mentions the project  
- Capability registry UI / Safety / FS  

---

## 4. Next after this DC is ★

1. Cursor drafts IC **`B1-assistant-defer-continuity`** (T1).  
2. Engineer ★ IC → Claude implements.  
3. Cursor review → ACCEPT → tag (IC sets version, likely **`0.6.9`**).

---

## 5. Engineer gate

Reply **★** (or amend kind name / capability id / phrase table scope) to lock this DC.  
Until ★: **no `src/` for Continuity-defer.**
