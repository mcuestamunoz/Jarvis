# Implementation Contract — Fase C CRSF byte-stream assembler (`B1-fase-c-crsf-byte-stream`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (stream assembler ≠ UART open ≠ live ELRS · C19 parse reused not rewritten · Authority ≠ Safety allow · C5 T5 on `radio.py` intact)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.19`**  
**Parents:**
- [C19 ★ ACCEPT](implementation_contract_fase_c_crsf_link_stub_b1.md) — `parse_crsf_frame` exact-buffer parse @ **`v0.5.17`**  
- [C20 ★ ACCEPT](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) — `crsf_dual_role.py` Authority `kill` bridge @ **`v0.5.18`**  
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — `RadioStubFrame` / `SimulatedRadioIngress` @ **`v0.5.3`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no serial product, flash, craft↔FS, Safety policy, or deepen-bridge-policy in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · C++ `native/flight_control/` **untouched**

**Type:** **Implementation Contract** — host-side **UART-shaped byte-stream assembler**: chunks of `bytes` in → zero or more complete `CrsfFrame` out, leftover held. Still fixture/host-only.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.19`**; git tag **`v0.5.19`** only after Engineer ACCEPT.  
**Not** USB/serial RX product · not `pyserial` / `/dev/tty*` / `/dev/cu.*` · not live ELRS air · not a UART peripheral driver · not RC→mixer/ESC · not Safety allow via Authority · not making `RadioIntentAdapter` succeed · not craft↔FS · not board flash · not deepen C20 policy (still one aux → `kill`).

**Outputs (required):**
1. New assembler module under `src/jarvis/capabilities/` — preferred name **`crsf_stream.py`**. **Forbidden:** putting stream/UART/serial APIs on `radio.py` (C5 T5 stays green) or rewriting CRC/parse inside the assembler (C19 `parse_crsf_frame` is the CRC source of truth)  
2. Tests feeding C19 fixtures in chunks (byte-at-a-time, mid-frame split, concatenated, garbage prefix, bad CRC)  
3. `.jes/artifacts/implementation_report_fase_c_crsf_byte_stream_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **byte-stream assembler ≠ UART open ≠ live ELRS ≠ Safety allow**  
5. `pyproject.toml` → **`0.5.19`** (+ re-pin `0.5.18` version-checkpoint tests)

**Checkpoint:** package **`0.5.19`** · Python suite ≥ **3444** + new tests · C5/C19/C20 suites still green · no I/O · Safety default unchanged

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-byte-stream`** — first UART-shaped CRSF byte-stream assembler |
| 2 | One front | Do **not** fold serial/USB open, `pyserial`, MCU UART, GPIO, flash, craft↔FS, Safety policy edits, mixer/ESC, or extra C20 kinds/channels/Intent into this Buy |
| 3 | What this Buy demonstrates | Bytes that arrive **in arbitrary chunks** (the shape of a UART) can be reassembled into the same `CrsfFrame` objects C19 already parses from a complete buffer. **Human:** “ya no hace falta entregarle el mensaje entero de una vez — el chorro se puede cortar en frames CRSF, aún sin abrir un puerto ni afirmar RX enchufado.” |
| 4 | Direction of dependency | Assembler **imports and calls** `crsf_stub.parse_crsf_frame` (and may import `crsf_dual_role` + `radio` for the optional helper). **`radio.py` must not** grow CRSF/stream/serial symbols (C5 T5). **`crsf_stub.py` parse/decode behavior stays unchanged** — C19 tests remain the contract |
| 5 | CRC / envelope truth | Do **not** reimplement CRC8 `0xD5` or the envelope layout in the assembler. Slice a candidate window of `frame_len + 2` bytes and pass **exactly** that window to `parse_crsf_frame`. C19 still rejects truncated/mismatch/bad-CRC on a complete window |
| 6 | Incomplete vs invalid | **Incomplete** candidate (buffer shorter than declared total) → **wait** (return no new frame; leftover kept). This is the opposite of C19’s `parse_crsf_frame`, which raises if you hand it a too-short buffer. **Invalid complete** window (bad CRC / length mismatch that C19 would raise) → **do not raise to the caller**; **drop 1 byte** and retry (UART hunt / resync). Report must state this |
| 7 | Plausible `frame_len` | CRSF length byte covers `type + payload + crc` and is conventionally **≤ 64**. If `frame_len < 2` or `frame_len > 64`, treat as desync: **drop 1 byte**, do not wait for a huge garbage window. Constant documented in code + report |
| 8 | Bounded leftover | Assembler holds a leftover buffer. Document a **max** (default **256** bytes). If leftover would exceed max after a `feed`, drop oldest bytes until within max (or equivalent documented bound). No unbounded growth on noise |
| 9 | Optional C20 helper | Provide a thin helper that, for each completed frame with type `0x16`, `decode_rc_channels_packed` then `ingest_rc_channels` (C20). Non-`0x16` frames are skipped by this helper (still emitted by the assembler itself). **Forbidden:** synthesizing Intent, calling `submit_command`, or calling `SafetyGate.evaluate`. C20 policy defaults unchanged (aux ch 4 / 1500 / `kill`) |
| 10 | Pure / no I/O | No `serial`, `socket`, `pty`, USB, subprocess, or `open()` of a device path in the assembler module real code. Tests feed `bytes`. No class named like `Serial`/`UartPort` that implies a device |
| 11 | `RadioIntentAdapter` | Remains **`NotImplementedError`** / `"not_implemented"` — even if fed stream output or bridged frames |
| 12 | Safety | `default_safety_gate()` stays RejectAll. Do not change `ArmedAllowlistSafetyGate`. Stream/bridge Authority is **trace-only** |
| 13 | No craft / no native | Continuity, Board, `library/`, `native/` untouched — no CRSF/ELRS/UART driver tokens under `native/` |
| 14 | Version | Bump **`0.5.18` → `0.5.19`**; tag **`v0.5.19`** on ACCEPT only |
| 15 | Forbidden claims | “Live ELRS” · “RX connected” · “UART open” · “serial driver” · “sticks drive craft” · “Authority allows HOLD/LAND” · “radio capability available” in default registry |

**Product sentence:**

```text
Ensamblador de stream de bytes con forma de UART: chunks → frames CRSF
completos, reutilizando el parse C19 y (opcional) el puente C20 — sin
abrir puerto, sin RF, sin que Authority abra Safety.
```

**Defaults locked by Cursor (Engineer pick 2026-09-22: UART stream):**
- New **`crsf_stream.py`** (do not bloat `crsf_stub.py`)  
- Call C19 `parse_crsf_frame` on exact slices; drop-1 resync on invalid complete windows  
- `frame_len` plausible range `[2, 64]`; leftover max **256**  
- Optional `0x16` → C20 ingest helper; no Intent; no serial  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  crsf_stub.py              # C19 — UNCHANGED parse/decode behavior
  crsf_dual_role.py         # C20 — UNCHANGED policy
  crsf_stream.py            # NEW — assembler
  radio.py                  # UNCHANGED public decode surface (T5)
  intent.py / safety.py     # UNCHANGED behavior

tests/
  test_fase_c_crsf_byte_stream_b1.py
  fixtures/crsf/            # reuse C19 .bin; extra stream fixtures optional
```

Report must name the public symbols. Do **not** create `src/jarvis/radio/` or `native/**/uart*` / `native/**/crsf*`.

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them.

### 2.1 Assembler

```text
CrsfByteStreamAssembler
  max_buffer: int = 256          # leftover cap
  max_frame_len: int = 64        # plausible CRSF length-byte max

  feed(data: bytes) -> list[CrsfFrame]
    # append data; return newly completed, CRC-valid frames (0..N)
    # never raises CrsfParseError to the caller

  leftover() -> bytes            # unconsumed buffer (tests)
  reset() -> None                # clear leftover + counters
  dropped_byte_count: int        # cumulative drop-1 / overflow drops (tests)
```

`feed(b"")` is a no-op returning `[]`. Concatenated complete frames in one `feed` return **all** of them, in order.

### 2.2 Optional C20 helper

```text
ingest_stream_bytes(
    data: bytes,
    *,
    assembler: CrsfByteStreamAssembler,
    policy: CrsfDualRolePolicy,
    ingress: SimulatedRadioIngress | None = None,
) -> list[RadioDualRoleResult]
  # feed → for each new 0x16 frame: decode RC → ingest_rc_channels
  # below-threshold C20 results are omitted (None not appended)
  # 0x14 / unknown types: skipped here; still in assembler.feed() output
```

### 2.3 Explicit non-goals

No `open_serial`, no baud-rate API, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no extra Authority kinds, no address whitelist required (C19 accepts any `device_addr`).

---

## 3. Integration rules

| Existing | C21 rule |
|---|---|
| C19 `parse_crsf_frame` | **Called** on exact candidate slices; not rewritten; still raises internally on bad windows (assembler catches) |
| C19 truncated fixture | Assembler **waits** if leftover is shorter than declared total — does **not** have to raise |
| C20 policy / bridge | Unchanged; optional helper is a caller |
| C5 `radio.py` | No `decode_*` / `open_serial` / `write_pwm` / stream types |
| C2 `RadioIntentAdapter` | Still refuses |
| C4 autonomy | **No** stream → `submit_command` |
| C17 Safety | Untouched |
| Registry | Default stays empty |

---

## 4. Tests (minimum)

Reuse `tests/fixtures/crsf/*.bin`. Mutated/synthetic concatenation is OK.

| ID | Check |
|---|---|
| T1 | One `feed` of `rc_channels_valid.bin` → exactly 1 `CrsfFrame` type `0x16`; leftover empty |
| T2 | Same fixture **one byte per `feed`** → no frame until the last byte, then 1 frame; leftover empty |
| T3 | Mid-frame split (e.g. 10 bytes then rest) → `[]` then 1 frame |
| T4 | Concatenate valid RC + valid link-stats fixtures in one `feed` → 2 frames, types `0x16` then `0x14`, leftover empty |
| T5 | Feed `rc_channels_truncated.bin` (declares 26, has 23) → **0 frames**, leftover kept (wait, not raise) |
| T6 | Garbage prefix (`b"\x00\x01\x02"` or similar) + valid RC fixture → eventually 1 valid `0x16` frame; `dropped_byte_count >= 1` |
| T7 | One `feed` of `rc_channels_bad_crc.bin` → **0** `CrsfFrame`; caller does **not** see `CrsfParseError` |
| T8 | Optional helper: stream containing an RC frame with aux ch 4 ≥ 1500 → at least one `RadioDualRoleResult` Authority `kill` (reuse C20 mutation/fixture approach); below-threshold stream → empty result list |
| T9 | No I/O imports / device `open(` in assembler module **real code** (comments/docstrings excluded, same style as C19/C20) |
| T10 | C5 T5: `radio.py` has no `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T11 | `RadioIntentAdapter` still `not_implemented` |
| T12 | Assembler / helper do not call `submit_command` / import autonomy surface for execution |
| T13 | `default_safety_gate()` still RejectAll |
| T14 | `pyproject` **`0.5.19`**; re-pin `0.5.18` checkpoints |
| T15 | Full suite green |
| T16 | Report: assembler ≠ UART open ≠ live ELRS ≠ Safety allow |
| T17 | Assembler source calls `parse_crsf_frame` (no second CRC implementation in `crsf_stream.py`) |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| `serial` / USB / `/dev/tty*` as acceptance | Still not a link product |
| Naming the module a “UART driver” in docs | This is a **byte buffer** with UART-shaped chunking |
| Claiming RX connected / live ELRS | No RF, no port |
| Pilot sticks control craft | No mixer/ESC path |
| Authority → Safety `allow` | C0/C17 honesty |
| Auto `submit_command` | Fake autonomy |
| Decode/stream APIs on `radio.py` | Breaks C5 T5 |
| Reimplement CRC in the assembler | Splits envelope truth from C19 |
| Deepen C20 policy / Intent from sticks | Separate Buy |
| Marking radio `available` in registry | Premature |
| Flash / craft↔FS | Process lock; other axis |

---

## 6. Docs

- PRIORIDAD: C21 in flight / CLOSED as appropriate  
- PLATFORM §13: C21 stream block + honesty line  
- ARCHITECTURE: short note under capabilities (`crsf_stream.py`)  
- README “What v0.5.19 includes”  

Honesty line (must appear in report + living docs):

```text
Byte-stream assembler ≠ UART open ≠ live ELRS ≠ a pilot link ≠ Safety allow
```

---

## 7. Acceptance

**PASS when:** T1–T17 · chunks reassemble to C19 frames · wait-on-truncated · drop-1 on bad complete window · optional C20 path typed · C5/C19/C20 locks hold · Safety default unchanged · version `0.5.19` · docs honest.

**FAIL if:** serial product · `CrsfParseError` leaked on bad CRC feed · CRC reimplemented · Safety allow via Authority · CRSF→autonomy executed · decode/stream stuffed into `radio.py` · C19 parse behavior changed.

---

## 8. Handoff

```text
Engineer → ★ this IC (C21)
Claude   → implement assembler + tests + report + 0.5.19
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.19
Cursor   → next Buy when Engineer prioritizes (deepen policy · board flash · craft↔FS — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C20 CLOSED @ v0.5.18. C21 B1-fase-c-crsf-byte-stream READY —
UART-shaped byte stream → CRSF frames (C19 parse reused; optional C20
bridge); not serial open; not live ELRS; Authority ≠ Safety allow.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **stream assembler only** (not opening a serial port) OK?  
2. Drop-1 resync on invalid complete windows (no raise to caller) OK?  
3. Module: **new `crsf_stream.py`** OK? (Cursor default)  
4. Optional `0x16` → C20 helper in this Buy OK? (Cursor default: **yes**, thin)  
5. Version **`0.5.19`** OK?  
6. Keep `RadioIntentAdapter` NotImplemented OK?  
