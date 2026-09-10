# Implementation Contract — Live motor visor via sourced SKU rebind B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2555** · live smoke folded into stations IC  
**Parents:**
- [engineer_next_geometry_motors_then_stations.md](engineer_next_geometry_motors_then_stations.md) — sequence ★1 then ★2
- Hélices visor copies **CLOSED** + ACCEPT @ **2550**
- Motor visor copies **CLOSED** @ **2473** — N from spec `motor_count`; geometry gate already live
- Motor envelope N2 / height cited **CLOSED** — `emax_rs2205_2300` ≠ `emax_rs2205s_2300`; Ø/height live **only** on the S row
- Idle catalog rebind B3 **CLOSED** — `cambiar motor` already reopens the motor catalog
- `set_motor_component` Bug78/FN-007 — preserves `motor_count` when the new spec omits it
- Stations / disk-origin / remaining pieces — **out** (★2 after this smoke)

**Type:** Glue the **already-shipped** bind + copies path so the sourced RaceSpec SKU produces N motor disks. Prefer **no `src/` / `library/` edit**.  
**Not** seeding Ø on `emax_rs2205_2300`. **Not** a cylinder. **Not** millimetre stations. **Not** N motor cards.

**Baseline:** package **`0.3.8`** · suite **2550**

**Output:** `.jes/artifacts/implementation_report_geometry_motor_visor_rebind_b1.md`

---

## 0. Engineer Buy (locked)

Engineer ★ sequence “ver motores, después juntar en el espacio”, then “redacta ic”. This IC is **★1 only**.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-rebind** — bind `emax_rs2205s_2300` (sourced Ø 27.9). Existing `_solid_copies` draws N motor disks |
| 2 | Identity | Do **not** copy 27.9 / 31.7 onto `emax_rs2205_2300`. Do **not** merge the two library rows |
| 3 | Count | After rebind, spec `motor_count` stays the project’s N (Bug78). 5min→**4**, 10min→**3**. Never default 4 |
| 4 | Solid | Disk from `diameter_mm` 27.9. `height_mm` 31.7 stays a **card field**. Ø+height **never** a cylinder |
| 5 | Cards | Still **one** `motors` card. Click any motor copy → that card |
| 6 | Layout | Presentation **row**, pose stripped. **Not** X of 230 |
| 7 | Physics | Rebind **does** change live numbers (S row thrust / no nameplate `max_watts`). That is **ACCEPT**, not a bug this Buy. Do not invent W on the S SKU |
| 8 | `src/` | **Empty unless** a named test below fails on the current bind→writer→projector seam. Then the smallest fix that preserves `motor_count` + projects S-row dims — **stop** if the fix is seeding the mute SKU or stations |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Tras cambiar el motor al RaceSpec citado (emax_rs2205s_2300), el visor
muestra N discos motor, N = motor_count del spec, más N discos hélice.
Una card cada uno. Fila, no X. Aún no es un quadrotor en milímetros.
```

**Not:**

```text
Ø copiado al SKU sin “s” · cilindro 31.7 · estaciones · default 4
```

---

## 1. You (Claude)

- Do **not** add `diameter_mm` / `height_mm` to `emax_rs2205_2300`.
- Do **not** mutate `workspace/` (Engineer smoke does the live rebind).
- Do **not** implement stations, disk-origin, cylinder, `"cabe"` on disks.
- Do **not** change `_bom_quantity`. Do **not** bump version.
- Prefer **tests + report only**. Touch `src/` only if P1–P5 cannot pass without a seam fix.
- Full pytest green. `ui/` empty unless you must (you must not).
- Write the implementation report when done.

---

## 2. Intent

```text
IDLE "cambiar motor" (already ships)
        → pick emax_rs2205s_2300
        → bind_motor_from_catalog (+ set_motor_component keeps motor_count)
        → spec.diameter_mm = 27.9, spec.motor_count = N
        → _geometry_from_spec = disk 27.9
        → _solid_copies = N   (existing motors branch)
        → visor row of N motor disks + existing N propeller disks
```

No new DTO key. No new visor layout.

---

## 3. Locked behavior

### 3.1 Library (unchanged)

| SKU | `diameter_mm` |
|---|---|
| `emax_rs2205s_2300` | **27.9** (already cited) |
| `emax_rs2205_2300` | still **absent** |

### 3.2 Bind → visor

`bind_motor_from_catalog(motor_spec_to_suggestion(S-row), base=spec_with_motor_count)` **or** `bind` without count then `set_motor_component` (Bug78) must yield a spec that `project_spatial_nodes` turns into:

- `geometry == {shape: disk, diameter_mm: 27.9}`
- `solidCopies == N` when `2 <= N <= 16`
- `fields` include `height_mm` 31.7 mm
- **one** node `id=="motors"`

Mute SKU bind still: no `geometry`, no `solidCopies`.

### 3.3 Copy / layout

No new UI strings. No `"quadrotor"`, `"cabe"`, `"X de 230"` in new copy.

---

## 4. Tests

### Python — `tests/test_geometry_motor_visor_rebind_b1.py`

Use real `default_library` + `bind_motor_from_catalog` + `motor_spec_to_suggestion` + `set_motor_component` + `project_spatial_nodes`. Include a propeller disk (Ø127 / `diameter_in` 5) so hélices copies stay in the picture.

| ID | Behavior |
|---|---|
| P1 | Bind **S** SKU + `set_motor_component` on a state whose motors spec is mute SKU with `motor_count=4` + prop disk → motors `geometry` disk 27.9, `solidCopies === 4`, `catalog_ref.sku == "emax_rs2205s_2300"`; still one motors node; propellers still `solidCopies === 4`; geometry still **disk** (not box/cylinder) |
| P2 | Same with `motor_count=3` → motors `solidCopies === 3` (10min-shaped; not coerced to 4) |
| P3 | Bind mute `emax_rs2205_2300` + `motor_count=4` + prop disk → motors **no** `geometry`, **no** `solidCopies`; propellers still 4 |
| P4 | Library: `get_motor("emax_rs2205_2300").diameter_mm` is None; S-row still 27.9 |
| P5 | `height_mm` 31.7 is a **field** on the motors node after P1 bind; `geometry.shape == "disk"` |

Do **not** delete motor-copies / height-cited tests.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `tests/test_geometry_motor_visor_rebind_b1.py` | P1–P5 |
| `src/` | **omit** unless a P-test proves a seam |
| `library/` | **empty** |
| `ui/` | **empty** |
| `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_motor_visor_rebind_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min` **and** `autonomía-de-10min`, architecture already closed (`cambiar motor` IDLE rebind B3):

| Step | Expected |
|---|---|
| `cambiar motor` | motor catalog offer (existing) |
| Pick `emax_rs2205s_2300` / RaceSpec | bind that SKU; `motor_count` unchanged |
| Card `motors` | one card; Ø 27.9; `height_mm` 31.7 text; SKU with **s** |
| 3D 5min | **4** motor disks **and** **4** hélice disks, **row**, not an X |
| 3D 10min | **3** + **3**, row |
| Hover / W | may change / `max_watts` may stay null on this SKU — **ACCEPT** |

Mute SKU remaining invisible **before** the pick is still correct.

Record [engineer_smoke_geometry_motor_visor_rebind_b1.md](engineer_smoke_geometry_motor_visor_rebind_b1.md) after review.

---

## 7. Done when

- [ ] P1–P5 green; full pytest green
- [ ] Mute SKU still has no library Ø
- [ ] No version bump; no stations; no cylinder
- [ ] Report written

---

## Explicitly not this IC

Seed `emax_rs2205_2300` Ø · merge the two EMAX rows · stations / disk-origin · cylinder · default-4 · invent `max_watts` on the S SKU · remaining pieces · Conversation Engine · version bump
