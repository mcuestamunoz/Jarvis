# Implementation Contract — Geometry assembly espacial B1 (`mounted_on` relation-only)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY FOR IMPLEMENTATION — Engineer ★ Buy B1 (`escribe IC`)  
**Parents:**
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- [investigation_contract_geometry_assembly_espacial_b1.md](investigation_contract_geometry_assembly_espacial_b1.md)
- [investigation_report_geometry_assembly_espacial_b1.md](investigation_report_geometry_assembly_espacial_b1.md)
- [investigation_review_geometry_assembly_espacial_b1.md](investigation_review_geometry_assembly_espacial_b1.md) — **PASS WITH NOTES** (N1–N5)
- Glyphs CLOSED @ **2344** · Catalog hygiene CLOSED @ **2350**

**Type:** First **assembly espacial** slice — declared mount **relation** only.  
**Not** numeric pose. **Not** fit/clearance. **Not** Board edges (B2). **Not** layout-as-truth.

**Baseline:** package **`0.3.8`** · suite **2350**

**Output:** `.jes/artifacts/implementation_report_geometry_assembly_espacial_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — `ComponentSpec.mounted_on: str \| None` relation-only |
| 2 | Ladder | **Assembly espacial** — “declarado montado en X”; ≠ ensamblado verificado / cabe |
| 3 | **N1** | **Do not** reuse or overload `parent_key` — new orthogonal field |
| 4 | **N3** | Bare `str \| None` (default `None`); always treated as **declared** — no new PropertyValue wrapper |
| 5 | **N4** | Writer-time **reject** if target key missing from `components` (no dangling silent store) |
| 6 | **N2** | Board: projector appends text field `"montado en"` when set — **not** via `_fields()` alone |
| 7 | Inference | **Never** from Board x/y, localStorage, BOM co-membership, or cardinality-of-one |
| 8 | B1+ / B2 | **Out** — no mm/orientation; no edge drawing |
| 9 | Version | **No** bump |

---

## 1. You

- Do **not** add pose / orientation / offset / face / mount-hole fields.
- Do **not** change `parent_key` writers, BOM peer-exclusion rules, or `clear_frame_part_children` semantics (except ensuring they still ignore `mounted_on`).
- Do **not** read Board layout / `localStorage` as physical truth.
- Do **not** draw canvas edges between cards.
- Do **not** invent catalog mount data; do **not** reopen ESC/thrust hygiene or Here3/Pixhawk.
- Do **not** bump package version.
- Full suite green. Zero weakened tests.
- Write `implementation_report_geometry_assembly_espacial_b1.md` when done.

---

## 2. Intent

```text
ComponentSpec.mounted_on: str | None = None
        ↓
writer sets / clears (declared only; target must exist)
        ↓
project_spatial_nodes → fields += { label: "montado en", value: <target key> }
        ↓
Board card text shows the relation (no new geometry math)
```

Product sentence:

> “Sé qué es, qué volumen declarado ocupa, y a qué se declara montado.”

---

## 3. Locked behavior

### 3.1 Schema — `ComponentSpec`

In `src/jarvis/schemas/action_schema.py`, add (additive, default `None`):

```text
mounted_on: str | None = None
```

Docstring must state:

- Orthogonal to `parent_key` (BOM topology of frame parts).
- Names another key in `design_properties.components` (including `frame_plate_1`, `frame_arm`, etc.).
- Always a **declared** relation — never inferred.
- No pose / fit semantics.

Existing projects deserialize unchanged (`extra="ignore"` already; new field defaults `None`).

### 3.2 Writer — single set/clear path

Add a small canonical writer (prefer `component_writers.py`), e.g. `set_component_mounted_on(project_state, component_key: str, target_key: str | None) -> ProjectState`:

| Case | Behavior |
|---|---|
| `target_key is None` | Clear `mounted_on` on the named component (idempotent if already None). |
| `target_key` set | Require `component_key` and `target_key` both exist in `components`. Require `component_key != target_key`. On success, set `mounted_on=target_key` on that spec. |
| Missing key / self-ref | **Raise** `ValueError` (or project-equivalent) — do not store dangling refs. |

Do **not** auto-set `mounted_on` from Continuity/orchestrator heuristics in this IC. Optional: a thin CLI/orchestrator path that calls the writer when the user explicitly declares a mount is **allowed** if tiny; otherwise tests may call the writer directly and report Continuity UX as deferred (name it in the report).

**Forbidden:** changing `parent_key` when setting `mounted_on`; inferring targets; reading pixel layout.

### 3.3 Board projector (N2)

In `src/jarvis/workspace/spatial_board.py` → `_fields` (or the emit path that builds `fields`):

- After existing property/SKU fields, if `spec.mounted_on` is not `None`, append:

```text
{"label": "montado en", "value": "<mounted_on key>"}
```

- If the target key is **absent** from `components` at project time (stale after delete), still show the stored string **or** show an honest absence value — prefer: show the key as stored and do **not** invent a replacement; stale targets should be rare if writer validates at set time. Optional hardening: if target missing at project time, value `"<key> (ausente)"` — allowed, not required.
- **No** change to glyphs, lanes, `kind`, or card `x`/`y` semantics.
- **No** UI React changes required if the generic `fields` renderer already displays arbitrary labels (confirm; if SpatialCard hardcodes labels, add the minimal display path only).

### 3.4 Non-interference

Confirm / regression-test:

- Specs with only `parent_key="frame"` behave as today (BOM / Board / clear children).
- Specs with `mounted_on` set are **not** treated as frame parts.
- `clear_frame_part_children` still only removes `parent_key == "frame"`.

### 3.5 Continuity / CLI copy (optional this IC)

If no user-facing set path ships, state that explicitly in the report (writer + Board + tests only). Do **not** invent “ensamblado” / “cabe” copy. If a message is added, it must say **declarado montado en**, never verified assembly.

---

## 4. Tests (required)

1. **Schema:** `ComponentSpec` defaults `mounted_on is None`; round-trip JSON preserves a set value.
2. **Writer set:** FC (or any) `mounted_on="frame_plate_1"` when both keys exist → persisted on spec.
3. **Writer reject:** missing target → error; self-mount → error.
4. **Writer clear:** `target_key=None` clears field.
5. **Board:** projector `fields` include `montado en` / target when set; omit when None.
6. **Non-regression:** frame part with `parent_key="frame"` still `kind: "part"` / BOM subline behavior unchanged; motor with `mounted_on` still top-level component (not frame child).

Run full suite; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | `mounted_on` field + docstring |
| `src/jarvis/core/component_writers.py` | `set_component_mounted_on` (or equivalent) |
| `src/jarvis/workspace/spatial_board.py` | append Board field (N2) |
| `tests/…` | §4 coverage |
| `.jes/artifacts/implementation_report_geometry_assembly_espacial_b1.md` | write |

**Optional (only if tiny explicit UX):** one orchestrator/CLI call site that invokes the writer on clear user intent.

**Do not change:** `parent_key` semantics · glyph math · `ui/**` unless required for fields display · catalog seeds · fit/CAD · package version.

---

## 6. Explicit non-goals

Numeric pose / orientation · fit / clearance / intersection · Board edge visualization (B2) · layout-as-SoT · inferring mounts · overloading `parent_key` · catalog mount patterns · Continuity redesign · ESC/thrust reopen · Here3/Pixhawk · HD-004 · System Optimization · version bump · weakened tests

---

## 7. Done criteria

- [ ] `mounted_on` on `ComponentSpec`, default `None`, orthogonal to `parent_key`.
- [ ] Writer set/clear with target-existence + no self-ref validation.
- [ ] Board shows `"montado en"` text when set; no glyph/lane change.
- [ ] Frame `parent_key` paths unchanged.
- [ ] Tests §4 green; full suite green; count reported.
- [ ] Implementation report written (note Continuity UX deferred if so).
- [ ] Cursor review PASS before Engineer close.

---

## 8. Stop conditions

Stop and ask before: adding pose fields, drawing edges, inferring mounts, changing `parent_key` consumers, treating Board layout as physical, or bumping version.
