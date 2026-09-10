# Implementation Contract — Pose Continuity subject: kit keys B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer “falta centralos” after XT60/harness **envelopes** exist (30×20×10 / 30×10×5) but no pose fields — probe: pose parser → **INCOMPLETE** for `conector`/`xt60`/`harness`/`cable de señal`/`power_connector`  
**Parents:**
- Declared sensors + kit envelope **CLOSED** @ **2593** — envelope subjects include kit; pose subjects do **not**
- Pose Continuity subject: plates **CLOSED** (report @ **2608**) — `_resolve_pose_subject` = electronics noun **then** plate noun; kit still missing
- Writer already accepts pose on any existing key if origin is a **box**

**Type:** Extend pose subject resolution to presence-gated kit keys (`power_connector` / `signal_harness`) using the **same** nouns as envelope. Prefer extracting a public kit resolver from envelope (mirror `resolve_plate_subject_noun`) rather than a third noun table.  
**Not** inventing mm. **Not** auto-pose. **Not** assembly-root change. **Not** sourced dims. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2608** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_continuity_pose_kit_subject_b1.md`

**Role lock:** **Claude implements.** Cursor = IC / review / PRIORIDAD only.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-pose-kit-subject** — Continuity can pose XT60 / harness boxes |
| 2 | Subject order | (1) electronics `resolve_component_subject_noun` (2) plate `resolve_plate_subject_noun` (3) **kit** resolver — presence-gated like envelope |
| 3 | Kit nouns | Same as envelope: conector / xt60 / power_connector · harness / cable de señal / signal_harness. Only if key ∈ `components` |
| 4 | Origin | Unchanged (part noun + plate noun). Engineer centers with `0 mm en x` + `0 mm en y` vs a **box** (typically `frame_plate`) |
| 5 | Collision | No `respecto` → envelope. With `respecto` → pose |
| 6 | CLEAR | `quita la pose del conector` / harness when subject resolves |
| 7 | Auto / invent | **No** auto-write. **No** catalog dims |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Puedo declarar el conector / harness a 0 mm en x y 0 mm en y [y Z en z]
respecto a frame_plate y quedan centrados en el racimo.
```

---

## 1. You (Claude)

- Extend `_resolve_pose_subject` (+ optional public `resolve_kit_subject_noun` extracted from envelope).
- Tests + report. Full pytest green.
- Do **not** change writer / visor / assembly root.
- Do **not** mutate `workspace/` or invent mm.
- Do **not** bump version.
- **STOP** if kit pose requires a new schema field.

---

## 2. Intent

```text
IDLE "declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"
  → SET power_connector, origin frame_plate, x=0 y=0 z=5

IDLE "declara el harness a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"
  → SET signal_harness …
```

---

## 3. Tests

`tests/test_continuity_pose_kit_subject_b1.py`

| ID | Behavior |
|---|---|
| P1 | `declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate` → SET `power_connector` |
| P2 | `declara el harness a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate` → SET `signal_harness` |
| P3 | `xt60` / `cable de senal` nouns when keys present |
| P4 | Kit noun with key **missing** → INCOMPLETE (not invented) |
| P5 | Electronics + plate pose regressions still SET |
| P6 | Envelope without `respecto` still pose `NONE` |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/declared_box_pose_declare_assist.py` | kit in `_resolve_pose_subject` |
| `src/jarvis/core/declared_envelope_declare_assist.py` | optional public kit subject export |
| `tests/test_continuity_pose_kit_subject_b1.py` | P1–P6 |
| `.jes/artifacts/implementation_report_continuity_pose_kit_subject_b1.md` | write |

---

## 5. Engineer smoke (after review)

```text
declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate
declara el harness a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate
```

(Adjust Z.) Expect pose fields on cards + solids near plate center.

Record [engineer_smoke_continuity_pose_kit_subject_b1.md](engineer_smoke_continuity_pose_kit_subject_b1.md).

---

## Explicitly not this IC

Invent XT60/cable mm · auto-pose · assembly root · sourced dims · Conversation Engine · version bump
