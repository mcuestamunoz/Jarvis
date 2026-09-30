# Implementation Contract — Assistant Task ↔ registry coherence (`B1-assistant-task-registry-coherence`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.11`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS; package/tag **`0.6.11` / `v0.6.11`**.  
**Parents:**
- T2 [`B1-capability-registry-product-fill`](implementation_contract_capability_registry_product_fill_b1.md) — ★ **ACCEPT CLOSED** @ **`v0.6.10`** (Engineer smoke OK)
- [`design_contract_capability_registry_product_fill_b0.md`](design_contract_capability_registry_product_fill_b0.md) §0 row 7 — explicitly deferred “soft id known in registry check” to a later IC
- T0 / T1 ★ CLOSED — `assistant_task` emits Tasks with finite capability strings; classify stays authoritative for *kind*, registry only gates *known id*
- Package parent: **`v0.6.10` / `0.6.10`**
- **Out / parked this cycle:** embedding JES-as-product inside `intelligence/` (Engineer 2026-09-30: not worth it) · vehicle verbs · voice/world · R4 · dispatcher / Safety

**Type:** **Soft coherence gate** — before returning a `Task`, `assistant_task` verifies every `required_capability_ids` entry exists in `CapabilityRegistry.load_default()`. Still **not** a dispatcher, Safety gate, or provider router.  
**Opens:** **`0.6.11` / `v0.6.11`** on Engineer ACCEPT.  
**Cola:** **T3**

**Not:** New Task kinds · changing Continuity / explain UX · registry write path · Skills · flight `available` · JES-in-product · Conversation Engine.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-assistant-task-registry-coherence`** |
| 2 | Where | `src/jarvis/intelligence/assistant_task.py` only for the gate (plus tests/docs/version). Prefer one private helper used by **both** `try_explain_concept_task` and `try_defer_to_continuity_task` after they would otherwise return a `Task` |
| 3 | Check | For each id in `task.required_capability_ids`: `CapabilityRegistry.load_default().get_capability(id) is not None`. Use **product default** registry only (no alternate seed injection required in production path) |
| 4 | On unknown id | **Refuse:** return `None` (same as “no Task”) — do **not** raise, do **not** emit Task with dangling capability, do **not** call LLM. Do **not** clear unrelated `intent.metadata` already written only if you set `task_kind` *after* the check succeeds (preferred: build Task, check, then write metadata / return; if check fails, return `None` with **no** `task_kind` written) |
| 5 | Soft ≠ dispatch | Check is **membership only**. Do **not** read `availability`, do **not** call providers, do **not** route fulfill through registry. Fulfill paths (cite / `_handle_project_status`) unchanged |
| 6 | Import direction | `assistant_task` **may** import `jarvis.capabilities.registry.CapabilityRegistry` (and schemas only if needed). Must **still not** import `jarvis.core` / `flight_software` / `vehicle_profiles`. `registry.py` must **still not** import `jarvis.intelligence` |
| 7 | Happy path | With T2 seed present, existing explain / defer phrases still emit the same Tasks as today (T0/T1 behavior preserved) |
| 8 | Orchestrator | **Zero** required changes unless a test needs it — global-command wire stays as T0/T1 |
| 9 | Version | Bump **`0.6.11`**; tag only after ACCEPT. Land only atop T2 ★ CLOSED @ **`v0.6.10`** |
| 10 | Docs | intelligence README (T3 section) · capabilities / PLATFORM one-liner (“Assistant soft-checks ids against default registry; still not a dispatcher”) · CONNECTIONS: **extend** existing T2/Fase C note (**no new C-xxx**) · PRIORIDAD T3 |

**Product sentence:**

```text
El Assistant solo emite Task si cada capability id pedida existe
en el registry por defecto — sin despachar, sin Safety, sin UX nueva.
```

---

## 1. Normative helper (sketch)

```python
def _capabilities_known_in_default_registry(capability_ids: list[str]) -> bool:
    registry = CapabilityRegistry.load_default()
    return all(registry.get_capability(cid) is not None for cid in capability_ids)
```

Call site pattern (both try_* functions):

```text
classify match → construct Task(required_capability_ids=[...])
  → if not _capabilities_known_in_default_registry(...): return None
  → set intent.metadata["task_kind"] = ...
  → return Task
```

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Assistant | `src/jarvis/intelligence/assistant_task.py` | Helper + gate on both try_* emitters |
| Tests | `tests/test_assistant_task_registry_coherence_b1.py` (**new**) | T1–T6 |
| Regression | Keep T0/T1/T2 suites green; bump stale `0.6.10` checkpoints forward |
| Version | `pyproject.toml` | `0.6.11` |
| Docs | intelligence README · PLATFORM/CONNECTIONS extend · PRIORIDAD | §0.10 |

Do **not** change `default_registry.json` shape in this Buy (T2 seed stays).

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | Explain-shaped Intent still → Task with `ontology.explain` when default seed present (T0 regression via gate) |
| T2 | Status phrase (`estado`) still → Task with `engineering.continuity` when default seed present (T1 regression via gate) |
| T3 | With a **monkeypatched** `CapabilityRegistry.load_default` returning empty registry (or registry missing those ids): explain-shaped Intent → `None` Task; no `task_kind` on metadata |
| T4 | Same empty/missing patch: status phrase → `None` Task; no `task_kind` |
| T5 | AST: `assistant_task.py` may import `jarvis.capabilities.registry`; must not import `jarvis.core` / `flight_software` / `vehicle_profiles`; `registry.py` still does not import `jarvis.intelligence` |
| T6 | `pyproject` reads `0.6.11` |

Optional but nice: assert gate does not call any fulfill path / LLM (no orchestrator required if unit-level).

---

## 4. Acceptance

- [ ] Both Task emitters soft-check default registry membership before return  
- [ ] Unknown id → `None`, no raise, no dangling Task  
- [ ] T0/T1 happy path unchanged with T2 seed · fences held · no dispatcher  
- [ ] Tests T1–T6 · report · docs · package `0.6.11`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.11`**  
- [ ] Prerequisite: T2 ★ ACCEPT + tag **`v0.6.10`** landed

---

## 5. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-assistant-task-registry-coherence (T3)

IC: .jes/artifacts/implementation_contract_assistant_task_registry_coherence_b1.md
Parents: T2 ★ CLOSED @ v0.6.10; DC registry-fill §0.7 soft check

In assistant_task.py, after constructing a Task in try_explain_concept_task
and try_defer_to_continuity_task, soft-check every required_capability_ids
entry exists in CapabilityRegistry.load_default() (get_capability not None).
If any missing → return None, do not set task_kind, do not raise.
Membership only — do not read availability, do not dispatch, do not change
fulfill paths or orchestrator. May import capabilities.registry; still no
core/FS/vehicle_profiles; registry must not import intelligence.
Tests T1–T6 (happy path + monkeypatched empty registry refuse).
Bump pyproject to 0.6.11. Docs: intelligence README, extend CONNECTIONS/PLATFORM
note (no new C-xxx), PRIORIDAD. Report. No ACCEPT claim.
```

---

## 6. Engineer gate

1. ★ ACCEPT **T2** (commit + tag **`v0.6.10`**) if not done yet.  
2. Reply **★** (or “procede / implementa”) on **this IC** to authorize Claude.  

Until IC ★: **no `src/` for T3.**  
**Parked:** JES-as-product inside Intelligence (explicit non-goal this cycle).
