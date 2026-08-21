# Implementation Contract — Impl D Create → BOM / SKU BOM

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Extend the existing BOM projection so it **consumes SKU identity** (`catalog_ref`) — honest resolved/unresolved status + quantity — without a parallel BOM authority and without Continuity ranking changes.

**Investigation:** [`.jes/artifacts/investigation_report_impl_d_create_bom_sku.md`](investigation_report_impl_d_create_bom_sku.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_impl_d_create_bom_sku.md`](investigation_review_impl_d_create_bom_sku.md) — **PASS WITH NOTES**  
**Checkpoint base:** tag **`checkpoint-impl-c`** · commit `c99fec6`

**Workflow:** Claude implements **Slices D1 → D2 → D3 → D4 (conditional) → D5 deferred to Cursor** + tests + report → Engineer → Cursor review → CLI probe → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked — do not reopen in implementation)

| ★ | Decision |
|---|---|
| **★1** | **RATIFIED — Option A.** Extend `build_component_bom` entries with `catalog_ref`, `sku_resolved`, `quantity`. **No** parallel `build_sku_bom`. |
| **★2** | **RATIFIED — motors + battery** for live SKU resolution. Schema is **family-agnostic** (one entry shape for all keys). Propeller/ESC/frame/FC/sensors: declared-only (`catalog_ref=None`, `sku_resolved=False`). |
| **★3** | **RATIFIED — Create-handoff (sense B) deferred.** No Continuity CTA / ranking / `next_useful_step` changes in this IC. |
| **★4** | **RATIFIED — no new gap type.** Do **not** add `GAP-BOM-SKU-UNRESOLVED`. Reuse G9-A `GAP-MOTOR-CATALOG-UNRESOLVED` as the actionable catalog signal. |
| **★5** | **RATIFIED — leave `catalog_bound` disconnected** from `_derive_subsystem_verdict` / overall ASSEMBLY READY. Do not wire ERF verdict semantics in this IC. |
| **★6** | **CONDITIONAL — include Slice D4 only if presentation-local.** Decouple CLI `estado` BOM section from `continuity["evidence"]` truthiness. **Forbidden under ★6:** Continuity ranking, `next_useful_step`, G9-A, Conversation Engine, evidence-block rewrite. If D4 cannot stay local → **STOP**, skip D4, report; track as separate debt. |

**Additional locks:**

- **Do not modify** `project_continuity.py` (★3).
- **Do not modify** G9-A / `resolve_motor_catalog_surface` / catalog gap types (★4).
- **Do not modify** ERF verdict derivation / `_bom_evidence` consumption of `catalog_bound` (★5).
- **Do not modify** `catalog_bind.py` / G5 invalidate order (frankenstein is a **display honesty** problem; do not “fix” invalidate by clearing `.name`).
- **Do not modify** G24–G27, Phase 2 physics, H5 ESC catalog, Conversation Engine, Step D.
- **Do not invent** SKUs, quantities, or ESC count (ESC `quantity` stays `None`).
- **Keep field name `name`** on BOM entries — do **not** rename to `display_name` (additive fields only).
- **Prefer** `default_library.has_motor` / `has_battery` for Scenario C re-check — **no** second catalog reader.

**Architecture constraint (strict):**

> Implement the **minimum change** required to satisfy the ratified ★ decisions. BOM remains a **pure projection** of `ProjectState`. Do **not** reinterpret architecture. If a contradiction with investigation/★ locks appears → **STOP** and report; do not silently expand scope.

---

## 1. Problem / intent

Today `build_component_bom` never reads `catalog_ref` and never derives quantity. Bound SKUs and freeform names are indistinguishable. After G5 divergence, `.name` can still look like a SKU while `catalog_ref is None` (Scenario D / frankenstein).

**Target (v1):**

```text
ProjectState (ComponentSpec.catalog_ref + params.motor_count)
        ↓
build_component_bom  →  entries with catalog_ref / sku_resolved / quantity
        ↓
format_bom_lines     →  [sku] only when resolved; qty=N when known
        ↓
CLI estado + views/sistema.md   (same authority, no drift)
```

**Exit criterion (Design §6):** *Create/BOM consumes SKU identity* — satisfied by data + formatting (+ D4 observability if ★6 gates pass). Create Continuity handoff remains deferred (★3).

---

## 2. Slice D1 — BOM entry schema (`project_closure.py`)

### 2.1 Additive fields on every `_entry(...)` dict

Keep existing keys: `key`, `name`, `completeness`, `missing_fields`, `component_type`.

Add:

| Field | Type | Rule |
|---|---|---|
| `catalog_ref` | `dict \| None` | If `spec.catalog_ref` is set → `{"family": ..., "sku": ...}` (plain dict; `model_dump()` if needed). Else `None`. |
| `sku_resolved` | `bool` | See §2.2 — **never** inferred from `.name` shape. |
| `quantity` | `int \| None` | See §2.3. |

Bucket lists (`defined` / `incomplete` / `missing` / `declarative`) and ERF gap functions that only read bucket membership **must remain behavior-compatible**.

### 2.2 `sku_resolved` computation (non-negotiable)

```text
if catalog_ref is None:
    sku_resolved = False
elif family == "motor":
    sku_resolved = default_library.has_motor(sku)
elif family == "battery":
    sku_resolved = default_library.has_battery(sku)
else:
    sku_resolved = False   # no v1 resolve path for other families
```

**Hard rule:** frankenstein (`.name` looks like SKU, `catalog_ref is None`) → `sku_resolved=False`. Never `looks_like_sku(name)`.

### 2.3 `quantity` derivation (v1)

| Key | Quantity |
|---|---|
| `motors` | `current_parameters["motor_count"]` if set; else `properties["motor_count"].value` if present; else `None` |
| `propellers` | same as motors’ resolved motor_count (documented **convention**, not measured fact) |
| `esc` | `None` (honest unknown — 4-in-1 vs per-motor not represented) |
| `battery`, `frame`, `flight_controller`, `sensors` | `1` |
| other keys | `1` if singleton-style; prefer `1` over inventing fleet math |

Do not invent ESC quantity.

### 2.4 Helpers

Prefer small private helpers in `project_closure.py` (e.g. `_bom_catalog_ref_dict`, `_bom_sku_resolved`, `_bom_quantity`) — no new module, no new subsystem.

### 2.5 Acceptance (D1)

- Bound motor in library → `sku_resolved=True`, `catalog_ref` populated, `quantity` matches `motor_count`.
- Unbound freeform → `catalog_ref=None`, `sku_resolved=False`.
- Frankenstein (bind then G5 diverge / clear `catalog_ref` only) → `sku_resolved=False` even if `.name` still equals old SKU string.
- Bound motor whose SKU was removed from library (Scenario C) → `catalog_ref` present, `sku_resolved=False`.

---

## 3. Slice D2 — `format_bom_lines` (+ automatic surfacing)

### 3.1 Formatting rules

Extend `format_bom_lines` only (call sites already pass lists through):

- When `sku_resolved` and `catalog_ref.sku`: include `[sku]` in the line (same visual language as Impl C `_build_label_components`).
- When `quantity is not None`: append `qty=N`.
- When **not** `sku_resolved`: **do not** emit `[sku]` — even if `name` looks like a catalog id (Scenario D honesty).
- Scenario C (`catalog_ref` set, unresolved): do **not** claim resolved; optional short marker `sin resolver` / omit brackets — pick one consistent form; do not invent a second SKU authority.

Example shapes (illustrative, not byte-locked):

```text
✓ motors: hobbywing_xrotor_2207_2450 [hobbywing_xrotor_2207_2450] qty=6 (high)
✓ motors: 4x 2306 freeform qty=4 (high)          # unbound; no [sku]
✓ motors: hobbywing_xrotor_2207_2450 qty=6 (high) # frankenstein; no [sku]
```

### 3.2 Surfacing

- `orchestrator.build_startup_context` / `render_views.render_sistema` — **no call-site changes required** if they already use `build_component_bom` + `format_bom_lines`.
- D4 (below) is the only intentional CLI presentation change.

### 3.3 Acceptance (D2)

- Unbound, no motor_count, no catalog: formatting stays equivalent to today (no `[sku]`, no invented qty).
- Bound SKU: line shows `[sku]` + `qty` when quantity known.
- Frankenstein: no `[sku]` bracket.

---

## 4. Slice D3 — Tests + CLI probe

### 4.1 New focused test file

`tests/test_impl_d_sku_bom.py` (or equivalent name) covering at least:

1. Bound motor → `sku_resolved=True`, `catalog_ref`, quantity.
2. Unbound freeform → `sku_resolved=False`, `catalog_ref=None`.
3. Frankenstein (catalog_ref cleared, name retained) → `sku_resolved=False`; `format_bom_lines` has no `[sku]` for that entry.
4. Architecture-complete + bound motor → existing BOM bucket / ERF BOM gap behavior unchanged for missing/incomplete (no new gap type; no verdict wiring).
5. Regression: `GAP-BOM-MISSING-*` / `GAP-BOM-INCOMPLETE-*` still driven only by missing/incomplete buckets.
6. Battery with `catalog_ref` via `bind_battery_from_catalog` (test path) → same entry shape as motors (`sku_resolved` via `has_battery`).

Reuse existing catalog bind / G5 divergence fixtures where possible (`test_catalog_bind_v1.py` patterns).

### 4.2 Existing suites — must stay green without weakening

- `tests/test_project_closure_v1.py`
- `tests/test_fn020_completeness_coherence.py`
- `tests/test_project_coherence.py`
- `tests/test_erf2_architecture.py`
- `tests/test_engineering_readiness_continuity.py`

Update assertions **only** if they pin exact `format_bom_lines` strings and D2 legitimately adds `qty=` / `[sku]`. Prefer additive expects over deleting coverage.

### 4.3 CLI probe

`scripts/cli_probe_impl_d_sku_bom.py` — scripted project: bind motor → assert BOM lines / estado path shows resolved SKU + qty; frankenstein path shows no false `[sku]`. Follow Impl C probe style (deterministic, no LLM required for core asserts).

### 4.4 Acceptance (D3)

All new tests pass; listed regression files green; probe documents PASS/FAIL clearly in implementation report.

---

## 5. Slice D4 — ★6 CLI suppression fix (CONDITIONAL)

### 5.1 Allowed change (presentation-only)

File: `src/jarvis/adapters/cli/main.py` — inside `render_startup_context` (or equivalent).

**Before:**

```python
if bom_lines and not continuity.get("evidence"):
```

**After (required shape):**

```python
if bom_lines:
```

Show "Componentes / gaps:" whenever `bom_lines` is non-empty, **independent** of Continuity evidence.

### 5.2 Explicitly out of D4

| Forbidden | Why |
|---|---|
| Edit `project_continuity.py` | ★3 / Continuity semantics |
| Change Continuity ranking / `next_useful_step` | ★3 |
| Fold BOM into Continuity `evidence` list | reopens ranking/copy |
| Change requirements-lines gate (`req_lines and not continuity.get("evidence")`) | sibling debt — **out of Impl D** unless Engineer expands ★6 in writing |
| Touch G9-A / ERF verdict | ★4 / ★5 |

### 5.3 STOP condition

If implementing D4 appears to require Continuity or ranking changes → **do not implement D4**; document in report as deferred debt; ship D1–D3 only.

### 5.4 Acceptance (D4, if shipped)

Fixture/project with Continuity evidence present (e.g. energy-model honesty note) **and** non-empty BOM lines → `estado` / `render_startup_context` still prints "Componentes / gaps:" including SKU-aware lines when D1–D2 apply.

---

## 6. Slice D5 — Docs / System Map

**Cursor later** (not Claude’s implement slice unless Engineer asks): `ARCHITECTURE.md` / `system_map` edges for SKU-aware BOM projection. Do not block code review on D5.

---

## 7. Forbidden (summary)

- Parallel `build_sku_bom` / second BOM authority  
- `GAP-BOM-SKU-UNRESOLVED` or any new BOM gap type  
- Wiring `catalog_bound` into verdicts  
- Continuity Create-handoff / ranking / CTA  
- Clearing or rewriting `.name` on G5 invalidate “to fix frankenstein”  
- Inventing ESC quantity or SKUs  
- Weakening tests to pass  
- Conversation Engine / Step D / Phase 2 / H5 / G24–G27 fixes  

---

## 8. Implementation report (required)

`.jes/artifacts/implementation_report_impl_d_create_bom_sku.md` must include:

1. Files changed  
2. Behavior changed (and explicitly what did **not** change)  
3. ★1–★6 how implemented / D4 shipped or STOP’d  
4. Tests added + commands run + results  
5. CLI probe result  
6. Remaining risks / deferred (Create-handoff, requirements-lines gate, catalog_bound verdict)  

---

## 9. Exit criterion

Impl D is complete when:

1. D1–D3 done and green.  
2. D4 either shipped under §5 constraints **or** explicitly deferred with STOP rationale.  
3. Scenario D cannot present as resolved `[sku]` in `format_bom_lines`.  
4. No new gap type; no Continuity ranking change; no ERF verdict wiring.  
5. Cursor implementation review PASS (or PASS WITH NOTES).  
6. Engineer may then checkpoint (`checkpoint-impl-d`) when ready.

---

## 10. Queue after implementation

```text
Claude: D1→D2→D3→(D4?) + report
        ↓
Cursor: implementation review
        ↓
Engineer: CLI walk / checkpoint-impl-d
        ↓
Future IC: Create-handoff (★3) · optional requirements-lines gate · optional catalog_bound verdict
```

---

**End of contract.**
