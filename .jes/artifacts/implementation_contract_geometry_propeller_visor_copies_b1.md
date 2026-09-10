# Implementation Contract — Propeller visor copies from motors spec `motor_count` B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2550** + smoke **ACCEPT**  
**Parents:**
- [investigation_review_geometry_quadrotor_kit_in_space_b0.md](investigation_review_geometry_quadrotor_kit_in_space_b0.md) **PASS WITH NOTES** · N1–N5
- [investigation_report_geometry_quadrotor_kit_in_space_b0.md](investigation_report_geometry_quadrotor_kit_in_space_b0.md)
- Motor visor copies B1 **CLOSED** @ **2473** — same N SoT, pose stripped, **this IC extends copies to propellers**
- `"cabe"` B1-min **CLOSED** @ **2540** — **out**
- Pose origin = box **CLOSED** @ **2456** / **2462** — **do not reopen** (disk-origin parked)
- Plate L×W **B0** — Rooster still no box (**out**)

**Type:** Projector **additive DTO** on the **one** `propellers` node: `solidCopies = N` from the **motors spec** `motor_count`. Visor already expands any node with `solidCopies` (`expandSolidCopies`).  
**Not** millimetre stations. **Not** a disk pose origin. **Not** N `ComponentSpec` / N cards / N BOM hélices. **Not** a motor Ø seed. **Not** remaining pieces (battery, sensors, kit).

**Baseline:** package **`0.3.8`** · suite **2540**

**Output:** `.jes/artifacts/implementation_report_geometry_propeller_visor_copies_b1.md`

---

## 0. Engineer Buy (locked)

Engineer ★ **`B1-copies-prop`** after investigation review. Product B first slice: N hélices in the **row**, not “en el espacio.”

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-copies-prop** — propeller visor copies only |
| 2 | Count SoT | **Same N as `_solid_copies` would use for motors:** `components["motors"].properties["motor_count"].value`. **Never** `current_parameters.motor_count` (BOM `_bom_quantity` stays params-first; **do not change it**). **Never** default 4. **Never** `configuration=quad_x`. **Never** a `propeller_count` field |
| 3 | Geometry gate | Emit propeller `solidCopies` only if `_geometry_from_spec(propellers)` is not `None`. Live both demos: Ø127 disk → copies **are** the smoke. Motors may still have **no** Ø — motors stay at zero solids (existing gate). **Independent** geometry: props copies do **not** require motor geometry |
| 4 | Range | Same as motors copies: omit unless `N` is a whole number and `2 <= N <= 16`. `1` / missing / `3.5` / out of range → omit key (visor shows 0 or 1 propeller solid from geometry alone) |
| 5 | Cards / BOM | Still **one** `propellers` card. Click any copy → `onSelect("propellers")`. Still one BOM hélice line |
| 6 | Layout | Existing presentation **row**. Pose on copies stays **stripped** (U3). **Not** X of 230. **Not** hélice-on-motor pose |
| 7 | Motors copies | Unchanged. Do not seed `emax_rs2205_2300.diameter_mm` from `emax_rs2205s_2300` |
| 8 | `ui/` | **No behavior change required.** `expandSolidCopies` is already key-agnostic. Optional: comment + one test that a `propellers` node expands. **Forbidden:** special-case `id === "motors"`, compose pose onto copies, invent stations |
| 9 | Version | **No** bump |

**Product sentence:**

```text
El visor muestra N discos de hélices, N = motor_count del spec de motors
(el mismo N que ya usa el visor de motores). Una card. Sin pose. Sin mm.
Los motores siguen invisibles si el SKU no tiene Ø. Aún no es un quadrotor.
```

**Not:**

```text
Cuatro hélices en X de 230 · pose hélice respecto a motor · Ø copiado del
EMAX con “s” · N cards · current_parameters manda · quad_x implica 4
```

---

## 1. You (Claude)

- Do **not** invent motor `diameter_mm` / copy the S-sibling Ø / invent Rooster L×W.
- Do **not** create `propellers_2` … ComponentSpecs or extra cards.
- Do **not** place copies using wheelbase, `mountedOn`, card `x/y`, or `quad_x` corners.
- Do **not** declare pose on hélices or loosen the disk-origin writer gate.
- Do **not** default N=4 when `motor_count` is missing.
- Do **not** read `current_parameters` for this DTO.
- Do **not** change `_bom_quantity`.
- Do **not** emit `solidCopies` on FC, ESC, frame, battery, sensors, kit, slots.
- Do **not** bump package version. Do **not** un-QUEUE fit. Do **not** mutate `workspace/`.
- Full pytest green. If you touch `ui/spatial-board`, `npm test && npm run typecheck`. If `ui/` is comment-only / new test only, still run those.
- **Amend** `tests/test_geometry_motor_count_instances_b1.py` **P1**: it currently asserts `"solidCopies" not in nodes["propellers"]` with a propeller **disk** in the fixture. After this Buy that assertion is **wrong**. Expect `solidCopies == 3` on propellers in that fixture (same N). Do **not** delete P2–P7.
- Write the implementation report when done.
- **Stop** if you need stations, a disk origin, or a catalog Ø to “see motors.” That is outside this IC.

---

## 2. Intent

```text
ComponentSpec motors.motor_count  (spec only)
        +
ComponentSpec propellers + existing propeller geometry DTO
        ↓
projector: optional solidCopies = N on the propellers node
          (only if propeller geometry and 2 ≤ N ≤ 16)
        ↓
existing expandSolidCopies → N layout ids, one selectId "propellers"
        ↓
row slots; click → the one hélices card
```

2D world unchanged: one propellers card, existing `mountedOn=motors` text/edge.

Motors node: still `_solid_copies` from **its own** spec + **its own** geometry (live: omit).

---

## 3. Locked behavior

### 3.1 Count (extend `_solid_copies`)

`place` already has `components`. Pass them in:

```text
_solid_copies(spec, components)
```

**Motors** (`suggested_key == "motors"`): **byte-identical** to today — count from **this** spec’s `motor_count`; require **this** spec’s geometry.

**Propellers** (`suggested_key == "propellers"`):

1. `_geometry_from_spec(spec)` is not `None` (the **propellers** spec)
2. `motors = components.get("motors")` exists
3. Parse `motors.properties["motor_count"].value` with the **same** rules as motors copies (`float` → integer, `2 <= N <= 16`)
4. Else omit

Missing motors key, missing `motor_count`, `1`, `0`, `3.5`, `None`, `>16` → omit propeller `solidCopies`.

**Never** substitute 4. **Never** read frame `configuration`. **Never** read `current_parameters`. **Never** read a property on the propellers spec as the count.

Extract a tiny shared parser for the integer range if that avoids duplicating the `float`/`is_integer` gate. Do not invent a new public API.

### 3.2 Projector DTO

Additive optional `solidCopies?: number` on the **propellers** node, same key motors already use.

Omit the key when §3.1 is `None`.

Live census after this Buy (do not mutate workspace to get it):

| Project | motors `solidCopies` | propellers `solidCopies` |
|---|---|---|
| `autonomía-de-5min` | omitted (no motor Ø) | **4** (Ø127 + spec `motor_count` 4) |
| `autonomía-de-10min` | omitted (no motor Ø) | **3** (Ø127 + spec `motor_count` 3) |

### 3.3 Visor

No new layout path. Copies remain unposed row occupants. `selectId` stays the node id.

If you add a UI test: a node `{ id: "propellers", solidCopies: 4, geometry: disk }` → `propellers#0..#3`, all `selectId "propellers"`, pose stripped.

### 3.4 Copy

No `"cabe"`, `"ensamblado"`, `"quatro motores"`, `"X de 230"`, `"quadrotor"` in new UI strings.

---

## 4. Tests

### Python — `tests/test_geometry_propeller_visor_copies_b1.py`

Use `project_spatial_nodes`. Prop disk via `diameter_in` 5 (Ø127) or `diameter_mm` 127 — either is a real geometry path already in production.

| ID | Behavior |
|---|---|
| P1 | motors `motor_count=3` **without** Ø + prop disk → motors no `geometry` / no `solidCopies`; propellers `geometry` present and `solidCopies === 3`. **One** node `id=="propellers"` |
| P2 | motors disk + `motor_count=3` + prop disk → **both** `solidCopies === 3` |
| P3 | motors disk + `motor_count=3` + prop **without** diameter → motors `solidCopies === 3`; propellers no `geometry`, no `solidCopies` |
| P4 | no `motor_count` + prop disk → propellers has `geometry`, **no** `solidCopies` |
| P5 | `motor_count=4` + prop disk → propellers `solidCopies === 4` (4 allowed **when the spec has 4**, not as a default) |
| P6 | frame `configuration=quad_x` + motors `motor_count=3` + prop disk → propellers `solidCopies === 3` |
| P7 | `motor_count=1` + prop disk → no `solidCopies` on propellers |
| P8 | `motor_count=3.5` + prop disk → no `solidCopies` on propellers |
| P9 | `current_parameters.motor_count=4` + motors spec `motor_count=3` + prop disk → propellers `solidCopies === 3` (params must **not** win) |
| P10 | no `motors` component + prop disk → no `solidCopies` on propellers |

### Existing — `tests/test_geometry_motor_count_instances_b1.py`

| ID | Change |
|---|---|
| P1 | **Amend:** with the fixture’s propeller disk, expect `nodes["propellers"]["solidCopies"] == 3`. Keep motors `solidCopies === 3` and one `id=="motors"` |

P2–P7 stay. P2 does not assert on propellers (motors still omit copies without Ø).

### UI — only if you touch `ui/` or add U5

Existing U1–U4 stay green. Optional U5: `id: "propellers"` + `solidCopies: 4` expands like motors.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `_solid_copies(spec, components)`; propellers branch; shared count parse |
| `tests/test_geometry_propeller_visor_copies_b1.py` | P1–P10 |
| `tests/test_geometry_motor_count_instances_b1.py` | P1 assertion amend |
| `ui/spatial-board/src/scene3dLayout.ts` | **optional** comment only |
| `ui/spatial-board/src/scene3dLayout.test.ts` | **optional** U5 |
| `.jes/artifacts/implementation_report_geometry_propeller_visor_copies_b1.md` | write |

`ui/` may stay empty of behavior. `library/` empty. `workspace/` empty. `project_closure.py` empty.

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min` **and** `autonomía-de-10min` (`jarvis board`):

| Step | Expected |
|---|---|
| Card `propellers` | still **one** card; disk Ø127 |
| 3D pane 5min | **4** propeller disks in the **row** (not an X) |
| 3D pane 10min | **3** propeller disks in the row |
| Card `motors` | still one card; **no** new motor solids (SKU still has no Ø) |
| Click any hélice solid | the **one** hélices card |
| Frame card | still no box; `wheelbase_mm` unused by this Buy |

Motors remaining invisible is **ACCEPT**, not a bug.

Record [engineer_smoke_geometry_propeller_visor_copies_b1.md](engineer_smoke_geometry_propeller_visor_copies_b1.md) after review.

---

## 7. Done when

- [ ] P1–P10 green; motor-copies P1 amended and green; P2–P7 still green
- [ ] Full pytest green; UI tests + typecheck green if `ui/` touched
- [ ] Live census: 5min 4 hélices / 10min 3 hélices; 0 motor solids; 1 card each
- [ ] No version bump; no catalog Ø; fit still QUEUED
- [ ] Report written

---

## Explicitly not this IC

Stations / per-copy pose array · disk-origin writer · seed `emax_rs2205_2300` Ø · default 4 · quad-X / wheelbase placement · cylinder · N BOM hélices · `_bom_quantity` change · `"cabe"` on disks · remaining pieces (battery, sensors, kit) · Three.js · Conversation Engine · version bump
