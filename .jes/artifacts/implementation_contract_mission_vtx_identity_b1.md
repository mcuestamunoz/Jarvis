# Implementation Contract — VTX identity + first catalog seed (`B1-mission-vtx-identity`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **ACCEPT CLOSED** (Engineer smoke 2026-09-18)

**Parents:**
- Engineer 2026-09-18: projects are **Jarvis smoke**, not “finish the drone”; paste HGLRC Zeus 800 cite → open Buy
- Engineer: cámara FPV ⇒ hace falta nombrar VTX (aunque aún no se compre en el taller)
- Mission payload identity — `cameras` / `radio_module`; **radio ≠ VTX**
- Pattern: [`B1-library-cameras-seed`](implementation_contract_library_cameras_seed_b1.md) — ESC-shaped pick→bind + mass mirror + rebind/refresh
- Mass/power writers — `set_mission_component_mass` / `set_mission_component_power` today only `cameras`/`radio_module` — **this Buy widens mission keys to include `vtx`** for mass (and optional later power)

**Type:** Add architecture home + identity for **`vtx`**, seed **`library/vtx/`** with one cited SKU (HGLRC Zeus 800), and wire the **complete** catalog lifecycle: load → list → ayúdame/pick → **bind** → `catalog_ref` + high → **mass mirror** → cambiar/actualiza VTX. Continuity can nudge when misión tiene cámara y no hay VTX.  
**Not** inventing DC `power_w` from RF **mW** (different physics) · SmartAudio/Tramp control UI · frequency plan · folding into `radio_module` · version bump · Conversation Engine · LLM inventing the row · workspace mutate (default tests-only).

**Output:** `.jes/artifacts/implementation_report_mission_vtx_identity_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3134** · UI ≥**105** (or current green at ★)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mission-vtx-identity`** — identity + first VTX catalog seed + fluid path |
| 2 | Key | Component key **`vtx`** (`suggested_key="vtx"`). Never overload `radio_module` / `cameras` |
| 3 | Block | New **`video_link`** → `["vtx"]`. Aliases: `vtx`, `vídeo`/`video` (tune), `enlace de video`, `transmisor de video`, `fpv vtx` — report exact set |
| 4 | Perception | Stays `["cameras"]` only — no forced VTX stub on camera-only projects |
| 5 | Folder | Exactly **`library/vtx/_datos.json`** |
| 6 | Row | **Only** §0.1 `hglrc_zeus_800` — project L/W/H + `mass_g` only. RF levels / Tramp / MMCX / mounting patterns stay in `source_note` |
| 7 | Loader | `VtxSpec` + `get_vtx` / `list_vtx` / `has_vtx` — `ComponentLibrary` sole reader. Optional `mass_g` on dataclass |
| 8 | Schema | `CatalogRef.family` Literal += **`"vtx"`** |
| 9 | Bind | `bind_vtx_from_catalog(sku, *, library=None, base=None)` — ESC/camera shape; `completeness="high"`; omit-key merge; `_VTX_CATALOG_PROJECTED_KEYS` ⊇ `{length_mm,width_mm,height_mm,mass_g}` |
| 10 | Pick = bind | Numbered pick **must** call bind; forbidden FC half-land without `catalog_ref` |
| 11 | Mass mirror | Widen mission mass keys to include **`vtx`**. After bind/rebind/refresh that sets `mass_g`, call `set_mission_component_mass` (recompute `mission_payload_mass_kg`). Preserve-manual on same-SKU refresh (camera class) |
| 12 | Power | **Do not** project `power_w` from 800 mW RF. No DC current in cite → no catalog electrical W this Buy. User may later `vtx N W` only if grammar/writers widened — **default this Buy: mass only**; if widening `set_mission_component_power` keys is needed for symmetry, report choice — **prefer mass-only** unless trivial |
| 13 | Rebind / refresh | `cambiar vtx` / `cambiar el vtx` + `actualiza el vtx` this Buy (`_REFRESH_BINDERS["vtx"]`) |
| 14 | Free-text | `vtx HGLRC` / bare `vtx` → medium, **no** Zeus dims/mass, **no** `catalog_ref`. Pick / explicit Zeus → bound path |
| 15 | Continuity | Mission intent + cameras present + no `vtx` → **“Declara VTX (enlace de vídeo)”** (or “Elige VTX de catálogo”). Slot: does not steal mount/autonomy/power camera holes — report position (recommend after camera power / before soft margin, or after camera identity if those cleared) |
| 16 | Guide | USER_GUIDE: VTX ≠ radio control; Phoenix + VTX story; pick Zeus 800 (37×37×5, 4.8 g); honesty RF mW ≠ consumo DC del modelo energético |
| 17 | Forbidden | RF mW → `power_w` · half-land · invent mm/g · fold into radio · Conversation Engine · version bump · LLM |
| 18 | Live | Default tests-only. Smoke: vigilancia add/pick Zeus |

**Product sentence:**

```text
Puedo elegir HGLRC Zeus 800 de catálogo como la cámara: ficha citada,
caja 37×37×5 mm, 4.8 g en el AUW — sin inventar vatios eléctricos
desde los mW de RF.
```

### 0.1 Locked seed row (Engineer paste 2026-09-18)

**Source:** [HGLRC — Zeus 800mW VTX](https://www.hglrc.com/products/hglrc-zeus-800mw-smart-mounting-20-20-30-30-vtx-for-fpv-racing-drone)

| JSON field | Value |
|---|---|
| name | `hglrc_zeus_800` |
| manufacturer | `HGLRC` |
| model | `Zeus 800` |
| identity_status | `verified` |
| length_mm / width_mm / height_mm | `37.0` / `37.0` / `5.0` |
| mass_g | `4.8` |
| source_url | `https://www.hglrc.com/products/hglrc-zeus-800mw-smart-mounting-20-20-30-30-vtx-for-fpv-racing-drone` |

**`source_note`:**

```text
Engineer cite 2026-09-18: HGLRC Zeus 800mW Smart Mounting VTX (OEM page).
Analog 5.8 GHz. RF power levels PIT/25/100/200/400/800 mW — citation only;
NOT projected as electrical power_w (RF output ≠ DC draw; no mA cite this Buy).
Input 6–26 V (2–6S). 5V/2A output. Antenna MMCX. Mount 20×20 / 30×30 M3 —
pattern cited, not a Board hole claim. Dims 37×37×5 mm → L=W=37 H=5.
Weight 4.8 g. Protocol IRC Tramp. Microphone yes. Not a control radio (ELRS).
```

### 0.2 Critical fork

```text
Radio (ELRS)  = control link     → radio_module
VTX (Zeus)    = video link       → vtx / video_link
Cameras seed: list → pick → bind_* → catalog_ref + high + mass mirror
VTX:          MUST follow same path — no half-land
```

### 0.3 Global seam checklist

| Seam | Required |
|---|---|
| `library/vtx/_datos.json` | ✓ |
| `VtxSpec` + list/get/has | ✓ |
| `CatalogRef.family` += `vtx` | ✓ |
| `bind_vtx_from_catalog` + omit-key | ✓ |
| `_REFRESH_BINDERS["vtx"]` | ✓ |
| Assist + orchestrator pick **via bind** + mass mirror | ✓ |
| Rebind/refresh nouns | ✓ |
| Mission mass keys += `vtx` | ✓ |
| Continuity CTA camera-without-vtx | ✓ |
| USER_GUIDE | ✓ |
| Free-text medium regression | ✓ |
| `sku_resolved` / `has_vtx` in BOM display | ✓ |

---

## 1. You (Claude)

1. Seed JSON §0.1 + loader.  
2. Architecture `video_link` + identity rule (free-text medium).  
3. Bind + pick + rebind + refresh + mass mirror + `has_vtx` BOM.  
4. Continuity CTA + guide + report (cite arithmetic / honesty RF≠DC).  
5. Tests T1–T12. No version bump. No RF→W invent.

**STOP if** pick ships without `catalog_ref`, or `power_w` invented from 800 mW.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `list_vtx` length 1; get `hglrc_zeus_800` |
| T2 | Bind → `vtx` + `catalog_ref` + 37×37×5 + `mass_g=4.8` + high |
| T3 | Free-text `vtx HGLRC` → medium, no seed mm/g, no `catalog_ref` |
| T4 | Orchestrator pick → `catalog_ref` + mass mirror (`mission_payload_mass_kg` includes 0.0048) |
| T5 | `cambiar vtx` / `actualiza el vtx` |
| T6 | Preserve manual mass on same-SKU refresh |
| T7 | No `power_w` on bind from RF levels |
| T8 | Continuity CTA when cameras & no vtx; clears when vtx present |
| T9 | `radio_module` / cameras paths unstolen |
| T10 | BOM `[hglrc_zeus_800]` via `has_vtx` |
| T11 | `video_link` resolvable; perception still cameras-only |
| T12 | Full suite; `0.4.1` |

---

## 3. Smoke (Engineer)

On vigilancia (Phoenix already bound):

1. Continuity or manual: `ayúdame a elegir vtx` / B `vtx`.  
2. Pick Zeus 800 → high + 4.8 g in AUW; lista muestra dims/masa.  
3. `cambiar vtx` / `actualiza el vtx` ok.  
4. Free-text `vtx HGLRC` still medium without false Zeus.  
5. Confirm not merged into radio ELRS.

**ACCEPT when:** full fluid path; mass mirrored; no RF mW as electrical W.

---

## 4. Out of scope

| Item | Note |
|---|---|
| DC `power_w` / current cite | Needs mA or Engineer-locked W |
| Tramp/SmartAudio control | Fase C / tools |
| Mount Continuity for vtx | Follow-on |
| More VTX SKUs | Later |
| M7 closeout | After this or parallel |

---

## 5. Done when

- [x] Engineer ★ (implement proceeded)  
- [x] Seed + fluid path + mass + Continuity + T1–T12 + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_mission_vtx_identity_b1.md)  
- [x] Engineer smoke ACCEPT (2026-09-18 — Zeus pick + rebind)

---

## 6. Handoff

```text
Cola → M7 gate (M5 PARK)
```
