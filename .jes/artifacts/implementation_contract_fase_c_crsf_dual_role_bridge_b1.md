# Implementation Contract — Fase C CRSF → dual-role bridge (`B1-fase-c-crsf-dual-role-bridge`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (bridge ≠ live ELRS · Authority ≠ Safety allow · no auto `submit_command` · `RadioIntentAdapter` still refuses · C5 T5 on `radio.py` intact)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.18`**  
**Parents:**
- [C19 ★ ACCEPT](implementation_contract_fase_c_crsf_link_stub_b1.md) — `crsf_stub.py` fixture parse @ **`v0.5.17`**  
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — `RadioStubFrame` / `SimulatedRadioIngress` @ **`v0.5.3`**  
- [C17 ★ ACCEPT](implementation_contract_fase_c_safety_real_policy_b1.md) — `ArmedAllowlistSafetyGate`; RejectAll default @ **`v0.5.15`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no serial product, flash, craft↔FS, Safety policy changes in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · C++ `native/flight_control/` **untouched**

**Type:** **Implementation Contract** — **bridge** decoded CRSF fields (from C19) into C5 dual-role types (`RadioStubFrame` → optional `SimulatedRadioIngress`), under a **documented, deterministic policy**. Still fixture/host-only.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.18`**; git tag **`v0.5.18`** only after Engineer ACCEPT.  
**Not** USB/serial RX product · not live ELRS air · not RC→mixer/ESC · not Safety allow via Authority · not making `RadioIntentAdapter` succeed · not craft↔FS · not board flash · not stream/UART assembler (defer).

**Outputs (required):**
1. Bridge API under `src/jarvis/capabilities/` — preferred: extend **`crsf_stub.py`** *or* thin new `crsf_dual_role.py` that imports `crsf_stub` + `radio` (document choice). **Forbidden:** putting CRSF decode or bridge APIs on `radio.py` (C5 T5 stays green)  
2. Tests using C19 fixtures / synthetic `CrsfRcChannels` (and link-stats if used)  
3. `.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **CRSF→dual-role bridge ≠ pilot link ≠ Safety allow**  
5. `pyproject.toml` → **`0.5.18`** (+ re-pin `0.5.17` version-checkpoint tests)

**Checkpoint:** package **`0.5.18`** · Python suite ≥ **3428** + new tests · C5/C19 suites still green · no I/O · Safety default unchanged

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-dual-role-bridge`** — first CRSF-decoded → dual-role bridge |
| 2 | One front | Do **not** fold serial/UART open, stream reassembly, GPIO, flash, craft↔FS, Safety policy edits, or mixer/ESC into this Buy |
| 3 | What this Buy demonstrates | Bytes that C19 already understands can produce a **typed** `RadioStubFrame` / `RadioDualRoleResult` under an explicit policy. **Human:** “el parse CRSF ya no muere en un struct — puede alimentar el modelo dual-role de C5, aún sin radio real ni Safety allow.” |
| 4 | Direction of dependency | Bridge may import `radio` + `crsf_stub`. **`radio.py` must not** grow CRSF symbols or decode APIs (C5 T5) |
| 5 | Policy (locked minimum) | Ship a small **documented** mapping object (name flexible), e.g. `CrsfDualRolePolicy`, with at least: **one aux RC channel index** (0–15) + **threshold** in CRSF 11-bit units → when channel ≥ threshold, emit Authority `kind="kill"` (or `"override"` — pick one, document). Below threshold → **no** dual-role frame (return `None` / empty result — document). Defaults must be explicit constants in code + report |
| 6 | Intent path (locked default) | **Authority-only** in this Buy. Do **not** invent Intent text from sticks/channels unless a later IC. Optional: policy flag to also emit `role="both"` is **out of scope** unless Engineer ★ expands |
| 7 | Link statistics (optional) | May attach LQ/RSSI into `RadioStubFrame.notes` or `authority_payload` when bridging; **must not** alone flip Safety. Pure notes enrichment is OK; do not require link-stats for PASS if RC policy path works |
| 8 | Ingress | Provide a pure helper that builds `RadioStubFrame`, and a thin helper that calls `SimulatedRadioIngress.ingest` when a frame is produced. **Forbidden:** calling `submit_command`, any `SafetyGate.evaluate`, or constructing execution claims |
| 9 | Pure / no I/O | No serial/socket/pty/USB/`open` device paths in bridge module code under test |
| 10 | `RadioIntentAdapter` | Remains **`NotImplementedError`** / `"not_implemented"` — even if fed CRSF bytes or bridge outputs |
| 11 | Safety | `default_safety_gate()` stays RejectAll. Do not change `ArmedAllowlistSafetyGate`. Authority from bridge is **trace-only** relative to Safety (same C5/C17 honesty) |
| 12 | No craft / no native | Continuity, Board, `library/`, `native/` untouched — no CRSF/ELRS tokens under `native/` |
| 13 | Version | Bump **`0.5.17` → `0.5.18`**; tag **`v0.5.18`** on ACCEPT only |
| 14 | Forbidden claims | “Live ELRS” · “RX connected” · “sticks drive craft” · “Authority allows HOLD/LAND” · “radio capability available” in default registry |

**Product sentence:**

```text
Puente determinista CRSF decodificado → RadioStubFrame / dual-role
(C5), con política documentada de Authority — sin serial, sin RF, sin
que Authority abra Safety.
```

**Defaults locked by Cursor (Engineer: deepen link after C19):**
- Authority-only from one aux channel + threshold → `kill`  
- Bridge outside `radio.py`  
- Optional `SimulatedRadioIngress.ingest` helper  
- No stream/UART assembler in this Buy  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  crsf_stub.py              # C19 — keep parse/decode; may ADD bridge helpers OR
  crsf_dual_role.py         # NEW preferred if bridge would bloat crsf_stub
  radio.py                  # UNCHANGED public decode surface (T5)
  intent.py / safety.py     # UNCHANGED behavior

tests/
  test_fase_c_crsf_dual_role_bridge_b1.py
  fixtures/crsf/            # reuse C19 .bin; may add one policy-specific fixture
```

Report must name the chosen module and public symbols.

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them.

### 2.1 Policy

```text
CrsfDualRolePolicy
  authority_channel_index: int   # 0..15
  authority_threshold: int       # CRSF 11-bit units, e.g. >= 1500 → fire
  authority_kind: Literal["kill"]  # locked default for this Buy
```

Validate index range and threshold in `[0, 2047]`.

### 2.2 Bridge

```text
rc_channels_to_stub_frame(
    channels: CrsfRcChannels,
    *,
    policy: CrsfDualRolePolicy,
    frame_id: str | None = None,
) -> RadioStubFrame | None
  # None when channel below threshold
  # RadioStubFrame(role="authority", authority_kind=..., authority_payload=..., notes=...)
```

### 2.3 Optional ingest helper

```text
ingest_rc_channels(
    channels: CrsfRcChannels,
    *,
    policy: CrsfDualRolePolicy,
    ingress: SimulatedRadioIngress | None = None,
) -> RadioDualRoleResult | None
  # builds stub frame then SimulatedRadioIngress.ingest; None if no frame
```

### 2.4 Explicit non-goals

No `open_serial`, no byte-stream assembler, no mixer/ESC, no Safety calls, no Intent synthesis from sticks.

---

## 3. Integration rules

| Existing | C20 rule |
|---|---|
| C19 `parse_crsf_frame` / decode | Reused; not rewritten |
| C5 `radio.py` | No new decode_* / open_serial / write_pwm |
| C2 `RadioIntentAdapter` | Still refuses |
| C4 autonomy | **No** bridge → `submit_command` |
| C17 Safety | Untouched |
| Registry | Default stays empty |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Channel ≥ threshold → `RadioStubFrame` role=`authority`, kind=`kill` |
| T2 | Channel < threshold → `None` (no frame) |
| T3 | Optional ingest helper → `RadioDualRoleResult` with AuthoritySignal source `radio`; intent None |
| T4 | End-to-end from C19 valid RC fixture: parse → decode → bridge (force one channel high in a synthetic/mutated payload **or** dedicated fixture) |
| T5 | No I/O imports / device `open(` in bridge module real code |
| T6 | `RadioIntentAdapter` still `not_implemented` |
| T7 | C5 T5: `radio.py` has no `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T8 | Bridge does not call `submit_command` / import autonomy surface for execution |
| T9 | `default_safety_gate()` still RejectAll; ArmedAllowlist unchanged if smoke-touched |
| T10 | `pyproject` **`0.5.18`**; re-pin `0.5.17` checkpoints |
| T11 | Full suite green |
| T12 | Report: bridge ≠ live ELRS ≠ Safety allow |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Serial/USB RX as acceptance | Still not a link product |
| Claiming pilot sticks control craft | No mixer/ESC path |
| Authority → Safety `allow` | C0/C17 honesty |
| Auto `submit_command` from bridge | Fake autonomy |
| Decode APIs on `radio.py` | Breaks C5 T5 |
| Stream reassembly / UART reader | Separate Buy |
| Marking radio `available` in registry | Premature |

---

## 6. Docs

- PRIORIDAD: C20 in flight / CLOSED as appropriate  
- PLATFORM §13: C20 bridge block + honesty line  
- ARCHITECTURE: short note under capabilities  
- README “What v0.5.18 includes”  

---

## 7. Acceptance

**PASS when:** T1–T12 · threshold policy works · ingest optional path typed · C5/C19 locks hold · Safety default unchanged · version `0.5.18` · docs honest.

**FAIL if:** serial product · Safety allow via Authority · CRSF→autonomy executed · decode stuffed into `radio.py` · Intent invented from sticks without ★ expansion.

---

## 8. Handoff

```text
Engineer → ★ this IC (C20)
Claude   → implement bridge + tests + report + 0.5.18
Cursor   → review
Engineer → ACCEPT + tag v0.5.18
Cursor   → next Buy when Engineer prioritizes (UART stream stub · deepen policy · board flash · craft↔FS — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C19 CLOSED @ v0.5.17. C20 B1-fase-c-crsf-dual-role-bridge READY —
CRSF decode → RadioStubFrame/Authority (kill aux policy); not live ELRS;
Authority ≠ Safety allow.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **bridge only** (not serial/UART) OK?  
2. Authority-only via **one aux channel → `kill`** OK? (Cursor default)  
3. Module: extend `crsf_stub.py` vs new `crsf_dual_role.py` — prefer **new thin file** if ★ silent? (Cursor default: **new `crsf_dual_role.py`**)  
4. Version **`0.5.18`** OK?  
5. Keep `RadioIntentAdapter` NotImplemented OK?  
