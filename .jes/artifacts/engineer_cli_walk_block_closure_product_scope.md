# Engineer CLI walk — Block Closure / PRODUCT_SCOPE

**Date:** 2026-09-01  
**Authority:** Engineer (walk done; Combo A typed-SKU abandoned)  
**Project:** `inspección-autonomía-mínima-5-minutos` (`eb61a0ed6fe2`)  
**Gate:** interconnection CLI after Block Closure B-PROP-ENERGY review PASS WITH NOTES (N1 closed)

---

## Verdict

**Walk closed.** Do not spend more time making Gate A PASS by typing a SKU the numbered catalog never offered.

| Claim | Result |
|---|---|
| Block line is honest (`NO CERRADO`, no false `descarga excedida`) | **PASS** |
| Battery SKU re-bind writes catalog Wh (`lipo_6s_10000mah` → 222.0, not 6) | **PASS** |
| Happy-path picker reaches manufacturer_test / block CERRADO | **FAIL** — Combo A is library+test only, not the offer |
| Product CLI can close B-PROP-ENERGY without a hidden SKU | **FAIL** |

Tests still close Gate A by exact bind. That does **not** replace this walk.

---

## What the Engineer actually did (happy path)

Create: dron · inspección + autonomía 5 min · payload 0.5 · restricciones ninguna · detallado · 2 motores · arquitectura A.

Then numbered catalog:

1. Motor **#1 `sunnysky_r2305_2500`** (not `sunnysky_r2205_2500`)
2. Prop **#4 `gf_5045x3`** (typed SKU first → LLM analyze; numbered pick bound)
3. ESC freeform **`ESC 40A`**
4. Battery **#6 `lipo_4s_1500mah`**
5. Frame **`PVC 650g`**
6. `Pixhawk 4'` + `Here3`

After `calcular`/`simular`/`estado` (4S 1500): sim **fail**, autonomía L0 **3.0 min** vs 5, empuje 15 N vs 16.35 N, `legacy_estimate · 7.5 N`, ERF mostly INCOMPLETE/UNVERIFIABLE, `PROJECT STATUS: NOT ASSEMBLY READY`, **BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO** (generic — N1 OK).

Then `definir bateria lipo_6s_10000mah` → 222.0 Wh, masa 2.556 kg, autonomía **30.3 min**, sim still fail (15 vs ~30 N). `GAP-MOTOR-CATALOG-UNRESOLVED` with SKU already bound. `ayúdame a elegir` reprinted `estado`. Frame iterate `PVC 200g` did not change mass.

Engineer stopped at `definir motor` (≥ 15.04 N/motor). Correct.

---

## Lies / traps the walk hit (product, interconnected)

1. **Catalog offer ≠ Gate A.** D8 top-5 by nameplate thrust. Combo A motor exists in JSON with Discrete OP `manufacturer_test` and is ranked out. `#1` is a different SunnySky (`r2305`, no OP → `legacy_estimate`).
2. **CTA watts.** After typing `gf_5045x3`, analyze: “este motor de catálogo no declara vatios” while the list showed `r2305` ~220W. Predicate is “SKU bound”, not “no watts”.
3. **Energy vs thrust spiral.** 4S 1500: autonomía L0 3 min (22.2 Wh / 440 W). 6S 10 Ah: autonomía OK, empuje impossible. Continuity does not warn that the heavier pack will invalidate the bound motor.
4. **`GAP-MOTOR-CATALOG-UNRESOLVED`.** Title says unresolved; evidence is `bound_sku_underspec`. `ayúdame a elegir` then no-ops (offer is pre-bind only). Investigation already named this; Block Closure IC left it out of scope.
5. **When the combo no longer fits, Jarvis does not propose a replacement.** Sim fail + heavier pack → generic “reduce weight / increase thrust”, Continuity stays on “sim no es PASS”, help-choose treats a bound SKU as done. This is the product spine of the next investigation (see [engineer_notes_cli_propose_on_misfit.md](engineer_notes_cli_propose_on_misfit.md)) — not a fifth equal bullet.
5. **Frame iterate vs override.** `PVC 200g` registered as material string; `structure_mass_override_kg` stayed 0.65. Structure — parked, not this next slice.

Physics unchanged: L0 `(Wh/W)×60` is not L1 hover; Combo A paper ~1.32 min is 4-motor Discrete OP, not this walk.

---

## What this is **not**

- Not a Block Closure formula fail.
- Not Option B ERF (dual `NOT ASSEMBLY READY` + `NO CERRADO` is required).
- Not H5 / C-081 (ESC stayed declarative; that was allowed).
- Not Catalog Foundation as locked in ★5 (ESC schema + 3–5 SKUs). Adding motors to JSON would not have put Combo A in the top 5.

---

## Next

Claude executes [investigation_contract_cli_catalog_assist_misfit_propose.md](investigation_contract_cli_catalog_assist_misfit_propose.md). Cursor reviews. Then Engineer ★ on T1 / T1+2 / STOP.
