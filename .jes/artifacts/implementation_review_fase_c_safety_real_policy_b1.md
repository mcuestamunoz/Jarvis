# Implementation Review — Fase C Safety-real policy gate (`B1-fase-c-safety-real-policy`)

**Date:** 2026-09-21  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_safety_real_policy_b1.md) · [report](implementation_report_fase_c_safety_real_policy_b1.md)  
**Verdict:** **PASS** — ★ ACCEPT CLOSED @ tag **`v0.5.15`**

---

## Summary

C17 ships the first real (non-RejectAll) Safety policy: **`ArmedAllowlistSafetyGate`** — starts disarmed (`"disarmed"`), arms only via explicit `arm()`, then allows **HOLD/LAND** from `autonomy:{verb}:{id}`; other verbs / bad ids reject with distinct reasons (not `"not_implemented"`). **`default_safety_gate()` / `RejectAllSafetyGate` bodies unchanged** vs tip. `authority_signal_id` unread. `submit_command` allow path still **`execution="not_implemented"`** (`surface.py`/`types.py` untouched). Smoke helper `smoke_policy_gate_hold_and_land`. Suite **3403 passed, 1 skipped** (+14). No premature `v0.5.15` tag.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Buy · one front · opt-in allow demo | **Pass** |
| 4 | `default_safety_gate()` stays RejectAll | **Pass** |
| 5 | No AllowAll under `src/` | **Pass** |
| 6–8 | ArmedAllowlist · HOLD/LAND · reason hygiene | **Pass** |
| 9–11 | Authority≠allow · allow≠execute · ESC≠Safety arm | **Pass** |
| 12–13 | `0.5.15` · no fake claims | **Pass** (tag deferred) |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| Read `ArmedAllowlistSafetyGate` vs IC §2 | Match |
| `default_safety_gate` / RejectAll evaluate body | Same as `v0.5.14` |
| `surface.py` / `types.py` diff vs tip | Empty |
| `class AllowAllSafetyGate` under `src/` | Absent |
| ESC coupling in capabilities | Honesty comments only |
| `pytest` C17 module | **14 passed** |
| C2 + C4 regression modules | **24 passed** |
| Full suite (T10) | **3403 passed, 1 skipped** |
| Tags: no `v0.5.15` | Confirmed |

**Note:** Living docs synced on ★ ACCEPT CLOSED @ tag **`v0.5.15`**.

---

## Verdict

**PASS** — ★ ACCEPT CLOSED @ tag **`v0.5.15`**.

Next fronts still one-at-a-time: MCU freestanding `.elf` · link (ELRS) · craft↔FS.
