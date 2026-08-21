# Investigation Review — Impl D Create → BOM / SKU BOM

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_impl_d_create_bom_sku.md`](investigation_contract_impl_d_create_bom_sku.md)  
**Report:** [`.jes/artifacts/investigation_report_impl_d_create_bom_sku.md`](investigation_report_impl_d_create_bom_sku.md)  
**Base:** tag `checkpoint-impl-c` · commit `c99fec6`

## Verdict

**PASS WITH NOTES**

Investigation complete: all 12 required sections present, zero `src/` / test changes. Central finding confirmed by independent code trace. Option C correctly rejected. Scenario D honesty rule is load-bearing and correctly made structural (`sku_resolved` ← `catalog_ref`, never `.name`).

## Checklist

| Gate | Result |
|---|---|
| §1.1 As-is BOM pipeline + consumers | **Pass** — single authority, no CLI/view drift |
| §1.2 SKU identity gaps / Scenario A–H | **Pass** — D handled as non-negotiable |
| §1.3 Quantity + line-item schema | **Pass** — ESC `null` is correctly honest |
| §1.4 Create handoff (sense B) | **Pass** — defer recommended |
| §1.5 ERF / ASSEMBLY READY interaction | **Pass** — no new gap type |
| §1.6 Design options (≥2) | **Pass** — A recommended, C rejected with G22-class dual-authority rationale |
| §1.7 Out-of-family policy | **Pass** |
| §1.8 Tests + CLI probe sketch | **Pass** |
| §1.9 Slice outline | **Pass** — D1–D5 |
| ★ decisions numbered | **Pass** — ★1–★6 |
| No production fix / no Conversation Engine | **Pass** |
| G24–G27 left out of scope | **Pass** |

## Code review highlights

**BOM never reads `catalog_ref`.** Confirmed: `build_component_bom._entry` only ships `key` / `name` / `completeness` / `missing_fields` / `component_type`. Quantity is never derived. One authority, correctly identified as enrichment target (Option A).

**Scenario D is already reachable.** Confirmed: `invalidate_diverged_catalog_refs` does `model_copy(update={"catalog_ref": None})` only — `.name` untouched (`catalog_bind.py:225`). Any BOM that keys off `.name` shape will lie. Structural `sku_resolved` rule is the correct fix.

**`catalog_bound` is write-only.** Confirmed: every `SubsystemEvidence(..., catalog_bound)` occurrence is a constructor write; `_derive_subsystem_verdict` never reads it. ★5 (leave disconnected in v1) is correct — wiring it would be a verdict-semantics change, not a data-honesty fix.

**CLI suppression finding (§2.3) is real and load-bearing.** Confirmed: `adapters/cli/main.py:255` — `if bom_lines and not continuity.get("evidence")`. Same gate applies to physical requirements lines (`:248`). File view `views/sistema.md` always renders BOM. Option A without D4 can ship correct data and still be invisible in `estado` during the exact post–Impl C walk shape (energy honesty note / catalog / physics evidence commonly populated).

## Notes (non-blocking for PASS; binding for IC)

1. **Schema field name:** report proposes `display_name`; today’s entry field is `name`. IC must **keep `name`** (additive fields only) — do not rename. Treat report’s `display_name` as alias language for the existing `name` field.

2. **★6 recommendation (Cursor):** **include Slice D4 in Impl D v1** as a tiny adjunct — decouple BOM section rendering from `continuity["evidence"]` truthiness (prefer: always show "Componentes / gaps:" when `bom_lines` non-empty; leave Continuity evidence block as-is). Do **not** fold BOM into Continuity evidence in this cut (that reopens ranking/copy risk). Requirements-lines gate is sibling debt — **out of Impl D** unless Engineer expands ★6; track separately if not fixed together.

3. **Scenario C re-check:** `has_motor` / `has_battery` via `default_library` is correct reuse — IC must forbid a second catalog reader. For non-motor/battery keys with a stray `catalog_ref` (shouldn’t exist today), `sku_resolved` stays false / null-safe.

4. **Propeller quantity = motor_count:** acceptable as documented convention in D1; IC should say “convention, not measured fact” in one line so it doesn’t become fake certainty.

5. **Probe 3 (frankenstein)** is the acceptance spine of D1 — must be an automated test, not only CLI.

## Cursor stance on ★ (for Engineer ratification)

| ★ | Cursor recommendation |
|---|---|
| ★1 Option A only | **Ratify** |
| ★2 motors + battery | **Ratify** |
| ★3 defer Create-handoff | **Ratify** |
| ★4 no new gap type | **Ratify** |
| ★5 leave `catalog_bound` disconnected | **Ratify** |
| ★6 CLI suppression | **Ratify: fix now (D4 in v1)** — otherwise Impl D is not product-visible in `estado` |

## Engineer ratification (2026-08-21)

Aligned with this review. Locked:

| ★ | Engineer |
|---|---|
| ★1–★5 | **RATIFIED** as recommended |
| ★6 | **CONDITIONAL** — include D4 only if presentation-local; no Continuity ranking / `next_useful_step` / G9-A |

## Next step

~~Await ★~~ → **DONE.** IC: [`implementation_contract_impl_d_create_bom_sku.md`](implementation_contract_impl_d_create_bom_sku.md) — READY FOR CLAUDE.
