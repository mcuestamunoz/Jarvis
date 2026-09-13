# Engineer note — Fit attest all components (cola)

**Date:** 2026-09-10  
**Parent:** Fit attestation B1 CLOSED · [next](engineer_next_fit_attestation_closed.md)  
**Status:** QUEUED (no ★ yet)

## Intent

Engineer wants a path to **Declarar verificado** on every relevant assembly component, understanding that screening is **declared AABB overlap from human-added pose**, not real-product similarity.

## What already works (no Buy)

Gate today: `screen_posed_envelope == overlap` + Board singleton (`solidCopies < 2`).

- **Already overlap (5min example):** `esc`, `power_connector`, `frame_cage`, `frame_standoff`, … → declare now.
- **Box + pose but `no_overlap`:** e.g. `battery`, `flight_controller`, `sensors`, `prop_adapter` → **Situar** until sobres cross → then declare.
- Screening copy UX: button only on `"Los sobres se solapan…"` (not `"no se solapan"`).

## What needs a Buy (cannot Situar alone)

| Subject | Blocker | Lean Buy shape (when ★) |
|---|---|---|
| **motors / propellers** | `disk` (not box) · often `no_pose` · `solidCopies ≥ 2` | Declared box (or other honest screening) + pose vs origin; **one** station seal (not N independent seals) — same spirit as Situar singleton |

## Out of scope until ★

- Renaming `overlap` → VERIFIED  
- Attesting `no_overlap` / disks silently  
- N seals per station copy  
- CAD / faces / margin / compose

## Pick when ★

Ops-first (walk Situar on remaining boxes) **or** IC for disk-station attestation — Engineer chooses.
