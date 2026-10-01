# Implementation Contract — Skills runtime software-only (`B1-capability-skills-runtime-software`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED after T20 ★  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.30`**

**Status:** **Implemented** (Claude Code) — Cursor review **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag **`v0.6.30`**.  
**Parents:** [DC ★ CLOSED](design_contract_capability_skills_runtime_software_b0.md) · T5 ★ · T20 ★ @ **`v0.6.29`**  
**Type:** First Skill runner — software Skills only.  
**Opens:** **`0.6.30` / `v0.6.30`**. **Cola:** **T21**

**Not:** vehicle Skill execution · copper · CHARGE · tip pins · Skill-first chat rewrite.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-capability-skills-runtime-software`** |
| 2 | Seed: `skill.explain_concept` + `skill.project_status` → `availability=available` (version bump fields OK). Other Skills remain `stub` |
| 3 | Add `jarvis.capabilities.skills_runtime.run_skill(skill_id: str, *, query: str \| None = None) -> SkillRunResult` (name flexible) with finite outcomes: `ok` / `reject` reasons (`unknown_skill` / `skill_stub` / `safety_reject` / …) |
| 4 | `skill.explain_concept` → reuse `fulfill_ontology_explain` (or identical cite path). `skill.project_status` → reuse Continuity status formatting used by defer fulfill (**read-only**; may require a ProjectState — if none, honest reject/`no_project`) |
| 5 | Software Safety: before run, required caps must satisfy same rules as T4 gate |
| 6 | Chat Task classify **unchanged** this Buy (still Task-direct). Tests call `run_skill` directly |
| 7 | Vehicle/ops skill ids → `skill_stub` reject |
| 8 | Version **`0.6.30`**; PLATFORM + intelligence README; CONNECTIONS (**no new C-xxx** unless unavoidable) |
| 9 | Out: copper · CHARGE · tip pins · Skill-first orchestrator rewrite |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | two skills → available |
| `capabilities/skills_runtime.py` | **new** runner |
| `capabilities/__init__.py` | export if needed |
| `tests/test_capability_skills_runtime_software_b1.py` | **new** |
| stub/cascade tests | adapt available vs stub |
| `pyproject.toml` | `0.6.30` |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `run_skill("skill.explain_concept", query=…)` → cite text / honest miss |
| T2 | `run_skill("skill.project_status")` with/without project — honest |
| T3 | `run_skill("skill.request_hold")` → stub reject |
| T4 | Seed: exactly those two Skills `available`; others stub |
| T5 | Chat Task path still green without Skill-first |
| T6 | No tip pins |

---

## 3. Acceptance

- [ ] Software Skills runnable · vehicle Skills stub · Task path intact · `0.6.30`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.30`**

---

## 4. Paste for Claude (AUTHORIZED — T20 ★ done)

```text
★ AUTHORIZED implementation — B1-capability-skills-runtime-software (T21)
Parent tip: T20 ★ ACCEPT CLOSED @ v0.6.29. Implement now → package 0.6.30.

IC: .jes/artifacts/implementation_contract_capability_skills_runtime_software_b1.md
DC: .jes/artifacts/design_contract_capability_skills_runtime_software_b0.md (★ CLOSED)

Mark skill.explain_concept + skill.project_status available.
Add skills_runtime.run_skill dispatching to existing fulfill paths.
Vehicle/ops skills stay stub. Chat Task classify unchanged.
Bump 0.6.30. No tip pins. No ACCEPT claim.
Not Skill-first chat (that is the next block after T21 ★).
```
