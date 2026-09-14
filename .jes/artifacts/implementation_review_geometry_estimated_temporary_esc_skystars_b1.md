# Implementation Review — Estimated-temporary ESC height (Skystars KO50A II) B1

**Date:** 2026-09-14  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_geometry_estimated_temporary_esc_skystars_b1.md) · [report](implementation_report_geometry_estimated_temporary_esc_skystars_b1.md)

**Verdict:** **PASS WITH NOTES** — ready for Engineer smoke §3

---

## Checklist

| Gate | Result |
|---|---|
| Catalog omits `height_mm` for `skystars_ko50a_ii_bls` | **Pass** — `get_esc` → L=41 W=46 mass=13.3 H=`None`; JSON row has no `height_mm` key |
| Hybrid project sources (lock #4) | **Pass** — live 10-min: L/W `declared` 0.9 · H `estimated_temporary` 0.3 · mass `declared` |
| Additive writer, not plate allowlist (lock #6) | **Pass** — `set_estimated_temporary_esc_height` separate; key=`esc` only; requires prior L×W |
| Continuity grammar + disclosure (locks #7/#10) | **Pass** — `estimated_temporary_esc_assist` + orchestrator bridge; disclosure ESTIMADA TEMPORAL + replace signal (T7) |
| §0.1 Engineer number, not agent invent (lock #8) | **Pass** — process pause on empty bag documented; Engineer chose `8` / `10-min-autonomía` (SpeedyBee 8.0 shown as reference only) |
| Gates without weakening (lock #9) | **Pass** — screening / attest / fit-relations unchanged; T4–T6 green; **live** screening=`estimated_dims`, esc fit row=`estimated_dims` |
| Replace path (lock #11) | **Pass** — refresh preserves estimate while catalog lacks H; overwrites once catalog cites H (tests) |
| §0.2 FC bag | **Pass (skipped)** — not taken; FC identity-only |
| Version / suite | **Pass** — `0.4.1`; 18 new tests green locally; report suite **2929** |
| Live apply scoped | **Pass** — 10-min Skystars + H=8 estimated box; 5min still SpeedyBee declared H |

---

## Independent checks (Cursor)

1. `pytest tests/test_geometry_estimated_temporary_esc_skystars_b1.py` → **18 passed**.  
2. Catalog: `default_library.get_esc("skystars_ko50a_ii_bls").height_mm is None`.  
3. Live `workspace/10-min-autonomía-…/state.json`: `catalog_ref.sku=skystars_ko50a_ii_bls`; geometry box 41×46×8; H source=`estimated_temporary`.  
4. Live `screen_posed_envelope(esc, components)` → `estimated_dims`.  
5. Live fit-relations: esc row `estimated_dims`; ready/attested 0/0 (plate estimated path still in force — expected).  
6. `autonomía-de-5min` ESC still SpeedyBee with H `declared` 8.0 — untouched.  
7. Reproduced report finding: `bind_esc_from_catalog("skystars_…", base=speedybee_spec)` **leaks** old `height_mm=8.0 source=declared` when new SKU omits the key.

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Accepted / queue | **`bind_esc_from_catalog` stale-property leak on cross-SKU rebind** when new catalog row omits a key the old SKU had. Confirmed independently. Final live state correct because estimate writer overwrote H in the same apply sequence — but bare `cambiar esc` alone would mislabel SpeedyBee H as declared Skystars. Separate ★ (bind hygiene), not this Buy. |
| **N2** | Soft | IC lock #3 also asked to tighten `source_note` pointing at project-only estimated H. Row correctly omits `height_mm`; note text still says H UNKNOWN/omitted without naming this Buy. Optional one-line note follow-up — not a FAIL. |
| **N3** | Process | Empty §0.1 initially → correct B0 pause → Engineer filled bag. Good. IC artifact on disk still showed `height_mm: ?` at review start — Cursor will sync filled bag for record. |
| **N4** | Info | Report INCOMPLETE prompt example uses `9.5 mm` (test fixture). Harmless; live bag is **8**. |

---

## Smoke script (Engineer)

On **`10-min-autonomía`**:

1. Board: ESC box **41×46×8**; identity Skystars KO50A II.  
2. Confirm disclosure path still works: e.g. re-declare `declara el esc estimado 8 mm` → ESTIMADA TEMPORAL copy.  
3. `cabe` / `relaciones` involving ESC → **refuse** / `estimated_dims` (not a false “cabe”).  
4. Confirm `library/esc/_datos.json` still has **no** `height_mm` for this SKU.  
5. FC Skystars (if present) still **no** board box — expected (§0.2 not taken).

---

## Verdict

**PASS WITH NOTES** — implementation matches IC primary locks. Awaiting Engineer smoke ACCEPT to close Buy.

**Queue after ACCEPT:** N1 bind-esc omit-key hygiene ★ (recommended before more cross-SKU ESC rebinds without a follow-up estimate write).
