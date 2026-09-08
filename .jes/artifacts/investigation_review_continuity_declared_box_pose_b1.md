# Investigation Review — Continuity declared box-local pose B1 (CLI / IDLE)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_continuity_declared_box_pose_b1.md](investigation_contract_continuity_declared_box_pose_b1.md)  
**Report:** [investigation_report_continuity_declared_box_pose_b1.md](investigation_report_continuity_declared_box_pose_b1.md)  
**Parents:** declared box-local pose writer CLOSED @ **2438** · Continuity `mounted_on` declare CLOSED @ **2380**

## Verdict

**PASS WITH NOTES**

Lean **B1 — thin Continuity declare/clear** is Buy-eligible. Grammar is honestly solvable without morro/gravedad tokens. Writer already encodes origin-must-be-box. B1+ (Scene3D move) and B2 (LLM parse) correctly rejected. B0 is allowed by contract but not required: there is no inescapable collision.

**No READY IC until Engineer ★.** Fit stub stays **QUEUED**. Airframe pose stub stays **DEFERRED**.

This investigation does **not** grow Class A envelopes (plates). Pose CLI places what already has a box. Envelope search remains a **parallel ★**, not this Buy.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + one sentence | **Pass** — B1, gated on `declara` + `mm` + `respecto` |
| Collision with `mounted_on` | **Pass with N1** — zero overlap; table oversimplified `fija` |
| Minimum grammar + clear path | **Pass** — one family; writer replace-whole locked |
| Subjects vs origins | **Pass** — subject = mount noun table; origin = writer box gate |
| B0 evaluated honestly | **Pass** — rejected because grammar exists, not ignored |
| B1+ / B2 rejected | **Pass** |
| Empirical dry-runs (no persist) | **Pass** — Cursor re-ran mount parse + writer |
| Demo census 3 box / 2 disk / 9 none | **Pass** — confirmed |
| Contingency sketch, not IC | **Pass with N2–N3** |
| No code / Scene3D / fit / version | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Demo 14 keys: 3 box (FC, ESC, battery), 2 disk, 9 none | **Confirmed** — `_geometry_from_spec` on `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` |
| All `declared_box_pose` null / `None` | **Confirmed** — JSON literals `null`; model `None`; non-null count 0 |
| `"esc montado en frame_plate"` → mount `SET` | **Confirmed** |
| Pose-shaped phrases → mount `NONE` | **Confirmed** (including `"declara el esc a 5 mm…"`) |
| `"quita el montaje del esc"` → mount `CLEAR`; `"quita la pose…"` → mount `NONE` | **Confirmed** |
| `"por que no puedo montar el dron"` → mount `NONE` | **Confirmed** |
| `"fija el esc en la placa"` | **N1** — live kind is `AMBIGUOUS_TARGET` (4 plates), not `SET` as the report table said. Gate still fires as mount, not pose. |
| Writer ESC→FC `x_mm=5` succeeds | **Confirmed** |
| Writer motors→`frame_plate` `ValueError` exact message | **Confirmed** |
| Orchestrator: mount @ ~960, refresh @ ~974, FN-005 @ ~980, **FN-014 @ ~1001** | **Confirmed** — N2 |
| FN-014 would steal the proposed pose phrase if pose bridge is after it | **Confirmed** — `resolve_acquisition_mention("declara el esc a 5 mm en x respecto al fc")` → `{kind: component, key: esc, block_key: propulsion}` |
| `git status --short -- src/ ui/ tests/ workspace/` | **Confirmed** empty for those trees at review time (investigation-only) |
| Fit stub / Scene3D / version `0.3.8` | **Confirmed** untouched |

---

## Agreement with report core

1. **`declara` + `mm` + `respecto` is a real disambiguator** — agree. Mount gates never require those tokens. Incomplete pose (`declara el esc` without mm/respecto) must fall through to FN-014, not invent a pose.  
2. **Do not reuse `fija`** — agree; empirically already claimed by mount.  
3. **Axis tokens = `x/y/z` and `largo/ancho/alto` only** — agree; `adelante`/`arriba` would relitigate declared axes.  
4. **Assist stays a parser; writer is the box/self/missing gate** — agree.  
5. **One utterance must name every axis wanted** — agree and **load-bearing**: writer replaces the whole `DeclaredBoxPose`, it does not merge. Carry into IC.  
6. **B1+ visor move is a later ★** — agree. Declaring millimetres ≠ placing CSS solids.  
7. **B2 LLM parse rejected** — agree.

---

## Notes

### N1 — `"fija el esc en la placa"` is mount `AMBIGUOUS_TARGET`, not `SET`

Four `frame_plate*` keys. Collision claim still holds (mount grammar owns `fija`+`en`). IC tests should use this phrase as “stays mount, not pose,” not as a successful SET.

### N2 — Insertion order is the real collision (FN-014)

Report sketches pose bridge after catalog refresh and before FN-005. That is **required**, not optional: FN-014 `_try_start_acquisition_from_mention` treats `declara el esc…` as acquisition. If the pose assist sits after FN-014, Continuity pose never runs.

Lock for IC: IDLE order `mounted_on` → catalog refresh → **declared box pose** → FN-005 → FN-014.

Also test: `"declarar batería"` / `"declarar el esc"` remain acquisition (pose `NONE` — missing `mm`+`respecto`).

### N3 — Origin resolution is a union, not only frame-part targets

Sketch says reuse `_resolve_target` for origin. `"respecto al fc"` needs the **subject** noun table; `"respecto a frame_plate"` needs frame-part targets. IC must resolve origin from **both**, then let the writer reject non-box. Do not `import` `_SUBJECT_PATTERNS` as a private API if an IC can export a small shared helper or duplicate the six nouns with a comment — hygiene, not architecture.

### N4 — Class A envelope search is not this Buy

Report correctly stayed off plate L×W. Engineer reflection (2026-09-08): the wall for *more 3D solids* is sourced envelope KNOW, not the visor and not Continuity pose. That remains a **named later ★** (Geometry-for-all method: datasheet → seed `source_url`/`source_note`). It does not reopen this investigation and does **not** justify an in-product web crawler (see Engineer question; review stance: **no** — new subsystem, LLM would become KNOW source).

---

## Buy options (reviewer)

| Option | Reviewer |
|---|---|
| B0 writer-only | Honest spare; **not** recommended now that grammar exists |
| **B1 thin Continuity** | **Recommend ★** |
| B1+ Scene3D from pose | **Reject this cycle** |
| B2 LLM parse | **Reject** |

---

## Closable

Investigation **CLOSED** for Buy. Engineer ★ **B1** (`procede` 2026-09-08). IC: [implementation_contract_continuity_declared_box_pose_b1.md](implementation_contract_continuity_declared_box_pose_b1.md). Package `0.3.8` · suite **2438**.
