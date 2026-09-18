# Implementation Contract — Catalog camera `power_w` from cite (`B1-catalog-camera-power-w`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** 2026-09-18 — Cursor PASS WITH NOTES · Engineer smoke ACCEPT

**Parents:**
- M3 CLOSED — [B1-mission-power-w](implementation_contract_mission_power_w_b1.md) · declare path + `mission_accessory_power_w` energy seam live; lock #4 deferred catalog projection
- Cameras seed CLOSED — [B1-library-cameras-seed](implementation_contract_library_cameras_seed_b1.md) · Phoenix 2 row has **mA@V in `source_note` only**
- Engineer 2026-09-18: with those cite numbers, derive `power_w` via **P = I × V** and project like `mass_g`
- Smoke: vigilancia already has Phoenix bound; manual `cámara 1 W` worked; catalog still does not project W

**Type:** Add explicit **`power_w`** on the Phoenix 2 catalog row (Engineer-locked value from cite arithmetic), load it on `CameraSpec`, project it in `bind_camera_from_catalog`, and **mirror** into `mission_accessory_power_w` on bind / rebind / refresh — same discipline as catalog `mass_g` → mission mass mirror.  
**Not** inventing from brand name alone · not scraping the web · not auto-parsing free-text `source_note` at runtime · not radio catalog · not VTX · not version bump · not Conversation Engine · not workspace mutate (default tests-only; Path D optional).

**Output:** `.jes/artifacts/implementation_report_catalog_camera_power_w_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3122** · UI ≥**105** (or current green at ★)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-catalog-camera-power-w`** — Phoenix cite → structured `power_w` → bind + energy mirror |
| 2 | Formula (★ locked) | **P = I × V** from existing cite only. Cite points: `200 mA @ 5 V` → **1.0 W**; `85 mA @ 12 V` → **≈ 1.02 W**. **Locked project value: `power_w = 1.0`** (5 V point; 12 V agrees within 2%) |
| 3 | JSON | Add **`power_w`: `1.0`** to `library/cameras/_datos.json` → `runcam_phoenix_2`. Extend `source_note` one line: `power_w=1.0 from 200mA@5V (P=I×V); 85mA@12V≈1.02W — Engineer ★ 2026-09-18` |
| 4 | Loader | `CameraSpec.power_w: float | None` optional; `_camera_from_raw` reads JSON field — **never** parse mA from `source_note` string at load time |
| 5 | Bind project | Extend `_CAMERA_CATALOG_PROJECTED_KEYS` with `power_w`. `bind_camera_from_catalog` projects `PropertyValue(unit="W", source="declared")` when row has it |
| 6 | Preserve manual | Same class as mass: if `base` already has user-declared `power_w` that differs from catalog, **do not** clobber on rebind/refresh without the existing omit/preserve discipline used for `mass_g` (report exact branch). Fresh bind (no base / no prior power) gets catalog 1.0 |
| 7 | Energy mirror | After every successful camera bind / rebind / refresh that sets catalog or preserved `power_w`, call **`set_mission_component_power`** (or shared helper that recomputes `mission_accessory_power_w`) — projecting `properties.power_w` alone is **not** enough (same as M3 / mass mirror) |
| 8 | Continuity | Bound Phoenix with catalog `power_w` → camera power hole **cleared** (no “Declara potencia de cámara”). Radio still declare-only this Buy |
| 9 | Free-text | `cámara RunCam` / unbound medium → **still no** invented W |
| 10 | Guide | USER_GUIDE: Phoenix pick now brings ~1 W into accessory draw; note formula + that craft rail voltage may differ (honesty). Soften “never converts mA” callout to “catalog rows may carry Engineer-locked `power_w` from cite I×V” |
| 11 | Forbidden | Runtime scrape of `source_note` · inventing W without JSON field · radio auto-W · Conversation Engine · version bump · LLM · claiming validated flight |
| 12 | Live | Default tests-only. Optional Path D: vigilancia already bound — `actualiza la cámara` or rebind to refresh catalog W + mirror |

**Product sentence:**

```text
Al elegir Phoenix 2 de catálogo, Jarvis proyecta 1 W (200 mA × 5 V de la
ficha) al consumo de misión — sin inventar y sin certificar el vuelo.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| JSON `power_w=1.0` + bind + mirror | Parsing mA from prose at runtime |
| Free-text still no W | Multi-SKU dump / radio catalog W |
| Guide honesty | Voltage-rail auto-select 5 vs 12 |

---

## 1. You (Claude)

1. Seed JSON + `CameraSpec` + loader.  
2. Bind project + preserve-manual discipline + mirror on bind/rebind/refresh.  
3. Tests T1–T8 + guide patch + report (cite arithmetic in report §).  
4. No version bump. No invent beyond locked 1.0.

**STOP if** tempted to regex `source_note` for mA instead of reading JSON `power_w`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `get_camera("runcam_phoenix_2").power_w == 1.0` |
| T2 | Fresh `bind_camera_from_catalog` → `properties.power_w == 1.0` + `catalog_ref` |
| T3 | Bind path (orchestrator or writer helper) → `mission_accessory_power_w` includes 1.0 (alone or + radio if set) |
| T4 | Free-text / medium RunCam → no `power_w` |
| T5 | `base` with manual `power_w=2.0` → rebind/refresh preserves 2.0 (mass-class discipline) **or** document if product chooses catalog-wins — **default: preserve manual** |
| T6 | Continuity: bound catalog camera with power → no camera power CTA |
| T7 | Radio-only missing power still CTA when camera power present |
| T8 | Full suite; `0.4.1` |

---

## 3. Smoke (Engineer)

On vigilancia (Phoenix already bound):

1. `actualiza la cámara` **or** `cambiar cámara` → pick 1 again.  
2. Confirm `power_w` / mirror present (message or `estado` evidence).  
3. `calcular` — accessory in play (display may still show 0.7 at 1-decimal; optional declare was already 1 W).  
4. Free-text check on a scratch project: `cámara RunCam` still no W.

**ACCEPT when:** catalog pick carries Engineer-locked 1.0 W into mission accessory without inventing from brand text.

---

## 4. Out of scope

| Item | Note |
|---|---|
| Auto-pick 5 V vs 12 V by craft rail | Needs more schema |
| Radio / VTX catalog W | Separate |
| Changing M3 declare grammar | Already closed |
| Version bump / M7 | Separate |

---

## 5. Done when

- [x] Engineer ★ (implement proceeded)  
- [x] JSON + bind + mirror + T1–T8 + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_catalog_camera_power_w_b1.md)  
- [x] Engineer smoke ACCEPT (2026-09-18)

---

## 6. Handoff

```text
Engineer → smoke §3 on vigilancia
Cursor   → close on ACCEPT
Cola     → M4 / M6 / M7
```
