# Implementation Contract — Top LiPo plate (`frame_plate_2`) envelope noun B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer “Dentro” (GPS situar OK) + “Vamos a por el siguiente, redacta IC frame_plate” → work order **#3 of 4**  
**Parents:**
- [Work order](engineer_next_geometry_remaining_pieces.md) — #1 multi-hop **CLOSED** · #2 sensors/kit **CLOSED** · **#3 this** · #4 sourced dims
- Declared battery + Main Plate envelope **CLOSED** — writer already allows **any** `is_frame_plate_key`; `"placa principal"` resolves Main Plate only
- Live probe (pre-Buy): `declara frame_plate_2 100 x 100 mm` and `declara la top (lipo) plate 100 x 100 mm` already **SET** `frame_plate_2`; Spanish `"placa lipo"` / `"placa top"` → **AMBIGUOUS_PLATE** (bare `placa`)
- Live 5min: `frame_plate_2` label **Top (LiPo) plate**, `thickness_mm` **2**, **no** L×W; battery `mounted_on=frame_plate_2` but pose still vs Main `frame_plate`
- Assembly root **CLOSED** — world origin stays exact key `frame_plate` box only — **never** `frame_plate_2`

**Type:** Continuity **noun** for Top LiPo plate (mirror `"placa principal"`) + tests. Prefer **no** writer allowlist change (already open). Prefer **no** visor / multi-hop / assembly-root change.  
**Not** inventing L×W. **Not** seeding Rooster plate footprint. **Not** 230-as-box. **Not** making Top LiPo the Scene3D world origin. **Not** HD Cam / small-front plates this Buy. **Not** sourced auto-fill (#4). **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2593**

**Output:** `.jes/artifacts/implementation_report_geometry_frame_plate_2_lipo_envelope_b1.md`

**Role lock:** **Claude implements.** Cursor = IC / review / PRIORIDAD only.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-plate2-noun** — Continuity can name the Top LiPo plate without typing the English label or the raw key |
| 2 | Target | Resolve to the plate whose **own** label normalizes to exactly `top (lipo) plate` (live Rooster `frame_plate_2`). If 0 matches → no subject (INCOMPLETE/NONE per existing). If 2+ → AMBIGUOUS_PLATE |
| 3 | Nouns | Accept at least: `placa lipo`, `placa top lipo`, `top lipo`, `top lipo plate` (after `_normalize_help`). Keep existing paths: exact key `frame_plate_2`, full label substring `top (lipo) plate` |
| 4 | Dims | Unchanged plate SET: **L×W** required; H from utterance or existing `thickness_mm` (live **2**). Never write `wheelbase_mm`. Never invent L/W |
| 5 | Writer | **No** allowlist change required (`is_frame_plate_key` already). Do not widen to non-plates |
| 6 | Assembly root | **Unchanged.** `frame_plate_2` box must **not** become Scene3D world origin. Add/keep a regression if cheap (visor test optional; Python “not ASSEMBLY_ROOT” is ui-only — at minimum document + do not touch `ASSEMBLY_ROOT_ID`) |
| 7 | Pose | **Out of writer.** After Top LiPo is a box, existing pose Continuity may use `respecto a frame_plate_2` (e.g. battery). Do **not** auto-repose battery from Main Plate |
| 8 | Other plates | HD Cam / small front / rear VTX — **out**. No new nouns for them this Buy |
| 9 | Library | **No** L×W seed on Rooster plates |
| 10 | Version | **No** bump |

**Product sentence:**

```text
Puedo decir "declara la placa lipo 100 x 100 mm" y Jarvis escribe el
sobre en frame_plate_2 (alto = thickness 2 mm si no digo H). Luego puedo
situar la batería respecto a esa placa. La Main Plate sigue siendo el
origen del visor.
```

**Not:**

```text
230 como L/W · seed catálogo · plate_2 como assembly root · HD Cam noun ·
auto-pose batería · Conversation Engine
```

---

## 1. You (Claude)

- Add a dedicated Top-LiPo resolver in `declared_envelope_declare_assist.py` (same shape as `_resolve_main_plate` / `_MAIN_PLATE_RE`).
- Optionally improve IDLE INCOMPLETE hint to mention `placa lipo` (one-line copy only).
- Do **not** change `ASSEMBLY_ROOT_ID` / `scene3dLayout` (unless a regression test in ui is the only way to prove plate_2 ≠ root — prefer **not** touching ui/).
- Do **not** seed `library/frames/_datos.json` L×W.
- Do **not** implement #4 sourced dims.
- Do **not** mutate `workspace/`.
- Do **not** bump version.
- Full pytest green.
- Write the implementation report when done.
- **STOP** if the only fix is inventing Top LiPo L×W from wheelbase 230.

---

## 2. Intent

```text
IDLE "declara la placa lipo 100 x 100 mm"
  → SET frame_plate_2, L=100 W=100, height_mm=None
  → orchestrator fills H from thickness_mm=2
  → projector box; pose origin unlocked for frame_plate_2

IDLE "declara la batería a 0/0/Z respecto a frame_plate_2"  (existing pose path)
  → battery on Top LiPo (Engineer-typed; not auto)
```

---

## 3. Locked behavior

| Phrase | Result |
|---|---|
| `declara la placa lipo 100 x 100 mm` (unique Top LiPo label present) | SET `frame_plate_2` |
| `declara frame_plate_2 100 x 100 mm` | SET (already works — keep) |
| `declara la placa principal 100 x 100 mm` | SET Main (regression) |
| bare `declara la placa 100 x 100 mm` with 2+ plates | AMBIGUOUS_PLATE (regression) |
| `respecto` present | NONE (pose owns it) |

---

## 4. Tests

New or extend: `tests/test_geometry_frame_plate_2_lipo_envelope_b1.py` (preferred) or add to battery/plate suite.

| ID | Behavior |
|---|---|
| P1 | Parser `declara la placa lipo 100 x 100 mm` → SET `frame_plate_2`, height None |
| P2 | Orchestrator or writer path: after SET, `height_mm` becomes 2 from thickness (mirror Main Plate P2 style — test the apply path that already exists) |
| P3 | `placa principal` still → `frame_plate` |
| P4 | bare `placa` with Main + Top LiPo → AMBIGUOUS_PLATE |
| P5 | Pose writer accepts `frame_plate_2` as origin **after** it has a box triple (existing rule — regression) |
| P6 | No `length_mm`/`width_mm` added to Rooster plate seeds in `library/frames/_datos.json` |

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | Top LiPo noun resolver |
| `src/jarvis/core/orchestrator.py` | optional hint copy |
| `tests/test_geometry_frame_plate_2_lipo_envelope_b1.py` | P1–P6 |
| `ui/` / `library/` L×W / `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_frame_plate_2_lipo_envelope_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min`:

| Step | Expected |
|---|---|
| `declara la placa lipo 100 x 100 mm` (or Engineer’s L×W — **not** 230 unless typed) | `frame_plate_2` box; H=2 from thickness; wheelbase still 230 |
| Optional: pose battery `respecto a frame_plate_2` | battery on Top LiPo; Main Plate still assembly root / X center |
| Forbidden | plate_2 becomes world origin; L/W = 230 without typing |

Record [engineer_smoke_geometry_frame_plate_2_lipo_envelope_b1.md](engineer_smoke_geometry_frame_plate_2_lipo_envelope_b1.md).

---

## 7. Done when

- [ ] P1–P6 green; full pytest green
- [ ] No library L×W seed; no assembly-root change; no version bump
- [ ] Report written

---

## Explicitly not this IC

Assembly root → plate_2 · invent L×W · 230-as-box · HD Cam / other plate nouns · sourced auto-fill · auto-pose battery · Conversation Engine · version bump
