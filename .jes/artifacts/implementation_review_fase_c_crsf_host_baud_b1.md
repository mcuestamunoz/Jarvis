# Implementation Review — Fase C CRSF host baud 420000 (`B1-fase-c-crsf-host-baud`)

**Date:** 2026-09-22  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_crsf_host_baud_b1.md) · [report](implementation_report_fase_c_crsf_host_baud_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.21`**

---

## Summary

C23 extends C22’s own `src/jarvis/capabilities/crsf_serial.py` (no sixth module) with opt-in Darwin host baud: `configure_host_baud(fd, baud=420000)` / `CrsfHostSerialIngress.configure_baud(...)`. On Darwin: raw 8N1 termios, then `IOSSIOSPEED`. Request number is derived from `_IOW('T', 2, speed_t)` — independent check equals **`0x80085402`**. Packed speed `struct.pack("@L", 420000)` is `420000`. Non-Darwin fail-closed. `attach_fd` / `attach_path` never auto-configure baud.

Tests: `tests/test_fase_c_crsf_host_baud_b1.py`. Darwin success path is mocked `fcntl.ioctl`. Unmocked ioctl on a pty is asserted to raise `CrsfHostSerialError` (ENOTTY-class). No hardware required. C22 suite re-run unmodified except version re-pin. Frozen modules (`radio.py` / `crsf_stub.py` / `crsf_dual_role.py` / `crsf_stream.py` / `intent.py` / `safety.py`) have **empty** git diffs. `pyserial` absent. `__all__` does not export baud helpers. Package file is **`0.5.21`**. Git tags: tip remains **`v0.5.20`**. No `v0.5.21` tag.

Honesty line is in PLATFORM §13 / ARCHITECTURE / README:

```text
Host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow
```

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–4 | Buy · one front · extend `crsf_serial.py` · ingest unchanged | **Pass** |
| 5 | Mock ioctl happy path; unmocked pty fail-closed, not skip-suite | **Pass** |
| 6 | Opt-in baud; attach never ioctl | **Pass** (T5, T20; `attach_path` source has no ioctl) |
| 7 | Derive `IOSSIOSPEED`; default 420000; positive int | **Pass** (`0x80085402`) |
| 8–9 | Raw 8N1 + Apple-typical order (termios then ioctl) | **Pass** — see N1 |
| 10 | Non-Darwin `CrsfHostSerialError` Darwin-only | **Pass** (T7 skip on Darwin + T7b patched linux) |
| 11–12 | No `/dev` scan · attach_path flags unchanged (`O_RDONLY\|O_NOCTTY\|O_NONBLOCK`) | **Pass** |
| 13–16 | No thread / no ELRS “connected” · C20/C21 unchanged · adapter refuse · Safety RejectAll | **Pass** |
| 17–19 | No craft/native UART driver · `0.5.21` file, tag only on ACCEPT · no fake claims | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `_darwin_iossiospeed_request()` | `0x80000000 \| (8<<16) \| (ord('T')<<8) \| 2` = **`0x80085402`** |
| `fcntl.ioctl` mock (T2) | request = derived; unpack `@L` = 420000 |
| Unmocked pty (T3) | raises `CrsfHostSerialError` (not skip) |
| T8 flags on pty | `~ICANON`, `~ECHO`, `CS8`, `CLOCAL`, `CREAD`, `VMIN=VTIME=0` |
| `attach_fd` / `attach_path` auto-baud | **Absent** |
| `pyserial` in `pyproject.toml` | **Absent** |
| Baud helpers in `capabilities/__init__.py` `__all__` | **Absent** (C22 pattern kept) |
| Frozen module diffs | **Empty** |
| Related pytest (C23+C22+C21+C19+C20+C5+C17+C2) | **134 passed, 1 skipped** (T7 by-design on Darwin) |
| Full suite (T17) | **3504 passed, 2 skipped** |
| Tag `v0.5.21` | Engineer ACCEPT (this closeout) |

---

## Notes (not a recut)

| ID | Note |
|---|---|
| N1 | IC §0.8 says raw 8N1 *after* a successful ioctl; §0.9 locks Apple-typical **termios then ioctl** and allows leaving termios mutation if ioctl fails. Shipped order matches **§0.9** and is reported. Not a fail. |
| N2 | Module-level `pytestmark = skipif(not _HAS_PTY)` also skips honesty tests on a non-POSIX runner (same C22 note). Fine on this Darwin project. |
| N3 | T5 spies `attach_fd`+`poll`, not `attach_path`. Source of `attach_path` still has no ioctl/termios. Acceptable. |
| N4 | IC mentioned `ctypes.c_ulong`; shipped `struct.pack("@L", baud)` into `fcntl.ioctl`. Equivalent for `_IOW` (kernel reads speed; no write-back required). |
| N5 | README `## Next` + banner still spoke as if C22 were tip and C23 still “awaiting Cursor review”. Closed in this review closeout. |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.21`**.

Living docs synced. Next: **C24** control-loop tick READY — then parked C25–C29 (RC setpoint · Esc HAL · CRSF failsafe · MCU UART stub · silicon map).
