# Implementation Contract — Fase C Safety-real policy gate B1 (`B1-fase-c-safety-real-policy`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (allow ≠ execute · Authority ≠ allow · RejectAll stays default · no hardware)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.15`**  
**Parents:**
- [C2 ★ ACCEPT](implementation_contract_fase_c_intent_safety_stub_b1.md) — Intent + `RejectAllSafetyGate` / `default_safety_gate()`  
- [C4 ★ ACCEPT](implementation_contract_fase_c_autonomy_surface_b1.md) — `submit_command` behind Safety; allow → still `execution="not_implemented"`  
- [C5 ★ ACCEPT](implementation_contract_fase_c_radio_dual_role_b1.md) — Authority is data/trace only; **Authority ≠ allow**  
- [C16 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) — tip **`v0.5.14`**; Engineer pick **C — Safety real** (no board required)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; keep RejectAll as shipped default unless this Buy explicitly keeps it  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · no MCU/GPIO/ESC coupling

**Type:** **Implementation Contract** — first **real Safety policy gate** (not RejectAll): an **opt-in** armed allow-list that can `allow` a tiny set of autonomy verbs under explicit arm, while **`default_safety_gate()` remains `RejectAllSafetyGate`** and **nothing still executes**.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.15`**; git tag **`v0.5.15`** only after Engineer ACCEPT.  
**Not** `AllowAllSafetyGate` · flipping the shipped default to permissive · Authority/radio → allow · executor/`execution="executed"` · ESC/GPIO/craft/CLI wiring · claiming “safe to fly.”

**Outputs (required):**
1. New policy gate class in `src/jarvis/capabilities/safety.py` (name locked preferred below) + exports in `capabilities/__init__.py`  
2. Tests proving disarmed/armed/allow-list/reject reasons + `submit_command` allow path still `execution="not_implemented"` + RejectAll/`default_safety_gate()` unchanged  
3. Optional thin smoke helper (preferred) showing HOLD/LAND allow under armed policy vs reject under default — **must not** claim execution  
4. `.jes/artifacts/implementation_report_fase_c_safety_real_policy_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **policy allow ≠ flying / ≠ executed / ≠ hardware**  
6. `pyproject.toml` → **`0.5.15`** (+ re-pin `0.5.14` version-checkpoint tests)

**Checkpoint:** package **`0.5.15`** · Python suite ≥ **3389** + new tests · default path still RejectAll-green · policy gate green on opt-in path

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-safety-real-policy`** — first real (non-RejectAll) Safety policy |
| 2 | One front | Do **not** fold MCU `.elf`, ELRS, craft↔FS, GPIO/ESC, executor, or CLI Intent→autonomy into this Buy |
| 3 | What this Buy demonstrates | An opt-in gate can **allow** a small verb allow-list only when explicitly **armed**, otherwise reject; `submit_command` may return `safety.outcome=="allow"` and still **`execution="not_implemented"`**. **Human:** “el portero ya no es solo ‘no a todo’ — puede decir sí a HOLD/LAND si lo armas a mano, pero **nadie ejecuta** todavía.” |
| 4 | Keep RejectAll as shipped default | **`default_safety_gate()` → `RejectAllSafetyGate` unchanged.** Existing rung regressions that pin RejectAll must stay green without rewriting their meaning. |
| 5 | Forbidden: AllowAll | **No** `AllowAllSafetyGate` (or equivalent always-allow) under `src/`. |
| 6 | Policy gate (locked preferred name) | **`ArmedAllowlistSafetyGate`** (alternate name OK if documented). Starts **disarmed**. API: `arm()` / `disarm()` (or equivalent explicit setters). `gate_id` distinct from `"reject_all"` (e.g. `"armed_allowlist"`). |
| 7 | Allow-list (locked minimum) | When **armed**, `allow` only for autonomy action ids matching **`HOLD` and `LAND`** (same `action_id` shape `submit_command` already builds: `autonomy:{verb}:{id}` — parse verb robustly). When armed but verb **not** on list (e.g. `TAKEOFF`) → `reject` with a clear reason (not `"not_implemented"`). When **disarmed** → always `reject` with reason e.g. `"disarmed"`. |
| 8 | RejectAll reason hygiene | `RejectAllSafetyGate` may keep reason `"not_implemented"` (historical). Policy gate **must not** reuse `"not_implemented"` for disarmed / not-on-list rejects. |
| 9 | Authority ≠ allow | Setting `authority_signal_id` / any `AuthoritySignal` must **not** flip allow. Tests must pin this. |
| 10 | Allow ≠ execute | Even when policy allows, `submit_command` remains **`execution="not_implemented"`**. Do **not** add an executor or `"executed"`. |
| 11 | ESC arm ≠ Safety arm | Do **not** couple to `SimulatedEscSink.arm()` / PWM sink. Safety arm is a **separate** software latch. |
| 12 | Version | Bump **`0.5.14` → `0.5.15`**; tag **`v0.5.15`** on ACCEPT only |
| 13 | Forbidden claims | “Safe to fly” · “armed vehicle” · “motors may spin” · “production Safety certified” |

**Product sentence:**

```text
Un portero de verdad (lista blanca + armado explícito) que puede permitir
HOLD/LAND en tests, mientras RejectAll sigue siendo el default del producto
y nada se ejecuta todavía.
```

**Defaults locked by Cursor (Engineer: procede / C):**
- `ArmedAllowlistSafetyGate` · allow-list HOLD+LAND only  
- `default_safety_gate()` stays RejectAll  
- No AllowAll · Authority≠allow · allow≠execute · no ESC coupling  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  safety.py          # + ArmedAllowlistSafetyGate (RejectAll untouched in behavior)
  __init__.py        # export new gate; docstring honesty updated
# optional:
src/jarvis/flight_software/autonomy/smoke.py  # thin smoke for policy path OR new helper
tests/test_fase_c_safety_real_policy_b1.py    # NEW
```

No new architectural subsystem. Stay inside `capabilities/` + existing autonomy surface.

---

## 2. Behavior table (normative)

| Gate | State | Request | Expected `outcome` | Notes |
|---|---|---|---|---|
| RejectAll (default) | n/a | any | `reject` | reason may stay `"not_implemented"` |
| ArmedAllowlist | disarmed | any | `reject` | reason e.g. `"disarmed"` |
| ArmedAllowlist | armed | HOLD/LAND action_id | `allow` | then submit → `execution="not_implemented"` |
| ArmedAllowlist | armed | TAKEOFF (or other) | `reject` | reason e.g. `"verb_not_allowed"` |
| ArmedAllowlist | any | + `authority_signal_id` set | unchanged | Authority ≠ allow |

Exact reason strings may vary if documented in report + tested; they must be non-empty on reject and **not** pretend execution happened.

---

## 3. Integration rules

| Existing | C17 rule |
|---|---|
| `default_safety_gate()` | Still RejectAll |
| `submit_command` | Unchanged contract: allow → `not_implemented`; reject → `not_attempted` |
| Rung regression tests pinning RejectAll | Stay green |
| Radio / Authority | Trace only; do not wire into allow |
| Craft / Board / CLI / C++ tree | Untouched |

---

## 4. Tests (minimum gate)

| ID | Check |
|---|---|
| T1 | `ArmedAllowlistSafetyGate` exists; starts disarmed; `disarm`/`arm` work |
| T2 | Disarmed → reject with non-`not_implemented` reason |
| T3 | Armed + HOLD and armed + LAND → allow |
| T4 | Armed + TAKEOFF (or other non-list verb) → reject |
| T5 | `authority_signal_id` set does not flip allow when disarmed / not-on-list |
| T6 | `submit_command(HOLD, policy_gate)` armed → `safety.allow` + `execution="not_implemented"` |
| T7 | `default_safety_gate()` still `RejectAllSafetyGate`; HOLD under default still reject + `not_attempted` |
| T8 | No `AllowAllSafetyGate` under `src/`; no `execution="executed"` introduced |
| T9 | Report + docs honesty; no premature `v0.5.15` tag |
| T10 | Python full suite green @ **`0.5.15`** |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Flip default to permissive | Process / suite contracts |
| AllowAll under `src/` | Explicit prior lock |
| Executor / `"executed"` | Allow ≠ execute |
| ESC sink / GPIO / craft wiring | One front / no hardware |
| “Safe to fly” language | Honesty |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.15 includes”  
- Explicit: **exists** = opt-in armed allow-list policy + RejectAll default; **impossible** = flying, executed autonomy, hardware Safety  

Also update Parked blurb: **real Safety** moves from parked → this Buy (then CLOSED after ACCEPT).

---

## 7. Acceptance

**PASS when:** T1–T10 · policy allow path proven · default RejectAll intact · no AllowAll · no execute · `0.5.15`.

**FAIL if:** default becomes permissive · AllowAll shipped · Authority implies allow · `"executed"` appears · ESC/craft coupled · “safe to fly” claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C17)
Claude   → ArmedAllowlistSafetyGate + tests + report + 0.5.15
Cursor   → review
Engineer → ACCEPT + tag v0.5.15
Cursor   → next Buy when prioritized
           (still one front: MCU .elf · link · craft↔FS · …)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C16 CLOSED @ v0.5.14. C17 B1-fase-c-safety-real-policy READY —
ArmedAllowlistSafetyGate (HOLD/LAND when armed); RejectAll stays default;
allow ≠ execute; no hardware.
```

---

## 10. Engineer ★ checklist

1. Opt-in policy gate (not flipping default) OK?  
2. Allow-list **HOLD + LAND** only when armed OK?  
3. RejectAll remains `default_safety_gate()` OK?  
4. Authority ≠ allow · allow ≠ execute OK?  
5. No ESC/craft/AllowAll OK?  
6. Version **`0.5.15`** OK?  
