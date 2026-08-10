# Commit Plan — FN-014…FN-023 stack (planning only)

**Date:** 2026-08-10  
**Status:** READY FOR ENGINEER APPROVAL — **no git commits executed**  
**Branch:** `main` (ahead of `origin/main` by 4 unrelated commits)  
**Baseline report:** suite 1558 after FN-023  

---

## Checkpoint rules (locked)

- No `workspace/`
- No secrets (scan of changed paths: clean)
- No accidental noise
- One architectural unit per commit
- No code edits while splitting
- No push until 4/5 local commits reviewed
- Tests for each cut travel with that cut’s commit
- Commit **only** when Engineer says explicitly “commitea”

---

## Exclude (never stage)

| Path | Why |
|---|---|
| `workspace/**` | Live project state / field sessions |
| `.env` / credentials | Secrets (none currently in the change set) |
| `__pycache__`, `.pytest_cache`, logs | Generated |

**Optional exclude (recommend):** `.jes/state/engineering_state.json` — volatile live JES cursor; prefer commit **5** only if you want a snapshot, or leave untracked forever.

---

## Soft-split vs hard-split (decision required)

Several files **mix multiple FNs in one working-tree diff**. Without interactive `git add -p` (forbidden in this agent) or hand-built patch series, we cannot put different hunks of the same file into different commits from the current tree alone.

### Recommendation: **Soft-split (A)**

| Approach | Meaning |
|---|---|
| **A — Soft-split (recommended)** | Put each **entangled file once**, in the **earliest** commit that needs it. Later commits add only **cut-pure** modules + tests. Bisect still works for pure modules (`acquisition_*`, `goal_planner`, `intent_resolver`, `project_closure`, FN tests). `orchestrator.py` lands early as one blob (contains FN-014…022 wiring). |
| **B — Hard-split** | Build ordered patch series / temporary trees so `orchestrator.py` grows FN-by-FN across commits 1→3. True bisect on orchestrator lines; **much more execution risk**; needs a dedicated execution session. |

**This plan assumes Soft-split A** unless Engineer orders B before “commitea”.

---

## Mixed files (detected)

| File | FNs entangled | Soft-split home |
|---|---|---|
| `src/jarvis/core/orchestrator.py` | FN-014…021 + FN-022 (not 023) | **Commit 1** (bulk is Acquisition); FN-019/020/021/022 hunks ride along |
| `src/jarvis/core/param_definition_session.py` | FN-016, 017, 018 | **Commit 1** |
| `docs/PROJECT_CONTINUITY.md` | FN-014…023 sections appended | **Commit 1** full file *or* split docs by commit if using hard doc edits — under Soft-split: **Commit 1** once (later commits skip docs) **OR** Commit 5 docs-only — see note |
| `docs/IMPLEMENTATION_TASKS.md` | same | same as Continuity |

**Docs note (Soft-split):** Putting all Continuity/TASKS updates in Commit 1 is honest (one blob) but pollutes Commit 1 with FN-019…023 narrative. Prefer:

- **Docs Soft:** Continuity + TASKS → **Commit 5 (JES/docs)** together with artifacts, **or**
- **Docs with code:** append-only narrative travels with Commit 1 only (simpler staging).

**Plan default:** docs → **Commit 5** with JES artifacts (keeps code commits code-focused). If Commit 5 is skipped, fold docs into Commit 1.

---

## Commit 1 — Acquisition Fluency (FN-014…018)

**Message (draft):**
```text
Add acquisition fluency: target authority, brief, and FN-014–018.

Deterministic IDLE/DEFINE acquisition routing with shared Brief prompts;
navigation/parse safety and plumbing without Conversation Engine.
```

### Stage (code + tests)

| Path | Role |
|---|---|
| `src/jarvis/core/acquisition_target.py` | **new** — FN-014/015/016 helpers |
| `src/jarvis/core/acquisition_brief.py` | **new** — FN-018 |
| `src/jarvis/config.py` | FN-016 `NAVIGATION_BACK_WORDS` |
| `src/jarvis/core/param_definition_session.py` | FN-016/017/018 session |
| `src/jarvis/core/orchestrator.py` | **entire current diff** (soft) — includes later FN wiring |
| `tests/test_fn014_acquisition_target_idle.py` | |
| `tests/test_fn015_pending_help.py` | |
| `tests/test_fn016_navigation_parse_safety.py` | |
| `tests/test_fn017_component_acquisition_plumbing.py` | |
| `tests/test_fn018_acquisition_brief.py` | |

### Not in Commit 1 (even under Soft-split)

- `goal_planner.py`, `intent_resolver.py` FN-023 lines, `project_closure.py` FN-020, `component_inference.py` FN-019, `aerial.py` count fix, FN-019…023 tests  
- Wait: **orchestrator.py already contains FN-019/020/021/022**. Soft-split means those land in C1. Then C2/C3 **must not re-stage orchestrator** (already committed). C2/C3 only add the **supporting** modules + tests that make those orchestrator calls resolvable.

**Critical Soft-split ordering implication:**

After C1 commits `orchestrator.py` with imports/`infer_component_for_key` / `component_presence_tier` / `is_engineering_intention` / `_handle_engineering_intent`:

- **C1 alone may be temporarily red** if those symbols live in files not yet committed — **unless** C1 also includes the minimal dependencies, **or** we reorder.

### Soft-split dependency fix (required)

To keep each commit **import-coherent** (tests for that layer green, or at least the package importable):

**Option A1 (preferred under Soft):** Commit 1 includes Acquisition-only files + orchestrator **but we must either hard-split orchestrator OR include forward deps in C1**.

**Practical Soft-split that stays green:**

| Commit | Must include for import/test coherence |
|---|---|
| **1** | acquisition_* + config + param_definition_session + orchestrator **+ all modules orchestrator already imports from later FNs** (`component_inference` FN-019 API, `project_closure` FN-020 API, `goal_planner` FN-022 API) **OR** hard-split orchestrator |
| **2** | FN-019…021 **tests** + aerial fix + any project_closure/component_inference leftover only if not in C1 |
| **3** | FN-022 **tests** (+ goal_planner if not in C1) |
| **4** | intent_resolver + FN-023 tests |
| **5** | docs + `.jes` |

That collapses Soft-split toward “C1 = all runtime code; C2–4 = tests-only slices” — still useful for bisect of **regressions by test file**, weaker for code archaeology.

### Better Soft-split (Engineer choice) — **Hybrid**

| Commit | Contents |
|---|---|
| **1 Acquisition** | `acquisition_target.py`, `acquisition_brief.py`, `config.py`, `param_definition_session.py`, tests FN-014…018, **and** orchestrator hunks that are Acquisition-only — **requires Hard-split of orchestrator** |
| **OR accept C1 mega-runtime** | All modified `src/` for FN-014…022 in Commit 1; Commits 2–4 = tests + tiny pure files only |

**Decision gate for Engineer before “commitea”:**

1. **Hybrid Soft (recommended compromise):**  
   - **Commit 1:** all current `src/` changes except `intent_resolver.py` (FN-023-only) — i.e. runtime stack FN-014…022 together.  
   - **Commit 2:** tests FN-019…021 + `aerial.py` if you prefer aerial with C2 — *if aerial already in C1, C2 is tests-only for 019–021*.  
   - Simpler: see **Final staging table** below.

---

## Final staging table (Hybrid Soft — locked proposal)

Goal: 4 code commits that are **each installable**, plus optional JES/docs.

### Commit 1 — Acquisition Fluency runtime + FN-014…018 tests

```
src/jarvis/core/acquisition_target.py          (new)
src/jarvis/core/acquisition_brief.py           (new)
src/jarvis/config.py
src/jarvis/core/param_definition_session.py
src/jarvis/core/orchestrator.py                # FULL current file (includes 019–022 wiring)
src/jarvis/core/component_inference.py         # needed by orchestrator FN-019 calls
src/jarvis/core/project_closure.py             # needed by orchestrator FN-020 calls
src/jarvis/core/goal_planner.py                # needed by orchestrator FN-022 calls
src/jarvis/domains/aerial.py                   # propeller count fix (used by FN-019 path)
tests/test_fn014_acquisition_target_idle.py
tests/test_fn015_pending_help.py
tests/test_fn016_navigation_parse_safety.py
tests/test_fn017_component_acquisition_plumbing.py
tests/test_fn018_acquisition_brief.py
tests/test_aerial_domain.py                    # count regression
tests/test_project_closure_v1.py               # FN-020-related updates ride with closure
tests/test_goal_planner.py                     # FN-022 keyword tests ride with goal_planner
```

**Honesty note:** Commit 1 message must say it also lands supporting FN-019…022 **runtime** to keep `orchestrator` coherent; behavioural ownership of 019–023 is still asserted by later test commits.

### Commit 2 — Coherence / Bare Size / Hygiene tests (FN-019…021)

```
tests/test_fn019_bare_propeller_size.py
tests/test_fn020_completeness_coherence.py
tests/test_fn021_session_hygiene.py
```

(Runtime already in C1.)

### Commit 3 — Engineering Intent tests (FN-022)

```
tests/test_fn022_engineering_intent.py
```

(Runtime already in C1 via `goal_planner` + orchestrator gate.)

### Commit 4 — Next-Step Continuity (FN-023) — **purest cut**

```
src/jarvis/core/intent_resolver.py
tests/test_fn023_next_step_help.py
```

### Commit 5 — Docs + JES artifacts (optional)

```
docs/PROJECT_CONTINUITY.md
docs/IMPLEMENTATION_TASKS.md
.jes/artifacts/implementation_contract_fn014.md … fn023.md
.jes/artifacts/implementation_review_fn022.md
.jes/artifacts/implementation_review_fn023.md
.jes/artifacts/cycle_close_fn014.md … fn021.md
.jes/artifacts/principle_acquisition_guided_engineering.md
.jes/artifacts/residual_engineering_intent_plan_vs_explore.md
.jes/artifacts/audit_2026-08-10_engineering_intent_vs_sticky_session.md
.jes/artifacts/field_note_2026-08-10_construir_dron_cli.md
.jes/artifacts/assessment_contract_acquisition_guidance.md
.jes/artifacts/assessment_report_acquisition_guidance.md
.jes/artifacts/commit_plan_fn014_fn023.md   # this file
# optional: .jes/state/engineering_state.json
```

---

## Pure-file map (quick reference)

| File | Owner under Hybrid Soft |
|---|---|
| `acquisition_target.py`, `acquisition_brief.py` | C1 |
| `config.py`, `param_definition_session.py` | C1 |
| `orchestrator.py` | C1 (entangled blob) |
| `component_inference.py`, `aerial.py`, `project_closure.py`, `goal_planner.py` | C1 (deps of blob) |
| `intent_resolver.py` | **C4 only** |
| tests FN-014…018 + aerial + closure + goal_planner | C1 |
| tests FN-019…021 | C2 |
| test FN-022 | C3 |
| test FN-023 | C4 |
| docs + `.jes/artifacts` | C5 |
| `workspace/` | **EXCLUDED** |

---

## Draft commit messages

1. `Add acquisition fluency stack (FN-014–018) and supporting FN-019–022 runtime.`
2. `Add FN-019–021 regression tests for bare size, coherence, and session hygiene.`
3. `Add FN-022 engineering-intent regression tests.`
4. `Route next-step help to Continuity via guidance patterns (FN-023).`
5. `Add JES contracts/reviews and Continuity docs for FN-014–023.`

---

## Pre-commit verification checklist (run when Engineer says “commitea”)

1. `git status` — confirm no `workspace/` staged  
2. Stage C1 paths only → `pytest` on C1 test files (+ smoke import)  
3. Commit C1  
4. Stage C2 → pytest FN-019…021 → commit  
5. Stage C3 → pytest FN-022 → commit  
6. Stage C4 → pytest FN-023 → commit  
7. Optional C5  
8. `git log --oneline -8` review with Engineer  
9. **No push**

---

## Out of scope until after checkpoint

- Create→BOM  
- Plan-vs-explore residual fix  
- Hard-split of `orchestrator.py` (unless Engineer upgrades this plan to B)

---

## Engineer decisions needed before execution

1. Confirm **Hybrid Soft** (this document) vs **Hard-split orchestrator (B)**.  
2. Confirm **Commit 5** yes/no (docs + `.jes`).  
3. Confirm exclude `.jes/state/engineering_state.json` (recommended yes).  
4. Say **“commitea”** (or “commitea sin JES”) to authorize execution.
