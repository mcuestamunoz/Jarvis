# Engineer note — Dual track: plate-box + disk-station (2026-09-15)

**Status:** ACTIVE dual PRIORIDAD  
**Decision:** Engineer wants **(1) plate-box** and **(2) disk-station fit/attest** — not a new generic Fit VERIFIED investigation (that ladder already shipped: screening + human attest for **boxes**).

## Order

| # | Track | Action now | Blocked on |
|---|---|---|---|
| **0** | **`B0-disk-station-fit-attest`** | ★ investigation (Claude report, no code) | — |
| **1** | **`B1-plate-box`** | Re-open when §0.1 bag filled + ★ path C/D/E | **Engineer caliper / cite / fixture** |
| — | Path N | Stay HOLD | schema |

Disk-station B0 can run **without** plate measurements. Plate-box unblocks stack `cabe`/attest when the plate is no longer `estimated_temporary`.

## Track 1 — Plate-box (your bag)

IC already exists: [implementation_contract_geometry_plate_box_b1.md](implementation_contract_geometry_plate_box_b1.md) (held B0 empty bag).

Paste a filled bag (example):

```text
### frame_plate (Main) L×W
authority: caliper | OEM drawing | fixture_disclosed
source_url_or_method: …
part: Main → frame_plate
measured_mm:
  length_mm: …
  width_mm: …
  height_mm: …   # or use thickness_mm already on spec
identity_status: measured | verified | fixture_disclosed
projects_to_apply: 10-min-autonomía | vigilancia | both | tests-only
path_star: C | D | E
```

**Forbidden:** body 175×173 · wheelbase · estimate from FC/ESC footprint.

Until this bag exists: estimated plate keeps blocking stack screening/attest — **correct**.

## Track 2 — Disk-station

Contract: [investigation_contract_disk_station_fit_attest_b0.md](investigation_contract_disk_station_fit_attest_b0.md)

After ★: Claude investigates → Cursor reviews → only then B1 IC (e.g. proxy-box station or radial rule — **not** cylinder-as-box).

## Explicitly not this dual track

CAD · banco · Optimization · Conversation Engine · reopen Fit VERIFIED B0 · invent plate mm · Path N
