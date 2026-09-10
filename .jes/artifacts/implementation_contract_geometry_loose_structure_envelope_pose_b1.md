# Implementation Contract — Loose structure/kit envelopes + pose subjects B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer ACCEPT on A1 + “procede a por las sueltas” + “un IC junto”  
**Parents:**
- [Feature lock — Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- [Work order](engineer_next_geometry_loose_and_arms.md) — A1 **CLOSED** + ACCEPT · **B1 this** · #4 sourced cola
- Frame arm visor X **CLOSED** + ACCEPT @ **2622**
- Kit envelope + pose kit subject **CLOSED** — pattern to mirror for these keys
- Live 5min mute cards (thickness/material/label only): `prop_adapter`, `frame_standoff`, `frame_cage`, plus Rooster plates 3–6 (see §0 lock 2)

**Type:** One Buy — extend **existing** declared-envelope writer/parser **and** pose Continuity subject resolution so Engineer can type L×W×H + situate these structure/kit keys. Presence-gated (key must already exist in `components`).  
**Not** inventing mm. **Not** seeding library. **Not** plate L×W auto-fill (plates already allowlisted). **Not** visor copies / X stations for standoffs. **Not** Conversation Engine. **Not** sourced dims (#4).

**Baseline:** package **`0.3.8`** · suite **2622** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_geometry_loose_structure_envelope_pose_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-loose-envelope-pose** — one IC for the remaining **non-plate** mute structure/kit holes |
| 2 | In allowlist (writer + envelope subject + pose subject) | Add exactly, presence-gated: `prop_adapter`, `frame_standoff`, `frame_cage`, `frame_caps`. Reuse existing mount nouns where possible (`adaptador`/`adapter`/`collet`, `standoff`/`separador(es)`, `jaula`/`cage`, `caps`/`tapas` + exact keys). Missing key → no invent |
| 3 | **Out of this IC (no code)** | `frame_plate*` ordinals (HD Cam, Rear VTX, Small front/rear, …) — **already** on envelope/pose plate path. Engineer types L×W (thickness fallback) **now** without waiting on Claude. Optional later: sourced #4 |
| 4 | SET dims | **Three** finite mm > 0. No thickness→H invent for these keys (even if a future seed has thickness). Pair-only → INCOMPLETE |
| 5 | CLEAR | Same clear phrases as battery/kit with resolved subject |
| 6 | Pose | Same nouns as envelope subjects; `\brespecto\b` still owns pose vs envelope collision. Origin rules unchanged (origin must be a box). Do **not** auto-pose |
| 7 | Visor | Projector already draws box from L×W×H. **No** `solidCopies` / station math for these keys |
| 8 | BOM | Still one ComponentSpec per key. Never N sibling keys for standoffs |
| 9 | Library / workspace / version | **No** seed invent · **no** workspace mutate · **no** bump |

**Product sentence:**

```text
Declaro L×W×H (y pose) de adaptador, standoff, jaula, caps si existen.
Las placas mute del Rooster ya se declaran con la gramática de placa.
No invento cotas.
```

**Not:**

```text
inventar L×W de HD Cam / VTX · seed library · 4 standoffs BOM ·
X stations for arms-of-standoff · Conversation Engine · sourced #4
```

---

## 1. You (Claude)

- Writer `_ENVELOPE_ALLOWED_LITERAL_KEYS` + error copy.
- Envelope subject resolver (prefer shared helper like kit/arm — presence-gated patterns or `resolve_declared_part_noun` filtered to this set).
- Pose `_resolve_pose_subject` must resolve the **same** noun set (no second table).
- Put new keys in `_NO_THICKNESS_FALLBACK_KEYS`.
- Tests + report. Full pytest.
- Do **not** change plate grammar. Do **not** invent mm. Do **not** bump version.
- **STOP** if the only path is inventing dims from Rooster marketing copy.

---

## 2. Intent

```text
IDLE "declara el adaptador 12 x 12 x 8 mm"
  → SET prop_adapter box

IDLE "declara el standoff 5 x 5 x 25 mm"
  → SET frame_standoff

IDLE "declara la jaula 40 x 40 x 30 mm" / caps if present
  → SET frame_cage / frame_caps

IDLE "declara el adaptador 0 0 5 mm en ejes respecto a motors"
  (or plate origin with box) → pose SET when origin is a box

Plates (no code): "declara la placa HD Cam 40 x 30 mm" already works today
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Writer SET each new key (when present) → three props `source=declared` |
| P2 | Parser nouns → SET for adapter / standoff / cage (/ caps if fixture has key) |
| P3 | Missing key + noun → no invent (NONE/INCOMPLETE per existing kit pattern) |
| P4 | Pose subject same nouns → SET when origin is a box; strip/`respecto` collision unchanged |
| P5 | Pair-only phrase → INCOMPLETE (no thickness fallback) |
| P6 | Battery / plate / kit / arm envelope regressions still green |
| P7 | Library untouched — no new L×W×H seeds on these SKUs |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | allowlist |
| `src/jarvis/core/declared_envelope_declare_assist.py` | subjects + no-thickness set |
| `src/jarvis/core/declared_box_pose_declare_assist.py` | same subjects on pose path |
| `tests/test_geometry_loose_structure_envelope_pose_b1.py` | P1–P7 |
| `.jes/artifacts/implementation_report_geometry_loose_structure_envelope_pose_b1.md` | write |

---

## 5. Engineer smoke (after review)

1. Declare adapter / standoff / cage (your mm) → boxes appear  
2. Pose at least one onto a plate/motor box origin  
3. Separately (no Claude): declare mute Rooster plates L×W if you want them in 3D now  

Record [engineer_smoke_geometry_loose_structure_envelope_pose_b1.md](engineer_smoke_geometry_loose_structure_envelope_pose_b1.md).

---

## Explicitly not this IC

Plate allowlist work · invent HD Cam/VTX footprint · sourced #4 · arm X reopen · Conversation Engine · version bump
