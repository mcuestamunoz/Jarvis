# Implementation Contract — Continuity declare `mounted_on` B1 (CLI / IDLE)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY FOR IMPLEMENTATION — Engineer ★ Buy (`procede con el IC` after Board smoke)  
**Parents:**
- [implementation_contract_geometry_assembly_espacial_b1.md](implementation_contract_geometry_assembly_espacial_b1.md) — **CLOSED** suite **2364** (`mounted_on` + Board text; §3.5 Continuity deferred)
- [implementation_review_geometry_assembly_espacial_b1.md](implementation_review_geometry_assembly_espacial_b1.md) — **PASS**
- Idle rebind precedent: [implementation_contract_idle_catalog_rebind_b3.md](implementation_contract_idle_catalog_rebind_b3.md) — thin IDLE phrase → existing writer

**Type:** User-facing **declare / clear** path for assembly relations already stored by `set_component_mounted_on`.  
**Not** pose mm. **Not** Board edges. **Not** fit. **Not** Conversation Engine. **Not** inference from layout.

**Baseline:** package **`0.3.8`** · suite **2364**

**Output:** `.jes/artifacts/implementation_report_continuity_mounted_on_declare_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1 Continuity declare** | YES — close assembly espacial §3.5 gap |
| 2 | Reuse writer | **Only** `set_component_mounted_on` — no second write path |
| 3 | Mode | **IDLE** with active project (same class as idle catalog rebind) |
| 4 | Copy | “**declarado** montado en …” — never “ensamblado” / “cabe” / “verificado” |
| 5 | Ambiguous plate | **Do not guess** among multiple plates — prompt list (keys + labels) |
| 6 | Pose / edges / fit | **Out** |
| 7 | Version | **No** bump |

---

## 1. You

- Do **not** invent mounts from Board position, BOM co-membership, or “only one plate.”
- Do **not** change `parent_key`, glyphs, or `set_component_mounted_on` validation rules (call it; don’t fork it).
- Do **not** open pose/fit/CAD or a multi-turn Conversation Engine.
- Do **not** bump package version.
- Full suite green. Zero weakened tests.
- Write `implementation_report_continuity_mounted_on_declare_b1.md` when done.

---

## 2. Intent

```text
IDLE + active project:
  "monta el FC en la placa principal"
  "ESC montado en frame_plate"
  "motores montados en los brazos"
  "quita el montaje del FC"
        ↓
  pure parse → (component_key, target_key | None | AMBIGUOUS)
        ↓
  set_component_mounted_on(...)  OR  list plates for disambiguation
        ↓
  save state + honest confirmation (Board already shows "montado en")
```

Product sentence:

> “Puedo declarar en el chat a qué va montado un componente, y verlo en el Board.”

---

## 3. Locked behavior

### 3.1 Pure assist module (new)

Prefer new file: `src/jarvis/core/mounted_on_declare_assist.py` (mirror `catalog_rebind_assist` thinness).

Export something like:

```text
parse_mounted_on_declare(user_input, components: dict[str, ComponentSpec]) -> MountDeclareResult
```

Where result is a small typed object / NamedTuple:

| Kind | Meaning |
|---|---|
| `SET` | `(component_key, target_key)` both resolved |
| `CLEAR` | `(component_key,)` clear mount |
| `AMBIGUOUS_TARGET` | `(component_key, candidates: list[tuple[key, label]])` — no write |
| `NONE` | phrase not a mount declare |

**Normalization:** strip accents for matching (same discipline as other assist modules).

**Gate phrase (must match to leave NONE):** mount language present, e.g. word-boundary / phrase tokens among:

- `montado en`, `montada en`, `montados en`, `montadas en`
- `montar en`, `monta el`, `monta la`, `monta los`, `monta las`
- `fija … en`, `fijar … en` (optional if cheap)
- clear: `quita el montaje`, `quitar montaje`, `sin montaje`, `desmonta`, `desmontar`

Do **not** fire on unrelated “montar” claims about buying/building the drone (“por que no puedo montar” status phrases stay status — if collision, require an explicit component noun + `en` target so status phrases without a component stay `NONE`).

### 3.2 Subject → `component_key`

Only resolve to a key **that already exists** in `components`:

| Nouns (examples; expand reasonably) | Key |
|---|---|
| `fc`, `flight controller`, `controladora`, `pixhawk` | `flight_controller` |
| `esc` | `esc` |
| `motor`, `motores` | `motors` |
| `bateria`, `baterias`, `battery` | `battery` |
| `sensor`, `sensores`, `gps`, `here3` | `sensors` |
| `helices`, `helice`, `propeller` | `propellers` (optional — allow if present) |

If subject noun matches but key absent → return a clear error path from orchestrator (not silent NONE): message that that component is not declared yet.

If no subject → `NONE` (don’t invent).

### 3.3 Target → `target_key`

Targets must exist in `components`:

| User tokens | Resolution |
|---|---|
| Exact key (`frame_plate_2`, `frame_arm`, `frame`) | That key if present |
| `brazo` / `brazos` / `arm` / `arms` | `frame_arm` if present |
| `jaula` / `cage` | `frame_cage` if present |
| `standoff` / `separador(es)` | `frame_standoff` if present |
| `frame` / `chasis` / `frame root` | `frame` if present |
| `placa` / `plate` / `placas` | See **plate rule** below |
| Label match | If user text contains a plate’s `properties["label"]` value (case-insensitive substring), pick that plate key when unique |

**Plate rule (locked):**

1. Collect all keys where `is_frame_plate_key(k)` (reuse `aerial.is_frame_plate_key`).
2. If user named an exact ordinal key or a **unique** label match → that key.
3. If user said bare `placa`/`plate` and **exactly one** plate key exists → that key.
4. If bare `placa`/`plate` and **2+** plates → `AMBIGUOUS_TARGET` with candidates `(key, label or "—")` sorted by key — **no write**.
5. Never default to `frame_plate` when siblings exist without a distinguishing token.

### 3.4 Orchestrator IDLE dispatch

In `orchestrator.py`, near other IDLE bridges (catalog rebind), **before** LLM fallback:

```text
IF IDLE and active project:
  result = parse_mounted_on_declare(user_input, components)
  IF NONE: fall through
  IF AMBIGUOUS_TARGET: return interactive message listing candidates; do not change mode unless needed
  IF SET/CLEAR:
    try set_component_mounted_on(...)
    save_state
    return confirmation
  IF subject missing from components: honest "aún no declarado"
  IF ValueError from writer: surface message (dangling/self — should be rare after parse)
```

Stay in **IDLE** after success (no wizard mode change required).

### 3.5 Confirmation copy (locked honesty)

Success set example shape (wording flexible):

> `Declarado: flight_controller montado en frame_plate.`  
> Optional second line: `Se verá en el Board como "montado en".`  
> **Forbidden:** ensamblado, cabe, verificado, correcto, fit.

Success clear:

> `Montaje declarado de flight_controller eliminado.`

Ambiguous:

> `Hay varias placas. Indica cuál, por ejemplo: frame_plate (Main Plate), frame_plate_2 (Top …).`

### 3.6 Board / schema

**No** schema change. **No** Board projector change required (already shows the field). Smoke: declare via chat → hard-refresh Board.

---

## 4. Tests (required)

New file preferred: `tests/test_continuity_mounted_on_declare_b1.py`

| # | Case |
|---|---|
| T1 | Parse SET: FC + `frame_plate` / “placa” with single plate |
| T2 | Parse SET: motors → `frame_arm` (“brazos”) |
| T3 | Parse CLEAR: “quita el montaje del FC” |
| T4 | AMBIGUOUS: bare “placa” with 2+ plates → no write |
| T5 | Unique label match: “placa principal” / Main Plate → correct key |
| T6 | NONE: unrelated status / “por que no puedo montar” without component+target |
| T7 | Orchestrator IDLE: happy path persists `mounted_on` + message contains `Declarado` / `montado en` |
| T8 | Orchestrator: missing subject component → honest error, no crash |
| T9 | Non-regression: idle `cambiar frame` / catalog rebind still works (one smoke assert or rely on existing suite) |

Run full suite; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/mounted_on_declare_assist.py` | **new** — pure parse |
| `src/jarvis/core/orchestrator.py` | IDLE dispatch + save + copy |
| `tests/test_continuity_mounted_on_declare_b1.py` | **new** |
| `.jes/artifacts/implementation_report_continuity_mounted_on_declare_b1.md` | write |

**Do not change:** `set_component_mounted_on` semantics · `parent_key` · glyphs · `ui/**` · seeds · package version.

---

## 6. Explicit non-goals

Pose / orientation · Board edges (B2) · fit/clearance · auto-infer mounts · wizard multi-step Conversation Engine · LLM-only parsing without deterministic assist · “ensamblado” claims · version bump · weakened tests

---

## 7. Done criteria

- [ ] IDLE Spanish declare/clear phrases call `set_component_mounted_on` and persist.
- [ ] Ambiguous multi-plate bare “placa” prompts; does not guess.
- [ ] Copy stays declared-only (no ensamblado/cabe).
- [ ] Board still shows relation after declare (smoke or projector assert via state).
- [ ] Tests T1–T9; full suite green; count reported.
- [ ] Implementation report written.
- [ ] Cursor review PASS before Engineer close.

---

## 8. Stop conditions

Stop and ask before: inferring mounts, adding pose, drawing edges, LLM-only routing without deterministic parse, or bumping version.
