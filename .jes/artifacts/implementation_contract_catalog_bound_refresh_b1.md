# Implementation Contract — Refresh catalog-bound component from seed B1

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY FOR IMPLEMENTATION — pending Engineer ★ Buy (investigation lean **B1**)  
**Parents:**
- [investigation_contract_catalog_bound_property_freshness_b1.md](investigation_contract_catalog_bound_property_freshness_b1.md)
- [investigation_report_catalog_bound_property_freshness_b1.md](investigation_report_catalog_bound_property_freshness_b1.md) — lean **B1 generic refresh**
- [investigation_review_catalog_bound_property_freshness_b1.md](investigation_review_catalog_bound_property_freshness_b1.md) — **PASS WITH NOTES**
- ESC mass hygiene B1 CLOSED (seed 15; N4 stale projects)
- Idle rebind B3 CLOSED (no ESC)

**Type:** Thin writer + Continuity IDLE phrase to **re-project** catalog physicals from the **current** seed via existing `bind_*_from_catalog(..., base=spec)`.  
**Not** ESC catalog picker. **Not** auto-refresh on Board load. **Not** Fase 2 geometry / Fase 3 mounts. **Not** fit/pose. **Not** FC/Here3 identity.

**Baseline:** package **`0.3.8`** · suite **2385**

**Output:** `.jes/artifacts/implementation_report_catalog_bound_refresh_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — refresh-from-`catalog_ref`, **all five** bind families |
| 2 | Primitive | Call existing `bind_{motor,battery,propeller,esc,frame}_from_catalog(sku, base=spec)` only |
| 3 | Preserve | `mounted_on`, `name`, `parent_key`, and any non-overwritten fields via `base=` merge |
| 4 | Continuity | IDLE deterministic phrase → writer; **no** LLM; **no** picker |
| 5 | No catalog_ref | Honest error — nothing to refresh |
| 6 | Board load | **No** silent refresh |
| 7 | Free-text ESC walk | **Out** — do not “fix” via `set_control_component` |
| 8 | Version | **No** bump |

---

## 1. You

- Do **not** invent a sixth binder or change seed values in this IC.
- Do **not** add ESC to idle **rebind/picker** B3 (different Buy).
- Do **not** auto-refresh on projector / Board read / save.
- Do **not** touch FC dimension tables, Here3, fit, pose, or plate footprints.
- Do **not** bump package version.
- Full suite green. Zero weakened tests.
- Write the implementation report when done.

---

## 2. Intent

```text
IDLE + active project:
  "actualiza el esc desde catálogo" / "refresca el esc"
  (same for motor(es), batería, hélice(s), frame/chasis)
        ↓
  parse → component_key (esc, motors, battery, propellers, frame)
        ↓
  refresh_component_from_catalog(state, key)
        ↓
  bind_*(sku, base=existing_spec) → save
        ↓
  "Actualizado desde catálogo (sku): mass_g 26 → 15 …"
```

Product sentence:

> “Puedo pedir que un componente ya vinculado al catálogo vuelva a tomar los números actuales del seed — sin perder el montaje declarado.”

---

## 3. Locked behavior

### 3.1 Writer (new)

Prefer `src/jarvis/core/component_writers.py`:

```text
refresh_component_from_catalog(project_state, component_key: str) -> ProjectState
```

Rules:

1. Load `spec = components[component_key]`; if missing → `ValueError` honest Spanish.  
2. If `spec.catalog_ref is None` → `ValueError`: not catalog-bound; nothing to refresh.  
3. Dispatch on `spec.catalog_ref.family` (`Literal`: motor/battery/propeller/esc/frame) → matching `bind_*_from_catalog`.  
4. Call `binder(spec.catalog_ref.sku, base=spec)`.  
5. Write result back at the **same** `component_key` (note: key `motors` / family `"motor"`).  
6. For **frame**: use the existing bind path that the codebase already uses for catalog frames; do **not** clear frame children unless an existing bind path already does (prefer preserve; if `bind_frame_from_catalog` alone is insufficient for a live frame root, stop and ask — do not invent Structure reopen).  
7. Return new `ProjectState` (immutable style consistent with other writers).

Optional helper: return or compute a small before/after dict of changed property values for Continuity copy (mass_g, etc.).

### 3.2 Continuity assist (new thin module or extend assist)

Pure parse, accent-stripped, like `mounted_on_declare_assist`:

- Gate: `actualiza` / `actualizar` / `refresca` / `refrescar` (+ optional `desde catalogo` / `del catalogo`).  
- Subject nouns → keys: esc; motor(es)→`motors`; bateria→`battery`; helice(s)/propeller→`propellers`; frame/chasis→`frame`.  
- No subject / unrecognized → `NONE` (fall through).  
- Do **not** fire on unrelated “actualizar” status phrases without a subject noun.

### 3.3 Orchestrator IDLE

Near mounted_on / catalog-rebind IDLE bridges, **before** LLM:

- If parse hits → call writer → save → confirmation.  
- Stay IDLE.  
- Surface `ValueError` as error status.

### 3.4 Confirmation copy (honesty)

Shape:

> `Actualizado desde catálogo (hobbywing_xrotor_40a_6s): mass_g 26 → 15.`  
> Optional: `Montaje declarado sin cambios.` if `mounted_on` still set.

**Forbidden:** corregido automáticamente, verificado, cabe, ensamblado.

If no property values changed (already fresh): honest “ya coincidía con el catálogo” — still ok status, no false diff.

---

## 4. Tests (required)

New file e.g. `tests/test_catalog_bound_refresh_b1.py`:

| # | Case |
|---|---|
| T1 | Writer: stale ESC mass 26 + catalog_ref → 15; `mounted_on` preserved |
| T2 | Writer: no `catalog_ref` → ValueError, no write |
| T3 | Writer: missing key → ValueError |
| T4 | Parse SET for esc / motors / battery phrases; NONE for bare “actualizar” |
| T5 | Orchestrator IDLE refresh esc on fixture project → persisted 15 + honest message |
| T6 | Non-regression: idle `cambiar frame` / mounted_on declare still work (smoke) |

Run full suite; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | `refresh_component_from_catalog` |
| `src/jarvis/core/catalog_refresh_assist.py` (or equiv.) | pure parse |
| `src/jarvis/core/orchestrator.py` | IDLE dispatch |
| `tests/test_catalog_bound_refresh_b1.py` | T1–T6 |
| `.jes/artifacts/implementation_report_catalog_bound_refresh_b1.md` | write |

**Do not change:** seeds · `bind_*` merge semantics (call as-is) · Board/ui · mounted_on writer · version

---

## 6. Explicit non-goals

ESC picker UX · auto-refresh on load · free-text ESC “fix” · Fase 2/3 · fit/pose · Here3/Pixhawk · inventing SKUs · version bump · weakened tests

---

## 7. Done criteria

- [ ] Writer refreshes all five families via existing binders + `base=`  
- [ ] Continuity IDLE phrases work for esc (and peers)  
- [ ] `mounted_on` preserved on ESC refresh test  
- [ ] Honest copy; no forbidden tokens  
- [ ] Tests T1–T6; full suite green; count reported  
- [ ] Report written  
- [ ] Cursor review; Engineer smoke: refresh demo ESC → Board 15 g

---

## 8. Stop conditions

Stop and ask before: changing `bind_frame_from_catalog` child-clear behavior, adding Board-load hooks, or building an ESC picker.
