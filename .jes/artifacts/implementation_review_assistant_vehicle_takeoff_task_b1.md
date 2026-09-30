# Implementation Review — Assistant vehicle TAKEOFF Task (`B1-assistant-vehicle-takeoff-task`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_assistant_vehicle_takeoff_task_b1.md) · [report](implementation_report_assistant_vehicle_takeoff_task_b1.md) · [DC ★](design_contract_assistant_vehicle_takeoff_task_b0.md)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS**. Package/tag **`0.6.17` / `v0.6.17`**.

**Review format (Engineer lock):** (1) what landed · (2) where it leaves us · (3) how it adds to the path.

---

## 1. Qué aterrizó (what landed)

Fourth vehicle Task kind — same seam as HOLD/LAND/GO_TO:

| Layer | What |
|---|---|
| Classify | `VEHICLE_TAKEOFF_PHRASES` (9) + `try_request_takeoff_task` → `flight.takeoff` |
| Guards | Refuses explain · Continuity · HOLD · LAND · GO_TO |
| Fulfill | `_handle_vehicle_takeoff` sibling; prior fulfill bodies untouched; `params={}` |
| UX | `vehicle_takeoff` · `reject`/`disarmed`/`not_attempted` — never airborne |
| Registry | `flight.takeoff` `not_implemented` · separate `provider.flight_takeoff` · skill stub |
| Safety honesty | Allow-list still `{HOLD,LAND,GO_TO}` — TAKEOFF not widened (gate B path unchanged) |
| Precedence | explain → defer → HOLD → LAND → GO_TO → **TAKEOFF** → fallthrough |

Package **`0.6.17`**. Cascade → 6 skills. RETURN_HOME / `arm()` out (T10 queued).

---

## 2. Cómo se verificó (independent)

1. IC §0 vs config / classify / fulfill / registry.  
2. Live: `despegar` → `vehicle_takeoff` + disarmed reject; HOLD/LAND/GO_TO intact.  
3. `_ALLOWED_VERBS` still excludes TAKEOFF; no `.arm(`; no software Safety in classify.  
4. Prior fulfill through-return bodies unchanged vs `v0.6.16`.  
5. Pytest: TAKEOFF+GO_TO+HOLD+LAND **32/32**.  
6. Docs: no new C-xxx; T10 queue left.

---

## 3. IC checklist — all **PASS** (T1–T8)

---

## 4. Dónde nos deja

```text
Chat verbs: HOLD · LAND · GO_TO · TAKEOFF  (all honest Safety reject)
Missing for basic mando set: RETURN_HOME (T10)
```

---

## 5. Cómo suma

Cierra el par TAKEOFF↔LAND en el Tasker. Queda RTL para el set de mando Vision.

---

## 6. Notes (non-blocking)

**N1 — Allow-list.** Correct to leave TAKEOFF out of `_ALLOWED_VERBS` this Buy; document for future `arm()` Buy.

---

## 7. Next

```text
DONE — T9 ★ ACCEPT CLOSED @ v0.6.17
Next: T10 RETURN_HOME — DC ★ CLOSED + IC ★ AUTHORIZED (same Engineer turn)
```

**ACCEPT by Engineer.**
