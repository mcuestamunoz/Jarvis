# Design Contract — Capability registry product fill (`DC-capability-registry-product-fill`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **design contract only**  
**Implementer:** none for this DC — disk behavior is a **later IC** after Engineer ★  
**Reviewer:** Engineer ★ (ratify / amend)

**Status:** **READY FOR ★**  
**Type:** Design / Architecture Lock — first **honest product seed** in C1’s empty Capability Registry for the two capability ids Assistant Tasks already require.  
**Not** an Implementation Contract. **Not** a dispatcher. **Not** Safety / FS / vehicle verbs / voice / world. **Not** Conversation Engine.

**Parents:**
- C1 [`B1-fase-c-capability-registry-scaffold`](implementation_contract_fase_c_capability_registry_scaffold_b1.md) — ★ ACCEPT CLOSED @ **`v0.5.0`** — schemas + empty `default_registry.json`
- T0 [`B1-assistant-explain-task`](implementation_contract_assistant_explain_task_b1.md) — ★ CLOSED @ **`v0.6.8`** — Tasks require `ontology.explain`
- T1 [`B1-assistant-defer-continuity`](implementation_contract_assistant_defer_continuity_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.9`** — Tasks require `engineering.continuity`
- Engineer 2026-09-29: ACCEPT T1 + proceed natural next = registry product fill (not vehicle / world)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | Product seed for the **two** capability strings Assistant already emits: **`ontology.explain`** and **`engineering.continuity`** |
| 2 | Honesty | Registry remains **descriptive**. Seeding does **not** create a Task→actuator dispatcher, Safety gate, or FS path. Fulfill stays where T0/T1 put it (intelligence cite / `core` Continuity) |
| 3 | Availability enum | Extend `CapabilityAvailability` with **`available`** — allowed **only** for non-actuation, already-shipped software fulfill paths. Flight / vehicle / radio ids must **not** appear as `available` in product seed (omit them, or `not_implemented` if a later Buy needs a placeholder) |
| 4 | Provider kind | Extend `ProviderKind` with **`software`** (name fixed unless ★ amends) for in-process product providers that are neither vehicle nor device |
| 5 | Seed shape (normative ids) | Default product registry (`CapabilityRegistry.load_default` seed) must contain **at least**: CapabilityRecord `ontology.explain` (`available`) + CapabilityRecord `engineering.continuity` (`available`) + matching ProviderRecord(s) of kind `software` whose `offered_capability_ids` cover those two. Skills: **zero** in this Buy (optional later) |
| 6 | Provider id names | Prefer finite stable slugs, e.g. `provider.ontology_explain` and `provider.engineering_continuity` (or one software provider offering both — IC picks one of these two shapes; both OK if ids stable and offered list exact) |
| 7 | Task path | **Do not** require Assistant/`assistant_task` to look up the registry before emitting a Task in this Buy. Finite strings on `Task.required_capability_ids` stay authoritative for classify. Optional later IC may add a soft “id known in registry” check |
| 8 | No flight | No `flight_*` / HOLD/LAND / GO_TO capabilities as `available`. No `vehicle`/`device` providers claiming live actuation |
| 9 | Out | Voice · world · R4 · Continuity ranking · rewriting T0/T1 UX · Capability registry UI · Safety executable |
| 10 | Next code | After this DC ★ → IC **`B1-capability-registry-product-fill`** (cola **T2**) → package bump (likely **`0.6.10`**) on that IC’s ACCEPT |

**Product sentence:**

```text
El registry deja de estar vacío: declara ontology.explain y
engineering.continuity como available (software), sin fingir vuelo
ni convertir el registry en dispatcher.
```

---

## 1. Why this Buy (not vehicle / R4)

T0 + T1 proved Intent→Task→capability **strings**. C1 left the product seed **empty** on purpose. The next honest step on the same axis is: those strings become **named rows** in the registry — so platform docs and future Safety/dispatch can see what Assistant already requires — **without** claiming motors fly.

Vehicle verbs and `world/` stay deferred: they need Safety + real providers, not a seed fill.

---

## 2. Explicit non-goals

- Making `CapabilityRegistry` the runtime router for orchestrator turns  
- Marking flight capabilities available  
- Changing Continuity ranking or explain cite behavior  
- Filling Skills catalog  

---

## 3. Next after this DC is ★

1. Cursor drafts IC **`B1-capability-registry-product-fill`** (T2).  
2. Engineer ★ IC → Claude implements.  
3. Cursor review → ACCEPT → tag (IC sets version, likely **`v0.6.10`**).

---

## 4. Engineer gate

Reply **★** (or amend: enum names / single vs dual providers / soft registry check on emit) to lock this DC.  
Until ★: **no `src/` for registry product fill.**
