# Implementation Review — Assistant vehicle HOLD Task (`B1-assistant-vehicle-hold-task`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_assistant_vehicle_hold_task_b1.md) · [report](implementation_report_assistant_vehicle_hold_task_b1.md) · [DC ★](design_contract_assistant_vehicle_hold_task_b0.md)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS**. Package/tag **`0.6.14` / `v0.6.14`**.

**Review format (Engineer lock):** (1) what landed · (2) where it leaves us · (3) how it adds to the path.

---

## 1. Qué aterrizó (what landed)

First **vehicle** Assistant Task kind, end-to-end without claiming flight:

| Layer | What |
|---|---|
| Classify | `VEHICLE_HOLD_PHRASES` + `try_request_hold_task` → `Task(request_hold)` / `flight.hold` |
| Membership | T3-style only — **no** `SoftwareCapabilitySafetyGate` (correct: cap is `not_implemented`+`vehicle`) |
| Fulfill | Orchestrator `_handle_vehicle_hold`: `propose_command(HOLD)` + `submit_command` via **fresh, never-armed** `ArmedAllowlistSafetyGate` |
| UX | Spanish message surfaces `reject` / `disarmed` / `not_attempted` — never `executed` |
| Registry | `flight.hold` (`not_implemented`) · `provider.flight_hold` (`vehicle`) · `skill.request_hold` (`stub`) |
| Precedence | explain → Continuity defer → HOLD → fallthrough (orchestrator order + classify guards) |
| Fence | `assistant_task` still no `flight_software` / `vehicle_profiles` / `jarvis.core`; FS import lives only in orchestrator fulfill |

Package **`0.6.14`**; no premature tag. LAND/GO_TO / `arm()` / `default_safety_gate` change all out (held).

Cascade: 39 Fase C skill-id asserts extended to three stubs; T2/T5/C1/C4/C41 “own” boundary tests scoped or allow-listed **`core/orchestrator.py` only** — isolation otherwise intact.

---

## 2. Cómo se verificó (independent)

1. Re-read IC §0 vs `config.py` / `assistant_task.try_request_hold_task` / `orchestrator._handle_vehicle_hold` / `default_registry.json`.  
2. Function-body check: classify body has **zero** `_software_safety` / `SoftwareCapabilitySafetyGate`; fulfill body has **zero** `.arm(`; constructs `ArmedAllowlistSafetyGate()`.  
3. Live `handle_user_text('hold', exploding LLM)` →  
   `action=vehicle_hold`, message contains `reject` / `disarmed` / `not_attempted`.  
4. `default_safety_gate()` still `RejectAllSafetyGate`; seed honesty as T5 asserts.  
5. Pytest: T6 **8/8**; with T0–T5 + C4/C41-related suites **58 passed**, only pre-existing stale `0.5.x` version checkpoints failed (out of scope).  
6. Docs: PLATFORM §10/§12/§13 · CONNECTIONS T6 note + C-010 extend · **no new C-xxx** · intelligence README T6 · PRIORIDAD.

**N1 (non-blocking):** `intelligence/__init__.py` does not re-export `try_request_hold_task` — same pattern as prior Task kinds (docstring notes package `__all__` stays narrow). Not an IC miss.

---

## 3. IC checklist

| Lock | Verdict |
|---|---|
| §0.2–0.4 Kind / phrases / `try_request_hold_task` | **PASS** |
| §0.5 Precedence after defer, before fallthrough | **PASS** |
| §0.6 Membership only — no software Safety gate | **PASS** |
| §0.7 Metadata after membership | **PASS** |
| §0.8 Registry honesty (`not_implemented` / vehicle / stub) | **PASS** |
| §0.9 Fulfill disarmed ArmedAllowlist · honest UX | **PASS** |
| §0.10 AST fence · cascade adapted not weakened | **PASS** |
| §0.11 Package `0.6.14` · docs · no new C-xxx | **PASS** |
| §0.12 LAND/GO_TO out | **PASS** |
| Tests T1–T8 | **PASS** (8/8) |

---

## 4. Dónde nos deja (where we are now)

```text
Chat/CLI HOLD phrase
  → Intent → try_request_hold_task (membership)
  → orchestrator._handle_vehicle_hold
  → propose_command(HOLD) + submit_command(disarmed ArmedAllowlist)
  → honest Safety reject (disarmed) / not_attempted

Registry @ 0.6.14
  software: ontology.explain, engineering.continuity (+ 2 stub skills)
  vehicle:  flight.hold not_implemented (+ skill.request_hold stub)

Still absent (by design):
  arm() UX · LAND · GO_TO · executed flight · Skill runner
```

Vision §10’s Safety→Flight Control link is now a **real code path** that stops honestly at Safety.

---

## 5. Cómo suma al camino (how it adds)

| Antes (T5) | Después (T6) |
|---|---|
| Catálogo software + Skills stub; Task path solo software | Primer verbo **vehicle** en el Tasker |
| `core` no tocaba `flight_software` | Un solo edge autorizado: orchestrator → C4 surface |
| Vision HOLD era diagrama | HOLD chat → Safety reject medible |
| Fence “intelligence ↛ FS” teórico para vehículo | Fence **probado**: classify en intelligence, fulfill en core |

Esto abre el patrón para LAND/GO_TO (Buys aparte): misma mesa de frases + membership + fulfill con política de arm explícita — sin reabrir el catálogo software ni el gate T4.

---

## 6. Notes (non-blocking)

**N1 — `__init__` exports.** Consistent with T0/T1; package `__all__` unchanged.  
**N2 — Phrase table.** Accented forms (`mantén`, `quédate`, `posición`) normalize onto the six stored entries — matches IC “pre-normalized” lock.  
**N3 — Cascade allow-lists.** Identity compare to `orchestrator.py` (not substring) — correct discipline; keep that pattern for later verbs.

---

## 7. Next

```text
DONE — T6 ★ ACCEPT CLOSED @ v0.6.14
Next: T7 vehicle LAND — DC ★ CLOSED + IC ★ AUTHORIZED (same Engineer turn)
```

**ACCEPT by Engineer.**
