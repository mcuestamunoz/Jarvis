# Implementation Report — Fase C craft↔FS bind (`B1-fase-c-craft-fs-bind`)

**IC:** [`implementation_contract_fase_c_craft_fs_bind_b1.md`](implementation_contract_fase_c_craft_fs_bind_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-27
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.44`** (Engineer 2026-09-27) · Cursor review PASS.

---

## 0. Read this first — honesty summary

This Buy adds a **one-way, read-only** bind: a `VehicleProfile` can
read craft identity (catalog SKU) via the existing `ComponentLibrary`
read surface, so flight-software smoke can finally name which craft it
is talking about — the last rung of this software month.

```text
profile reads craft != Continuity drives firmware
craft identity in RAM != flash != arm != flying
directed seam != craft imports flight_software
```

**Exists:** a `BoundVehicleProfile` that mirrors a real catalog frame
row's identity fields (SKU/manufacturer/model/size class), read-only,
via a directed seam (`vehicle_profiles` → craft). **Impossible:**
Continuity commanding firmware, craft packages importing
`flight_software`, or this bind writing `library/`/workspace. Nothing
in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/vehicle_profiles/bind.py                # NEW — BoundVehicleProfile + bind_profile_to_craft_identity
src/jarvis/vehicle_profiles/loader.py               # EXTENDED — load_this_quad_profile
src/jarvis/vehicle_profiles/data/this_quad.json     # NEW — fixture bound to hglrc_my5_5in
src/jarvis/vehicle_profiles/__init__.py             # EXTENDED — new exports + docstring paragraph
src/jarvis/vehicle_profiles/schemas.py              # UNCHANGED — VehicleProfile itself untouched

tests/test_fase_c_craft_fs_bind_b1.py   # NEW — 9 tests
```

Not placed under `capabilities/`. No Continuity tool added anywhere
that calls `flight_software`.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| Bind API under `vehicle_profiles/` | Output 1 | ✅ `bind_profile_to_craft_identity(profile, craft_sku, library=None) -> BoundVehicleProfile` in `bind.py` |
| Read-only, existing craft read surface | Output 1 | ✅ uses `ComponentLibrary` (`jarvis.knowledge.library`) — no second SoT invented |
| Checked-in fixture binding to a real catalog SKU | Output 2 | ✅ `this_quad.json` + `hglrc_my5_5in` (present, desk-preferred SKU) |
| Direction locked (FS→craft read only) | §0.4 | ✅ verified via grep — see §6 |
| Identity surface minimal (SKU + optional display/class) | §0.5 | ✅ `craft_sku`/`craft_manufacturer`/`craft_model`/`craft_size_class_inch` only — no BOM explode, no geometry, no invented fields |
| API shape: extend `VehicleProfile` OR a bind helper/view | §0.6 | ✅ chose a `BoundVehicleProfile` wrapper — see §2.1 |
| Continuity role unchanged | §0.7 | ✅ no Continuity tool touched; `submit_command`/`propose_command` not imported by `bind.py` |
| Native C++ not required | §0.8 | ✅ Python only, no `native/flight_control` changes |
| Freeze | §0.9 | ✅ `icm42688p.*`, `safety.py`, `sim_executor.py`, `loop.*`, `plant.*` all `git diff --stat` empty |
| Version `0.5.44` | §0.10 | ✅ `pyproject.toml` + 48 checkpoint tests re-pinned |

### 2.1 Disclosed design choices

**`BoundVehicleProfile` wrapper, not an extension of `VehicleProfile`
itself (the IC's own §0 decision 6 offered both):** adding `craft_*`
fields directly onto `VehicleProfile` was rejected in favor of a small,
separate wrapper type. `VehicleProfile` (`extra="forbid"`) has been the
one schema every Buy since C3 has loaded fixtures against — widening it
would touch a type pinned by 40+ Buys' own fixtures for a feature only
some profiles need. A wrapper type makes "this profile view is bound to
a real catalog frame" something a caller explicitly asks for
(`bind_profile_to_craft_identity(...)`), never an always-present-but-
usually-`None` field silently riding along on every profile.
`load_smoke_profile()`/`smoke_quad_hal_imu` are completely unaffected —
still return/declare a plain, unbound `VehicleProfile`, exactly as
every prior Buy in this ladder already relied on (re-verified, T3).

**Error handling reuses the existing craft error, does not invent a
second one:** `ComponentLibrary.get_frame(sku)` already raises `KeyError`
with a clear "not in library, available: ..." message on a miss. This
Buy's own `bind_profile_to_craft_identity` lets that exception
propagate unmodified rather than wrapping it in a new
`CraftBindError`-shaped type — the IC's own §0 decision 1 preference
("prefer existing craft read surfaces ... over inventing a second SoT")
extends naturally to not inventing a second error type for the same
failure mode. Documented in `bind.py`'s own docstring, tested directly
(T2).

**Fixture design — identity only, no invented geometry (IC §0 decision
5, locked):** `this_quad.json` carries the same five fields every
profile in this ladder already carries since C3
(`id`/`display_name`/`vehicle_class`/`rung`/`notes`) — no geometry,
mass, or power field was added to the JSON itself. All of the craft
identity (`manufacturer`/`model`/`size_class_inch`) comes exclusively
from the bind call reading `hglrc_my5_5in`'s own already-seeded catalog
row at call time, never hand-copied into the fixture JSON.

**No new Continuity turn, no autonomy import (IC §0 decision 7,
confirmed by source inspection, not just absence of a call site):**
`bind.py` imports `jarvis.knowledge.library` (the one craft read
surface this Buy is authorized to read) and `jarvis.vehicle_profiles.schemas`
— nothing else. It does not import `jarvis.core`, `jarvis.adapters`,
`jarvis.capabilities`, or `jarvis.flight_software.autonomy`, and the
strings `submit_command`/`propose_command` do not appear anywhere in
the file (T6).

### 2.2 Non-goals (IC §0 decision 2) — confirmed absent

Assistant implementation, silicon, live SPI1/gyro, "we fly," Continuity→FS
command path, craft importing `flight_software`, bind writing
`library/`/workspace — confirmed by grep (§6) and by this Buy's own
test file's structural checks (T4, T5, T6).

---

## 3. Verified — real test runs

Before formalizing any test, the bind was run standalone confirming it
reads the real catalog row end-to-end and rejects an unknown SKU:

```text
$ python3 -c "..."
bound: profile=VehicleProfile(id='this_quad', ...) craft_sku='hglrc_my5_5in' ...
sku: hglrc_my5_5in mfr: HGLRC model: MY5 size: 5.0
KeyError raised as expected: "Frame 'nonexistent_sku_xyz' no está en la biblioteca. Disponibles: armattan_roo..."
smoke still loads: smoke_quad_hal_imu
```

```text
$ python -m pytest tests/test_fase_c_craft_fs_bind_b1.py -v
9 passed
$ python -m pytest -q
3759 passed, 9 skipped
```

Baseline before this Buy: `3750 passed, 9 skipped`. Delta: **+9
passed** — exactly the new test count, zero regressions.

```text
$ ctest --test-dir build/flight_control
100% tests passed out of 111
```

Unaffected, as expected — this Buy touches no C++ file (native C++ not
required per IC §0 decision 8), confirmed by an unchanged `111/111`
against the baseline C42's own report left at `111/111`.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `icm42688p.hpp`/`.cpp` (C42) | Untouched — `git diff --stat` empty |
| `sim_executor.py` (C40), `safety.py` (C41) | Untouched — `git diff --stat` empty |
| `loop.hpp`/`loop.cpp`/`loop.py`, `plant.hpp`/`plant.cpp`/`plant.py` | Untouched — `git diff --stat` empty |
| `VehicleProfile` (`schemas.py`) | Untouched — `git diff --stat` empty; `BoundVehicleProfile` is a separate, new type |
| `library/frames/_datos.json` | Untouched — mtime/content re-verified identical before/after a bind call (T4) |
| `src/jarvis/core`, `src/jarvis/adapters`, `src/jarvis/workspace` | Untouched — re-verified zero references to `jarvis.flight_software`/`jarvis.vehicle_profiles` (T5) |
| Safety/registry | Untouched |

No pre-existing test required a disclosed retarget in this Buy — pure
addition, no behavior change to any frozen module.

---

## 5. Tests run

`tests/test_fase_c_craft_fs_bind_b1.py` — **9 tests**, covering IC §2's
T1-T6 (T7's "suite green" half is the process run in §3; T8 is this
report):

| Test | Covers |
|---|---|
| `test_t1_bind_to_fixture_catalog_sku_exposes_that_sku` | T1 |
| `test_t1_direct_library_lookup_matches_the_catalog_row` | T1 (cross-check against `ComponentLibrary` directly) |
| `test_t2_unknown_sku_raises_documented_error_not_silent_success` | T2 |
| `test_t3_unbound_smoke_profile_still_loads` | T3 |
| `test_t4_bind_does_not_write_library_or_workspace` | T4 |
| `test_t5_craft_paths_still_do_not_import_flight_software` | T5 |
| `test_t6_bind_module_imports_only_the_craft_read_surface` | T6 |
| `test_t7_pyproject_version_is_0_5_44` | T7 (version half) |
| `test_t7_full_suite_process_gate_placeholder` | T7 marker |

No Catch2 cases — native C++ is explicitly not required by this IC
(§0 decision 8), and Safety-style Python-only precedent (C41) already
established that not every Buy needs a C++ twin.

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/icm42688p.hpp native/flight_control/src/icm42688p.cpp \
    src/jarvis/flight_software/autonomy/sim_executor.py src/jarvis/capabilities/safety.py \
    src/jarvis/flight_software/flight_control/loop.py src/jarvis/flight_software/flight_control/plant.py \
    src/jarvis/vehicle_profiles/schemas.py \
    library/frames/_datos.json
(empty — every named module byte-unchanged, including the catalog file itself)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
(empty — no craft/library/Board diffs of any kind, pre-existing or otherwise, at this point in the session)
```

`grep -rln "jarvis.flight_software\|jarvis.vehicle_profiles" src/jarvis/core src/jarvis/adapters src/jarvis/workspace`
— empty, both before and after this Buy's own changes (re-verified,
T5). `bind.py`'s own source contains no `jarvis.core`/`jarvis.adapters`/
`jarvis.capabilities`/`jarvis.flight_software.autonomy` reference and no
`submit_command`/`propose_command` string (T6).

---

## 7. Files changed

**New:**
- `src/jarvis/vehicle_profiles/bind.py`
- `src/jarvis/vehicle_profiles/data/this_quad.json`
- `tests/test_fase_c_craft_fs_bind_b1.py`
- `.jes/artifacts/implementation_report_fase_c_craft_fs_bind_b1.md` (this file)

**Modified:**
- `src/jarvis/vehicle_profiles/loader.py` (`load_this_quad_profile` appended)
- `src/jarvis/vehicle_profiles/__init__.py` (new exports: `BoundVehicleProfile`, `bind_profile_to_craft_identity`, `load_this_quad_profile`; docstring paragraph)
- `pyproject.toml` (`0.5.43` → `0.5.44`)
- 48 pre-existing test files re-pinned from `0.5.43` to `0.5.44`
- `README.md`, `docs/ARCHITECTURE.md` (new paragraph after C42), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §8)

---

## 8. Docs updated (honesty confirmed — not claiming ACCEPT/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.44 includes (LANDED — awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)" section; "Next" pointers retargeted to note this closes the software-month arc.
- `docs/ARCHITECTURE.md` — new C43 paragraph after the C42 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C43 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C43 table row both changed to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — **not touched**, per the IC's own explicit carve-out (§0 decision 8: native C++ not required).

No file in this Buy claims `v0.5.44` is tagged, ACCEPT CLOSED,
"Continuity flies the quad," "firmware bound," "craft imports FS,"
"SPI1 live," or "we fly." Confirmed via `git tag -l | sort -V | tail -6`
at close of this Buy: `v0.5.38`, `v0.5.39`, `v0.5.40`, `v0.5.41`,
`v0.5.42`, `v0.5.43` — `v0.5.44` does not exist yet.

---

## 9. Residual / next steps

- Per the IC's own handoff, after Cursor review + Engineer ★ ACCEPT + tag `v0.5.44`, this closes the software-month arc (the Month note's own "Assistant PARKED until C43" condition). Assistant design-contract discussion may then begin — it still needs its own ★ to implement, this report does not authorize that.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report) remains unfixed, unrelated to this Buy.
- The bind is one-directional and read-only by construction (a plain function call, not a stored reference) — there is no live-sync concern (e.g. the catalog changing after a bind) to track, since each `bind_profile_to_craft_identity` call re-reads the library fresh (or uses the caller-supplied instance).
- Only one fixture (`this_quad.json` → `hglrc_my5_5in`) was bound this Buy, matching the IC's own "at least one" minimum — a future Buy wanting other craft profiles bound would follow the same `bind_profile_to_craft_identity` call, no new API needed.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T8: ✅ T1-T6 in Python (9/9 passing), T7's suite/ctest half in §3, T8 in this report.
- One-way bind: ✅ `bind_profile_to_craft_identity` reads via `ComponentLibrary`; craft-side isolation re-verified in both directions (T5/T6).
- Fixture SKU: ✅ `this_quad.json` bound to `hglrc_my5_5in`, a real, already-seeded catalog frame.
- Version `0.5.44`: ✅ `pyproject.toml` + all 48 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions**
(Continuity→FS command path, craft imports FS, library/workspace
mutation, "we fly") — none present, verified above.
