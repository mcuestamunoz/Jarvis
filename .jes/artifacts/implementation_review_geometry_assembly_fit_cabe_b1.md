# Implementation Review — Geometry assembly fit B1-min (posed box–box screening)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_assembly_fit_cabe_b1.md](implementation_contract_geometry_assembly_fit_cabe_b1.md)  
**Report:** [implementation_report_geometry_assembly_fit_cabe_b1.md](implementation_report_geometry_assembly_fit_cabe_b1.md)

## Verdict

**PASS WITH NOTES**

AABB lives in Python on raw `declared_box_pose` mm. Missing axes are **not** 0. Board field `sobres` + IDLE whole-word `cabe`. No `"cabe"` / `VERIFIED` in Jarvis copy. `ui/` / `scene3dLayout.ts` untouched. Suite **2540** re-ran here (2532 + 8). Closable after Engineer smoke §6 on **`autonomía-de-10min`**.

---

## Checklist

| Criterion | Result |
|---|---|
| `screen_posed_envelope` statuses | **Pass** |
| AABB declared mm, center-to-center, inclusive touch | **Pass** — Cursor: `x=47` overlap, `x=47.01` no_overlap |
| Missing axis → `pose_incomplete`, no arithmetic 0 | **Pass** |
| No `mounted_on` / no origin chains / no cylinder | **Pass** |
| Locked Spanish + “screening, no verificado” | **Pass** |
| Forbidden tokens absent from helper copy | **Pass** |
| Board `sobres` after pose Δ; DTO keys unchanged | **Pass** — T5 |
| IDLE after pose bridge, before help-choose | **Pass** |
| Whole-word `\bcabe\b`; not in `COMPONENT_TERM_ALIASES` | **Pass** |
| No wizard / no Gap / `engineering_readiness.py` empty | **Pass** |
| `project_continuity.py` / pose parser empty this Buy | **Pass** |
| `ui/` empty | **Pass** |
| Version `0.3.8` | **Pass** |
| T0–T7 green | **Pass** |
| Full suite **2540** | **Pass** |
| Stub 2026-09-07 not implemented as READY | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Incomplete live-shaped `x_mm=5` → faltan y, z | **Confirmed** T0 |
| `(5,0,0)` overlap / `(200,0,0)` no_overlap | **Confirmed** T1/T2 |
| Origin disk / missing origin | **Confirmed** T3 |
| Child disk → `child_not_box` | **Confirmed** T4 |
| `declaredBoxPose` keys still `{originKey, xMm}` | **Confirmed** T5 |
| `_block_progress_status` twin | **Confirmed** T6 (see N1) |
| `"cabe el esc"` / `"¿cabe el esc?"` no LLM | **Confirmed** T7 |
| Local `_geometry_from_spec` import (no `ui/`) | **Confirmed** |
| Inclusive `|d| ≤ sum of halves` | **Confirmed** (touch 47 mm) |

---

## Notes

### N1 — T6 does not call readiness `overall`

IC asked a twin on `_block_progress_status` **and** readiness `overall`. Tests only equalize block progress. `engineering_readiness.py` has **zero** diff and no new `Gap` type, so overall cannot flip from this Buy. Not a reopen.

### N2 — Bare `"cabe"` untested in T7

Handler supports it when exactly one posed component exists. T7 only sends `"cabe el esc"` / `"¿cabe el esc?"`. Smoke: both forms.

### N3 — Disambiguation action name

Two posed components → `action: component_description_prompt` while mode stays IDLE. Not a DEFINE wizard. Next utterance should still include `cabe` (e.g. `cabe el esc`); a bare `esc` will not hit this bridge. Acceptable B1-min.

### N4 — Pose REPLACE

Smoke must re-declare **x+y+z in one phrase**. `declared_box_pose_declare_assist` was not edited.

### N5 — Absence copy says “ensamblaje”, not “ensamblado”

Forbidden token is `ensamblado`. Honest “no verifica ensamblaje físico” is allowed.

---

## Phase

Implementation **CLOSED**. Engineer smoke: [engineer_smoke_geometry_assembly_fit_cabe_b1.md](engineer_smoke_geometry_assembly_fit_cabe_b1.md) **ACCEPT** (5min fail-closed + 10min overlap). Package `0.3.8` · suite **2540**.

Sim FAIL on 10min is P-energy, not this Buy.

Walk on **`autonomía-de-10min`**:

1. Board ESC `sobres` = pose incompleta (x=5 only).  
2. `declara el esc a 5 mm en x y 0 mm en y y 0 mm en z respecto al fc` → se solapan.  
3. Far pose → no se solapan.  
4. `cabe` / `¿cabe el esc?` → same text, not LLM.  
5. Hover / 4/4 / energy `NOT ASSEMBLY READY` unchanged.

Do **not**: treat visor 0 as a declared axis; invent Rooster L×W; add a Gap; port `scene3dLayout.ts`.
