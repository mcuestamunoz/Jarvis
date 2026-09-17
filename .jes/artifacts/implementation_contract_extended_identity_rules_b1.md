# Implementation Contract — Extended identity rules (`B1-extended-identity-rules`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** — Engineer smoke ACCEPT 2026-09-17 (`estado`: payload_bay / arm / wheels / gearbox present)  

**Parents:**
- Software closeout queue **#5** — [engineer_note_software_closeout_queue.md](engineer_note_software_closeout_queue.md)
- Mission payload identity **CLOSED** — cameras/radio only; left gated: `payload` / `manipulation` / `actuation` / `transmission` ([IC](implementation_contract_mission_payload_identity_b1.md) lock #5)
- Block-gate **CLOSED** — refuse until every `BLOCK_TO_COMPONENTS` key has a `ComponentRule`
- Pattern to mirror: cameras/radio identity completeness (model → medium; **no** invented mm/g/W)
- USER_GUIDE: “payload, brazo, ruedas, gearbox — no hay regla” ([§](../../docs/USER_GUIDE_CRAFT_MONTAGE.md))
- `ground.py` already has a `wheels` rule for the **ground** registry — this Buy must unlock the same keys for **`aerial_registry`** (gate default) without breaking ground

**Type:** Add **identity-only** `ComponentRule`s so SYSTEM_DEFINITION **B** can honestly accept the four remaining gated blocks — **`payload_bay`**, **`arm`** (manipulator — **not** `frame_arm`), **`wheels`**, **`gearbox`** — without inventing mass, geometry, catalog SKUs, or control software.  
**Not** `library/` seeds for these families.  
**Not** mirrored mass into energy.  
**Not** firmware / kinematics physics.  
**Not** changing `frame_arm` Structure B.  
**Not** version bump. **Not** `workspace/` mutation (tests-only).

**Output:** `.jes/artifacts/implementation_report_extended_identity_rules_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3027** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-extended-identity-rules`** — identity rules for the four still-gated keys |
| 2 | Keys in | **`payload_bay`**, **`arm`**, **`wheels`**, **`gearbox`** only |
| 3 | Blocks unlocked | After rules exist: `block_components_are_resolvable` → **True** for `payload`, `manipulation`, `actuation` (motors already + wheels), `transmission` |
| 4 | Registry | Add rules to **`aerial_registry`** (gate default). If ground already covers `wheels`, do **not** regress ground; prefer shared extractor helpers imported by both registries **or** aerial-only duplicates that stay identity-equivalent — report choice |
| 5 | `arm` ≠ `frame_arm` | Manipulator key stays **`arm`** (`BLOCK_TO_COMPONENTS["manipulation"]`). **Never** write manipulator identity onto `frame_arm`. Keywords must prefer `manipulador` / `brazo robot` / `robotic arm` / `brazo manipulador` — **avoid** bare `brazo`/`arm` alone if that steals Structure B frame-arm extraction (tune + regression test) |
| 6 | Extractors | Identity-only: `model` (optional `label`) from aliases or conservative free-text remainder. **Never** invent `length_mm`/`width_mm`/`height_mm`/`mass_g`/`power_w`/gear ratios |
| 7 | Completeness | Same ladder as cameras/radio: no model → `low` + hint; model present → **`medium`**. Do **not** claim `high` without a future catalog bind ★ |
| 8 | Keywords (minimum — exact tuples in report) | `payload_bay`: payload / bahía / bahia / carga útil (careful vs numeric `payload_kg`) · `arm`: see lock #5 · `wheels`: rueda(s) / wheel(s) · `gearbox`: gearbox / caja de cambios / reductor — tune over-match; document exclusions |
| 9 | SYSTEM_DEFINITION examples | May add one working example (e.g. `'payload'` / `'manipulador'`) alongside cámara/batería — only if resolvable |
| 10 | Guide | Patch USER_GUIDE line that says these blocks cannot be added — mark unlocked after ship |
| 11 | Forbidden | Catalog JSON seeds · invent mm/g · fold `arm` into `frame_arm` · fold `wheels` into `motors` · kinematics / drivetrain physics · Continuity rewrite · version bump · Conversation Engine · LLM |
| 12 | Live | Default **tests-only** |

**Product sentence:**

```text
Puedo declarar bahía de carga, brazo manipulador, ruedas y gearbox
como identidad (qué es), sin inventar cotas ni física —
así B ya no se niega en vacío para esos bloques.
```

### 0.1 Enough / not enough

| Key | Enough this Buy | Not this Buy |
|---|---|---|
| `payload_bay` | “payload GoPro bay” / “bahía de carga” → medium identity | Mass, volume, Board solid |
| `arm` | “brazo manipulador” / “robotic arm” → medium | DOF, reach mm, `frame_arm` carbon tubes |
| `wheels` | “4 ruedas” / “wheels omni” → medium identity | Tire physics, ground wizard param path redesign |
| `gearbox` | “gearbox 5:1” as **label/model text only** → medium | Ratio as engineering constraint / efficiency |

---

## 1. You (Claude)

1. Add four identity extractors + completeness + `ComponentRule`s (aerial; ground coexistence per lock #4).  
2. Prove gate unlocks the four blocks; cameras/radio/frame_arm regressions green.  
3. Update SYSTEM_DEFINITION example copy + USER_GUIDE trap line.  
4. Tests T1–T10 + report exact keywords.  
5. No library seeds. No version bump. No workspace write.

**STOP if** forced to invent geometry/mass or to merge manipulator into `frame_arm`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Helper: `payload` / `manipulation` / `actuation` / `transmission` → **resolvable** with live `aerial_registry` |
| T2 | Free-text / extractor: phrase → `payload_bay` medium (model set) |
| T3 | Manipulator phrase → `arm` medium; **does not** create/overwrite `frame_arm` |
| T4 | Wheels phrase → `wheels` medium |
| T5 | Gearbox phrase → `gearbox` medium |
| T6 | SYSTEM_DEFINITION B → `payload` / `brazo manipulador` (or locked alias) **accepts**; stubs present after `listo` |
| T7 | Bare frame-arm path still works (“brazo carbono” / existing Structure B fixtures) — no steal |
| T8 | cameras/radio identity tests still green |
| T9 | Completeness: no model → low; with model → medium (not high) |
| T10 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. Throwaway drone → SYSTEM_DEFINITION → **B** → add `payload` (or `carga útil`) → accept → `listo`.  
2. Optional: `manipulador` / `ruedas` / `gearbox` same path.  
3. Free-text declare e.g. `bahía de carga` / `brazo manipulador` → medium in `estado`.  
4. Confirm frame arms (MY5-style) still declare as `frame_arm`, not `arm`.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| `library/cameras` / payload / arm physics bags | Parked |
| Mirrored mass into energy | Later ★ |
| Lidar key | Still named debt from perception narrow |
| plate-box / Path N / HD-* | Parked |
| Ground wizard param redesign | Orthogonal |

---

## 5. Done when

- [x] ★  
- [x] Four rules + gate unlock + T1–T10 + report + guide patch  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_extended_identity_rules_b1.md)  
- [x] Engineer smoke ACCEPT 2026-09-17

---

## 6. Handoff

```text
Engineer → ★ B1-extended-identity-rules (this IC)
Claude   → implement identity rules + tests + report
Cursor   → review
Engineer → smoke §3
```
