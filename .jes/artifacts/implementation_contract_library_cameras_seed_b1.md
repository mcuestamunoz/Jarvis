# Implementation Contract — First `library/cameras` seed (`B1-library-cameras-seed`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** 2026-09-18 — Cursor PASS WITH NOTES · Engineer smoke ACCEPT WITH NOTES (vigilancia live)

**Parents:**
- Engineer 2026-09-17: camera like GPS — one real SKU; then “manda IC” + **evaluate ALL global seams** so UX is fluid (last catalog family hurt)
- Pain evidence — [`B1-library-fc-sensors`](implementation_review_library_fc_sensors_b1.md) **N1**: binds existed but IDLE pick stayed free-text → often **no `catalog_ref`**; refresh/rebind lagged until [`B1-catalog-hygiene`](implementation_contract_catalog_hygiene_mission_suggestions_b1.md)
- Pattern to mirror for **pick**: **ESC** (`bind_*` on numbered pick), **not** FC free-text-only apply
- Pattern to mirror for **seed/loader**: `library/sensors/` + `SensorSpec` + `list_sensors`
- Cite locked §0.1 — RunCam Phoenix 2
- Mission mass CLOSED — catalog `mass_g` must refresh `mission_payload_mass_kg`
- M2 mount Continuity — [review PASS WITH NOTES](implementation_review_mission_continuity_mount_endurance_b1.md) · **N3 of that review**: this cameras Buy stays open; M2 does **not** replace `mounted_on` / Continuity mount CTAs

**Type:** Add **`library/cameras/`** with one cited SKU and wire the **complete** catalog lifecycle in **this** Buy: load → list → ayúdame/pick → **bind** → `catalog_ref` + high → mass mirror → **cambiar cámara** rebind → **actualiza la cámara** refresh → omit-key hygiene — so cameras behave like a first-class catalog family from day one.  
**Not** multi-SKU dump · invent mm/g · auto-bind bare “RunCam” · M2 Continuity · VTX · version bump · Conversation Engine · LLM inventing the row · workspace mutate (default tests-only).

**Output:** `.jes/artifacts/implementation_report_library_cameras_seed_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3068** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-library-cameras-seed`** — first camera + **full fluid path** |
| 2 | Folder | Exactly **`library/cameras/_datos.json`** |
| 3 | Row | **Only** §0.1 `runcam_phoenix_2` — project L/W/H + `mass_g` only; TVL/FOV/mA stay in `source_note` |
| 4 | Loader | `CameraSpec` + `get_camera` / `list_cameras` / `has_camera` — `ComponentLibrary` sole reader. Include optional `mass_g` on the dataclass |
| 5 | Schema | Widen `CatalogRef.family` Literal with **`"cameras"`** (match `suggested_key`) |
| 6 | Bind | `bind_camera_from_catalog(sku, *, library=None, base=None)` — ESC shape; `suggested_key="cameras"`; completeness **`high`**; project cited props; **`_merge_base_properties_dropping_stale_catalog_keys`** with `_CAMERA_CATALOG_PROJECTED_KEYS` ⊇ `{length_mm,width_mm,height_mm,mass_g}` |
| 7 | Pick = bind | Numbered catalog pick MUST call **`bind_camera_from_catalog`**, then persist via writer path. **Forbidden:** FC-style “pick → free-text `infer_component_for_key` only” that leaves no `catalog_ref` |
| 8 | Mass mirror | After every successful bind / rebind / refresh that sets `mass_g`, call **`set_mission_component_mass`** (or shared helper that recomputes `mission_payload_mass_kg`). Projecting `properties.mass_g` alone is **not** enough |
| 9 | Assist | List from **`list_cameras()`** (extend `control_identity_catalog_assist` or thin camera sibling — report choice). Session field for suggestions if needed (mirror FC/sensors session shape) |
| 10 | Orchestrator | Wire offer + apply for perception/`cameras` context and/or `ayúdame a elegir cámara`. IDLE acquisition for cameras must reach the same list |
| 11 | Rebind **this Buy** | Extend `catalog_rebind_assist`: `cambiar cámara` / `cambiar camara` / `cambiar camera` → `cameras`; orchestrator branch offers list (hygiene B pattern). Do **not** defer rebind to a follow-on Buy |
| 12 | Refresh **this Buy** | Extend `catalog_refresh_assist` subject nouns + register `"cameras": bind_camera_from_catalog` in **`_REFRESH_BINDERS`**. `actualiza la cámara` / `actualiza la camara` must succeed when bound |
| 13 | Free-text | `cámara RunCam` → **medium**, **no** Phoenix dims/mass, **no** `catalog_ref`. Explicit “Phoenix 2” / sku pick → bound path. Document aliases in report |
| 14 | Preserve on rebind | `base=` keeps `mounted_on` / `declared_box_pose` (same as ESC/FC binds) |
| 15 | Guide | Patch USER_GUIDE: remove “no hay library/cameras”; document pick / `cambiar cámara` / `actualiza la cámara` |
| 16 | Forbidden | Half-land (bind without pick/rebind/refresh) · invent mm/g · bare RunCam→Phoenix · fold into `sensors` · Conversation Engine · version bump · LLM |
| 17 | Live | Default **tests-only**. Optional ★ Path D: rebind vigilancia to `runcam_phoenix_2` |

**Product sentence:**

```text
Puedo elegir RunCam Phoenix 2 de catálogo como el GPS: ficha citada,
caja 19³ mm, 9 g en el AUW, cambiar/actualizar cámara — sin inventar
y sin dejar el bind a medias como pasó con FC.
```

### 0.1 Locked seed row (Engineer paste 2026-09-17)

**Source:** [shop.runcam.com — RunCam Phoenix 2](https://shop.runcam.com/runcam-phoenix-2/)

| JSON field | Value |
|---|---|
| name | `runcam_phoenix_2` |
| manufacturer | `RunCam` |
| model | `Phoenix 2` |
| identity_status | `verified` |
| length_mm / width_mm / height_mm | `19.0` / `19.0` / `19.0` |
| mass_g | `9.0` |
| source_url | `https://shop.runcam.com/runcam-phoenix-2/` |

**`source_note`:**

```text
Engineer cite 2026-09-17: RunCam shop Phoenix 2. Net Weight 9g;
Dimensions 19mm*19mm*19mm → L=W=H=19 (cube as printed). Lens 2.1mm M12
FOV155° (4:3), 1000TVL, 1/2" CMOS, PAL/NTSC, 4:3/16:9, DC 5-36V,
Current 200mA@5V / 85mA@12V — citation only; not power_w this Buy (M3).
Housing ABS. No mount-hole pattern claimed. Not a generic "RunCam" brand bind.
```

### 0.2 Critical design fork (do not repeat FC mistake)

```text
FC/GPS land:  library + bind functions, but pick often free-text → weak catalog_ref
ESC path:     list → pick → bind_*_from_catalog → catalog_ref + high
Cameras:      MUST follow ESC path + mass mirror + rebind/refresh in THIS Buy
```

### 0.3 Global seam checklist (implementer — all required)

| Seam | Required |
|---|---|
| `library/cameras/_datos.json` | ✓ |
| `library.py` CameraSpec + list/get/has | ✓ |
| `CatalogRef.family` += `cameras` | ✓ |
| `bind_camera_from_catalog` + omit-key merge | ✓ |
| `_REFRESH_BINDERS["cameras"]` | ✓ |
| Assist `list_cameras` + orchestrator offer/apply (**bind** on pick) | ✓ |
| `catalog_rebind_assist` cámara nouns + IDLE branch | ✓ |
| `catalog_refresh_assist` cámara nouns | ✓ |
| Mass mirror after bind/rebind/refresh | ✓ |
| USER_GUIDE patch | ✓ |
| Free-text medium regression | ✓ |
| Board box from L×W×H (existing projector — regression test) | ✓ |

---

## 1. You (Claude)

1. Seed JSON from §0.1.  
2. Loader + schema + bind (omit-key) + refresh binder.  
3. Assist + orchestrator pick **via bind** + rebind + refresh.  
4. Mass mirror on all write paths that set catalog `mass_g`.  
5. Tests T1–T8 + E1–E8 below + guide + report (call out fork §0.2).  
6. No version bump. No invent. No workspace write unless ★ Path D.

**STOP if** pick path would ship without `catalog_ref`, or rebind/refresh deferred “like FC N1”.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `list_cameras()` length 1; get `runcam_phoenix_2` |
| T2 | `bind_camera_from_catalog` → `cameras` + `catalog_ref` + 19³ + `mass_g=9` + high |
| T3 | Free-text `cámara RunCam` → medium, no seed mm/g, no `catalog_ref` |
| T4 | Assist/list exposes sku |
| T5 | Bind → `mission_payload_mass_kg` ≈ 0.009 (P1) |
| T6 | Omit-key: base had extra catalog key new row omits → dropped (synthetic OK) |
| T7 | Sensors/FC rebind+refresh regressions still green |
| T8 | Full pytest; `0.4.1` |
| E1 | Orchestrator: help-choose / list → pick → **`catalog_ref` present** + high + mass mirror |
| E2 | `cambiar cámara` → rebind offer |
| E3 | Bound then `actualiza la cámara` → refresh succeeds + mirror intact |
| E4 | Rebind `base=` preserves `mounted_on` / pose if set |
| E5 | Projector/box: bound cameras → box 19³ (same class as FC/sensor projector test) |
| E6 | Direct write of `mission_payload_mass_kg` still blocked (mirrored param) |

---

## 3. Smoke (Engineer)

1. `library/cameras/_datos.json` on disk.  
2. Declare/pick Phoenix 2 from catalog → `estado` high + 19 mm + 9 g; AUW moves.  
3. `cambiar cámara` → list again.  
4. `actualiza la cámara` → ok.  
5. Separate: `cámara RunCam` still medium without false Phoenix.  
6. Optional: vigilancia rebind to seed.

**ACCEPT when:** full loop works; no half-wired bind; no invented numbers.

---

## 4. Out of scope

| Item | Note |
|---|---|
| M2 mount + endurance Continuity | Already separate Buy (PASS WITH NOTES / smoke) — not owned here |
| M3 `power_w` from 200mA@5V | Later |
| More camera SKUs | Add rows later |
| VTX / radio catalog | Separate |
| Workspace migrate vigilancia | Only if ★ Path D |

---

## 5. Done when

- [x] Cite row locked (§0.1)  
- [x] Engineer ★ (full-path locks)  
- [x] library + **fluid** bind/pick/rebind/refresh + mass mirror + T/E tests + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_library_cameras_seed_b1.md)  
- [x] Engineer smoke ACCEPT WITH NOTES (vigilancia 2026-09-18) — pick/rebind OK; display `(SKU sin resolver)` soft; `actualiza` not exercised in transcript

---

## 6. Handoff

```text
Engineer → smoke cameras §3 (+ optional M2 §3 same session)
Cursor   → close on ACCEPT
Cola     → M3 / M7 when smokes land
```
