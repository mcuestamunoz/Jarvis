# Implementation Contract — Fase C craft↔FS bind (`B1-fase-c-craft-fs-bind`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (profile reads craft identity ≠ Continuity drives firmware ≠ craft imports FS)

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-27 — IC passed to Claude = execute directly)  
**Parents:**
- [C42 ★ ACCEPT](implementation_contract_fase_c_icm_register_client_b1.md) — ICM WHO_AM_I on ScriptedSpi @ **`v0.5.43`**  
- [C3 ★ ACCEPT](implementation_contract_fase_c_first_fc_rung_b1.md) — `vehicle_profiles` smoke JSON, no craft bind @ **`v0.5.1`**  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C43 last software-month rung; Assistant PARKED until C43 CLOSED  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board remain authoritative for craft identity

**Type:** **Implementation Contract** — a **one-way bind**: a *this-quad* `VehicleProfile` (or thin loader beside it) can **read** craft identity (catalog SKU / frame id / declared class fields) so flight-software smoke knows which craft it is talking about. Still **not** Continuity commanding firmware, still **not** craft packages importing `flight_software`.  
**Package:** bump **`0.5.43` → `0.5.44`**; git tag **`v0.5.44`** only after Engineer ACCEPT.

**Not** Continuity → FS command path · not Board mutating FS · not FS writing craft workspace/BOM · not silicon · not SPI1 live · not Assistant implement · not “we fly”.

**Outputs (required):**
1. A bind API under `vehicle_profiles/` (preferred) or a tiny dedicated module it owns — e.g. `bind_profile_to_craft_identity(...)` / `load_profile_for_craft(...)` — that attaches **read-only** craft identity fields onto a profile (or returns a bound view). Prefer **existing** craft read surfaces (`ComponentLibrary` / catalog JSON / declared project properties) over inventing a second SoT.  
2. At least one checked-in profile or fixture that binds to a **real catalog SKU already in tree** (desk preference: `hglrc_my5_5in` if present; otherwise any seeded frame SKU) — identity fields only (sku / display / class), **not** inventing geometry or mass.  
3. Tests: `tests/test_fase_c_craft_fs_bind_b1.py` — bind succeeds for the fixture SKU; missing SKU → documented error; **craft / Continuity / Board / adapters / core orchestrator paths still do not import `jarvis.flight_software` or call into FS to “flash/drive”**; FS/profile bind does **not** write workspace or `library/`.  
4. Report + docs honesty: **profile reads craft ≠ Continuity drives firmware ≠ craft imports FS ≠ flying**  
5. `pyproject.toml` → **`0.5.44`** (+ re-pin `0.5.43` checkpoints)

**Checkpoint:** package **`0.5.44`** · suite green · host `ctest` unchanged-or-green · isolation direction locked · C42 ICM untouched

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-craft-fs-bind`** — this-quad profile **reads** craft identity |
| 2 | One front | Do **not** fold Assistant, silicon, live SPI1, DShot wire, Continuity→firmware, Board polish |
| 3 | What this Buy demonstrates | The software-month tip can name *which craft* a profile is about by reading catalog/project identity. Isolation becomes a **directed** seam (FS may read craft), not a permanent wall. **Human:** “el perfil del quad ya sabe qué craft es; Continuity sigue sin mandar el firmware.” |
| 4 | Direction | **FS / `vehicle_profiles` → craft (read).** Forbidden: Continuity/CLI/Board/adapters/`src/jarvis/core` importing `jarvis.flight_software` or `jarvis.vehicle_profiles` to command actuators/firmware. Forbidden: bind writing `library/` or mutating workspace as SoT. |
| 5 | Identity surface | Minimal: catalog **SKU** (+ optional display_name / vehicle_class mirrored from catalog if already present). Do **not** require BOM explode, geometry layout, or power ladder. Do **not** invent fields absent from catalog. |
| 6 | API shape | Prefer extend `VehicleProfile` with optional identity fields **or** a small `BoundVehicleProfile` / bind helper — pick one, document. Keep `smoke_quad_hal_imu` working (unbound smoke still valid). |
| 7 | Continuity | **Unchanged role.** No new Continuity turn that flashes, arms, or submits autonomy into FS. No `submit_command` from craft paths. |
| 8 | Native C++ | **Not required.** Python bind is enough. Do not force `native/flight_control` changes. |
| 9 | Freeze | C42 `icm42688p.*` untouched. Safety / sim executor / plant / loop behavior-frozen unless a disclosed one-line import-path test needs a re-pin. |
| 10 | Version | **`0.5.43` → `0.5.44`**; tag on ACCEPT only |
| 11 | Forbidden claims | “Continuity flies the quad” · “firmware bound” · “craft imports FS” · “SPI1 live” · “we fly” |

**Product sentence:**

```text
Un VehicleProfile de este quad lee la identidad craft (SKU) —
Continuity sigue sin mandar el firmware.
```

**Defaults locked by Cursor:**
- One-way read bind in `vehicle_profiles/`  
- Fixture SKU from existing catalog (`hglrc_my5_5in` preferred)  
- Package **`0.5.44`**  
- Assistant stays PARKED until this Buy ★ ACCEPT CLOSED

---

## 1. Package layout (normative intent)

```text
src/jarvis/vehicle_profiles/
  schemas.py          # optional identity fields OR bound view type
  bind.py             # NEW (name flexible) — read-only craft identity bind
  data/*.json         # optional bound profile fixture

tests/test_fase_c_craft_fs_bind_b1.py
```

Do **not** put bind under `capabilities/`. Do **not** add Continuity tools that call FS.

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Bind to fixture catalog SKU → profile/view exposes that SKU |
| T2 | Unknown SKU → documented error (not silent empty success) |
| T3 | Unbound smoke profile still loads (`smoke_quad_hal_imu`) |
| T4 | No writes to `library/` / workspace from bind |
| T5 | Craft paths (`core` / adapters / Continuity entrypoints as already gated) still do **not** import `jarvis.flight_software` |
| T6 | FS/profile may import craft **read** surfaces — disclosed; reverse import still forbidden |
| T7 | `pyproject` **`0.5.44`**; suite green |
| T8 | Report honesty line present |

---

## 3. Honesty / forbidden

```text
profile reads craft ≠ Continuity drives firmware
craft identity in RAM ≠ flash ≠ arm ≠ flying
directed seam ≠ craft imports flight_software
```

---

## 4. Acceptance

**PASS when:** T1–T8 · one-way bind · fixture SKU · version `0.5.44`.  
**FAIL if:** Continuity→FS command path · craft imports FS · library/workspace mutation · “we fly”.

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → craft↔FS read bind + tests + report + 0.5.44
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.44
Cola     → Assistant DC unpark discussion (no implement until ★)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C43 craft↔FS bind — this-quad profile reads craft identity.
Package 0.5.44. Continuity ≠ firmware. Assistant PARKED until ACCEPT.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-27 (IC passed to Claude = execute)  
- [ ] After landing: Cursor review · then ACCEPT + tag `v0.5.44`  
- [ ] After C43 CLOSED: Assistant DC may be discussed (still needs its own ★ to implement)  
