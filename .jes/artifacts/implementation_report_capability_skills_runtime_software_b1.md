# Implementation Report — Skills runtime software-only (`B1-capability-skills-runtime-software`, T21)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_capability_skills_runtime_software_b1.md`](implementation_contract_capability_skills_runtime_software_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_capability_skills_runtime_software_b0.md) · T5 ★ · T20 ★ ACCEPT CLOSED @ **`v0.6.29`**  
**Status:** Implemented — await Cursor review → Engineer ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.30` / **`v0.6.30`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/skills_runtime.py` | **new** — `run_skill(skill_id, *, query=None, project_status_provider=None) -> SkillRunResult`. Looks a Skill up, requires `availability=available`, re-checks required capability ids through the same T4-shaped `SoftwareCapabilitySafetyGate` rules, dispatches to the one existing fulfill path per Skill |
| `src/jarvis/capabilities/data/default_registry.json` | `skill.explain_concept`/`skill.project_status` → `availability=available`, `version` bumped to `0.6.30` (IC §0 row 2 allows the version bump). Every other Skill (vehicle/arm/ops) left byte-unchanged, still `stub` |
| `src/jarvis/capabilities/__init__.py` | exports `run_skill`/`SkillRunResult` |
| `tests/test_capability_skills_runtime_software_b1.py` | **new** T1–T6 |
| `tests/test_capability_skills_seed_b1.py` | T5's own two tests that asserted these Skills stay `stub` retargeted to `available` (one set-membership check, one exact-JSON-shape check) — both now factually correct per this Buy |
| `pyproject.toml` | `0.6.30` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) · intelligence README |

**Not touched:** Assistant Task classify (`assistant_task.py` still never looks a Skill up before emitting a Task — verified by new T5, which also asserts the literal strings `"skills_runtime"`/`"run_skill"` don't appear in that file's source), `_handle_global_commands`/any orchestrator wiring, any vehicle/ops Skill's `availability` (all stay `stub`), `propose_command`/`AutonomyVerb`/any sim or flight path, tip-version pins (T17 guardrail re-verified green).

---

## 2. A design note on layering (flagging for review)

`jarvis.capabilities` modules have consistently never imported `jarvis.intelligence`/`jarvis.core` upward (documented in `registry.py`'s and `safety.py`'s own docstrings: "`registry.py` itself still never imports `jarvis.intelligence`"). This Buy's own IC locks the file at `capabilities/skills_runtime.py` and explicitly names `fulfill_ontology_explain` (which lives in `jarvis.intelligence.assistant_task`) as the thing to reuse for `skill.explain_concept` — so `skills_runtime.py` does import it, lazily (inside the function body, not at module load time, avoiding any import-time cycle risk), which is the **first** `capabilities → intelligence` import edge in this codebase. I resolved the other half of the same tension — `skill.project_status` needing a live `ProjectState`/Continuity formatting that only exists on `JarvisOrchestrator` (`jarvis.core`) — **without** crossing that boundary at all: `run_skill` accepts an optional `project_status_provider` callable that the *caller* supplies (e.g. a test, or a future orchestrator hook, passing in `orchestrator.build_startup_context` — the read-only builder, deliberately not `_handle_project_status`, which has a session-mutating side effect). With no provider supplied, the honest result is `reject`/`no_project` — no Continuity ranking logic is duplicated here, satisfying DC §0 row 2 ("No new Continuity ranking logic") by construction. Flagging the one new import edge explicitly in case Cursor/Engineer want it resolved differently (e.g. moving `skills_runtime.py` to a different package).

**Also caught early:** my first draft of the new test file constructed a bare `JarvisOrchestrator()` (no `workspace_root`) for the `project_status_provider` end-to-end check, which picked up a real project from the user's actual on-disk workspace instead of being isolated — fixed to use `tmp_path` like the rest of the suite before this ever reached a commit.

---

## 3. Tests executed

```text
pytest tests/test_capability_skills_runtime_software_b1.py -q
→ 7 passed

pytest tests/test_capability_skills_seed_b1.py -q
→ all passed (2 retargeted)

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3895 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T21 tip: baseline was `3888 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 7 new T21 tests passing.

---

## 4. Remaining

None for this Buy. Explicitly **not** in scope (per IC/DC): wiring `run_skill` into chat ("Skill-first" — the next block after this one), vehicle/ops Skill execution, copper, CHARGE.
