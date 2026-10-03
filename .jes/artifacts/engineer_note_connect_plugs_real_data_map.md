# Engineer note — Connect plugs / real-data debt map

**Date:** 2026-10-03  
**Status:** **OPEN living map** (seeded by `B1-connect-plugs-real-data-map`, T33 @ `0.6.42`)  
**Author:** Claude Code (forensic verification pass) · seed by JES/Cursor

**Purpose:** Jarvis is full of places where the architecture is deliberately left ready for real data (GPS coordinates, battery telemetry, live sensors, voice/radio ingress, hardware on a bench) but today stays honest instead of inventing it. Those seams are scattered across IC/review/CONNECTIONS/PLATFORM/code comments. **This is the one place to look** when real data shows up and you need to know *where to connect it* — not a roadmap, not a priority list, not a second PRIORIDAD.

**Not this document:** a schedule of when each row gets built. A row's `status` says what's true today; `connect_later` says what the eventual wiring looks like. Closing a row happens in that row's own Buy, which then updates this map (lock 5 of the DC).

---

## Taxonomy

| Type | Meaning |
|---|---|
| **A** | Software connect plug — architecture is wired, only a real data source needs to fill it in |
| **B** | Honesty stub — a channel/capability/execution field that always refuses or never claims success, by design |
| **C** | Parked hardware/lab — needs a physical bench, SKU, or lab campaign before any software Buy can close it |
| **D** | Horizon — a larger not-yet-started product surface (voice/world) that later rows will plug into |

---

## A — Software connect plugs

| id | type | deferred | seam_today | connect_later | status | evidence |
|---|---|---|---|---|---|---|
| `sd-go-to` | A | GO_TO coords → T20 sim tick | `JarvisOrchestrator._sim_autonomy_tick_note` + `_resolve_go_to_destination` (metadata `go_to_x_m`/`go_to_y_m` → prove-now parse → else honest sin destino) | later GPS/world/voice fill `Intent.metadata`; prove-now `go to <x> <y>` already works in chat | **★ CLOSED** — T32 ★ ACCEPT CLOSED @ **`v0.6.41`** (stacked on this tip) · SD-GO_TO note CLOSED | `.jes/artifacts/implementation_review_assistant_chat_go_to_destination_b1.md` · `.jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md` |
| `sim-tick-takeoff` | A | TAKEOFF sim tick | `_handle_vehicle_takeoff` never calls `_sim_autonomy_tick_note` at all (verified: no call site) | a future Buy would call the tick helper after `allow`, same shape as HOLD/LAND once an altitude target exists | Parked — no named Buy | `src/jarvis/core/orchestrator.py::_handle_vehicle_takeoff` |
| `sim-tick-return-home` | A | RTL sim tick | `_handle_vehicle_return_home` never calls the tick helper (verified) | same pattern, needs a home-point target | Parked — no named Buy | `src/jarvis/core/orchestrator.py::_handle_vehicle_return_home` |
| `sim-tick-follow` | A | FOLLOW sim tick | `_handle_vehicle_follow` never calls the tick helper (verified) | same pattern, needs a target/person | Parked — no named Buy | `src/jarvis/core/orchestrator.py::_handle_vehicle_follow` |
| `sim-tick-patrol` | A | PATROL sim tick | `_handle_vehicle_patrol` never calls the tick helper (verified) | same pattern, needs a route/circuit | Parked — no named Buy | `src/jarvis/core/orchestrator.py::_handle_vehicle_patrol` |
| `takeoff-altitude-params` | A | TAKEOFF altitude | `propose_command(AutonomyVerb.TAKEOFF, …, params={})` always empty (verified) | a metadata/prove-now plug analogous to `sd-go-to`, once named | **OPEN gap — no named metadata Buy** (unlike `sd-go-to`, which now has T32) | `src/jarvis/core/orchestrator.py::_handle_vehicle_takeoff` |
| `follow-target-params` | A | FOLLOW target | `propose_command(AutonomyVerb.FOLLOW, …, params={})` always empty (verified) | a target-identity plug, once named | **OPEN gap — no named metadata Buy** | `src/jarvis/core/orchestrator.py::_handle_vehicle_follow` |
| `patrol-route-params` | A | PATROL route | `propose_command(AutonomyVerb.PATROL, …, params={})` always empty (verified) | a route/waypoint-list plug, once named | **OPEN gap — no named metadata Buy** | `src/jarvis/core/orchestrator.py::_handle_vehicle_patrol` |
| `sim-autonomy-z-m` | A | Optional altitude in sim ticks | `SimAutonomyParams.z_m` exists and is read by the sim executor (HOLD/GO_TO/LAND all consult it, falling back to the plant's true z) — but no chat caller ever sets it (verified: no `z_m=` call site in `orchestrator.py`'s autonomy path) | a future altitude-bearing Buy (e.g. TAKEOFF altitude, or a GO_TO 3-D extension) would pass `z_m` the same way T32 now passes `x_m`/`y_m` | OPEN — shaped, unused | `src/jarvis/flight_software/autonomy/sim_executor.py::SimAutonomyParams` |

## B — Honesty stubs

| id | type | deferred | seam_today | connect_later | status | evidence |
|---|---|---|---|---|---|---|
| `flight-caps-not-implemented` | B | Real vehicle execution for every `flight.*` verb | All seven `flight.*` capabilities (`hold`/`land`/`go_to`/`takeoff`/`return_home`/`follow`/`patrol`) stay `not_implemented`/`vehicle` in the registry; their Skill rows flipped `available` only as a **gate**, never a capability claim | a real flight-control integration Buy would flip the capability itself, not just the Skill gate | OPEN — intentional, by design | `src/jarvis/capabilities/data/default_registry.json` |
| `ops-charge-not-implemented` | B | Real battery charging | `ops.charge` stays `not_implemented`/`device`; `_handle_ops_charge` never calls `propose_command`/any executor | a real charger-ops integration Buy, parked on hardware | OPEN + Parked (hardware) | `src/jarvis/core/orchestrator.py::_handle_ops_charge` |
| `c4-execution-never-executed` | B | `AutonomySubmissionResult.execution == "executed"` | `submit_command` only ever returns `"not_attempted"` (reject) or `"not_implemented"` (allow) — verified, no third branch exists | a real actuation Buy would need an explicit, separate Engineer ★ to add that branch | OPEN — locked by design | `src/jarvis/flight_software/autonomy/surface.py` |
| `arm-latch-not-esc` | B | ESC/motor arm ≠ chat Safety latch | `_handle_arm_policy`/`_handle_disarm_policy` only toggle the process-scoped `ArmedAllowlistSafetyGate` latch — never touch ESC/ `SimulatedEscSink`/motors (AST-fenced, T16) | a real arm Buy would be a separate, ESC-fence-reviewed change, not a latch rename | OPEN — honesty by design | `src/jarvis/core/orchestrator.py::_handle_arm_policy` |
| `voice-intent-ingress` | B | Voice → `Intent` | `VoiceIntentAdapter.parse(raw_text) -> Intent(source=VOICE)` mirrors `TerminalIntentAdapter`; twelve orch classify sites honor caller's `source` (default `TERMINAL`) via `_parse_intent`. Radio/Api unchanged — still `NotImplementedError` | T36 (fixture voice loop) exercises this seam end-to-end without a mic; T37 later wires a real external STT into the same `parse(raw_text)` call | **★ CLOSED** — T35 ★ ACCEPT CLOSED @ **`v0.6.43`** | `src/jarvis/capabilities/intent.py::VoiceIntentAdapter` · [review ★](implementation_review_assistant_voice_intent_ingress_b1.md) · [voice DC ★](design_contract_assistant_chat_voice_channels_b0.md) |
| `radio-intent-live` | B | Live/unclassified radio → `Intent` | `RadioIntentAdapter.parse` always raises `NotImplementedError` (verified); `jarvis.capabilities.radio.SimulatedRadioIngress` exists as a typed, simulated stand-in only | a real radio Buy implements this adapter on real hardware | Parked | `src/jarvis/capabilities/intent.py::RadioIntentAdapter` |
| `api-intent-ingress` | B | API → `Intent` | `ApiIntentAdapter.parse` always raises `NotImplementedError` (verified) | a real API ingress Buy implements this adapter | Parked | `src/jarvis/capabilities/intent.py::ApiIntentAdapter` |
| `ui-intent-ingress` | B | UI → `Intent` | **Forensic extension (not in seed §0b):** `IntentSource.UI = "ui"` exists as an enum member, but unlike VOICE/RADIO/API there is no `UiIntentAdapter` class at all — not even a `NotImplementedError` stub | a real UI Buy would need to add the adapter class first, then implement it | **OPEN gap — enum member with no adapter stub** | `src/jarvis/capabilities/intent.py::IntentSource` |

## C — Parked hardware/lab

| id | type | deferred | seam_today | connect_later | status | evidence |
|---|---|---|---|---|---|---|
| `copper-esc-live-flight` | C | Live ESC/motors/copper flight | `SimulatedEscSink` (force→PWM µs stub, AST-fenced out of `core`/`adapters` by T16) | a real craft, assembled and bench-tested | Parked — hasta componentes/ensamblar | `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD "Parked (hasta componentes / ensamblar)" |
| `esc-gpio-sink` | C | GPIO `EscOutput` driver (vs. `SimulatedEscSink`) | `SimulatedEscSink` only (C10) | a GPIO-backed driver on real silicon | Parked — needs bench | `.jes/artifacts/engineer_note_fase_c_bench_before_silicon_2026_09_24.md` |
| `dshot-wire` | C | DShot on a real wire | DShot encode exists as a stub (C-series), never wired to a physical line | wire DShot to a real ESC once on the bench | Parked — needs bench | same bench note |
| `gyro-spi1-live` | C | ICM42688P SPI1 live (vs. `sim_imu_hal.py`) | `sim_imu_hal.py` (simulated gyro/accel HAL) | real SPI1 transactions against the ICM42688P | Parked — needs bench | same bench note |
| `mcu-usart-on-chip` | C | On-chip USART (vs. stub) | UART HAL stub (C-series) | on-chip USART peripheral, once on silicon | Parked — needs bench | `docs/IMPLEMENTATION_TASKS.md` row "Silicon" |
| `c30-desk-dfu` | C | Desk DFU flash (overwrites Betaflight) | FC still runs Betaflight; C30 IC written but parked | flash Jarvis once a trusted bench/restore path exists | Parked — needs a trusted bench/restore path first | same bench note |
| `linux-crsf-baud` | C | Linux 420000 baud CRSF (Darwin `IOSSIOSPEED` path already done, C23) | Darwin-only `IOSSIOSPEED` 420000 baud opt-in (C23) | the Linux-equivalent ioctl/termios path | Parked | `docs/IMPLEMENTATION_TASKS.md` row "Silicon" |
| `live-elrs` | C | Live ELRS RF decode (vs. CRSF fixture parse, C19/C21/C22/C23) | CRSF byte-stream/serial/baud stack parses fixtures and host serial, never live RF | a real ELRS receiver on the wire | Parked | `.jes/artifacts/implementation_review_fase_c_crsf_link_stub_b1.md` and siblings ("≠ live ELRS" repeated through C19–C23) |
| `sim-sensor-hals` | C | Live GPS/baro/mag/IMU vs. `Simulated*Hal` | `sim_imu_hal.py`, `sim_mag_hal.py`, `sim_position_hal.py`, `sim_altitude_hal.py` (all simulated, no live counterpart on disk — forensically confirmed) | live sensor drivers on real silicon | Parked | `src/jarvis/flight_software/flight_control/` |
| `hd-001` | C | Battery C-rate derating (M3) | no measured curve for the current SKU | T1 (manufacturer curve) or T2 (instrumented bench) campaign | OPEN lab | `docs/HARDWARE_DEBT.md` HD-001 |
| `hd-002` | C | Isolated ESC loss (`P_motor_input` → `P_battery`) | no isolated ESC/motor power measurement | bench T2 with ESC + motor + dual power measurement | OPEN lab | `docs/HARDWARE_DEBT.md` HD-002 |
| `hd-003` | C | Sag / OCV / `R_internal` under load (parked) | no sag/OCV measurement under load | a logged `V(t)`/`I(t)` bench campaign | OPEN lab | `docs/HARDWARE_DEBT.md` HD-003 |
| `hd-004` | C | Operating-Point → consumption curve (flight autonomy) | `hover_energy_autonomy_min` ≈ 1.32 min (Combo A) — no OP→consumption curve | an instrumented flight/bench OP curve | OPEN lab | `docs/HARDWARE_DEBT.md` HD-004 |
| `hd-005` | C | Craft OP XING-E + Gemfan 51466-3 + 4S (#4d follow-on) | no measured craft Operating Point for this prop/motor/battery combo | a bench campaign on the actual SKUs | OPEN lab | `docs/HARDWARE_DEBT.md` HD-005 |

## D — Horizon

| id | type | deferred | seam_today | connect_later | status | evidence |
|---|---|---|---|---|---|---|
| `a4-voice-world` | D | Voice/world reusing the now-complete Skill-first set | Chat-only `run_skill` Skill-first (all twelve declared Skills, T22–T31) · voice Intent ingress ★ @ `v0.6.43` · fixture voice loop ★ @ `v0.6.44` · external STT process seam ★ @ `v0.6.45` · external TTS process seam ★ @ `v0.6.46` · v1 checkpoint Implemented @ `0.7.0` (T39, not yet ★ ACCEPT): fixture → twelve Skills → fake TTS + STT→Skill→TTS proven end-to-end | None — voice half complete pending T39 ★; world half = T40 (own DC later) | **Voice half Implemented, pending review**; world deferred (T40) | [cola note](engineer_note_voice_phase_c_cola.md) · [voice DC ★](design_contract_assistant_chat_voice_channels_b0.md) · T39 IC @ `0.7.0` |
| `world-package` | D | `world/` rooms/devices | No `world` package exists | a new `src/jarvis/world/` package, once scoped | Parked — **not on disk** · **not voice v1** · cola **T40** (own DC) | `src/jarvis/` directory listing · [cola note](engineer_note_voice_phase_c_cola.md) |
| `go-to-metadata-plug-for-world` | D | world/GPS/voice → GO_TO's `go_to_x_m`/`go_to_y_m` metadata keys | T32 `_resolve_go_to_destination` metadata connect plug landed @ `v0.6.41` (see `sd-go-to`) | a later world/voice Buy populates `Intent.metadata["go_to_x_m"]`/`["go_to_y_m"]`; no new resolver needed — T34-inv Q6 recommends voice rely on this metadata path rather than STT-transcribed spoken coordinates | **OPEN shaped** — plug ready; world/voice source still horizon | `.jes/artifacts/design_contract_assistant_chat_go_to_destination_b0.md` · T32 ★ @ `v0.6.41` · [investigation report](investigation_report_assistant_voice_e2e_b0.md) |

---

## Footnotes (scoped out per DC lock 3)

- **Geometry Path N / Board polish** — these are mechanical/geometry debts, a different domain than the Assistant/Skill/sim/copper/ops seams this map indexes. Not rows here; see `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD "Parked (silicon / lab)" line for pointers.
- **Continuity kit-tip spam (G1)** and **closed Skill-first stubs already flipped** (HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL/ARM/DISARM/CHARGE Skills, all `available` as of T31) are explicitly out of scope — they are not open debts, or belong to a laterally different backlog.

---

## Maintenance

When a Buy closes or opens a row in this map, that Buy's own docs pass updates the row's `status`/`evidence` here (DC lock 5) — this Buy (T33) only seeds and forensically verifies the map; it does not close any of the debts it lists.
