# Design — G10 Material Catalog / Frame Acquisition

**Status: CLOSED ★1–★8** (Engineer lock 2026-08-15 — Cursor recommendations accepted as-is)

**Type:** Design authority for G10 implementation.  
**Companion:** [investigation_g10_materials_frame.md](investigation_g10_materials_frame.md)  
**Review:** [implementation_review_g10_materials_frame.md](implementation_review_g10_materials_frame.md) — PASS WITH NOTES  
**IC:** [implementation_contract_g10_materials_frame.md](implementation_contract_g10_materials_frame.md)  
**Checkpoint base:** `checkpoint-g3` (`a3b72b8`)

---

## 0. Locked option

**O2 — Library-canonical** + force-frame (O1) + list-materials (O4).

Store library Spanish names in `components["frame"].properties["material"]`.  
Shared alias table → library names. Force-frame FN-019 mirror. Keywords expanded.  
Legacy slug read-shim. Mutation stops reading `structure.material` as SoT.  
Remove ghost `madera`. Deterministic list-materials 0-LLM.

Rejected: O1-only (keeps EN slugs), O3 (JSON slugs), O4 without force-frame.

---

## 1. ★ Decisions — LOCKED

| ★ | Lock |
|---|---|
| **★1** | Canonical = library Spanish name in `components["frame"].properties["material"]` |
| **★2 (b)** | Single shared alias module (`domains/materials.py` preferred) — aerial + iterate_domain import it |
| **★3** | Force-frame when `expected_keys` includes frame and inference is all-generic (FN-019 mirror) |
| **★4** | Expand frame keywords for all 8 library material stems |
| **★5** | `get_frame_material` read-time shim: `carbon_fiber`/`aluminum`/`plastic` → library names |
| **★6** | `apply_material_mutation` must not prefer `structure.material` as SoT; field deletion optional |
| **★7 (a)** | Remove `madera` from aliases; no library JSON add |
| **★8** | Deterministic list-materials intent → `list_materials()`, 0 LLM |

---

## 2. Rationale (summary)

Investigation §5 proved three vocabularies + silent wrong mass when mutate reads stale
`structure.material`. Library Spanish is already what create_project / iterate mutation use;
English `MATERIAL_MAP` slugs were the outlier. O2 removes that boundary. Force-frame + keywords
are complementary. List-materials closes the LLM fallback for catalog queries.

---

## 3. Blast radius (normative for IC)

| File | Change |
|---|---|
| `src/jarvis/domains/materials.py` (new) | Shared alias table ★2 |
| `src/jarvis/domains/aerial.py` | Shared aliases; keywords ★4; → library names ★1 |
| `src/jarvis/core/iterate_domain.py` | Import shared; drop `madera` ★7 |
| `src/jarvis/core/orchestrator.py` | Force-frame ★3; list-materials ★8 |
| `src/jarvis/core/mutation_engine.py` | Canonical SoT ★6 |
| `src/jarvis/utils/design_utils.py` | Legacy shim ★5 |
| `src/jarvis/core/intent_resolver.py` | List-materials patterns ★8 |
| `library/materiales/_datos.json` | **Not touched** |

### Required tests

1. Acquisition coverage — all 8 library materials via frame wizard → `get_material()` accepts.  
2. Dual-name regression — investigation §5.2; density ratio uses declared frame material.  
3. `madera` no longer a known alias / no ghost hard path.  
4. List-materials — deterministic, 0 LLM, matches `list_materials()`.

---

## 4. Out of scope

G8 / R3 / R4 / G9 · Impl C · frame SKUs · Conversation Engine · new library materials · dual-dispatch.

---

## 5. Catalog v1 / Impl C

**Copy later:** one alias table → library identity; scoped wizard force-*.  
**Do not generalize:** materials stay density-only (no `catalog_ref`).

---

## Decision log

| Date | Event |
|---|---|
| 2026-08-15 | Investigation + Design OPEN (Claude) |
| 2026-08-15 | Cursor review PASS WITH NOTES |
| 2026-08-15 | Engineer ★1–★8 LOCKED (as Cursor recommended, incl. ★8) |
