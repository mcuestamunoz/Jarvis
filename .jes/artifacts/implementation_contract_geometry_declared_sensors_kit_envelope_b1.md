# Implementation Contract — Declared sensors + kit envelope B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer work order step **2 of 4** (“procede con los 4 en orden”)  
**Parents:**
- [Work order](engineer_next_geometry_remaining_pieces.md) — #1 multi-hop **CLOSED** · **#2 this** · #3 plate_2 · #4 sourced dims
- Declared battery + Main Plate envelope **CLOSED** + ACCEPT @ **2583** — writer allowlist is **only** `battery` + `frame_plate*`; parser filters out sensors/kit
- Kit SKUs D **CLOSED** — live `power_connector` / `signal_harness` rows exist; **no** L×W×H on either SKU (cable length ≠ box)
- Live 5min: `sensors` = GPS M9N (identity only, **no** box); kit harness bound; no sensor/kit solid in 3D
- Multi-hop / assembly root **CLOSED** — out of this Buy

**Type:** Extend the **existing** declared-envelope writer + IDLE parser to also accept **`sensors`** and kit keys **`power_connector`** / **`signal_harness`**. Engineer-typed L×W×H only (`source=declared`). Projector already draws a box from that triple.  
**Not** catalog seed. **Not** inventing GPS / XT60 / cable dims. **Not** auto-pose. **Not** `frame_plate_2` Buy (#3). **Not** sourced auto-fill (#4). **Not** Conversation Engine. **Not** visor layout change.

**Baseline:** package **`0.3.8`** · suite **2583** (confirm live count in report)

**Output:** `.jes/artifacts/implementation_report_geometry_declared_sensors_kit_envelope_b1.md`

**Role lock:** **Claude implements** `src/` / tests. Cursor does **not** land this Buy’s code.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-sensors-kit-envelope** — declare / clear box on sensors + kit holes |
| 2 | Allowed keys (writer) | Keep `battery` + `is_frame_plate_key`. **Add** exactly: `sensors`, `power_connector`, `signal_harness`. Still **ValueError** for `frame` root, arms, cage, standoff, motors, ESC, FC, propellers, other keys |
| 3 | SET dims | Sensors and kit require **three** finite mm > 0 (L, W, H). **No** thickness fallback (that stays plate-only). Pair-only phrase → INCOMPLETE |
| 4 | CLEAR | Same clear phrases as battery/plate (`quita el sobre` / `quita las cotas`) with a resolved subject |
| 5 | Source | `PropertyValue(..., unit="mm", source="declared")` on the three axes. Never `catalog` |
| 6 | Physics / bind | Never touch `catalog_ref`, energy, kit pin/pitch fields, or `current_parameters`. Never call `set_battery_component` / kit bind writers on this path |
| 7 | Parser subjects | Accept `sensors` via existing subject noun (`sensores`/`sensor`/`gps`/…). Accept kit via noun patterns for `power_connector` / `signal_harness` (reuse acquisition-style words: conector / xt60 / harness / cable de señal / signal_harness / power_connector) — only if that key **exists** in `components`. Missing key → INCOMPLETE (SET) or NONE (CLEAR), never invent a component |
| 8 | Collision | `\brespecto\b` → NONE (pose owns it). Battery/plate paths **unchanged** |
| 9 | Pose / visor | **Out.** After a box exists, existing pose Continuity may situate it (Engineer types). Do not auto-pose. Do not change `scene3dLayout` |
| 10 | Library | **No** seed of L×W×H on GPS / Pololu / Pi Hut rows. Cable `cable_length_options_mm` must **not** become `length_mm` |
| 11 | Version | **No** bump |

**Product sentence:**

```text
Puedo declarar L×W×H del GPS/sensores y del conector/harness. El visor
pinta esas cajas. No invento cotas del catálogo ni del largo del cable.
```

**Not:**

```text
seed GPS dims · XT60 box inventada · cable 100mm como length_mm ·
frame_plate_2 Buy · sourced auto-fill · pose automática · Conversation Engine
```

---

## 1. You (Claude)

- Extend `set_component_declared_box_envelope` allowlist + error copy.
- Extend `declared_envelope_declare_assist` subject resolution (keep battery/plate behavior byte-compatible).
- Wire orchestrator only if the existing envelope IDLE path already covers new keys once parser/writer accept them — do **not** add a parallel route.
- Do **not** seed `library/**` dims for sensors or kit.
- Do **not** implement #3 / #4.
- Do **not** change multi-hop / assembly root / visor X.
- Do **not** mutate `workspace/`.
- Do **not** bump version.
- Full pytest green. `ui/` empty unless a proven DTO hole (you must not need it).
- Write the implementation report when done.
- **STOP** if the only path is inventing GPS or connector millimetres from marketing copy.

---

## 2. Intent

```text
IDLE "declara el gps 40 x 40 x 12 mm"
  → parse SET sensors + triple
  → set_component_declared_box_envelope(...)
  → projector box

IDLE "declara el harness 30 x 10 x 5 mm"  (fixture numbers — not catalog)
  → SET signal_harness

IDLE "quita el sobre del sensor"
  → CLEAR sensors
```

---

## 3. Locked behavior

### 3.1 Writer

| Key | Allowed |
|---|---|
| `battery`, `frame_plate*` | yes (unchanged) |
| `sensors`, `power_connector`, `signal_harness` | **yes (new)** |
| anything else | ValueError |

SET / CLEAR merge rules unchanged (preserve other properties; three axes only).

### 3.2 Parser

| Phrase shape | Result |
|---|---|
| `declara` + subject + `A x B x C mm` | SET (if subject allowed + present) |
| `declara` + sensors/kit + only pair | INCOMPLETE |
| `declara` + plate pair | unchanged (thickness fill at orchestrator) |
| `respecto` present | NONE |
| unknown / missing component | INCOMPLETE or NONE per existing conventions |

### 3.3 Copy

Idle confirmation should mirror battery style (Declarado: … source=declared). No “verificado” / “cabe” / ensamblado claims.

---

## 4. Tests

New file preferred: `tests/test_geometry_declared_sensors_kit_envelope_b1.py`

| ID | Behavior |
|---|---|
| P1 | Writer SET on `sensors` with 3 mm → properties + `source=declared` |
| P2 | Writer SET on `signal_harness` / `power_connector` |
| P3 | Writer rejects `esc` / `motors` / `frame` (still ValueError) |
| P4 | Writer CLEAR sensors removes the three keys only |
| P5 | Parser `declara el gps … 40 x 40 x 12 mm` → SET `sensors` |
| P6 | Parser kit noun → SET correct kit key when present in components |
| P7 | Parser pair-only on sensors → INCOMPLETE |
| P8 | Parser `respecto` → NONE |
| P9 | Battery + placa principal regression still SET as today |
| P10 | No `library/kit_hardware` / sensors seed gains `length_mm` |

Full suite green. Report the new count.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | allowlist + docstring |
| `src/jarvis/core/declared_envelope_declare_assist.py` | subject resolve for sensors + kit |
| `src/jarvis/core/orchestrator.py` | only if apply/copy needs a tiny touch |
| `tests/test_geometry_declared_sensors_kit_envelope_b1.py` | P1–P10 |
| `library/` / `ui/` / `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_declared_sensors_kit_envelope_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min`:

| Step | Expected |
|---|---|
| `declara el gps 40 x 40 x 12 mm` (or Engineer’s real mm) | sensors box in Board/3D |
| Optional kit declare with **typed** triple | kit box; pin/pitch untouched |
| `cambiar gps` / catalog | identity unchanged; no invented catalog dims |
| Forbidden | GPS box appearing without declare; cable length as box L |

Record [engineer_smoke_geometry_declared_sensors_kit_envelope_b1.md](engineer_smoke_geometry_declared_sensors_kit_envelope_b1.md).

---

## 7. Done when

- [ ] P1–P10 green; full pytest green
- [ ] No library dim seeds; no version bump; #3/#4 not started
- [ ] Report written

---

## Explicitly not this IC

`frame_plate_2` Buy · sourced catalog auto-fill · invent GPS/XT60 mm · multi-hop/visor edits · Conversation Engine · version bump
