# Implementation Contract — Fase C CRSF host serial ingest (`B1-fase-c-crsf-host-serial`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (host serial ingest ≠ live ELRS ≠ RX connected · pytest green **without** a physical RX · C21 assembler reused · C5 T5 on `radio.py` intact · Authority ≠ Safety allow)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.20`**  
**Parents:**
- [C21 ★ ACCEPT](implementation_contract_fase_c_crsf_byte_stream_b1.md) — `CrsfByteStreamAssembler` @ **`v0.5.19`**  
- [C20 ★ ACCEPT](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) — Authority `kill` bridge @ **`v0.5.18`**  
- [C19 ★ ACCEPT](implementation_contract_fase_c_crsf_link_stub_b1.md) — `parse_crsf_frame` @ **`v0.5.17`**  
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — `radio.py` T5: no `open_serial` / `decode_crsf` on that module @ **`v0.5.3`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, craft↔FS, Safety policy, deepen-C20-policy, or MCU UART driver in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · C++ `native/flight_control/` **untouched**

**Type:** **Implementation Contract** — host-side **serial-shaped byte source**: pull bytes from an already-open FD (tests: POSIX `pty`) or an opt-in device **path**, `feed` C21’s assembler, get `CrsfFrame`s.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.20`**; git tag **`v0.5.20`** only after Engineer ACCEPT.  
**Not** live ELRS air · not “RX connected” as a product claim · not `pyserial` · not 420000 baud configuration (ELRS-on-macOS ioctl) · not a MCU UART/HAL · not auto-scan of `/dev/cu.*` · not RC→mixer/ESC · not Safety allow via Authority · not making `RadioIntentAdapter` succeed · not craft↔FS · not board flash · not deepen C20 policy.

**Outputs (required):**
1. New ingress module under `src/jarvis/capabilities/` — preferred name **`crsf_serial.py`**. **Forbidden:** putting `open_serial` / decode / stream APIs on `radio.py` (C5 T5) or adding I/O into `crsf_stream.py` (C21 stays a pure buffer)  
2. Tests using POSIX `pty` (or equivalent loopback FD) + C19 fixtures — **no physical receiver required for PASS**  
3. `.jes/artifacts/implementation_report_fase_c_crsf_host_serial_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **host serial ingest ≠ live ELRS ≠ RX connected ≠ Safety allow**  
5. `pyproject.toml` → **`0.5.20`** (+ re-pin `0.5.19` version-checkpoint tests). **No new runtime dependency** (no `pyserial`)

**Checkpoint:** package **`0.5.20`** · Python suite ≥ **3465** + new tests · C5/C19/C20/C21 suites still green · Safety default unchanged · pytest PASS without a USB RX plugged in

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-host-serial`** — first host serial-shaped ingest into C21 |
| 2 | One front | Do **not** fold MCU UART, GPIO, flash, craft↔FS, Safety policy, mixer/ESC, C20 extra kinds/Intent, or custom-baud (420000 / `IOSSIOSPEED`) into this Buy |
| 3 | What this Buy demonstrates | Bytes can be **pulled from a host FD/path** and handed to the C21 assembler. **Human:** “ya no hace falta que un test nos pase el `bytes` a mano — podemos leerlos de un descriptor, aún sin afirmar que hay un receptor ELRS ni configurar 420000 baud.” |
| 4 | Direction of dependency | Ingress **imports** `crsf_stream` (and may call C20 helper). **`radio.py` must not** grow serial/CRSF symbols (C5 T5). **`crsf_stream.py` stays I/O-free** — C21 tests remain the contract |
| 5 | Test path (locked) | PASS uses a **POSIX `pty`** (or equivalent loopback): write fixture bytes on one side, `poll()` the other. **Forbidden:** requiring `/dev/cu.*` / USB serial hardware for pytest |
| 6 | FD vs path | **Required:** attach an already-open FD (`attach_fd`) — tests own the pty. **Optional:** `attach_path(path)` opens a node read-only/non-blocking. Path-open **must not** be the only way to PASS. `attach_fd` does **not** own/close the FD; `attach_path` **does** own and `close()` it |
| 7 | Pull, not a live thread | `poll()` (name flexible) does **one** non-blocking read + `assembler.feed`. No background thread, no “link up” flag, no auto-reconnect loop claiming a receiver is connected |
| 8 | Baud / termios | **Deferred.** This Buy does **not** set 420000 (the usual ELRS CRSF rate) and does **not** add `pyserial`. Opening a path is “give me bytes from this node,” not “I configured an ELRS RX.” Document that a real ELRS UART on macOS typically needs a custom-baud ioctl — **later IC** |
| 9 | No auto-discovery | Do **not** glob `/dev/cu.*` / `/dev/ttyUSB*` / enumerate USB. Caller passes FD or path |
| 10 | Optional C20 helper | Thin helper: `poll` → for each new `0x16` frame, `decode_rc_channels_packed` + C20 `ingest_rc_channels` (or reuse C21 `ingest_stream_bytes` if that fits without double-feeding). Policy defaults unchanged. **Forbidden:** `submit_command`, `SafetyGate.evaluate`, Intent from sticks |
| 11 | POSIX | Host ingest is **POSIX** (`pty`, `os.read`). Non-POSIX: skip the pty tests with a clear reason, or fail-closed if the project has no such runner — do **not** add Windows serial stacks in this Buy |
| 12 | `RadioIntentAdapter` | Remains **`NotImplementedError`** / `"not_implemented"` |
| 13 | Safety | `default_safety_gate()` stays RejectAll. Do not change `ArmedAllowlistSafetyGate` |
| 14 | No craft / no native | Continuity, Board, `library/`, `native/` untouched — no UART/CRSF driver under `native/` |
| 15 | Version | Bump **`0.5.19` → `0.5.20`**; tag **`v0.5.20`** on ACCEPT only |
| 16 | Forbidden claims | “Live ELRS” · “RX connected” · “UART driver” · “baud 420000 works” · “sticks drive craft” · “Authority allows HOLD/LAND” · “radio capability available” in default registry |

**Product sentence:**

```text
Leer bytes desde un FD/path de host y alimentarlos al ensamblador C21
(tests con pty, sin RX físico) — ingest serial de host, no ELRS al aire,
sin baud 420000, sin que Authority abra Safety.
```

**Defaults locked by Cursor (Engineer pick 2026-09-22: serial):**
- New **`crsf_serial.py`**  
- `pty` tests; no `pyserial`; no 420000 baud  
- `attach_fd` required; `attach_path` optional; pull `poll()`  
- Optional `0x16` → C20 helper; C21 assembler unchanged  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  crsf_stream.py            # C21 — UNCHANGED I/O-free behavior
  crsf_dual_role.py         # C20 — UNCHANGED policy
  crsf_stub.py              # C19 — UNCHANGED parse
  crsf_serial.py            # NEW — host FD/path ingest
  radio.py                  # UNCHANGED (T5)

tests/
  test_fase_c_crsf_host_serial_b1.py
  fixtures/crsf/            # reuse C19 .bin
```

Report must name public symbols. Do **not** create `native/**/uart*` / `native/**/crsf*`. Do **not** add `pyserial` to `pyproject.toml`.

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them.

### 2.1 Ingress

```text
CrsfHostSerialError          # typed attach/read failures (not CrsfParseError)

CrsfHostSerialIngress
  assembler: CrsfByteStreamAssembler   # injected or default-constructed

  attach_fd(fd: int) -> None
    # non-blocking reads from fd; does not close fd on close()

  attach_path(path: str) -> None
    # open path O_RDONLY|O_NOCTTY|O_NONBLOCK (or POSIX equivalent)
    # owns the FD; close() releases it
    # does NOT configure baud

  poll(*, max_bytes: int = 64) -> list[CrsfFrame]
    # one non-blocking os.read; empty/EAGAIN → []
    # feed bytes to assembler; return newly completed frames
    # never raises CrsfParseError (C21 already swallows those)

  close() -> None
    # close owned path-FD only; detach
```

Calling `poll` before attach → typed error or documented `[]` (pick one, report).

### 2.2 Optional C20 helper

```text
poll_and_ingest(
    ingress: CrsfHostSerialIngress,
    *,
    policy: CrsfDualRolePolicy,
    ingress_radio: SimulatedRadioIngress | None = None,
) -> list[RadioDualRoleResult]
  # poll → 0x16 frames → C20 ingest_rc_channels; omit None / non-0x16
```

If implementing this via leftover bytes + `ingest_stream_bytes`, **must not** `feed` the same bytes twice into the same assembler.

### 2.3 Explicit non-goals

No `pyserial`, no baud API, no USB VID/PID scan, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no background reader thread, no “connected” boolean that means ELRS.

---

## 3. Integration rules

| Existing | C22 rule |
|---|---|
| C21 `CrsfByteStreamAssembler` | **Called**; not rewritten; still no I/O inside `crsf_stream.py` |
| C20 policy / bridge | Unchanged; optional helper is a caller |
| C19 parse | Unchanged (via C21) |
| C5 `radio.py` | No `decode_*` / `open_serial` / `write_pwm` / stream types |
| C2 `RadioIntentAdapter` | Still refuses |
| C4 autonomy | **No** serial → `submit_command` |
| C17 Safety | Untouched |
| Registry | Default stays empty |

---

## 4. Tests (minimum)

Reuse `tests/fixtures/crsf/*.bin`. POSIX `pty` (`os.openpty` / `pty.openpty`). Skip with an explicit reason only if `openpty` is missing.

| ID | Check |
|---|---|
| T1 | PTY: write `rc_channels_valid.bin` to the slave in one shot; `attach_fd` master; `poll` until 1 frame type `0x16` (loop a small bounded number of `poll`s if needed) |
| T2 | PTY: write the same fixture **in small chunks** across several writes; polls reassemble to 1 frame (C21 wait behavior via the FD) |
| T3 | `poll` with no new bytes → `[]`, no raise |
| T4 | Optional `attach_path`: open the pty **slave path** (or a documented equivalent loopback path), write from the other side, get ≥1 valid frame — still no USB hardware |
| T5 | `close()` after `attach_path` releases the owned FD (further `poll` does not succeed as if still attached) |
| T6 | Optional helper: PTY bytes with aux ch 4 ≥ 1500 → Authority `kill`; all-992 fixture → empty result list |
| T7 | C5 T5: `radio.py` has no `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T8 | `RadioIntentAdapter` still `not_implemented` |
| T9 | No `submit_command` / autonomy import for execution in the new module |
| T10 | `default_safety_gate()` still RejectAll |
| T11 | `crsf_stream.py` still has no I/O imports / device `open(` in **real code** |
| T12 | No `pyserial` in `pyproject.toml` dependencies |
| T13 | No glob/scan of `/dev/cu` / `/dev/ttyUSB` in the module real code |
| T14 | `pyproject` **`0.5.20`**; re-pin `0.5.19` checkpoints |
| T15 | Full suite green **without** a physical RX |
| T16 | Report: host serial ingest ≠ live ELRS ≠ RX connected ≠ Safety allow; baud 420000 deferred |
| T17 | No CRSF/ELRS/UART **driver** tokens under `native/` (honesty prose that *denies* UART I/O may remain, same C21 lesson — do not bare-substring `"uart"` across `native/` READMEs) |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Pytest that needs a real ELRS RX / USB serial | B1 must PASS on a Mac with no radio |
| `pyserial` dependency | Avoid a driver-shaped stack; stdlib FD is enough |
| Setting 420000 baud / claiming ELRS UART timing | Custom-baud ioctl is a later, platform-specific Buy |
| Auto-scan `/dev/cu.*` | Looks like “we found your RX” |
| Background thread + “connected=true” | Fake link product |
| Decode/serial APIs on `radio.py` | C5 T5 |
| I/O inside `crsf_stream.py` | C21 lock |
| MCU UART under `native/` | Wrong axis |
| Authority → Safety `allow` | C0/C17 |
| Auto `submit_command` | Fake autonomy |
| Marking radio `available` in registry | Premature |
| Flash / craft↔FS / deepen C20 policy | Process lock |

Honesty line (report + living docs):

```text
Host serial ingest ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow
```

---

## 6. Docs

- PRIORIDAD: C22 in flight / CLOSED as appropriate  
- PLATFORM §13: C22 host-serial block + honesty line + baud-420000 deferred  
- ARCHITECTURE: short note under capabilities (`crsf_serial.py`)  
- README “What v0.5.20 includes”  

---

## 7. Acceptance

**PASS when:** T1–T17 · pty ingest yields C19 frames via C21 · no hardware RX required · no `pyserial` · no 420000 claim · C5/C19/C20/C21 locks hold · Safety default unchanged · version `0.5.20` · docs honest.

**FAIL if:** pytest requires a dongle · `pyserial` added · baud-420000 claimed working · serial stuffed into `radio.py` · I/O added to `crsf_stream.py` · Safety allow via Authority · CRSF→autonomy executed · “RX connected” / live ELRS in living docs.

---

## 8. Handoff

```text
Engineer → ★ this IC (C22)
Claude   → implement ingest + pty tests + report + 0.5.20
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.20
Cursor   → next Buy when Engineer prioritizes (deepen policy · board flash · craft↔FS · baud-420000 — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C21 CLOSED @ v0.5.19. C22 B1-fase-c-crsf-host-serial READY —
host FD/path → C21 assembler (pty tests; no pyserial; baud 420000
deferred); not live ELRS; not RX connected; Authority ≠ Safety allow.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **host FD/path ingest** (pty tests; not a live ELRS product) OK?  
2. **No `pyserial`** and **baud 420000 deferred** OK?  
3. Module: **new `crsf_serial.py`** OK?  
4. Optional `attach_path` + optional C20 helper in this Buy OK? (Cursor default: **yes**, thin)  
5. Version **`0.5.20`** OK?  
6. Keep `RadioIntentAdapter` NotImplemented OK?  
