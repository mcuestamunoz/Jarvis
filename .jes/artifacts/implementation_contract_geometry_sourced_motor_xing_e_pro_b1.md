# Implementation Contract — #4d Sourced motor iFlight XING-E Pro 2207 2450KV B1 (reopen)

**Project:** Jarvis  
**Date:** 2026-09-11 (reopen) · original 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ under §0.2 path A **or** B  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **★ ACCEPTED — Path A-pending-verification** (Engineer 2026-09-11). Seed with OEM chart `thrust_n=16.46` (6045 @ 16 V); `identity_status=partially_verified`; OP `confidence=0.85`; `source_note` **VERIFICATION PENDING**. Live chart URL on `shop.iflight.com` is `source_reference`. Craft 51466 still HD-005.  
**Implementer:** Cursor — implementing now after this ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Baseline:** package **`0.4.1`** · suite **≥2723** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_motor_xing_e_pro_b1.md` (reopen section)

---

## 0. Engineer Buy (locked)

### Evidence ladder (product policy)

```text
                 EVIDENCE
                    │
        ┌───────────┼────────────┐
        ↓           ↓            ↓
   VERIFIED      ESTIMATED     MEASURED
   manufacturer  model/method  our bench
   published OP  (explicit)    (future)
```

| Level | #4d seed | Meaning |
|---|---|---|
| **1 — Manufacturer (direct)** | **NOT YET** | Live/archived fetch from **iFlight-controlled** URL of the chart |
| **1b — Manufacturer chart mirrored** | **AVAILABLE** | iFlight-branded sheet bytes recovered; host is distributor CDN; historical iFlight path identified but not fetchable now |
| **2 — Estimated** | **OUT** | Craft XING + 51466-3 + 4S |
| **3 — Bench** | **OUT / HD-005** | Craft precision; not this gate |

**Honesty (locked):**

```text
Tenemos el asset del chart (espejo) y la URL histórica iFlight identificada.
No maquillamos el mirror como fuente primaria directa.
Craft Gemfan 51466-3 / 4S sigue sin OP exacto (HD-005).
```

### 0.2 Provenance bag + ★ paths (Engineer chooses)

```text
source_status: manufacturer_chart_mirrored
primary_url_historical: https://shop.iflight-rc.com/image/cache/catalog/product/XING-E-Pro-2207/2450KV-1000x1000.jpg
accessible_copy_url: https://cdn11.bigcommerce.com/s-kgkeg34ccb/product_images/uploaded_images/2450kv-1000x1000-1200x1200.jpg
local_archive: .jes/artifacts/refs/xing_e_pro_2207_2450kv_iflight_chart.jpg
verification: pending_primary_archive

# Historical origin evidence (not a fetch of the bytes from iFlight today):
#   Reddit r/fpv 2022 — user linked the shop.iflight-rc.com chart URL as
#   "the motor chart for that motor":
#   https://www.reddit.com/r/fpv/comments/v6gi56
# Distributor page that retains the same asset name:
#   https://rotorvillage.ca/iflight-xing-e-PRO-2207-1800-2450kv-motor/
# REJECTED as live op_source: shop.iflight-rc.com (TLS/404/insecure — Engineer)

# Chart content verified from accessible_copy (Cursor 2026-09-11):
#   Title: iFlight XING-E Pro 2207 2450KV 4S
#   Peak row: 6045 / 16 V / 100% → 42.63 A / 1679 gf / 682.1 W
```

| Path | When ★ | Catalog labeling |
|---|---|---|
| **A — Strict Level-1** | Only after Wayback / OEM re-host / Engineer-held primary archive of `primary_url_historical` (or equivalent iFlight URL) fetches successfully | `source_type: manufacturer_test` · `source_reference: <primary>` · note may mention mirror as corroboration |
| **B — Seed on mirrored chart** | Engineer explicitly ★ path B now | `source_type: manufacturer_test` **with mandatory** `source_note` leading with `manufacturer_chart_mirrored` + historical URL + accessible_copy_url + `verification: pending_primary_archive`. **Do not** claim “fetched live from iFlight”. Confidence ≤ **0.85** unless Engineer ★ higher |
| **C — No seed** | Default while HOLD | Numbers stay in IC bag only; wizard uses EMAX / numeric thrust |

**Current disposition (Engineer 2026-09-11 evening):** ★ **Path A-pending-verification** — use live `shop.iflight.com` TEST REPORT chart as `source_reference`; seed `thrust_n` from 6045 peak; mark **VERIFICATION PENDING** in notes (`partially_verified`, confidence 0.85). Move smoke forward with real purchase stack. Craft 51466 remains HD-005.

| # | Decision | Lock |
|---|---|---|
| 1 | SKU | `iflight_xing_e_pro_2207_2450` (2450 only) |
| 2 | Leave | EMAX + Hobbywing 2207 untouched |
| 3 | Geometry | φ28.5 · `height_mm=33.1` (body 19.7 on chart → note) |
| 4 | Shaft | `shaft_diameter_mm=5` (internal 4 / M5 → note) |
| 5 | Stator | 22 / 7 from chart |
| 6 | Electrical | KV 2450 · I 42.63 · P 682.1 · R 46.8 mΩ note |
| 7 | Mass | 33.8 g |
| 8 | Thrust numbers (held) | 6045 @ 16 V / 100% → **16.46 N** / 42.63 A / 682.1 W |
| 9 | Craft | No 51466 OP this Buy |
| 10 | HD-005 | Remains **craft** follow-on — **not** closed by recovering this chart |
| 11 | Out | Relabel mirror as direct primary · invent 51466 · borrow EMAX thrust · version bump |

**Product sentence:**

```text
El chart OEM está recuperado como asset espejado; la URL iFlight histórica
está identificada pero no archivada funcionalmente. No ★ Level-1 directo
hasta primary archive — o ★ path B con disclosure mirrored.
```

### 0.1 Identity (unchanged — OK)

```text
source_url: https://iflight-rc.eu/es-es/products/xing-e-pro-2207-fpv-motor
# EU page = identity/electrical; thrust sheet is the chart asset above
```

### Catalog mapping (only after path A or B ★)

```text
thrust_n (root): 16.46
operating_points[0]:
  propeller_sku: null
  voltage_v: 16.0
  thrust_n: 16.46
  current_a: 42.63
  power_w: 682.1
  fallback_only: true
  source_type: manufacturer_test
  confidence: 0.95 if path A else ≤0.85 if path B
  source_reference: <primary if A | accessible_copy_url if B>
  source_note: |
    MUST state path A or B. If B: manufacturer_chart_mirrored;
    primary_url_historical=shop.iflight.../2450KV-1000x1000.jpg;
    accessible_copy=cdn11.bigcommerce...; verification pending_primary_archive;
    peak 6045 @ 16V/100% = 1679 gf / 42.63 A / 682.1 W.
    NOT craft Gemfan 51466-3 + 4S (HD-005).
```

**design_space (suggested):** `{min_thrust_n: 13, max_thrust_n: 20, kv_min: 2300, kv_max: 2600}`

---

## 1. You (implementer)

1. **Do nothing** until Engineer ★ path **A** or **B**.  
2. Path A: verify primary archive fetch before seed. Path B: seed only with mirrored disclosure in `source_note`.  
3. Insert SKU; leave EMAX/Hobbywing stable; rebind designated project; tests; report; sync HD-005 (craft, still open).  
4. **STOP** if asked to call the CDN “primary iFlight fetch” without path B disclosure.

---

## 2. Intent

```text
Chart asset mirrored + historical iFlight URL identified
        ↓
HOLD — pending_primary_archive (strict)  OR  Engineer ★ path B
        ↓
(seed only after A or B)
        ↓
SKU + rebind; craft 51466 → still HD-005
```

---

## 3. Tests (minimum) — after ★ only

| ID | Assert |
|---|---|
| T1 | Geometry/electrical/`thrust_n≈16.46` per bag |
| T2 | OP fallback row; `source_note` contains **6045** and **not** craft 51466; if path B → note contains `mirrored` / historical URL |
| T3–T6 | Same as prior reopen IC (bind disk; EMAX/Hobbywing stable; no 1800/2750; no invented 51466 OP; resolve honesty) |

---

## 4. Files (expected) — after ★ only

| Path | Action |
|---|---|
| `library/motores/_datos.json` | insert SKU |
| Designated workspace state | motors rebind |
| `tests/test_geometry_sourced_motor_xing_e_pro_b1.py` | write |
| `.jes/artifacts/refs/xing_e_pro_2207_2450kv_iflight_chart.jpg` | already archived |
| docs / report / state | sync |
| ui / version / OP schema | **no** |

---

## 5. Smoke — after land

XING-E Ø28.5; thrust labeled per path A/B honesty; Gemfan 51466 ≠ 6045 OP.

---

## 6. Out of scope

Closing HD-005 (craft) · inventing 51466 OP · Conversation Engine · version bump

---

## 7. Handoff

```text
Engineer now → keep hunting Wayback / OEM primary archive of historical URL
            → OR explicitly ★ path B (mirrored seed with disclosure)
            → OR continue smoke #4* with EMAX (path C)
Cursor/Claude → implement only after A or B ★
```

**Clarification:** Recovering this chart does **not** close [HD-005](../../docs/HARDWARE_DEBT.md#hd-005--craft-op-xing-e--gemfan-51466-3--4s-4d-follow-on). HD-005 is craft combo (51466-3 + 4S) estimate/bench.
