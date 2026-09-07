# Implementation Contract — Geometry Assembly Pose B1+ · **B0 Defer**

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** n/a (doc-only close — no code)  
**Reviewer:** Cursor self-check against this IC after state/docs update

**Status:** READY FOR IMPLEMENTATION — Engineer asked to `redacta Ic` after investigation lean **B0 Defer**  
**Parents:**
- [investigation_contract_geometry_assembly_pose_b1plus.md](investigation_contract_geometry_assembly_pose_b1plus.md)
- [investigation_report_geometry_assembly_pose_b1plus.md](investigation_report_geometry_assembly_pose_b1plus.md) — lean **B0 Defer**
- [investigation_review_geometry_assembly_pose_b1plus.md](investigation_review_geometry_assembly_pose_b1plus.md) — **PASS WITH NOTES**
- Stub: [implementation_contract_geometry_assembly_pose_b1plus.md](implementation_contract_geometry_assembly_pose_b1plus.md) — superseded by this Defer IC

**Type:** Formal **Defer** of numeric pose. **Zero code.** Closes assembly queue item **2/3**.  
**Not** a schema Buy. **Not** Continuity pose. **Not** fit.

**Baseline:** package **`0.3.8`** · suite **2385**

**Output:** `.jes/artifacts/implementation_report_geometry_assembly_pose_b1plus_defer.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B0 — Defer** numeric pose |
| 2 | Code | **None** — no `src/` / `tests/` / `ui/` / catalog edits |
| 3 | Stub IC | Mark **DEFERRED** — do not implement under that filename |
| 4 | Reaffirm | Prior assembly-espacial B1+ rejection **stands** (addressability ≠ reference frame) |
| 5 | Fit (queue 3/3) | **Not** opened by this IC — remains queued stub until separate ★ |
| 6 | Version | **No** bump |

---

## 1. You

- Do **not** add pose / offset / orientation / origin fields to `ComponentSpec` or elsewhere.
- Do **not** invent axis conventions, plate centers, or catalog mount patterns.
- Do **not** treat Board `x`/`y` as physical pose.
- Do **not** open fit/clearance or Continuity “pose mm” parsers.
- Update engineering state + `IMPLEMENTATION_TASKS` + stub status; write the short implementation report.
- Full suite: **not required** if `git status --short -- src/ tests/ ui/` stays empty (doc-only). If any code path is touched by mistake, stop and revert.

---

## 2. Intent

```text
Investigation B0 Defer
        ↓
Lock: no numeric pose this cycle
        ↓
Queue 2/3 CLOSED as DEFERRED
        ↓
Assembly relation rung remains: mounted_on + Continuity + Board edges
```

Product stance (honest):

> “Sé a qué se declara montado; **no** afirmo una pose mm hasta existir origen/eje honestos.”

---

## 3. Locked behavior (doc-only)

### 3.1 Stub supersession

In `implementation_contract_geometry_assembly_pose_b1plus.md`, set status to:

> **DEFERRED 2026-09-07** — superseded by this Defer IC. DO NOT IMPLEMENT. Reopen only if Engineer ★ after a reversal condition from the investigation report (§E).

### 3.2 State / tasks

- `geometry_assembly_pose_b1plus` → DEFERRED CLOSED (investigation B0)  
- PRIORIDAD: idle or await Engineer next focus (fit stub stays queued, not active)  
- `active_operation`: null  

### 3.3 Explicit non-goals

Any pose schema · Continuity pose phrases · Board glyph reposition from numbers · fit investigation auto-open · version bump · weakened tests

---

## 4. Tests

None. Doc-only. Confirm with:

```text
git status --short -- src/ tests/ ui/ library/
```

must be empty for this cycle.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `implementation_contract_geometry_assembly_pose_b1plus.md` | status → DEFERRED |
| `docs/IMPLEMENTATION_TASKS.md` | close cola 2/3 as deferred |
| `.jes/state/engineering_state.json` | defer closed; idle |
| `.jes/artifacts/implementation_report_geometry_assembly_pose_b1plus_defer.md` | write |

**Do not change:** any production code, UI, seeds, package version.

---

## 6. Done criteria

- [ ] Stub marked DEFERRED  
- [ ] State/tasks reflect Defer close of queue 2/3  
- [ ] Report written; `src/`/`tests/`/`ui/` untouched  
- [ ] Fit stub remains queued (not silently activated)

---

## 7. Stop conditions

Stop and ask before: writing pose fields, opening fit as part of this IC, or treating Defer as permanent Reject.
