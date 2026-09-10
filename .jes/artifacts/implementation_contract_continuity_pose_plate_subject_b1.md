# Implementation Contract — Pose Continuity subject: plates B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer “queda situarla con todo el equipo” after Top LiPo envelope: `frame_plate_2` box + battery posed on it sit in the **row** because pose Continuity **cannot name a plate as subject**  
**Parents:**
- [Work order](engineer_next_geometry_remaining_pieces.md) — insert before sourced-dims #4 (situar gap)
- Top LiPo envelope noun **PASS WITH NOTES** @ **2602** — `placa lipo` SET envelope works; pose subject still electronics-only
- Continuity declared box pose **CLOSED** — subject = `resolve_component_subject_noun` only (no plates)
- Writer `set_component_declared_box_pose` already accepts **any** existing component as the posed key; origin must be a **box** (Main Plate / Top LiPo once enveloped)
- Multi-hop / assembly root **CLOSED** — Main `frame_plate` stays world origin; posed `frame_plate_2` vs Main will compose; battery vs plate_2 composes on top

**Type:** Extend **pose** parser subject resolution so plates can be posed (same nouns as envelope: exact key, label match, `placa principal`, `placa lipo` / top lipo). Prefer **no** writer change. Prefer **no** visor change.  
**Not** auto-pose. **Not** inventing mm. **Not** assembly root → plate_2. **Not** sourced dims (#4). **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2602**

**Output:** `.jes/artifacts/implementation_report_continuity_pose_plate_subject_b1.md`

**Role lock:** **Claude implements.** Cursor = IC / review / PRIORIDAD only.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-pose-plate-subject** — Continuity can pose a plate box relative to another box |
| 2 | Subject resolve | On the subject segment (before `respecto`), try in order: (a) existing `resolve_component_subject_noun`; (b) exact plate key / label / `placa principal` / `placa lipo` paths — **reuse** envelope helpers or `resolve_declared_part_noun`, do **not** invent a third noun table. Prefer importing the public/shared plate resolvers already used by envelope |
| 3 | Allowed posed keys | Any component the writer already accepts (including `frame_plate*`). Parser must resolve at least: `frame_plate_2`, `placa lipo` / `top lipo`, `placa principal` / `frame_plate` when those keys exist |
| 4 | Origin | Unchanged: `resolve_declared_part_noun` after `respecto` (Main Plate, FC, etc.). Writer still rejects non-box origins |
| 5 | Collision | Envelope still owns phrases **without** `respecto`. Pose still requires `declara` + `mm` + `respecto`. `declara la placa lipo 100 x 100 mm` (no respecto) → envelope. `declara la placa lipo a 0 mm en z respecto a frame_plate` → pose |
| 6 | CLEAR | `quita la pose de la placa lipo` / `frame_plate_2` must CLEAR when subject resolves to that plate |
| 7 | Visor / root | **No** `ASSEMBLY_ROOT_ID` change. plate_2 posed vs Main sits on the racimo via multi-hop |
| 8 | Auto | **Do not** auto-write plate_2 pose or move battery |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Puedo declarar la placa lipo a 0/0/Z mm respecto a la placa principal
y el visor la pone (con la batería encima) en el conjunto.
```

**Not:**

```text
auto-pose · plate_2 como assembly root · inventar Z · sourced dims ·
Conversation Engine
```

---

## 1. You (Claude)

- Change `declared_box_pose_declare_assist.py` (+ tests). Reuse plate noun logic from envelope / `resolve_declared_part_noun` — avoid duplicating regexes if a small shared helper is cleaner **inside existing modules** (no new architectural subsystem).
- Do **not** change writer honesty rules (origin must be box).
- Do **not** change assembly root / multi-hop.
- Do **not** start sourced-dims #4.
- Do **not** mutate `workspace/`.
- Do **not** bump version.
- Full pytest green.
- Write the implementation report when done.
- **STOP** if posing a plate requires a new schema field.

---

## 2. Intent

```text
IDLE "declara la placa lipo a 0 mm en x y 0 mm en y y 20 mm en z respecto a frame_plate"
  → SET subject=frame_plate_2, origin=frame_plate, axes…
  → writer OK (Main is box)
  → multi-hop: plate_2 on Main; battery already vs plate_2 stacks on it
```

---

## 3. Tests

New: `tests/test_continuity_pose_plate_subject_b1.py`

| ID | Behavior |
|---|---|
| P1 | `declara la placa lipo a 0 mm en z respecto a frame_plate` → SET `frame_plate_2`, origin `frame_plate`, z=0 |
| P2 | `declara frame_plate_2 a 0 mm en x y 0 mm en y y 15 mm en z respecto a la placa principal` → SET |
| P3 | Envelope regression: `declara la placa lipo 100 x 100 mm` (no respecto) still envelope SET (or NONE for pose parser) |
| P4 | Electronics pose regression: `declara el esc a 5 mm en x respecto al fc` still SET esc |
| P5 | `quita la pose de la placa lipo` → CLEAR `frame_plate_2` when pose present |
| P6 | Writer still rejects pose whose origin is shapeless |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/declared_box_pose_declare_assist.py` | plate subject resolve |
| `src/jarvis/core/declared_envelope_declare_assist.py` | only if extracting a shared public helper |
| `tests/test_continuity_pose_plate_subject_b1.py` | P1–P6 |
| `ui/` / `library/` | **empty** |
| `.jes/artifacts/implementation_report_continuity_pose_plate_subject_b1.md` | write |

---

## 5. Engineer smoke (after Cursor review)

| Step | Expected |
|---|---|
| Pose placa lipo vs Main (Engineer picks Z) | Top LiPo + battery join the central stack; X unchanged |
| Main Plate still assembly root | **Pass** |

Record [engineer_smoke_continuity_pose_plate_subject_b1.md](engineer_smoke_continuity_pose_plate_subject_b1.md).

---

## Explicitly not this IC

Assembly root change · invent Z · auto-pose · sourced dims · Conversation Engine · version bump
