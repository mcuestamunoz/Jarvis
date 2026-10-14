# Implementation Review — Assistant chat ArmedAllowlist widen (`B1-assistant-vehicle-allowlist-widen`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (independent pass — Engineer pasted Claude T14 push summary)  
**Against:** [IC](implementation_contract_assistant_vehicle_allowlist_widen_b1.md) · [report](implementation_report_assistant_vehicle_allowlist_widen_b1.md) · [DC ★](design_contract_assistant_vehicle_allowlist_widen_b0.md)  
**Tip reviewed:** `a0964e8` on `cursor/allowlist-widen-impl-8ac5` (parent tip T16 ★ `v0.6.24` / `8e2ad8f`)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.25` / `v0.6.25`**.

**Process note:** Claude Code implemented. Same-session implementer green is not review of record. This pass re-audits the tip against IC §0 locks with live E2E + pytest.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Incomplete widen (still missing a chat verb) | **Clear** — frozenset is exactly the seven `AutonomyVerb` chat values |
| `allow` claims / becomes execute | **Clear** — armed submit → `not_implemented`; never `"executed"`; `SimAutonomyExecutor` absent from orchestrator |
| Sim executor widened / wired from chat | **Clear** — sim `_SUPPORTED_VERBS` still HOLD/LAND/GO_TO; orch has no `SimAutonomyExecutor` |
| Disarmed path regresses | **Clear** — still `reject`/`disarmed` |
| Arm UX copy still says TAKEOFF/RH `verb_not_allowed` | **Clear** — `_handle_arm_policy` lists all seven → allow/not_implemented |
| New Task / phrase / cap / skill | **Clear** — cascade still 10/11; `config.py` untouched |
| Prior suites left asserting old allow-list | **Clear** — vehicle/arm + C17/C41 probes retargeted (CHARGE for `verb_not_allowed`) |
| Historical tip-pin mass rewrite | **Clear** — parked `0.5.x` pins still red; count unchanged at 52 |
| Stale fulfill-method docstrings still say “excludes … verb_not_allowed” | **Found** — informational (N1); IC forbade fulfill-body rewiring |

---

## 1. Qué aterrizó

| Layer | What |
|---|---|
| Safety | `_ALLOWED_VERBS` → seven chat AutonomyVerbs; docstring honesty (allow ≠ execute) |
| Orchestrator | arm-policy Spanish copy only |
| Registry | `safety.chat_armed_allowlist` version `0.6.25` |
| Tests | new T1–T8 + retargeted vehicle/arm + C17/C41 CHARGE probes |
| Package | **`0.6.25`** |

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs `safety.py` / arm message / registry / orch sim-scan.  
2. Live E2E: `armar` then takeoff/rtl/follow/patrol/hold → `allow`/`not_implemented`; `desarmar` then patrol → `disarmed`; armed gate rejects `autonomy:CHARGE:…` with `verb_not_allowed`.  
3. Pytest: new widen + eight vehicle/arm suites — **all green**; C17/C41 suites green except parked historical version pins.  
4. Scope: no `config.py` / `sim_executor.py` edits; fulfill bodies byte-stable aside from arm-policy copy.

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2 seven-verb frozenset | **PASS** |
| §0.3 docstring / no ESC / no sim coupling | **PASS** |
| §0.4 latch API / shared gate construction unchanged | **PASS** |
| §0.5 armed → allow/not_implemented for all seven | **PASS** |
| §0.6 disarmed unchanged | **PASS** |
| §0.7 arm-policy copy | **PASS** |
| §0.8 cascade 10/11 + optional version bump | **PASS** |
| §0.9 tests T1–T8 + prior suite retarget | **PASS** (incl. C17/C41 CHARGE probes — N2) |
| §0.10 version `0.6.25` + docs | **PASS** |
| §0.11 CHARGE / copper / tip pins / FN-016 out | **PASS** |

---

## 4. Dónde nos deja

```text
After armar: HOLD…PATROL → allow/not_implemented (chat)
Sim / copper / CHARGE still later
Next candidates: CHARGE · copper · tip-pin cleanup
```

---

## 5. Cómo suma

El latch de T11 deja de mentir a medias: armar el chat ahora implica la misma clase de Safety `allow` para todo el mando verbal expuesto, sin fingir ejecución.

---

## 6. Notes

**N1 — Stale fulfill docstrings (informational).** `_handle_vehicle_takeoff` / `_follow` / `_patrol` (and some intercept comments) still say allow-list excludes those verbs. IC locked “no fulfill rewiring”; arm-policy user-facing copy is correct. Optional polish later — not blocking ACCEPT.

**N2 — C17/C41 CHARGE probes.** Correct real retarget: with no excluded `AutonomyVerb` left, `verb_not_allowed` probes use `CHARGE` (never a chat Task / never in allow-list). Matches IC “retarget prior suites” spirit beyond the named vehicle files.

**N3 — Process.** Claude implementer green ≠ review of record. Engineer ★ ACCEPT still required for tag `v0.6.25`.

---

## 7. Next

```text
★ ACCEPT CLOSED @ v0.6.25 (Engineer 2026-10-01)
T17 tip-pin cleanup ★ ACCEPT CLOSED @ v0.6.26 (same tip chain)
Next candidates: CHARGE · copper · N1 fulfill docstring polish · Skills runtime
```
