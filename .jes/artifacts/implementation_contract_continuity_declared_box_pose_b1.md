# Implementation Contract — Continuity declared box-local pose B1 (CLI / IDLE)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2456**) + Engineer **ACCEPT**  
**Parents:**
- [investigation_review_continuity_declared_box_pose_b1.md](investigation_review_continuity_declared_box_pose_b1.md) — **PASS WITH NOTES** · lean **B1**
- [investigation_report_continuity_declared_box_pose_b1.md](investigation_report_continuity_declared_box_pose_b1.md)
- Writer already CLOSED: [implementation_contract_geometry_pose_declared_box_frame_b1.md](implementation_contract_geometry_pose_declared_box_frame_b1.md) @ suite **2438**
- Precedent: [implementation_contract_continuity_mounted_on_declare_b1.md](implementation_contract_continuity_mounted_on_declare_b1.md) @ **2380**
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- Airframe pose stub — **still DEFERRED**
- Scene3D-from-pose — **later ★** (not this Buy)
- Class A envelope search — **parallel later ★** (not this Buy; not an in-product crawler)

**Type:** User-facing **declare / clear** path for `declared_box_pose` already stored by `set_component_declared_box_pose`.  
**Not** Scene3D placement. **Not** `"cabe"`. **Not** LLM parse. **Not** plate L×W. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2438**

**Output:** `.jes/artifacts/implementation_report_continuity_declared_box_pose_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1 Continuity declare/clear** | YES |
| 2 | Reuse writer | **Only** `set_component_declared_box_pose` — no second write path; do **not** duplicate box/self/missing checks in the parser |
| 3 | Mode | **IDLE** + active project |
| 4 | Gate | SET requires **all three**: `declara`/`declarar` + `\bmm\b` + `respecto`. Do **not** use `fija` (already mount) |
| 5 | Axes | Tokens `x`/`y`/`z` and `largo`/`ancho`/`alto` only. **Forbidden:** adelante, atrás, arriba, abajo, izquierda, derecha, morro, gravedad |
| 6 | Replace-whole | Writer replaces the entire `DeclaredBoxPose`. One utterance must name **every** axis the user wants set; omitted axes store `None` (not a merge with a previous pose) |
| 7 | IDLE order | `mounted_on` → catalog refresh → **this pose bridge** → FN-005 → **FN-014**. Pose **before** FN-014 is load-bearing |
| 8 | Copy | Confirm with `POSE_AXES_HONESTY_LABEL` **verbatim**. Never ensamblado / cabe / verificado / morro / posición real |
| 9 | Scene3D / fit / version | **Out** / QUEUED / **no bump** |

**Honest product sentence:**

```text
Puedo declarar en el chat un desplazamiento en milímetros respecto al centro
de una caja ya medida (ejes locales declarados L→+X, W→+Y, H→+Z) y verlo
en la card. Eso no es el morro del drone ni “cabe.”
```

---

## 1. You

- Do **not** move `Scene3D` / `layoutSolidsRow` / CSS 3D solids.
- Do **not** change `set_component_declared_box_pose` validation rules (call it; don’t fork it).
- Do **not** infer origin from `mounted_on` or Board x/y.
- Do **not** accept directional synonyms (`adelante`/`arriba`…).
- Do **not** import `_SUBJECT_PATTERNS` / `_resolve_target` as private API. **Promote** thin public wrappers on `mounted_on_declare_assist.py` (behavior unchanged) and import those from the new pose assist. Do not copy the plate-ambiguity rule.
- Do **not** bump package version. Do not weaken tests.
- Full pytest. Prefer **no** `ui/` change (cards already render `fields`).
- Write the implementation report when done.

---

## 2. Intent

```text
IDLE + active project:
  "declara el esc a 5 mm en x respecto al fc"
  "declara el esc a 5 mm en x y -2 mm en z respecto al fc"
  "quita la pose del esc"
        ↓
  pure parse → SET | CLEAR | AMBIGUOUS_ORIGIN | INCOMPLETE | NONE
        ↓
  SET/CLEAR → set_component_declared_box_pose(...) + save
  writer ValueError → surface message (shapeless/disk/self/missing)
        ↓
  Board already shows origen pose / ejes pose / Δx mm
```

Canonical SET family (one family, not a language):

```text
declara[r] <subject> a <N> mm en <eje> [y <N> mm en <eje> …] respecto a[l] <origin>
```

CLEAR family:

```text
quita[r] [la] pose [de[l] <subject>]
```

---

## 3. Locked behavior

### 3.1 Pure assist module (new)

New file: `src/jarvis/core/declared_box_pose_declare_assist.py`

Mirror `mounted_on_declare_assist` thinness: deterministic parse, **no LLM**, **no mutation**.

```text
parse_declared_box_pose_declare(user_input, components) -> PoseDeclareResult
```

| Kind | Meaning |
|---|---|
| `SET` | `component_key`, `origin_key`, `x_mm`/`y_mm`/`z_mm` (each `float \| None`; **at least one** axis set) |
| `CLEAR` | `component_key` |
| `AMBIGUOUS_ORIGIN` | subject resolved; origin not uniquely resolved — `candidates` like mount plates; **no write** |
| `INCOMPLETE` | gate matched (`declara`+`mm`+`respecto`) but no axis token / no subject — **no write** (must **not** be `NONE`, or FN-014 steals) |
| `NONE` | not a pose declare/clear |

**Normalization:** `_normalize_help` (accents), same as mount.

**SET gate (all required):**

- `declara` or `declarar` (word boundary)
- `\bmm\b`
- `respecto`

**CLEAR gate:** `quita`/`quitar` + `pose` (mirrors `quita el montaje`). Must **not** match `quita el montaje`.

**Forbidden gates:** `fija` / `fijar`. Pose parser must return `NONE` for `"fija el esc en la placa"` (mount owns it → live demo `AMBIGUOUS_TARGET`, not SET).

### 3.2 Subject / origin segments

- Subject: text **before** the first `respecto` (SET) or whole phrase (CLEAR).
- Origin: text **after** the first `respecto`.
- Do **not** split on `en` (the axis clause is `en x` / `en largo`).

Subject nouns: same six keys as mount (`flight_controller`, `esc`, `motors`, `battery`, `sensors`, `propellers`) via the **public** subject helper.

Origin: public part-noun helper (exact key + plate labels + arm/cage/standoff/frame + component aliases). Then writer rejects non-box. Parser does **not** pre-check `_geometry_from_spec`.

If origin noun missing / unresolved → `AMBIGUOUS_ORIGIN` with empty `candidates` (honest; not `NONE`).

If bare `placa` and 2+ plates → `AMBIGUOUS_ORIGIN` with the same candidate tuples mount uses — **no write**.

### 3.3 Axis parse (replace-whole)

Map: `x`/`largo` → `x_mm`; `y`/`ancho` → `y_mm`; `z`/`alto` → `z_mm`.

Find all `(-?\d+(?:[.,]\d+)?)\s*mm\s+en\s+(x|y|z|largo|ancho|alto)` in the **normalized** phrase. Last token wins if the same axis is repeated.

Omitted axes → `None` on the new `DeclaredBoxPose` (clears any previous value on that axis because the writer replaces the object).

Zero axis matches after SET gate → `INCOMPLETE`.

### 3.4 Public helpers on mount assist (tiny, behavior-preserving)

In `mounted_on_declare_assist.py`, export without changing parse results of existing tests:

```text
resolve_component_subject_noun(normalized) -> str | None
     # today's _resolve_subject

resolve_declared_part_noun(normalized, components) -> str | MountDeclareResult | None
     # today's _resolve_target
```

Pose assist imports **only** these (plus `_normalize_help` if already the shared catalog helper — prefer `jarvis.core.motor_catalog_assist._normalize_help` like mount does, not a new normalizer).

### 3.5 Orchestrator IDLE dispatch (order locked)

In `_handle_user_text_inner` (or equivalent), **after** `_try_handle_catalog_refresh` and **before** FN-005 `is_help_choose_phrase`:

```text
IF IDLE and active project:
  pose_result = parse_declared_box_pose_declare(...)
  IF NONE: fall through  # "declarar el esc" / "declarar batería" must reach FN-014
  IF AMBIGUOUS_ORIGIN: interactive list; no write
  IF INCOMPLETE: error/interactive “indica sujeto y eje (x/y/z o largo/ancho/alto)”; no write
  IF subject key not in components: honest “aún no declarado”; no write
  IF SET: DeclaredBoxPose(...) → set_component_declared_box_pose → save
  IF CLEAR: set_component_declared_box_pose(..., None) → save
  IF ValueError: surface writer message (e.g. frame_plate / motors origin)
```

Stay **IDLE** after success.

**Regression:** `"declarar el esc"` and `"declarar batería"` must still be FN-014/acquisition (pose `NONE`). `"esc montado en frame_plate"` still mount (pose `NONE`). `"cambiar frame"` still catalog rebind.

### 3.6 Confirmation copy (locked honesty)

SET (wording flexible except the honesty line, which is **verbatim**):

```text
Declarado: esc a 5 mm en x respecto a flight_controller.
Ejes: locales declarados (L→+X, W→+Y, H→+Z); no morro; no gravedad.
```

Second line = `Ejes: ` + `POSE_AXES_HONESTY_LABEL` (import from `spatial_board`).

CLEAR:

```text
Pose declarada de esc eliminada.
```

**Forbidden in any new string:** ensamblado, cabe, verificado, morro, adelante, posición real, gravedad as a claim (the honesty label’s “no gravedad” is the only allowed occurrence).

### 3.7 Schema / Board / visor

**No** schema change. **No** Board projector change. **No** `ui/` change. After persist, `project_spatial_nodes` already emits `origen pose` / `ejes pose` / `Δx mm`.

---

## 4. Tests (required)

New file: `tests/test_continuity_declared_box_pose_b1.py`

Fixtures: ESC + FC with full L×W×H (copy `_fc_spec` from `test_geometry_pose_declared_box_frame_b1.py`); include `frame_plate` shapeless and `motors` disk when testing writer errors. Orchestrator helper: same pattern as `test_continuity_mounted_on_declare_b1.py` (`_RefuseLLM`, `_project_with_components`).

| # | Case |
|---|---|
| T1 | Parse SET: `"declara el esc a 5 mm en x respecto al fc"` → `esc`, origin `flight_controller`, `x_mm=5`, y/z `None` |
| T2 | Parse SET multi-axis: `"declara el esc a 5 mm en x y -2 mm en z respecto al fc"` → x=5, z=-2, y `None` |
| T3 | Parse CLEAR: `"quita la pose del esc"` |
| T4 | Pose `NONE`: `"esc montado en frame_plate"` |
| T5 | Pose `NONE`: `"fija el esc en la placa"` (mount owns `fija`; do **not** assert mount SET — demo is `AMBIGUOUS_TARGET`) |
| T6 | Pose `NONE`: `"declarar el esc"`, `"declarar batería"`, `"por que no puedo montar el dron"` |
| T7 | Pose `NONE`: `"quita el montaje del esc"` |
| T8 | Parse SET origin plate: `"declara los motores a 3 mm en x respecto a frame_plate"` → SET at parse; orchestrator surfaces writer `ValueError` (no persist) |
| T9 | Orchestrator IDLE happy path: phrase T1 persists `declared_box_pose`; message contains `Declarado` + verbatim honesty label; Board fields `origen pose` / `Δx mm`; no `ensamblado`/`cabe` |
| T10 | Orchestrator CLEAR after T9 |
| T11 | Orchestrator: `"declarar el esc"` still acquisition-shaped (not a pose persist; must **not** set `declared_box_pose`) |
| T12 | Non-regression: `"cambiar frame"` still works (same assert family as mount T9) |

Existing `tests/test_continuity_mounted_on_declare_b1.py` must stay green (public wrappers must not change mount parse).

Run full suite; report count (expect **2438 + new tests**).

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/declared_box_pose_declare_assist.py` | **new** — pure parse |
| `src/jarvis/core/mounted_on_declare_assist.py` | public wrappers only; **no** parse-behavior change |
| `src/jarvis/core/orchestrator.py` | IDLE pose bridge **after refresh, before FN-005** |
| `tests/test_continuity_declared_box_pose_b1.py` | **new** |
| `.jes/artifacts/implementation_report_continuity_declared_box_pose_b1.md` | write |

**Do not change:** `set_component_declared_box_pose` rules · `Scene3D.tsx` · `scene3dLayout.ts` · seeds · fit stub · package version · demo `state.json` (tests use tmp projects)

---

## 6. Explicit non-goals

Scene3D placement · fit/`cabe` · arm individuation · plate L×W invention · airframe +X · LLM millimetre parse · in-product web search · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [ ] IDLE SET/CLEAR persist via existing writer  
- [ ] Gate collision tests T4–T7; FN-014 T11  
- [ ] Shapeless origin surfaces writer error (T8)  
- [ ] Honesty label verbatim in confirm  
- [ ] `ui/` 3D files unchanged (`git diff -- ui/spatial-board/src/Scene3D.tsx ui/spatial-board/src/scene3dLayout.ts` empty)  
- [ ] Full pytest green; count reported  
- [ ] Report written  
- [ ] Cursor review next  

---

## 8. Stop conditions

Stop and ask before: moving 3D solids; merging pose into `mounted_on`; adding `adelante`/`arriba`; placing this bridge after FN-014; opening fit; bumping version.
