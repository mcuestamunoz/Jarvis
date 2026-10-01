# Implementation Review — Assistant chat → sim copper (`B1-assistant-chat-sim-copper`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (independent pass — Engineer pasted Claude T20 push summary)  
**Against:** [IC](implementation_contract_assistant_chat_sim_copper_b1.md) · [report](implementation_report_assistant_chat_sim_copper_b1.md) · [DC ★](design_contract_assistant_chat_sim_copper_b0.md)  
**Tip reviewed:** `3293e77` on `cursor/chat-sim-copper-impl-8ac5` (parent tip T19 ★ `v0.6.28` @ `43ece84`)  
**Verdict:** **PASS WITH NOTES** — package ready for Engineer ★ ACCEPT → tag **`v0.6.29`**. **No ACCEPT claim from Cursor.**

**Process note:** Claude Code implemented. Same-session implementer green is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| `submit_command` widened to `"executed"` / sim inside C4 | **Clear** — path (a); execution stays `not_implemented` |
| Tick when disarmed | **Clear** — tick only after `safety.outcome == "allow"` (T3) |
| Tick for TAKEOFF/RH/FOLLOW/PATROL | **Clear** — no tick, no `"Simulación"` (T2/T2b) |
| ESC / `SimulatedEscSink` from orch chat path | **Clear** — T16 fence green on orchestrator (T4) |
| Invented GO_TO coordinates | **Clear (N1)** — ValueError → honest “sin destino”; no fake target |
| Tip-version pin reintroduced | **Clear** — T17 guardrail green |
| Isolation fences silently deleted | **Clear (N2)** — retarget exclude `orchestrator.py` by name only |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 lazy process-scoped `SimAutonomyExecutor` | **PASS** |
| §0.3 path (a) — `submit_command` unchanged; tick after allow; message says simulación | **PASS** |
| §0.4 TAKEOFF/RH/FOLLOW/PATROL no tick | **PASS** |
| §0.5 Disarmed no tick | **PASS** |
| §0.6 Never ESC / SimulatedEscSink | **PASS** |
| §0.7 Tests armed HOLD tick · PATROL no tick · disarmed no tick · ESC fence | **PASS** (+ LAND/GO_TO/TAKEOFF/RTL/FOLLOW coverage) |
| §0.8 version `0.6.29` · docs · no new C-xxx | **PASS** |
| §0.9 Out: CHARGE · Skills · tip pins · live copper | **PASS** |

---

## 2. Verification (this pass)

- T20 suite + tip-pin guardrail + allowlist + C40/C11/C26 isolation retargets + ESC stub fence helpers: **65 passed**.
- Live read of `_sim_autonomy_tick_note` / three fulfills: tick gated on `allow`; GO_TO catches `ValueError` without inventing params.

---

## 3. Notes

**N1 — GO_TO without destination (IC gap, accepted resolution).** IC §2/§3 spoke of HOLD/LAND/GO_TO sim tick after allow, but chat GO_TO still ships empty params (T8 lock) while C40 `tick(GO_TO, …)` requires `x_m`/`y_m`. Claude’s resolution — catch `ValueError`, append honest “Simulación no disponible sin destino…” — is the correct in-Buy choice (no invented coords, no crash). Documented in report + T1c. **Not blocking.** Coordinate parse / real GO_TO sim remains a later Buy if Engineer wants it.

**N2 — Isolation fence retarget.** Historical “no SimAutonomyExecutor under core/” tests now exclude `orchestrator.py` by name; other core/adapters files still checked. Correct for an intentional orch-side wire. T14’s own “no sim from chat” test rewritten to the permanent ESC-fence invariant.

**N3 — Process.** Await Engineer ★ ACCEPT for tag `v0.6.29`. Next cola: T21 Skills runtime software.

---

## 4. Next

```text
Cursor review: PASS WITH NOTES @ 3293e77
Await Engineer ★ ACCEPT → tag v0.6.29
Then Claude: T21 Skills runtime software @ 0.6.30
```
