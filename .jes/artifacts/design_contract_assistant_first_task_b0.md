# Design Contract — First Assistant Task seam (`DC-assistant-first-task`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **design contract only**  
**Implementer:** none for this DC — disk behavior is a **later IC** after Engineer ★ on this DC  
**Reviewer:** Engineer ★ (ratify / amend)

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-29) — ratified as drafted; no amendments. Unlocks IC **`B1-assistant-explain-task`** (T0) only — not `src/` by itself.  
**Type:** Design / Architecture Lock — **what the first `Task` is**, who emits it, and what it must never become.  
**Not** an Implementation Contract. **Not** a version bump by itself. **Not** voice, world, lavadora, GO_TO, or Conversation Engine.

**Parents:**
- [`design_contract_assistant_placement_b0.md`](design_contract_assistant_placement_b0.md) (**★ CLOSED**) — `intelligence/` = Assistant home; seams Intent → Assistant → capabilities → Safety → provider
- [`design_contract_fase_c_skill_capability_architecture.md`](design_contract_fase_c_skill_capability_architecture.md) (**C0 ★ CLOSED**) — Assistant ≠ FS; `Intent → Task → required capabilities → …`
- C2 shipped stubs: `jarvis.capabilities.intent.Intent` / `Task` (`Task` exists; almost no production path constructs it)
- Explain/cite epoch **A0–A8 ★ CLOSED** @ tip **`v0.6.7`** — honest ontology cite canal exists; it is **library**, not Assistant-as-tasker yet
- Engineer 2026-09-29: intelligence = platform Assistant that turns intent into tasks with required capabilities; proceed with first minimal Task DC (no Conversation Engine)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Definition | **`intelligence/` owns Assistant tasking.** Explain/cite remains a *capability provider* the Assistant may require — not the definition of the package |
| 2 | Reuse Task schema | First seam uses existing **`jarvis.capabilities.intent.Task`** (`intent_id` + `required_capability_ids`). Do **not** fork a second Task type in `intelligence/` unless a later DC ★ amends |
| 3 | Who constructs Task | **`jarvis.intelligence`** (Assistant) constructs `Task` from an `Intent` (or refuses honestly). Orchestrator / CLI may *call* Assistant; they must not become a second task brain |
| 4 | First Task kind (this DC) | **`explain_concept`** only — see §2. One vertical that already has a real provider (A3/A7 cite path) |
| 5 | Capability id (normative string) | Required capability for that kind: **`ontology.explain`** (finite string; not a registry product yet — C1 registry stays empty until its own IC) |
| 6 | No Conversation Engine | No parallel orchestrator. No LLM as SoT. No moving Continuity ranking / `step()` / craft decisions into `intelligence/` |
| 7 | No vehicle / world this DC | No `GO_TO`, HOLD/LAND, house rooms, lavadora, STT, `VoiceIntentAdapter` fill, `world/` mkdir |
| 8 | Continuity stays Engineer | Craft “cómo va el proyecto / siguiente paso” stays **`core/`**. A later Task kind may *defer* to Continuity; **not** this first kind |
| 9 | Safety | Emitting a Task ≠ Safety allow ≠ actuation. First kind is read-only cite — still must not write motors or skip future Safety when other kinds land |
| 10 | Next code | Only after this DC ★: a named IC (suggested cola **T0** / `B1-assistant-explain-task`) may implement the seam and bump package |

---

## 1. What “Assistant Task” means here

```text
Intent  (capabilities — what was asked, channel)
   ↓
Assistant  (intelligence — classify / emit Task or refuse)
   ↓
Task  (intent_id + required_capability_ids)
   ↓
Provider fulfill   (this Buy’s only provider: ontology explain / cite)
```

**Product sentence:**

```text
El Assistant no “explica porque el orquestador tiene un if”.
Emite un Task explain_concept que exige ontology.explain;
el provider de cite cumple — sin LLM como verdad.
```

---

## 2. First kind — `explain_concept` (normative)

| Field | Lock |
|---|---|
| Kind name | `explain_concept` (metadata or future enum — IC picks representation; keep finite) |
| When | Terminal (or chat) Intent whose ask is an **explain-shaped** query — same grain as A7 prefixes `jarvis explain ` / `explain `, or an explicit Assistant entry the IC defines. **No** bare craft phrases stolen |
| Task | `Task(intent_id=…, required_capability_ids=["ontology.explain"])` |
| Fulfill | Existing A3 resolve + format (and A7 intercept may be **refactored** to call Assistant→Task→fulfill so there is one path — IC decides; behavior must stay: zero LLM on this path) |
| Refuse | Non-explain Intent → Assistant returns no Task / honest miss for this kind (fall through to today’s Continuity/LLM craft paths — **unchanged** by this DC alone) |

**Forbidden for this kind:** inventing SKU numbers; reading Continuity to pick craft next step; calling FS; creating world graph.

---

## 3. Explicitly deferred Task kinds (not this DC)

| Kind (illustrative) | Why later |
|---|---|
| `defer_to_continuity` / project status | Needs clear handoff contract with `core/` — separate IC |
| `request_vehicle_verb` (HOLD/LAND/…) | Needs Safety + FS provider honesty |
| `go_to_place` / home automation | Needs `world/` + device providers — A4 parked |
| Multi-step plans / memory | Planning + memory subsystems — not first seam |

---

## 4. Package shape (design — not mkdir free-for-all)

Conceptual (IC may add one small module under `intelligence/`):

```text
src/jarvis/intelligence/
  … existing explain / retrieve / continuity_cite …
  assistant_task.py   # or similarly named — Intent → Task | None for explain_concept
```

Locks:

- May import `jarvis.capabilities.intent` (`Intent`, `Task`).
- Must **not** import `jarvis.flight_software` / `vehicle_profiles`.
- Must **not** import Continuity ranking helpers to *decide* craft steps.
- `project_continuity.py` still must not import `intelligence` for ranking (A6 fence holds).

---

## 5. Relation to A7

A7 proved: chat can cite without LLM.  
This DC says: that behavior belongs under **Assistant Task emission**, not forever as a one-off orchestrator special case.

IC after ★ may:

- keep A7 user-visible behavior, and  
- route fulfill through `intelligence` Task emission,  

or keep A7 as thin adapter calling the same Assistant function. **No behavior regression** on explain prefixes.

---

## 6. Out of scope (this DC)

- Implementing `src/` (wait for IC after ★)  
- R4 LLM cite  
- Maps/topic expand  
- Filling capability registry product surface beyond the finite string `ontology.explain`  
- Voice / radio / API Intent adapters becoming real  
- Conversation Engine / Decision Engine  

---

## 7. Next after this DC is ★

1. Engineer ★ ratifies (or amends kind / capability id).  
2. Cursor drafts IC **`B1-assistant-explain-task`** (cola **T0**) — implement Intent→Task→`ontology.explain` fulfill; tests; docs; package bump.  
3. Claude implements after IC ★.  
4. Later DCs/ICs: `defer_to_continuity`, vehicle verbs, world — each ★ alone.

---

## 8. Engineer gate

Reply **★** (or amend: different first kind / capability id) to lock this DC.  
Until ★: **no `src/` Task-seam implementation.**
