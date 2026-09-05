# Implementation Contract — Structure Foundations (claim copy)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · claim-copy slice **CLOSED**  
**Review:** [implementation_review_structure_foundations.md](implementation_review_structure_foundations.md)  
**Report:** [implementation_report_structure_foundations.md](implementation_report_structure_foundations.md)  
**Suite:** **2171**

**Type:** Claim-language — BOM + Continuity situation. **Not** catalog. **Not** layout params. **Not** CAD. **Not** Structure A reopen.

**Parents:**
- [investigation_report_structure_foundations.md](investigation_report_structure_foundations.md)
- [investigation_review_structure_foundations.md](investigation_review_structure_foundations.md) — **PASS WITH NOTES**
- [engineer_ratification_structure_foundations.md](engineer_ratification_structure_foundations.md)

**Baseline:** tag **`v0.3.6`** · claim hygiene + control parity in tree · suite **2164**

**Buy:** Claim/completeness **copy only** (primary = BOM; Continuity gate = defense-in-depth per review N1).

---

## 0. You

- Edit only files in §5.
- Do **not** change `_frame_completeness`, `classify_component`, `component_presence_tier`.
- Do **not** change `frame_class_compatibility_state`, `frame_size_blocks_structure_complete`, gap types/severity/blocks.
- Do **not** change `_derive_overall` / `_structure_evidence` / ASSEMBLY_READY eligibility.
- Do **not** add `CatalogRef` family `"frame"`, `library/frames/`, wheelbase/arm/clearance keys.
- Do **not** reopen CAD / FEA / “cabe” / class→thrust.
- Full suite green. Zero weakened tests.

---

## 1. Intent

When propeller \(D\) is known and frame class is **missing** or **incompatible** (LEVEL A):

- Architecture / ERF / next-step already behave correctly (Structure A).
- BOM must **not** look like a fully settled `✓ frame … (high)` with no caveat.
- Continuity must **not** say `Diseño validado en simulación (PASS)` if a live `GAP-FRAME-SIZE-MISSING` / `GAP-FRAME-PROP-SIZE` is present on `readiness` (even when `architecture_progress` is omitted).

When class is compatible or not required: BOM and “Diseño validado” paths unchanged (aside from existing margin/autonomy gates).

---

## 2. Locked behavior

### 2.1 BOM — `project_closure.format_bom_lines`

Extend `_bom_completeness_tail` (or sibling helper) so that for
`key == "frame"` in the **defined** bucket, when class screening is **not
closed**, the tail becomes:

**Missing class** (`frame_class_compatibility_state` → `"missing"`):

```text
(high — compatibilidad de clase nivel A pendiente)
```

**Incompatible** (`→ "class_incompatible"`):

```text
(high — clase incompatible nivel A)
```

(Use the entry’s actual `completeness` string in place of `high` if different.)

When state is `not_required` or `class_compatible`, frame tail stays plain
`({completeness})` — same as motors today.

**How to get class state (pick smallest diff):**

- Preferred: `format_bom_lines(bom, project_state=None)`. When `project_state`
  is provided, call existing `frame_class_compatibility_state(project_state)`.
- Update callers that have state: `orchestrator.build_startup_context`
  (`component_bom_lines`), `workspace/render_views.py`. Callers without state
  keep prior plain tails (backward compatible).

Do **not** put readiness/gap objects into BOM formatting if the pure class
state helper suffices.

**Unchanged:** `_bom_identity_suffix`, sensors/motors/FC tails (FC keeps control-parity identity suffix).

### 2.2 Continuity situation — `project_continuity.py`

Before the plain `elif sim_status == "pass":` → Diseño validado branch, and
after existing autonomy / `margin_claim_weak` guards, add:

```text
elif sim_status == "pass" and _frame_class_gap_live(readiness):
    situation = <locked string>
```

**Predicate `_frame_class_gap_live(readiness)`:** `True` when `readiness` is
not `None` and any gap has `gap_type` in
`{"GAP-FRAME-SIZE-MISSING", "GAP-FRAME-PROP-SIZE"}`.

**Locked situation string (verbatim, both gap types):**

```text
Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente.
```

When `readiness` is omitted: behavior unchanged (existing callers).

Next-step copy from `_frame_class_next_step` / Structure A: **unchanged**.

### 2.3 Out of this IC

- `_frame_completeness` formula  
- Architecture 4/4 / `frame_next_missing_*`  
- Frame catalog / layout params / CAD  
- General “PASS + any gap” Continuity rewrite  

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_project_closure_v1.py` (or BOM format tests) | Frame defined, D known, no class → BOM line contains `compatibilidad de clase nivel A pendiente`. Class incompatible → `clase incompatible nivel A`. Class compatible → plain `(high)` without those phrases. Motors line unchanged. |
| `tests/test_project_continuity.py` | `readiness` with `GAP-FRAME-SIZE-MISSING`, `sim` PASS, `architecture_progress=None` → situation is §2.2 locked string, **not** `Diseño validado`. Class-compatible / no frame gaps + PASS → still `Diseño validado` (unless margin/autonomy gates fire). |
| Regression | Existing Structure A / claim-hygiene Continuity tests stay green. |

---

## 4. Explicit non-goals

Catalog frames · layout params · CAD/FEA · changing Structure A screening ·
`_derive_overall` · control/claim-hygiene reopen beyond this narrow gate.

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/core/project_closure.py` | §2.1 |
| `src/jarvis/core/project_continuity.py` | §2.2 |
| `src/jarvis/core/orchestrator.py` | Pass `project_state` into `format_bom_lines` if needed |
| `src/jarvis/workspace/render_views.py` | Same, if needed |
| `tests/test_project_closure_v1.py` | BOM |
| `tests/test_project_continuity.py` | Continuity |

---

## 6. Done criteria

- §2.1–§2.2 locked strings  
- Mandatory tests + full suite green  
- No ERF / Structure A screening / catalog / layout edits  
- Implementation report lists files, tests, residual (N1: main `estado` path already arch-honest; catalog/layout still options)

---

## 7. After implementation

Cursor reviews. On PASS, Structure Foundations **claim-copy slice** closes.
Catalog / layout remain **options** for a later Engineer-named thread — not automatic.
