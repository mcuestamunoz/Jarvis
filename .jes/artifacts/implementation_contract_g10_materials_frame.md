# Implementation Contract — G10 Material Catalog / Frame Acquisition

**Project:** Jarvis  
**Date:** 2026-08-15  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — library-canonical material identity + frame acquisition + list-materials.  

**Closes:** G10 🟡 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)  

**Design authority (CLOSED ★1–★8):** [`.jes/artifacts/design_g10_materials_frame.md`](design_g10_materials_frame.md)  
**Investigation:** [`.jes/artifacts/investigation_g10_materials_frame.md`](investigation_g10_materials_frame.md)  
**Review of design:** [`.jes/artifacts/implementation_review_g10_materials_frame.md`](implementation_review_g10_materials_frame.md)  

**Checkpoint base:** tag **`checkpoint-g3`**  

**Workflow:** Claude implements + tests + report → Engineer forwards → **Cursor review** → **CLI probe** → commit/tag only if Engineer asks. **Do not commit or push unless asked.**

---

## 0. Why this cut

```text
CLI: plastico / PVC rejected in frame wizard; only "fibra de carbono 450g" worked
        +
Silent wrong mass: mutate prefers stale structure.material over declared frame
```

Design CLOSED: **O2 library-canonical** + force-frame + list-materials.  
This cut implements ★1–★8. No G8/G9/R3/Impl C.

```text
checkpoint-g3
        │
        ▼
G10 IMPLEMENTATION  ← you are here
        │
        ▼
Cursor review → CLI → checkpoint-g10
        │
        ▼
R3 design …
```

---

## 1. Locked decisions (do not re-open)

| ★ | Requirement |
|---|---|
| ★1 | Store library Spanish names in `components["frame"].properties["material"]` |
| ★2 (b) | One shared alias table (prefer `src/jarvis/domains/materials.py`) |
| ★3 | Force-frame FN-019 mirror when scoped wizard expects frame |
| ★4 | Expand frame keywords for all 8 library stems |
| ★5 | `get_frame_material` read-shim for legacy EN slugs |
| ★6 | `apply_material_mutation` must not use `structure.material` as SoT |
| ★7 (a) | Remove `madera` from aliases; no library JSON edit |
| ★8 | Deterministic list-materials → `list_materials()`, 0 LLM |

---

## 2. Out of scope (hard)

| Forbidden |
|---|
| G8 / R3 / R4 / G9 Continuity honesty |
| Catalog Impl C, battery/prop SKU UX, BOM |
| Adding materials to `library/materiales/_datos.json` |
| Frame SKU catalogs / `catalog_ref` on materials |
| Conversation Engine / Step D / dual-dispatch refactor |
| Opportunistic large refactors outside blast radius |
| Weakening tests to pass |
| Commit / push unless Engineer asks |

**Allowed optional:** stop writing `structure.material` on iterate apply if cheap; deleting the field entirely is **not** required for PASS.

---

## 3. Implementation requirements

### 3.1 Shared alias table (★1, ★2, ★7)

Create `src/jarvis/domains/materials.py` (preferred) containing:

- Alias → **library canonical Spanish name** for all 8 library materials + reasonable ES/EN variants (absorb current `_KNOWN_MATERIALS` minus `madera`, plus any missing stems needed for acquisition: `cf`, `alu`, `abs`, `nylon`, etc. as aliases to library names).
- Helper e.g. `resolve_material_alias(text) -> str | None` and/or the dict used by extractors.
- **No `madera`.**

Wire:

- `aerial.MATERIAL_MAP` / `extract_frame_properties` → use shared table (emit library names, not `carbon_fiber`).
- `iterate_domain._KNOWN_MATERIALS` → import/re-export shared table (or delete local dict and import).

Do not leave two divergent dicts.

### 3.2 Frame keywords (★4)

Expand frame `ComponentRule.keywords` in `aerial.py` so cold phrases mentioning library materials resolve to frame (e.g. `plastico`, `pvc`, `titanio`, `acero`, `kevlar`, `magnesio`, accented forms as needed). Keep existing structure keywords (`frame`, `chasis`, …).

### 3.3 Force-frame (★3)

In `orchestrator._handle_component_description`, immediately after the propellers FN-019 force block, add the same pattern for `"frame" in expected_keys` when all specs are `generic_component`. Reuse `infer_component_for_key(..., "frame")`. No second parser.

### 3.4 Legacy shim (★5)

In `get_frame_material`, if stored value is `carbon_fiber` / `aluminum` / `plastic` (and any other known legacy slug), return the library Spanish equivalent before callers use it. Document in docstring that stored canonical is now library Spanish.

### 3.5 Mutation SoT (★6)

In `mutation_engine.apply_material_mutation`, resolve `current_material` from `state["material"]` (canonical, already seeded by iterate via `get_frame_material`) **before** / **instead of** preferring `structure.material`.

Regression must fail on pre-fix behavior (investigation §5.2): after wizard sets carbon fiber and iterate changes to pvc, density ratio must be carbon→pvc, not aluminio→pvc.

### 3.6 List-materials (★8)

- Add narrow patterns in `intent_resolver` (or adjacent) for catalog-list queries about materials, e.g.:
  - `qué materiales` / `que materiales`
  - `materiales disponibles`
  - `catálogo de materiales` / `catalogo de materiales`
  - similar narrow variants — finalize without stealing normal iterate `"material"` variable selection
- Dispatch to a small orchestrator handler that formats `default_library.list_materials()` (name + density), **0 LLM**.
- Must win over analyze/LLM for those phrases (same discipline as other deterministic intents).

Precedence note: do not break existing `"material"` as iterate variable keyword for mutate flows. List phrases should be more specific than bare `"material"`.

---

## 4. Acceptance tests (required)

Create `tests/test_g10_materials_frame.py` (or split if clearer). Minimum:

| ID | Assert |
|---|---|
| T1 | For each of 8 library names: `"{name} 400g"` with `expected_keys=["frame"]` → frame saved; `get_material(stored)` succeeds |
| T2 | `"plastico 390g"` / `"pvc 390g"` / `"PVC 390g"` succeed in scoped frame wizard (no re-prompt loop) |
| T3 | Force-frame: phrase that lacks structure keywords but has material+mass still works when `expected_keys=["frame"]` |
| T4 | Dual-name regression: set frame via `set_frame_material(..., "fibra de carbono")` while leaving stale `structure.material="aluminio"`; apply mutate to `pvc`; assert mass factor uses ρ_carbon/ρ_pvc path (not aluminio) |
| T5 | Legacy shim: frame property `carbon_fiber` → `get_frame_material` returns `fibra de carbono` (or library-accepted name) |
| T6 | `madera` no longer resolves via alias table to a fake canonical |
| T7 | List-materials phrase → action/status ok, message contains all 8 names (or densities), RefuseLLM unused |
| T8 | Existing happy path `"fibra de carbono 450g"` still works; `aluminio 450g` still works |

Also run relevant existing suites touched (iterate material, FN-019 propellers, assisted acquisition) — no regressions.

---

## 5. CLI probe (Engineer, after Cursor PASS)

```text
# frame wizard / DEFINE_MISSING on frame
plastico 390g          → accept
pvc 400g               → accept
que materiales tenemos en el catalogo?  → deterministic list (no LLM invent)
# optional iterate after frame declared as fibra de carbono:
cambiar material a pvc → mass change coherent with carbon→pvc (not aluminio base)
```

---

## 6. Deliverables

| Artifact | Required |
|---|---|
| Code changes per §3 | Yes |
| `tests/test_g10_materials_frame.py` (or equiv.) | Yes |
| `.jes/artifacts/implementation_report_g10_materials_frame.md` | Yes |
| Update G10 status in `cli_findings_…` to Fixed (pending CLI) | Yes, in report or findings |
| Design/map updates if a new intent needs a C-xxx note | Optional, doc-only if evidence clear |
| Commit / tag | **No** unless Engineer asks |

### Report must include

```text
FILES CHANGED:
BEHAVIOR CHANGED:
TESTS ADDED/UPDATED:
TESTS EXECUTED:
★1–★8 COVERAGE: (checklist)
RISKS / FOLLOW-UPS: (G9 still out; madera not in library)
```

---

## 7. Pass criteria (Cursor review)

| # | Criterion |
|---|---|
| 1 | All 8 library materials declarable via frame wizard |
| 2 | Stored material is library Spanish; `get_material` accepts it |
| 3 | §5.2 dual-name regression test green |
| 4 | Force-frame present and tested |
| 5 | Legacy EN slug shim works |
| 6 | `madera` removed from aliases |
| 7 | List-materials 0 LLM |
| 8 | No G8/G9/Impl C / library JSON material adds |
| 9 | Targeted + related regression tests green |

**Grades:** PASS / PASS WITH NOTES / FAIL.

---

## 8. Suggested working order

```text
1. Read design CLOSED + investigation §5.2
2. Add domains/materials.py shared aliases (− madera)
3. Retarget aerial extract_frame_properties + keywords
4. Wire iterate_domain to shared table
5. Force-frame in orchestrator
6. get_frame_material shim
7. mutation_engine SoT fix + regression test first (red→green)
8. list-materials intent + handler
9. Full T1–T8 + related suites
10. Write implementation_report_g10_materials_frame.md
11. STOP — no commit
```

---

## 9. Handoff back to Engineer

```text
VERDICT: <PASS self-check>
REPORT: .jes/artifacts/implementation_report_g10_materials_frame.md
★ COVERAGE: 1–8 done / gaps
TESTS: <counts>
NEXT: Cursor review → CLI → checkpoint-g10
CODE: <file list>
```
