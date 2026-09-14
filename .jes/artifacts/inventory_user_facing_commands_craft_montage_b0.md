# Phase 0 Inventory — User-facing commands toward craft montage

**Buy:** `B1-user-guide-craft-montage` (Phase 0 of 2)
**Date:** 2026-09-14
**Method:** code + tests only, never chat memory — every row below cites an exact regex, function, or file. Verified against the live `src/jarvis/core/*_assist.py` set, `orchestrator.py`'s `_try_handle_*`/`_offer_*`/`_apply_*` methods, `ui/spatial-board/src/Scene3D.tsx`, `src/jarvis/adapters/cli/main.py`, and `.jes/artifacts/engineer_smoke_*.md` / `implementation_review_*.md` for "phrases that actually worked" cross-checks.

---

## Counts

- **19** `*_assist.py` modules under `src/jarvis/core/` (recounted at ★ time — matches the IC's own estimate exactly).
- **14** `_try_handle_*` IDLE bridges enumerated in `orchestrator.py` (the deterministic Continuity dispatch block, `mounted_on` → `idle_frame_part_declare`).
- **6** catalog families with a working "ayúdame a elegir" help-choose + pick-apply pair (motors, propellers, battery, frame, ESC, flight_controller/sensors identity-only) + **2** kit-hardware holes (power_connector, signal_harness) sharing the same generic gate.
- **5** catalog families with a working "cambiar `<familia>`" rebind trigger (frame, motors, propellers, battery, esc) — **flight_controller/sensors excluded on purpose** (see Gaps below).
- **~35** distinct `engineer_smoke_*.md` / `implementation_review_*.md` artifacts consulted for phrase cross-checks; none of the guide's cheatsheet phrases contradicted a closed smoke.

---

## 1. Orchestrator IDLE bridges (dispatch order, exact)

This is the literal order `orchestrator.py`'s IDLE block checks them in (each returns `None` to fall through to the next):

| # | Bridge | Trigger (evidence) | Writer/assist | Mutates? |
|---|---|---|---|---|
| 1 | `_try_handle_mounted_on_declare` | `mounted_on_declare_assist.py`: SET `\bmontad[ao]s?\s+en\b\|\bmontar\s+en\b` or `\bmonta\s+(?:el\|la\|los\|las)\b`; CLEAR `\bquita(?:r)?\s+(?:el\s+)?montaje\b\|\bsin\s+montaje\b\|\bdesmonta(?:r)?\b` | `set_component_mounted_on` | yes |
| 2 | `_try_handle_mount_standard_assist` | `mount_standard_assist.py` `_TRIGGER_RE = r"montajes?\s+estandar\|que\s+falta\s+montar"` | none (checklist only) | no |
| 3 | `_try_handle_craft_montage_stack_assist` | `craft_montage_stack_assist.py` `_TRIGGER_RE = r"apilar\s+en\s+placa\|proponer\s+stack\s+centrado"` | none (checklist only) | no |
| 4 | `_try_handle_layout_pack_assist` | `layout_pack_assist.py`: bare `\blayout\s+pack\b` or named `aplicar\s+layout\s+([a-z0-9_]+)` | none (checklist only) | no |
| 5 | `_try_handle_silhouette_product_b_assist` | `silhouette_product_b_assist.py` `_TRIGGER_RE = r"\bsilueta\b\|parece\s+un\s+dron\|\bproduct\s+b\b"` | none (checklist only) | no |
| 6 | `_try_handle_fit_relations_assist` | `fit_relations_assist.py` `_TRIGGER_RE = r"\brelaciones\b\|\bfit\b\|que\s+falta\s+verificar\|verificaciones\s+de\s+encaje"` | none (checklist only) | no |
| 7 | `_try_handle_catalog_refresh` | `catalog_refresh_assist.py` `_GATE_RE = r"\b(?:actualiza(?:r)?\|refresca(?:r)?)\b"` + subject noun (esc/motors/battery/frame/propellers) | `refresh_component_from_catalog` | yes |
| 8 | `_try_handle_declared_box_pose` | `declared_box_pose_declare_assist.py`: SET requires `declara`+mm+`\brespecto\b`; CLEAR `\bquita(?:r)?\s+(?:la\s+)?pose\b` | `set_component_declared_box_pose` | yes |
| 9 | `_try_handle_estimated_temporary_plate_declare` | `estimated_temporary_plate_assist.py`: `declara`+provisional keyword (`estimad[ao]s?\|temporal(?:es)?\|provisional(?:es)?`)+dims, plate subject only | `set_estimated_temporary_plate_envelope` | yes |
| 10 | `_try_handle_estimated_temporary_esc_height_declare` | `estimated_temporary_esc_assist.py`: same provisional gate, ESC subject only, one `<N> mm` | `set_estimated_temporary_esc_height` | yes |
| 11 | `_try_handle_declared_box_envelope` | `declared_envelope_declare_assist.py`: `declara`+dims, subjects battery/sensors/any `frame_plate*`/`power_connector`/`signal_harness`/`frame_arm`/`prop_adapter`/`frame_standoff`/`frame_cage`/`frame_caps` (never frame root/motors/ESC/FC/propellers); CLEAR `\bquita(?:r)?\s+(?:el\s+)?sobre\b\|\bquita(?:r)?\s+(?:las\s+)?cotas\b` | `set_component_declared_box_envelope` | yes |
| 12 | `_try_handle_cabe_screening` | `_CABE_WORD_RE = re.compile(r"\bcabe\b", re.IGNORECASE)` (orchestrator.py) | none (screening text only) | no |
| 13 | `_try_handle_fit_attestation` | `_DECLARO_VERIFICADO_RE = r"\bdeclaro\s+verificad[oa]\b"`; CLEAR `_QUITA_VERIFICACION_RE = r"\bquit[ao]r?\s+(?:la\s+)?verificaci[oó]n\b"` | `set_component_declared_fit_attestation` | yes |
| 14 | `_try_handle_idle_frame_part_declare` | free text like `"6 standoffs"` / `"4 brazos fibra"` via `extract_all_frame_part_properties` | `upsert_frame_part` | yes |

## 2. Catalog identity acquisition (help-choose + rebind)

**Help-choose gate** (shared, `motor_catalog_assist.HELP_CHOOSE_PHRASES`, reused by import into every family module): `"ayudame a elegir"`, `"ayúdame a elegir"`, `"ayudame a escoger"`, `"ayúdame a escoger"`, `"busca motores"`/`"buscar motores"` (motor-specific literal), `"propon candidatos"`/`"propón candidatos"`, plus a soft match (`"ayudame"` + one of `elegir`/`escoger`/`motor`/`opcion`). Each family's own orchestrator pair applies it in its own scoped branch:

| Family | Offer / apply methods | List source |
|---|---|---|
| Motors | `_offer_component_motor_catalog` / `_apply_component_motor_catalog_pick` | `motor_catalog_assist.build_motor_catalog_suggestions` |
| Propellers | `_offer_component_propeller_catalog` / `_apply_component_propeller_catalog_pick` | `propeller_catalog_assist` |
| Battery | `_offer_component_battery_catalog` / `_apply_component_battery_catalog_pick` | `battery_catalog_assist.build_battery_catalog_suggestions` (limit=None, no truncation) |
| Frame | `_offer_component_frame_catalog` / `_apply_component_frame_catalog_pick` | `frame_catalog_assist` |
| ESC | `_offer_component_esc_catalog` / `_apply_component_esc_catalog_pick` | `esc_catalog_assist` |
| Flight controller | `_offer_flight_controller_identity_catalog` / `_apply_control_identity_catalog_pick(family="flight_controller")` | `control_identity_catalog_assist.build_flight_controller_identity_suggestions` → `ComponentLibrary.list_fcs()` (only rows with a full cited box — `skystars_f4_v4` is identity-only and never appears here) |
| Sensors/GPS | `_offer_sensor_identity_catalog` / `_apply_control_identity_catalog_pick(family="sensors")` | `control_identity_catalog_assist.build_sensor_identity_suggestions` → `list_sensors()` |
| Kit hardware (`power_connector`/`signal_harness`) | `_offer_kit_hardware_catalog` / `_apply_kit_hardware_catalog_pick` | `kit_hardware_catalog_assist.build_kit_hardware_catalog_suggestions` |

**Rebind gate** (`catalog_rebind_assist.resolve_idle_catalog_rebind`): `_REBIND_VERB_RE = r"\b(?:cambiar|cambia|definir|define|modificar|modifica)\b"` (or the soft `"ayudame... elegir/escoger"` form) + a bare family noun with **no** trailing SKU token (`_is_pure_rebind_phrase`) → re-offers that family's list. Supports exactly **frame, motors, propellers, battery, esc** (`_FAMILY_NOUN_PATTERNS`). `flight_controller`/`sensors` are **not** in this table — a bare `"cambiar controladora"` does **not** reopen the FC picker today (see Gaps §5).

## 3. Envelopes (L×W×H)

| Kind | Phrase shape | Subjects | Writer |
|---|---|---|---|
| Declared (cited or Engineer-typed) | `"declara <sujeto> L x W [x H] mm"` | battery, sensors, any `frame_plate*`, `power_connector`, `signal_harness`, `frame_arm`, `prop_adapter`, `frame_standoff`, `frame_cage`, `frame_caps` | `declared_envelope_declare_assist` → `set_component_declared_box_envelope` |
| Declared clear | `"quita el sobre de X"` / `"quita las cotas de X"` | same as above | same |
| Estimated plate | `"declara frame_plate estimada/temporal/provisional L x W [x H] mm"` | any `frame_plate*` only | `estimated_temporary_plate_assist` → `set_estimated_temporary_plate_envelope` |
| Estimated ESC height (hybrid) | `"declara el esc estimado/temporal/provisional H mm"` | `esc` only, requires prior cited L×W | `estimated_temporary_esc_assist` → `set_estimated_temporary_esc_height` |
| Catalog bind (automatic) | no phrase — happens on pick/bind | any catalog-bindable family whose seed cites L×W×H | each family's `bind_*_from_catalog` |

**Explicit exclusion, confirmed by code+docstring:** `declared_envelope_declare_assist.py` never accepts `frame` root, `motors`, `ESC`, `FC`, or `propellers` as a SUBJECT — those families only ever get a box via catalog bind (or, for ESC height specifically, the estimated-temporary path above).

## 4. Mounts (`mounted_on`)

- **Direct declare** (see bridge #1 above) — subjects fc/esc/motor(es)/bateria/sensor(es)/helice(s) (shared table, `mounted_on_declare_assist._SUBJECT_PATTERNS`, reused by `declared_box_pose_declare_assist` and `estimated_temporary_esc_assist` for subject resolution too); targets: `frame`, `frame_arm`, `frame_cage`, `frame_standoff`, any `frame_plate*`, or another component alias (e.g. `"hélices montadas en los motores"`).
- **Checklist** — `mount_standard_assist.build_mount_standard_checklist` lists every still-undeclared in-scope edge (propellers→motors, motors→frame_arm, esc/fc/battery/sensors→plate/frame) with the exact ready-to-type phrase; never writes.

## 5. Poses (`declared_box_pose`)

| Command | Shape | Scope |
|---|---|---|
| Direct declare | `"declara X a N mm en <eje> respecto a Y"` (multiple axes in one phrase OK) | any component, origin must resolve to a `box` shape |
| Clear | `"quita la pose de X"` | — |
| Path F stack checklist | `"apilar en placa"` / `"proponer stack centrado"` | FC/ESC/battery/sensors onto the single unambiguous boxed `frame_plate*`; z = `plate.height_mm/2 + child.height_mm/2` |
| Named layout pack | `"layout pack"` (bare, only when exactly one pack is registered) / `"aplicar layout <pack_id>"` | pose + mount rows for a named, curated kit pack (e.g. `hglrc_my5_flush_stack_b1`) |
| Board Situar (UI, not CLI) | click **"Situar"** toggle → click a box to select → drag to move (Shift = lock depth axis, Alt+drag = orbit camera) → **"Recentrar 3D"** to re-center; a solid with no origin yet opens an **"Origen para X:"** picker + **"Fijar origen"** button instead of arming a drag | any singleton solid (never a `solidCopies ≥ 2` station copy); writes through the SAME `set_component_declared_box_pose` writer as the CLI phrase (`ui/spatial-board/src/Scene3D.tsx`) |

## 6. Motors/propellers on the Visor (automatic, no direct command)

Once the frame cites `configuration == "quad_x"` + a positive `wheelbase_mm`, and `motors.motor_count` is a whole number in `[2, 16]`:
- Motors/propellers/`prop_adapter` render as `solidCopies` at the raw quad-X station points (unchanged since Visor X stations B1).
- `frame_arm` (when `motor_count == 4` specifically) renders as an **L-aware diagonal** placement instead (its own declared `length_mm` placed along the origin→station ray) — Arm radial Visor B1.
- A motor/propeller with **both** a diameter path **and** a cited axial fact (Motor `height_mm`, or Propeller `hub_thickness_mm`) renders as a **cylinder**, not a flat disk — Disk axial Visor B1. Neither of these two Visor behaviors has a user-typed trigger; they follow automatically from what's already cited/declared.

## 7. Comprobación / honestidad

| Command | What it answers | Never claims |
|---|---|---|
| `"cabe"` / `"¿cabe?"` / `"cabe el esc"` | AABB screening (`overlap`/`no_overlap`/`pose_incomplete`/`estimated_dims`/`origin_unusable`/`child_not_box`/`no_pose`) for one posed child vs. its origin | never "VERIFIED"/"ensamblado" |
| `"declaro verificado el X"` / `"declaro verificada la X"` | Engineer sign-off SET — refuses unless that pair currently screens `overlap` | never a Jarvis-computed proof |
| `"quita la verificación"` / `"quitar verificación"` | clears an attestation | — |
| `"relaciones"` / `"fit"` / `"qué falta verificar"` / `"verificaciones de encaje"` | per-relation checklist (FC/ESC/battery/sensors→plate; motors→frame_arm; propellers→motors), status ∈ `missing_origin`/`no_box_child`/`no_box_origin`/`ambiguous_plate`/`estimated_dims`/`no_pose`/`screen_*`/`attested`/`n_a_disk` | never "ASSEMBLY READY" (printed literally in the footer) |
| `"silueta"` / `"parece un dron"` / `"product b"` | racimo (A) / silueta estimada (B\*) / silueta (B) checklist | never visual recognition — a deterministic property check, per the silhouette semantics lock |

## 8. Global orientation (sidebar per lock #8 — not the spine)

- `jarvis --chat` — start the interactive CLI (`src/jarvis/adapters/cli/main.py`); `jarvis board` — launch the Board visor (separate subcommand).
- At startup with existing projects: type `n`/`nuevo`/`crear` for a new one, a number to continue an existing one, or free text (e.g. `"quiero diseñar un dron"`) to start `CREATE_PROJECT_INTERACTIVE`.
- `"estado"` / `"resumen"` / `"resumen del proyecto"` / `"como va el proyecto"` (`intent_resolver.py` guidance patterns) → project status/orientation, any time, never opens a wizard.
- `"calcular"` / `"simular"` — energy/sim recompute, LLM-intent-routed rather than a fixed deterministic regex; **not inventoried further** per lock #8 (adjacent, not montage spine).

## 9. Ordered montage spine (draft — mirrors the craft-montage honesty lock's own A–D)

```text
0. jarvis --chat → nuevo proyecto / continuar          [§8]
A. Identidad + catálogo: motor/hélice/batería/ESC/frame/FC/GPS
   via "ayúdame a elegir" o "cambiar <familia>"          [§2]
B. Placa main: citada (catálogo/medida) o
   "declara frame_plate estimada L x W [x H] mm"          [§3]
C. Sobres L×W×H para el resto del stack (batería/sensores
   ya declarados o vía catálogo; ESC vía catálogo + H
   estimada si falta ficha)                                [§3]
D. Montajes: "montajes estándar" → confirmar frases        [§4]
E. Poses: "apilar en placa" / "layout pack" / Situar        [§5]
F. Motores/hélices en Visor X — automático si wheelbase
   + quad_x + motor_count ya citados                       [§6]
G. Comprobar: "cabe" → "relaciones"/"fit" →
   "declaro verificado" (solo si overlap) →
   "parece un dron"                                         [§7]
```

Every step cites ≥1 row above by section number. Step F is the only fully-automatic step (no phrase to type).

## 10. Gaps / traps (phrases a user might reasonably expect that do NOT exist)

1. **`"cambiar controladora"` / `"cambiar gps"` does not reopen the FC/sensor picker.** `catalog_rebind_assist._FAMILY_NOUN_PATTERNS` only covers frame/motors/propellers/battery/esc — flight_controller and sensors were never added (Library FC/sensors P0's own review N1: "FC bind exists, IDLE rebind not wired"). Today the only way to change FC/GPS identity is the free-text extractor path via `"ayúdame a elegir"` re-offering, or typing the model name directly (e.g. `"Pixhawk 4"`).
2. **`"actualiza el fc"` / `"actualiza el gps"` do not refresh anything.** `catalog_refresh_assist._SUBJECT_PATTERNS` deliberately excludes flight_controller/sensors (same minimal-surface reason as #1) — confirmed by that module's own comment.
3. **No FC/ESC/motor/propeller subject in the plain declared-envelope grammar.** A user who types `"declara el esc 45 x 44 x 8 mm"` gets no match at all — ESC's box only ever arrives via catalog bind, or (height only) the estimated-temporary path.
4. **A rebind that switches an ESC to a SKU whose catalog row omits a property the OLD SKU had can silently keep the stale value labeled `declared`.** `bind_esc_from_catalog`'s `base=` merge only overwrites a key the NEW spec actually defines (found live during the estimated-temporary-ESC-Skystars Buy; flagged as its own debt, not fixed there).
5. **Motors/propellers never get a "cabe"/attest verdict**, even when rendered as a cylinder — `screen_posed_envelope` is box-only by design; disk-station fit attest is an explicitly separate, not-yet-built Buy.
6. **A bare `"layout pack"` only works while exactly one pack is registered.** `resolve_layout_pack_trigger`'s own fallback (`packs[0] if len(packs) == 1 else None`) has no disambiguation UI yet for a second pack.

## 11. Out of montage spine (found, deferred to the guide's short appendix)

- `"calcular"` / `"simular"` / `"estado"` / `"resumen"` — energy/sim + orientation, always available, never blocking the montage path.
- `DEFINE_MISSING_PARAMETERS` wizard (triggered automatically on project creation when required params are missing) — out of this guide's own scope per lock #9 ("wizard DEFINE_MISSING deep dive").
- Frame-part count declare (`"6 standoffs"`, `"4 brazos fibra"`) — real and useful, but a structure-BOM concern orthogonal to the box/pose/mount spine; mentioned once, not elaborated.

---

**STOP-gate confirmation:** every spine step in §9 cites at least one inventory row above; no guide phrase will be drafted from memory without a matching row in §§1–8.
