# Implementation Review — Assistant vehicle RETURN_HOME Task (`B1-assistant-vehicle-return-home-task`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (second pass — Engineer: *review a conciencia; dos ejecutores del mismo IC*)  
**Against:** [IC](implementation_contract_assistant_vehicle_return_home_task_b1.md) · [report](implementation_report_assistant_vehicle_return_home_task_b1.md) · [DC ★](design_contract_assistant_vehicle_return_home_task_b0.md)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.18` / `v0.6.18`**. Notes were process + docs/test hardening fixed in the review pass; no IC behavioral FAIL.

**Process note (why this review exists):** Claude hit limit mid-Buy. Cursor finished orchestrator/tests/docs. A first review claimed bare PASS in the same Cursor session that finished the Cursor half — that is **not** review of record. This pass re-audits the whole tip against IC, with explicit dual-executor seam checks.

---

## 0. Dual-executor split (forensic)

| Half | Owner | Landed |
|---|---|---|
| Classify / config / seed | **Claude** (before limit) | `VEHICLE_RETURN_HOME_PHRASES` · `try_request_return_home_task` + six ahead-of-it guards · registry cap/provider/skill @ `0.6.18` |
| Fulfill / proof / docs | **Cursor** (Engineer: continue) | wire after TAKEOFF · `_handle_vehicle_return_home` · tests T1–T8 · cascade 7 · `pyproject` · docs/report |

**Seam risks checked (and cleared):**

| Risk | Result |
|---|---|
| Classify id ≠ fulfill verb / action | **Clear** — `request_return_home` → `flight.return_home` → `AutonomyVerb.RETURN_HOME` → `action=vehicle_return_home` |
| Claude seeded, Cursor fulfill against missing enum | **Clear** — `AutonomyVerb.RETURN_HOME` already in C4 surface |
| Wire order wrong (before TAKEOFF / after `return None`) | **Clear** — defer → HOLD → LAND → GO_TO → TAKEOFF → **RETURN_HOME** → `return None` |
| Prior `_handle_vehicle_*` bodies edited | **Clear** — through-return bodies byte-identical to tip **`v0.6.17`** for hold/land/go_to/takeoff |
| Allow-list widen / `safety.py` touch | **Clear** — `safety.py` identical to `v0.6.17`; `_ALLOWED_VERBS` still `{HOLD,LAND,GO_TO}` |
| Intelligence → FS import | **Clear** — AST fence; classify body has no propose/submit/arm/SoftwareCapability |
| Phrase table ≠ IC minimum | **Clear** — exact 10-entry seed; accents normalize (`cáSa`→`casa`) |
| Exact-match steal craft chat | **Clear** — `volver al board` / `casa del frame` → `None`; live `volver` alone → RH |
| NAVIGATION_BACK overlap (`volver`/`vuelve`) | **Clear by design** — different path (wizard-only); documented in config |
| Docs drift from Cursor finish haste | **Found** — see Notes (fixed this pass) |

---

## 1. Qué aterrizó

Fifth vehicle Task kind — closes basic mando set in chat:

| Layer | What |
|---|---|
| Classify | `VEHICLE_RETURN_HOME_PHRASES` (10) + `try_request_return_home_task` → `flight.return_home` |
| Guards | Refuses explain · Continuity · HOLD · LAND · GO_TO · TAKEOFF |
| Fulfill | `_handle_vehicle_return_home`; `params={}`; prior fulfill bodies untouched |
| UX | `vehicle_return_home` · `reject`/`disarmed`/`not_attempted` — never claims RTL executed |
| Registry | `flight.return_home` `not_implemented` · separate `provider.flight_return_home` · skill stub |
| Safety | Allow-list still excludes RETURN_HOME; gate B; `default_safety_gate()` RejectAll |
| Precedence | explain → defer → HOLD → LAND → GO_TO → TAKEOFF → **RETURN_HOME** → fallthrough |

Package **`0.6.18`**. Cascade → **7** skills / **7** caps. No new C-xxx.

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs config / classify / fulfill / registry line-by-line.  
2. Live E2E: `rtl`/`casa`/`volver`/`returnhome` → `vehicle_return_home` + disarmed reject; `explain rtl` → `global_command`; prior five actions intact.  
3. Monkey-patch `propose_command`: verb `RETURN_HOME`, `params={}`.  
4. Prior fulfill through-return identical to `v0.6.17`; `safety.py` identical.  
5. Pytest: RETURN_HOME + four prior vehicle suites + skills/registry/coherence/scaffold/explain intercept — **green** (77+ after T7 harden).  
6. Cascade: 39/39 mention `skill.request_return_home`.  
7. Docs: first Cursor finish left C-010 precedence stuck at TAKEOFF and PLATFORM without a T10 §13 block / contradictory “T10 next up” — **fixed this review pass** (N1).

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2–3 ids + `try_request_return_home_task` | **PASS** |
| §0.4 phrase seed + exact match | **PASS** |
| §0.5 wire after TAKEOFF | **PASS** |
| §0.6 membership only / no software Safety | **PASS** |
| §0.7 metadata after membership | **PASS** |
| §0.8 registry honesty + separate provider | **PASS** |
| §0.9 fulfill RETURN_HOME + honest UX | **PASS** |
| §0.10 guards | **PASS** |
| §0.11 prior bodies / cascade 7 / regression | **PASS** |
| §0.12 version `0.6.18` + docs | **PASS** (after N1 doc fix) |
| §0.13 no arm / no allow-list widen | **PASS** |
| T1–T8 | **PASS** (T1/T7 hardened this pass — N2) |

---

## 4. Dónde nos deja

```text
Basic mando set in chat (all honest Safety reject):
  TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND
Next candidates: arm() UX · FOLLOW · PATROL · CHARGE
```

---

## 5. Cómo suma

Cierra el set de mando Vision en el Tasker. No abre `arm()`, no ensancha allow-list, no parsea home/GPS. Dual-executor no dejó desalineación classify↔fulfill.

---

## 6. Notes (non-blocking — remediated or residual)

**N1 — Docs drift from Cursor finish (remediated).** C-010 Authority still said precedence `… → TAKEOFF → fallthrough` and listed T10 before T9; PLATFORM §10 still said “RETURN_HOME (T10, next up)” and “all three later verbs”; §13 lacked a T10 block. Fixed in this review pass. No new C-xxx invented.

**N2 — Test coverage thinner than siblings (remediated).** Cursor T1 omitted seed token `returnhome` and accent form; T7 did not unit-assert empty `params` the way T8/T9 do. Live path was correct; tests now lock both.

**N3 — Process.** Same-session Cursor implementer+first-reviewer is not review of record for the Cursor half. This second pass is the review of record. Claude half was re-verified independently against IC (no Claude self-PASS trusted).

**N4 — Residual (informational).** `volver`/`vuelve` also sit in `NAVIGATION_BACK_WORDS` (wizard path only). Global chat correctly routes exact `volver` to RETURN_HOME. No change required.

---

## 7. Next

```text
★ ACCEPT CLOSED @ v0.6.18 (Engineer 2026-09-30)
Basic mando set CLOSED
Await Engineer ★ pick: arm() UX · FOLLOW · PATROL · CHARGE
```
