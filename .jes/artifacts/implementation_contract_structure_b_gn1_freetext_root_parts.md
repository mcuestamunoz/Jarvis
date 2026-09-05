# Implementation Contract — Structure B G-N1 Free-text Root+Parts

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code / Cursor  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · G-N1 **CLOSED** (suite **2229**)  
**Review:** [implementation_review_structure_b_gn1_freetext_root_parts.md](implementation_review_structure_b_gn1_freetext_root_parts.md)  
**Report:** [implementation_report_structure_b_gn1_freetext_root_parts.md](implementation_report_structure_b_gn1_freetext_root_parts.md)  
**Type:** Orchestrator wiring + multi-part extraction. **Not** MEASURE. **Not** PASS widen. **Not** new subsystem.

**Parents:**
- [implementation_review_structure_b_parts_graph.md](implementation_review_structure_b_parts_graph.md) — **G-N1** residual
- [implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md) — Fase 1 CLOSED (API existed; wizard unwired)
- [engineer_structure_block_preclose_audit.md](engineer_structure_block_preclose_audit.md)

**Baseline:** suite **2223**

**Buy:** One free-text frame message may declare **root + parts together**, e.g.  
`"fibra 450g, 4 brazos carbono, jaula titanio"`.

---

## 0. You

- Edit only files in §5.
- Do **not** add `frame_arm`/etc. to `BLOCK_TO_COMPONENTS`.
- Do **not** change `_structure_evidence` / `_derive_*` / `_frame_completeness`.
- Do **not** cross-check part `count` ↔ `motor_count` or `configuration` ↔ parts.
- Do **not** invent parts from bare numbers without a part-type word.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

```text
User (frame wizard / frame free-text):
  "fibra 450g, 4 brazos carbono, jaula titanio"
        ↓
  components["frame"]           ← mass/material/(size/config/wheelbase if present)
  components["frame_arm"]       ← parent_key=frame, count=4, material=…
  components["frame_cage"]      ← parent_key=frame, material=…
  BOM └ sub-lines under frame (existing N1 path)
```

Catalog-assist path unchanged. PASS unchanged.

---

## 2. Locked behavior

### 2.1 Multi-part extraction — `domains/aerial.py`

Add **`extract_all_frame_part_properties(normalized) -> list[tuple[str, dict[str, PropertyValue]]]`**:

- Scan for **all** locked part types present (`frame_arm` / `frame_plate` / `frame_cage` / `frame_standoff`), not only the longest single match.
- At most **one entry per locked key** (longest alias wins per key).
- Scope `count` / `material` to the **clause** containing that part alias. Clauses split on `,` / `;` / ` y ` / ` and ` (case-insensitive). Prevents root `"fibra 450g"` material from attaching to `"jaula titanio"`.
- No part-type alias → empty list (never fabricate from a bare `"4"`).
- Keep **`extract_frame_part_properties`** as a thin wrapper: first element of `extract_all_…` or `None` (existing unit tests keep working).

### 2.2 Apply path — `orchestrator._apply_inferred_component_spec`

When applying `suggested_key == "frame"`:

1. Existing `set_frame_material(mass, material, size)` unchanged in role.
2. **Also** merge onto the frame root any already-extracted `configuration` / `wheelbase_mm` from `spec.properties` (declared-only; closes free-text gap where extract ran but writer dropped them).
3. Given the **raw user text** for this turn, run `extract_all_frame_part_properties` and `upsert_frame_part` for each hit (`parent_key="frame"`).
4. Saved message may briefly name upserted parts (e.g. `+ arm×4, cage`) — optional, keep short; must not claim fit/strength.

Pass `source_text=user_input` into apply (or equivalent) from `_handle_component_description`’s processable loop — **only** for the frame branch.

### 2.3 When this fires

- Frame wizard (`expected_keys` contains / is `frame`) **and** free-text path that already applies an inferred frame spec.
- Parts-only follow-up on an existing frame (e.g. frame already high, user later says `"4 brazos carbono"`): if that text is handled as a frame apply/re-apply, parts upsert; if it falls through as generic/low without frame apply, **do not** invent a new top-level routing subsystem — prefer: when `expected_keys[0]=="frame"` OR persisted frame exists and inferred/forced key is frame, still run part upsert on that text even if root props are empty (upsert parts only; do not wipe root).

Minimal rule that satisfies Engineer approach:

```text
IF this turn applies a frame ComponentSpec (force-frame or suggested_key frame):
   merge root props + upsert all extracted parts from raw text
ELIF expected_keys and expected_keys[0]=="frame" and extract_all returns non-empty
     and a frame component already exists:
   upsert parts only (do not create empty frame stub)
ELSE:
   no part writes
```

### 2.4 Unchanged

- BOM N1 filter + `└` rendering  
- Catalog bind / assist upsert  
- Structure PASS / completeness  
- Forbidden claim sentences from Fase 1 IC  

---

## 3. Tests (mandatory)

| Area | What |
|---|---|
| `extract_all_…` | `"fibra 450g, 4 brazos carbono, jaula titanio"` → arm count+material + cage material; root extract still mass+material |
| Clause isolation | Cage clause does not inherit root `fibra` |
| Single-part wrapper | Existing `extract_frame_part_properties` tests still pass |
| Bare `"4"` / `"4 motores"` | No frame parts |
| Orchestrator / writer | Create project → describe frame with root+parts message → `frame_arm`/`frame_cage` present with `parent_key`; BOM has `└` not peers |
| Parts-only after frame | Frame already set → `"standoffs aluminio"` in frame context upserts `frame_standoff` |
| PASS regression | With free-text children, structure verdict identical twin without (reuse pattern from Fase 1 test) |
| Full suite | Green |

---

## 4. Explicit non-goals

- MEASURE / CAD  
- Wizard UX copy redesign  
- `compressed-x` alias (G-N3) unless free  
- Armattan seed counts (G-N2)  
- Version bump  

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/domains/aerial.py` | `extract_all_…` + wrapper |
| `src/jarvis/core/orchestrator.py` | §2.2–2.3 wire |
| `src/jarvis/core/component_writers.py` | optional small merge helper for config/wheelbase; docstring update |
| `tests/test_frame_parts_graph_v1.py` and/or `tests/test_frame_parts_freetext_gn1.py` | §3 |

---

## 6. Done criteria

- Root+parts single message works end-to-end  
- Multi-part + clause isolation  
- PASS/BOM N1 intact  
- Full suite green  
- Implementation report short  

---

## 7. After implementation

Cursor reviews against this IC. On PASS → G-N1 closed; Structure block may ★-close with G-N1 absorbed.
