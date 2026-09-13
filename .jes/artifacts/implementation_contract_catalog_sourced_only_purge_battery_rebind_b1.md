# Implementation Contract — Catalog sourced-only purge + battery rebind P0

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ★ (Engineer)

**Type:** Data honesty purge of unsourced catalog SKUs + fix battery rebind list/SKU bind (Field Note B1+B2).  
**Parents:** [field_note_smoke_rebind_battery_sensor_bugs_b0.md](field_note_smoke_rebind_battery_sensor_bugs_b0.md) · Engineer: *eliminar todo componente sin datos REALES / URL*.

**Product base:** tag **`v0.4.1`** (+ pending landings). Suite viva ~**2785**.

**Workflow:** Engineer ★ → Claude implements + report → Cursor review → Engineer smoke (`cambiar bateria` shows Tattu; free-text SKU binds; no generic LiPo without URL).

---

## 0. Engineer ratification (locked intent — awaiting ★)

| ★ | Decision |
|---|---|
| **★1** | **Sourced-only product catalog.** A buyable component seed may remain in `library/{baterias,motores,helices,frames,esc,kit_hardware}/_datos.json` **only if** it has a non-empty `source_url` (manufacturer or retailer product page, or the cited authority page already used as identity ground truth). No inventing URLs. |
| **★2** | **Delete** rows that fail ★1. Do **not** keep “placeholder” / anonymous `lipo_*` / `generic_*` rows “for tests”. Redirect tests to remaining sourced SKUs. |
| **★3** | **`library/materiales`** is **out of scope** (material types, not buyable SKUs). |
| **★4** | **Battery rebind P0 (B1+B2):** after purge, assist lists **all** remaining batteries (no hard `limit=10` that truncates). Free-text SKU token and `ayúdame a elegir` must work in the battery rebind / DEFINE offer session. |
| **★5** | **Do not invent** replacement SKUs in this Buy. If a family would go empty, stop and ask Engineer — inventory below shows none empty after purge. |
| **★6** | Sensors / FC identity tables (`aerial.py` maps) are **out of scope** unless they already live as `_datos.json` product rows (they do not today). **B3 sensors rebind** stays a separate P1 Buy. |

---

## 1. Problem / intent

### 1.1 Smoke (Engineer)

1. `cambiar bateria` omits `tattu_2300mah_4s_75c_xt60` because `build_battery_catalog_suggestions(..., limit=10)` truncates a 12-row library.  
2. Typing the Tattu SKU / `ayúdame a elegir` after rebind loops the define Brief.  
3. Engineer policy: **do not show a list of anonymous LiPo packs without real URL** — same bar for motors, props, frames, ESC, kit.

### 1.2 Target

```text
library product families
  → only rows with source_url
  → assist lists = full remaining catalog for batteries (and honest limits for motors/props from that set)
  → cambiar bateria → numbered list includes tattu_… + gens_ace_…
  → user types tattu_2300mah_4s_75c_xt60 → bind_battery_from_catalog
  → ayúdame a elegir (same session) → re-shows list → pick N works
```

---

## 2. Inventory (Cursor 2026-09-13 — gate = non-empty `source_url`)

### 2.1 KEEP (sourced)

| Family | SKUs |
|---|---|
| **baterias (5)** | `gens_ace_2200mah_3s_35c_gtech`, `tattu_2300mah_4s_75c_xt60`, `lipo_4s_1500mah` (CNHL), `lipo_4s_5000mah` (Spektrum), `lipo_6s_6000mah` (GNB) |
| **motores (3)** | `emax_rs2205s_2300`, `sunnysky_r2205_2500`, `iflight_xing_e_pro_2207_2450` |
| **helices (6)** | `gemfan_5045_hbn`, `dal_7040`, `apc_10x6_ep`, `hq_5045_bn`, `gf_5045x3`, `gemfan_hurricane_mck_51466_3_v2` |
| **frames (6)** | all current (already sourced) |
| **esc (2)** | all current |
| **kit_hardware (2)** | all current |

### 2.2 DROP (no `source_url`)

| Family | SKUs |
|---|---|
| **baterias (7)** | `lipo_2s_850mah`, `lipo_3s_1300mah`, `lipo_3s_2200mah`, `lipo_4s_10000mah`, `lipo_6s_10000mah`, `lipo_6s_22000mah`, `lipo_12s_16000mah` |
| **motores (20)** | `sunnysky_x2216_11`, `t-motor_mn3110_700`, `emax_rs2205_2300`, `sunnysky_x2212_980`, `t-motor_mn4014_400`, `generic_920kv`, `brotherhobby_avenger_2500`, `t-motor_f80_2400`, `sunnysky_v4006_740`, `t-motor_mn5008_340`, `emax_eco_ii_2207_1700`, `hobbywing_xrotor_2207_2450`, `t-motor_antigravity_mn4006_380`, `sunnysky_r2305_2500`, `generic_1500kv`, `generic_700kv`, `t-motor_u8_170`, `sunnysky_x2820_900`, `emax_mt2216_810`, `brotherhobby_returner_r5_2700` |
| **helices (13)** | `gemfan_5030`, `gemfan_6040`, `apc_8x4_5`, `apc_10x4_5`, `apc_11x5_5`, `tmotor_12x4`, `tmotor_13x4_4`, `tmotor_15x5`, `tmotor_16x5_4`, `tmotor_17x5_8`, `tmotor_18x6_1`, `tmotor_22x6_7`, `tmotor_24x7_2` |

**Note:** KEEP batteries that still use `lipo_*` **keys** but have real manufacturer + `source_url` are **allowed** this Buy (SKU rename optional polish — not required). Do **not** delete them.

---

## 3. Code / assist requirements

### 3.1 Data

1. Remove DROP rows from the three `_datos.json` files.  
2. Do **not** mutate KEEP row physics / URLs except if a test-only comment in `source_note` must stop referring to a deleted sibling (optional cleanup).  
3. Live workspace projects that still `catalog_ref` a DROP SKU are **not** auto-migrated this Buy (disclose in report). Engineer rebinds on next walk if needed.

### 3.2 Battery assist / rebind (B1+B2)

| ID | Requirement |
|---|---|
| **Bat-list** | `build_battery_catalog_suggestions`: default so **all** library batteries appear (e.g. `limit=None` / `limit=len(list)` / raise default ≥ catalog size). Document the new contract; remove the stale “10 = full v1 catalog” comment. |
| **Bat-sku** | When battery rebind / DEFINE-missing / catalog-offer session is active, free-text that contains a live SKU (`detect_battery_sku_token`) → `bind_battery_from_catalog` (reuse existing binder). |
| **Bat-help** | `ayúdame a elegir` / `is_help_choose_phrase` in that same session **re-offers** the numbered list (does not loop the plain define Brief alone). |
| **Bat-pick** | Number pick against the offered list still works. |

Prefer thin changes in `battery_catalog_assist.py` + orchestrator offer/apply / rebind session paths already used by motors/props — **no new Conversation Engine**.

### 3.3 Motor / propeller assists

- After purge, any hardcoded tip lists that name DROP motors (e.g. Continuity “candidatos que sí declaran W: sunnysky_r2305… brotherhobby…”) **must** be updated to remaining sourced motors that actually declare W (likely `sunnysky_r2205_2500`, `iflight_xing_e_pro_2207_2450`, … — verify from KEEP rows, do not invent W).  
- Motor/prop suggestion `limit` may stay design-space filtered, but the **pool** is only KEEP SKUs.

### 3.4 Guardrail (recommended, small)

Add a unit test (or extend `test_component_library` / catalog foundation) asserting:

```text
for every product family in {baterias, motores, helices, frames, esc, kit_hardware}:
  every seed row has non-empty source_url
```

So the catalog cannot silently re-grow anonymous LiPo again.

---

## 4. Tests

### 4.1 New / extended

| Test | Assert |
|---|---|
| Catalog sourced-only gate | every product seed has `source_url` |
| Battery list completeness | `build_battery_catalog_suggestions` includes `tattu_2300mah_4s_75c_xt60` and `gens_ace_…` when both exist |
| Battery rebind SKU | IDLE/`cambiar bateria` session + free-text Tattu SKU → bind succeeds |
| Battery rebind help | same session + help-choose → list text includes Tattu → pick binds |

### 4.2 Redirect (do not weaken)

Any test that referenced a DROP SKU must switch to a **KEEP** SKU with analogous role when possible, e.g.:

| Dropped (examples) | Prefer redirect |
|---|---|
| `lipo_6s_10000mah` / anonymous Wh packs | `lipo_6s_6000mah` or `tattu_…` / `gens_ace_…` as fits the assertion |
| `sunnysky_r2305_2500` / `emax_rs2205_2300` | `sunnysky_r2205_2500` / `emax_rs2205s_2300` / `iflight_xing_e_pro_2207_2450` |
| `generic_*` motors | sourced motor or drop the “generic” scenario if it only existed to prove invention — disclose |
| `gemfan_5030` / bare APC/T-Motor props | KEEP prop with URL |

Disclose every redirected golden in the implementation report. **Forbidden:** delete assertions only to make the suite pass; **forbidden:** re-seed DROP rows under a new name without URL.

### 4.3 Suite

Targeted new tests green + full suite green before report. Update suite count in report.

---

## 5. Explicit non-goals

- Sensors / `cambiar sensor` rebind (Field Note **B3**)  
- Frame rebind stale wb/body (**B4**)  
- Continuity ASSEMBLY READY vs bloque copy (**B5**) beyond fixing DROP SKU names in tips  
- Estimated-temporary plate / layout cola  
- Renaming KEEP `lipo_*` keys to branded SKU ids  
- Fetching live pages / verifying URLs still HTTP 200  
- Auto-rebinding live `workspace/` projects off DROP refs  

---

## 6. Files (expected)

| Path | Change |
|---|---|
| `library/baterias/_datos.json` | delete 7 DROP |
| `library/motores/_datos.json` | delete 20 DROP |
| `library/helices/_datos.json` | delete 13 DROP |
| `src/jarvis/core/battery_catalog_assist.py` | list limit / comment |
| `src/jarvis/core/orchestrator.py` (and/or thin assist) | Bat-sku + Bat-help in rebind session |
| Continuity / tip copy that hardcodes DROP motor names | update to KEEP |
| `tests/test_*` | gate + rebind + redirects |
| `.jes/artifacts/implementation_report_catalog_sourced_only_purge_battery_rebind_b1.md` | Claude |

---

## 7. Acceptance (Engineer smoke)

```text
cambiar bateria
  → list shows all 5 KEEP batteries including tattu_2300mah_4s_75c_xt60
  → type tattu_2300mah_4s_75c_xt60 → bind OK (not define Brief loop)
  → (or) ayúdame a elegir → list → pick N → bind OK

cambiar motor / ayúdame a elegir
  → no generic_920kv / anonymous motors without URL

estado / Continuity tips
  → no recommendations naming deleted SKUs
```

---

## 8. Done when

1. DROP rows gone; KEEP unchanged in physics.  
2. Sourced-only gate test green.  
3. Battery list + SKU + help-choose paths green.  
4. Suite green; report lists redirects and any live-project DROP refs left.  
5. Cursor review PASS.  
6. Engineer smoke §7.

---

## 9. Open for Engineer ★ only

Confirm ★1–★6. Optional: also ★-rename KEEP `lipo_4s_1500mah` / `lipo_4s_5000mah` / `lipo_6s_6000mah` to branded keys in a follow-on (not this IC unless ★ expands).
