# Implementation Contract — FN-020

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Completeness coherence — Continuity ↔ BOM ↔ architecture progress  
**Depends on:** FN-017, FN-018 (closed); principle Acquisition as Guided Engineering  
**Does not implement:** FN-019 (bare `10x4.5`), Create→BOM handoff, Step D Guided Engineering  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. No commit/push unless asked.

**Priority:** Engineer ranked this **before** FN-019.

---

## 1. Intent

After a full architecture walk, the CLI can show **both**:

```text
✓ Arquitectura completa (4/4)
Situación: … aún tiene gaps de componentes
Evidencia: Gap: battery — incompleto
           Gap: sensors — incompleto
Siguiente paso: Arquitectura completa (4/4) — …
```

Live project `construir-dron-6ac77f21daf5`:

```text
battery:  completeness=medium  (measurable props present)
sensors:  completeness=medium  (gps_model present)
```

**Root contradiction:** two completeness models

| Consumer | Rule today | Effect on medium battery/sensors |
|---|---|---|
| `_block_progress_status` (architecture N/M) | non-`low` counts as present | blocks → **complete** → 4/4 |
| `build_component_bom` → Continuity gaps | `medium` → **incomplete** | Continuity says gaps / “aún tiene gaps” |

Acquisition Target / Brief / block chaining follow architecture. Continuity follows BOM. Same ProjectState, two truths → Guided Engineering would teach the wrong urgency.

**Target:** one coherent classification of component presence, consumed by architecture progress **and** Continuity (and BOM reporting). Messaging must not claim “architecture complete” and “component gaps blocking the system” as if they were the same failure mode.

---

## 2. Design — single classifier

### 2.1 Introduce one Core helper (preferred location: `project_closure.py`)

```text
classify_component(key, spec, project_state) -> Literal[
  "missing",      # not in components
  "stub",          # present but completeness low / empty
  "declared",      # non-low + has measurable signal (or intentional name-only policy — see below)
  "defined",       # high + measurable + no outstanding missing_fields (strict close)
]
```

Or equivalent enum/str with stable names. **Must** be pure over ProjectState (no I/O).

Reuse existing `_MEASURABLE` / motor_count-from-params logic from `build_component_bom` — do not fork a third copy of measurability.

### 2.2 Wire consumers

| Consumer | Must use classifier |
|---|---|
| `build_component_bom` | Buckets derived from classifier (missing / incomplete-or-stub / declared / defined / declarative-only if kept) |
| `_block_progress_status` / `_component_is_low` | “Present for architecture” = not `missing` and not `stub` (i.e. `declared` **or** `defined`) — **same threshold as today for block complete**, but expressed via the shared helper |
| `build_project_continuity` | Gap evidence + “aún tiene gaps” situation only for **actionable** incompleteness — see §2.3 |

Do **not** leave Continuity reading a BOM that still calls `medium` “incomplete” while architecture treats it as complete, without changing Continuity wording.

### 2.3 Continuity messaging rules (normative)

When architecture progress is **fully complete** (e.g. `4/4` and no next block):

1. **Do not** use situation  
   `"Física orientativa en PASS, pero el sistema aún tiene gaps de componentes."`  
   solely because BOM lists `medium` components that already count as architecture-present.

2. If only enrichment remains (`declared` but not `defined`), Continuity may:
   - omit them from “Gap:” evidence, **or**
   - show a softer line: e.g. `Detalle opcional: battery (especificación parcial)` / list `missing_fields` when non-empty  
   and next step should prefer optimize/simulate / “diseño validado…” — **not** “completa la especificación de battery” as if the architecture block were still open.

3. If `missing` or `stub` components remain, keep strong gap language (those are real acquisition targets).

4. When showing gaps, never print bare `"incompleto"` if `missing_fields` is empty — prefer `"especificación parcial"` or omit the gap line for that entry under rule 2.

### 2.4 Explicit non-goals of this cut

- Changing physics / sim PASS criteria  
- Forcing all components to `high` before 4/4  
- Create→propellers handoff  
- FN-019 bare size  
- Conversation Engine / Step D  

---

## 3. Scope

### In scope

| # | Change |
|---|---|
| 1 | Shared `classify_component` (or equivalent) in Core |
| 2 | Refactor `build_component_bom` to use it |
| 3 | Refactor architecture “is this component present?” to use the same present/stub threshold |
| 4 | Adjust Continuity situation/evidence/next-step per §2.3 |
| 5 | Tests from live field shape (battery+sensors medium, architecture complete) |
| Docs | Continuity note + IMPLEMENTATION_TASKS |

### Out of scope

- FN-019  
- Create wizard → component seeding  
- Softening `_BLOCK_COMPONENT_HINTS` “batería y motores” (optional tiny fix only if touched; else defer)  
- Step D  

---

## 4. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | Fixture like live project: all arch keys present; battery+sensors `medium` with measurable props; sim PASS | Architecture progress still **complete** (4/4) — do not regress block complete to require `high` unless classifier explicitly maps medium→stub (must **not**) |
| B | Same fixture → Continuity | Situation must **not** claim system still has component gaps in the strong sense while also advertising architecture complete; Gap lines must not say blank `incompleto` for those medium entries (omit or softer “parcial”) |
| C | Same fixture → next_useful_step | Must **not** prioritize “Completa battery…” / BOM-incomplete as if architecture were open; prefer PASS/optimize/simulate family when no missing/stub |
| D | Component truly `low` or missing while others done | Still strong gap + acquisition-relevant next step |
| E | Propulsion incomplete (propellers missing) | Unchanged urgency — architecture not 4/4; Continuity still points at propulsion/propellers |
| F | Existing Continuity unit tests updated if assertions assumed medium≡incomplete gap pressure |
| G | Full suite green |

---

## 5. Tests (required)

File: `tests/test_fn020_completeness_coherence.py` (+ update `tests/test_project_continuity.py` as needed)

Minimum:

1. `test_medium_battery_sensors_architecture_complete`  
2. `test_continuity_no_strong_gaps_when_architecture_complete_medium_only`  
3. `test_continuity_next_step_not_complete_battery_when_arch_closed`  
4. `test_stub_or_missing_still_strong_gap`  
5. `test_classifier_shared_bom_and_architecture` (same input → consistent present vs stub)

Reuse `construir-dron` shape or build specs matching live completeness.

Baseline suite: **1514**. Full suite required.

---

## 6. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/project_closure.py` | Classifier + BOM refactor |
| `src/jarvis/core/project_continuity.py` | Situation/evidence/next-step rules §2.3 |
| `src/jarvis/core/orchestrator.py` | `_component_is_low` / `_block_progress_status` call shared helper (thin) |
| `tests/test_fn020_completeness_coherence.py` | **Create** |
| `tests/test_project_continuity.py` | Update |
| `docs/PROJECT_CONTINUITY.md` | FN-020 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete |

**Forbidden:** FN-019 registry changes; Create handoff; Guidance Engine; LLM; silent deletion of medium components from ProjectState.

---

## 7. Implementation report (Claude)

1. Diff per file  
2. Classifier API + mapping table (missing/stub/declared/defined)  
3. How architecture vs Continuity each consume it  
4. Exact Continuity copy changes for the live 4/4 + medium case  
5. Tests + suite count  
6. Confirmation: no FN-019 / no Create handoff / no Step D  
7. Residuals  

No commit/push unless asked.

---

## 8. Review checklist (Cursor)

- [ ] One classifier; no dual thresholds left undocumented  
- [ ] Live-shaped medium battery/sensors: 4/4 OK, Continuity not contradictory  
- [ ] Real missing/stub still urgent  
- [ ] Suite green  
- [ ] FN-019 untouched  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 9. Queue after this cut

1. **FN-019** — bare `10x4.5` when pending propellers (contract already at `implementation_contract_fn019.md`)  
2. **Create → BOM handoff** — later contract  
3. **Step D** — blocked until Engineer authorizes  
