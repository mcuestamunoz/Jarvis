# Implementation Report — Connect plugs / real-data debt map (`B1-connect-plugs-real-data-map`, T33)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_connect_plugs_real_data_map_b1.md`](implementation_contract_connect_plugs_real_data_map_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_connect_plugs_real_data_map_b0.md) · PRIORIDAD parked · [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md) · `docs/HARDWARE_DEBT.md` · T31 ★ ACCEPT CLOSED @ `v0.6.40` (this Buy's own tip; T32 @ `0.6.41` branches separately and may still be in flight)  
**Status:** **★ ACCEPT CLOSED** @ tip **`v0.6.42`** (stacked on T32 ★ `v0.6.41`).  
**Package / tag:** `0.6.42` / **`v0.6.42`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `.jes/artifacts/engineer_note_connect_plugs_real_data_map.md` | **new** — the living SoT map: taxonomy legend (A software plug / B honesty stub / C parked hardware/lab / D horizon), four tables with the exact 7-column schema the IC locks (`id · type · deferred · seam_today · connect_later · status · evidence`), footnotes for the DC's explicit scope-out items, and a maintenance note |
| `tests/test_connect_plugs_real_data_map_b1.py` | **new** T1–T4 |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD header + Software-debt line + SoT line + COLA header + the T33 row updated to "Implemented…await Cursor review"; T32's own row/SD-GO_TO row left untouched (different Buy's docs responsibility) |
| `docs/PLATFORM_CAPABILITY_VISION.md` | T33's note updated to "Implemented" and expanded with the forensic findings (T32 not-yet-landed caveat, the `ui-intent-ingress` extension) |
| `docs/system_map/CONNECTIONS.md` | T33's "Extended by" sentence updated to "Implemented" (no new C-xxx, unchanged) |
| `docs/HARDWARE_DEBT.md` | one-line pointer added right under the intro, directing to the new map for the full connect-later index (hardware-only scope stays unchanged otherwise) |
| `.jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md` | one-line pointer added to the SoT-pointers line, cross-referencing the new map's `sd-go-to` row — Status line (`Buy AUTHORIZED`) left untouched, since T32 itself still owns closing this note |
| `pyproject.toml` | `0.6.42` |

**Not touched:** any `src/` file (verified via `git status` before/after — only docs + the two new `.jes`/`tests` files changed), the SD-GO_TO note's own Status line (stays "Buy AUTHORIZED" — T32's Buy, not this one's, closes it), T32's own COLA row in `IMPLEMENTATION_TASKS.md` (left as `★ AUTHORIZED`, accurate for *this* branch's own tip, which forked before T32's implementation commit and does not contain it), tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green).

---

## 2. Forensic pass (IC §0 lock 3 — do not blind-copy the seed)

Every seed id from the IC's §0b table was checked against this Buy's own tip (not assumed from the seed's own status hints):

- **`sd-go-to`** — the seed hint said "AUTHORIZED T32 @ 0.6.41". Checked directly: `grep`ed `orchestrator.py`/`assistant_task.py` on this branch for `_resolve_go_to_destination`/`parse_go_to_destination` — **neither symbol exists here**. Traced further: Claude's own T32 implementation is pushed to a sibling branch (`cursor/chat-go-to-destination-impl-8ac5` @ commit `1d7414f`), not yet reviewed/landed. The map's `status` cell for this row and for `go-to-metadata-plug-for-world` (D) says exactly that — "Implemented, not yet landed on this tip" — rather than repeating the seed's now-stale "AUTHORIZED" framing.
- **`sim-tick-takeoff`/`sim-tick-return-home`/`sim-tick-follow`/`sim-tick-patrol`** — confirmed by reading `_handle_vehicle_takeoff`/`_handle_vehicle_return_home`/`_handle_vehicle_follow`/`_handle_vehicle_patrol` directly: none calls `_sim_autonomy_tick_note` at all (not even a caught-and-reported attempt, unlike GO_TO).
- **`takeoff-altitude-params`/`follow-target-params`/`patrol-route-params`** — confirmed each `propose_command(...)` call site uses `params={}` literally, with no named Buy anywhere in `IMPLEMENTATION_TASKS.md`'s COLA for a metadata plug (unlike `sd-go-to`, which now has T32).
- **`sim-autonomy-z-m`** — confirmed `SimAutonomyParams.z_m` is read by the sim executor for HOLD/GO_TO/LAND (falls back to the plant's true z when absent) but grepped `orchestrator.py` for any `z_m=` call site in the autonomy path — none exists.
- **B-series (`flight-caps-not-implemented`, `ops-charge-not-implemented`, `c4-execution-never-executed`, `arm-latch-not-esc`, `voice-intent-ingress`, `radio-intent-live`, `api-intent-ingress`)** — each verified directly against `default_registry.json`, `orchestrator.py`, `flight_software/autonomy/surface.py`, and `capabilities/intent.py`.
- **C-series** — HD-001…HD-005 confirmed present in `HARDWARE_DEBT.md` (expanded to five individual rows in the map, rather than the seed's condensed `hd-001…hd-005` notation, so each id is a literal, independently-testable string); the silicon/bench items (`esc-gpio-sink`, `dshot-wire`, `gyro-spi1-live`, `mcu-usart-on-chip`, `c30-desk-dfu`, `linux-crsf-baud`, `live-elrs`) confirmed against the bench note and PRIORIDAD's "Parked (silicon / lab)" line; `sim-sensor-hals` confirmed by listing `src/jarvis/flight_software/flight_control/` for the four `sim_*_hal.py` files and finding no live counterpart.
- **D-series** — `a4-voice-world` confirmed against PRIORIDAD's own "A4" row; `world-package` confirmed by listing `src/jarvis/` directly — **no `world` directory exists** (not assumed from the seed, checked).
- **Extension found beyond the seed:** `IntentSource.UI = "ui"` exists as an enum member in `capabilities/intent.py`, but unlike VOICE/RADIO/API there is **no `UiIntentAdapter` class at all** — not even a `NotImplementedError` stub. Added as `ui-intent-ingress` (type B) with status "OPEN gap — enum member with no adapter stub", called out explicitly in the map as a forensic addition, not part of the IC's seed.

No new Gap beyond the IC's own explicit callouts (TAKEOFF altitude / FOLLOW target / PATROL route) was found to be missing a named Buy — those three were already flagged correctly in the seed and are reproduced as-is.

---

## 3. Tests executed

```text
pytest tests/test_connect_plugs_real_data_map_b1.py -q
→ 4 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3957 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T33 tip (stash push/pop): baseline was `3953 passed, 9 skipped, 0 failed`. **Zero behavior change** — the only delta is the 4 new T33 tests passing; `git status` before committing confirmed no `src/` file was touched, only docs + the two new files.

---

## 4. Remaining

None for this Buy — it is explicitly docs-only and does not close any debt it lists (DC lock 5: each row closes in its own future Buy, which then updates this map). Maintenance going forward: whenever a Buy opens or closes a connect-later debt, that Buy's own docs pass should update the corresponding row here.
