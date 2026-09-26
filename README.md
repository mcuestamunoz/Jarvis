# Jarvis

**v0.5.40 tagged tip** · C39 position loop ★ ACCEPT CLOSED — sim position + xy→tilt · C38 altitude ★ ACCEPT CLOSED — still not live GPS, still not flying

Deterministic engineering engine for designing physical systems with AI-assisted natural language.

Jarvis is **aerial-first** (drones and related vehicles): you describe goals and components in Spanish; calculation and simulation stay rule-based and auditable. The model may interpret — it does not invent the physics.

Read the one-page contract: [VISION.md](VISION.md).

**Fase C (platform scaffold) in plain language:** what “scaffold” means and what each new package is for — [ARCHITECTURE.md §1a](docs/ARCHITECTURE.md).

## Quick start

```bash
git clone https://github.com/mcuestamunoz/Jarvis.git
cd Jarvis
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,mcp]"
```

**CLI chat** (optional: local [Ollama](https://ollama.com) for `analyze` / free-form interpret):

```bash
python -m jarvis.main --chat
# or
jarvis --chat
```

**Pizarra** (visor 3D + Continuity spatial assembly; huecos de arquitectura = slots, no BOM; mutación = CLI / Continuity / Situar drag):

```bash
jarvis board
```

**Tests:**

```bash
pytest
```

**MCP server** (Cursor / MCP clients):

```bash
python -m jarvis.adapters.mcp.server
```

Workspace projects live under `workspace/` (override with `JARVIS_WORKSPACE_ROOT`).  
Ollama defaults: `JARVIS_OLLAMA_BASE_URL`, `JARVIS_OLLAMA_MODEL` (see `src/jarvis/config.py`).

## What v0.5.30 includes

Fase C · **C32** (`B1-fase-c-mcu-spi-hal-stub`) — **the SPI port got a name, still not the gyro**:

- New `native/flight_control/include/jarvis/fc/spi.hpp`/`src/spi.cpp`: `SpiBytePort` — an abstract base with a virtual destructor exposing `transfer(tx, rx, n) -> size_t` (copies up to `n` bytes from TX into RX, in order, never blocks) — and `LoopbackSpi`, the **only** implementation: RX = TX, default capacity `256`.
- A transfer past capacity **returns a short count** rather than growing unbounded — same overflow policy `LoopbackUart` (C28) already uses. Unlike `LoopbackUart`'s own persistent FIFO, `LoopbackSpi` carries **no state between calls** — a real SPI transfer is a single synchronous exchange, not a stream.
- **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA** anywhere in either file.
- The desk FC's own gyro (when later wired) is an **ICM42688P** on SPI — cited only as desk identity in a comment, never in real code: no `WHO_AM_I` read, no register map, no sample.
- `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30), and `uart.hpp`/`uart.cpp` (C28) all stay byte-identical — idle is still only PC13, no SPI poll in `main`. `SimulatedImuHal` (C3) untouched.
- **MCU SPI stub != chip SPI != gyro live != flying.** A named SPI byte port exists; an in-memory loopback implements it.
- Package **`0.5.30`** · tagged **`v0.5.30`** · suite **3649** · host `ctest` **60/60** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_mcu_spi_hal_stub_b1.md)
- **Next:** C33 CLOSED @ **`v0.5.31`**.

## What v0.5.31 includes

Fase C · **C33** (`B1-fase-c-spi-scripted-slave`) — **a second `SpiBytePort`: canned RX, not TX echo, still not the gyro**:

- Extends the existing `native/flight_control/include/jarvis/fc/spi.hpp`/`src/spi.cpp` (no new file) with `ScriptedSpi`, a second `SpiBytePort` implementation — `LoopbackSpi` (C32) stays byte-behavior-unchanged.
- `ScriptedSpi(canned_rx)` fills `rx[0..accepted)` from a pre-loaded byte script, **never** from `tx` — this is how a test pretends "a device answered" without any real chip. `set_next_rx(...)` reprograms the script for subsequent transfers; each `transfer(...)` call fills RX from the start of the currently-loaded script (a fixed canned response, not a consuming stream across calls).
- Same overflow policy as `LoopbackSpi`/`LoopbackUart`: a script shorter than the requested `n` **returns a short count**, and the untouched tail of `rx` is left exactly as the caller passed it in.
- **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA**, zero CRSF/ELRS tokens anywhere in `native/`. `WHO_AM_I`/`ICM42688P` appear only in comments (e.g. "a future gyro test could load `0x47` here"), never in real code.
- `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), and `uart.hpp`/`uart.cpp` (C28) all stay byte-identical — no SPI poll in `main`.
- **Scripted SPI != gyro live != chip SPI != flying.** A canned-RX test double exists. Nothing here reads a real device.
- Package **`0.5.31`** · tagged **`v0.5.31`** · suite **3667** · host `ctest` **66/66** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_spi_scripted_slave_b1.md)
- **Next:** C34 CLOSED @ **`v0.5.32`**.

## What v0.5.32 includes

Fase C · **C34** (`B1-fase-c-spi-scripted-gyro-probe`) — **a client of `SpiBytePort`, not a gyro driver**:

- New `native/flight_control/include/jarvis/fc/spi_probe.hpp`/`src/spi_probe.cpp`: `probe_rx(SpiBytePort& port, uint8_t* rx, size_t n) -> size_t` — sends `n` dummy **zero** TX bytes (never a register address) and returns whatever `port.transfer(...)` moves into `rx`. `n == 0` returns `0`. `spi.hpp`/`spi.cpp` (C32/C33) get **zero edits** — the port stays the port, `spi_probe.*` is the first caller.
- On `ScriptedSpi` (C33) loaded with a placeholder fixture byte, `probe_rx` returns that byte — proving the RX path end-to-end. On `LoopbackSpi` (C32), `probe_rx` returns all-zeros (the dummy TX echoed back) — proving the client is port-shaped, not tied to one implementation.
- Same overflow policy as the port itself: a script shorter than `n` **returns a short count**, untouched tail of `rx` left exactly as passed in.
- **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA, zero CRSF/ELRS tokens** anywhere in `native/`. `WHO_AM_I`/`ICM42688P`/register address `0x75` do not appear anywhere in `spi_probe.*`, not even in a comment — the fixture byte itself lives in tests only, never in library code.
- `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `uart.hpp`/`uart.cpp` (C28), and `loop.hpp`/`loop.cpp`/`loop.py` (C3/C4) all stay byte-identical — no probe poll in `main`, no IMU-into-`step` wiring.
- **Scripted gyro probe != gyro live != chip SPI != WHO_AM_I != flying.** A byte-probe client exists. Nothing here reads a real device or claims an identity register.
- Package **`0.5.32`** · tagged **`v0.5.32`** · suite **3679** · host `ctest` **72/72** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_spi_scripted_gyro_probe_b1.md)
- **Next:** Taller CSS [`B1-geometry-taller-css-cuboid-faces`](.jes/artifacts/implementation_contract_geometry_taller_css_cuboid_faces_b1.md) READY — six faces on a thin plate (visor, not CAD). Cola: standoff points. DShot wire / C30 DFU parked until bench.

## What v0.5.33 includes

Fase C · **C35** (`B1-fase-c-step-failsafe-hold-ticks`) — **tests only: many ticks, still not flying**:

- **No production code changed.** `loop.py`/`loop.hpp`/`loop.cpp`, `rc_hold.hpp`/`rc_hold.cpp`, `crsf_failsafe.py`, and `spi_probe.hpp`/`spi_probe.cpp` are all byte-unchanged — this Buy only chains the EXISTING `ControlLoop::step`/`FlightControlLoop.step` and `RcHoldWatch`/`CrsfRcHoldWatch` + `failsafe_loop_inputs` more times, and in a new combination.
- New tests (Python + 4 new Catch2 cases in `test_loop.cpp`): **1000** `step()` ticks with a canned level IMU sample (`accel ≈ (0,0,-9.81)`, gyro zeros) and no plant — every tick's four motor forces stay finite and in `[0, 1]`.
- A **stale** hold watch (never noted, or past the 0.5 s timeout) feeds `failsafe_loop_inputs(t)` into that same `step()` — `collective` passed in is `0`, forces still finite and in `[0, 1]`. No `EscOutput`/GPIO call anywhere in the new tests.
- "Hold" means feeding `level_setpoint` for those N ticks, not `AutonomyVerb.HOLD` reaching execution — `submit_command(HOLD)` still returns `execution="not_attempted"` under the default `RejectAllSafetyGate`, re-asserted explicitly.
- `probe_rx` (C34) is **not** used as an IMU source anywhere in these tests — the canned IMU sample is a plain struct literal, same as every prior Buy on this axis.
- **Many ticks != flying != 6-DoF. Failsafe -> step != motors cut != HOLD executed.** A thousand ticks of `step()` on canned IMU, and a stale-RC path into the same `step()`, both exist. Nothing here is a flying plant, a motor cut, or an executed autonomy command.
- Package **`0.5.33`** · tagged **`v0.5.33`** · suite **3691** · host `ctest` **76/76** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_step_failsafe_hold_ticks_b1.md)
- **Next:** Taller CSS cylinder faces ★ ACCEPT CLOSED @ **`v0.5.35`**. D2 docs LANDED @ package `0.5.36` (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet). Cola: standoff points. DShot wire / C30 DFU parked until bench.

## What v0.5.34 includes

Geometry / visor · **`B1-geometry-taller-css-cuboid-faces`** — **six box faces stop exploding on a thin plate, still not CAD**:

- **UI/CSS visor fix, not a Fase C flight-software Buy.** New pure helper `ui/spatial-board/src/cuboidFaces.ts` — `cuboidFaceLayout(w, d, h)` — returns six `{name, width, height, left, top, transform}` entries; `Solid3D.tsx`'s `box` branch now maps them onto the six `.sb-solid__face` nodes instead of hardcoding six transform strings inline.
- Root cause: each face sat at the `.sb-solid__face` CSS default `left: 0; top: 0`. `front`/`back` match the wrapper's own `w x h` size so they were never wrong, but `left`/`right` (width `d`) and `top`/`bottom` (height `d`) do not — with `transform-origin: 50% 50%` (never overridden), an off-center face rotates about the wrong point and swings out, worst on a thin plate.
- Fix: center every face first (`left: (w-fw)/2`, `top: (h-fh)/2`), **then** rotate, **then** `translateZ(half-extent along that face's own normal)`. Still exactly **six** `.sb-solid__face` nodes — no seventh, no CAD, no fit verdict.
- Verified against the MY5 top-plate fixture (`161x42x2mm`, `pxPerMm 0.5` -> `80.5x21x1`px): `top`/`bottom` center to `translateZ(0.5px)`, `left`/`right` to `translateZ(40.25px)`, and no face's transform string contains `translateX`/`translateY` — centering lives entirely in `left`/`top`, never in the transform.
- Cylinder/disk branches in `Solid3D.tsx`, the projector, the `geometry` DTO, and `spatial_board.py` all stay **byte-unchanged** — `git diff --stat` empty.
- **Visor cuboid != CAD != fit != extra parts != a 2D card's own origin.** Six CSS faces that meet on a thin declared box exist. Nothing here is a machined plate, a fit verdict, or a seventh part.
- Package **`0.5.34`** · tagged **`v0.5.34`** · UI vitest **136/136** · `tsc --noEmit` clean · Python suite **3691** (unchanged — no new Python tests) — ★ ACCEPT CLOSED (Engineer Taller smoke 2026-09-25) — [review](.jes/artifacts/implementation_review_geometry_taller_css_cuboid_faces_b1.md)
- **Next:** Taller CSS cylinder faces ★ ACCEPT CLOSED @ **`v0.5.35`**. D2 docs [`B1-docs-truth-sync-after-c35`](.jes/artifacts/implementation_contract_docs_truth_sync_after_c35_b1.md) READY. Cola: standoff points.

## What v0.5.35 includes

Geometry / visor · **`B1-geometry-taller-css-cylinder-faces`** — **caps + 16 slats stop exploding on a short/tall cylinder, still not CAD**:

- **UI/CSS visor fix, not a Fase C flight-software Buy** — same fix, same class of bug, as the cuboid Buy that shipped @ `v0.5.34`. New pure helper `ui/spatial-board/src/cylinderFaces.ts` — `cylinderSolidLayout(diameterPx, heightPx)` — returns `{caps, slats}`: 2 caps and 16 side slats, each `{width, height, left, top, transform}`; `Solid3D.tsx`'s `cylinder` branch now maps them onto the `.sb-solid__disk-face`/`.sb-solid__face` nodes instead of hardcoding the transforms inline.
- Root cause: each `D x D` cap sat at the CSS default `left: 0; top: 0` on a `D x H` wrapper — correct only when `H == D`. With `transform-origin: 50% 50%` (never overridden), a short prop hub (`H << D`) or a tall standoff-shaped post (`H >> D`) rotates each cap about the wrong point and it swings off axis. The 16 side slats already re-centered horizontally before this Buy — that part was already correct and is reused unchanged, just relocated into the new helper.
- Fix: center each cap first (`left: 0`, `top: (H-D)/2` — negative when `H < D`), **then** rotate, **then** `translateZ(H/2)` — never `translateY` again after centering. Still exactly **2** caps and **16** slats (N frozen) — no 17th face, no invented diameter or height.
- Verified against a short-hub fixture (Ø130.72 x 6.8mm -> px `65.36x3.4`, cap `top=-30.98`, `translateZ(1.7px)`) and a tall-post fixture (Ø6 x 30mm -> px `3x15`, cap `top=6`, `translateZ(7.5px)`) — both directions of the bug, not just the thin-plate case. No cap or slat transform string contains `translateX`/`translateY`.
- `cuboidFaces.ts` (the box helper), the disk branch, `SCENE3D.pxPerMm`, the projector, the `geometry` DTO, and `spatial_board.py` all stay **byte-unchanged** — `git diff --stat` empty on every one of them.
- **Visor cylinder != CAD != fit != extra parts != round metal != a standoff hole pattern.** 2 CSS caps + 16 CSS slats that meet on a declared Ø x H exist. Nothing here is a turned standoff, a prop hub from the mill, or a fit verdict.
- Package **`0.5.35`** · tagged **`v0.5.35`** · UI vitest **142/142** · `tsc --noEmit` clean · Python suite **3691** (unchanged — no new Python tests) — ★ ACCEPT CLOSED (Engineer Taller smoke 2026-09-25) — [review](.jes/artifacts/implementation_review_geometry_taller_css_cylinder_faces_b1.md)
- **Next:** D2 docs LANDED @ package **`0.5.36`** (awaiting Cursor review + Engineer ★ ACCEPT, no `v0.5.36` tag yet) — [`B1-docs-truth-sync-after-c35`](.jes/artifacts/implementation_contract_docs_truth_sync_after_c35_b1.md) · [report](.jes/artifacts/implementation_report_docs_truth_sync_after_c35_b1.md). Cola: standoff points.

## What v0.5.36 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.36` tag yet)

Docs · **`B1-docs-truth-sync-after-c35`** — **maps and READMEs now name the same tip as `ARCHITECTURE.md`**:

- **Docs-only Buy** — no `src/`, `ui/`, or `library/` product edits. A Phase 0 inventory (`.jes/artifacts/inventory_docs_truth_sync_after_c35_b0.md`, one row per in-scope file) was written and gated before any Phase 1 edit, per the IC's own STOP-before-bulk-edits rule.
- `docs/system_map/README.md` and `JARVIS_SYSTEM_MAP.md`'s own "Fase C" section stopped naming tip `v0.5.3`/suite `3236` (a snapshot from C1-C5, 2026-09-20) as current — both now name tip `v0.5.35`, live suite/UI/ctest counts, and point at `ARCHITECTURE.md` §1c / `PLATFORM_CAPABILITY_VISION.md` §13.
- `CONNECTIONS.md` gets **one new changelog paragraph** (C6-C35 + Taller CSS, no new C-xxx) after its existing C1-C5 entry — the canonical registry table itself is untouched, still ending at C-113.
- The interactive canvas (`jarvis-system-map.canvas.tsx`) and `DIAGRAMS.md` both stopped implying "no C++/CMake tree" or "C++ (future IC)" as a *current* fact — a C++ host+MCU-cross-compile tree has existed under `native/flight_control/` since C13. No fake SPI/`step` graph nodes were added — this is prose-only.
- `native/flight_control/README.md`'s own layout list now names `dshot.hpp`, `spi.hpp`, `spi_probe.hpp`, and their test files (previously stopped at C28's `uart.hpp`); C30's two "not yet tagged" mentions are corrected to "★ ACCEPT CLOSED @ tag `v0.5.28`" (the tag exists — `git tag -l v0.5.28`); new honesty paragraphs for C31-C35 were added matching this README's own established per-Buy style.
- `docs/USER_GUIDE_CRAFT_MONTAGE.md` §8.4 gets one short Spanish paragraph: a declared box is one six-face prism, a declared cylinder is one body (2 caps + 16 slats), a thin plate or short hub is still one solid — not extra parts, not CAD, not a fit verdict. No MY5 mm, no standoff ×8 anywhere in it.
- `docs/system_map/00_entry/ENTRY_MAP.md`'s visor projector row gets one clause naming Taller CSS cuboid + cylinder @ `v0.5.35`, still C-094/C-113 class, no new C-xxx.
- **Left untouched, verified clean:** `VISION.md`, `docs/PROJECT_CONTINUITY.md`, `docs/ENGINEERING_READINESS_VISION.md`, `docs/BUGS.md`/`FASE_LLM.md`/`CODE_AUDIT_CORE.md` (already carry `HISTORICAL` banners), `docs/IMPLEMENTATION_TASKS.md`'s closed archive sections, `ARCHITECTURE.md` §1c's own historical C3 quote, and 22 other `docs/*.md` files with zero stale Fase C references (grep-verified, listed in the inventory).
- **Docs tip != flying != gyro live != DShot pin != new C-xxx != standoff ×8 shipped.** Maps and READMEs that name the same tagged tip as `ARCHITECTURE.md` exist. Nothing here is a new craft connection, firmware on the desk, or the MY5/standoff catalog claimed as shipped.
- Package **`0.5.36`** · Python suite **3691** (unchanged) · UI vitest **142/142** · host `ctest` **76/76** — landed, awaiting Cursor review + Engineer ★ ACCEPT, **no `v0.5.36` tag yet** — [report](.jes/artifacts/implementation_report_docs_truth_sync_after_c35_b1.md)
- **Next:** awaiting Engineer ★ ACCEPT on this docs Buy. Cola: standoff points.

## What v0.5.37 includes

Fase C · **C36** (`B1-fase-c-sim-6dof-plant`) — **a toy body that can move through space, not just tilt**:

- New `ToyQuad6DofPlant` (Python `plant.py` + C++ `plant.hpp`/`plant.cpp`) beside unchanged `ToyQuadAttitudePlant` (C11) — purely additive; C11 tilt-recovery smoke still green.
- Translation: `thrust_body = (0,0,thrust_gain*sum(forces))` · `a_world = R(q)·(thrust/mass)+g` · semi-implicit Euler · ENU `g=(0,0,-9.81)`.
- `ImuSample` stays C11-shaped (gravity in body + gyro — no specific force). Pose on `true_position_m` / `true_velocity_mps` only. Plant stays **outside** `loop.step`.
- **6-DoF toy ≠ flying ≠ product aero ≠ MY5 truth.**
- Package **`0.5.37`** · tagged **`v0.5.37`** · suite **3696** · host `ctest` **82/82** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_sim_6dof_plant_b1.md)
- **Next:** C37 ★ ACCEPT CLOSED @ **`v0.5.38`**.

## What v0.5.38 includes

Fase C · **C37** (`B1-fase-c-mag-yaw-rung`) — **yaw stops being only gyro drift**:

- `MagSample` + `SimulatedMagHal` (Py+C++) — caller-supplied true q; toy horizontal world field; HAL never owns a plant.
- `ComplementaryAttitudeEstimator.update(sample, mag=None)` — mag optional; `mag=None` ≡ C7; yaw-only world-frame correction when present.
- `RC_CH_YAW` unlocked (`RC_MAX_YAW_RAD=π`); roll/pitch/throttle unchanged. Mag fusion **outside** `loop.step`.
- **Sim mag ≠ live mag ≠ flying.**
- Package **`0.5.38`** · tagged **`v0.5.38`** · suite **3706** · host `ctest` **88/88** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_mag_yaw_rung_b1.md)
- **Next:** C38 ★ ACCEPT CLOSED @ **`v0.5.39`**. Cola: C39 position loop (sim). Assistant PARKED. Silicon parked.

## What v0.5.39 includes (★ ACCEPT CLOSED)

Fase C · **C38** (`B1-fase-c-altitude-loop`) — **collective stops being only the RC stick or a fixed constant**:

- New `AltitudeSample` + `SimulatedAltitudeHal` (Python `sim_altitude_hal.py` + C++ `sim_altitude_hal.hpp`/`.cpp`) — a direct altitude port, not a fake ISA pressure/meteorology model: `read_altitude(true_z_m, t_s)` returns the caller-supplied true height directly. This HAL never owns or secretly consults a plant.
- New `AltitudeController` (Python `altitude_controller.py` + C++ `altitude_controller.hpp`/`.cpp`) — one law only, run **outside** `FlightControlLoop.step`: `collective = clip(hover_bias + kp*(z_des_m - altitude_m) - kd*vz_mps, 0, 1)`. `hover_bias` defaults to the toy hover point that actually balances `ToyQuad6DofPlant`'s own default gravity/thrust constants (`mass_kg*g/(4*thrust_gain)` ≈ `0.1226`) — **not** the IC's suggested `hover_collective()` (`0.5`), which was verified empirically to badly mismatch this plant's own physics and never settle near the setpoint. `vz_mps` is caller-supplied (the smoke passes `ToyQuad6DofPlant.true_velocity_mps[2]` directly), not internally integrated.
- Deliberately named `sim_altitude_hal.py`/`altitude_controller.py`, not `altitude.py` — this codebase already ships `attitude.py` (the C7 estimator); "altitude"/"attitude" differ by one letter, avoided the same way in file names, class names (no `AltitudeSetpoint` next to the existing `AttitudeSetpoint` — a plain `z_des_m` float is used instead), and the C++ headers.
- New smoke `run_altitude_loop_smoke` chains `alt.compute(...)` → `loop.step(...)` → `plant.step(...)` exactly as this Buy's own IC requires — starting at `z=0` with `z_des_m=2.0`, verified converging monotonically (no overshoot) to within `0.07m` of the setpoint over 500 steps (5 seconds sim time).
- **Sim altitude != live baro/ToF chip. z→collective in RAM != altitude hold in air.** A simulated height measurement drives thrust so the toy plant moves in `z`. Nothing here reads a real sensor or claims any real vehicle holds altitude.
- Package **`0.5.39`** · tagged **`v0.5.39`** · suite **3714** · host `ctest` **93/93** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_altitude_loop_b1.md)
- **Next:** C39 ★ ACCEPT CLOSED @ **`v0.5.40`**. Cola: C40 autonomy executor (sim). Assistant PARKED. Silicon parked.

## What v0.5.40 includes (★ ACCEPT CLOSED)

Fase C · **C39** (`B1-fase-c-position-loop`) — **horizontal motion stops being only open-loop tilt or luck**:

- New `PositionSample` + `SimulatedPositionHal` (Python `sim_position_hal.py` + C++ `sim_position_hal.hpp`/`.cpp`) — a direct ENU port, not a NMEA/WGS84/optical-flow stack: `read_position(true_x_m, true_y_m, t_s)` returns the caller-supplied true horizontal position (East/North) directly. Optional `z_m` allowed, unused by the controller. This HAL never owns or secretly consults a plant.
- New `PositionSetpoint(x_m, y_m)` + `PositionController` (Python `position_controller.py` + C++ `position_controller.hpp`/`.cpp`) — one law only, run **outside** `FlightControlLoop.step`: `pitch_rad = clip(kp*(x_des-x) - kd*vx, -max_tilt_rad, max_tilt_rad)`, `roll_rad = clip(-(kp*(y_des-y) - kd*vy), -max_tilt_rad, max_tilt_rad)`, composed into an `AttitudeSetpoint` quaternion with yaw held at `0`. `max_tilt_rad` defaults to `RC_MAX_TILT_RAD` (pi/6, 30 degrees, C25).
- Signs derived and proven: a positive pitch rotates body +Z thrust onto positive world X (East) — no sign flip on the pitch term; a positive roll rotates body +Z thrust onto negative world Y (South) — hence the sign flip on the roll term. Verified with a direct closed-loop test: East-only setpoint moves `true_position_m[0]` up, North-only setpoint moves `true_position_m[1]` up, with no cross-axis coupling.
- No naming-collision concern this Buy (unlike C38's `altitude`/`attitude`) — `PositionSetpoint`/`PositionController`/`PositionSample`/`SimulatedPositionHal` are used directly, typed, per the IC's own preference.
- New smoke `run_position_loop_smoke` chains `pos.compute(...)` → `alt.compute(...)` (C38's own `AltitudeController`, unchanged) → `loop.step(...)` → `plant.step(...)` — starting at `(0,0,0)` with `x_des_m=5.0, y_des_m=0.0, z_des_m=2.0`, verified horizontal distance shrinking from `5.0m` to under `0.25m` over 1000 steps (10 seconds sim time).
- **Sim position != live GPS/flow chip. xy→tilt in RAM != position hold in air != GO_TO executed. An ENU point in RAM != a house map.** Nothing here reads a real sensor or claims any real vehicle holds position, and this Buy does not implement the `AutonomyVerb.GO_TO` executor (that stays C40, a separate, future Buy) — `propose_command(GO_TO)` still hits `RejectAllSafetyGate`.
- Package **`0.5.40`** · tagged **`v0.5.40`** · suite **3723** · host `ctest` **101/101** — ★ ACCEPT CLOSED — [review](.jes/artifacts/implementation_review_fase_c_position_loop_b1.md)
- **Next:** C40 autonomy executor (sim setpoints). Assistant PARKED. Silicon parked.

## What v0.5.29 includes

Fase C · **C31** (`B1-fase-c-dshot-encode-stub`) — **the DShot 16-bit frame, in RAM, still not a pin**:

- New `src/jarvis/flight_software/flight_control/dshot.py` + `native/flight_control/include/jarvis/fc/dshot.hpp`/`src/dshot.cpp`: `encode_dshot_frame(throttle, telemetry=False) -> uint16` — `value = (throttle << 1) | telemetry`, `checksum = (value ^ (value>>4) ^ (value>>8)) & 0xF`, `frame = (value << 4) | checksum`, `throttle` a required `[0, 2047]` integer (out of range raises a typed error).
- **Vectors verified in both languages**: `throttle=0 -> 0x0000`, `throttle=48 -> 0x0606`, `throttle=2047 -> 0xFFEE`.
- **Special range documented, not implemented**: DShot's own protocol reserves `0..47` as commands (beep, 3D, etc.) — this module encodes the 11-bit field as given, no command table.
- Optional `encode_motor_forces_dshot(forces) -> 4x uint16` linearly maps force `[0,1]` onto throttle **`48..2047`** (never `0..2047`) — a **parallel** path; `encode_motor_forces` (PWM-µs, C10/C14) and `EscOutput`/`SimulatedEscSink` (C26) both stay byte-unchanged.
- `mcu/hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30) stay byte-identical — idle is still PC13, not DShot.
- DShot150/300/600 appear only as cited protocol names in comments, never as a claimed timer period or GPIO toggle rate.
- **DShot encode != pin != motors != flying.** A 16-bit DShot packet computed in software exists. Nothing here makes an ESC see a waveform.
- Package / tag **`v0.5.29`** · suite **3635** · host `ctest` **55/55** — [review](.jes/artifacts/implementation_review_fase_c_dshot_encode_stub_b1.md)
- **Next:** C32 CLOSED @ **`v0.5.30`**. C33 [`B1-fase-c-spi-scripted-slave`](.jes/artifacts/implementation_contract_fase_c_spi_scripted_slave_b1.md) READY.

## What v0.5.28 includes

Fase C · **C30** (`B1-fase-c-mcu-flash-observable`) — **a DFU-able LED image exists; it has not been seen on the desk**:

- Closes the two residuals C29 B1 left uncorrected in code: **(a)** `stub_main`'s idle loop was an empty `while (true)` — a successful `Reset_Handler` looked identical to a dead board; **(b)** CMake had no dependency on `linker_cortex_m4.ld`, so editing it never triggered a relink (C29's own test workaround deleted the `.elf` first — not a real fix).
- **(a)** New `native/flight_control/mcu/hello_led.h`/`hello_led.c`: bare `volatile` MMIO (no CMSIS, no HAL) toggling **PC13**, cited from Betaflight's own unified target for this FC (`HGLR-HGLRCF405V2.config`, `resource LED 1 C13`) — deliberately not PA8 (that target's own `resource MOTOR 6 A08`) and not PB1 (`LED_STRIP`). Register addresses cited from **RM0090**, transcribed by hand. The busy-wait between toggles is explicitly uncalibrated — a visible flicker at reset-default HSI 16 MHz, never a claimed millisecond period.
- **(b)** `set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY LINK_DEPENDS .../linker_cortex_m4.ld)` in `CMakeLists.txt` — verified by touching the `.ld` and rebuilding **without** deleting the prior `.elf`: the `.elf`'s mtime advances, confirming a genuine relink.
- A `POST_BUILD` step produces `fc_mcu_stub.bin` (load address `0x08000000`, unchanged from C29) for **USB DFU** — documented in `native/flight_control/README.md` alongside the restore procedure (reflash target **HGLRCF405V2** from Betaflight Configurator) and the props-off/battery-off warning.
- `uart.hpp`/`crsf_serial.py` stay byte-identical; `startup_cortex_m4.c`/`syscalls_stub.c`/C16's own toolchain flags too. No NVIC/EXTI/IRQ/DMA, no motor-pin write anywhere.
- **Flashed LED blink != flying != DShot != USART live != Betaflight HGLRCF405V2.** An image the Engineer can DFU onto the desk F405 whose idle loop toggles the cited status LED now exists; CMake will relink if the linker script changes.
- Package / tag **`v0.5.28`** · suite **3619** · host `ctest` **51/51** — [review](.jes/artifacts/implementation_review_fase_c_mcu_flash_observable_b1.md). Report §11: **not flashed on desk**.
- **Next:** C31 [`B1-fase-c-dshot-encode-stub`](.jes/artifacts/implementation_contract_fase_c_dshot_encode_stub_b1.md) READY (DShot frame in RAM, not pin). C30 DFU smoke parked until bench.

## What v0.5.27 includes

Fase C · **C29 B1** (`B1-fase-c-silicon-cited-flash-map`) — **the linker now cites the desk MCU's own datasheet, still not flashed**:

- C29 B0 (investigation) recommended parking until the Engineer named an MCU — on 2026-09-24 they did: desk stack **HGLRC F460 6S V1**, FC SKU **HGLRC F405 8S V1**, MCU line **STM32F405** (printed in that FC's own manual). This B1 replaces C18's disclosed fiction with that citation.
- `native/flight_control/mcu/linker_cortex_m4.ld` now uses `FLASH` `1024K` at `0x08000000` / `RAM` `128K` at `0x20000000` (SRAM1+SRAM2 contiguous) — taken from **ST RM0090 Table 3** (STM32F405xx/07xx, "Memory map"), not from the HGLRC manual itself (which names the MCU line but prints no ORIGIN/LENGTH numbers).
- CCM RAM (`0x10000000`, 64 KiB per RM0090) is deliberately **excluded** from the `MEMORY` block — folding it into a flat RAM region would be its own undisclosed simplification.
- The linker's own honesty comment cites both the desk identity (HGLRC) and the map source (RM0090), plus the disclosed residual: the HGLRC manual doesn't print the STM32F405's exact order-code suffix, but RM0090 Table 3's figures apply to the whole xx/07xx line regardless.
- `mcu/stub_main.cpp` was relinked and verified (`readelf -l`: `VirtAddr 0x08000000`, entry point `0x8000045`) but stays **byte-unchanged** — no new peripheral was touched. `cmake/toolchains/arm-none-eabi.cmake` (C16's own CPU flags) also stays byte-unchanged.
- No CMSIS, no STM32Cube, no OpenOCD/J-Link anywhere in the touched files.
- **Cited FLASH map != flashed != boots on FC != Betaflight HGLRCF405V2.** The linker now uses ST's own published addresses for this MCU, but that remains a compile/link-time fact on the Mac, never a claim about the HGLRC stack itself.
- Package / tag **`v0.5.27`** · suite **3598** · host `ctest` **51/51** — [review](.jes/artifacts/implementation_review_fase_c_silicon_cited_flash_map_b1.md)
- **Next:** Engineer pick among parked axes — board flash · GPIO/DShot wire · craft↔FS

## What v0.5.26 includes

Fase C · **C28** (`B1-fase-c-mcu-uart-hal-stub`) — **the MCU side got a UART-shaped port, still not a chip peripheral**:

- New `native/flight_control/include/jarvis/fc/uart.hpp` + `src/uart.cpp`: `UartBytePort` — an abstract base with a virtual destructor exposing `read(dst, n)`/`write(src, n)` (neither blocks nor throws on a full/empty port) — and `LoopbackUart`, the **only** implementation: an in-memory FIFO (default capacity `256`).
- A write past remaining capacity **returns a short count** (refuses the extra bytes) rather than growing unbounded or overwriting already-queued bytes — a chosen, tested overflow policy.
- **Zero USART registers, zero CMSIS, zero `IOSSIOSPEED`/`termios`, zero IRQ/DMA** anywhere in either file — grep-verified in real code.
- `mcu/stub_main.cpp` still does **not** reference `UartBytePort`/`LoopbackUart` — no UART poll loop was added to `Reset_Handler`/`main`; the `.elf` still links against the ARM toolchain when present.
- `capabilities/crsf_serial.py` (Mac host serial, C22/C23) stays byte-identical — this Buy is C++-only on the MCU tree, no Python UART driver added.
- The C21-C27 lock of **zero CRSF/ELRS mentions anywhere under `native/`**, even in comments, holds — re-verified tree-wide (proactive grep on the new header; this Buy ID contains no protocol tokens, so no rewrite was required).
- **MCU UART stub != chip USART != Darwin baud != live ELRS.** A named byte port exists; an in-memory loopback implements it. Nothing here is a USART talking to a receiver, the Mac's own `IOSSIOSPEED` moved onto the chip, or ExpressLRS running on the MCU.
- Package / tag **`v0.5.26`** · suite **3584** · host `ctest` **51/51** — [review](.jes/artifacts/implementation_review_fase_c_mcu_uart_hal_stub_b1.md)
- **Next (one front at a time):** C29 B1 silicon + cited FLASH map — [IC](.jes/artifacts/implementation_contract_fase_c_silicon_cited_flash_map_b1.md)

## What v0.5.25 includes

Fase C · **C27** (`B1-fase-c-crsf-stream-timeout-failsafe`) — **stale sticks stop being treated as live, still not a motor cut**:

- New `src/jarvis/capabilities/crsf_failsafe.py` — a sixth **separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`crsf_serial.py`/`intent.py`/`safety.py` all byte-unchanged).
- `CrsfRcHoldWatch` is an **age watch, not a parser**: `note_rc(now_s)` records the last time a valid `0x16` frame arrived; `evaluate(now_s)`/`is_stale(now_s)` compare that against `timeout_s` (default `0.5` s, illustrative, not sourced from any real ExpressLRS product spec) — `age_s <= timeout_s` is fresh, `age_s > timeout_s` is stale, never-noted is stale with `reason="never"`.
- Every method takes `now_s` as a caller-supplied argument — this module never calls `time.time()` as its own source of truth. A `now_s` earlier than the last noted time raises a typed `ValueError`.
- `failsafe_loop_inputs(t_s)` returns C8's own `level_setpoint(t_s)` plus `collective=0.0` — C25's own `RcLoopInputs` reused unchanged — and never calls `FlightControlLoop.step`, `EscOutput.apply_forces`, or any `SafetyGate.evaluate`.
- The optional `feed_and_note_rc(...)` helper calls C21's own `assembler.feed(data)` unchanged, notes only on a completed `0x16` frame, and never calls `ingest_stream_bytes` — C21's own default helper stays untouched.
- C++ twin: `native/flight_control/include/jarvis/fc/rc_hold.hpp` + `src/rc_hold.cpp`, added to `jarvis_fc`, **deliberately protocol-agnostic** — no radio-link protocol name anywhere in that tree, even in comments (same C21-C26 lock, re-verified tree-wide).
- C20's `CrsfDualRolePolicy` and C25's `map_rc_to_loop_inputs` are untouched and not imported here.
- **Timeout failsafe != motors cut != live ELRS != Safety allow.** An age watch exists; after `0.5` s without a noted RC sample, sticks are no longer treated as live; the recommended inputs are level attitude plus zero collective.
- Package / tag **`v0.5.25`** · suite **3572** · host `ctest` **45/45** — [review](.jes/artifacts/implementation_review_fase_c_crsf_stream_timeout_failsafe_b1.md)
- **Next (one front at a time):** C28 MCU UART HAL stub — [IC](.jes/artifacts/implementation_contract_fase_c_mcu_uart_hal_stub_b1.md)

## What v0.5.24 includes

Fase C · **C26** (`B1-fase-c-esc-output-hal`) — **the ESC output got a named port, still not a pin**:

- `esc.py`/`esc.hpp` (C10/C14's own module) gain `EscOutput` — Python `abc.ABC`, C++ abstract base with a virtual destructor — exposing `apply_forces(forces: MotorForceCommand) -> EscApplyResult` plus `arm()`/`disarm()`/`armed` (identical semantics to C10).
- `SimulatedEscSink` **is-a** `EscOutput` in both languages. Its C10 `apply(EscPwmCommand)` path and arming behavior stay byte-identical — `apply_forces` is a thin wrapper: `encode_motor_forces(forces)` then `apply(cmd)`.
- The `esc.cpp` diff is **purely additive** — verified line-by-line: zero lines removed/changed, four lines added. `esc.py`/`esc.hpp`/`esc.cpp` are the **only** rung files touched this Buy; `filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant` all stay `git diff --stat` empty.
- The mixer still speaks **forces only** — `mixer.py`/`mixer.hpp` gain no PWM/DShot/pin knowledge, grep-verified in real code.
- `step` still never calls `apply`/`apply_forces`/`SimulatedEscSink` — `loop.py`/`loop.hpp`/`loop.cpp` stay byte-unchanged, re-verified explicitly.
- **Only one implementation ships**: `SimulatedEscSink`. No GPIO sink, no unimplemented pin class, no DShot this Buy.
- **EscOutput HAL != pin != motors != DShot.** A named port exists; the simulated sink implements it; the mixer still does not know the wire protocol.
- Package / tag **`v0.5.24`** · suite **3553** · host `ctest` **39/39** — [review](.jes/artifacts/implementation_review_fase_c_esc_output_hal_b1.md)
- **Next (one front at a time):** C27 CRSF stream-timeout failsafe — [IC](.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)

## What v0.5.23 includes

Fase C · **C25** (`B1-fase-c-rc-setpoint`) — **RC channels got a language toward the tick, still not flying**:

- New `src/jarvis/flight_software/flight_control/rc_setpoint.py`: `map_rc_to_loop_inputs(channels, *, t_s) -> RcLoopInputs` — an illustrative AETR map (not a real TX model): roll/pitch/throttle = channel indices `0`/`1`/`2`; the yaw channel is **unused this Buy** (no magnetometer anywhere in this tree, so no absolute heading a yaw stick could honestly command).
- `CRSF_CH_MIN`/`CRSF_CH_MID`/`CRSF_CH_MAX` = `172`/`992`/`1811` (the same illustrative 11-bit convention already used around C20's policy). Throttle maps linearly onto `collective ∈ [0, 1]`, clipped — mid-stick gives `≈0.5003`, not exactly `0.5` (documented, not rounded away).
- Roll/pitch deflection is measured from `992`, scaled to reach exactly `π/6` (30°) at either endpoint, clipped beyond it, composed into `q_body_to_world_desired` via the standard body 3-2-1 Euler-to-quaternion formula with yaw fixed at `0`.
- C++ twin: `native/flight_control/include/jarvis/fc/rc_setpoint.hpp` + `src/rc_setpoint.cpp`, added to `jarvis_fc`, same thresholds/formula, `std::vector<int>` in place of any CRSF-shaped type — the C21-C23 lock of **zero CRSF/ELRS mentions anywhere under `native/`** stays intact (even in comments).
- Optional `step_with_rc(loop, sample, channels)` maps then calls C24's own `FlightControlLoop.step` unchanged — `loop.py`/`loop.hpp`/`loop.cpp` all byte-unchanged; never calls a plant, `SimulatedEscSink`, or `SafetyGate.evaluate`.
- C20's `CrsfDualRolePolicy` (aux → Authority `kill`) untouched and not imported here. `radio.py` still has no stick API. `default_safety_gate()` unchanged.
- **RC->setpoint != flying != sticks drive motors != Safety allow != yaw lock.** A deterministic, documented map from already-decoded channel units to the two arguments `step` already accepted — no pilot flies anything, no motor spins, no heading-hold exists.
- Package / tag **`v0.5.23`** · suite **3538** · host `ctest` **36/36** — [review](.jes/artifacts/implementation_review_fase_c_rc_setpoint_b1.md)
- **Next (one front at a time):** C27 CRSF stream-timeout failsafe — [IC](.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)

## What v0.5.22 includes

Fase C · **C24** (`B1-fase-c-control-loop-tick`) — **the control loop got a name, still not flying**:

- New `src/jarvis/flight_software/flight_control/loop.py`: `FlightControlLoop.step(sample, setpoint, collective) -> ControlTickResult` — extracts the body C11/C13 already ran **inlined** into one named tick: `filter_sample -> estimator.update -> controller.compute -> bridge.convert -> mixer.mix`, exactly the existing order, calling each existing rung's own unmodified method. No new math.
- C++ twin: `native/flight_control/include/jarvis/fc/loop.hpp` + `src/loop.cpp`, added to `jarvis_fc`, same order, same existing classes.
- `step` **does not** call the plant, read a real HAL, or write a pin — the caller still supplies `ImuSample` and consumes `MotorForceCommand`/`EscPwmCommand` itself. `dt` is **not** an argument (no 1 kHz ISR claim); `AttitudeSetpoint`/`collective` are plain arguments (no RC decoding — mapping sticks to them is C25).
- `run_controlled_flight_sim_smoke` (Python, C11) and `fc_closed_loop_smoke` (C++, C13) are refactored to **call** `step` instead of inlining the chain — verified bit-identical to the pre-refactor behavior: `15° → 0.252°` in 200 steps, no gain retuned.
- `mcu/stub_main.cpp` still has no `ControlLoop`/`step(` control cycle — no `Reset_Handler` spin.
- `radio.py`/`crsf_*.py`/`intent.py`/`safety.py`/`autonomy/` all byte-unchanged. `default_safety_gate()` unchanged.
- **Named control tick != flying != MCU ISR != motors != RC sticks.** One named cycle, IMU+setpoint+collective in, four motor forces out, reusing C6-C12/C13 unchanged; plant, ESC pin, and RC mapping remain later cola.
- Package / tag **`v0.5.22`** · suite **3520** · host `ctest` **31/31** — [review](.jes/artifacts/implementation_review_fase_c_control_loop_tick_b1.md)
- **Next (one front at a time):** C27 CRSF stream-timeout failsafe — [IC](.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)

## What v0.5.21 includes

Fase C · **C23** (`B1-fase-c-crsf-host-baud`) — **Darwin host baud 420000, still not a live link**:

- Extends C22's own `src/jarvis/capabilities/crsf_serial.py` — **no sixth module** — with **opt-in** Darwin host baud configuration: `configure_host_baud(fd, baud=420000)` / `CrsfHostSerialIngress.configure_baud(...)`.
- On `sys.platform == "darwin"`, applies raw 8N1 termios (disabling canonical mode and the CR/NL translations that would corrupt binary CRSF) then issues the real `IOSSIOSPEED` ioctl — the request number **derived** from the `_IOW('T', 2, speed_t)` macro, not copied from `pyserial` or any library; independently verified to equal `0x80085402`.
- On any other platform it **fails closed** with a typed `CrsfHostSerialError` — no Linux `TCSETS2`/`BOTHER`, no Windows serial stack.
- `attach_fd`/`attach_path` still **never** auto-configure baud — C22's own "open = give me bytes" contract is unchanged, re-verified by re-running C22's own test suite unmodified.
- **Every PASS requires no hardware**: the Darwin success path is proven entirely via a mocked `fcntl.ioctl`; the one **unmocked** ioctl call runs against a real POSIX `pty` and is **asserted to fail** (a pty is not a UART) — that failure is the honest, expected outcome, not something skipped around.
- A successful ioctl is a host OS configuration fact, never proof a receiver exists. **No `pyserial` dependency was added.**
- `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`intent.py`/`safety.py` all byte-unchanged. `default_safety_gate()` unchanged.
- **Host baud 420000 != live ELRS != RX connected != UART driver != Safety allow.** Darwin can be asked to clock an attached FD at an ELRS-typical rate, proven without hardware via ioctl mock, nothing more.
- Package file / tag **`v0.5.21`** · suite **3504** — [review](.jes/artifacts/implementation_review_fase_c_crsf_host_baud_b1.md)
- **Next (one front at a time):** C27 CRSF stream-timeout failsafe — [IC](.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)

## What v0.5.20 includes

Fase C · **C22** (`B1-fase-c-crsf-host-serial`) — **CRSF host serial ingest, still not a live link**:

- New `src/jarvis/capabilities/crsf_serial.py` — a **fifth separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`intent.py`/`safety.py` all byte-unchanged).
- `CrsfHostSerialIngress` pulls bytes from an already-open host FD (`attach_fd`, caller-owned, never closed by this module) or an opt-in device path (`attach_path`, ingress-owned, closed on `.close()`); `poll(...)` performs exactly **one** non-blocking read then feeds C21's own `CrsfByteStreamAssembler`, unchanged — no background thread, no "connected" flag, no `/dev/cu.*` auto-scan.
- **Every PASS in this Buy's own test suite uses a POSIX `pty` as its loopback — no physical receiver or USB serial adapter is required**, verified by running the full suite with nothing plugged in.
- **No `pyserial` dependency was added**, and **420000 baud (the rate a real ELRS link runs at) is not configured anywhere** — opening a path here means "give me bytes from this node," not "I configured an ELRS receiver"; custom-baud configuration is explicitly deferred to a later, platform-specific IC.
- A real pty gotcha was found and disclosed while testing: POSIX ptys default to canonical (line-buffered) mode, which silently held binary CRSF bytes back from a reader until a newline appeared — fixed entirely in the test harness (`tty.setraw(...)`), not in the shipped module, which has no terminal-mode logic at all.
- Optional `poll_and_ingest(...)` helper reuses C20's `ingest_rc_channels(...)` unchanged for any completed `0x16` frames.
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError`. `default_safety_gate()` unchanged.
- **Host serial ingest != live ELRS != "RX connected" != UART driver != Safety allow.** A pull-based FD/path reader proving bytes can be pulled from a host source and reassembled by C21's own assembler, verified entirely via `pty` loopback, nothing more.
- Tag **`v0.5.20`** · suite **3485** — [review](.jes/artifacts/implementation_review_fase_c_crsf_host_serial_b1.md)
- **Next (one front at a time — Engineer picks):** deepen policy · board flash · craft↔FS · baud 420000

## What v0.5.19 includes

Fase C · **C21** (`B1-fase-c-crsf-byte-stream`) — **CRSF byte-stream assembler, still not a UART**:

- New `src/jarvis/capabilities/crsf_stream.py` — a **fourth separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`intent.py`/`safety.py` all byte-unchanged).
- `CrsfByteStreamAssembler.feed(data: bytes) -> list[CrsfFrame]` reassembles frames from bytes delivered in **arbitrary chunks** (the shape a UART delivers data in) by slicing exact `frame_len + 2` candidate windows and handing them, unmodified, to C19's own `parse_crsf_frame` — no second CRC8/envelope implementation (verified: no `0xD5` anywhere in the module).
- **Incomplete** candidates wait in a bounded leftover buffer (default cap `256` bytes); **invalid complete** windows (bad CRC, or a declared `frame_len` outside the plausible `[2, 64]` range) are never raised to the caller — the assembler drops exactly one byte and resyncs, looping until it finds a valid frame or exhausts the buffer.
- Optional `ingest_stream_bytes(...)` helper reuses C20's `ingest_rc_channels(...)` **unchanged** for any completed `0x16` frames — C20's policy (one aux channel, one threshold, `AuthorityKind="kill"` only) is neither deepened nor reconfigured here.
- **Zero I/O anywhere in the module** — no serial/socket/pty/USB/`open()`, no class named like `Serial`/`UartPort`.
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError`, even fed real assembled frames. `default_safety_gate()` unchanged.
- **Byte-stream assembler != UART open != live ELRS != a pilot link != Safety allow.** A pure in-memory buffer proving bytes delivered in chunks reassemble into the same frames C19 already parses from a complete buffer, nothing more.
- Tag **`v0.5.19`** · suite **3465** — [review](.jes/artifacts/implementation_review_fase_c_crsf_byte_stream_b1.md)
- **Next (one front at a time — Engineer picks):** host serial ingest · deepen policy · board flash · craft↔FS

## What v0.5.18 includes

Fase C · **C20** (`B1-fase-c-crsf-dual-role-bridge`) — **CRSF decode → dual-role bridge, still not a link**:

- New `src/jarvis/capabilities/crsf_dual_role.py` — a **third separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`intent.py`/`safety.py` all byte-unchanged).
- Bridges C19's decoded `CrsfRcChannels` into C5's typed `RadioStubFrame`/`RadioDualRoleResult` under one documented, deterministic policy: `CrsfDualRolePolicy` (one aux channel index + threshold, illustrative defaults channel `4`/`1500`, not sourced from any real hardware) — at/above threshold emits `AuthorityKind="kill"` **only** (Authority-only, never Intent); below threshold, returns `None`.
- Optional `link_stats` enrichment folds LQ/RSSI/SNR into `RadioStubFrame.notes` without ever changing whether Authority fires. `ingest_rc_channels(...)` optionally routes a produced frame through `SimulatedRadioIngress.ingest(...)`.
- **Authority from this bridge stays trace-only relative to Safety** — explicitly tested: wiring the bridge's own `AuthoritySignal.id` into a `SafetyRequest.authority_signal_id` still yields `reject` on both `RejectAllSafetyGate` and an armed `ArmedAllowlistSafetyGate`; `default_safety_gate()` is unchanged.
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError`, even fed a real bridge-produced frame. The bridge never calls `submit_command` or imports the autonomy surface.
- **No I/O anywhere in the module** — no serial/socket/pty/USB/subprocess.
- **Bridge != live ELRS != a pilot link != Safety allow.** A deterministic, documented map from already-decoded bytes to a typed dual-role frame, nothing more.
- Tag **`v0.5.18`** · suite **3444** — [review](.jes/artifacts/implementation_review_fase_c_crsf_dual_role_bridge_b1.md)
- **Next (one front at a time — Engineer picks):** UART stream · deepen policy · board flash · craft↔FS

## What v0.5.17 includes

Fase C · **C19** (`B1-fase-c-crsf-link-stub`) — **first CRSF byte-fixture link stub (ELRS-shaped, host-only)**:

- New `src/jarvis/capabilities/crsf_stub.py` — a **separate** module from C5's own `radio.py` on purpose (its no-decode-API lock stays byte-unchanged, confirmed via `git diff`).
- Parses the CRSF envelope (`[device_addr][frame_len][type][payload][crc8]`, CRC8 poly `0xD5` over `type+payload`) from checked-in fixture bytes into `CrsfFrame`, then decodes `0x16` `RC_CHANNELS_PACKED` (16 × 11-bit channels) and `0x14` `LINK_STATISTICS` (RSSI/LQ/SNR fields).
- Truncated frames and bad-CRC frames both raise a typed `CrsfParseError` — no silent partial success — verified against four checked-in `.bin` fixtures under `tests/fixtures/crsf/`.
- **Zero I/O anywhere in the module** — no serial/socket/pty/USB/subprocess, confirmed by inspecting real code with comments/docstrings stripped.
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` even when fed real CRSF fixture bytes; `default_safety_gate()` and `ArmedAllowlistSafetyGate` are untouched.
- Nothing decoded here reaches `SimulatedRadioIngress`, autonomy `submit_command`, or any `SafetyGate`. No CRSF/ELRS token anywhere under `native/`.
- **Fixture CRSF parse != live ELRS != a pilot link != a CRSF driver product.** This module can decode a byte sequence, nothing more: no receiver is "connected," no air protocol (RF/binding/telemetry) is implemented, no pilot's sticks drive anything.
- Tag **`v0.5.17`** · suite **3428** — [review](.jes/artifacts/implementation_review_fase_c_crsf_link_stub_b1.md)
- **Next (one front at a time — Engineer picks after C20 ACCEPT):** UART stream · deepen policy · board flash · craft↔FS

## What v0.5.16 includes

Fase C · **C18** (`B1-fase-c-cpp-mcu-freestanding-elf`) — **first freestanding linked MCU `.elf`**:

- New `native/flight_control/mcu/` — generic Cortex-M4 linker script (`FLASH` at `0x00000000` / `RAM` at `0x20000000`, the ARM-architected generic Code/SRAM regions, not any vendor's remapped boot address; 256 KiB/64 KiB illustrative sizes, explicitly fictional), a 16-entry ARMv7-M vector table + `Reset_Handler` startup, minimal newlib syscall stubs (no semihosting, no real I/O), and a thin entry point that **links real `jarvis_fc` code**.
- Reuses C16's own toolchain file **unchanged** — produces `fc_mcu_stub.elf` alongside the existing `libjarvis_fc.a`.
- **A real link was performed and verified**: `readelf -h` shows `Machine: ARM`, `Type: EXEC`, a real entry point, soft-float ABI; `nm` confirms `jarvis::fc::ImuLowPassFilter::filter_sample` and `encode_motor_forces` are linked in as defined (not merely referenced) symbols.
- **C++ exceptions kept enabled** (option (a) over disabling them) — the rung sources' `throw std::invalid_argument(...)` calls are untouched; the C++ runtime resolves via the toolchain's own libstdc++/newlib plus this Buy's own syscall stubs.
- **A real build-system gap was hit and fixed, disclosed**: the `.c` startup/syscall sources were silently never compiled (CXX-only `project()`) until C was added as a project language — the linker's `cannot find entry symbol Reset_Handler` warning is gone after the fix.
- Host build **re-verified unaffected**: `ctest` still 28/28 green.
- **No GPIO/flash/OpenOCD/vendor BSP anywhere** (grep-verified).
- `default_safety_gate()` unchanged; autonomy `submit_command` still always rejects. Does not touch Continuity, orchestrator IDLE, Board, or `library/`.
- **Freestanding `.elf` != flashed / != boots on hardware / != motors / != GPIO.** A linked, inspectable, host-only ARM executable, nothing more; this image has never run on any board.
- Tag **`v0.5.16`** · suite **3412** — [review](.jes/artifacts/implementation_review_fase_c_cpp_mcu_freestanding_elf_b1.md)
- **Next (one front at a time — Engineer picks after C19 ACCEPT):** board flash · craft↔FS · deepen link stub

## What v0.5.15 includes

Fase C · **C17** (`B1-fase-c-safety-real-policy`) — **first real (non-RejectAll) Safety policy gate**:

- `src/jarvis/capabilities/safety.py` — `ArmedAllowlistSafetyGate`: **opt-in**, starts **disarmed** (always rejects, reason `"disarmed"`), and once explicitly `arm()`ed allows **only** `HOLD`/`LAND` (parsed from `submit_command`'s own `autonomy:{verb}:{id}` action-id shape); any other verb or a malformed `action_id` is rejected too (`"verb_not_allowed"` / `"unparseable_action_id"` — neither reuses RejectAll's `"not_implemented"`).
- **`default_safety_gate()` is byte-unchanged** — `git diff` confirms zero lines touched in `RejectAllSafetyGate` or the factory function; the shipped product default remains "reject everything."
- `evaluate()` never reads `authority_signal_id` at all — Authority (C5) stays trace-only, unable to flip a decision through this or any gate.
- `submit_command`'s `allow` branch, unreachable in shipped code since C4, already resolved to `execution="not_implemented"` — **zero changes** were needed to `flight_software/autonomy/surface.py`/`types.py`; verified at runtime via `typing.get_args(ExecutionState) == {"not_attempted", "not_implemented"}`.
- New `smoke_policy_gate_hold_and_land()` helper demonstrates the armed allow path end-to-end (both verbs `allow`, `execution` still `"not_implemented"`).
- **No `AllowAllSafetyGate` anywhere in `src/`, no `SimulatedEscSink`/GPIO coupling, no craft/CLI wiring.**
- **Policy allow != flying / != executed autonomy / != hardware Safety / != "safe to fly".** A real, opt-in, narrowly-scoped software gate now exists alongside the unchanged RejectAll default; no gate shipped in `src/` can ever return `execution="executed"`.
- Tag **`v0.5.15`** · suite **3403** — [review](.jes/artifacts/implementation_review_fase_c_safety_real_policy_b1.md)
- **Next (one front at a time — Engineer picks):** MCU freestanding `.elf` · link (ELRS) · craft↔FS

## What v0.5.14 includes

Fase C · **C16** (`B1-fase-c-cpp-mcu-cross-compile`) — **first MCU cross-compile scaffold, a compile-time proof only**:

- New `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` — `CMAKE_SYSTEM_NAME Generic`, generic **Cortex-M4** (`-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`, not a claim about any specific board's silicon).
- Separate build (`build/flight_control_mcu`) produces **only** `libjarvis_fc.a` for that triple — gated entirely via CMake (no `#ifdef` in any rung source), so Catch2/the unit-test binary/both smokes never build on the MCU path.
- **A real cross-build was performed and verified**: `arm-none-eabi-objdump` confirms `file format elf32-littlearm, architecture: armv7e-m` on the produced archive — genuine target code.
- **A real toolchain-completeness problem was hit and disclosed**: the bare Homebrew `arm-none-eabi-gcc` formula has no bundled `newlib`/`libstdc++` and fails to compile `<optional>`; the working build used the xPack `arm-none-eabi-gcc` v15.2.1-1.1 release instead. The new pytest wrapper handles both outcomes — skips with a specific install hint rather than hard-failing when a compiler is present but incomplete.
- Host build **re-verified unaffected**: `ctest` still 28/28 green (unit suite + both smokes).
- **No GPIO/flash/OpenOCD/vendor BSP anywhere** — STM32Cube, CMSIS device packs, ChibiOS, FreeRTOS, PX4, ArduPilot all absent (grep-verified).
- `default_safety_gate()` unchanged; autonomy `submit_command` still always rejects. Does not touch Continuity, orchestrator IDLE, Board, or `library/`.
- **MCU cross-compile != flashed / != flying / != firmware runs on a flight controller / != GPIO-verified.** A compile-time proof the steel-ladder sources build freestanding for a Cortex-M4-class target, nothing more; no board has run this code.
- Tag **`v0.5.14`** · suite **3389** — [review](.jes/artifacts/implementation_review_fase_c_cpp_mcu_cross_compile_b1.md)
- **Next (one front at a time — Engineer picks):** Safety-real · MCU freestanding `.elf` · link · craft↔FS

## What v0.5.13 includes

Fase C · **C15** (`B1-fase-c-cpp-unit-tests`) — **a real C++ unit-test framework, deepening host verification**:

- **Catch2 v3, pinned to release tag `v3.7.1`** (commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14`), fetched via CMake `FetchContent` — network needed once at first configure, none needed after (offline story documented in `native/flight_control/README.md`).
- New `native/flight_control/tests/` — **26 `TEST_CASE`s / ~494 assertions**, at least one per steel rung: filter, attitude (including a C11 Amendment A regression guard), controller (sign-check on the dominant axis), rate_torque, mixer (documented X-geometry sign check), esc.
- `ctest` now runs **28 entries** total: the 26 unit cases (individually discovered via `catch_discover_tests`) plus both pre-existing smoke binaries — all green.
- **Behavior freeze honored exactly**: `git diff --stat` on every pre-existing rung source (`filter.cpp`…`esc.cpp`/`plant.cpp`/all headers) is empty — this Buy added coverage only, no bug exposed, no Engineer-call needed.
- Both smoke binaries **remain unmodified**; `fc_closed_loop_smoke` re-verified byte-identical: `15° → 0.252°` in 200 steps.
- **No GPIO/pigpio/`/dev/mem`/serial/DShot/socket anywhere in the new test sources** (grep-verified).
- `default_safety_gate()` unchanged; autonomy `submit_command` still always rejects. Does not touch Continuity, orchestrator IDLE, Board, or `library/`.
- **C++ unit tests != flying / != MCU verification / != production-hardened / != algorithm change.** A host desktop `ctest` run with a real framework instead of two hand-rolled smoke mains, nothing more.
- Tag **`v0.5.13`** · suite **3380** — [review](.jes/artifacts/implementation_review_fase_c_cpp_unit_tests_b1.md)
- **Next (one front at a time — Engineer picks):** MCU cross-compile · Safety-real · link · craft↔FS

## What v0.5.12 includes

Fase C · **C14** (`B1-fase-c-cpp-esc-pwm-stub`) — **steel-ladder parity for the ESC/PWM encoding stub**:

- `native/flight_control/include/jarvis/fc/esc.hpp` + `src/esc.cpp` — ports Python C10's `encode_motor_forces`/`SimulatedEscSink` into the C++ tree: same linear force→PWM-µs map (`force=0 → min_us`, `force=1 → max_us`, default `1000`–`2000`, `min_us < max_us` enforced), same in-memory `SimulatedEscSink` (`armed` starts `false`; `apply(cmd)` always records the command, `applied=true` only while armed, otherwise `applied=false`/`reason="disarmed"`).
- New, **separate** `fc_esc_pwm_smoke` executable (18 checks, all passing) — kept apart from the C13 tip smoke on purpose, so that one stays focused.
- `fc_closed_loop_smoke` (C13's own tip) re-verified **byte-identical**: `15° → 0.252°` in 200 steps, unaffected by this Buy.
- **No GPIO/pigpio/`/dev/mem`/serial/DShot/Oneshot/Multishot/socket anywhere in the new sources** (grep-verified).
- Python `esc.py` **untouched** — re-verified with the same before/after values.
- `default_safety_gate()` unchanged; autonomy `submit_command` still always rejects. Does not touch Continuity, orchestrator IDLE, Board, or `library/`.
- **C++ ESC stub != hardware write / != ESC online / != motors spinning.** Closes the C++ tree's module parity with the Python wooden ladder (filter/attitude/controller/rate_torque/mixer/esc, plus the plant tip).
- Tag **`v0.5.12`** · suite **3368** — [review](.jes/artifacts/implementation_review_fase_c_cpp_esc_pwm_stub_b1.md)
- **Next (one front at a time — Engineer picks):** MCU cross-compile · deepen C++ tests · real Safety · real link · craft↔FS

## What v0.5.11 includes

Fase C · **C13** (`B1-fase-c-cpp-flight-control-scaffold`) — **the first material C++ scaffold for `flight_control`**:

- New **`native/flight_control/`** tree (outside `src/jarvis/`, locked path) — C++17, **host-only** CMake ≥ 3.16 build. Not MCU firmware, not a board bring-up, no cross-compile requirement in this Buy.
- Mirrors the Python wooden ladder module-for-module: `filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant`, same formulas, same ENU convention, same honesty notes — including the C11 Amendment A accel-correction sign fix from day one.
- `fc_closed_loop_smoke` executable (also runnable via `ctest`) runs the same closed-loop tip: seeded at 15° tilt, the true tilt error recovers to **0.252°** after 200 steps — matching the Python ladder's own number, though bit-identity was not required by the IC.
- **No GPIO/pigpio/`/dev/mem`/serial/DShot/socket anywhere in the tree** (grep-verified) — pure host math and stdout. No PX4/ArduPilot vendored.
- Python `flight_software/` package **untouched except a docstring pointer** — it remains the design guide and the craft platform; this Buy does not delete or replace it.
- `default_safety_gate()` unchanged; autonomy `submit_command` still always rejects. Does not touch Continuity, orchestrator IDLE, Board, or `library/`.
- **C++ scaffold != flying / != hardware flight controller / != firmware on any board / != replacing Python craft SoT.** A host desktop build proving the same algorithmic ladder in a second language, nothing more.
- Tagged **`v0.5.11`** on Engineer ACCEPT (suite **3358**) — [review](.jes/artifacts/implementation_review_fase_c_cpp_flight_control_scaffold_b1.md)
- **Next (one front at a time):** deepen C++ parity · MCU cross-compile · Safety-real · link · craft↔FS — Engineer prioritizes

## What v0.5.10 includes

Fase C · **C12** (`B1-fase-c-rate-torque-bridge`) — **closes the rate ≠ torque honesty gap C9/C11 left open on purpose**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created in this Buy.
- `src/jarvis/flight_software/flight_control/rate_torque.py` — `LinearRateTorqueBridge.convert(rates: BodyRateCommand) -> BodyTorqueCommand`: **one feedforward map only** (`tau_i = gain_i * omega_cmd_i` per axis, scalar or per-axis gains, each finite and `> 0`) — **not** a cascaded rate PID (no `kp * (omega_cmd - omega_measured)` term, no integral/derivative state)
- `BodyTorqueCommand.tau_body` is explicitly **normalized/dimensionless, torque-like** — never claimed as Newton-metres of any real vehicle
- `QuadXMixer.mix(collective, torques: BodyTorqueCommand)` is **migrated**: it no longer accepts a bare `BodyRateCommand` at all — no silent dual API (passing a rate directly raises `AttributeError`, not a quiet misinterpretation)
- C11's closed-loop tip re-verified through the bridge and **unchanged**: `15° → 0.252°` in 200 steps, identical to before migration — **no gain retune needed**, since the bridge's default `gain=1.0` is a mathematical no-op relative to the mixer's pre-migration direct pass-through
- `default_safety_gate()` unchanged — the bridge is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Bridge != rate loop product / != physical N·m / != flying.** A single named feedforward step exists now instead of an implicit rate-as-torque assumption
- Tagged **`v0.5.10`** on Engineer ACCEPT (suite **3348**) — [review](.jes/artifacts/implementation_review_fase_c_rate_torque_bridge_b1.md)
- **Next:** ★ **C13** C++ scaffold IC (material change of the wooden ladder)

## What v0.5.9 includes

Fase C · **C11** (`B1-fase-c-controlled-flight-sim-tip`) — **closes the C0 §7 wooden-ladder tip: toy closed-loop sim, no hardware**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/plant.py` — `ToyQuadAttitudePlant`: toy, attitude-only, explicitly-not-product-physics dynamics. `step(forces: MotorForceCommand, *, dt_s) -> ImuSample` advances from C9 forces (**not** PWM) and emits an `ImuSample` **consistent with its own true attitude** — the C3→C10 chain now runs as a real closed loop
- `run_controlled_flight_sim_smoke()`: from a documented 15° initial tilt, true tilt error drops below 2° within 200 steps. `run_open_loop_baseline_smoke()`: the same plant with zero correction stays at a constant 15° — no passive righting, proving the closed loop does real work
- **Rate ≠ torque remains open**: C9's mixer still treats body rate as its mix channel; this plant does not silently insert a rate→torque controller — it uses its own, separately-documented toy force→angular-acceleration map
- **Also fixed, disclosed:** a real sign bug in C7's `ComplementaryAttitudeEstimator` (tagged `v0.5.5`, ACCEPT CLOSED) — its accel correction had the cross-product argument order reversed, converging estimates *away* from the true tilt for any non-level input (confirmed even at 0.1°; every pre-existing C7 test only fed already-level accel, so this was never exercised). One-line fix + a new regression test in C7's own test file
- `default_safety_gate()` unchanged — advancing the plant is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Sim closed-loop tip @ 0.5.9 != flying / != hardware-verified flight / != physics-accurate sim.** No motor spins, no real vehicle exists
- Tagged **`v0.5.9`** on Engineer ACCEPT (suite **3330**) — [review](.jes/artifacts/implementation_review_fase_c_controlled_flight_sim_tip_b1.md)

## What v0.5.8 includes

Fase C · **C10** (`B1-fase-c-esc-pwm-stub-rung`) — **sixth `flight_control` rung: ESC/PWM command encoding stub, in-memory sink only**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/esc.py` — `encode_motor_forces(forces, *, min_us=1000, max_us=2000) -> EscPwmCommand`: linear map, `force=0 → min_us`, `force=1 → max_us`; `min_us`/`max_us` must be finite with `min_us < max_us`
- **Exactly one encoding** — classic PWM-in-µs only; no DShot/Oneshot/Multishot shipped alongside it
- `SimulatedEscSink` — `armed` starts `False`; `apply(cmd)` always records the command in memory but only reports `applied=True` while armed (`applied=False`, `reason="disarmed"` otherwise) — no `RPi.GPIO`, `pigpio`, `/dev/mem`, serial, or socket I/O anywhere
- **Not wired to C4**: no auto-routing of `AutonomyVerb.HOLD`
- `run_esc_pwm_smoke()` — full C3→C10 pipeline smoke path, disarmed by default (reuses the existing `smoke_quad_hal_imu` profile, no schema change)
- `default_safety_gate()` unchanged — encoding/recording a PWM command is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **ESC/PWM stub @ 0.5.8 != hardware ESC / != flying.** No pin, port, or socket exists anywhere, and no motor is claimed to spin
- Tagged **`v0.5.8`** on Engineer ACCEPT (suite **3315**) — [review](.jes/artifacts/implementation_review_fase_c_esc_pwm_stub_rung_b1.md)

## What v0.5.7 includes

Fase C · **C9** (`B1-fase-c-mixer-rung`) — **fifth `flight_control` rung: motor allocation, four numbers only**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/mixer.py` — `QuadXMixer`: one documented quadrotor-X layout (motors `0..3` = FR/FL/RL/RR, 45° off body axes) via a fixed linear allocation matrix
- `mix(collective, rates: BodyRateCommand) -> MotorForceCommand` — `collective` clamped to `[0, 1]`; output is four `[0, 1]`-clamped, dimensionless motor force numbers
- **Honesty-critical simplification, stated explicitly:** C8's `BodyRateCommand.omega_body_rad_s` is a body *rate*, not a true body *torque* — this B1 mixer treats it directly as roll/pitch/yaw mix channels to teach allocation geometry, without claiming rate ≡ torque physically and without inventing a second controller to bridge that gap
- `roll_scale`/`pitch_scale`/`yaw_scale` (default `0.05` each) must be finite and `>= 0`; a `0` disables that channel
- **Exactly one layout** — no `+`/H/Y6/octo mixing matrix shipped alongside it
- **Not wired to C4**: no auto-routing of `AutonomyVerb.HOLD`
- `hover_collective()` and `run_mixer_smoke()` — tests/smoke only, no hover-thrust or hardware claim (reuses the existing `smoke_quad_hal_imu` profile, no schema change)
- `default_safety_gate()` unchanged — mixing is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Mixer stub @ 0.5.7 != ESC / != flying.** No PWM, DShot, ESC UART, or GPIO exists anywhere, and no motor is claimed to spin
- Tagged **`v0.5.7`** on Engineer ACCEPT (suite **3297**)

## What v0.5.6 includes

Fase C · **C8** (`B1-fase-c-attitude-controller-rung`) — **fourth `flight_control` rung: attitude controller, body-rate output only**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/controller.py` — `PdAttitudeController`: `omega_cmd = kp * e_rot - kd * omega_measured` (`kp` default `6.0`, must be `> 0`; `kd` default `0.6`, must be `>= 0`; both finite)
- `e_rot` is the body-frame small-angle rotation vector from the C7 `AttitudeState` toward an `AttitudeSetpoint`, extracted from the shortest-path error quaternion; `omega_measured` is `AttitudeState.omega_body_rad_s` (damping term)
- **Exactly one controller** — no cascaded rate PID, LQR, MPC, or INDI shipped alongside it
- `compute(setpoint, state) -> BodyRateCommand` — **body-rate number only**: no motor thrust, no mixer matrix, no PWM/ESC, no collective-thrust channel, no position/velocity loop
- **Not wired to C4**: `AutonomyVerb.HOLD` is never auto-routed into this controller; the module never calls `submit_command`
- `level_setpoint(t_s)` — identity-quaternion setpoint for tests/smoke only, no hover-thrust claim
- `run_attitude_controller_smoke()` — pipeline smoke path (reuses the existing `smoke_quad_hal_imu` profile, no schema change)
- `default_safety_gate()` unchanged — computing a rate command is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Controller stub @ 0.5.6 != flying / != motor commands.** Mixer and ESC remain future ICs, each its own front
- Tagged **`v0.5.6`** on Engineer ACCEPT (suite **3280**)

## What v0.5.5 includes

Fase C · **C7** (`B1-fase-c-attitude-estimation-rung`) — **third `flight_control` rung: attitude estimation, sim-only, one algorithm**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/attitude.py` — `ComplementaryAttitudeEstimator`: gyro integration fused with accel-derived tilt via a small-angle proportional correction (`gain` constructor param, default `0.02`, rejects values outside `(0, 1]`)
- **Exactly one algorithm** — explicitly **not** Mahony/Madgwick/EKF/UKF/MEKF by name: no bias/integral state, no gradient descent, no covariance propagation
- `update(sample: ImuSample) -> AttitudeState` — unit quaternion `(w, x, y, z)` mapping body → **`enu`** world frame (locked), plus body angular rate
- **Hard cut:** no magnetometer, no GPS/baro, no online gyro-bias learning, no position/velocity — yaw is gyro-integrated only, with no absolute heading reference
- Reuses C6's `ImuLowPassFilter`/`ImuSample` directly — no parallel filter reimplemented inside the estimator
- `read_attitude(hal, filt, estimator)` pipes `SimulatedImuHal` → `ImuLowPassFilter` → estimator; `vehicle_profiles.run_hal_imu_attitude_smoke()` is the pytest-visible smoke path (reuses the existing `smoke_quad_hal_imu` profile, no schema change)
- **Known simulator limitation:** `SimulatedImuHal` isn't attitude-aware — it always emits a fixed-direction gravity vector, so this Buy's tests validate against synthetic in-memory `ImuSample` sequences with known tilts, not solely via the shared sim HAL
- `default_safety_gate()` unchanged — estimation is not actuation; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Attitude stub @ 0.5.5 != flight-verified attitude / != controlled flight.** Controller, mixer, and ESC remain future ICs, each its own front
- Tagged **`v0.5.5`** on Engineer ACCEPT (suite **3264**)

## What v0.5.4 includes

Fase C · **C6** (`B1-fase-c-imu-filtering-rung`) — **second `flight_control` rung: IMU filtering, sensing post-process only**:

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- `src/jarvis/flight_software/flight_control/filter.py` — `ImuLowPassFilter`: deterministic first-order EMA (`alpha` constructor param, default `0.2`, rejects values outside `(0, 1]`), applied per-axis to `accel_mps2`/`gyro_rad_s`
- `filter_sample(raw: ImuSample) -> ImuSample` reuses C3's `ImuSample` verbatim — no parallel type. First sample after construction/`reset()` seeds the filter unsmoothed
- **Sensing post-process, not estimation:** no quaternion, no Euler angles, no Madgwick/Mahony/EKF output — that belongs to a later, separate estimation-class rung
- `read_filtered(hal, filt)` pipes `SimulatedImuHal.read_imu()` through the filter; `vehicle_profiles.run_hal_imu_filter_smoke()` is the pytest-visible smoke path
- `default_safety_gate()` unchanged — filtering is not actuation, no `allow` required; autonomy `submit_command` still always rejects
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **Filter rung @ 0.5.4 != attitude / != controlled flight.** State estimation, attitude/rate/position control, mixer, and ESC remain future ICs
- Tagged **`v0.5.4`** on Engineer ACCEPT (suite **3249**)

## What v0.5.3 includes

Fase C · **C4 + C5** as **one ACCEPT block** (Engineer 2026-09-20) — package/tag **`v0.5.3`**. Intermediate tag **`v0.5.2` was never cut** (see [docs truth-sync](.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md)).

### C4 — autonomy command surface (`B1-fase-c-autonomy-surface`)

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- Opens `src/jarvis/flight_software/autonomy/` — `AutonomyVerb` (`TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/`PATROL`), `propose_command()`, `submit_command()`
- Every `submit_command` call goes through `SafetyGate.evaluate(...)` first — with `RejectAllSafetyGate`, `HOLD`/`LAND` always `outcome=reject` / `execution="not_attempted"`
- Even a test-local fake `allow` gate cannot make `execution` become `"executed"` — resolves to `"not_implemented"`
- No `flight_software/autonomy/executor.py`; C3 IMU rung unchanged; registry still empty
- **Command surface != flyable autonomy**

### C5 — radio dual-role stub (`B1-fase-c-radio-dual-role`)

- `src/jarvis/capabilities/radio.py` — `RadioStubFrame` → `SimulatedRadioIngress` → `RadioDualRoleResult` (`Intent` and/or `AuthoritySignal`)
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` (live path refuse)
- Optional `SafetyRequest.authority_signal_id` — RejectAll unchanged; authority never implies allow
- **Dual-role stub != live ELRS** — no CRSF/ELRS decode, no serial I/O, no radio→autonomy auto-submit
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- Tagged **`v0.5.3`** on Engineer ACCEPT (suite **3236**)

## What v0.5.1 includes

Fase C · **C3** (`B1-fase-c-first-fc-rung`) — **first `flight_control` rung, sensing-only**:

- **Engineer amendment (on top of the C3 IC): "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** Everything here is a Python platform scaffold, not the production flight controller; the real `flight_control` runtime/firmware will be C++ in later Buys with its own IC. No C++ tree, no CMake created in this Buy.
- Opens `src/jarvis/flight_software/flight_control/` and `src/jarvis/vehicle_profiles/` on disk for the first time — **exactly one rung**: HAL + simulated IMU sample acquisition (`ImuHal`, `SimulatedImuHal`, `ImuSample`)
- No filtering, no state estimation, no attitude/rate/position controller, no mixer, no ESC/PWM, no autonomy verbs — none of it exists in this package yet
- `SimulatedImuHal` is deterministic (same `seed` → same sample sequence) and never touches real hardware, a bus, or a network socket
- One pytest smoke `VehicleProfile` (`smoke_quad_hal_imu`) + `run_hal_imu_smoke()` in `vehicle_profiles/` — not bound to any craft workspace/BOM/catalog SKU
- **Naming split (honesty-critical):** craft catalog `flight_controller` (a BOM part) and `flight_software.flight_control` (this control spine) are different systems of record — never conflated
- `default_safety_gate()` unchanged — still always `RejectAllSafetyGate`; no `AllowAllSafetyGate` anywhere in `src/`
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **First rung stub @ 0.5.1 != controlled flight.** Estimation/control/mixer/ESC/autonomy remain future ICs (C4+)
- Tagged **`v0.5.1`** on Engineer ACCEPT (see `.jes/artifacts/implementation_review_fase_c_first_fc_rung_b1.md`)

## What v0.5.0 includes

Fase C · **C1** scaffold (`B1-fase-c-capability-registry-scaffold`) — **schemas only, no runtime**:

- `src/jarvis/capabilities/` — typed `CapabilityRecord` / `ProviderRecord` / `SkillRecord` (Pydantic) + a `CapabilityRegistry` with a query-only API (list / get-by-id / "who offers capability X?")
- `CapabilityRegistry.load_default()` is **always empty** — 0 capabilities, 0 providers, 0 skills. No path in the product marks flight/actuation as `available`; the `availability` enum only offers `stub` / `not_implemented` in C1
- **No execution path**: no method or field named `execute` / `dispatch` / `command_esc`; nothing here turns a record into a motor/ESC/autonomy command
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/` — craft SoT stays the `v0.4.3` surface
- **Scaffold @ 0.5.0 != Flight Software shipped.** At C1, `flight_software/` did not exist yet; C3 @ `v0.5.1` opens the first Python scaffold rung (production FC runtime remains C++ / future IC)
- Git tag **`v0.5.0`** / `checkpoint-fase-c-capability-registry` (Engineer ACCEPT 2026-09-20)

## What v0.4.3 includes (tag)

Last pre–Fase C checkpoint ([closeout note](.jes/artifacts/engineer_note_v0_4_3_pre_fase_c_close.md)):

- Everything in **v0.4.2** (Fase M mission craft), plus:
  - **D1** docs/` truth-sync @ code · obsolete labeled
  - **U1** Board **Taller 3D** default · Grafo tab · inspector + mount chain to plate · piece chips
  - IDLE first-acquire catalog scoped to `vtx`/`cameras` (FN-009 / terrestrial wizard preserved)
- Live suite **3166** · UI **132**
- Next: **Fase C** @ **`0.5.0`** on first Engineer ★ Buy

## What v0.4.2 included

Mission craft software checkpoint (**Fase M CLOSED** — [M7 closeout](.jes/artifacts/engineer_note_fase_m_closeout_m7.md)):

- Continuity mission intent + wizard vigilancia nudge + SYSTEM_DEFINITION **B** routing
- Mission `mass_g` → AUW; Continuity ladder mount + autonomía objetivo; `power_w` declare + Phoenix catalog W
- `library/cameras` Phoenix 2 + `library/vtx` Zeus 800 — fluid catalog help-choose / rebind / mass mirror (RF mW ≠ DC W)
- BOM `[sku]` display for cameras / FC / sensors; craft-montage user guide sync
- Live suite **3165** · UI **105**

## What v0.4.1 included

- Everything in **v0.4.0** (Continuity spatial assembly), plus Board **Situar**:
  - **C-113** — Scene3D drag → `board_pose_bridge` → same `set_component_declared_box_pose` writer as CLI `declara…`
  - Free camera while situating (no forced cenital); screen-plane drag follows the cursor; Shift = profundidad (Y)
  - Situar UX: larger pane, zoom range, live preview
  - Standoff count gate B4-min (`count==4` → corners; else omit)
- Live suite **2669** · UI **80**
- Locks unchanged: Prop/Energy = HD-004 wall; System Optimization deferred until pain; screening AABB ≠ fit VERIFIED

## What's landed between v0.4.1 and v0.4.2 (now tagged)

The **craft montage** + **mission craft** arc — empty project → montaje honesto + identidad/masa/montaje/potencia/VTX sin inventar física:

- Checklist family, estimated-temporary dims, arm/disk Visor, FC/sensors library envelopes
- Mission payload identity → cameras/radio → Continuity ladder → catalog seeds
- See `docs/IMPLEMENTATION_TASKS.md` and [USER_GUIDE_CRAFT_MONTAGE.md](docs/USER_GUIDE_CRAFT_MONTAGE.md)

## Next

**Tip tagged `v0.5.40`** — C39 position ★ ACCEPT CLOSED (sim position + xy→tilt; ≠ live GPS ≠ flying). C38 @ `v0.5.39`. C37 @ `v0.5.38`. C36 @ `v0.5.37`. Cola: C40 autonomy executor. Desk DFU parked until bench — [bench note](.jes/artifacts/engineer_note_fase_c_bench_before_silicon_2026_09_24.md).

Parked (bags/lab): C30 DFU smoke · plate-box · Path N · HD-* · more camera/radio SKUs · Board inspector polish · GPIO/DShot wire · craft↔FS wiring · deepen policy beyond one aux · Linux baud.

See `docs/IMPLEMENTATION_TASKS.md`.

## Docs

| Doc | Role |
|-----|------|
| [VISION.md](VISION.md) | Product contract (non-technical) |
| [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) | v1 usable — when a project is “done” |
| [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md) | A' — Situation / Evidence / Next useful step |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system is built |
| [docs/system_map/README.md](docs/system_map/README.md) | System Map — connections & authority |
| [docs/USER_GUIDE_CRAFT_MONTAGE.md](docs/USER_GUIDE_CRAFT_MONTAGE.md) | Command-level walk: empty project → montaje honesto en Board |
| [docs/IMPLEMENTATION_TASKS.md](docs/IMPLEMENTATION_TASKS.md) | Roadmap, gaps, software/product debt |  
| [docs/HARDWARE_DEBT.md](docs/HARDWARE_DEBT.md) | Physics debt gated on T1/T2 lab (ESC η, battery C-rate, sag, OP→consumo) |
| [.jes/artifacts/cli_findings_post_catalog_bind_v1.md](.jes/artifacts/cli_findings_post_catalog_bind_v1.md) | Living CLI findings register (G9–G20) |
| [src/jarvis/README.md](src/jarvis/README.md) | Deeper product / flow reference |

## Tags

`v0.5.21` / `checkpoint-fase-c-crsf-host-baud` — Fase C C23: Darwin IOSSIOSPEED 420000 + raw 8N1 on C22 FD; suite **3504** · UI **132**.  
`v0.5.20` / `checkpoint-fase-c-crsf-host-serial` — Fase C C22: CRSF host serial ingest (pty); suite **3485** · UI **132**.  
`v0.5.11` / `checkpoint-fase-c-cpp-scaffold` — Fase C C13: first C++ flight_control host scaffold; suite **3358** · UI **132**.  
`v0.5.10` / `checkpoint-fase-c-rate-torque` — Fase C C12: rate→torque honesty bridge; suite **3348** · UI **132**.  
`v0.5.9` / `checkpoint-fase-c-sim-tip` — Fase C C11: toy closed-loop wooden-ladder tip (+ C7 accel sign fix); suite **3330** · UI **132**.  
`v0.5.8` / `checkpoint-fase-c-esc-pwm` — Fase C C10: force→PWM µs + SimulatedEscSink; suite **3315** · UI **132**.  
`v0.5.7` / `checkpoint-fase-c-mixer` — Fase C C9: quad-X mixer; suite **3297** · UI **132**.  
`v0.5.6` / `checkpoint-fase-c-controller` — Fase C C8: PD attitude → body-rate command; suite **3280** · UI **132**.  
`v0.5.5` / `checkpoint-fase-c-attitude` — Fase C C7: complementary attitude estimation rung; suite **3264** · UI **132**.  
`v0.5.4` / `checkpoint-fase-c-imu-filter` — Fase C C6: IMU EMA/low-pass filter rung; suite **3249** · UI **132**.  
`v0.5.3` / `checkpoint-fase-c-autonomy-radio` — Fase C C4+C5 one block: autonomy command surface + radio dual-role stub; suite **3236** · UI **132**. (**No `v0.5.2` tag** — see truth-sync note.)  
`v0.5.1` / `checkpoint-fase-c-first-fc-rung` — Fase C C3: first `flight_control` rung (HAL + simulated IMU), `flight_software/`+`vehicle_profiles/` opened; Python scaffold, production FC runtime is C++ (future IC); suite **3206** · UI **132**.  
`v0.5.0` / `checkpoint-fase-c-capability-registry` — Fase C open: empty Capability Registry scaffold; suite **3181** · UI **132**.  
`v0.4.3` / `checkpoint-board-taller-3d` — pre–Fase C CLOSED: docs truth-sync + Board Taller 3D; suite **3166** · UI **132**.  
`v0.4.2` / `checkpoint-fase-m-mission-craft` — Fase M CLOSED: mission mass + Continuity ladder + cameras/VTX seeds + B routing; suite **3165** · UI **105**.  
`v0.4.1` / `checkpoint-board-situar` — Board Situar drag→pose (C-113) + free camera + standoff count gate; suite **2669** · UI **80**.  
`v0.4.0` / `checkpoint-continuity-spatial-assembly` — Continuity spatial assembly (*situar el mapa*); suite **2652**.  
`v0.3.8` / `checkpoint-spatial-board-projector` — ship `spatial_board.py` (was gitignored); `/workspace/` ignore.  
`v0.3.7` / `checkpoint-structure-representation-closed` — Structure representation arc closed (catalog→parts→rebind→plates); suite **2294**.  
`v0.3.6` / `checkpoint-experimental-prop-energy-closed` — experimental prop/energy/Structure A/fail-routing construction closed; knowledge-parity phase starts.  
`v0.3.5` / `checkpoint-phase25-hover-energy` — Phase 2.5 honest hover-regime autonomy.  
`v0.3.4` / `checkpoint-motor-op-voltage-coherence` — motor OP voltage gate + DSE live params.  
`v0.3.3` / `checkpoint-validation-case-regression-gate` — Validation Case probe/docs.  
`v0.3.2` / `checkpoint-deferred-queue-cd` — Deferred Queue C+D.  
`v0.3.1` / `checkpoint-next-engineering-block` — G24-A + P2-2 OP bridge.  
`v0.3.0` / `checkpoint-propeller-catalog-bind` — propeller help-choose → exact OP.  
`v0.2.0` — H1–H4 handoffs closed; System Map at 0 RED.  
`v0.1.0-prototype` — first functional cut.
