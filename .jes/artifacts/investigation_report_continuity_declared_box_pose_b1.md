# Investigation Report — Continuity Declared Box-Local Pose B1 (CLI / IDLE)

**IC:** [investigation_contract_continuity_declared_box_pose_b1.md](investigation_contract_continuity_declared_box_pose_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2438 (unchanged — investigation only, no code/tests touched, nothing persisted to the demo project)

---

## 1. Executive recommendation

**B1 — thin Continuity declare/clear, mirroring `mounted_on_declare_assist` exactly, gated on a verb the mount grammar has never claimed.** The grammar is honestly solvable: gating on `"declara(r)"` + a millimetre-shaped number + `"respecto"` produces zero collision with `mounted_on_declare_assist`'s own gates (`montado en`/`monta ... en`/`fija ... en`/clear), confirmed empirically against seven phrases including the one genuine near-miss this investigation found (`"fija"` is already claimed by the mount grammar — a pose grammar must **not** reuse it, and this report's proposed grammar doesn't). Subject and origin resolution can reuse the mount assist's own noun tables rather than duplicating them. The writer's existing rejection rules (non-box origin, self-origin, missing key) need no new logic — the assist stays a pure parser, exactly as thin as its precedent.

---

## 2. Collision + grammar

**Forbidden verb, found empirically, not assumed:** `mounted_on_declare_assist._FIJA_RE` already gates on `"fija(r)"` (combined with `"en"`) for phrases like `"fija el ESC en la placa"`. A pose grammar that also used `"fija"` as its declare verb would either collide outright or require careful disambiguation for no benefit — this report recommends against it explicitly, having checked.

**Proposed gate (verified, not merely proposed):**
- SET: contains `"declara"`/`"declarar"`, a millimetre-shaped number (`\bmm\b`), and `"respecto"`.
- CLEAR: `"quita"`/`"quitar"` + `"pose"` (mirrors `"quita el montaje"` exactly, substituting the noun).

**Required tokens (Question A, answered):** `mm` and `respecto` together are the disambiguator — no status Spanish phrase in ordinary use pairs a millimetre figure with "respecto a [something]" incidentally, and no existing mount phrase (`"montado en"`, `"monta el/la/los/las"`, `"fija ... en"`) ever contains either token. Requiring **both**, not just one, is deliberate: `"respecto"` alone could appear in unrelated status phrases ("con respecto al proyecto..."), and a bare `mm` could appear in an unrelated numeric declare (a battery capacity, say) — the conjunction of both is what's actually distinctive to a pose declaration.

**Working axis tokens:** bare `x`/`y`/`z`, or `largo`/`ancho`/`alto` (length/width/height — the same words the declared-axes convention itself is named after: `L→+X, W→+Y, H→+Z`). **Forbidden, confirmed not proposed:** `adelante`/`atrás`/`arriba`/`abajo`/`izquierda`/`derecha` — every one of these implies a real-world direction (heading or gravity) the convention explicitly disclaims (`POSE_AXES_HONESTY_LABEL`: "no morro; no gravedad"); accepting them as synonyms would silently reintroduce the exact claim the schema's own docstring forbids.

---

## 3. Baseline + empirical dry-runs

- **`DeclaredBoxPose`/`set_component_declared_box_pose`** (re-read in full this session): unchanged since its own IC — origin must exist, must resolve to `geometry.shape == "box"` via `_geometry_from_spec` (reused, not re-implemented), must differ from the subject, else `ValueError`. Board labels (`origen pose`, `ejes pose`, `Δx mm`/`Δy mm`/`Δz mm`) confirmed unchanged in `spatial_board.py`.
- **Live demo census** (re-verified live against `workspace/autonomía-de-10min-9ada1a1b0cca/state.json`): `flight_controller`/`esc`/`battery` are `box`; `motors`/`propellers` are `disk`; the remaining 9 keys have no `geometry`. **`declared_box_pose` is present as a literal `null` key on every one of the 14 components** (a harmless artifact of the schema addition being re-serialized the last time the file was saved — confirmed via `grep -o '"declared_box_pose":[^,}]*' ... | sort -u` returning only `"declared_box_pose": null`) but **zero non-null value exists anywhere** — confirmed by a direct check. `git status --short -- workspace/` is empty throughout this investigation — nothing was persisted by any dry-run below.
- **Empirical gate test** (live, this session — not asserted):

  | Phrase | `mounted_on` gate | Proposed pose gate |
  |---|---|---|
  | `"esc montado en frame_plate"` | `SET` | `None` |
  | `"declara el esc a 5 mm en x respecto al fc"` | `None` | `SET` |
  | `"declara los motores a 3 mm en x respecto a frame_plate"` | `None` | `SET` |
  | `"por que no puedo montar el dron"` | `None` | `None` |
  | `"quita la pose del esc"` | `None` | `CLEAR` |
  | `"quita el montaje del esc"` | `CLEAR` | `None` |
  | `"fija el esc en la placa"` | `SET` | `None` |

  Zero overlap across all seven — including the deliberately-chosen near-miss (`"fija el esc en la placa"`, which must stay mount-only and does).

- **Writer dry-run** (live, against an in-memory copy of the real demo project — never saved): `set_component_declared_box_pose(state, "esc", DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0))` succeeds, matching the phrase `"declara el esc a 5 mm en x respecto al fc"`. `set_component_declared_box_pose(state, "motors", DeclaredBoxPose(origin_key="frame_plate", x_mm=3.0))` — matching `"declara los motores a 3 mm en x respecto a frame_plate"` — correctly raises `ValueError: 'frame_plate' no tiene una caja declarada (geometry: box) — no puede ser origen de pose.` Both confirm the assist can stay a pure parser and let the existing writer be the sole honesty gate, exactly as Locked Stance 1 requires.

---

## 4. Answers A–F

### A — Collision with `mounted_on`

Answered above (§2) — solvable, verified empirically, zero overlap with the actual shipped mount grammar.

### B — Minimum grammar

One phrase family: `"declara <subject> a <N> mm en <eje> [y <N> mm en <eje> ...] respecto a[l] <origin>"`. A single utterance may name multiple axes (`"declara el esc a 5 mm en x y -2 mm en z respecto al fc"`) — this matters because the writer **replaces** the whole `DeclaredBoxPose` object per call (confirmed by re-reading `set_component_declared_box_pose`: `updated_spec = spec.model_copy(update={"declared_box_pose": pose})`, not a merge) — so a "declare" phrase must state every axis the user currently wants set, in one go, exactly mirroring "declaring" semantics rather than incremental patching. This is a locked grammar property to carry into any future IC, not an implementation detail to rediscover later.

**Ambiguity handling**: if the origin noun doesn't resolve to a live component key at all, the assist should surface the same "not found" honesty style `mounted_on_declare_assist` already uses (`AMBIGUOUS_TARGET` with empty candidates) rather than falling through to `NONE` — a clearly mount/pose-shaped phrase that fails to resolve should say so, not silently defer to the LLM. If the origin noun resolves to a real key that **isn't** a box (a plate, an arm, a disk), the assist should **not** pre-check shape itself — let the call reach the writer and surface its `ValueError` message, confirmed above to already be clear and specific.

### C — Subjects vs origins

**Subject**: any existing, declared component key (broader than `mounted_on`'s fixed six-noun table, in principle) — but for a first, thin Buy, reusing the exact same subject-noun vocabulary `mounted_on_declare_assist` already has (`flight_controller`/`esc`/`motors`/`battery`/`sensors`/`propellers`) is sufficient to cover every live-demo case and keeps the parser genuinely thin; widening the subject vocabulary beyond that table is a separate, later concern, not blocking this Buy. **Origin**: box-only, already fully encoded and enforced by the writer (confirmed via the dry-run above) — the assist needs no separate origin-shape check of its own.

### D — Buy options

| Option | Recommended? |
|---|---|
| **B0 — Keep writer-only** | No — the grammar problem this option would be excused by (an inescapable collision, or an honest convention only expressible via forbidden directional words) does not exist; §2/§3 prove the opposite. |
| **B1 — Thin Continuity declare/clear (recommended)** | Yes — grammar solved, zero new writer logic, reuses existing noun tables, matches the exact precedent shape `mounted_on`'s own Continuity cycle already established. |
| **B1+ — Also move Scene3D solids** | **Rejected this cycle**, exactly as the writer IC itself locked — `layoutSolidsRow`/`Scene3D` remain untouched; a pose fact existing is not the same decision as a later, separate visor Buy choosing to consume it. |
| **B2 — LLM / Conversation Engine parse** | **Rejected** — Continuity's entire discipline through every cycle this session (`mounted_on`, catalog refresh, this investigation) has been deterministic regex parsing with the LLM explicitly refused in every test; nothing about millimetre offsets changes that calculus, and §2/§3 show a deterministic grammar is fully achievable. |

### E — Contingency sketch (B1 — not an IC)

```text
New file: src/jarvis/core/declared_box_pose_declare_assist.py
  - import _SUBJECT_PATTERNS from mounted_on_declare_assist (reuse, don't duplicate)
  - reuse mounted_on_declare_assist's target-noun resolution (_resolve_target-shaped
    helper) for the ORIGIN noun too — a plate/arm origin should resolve to a real
    key and let the writer reject it with its own clear message, not dead-end
    the parser silently
  - new gate: _DECLARE_MM_RE (requires "declara(r)" + \bmm\b + "respecto")
    and _CLEAR_POSE_RE ("quita(r) (la) pose")
  - axis token map: {"x": "x_mm", "largo": "x_mm", "y": "y_mm", "ancho": "y_mm",
    "z": "z_mm", "alto": "z_mm"} — bare letters and length/width/height words
    only, nothing directional
  - result type mirrors MountDeclareResult: SET (subject, origin, {axis: value}),
    CLEAR (subject), AMBIGUOUS_TARGET (subject, candidates), NONE

Orchestrator: a new _try_handle_declared_box_pose bridge, inserted in
_handle_user_text_inner immediately after _try_handle_catalog_refresh
(line ~974-979) and before the FN-005 help-choose chain — the same
insertion point every deterministic IDLE bridge added this session has
used, and safe per §3's empirical proof of zero gate overlap with either
of the two bridges already there.

Confirmation copy: "Declarado: <subject> a <axis deltas> respecto a
<origin>. Ejes: locales declarados (L→+X, W→+Y, H→+Z); no morro; no
gravedad." — reusing POSE_AXES_HONESTY_LABEL verbatim, never a paraphrase.

Tests: a new tests/test_continuity_declared_box_pose_b1.py mirroring
tests/test_continuity_mounted_on_declare_b1.py's own shape (parse-only
cases, then orchestrator IDLE persistence cases) — no UI change expected,
cards already render `fields` generically.
```

**Not provided, per the IC's own instruction**: no code, no new file actually written, no orchestrator edit made.

### F — Out of scope checklist

`Scene3D.tsx`/`scene3dLayout.ts`: not opened this cycle (confirmed no `git diff`, this was a read-only investigation). Fit stub: not opened, still `QUEUED — DO NOT IMPLEMENT` (unread even, not needed for this question). Arm individuation: not referenced. Plate L×W: not referenced beyond citing its already-settled absence. Airframe pose stub: confirmed still `DEFERRED`, not reopened — this investigation is exclusively about Continuity for the box-local field, never about a body-frame convention. Version: unchanged, `pyproject.toml` still `0.3.8`. Conversation Engine: rejected explicitly in §4.D.

---

## 5. Non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. `git status --short -- workspace/` is empty — every dry-run in §3 operated on an in-memory copy of `ProjectState`, loaded once via `model_validate_json`, never re-saved. No Scene3D/`layoutSolidsRow` file opened or modified. No fit stub touched. No `adelante`/`arriba`/`morro`/`gravedad` proposed as accepted grammar tokens — §2 names them explicitly as forbidden. No `mounted_on` used as an implicit pose origin anywhere in the proposed grammar — origin is always a separately-named noun in the phrase, resolved independently. No airframe `+X` claim, no arm individuation, no plate L×W invention. No package version bump. No Implementation Contract was written — §4.E is explicitly a contingency sketch, not IC-ready text; Cursor writes any IC after ★.
