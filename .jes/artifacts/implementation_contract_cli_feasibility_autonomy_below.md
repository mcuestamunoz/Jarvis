# Implementation Contract — CLI feasibility: calculated autonomy below target

**Project:** Jarvis  
**Date:** 2026-09-02  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (Engineer: “procede con la opción más adecuada”)  
**Reviewer:** Cursor against this IC after the edit

**Status:** RATIFIED by Engineer proceed (2026-09-02). Implement this file only.

**Type:** Claim-language / Continuity. **Not** new physics. **Not** ERF. **Not** T1+2 / Tier 3. **Not** `definir motor` / catalog picker.

**Parent:** [implementation_contract_cli_feasibility_semantics.md](implementation_contract_cli_feasibility_semantics.md) §2.1 — that IC left `"Diseño validado…"` when `autonomy_min` **was** computed. Field walk 2026-09-02 (`autonomia-15min`, 5.0 min vs 15 min, sim **pass**) showed that hole.

**Why this cut (not the other two):**
- Re-offer motor catalog while thrust still covers would send the user down the wrong block.
- Joint motor+prop+battery propose is Tier 3 (frozen).

---

## 0. You

- Edit only files listed in §5.
- Do not change `simulator.py` pass/fail (thrust PASS + `autonomy_below_restriction` warning stays).
- Do not change `engineering_readiness.py` / `ASSEMBLY_READY` / block closure.
- Do not invent combos, SKUs, `motor_power_w`, or hover minutes.
- Do not reopen T1 help-choose, G22, or battery picker filtering.
- Full suite green. Zero weakened tests.

---

## 1. Intent (field fixture)

After 4/4 + `calcular`/`simular`/`estado` on a closed BOM with:

- `simulation.status == "pass"`
- `autonomy_target_min = 15`
- `current_autonomy_min ≈ 5.0` (or `warnings` contains `autonomy_below_restriction`)

Continuity **must not** say `Diseño validado en simulación (PASS)`.

It **must** reuse the parent IC locked situation string (same claim: thrust PASS ≠ autonomy demonstrated).

---

## 2. Locked behavior

### 2.1 Continuity `situation` — `project_continuity.py`

Extend the existing §2.1 branch. Fire the **same** string when `sim_status == "pass"` and an autonomy target exists and **any** of:

1. calculated autonomy absent (`calculations.autonomy_min` is None **or** `energy_status == "missing_energy_parameters"`) — already shipped;
2. `physical_requirements.current_autonomy_min` is not None **and** `< autonomy_target_min`;
3. `"autonomy_below_restriction"` in `simulation.warnings`.

Locked string (verbatim, already in product):

```text
Comprobación de empuje: PASS. Candidato inicial — la autonomía del objetivo no está demostrada.
```

Keep `"Diseño validado en simulación (PASS). …"` when there is **no** autonomy constraint, or when current autonomy **meets or exceeds** the target.

Keep `"Física orientativa en PASS…"` for incomplete/missing BOM (order of branches unchanged).

Extract a small helper in `project_continuity.py` if it avoids duplicating the predicate. No new module.

### 2.2 Continuity `next_useful_step` — same file

When the autonomy target is **calculated and below** (predicate 2 or 3 above), rank-2 must **not** keep the architecture-complete / “puedes optimizar o simular” / “Diseño en PASS — puedes iterar” CTA.

Locked next step (verbatim):

```text
La autonomía calculada está por debajo del objetivo. Revisa energía (batería o consumo) o el requisito; el empuje ya es PASS.
```

`next_useful_why`: `autonomy_below_restriction` (existing warning code; do not invent a catalog CTA).

**Do not** name SKUs. **Do not** say `ayúdame a elegir`. Underspec (T1) rank-2 stays first when `_underspec_live`.

Uncalculated-autonomy ranking (parent IC, missing W / catalog-bound no nameplate) is **unchanged**.

### 2.3 Evidence

Already shows `Autonomía objetivo: 15 min (actual ~5.0 min)` when current is set. **Do not** change that line.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_project_continuity.py` | Closed BOM + sim PASS + target 15 + current 5.0 + warning `autonomy_below_restriction` → situation contains `Comprobación de empuje` / `Candidato inicial`, **not** `Diseño validado`. Next step is the locked §2.2 string; does **not** contain `Arquitectura completa`, `optimizar`, `puedes iterar`. |
| same | Target 15 + current 15 (or 20) + no autonomy warning → still `Diseño validado`. |
| same | Existing uncalculated fixture (`test_situation_thrust_feasibility_only_when_autonomy_unmet`) stays green. |
| same | Existing no-constraint fixture stays green. |
| `tests/test_cli_feasibility_semantics.py` | Must stay green (uncalculated field fixture). |

Optional: one orchestrator-level test is **not** required if the unit fixture covers situation + next step. Do not add a new DSE/catalog probe.

---

## 4. Non-goals

```text
engineering_readiness.py / ASSEMBLY_READY / GAP-REQUIREMENTS-UNMET
simulator pass/fail / energy physics / (Wh/W)×60
T1 help-choose / definir motor reprint / G22
Tier 3 combo propose / battery catalog filter
Block closure CERRADO copy
P26 / P27-A / H5 / Conversation Engine
calcular/simular numeric line (already prints 5.0 min + restriction banner)
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/project_continuity.py` | Predicate + situation + next-step override |
| `tests/test_project_continuity.py` | New tests |
| `docs/IMPLEMENTATION_TASKS.md` | In progress / done |
| `.jes/state/engineering_state.json` | Sync |
| `.jes/artifacts/implementation_report_cli_feasibility_autonomy_below.md` | After implement |

---

## 6. Acceptance

- 15 vs 5.0 + sim pass + closed BOM: no `Diseño validado` in situation; locked thrust-feasibility sentence present.
- Next step names energy/requirement, not architecture-complete / iterate, not a motor picker.
- Autonomy met → `Diseño validado` unchanged.
- Uncalculated parent fixture unchanged.
- Sim still `pass` for thrust. ERF dual (Requirements INCOMPLETE vs Continuity) allowed (parent ★1).
- Suite green. No `src/` outside §5.

---

## 7. After you finish

Write `implementation_report_cli_feasibility_autonomy_below.md` (files, tests run, physics unchanged).
