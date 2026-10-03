# Implementation Contract — Connect plugs / real-data debt map (`B1-connect-plugs-real-data-map`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.42`**

**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT → tag `v0.6.42`.  
**Parents:** [DC ★ CLOSED](design_contract_connect_plugs_real_data_map_b0.md) · PRIORIDAD parked · [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md) · `docs/HARDWARE_DEBT.md`  
**Type:** Docs-only index Buy — forensic map of real-data / connect-later debts.  
**Opens:** **`0.6.42` / `v0.6.42`**. **Cola:** **T33**

**Not:** implementing any connect (GPS, ESC, battery, voice) · closing T32 · inventing plugs · rewriting CONNECTIONS wholesale · tip pins · runtime behavior change.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-connect-plugs-real-data-map`** |
| 2 | **Create SoT:** `.jes/artifacts/engineer_note_connect_plugs_real_data_map.md` — living index. Title + date + status **OPEN living map**. Intro: purpose = “when real data applies, connect here”; not a roadmap |
| 3 | **Forensic pass required:** Claude must re-verify tip (docs + `src/` + `HARDWARE_DEBT` + engineer notes + PRIORIDAD parked). Do **not** copy Cursor’s seed blindly — confirm symbols exist; note T32 code may still be AUTHORIZED-not-landed |
| 4 | **Seed inventory (must appear, verify/extend):** see §0b. Add rows if forensic finds more; mark **Gap** where empty-params honesty has no named plug Buy |
| 5 | **Table columns (exact):** `id` · `type` (A/B/C/D) · `deferred` · `seam_today` · `connect_later` · `status` · `evidence` |
| 6 | **Wire docs:** PRIORIDAD — one line under Software debt / Parked pointing to this map; short PLATFORM § note; CONNECTIONS one “Extended by T33” sentence (**no new C-xxx**). Optional: one-line pointer from SD-GO_TO note + HARDWARE_DEBT header |
| 7 | **`pyproject.toml` → `0.6.42`**. No `src/` behavior change. Tip-pin + ESC fence still green (docs-only should not break them) |
| 8 | Tests: minimal — e.g. assert SoT file exists + contains required section headers / at least the seed `id`s listed in §0b (string presence). No tip pins |
| 9 | Out: implementing plugs · merging T32 · claiming debts CLOSED · copper/voice/GPS work |

### 0b. Seed inventory (Cursor forensic 2026-10-03 — verify)

**A — software connect plugs**

| id | deferred (short) | seam hint | status hint |
|---|---|---|---|
| `sd-go-to` | GO_TO coords → T20 sim tick | `_sim_autonomy_tick_note` / T32 `_resolve_go_to_destination` + metadata `go_to_x_m`/`go_to_y_m` | AUTHORIZED T32 @ 0.6.41 |
| `sim-tick-takeoff` | TAKEOFF sim tick | no tick in `_handle_vehicle_takeoff`; C40 unsupported | Parked |
| `sim-tick-return-home` | RTL sim tick | same pattern | Parked |
| `sim-tick-follow` | FOLLOW sim tick | same | Parked |
| `sim-tick-patrol` | PATROL sim tick | same | Parked |
| `takeoff-altitude-params` | TAKEOFF altitude params | `params={}` | OPEN gap (no named Buy) |
| `follow-target-params` | FOLLOW target | `params={}` | OPEN gap |
| `patrol-route-params` | PATROL route | `params={}` | OPEN gap |
| `sim-autonomy-z-m` | optional `z_m` in sim | `SimAutonomyParams.z_m` unused by chat | OPEN shaped |

**B — honesty stubs**

| id | deferred | seam hint | status hint |
|---|---|---|---|
| `flight-caps-not-implemented` | real vehicle execute | `flight.*` not_implemented; Skills gate-only | OPEN intentional |
| `ops-charge-not-implemented` | real battery charge | `ops.charge` + `_handle_ops_charge` | OPEN + Parked hardware |
| `c4-execution-never-executed` | `execution=executed` | `submit_command` surface | OPEN locked |
| `arm-latch-not-esc` | ESC arm ≠ Safety latch | `_handle_arm_policy` | OPEN honesty |
| `voice-intent-ingress` | Voice→Intent | `VoiceIntentAdapter` NotImplemented | Parked phase C |
| `radio-intent-live` | live radio Intent | `RadioIntentAdapter` NotImplemented | Parked |
| `api-intent-ingress` | API Intent | `ApiIntentAdapter` NotImplemented | Parked |

**C — parked hardware/lab**

| id | deferred | status hint |
|---|---|---|
| `copper-esc-live-flight` | live ESC/motors/copper | Parked |
| `esc-gpio-sink` | GPIO EscOutput driver | Parked |
| `dshot-wire` | DShot on wire | Parked |
| `gyro-spi1-live` | ICM42688P SPI1 live | Parked |
| `mcu-usart-on-chip` | on-chip USART | Parked |
| `c30-desk-dfu` | desk DFU stub bin | Parked |
| `linux-crsf-baud` | Linux 420000 baud | Parked |
| `live-elrs` | live ELRS RF | Parked |
| `sim-sensor-hals` | live GPS/baro/mag/IMU vs Simulated*Hal | Parked |
| `hd-001` … `hd-005` | C-rate / ESC loss / sag / OP consumption / craft OP | OPEN lab (HARDWARE_DEBT) |

**D — horizon**

| id | deferred | status hint |
|---|---|---|
| `a4-voice-world` | voz/world reuse Skills | Parked / Horizon |
| `world-package` | `world/` rooms/devices | Parked not on disk |
| `go-to-metadata-plug-for-world` | world/GPS/voice → GO_TO metadata | AUTHORIZED via T32 design |

---

## 1. Files

| Path | Change |
|---|---|
| `.jes/artifacts/engineer_note_connect_plugs_real_data_map.md` | **new** SoT map |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD link + T33 row |
| `docs/PLATFORM_CAPABILITY_VISION.md` | short T33 note |
| `docs/system_map/CONNECTIONS.md` | one Extended-by sentence |
| `docs/HARDWARE_DEBT.md` | optional one-line pointer at top |
| `tests/test_connect_plugs_real_data_map_b1.py` | **new** presence/seed-id asserts |
| `pyproject.toml` | `0.6.42` |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | SoT file exists under `.jes/artifacts/` |
| T2 | Contains taxonomy legend A/B/C/D and a markdown table |
| T3 | Contains every seed `id` from §0b (string match) |
| T4 | No tip pins |

---

## 3. Acceptance

- [ ] Living map SoT verified against tip · PRIORIDAD wired · `0.6.42` · gaps called out  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.42`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-connect-plugs-real-data-map (T33)
Parent tip: T31 ★ @ v0.6.40 (T32 @ 0.6.41 may be in flight). Package 0.6.42.

IC: .jes/artifacts/implementation_contract_connect_plugs_real_data_map_b1.md
DC: .jes/artifacts/design_contract_connect_plugs_real_data_map_b0.md (★ CLOSED)

Docs-only: living SoT map of connect plugs / real-data debts.
- Create .jes/artifacts/engineer_note_connect_plugs_real_data_map.md
- Forensic re-verify tip (do not blind-copy seed). Confirm symbols;
  note if T32 resolver not landed yet.
- Table columns: id | type(A/B/C/D) | deferred | seam_today |
  connect_later | status | evidence
- Include all §0b seed ids; extend if you find more; mark Gaps
  (TAKEOFF altitude / FOLLOW target / PATROL route lack named Buys).
- Wire PRIORIDAD + short PLATFORM + CONNECTIONS (no new C-xxx).
  Optional HARDWARE_DEBT header pointer.
- tests/test_connect_plugs_real_data_map_b1.py — file exists + seed ids.
- pyproject 0.6.42. No src/ behavior change. No tip pins. No ACCEPT claim.
Not implementing GPS/ESC/battery/voice · not closing T32 · not inventing plugs.
```
