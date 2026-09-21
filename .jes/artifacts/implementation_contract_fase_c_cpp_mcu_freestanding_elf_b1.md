# Implementation Contract — Fase C MCU freestanding `.elf` (`B1-fase-c-cpp-mcu-freestanding-elf`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (`.elf` ≠ flashed · ≠ GPIO · generic memory map ≠ real board · host green)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.16`**  
**Parents:**
- [C16 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) — `libjarvis_fc.a` for `arm-none-eabi` @ **`v0.5.14`**; ELF/linker/startup deferred  
- [C17 ★ ACCEPT](implementation_contract_fase_c_safety_real_policy_b1.md) — Safety-real CLOSED @ **`v0.5.15`**; Engineer pick **F — MCU `.elf` freestanding**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, GPIO, ELRS, craft↔FS, Safety changes in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · Python wooden ladder **retained** · C++ rung **math behavior-frozen**

**Type:** **Implementation Contract** — first **linked freestanding MCU `.elf`** for `native/flight_control/`: generic Cortex-M4 linker script + minimal startup + thin entry that links `jarvis_fc`, producing an inspectable ARM ELF **without** flashing any board and **without** a vendor BSP.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.16`**; git tag **`v0.5.16`** only after Engineer ACCEPT.  
**Not** OpenOCD/J-Link flash · STM32Cube/CMSIS device pack · GPIO/DShot · semihosting-as-product · claiming the image boots on a real FC · changing host default.

**Outputs (required):**
1. Generic **linker script** + **minimal startup** (`Reset_Handler` → `main`) under `native/flight_control/` (preferred: `mcu/` or `cmake/…` — document layout)  
2. Thin **MCU entry** TU that links `jarvis_fc` and exercises at least one non-hardware API (see §0)  
3. CMake MCU path builds a named **`.elf`** target (separate from host); `libjarvis_fc.a` may still build  
4. Host default build + `ctest` still green  
5. Thin pytest: toolchain present → configure+build + assert `.elf` is ARM (objdump/readelf); absent/incomplete → skip-with-hint (same honesty as C16)  
6. `.jes/artifacts/implementation_report_fase_c_cpp_mcu_freestanding_elf_b1.md`  
7. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **`.elf` ≠ flashed / ≠ runs on FC / ≠ GPIO**  
8. `pyproject.toml` → **`0.5.16`** (+ re-pin `0.5.15` version-checkpoint tests)

**Checkpoint:** package **`0.5.16`** · Python suite ≥ **3403** + new tests · host `ctest` green · MCU `.elf` produced when full toolchain present (or skip path documented + implementer evidence)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-cpp-mcu-freestanding-elf`** — first freestanding linked `.elf` |
| 2 | One front | Do **not** fold flash scripts, GPIO/DShot, ELRS, craft↔FS, Safety policy changes, or vendor BSP into this Buy |
| 3 | What this Buy demonstrates | With a full `arm-none-eabi` toolchain, Jarvis can **link** a freestanding Cortex-M4-class image that includes `jarvis_fc`. **Human:** “ya no es solo una caja de objetos — es un programa ARM que puedes mirar con `objdump`, aún sin enchufar la placa.” |
| 4 | Reuse C16 toolchain | Keep **`cmake/toolchains/arm-none-eabi.cmake`** (Cortex-M4 / thumb / soft-float). Extend CMake gating as needed; do not invent a second CPU class in this Buy. |
| 5 | Memory map (locked honesty) | Linker script uses a **generic fictional** FLASH/RAM layout (sizes documented in script comments — e.g. 256 KiB FLASH / 64 KiB RAM class). **Explicitly not** a claim of any named board’s silicon or memory map. |
| 6 | Artifact (locked minimum) | Produce a named ELF (e.g. `fc_mcu_stub.elf` — name flexible if documented) with a defined entry/`Reset_Handler`. Optional `.bin` via `objcopy` is nice-to-have, not required. |
| 7 | Entry behavior (locked minimum) | `main` (or equivalent) must **call into `jarvis_fc`** at least once in a way that pulls real ladder symbols (e.g. construct `ImuLowPassFilter` and filter one sample, or `encode_motor_forces` on a trivial force vector). Infinite idle loop after that is OK. **No** UART/GPIO/printf-to-hardware requirement. |
| 8 | C++ runtime / exceptions | Rung sources may `throw`. Acceptable resolutions (document choice in report): (a) link toolchain **libstdc++/newlib** (or nano) with minimal syscall stubs (`_sbrk`/`_exit`/…), or (b) MCU-only compile flags such as `-fno-exceptions` **without** changing source math — prefer (a) if it keeps sources untouched. Do **not** rewrite rung APIs to remove throws “while we’re here.” |
| 9 | No vendor BSP | **Forbidden** as required deps: STM32Cube, CMSIS device packs, ChibiOS, FreeRTOS, PX4, ArduPilot, libopencm3 tree. Startup + linker script + stubs are **ours**, generic. |
| 10 | No flash / no GPIO | **Forbidden:** OpenOCD/J-Link product flash path, pin drivers, DShot, board bring-up as acceptance. |
| 11 | Host remains default | Host configure/build/`ctest` unchanged in role and green. MCU ELF is additive under the cross toolchain build dir. |
| 12 | Toolchain missing / incomplete | Same C16 honesty: skip-with-hint if no full toolchain (bare brew without libstdc++ must not hard-fail the suite). Prefer a successful ELF build in the implementer report when a full toolchain is available. |
| 13 | Behavior freeze | No intentional rung math changes. |
| 14 | Version | Bump **`0.5.15` → `0.5.16`**; tag **`v0.5.16`** on ACCEPT only |
| 15 | Forbidden claims | “Boots on STM32/Betaflight FC” · “flashed and verified” · “production firmware” · “GPIO live” |

**Product sentence:**

```text
Enlazar un .elf freestanding Cortex-M4 genérico (startup + linker +
stub que llama a jarvis_fc) — inspectable en el Mac, sin flashear ni
BSP de fabricante.
```

**Defaults locked by Cursor (Engineer: procede / F):**
- Reuse C16 `arm-none-eabi` toolchain  
- Generic fictional memory map (disclosed)  
- Thin entry that calls into `jarvis_fc`  
- No flash · no vendor BSP · host stays default  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  cmake/toolchains/arm-none-eabi.cmake   # EXISTING (C16) — reuse
  CMakeLists.txt                         # + MCU ELF target when cross-compiling
  mcu/                                   # NEW preferred
    linker_cortex_m4.ld                  # generic FLASH/RAM (fictional map)
    startup_cortex_m4.S                  # or .c — Reset_Handler → main
    syscalls_stub.c                      # optional — newlib stubs if needed
    stub_main.cpp                        # calls into jarvis_fc, then idle
  README.md                              # + ELF build/inspect commands
```

Exact filenames may vary; report must list them and the CMake target name.

---

## 2. Build / inspect commands (normative examples)

```bash
# MCU path (full toolchain on PATH — e.g. xPack)
cmake -S native/flight_control -B build/flight_control_mcu \
  --toolchain "$(pwd)/native/flight_control/cmake/toolchains/arm-none-eabi.cmake"
cmake --build build/flight_control_mcu --target <elf_target>

arm-none-eabi-objdump -f build/flight_control_mcu/<elf_name>
arm-none-eabi-readelf -h build/flight_control_mcu/<elf_name>   # Machine: ARM, Entry point present
```

Host path must still:
```bash
cmake -S native/flight_control -B build/flight_control && cmake --build build/flight_control
cd build/flight_control && ctest --output-on-failure
```

---

## 3. Integration rules

| Existing | C18 rule |
|---|---|
| C16 `.a` path | Keep; ELF is additive |
| Host Catch2 + smokes | Remain green |
| Rung sources | Math frozen |
| Safety (C17) / craft / radio | Untouched |
| Flash / GPIO / BSP | Out of scope |

---

## 4. Tests (minimum gate)

| ID | Check |
|---|---|
| T1 | Linker script + startup + stub entry exist under `native/flight_control/` |
| T2 | When full toolchain present: MCU build produces `.elf`; `objdump`/`readelf` show ARM + entry point |
| T3 | ELF links symbols from `jarvis_fc` (nm/objdump evidence in test or report) |
| T4 | When toolchain absent/incomplete: pytest skips with install hint (suite does not fail) |
| T5 | Host `ctest` still green; tip class ~15°→~0.25° |
| T6 | No OpenOCD/flash product scripts; no vendor BSP required; no GPIO drivers |
| T7 | No `.cpp` under `src/jarvis/` from this Buy; craft isolation |
| T8 | Report lists layout, memory-map honesty, runtime link strategy (libstdc++ vs flags), inspect commands |
| T9 | Docs honest; no premature `v0.5.16` tag |
| T10 | Python full suite green @ **`0.5.16`** |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| “Runs on board X” / flash acceptance | No hardware |
| Vendor Cube/RTOS required | Scope |
| Quiet rung refactors | Behavior freeze |
| Breaking host default | Process |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.16 includes”  
- Explicit: **exists** = inspectable freestanding ARM `.elf` linking `jarvis_fc`; **impossible** = flashed FC, motors, GPIO, “boots on hardware”  

Update Parked: MCU `.elf` moves from parked → this Buy.

---

## 7. Acceptance

**PASS when:** T1–T10 · ELF built (or honest skip + implementer evidence) · host green · no flash/BSP/GPIO · `0.5.16`.

**FAIL if:** host broken · vendor SDK required · flash claimed · “runs on FC” claim · silent math changes.

---

## 8. Handoff

```text
Engineer → ★ this IC (C18)
Claude   → linker + startup + stub + CMake ELF target + pytest + report + 0.5.16
Cursor   → review
Engineer → ACCEPT + tag v0.5.16
Cursor   → next Buy when prioritized
           (still one front: flash later · link · craft↔FS · …)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C17 CLOSED @ v0.5.15. C18 B1-fase-c-cpp-mcu-freestanding-elf READY —
generic Cortex-M4 linker+startup+stub ELF linking jarvis_fc; no flash/BSP.
```

---

## 10. Engineer ★ checklist

1. Freestanding `.elf` (not just `.a`) OK?  
2. Generic fictional memory map (not a named board) OK?  
3. Stub must call into `jarvis_fc` OK?  
4. No flash / no vendor BSP / host stays default OK?  
5. Skip-with-hint if toolchain incomplete OK?  
6. Version **`0.5.16`** OK?  
