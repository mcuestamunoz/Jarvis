# Implementation Report — Fase C ICM register client (`B1-fase-c-icm-register-client`)

**IC:** [`implementation_contract_fase_c_icm_register_client_b1.md`](implementation_contract_fase_c_icm_register_client_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-27
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.43`** (Engineer 2026-09-27) · Cursor review PASS WITH NOTES.

---

## 0. Read this first — honesty summary

This Buy adds a datasheet-cited ICM42688P `WHO_AM_I` register client on
`SpiBytePort` (tests use `ScriptedSpi`/`LoopbackSpi`) — the placeholder
probe (`probe_rx`, C34) becomes a named device transaction, still on
the same lab-fiction bus.

```text
ICM register client on ScriptedSpi != chip SPI1
WHO_AM_I in RAM != gyro live != samples in step
datasheet cite != lab measurement on copper
```

**Exists:** a cited, tested register-read client that talks to
`SpiBytePort` exactly like `probe_rx` already does, just naming a real
register instead of sending dummy zero bytes. **Impossible:** this
running against a real chip on SPI1, any CS/GPIO pin, a full IMU
driver, or any sample reaching `FlightControlLoop.step`/
`ControlLoop::step`. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
native/flight_control/include/jarvis/fc/icm42688p.hpp   # NEW — constants + WhoAmIResult + read_who_am_i
native/flight_control/src/icm42688p.cpp                    # NEW
native/flight_control/tests/test_icm42688p.cpp             # NEW — 6 Catch2 cases

tests/test_fase_c_icm_register_client_b1.py   # NEW — 9 structural tests (no Python SPI port)
```

C++-native only, same axis as C32-C34 — **no Python `SpiBytePort` or
client was added**, matching C34's own locked precedent
(`test_no_python_spi_port_added`, re-pinned by this Buy's own test of
the same name). Not placed under `capabilities/`; does not import
Continuity.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| Cited WHO_AM_I read via `SpiBytePort` | §0.4 | ✅ `kIcm42688pRegWhoAmI = 0x75`, `kIcm42688pWhoAmIValue = 0x47` — named constants, not a bare magic byte |
| Datasheet citation | Output 2 | ✅ TDK InvenSense ICM-42688-P (DS-000347) — see §2.1 for the corroboration path disclosure |
| Transaction shape (write reg\|read-bit, then read data) | §0.5 | ✅ 2-byte full-duplex: `TX[0] = reg \| 0x80`, `TX[1]` = dummy, `RX[1]` = value |
| API (`read_who_am_i(SpiBytePort&) -> WhoAmIResult`) | §0.6 | ✅ chosen name/shape, `probe_rx` kept unmodified |
| Optional second register | §0.7 | ✅ deliberately NOT added — disclosed scope choice, §2.1 |
| Languages | §0.8 | C++ only (no Python port, per IC's own fallback — see §1) |
| Freeze | §0.9 | ✅ `spi.hpp`/`spi.cpp`/`spi_probe.hpp`/`spi_probe.cpp` `git diff --stat` empty |
| Version `0.5.43` | §0.10 | ✅ `pyproject.toml` + 47 checkpoint tests re-pinned |

### 2.1 Disclosed design choices

**Datasheet citation, and its own honestly-disclosed limitation:** the
IC requires citing "TDK datasheet section/table." This session
attempted to fetch the actual ICM-42688-P datasheet PDF (DS-000347)
directly, three times, from three different mirrors
(invensense.tdk.com, product.tdk.com, alldatasheet.com) — every attempt
returned HTTP 403. Rather than fabricate a section/table number this
session never actually read, the register address (`0x75`) and expected
value (`0x47`) were verified two other ways: (1) a web search whose
summarized results directly named "WHO_AM_I register ... address 0x75
... value 0x47" for the ICM-42688-P; (2) fetching the open-source
PX4-Autopilot flight-controller driver's own register header
(`InvenSense_ICM42688P_registers.hpp`), which independently defines
`WHOAMI = 0x47` and `BANK_0::WHO_AM_I = 0x75` — that driver itself
implements this same datasheet's register map, so it corroborates the
value from a second, unrelated source rather than merely repeating the
first search's own summary. This corroboration path (two independent
sources, no direct PDF read) is disclosed verbatim in
`icm42688p.hpp`'s own header comment, not silently presented as if the
PDF had been read directly.

**Transaction shape, also corroborated the same way:** the IC's own
§0 decision 5 anticipated "typically write reg|read-bit then read
data." The exact 2-byte shape (`TX[0] = reg | 0x80`, `TX[1]` = dummy,
`RX[1]` = value) and the `0x80` read-bit convention were confirmed by
fetching PX4's own `ICM42688P.cpp` `RegisterRead` implementation
(2-byte transfer, `DIR_READ` OR'd into the address byte, `cmd[1]`
returned as the value) — the same InvenSense-family SPI convention used
across this chip lineage (MPU-6000/9250, ICM-20948, etc.), not
something invented for this Buy.

**No second register (a deliberate, disclosed omission, not a silent
one):** the IC allows one optional extra cited register "if tiny." This
session chose not to add one — a second register's address/reset value
could not be corroborated with the same two-independent-source
confidence as `WHO_AM_I` within this Buy's own scope, and shipping one
well-verified register beats shipping two, one of which would rest on
weaker sourcing. This is stated in `icm42688p.hpp`'s own header comment
and repeated here, not omitted quietly.

**C34's own coincidence, re-confirmed, not re-cited:** the IC's own §0
decision 4 notes C34's placeholder fixture byte (`0x47`) may equal the
real WHO_AM_I value. It does. `spi_probe.hpp`/`.cpp` still contain no
`0x47` literal (re-verified — `test_t4_probe_rx_and_c34_ports_untouched`
below), and the real citation lives only in `icm42688p.hpp`/`.cpp`,
never retroactively added to C34's own files.

**Short-transfer honesty:** `WhoAmIResult.bytes_transferred` is
reported explicitly, and `matches_expected` is `false` whenever
`bytes_transferred < 2` — a transfer that comes back short (an
exhausted `ScriptedSpi` script, or a hypothetical future port with a
smaller bound) can never be silently treated as a match just because
whatever partial byte happened to land in an uninitialized `value`
looked right. Verified by a dedicated Catch2 case with a 1-byte
`ScriptedSpi` script against a 2-byte request.

**`RecordingSpi` test double (not a change to any shipped port):** T3
("uses `SpiBytePort::transfer`, not a hidden bypass") is verified two
ways — a structural grep for `.transfer(` in `icm42688p.cpp` (Python
test), and a Catch2 case using a small, test-local `RecordingSpi`
subclass of `SpiBytePort` that captures the exact TX bytes sent, then
asserts they equal `{0xF5, 0x00}` (`0x75 | 0x80 = 0xF5`). This double
lives only in `test_icm42688p.cpp`, not in any shipped header.

### 2.2 Non-goals (IC §0 decision 2) — confirmed absent

Live SPI1, CS GPIO, full IMU driver, samples into
`FlightControlLoop.step`/`ControlLoop::step`, DShot wire, C30 DFU,
craft↔FS, Assistant, "gyro live" — confirmed by grep (§6) and by this
Buy's own Python test file's structural checks.

---

## 3. Verified — real builds, real test runs

```text
$ cmake --build build/flight_control -j4
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/icm42688p.cpp.o
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 111
```

```text
$ python -m pytest tests/test_fase_c_icm_register_client_b1.py tests/test_fase_c_spi_scripted_gyro_probe_b1.py -v
21 passed
$ python -m pytest -q
3750 passed, 9 skipped
```

Baseline before this Buy: `3741 passed, 9 skipped` (Python), `105/105`
(host `ctest`). Delta: **+9 passed** (Python), **+6** (`ctest`) —
exactly the new test counts, zero regressions, including on C34's own
`probe_rx` cases (all 6 re-verified green, unmodified).

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `spi.hpp`/`spi.cpp` (`SpiBytePort`/`LoopbackSpi`/`ScriptedSpi`) | Untouched — `git diff --stat` empty |
| `spi_probe.hpp`/`spi_probe.cpp` (`probe_rx`, C34) | Untouched — `git diff --stat` empty; kept, not replaced |
| `test_spi.cpp`/`test_spi_probe.cpp` | Untouched — `git diff --stat` empty; all 6 `probe_rx` cases still pass |
| `loop.hpp`/`loop.cpp`/`loop.py`, `plant.hpp`/`plant.cpp`/`plant.py` | Untouched — `git diff --stat` empty |
| `sim_imu_hal.py` | Untouched — `git diff --stat` empty (re-pinned from C34's own freeze check) |
| `sim_executor.py` (C40), `safety.py` (C41) | Untouched — `git diff --stat` empty |
| Safety/craft/registry | Untouched |

No pre-existing test required a disclosed retarget in this Buy — pure
addition, no behavior change to any frozen module.

---

## 5. Tests run

### 5.1 C++ — new Catch2 cases

`native/flight_control/tests/test_icm42688p.cpp` — 6 new `TEST_CASE`s,
tag `[icm42688p][c42]`: T1 (`ScriptedSpi` cited value → match), T2
(`ScriptedSpi` wrong byte → documented mismatch), T3 (exact 2-byte TX
via a recording fake), a `LoopbackSpi` non-false-positive case (IC's
own required output 3), a short-transfer mismatch case, and a constants
sanity check.

```text
100% tests passed out of 111
```

Baseline before this Buy: 105 host tests. Delta: **+6**, exactly the
new `TEST_CASE` count.

### 5.2 Python — new structural module

`tests/test_fase_c_icm_register_client_b1.py` — **9 tests**, covering
IC §2's T3 (structural half), T4, T5, T7 (version), plus CMake-wiring
and no-Python-SPI-port checks mirroring C34's own established pattern
exactly (T1/T2/T6 are the Catch2 behavioral cases above):

| Test | Covers |
|---|---|
| `test_t3_uses_spi_byte_port_transfer_not_a_hidden_bypass` | T3 (structural half) |
| `test_t4_probe_rx_and_c34_ports_untouched` | T4 |
| `test_t5_no_craft_board_edits_and_no_imu_into_step` | T5 |
| `test_cited_who_am_i_constants_present_and_documented` | Output 2 (citation presence) |
| `test_cmake_wires_icm42688p_into_jarvis_fc_and_unit_tests` | Build wiring |
| `test_t7_pyproject_version_is_0_5_43` | T7 (version half) |
| `test_t7_full_suite_process_gate_placeholder` | T7 marker |
| `test_default_safety_gate_still_reject_all` | Regression (C4/C17) |
| `test_no_python_spi_port_added` | C34's own locked precedent, re-pinned |

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/spi.hpp native/flight_control/src/spi.cpp \
    native/flight_control/include/jarvis/fc/spi_probe.hpp native/flight_control/src/spi_probe.cpp \
    native/flight_control/tests/test_spi.cpp native/flight_control/tests/test_spi_probe.cpp \
    src/jarvis/flight_software/flight_control/loop.py src/jarvis/flight_software/flight_control/plant.py \
    src/jarvis/flight_software/flight_control/sim_imu_hal.py \
    src/jarvis/flight_software/autonomy/sim_executor.py src/jarvis/capabilities/safety.py
(empty — every named module byte-unchanged)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
(empty this Buy — no pre-existing craft-geometry diffs remain outstanding at this point)
```

`icm42688p.cpp`'s own real code (comments stripped) contains no
`spi1`/`spi2`/`spi3`/`->dr`/`.dr`/`cmsis`/`gpio`/`nss` token
(`test_t3_...`); no `.py` file under `src/jarvis/flight_software/`
references `read_who_am_i`, `SpiBytePort`, or `icm42688p`
(`test_no_python_spi_port_added`); no `.py` file under `src/jarvis/core`
or `src/jarvis/adapters` references either symbol
(`test_t5_...`).

---

## 7. Files changed

**New:**
- `native/flight_control/include/jarvis/fc/icm42688p.hpp`
- `native/flight_control/src/icm42688p.cpp`
- `native/flight_control/tests/test_icm42688p.cpp`
- `tests/test_fase_c_icm_register_client_b1.py`
- `.jes/artifacts/implementation_report_fase_c_icm_register_client_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (one new source added to `jarvis_fc`; one new test file added to `fc_unit_tests`)
- `pyproject.toml` (`0.5.42` → `0.5.43`)
- 47 pre-existing test files re-pinned from `0.5.42` to `0.5.43`
- `README.md`, `docs/ARCHITECTURE.md` (new paragraph after C41), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §8)

---

## 8. Docs updated (honesty confirmed — not claiming ACCEPT/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.43 includes (LANDED — awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` — new C42 paragraph after the C41 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C42 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C42 table row both changed to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — new paragraph after the C34 paragraph naming `icm42688p.*`, the datasheet citation, and its own disclosed PDF-fetch limitation; layout listing (§ tree) updated with the two new files.

No file in this Buy claims `v0.5.43` is tagged, ACCEPT CLOSED, "gyro
live," "SPI1 works," "WHO_AM_I on copper," "IMU fused into step," or
"we fly." Confirmed via `git tag -l | sort -V | tail -6` at close of
this Buy: `v0.5.37`, `v0.5.38`, `v0.5.39`, `v0.5.40`, `v0.5.41`,
`v0.5.42` — `v0.5.43` does not exist yet.

---

## 9. Residual / next steps

- C43 (craft↔FS bind) is next per the IC's own handoff, after Cursor review + Engineer ★ ACCEPT + tag `v0.5.43`. Assistant/placement work stays PARKED until then.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report) remains unfixed, unrelated to this Buy.
- The datasheet citation's own corroboration path (§2.1) — two independent sources, no direct PDF read — is a disclosed limitation, not a resolved one. If a future Buy gains PDF access, re-confirming the exact section/table number against the primary source would strengthen this citation further, though the address/value pair itself is already corroborated by an independent open-source driver.
- No second register was added (§2.1) — a future Buy adding one should apply the same two-source corroboration bar this Buy held itself to, not merely copy a value from one driver.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T8: ✅ T1/T2/T6 in C++ Catch2 (6/6 passing), T3-T5/T7 in Python (9/9 passing), T8 in this report.
- Cited `WHO_AM_I` client: ✅ named constants (`kIcm42688pRegWhoAmI`, `kIcm42688pWhoAmIValue`), datasheet citation with disclosed corroboration path, no bare magic `0x47`.
- `ScriptedSpi` tests green: ✅ T1/T2 both pass; `LoopbackSpi` non-false-positive case also passes.
- Version `0.5.43`: ✅ `pyproject.toml` + all 47 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions** (live
SPI1, IMU into `step`, craft wiring, "gyro live," uncited magic ID) —
none present, verified above.
