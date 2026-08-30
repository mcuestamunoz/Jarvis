# Implementation Contract — Requirements Closure (IC 1 / Project Closure arc)

**Project:** Jarvis  
**Date:** 2026-08-30  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Requirements subsystem closure — **★3(b) explicit no-restrictions semantics** + **G26 mid-session constraint write path** + defense-in-depth on derived params. Unblocks `ASSEMBLY READY` for otherwise-complete projects without touching physics, catalog UX, or BOM policy.

**Investigation:** [`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`](investigation_report_project_closure_assembly_ready.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_project_closure_assembly_ready.md`](investigation_review_project_closure_assembly_ready.md) — **PASS WITH NOTES**  
**Checkpoint base:** tag **`v0.3.0`** / **`checkpoint-propeller-catalog-bind`** · commit `2efe1c2`

**Arc position:** IC **1 of 3** (Option D). IC 2 = Battery Catalog UX + G27. IC 3 = Closure policy + propeller `sku_resolved`. **G24 out of scope.**

**Workflow:** Claude implements **Req-1 → Req-6 in order** + report → Cursor review → CLI probe on Fixture 2 → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | Sequence Option D — **this IC first** (Requirements Closure). |
| **★2** | G26: fix the **write path** into `current_parameters["restrictions"]` (re-derive `parsed_constraints` via existing `ProjectState.model_copy` override). Add `is_derived` gate to `param_definition_session` as **defense-in-depth**, not instead of the write path. |
| **★3** | **(b) RATIFIED** — explicit “sin restricciones” counts as **requirements satisfied**. Strict distinction below (§2). **Must not** fabricate numeric constraints or infer undeclared requirements. |
| **★4–★9** | Deferred to IC 2/3 — **do not implement** battery UX, G27, propeller `sku_resolved`, family policy docs, or G24 in this cut. |

**IC 1 gate (Engineer, locked):**

> Requirements PASS **without** altering physics, **without** touching P2-1, **without** inventing components, **without** weakened tests.

---

## 1. Problem / intent

### 1.1 Today

`_requirements_evidence` (`engineering_readiness.py:880-889`):

```python
defined = bool(constraints)  # constraints = parsed_constraints only
```

`parsed_constraints` is derived solely from numeric regex matches in `_parse_constraints` (`state_schema.py:20-54`). Placeholder phrases like `"no"` / `"ninguna"` match **no** regex → `{}` → `requirements.defined=False` **even when the user explicitly declared no restrictions at create time**.

**Live proof (Fixture 2):** workspace `1-324107ef7006` — 8/9 subsystems PASS, **0 gaps**, sim PASS — blocked only by `requirements INCOMPLETE` with `restrictions="no"`, `parsed_constraints={}`.

**G26 (parallel bug):** mid-session attempts to restate constraints (e.g. `"cambia restrictions a autonomia minima 15 min"`) can write a loose `current_parameters["autonomia"]` via `param_definition_session.apply_and_recalculate` — bypassing the `is_derived` gate that `semantic_intent_adapter.adapt()` already enforces — while **`restrictions` never updates**, so `parsed_constraints` stays stale.

### 1.2 Target

**A — Explicit no-restrictions (★3 b):**

```text
restrictions = "no" | "ninguna" | … (closed explicit-none list, §2.2)
  → requirements.defined = True
  → parsed_constraints stays {} (no fake numeric keys)
  → Fixture 2 → overall ASSEMBLY_READY (8/9 already PASS + requirements PASS)
```

**B — Numeric constraint declared:**

```text
restrictions updated to "autonomia minima 15 min" (mid-session or at create)
  → current_parameters["restrictions"] written
  → parsed_constraints re-derived → {autonomy_min: 15.0}
  → if sim autonomy < 15 → honest GAP-REQUIREMENTS-UNMET:autonomy (HIGH)
  → if sim autonomy ≥ 15 → requirements PASS, no gap
  → never writes loose current_parameters["autonomia"]
```

**C — Unset / ambiguous:**

```text
restrictions absent | "" | whitespace-only | unparseable constraint text
  → requirements.defined = False (INCOMPLETE)
```

---

## 2. Locked semantics (★3 — non-negotiable)

### 2.1 `requirements.defined` predicate

Replace the bare `bool(parsed_constraints)` check with a **two-branch** predicate (single helper — see Req-2):

```text
requirements_declared(project_state) :=
    bool(parsed_constraints)                          # numeric constraints parsed
    OR restrictions_explicitly_none(restrictions)     # ★3(b) — see §2.2
```

```text
requirements.defined := requirements_declared(project_state)
```

**Must NOT:**

- Add fake entries to `parsed_constraints` for explicit-none (e.g. do **not** set `autonomy_min=0` or a sentinel float).
- Treat empty `parsed_constraints` alone as PASS unless §2.2 applies.
- Infer numeric requirements the user never declared.

### 2.2 Explicit-none phrase list (closed)

Implement `restrictions_explicitly_none(text: str) -> bool` in **`state_schema.py`** (same module as `_parse_constraints` — single authority).

**Minimum tokens (normalize: strip, lower, NFD diacritic-strip — reuse `_normalize_name` pattern or equivalent):**

| Token / phrase class | Examples |
|---|---|
| Spanish/English negation | `"no"`, `"ninguna"`, `"ninguno"`, `"ningun"`, `"none"`, `"n/a"`, `"na"` |
| Explicit none phrases | `"sin restricciones"`, `"sin restriccion"`, `"no restrictions"`, `"without restrictions"` |

**Must return False for:**

- `None`, missing key, `""`, whitespace-only
- Strings that **contain** parseable numeric constraints (e.g. `"autonomia minima 15 min"`) — numeric branch wins; explicit-none is only when **no** numeric key parsed **and** the full string matches explicit-none
- Ambiguous free text (`"tal vez"`, `"no se"`) — treat as **not** explicit-none → INCOMPLETE

**Interaction with FN-010 objective fallback:** when `restrictions` is explicit-none, **do not** use objective fallback to manufacture `parsed_constraints` for the purpose of flipping `requirements.defined` from false to true. Objective fallback remains for `_parse_constraints` numeric extraction only when restrictions is **not** explicit-none. (If restrictions says `"no"` but objective says `"15 min autonomia"`, ★3(b) says restrictions explicit-none wins for the **declared** state — document behavior in report; **recommended:** explicit-none on restrictions means no autonomy requirement from objective either, since the user declared no restrictions at project level. Engineer intent: `"no"` is a deliberate project-level statement.)

### 2.3 Unparseable declared constraint → INCOMPLETE

When `restrictions` is **non-empty**, not explicit-none, and `_parse_constraints` returns `{}` (and objective fallback also yields `{}`):

```text
requirements.defined = False
```

Do **not** silently PASS. User attempted to declare a constraint the system could not parse.

### 2.4 GAP-REQUIREMENTS-UNMET unchanged in spirit

When `parsed_constraints` **does** contain numeric targets, existing gap logic (`_requirements_unmet_gaps`, `engineering_readiness.py:623-696`) continues to fire honestly (mass/autonomy/blocking_params). ★3(b) does **not** suppress unmet numeric requirements.

---

## 3. G26 fix scope (★2 — locked)

### 3.1 Primary: mid-session `restrictions` write path

**Goal:** user can update the **project-level** constraint string after create; `ProjectState.model_copy(update={"current_parameters": {...}})` re-derives `parsed_constraints` (existing override at `state_schema.py:160-173`).

**Minimum user-facing scenarios (must work without LLM inventing values):**

| User turn (examples) | Expected persistence |
|---|---|
| `"cambia restrictions a autonomia minima 15 min"` | `current_parameters["restrictions"]` = normalized constraint text; `parsed_constraints.autonomy_min` = 15.0 |
| `"restrictions: peso maximo 2.5kg"` | `parsed_constraints.max_weight_kg` = 2.5 |
| `"sin restricciones"` / `"ninguna"` | `restrictions` updated; explicit-none → `parsed_constraints={}`, `requirements.defined=True` |

**Routing guidance (investigate minimally, implement smallest surface):**

- Prefer a **deterministic** path (orchestrator intercept and/or `param_definition_session` special-case) that recognizes **restrictions / restricciones** as a **project-level string field**, not a float param.
- Do **not** route constraint phrases through `apply_and_recalculate({"autonomia": 15})` or any derived param write.

**Out of scope for G26 fix:** iterate-wizard `IterationDraft.restrictions` (`iterate_interactive_session.py`) — that remains a per-iteration note, not project-level constraints (confirmed in investigation report §3).

### 3.2 Defense-in-depth: `is_derived` gate in `param_definition_session`

Before `apply_and_recalculate` commits param updates, reject any key where `PARAMETER_REQUIREMENTS[key].is_derived` (mirror `semantic_intent_adapter.py:151-159` behavior):

- Return interactive/error with `derived_message` redirect — **never** write `autonomia`, `empuje_disponible`, etc. as loose `current_parameters` keys.
- Applies even when routing mis-fires — stops the G26 symptom at minimum.

---

## 4. Implementation slices (Req-1 … Req-6)

Execute **in order**. Each slice should leave the suite green.

### Req-1 — Explicit-none helper (`state_schema.py`)

- Add `restrictions_explicitly_none(restrictions: str | None) -> bool` with closed list §2.2.
- Unit tests: true for `"no"`, `"ninguna"`, `"sin restricciones"`; false for `""`, `None`, `"autonomia 15 min"`, ambiguous strings.

### Req-2 — Requirements declared predicate (`engineering_readiness.py`)

- Add module-level or shared helper `requirements_declared(project_state) -> bool` per §2.1–2.3 (may import helpers from `state_schema`).
- Update `_requirements_evidence.defined` to use it.
- **Do not** change `_derive_overall`, gap builders, or other subsystems.

### Req-3 — G26 write path

- Implement mid-session update of `current_parameters["restrictions"]` for the scenarios §3.1.
- Ensure save goes through `workspace_manager.save_state` + `ProjectState.model_copy` so `parsed_constraints` re-derives.
- Smallest routing change — document chosen entry point in implementation report.

### Req-4 — `is_derived` gate (`param_definition_session.py`)

- Block derived param writes in `apply_and_recalculate` (or single earlier choke point).
- Regression: attempt to apply `autonomia=15` → rejection, `current_parameters` unchanged.

### Req-5 — Tests (`tests/test_requirements_closure.py` — new)

Minimum tests (names indicative):

1. `test_requirements_pass_when_restrictions_explicitly_no` — `restrictions="no"`, `{}` parsed_constraints → `requirements.verdict == PASS` (other subsystems crafted PASS).
2. `test_requirements_incomplete_when_restrictions_absent` — key missing → INCOMPLETE.
3. `test_requirements_incomplete_when_restrictions_unparseable` — non-empty gibberish → INCOMPLETE.
4. `test_fixture2_shape_assembly_ready_after_req1_req2` — load/build state matching `1-324107ef7006` shape → `overall == ASSEMBLY_READY`.
5. `test_g26_restrictions_update_sets_parsed_constraints` — orchestrator/session path: constraint phrase → `restrictions` string + `parsed_constraints.autonomy_min`.
6. `test_g26_derived_autonomia_rejected` — `autonomia=15` via param session → not persisted.
7. `test_gap_requirements_unmet_autonomy_when_target_exceeds_sim` — `autonomy_min=15`, sim 5 min → HIGH gap, NOT ASSEMBLY READY (probe #3 negative arm).
8. `test_p2_propulsion_resolution_unchanged` — smoke: existing P2-1 test helper or single assertion that `resolve_operating_point` / propulsion evidence path untouched (no edits to `library.py` / OP resolver).

**Zero weakened tests.** Any assertion change in existing files must be disclosed in implementation report with rationale (same discipline as propeller IC).

### Req-6 — CLI probe (`scripts/cli_probe_requirements_closure.py`)

Deterministic probe against **Fixture 2** (`workspace/1-324107ef7006` or copy in `tmp_path` seeded from that shape):

| Step | Action | Pass criterion |
|---|---|---|
| 1 | Load Fixture-2-shaped project → `build_engineering_readiness` | 8/9 PASS pre-fix baseline documented OR post-fix: **overall ASSEMBLY_READY** with `restrictions="no"` |
| 2 | `estado` / project_status | `PROJECT STATUS: ASSEMBLY READY` |
| 3 | Update restrictions to achievable autonomy (≤ live `autonomy_min`) | `requirements` PASS, overall ASSEMBLY_READY |
| 4 | Update restrictions to unachievable autonomy (e.g. 15 min when sim ~5 min) | `GAP-REQUIREMENTS-UNMET:autonomy` visible, overall NOT ASSEMBLY READY |
| 5 | Attempt derived-param write (`autonomia=15` without restrictions update) | Rejected; `restrictions` unchanged |

Target: **5/5 PASS**. Real wizard turns where applicable; no state patches that bypass the write path under test.

---

## 5. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/schemas/state_schema.py` | Req-1; optional `_parse_constraints` FN-010 interaction note |
| `src/jarvis/core/engineering_readiness.py` | Req-2 only (`_requirements_evidence`) |
| `src/jarvis/core/param_definition_session.py` | Req-3/4 |
| `src/jarvis/core/orchestrator.py` | Req-3 **only if** routing requires it — smallest diff |
| `tests/test_requirements_closure.py` | Req-5 (new) |
| `scripts/cli_probe_requirements_closure.py` | Req-6 (new) |

**Must NOT change:**

- `library.py`, `resolve_operating_point`, `component_writers` propulsion OP bridge, `catalog_bind.py`
- `project_closure._bom_sku_resolved` (IC 3)
- Battery/propeller catalog assist, G27 parser, G24 DSE
- `docs/ENGINEERING_READINESS_VISION.md` (IC 3 policy doc sync)
- Version in `pyproject.toml`

---

## 6. Explicit non-goals (this IC)

- Battery catalog pick UX / `bind_battery_from_catalog` call sites (IC 2)
- G27 free-text Wh parsing (IC 2)
- Propeller `(SKU sin resolver)` display fix (IC 3)
- Family policy matrix ratification in vision doc (IC 3)
- New gap types, new subsystems, Conversation Engine
- Wiring `catalog_bound` into subsystem verdicts
- Auto-refresh calc/sim after requirements change (user may still `calcular` manually — unchanged)
- Version bump / checkpoint tag — Engineer call after review

---

## 7. Acceptance (Cursor review)

**PASS** if:

- Fixture-2-shaped project reaches **`ASSEMBLY READY`** with `restrictions="no"` and zero new gaps (Req-2 + probe step 2)
- Explicit-none does **not** add fake `parsed_constraints` entries
- G26 write path persists `restrictions` + re-derives `parsed_constraints`; derived `autonomia` write rejected
- Unachievable numeric constraint surfaces **GAP-REQUIREMENTS-UNMET** honestly (probe step 4)
- Full suite green; probe 5/5
- P2-1 / propulsion paths untouched (git diff confirms)
- No weakened tests without disclosure

**FAIL** if:

- `requirements PASS` achieved by inventing constraints or components
- Empty `restrictions` treated as PASS
- `parsed_constraints` polluted with sentinel floats for explicit-none
- Physics / OP resolver / catalog UX changed in this diff

---

## 8. Queue after IC 1

```text
IC 1 PASS + CLI probe 5/5
  ↓
Engineer optional checkpoint (e.g. checkpoint-requirements-closure)
  ↓
Cursor: IC 2 Battery Catalog UX + G27
  ↓
IC 3 Closure policy + propeller sku_resolved
```

---

**End of contract.**
