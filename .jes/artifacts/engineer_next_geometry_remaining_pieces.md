# Work order — Remaining situar Buys (ordered 1→4)

**Date:** 2026-09-09  
**Authority:** Engineer “procede con los 4 en orden” + “¿los 3 primeros en un mismo IC?”  
**Answer on packaging:** **No — not one mega-IC.** Three separate ICs for #1–#3, then #4. Same *sequence*, different *contracts*.  
**Role lock:** **Claude implements** `src/` / `ui/`. Cursor = IC + review + PRIORIDAD only.

---

## Why not one IC for #1–#3

| # | Buy | Surface | Failure mode if bundled |
|---|---|---|---|
| 1 | Multi-hop pose | `ui/` layout only | Chain/cycle bugs hide under envelope noise |
| 2 | Sensors / kit boxes | writer allowlist + Continuity + maybe seeds | Catalog honesty ≠ layout |
| 3 | `frame_plate_2` as origin | mostly Continuity walk — writer **already** allows any `frame_plate*` envelope | May shrink to smoke + pose; not a layout rewrite |

One review / one smoke / one rollback boundary per Buy. Order is locked; **procede** opens only the next READY IC.

---

## Order (locked)

| Step | IC | Status |
|---|---|---|
| **1** | [Multi-hop pose composition B1](implementation_contract_geometry_pose_multihop_b1.md) | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_pose_multihop_b1.md)) |
| **2** | [Sensors / kit declared envelopes B1](implementation_contract_geometry_declared_sensors_kit_envelope_b1.md) | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_declared_sensors_kit_envelope_b1.md)) — GPS box; situar = pose Continuity |
| **3** | [Top LiPo `frame_plate_2` envelope noun B1](implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md) | **CLOSED** + ACCEPT ([smoke](engineer_smoke_geometry_frame_plate_2_lipo_envelope_b1.md)) |
| **3b** | [Pose Continuity subject: plates B1](implementation_contract_continuity_pose_plate_subject_b1.md) | **CLOSED** (situar walked) |
| **3c** | [Pose Continuity subject: kit keys B1](implementation_contract_continuity_pose_kit_subject_b1.md) | **CLOSED** + ACCEPT ([smoke](engineer_smoke_continuity_pose_kit_subject_b1.md)) |
| **4** | Sourced / catalog dims auto-fill (cited only, never invent) | **Next cola** — wait ★ |

Forbidden across all four without a new ★: invent mute L×W · 230-as-box · disk-origin · Conversation Engine · version bump unless a later IC says so.

---

## Default recommendation

Wait Engineer ★. Default next: IC **#4** sourced dims (cited only). Alt: Continuity walk prop_adapter / caps / standoff (declare mm if known).
