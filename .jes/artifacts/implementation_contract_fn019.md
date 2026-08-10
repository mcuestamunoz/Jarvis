# Implementation Contract — FN-019

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION (FN-020 closed — this cut is next)  

**Plan ref:** Field unblock after FN-018 — bare propeller size  
**Depends on:** FN-017, FN-018 (closed); **FN-020 (completeness coherence) preferred first**  
**Does not implement:** Step D, Conversation Engine, battery priority, Brief rewrite  

**Workflow:** Claude implements → Engineer forwards report → Cursor reviews. No commit/push unless asked.

**Engineer priority (2026-08-10):** FN-020 Continuity/BOM coherence first; then this cut; Create→BOM handoff later.

---

## 1. Intent

CLI field block (new project → propulsion → declare propellers):

```text
Brief: Describe las hélices. Ej: '10x4.5' o 'hélices de carbono'
User: 10x4.5
Today: Brief repeats (infer → generic_component low → key-aware re-prompt)
User: ayudame a definir
Today: Brief again (FN-015 by design)

Target: bare size pattern while pending/expected is propellers → save propellers (same as "hélices 10x4.5")
0 LLM
```

Also: `COMPONENT_PROMPTS` / Brief example must not advertise an input that fails.

---

## 2. Root cause

Aerial propeller rule keywords are only `helice` / `hélice` / `propeller` / `props` (`aerial.py`).  
`extract_propeller_properties` can parse `10x4.5`, but **match never runs** without a keyword → `generic_component`.  
FN-017/018 correctly refuse generic write and re-prompt — so the user loops on the Brief.  
Deferred explicitly in FN-016/017; now field-blocking because the example text is `10x4.5`.

---

## 3. Scope

### In scope

| # | Change |
|---|---|
| 1 | When acquisition expected/pending includes `propellers`, treat bare `NxP` / `N x P` (inches) as propeller input — either extend aerial match **or** a narrow pre-infer hook in `_handle_component_description` that only fires if `propellers` ∈ `expected_keys` |
| 2 | Align example copy if needed so advertised examples work (prefer making `10x4.5` work over changing the example away from it) |
| 3 | Tests: bare `10x4.5` and `10 x 4.5` save propellers in Phase A; `hélices 10x4.5` still works; non-propeller pending must not invent propellers from bare size |
| Docs | Short Continuity note |

### Out of scope

- Step D / Brief redesign  
- Accepting bare `10` alone as full propellers (diameter-only may stay low/partial — prefer `NxP` with pitch)  
- Torque/battery routing  
- Changing create-project helices diameter/RPM bridge (separate concern)  

---

## 4. Design (preferred)

**Preferred (smallest, scoped):** In `_handle_component_description`, before or after `infer_components`, if `propellers` ∈ `expected_keys` and input matches propeller size regex (reuse logic from `extract_propeller_properties` / same pattern), synthesize or force a propellers spec via existing extractor — do **not** open this globally in IDLE for random `10x4.5` text unless also clearly in propeller acquisition.

**Alternative:** Add size-pattern as a propeller keyword/signal inside `aerial.py` match — must prove it does not steal unrelated inputs (e.g. frame `450g`, motor models). Prefer expected_keys gate if unsure.

FN-016 float guard: bare `10` (no x pitch) must still not become `collected_params["propellers"]=10` on numeric path; this cut is about **component inference**, not ParamDefinitionSession zip.

---

## 5. Acceptance

| # | Scenario | Expected |
|---|---|---|
| A | Phase A propellers pending; `10x4.5` | Saves propellers; completeness not low; leaves wizard or advances |
| B | Same; `10 x 4.5` | Same as A |
| C | Same; `hélices 10x4.5` | Still works |
| D | Phase A propellers; `5` (bare number) | Still re-prompt Brief (not silent float assign; not fake propellers unless you explicitly support diameter-only — default: re-prompt) |
| E | Frame pending; `10x4.5` | Must **not** save as propellers (stay frame path / re-prompt frame) |
| F | FN-018 Brief / FN-015 help still 0 LLM | Green |
| G | `plastico 450g` still no generic write | Green |

---

## 6. Tests

`tests/test_fn019_bare_propeller_size.py` — minimum A–E + F/G smoke.

Full suite. Baseline: **1514**.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/domains/aerial.py` | Optional match signal |
| `src/jarvis/core/orchestrator.py` | Preferred expected_keys-gated hook |
| `src/jarvis/core/component_inference.py` | Only if shared helper is cleaner |
| `src/jarvis/core/acquisition_target.py` / `acquisition_brief.py` | Copy only if example must change |
| `tests/test_fn019_bare_propeller_size.py` | **Create** |
| docs Continuity / IMPLEMENTATION_TASKS | Note |

**Forbidden:** Conversation Engine; Step D; LLM; weakening FN-017 generic refuse globally.

---

## 8. Report (Claude)

1. Diff per file  
2. Approach chosen (aerial vs expected_keys hook) + why  
3. Regex / match rules + non-matches  
4. Proof frame pending does not steal `10x4.5`  
5. Tests + suite count  
6. No Step D / no Conversation Engine  
7. Residuals  

No commit/push unless asked.

---

## 9. Review checklist (Cursor)

- [ ] `10x4.5` saves propellers in Phase A  
- [ ] Frame path not stolen  
- [ ] Bare `5` does not corrupt  
- [ ] FN-017/018 regressions green  

**Verdict:** PASS / PASS WITH NOTES / FAIL  
