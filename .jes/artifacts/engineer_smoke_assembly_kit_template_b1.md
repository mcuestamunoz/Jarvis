# Engineer smoke — Assembly kit template B1-min (2026-09-09)

**Project:** `autonomía-de-10min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_assembly_kit_template_b1.md) §6 · [review](implementation_review_assembly_kit_template_b1.md) PASS WITH NOTES @ suite **2507** (XT60 one-token hotfix T4d @ **2508**)

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Architecture | still **4/4** after kit keys exist | **PASS** — `estado` “Arquitectura 4/4 — completa ✓” |
| 2 | `definir conector` | single-key wizard; Brief example `'XT60'` saves (N1 hotfix) | **PASS** — `power_connector: XT60` `◇` declarativo |
| 3 | `definir harness` | free text; not energy composite | **PASS** — Brief “cable JST-SH 6 pines”; `component_description_saved` |
| 4 | Cards | both kit keys present; no catalog SKU required | **PASS** — `signal_harness: cable JST-SH 6 pines qty=1 (declarativo)` |
| 5 | Continuity after both filled | kit holes gone; next rank is physics/sim if that is the blocker | **PASS** — next = `GAP-SIM-NOT-PASS` (not kit) |
| 6 | ASSEMBLY READY | live with holes **or** declarative kit + open physics **must not** become ready solely because 4/4 | **PASS** — `BOM UNVERIFIABLE` · `NOT ASSEMBLY READY` (review N3) |

Leaving slots pending was also ACCEPT (IC §6). This walk went further and **declared** both. That is still ACCEPT.

## Out of this Buy (do not reopen kit)

Energy detour on the same demo: `emax_rs2205_2300` qty=3, `lipo_6s_10000mah`, propulsión `legacy_estimate` 8.0 N, sim **fail**, autonomía ~17.8 min vs 10 min objetivo. Continuity correctly ranks **GAP-SIM-NOT-PASS** after kit holes are filled. That is **P-energy**, not a kit defect. Kit does not check XT60 vs battery connector (Lumenier XT30 class) this Buy.

Do **not** append kit keys to `BLOCK_TO_COMPONENTS`. Do **not** treat sim FAIL as a kit reopen.
