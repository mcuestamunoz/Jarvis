# Implementation Report — #4d Sourced motor iFlight XING-E Pro 2207 2450KV B1

Status: **IMPLEMENTED** (reopen ★ Path A-pending-verification) — 2026-09-11  
Parent: `implementation_contract_geometry_sourced_motor_xing_e_pro_b1.md`  
Baseline in: package `0.4.1` · suite was `2723` · UI `83`  
Baseline out: package `0.4.1` (unchanged) · targeted tests **6 passed** · full suite run separately

## Engineer ★ (this land)

Use OEM chart peak thrust for catalog `thrust_n`, disclosed as **VERIFICATION PENDING** (usable for real-component smoke; craft/bench still open). Live iFlight storefront chart:

`https://shop.iflight.com/image/catalog/TEST%20REPORT/XING-E-Pro-2207-2450KV.png`

Peak row: **6045 @ 16 V / 100% → 1679 gf (16.46 N) / 42.63 A / 682.1 W**.  
Not claimed as Gemfan 51466-3 + 4S behavior (HD-005).

## What landed

- New SKU `iflight_xing_e_pro_2207_2450` in `library/motores/_datos.json`
  - Geometry/electrical per bag; `identity_status: partially_verified`
  - Root `thrust_n: 16.46`
  - One `fallback_only` OP, `source_type: manufacturer_test`, `confidence: 0.85`, VERIFICATION PENDING in `source_note`
- Live/smoke rebind: `workspace/autonomía-15min-d2fe43e72976/state.json` motors → new SKU (Ø28.5, thrust 16.46, count 4)
- Tests: `tests/test_geometry_sourced_motor_xing_e_pro_b1.py` (T1–T6)
- Archives: `.jes/artifacts/refs/xing_e_pro_2207_2450kv_shop_iflight_TEST_REPORT.png` (+ prior JPEG mirror)

## Untouched

- `emax_rs2205s_2300`, `hobbywing_xrotor_2207_2450`
- No 1800/2750 SKUs
- No craft 51466 OP row
- No version bump / OP schema keys
- HD-005 remains open (craft combo)

## Historical notes (prior cycles)

Earlier sections of this file documented T3 deferral and Path C HOLD research (BigCommerce mirror, historical `shop.iflight-rc.com`, Engineer HOLD). Those remain audit trail; disposition above supersedes them for implementation.

## Follow-up

- Engineer smoke on 15min: motors card Ø28.5 / thrust honest to chart + pending verification wording
- Bind rest of #4* stack (Tattu, SpeedyBee ESC, Gemfan 51466, FC/GPS)
- HD-005 when craft OP estimate/bench exists
