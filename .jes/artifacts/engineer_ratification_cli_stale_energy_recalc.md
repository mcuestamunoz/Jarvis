# Engineer Ratification — CLI Continuity: recalc after watts-recovery pick

**Date:** 2026-09-02  
**Authority:** Engineer (“procede” after the emax → r2305 walk interstitial)  
**IC:** [implementation_contract_cli_stale_energy_recalc.md](implementation_contract_cli_stale_energy_recalc.md)

## Cut chosen

Continuity rank + ReasoningLayer empty-missing guard + omit pick “optimizar” hint. **Not** auto-`calcular`. **Not** Option B.

## ★

| ★ | Decision |
|---|---|
| **★1** | Stale sim `missing_energy_parameters` must not ask the user to declare W/Wh that are already in the project. |
| **★2** | Next step is `calcular` / `simular`. Situation stays “autonomía no demostrada” until there is a number. |
| **★3** | Do not auto-run calculate/simulate on pick. |
| **★4** | Watts recovery (emax no-W), autonomy-below (5 vs 15), G21 covering-with-W **unchanged**. |
| **★5** | Option B / `_derive_overall` / T1+2 / Tier 3 / invent W **frozen**. |

Claude implements the IC. JES reviews after the report. This chat does not edit `src/`.
