# Implementation Contract — Fase C CRSF host baud 420000 (`B1-fase-c-crsf-host-baud`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (host baud 420000 ≠ live ELRS ≠ RX connected · pytest green **without** a physical RX or USB-serial adapter · C22 ingest reused · ioctl mocked on Darwin · no `pyserial` · C5 T5 on `radio.py` intact · Authority ≠ Safety allow)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.21`**  
**Parents:**
- [C22 ★ ACCEPT](implementation_contract_fase_c_crsf_host_serial_b1.md) — `CrsfHostSerialIngress` @ **`v0.5.20`** (IC §0 decision 8 deferred this Buy)  
- [C21 ★ ACCEPT](implementation_contract_fase_c_crsf_byte_stream_b1.md) — `CrsfByteStreamAssembler` @ **`v0.5.19`**  
- [C20 ★ ACCEPT](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) — Authority `kill` bridge @ **`v0.5.18`**  
- [C19 ★ ACCEPT](implementation_contract_fase_c_crsf_link_stub_b1.md) — `parse_crsf_frame` @ **`v0.5.17`**  
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — `radio.py` T5: no `open_serial` / `decode_crsf` on that module @ **`v0.5.3`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, craft↔FS, Safety policy, deepen-C20-policy, MCU UART driver, or live ELRS product in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · C++ `native/flight_control/` **untouched**

**Type:** **Implementation Contract** — host-side **custom baud** on an already-attached serial FD: issue Darwin `IOSSIOSPEED` for **420000** (the usual ELRS CRSF UART rate) plus raw 8N1 so binary CRSF is not line-buffered. Still not a live link.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.21`**; git tag **`v0.5.21`** only after Engineer ACCEPT.  
**Not** live ELRS air · not “RX connected” as a product claim · not “baud 420000 works against a real RX” · not `pyserial` · not auto-scan of `/dev/cu.*` · not Linux `TCSETS2` (fail-closed this Buy) · not a MCU UART/HAL · not changing C22 `attach_path` default (still no baud unless asked) · not RC→mixer/ESC · not Safety allow via Authority · not making `RadioIntentAdapter` succeed · not craft↔FS · not board flash · not deepen C20 policy.

**Outputs (required):**
1. Baud/line-discipline API on the **existing** C22 module `src/jarvis/capabilities/crsf_serial.py`. **Forbidden:** a sixth capabilities module; putting baud/serial APIs on `radio.py` (C5 T5); adding I/O or termios into `crsf_stream.py` (C21 stays a pure buffer); adding `pyserial`
2. Tests that **PASS with no USB serial adapter / no ELRS RX** — Darwin happy-path via **`fcntl.ioctl` mock**; unmocked `pty` is **not** a UART and must not be the only way to PASS
3. `.jes/artifacts/implementation_report_fase_c_crsf_host_baud_b1.md`
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow**
5. `pyproject.toml` → **`0.5.21`** (+ re-pin `0.5.20` version-checkpoint tests, including C22’s). **No new runtime dependency**

**Checkpoint:** package **`0.5.21`** · Python suite ≥ **3485** + new tests · C5/C19/C20/C21/C22 suites still green · Safety default unchanged · pytest PASS without a USB RX plugged in

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-host-baud`** — first host custom-baud (420000) configuration for C22’s FD |
| 2 | One front | Do **not** fold MCU UART, GPIO, flash, craft↔FS, Safety policy, mixer/ESC, C20 extra kinds/Intent, `/dev` scan, `pyserial`, Linux `TCSETS2`, or a live-ELRS product into this Buy |
| 3 | What this Buy demonstrates | The host can **ask Darwin to clock an already-open serial FD at 420000** and put that FD in **raw 8N1** (binary CRSF, not canonical line buffering). **Human:** “ya no es solo ‘abre el nodo y lee bytes’ — podemos pedir el ritmo ELRS-típico al SO, aún sin afirmar que hay un receptor ni que el aire funciona.” |
| 4 | Module | **Extend `crsf_serial.py`.** Baud is a property of the host serial FD, not a new capability rung. C22 ingest (`attach_fd` / `attach_path` / `poll` / `poll_and_ingest`) stays the ingest contract — **default path-open still does not set baud** |
| 5 | Test path (locked) | PASS does **not** require `/dev/cu.*` / USB-serial / ELRS hardware. Darwin success path is proven by **mocking `fcntl.ioctl`** (and asserting request + speed). A POSIX `pty` is **not** a UART: unmocked `IOSSIOSPEED` on a pty **may raise** `CrsfHostSerialError` (ENOTTY / equivalent) — that is honesty, not a fail. **Forbidden:** skipping the whole suite when no dongle is plugged in |
| 6 | Opt-in, not default | `attach_path` / `attach_fd` **must not** auto-call baud config. Caller invokes `configure_host_baud` / `ingress.configure_baud` explicitly. C22 tests remain valid without edits to their attach/poll behavior (re-pin version only) |
| 7 | Darwin ioctl | On `sys.platform == "darwin"`: issue **`IOSSIOSPEED`** (`_IOW('T', 2, speed_t)` from Darwin `ioss.h` / `ioccom.h`). Derive the request from Darwin `_IOC` macros and `sizeof(speed_t)` (`unsigned long` → `ctypes.c_ulong`). **Do not** copy `pyserial`’s packed constant as source of truth. Pack the speed as a mutable `ctypes.c_ulong` (or equivalent) and pass it to `fcntl.ioctl`. Default **`baud=420000`**. Any other **positive `int`** is allowed (no ELRS rate table in this Buy) |
| 8 | Raw 8N1 (same call) | After a **successful** ioctl, apply POSIX termios **raw 8N1** on the same FD: 8 data bits, no parity, 1 stop, non-canonical (`~ICANON`, `~ECHO`), `CLOCAL`, `CREAD`, `VMIN=0`, `VTIME=0`. **Why:** C22 N3 — canonical mode holds binary CRSF until newline. Baud without raw is a paper win. If ioctl **fails**, raise `CrsfHostSerialError` and **do not claim success** (termios-before-ioctl mutation on a failing pty is acceptable to leave; report the order) |
| 9 | Call order (locked) | Apple-typical: (1) `tcgetattr` + raw 8N1 `tcsetattr` (2) `IOSSIOSPEED` with the requested baud. If ioctl fails → typed error. Report the actual order shipped |
| 10 | Non-Darwin | **Fail-closed:** `configure_host_baud` raises `CrsfHostSerialError` with a clear “Darwin-only in this Buy” reason. Do **not** add Linux `TCSETS2` / `BOTHER` or a Windows stack here. Tests on non-Darwin: assert the typed error (or skip Darwin-ioctl packing tests with an explicit reason) |
| 11 | No auto-discovery | Still no glob of `/dev/cu.*` / `/dev/ttyUSB*`. Caller already has an FD from C22 |
| 12 | Open flags | Do **not** change C22 `attach_path` flags (`O_RDONLY\|O_NOCTTY\|O_NONBLOCK`). Some USB-serial chips prefer `O_RDWR`; that is **caller `attach_fd`**, not this Buy rewriting path-open |
| 13 | Pull / threads | Unchanged: no background thread, no “link up” / “connected” flag that means ELRS. `.attached` still means “FD present” |
| 14 | C20 / C21 | Unchanged. `poll` / `poll_and_ingest` behavior unchanged except that a caller **may** have configured baud on the FD first |
| 15 | `RadioIntentAdapter` | Remains **`NotImplementedError`** / `"not_implemented"` |
| 16 | Safety | `default_safety_gate()` stays RejectAll. Do not change `ArmedAllowlistSafetyGate` |
| 17 | No craft / no native | Continuity, Board, `library/`, `native/` untouched — no UART/CRSF driver under `native/` |
| 18 | Version | Bump **`0.5.20` → `0.5.21`**; tag **`v0.5.21`** on ACCEPT only |
| 19 | Forbidden claims | “Live ELRS” · “RX connected” · “UART driver” · “baud 420000 works” (as in: talked to a real RX) · “sticks drive craft” · “Authority allows HOLD/LAND” · “radio capability available” in default registry |

**Product sentence:**

```text
Pedir al host Darwin 420000 baud (IOSSIOSPEED) y raw 8N1 en un FD
ya abierto por C22 — ritmo UART ELRS-típico, no ELRS al aire,
sin dongle obligatorio en pytest, sin que Authority abra Safety.
```

**Defaults locked by Cursor (Engineer pick 2026-09-22: baud):**
- Extend **`crsf_serial.py`** (no sixth module)  
- Opt-in `configure_host_baud(fd, baud=420000)` + `ingress.configure_baud(...)`  
- Darwin `IOSSIOSPEED` + raw 8N1; non-Darwin fail-closed  
- Tests: mock ioctl; no hardware; no `pyserial`  
- `attach_path` default still does **not** set baud  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  crsf_serial.py            # C22 ingest + NEW baud/raw helpers
  crsf_stream.py            # C21 — UNCHANGED I/O-free behavior
  crsf_dual_role.py         # C20 — UNCHANGED policy
  crsf_stub.py              # C19 — UNCHANGED parse
  radio.py                  # UNCHANGED (T5)

tests/
  test_fase_c_crsf_host_baud_b1.py
  test_fase_c_crsf_host_serial_b1.py   # still green (version re-pin only)
```

Report must name public symbols. Do **not** create `native/**/uart*` / `native/**/crsf*`. Do **not** add `pyserial` to `pyproject.toml`.

`capabilities/__init__.py` docstring may mention C23; **do not** dump baud helpers into `__all__` unless already exporting C22 (today it does not — keep that pattern).

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them. Prefer the names below.

### 2.1 Free function + ingress method

```text
CRSF_HOST_BAUD_ELRS = 420000    # documented default; ELRS-typical CRSF UART rate

configure_host_baud(fd: int, baud: int = 420000) -> None
  # Darwin: raw 8N1 termios + IOSSIOSPEED(baud)
  # non-Darwin: raise CrsfHostSerialError (Darwin-only this Buy)
  # baud must be a positive int; otherwise typed error
  # does not open, close, attach, or poll
  # does not mean a receiver is present

CrsfHostSerialIngress.configure_baud(self, baud: int = 420000) -> None
  # requires an attached FD; delegates to configure_host_baud(self._fd, baud)
  # if not attached → CrsfHostSerialError (not silent [])
```

Reuse `CrsfHostSerialError` for attach/ioctl/termios failures. Do **not** raise bare `OSError` across the public boundary (may chain `from exc`).

### 2.2 C22 behavior that must stay

```text
attach_fd / attach_path / poll / close / poll_and_ingest
  # attach_path still does NOT configure baud
  # poll still one non-blocking os.read + assembler.feed
```

### 2.3 Explicit non-goals

No `pyserial`, no `/dev` scan, no Linux `TCSETS2`, no Windows serial, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no background reader thread, no “connected” boolean that means ELRS, no auto-baud on `attach_path`, no claim that ioctl success ⇒ RX present.

---

## 3. Integration rules

| Existing | C23 rule |
|---|---|
| C22 `CrsfHostSerialIngress` | **Extended**; default ingest unchanged |
| C21 `CrsfByteStreamAssembler` | Unchanged; still no I/O / termios inside `crsf_stream.py` |
| C20 policy / bridge | Unchanged |
| C19 parse | Unchanged |
| C5 `radio.py` | No `decode_*` / `open_serial` / `write_pwm` / baud / ioctl |
| C2 `RadioIntentAdapter` | Still refuses |
| C4 autonomy | **No** baud/serial → `submit_command` |
| C17 Safety | Untouched |
| Registry | Default stays empty |

---

## 4. Tests (minimum)

New file `tests/test_fase_c_crsf_host_baud_b1.py`. **No physical receiver required for PASS.**

| ID | Check |
|---|---|
| T1 | Constant / default **420000** is the documented ELRS-typical rate used when `baud` is omitted |
| T2 | Darwin + **mocked** `fcntl.ioctl`: `configure_host_baud(fd, 420000)` returns; mock was called; request equals derived `IOSSIOSPEED`; packed speed is **420000**. Use a pty (or other open FD) only as the `fd` argument — the mock is what makes it succeed |
| T3 | Darwin **unmocked** `configure_host_baud` on a **pty** raises `CrsfHostSerialError` (pty is not a UART). Do not treat this as skip-the-suite |
| T4 | `ingress.configure_baud()` before attach → `CrsfHostSerialError` |
| T5 | `attach_path` / `attach_fd` **without** `configure_baud` issues **no** `ioctl` / `IOSSIOSPEED` (spy or equivalent). C22 default preserved |
| T6 | Non-positive `baud` → typed error; no ioctl |
| T7 | `sys.platform != "darwin"`: `configure_host_baud` raises Darwin-only `CrsfHostSerialError` (skip T2 packing assertions on that runner with an explicit reason) |
| T8 | Successful Darwin mock path also applies **raw 8N1** (assert `termios` flags on the pty: non-canonical, CS8, `VMIN=0` — pick a small documented subset; report which flags) |
| T9 | C5 T5: `radio.py` has no `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T10 | `RadioIntentAdapter` still `not_implemented` |
| T11 | No `submit_command` / autonomy import for execution in baud-related **real code** |
| T12 | `default_safety_gate()` still RejectAll |
| T13 | `crsf_stream.py` still has no I/O / `fcntl` / `termios` / device `open(` in **real code** |
| T14 | No `pyserial` in `pyproject.toml` dependencies |
| T15 | No glob/scan of `/dev/cu` / `/dev/ttyUSB` in `crsf_serial.py` real code |
| T16 | `pyproject` **`0.5.21`**; re-pin `0.5.20` checkpoints (including C22 T14) |
| T17 | Full suite green **without** a physical RX / USB-serial adapter |
| T18 | Report: host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow; ioctl mock is the hardware-free proof |
| T19 | No CRSF/ELRS/UART **driver** tokens under `native/` (honesty prose that *denies* UART I/O may remain — do not bare-substring `"uart"` across `native/` READMEs) |
| T20 | C22 suite still green (pty ingest). Do not “fix” C22 by auto-baud on attach |

Honesty tests: strip comments/docstrings before scanning real code (same C22 lesson).

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Pytest that needs a real ELRS RX / USB serial | B1 must PASS on a Mac with no radio |
| `pyserial` dependency | Stdlib `fcntl` + `termios` is the point of this Buy |
| Claiming “baud 420000 works” as live RX | Ioctl issued ≠ receiver present ≠ RF |
| Treating pty success as the UART proof | Pty is not a 420000 serial device |
| Auto-scan `/dev/cu.*` | Looks like “we found your RX” |
| Auto-baud on `attach_path` | Breaks C22 “open = give me bytes” |
| Background thread + “connected=true” | Fake link product |
| Decode/serial/baud APIs on `radio.py` | C5 T5 |
| I/O / termios inside `crsf_stream.py` | C21 lock |
| Linux `TCSETS2` / Windows serial | Wrong platform for this Darwin Buy |
| MCU UART under `native/` | Wrong axis |
| Authority → Safety `allow` | C0/C17 |
| Auto `submit_command` | Fake autonomy |
| Marking radio `available` in registry | Premature |
| Flash / craft↔FS / deepen C20 policy | Process lock |

Honesty line (report + living docs):

```text
Host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow
```

**Exists:** Darwin can be asked to set 420000 + raw 8N1 on an attached FD; proven without hardware via ioctl mock.  
**Impossible:** a live ExpressLRS link; a receiver “connected”; sticks driving craft; Authority opening Safety.

---

## 6. Docs

- PRIORIDAD: C23 in flight / CLOSED as appropriate  
- PLATFORM §13: C23 host-baud block + honesty line (update the C22 “baud deferred” next-front sentence)  
- ARCHITECTURE: short note under capabilities (`crsf_serial.py` now opt-in baud)  
- README “What v0.5.21 includes”  
- `crsf_serial.py` module docstring: replace “420000 deferred” with this Buy’s claim + honesty line  
- `capabilities/__init__.py` C22 paragraph: baud is no longer “deferred”; keep ≠ live ELRS  

---

## 7. Acceptance

**PASS when:** T1–T20 · Darwin ioctl mock proves 420000 `IOSSIOSPEED` · unmocked pty is fail-closed not skipped-suite · no hardware RX required · no `pyserial` · no live-ELRS/RX-connected claim · C5/C19/C20/C21/C22 locks hold · Safety default unchanged · version `0.5.21` · docs honest.

**FAIL if:** pytest requires a dongle · `pyserial` added · “baud 420000 works” as RX claim · auto-baud on `attach_path` · serial/baud stuffed into `radio.py` · termios/I/O added to `crsf_stream.py` · Safety allow via Authority · CRSF→autonomy executed · “RX connected” / live ELRS in living docs.

---

## 8. Handoff

```text
Engineer → ★ this IC (C23)
Claude   → implement baud/raw on crsf_serial.py + mock-ioctl tests + report + 0.5.21
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.21
Cursor   → next Buy when Engineer prioritizes (deepen policy · board flash · craft↔FS · Linux baud — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C22 CLOSED @ v0.5.20. C23 B1-fase-c-crsf-host-baud READY —
Darwin IOSSIOSPEED 420000 + raw 8N1 on C22 FD (ioctl mock tests;
no pyserial; no dongle); not live ELRS; not RX connected;
Authority ≠ Safety allow.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **host Darwin 420000 baud** (ioctl mock tests; not a live ELRS product) OK?  
2. **No `pyserial`**, **no `/dev` scan**, **non-Darwin fail-closed** OK?  
3. Module: **extend `crsf_serial.py`** (no sixth module) OK?  
4. **Opt-in** `configure_baud` (attach_path default stays no-baud) OK?  
5. **Raw 8N1 in the same call** as ioctl (C22 N3: canonical kills binary CRSF) OK?  
6. Version **`0.5.21`** OK?  
7. Keep `RadioIntentAdapter` NotImplemented OK?  
