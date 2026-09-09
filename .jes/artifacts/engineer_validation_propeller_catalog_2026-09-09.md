# Engineer validation — Propeller catalog (identity + ficha física, 2026-09-09)

**Authority:** Engineer (first external pass on all 17 helix rows)  
**Capturer:** Cursor (JES) — not an Implementation Contract  
**Parents:** [investigation_contract_geometry_propeller_envelope_b1.md](investigation_contract_geometry_propeller_envelope_b1.md) · Claude report [investigation_report_geometry_propeller_envelope_b1.md](investigation_report_geometry_propeller_envelope_b1.md)

**Status:** Engineer evidence for review. **No `src/` edits.**

Engineer lock stated in-session:

> No limitar el enriquecimiento a `mass_g`. Capturar la ficha física que el fabricante publique. Separar geometría, montaje y operación. Si el proveedor no lo publica → UNKNOWN. Nunca una estimación disfrazada de dato físico.

---

## 1. Target vocabulary (Engineer — not seeded)

Conceptual bags (identity / geometry / mounting / physical / operating / environment / evidence). This is a **catalog-v2 wishlist**, not a mandate to add every key in one Buy. Cursor review ranks which keys are B1 vs later.

---

## 2. Census (Engineer)

| SKU | Estado | Engineer note |
|---|---|---|
| `gemfan_5045_hbn` | 🟡 | 5×4.5 HBN exists (Oscar Liang); ficha física primaria incompleta → mass/hub/blades **UNKNOWN** |
| `gf_5045x3` | 🟢/🟡 | PMAB5045-3: 3 palas, ABS, 4.5 g, hub Ø 5 mm, hub H 9.5 mm ([Lemon FPV](https://www.lemonfpv.com/h-pd-629.html)) |
| `hq_5045_bn` | 🔴 | Identificar qué BN; no asumir variante |
| `gemfan_5030` | 🟡 | Variantes; `5 g` no KNOW; no usar 2.82 g hasta fijar 2 vs 3 palas |
| `gemfan_6040` | 🟢/🟡 | Si es 3-blade BN GF nylon: 5.2 g, hub 5 / 9.5 ([EMAX](https://emaxmodel.com/products/2-pairs-gemfan-6040-6x4-inch-glass-fiber-nylon-three-blade-propeller-prop-black)) — actual `7 g` incorrecto **si** esa variante |
| `dal_7040` | 🟢 **LOCKED** | SKU **=** DALProp Cyclone 7040. GetFPV 2026-09-09: 7×4, 2 palas, Pure PC, hub Ø 5 mm, hub H 7 mm, POPO, 5.7 g, CW/CCW. URL: https://www.getfpv.com/dalprop-cyclone-7040-7-2-blade-propeller.html — **next IC seed**, not B0+B1 (`gf_5045x3` only). B0 will drop the unsourced `9 g` first. |
| `apc_8x4_5` | 🟡 | MRP 9.07 g vs MRP(ST) 11.06 g; catálogo `12 g` no VERIFIED; partir SKU |
| `apc_10x4_5` | 🟡 | MR(ST) 16.16 g encontrado; SKU no dice (ST) → no aplicar |
| `apc_11x5_5` | 🟢/🟡 | MR oficial 17.0 g, hub 0.65" / 0.35" ([APC](https://www.apcprop.com/product/11x5-5mr/)); catálogo `22 g` no coincide |
| `tmotor_12x4` | 🟢 | 14.5 g, CF+Epoxy, 2 palas, RPM/thrust/temps ([RobotShop](https://www.robotshop.com/products/t-motor-12-4-carbon-fiber-propeller-pair)) — catálogo `30 g` |
| `tmotor_13x4_4` | 🟡 | Identidad OK; masa 15.7 g **secondary** |
| `tmotor_15x5` | 🟢 | 21±1.5 g, CF, 2 palas, 6 kg, 5200–7000 rpm ([T-MOTOR](https://shop.tmotor.com/products/15-5-polished-carbon-fiber-propeller)) — catálogo `55 g` |
| `tmotor_16x5_4` | 🟡 | CAD/2D oficial; masa 25±1.5 g secondary |
| `tmotor_17x5_8` | 🟢 | 26.5±1.5 g, CF+Epoxy, 7.5 kg, 3500–6000 ([T-MOTOR](https://shop.tmotor.com/products/p17-5-8-carbon-fiber-uav-propeller)) — catálogo `85 g` |
| `tmotor_18x6_1` | 🟢 | 31.5±1.5 g, 8.2 kg, 3000–6000 — catálogo `95 g` |
| `tmotor_22x6_7` | 🔴 | Oficial actual **P22×6.6**, no 6.7. No enriquecer. Identidad primero. ([T-MOTOR](https://shop.tmotor.com/collections/multirotor-uav-propellers) · Download Center P22*6.6) |
| `tmotor_24x7_2` | 🟢 | 56±2 g, hole 10 mm, CF+Epoxy, 15 kg, 2400–4500; STEP oficial — catálogo `190 g` |

Engineer enrich-now list (identity still to lock on 🟡): `gf_5045x3`, `gemfan_6040`, `dal_7040`, `tmotor_12x4`, `tmotor_15x5`, `tmotor_17x5_8`, `tmotor_18x6_1`, `tmotor_24x7_2`.

Engineer: **do not hand-edit all 17 masses yet** — identity migration first.

---

## 3. Spatial ladder (Engineer — later ★)

L1 envelope Ø (already CSS disk) · L2 hub/envelope · L3 manufacturer 2D · L4 official STEP (T-Motor Download Center). Engineer: T-Motor CAD should not be approximated from diameter+pitch **when STEP exists**.

Mapping-path parent already: **STEP visor-only, never SoT in core**. This ladder is named debt, not this envelope Buy.

---

## 4. Explicit Engineer “do not”

Fake KNOW (`mass_g: 55` because it “looks reasonable”). Seed UNKNOWN as a number. Enrich `tmotor_22x6_7` before identity. Collapse APC variants under one SKU.

---

## 5. Next-IC queue (Engineer listings after B0+B1)

| SKU | Status | Seed when |
|---|---|---|
| `dal_7040` | **LOCKED** 2026-09-09 | After current IC: GetFPV Cyclone 7040 — 2 palas, Pure PC, hub 5/7 mm, 5.7 g; POPO in `source_note` (no new schema). Claude re-fetches the URL. |
| `apc_10x6_ep` | **CANDIDATE NEW SKU** | GetFPV APC 10×6EP CW gray — 10×6, 2 palas, nylon long fiber, hub ID 6.35 mm, hub Ø 20.3 mm, hub H 9.9 mm, 20.1 g, POPO no. https://www.getfpv.com/propellers/x-class-propellers/apc-10x6ep-2-blade-propeller-cw-gray.html — **not** `apc_10x4_5` (otro paso / otra serie). |
