# Implementation Contract — Declared battery envelope + Main Plate L×W B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2583** + smoke **ACCEPT**  
**Parents:**
- [engineer_next_geometry_remaining_pieces.md](engineer_next_geometry_remaining_pieces.md) — Engineer overrode “do not mix 3a/3c”; this IC **is** both
- ESC visor rebind **CLOSED** + ACCEPT @ **2573**
- Battery envelope catalog B1 **CLOSED** @ **2316** — `lipo_3s_2200mah` still has **no** L×W×H; **do not** seed it
- Plate L×W investigation **B0** — [review](investigation_review_geometry_plate_lw_sourced_b1.md): Engineer-**declared** Main Plate L×W is the only 3D path for this Rooster; **never** stitch `wheelbase_mm` 230; **never** copy iFlight 202×202
- Pose writer **CLOSED** @ **2456** — origin must be `geometry: box`. After this Buy, Main Plate **may** be an origin (existing writer; no pose-schema change)
- Continuity pose declare **CLOSED** @ **2456** — gate `declara` + `mm` + `respecto`. Envelope phrases **must not** include `respecto`
- Visor X **CLOSED** @ **2562** — **out** (do not retarget stations onto the plate)
- `"cabe"` B1-min **CLOSED** @ **2540**

**Type:** IDLE **declare / clear** of a **box triple** on two families only: `battery` and `frame_plate*`. Writer merges `length_mm` / `width_mm` / `height_mm` with `source=declared`. Projector already draws a box from that triple.  
**Not** catalog seed. **Not** wheelbase-as-box. **Not** auto-pose. **Not** visor-X origin unification. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2573**

**Output:** `.jes/artifacts/implementation_report_geometry_declared_battery_plate_envelope_b1.md`

---

## 0. Engineer Buy (locked)

Live 5min: battery `lipo_3s_2200mah` (energy/mass **cited**, **no** box); `frame_plate` label **Main Plate**, `thickness_mm` **4** (cited), no L×W. Engineer asked **one** IC for both holes. You **do not** invent the millimetres — Continuity writes what the Engineer types. Tests use **fixture** numbers that are **not** 230 and **not** a catalog battery row.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-declared-envelope** — battery **and** Main Plate in one writer + one IDLE parse |
| 2 | Allowed keys | `battery` **or** `is_frame_plate_key(key)` only. **Not** `frame` root, arms, cage, standoff, motors, ESC, FC, kit, sensors |
| 3 | Battery SET | Utterance must name **three** finite mm: L, W, H. Never copy energy/mass into a box. `catalog_ref` / Wh / `mass_g` / `cell_count` **unchanged** |
| 4 | Plate SET | Utterance names **L and W**. Third axis: if the utterance names H, use it; **else** copy that spec’s existing `thickness_mm` into `height_mm` (`source=declared`). If no thickness and no H → INCOMPLETE. **Do not** write `wheelbase_mm`. **Do not** alias `body_*` |
| 5 | Thickness | Plate `thickness_mm` **stays**. Box axis is `height_mm`. Do not delete or overwrite thickness |
| 6 | Source | All three box keys `PropertyValue(..., unit="mm", source="declared")`. Never `catalog` for these writes |
| 7 | Physics | Dims **never** enter `current_parameters` / hover / PASS / `set_battery_component` energy path |
| 8 | Pose / X | **Out** of the writer. After the plate is a box, existing `set_component_declared_box_pose` **must** accept it as origin (add a P-test). Do **not** auto-declare battery pose. Do **not** move visor X onto the plate |
| 9 | Collision | Envelope parse returns **NONE** if `\brespecto\b` (pose owns that). Pose parse unchanged |
| 10 | Version | **No** bump |

**Product sentence:**

```text
Puedo declarar L×W×H de la batería y L×W de la placa Main (alto = grosor
citado 4 mm si no digo H). El visor pinta esas cajas. No es 230 de
wheelbase ni un pack 4S. Aún no unifico la X de hélices con el carbono.
```

**Not:**

```text
seed lipo_3s_2200mah · 230 como L o W · iFlight 202 · sobre en frame root
· pose automática · estaciones visor sobre la placa · Conversation Engine
```

---

## 1. You (Claude)

- Do **not** add `length_mm` to `library/baterias/_datos.json` for `lipo_3s_2200mah` (or any other row).
- Do **not** add L×W to `library/frames/_datos.json` Rooster plates.
- Do **not** read `wheelbase_mm` / `max_stack_height_mm` / `body_*` in this writer or parser.
- Do **not** call `set_battery_component` for this path (energy mirror stays untouched).
- Do **not** change `_geometry_from_spec` box-requires-full-triple.
- Do **not** change visor X / `solidCopyOffsetsMm` / `layoutSolidsRow` math.
- Do **not** mutate `workspace/` (Engineer types live mm).
- Do **not** bump version.
- Full pytest green. `ui/` empty unless a test proves a DTO hole (you must not need it).
- Write the implementation report when done.
- **STOP** if the only way to get a plate box is stitching 230 into L or W.

---

## 2. Intent

```text
IDLE (no respecto):
  "declara la batería 80 x 34 x 22 mm"
  "declara la placa principal 100 x 100 mm"   → H from thickness_mm 4
  "quita el sobre de la batería"
  "quita el sobre de la placa principal"
        ↓
  declared_envelope_declare_assist  (pure parse)
        ↓
  set_component_declared_box_envelope  (merge three keys; CLEAR pops them)
        ↓
  _geometry_from_spec → box
        ↓
  visor solid; plate may be pose origin via existing writer
```

---

## 3. Locked behavior

### 3.1 Writer — `set_component_declared_box_envelope`

New function in `component_writers.py` (same file as pose/mount; **one** write path).

**SET** `(state, key, length_mm, width_mm, height_mm)`:

- Key must exist.
- Key must be `battery` or a frame-plate key. Else `ValueError`.
- All three floats finite and `> 0`.
- Merge into `spec.properties` only those three keys. Preserve `catalog_ref`, `declared_box_pose`, `mounted_on`, name, parent, every other property.
- Return new `ProjectState` (caller saves).

**CLEAR** `(state, key, None)` or dedicated `height_mm=None` clear API: pop `length_mm`/`width_mm`/`height_mm` only. Leave `thickness_mm`. Idempotent if already absent.

Do **not** route battery through `set_battery_component`.

### 3.2 Parser — `declared_envelope_declare_assist.py`

Pure parse. No LLM. Reuse `resolve_component_subject_noun` and `resolve_declared_part_noun` (public wrappers). **Do not** import private `_` names.

**NONE** when:

- no `declara`/`declarar` and not a CLEAR phrase; or
- `\brespecto\b` present (pose); or
- no `A x B [x C] mm` / `A × B [× C] mm` / `A por B por C mm` triple-or-pair

**CLEAR** gate (must not match `quita la pose` / `quita el montaje`):

```text
quita(?:r)?\s+(?:el\s+)?sobre
quita(?:r)?\s+(?:las\s+)?cotas
```

Subject: battery noun **or** plate resolution (below). No subject → NONE for CLEAR (fall through), INCOMPLETE for SET-shaped.

**SET numbers:**

- Three numbers before `mm` → L, W, H in that order (verbatim print order, same N2a as battery catalog envelope).
- Two numbers before `mm` → L, W only (plate path).

Separators: `x`, `×`, `por` (normalized). Comma decimals OK.

**Subject / plate:**

| Phrase token | Resolve |
|---|---|
| battery nouns (existing table) | `battery` |
| exact key `frame_plate` / `frame_plate_2` / … | that key |
| label substring (existing `_label_match`) | unique plate or AMBIGUOUS |
| `\bplaca principal\b` / `\bmain plate\b` | the plate whose label normalizes to **main plate** (live: `frame_plate`). If none / several → AMBIGUOUS / INCOMPLETE |
| bare `placa`/`plate` | same as mount: 2+ plates → AMBIGUOUS with candidates |

Kinds: `SET` | `CLEAR` | `AMBIGUOUS_PLATE` | `INCOMPLETE` | `NONE`.

**INCOMPLETE:** SET-shaped (declara + mm + NxN) but missing subject, or battery with only two numbers, or plate with two numbers and **no** `thickness_mm` on that spec and no third number.

Orchestrator fills plate H from `thickness_mm` **in the writer call**, not by inventing a number in the parser. Parser may return `height_mm=None` for the two-number plate case; apply step reads thickness.

### 3.3 IDLE dispatch

After pose bridge, before FN-005 / FN-014:

```text
IF IDLE:
  parse envelope
  NONE → fall through
  INCOMPLETE / AMBIGUOUS_PLATE → honest message, no LLM
  SET/CLEAR → writer + save
```

Confirm copy: state the three mm and the key. Honesty: `source=declared`. Never `cabe` / `verificado` / `230 de wheelbase` / `ensamblado`.

Plate two-number confirm may say the alto was taken from `thickness_mm` (cited), not newly measured.

### 3.4 Refresh

`refresh_component_from_catalog` on battery must **keep** declared L×W×H when the catalog row still omits them (existing `{**base.properties, **projected}` — add a P-test so a future binder that drops unknown keys fails).

Frame root refresh must **not** strip plate children (already true).

### 3.5 Pose origin (no new pose feature)

After SET on `frame_plate`, `set_component_declared_box_pose(state, "battery", DeclaredBoxPose(origin_key="frame_plate", z_mm=10))` **succeeds**. Before SET it still `ValueError` (not a box). This is the “juntos” payoff. Do not auto-write that pose.

### 3.6 Projector / UI

No `spatial_board.py` / `ui/` change expected. Box triple → existing solid.

---

## 4. Tests

### Python — `tests/test_geometry_declared_battery_plate_envelope_b1.py`

Fixture numbers (**forbidden** as catalog claims): battery **80 / 34 / 22**; plate **100 / 100** (H from thickness **4**). Never 230, never 202, never 138.5.

| ID | Behavior |
|---|---|
| P1 | Parse+write battery 80×34×22 on a `lipo_3s_2200mah` spec → properties those three, `source=declared`; `catalog_ref` still that SKU; Wh/mass/cells unchanged; projector `geometry` box 80/34/22 |
| P2 | Parse+write `declara la placa principal 100 x 100 mm` on live-shaped Main Plate (`thickness_mm=4`, label Main Plate) → L=100 W=100 `height_mm=4`; `thickness_mm` still 4; `wheelbase` on **frame** still 230 if present; projector box 100/100/4; **one** plate node |
| P3 | Two-number phrase on **battery** → INCOMPLETE; no write |
| P4 | Bare `declara la placa 100 x 100 mm` with **two** plates → AMBIGUOUS_PLATE; no write |
| P5 | CLEAR battery pops only the three box keys; energy fields remain |
| P6 | Writer SET on `frame` / `motors` → `ValueError`; no geometry invented on frame root |
| P7 | After P2, `set_component_declared_box_pose` battery vs `frame_plate` **succeeds**; before P2 it raises |
| P8 | Phrase with `respecto` → envelope parse NONE (pose still owns it) |
| P9 | `refresh_component_from_catalog` battery after P1 → L×W×H still 80/34/22 |
| P10 | IDLE orchestrator: SET battery phrase saves; `cambiar batería` still opens battery catalog (B3 regression, one check) |

Do **not** delete battery-envelope / plate-B0 / pose / visor-X tests.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | new parser |
| `src/jarvis/core/component_writers.py` | `set_component_declared_box_envelope` |
| `src/jarvis/core/orchestrator.py` | IDLE bridge after pose |
| `tests/test_geometry_declared_battery_plate_envelope_b1.py` | P1–P10 |
| `library/` | **empty** |
| `ui/` | **empty** |
| `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_declared_battery_plate_envelope_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min`. **You type the millimetres** (not the test fixtures unless you choose them).

| Step | Expected |
|---|---|
| `declara la batería <L> x <W> x <H> mm` | Card battery: three mm, SKU still `lipo_3s_2200mah`, Wh/mass unchanged; 3D **box** |
| `declara la placa principal <L> x <W> mm` | Card Main Plate: L×W; alto 4 if you omitted H; thickness 4 remains; frame wheelbase still **230**; 3D **box**. Not an X of motors |
| Optional | `declara la batería a … mm respecto a frame_plate` — now legal **because** the plate is a box. Not required to ACCEPT this Buy |
| Forbidden tell | 3D plate size equals 230 **only if you typed 230**. If you did not, that is a **fail** |

Record [engineer_smoke_geometry_declared_battery_plate_envelope_b1.md](engineer_smoke_geometry_declared_battery_plate_envelope_b1.md) after review.

---

## 7. Done when

- [ ] P1–P10 green; full pytest green
- [ ] Library battery/frame seeds unchanged
- [ ] No visor-X edit; no version bump
- [ ] Report written

---

## Explicitly not this IC

Seed `lipo_3s_2200mah` dims · Rooster catalog L×W · wheelbase→box · iFlight 202 on Rooster · envelope on `frame` root · auto-pose · visor X retarget · kit/sensors boxes · Conversation Engine · version bump
