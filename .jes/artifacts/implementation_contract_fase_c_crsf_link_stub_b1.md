# Implementation Contract — Fase C CRSF link stub (`B1-fase-c-crsf-link-stub`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (fixture decode ≠ live ELRS · no serial · Authority ≠ Safety allow · `RadioIntentAdapter` still refuses)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.17`**  
**Parents:**
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — dual-role stub @ **`v0.5.3`**; `RadioStubFrame` / `SimulatedRadioIngress`; **no** CRSF bytes in `radio.py` (T5)  
- [C18 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) — freestanding `.elf` CLOSED @ **`v0.5.16`**; Engineer pick **link ELRS**  
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §3 radio · §5 Authority  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, GPIO, craft↔FS, Safety policy changes in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · C++ `native/flight_control/` **untouched**

**Type:** **Implementation Contract** — host-side **CRSF frame parse stub** from **checked-in / synthetic byte fixtures** (the wire format ExpressLRS commonly uses on UART). Typed parse result only.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.17`**; git tag **`v0.5.17`** only after Engineer ACCEPT.  
**Not** live ExpressLRS RF · not USB/serial open to a real RX · not making `RadioIntentAdapter` succeed · not RC→mixer/ESC · not Safety / `ArmedAllowlist` changes · not production C++ radio · not board flash.

**Outputs (required):**
1. New module under `src/jarvis/capabilities/` — preferred name **`crsf_stub.py`** (must **not** put `decode_crsf` / CRSF parsers inside `radio.py` — preserve C5 T5 honesty)  
2. Tests + checked-in hex fixtures (or equivalent bytes in test module) for the locked frame set  
3. `.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **CRSF fixture decode ≠ ExpressLRS on air ≠ pilot link**  
5. `pyproject.toml` → **`0.5.17`** (+ re-pin `0.5.16` version-checkpoint tests)

**Checkpoint:** package **`0.5.17`** · Python suite ≥ **3412** + new tests · C5 radio suite still green · no I/O in module under test

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-link-stub`** — first byte-level CRSF parse stub (ELRS-shaped link front) |
| 2 | One front | Do **not** fold serial drivers, USB RX open, GPIO, MCU radio C++, craft↔FS, Safety policy, or flash into this Buy |
| 3 | What this Buy demonstrates | Jarvis can **parse a documented minimal CRSF packet set** from fixtures into typed fields (envelope + at least RC channels). **Human:** “ya entendemos bytes CRSF en el Mac — aún sin enchufar el receptor ni afirmar link en el aire.” |
| 4 | Protocol honesty | Document: ExpressLRS often carries **CRSF** on the UART between RX and FC. This Buy parses **CRSF bytes**. It does **not** implement the ELRS air protocol, binding, telemetry RF, or “connected to TX.” |
| 5 | Module boundary | New **`crsf_stub.py`** (name flexible if documented). **Forbidden:** adding `decode_crsf` / `decode_elrs` / `open_serial` as public APIs on `radio.py` (C5 T5 must stay green) |
| 6 | Envelope (locked minimum) | Parse CRSF frame layout: `[device_addr][frame_len][type][payload…][crc8]` with CRC8 poly **`0xD5`** over `type + payload` (standard CRSF). Reject truncated frames and bad CRC with a typed error (exception or result type — document choice) |
| 7 | Frame types (locked minimum) | At least **`0x16` `RC_CHANNELS_PACKED`** → 16 channels × 11-bit packed decode to integers. **Recommended** (include unless blocked): **`0x14` `LINK_STATISTICS`** → a small typed struct (rssi/lq/… fields as documented; unknown bytes may be left raw). Other types: either typed-as-unknown payload or explicit reject — document |
| 8 | Fixtures | At least one **valid** RC-channels fixture and one **invalid** (bad CRC and/or truncated). Prefer `tests/fixtures/crsf/*.bin` or hex constants in the new test file — must be **checked in**, not downloaded at test time |
| 9 | Pure functions only | No `open()`, `serial`, `socket`, `pty`, USB, or subprocess I/O in the module under test. Tests feed `bytes` |
| 10 | C5 dual-role | `SimulatedRadioIngress` / `RadioStubFrame` remain the simulated dual-role path. **Optional** thin helper mapping decoded fields → notes/`RadioStubFrame` is allowed but **not** required. **Forbidden:** auto `submit_command`, Safety `allow`, or claiming Authority from CRSF bytes without an explicit later IC |
| 11 | `RadioIntentAdapter` | Remains **`NotImplementedError`** with `"not_implemented"` — live/unclassified path. Do **not** route fixture bytes through it as “success” |
| 12 | Safety | `default_safety_gate()` stays `RejectAllSafetyGate`. Do **not** change `ArmedAllowlistSafetyGate` or any evaluate path. Authority from radio stays unable to flip allow |
| 13 | No craft / no native radio | Do not change Continuity, Board, `library/`, or add CRSF/ELRS symbols under `native/` |
| 14 | Version | Bump **`0.5.16` → `0.5.17`**; tag **`v0.5.17`** on ACCEPT only |
| 15 | Forbidden claims | “Live ELRS link” · “RX connected” · “pilot sticks drive mixer” · “CRSF driver product” · “radio capability available” in default registry |

**Product sentence:**

```text
Parsear frames CRSF mínimos desde fixtures de bytes (envelope + RC
channels) — stub de link ELRS-shaped en host, sin serial ni RF real.
```

**Defaults locked by Cursor (Engineer: ACCEPT C18 + procede link ELRS):**
- Host Python `crsf_stub.py` (not inside `radio.py`)  
- CRC8 `0xD5` · type `0x16` required · `0x14` recommended  
- Fixtures only · no I/O · no Safety / native / craft coupling  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  radio.py           # UNCHANGED role — C5 dual-role sim; T5 still forbids decode_* here
  crsf_stub.py       # NEW — parse + decode pure functions / types
  __init__.py        # export new public types carefully (optional)

tests/
  fixtures/crsf/     # NEW preferred — checked-in .bin or .hex
  test_fase_c_crsf_link_stub_b1.py
```

Do **not** create `src/jarvis/radio/` or `flight_software/radio/` or `native/**/crsf*`.

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them.

### 2.1 Envelope

```text
parse_crsf_frame(data: bytes) -> CrsfFrame
  # or Result[CrsfFrame, CrsfParseError]
  # validates length + CRC8(poly=0xD5)
```

`CrsfFrame` fields at least: `device_addr`, `frame_type`, `payload: bytes` (and optionally raw frame / crc).

### 2.2 RC channels

```text
decode_rc_channels_packed(payload: bytes) -> CrsfRcChannels
  # 16 × 11-bit channels → tuple/list of int
  # reject wrong payload length
```

### 2.3 Link statistics (recommended)

```text
decode_link_statistics(payload: bytes) -> CrsfLinkStatistics
  # document field map; keep small
```

### 2.4 Optional describe helper

```text
describe_crsf_frame(frame: CrsfFrame) -> str
  # debug/tests — no Safety / autonomy calls
```

### 2.5 Explicit non-goals in this module

No `open_serial`, no `ElrsLink`, no `connect()`, no background reader threads.

---

## 3. Integration rules

| Existing | C19 rule |
|---|---|
| C5 `radio.py` | Untouched behavior; T5 stays green |
| C2 `RadioIntentAdapter` | Still refuses |
| C4 autonomy | **No** CRSF → `submit_command` |
| C17 Safety | Untouched; default RejectAll |
| Registry | Default stays empty |
| C13–C18 native | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Valid RC_CHANNELS_PACKED fixture → 16 channel ints in documented range/shape |
| T2 | Truncated frame → typed parse failure (no hang / no partial silent success) |
| T3 | Bad CRC → typed parse failure |
| T4 | (If LINK_STATISTICS included) valid fixture → typed fields populated |
| T5 | Module under test has **no** `serial`/`socket`/`pty` imports and no `open(` for device paths |
| T6 | `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` matching `not_implemented` |
| T7 | C5 T5 still holds: `radio.py` has no public `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T8 | Grep: no CRSF/ELRS under `native/`; no craft imports of new symbols from `core/` / `adapters/` |
| T9 | `default_safety_gate()` still RejectAll; ArmedAllowlist behavior unchanged if smoke-touched |
| T10 | `pyproject` **`0.5.17`**; re-pin `0.5.16` version checkpoints |
| T11 | Full suite green |
| T12 | Report states: fixture CRSF ≠ live ELRS ≠ pilot link; no serial product |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Opening USB/serial to a real RX as acceptance | Hardware link ≠ this Buy |
| Claiming “ELRS connected / on air” | Air protocol not implemented |
| RC channels → mixer / ESC / PWM | C0 Safety chain |
| Making `RadioIntentAdapter` succeed on bytes | Would fake live radio |
| Putting decode APIs on `radio.py` | Breaks C5 T5 honesty |
| Safety allow via CRSF / Authority | Fake pilot authority |
| C++ CRSF stack in `native/` | Separate future IC |
| Marking radio `available` in default registry | Premature capability claim |

---

## 6. Docs

- PRIORIDAD: C19 in flight / CLOSED as appropriate  
- PLATFORM §13: C19 CRSF fixture stub block + honesty line  
- ARCHITECTURE: short note under capabilities (CRSF stub ≠ ELRS product)  
- README “What v0.5.17 includes”  

---

## 7. Acceptance

**PASS when:** T1–T12 · valid RC fixture parses · bad frames fail typed · no I/O · C5 radio locks hold · Safety default unchanged · version `0.5.17` · no craft/native coupling · docs honest.

**FAIL if:** serial product path · live-ELRS claim · `RadioIntentAdapter` succeeds · CRSF→autonomy executed · decode stuffed into `radio.py` breaking T5 · Safety weakened.

---

## 8. Handoff

```text
Engineer → ★ this IC (C19) after C18 ACCEPT @ v0.5.16
Claude   → implement crsf_stub.py + fixtures + tests + report + 0.5.17
Cursor   → review
Engineer → ACCEPT + tag v0.5.17
Cursor   → next Buy when Engineer prioritizes (board flash · craft↔FS · deepen link — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C18 CLOSED @ v0.5.16. C19 B1-fase-c-crsf-link-stub READY —
CRSF byte-fixture parse (RC channels); not live ELRS; no serial.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **fixture CRSF parse** (not USB RX product) OK?  
2. Module **`crsf_stub.py`** separate from `radio.py` OK?  
3. Require **`0x14` LINK_STATISTICS** in this Buy, or allow RC-only minimum? (Cursor default: **include `0x14`**)  
4. Version **`0.5.17`** OK?  
5. Keep `RadioIntentAdapter` NotImplemented OK?  
