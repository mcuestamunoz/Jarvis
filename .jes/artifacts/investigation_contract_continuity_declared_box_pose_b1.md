# Investigation Contract — Continuity declared box-local pose B1 (CLI / IDLE)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede` 2026-09-08 — same sequencing as `mounted_on`: schema + writer + Board text **CLOSED**; next = **IDLE phrase** that calls the existing writer.  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_continuity_declared_box_pose_b1.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **B1** (`procede` 2026-09-08) · IC READY FOR CLAUDE  
**Report:** [investigation_report_continuity_declared_box_pose_b1.md](investigation_report_continuity_declared_box_pose_b1.md)  
**Review:** [investigation_review_continuity_declared_box_pose_b1.md](investigation_review_continuity_declared_box_pose_b1.md)  
**IC:** [implementation_contract_continuity_declared_box_pose_b1.md](implementation_contract_continuity_declared_box_pose_b1.md)  
**Parents (mandatory):**
- [implementation_contract_geometry_pose_declared_box_frame_b1.md](implementation_contract_geometry_pose_declared_box_frame_b1.md) — **CLOSED** suite **2438** + Engineer ACCEPT (`DeclaredBoxPose` + `set_component_declared_box_pose` + Board text)
- [implementation_review_geometry_pose_declared_box_frame_b1.md](implementation_review_geometry_pose_declared_box_frame_b1.md) — **PASS WITH NOTES** (no Continuity this Buy; same gap `mounted_on` had for one cycle)
- [engineer_smoke_geometry_pose_declared_box_frame_b1.md](engineer_smoke_geometry_pose_declared_box_frame_b1.md) — **ACCEPT**
- Precedent: [implementation_contract_continuity_mounted_on_declare_b1.md](implementation_contract_continuity_mounted_on_declare_b1.md) — **CLOSED** @ **2380** (`mounted_on_declare_assist` + orchestrator IDLE bridge)
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — rung 3 = place; Board drag ≠ pose
- Airframe pose stub — **still DEFERRED** (different Buy; do not reopen)
- Fit stub — **QUEUED — DO NOT IMPLEMENT**

**Type:** Investigation only — minimum honest **Continuity IDLE** path that writes `declared_box_pose` via the **existing** writer, so the Engineer can type a phrase and see `origen pose` / `Δx mm` on the Board card.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** Scene3D placement from numbers. **Not** `"cabe"`. **Not** arm individuation. **Not** plate L×W. **Not** Conversation Engine.

**Checkpoint base:** package **`0.3.8`** · suite **2438**

**Single objective (locked):**

> Determine the **minimum honest IDLE grammar + wiring** that calls `set_component_declared_box_pose` (no second writer), mirroring `mounted_on_declare_assist` thinness, without colliding with `"montado en"`, without treating L→+X as morro/gravedad, and without moving CSS 3D solids.

**Product sentence this would enable (only after a later ★ Buy ≠ B0):**

```text
Puedo declarar en el chat un desplazamiento en milímetros respecto al centro
de una caja ya medida (ejes locales declarados L→+X, W→+Y, H→+Z) y verlo
en la card. Eso no es el morro del drone ni “cabe.”
```

**Not:**

```text
Pon el ESC en su sitio · el sólido 3D se mueve · cabe · montado en = pose
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy / Defer / re-scope before any READY IC.

**Do not implement. Do not bump version. Do not change Scene3D / layoutSolidsRow. Do not un-QUEUE fit. Do not invent plate L×W or motor cylinder. Do not parse millimetres with the LLM. Do not treat Board x/y as pose.**

---

## 0. Role split

```text
Engineer  → procede (Continuity pose after writer CLOSED)
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_continuity_declared_box_pose_b1.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists now

Declared box-local pose B1 shipped **writer + Board text only**. Live demo cards do **not** show `origen pose` / `Δx` because nothing has written `declared_box_pose` into `state.json`. Phrases like “pon el ESC a 5 mm del FC” fall through (LLM / status) — they do **not** call the writer.

This is the **same sequencing hole** Continuity closed for `mounted_on` (schema @ **2364** → IDLE declare @ **2380**). The Engineer asked what to type in CLI; the honest answer today is **nothing for pose**.

Wrong next moves:

```text
move CSS 3D solids from numbers before a declare path exists
invent “morro / adelante / gravedad” as parse tokens
reuse montado-en assist to also write millimetres
open fit because cards still sit in a row
individuate frame_arm so CLI can say “brazo delantero”
```

---

## 2. Locked stances (do not re-litigate)

1. **Reuse writer only** — `set_component_declared_box_pose`. No second write path. Writer rules stand: origin must exist, must be projector `geometry.shape === "box"`, not self, not disk, not shapeless.  
2. **Axes copy is declared** — `locales declarados (L→+X, W→+Y, H→+Z); no morro; no gravedad`. Confirm strings must not say adelante / morro / gravedad / ensamblado / cabe / posición real.  
3. **Orthogonal to `mounted_on`** — pose does **not** require a mount; mount does **not** imply pose. Do not infer origin from `mounted_on`.  
4. **IDLE + active project** — same class as `mounted_on_declare_assist` / catalog rebind. Deterministic parse, **no LLM**.  
5. **Board already projects** — after a successful write + save, `_fields` already shows origin / honesty / optional Δ. Continuity does not need a new projector.  
6. **Scene3D out** — `layoutSolidsRow` stays a presentation row even if pose is declared. Placement of solids = later ★.  
7. **Live origins today** — demo boxes: `flight_controller`, `esc`, `battery`. Disks (`motors`, `propellers`) and shapeless frame parts **cannot** be origin (writer `ValueError` — report must keep that).  
8. **Airframe pose stub** stays DEFERRED. This investigation is Continuity for the **declared box-local** field, not body-frame +X.  
9. Prefer **thin** over wizard. B0 (no CLI, keep writer-only) is allowed if evidence says phrases cannot be honest yet.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `DeclaredBoxPose` + `set_component_declared_box_pose` | Confirm public signature, reject cases, Board labels (`origen pose`, `ejes pose`, `Δx mm`…) |
| `mounted_on_declare_assist.py` | Gate phrases, subject nouns, NONE vs SET vs AMBIGUOUS — **template**, not a merge |
| `Orchestrator._try_handle_mounted_on_declare` | IDLE order: where mount parse sits; what a pose assist must not steal |
| Demo `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` | Confirm `declared_box_pose` absent on all keys; list which keys `_geometry_from_spec` → box / disk / none |
| Tests | `tests/test_geometry_pose_declared_box_frame_b1.py` + Continuity mount declare tests — reuse pattern, do not weaken |
| Board copy constant | `POSE_AXES_HONESTY_LABEL` — confirmation message must stay compatible |

**Empirical (required):** dry-run (no persist) at least:

- a mount phrase (`esc montado en frame_plate`) — must remain mount, not pose
- a millimetre-shaped phrase with FC/ESC/battery nouns
- a phrase that would use `frame_plate` or `motors` as origin (expect reject if parsed as pose)
- a status / “montar el drone” phrase — must stay `NONE` for both assists

Cite results — do not guess. You may call the writer in a **throwaway** Python snippet against a **copy** of state; do **not** save the demo.

---

## 4. Questions the report must answer

### A. Collision with `mounted_on`

Can pose grammar be gated so `"montado en"` never writes millimetres? What tokens are **required** (mm / Δ / ejes / respecto) so status Spanish does not fire?

### B. Minimum grammar

Propose **one** B1 phrase family (not a language). Must include: subject key, origin key (box), at least one of `x_mm`/`y_mm`/`z_mm`, and a **clear** path. Name axis tokens that are honest (`x`/`largo`/`L` vs forbidden `adelante`/`arriba` if those imply gravity/nose).

Ambiguity: if origin noun matches two boxes, or none — do **not** guess (same class as plate list).

### C. Subjects vs origins

Which live keys may be **posed** (any existing component?) vs which may be **origin** (box only)? Recommendation: subject = any declared key except origin; origin = box-only. Confirm writer already encodes origin constraint.

### D. Buy options (must include)

| Option | Intent |
|---|---|
| **B0 — Keep writer-only** | No IDLE phrase; Engineer/tests call writer; Board text stays dark on demo | Allowed if grammar cannot be honest without morro/gravity |
| **B1 — Thin Continuity declare/clear** | New assist sibling + orchestrator bridge; **only** existing writer; Board text lights up | Default lean **if** A–C are solvable |
| **B1+ — Also move Scene3D solids** | Place CSS 3D from `declared_box_pose` | **Default reject this cycle** (IC of writer explicitly forbade visor move) |
| **B2 — LLM / Conversation Engine parse** | Natural language millimetres | **Reject** — Continuity stays deterministic |

### E. Contingency sketch (if Buy = B1)

Not an IC: new file (name suggestion: `declared_box_pose_declare_assist.py`), orchestrator hook **after** or **before** mount parse (justify order), confirm/error copy using honesty label, test file sketch. **No** UI logic change expected (cards already render `fields`).

### F. Out of scope checklist

Confirm untouched: Scene3D, fit stub, arm individuation, plate L×W, airframe pose stub, version, Conversation Engine.

---

## 5. Report format (mandatory)

1. **Executive recommendation** — B0 / B1 / B1+ / B2 + one sentence.  
2. **Collision + grammar** — working vs forbidden tokens.  
3. **Empirical parse / writer dry-runs.**  
4. **Buy options** with B1+ and B2 rejected or evidenced.  
5. **Contingency sketch** (if B1).  
6. **Non-goals honored.**

---

## 6. Done criteria (investigation)

- [ ] Live demo: pose field absent; box/disk/none census cited  
- [ ] Mount phrase proven not to collide  
- [ ] B0 allowed and evaluated honestly  
- [ ] If lean B1: one phrase family + file sketch, no IC yet  
- [ ] No code committed to `src/` / `ui/` / demo `state.json`

---

## 7. Stop conditions

Stop and ask before: proposing Scene3D move as part of this Buy; using `mounted_on` as implicit origin; adding `adelante`/`arriba` as axis synonyms; opening fit; merging this into the deferred airframe pose stub.
