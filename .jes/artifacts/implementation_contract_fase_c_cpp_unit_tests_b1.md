# Implementation Contract — Fase C deepen C++ unit tests (`B1-fase-c-cpp-unit-tests`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (framework ≠ MCU · smokes still green · no GPIO · algorithms unchanged)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.13`**  
**Parents:**
- [C14 ★ ACCEPT](implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md) — steel-ladder module parity CLOSED @ **`v0.5.12`**  
- Engineer 2026-09-21: pick **A — deepen C++ tests** as the next one front  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no MCU, GPIO, Safety-real, ELRS, or craft↔FS in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · Python wooden ladder **retained** · C++ rung sources **behavior-frozen** unless a test exposes a clear bug (then stop and ask)

**Type:** **Implementation Contract** — introduce a **real C++ unit-test harness** under `native/flight_control/` and add **per-rung unit cases** so the steel ladder is checked module-by-module, not only by two hand-rolled smoke mains.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.13`**; git tag **`v0.5.13`** only after Engineer ACCEPT.  
**Not** MCU/cross-compile · Safety-real · ELRS · GPIO/DShot · rewriting Python tests as the SoT · claiming “production-hardened FC” · changing rung math “while we’re here.”

**Outputs (required):**
1. CMake wiring for a unit-test framework (see §0 lock) + `ctest` discovery of the new suite  
2. New C++ unit-test sources under `native/flight_control/tests/` (preferred) covering the six steel rungs + thin plant/quat helpers as needed  
3. Existing `fc_closed_loop_smoke` + `fc_esc_pwm_smoke` **remain** and stay green via `ctest`  
4. Thin pytest wrapper (run `ctest` / unit binary if built · skip-with-build-hint if unbuilt) + Python suite green @ **`0.5.13`**  
5. `.jes/artifacts/implementation_report_fase_c_cpp_unit_tests_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **unit tests ≠ flying / ≠ MCU / ≠ algorithm change**  
7. `pyproject.toml` → **`0.5.13`** (+ re-pin `0.5.12` version-checkpoint tests)

**Checkpoint:** package **`0.5.13`** · Python suite ≥ **3368** + new tests · `ctest` runs smoke **and** unit suite green at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-cpp-unit-tests`** — deepen host C++ verification |
| 2 | One front | Do **not** fold MCU cross-compile, Safety-real, ELRS, GPIO/DShot, or craft↔FS into this Buy |
| 3 | What this Buy demonstrates | `ctest` (or equivalent) runs a **named unit-test binary** with per-rung cases (filter / attitude / controller / rate_torque / mixer / esc at minimum), plus the two existing smokes. **Human:** “dejamos de confiar solo en dos scripts a mano — cada peldaño de acero tiene exámenes propios.” |
| 4 | Framework (locked preferred) | **Catch2 v3** via CMake `FetchContent` with a **pinned** release tag/commit (reproducible). **Acceptable alternate:** **doctest** (also pinned) if Catch2 is painful on the host toolchain — **document choice + pin** in the report. Do **not** invent a third hand-rolled assert harness. |
| 5 | Network at configure | FetchContent may need network **once** at configure time. Document the pin and the offline story (already-populated build dir / cached `_deps`). Do **not** require network to *run* tests after build. |
| 6 | Behavior freeze | **No intentional algorithm changes** in `filter`…`esc`/`plant`/`quat_math`. If a unit test exposes a real bug vs Python guide, **STOP** and surface it — do not “fix while testing” without Engineer call. |
| 7 | Smokes stay | Keep `fc_closed_loop_smoke` and `fc_esc_pwm_smoke`. Do **not** delete them. Optional: thin shared assert helpers, but tip criterion (`15° → ~0.252°` class recovery) must remain green. |
| 8 | Depth (minimum, not full Python parity) | At least **one meaningful `TEST_CASE` (or equivalent) per rung**: filter, attitude, controller, rate_torque, mixer, esc. Plant and/or `quat_math` encouraged but not mandatory if timeboxed. **Not required:** full mirror of every Python pytest in C6–C14. |
| 9 | Path | Stay under **`native/flight_control/`**. Prefer `tests/*.cpp`. No `.cpp` under `src/jarvis/`. |
| 10 | Language / host | C++17 · same CMake project · **host-only** |
| 11 | Version | Bump **`0.5.12` → `0.5.13`**; tag **`v0.5.13`** on ACCEPT only |
| 12 | Forbidden claims | “Production-hardened” · “MCU-ready verified” · “firmware certified” · any GPIO/hardware verification |

**Product sentence:**

```text
Meter un framework de tests C++ de verdad y exámenes por peldaño
en native/flight_control/, sin tocar el algoritmo ni fingir hardware.
```

**Defaults locked by Cursor (Engineer: procede / A):**
- Catch2 v3 preferred (doctest OK with documented pin)  
- Keep both smoke binaries  
- Behavior freeze on rung math  
- Depth = per-rung minimum, not full Python parity  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  CMakeLists.txt              # FetchContent + add_executable(fc_unit_tests …) + ctest
  tests/                      # NEW
    main.cpp                  # optional Catch2 main / or CATCH_CONFIG_MAIN in one TU
    test_filter.cpp           # NEW (names flexible; one file-per-rung preferred)
    test_attitude.cpp
    test_controller.cpp
    test_rate_torque.cpp
    test_mixer.cpp
    test_esc.cpp
    # optional: test_plant.cpp, test_quat_math.cpp
  smoke/                      # UNCHANGED role — both binaries remain
  include/ … src/             # behavior-frozen unless Engineer-approved bugfix
```

Exact filenames may vary; report must list them. Goal: a reviewer can open `tests/` and see rung coverage without hunting inside smoke mains.

---

## 2. Minimum case intent (normative examples — not a full port)

| Rung | Minimum assert spirit (match existing C++ API) |
|---|---|
| filter | First sample seeds; second sample moves toward raw with α (EMA shape) |
| attitude | Level / known tilt update stays finite; or complementary step does not NaN |
| controller | PD from tilted error → body-rate command with expected **sign** on dominant axis |
| rate_torque | Identity / feedforward: rate in → torque-like out finite and same sign |
| mixer | Hover / equal thrust allocation: four forces finite, in `[0,1]` after clamp policy already in API |
| esc | force 0→1000 / 1→2000; disarmed record-but-refuse (may overlap smoke — OK) |

Tolerances: use the same order of magnitude as existing smokes (`1e-9` where exact; looser where integration noise is expected). Document any intentional looseness in the report.

---

## 3. Integration rules

| Existing | C15 rule |
|---|---|
| C13/C14 modules | Link `jarvis_fc`; do not fork duplicate math |
| Smoke binaries | Remain; still registered in `ctest` |
| Python suite | Untouched except version re-pins + new thin wrapper module |
| Craft / RejectAll / autonomy | Untouched |
| MCU / Safety / link | Out of scope |

---

## 4. Tests (minimum gate)

| ID | Check |
|---|---|
| T1 | CMake configures with pinned Catch2 (or doctest) and builds `fc_unit_tests` (name flexible) |
| T2 | Unit suite has ≥1 case each for filter, attitude, controller, rate_torque, mixer, esc |
| T3 | `ctest` (or documented equivalent) runs **unit suite + both smokes** — all green |
| T4 | `fc_closed_loop_smoke` still recovers (same tip class: ~15° → ~0.25°) |
| T5 | No GPIO/DShot/serial/socket call sites introduced; no `.cpp` under `src/jarvis/` |
| T6 | Rung sources byte-unchanged **or** only Engineer-approved bugfix disclosed in report |
| T7 | Thin pytest wrapper: runs ctest/unit+smokes if built · skip-with-build-hint if not |
| T8 | Python full suite green @ **`0.5.13`** |
| T9 | Report lists framework pin, case inventory, honesty statement |
| T10 | Docs honest; no premature `v0.5.13` tag |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| MCU target / cross-compile “while we’re here” | One front |
| Deleting smoke binaries | Tip + ESC visibility retained |
| Quiet algorithm refactors | Behavior freeze |
| Claiming production / certified / hardware-verified | Honesty |
| Vendoring a giant unrelated SDK | Scope |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.13 includes”  
- Explicit: **exists** = host Catch2/doctest unit suite + per-rung cases + smokes; **impossible** = MCU proof, flying vehicle, Safety-real  

---

## 7. Acceptance

**PASS when:** T1–T10 · unit suite green · both smokes green · no GPIO · Python suite green · `0.5.13` · behavior freeze honored (or approved fix disclosed).

**FAIL if:** hand-rolled-only “framework” · smokes deleted/broken · silent math changes · MCU/Safety/link folded in · premature “hardened firmware” claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C15)
Claude   → Catch2/doctest + tests/ + CMake + pytest wrapper + report + 0.5.13
Cursor   → review
Engineer → ACCEPT + tag v0.5.13
Cursor   → next Buy when prioritized
           (still one front: MCU · Safety-real · link · craft↔FS · …)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C14 CLOSED @ v0.5.12. C15 B1-fase-c-cpp-unit-tests READY —
Catch2/doctest + per-rung host unit cases; keep smokes; no MCU/GPIO.
```

---

## 10. Engineer ★ checklist

1. Catch2 v3 preferred (doctest OK with pin) OK?  
2. Per-rung minimum depth (not full Python parity) OK?  
3. Keep both smoke binaries OK?  
4. Behavior freeze on rung math OK?  
5. Version **`0.5.13`** OK?  
