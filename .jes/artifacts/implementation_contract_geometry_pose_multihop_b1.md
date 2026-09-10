# Implementation Contract — Pose multi-hop composition B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer ★ “procede con los 4 en orden” → step **1 of 4**  
**Parents:**
- [Work order](engineer_next_geometry_remaining_pieces.md) — #1 multi-hop · #2 sensors/kit · #3 plate_2 · #4 sourced dims
- Scene3D-from-pose **CLOSED** @ **2462** — **single-level** (origin = row slot / root); chain deferred
- Visor assembly root **CLOSED** + ACCEPT — `frame_plate` box at world 0; pose vs root from world center
- Live 5min: ESC `5/0/0` vs FC; FC `0/0/8` vs plate; ESC visually “raro” because it anchors to FC’s **row slot**, not FC’s posed center

**Type:** Visor-only composition in `layoutSolidsFromPose` (+ tests). Prefer **no** Python DTO / writer change.  
**Not** sensors/kit envelopes. **Not** `frame_plate_2` Buy. **Not** sourced auto-fill. **Not** inventing mm. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2583** (assembly-root era; confirm live count in report)

**Output:** `.jes/artifacts/implementation_report_geometry_pose_multihop_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-multihop** — compose declared-box poses along the origin chain |
| 2 | Composition | Child center = **laid center of origin** + Δmm (same axis remap as today). If the origin is itself posed (and its origin is a box), use the origin’s **composed** center — not its row slot |
| 3 | Assembly root | Unchanged: active `frame_plate` box still world 0. A pose whose chain reaches the root measures from that world center |
| 4 | Cycle | If walking `originKey` revisits an id → **break**: use that id’s **row-slot center** (or world 0 if it is the active root). No throw; solid must not vanish |
| 5 | Missing / not-box mid-chain | Same as today: that hop fails → item keeps its **own** row slot (`originY=originZ=0`) |
| 6 | `offsetMm` stations | **Never** enter the pose chain. Still absolute around world 0. Copies still strip `declaredBoxPose` |
| 7 | Depth | No artificial max beyond cycle detection (live depth 2 is enough; chains of 3+ must work in tests) |
| 8 | Python / writer | **No** change to pose writer, envelope writer, or projector DTO |
| 9 | N1 tidy / root skip | Keep assembly-root row filter (root + `offsetMm` out of row cursor) |
| 10 | Version | **No** bump |

**Product sentence:**

```text
Si el ESC está respecto al FC y el FC respecto a la placa, el visor
coloca el ESC encima del FC ya situado en la placa — no en el hueco
de fila del FC.
```

**Not:**

```text
sensors/kit · plate_2 Buy · inventar mm · 230-as-box · disk-origin ·
componer offsetMm de la X · Conversation Engine
```

---

## 1. You (Claude)

- Change `ui/spatial-board/src/scene3dLayout.ts` (+ tests). Touch `src/` only if a test proves a DTO hole (you must not need it).
- Do **not** implement #2–#4 of the work order in this cycle.
- Do **not** invent plate/sensor dims. Do **not** mutate `workspace/`.
- Do **not** bump version.
- Full pytest green. `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.
- **STOP** if composition requires changing Continuity declare semantics or writer rules.

---

## 2. Intent

```text
layoutSolidsFromPose (after root + offsetMm + row slots):
  for each posed item:
    originCenter = resolveComposedCenter(originKey, visiting={})
    place child at originCenter + Δmm (axis remap) − childWrap/2

resolveComposedCenter(id, visiting):
  if id is active root → (0, 0) in declared-mm center space
  if id ∈ visiting → row-slot center of id (cycle break)
  if id has declaredBoxPose to a box origin:
    return resolveComposedCenter(originKey, visiting∪{id}) + that pose’s Δmm
  else:
    return row-slot center of id
```

Exact px math must stay consistent with today’s remap (+X→`originX`, +Z→`originY`, +Y→`originZ`) and wrapper centering.

---

## 3. Locked behavior

### 3.1 Worked example (live 5min shape)

| Item | Pose | Expected visor |
|---|---|---|
| `frame_plate` box | — | world 0 (root) |
| FC | `0/0/8` vs plate | on plate + 8 mm Z→CSS Y |
| ESC | `5/0/0` vs FC | on **posed FC center** + 5 mm X — **not** on FC’s old row slot |
| motors#i | `offsetMm` X | unchanged around world 0 |

### 3.2 Cycle example

`A` → `B` → `A`: when resolving A’s center for B (or deeper), the revisit of A uses A’s row-slot center (or world 0 if A is root). Both solids still render.

### 3.3 Copy / chrome

No new CLI strings. `clusterCenterPx` unchanged (AABB of laid wrappers).

---

## 4. Tests

### UI — `ui/spatial-board/src/scene3dLayout.test.ts`

| ID | Behavior |
|---|---|
| U20 | Plate root + FC posed vs plate + ESC posed vs FC → ESC center ≈ FC composed center + 5 mm X (prove ESC is **not** at FC’s row-slot-only placement) |
| U21 | Single-hop only (ESC vs unposed FC, no root) → byte-compatible with pre-multihop single-hop arithmetic |
| U22 | Cycle A↔B → both still laid; no throw; cycle break uses slot |
| U23 | Mid-chain missing / not-box origin → child stays on its row slot |
| U24 | `offsetMm` copy ignored by chain (station still at absolute 0+offset) |

### Python

No new Python file required. Still run full pytest if you touch nothing under `src/` (prove no drift).

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `ui/spatial-board/src/scene3dLayout.ts` | composed center resolution |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U20–U24 |
| `src/` | **empty** unless proven necessary |
| `library/` / `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_pose_multihop_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min` (poses already present):

| Step | Expected |
|---|---|
| Reload Board / 3D | ESC sits on the FC stack on the plate, not floating on an empty row slot |
| X of motors/props | Unchanged around plate |
| Screening footers | May still say overlap — screening ≠ VERIFIED; not a fail |

Record [engineer_smoke_geometry_pose_multihop_b1.md](engineer_smoke_geometry_pose_multihop_b1.md) after review.

---

## 7. Done when

- [ ] U20–U24 green; `npm test` + `typecheck` green; full pytest green
- [ ] No Python pose/envelope change; no version bump; #2–#4 not started
- [ ] Report written

---

## Explicitly not this IC

Sensors/kit · `frame_plate_2` Buy · sourced dims · invent L×W · 230-as-box · disk-origin · composing X stations · Conversation Engine · version bump
