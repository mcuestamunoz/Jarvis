# Implementation Review — FN-016 vs RETURN_HOME wizard precedence (`B1-fn016-rtl-wizard-precedence`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (independent pass — Engineer pasted Claude T15 push summary)  
**Against:** [IC](implementation_contract_fn016_rtl_wizard_precedence_b1.md) · [report](implementation_report_fn016_rtl_wizard_precedence_b1.md) · [DC ★](design_contract_fn016_rtl_wizard_precedence_b0.md)  
**Tip reviewed:** `702babe` on `cursor/fn016-rtl-precedence-impl-8ac5` (parent IC tip `4d73435`)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.23` / `v0.6.23`**.

**Process note:** Claude Code implemented. Same-session implementer green is not review of record. This pass re-audits the tip against IC §0 locks with live E2E + pytest.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Fix after RETURN_HOME / too late in dispatch | **Clear** — early check in `_handle_global_commands` after Continuity defer, **before** ARM and all vehicle intercepts |
| Removed `volver`/`vuelve` from RTL phrases | **Clear** — `config.py` byte-untouched vs IC parent |
| Expanded global `ESCAPE_WORDS` | **Clear** — not touched |
| IDLE `volver` broken | **Clear** — live E2E + `test_idle_volver_still_vehicle_return_home` → `vehicle_return_home` |
| Wizard cancel shape drift | **Clear** — same `status=cancelled` / `action=define_missing_params` / message as DEFINE_MISSING FN-016 block |
| Defense-in-depth removed | **Clear** — DEFINE_MISSING-branch FN-016 + `ParamDefinitionSession.answer` still present |
| T14 / T16 implemented accidentally | **Clear** — `safety.py` untouched; ESC fence test still string-scan |
| Historical Fase C tip-pin mass rewrite | **Clear** — only active-lineage Assistant/vehicle checkpoints `0.6.21`→`0.6.23` |
| Package / tip sync on wrong base | **Clear** — impl landed on suite-honesty tip that already carries T13 ★ @ `v0.6.21` |

---

## 1. Qué aterrizó

| Layer | What |
|---|---|
| Orchestrator | DEFINE_MISSING + `is_navigation_back_phrase` → cancel before vehicle Tasks |
| Phrases | `VEHICLE_RETURN_HOME_PHRASES` / `NAVIGATION_BACK_WORDS` unchanged |
| Tests | FN-016 suite strengthened + IDLE RTL regression + `0.6.23` pin |
| Package | **`0.6.23`** |

Root cause confirmed live before review: mid-wizard `volver` → `vehicle_return_home`. After tip: `cancelled` / `define_missing_params`.

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs orchestrator placement / config diff / defense blocks.  
2. Live E2E: DEFINE_MISSING + `volver` → cancel + IDLE; IDLE + `volver` → `vehicle_return_home`.  
3. Pytest: FN-016 + eight vehicle/arm suites — **82 passed** (re-run this pass).  
4. Scope vs IC parent: orch + FN-016 tests + active-lineage tip bumps + PRIORIDAD/report only.  

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2 early cancel before vehicle intercepts | **PASS** |
| §0.3 RTL / nav phrase tables untouched | **PASS** |
| §0.4 IDLE RETURN_HOME intact | **PASS** |
| §0.5 tests (volver/vuelve/atras + IDLE) | **PASS** |
| §0.6 version `0.6.23` + docs | **PASS** (see N1) |
| §0.7 ESC / tip-pin / allow-list / CHARGE out | **PASS** |
| T1–T5 | **PASS** |

---

## 4. Dónde nos deja

```text
DEFINE_MISSING + volver/vuelve/atras → cancel (FN-016 restored)
IDLE + volver/vuelve → RETURN_HOME (T10 intact)
Next AUTHORIZED: T16 ESC fence @ 0.6.24 · T14 allow-list @ 0.6.22 (version retarget note N1)
```

---

## 5. Cómo suma

Cierra la regresión real introducida al solapar frases RTL con navegación de wizard: el modo acquisition vuelve a ganar sin empobrecer el mando IDLE.

---

## 6. Notes

**N1 — Package numbering vs T14.** Tip jumps `0.6.21` → `0.6.23` because T14 (`0.6.22`) is still AUTHORIZED-only. Correct for this Buy. When Claude implements T14, retarget its package to the then-current tip+1 (likely `0.6.25` if T16 takes `0.6.24`), or land T14 before tagging if Engineer wants linear `0.6.22` consumed.

**N2 — Process.** Claude implementer green ≠ review of record. This Cursor pass is the review of record for IC compliance. Engineer ★ ACCEPT applied this close.

**N3 — Baseline.** Report’s 54→53 (FN-016 fixed; ESC fence + historical pins remain) matches the two-Buy split already authorized.

---

## 7. Next

```text
★ ACCEPT CLOSED @ v0.6.23 (Engineer 2026-10-01)
Await Engineer ★ pick: T16 ESC fence · T14 allow-list (retarget T14 package)
```
