# Implementation Contract — Capability Skills product seed (`B1-capability-skills-seed`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery (Engineer: IC pasted to Claude = authorized)  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.13`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS; package/tag **`0.6.13` / `v0.6.13`**.
**Parents:**
- T4 [`B1-assistant-software-safety-bridge`](implementation_review_assistant_software_safety_bridge_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.12`**
- T2 registry seed — capabilities `ontology.explain` / `engineering.continuity` already `available` software
- C1 `SkillRecord` schema — shipped empty `skills: []` since `v0.5.0`
- Engineer 2026-09-30: order **Skills seed first**, then **vehicle HOLD** (first of many autonomy Task kinds)

**Type:** **Descriptive Skills catalog fill** — two Skill rows that declare the required capabilities already used by Assistant Tasks. **No** Skill runtime, **no** dispatcher, **no** change to Task classify/Safety/fulfill.  
**Opens:** **`0.6.13` / `v0.6.13`** on Engineer ACCEPT.  
**Cola:** **T5**

**Not:** `run_skill` · Assistant looking up Skills before emitting Tasks · vehicle HOLD · changing Safety gates · Continuity ranking · voice/world · R4.

**Next after this Buy (not this IC):** DC **`DC-assistant-vehicle-hold-task`** — first vehicle Task kind (`request_hold` / HOLD); then later LAND, GO_TO, … each as own Buys.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-capability-skills-seed`** |
| 2 | Seed | Exactly **two** Skills in `default_registry.json` `skills` array (see §1). Capabilities + providers **unchanged** |
| 3 | Skill ids | `skill.explain_concept` · `skill.project_status` (names fixed) |
| 4 | Required caps | `skill.explain_concept` → `["ontology.explain"]`; `skill.project_status` → `["engineering.continuity"]` |
| 5 | Availability honesty | Both Skills **`availability: stub`** — declared catalog rows only; there is still **no** Skill execution path. Do **not** mark Skills `available` (that would imply a live Skill runner) |
| 6 | Version field | Skill `version` = `"0.6.13"` |
| 7 | Runtime | **Zero** `assistant_task` / orchestrator / Safety / Continuity changes. Task path remains authoritative |
| 8 | Validation | Existing registry reject-on-load must still catch dangling `required_capability_ids` (skills referencing unknown caps) — covered by load of seed + tests |
| 9 | Fase C empty-skills asserts | Any test that still asserts `skills() == []` as product truth must be adapted to “exactly these two stub skills” **or** keep asserting only what remains true for *that* Buy’s isolation story — do **not** weaken no-dispatch / no-craft-import checks. Prefer updating the 39-file T2-era “skills stay empty” comments/asserts the same way T2 updated empty capabilities — scripted if needed |
| 10 | Version / docs | Bump **`0.6.13`**; capabilities docstring/README · PLATFORM §13 one-liner · CONNECTIONS extend (**no new C-xxx**) · intelligence README pointer (“Skills catalog names the two Task verticals; emit path still Task not Skill”) · PRIORIDAD T5 |

**Product sentence:**

```text
El registry declara dos Skills stub que exigen ontology.explain /
engineering.continuity — catálogo honesto; el Assistant sigue emitiendo
Tasks (T0–T4), sin runtime de Skills.
```

---

## 1. Normative seed (`skills` array only)

Capabilities and providers blocks stay exactly as tip `v0.6.12`. Replace empty skills with:

```json
"skills": [
  {
    "id": "skill.explain_concept",
    "version": "0.6.13",
    "required_capability_ids": ["ontology.explain"],
    "availability": "stub"
  },
  {
    "id": "skill.project_status",
    "version": "0.6.13",
    "required_capability_ids": ["engineering.continuity"],
    "availability": "stub"
  }
]
```

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Seed | `src/jarvis/capabilities/data/default_registry.json` | §1 skills fill |
| Docs in package | `schemas.py` / `registry.py` / `__init__.py` docstrings as needed | Skills no longer forever-empty |
| Tests | `tests/test_capability_skills_seed_b1.py` (**new**) | T1–T6 |
| Adapt | Fase C / T2-era tests asserting `skills()==[]` | §0.9 |
| Version | `pyproject.toml` | `0.6.13` |
| Docs | PLATFORM · CONNECTIONS · intelligence README · PRIORIDAD | §0.10 |

Do **not** modify `assistant_task.py`, `safety.py` gate logic, orchestrator, or Continuity ranking.

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | `load_default().skills()` has exactly the two ids; both `availability == stub` |
| T2 | Each skill’s `required_capability_ids` resolve via `get_capability` (caps still present) |
| T3 | Capabilities/providers counts and ids unchanged vs T2 seed (still exactly the two software caps/providers) |
| T4 | Constructing a registry with a skill requiring unknown cap still raises `CapabilityRegistryError` (reject-on-load held) |
| T5 | AST / public API: `CapabilityRegistry` still has no execute/dispatch/run_skill public method names (same grain as C1/T2) |
| T6 | `pyproject` reads `0.6.13` |

Keep T0–T4 suites green; bump stale `0.6.12` checkpoints forward.

---

## 4. Acceptance

- [ ] Skills seed §1 loaded via `load_default`  
- [ ] Skills are `stub`; Task/Safety paths untouched  
- [ ] Empty-skills test cascade adapted, not weakened  
- [ ] Tests T1–T6 · report · docs · package `0.6.13`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.13`**

---

## 5. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-capability-skills-seed (T5)

IC: .jes/artifacts/implementation_contract_capability_skills_seed_b1.md
Parents: T4 ★ CLOSED @ v0.6.12; Engineer order: Skills then vehicle HOLD

Fill default_registry.json skills array per IC §1:
skill.explain_concept → [ontology.explain], stub;
skill.project_status → [engineering.continuity], stub.
Do NOT change capabilities/providers rows, assistant_task, safety gates,
orchestrator, or Continuity ranking. No Skill runtime/dispatcher.
Adapt any tests that still assert skills()==[] (T2-era cascade) without
weakening isolation/no-dispatch checks.
Tests T1–T6. Bump pyproject to 0.6.13. Docs + PRIORIDAD. Report.
No ACCEPT claim.
```

---

## 6. After ACCEPT

Cola next: **DC-assistant-vehicle-hold-task** (HOLD first; LAND/GO_TO later Buys).
