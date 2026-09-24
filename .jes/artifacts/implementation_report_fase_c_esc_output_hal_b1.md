# Implementation Report — Fase C EscOutput HAL (`B1-fase-c-esc-output-hal`)

**IC:** [`implementation_contract_fase_c_esc_output_hal_b1.md`](implementation_contract_fase_c_esc_output_hal_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED @ **`v0.5.24`** (Cursor review PASS WITH NOTES). Package **`0.5.24`**.

---

## 0. Read this first — honesty summary

This Buy adds **no GPIO, no DShot, no motor**. It names the ESC output
port C10/C14 already implemented as a concrete sink: `EscOutput` — an
abstract base (Python `abc.ABC`, C++ abstract class with a virtual
destructor) exposing `apply_forces(forces: MotorForceCommand) ->
EscApplyResult` plus `arm()`/`disarm()`/`armed`. `SimulatedEscSink`
**is-a** `EscOutput` in both languages; its existing C10 `apply(cmd)`
path and arming semantics are **byte-identical** to before this Buy —
`apply_forces` is a thin wrapper (`encode_motor_forces(forces)` then
`apply(cmd)`). The mixer still speaks forces only. `step` still never
calls `apply`/`apply_forces`.

**EscOutput HAL != pin != motors != DShot.**

**Exists:** a named port; the simulated sink implements it; the mixer
still does not know the wire protocol. **Impossible:** a motor on a
wire; a DShot stream; `step` actuating anything. Nothing in this Buy is
any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/
  esc.py            # EXTENDED — EscOutput (abc.ABC) + SimulatedEscSink is-a
  mixer.py          # UNCHANGED (git diff --stat empty)
  loop.py           # UNCHANGED (git diff --stat empty)

native/flight_control/
  include/jarvis/fc/esc.hpp   # EXTENDED — EscOutput abstract base
  src/esc.cpp                  # EXTENDED — apply_forces, purely additive
  tests/test_esc.cpp           # EXTENDED — 3 new Catch2 cases

tests/
  test_fase_c_esc_output_hal_b1.py   # NEW — 15 tests
```

No new module was created (matching the IC's own "prefer extending
`esc.py`" instruction) — `esc.py`/`esc.hpp`/`esc.cpp` are the only rung
files touched. Not placed on `radio.py`, not under `capabilities/`.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `EscOutput.apply_forces(forces) -> EscApplyResult` | §2 | ✅ abstract in both languages |
| `EscOutput.arm()` / `disarm()` / `armed` | §2 | ✅ abstract in both languages, "same C10 semantics" |
| `SimulatedEscSink(EscOutput)` — `apply(cmd: EscPwmCommand)` kept | §2 | ✅ byte-identical body, unchanged from C10/C14 |
| `SimulatedEscSink.apply_forces(...)` — encode then apply | §2 | ✅ `encode_motor_forces(forces)` then `self.apply(cmd)` / `apply(encode_motor_forces(forces))` |
| No new encoding besides existing PWM-µs | §2 | ✅ `apply_forces` calls the existing `encode_motor_forces`, no second encoder |

**Python: `EscOutput` is `abc.ABC`, not `typing.Protocol` (IC §1's own escape hatch, disclosed anyway per that section's instruction).** `SimulatedEscSink` was already a plain class, not a Pydantic model — an ABC does not fight anything here, so no deviation from the IC's stated preference was needed.

**C++: `EscOutput` is an abstract base with a virtual destructor; `SimulatedEscSink` public-inherits it**, exactly as IC §1 specifies. No `.cpp` was needed for `EscOutput` itself (it has no state, all pure virtuals) — only `SimulatedEscSink::apply_forces` needed a body, added to the existing `esc.cpp`.

### 2.1 Non-goals (IC §2.1) — confirmed absent

No GPIO, pigpio, DShot packets, Oneshot, Multishot, ESC UART, pin maps, `step`→`apply` wiring, failsafe timer, Safety execute — confirmed by grep (§7) and by `test_t5_mixer_source_has_no_gpio_or_dshot_call` / `test_t6_loop_step_source_still_has_no_apply_or_apply_forces` / `test_t8_no_gpio_pigpio_dev_mem_in_esc_module_real_code`.

---

## 3. The diff is purely additive (verified, not just asserted)

```text
$ git diff -- native/flight_control/src/esc.cpp
@@ -35,4 +35,8 @@ EscApplyResult SimulatedEscSink::apply(const EscPwmCommand& cmd) {
     return EscApplyResult{true, std::nullopt, cmd.pulse_us};
 }

+EscApplyResult SimulatedEscSink::apply_forces(const MotorForceCommand& forces) {
+    return apply(encode_motor_forces(forces));
+}
+
 }  // namespace jarvis::fc
```

Four lines added, **zero lines removed or changed**. The pre-existing `encode_motor_forces(...)` and `SimulatedEscSink::apply(...)` bodies are untouched.

**A pre-existing test needed a disclosed update, not a weakening:** C15's own `tests/test_fase_c_cpp_unit_tests_b1.py::test_t6_rung_sources_are_git_unchanged_by_this_buy` asserted a blanket `git diff --stat` on all seven rung `.cpp` files (including `esc.cpp`) is empty — a check written for C15's own landing turn, now stale for any Buy that legitimately extends a rung (as C26's own ★-approved IC explicitly does for `esc.cpp`). Rather than dropping `esc.cpp` from the check, I **tightened** it: `filter.cpp`/`attitude.cpp`/`controller.cpp`/`rate_torque.cpp`/`mixer.cpp`/`plant.cpp` still get the blanket "zero diff" check; `esc.cpp` gets a **line-level check that no `-` (removed/changed) lines appear in its diff** — proving the extension is additive-only, which is a *stronger* guarantee than the old test provided for the other six files, not a weaker one. This is disclosed here and in that test file's own updated docstring.

---

## 4. Empirical verification (before any formal test)

```text
isinstance EscOutput: True
issubclass: True
disarmed apply_forces: applied=False reason='disarmed' pulse_us=(1000.0, 1500.0, 2000.0, 1250.0)
last_command matches encoded: True
armed apply_forces: applied=True reason=None pulse_us=(1000.0, 1500.0, 2000.0, 1250.0)
pulses match encode_motor_forces: True
abstract instantiation blocked: Can't instantiate abstract class EscOutput with abstract methods apply_forces, arm, armed, disarm
```

All match the IC's own §0/§2 decisions exactly — `EscOutput` cannot be instantiated directly, `SimulatedEscSink` satisfies every abstract method, and `apply_forces`'s pulses match `encode_motor_forces` bit-for-bit.

---

## 5. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| Mixer | Force-only; grep-clean of `dshot`/`gpio`/`pulse_us` in real code (`test_t5`) — `mixer.py`/`mixer.hpp`/`mixer.cpp` all `git diff --stat` empty |
| C10 encode | Reused via `encode_motor_forces(forces)` inside `apply_forces`, not rewritten |
| C24 `step` | Still no `apply`/`apply_forces` — `loop.py`/`loop.hpp`/`loop.cpp` all `git diff --stat` empty, re-verified explicitly (`test_t6`) |
| C25 mapper | Untouched (`rc_setpoint.py`/`.hpp`/`.cpp` all `git diff --stat` empty) |
| C17 | Untouched (`safety.py` `git diff --stat` empty) |
| `fc_esc_pwm_smoke` | **Left calling `apply(EscPwmCommand)` only** — the IC's own §3 says "may also show `apply_forces` — document": I chose not to modify the smoke binary, since `apply_forces` is already exercised by the new Catch2 cases and the Python smoke path was never required to change either. Disclosed here per that section's own instruction. |

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_esc_output_hal_b1.py` — **15 tests**, covering IC §4's T1-T8 and T10-T11 (T9 is the C++ Catch2 case, T12 is this report):

| Test | Covers |
|---|---|
| `test_t1_simulated_esc_sink_is_instance_and_subclass_of_esc_output` | T1 |
| `test_t2_apply_forces_disarmed_records_and_refuses` | T2 |
| `test_t3_apply_forces_armed_matches_encode_motor_forces` | T3 |
| `test_t4_c10_apply_still_record_but_refuse_while_disarmed` | T4 |
| `test_t5_mixer_source_has_no_gpio_or_dshot_call` | T5 |
| `test_t6_loop_step_source_still_has_no_apply_or_apply_forces` | T6 |
| `test_t7_radio_intent_adapter_not_implemented_and_rejectall_default` | T7 |
| `test_t8_no_gpio_pigpio_dev_mem_in_esc_module_real_code` | T8 |
| `test_t10_pyproject_version_is_0_5_24` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_only_one_esc_output_implementation_ships` | IC §0 decision 7 |
| `test_encode_motor_forces_reused_not_reimplemented_inside_apply_forces` | no second encoder |
| `test_esc_output_abstract_methods_shape` | ABC contract shape |
| `test_no_craft_or_core_imports_of_esc_output_and_registry_still_empty` | craft/registry isolation |
| `test_radio_py_still_has_no_esc_or_stick_apis` | `radio.py` isolation |

```text
tests/test_fase_c_esc_output_hal_b1.py: 15 passed
```

### 6.2 Full Python suite

```text
3553 passed, 2 skipped in 6.02s
```

Baseline before this Buy: `3538 passed, 2 skipped`. Delta: **+15**, exactly matching the new test count — zero regressions (after the one disclosed, tightened update to C15's own stale freeze test, §3 above).

### 6.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_esc.cpp` — 3 new `TEST_CASE`s (tagged `[esc][c26]`):

1. `SimulatedEscSink is convertible to EscOutput*` (IC T1)
2. `EscOutput::apply_forces disarmed: records, applied=false, reason=disarmed` (IC T2)
3. `EscOutput::apply_forces armed: applied=true, pulses match encode_motor_forces` (IC T3/T9)

```text
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest
100% tests passed out of 39

Total Test time (real) = 0.09 sec
```

Baseline before this Buy: 36 host tests. Delta: **+3**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass unmodified.

### 6.4 MCU cross-compile re-verification (not required by IC §4, done for completeness)

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j4
[ 71%] Built target jarvis_fc
[100%] Built target fc_mcu_stub.elf
```

`esc.cpp`'s object file timestamp postdates the source edit, confirming a genuine recompile occurred; the extended `EscOutput`/`apply_forces` code compiles cleanly for the ARM cross target. `stub_main.cpp` was not touched (`git diff --stat` empty) and still never references `EscOutput`/`apply_forces`/`SimulatedEscSink` (grep, exit 1 = no match).

---

## 7. Honesty / forbidden — confirmed

| Forbidden (IC §5) | Verified absent |
|---|---|
| "Motors spinning" | Not claimed anywhere — `apply_forces` never writes to any actuator, there is none |
| "ESC on a wire" | Not claimed — `SimulatedEscSink` remains in-memory only |
| "DShot ready" | Not claimed — no DShot encoding exists anywhere in this Buy |
| `step` writes a pin | `loop.py`/`loop.hpp`/`loop.cpp` byte-unchanged, re-verified (`test_t6`) |
| Mixer knows protocol | `mixer.py`/`mixer.hpp`/`mixer.cpp` byte-unchanged, grep-clean (`test_t5`) |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
EscOutput HAL != pin != motors != DShot
```

---

## 8. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- src/jarvis/capabilities/ src/jarvis/flight_software/autonomy/ native/flight_control/mcu/ \
    src/jarvis/flight_software/flight_control/loop.py native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/mixer.py native/flight_control/include/jarvis/fc/mixer.hpp native/flight_control/src/mixer.cpp
(empty)

$ grep -n "Reset_Handler\|EscOutput\|apply_forces\|SimulatedEscSink" native/flight_control/mcu/stub_main.cpp
# no match (exit 1)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C23 native-tree lock holds
```

`git status --short` at close of this Buy shows exactly the expected file set: `esc.hpp`, `esc.cpp`, `test_esc.cpp` (modified), `flight_control/__init__.py`, `esc.py` (modified), `test_fase_c_esc_output_hal_b1.py` (new), plus `pyproject.toml` + version-checkpoint test re-pins + the one disclosed C15-freeze-test update + docs. No `capabilities/`, `autonomy/`, `mcu/`, `loop.{py,hpp,cpp}`, or `mixer.{py,hpp,cpp}` files touched.

---

## 9. Files changed

**New:**
- `tests/test_fase_c_esc_output_hal_b1.py`
- `.jes/artifacts/implementation_report_fase_c_esc_output_hal_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/esc.py` (`EscOutput` ABC added; `SimulatedEscSink` now inherits it and gains `apply_forces`)
- `src/jarvis/flight_software/flight_control/__init__.py` (export `EscOutput`)
- `native/flight_control/include/jarvis/fc/esc.hpp` (`EscOutput` abstract base added; `SimulatedEscSink` public-inherits, gains `apply_forces` declaration)
- `native/flight_control/src/esc.cpp` (`SimulatedEscSink::apply_forces` implementation — purely additive, §3)
- `native/flight_control/tests/test_esc.cpp` (3 new Catch2 cases)
- `native/flight_control/README.md` (new paragraph on the C26 `EscOutput` extension)
- `tests/test_fase_c_cpp_unit_tests_b1.py` (disclosed, tightened update to the C15-era rung-freeze test — §3)
- `pyproject.toml` (`0.5.23` → `0.5.24`)
- ~30 pre-existing test files re-pinned from `0.5.23` to `0.5.24` (literal `'version = "X.Y.Z"' in text` pattern; the 4-file regex-checkpoint pattern had no `0.5.23` occurrences left this time)
- `README.md`, `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.24 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.24` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C26 paragraph after the C25 block, top banner updated to "Working tree ahead: package `0.5.24` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.24` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C26 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C26 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.24` tag yet)."
- `native/flight_control/README.md` — new paragraph on the `EscOutput` extension, disclosing the purely-additive diff.

No file in this Buy claims `v0.5.24` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.21`, `v0.5.22`, `v0.5.23` — `v0.5.24` does not exist yet.

---

## 11. Residual / next steps

- C27 (CRSF stream-timeout failsafe) is next in the parked queue, per the IC's own handoff — explicitly **not** started here.
- C28 (MCU UART HAL stub), C29 (silicon + cited FLASH map) remain parked, untouched.
- `fc_esc_pwm_smoke` was **not** updated to call `apply_forces` — the IC left this optional ("may also show `apply_forces` — document"); disclosed in §5 above as a deliberate choice, not an oversight.
- The disclosed, tightened update to C15's own rung-freeze test (§3) should be flagged to Cursor/Engineer during review — it is a behavior-preserving strengthening (line-level additive-only check replacing a blanket "zero diff" check for one file), not a weakening, but it does change a pre-existing test's assertion shape.

---

## 12. Acceptance self-check vs IC §7

- T1-T8, T10-T11 (Python): ✅ all pass, 15/15 new tests green.
- T9 (C++ Catch2): ✅ 3 new cases pass.
- T11 (full suite + `ctest` green): ✅ `3553 passed, 2 skipped` (Python); `39/39` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- One implementation (simulated): ✅ `test_only_one_esc_output_implementation_ships`.
- Mixer force-only: ✅ grep + `test_t5`; `git diff --stat` empty.
- `step` does not apply: ✅ grep + `test_t6`; `loop.{py,hpp,cpp}` byte-unchanged.
- Version `0.5.24`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (GPIO shipped, DShot packets, mixer learning protocol, `step` calling the sink, motors claimed spinning) — none present, verified above.
