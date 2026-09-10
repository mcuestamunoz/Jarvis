# Engineer smoke — Prop adapter ask B1 (2026-09-09)

**Project:** `autonomía-de-5min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_kit_prop_adapter_ask_b1.md) §6 · [review](implementation_review_kit_prop_adapter_ask_b1.md) PASS WITH NOTES @ suite **2523**

Post-4/4 IDLE walk (hélices already declared). Sequential hélices→Brief is T3 in tests; this walk covers skip + later declare.

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | `estado` before fill | `prop_adapter` missing; 4/4; hover twin | **PASS** — `✗ prop_adapter: no definido` · `Falta definir: prop_adapter` · BOM INCOMPLETE · margen **2.94** · arquitectura 4/4 |
| 2 | `definir adapter` | kit single-key Brief | **PASS** — “¿Cómo montas la hélice? …” |
| 3 | `no lo sé` | no spec; hole stays; ESC/architecture unchanged | **PASS** — “queda pendiente cómo montas la hélice”; `estado` still `✗ prop_adapter`; 4/4; margen 2.94 |
| 4 | `definir adapter` again | Brief reopens | **PASS** |
| 5 | `con adaptador/collet` | declarative spec; no `catalog_ref`; slot gone | **PASS** — “Prop adapter registrado.” · `◇ prop_adapter: con adaptador/collet qty=1 (declarativo)` · no mm |
| 6 | Hover / vatios | unchanged | **PASS** — margen **2.94**; requisito ≥ 2.72 N/motor; autonomía ~1.5 vs 5 min (energy, not adapter) |
| 7 | ASSEMBLY READY | kit fill must not become ready | **PASS** — BOM **PASS**; `NOT ASSEMBLY READY` · TOP GAP is `GAP-REQUIREMENTS-UNMET:autonomy` |

N1 (`definir esc` does not steal to adapter) not re-walked here: this project was already 4/4; IDLE `definir adapter` is the locked post-architecture path.

## Out of this Buy

Autonomy ~1.5 min vs 5 min and `legacy_estimate` 8.0 N are P-energy. Do not reopen adapter. Connector on this project is already `pololu_xt60_pair` (D catalog) — D help-choose walk is a separate smoke.

Do **not** append `prop_adapter` to `BLOCK_TO`. Do **not** infer hub vs shaft. No adapter SKU.
