# Investigation Review — Connect Remaining `mounted_on` B1 (Fase 3 / Conn)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_connect_remaining_mounted_on_b1.md](investigation_contract_connect_remaining_mounted_on_b1.md)  
**Report:** [investigation_report_connect_remaining_mounted_on_b1.md](investigation_report_connect_remaining_mounted_on_b1.md)

## Verdict

**PASS WITH NOTES**

Lean **B1** is correct: Conn is mostly already shipped; the real Buy is a narrow parse bug-fix, not new mount capability. Frame parts stay target-only (`parent_key`). B2 auto-infer correctly rejected.

**Note N1 is load-bearing for the IC:** subject-before-`en` alone does **not** make `"hélices montadas en los motores"` succeed — after that fix, target `"los motores"` still resolves to `None` (no Spanish alias for key `motors`). IC must lock **both** subject scoping **and** component-noun target aliases (reuse subject table on the target segment when the key exists).

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean B1 bug-fix | **Pass** |
| Gap matrix + Continuity coverage | **Pass** |
| Empirical parse (collisions) | **Pass** — Cursor reconfirmed |
| `parent_key` vs `mounted_on` for frame parts | **Pass** — keep target-only |
| B0/B1+/B2 evaluated | **Pass** |
| Contingency sketch | **Pass with N1** — incomplete for propellers→motores |
| No code | **Pass** |

---

## Independent verification

| Phrase | Cursor result |
|---|---|
| `helices montadas en los motores` | `AMBIGUOUS_TARGET(motors)` — wrong subject |
| `sensor montado en el esc` | `SET(esc→esc)` — self-mount |
| Subject scoped before `en` (probe) | subject→`propellers` / `sensors` **correct** |
| Target after fix (probe) | `el esc`→`esc` ✅ · `los motores`→`None` ❌ |
| `propellers montados en motors` | `SET` ✅ (literal key) |

---

## Notes for IC

### N1 — Dual lock (subject scope + target component nouns)

| Lock | Why |
|---|---|
| Subject search = text **before** first `\ben\b` | Fixes wrong-subject class (report) |
| Target may resolve via **same noun→key map** as subjects when key ∈ `components` | Fixes `"en los motores"` → `motors` |
| CLEAR branch unchanged | No `en` collision |
| No new writer / no inference / no frame-part subjects | Locked stances |

### N2 — B0 not a full close

Agree — natural Conn phrases fail today with wrong-cause errors.

### N3 — Label translation still intentional

`"placa principal"` ≠ `"Main Plate"` remains design, not this Buy.

---

## Phase

Investigation **reviewable**. IC READY authored for ★ Buy B1 (dual lock) → Claude implement.
