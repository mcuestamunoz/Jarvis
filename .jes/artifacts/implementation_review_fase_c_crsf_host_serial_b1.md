# Implementation Review — Fase C CRSF host serial ingest (`B1-fase-c-crsf-host-serial`)

**Date:** 2026-09-22  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_crsf_host_serial_b1.md) · [report](implementation_report_fase_c_crsf_host_serial_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.20`**

---

## Summary

C22 adds **`src/jarvis/capabilities/crsf_serial.py`**: `CrsfHostSerialIngress` + `CrsfHostSerialError` + `poll_and_ingest`. Pull-based: one non-blocking `os.read` per `poll`, then C21 `assembler.feed`. `attach_fd` does not own the FD; `attach_path` does (`O_RDONLY|O_NOCTTY|O_NONBLOCK`, **no baud**). Tests are POSIX `pty` loopback — no physical RX. `pyserial` absent. `radio.py` / `crsf_stub.py` / `crsf_dual_role.py` / `crsf_stream.py` / `intent.py` / `safety.py` diffs **empty**. Independent suite **3485 passed, 1 skipped** (+20). Tip tagged **`v0.5.20`**.

**N1 (docs, closed in this review):** README `## Next` still spoke as if C21 were tip and host serial still a pick. Required C22 honesty line was already in the v0.5.20 / PLATFORM §13 blocks. Footer synced to review PASS · awaiting ACCEPT.

**N2 (tests, left open):** module-level `pytestmark = skipif(not _HAS_PTY)` also skips non-pty honesty tests (T7–T14, T17) on a non-POSIX runner. Fine on this Darwin project; IC asked to skip *pty* tests only.

**N3 (disclosed, not a fail):** POSIX pty canonical mode held binary CRSF until newline. Fix is `tty.setraw` in the **test fixture only** — shipped module has zero termios. Correct place.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Buy · one front · FD/path → C21 frames | **Pass** |
| 4 | Ingress imports stream; `radio.py` T5; `crsf_stream.py` I/O-free | **Pass** |
| 5–7 | PTY tests · attach_fd vs path ownership · pull `poll`, no thread | **Pass** |
| 8–9 | No 420000 / no `pyserial` · no `/dev` scan | **Pass** |
| 10–14 | Optional C20 helper · POSIX · adapter refuse · Safety · no craft/native | **Pass** |
| 15–16 | `0.5.20` · no fake ELRS/RX/baud claims · **no premature tag** | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `attach_fd` / `attach_path` / `poll` / `close` / `poll_and_ingest` | Present |
| `poll` before attach | `[]` (documented choice) |
| `parse` / assembler I/O | C21 called; `crsf_stream.py` still no `os.read`/`open(` |
| `pyserial` in `pyproject.toml` | **Absent** |
| Baud / `termios` / `IOSSIOSPEED` in assembler module real code | **Absent** (docstring only) |
| Threading / `connected` flag | **Absent** (`.attached` = FD present, not ELRS) |
| Locked module diffs | **Empty** |
| Related pytest (C22+C21+C19+C20+C5+C17) | **104 passed** (pty tests need a real tty; sandbox `out of pty devices` is an environment note, not a product fail) |
| Full suite (T15) | **3485 passed, 1 skipped** |
| Tag `v0.5.20` | Engineer ACCEPT (this closeout) |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.20`**.

Living docs synced. Next fronts still one-at-a-time — Engineer picks: deepen C20 policy · board flash · craft↔FS · baud 420000.
