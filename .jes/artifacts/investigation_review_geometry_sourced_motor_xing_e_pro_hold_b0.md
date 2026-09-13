# Investigation Review — #4d XING-E reopen HOLD (Path C)

**Date:** 2026-09-11  
**Reviewer:** Cursor (JES Engineer Interface)  
**Contract:** [implementation_contract_geometry_sourced_motor_xing_e_pro_b1.md](implementation_contract_geometry_sourced_motor_xing_e_pro_b1.md)  
**Report:** [implementation_report_geometry_sourced_motor_xing_e_pro_b1.md](implementation_report_geometry_sourced_motor_xing_e_pro_b1.md) (reopen section)

## Verdict

**PASS** · Path **C HOLD** accepted. No seed. No code. Suite/version untouched.

Engineer judgment to stay on HOLD stands even though a stronger live OEM chart URL now exists (see N1). Revisit Path A later if desired; do not treat HOLD as rejecting the finding’s *accuracy*.

---

## Checklist

| Criterion | Result |
|---|---|
| No `library/motores` / workspace / tests mutation | **Pass** — no `xing` / `iflight_xing` SKU in catalog |
| Path C honored (no self-★) | **Pass** |
| HD-005 left orthogonal (craft) | **Pass** |
| PRIORIDAD / report document `shop.iflight.com` lead | **Pass** |
| Smoke not blocked on XING seed | **Pass** — use existing catalog motor |

---

## Notes

### N1 — Live chart URL is real (distinct from earlier 404 path)

Cursor independent check (2026-09-11):

- `…/image/cache/catalog/product/XING-E-Pro-2207/2450KV-1000x1000.jpg` on `shop.iflight.com` → **404** (the path Cursor warned about earlier).
- `https://shop.iflight.com/image/catalog/TEST%20REPORT/XING-E-Pro-2207-2450KV.png` → **HTTP 200**, PNG archived at `.jes/artifacts/refs/xing_e_pro_2207_2450kv_shop_iflight_TEST_REPORT.png`.
- Product page `…/xing-e-pro-2207-2-6s-fpv-nextgen-motor-pro874` → **200**.

So Claude’s reopen finding is **stronger than the dead `image/cache/…` path**. Under the IC’s literal Path A wording it is a credible Level-1 candidate. Engineer still chose HOLD — **valid**. Future reopen: start from this TEST REPORT PNG URL, not the 404 cache path.

### N2 — Smoke motor status

XING-E is **not** in catalog and **not** bound on any workspace project. New smoke project `autonomía-15min-d2fe43e72976` has architecture keys but motors `catalog_ref=None`, `completeness=low`, no `per_motor_max_thrust_n`. Continue smoke with a catalog motor that already has `thrust_n` (e.g. `emax_rs2205_2300` / RaceSpec `emax_rs2205s_2300`).

---

## Disposition

| Item | Action |
|---|---|
| #4d | **HOLD** — accepted |
| Path A revisit | Optional later using TEST REPORT PNG URL |
| Smoke #4* | Proceed with EMAX (or other seeded motor) — **not** XING |
