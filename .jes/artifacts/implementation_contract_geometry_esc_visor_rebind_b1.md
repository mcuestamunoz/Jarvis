# Implementation Contract — Live ESC visor via sourced SKU rebind B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2573** + smoke **ACCEPT**  
**Parents:**
- [engineer_next_geometry_remaining_pieces.md](engineer_next_geometry_remaining_pieces.md) — 3a envelopes before 3b/3c
- ESC envelope **CLOSED** @ **2327** — `hobbywing_xrotor_40a_6s` already has cited box **50.0 × 21.6 × 12.0** mm
- `bind_esc_from_catalog` already projects that triple; docstring still says no CLI/UX caller
- Idle catalog rebind **B3 CLOSED** @ **2276** — motors / propellers / battery / frame. **ESC was explicitly out**
- Pose writer **CLOSED** @ **2456** — origin must be a **box**. Live 5min ESC already has pose vs FC (no solid)
- Scene3D-from-pose **CLOSED** @ **2462** · `"cabe"` B1-min **CLOSED** @ **2540**
- Visor X **CLOSED** @ **2562** — **out** (do not touch stations)
- Battery `lipo_3s_2200mah` has **no** L×W×H — **out** (do not invent, do not rebind to a 4S pack this Buy)
- Plate L×W **B0** — **out**

**Type:** IDLE named rebind for **ESC only** + bind-with-`base` so the sourced Hobbywing box appears on the visor **and** an already-declared `declared_box_pose` survives.  
**Not** a propulsion-composite ESC wizard. **Not** seeding dims onto the freeform 40A identity. **Not** battery envelope. **Not** Rooster L×W.

**Baseline:** package **`0.3.8`** · suite **2562**

**Output:** `.jes/artifacts/implementation_report_geometry_esc_visor_rebind_b1.md`

---

## 0. Engineer Buy (locked)

Engineer: situar el resto; skip investigation; **procede primero por el que Cursor cree**. First slice = ESC (cited box exists; live pose vs FC already exists; visor has nothing to draw).

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-rebind** — IDLE `cambiar esc` / `ayúdame a elegir esc` offers the **1-row** ESC catalog; pick binds `hobbywing_xrotor_40a_6s` |
| 2 | Identity | Do **not** copy 50.0 / 21.6 / 12.0 onto a freeform ESC without `catalog_ref`. Bind the SKU |
| 3 | Pose | Apply uses `bind_esc_from_catalog(sku, base=existing_esc)`. `declared_box_pose` and `mounted_on` **survive**. Do **not** bind without `base` on a live spec that already has pose |
| 4 | Solid | Projector `_geometry_from_spec` → **box** 50.0 × 21.6 × 12.0. Not a disk. Not a cylinder |
| 5 | Cards | Still **one** `esc` card. Pose vs FC (if already declared) feeds Scene3D-from-pose as today |
| 6 | Composite | **Do not** add ESC help-choose / pick inside the propulsion wizard `["motors","propellers","esc"]`. Gate: `expected_keys == ["esc"]` only |
| 7 | Physics | Bind **does** project catalog `current_a` 40 and `mass_g` 15. 2–6S ESC on a 3S pack is **ACCEPT**. Do not invent energy/hover changes as this Buy’s bug |
| 8 | `"cabe"` | After the box exists, existing screening may emit overlap text on a complete xyz pose. That is **in-scope honesty**, not a new fit engine |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Tras cambiar el ESC al XRotor 40A citado, el visor muestra una caja
50×21.6×12 mm. Si ya había pose respecto al FC, se conserva y el sólido
se sitúa. Una card. No es el mapa respecto al carbono.
```

**Not:**

```text
mm copiados al ESC freeform · wizard ESC dentro de propulsión ·
dims de lipo_3s_2200mah · L×W Rooster · Conversation Engine
```

---

## 1. You (Claude)

- Do **not** seed `length_mm` on `lipo_3s_2200mah` or any battery row.
- Do **not** invent Rooster L×W. Do **not** touch visor X / `solidCopyOffsetsMm`.
- Do **not** copy Hobbywing dims onto a spec that stays `catalog_ref is None`.
- Do **not** add `_wants_catalog_help` for `esc` when `esc` is merely a member of a composite `expected_keys` list.
- Do **not** mutate `workspace/` (Engineer smoke does the live rebind).
- Do **not** bump version.
- Full pytest green. `ui/` empty unless a test proves a DTO hole (you must not need it — box + pose already project).
- Write the implementation report when done.
- **STOP** if the only way to preserve pose is a new pose schema or a disk origin.

---

## 2. Intent

```text
IDLE "cambiar esc" | "ayúdame a elegir esc"
        → pending=["esc"] + DEFINE_MISSING
        → _offer_component_esc_catalog  (list_escs, 1 row today)
        → pick N
        → bind_esc_from_catalog(sku, base=existing esc spec)
        → set_control_component
        → geometry box 50×21.6×12
        → declared_box_pose unchanged if it was set
        → visor: ESC solid at pose vs FC (if pose complete)
```

No new DTO key. No library seed change (row already cited).

---

## 3. Locked behavior

### 3.1 Resolver (`catalog_rebind_assist.py`)

Widen `CatalogRebindKey` with `"esc"`.

| Key | Nouns (normalized, word-boundary) |
|---|---|
| `esc` | `esc` only (`\besc\b`) |

Priority when multiple nouns: existing order, then **esc last**:  
`frame` > `motors` > `propellers` > `battery` > `esc`.

Add `esc` to `_PURE_PHRASE_STRIP_RE` so `"cambiar esc"` is a pure reopen (residual empty).  
Phrases that name a SKU after the family still return `None`.

`cambiar motor` / `cambiar batería` / bare `ayúdame a elegir` **unchanged**.

### 3.2 IDLE dispatch (`orchestrator.py`)

Replace the B3 `else: battery` catch-all with **explicit** branches (the catch-all would steal `cambiar esc` into the battery catalog):

```text
frame → _offer_component_frame_catalog
motors → _offer_component_motor_catalog
propellers → _offer_component_propeller_catalog
battery → _offer_component_battery_catalog
esc → _offer_component_esc_catalog(session, ["esc"])
```

Same B3 gates: IDLE, architecture 4/4 (`_next_pending_block is None`), component **present and not stub**.

### 3.3 Assist + session

New thin `src/jarvis/core/esc_catalog_assist.py` mirroring kit/frame:

- `list_escs()` capped, no ranking, no “best ESC for my motor”
- Reuse `is_help_choose_phrase` / `match_suggestion_by_input` from `motor_catalog_assist`
- Suggestion fields: `idx`, `name` (SKU), `manufacturer`, `model`, `part_number`, `continuous_current_a`, optional L/W/H
- Format: numbered list; CTA same family as kit/frame (“Elige un número…”)

`InteractiveSessionState.esc_suggestions: list[dict] = []` — runtime-only, **not** in `_PERSISTED_SESSION_FIELDS`.

★4: every existing `_offer_component_*_catalog` / kit offer **clears** `esc_suggestions`. ESC offer clears the other five lists.

### 3.4 Apply

`_apply_component_esc_catalog_pick`:

```text
existing = components.get("esc")
spec = bind_esc_from_catalog(suggestion["name"], base=existing)
set_control_component(state, spec)
```

**Must** pass `base` when `existing` is not None. Writer is the existing `set_control_component` (ESC already saves through it).

Rewrite `bind_esc_from_catalog` docstring: IDLE rebind + this apply path **do** call it. Honesty only.

### 3.5 `_handle_component_description` pick

After kit-hardware branch, **before** affirmative:

```text
IF expected_keys == ["esc"]:
    help-choose → offer ESC catalog
    else if session.esc_suggestions → match → apply
```

`expected_keys == ["esc"]` is the lock. ` "esc" in expected_keys ` is **forbidden** as the gate (would fire in propulsion composite).

### 3.6 Projector

No `spatial_board.py` change expected. After bind, `project_spatial_nodes` ESC node:

- `geometry == {shape: box, length_mm: 50.0, width_mm: 21.6, height_mm: 12.0}`
- `declaredBoxPose` present **iff** the pre-bind spec had a pose whose origin is still a box (same `_declared_box_pose_dto` gate)

### 3.7 Copy

No `"quadrotor"`, `"cabe"`, `"mapa"`, `"L×W Rooster"` in new user-facing catalog CTA. Screening copy on the card stays the existing `"cabe"` helper — do not add new fit strings.

---

## 4. Tests

### Python — `tests/test_geometry_esc_visor_rebind_b1.py`

Use real `default_library` + `bind_esc_from_catalog` + `set_control_component` + `project_spatial_nodes` + orchestrator IDLE where named.

| ID | Behavior |
|---|---|
| P1 | Bind Hobbywing with `base=` a freeform ESC that has `declared_box_pose` vs an FC **box** + `set_control_component` → ESC `geometry` box 50.0 / 21.6 / 12.0; `catalog_ref.sku == "hobbywing_xrotor_40a_6s"`; pose origin/x still the pre-bind values; one `esc` node |
| P2 | Freeform ESC (`catalog_ref is None`, `current_a` only, same pose) → **no** `geometry` on the ESC node (pose DTO may still exist — that is today’s pose-without-solid) |
| P3 | Library: `get_esc("hobbywing_xrotor_40a_6s")` still 50.0 / 21.6 / 12.0; `list_escs()` length **1** |
| P4 | Resolver: `cambiar esc` / `ayúdame a elegir esc` → `"esc"`; `cambiar motor` still `"motors"`; bare `ayúdame a elegir` still `None`; `cambiar esc hobbywing_xrotor_40a_6s` still `None` |
| P5 | Closed 4/4 architecture + non-stub freeform ESC + FC box + pose: IDLE `cambiar esc` → `esc_suggestions` non-empty, names the Hobbywing SKU; **not** `battery_suggestions`; `pending_missing_params == ["esc"]` |
| P6 | P5 then pick the Hobbywing idx → `catalog_ref` set; pose preserved; projector geometry box as P1 |
| P7 | DEFINE_MISSING with `expected_keys=["motors","propellers","esc"]` + live `esc_suggestions` leftover **must not** apply an ESC pick from `"1"` (composite gate). Prefer: help-choose `ayúdame a elegir` in that composite does **not** return `esc_suggestions` |

Do **not** delete ESC envelope / pose / `"cabe"` / B3 tests.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/esc_catalog_assist.py` | new, thin |
| `src/jarvis/core/catalog_rebind_assist.py` | `esc` key |
| `src/jarvis/core/orchestrator.py` | IDLE branch, offer/apply, singleton pick, ★4 clears |
| `src/jarvis/schemas/action_schema.py` | `esc_suggestions` |
| `src/jarvis/core/catalog_bind.py` | docstring honesty |
| `src/jarvis/core/state_manager.py` | comment: `esc_suggestions` runtime-only |
| `tests/test_geometry_esc_visor_rebind_b1.py` | P1–P7 |
| `library/` | **empty** |
| `ui/` | **empty** |
| `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_esc_visor_rebind_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min` (architecture already closed):

| Step | Expected |
|---|---|
| `cambiar esc` | ESC catalog, one Hobbywing row — **not** battery list |
| Pick `1` / XRotor | `catalog_ref` Hobbywing; card L×W×H 50 / 21.6 / 12; pose vs FC **still there** |
| 3D | ESC **box** at the declared offset vs FC, plus existing FC box + 4+4 visor X |
| `"cabe"` | May now screen (box vs box). Overlap line = screening, not VERIFIED |
| `cambiar motor` | still motors catalog |

10min: same phrase if ESC is present and not a stub. If 10min ESC is already a different identity, pick still binds Hobbywing (one row). Do **not** invent a second ESC SKU.

Record [engineer_smoke_geometry_esc_visor_rebind_b1.md](engineer_smoke_geometry_esc_visor_rebind_b1.md) after review.

---

## 7. Done when

- [ ] P1–P7 green; full pytest green
- [ ] Freeform ESC still has no geometry until bind
- [ ] No battery seed; no Rooster L×W; no visor-X edit; no version bump
- [ ] Report written

---

## Explicitly not this IC

Battery L×W×H (no cited source on `lipo_3s_2200mah`) · 3c declared plate L×W · disk-origin pose · ESC picker inside propulsion composite · Conversation Engine · version bump
