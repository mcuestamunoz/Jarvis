# Implementation Contract — Mount standard assist B1 (`B1-mount-standard-assist`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement)  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** APPROVED FOR IMPLEMENT — Engineer ★ **`B1-mount-standard-assist`** (2026-09-13)  
**Parents:**
- [investigation_contract_board_drone_default_layout_b0.md](investigation_contract_board_drone_default_layout_b0.md)  
- [investigation_report…](investigation_report_board_drone_default_layout_b0.md) · [review PASS WITH NOTES](investigation_review_board_drone_default_layout_b0.md) — lean kept  
- Continuity spatial assembly ★ — [feature lock](engineer_lock_continuity_spatial_assembly_feature.md)  
- `mounted_on_declare_assist.py` + `set_component_mounted_on` CLOSED  
- Conn B1 CLOSED — remaining mounts walk; this Buy is **discoverability**, not new physics  
- Catalog assist pattern: `motor_catalog_assist.py` / peers — suggest, never silent write  

**Type:** Deterministic **suggest-only** assist for the already-expressible standard drone mount graph.  
**Not** auto-pose / stack-by-dimension. **Not** plate L×W invent. **Not** widening Continuity subjects (`frame_arm`, `power_connector`, `signal_harness` as mount subjects — park unless later ★). **Not** Board Situar layout. **Not** Conversation Engine. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_mount_standard_assist_b1.md`

**Cola after this Buy:** see §6 and [engineer_note_board_situar_work_cola.md](engineer_note_board_situar_work_cola.md)

**Checkpoint:** package **`0.4.1`** · suite ~**2747**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mount-standard-assist`** — checklist of **undeclared but expressible** standard mounts + Continuity phrase to type |
| 2 | Edges in scope (only these) | `propellers→motors` · `motors→frame_arm` (when `frame_arm` exists) · `esc→frame`/`frame_plate*` · `flight_controller→frame`/`frame_plate*` · `battery→frame`/`frame_plate*` · `sensors→frame`/`frame_plate*`/`esc` as already allowed by target resolver — **prefer** the single best target rule below |
| 3 | Target pick rule | Reuse existing Continuity target resolution honesty: if exactly one plate → that plate; if bare `frame` is the only clear target for sensors/battery historically allowed → keep same assist nouns Continuity already accepts; if **ambiguous plates** → list as AMBIGUOUS (do not guess). Never invent a mount target key that `parse_mounted_on_declare` would refuse |
| 4 | Out of graph this Buy | `frame_arm→plate` (arm not a subject) · connector/harness as subjects · any pose / Δmm |
| 5 | UX surface | CLI/IDLE: a clear phrase family (e.g. `montajes estándar` / `ayúdame con montajes` / `qué falta montar` — pick 1–2 Spanish triggers, document them). Output numbered undeclared edges + exact example phrase per edge. Optional: typing the number runs the **same** `parse_mounted_on_declare` + `set_component_mounted_on` path already used for typed Continuity (confirm write) — **or** user retypes the phrase; either OK if documented. Prefer number→existing writer if thin |
| 6 | Silent write | **Forbidden.** Never write mounts without user confirm (number pick or typed phrase) |
| 7 | Live matrix | Compute from **current** `ProjectState` undeclared edges — do not assume Conn smoke state (review N1: live `motors→arm` often missing) |
| 8 | Pattern | New thin pure module (e.g. `mount_standard_assist.py`) + orchestrator IDLE bridge; mirror catalog-assist style |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Jarvis lista qué montajes estándar del dron aún faltan (solo los que
Continuity ya sabe declarar) y me da la frase exacta; yo confirmo.
No inventa poses ni la caja de la placa.
```

---

## 1. You (Claude)

- Add pure builder: given `components` dict → list of `{subject, target, example_phrase, reason}` for undeclared in-scope edges.  
- Wire IDLE/orchestrator trigger + format message in Spanish.  
- Tests: empty project / 5min-shaped (prop already on motors, esc on plate, motors arm missing) / ambiguous plates / no `frame_arm` → skip motor→arm edge.  
- Do **not** change writer gates, pose, Scene3D, plate envelopes.  
- Do **not** mutate `workspace/`. Do **not** bump version.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | All in-scope edges undeclared → list includes prop→motors, motors→arm (if arm exists), stack→plate/frame |
| T2 | Already-declared edge omitted |
| T3 | No `frame_arm` → no motors→arm suggestion |
| T4 | Ambiguous multi-plate → no silent pick (AMBIGUOUS or ask Continuity plate rule) |
| T5 | Example phrase parses via `parse_mounted_on_declare` as SET (or AMBIGUOUS when expected) |
| T6 | Full pytest green; package still `0.4.1` |

---

## 3. Smoke (Engineer)

1. On `autonomía-15min` (few mounts): trigger assist → see missing standard edges + phrases.  
2. Confirm one (number or type) → `mounted_on` set; Board edge if applicable.  
3. Re-trigger → that edge gone from list.  
4. Confirm assist never writes pose / never claims plate box root.

---

## 4. Out of scope

Plate L×W · stack-rule Δmm · layout pack · arm-as-subject vocab · kit harness/connector as mount subjects · Situar UX · Three.js · version bump

---

## 5. Done when

- [ ] Assist module + IDLE wire + T1–T6  
- [ ] Report written; package `0.4.1`  
- [ ] Engineer smoke ACCEPT  

---

## 6. Cola after this Buy (locked order for Engineer)

| Order | ★ | Qué | Gate |
|---|---|---|---|
| **Now** | **`B1-mount-standard-assist`** | This IC | Implement |
| 1 | **`B1-plate-box`** | Main-plate root activates — **data only** (Option B caliper or new cite L×W on `frame_plate`) | Citation / caliper ★ |
| 2 | **`B1-stack-rule`** (optional) | Envelope stacking/centering with **disclosed** assumption copy | After plate box (or narrow prop-on-motor ★ alone) |
| 3 | **`B1-layout-pack-cited`** | Named kit pose pack with disclosed authority | Citation or Engineer-measured table |
| 4 | Silhouette polish (Product B) | Visor “parece dron” | Downstream of plate/arm data |
| — | Subject-vocab widen (`frame_arm` / kit as mount subjects) | Separate ★ if needed | Not this Buy |
| — | Parked | LLM auto-pose · invent plate · Conversation Engine | Forever unless ★ |

---

## 7. Handoff

```text
Claude  → implement + report
Cursor  → review
Engineer → smoke §3
```
