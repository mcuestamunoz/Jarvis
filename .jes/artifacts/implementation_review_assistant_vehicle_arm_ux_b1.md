# Implementation Review — Assistant vehicle Safety arm UX (`B1-assistant-vehicle-arm-ux`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent pass — Engineer: *Revisa y si es todo correcto accept con tag*)  
**Against:** [IC](implementation_contract_assistant_vehicle_arm_ux_b1.md) · [report](implementation_report_assistant_vehicle_arm_ux_b1.md) · [DC ★](design_contract_assistant_vehicle_arm_ux_b0.md)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.19` / `v0.6.19`**.

**Process note:** Cursor implemented (Engineer “implementa tú”). Same-session implementer self-PASS is not review of record. This pass re-audits the tip against IC §0 locks with live E2E + pytest.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Classify ids ≠ fulfill actions | **Clear** — `request_arm_policy`/`request_disarm_policy` → `vehicle_arm_policy`/`vehicle_disarm_policy` |
| ARM uses vehicle membership-only path | **Clear** — T3 membership **and** T4 `SoftwareCapabilitySafetyGate` |
| Fresh gate per vehicle fulfill (pre-T11 bug) | **Clear** — only lazy `_vehicle_chat_safety_gate()` singleton; five fulfills retargeted |
| `gate.arm()` inside HOLD/LAND/GO_TO/TAKEOFF/RH | **Clear** — arm/disarm only in `_handle_arm/disarm_policy` |
| Allow-list widen / `safety.py` touch | **Clear** — `safety.py` identical to `v0.6.18`; `_ALLOWED_VERBS` still `{HOLD,LAND,GO_TO}` |
| Intelligence → FS / core import | **Clear** — AST fence T9 |
| Exact-match steal craft chat | **Clear** — `arma el frame` → classify `None`; falls through (no arm action) |
| Accent seed (`armar política`) | **Clear** — normalizes onto `armar politica` |
| Wire order wrong | **Clear** — explain → defer → **ARM** → **DISARM** → HOLD → … → RETURN_HOME |
| Cascade counts | **Clear** — **8** caps / **9** skills |
| Stale wire comments (“fresh never-armed”) | **Found** — remediated this pass (N1) |

---

## 1. Qué aterrizó

| Layer | What |
|---|---|
| Config | `VEHICLE_ARM_PHRASES` · `VEHICLE_DISARM_PHRASES` (finite, accent-free) |
| Classify | `try_request_arm/disarm_policy_task` → `safety.chat_armed_allowlist` via T4 software Safety |
| Guards | Refuse explain · Continuity · each other · five vehicle phrase tables |
| Fulfill | Shared gate `arm()`/`disarm()`; honest software-latch Spanish; never ESC/motors |
| Retarget | Five vehicle fulfills submit through `_vehicle_chat_safety_gate()` |
| Registry | cap `available` + software provider + 2 skill stubs @ `0.6.19` |
| Safety | Allow-list unwidened; after ARM: HOLD/LAND/GO_TO → allow/not_implemented; TAKEOFF/RH → verb_not_allowed |
| Precedence | explain → defer → **ARM** → **DISARM** → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME |

Package **`0.6.19`**. No new C-xxx. No AutonomyVerb for arm.

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs config / classify / fulfill / registry / safety.py line-by-line.  
2. Live E2E: default `hold`→disarmed; `armar`→armed + honest message; `hold`/`land`/`go to`→allow/not_implemented; `takeoff`/`rtl`→verb_not_allowed; `desarmar`→hold disarmed again; `armar política` accent; `arma el frame` not stolen; `explain imu` intact.  
3. Shared gate identity: repeated `_vehicle_chat_safety_gate()` returns same instance; only one `ArmedAllowlistSafetyGate()` construction site.  
4. Pytest targeted: arm_ux + five vehicle + T4 + skills + coherence — **72 passed**.  
5. Cascade: registry `8` caps / `9` skills; `safety.py` diff vs `v0.6.18` empty.  
6. Docs/PRIORIDAD/PLATFORM/CONNECTIONS/USER_GUIDE/intelligence README present; ACCEPT close updated this pass.

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2–3 ids + try_* | **PASS** |
| §0.4 phrase seed + exact match + accents | **PASS** |
| §0.5 wire after defer, before HOLD | **PASS** |
| §0.6 T3+T4 software Safety; refuse priors | **PASS** |
| §0.7 metadata after Safety allow | **PASS** |
| §0.8 registry honesty + prior rows kept | **PASS** |
| §0.9 shared gate + honest ARM/DISARM UX | **PASS** |
| §0.10 five fulfills retargeted; no arm in them | **PASS** |
| §0.11 allow-list unwidened; verb_not_allowed surfaced | **PASS** |
| §0.12 AST fence | **PASS** |
| §0.13 cascade 8/9 + prior suites green | **PASS** |
| §0.14 version `0.6.19` + docs | **PASS** (ACCEPT close this pass) |
| §0.15 FOLLOW / widen / sim / copper out | **PASS** |
| T1–T10 | **PASS** |

---

## 4. Dónde nos deja

```text
Basic mando set + Safety arm UX latch:
  ARM/DISARM (software latch) · TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND
Next candidates: FOLLOW · PATROL · allow-list widen · CHARGE
```

---

## 5. Cómo suma

Cierra “quién arma” del chat sin abrir ESC/motores ni ensanchar allow-list. El latch compartido hace que HOLD/LAND/GO_TO puedan demostrar `allow`/`not_implemented` de forma honesta; TAKEOFF/RETURN_HOME siguen `verb_not_allowed` hasta un Buy explícito.

---

## 6. Notes

**N1 — Stale wire comments (remediated).** LAND/GO_TO/TAKEOFF/RETURN_HOME intercept comments still said “fresh, never-armed ArmedAllowlistSafetyGate” after T11 retarget. Fulfill bodies were already correct; comments updated this ACCEPT pass.

**N2 — Process.** Engineer authorized Cursor implement + this review/ACCEPT. Review of record is this pass (not the implementer session’s informal green).

**N3 — Residual (informational).** Pre-existing tip pin `test_assistant_terminal_canal_b1` still expects `0.6.3` — not owned by this Buy (IC only bumps stale `0.6.18` checkpoints).

---

## 7. Next

```text
★ ACCEPT CLOSED @ v0.6.19 (Engineer 2026-09-30)
Await Engineer ★ pick: FOLLOW · PATROL · allow-list widen · CHARGE
```
