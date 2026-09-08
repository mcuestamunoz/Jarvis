# Implementation Contract — Conn B1 (`mounted_on` subject/target parse symmetry)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · closable · suite **2429**  
**Review:** [implementation_review_connect_remaining_mounted_on_b1.md](implementation_review_connect_remaining_mounted_on_b1.md)  
**Report:** [implementation_report_connect_remaining_mounted_on_b1.md](implementation_report_connect_remaining_mounted_on_b1.md)  
**Parents:**
- [investigation_contract_connect_remaining_mounted_on_b1.md](investigation_contract_connect_remaining_mounted_on_b1.md)
- [investigation_report_connect_remaining_mounted_on_b1.md](investigation_report_connect_remaining_mounted_on_b1.md) — lean **B1**
- [investigation_review_connect_remaining_mounted_on_b1.md](investigation_review_connect_remaining_mounted_on_b1.md) — **PASS WITH NOTES** (N1 dual lock)
- Continuity declare B1 CLOSED @ **2380**
- Assembly relation rung CLOSED

**Type:** Narrow deterministic parse fix in `mounted_on_declare_assist.py` only.  
**Not** new mount vocabulary for frame parts as subjects. **Not** auto-infer. **Not** writer change. **Not** pose/fit. **Not** Here3 identity.

**Baseline:** package **`0.3.8`** · suite **2418**

**Output:** `.jes/artifacts/implementation_report_connect_remaining_mounted_on_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — parse symmetry bug-fix |
| 2 | Subject scope | Resolve subject only on text **before** first `\ben\b` (SET branch) |
| 3 | Target component nouns | On target segment, also match the **same** noun→key patterns as subjects when that key exists in `components` (so `"motores"` → `motors`) |
| 4 | Writer | **Unchanged** — still only `set_component_mounted_on` |
| 5 | Frame parts as subjects | **Still none** — `parent_key` remains composition |
| 6 | Inference / Board layout | **Out** |
| 7 | Version | **No** bump |

---

## 1. You

- Do **not** invent mounts or change `set_component_mounted_on`.
- Do **not** add `frame_arm`/`frame_plate`/cage/standoff as Continuity **subjects**.
- Do **not** open pose/fit/Conn auto-wizard / Conversation Engine.
- Do **not** bump package version.
- Full suite green. Zero weakened tests.
- Write the implementation report when done.

---

## 2. Intent

```text
"hélices montadas en los motores"
  → subject_segment (before en) → propellers
  → target_segment (after en)  → motors  (via component-noun alias)
  → SET → set_component_mounted_on

"sensor montado en el esc"
  → sensors → esc → SET  (no self-mount)
```

Product sentence:

> “Puedo declarar hélices en motores y sensor en ESC con las frases naturales — sin errores de causa falsa.”

---

## 3. Locked behavior

### 3.1 Subject before `en` (SET only)

In `parse_mounted_on_declare` SET branch:

```text
en_match = _EN_RE.search(normalized)
subject_segment = normalized[:en_match.start()] if en_match else normalized
subject = _resolve_subject(subject_segment)
```

Do **not** call `_resolve_subject(normalized)` on the full string for SET.

CLEAR branch: leave as-is (whole-string subject is fine; no target collision).

### 3.2 Target: component-noun aliases

After existing `_resolve_target` steps (exact key, plate labels, arm/cage/standoff/frame, bare plate), **or integrated cleanly inside it**:

If still unresolved, scan the target segment with the **same** `_SUBJECT_PATTERNS` (or a shared noun map extracted once). If a pattern matches and that canonical key is present in `components`, return that key as target.

Priority among component-noun matches: same fixed order as today’s subject table (fc > esc > motors > battery > sensors > propellers) — first match in the **target segment only**.

Do **not** invent keys absent from `components`.

Structure-part target nouns (arm/plate/…) stay as today; this alias path is for **electronics/propulsion/payload keys** that can be mount *targets* (esp. `motors`, also `esc`/`battery`/… when phrased in Spanish without using the raw key).

### 3.3 Non-regression

Existing working phrases must still SET/CLEAR/AMBIGUOUS as before:

- `"propellers montados en motors"` (literal)
- `"monta las helices en frame_arm"` / brazo
- `"sensor montado en la placa"` → AMBIGUOUS with 2+ plates
- `"quita el montaje del esc"` CLEAR
- `"esc montado en frame_plate"` (subject before en must still be esc, not confused)

### 3.4 Honesty

No copy changes required except that the previously wrong-cause paths now succeed. Forbidden tokens unchanged (`ensamblado` / `cabe` / `verificado`).

---

## 4. Tests (required)

Extend `tests/test_continuity_mounted_on_declare_b1.py` or add `tests/test_connect_remaining_mounted_on_b1.py`:

| # | Case |
|---|---|
| T1 | `"helices montadas en los motores"` → `SET(propellers, motors)` |
| T2 | `"sensor montado en el esc"` → `SET(sensors, esc)` — never self-mount |
| T3 | `"monta las helices en los motores"` → `SET(propellers, motors)` |
| T4 | Non-reg: `"propellers montados en motors"` still SET |
| T5 | Non-reg: `"sensor montado en la placa"` still AMBIGUOUS (2+ plates) |
| T6 | Non-reg: CLEAR `"quita el montaje del esc"` |
| T7 | Orchestrator IDLE: T1 phrase persists `propellers.mounted_on == "motors"` (fixture with both keys) |

Full suite green; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/mounted_on_declare_assist.py` | Subject segment + target component-noun alias |
| `tests/test_*mounted_on*.py` | T1–T7 |
| `.jes/artifacts/implementation_report_connect_remaining_mounted_on_b1.md` | write |

**Do not change:** `component_writers.py` · Board/UI · seeds · version · frame-part subject vocabulary

---

## 6. Explicit non-goals

Auto-infer mounts · frame-part subjects · guided “qué falta” list (B1+) · pose/fit · Here3 unfreeze · version bump · weakened tests

---

## 7. Done criteria

- [ ] T1–T3 collision phrases SET correctly  
- [ ] T4–T6 non-regressions  
- [ ] T7 orchestrator persist  
- [ ] Full suite green  
- [ ] Report written  
- [ ] Cursor review  

---

## 8. Stop conditions

Stop and ask before: adding frame-part subjects, changing writer validation, or any Board-layout inference.
