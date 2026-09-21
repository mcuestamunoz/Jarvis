# Implementation Contract — Fase C MCU cross-compile scaffold (`B1-fase-c-cpp-mcu-cross-compile`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (cross-compile ≠ flashing · ≠ GPIO · host path still green · no board SDK creep)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.14`**  
**Parents:**
- [C15 ★ ACCEPT](implementation_contract_fase_c_cpp_unit_tests_b1.md) — Catch2 host unit suite CLOSED @ **`v0.5.13`**  
- Engineer 2026-09-21: pick **B — MCU / cross-compile** as the next one front  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real, ELRS, craft↔FS, or GPIO product path in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · Python wooden ladder **retained** · C++ rung **math behavior-frozen**

**Type:** **Implementation Contract** — first **MCU-oriented cross-compile scaffold** for `native/flight_control/`: a documented CMake toolchain that builds the steel-ladder library for an ARM bare-metal triple, **without** flashing a board, without a vendor BSP, and without GPIO/PWM peripherals.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.14`**; git tag **`v0.5.14`** only after Engineer ACCEPT.  
**Not** OpenOCD/flash scripts as product · STM32Cube/ChibiOS/FreeRTOS import · GPIO/DShot drivers · Safety-real · ELRS · claiming “firmware runs on a flight controller” · replacing the host default build.

**Outputs (required):**
1. CMake **toolchain file** under `native/flight_control/` (preferred path: `cmake/toolchains/arm-none-eabi.cmake` or equivalent documented) targeting **`arm-none-eabi`** with a locked CPU (see §0)  
2. Documented configure+build commands that produce a **cross-built `jarvis_fc` static library** (`.a`) for that triple  
3. Host default build (`cmake -S native/flight_control -B build/flight_control`) **unchanged in role** and still green (smokes + unit suite)  
4. Thin pytest wrapper: if `arm-none-eabi-g++` (or documented compiler) is present → configure+build MCU tree and assert artifact exists; if absent → **skip with install hint** (do not fail the whole Python suite)  
5. `.jes/artifacts/implementation_report_fase_c_cpp_mcu_cross_compile_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **cross-compile ≠ flashed · ≠ flying · ≠ GPIO**  
7. `pyproject.toml` → **`0.5.14`** (+ re-pin `0.5.13` version-checkpoint tests)

**Checkpoint:** package **`0.5.14`** · Python suite ≥ **3380** + new tests · host `ctest` still green · MCU `.a` produced when toolchain present (or skip path documented and exercised in report)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-cpp-mcu-cross-compile`** — first MCU cross-compile scaffold |
| 2 | One front | Do **not** fold Safety-real, ELRS, craft↔FS, GPIO/DShot product drivers, or board bring-up/flash into this Buy |
| 3 | What this Buy demonstrates | With an ARM bare-metal toolchain installed, Jarvis can **cross-compile** `jarvis_fc` for an MCU-class triple. **Human:** “por fin compilamos el acero *como si* fuera para el chip — aún sin enchufar la placa ni tocar un pin.” |
| 4 | Triple / CPU (locked) | Toolchain: **`arm-none-eabi`**. CPU flags locked preferred: **`-mcpu=cortex-m4 -mthumb`** (generic Cortex-M4 class used by many FCs — **not** a claim of any specific board). Document exact flags in README/report. |
| 5 | Artifact (locked minimum) | Produce **`libjarvis_fc.a`** (or CMake’s equivalent static archive) in a **separate** build directory (e.g. `build/flight_control_mcu`). **Full linked `.elf` + linker script + startup is optional** and must not pull a vendor SDK; if omitted, say so honestly. |
| 6 | Host remains default | Default docs/commands stay **host**. Cross build is an **additive** path via `--toolchain` / `-DCMAKE_TOOLCHAIN_FILE=…`. Host smokes + Catch2 suite must remain green. |
| 7 | Catch2 on MCU | **Do not** FetchContent/build Catch2 for the MCU target in this Buy (heavy / host-oriented). MCU path builds the **library** (and optional tiny freestanding stub), not the unit-test binary. |
| 8 | No vendor BSP | **Forbidden:** STM32Cube, CMSIS device packs as a required dependency, ChibiOS, FreeRTOS, PX4, ArduPilot, libopencm3 as a required tree. Pure toolchain + our sources. |
| 9 | No flash / no GPIO | **Forbidden:** OpenOCD/J-Link flash scripts as acceptance, `gpio`/`pigpio`/`TIM` PWM drivers, DShot, serial bring-up. Toolchain comments may mention future flash — no product path. |
| 10 | Toolchain missing | Dev machines without `arm-none-eabi-g++`: pytest **skips** MCU build tests with a clear install hint (e.g. Homebrew `gcc-arm-embedded` / distro package). Report must still show a successful cross-build on a machine that has the toolchain **or** document that CI/dev verification used skip — prefer at least one successful cross-build in the implementer’s report. |
| 11 | Behavior freeze | No intentional changes to rung math. CMake may gate host-only targets (Catch2, smoke executables) when cross-compiling. |
| 12 | Version | Bump **`0.5.13` → `0.5.14`**; tag **`v0.5.14`** on ACCEPT only |
| 13 | Forbidden claims | “Runs on Betaflight/iNav FC” · “flashed and verified on hardware” · “production firmware” · “GPIO verified” |

**Product sentence:**

```text
Añadir un toolchain CMake arm-none-eabi (Cortex-M4 genérico) que compile
la librería jarvis_fc para MCU — sin flashear, sin BSP de fabricante y
sin GPIO — dejando el build host como camino por defecto.
```

**Defaults locked by Cursor (Engineer: procede / B):**
- `arm-none-eabi` + Cortex-M4 thumb flags  
- Separate MCU build dir; static lib minimum  
- No Catch2 on MCU; no vendor BSP; no flash  
- Skip-with-hint if toolchain absent  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  cmake/toolchains/arm-none-eabi.cmake   # NEW (path flexible if documented)
  CMakeLists.txt                         # gate: when cross-compiling, skip Catch2/smoke executables (or equivalent)
  README.md                              # host + MCU configure commands + toolchain install hint
  include/ … src/                        # behavior-frozen
  tests/ smoke/                          # host-only; not required on MCU build
```

---

## 2. Build commands (normative examples — adjust paths in report)

**Host (must stay green):**
```bash
cmake -S native/flight_control -B build/flight_control
cmake --build build/flight_control
cd build/flight_control && ctest --output-on-failure
```

**MCU cross (additive):**
```bash
cmake -S native/flight_control -B build/flight_control_mcu \
  --toolchain native/flight_control/cmake/toolchains/arm-none-eabi.cmake
cmake --build build/flight_control_mcu --target jarvis_fc
# assert: libjarvis_fc.a (or equivalent) exists and `file`/`arm-none-eabi-objdump` shows ARM
```

Exact toolchain filename may vary; report must paste the working commands.

---

## 3. Integration rules

| Existing | C16 rule |
|---|---|
| Host Catch2 + smokes | Remain; still green on host build |
| Rung sources | Math frozen; optional `#ifdef` only if unavoidable — prefer CMake gating |
| Python suite | Version re-pins + new thin MCU wrapper only |
| Craft / RejectAll / autonomy | Untouched |
| Safety / link / GPIO drivers | Out of scope |

---

## 4. Tests (minimum gate)

| ID | Check |
|---|---|
| T1 | Toolchain file exists and sets `CMAKE_SYSTEM_NAME` / compilers for `arm-none-eabi` + locked CPU flags |
| T2 | When toolchain present: MCU configure+build produces static `jarvis_fc` archive; artifact is ARM (objdump/file) |
| T3 | When toolchain absent: pytest skips with install hint (suite does not fail) |
| T4 | Host build + `ctest` (unit + both smokes) still green; tip class ~15°→~0.25° |
| T5 | No GPIO/DShot/flash/OpenOCD product scripts; no vendor BSP required |
| T6 | No `.cpp` under `src/jarvis/`; craft isolation |
| T7 | Report lists toolchain pin/flags, artifact path, honesty statement, skip story |
| T8 | Python full suite green @ **`0.5.14`** |
| T9 | Docs honest; no premature `v0.5.14` tag |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| “Firmware verified on hardware” | Not this Buy |
| Flash CI as acceptance | One front / no lab claim |
| Vendor Cube/RTOS required | Scope |
| GPIO/PWM/DShot drivers | Hardware |
| Breaking host default path | Process |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.14 includes”  
- Explicit: **exists** = cross-compile recipe + ARM `.a` when toolchain installed; **impossible** = board runs code, motors spin, Safety-real  

---

## 7. Acceptance

**PASS when:** T1–T9 · host green · MCU `.a` when toolchain present (or honest skip + implementer evidence) · no BSP/flash/GPIO · `0.5.14`.

**FAIL if:** host broken · vendor SDK required · flash claimed as done · GPIO drivers shipped · “runs on FC” claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C16)
Claude   → toolchain file + CMake gating + README + pytest + report + 0.5.14
Cursor   → review
Engineer → ACCEPT + tag v0.5.14
Cursor   → next Buy when prioritized
           (still one front: Safety-real · link · craft↔FS · board flash later · …)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C15 CLOSED @ v0.5.13. C16 B1-fase-c-cpp-mcu-cross-compile READY —
arm-none-eabi Cortex-M4 toolchain; jarvis_fc.a; no flash/GPIO/BSP.
```

---

## 10. Engineer ★ checklist

1. `arm-none-eabi` + Cortex-M4 (generic, not a board claim) OK?  
2. Static lib minimum (ELF optional, no vendor SDK) OK?  
3. Host remains default + must stay green OK?  
4. Skip-with-hint if toolchain missing OK?  
5. Version **`0.5.14`** OK?  
6. Explicit: **not** flash / **not** GPIO / **not** “runs on FC” OK?  
