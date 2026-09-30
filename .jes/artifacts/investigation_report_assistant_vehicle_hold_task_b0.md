# Investigation Report — Assistant vehicle HOLD Task seam (`INV-assistant-vehicle-hold-task`)

**Date:** 2026-09-30  
**Investigator:** Cursor (read-only)  
**Against:** [INV contract](investigation_contract_assistant_vehicle_hold_task_b0.md)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — proceed DC+IC HOLD. Gate policy locked as **B** (ArmedAllowlist disarmed by default).  
**No `src/` changed.**

---

## 1. Qué aterrizó esta investigación

Mapa de enganches reales para un primer Task `request_hold` / HOLD, con fences y opciones de honesty. Conclusión: el código FS/Safety **ya existe**; falta el **puente Assistant → orchestrator → surface** sin romper el fence `intelligence ↛ flight_software`.

---

## 2. Respuestas Q1–Q8

### Q1 — Call chain HOLD hoy

```text
propose_command(AutonomyVerb.HOLD)           # types/surface — no Safety
  → AutonomyCommand
submit_command(command, gate)                # surface.py
  → SafetyRequest(action_id="autonomy:HOLD:{command.id}")
  → gate.evaluate(...)
  → if reject: execution="not_attempted"
  → if allow:  execution="not_implemented"   # NEVER "executed" in shipped src/
```

| Gate | HOLD result |
|---|---|
| `default_safety_gate()` → `RejectAllSafetyGate` | reject / `not_attempted` (smoke_hold_and_land) |
| `ArmedAllowlistSafetyGate` + `arm()` | allow / `not_implemented` (smoke_policy_gate_hold_and_land) |
| Disarmed ArmedAllowlist | reject / `disarmed` |

**Orchestrator:** zero references to `submit_command` / ArmedAllowlist today — HOLD no está en el chat path.

**Citations:** `flight_software/autonomy/surface.py`, `types.py`, `smoke.py`, `capabilities/safety.py` (`ArmedAllowlistSafetyGate`).

### Q2 — Dónde clasifica el Assistant

**Recommend:** extend `assistant_task.py` with `try_request_hold_task` (same grain as explain/defer) + finite phrase table in `jarvis.config` (e.g. `HOLD_DEFER_PHRASES` / `VEHICLE_HOLD_PHRASES`).

Do **not** create a second brain in orchestrator; orchestrator only: Intent → try_* → fulfill helper.

### Q3 — Registry honesty

| Record | Recommendation |
|---|---|
| Capability `flight.hold` | `availability: not_implemented` (or `stub`) — **never** `available` |
| Provider | `kind: vehicle` (or software stub provider that does **not** claim copper) — prefer **vehicle** + honest non-available cap |
| Skill `skill.request_hold` | `stub`, `required_capability_ids: ["flight.hold"]` |

SoftwareCapabilitySafetyGate must **not** allow this path (it requires `available` + software provider).

### Q4 — Which Safety on Assistant HOLD path

| Option | Pros | Cons |
|---|---|---|
| A. Always `default_safety_gate()` (RejectAll) | Max honesty tip; UX always reject | No exercise of ArmedAllowlist from chat |
| B. `ArmedAllowlistSafetyGate` **disarmed** by default | Same UX reject (`disarmed`); real gate type | Need product policy for who arms |
| C. Armed in tip | Demuestra allow→`not_implemented` | Fácil malinterpretar como “HOLD listo” |

**Recommend for first IC:** **B** (or A) — chat HOLD → Task → Safety reject honest message; optional test-only armed path like existing smoke. **Do not** change `default_safety_gate()` factory.

### Q5 — Who fulfills (import fence)

**Critical:** `assistant_task` **must not** import `jarvis.flight_software` (existing AST fence).

```text
intelligence: classify → Task(request_hold, required=["flight.hold"])
     ↓ (no FS import)
orchestrator (or thin core helper):
     propose_command(HOLD) + submit_command(gate)
     → format message from AutonomySubmissionResult
```

Registry/Safety for vehicle: gate evaluate may live in core fulfill (passing ArmedAllowlist or RejectAll), not inside intelligence. Intelligence may still do **registry membership** for `flight.hold` (T3-style) but **not** SoftwareCapabilitySafetyGate allow (would always fail / wrong gate).

**Recommend:** membership check that id exists; Safety **only** in core fulfill via autonomy surface (surface already calls gate). Avoid double-gating confusion: either (1) Task emit after membership only, Safety inside `submit_command`, or (2) document two layers clearly. Prefer **(1)** — mirrors C4 design (Safety at submit).

### Q6 — Precedence

```text
explain → Continuity defer → HOLD → fallthrough
```

HOLD must not steal explain/status phrases.

### Q7 — Minimal first IC vs later

**First IC (after DC):**

- Phrases + `try_request_hold_task`
- Seed `flight.hold` + skill stub
- Orchestrator wire → `propose`/`submit` + honest message (reject or not_implemented)
- Tests: classify, fence AST, no execution, precedence
- Package bump (likely `0.6.14` after T5 `0.6.13` ACCEPT)

**Later Buys:** LAND, GO_TO, arm UX, sim executor tick from chat, voice ingress, marking anything `available`.

### Q8 — Artifact sequence

```text
DONE: INV report (this)
NEXT: DC-assistant-vehicle-hold-task (locks kind/cap/gate/fulfill/UX honesty)
THEN: IC ★ AUTHORIZED → Claude
```

---

## 3. Dónde nos deja

| Pieza | Estado |
|---|---|
| FS HOLD surface | **Listo** (C4) |
| ArmedAllowlist HOLD | **Listo** (C17) |
| Assistant → HOLD | **Ausente** |
| Orchestrator → submit_command | **Ausente** |
| Registry flight.hold | **Ausente** |

Riesgo no era “¿dónde está HOLD?” sino **cómo cruzar el fence** intelligence/FS y **qué honesty de Safety/UX** fijar en tip.

---

## 4. Cómo suma al camino

Tras T5 (Skills software stub), el siguiente piso Vision es **PHYSICAL / drone**. Esta INV confirma que no inventamos FS: solo abrimos el **Tasker** hacia una superficie que ya niega execute. HOLD es el **primero de muchos** verbos; el DC debe decir explícitamente “LAND/GO_TO = Buys aparte”.

---

## 5. Recommendation to Engineer — ★ DONE (same turn)

1. ★ ACCEPT INV — **done** (gate **B** locked).  
2. DC + IC HOLD AUTHORIZED — **done** (same Engineer turn).  
3. T5 ACCEPT/tag **`v0.6.13`** — **done** this turn.
