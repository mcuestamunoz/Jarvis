# ★6 Validation Case — Operating Point dataset (APPROVED — final)

**Status:** ★6 **APPROVED** with Engineer corrections (2026-08-21) · **READY FOR IC**  
**Rule:** Real sourced numbers only. Never invent. Never label estimate as `manufacturer_test`.

---

## Locks (final)

| Decision | Lock |
|---|---|
| Physical OPs = motor + prop + voltage | YES (OP-1, OP-2, OP-3) |
| OP-0 `fallback_only` for CLI without prop-bind | YES — resolver must preserve flag |
| EMAX test-table motor SKU | **`emax_rs2205s_2300`** (RS2205**S**) — do **not** attach these OPs to `emax_rs2205_2300` |
| Existing `emax_rs2205_2300` | Leave as legacy Model-1 row (non-S); no OP seed from RS2205S table |
| SunnySky OP motor | **`sunnysky_r2205_2500`** (new) — never overwrite `sunnysky_r2305_2500` |
| OP-3 RPM | **27082** (from published table) |
| `efficiency_gf_per_w` | g/W only — never treat as η∈[0,1] |
| Multi-match same motor+prop+V | v1: **max thrust_n** + `selection_reason="v1_max_thrust"` (provisional) |
| Resolver quality enum | **Required:** `exact_operating_point` \| `fallback_operating_point` \| `legacy_estimate` |

---

## Catalog actions for IC

| SKU | Action |
|---|---|
| `emax_rs2205s_2300` | **ADD** new motor row + `operating_points[]` (OP-0/1/2) |
| `emax_rs2205_2300` | **KEEP** unchanged (legacy RS2205 non-S / Model-1); no RS2205S OP data |
| `sunnysky_r2205_2500` | **ADD** new motor row + OP-3 |
| `sunnysky_r2305_2500` | **KEEP** untouched |
| `hq_5045_bn` | **ADD** propeller (5.0×4.5, tags for HQ5045 BN naming) |
| `gf_5045x3` | **ADD** propeller (5.0×4.5 tri-blade GF5045×3) |

---

## Approved OP rows

### OP-1 — EMAX RS2205S 2300KV / 16V / 5045

```text
motor_sku:        emax_rs2205s_2300
propeller_sku:    hq_5045_bn
voltage_v:        16.0
rpm:              23080
thrust_n:         9.1986
current_a:        25.0
power_w:          400.0
efficiency_gf_per_w: 2.35
fallback_only:    false
source_type:      manufacturer_test
confidence:       0.98
source_reference: https://www.getfpv.com/emax-rs2205s-2300kv-racespec-motor-cw.html
source_note:      EMAX RS2205S sample test (GetFPV). 16 V, 5045, 25 A, 938 g, 400 W, 23080 RPM.
approved_by:      Engineer research pass
approved_date:    2026-08-21
```

### OP-2 — EMAX RS2205S 2300KV / 16V / 5045 (high load)

```text
motor_sku:        emax_rs2205s_2300
propeller_sku:    hq_5045_bn
voltage_v:        16.0
rpm:              23560
thrust_n:         9.7086
current_a:        27.0
power_w:          432.0
efficiency_gf_per_w: 2.29
fallback_only:    false
source_type:      manufacturer_test
confidence:       0.98
source_reference: https://www.getfpv.com/emax-rs2205s-2300kv-racespec-motor-cw.html
source_note:      Same table, higher load: 27 A, 990 g, 432 W, 23560 RPM.
approved_by:      Engineer research pass
approved_date:    2026-08-21
```

### OP-3 — SunnySky R2205 2500KV / 14.8V / GF5045×3

```text
motor_sku:        sunnysky_r2205_2500
propeller_sku:    gf_5045x3
voltage_v:        14.8
rpm:              27082
thrust_n:         12.5525
current_a:        40.0
power_w:          592.0
efficiency_gf_per_w: 2.16
fallback_only:    false
source_type:      manufacturer_test
confidence:       0.97
source_reference: https://img.banggood.com/file/products/20181018062904ER22052500KV.pdf
source_note:      R2205 KV2500 table: GF5045x3, 14.8 V, 40 A, 1280 gf, 592 W, 27082 RPM. Also listed on SunnySky USA product page.
approved_by:      Engineer research pass
approved_date:    2026-08-21
```

### OP-0 — EMAX RS2205S / 4S headline fallback (NOT a complete OP)

```text
motor_sku:        emax_rs2205s_2300
propeller_sku:    null
voltage_v:        16.8
rpm:              null
thrust_n:         10.0420
current_a:        null
power_w:          null
efficiency_gf_per_w: null
fallback_only:    true
source_type:      manufacturer_test
confidence:       0.95
source_reference: https://shop.emaxmodel.com/products/emax-rs2205-racespec-motor-cooling-series
source_note:      FALLBACK ONLY. Headline 1024 gf max at 4S with HQ5045 BN. Resolver MUST return resolution_type=fallback_operating_point. Not propeller-independent physics.
approved_by:      Engineer research pass
approved_date:    2026-08-21
```

---

## Resolver contract (must be code, not docs-only)

```text
resolution_type ∈ {
  exact_operating_point,      # motor+prop+voltage match, fallback_only=false
  fallback_operating_point,   # fallback_only=true row (OP-0)
  legacy_estimate             # bare MotorSpec.thrust_n
}

priority:
  1. exact matches → if multiple, pick max thrust_n, selection_reason="v1_max_thrust"
  2. fallback_only row for motor (+ voltage if present)
  3. legacy MotorSpec.thrust_n → resolution_type=legacy_estimate, source_type=estimated
```

CLI/`estado` must never show a fallback or legacy result as if it were an exact OP.

---

## Green light

**★6 APPROVED — READY FOR P2-1 IMPLEMENTATION CONTRACT**

---

**End of ★6 approval (final).**
