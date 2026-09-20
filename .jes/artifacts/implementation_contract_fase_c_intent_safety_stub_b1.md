# Implementation Contract — Fase C Intent ingress + Safety gate stub (`B1-fase-c-intent-safety-stub`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (no false “armed” / no actuator path)

**Status:** READY FOR ★  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — Intent → … → Safety; channels; radio dual-role (architecture)  
- [C1 ★ ACCEPT](implementation_contract_fase_c_capability_registry_scaffold_b1.md) — empty Capability Registry @ **`0.5.0`**  
- Craft SoT Continuity / CLI unchanged  

**Type:** **Implementation Contract** — **typed Intent ingress model** + **Safety/Authority gate interface** as **non-operational stubs**.  
**Package:** stay **`0.5.0`** (no bump unless Engineer ★ asks `0.5.1`).  
**Not** voice STT/TTS · not ELRS stack · not FC/HAL · not Skill execution · not wiring orchestrator Continuity into flight · not Board chat.

**Outputs (required):**
1. Code under `src/jarvis/capabilities/` (or sibling `intent/` / `safety/` modules **inside** the capabilities package tree — prefer `src/jarvis/capabilities/intent.py` + `safety.py` to avoid new top-level packages without need)  
2. Tests  
3. `.jes/artifacts/implementation_report_fase_c_intent_safety_stub_b1.md`  
4. Docs honesty: PRIORIDAD + short ARCHITECTURE / PLATFORM_CAPABILITY note — stubs ≠ live Safety  

**Checkpoint:** package **`0.5.0`** · suite ≥ **3181** at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-intent-safety-stub`** — Intent records + channel adapters **stubs** + Safety gate **interface** |
| 2 | C0/C1 authority | C0 architecture only; C1 registry exists empty. This IC is the **first** authority for Intent/Safety **types + stub APIs** on disk |
| 3 | Intent | Typed `Intent` (and optional thin `Task` stub) describing **what was asked**, not how to fly |
| 4 | Channels | Enum/source ids: at least `terminal`, `voice`, `radio`, `api` (and optionally `ui`). Each channel has a **placeholder adapter** that can wrap a string/payload into an `Intent` **or** explicitly raise `NotImplementedError` / return `availability=not_implemented` — **lock: adapters exist as typed callables/classes that construct Intent from a raw string for `terminal` only; `voice`/`radio`/`api` adapters exist but always return `not_implemented` / refuse without producing a “success flight intent”** |
| 5 | Safety gate | Interface `SafetyGate.evaluate(request) -> SafetyDecision` with outcomes at least `allow` \| `reject` (and optional `defer`). **C2 default implementation:** `RejectAllSafetyGate` (or `UnknownSafetyGate`) that **always rejects** with reason `not_implemented` — so nothing can accidentally “pass” Safety in C2 |
| 6 | Authority vs Intent | Types distinguish `IntentSource` vs `AuthoritySignal` (radio may later emit both). C2 ships the **type split** + a stub `AuthoritySignal` record; **no** ELRS decode |
| 7 | Pipeline stub | Optional pure function `propose_resolution(intent) -> ResolutionProposal` that **does not** call actuators and **does not** mark capabilities available. May attach empty registry lookup. Must end with **mandatory** `safety.evaluate(...)` before any hypothetical “execution” step — and since gate always rejects, “execution” step must be **absent** or a no-op that asserts decision was reject |
| 8 | No craft coupling | Do **not** change `orchestrator.py` Continuity paths, Board, or `library/`. Terminal Intent adapter is a **library API**, not a CLI rewrite |
| 9 | Registry | May **read** `CapabilityRegistry.load_default()` (still empty). Must **not** require non-empty registry |
| 10 | Honesty | Forbidden: `allow` by default · claiming radio/voice live · any ESC/mixer/PWM · Skill.execute |
| 11 | Version | **No bump** (remain `0.5.0`) unless Engineer ★ `0.5.1` |
| 12 | Forbidden | `flight_software/` · Conversation Engine · Board chat · real Safety policy that allows flight |

**Product sentence:**

```text
Modelar cómo entra la intención (terminal ahora; voz/radio/api como
stubs honestos) y obligar a pasar por una puerta Safety que en C2
siempre rechaza — sin fingir autoridad ni actuación.
```

---

## 1. Schemas / types (minimal)

### 1.1 `IntentSource` (enum)

`terminal` | `voice` | `radio` | `api` | (`ui` optional)

### 1.2 `Intent`

| Field | Notes |
|---|---|
| `id` | uuid or str |
| `source` | `IntentSource` |
| `raw_text` | str (may be empty for non-text future) |
| `created_at` | optional ISO / datetime |
| `metadata` | optional dict with `extra="forbid"` or bounded keys only |

### 1.3 `Task` (optional thin stub)

If included: `id`, `intent_id`, `required_capability_ids: list[str]` (default `[]`). No execution fields.

### 1.4 `AuthoritySignal` (stub record)

| Field | Notes |
|---|---|
| `id` | |
| `source` | at least `radio` \| `api` \| `operator` |
| `kind` | e.g. `override` \| `kill` \| `mode` \| `unknown` — **data only** |
| `payload` | optional opaque str |

**Not** decoded RC channels.

### 1.5 `SafetyDecision`

| Field | Notes |
|---|---|
| `outcome` | `allow` \| `reject` \| (`defer` optional) |
| `reason` | str, required on reject |
| `gate_id` | str identifying which gate implementation |

### 1.6 `SafetyRequest` (input to gate)

Minimal: references `intent_id` and/or proposed action id string; **no** actuator command blob.

---

## 2. APIs (normative)

### 2.1 Channel adapters

```text
TerminalIntentAdapter.parse(raw_text: str) -> Intent
  # constructs Intent(source=terminal, raw_text=...)

VoiceIntentAdapter.parse(...) -> NEVER a successful flight intent in C2
  # raise NotImplementedError OR return a Result type with not_implemented
  # Lock: raise NotImplementedError with message containing "not_implemented"

RadioIntentAdapter.parse(...) -> same as voice (NotImplementedError)

ApiIntentAdapter.parse(...) -> same as voice (NotImplementedError)
```

### 2.2 Safety

```text
SafetyGate (Protocol or ABC)
  evaluate(request: SafetyRequest) -> SafetyDecision

RejectAllSafetyGate
  evaluate(...) -> SafetyDecision(outcome=reject, reason="not_implemented", ...)
```

**Lock:** the **only** shipped default gate factory (`default_safety_gate()`) returns `RejectAllSafetyGate`.  
An `AllowAllSafetyGate` **must not** ship in C2 (even for tests of “happy path allow” — if needed, tests may construct a local fake **inside the test file only**, not in `src/`).

### 2.3 Optional pipeline helper

```text
run_intent_through_safety(intent: Intent, gate: SafetyGate) -> SafetyDecision
  # builds SafetyRequest from intent; returns gate.evaluate(...)
  # MUST NOT call any actuator / skill execute / registry “run”
```

---

## 3. Package layout (guidance)

```text
src/jarvis/capabilities/
  schemas.py          # existing C1
  registry.py         # existing C1
  intent.py           # NEW — Intent, sources, adapters
  safety.py           # NEW — SafetyGate, RejectAll, AuthoritySignal
  __init__.py         # export new public types carefully
```

Do **not** create top-level `src/jarvis/flight_software/` or `safety/` package outside capabilities unless a later IC says so.

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `TerminalIntentAdapter.parse("hola")` → Intent with `source=terminal`, raw_text set |
| T2 | Voice / Radio / Api adapters → `NotImplementedError` (or locked refuse) |
| T3 | `default_safety_gate().evaluate(...)` → `reject` + reason contains `not_implemented` |
| T4 | `AllowAllSafetyGate` **not** importable from public `jarvis.capabilities` (or does not exist under `src/`) |
| T5 | `run_intent_through_safety` returns reject when using default gate |
| T6 | `AuthoritySignal` can be constructed; no decode/ELRS |
| T7 | No public method named like `execute`/`dispatch`/`command_esc` on new modules |
| T8 | C1 `load_default()` still empty; unchanged |
| T9 | `pyproject` still `0.5.0` |
| T10 | Full suite green (no craft regression) |
| T11 | Report confirms H-locks |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Default gate `allow` | Would fake Safety |
| Voice/radio “working” parse | Not implemented |
| Hooking CLI `handle_user_text` to Safety | Scope; craft Continuity stays |
| Creating available flight capabilities | C1 honesty |
| ELRS/CRSF drivers | C5 |
| FC rung / mixer | C3 |

---

## 6. Docs

- PRIORIDAD: C2 in flight / CLOSED as appropriate  
- One paragraph under ARCHITECTURE §1b or PLATFORM_CAPABILITY §13: Intent/Safety **stubs**; default reject  
- C0 attack order note: C2 landed as stub  

---

## 7. Acceptance

**PASS when:** T1–T11 · default Safety always rejects · terminal Intent only · no FS tree · version stays 0.5.0.  

**FAIL if:** anything can `allow` by default · voice/radio pretend live · orchestrator flight path · actuators.

---

## 8. Handoff

```text
Engineer → ★ this IC (C2)
Claude   → implement intent.py + safety.py + tests + report
Cursor   → review
Engineer → ACCEPT
Cursor   → C3 IC (first FC rung) when Engineer prioritizes
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C1 ACCEPT @ v0.5.0. C2 B1-fase-c-intent-safety-stub READY —
terminal Intent + RejectAll SafetyGate; voice/radio/api NotImplemented.
```
