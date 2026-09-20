# Implementation Contract — Fase C autonomy command surface (`B1-fase-c-autonomy-surface`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (no live HOLD/LAND · Safety still vetoes)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.3`** (with C5 as one block — no `v0.5.2` tag; see [docs truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md))  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §8 autonomy vocabulary · §10 C4 · Safety before actuation  
- [C2 ★ ACCEPT](implementation_contract_fase_c_intent_safety_stub_b1.md) — `RejectAllSafetyGate` / `SafetyRequest` / `SafetyDecision`  
- [C3 ★ ACCEPT](implementation_contract_fase_c_first_fc_rung_b1.md) — HAL+IMU Python scaffold @ **`v0.5.1`** · Engineer C++ amendment  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — typed **autonomy command surface** (propose verbs) that **must** pass through Safety before any hypothetical execution.  
**Package:** bump to **`0.5.2`**; git tag **`v0.5.2`** only after Engineer ACCEPT.  
**Not** live vehicle motion · not attitude/controller/mixer/ESC · not extending C3 IMU rung · not ELRS (C5) · not wiring CLI Intent→autonomy · not `AllowAllSafetyGate` · not production C++ FC/autonomy firmware.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/autonomy/` (path locked §0)  
2. Tests  
3. `.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — autonomy **surface stub ≠ flyable autonomy**; retain C3 C++ honesty for FC runtime  
5. `pyproject.toml` → **`0.5.2`** (+ re-pin version-checkpoint tests)

**Checkpoint:** package **`0.5.2`** · suite ≥ **3206** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-autonomy-surface`** — autonomy command **types + submit-through-Safety API** (non-operational) |
| 2 | Package path | Create **`src/jarvis/flight_software/autonomy/`** (C0 tree; C3 forbade this until now). Do **not** put autonomy under `capabilities/` |
| 3 | Vocabulary | Ship `AutonomyVerb` enum covering C0 starter set: `TAKEOFF` \| `HOLD` \| `GO_TO` \| `FOLLOW` \| `RETURN_HOME` \| `LAND` \| `PATROL`. C4 **must** exercise at least **`HOLD`** and **`LAND`** end-to-end through Safety in tests; other verbs are valid enum members and may be proposed the same way |
| 4 | Safety gate mandatory | Any public “submit / run / dispatch” path **must** call `SafetyGate.evaluate(SafetyRequest(...))` **before** any execution step. With `default_safety_gate()`, outcome is always **`reject`** — therefore the execution step is **absent** or a no-op that records `rejected` / `not_implemented` and **never** touches FC actuators (there are none) |
| 5 | No live autonomy | Forbidden: claiming vehicle held/landed/took off; calling mixer/ESC; advancing C3 HAL beyond read_imu; starting threads/loops that pretend to fly |
| 6 | Language honesty | Same Engineer rule as C3: this Buy is **Python platform scaffold**. Phrase (or clear equivalent) in `autonomy/` package docstring: **`Python scaffold / sim only — production flight_control runtime is C++ (future IC)`**. No C++/CMake tree. Autonomy *command surface* may stay Python long-term as orchestration; it still must not pretend to be the production control loop |
| 7 | Registry | Default `CapabilityRegistry.load_default()` stays **empty**. Do not mark an `autonomy` capability `available` |
| 8 | No craft coupling | Do **not** change orchestrator Continuity, Board, or `library/`. Do **not** wire `TerminalIntentAdapter` → autonomy submit |
| 9 | Relationship to Intent | Optional helper may accept an `intent_id` string on the command record for traceability. **Do not** require parsing natural language in C4 |
| 10 | Version | Bump **`0.5.1` → `0.5.2`**; tag **`v0.5.2`** on Engineer ACCEPT only |
| 11 | Forbidden | ELRS · Conversation Engine · Board chat · `AllowAllSafetyGate` in `src/` · extending IMU→filter/controller ladder |
| 12 | GO_TO / FOLLOW params | Commands may carry optional opaque `params: dict[str, str]` (bounded / `extra=forbid` on the model). C4 does **not** validate waypoints or perception — params are data only |

**Product sentence:**

```text
Exponer verbos de autonomía (HOLD/LAND/…) como comandos tipados que
siempre pasan por Safety — y con el gate actual siempre se rechazan —
sin fingir que el vehículo ya vuela o aterriza.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/
  flight_control/          # C3 — unchanged (no new rung)
  autonomy/                # NEW — C4
    __init__.py            # honest docstring (scaffold; Safety-gated; ≠ live autonomy)
    types.py               # AutonomyVerb, AutonomyCommand, AutonomySubmissionResult
    surface.py             # propose_command / submit_command (names may vary; see §2)
```

Optional thin re-exports from `jarvis.flight_software.autonomy`.  
**Do not** create `flight_software/autonomy/executor.py` that writes motors.

---

## 2. Types / APIs (normative)

### 2.1 `AutonomyVerb`

```text
TAKEOFF | HOLD | GO_TO | FOLLOW | RETURN_HOME | LAND | PATROL
```

Use `str` Enum (project style).

### 2.2 `AutonomyCommand`

| Field | Notes |
|---|---|
| `id` | uuid/str |
| `verb` | `AutonomyVerb` |
| `intent_id` | optional str (trace to C2 Intent) |
| `params` | optional `dict[str, str]` default `{}` — opaque; no actuator blob |
| `created_at` | optional ISO timestamp |

`extra="forbid"` if Pydantic.

### 2.3 `AutonomySubmissionResult`

| Field | Notes |
|---|---|
| `command_id` | str |
| `verb` | AutonomyVerb |
| `safety` | `SafetyDecision` (embedded or mirrored fields) |
| `execution` | Literal `"not_attempted"` \| `"not_implemented"` — **C4 lock: never `"executed"`** under any shipped path |

When Safety rejects (default): `execution` must be `"not_attempted"` (preferred) or `"not_implemented"`.

### 2.4 Surface API

```text
propose_command(verb: AutonomyVerb, *, intent_id: str | None = None,
                params: dict[str, str] | None = None) -> AutonomyCommand
  # pure constructor helper — does not call Safety

submit_command(command: AutonomyCommand, gate: SafetyGate) -> AutonomySubmissionResult
  # 1) build SafetyRequest(intent_id=command.intent_id, action_id=f"autonomy:{command.verb}:{command.id}")
  # 2) decision = gate.evaluate(request)
  # 3) if decision.outcome != "allow": return result with that safety + execution="not_attempted"
  # 4) if decision.outcome == "allow":  # only reachable with a test-local fake gate
  #       still MUST NOT actuate — return execution="not_implemented"
  #       (optional: reason note in result; do not add AllowAll to src/)
```

**Lock:** there is **no** shipped function named like `execute_hold` / `run_land` / `dispatch_autonomy` that skips Safety.

### 2.5 Optional smoke helper

```text
smoke_hold_and_land(gate: SafetyGate | None = None) -> list[AutonomySubmissionResult]
  # proposes HOLD then LAND; submits each via default_safety_gate() if gate is None
  # asserts both results are reject / not_attempted
```

Place under `autonomy/smoke.py` or tests-only — if shipped in `src/`, must use RejectAll by default.

---

## 3. Integration rules (C1–C3)

| Existing | C4 rule |
|---|---|
| `RejectAllSafetyGate` / `default_safety_gate()` | **Unchanged** — still the only shipped factory |
| `flight_control` HAL/IMU | **Unchanged** — autonomy must not call `read_imu` as a fake “hold” |
| `vehicle_profiles` | Untouched unless a one-line doc cross-ref; no new profile required |
| Capability registry | Stays empty by default |
| Craft / orchestrator | Zero imports of `jarvis.flight_software.autonomy` |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `propose_command(HOLD)` → `AutonomyCommand` with verb HOLD |
| T2 | `submit_command(..., default_safety_gate())` → safety.outcome `reject`, execution `not_attempted` (or locked `not_implemented`) |
| T3 | Same for `LAND` |
| T4 | Every `AutonomyVerb` member can be proposed (constructs without error) |
| T5 | No public method under `autonomy/` whose name contains `pwm`/`esc`/`motor`/`mixer`/`arm`/`actuat` |
| T6 | `AllowAllSafetyGate` still absent from `src/`; default gate still reject |
| T7 | With a **test-local** fake gate that returns `allow`, `submit_command` still returns `execution != "executed"` (must be `not_implemented`) |
| T8 | `CapabilityRegistry.load_default()` still empty |
| T9 | `pyproject` version **`0.5.2`**; re-pin prior `0.5.1` pins |
| T10 | Zero imports of `jarvis.flight_software.autonomy` from `core/` / `adapters/` |
| T11 | No new `.cpp`/CMake under `flight_software/` / `vehicle_profiles/` (extend C3 guard or duplicate) |
| T12 | Full suite green |
| T13 | Report confirms H-locks + “surface ≠ live autonomy” + C++ FC honesty |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| `execution="executed"` on any shipped path | Would fake autonomy |
| Default Safety `allow` | Would fake authority |
| Skipping Safety on submit | Breaks C0 chain |
| Calling SimulatedImuHal as “holding” | Wrong layer / fake behavior |
| CLI/Board “land now” wiring | Scope |
| Marking autonomy capability available | C1 honesty |
| C++/CMake tree | C3 amendment continues |

---

## 6. Docs

- PRIORIDAD: C4 in flight / CLOSED as appropriate  
- PLATFORM §13: C4 block — command surface stub; still RejectAll  
- ARCHITECTURE: short §1d (or extend §1c) for `flight_software/autonomy/`  
- README “What v0.5.2 includes” when bumped  

---

## 7. Acceptance

**PASS when:** T1–T13 · HOLD/LAND submit always reject under default gate · no `executed` · no craft coupling · version `0.5.2` · FC rung unchanged · no C++ tree.

**FAIL if:** anything flies / arms / writes PWM · AllowAll in `src/` · Intent wired from CLI · autonomy skips Safety.

---

## 8. Handoff

```text
Engineer → ★ this IC (C4)
Claude   → implement autonomy/ + tests + report + 0.5.2
Cursor   → review
Engineer → ACCEPT + tag v0.5.2
Cursor   → C5 IC (Radio/ELRS Authority+Intent) when Engineer prioritizes
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C3 ACCEPT @ v0.5.1. C4 B1-fase-c-autonomy-surface READY —
HOLD/LAND/… typed commands behind RejectAll Safety; Python scaffold only.
```

---

## 10. Engineer ★ checklist (optional amendments)

1. Version **`0.5.2`** OK? (alt: stay `0.5.1`)  
2. Full C0 verb enum OK, with HOLD+LAND required in tests?  
3. Confirm: even a test-local `allow` must **not** set `execution="executed"` in C4  
4. No CLI wiring OK?  
