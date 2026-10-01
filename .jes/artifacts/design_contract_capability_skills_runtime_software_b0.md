# Design Contract — Skills runtime (software-only first rung) (`DC-capability-skills-runtime-software`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer: next cola after T14/T17 ★)  
**Author:** JES / Cursor  
**Type:** First **Skill runtime** — software Skills only  
**Parents:** T5 Skills seed ★ · T0/T1 Task fulfills · T4 software Safety

## Intent

Registry declares Skills as `stub` with no runner. First runtime: make the two **software** Skills (`skill.explain_concept`, `skill.project_status`) honestly `available` and add a thin dispatcher that fulfills them by calling the **existing** Task fulfill paths — without replacing Task classify and without touching vehicle/ops Skills.

## Locks

1. Mark only `skill.explain_concept` + `skill.project_status` → `availability=available`. All vehicle/arm/ops Skills stay `stub`.
2. Add `CapabilityRegistry.run_skill(skill_id, …)` (or sibling module `skills_runtime.py`) that: looks up skill → checks `available` → requires caps still pass T4-shaped software Safety → dispatches to existing `fulfill_ontology_explain` / Continuity status helper. **No** new Continuity ranking logic.
3. Assistant Task classify path remains authoritative for chat — runtime is an **additional** API (tests + optional orch hook). Do **not** require chat to go Skill-first this Buy (optional: orch may call run_skill after Task emit for those two kinds only — prefer **API + tests first**, chat still Task-direct unless trivial).
4. Vehicle/ops Skills: run_skill → reject/`stub` reason; never invent flight.
5. Out: copper · CHARGE · tip pins · voice · replacing Task seam.

## Opens

IC **`B1-capability-skills-runtime-software`** → package **`0.6.30`**.
