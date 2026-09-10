# Work order — Juntar sueltas + 4 brazos

**Date:** 2026-09-10  
**Authority:** Engineer “falta juntar todas las piezas sueltas, al igual que los 4 arm frames”  
**Role:** Claude implements · Cursor IC/review only

## Why not one mega-IC (A+B)

| Track | Surface | Blocker |
|---|---|---|
| **A — 4 arms in X** | Projector `solidCopies` + quad-X stations | **CLOSED** + ACCEPT @ **2622** |
| **B — Loose pieces** | Continuity envelope + pose subjects | Keys not on allowlist: `prop_adapter`, `frame_standoff`, `frame_cage`, `frame_caps` |

**B1 is one IC** (envelope + pose together). Mute `frame_plate*` (HD Cam, VTX, small front/rear) already use plate grammar — Engineer types L×W **without** this Buy.

Forbidden without ★: invent arm L from 230 · invent plate footprints · Conversation Engine.

---

## Order (locked)

| Step | Buy | Status |
|---|---|---|
| **A1** | [IC](implementation_contract_geometry_frame_arm_visor_x_b1.md) — arm box + visor X | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_frame_arm_visor_x_b1.md)) |
| **B1** | [IC](implementation_contract_geometry_loose_structure_envelope_pose_b1.md) — loose envelopes + pose | **LANDING** @ **2640** — review/smoke pending |
| **B2** | [IC](implementation_contract_geometry_prop_adapter_visor_x_b1.md) — adapter N copies at X | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_prop_adapter_visor_x_b1.md)) |
| **B3** | [IC](implementation_contract_geometry_frame_standoff_corners_b1.md) — standoff ×4 Main Plate corners | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_frame_standoff_corners_b1.md)) |
| **B4** | [IC](implementation_contract_geometry_standoff_count_gate_b4.md) — count gate (N=4 corners; missing/≠4 omit) | **CLOSED** review PASS @ **2661** |
| **B5** | [IC](implementation_contract_board_drag_pose_b1.md) — Board drag → pose | **CLOSED** review PASS @ **2668** · smoke pending |
| **B6** | IDLE frame-part count declare (`6 standoffs` → `count`, no LLM) | **Cola** — [nota](engineer_note_idle_frame_part_count_declare.md) |
| **B7** | Standoff visor layout N≠4 (6/8 …) | **Cola** — after B6 can set count; B4-min still omit if N≠4 |
| **#4** | Sourced dims auto-fill (cited only) | Cola |

---

## Default

Handoff: B3 **CLOSED**. Wait Engineer ★ — drag-place investigation or B4 / #4.  
Plate label noun — **dropped from cola** (leave as-is).  
Concept: [engineer_note_board_drag_place_concept.md](engineer_note_board_drag_place_concept.md).
