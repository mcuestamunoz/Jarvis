# Implementation Contract — Fase C Radio dual-role ingress stub (`B1-fase-c-radio-dual-role`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (no ELRS decode · no Safety bypass · Authority ≠ Intent)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.3`** (with C4 as one block — no `v0.5.2` tag; see [docs truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md))
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §3 radio dual-role · §5 Authority · §10 C5  
- [C2 ★ ACCEPT](implementation_contract_fase_c_intent_safety_stub_b1.md) — `Intent` / `RadioIntentAdapter` (NotImplemented) / `AuthoritySignal`  
- [C4](implementation_contract_fase_c_autonomy_surface_b1.md) — autonomy surface behind RejectAll (ACCEPT before or with this Buy’s land — **do not implement C5 until C4 is ACCEPT CLOSED** unless Engineer ★ says otherwise)  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — typed **radio dual-role model** (Intent **and/or** Authority) + **simulated** ingress only.  
**Package:** bump to **`0.5.3`** after C4’s `0.5.2` is on tip; git tag **`v0.5.3`** only after Engineer ACCEPT.  
**Not** real ELRS/CRSF decode · not serial/USB/SPI drivers · not RC stick→mixer · not weakening RejectAll · not wiring CLI · not live autonomy execution · not production C++ radio stack.

**Outputs (required):**
1. Code under `src/jarvis/capabilities/` (prefer new `radio.py`; may thin-extend `intent.py` / `safety.py` only as needed — **no** new top-level package)  
2. Tests  
3. `.jes/artifacts/implementation_report_fase_c_radio_dual_role_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — dual-role **stub ≠ live ELRS**  
5. `pyproject.toml` → **`0.5.3`** (+ re-pin version-checkpoint tests)

**Checkpoint:** package **`0.5.3`** · suite ≥ **3219** (or post-C4-ACCEPT baseline) + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-radio-dual-role`** — radio as **Intent source** and/or **Authority** — types + simulated ingress |
| 2 | Dual-role (C0) | A radio event may yield: (a) `Intent` only, (b) `AuthoritySignal` only, or (c) **both** as separate typed objects in one result record. **Never** collapse RC/authority into an Assistant “skill” or into autonomy `execute` |
| 3 | Keep C2 refuse path | Existing `RadioIntentAdapter.parse(...)` remains **`NotImplementedError`** with `"not_implemented"` (live/unclassified radio path). C5 adds a **separate** simulated API — do not silently make `RadioIntentAdapter` “work” for arbitrary payloads |
| 4 | Simulated only | Ship `SimulatedRadioIngress` (name may vary) that accepts a **typed stub frame** (not CRSF bytes) and returns a dual-role result. **No** binary protocol decode, **no** hardware I/O |
| 5 | Authority kinds | Reuse / stay compatible with C2 `AuthoritySignal` (`source` includes `radio`; `kind` at least `override` \| `kill` \| `mode` \| `unknown`). May add stub kinds only if documented; prefer existing set |
| 6 | Intent from radio | When the stub frame declares an intent role, construct `Intent(source=RADIO, raw_text=...)` with explicit stub text (e.g. `"RETURN_HOME"` as text — **not** calling autonomy `submit` automatically) |
| 7 | Safety | `default_safety_gate()` stays `RejectAllSafetyGate`. Optional: extend `SafetyRequest` with `authority_signal_id: str \| None = None` for traceability — **must not** change reject-all behavior. Forbidden: authority “wins” into `allow` |
| 8 | No auto-fly | Forbidden: simulated radio → autonomy `submit` → claim executed; radio → ESC/PWM; radio bypasses Safety |
| 9 | No craft coupling | Do **not** change orchestrator Continuity, Board, or `library/` |
| 10 | Version | **`0.5.2` → `0.5.3`** (assumes C4 ACCEPT @ `0.5.2`); tag **`v0.5.3`** on ACCEPT |
| 11 | Language / stack | Python platform scaffold. Phrase in new module docstring: dual-role stub; **production radio/ELRS stack = future IC** (may be native/C++ — not this Buy). No C++/CMake tree |
| 12 | Forbidden | Real ExpressLRS / CRSF / SBUS drivers · Conversation Engine · Board chat · `AllowAllSafetyGate` · marking radio capability `available` in default registry |

**Product sentence:**

```text
Modelar la radio como canal dual (Intent y/o Authority) con ingress
simulado tipado — sin decode ELRS real y sin que la radio salte Safety
ni actúe motores.
```

---

## 1. Package layout (normative)

```text
src/jarvis/capabilities/
  intent.py          # C2 — RadioIntentAdapter stays NotImplemented
  safety.py          # C2 — optional SafetyRequest.authority_signal_id only
  radio.py           # NEW — stub frame, dual-role result, SimulatedRadioIngress
  __init__.py        # export new public types carefully
```

Do **not** create `src/jarvis/radio/` or `flight_software/radio/` in this Buy.

---

## 2. Types / APIs (normative)

### 2.1 `RadioStubFrame`

Typed stand-in for “what came off the link” **without** decoding a real protocol:

| Field | Notes |
|---|---|
| `id` | uuid/str |
| `role` | Literal `"intent"` \| `"authority"` \| `"both"` |
| `intent_text` | str — required if role is `intent` or `both`; else empty |
| `authority_kind` | same literals as `AuthoritySignal.kind` — required if role is `authority` or `both` |
| `authority_payload` | optional opaque str |
| `notes` | optional honesty string |

`extra="forbid"`. **No** `channels: list[int]` RC raw map pretending to be ELRS.

### 2.2 `RadioDualRoleResult`

| Field | Notes |
|---|---|
| `frame_id` | str |
| `intent` | `Intent \| None` |
| `authority` | `AuthoritySignal \| None` |

Invariants (enforce in validator or factory):

- role `intent` → intent set, authority None  
- role `authority` → authority set, intent None  
- role `both` → both set  

### 2.3 `SimulatedRadioIngress`

```text
ingest(frame: RadioStubFrame) -> RadioDualRoleResult
  # builds Intent(source=RADIO, ...) and/or AuthoritySignal(source="radio", ...)
  # never opens sockets / serial / files for RF
```

### 2.4 Optional helper (pure)

```text
describe_dual_role(result: RadioDualRoleResult) -> str
  # short debug string for tests/docs — no Safety call required
```

### 2.5 `RadioIntentAdapter` (unchanged contract)

```text
RadioIntentAdapter.parse(raw_payload) -> still raises NotImplementedError("...not_implemented...")
```

Document in module docstring: live/unclassified path remains refuse; use `SimulatedRadioIngress` for stub dual-role.

### 2.6 Optional SafetyRequest extension

If implemented:

```text
SafetyRequest.authority_signal_id: str | None = None
```

Tests: RejectAll still rejects when this field is set. Autonomy `submit_command` may ignore it in C5 (no requirement to thread radio→autonomy).

---

## 3. Integration rules

| Existing | C5 rule |
|---|---|
| C2 Intent / AuthoritySignal | Reuse; do not duplicate parallel types |
| C4 autonomy | **No** automatic `submit_command` from radio ingest |
| C3 flight_control | Untouched |
| Registry | Default stays empty |
| RejectAll | Unchanged |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Stub frame `role=intent` → result.intent.source == RADIO, authority is None |
| T2 | Stub frame `role=authority` kind=`kill` → AuthoritySignal source radio, intent None |
| T3 | Stub frame `role=both` → both populated; types distinct |
| T4 | `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` matching `not_implemented` |
| T5 | No public method under `radio.py` named like `decode_crsf` / `decode_elrs` / `open_serial` / `write_pwm` |
| T6 | Default Safety still reject; if `authority_signal_id` added, still reject |
| T7 | Grep: no `.cpp`/CMake under `capabilities/` from this Buy; no ELRS driver tree |
| T8 | Zero craft imports of new radio symbols from `core/` / `adapters/` |
| T9 | Registry `load_default()` still empty |
| T10 | `pyproject` **`0.5.3`**; re-pin `0.5.2` pins |
| T11 | Full suite green |
| T12 | Report confirms dual-role + no live ELRS + no Safety bypass |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| CRSF/ELRS binary decode presented as product | No RF stack Buy |
| Radio → motors / mixer | C0 Safety chain |
| Making `RadioIntentAdapter` silently succeed | Would fake live radio |
| Authority implies Safety `allow` | Fake pilot authority |
| Collapsing kill/override into Skill.execute | Wrong layer |
| CLI “stick” simulation wired to Continuity | Scope |

---

## 6. Docs

- PRIORIDAD: C5 in flight / CLOSED as appropriate  
- PLATFORM §13: C5 dual-role stub block  
- ARCHITECTURE: short note under capabilities (radio dual-role stub)  
- README “What v0.5.3 includes”  

---

## 7. Acceptance

**PASS when:** T1–T12 · dual-role types work in sim · `RadioIntentAdapter` still refuses · RejectAll unchanged · no ELRS drivers · version `0.5.3` · no craft coupling.

**FAIL if:** real protocol decode · Safety allow via authority · radio→autonomy executed · craft wiring.

---

## 8. Handoff

```text
Engineer → ACCEPT C4 (+ tag v0.5.2) if still open, then ★ this IC (C5)
Claude   → implement radio.py + tests + report + 0.5.3
Cursor   → review
Engineer → ACCEPT + tag v0.5.3
Cursor   → next Buy when Engineer prioritizes (further FC rungs / real Safety policy / native stacks — separate ICs)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C4 autonomy surface landed (await ACCEPT @ 0.5.2). C5
B1-fase-c-radio-dual-role READY — simulated Intent|Authority dual-role;
RadioIntentAdapter stays NotImplemented; no ELRS decode.
```

---

## 10. Engineer ★ checklist

1. Confirm implement **after** C4 ACCEPT (recommended)  
2. Version **`0.5.3`** OK?  
3. Keep `RadioIntentAdapter` NotImplemented OK?  
4. Optional `SafetyRequest.authority_signal_id` — include or skip? (default: **include**, reject behavior unchanged)  
