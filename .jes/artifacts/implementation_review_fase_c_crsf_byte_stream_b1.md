# Implementation Review — Fase C CRSF byte-stream assembler (`B1-fase-c-crsf-byte-stream`)

**Date:** 2026-09-22  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_crsf_byte_stream_b1.md) · [report](implementation_report_fase_c_crsf_byte_stream_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.19`**

---

## Summary

C21 adds **`src/jarvis/capabilities/crsf_stream.py`**: `CrsfByteStreamAssembler` + optional `ingest_stream_bytes`. Chunks of `bytes` → zero or more C19 `CrsfFrame`s. Candidate windows are sliced at `frame_len + 2` and passed **unmodified** to `parse_crsf_frame` (no second CRC8/`0xD5` in the assembler). Incomplete candidates **wait**; invalid complete windows **drop 1 byte** and resync — `CrsfParseError` is not leaked. Leftover cap default **256**; plausible `frame_len` **[2, 64]**. Optional helper reuses C20 `ingest_rc_channels` for `0x16` only. `radio.py` / `crsf_stub.py` / `crsf_dual_role.py` / `intent.py` / `safety.py` diffs **empty**. Independent suite **3465 passed, 1 skipped** (+21). Tip tagged **`v0.5.19`**.

**N1 (docs, closed in this review):** README `## Next` and a trailing PLATFORM honesty line still spoke as if C21 were unpicked / UART stream parked. Required C21 honesty line was already present in the v0.5.19 / §13 blocks. Footer/trailers synced to “review PASS · awaiting ACCEPT”; UART stream removed from parked lists.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Buy · one front · UART-shaped chunks → C19 frames | **Pass** |
| 4–5 | Deps one-way · `parse_crsf_frame` is CRC truth · `radio.py` T5 | **Pass** (`git diff` empty on locked modules; T17 no `0xD5`) |
| 6–8 | Wait-on-incomplete · drop-1 on invalid complete · `frame_len` `[2,64]` · max leftover 256 | **Pass** |
| 9 | Optional `0x16` → C20 helper; policy not deepened | **Pass** |
| 10–13 | No I/O · adapter refuse · Safety untouched · no craft/native CRSF | **Pass** |
| 14–15 | `0.5.19` · no fake UART/ELRS claims · **no premature tag** | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `CrsfByteStreamAssembler` / `feed` / `leftover` / `reset` / `dropped_byte_count` | Present |
| `ingest_stream_bytes` → C20 `ingest_rc_channels` | Present; non-`0x16` skipped |
| `parse_crsf_frame` called on exact slices | Present |
| Second CRC in assembler | **Absent** (`0xD5` only in tests’ synthetic T8 packer) |
| `radio` / `crsf_stub` / `crsf_dual_role` / `intent` / `safety` diff | **Empty** |
| C5 T5 on `radio.py` | Absent decode/serial symbols |
| I/O / `Serial` / `UartPort` in assembler real code | Absent (docstring mentions `/dev/tty*` only as **not** this module) |
| CRSF/ELRS under `native/` · craft wiring to assembler | Absent |
| Related pytest (C21+C19+C20+C5+C17) | **84 passed** |
| Full suite (T15) | **3465 passed, 1 skipped** |
| Tag `v0.5.19` | Engineer ACCEPT (this closeout) |

**T7 leftover (not a fail):** feeding `rc_channels_bad_crc.bin` yields 0 frames and no raise. After drop-1 hunt the leftover can be non-empty (report: 22 bytes waiting). IC required zero frames + no leak, not empty leftover.

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.19`**.

Living docs synced. Next fronts still one-at-a-time — Engineer picks: host serial ingest (if continuing link) · deepen C20 policy · board flash · craft↔FS.
