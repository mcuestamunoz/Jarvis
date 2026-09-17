# Implementation Contract — Mission payload identity rules (`B1-mission-payload-identity`)

**Project:** Jarvis  
**Date:** 2026-09-15  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** CLOSED · Cursor review PASS WITH NOTES · Engineer smoke **ACCEPT** (2026-09-15)  



**Parents:**
- SYSTEM_DEFINITION block-gate **CLOSED** — [IC](implementation_contract_system_definition_block_gate_b1.md) — unresolvable blocks refused; `perception`/`communication` still gated because no `ComponentRule`
- Investigation lean **B1-min (b)** — [report](investigation_report_mission_functional_payload_holes_b0.md) · [review](investigation_review_mission_functional_payload_holes_b0.md)
- Next-step note — [engineer_note_next_after_system_definition_gate.md](engineer_note_next_after_system_definition_gate.md) — identity-first cameras/radio; **not** flight-stack software
- Pattern to mirror: FC/sensors identity completeness (`_flight_controller_completeness` / `_sensor_completeness`) — model present → medium/high; **no** invented mm/g
- Gate helper: `block_components_are_resolvable` requires **every** key in `BLOCK_TO_COMPONENTS[block]` to have a rule

**Type:** Make **mission payload** subsystems **resolvable** at identity level so SYSTEM_DEFINITION **B** can honestly accept `perception` / `communication`, and free-text / Continuity can declare a camera or radio **without** inventing mass, geometry, catalog SKUs, or firmware.  
**Not** `library/cameras` seeds (no Engineer cite bags this Buy).  
**Not** mirrored `camera_mass_kg` / energy coupling.  
**Not** wizard “vigilancia” nudge (follow-on).  
**Not** Continuity `increase_payload` rewrite.  
**Not** Betaflight/PX4/MAVLink/companion software.  
**Not** version bump. **Not** `workspace/` mutation unless ★ Path D (default: tests-only).

**Output:** `.jes/artifacts/implementation_report_mission_payload_identity_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2938** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mission-payload-identity`** — identity `ComponentRule`s for mission payload keys |
| 2 | Keys in | **`cameras`** and **`radio_module`** only |
| 3 | Perception expansion | Change `BLOCK_TO_COMPONENTS["perception"]` from `["cameras", "lidar"]` to **`["cameras"]` only**. Lidar remains a named debt (alias `lidar` may still map to block `perception`, but expansion no longer creates a `lidar` stub). Document in report + `source` comment at the dict |
| 4 | Communication | Keep `BLOCK_TO_COMPONENTS["communication"] = ["radio_module"]` — unlocks once `radio_module` rule exists |
| 5 | Still gated | `payload` (`payload_bay`), `manipulation` (`arm`), `actuation` (`wheels`), `transmission` (`gearbox`) — **unchanged** refuse via existing gate |
| 6 | ComponentRules | Add two rules to `aerial_registry` (keywords Spanish/English): cameras (`camara`/`cámara`/`camera`/`camaras`/`visión`/`vision`/`fpv` as keyword-only openers — careful not to steal unrelated “sensor”); radio (`radio`/`elrs`/`crossfire`/`telemetria`/`telemetry`/`rx`/`emisor`/`receptor` — tune to avoid over-match; report exact tuples) |
| 7 | Extractors | Identity-only: set `model` (and optionally `label`) `PropertyValue` from recognized aliases or a conservative free-text remainder; **never** parse/invent `length_mm`/`width_mm`/`height_mm`/`mass_g`/`power_w`. Empty props OK → completeness `low` |
| 8 | Completeness | Mirror sensors/FC spirit: no model → `low` + hint; model present → **`medium`** (identity declared, no physical proof). Do **not** claim `high` without a future catalog bind ★ |
| 9 | Maps | Small optional alias maps in `aerial.py` (e.g. common FPV camera / ELRS phrases → canonical model strings) — **only** identity tokens, no dims. Empty map + free-text model capture is OK if tests prove a phrase like `"cámara RunCam"` / `"radio ELRS"` reaches medium |
| 10 | SYSTEM_DEFINITION | After this Buy: `block_components_are_resolvable("perception")` and `("communication")` → **True**; B → `cámara` / `comunicación` **accepts**, creates stubs, and free-text can raise completeness. Gate helper **unchanged** |
| 11 | Step-1 examples | May add one mission example that now works (e.g. `'cámara'` or `'comunicación'`) alongside resolvable base examples — or keep batería/frame/control and rely on accept path; if examples mention cámara, they must be resolvable (lock #6 of gate IC). Prefer: `Ejemplo: 'batería', 'frame', 'cámara'` |
| 12 | Forbidden | Catalog JSON seeds · invent mm/g/W · mirrored mass into `calculate_total_mass` · fold camera into `sensors` key · firmware/MAVLink · Continuity next-step rewrite · version bump · Conversation Engine |
| 13 | Live | Default **tests-only**. Optional ★ Path D: none required |

**Product sentence:**

```text
Puedo declarar cámara y radio como identidad de misión (qué llevo),
sin inventar cotas ni firmware; así la arquitectura B ya no miente
ni se niega en vacío.
```

### 0.1 “Enough” for identity (Engineer lock)

| Family | Enough this Buy | Not enough / later |
|---|---|---|
| `cameras` | User can say e.g. `cámara RunCam` / `FPV camera` → `cameras` component with `model` · completeness ≥ medium | Mass, box, catalog SKU, Board solid, power draw |
| `radio_module` | User can say e.g. `radio ELRS` / `receptor Crossfire` → `radio_module` with `model` · ≥ medium | Binding, protocols as engineering claims, mass |

No §0.1 numeric bag — identity strings only; agent must not invent product SKUs beyond alias map entries that are **labels**, not physics.

---

## 1. You (Claude)

1. Narrow `perception` → `["cameras"]`; comment lidar debt.  
2. Add extractors + completeness + two `ComponentRule`s in `aerial.py` (or thin adjacent module imported into registry — prefer keep pattern with other aerial extractors).  
3. Confirm gate unlocks perception + communication; payload/manipulation still refuse.  
4. Update SYSTEM_DEFINITION example copy per lock #11.  
5. Tests T1–T8. Report exact keywords, completeness ladder, example phrases.  
6. No library seeds. No version bump. No workspace write unless ★.

**STOP if** forced to invent camera L×W×H/mass or to implement firmware/config generation.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `block_components_are_resolvable("perception")` → True; `"communication"` → True |
| T2 | `payload` / `manipulation` / `actuation` / `transmission` still False |
| T3 | SYSTEM_DEFINITION B → `cámara` / `visión artificial` → **accept**; after `listo`, `cameras` in components (no `lidar` key) |
| T4 | B → `comunicación` → accept; `radio_module` present; no refuse message |
| T5 | Free-text / `infer_component_for_key` path: phrase with camera keyword + model → `suggested_key=cameras`, completeness medium (or documented ladder) |
| T6 | Radio phrase → `radio_module`, medium when model present; bare `radio` alone may stay low with hint |
| T7 | Extractors never attach `length_mm`/`mass_g`/`power_w` from invented digits |
| T8 | Full pytest green; `0.4.1`; prior gate refuse tests for perception/communication **updated** to accept path; payload refuse tests still fail-closed |

---

## 3. Smoke (Engineer)

1. Throwaway drone → SYSTEM_DEFINITION **B** → `cámara` → accepted (not refuse).  
2. Declare identity e.g. `cámara RunCam` (or Continuity equivalent) → card shows model; completeness not stuck forever at unresolvable low.  
3. Same for `comunicación` / `radio ELRS`.  
4. Confirm `payload` / `brazo` still refused.  
5. Confirm no catalog files under `library/cameras` invented.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| `library/cameras` / cited dims + mass | Needs Engineer bags |
| Lidar key / perception multi-key | Re-add when lidar rule+bags exist |
| `payload_bay` / `arm` / `wheels` / `gearbox` rules | Separate ★ |
| Mirrored mass into energy | After cited mass exists |
| Wizard vigilancia nudge | After this ships |
| Continuity intent vs increase_payload | After holes used in smokes |
| Flight-stack software | OUT |

---

## 5. Done when

- [x] ★  
- [x] Rules + perception narrowing + T1–T8 + report  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_mission_payload_identity_b1.md)  
- [x] Engineer smoke ACCEPT (2026-09-15) — identity on vigilancia + throwaway B accept/refuse

---

## 6. Handoff

```text
Engineer → ★ B1-mission-payload-identity
Claude   → implement identity rules + tests + report (no catalog physics)
Cursor   → review
Engineer → smoke §3 (or waive)
```
