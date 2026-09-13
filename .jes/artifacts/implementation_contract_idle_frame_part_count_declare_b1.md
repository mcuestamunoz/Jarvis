# Implementation Contract — IDLE frame-part count declare B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (this chat)  
**Reviewer:** Engineer smoke after report

**Status:** **CLOSED** — smoke **ACCEPT** with B7 ([smoke](engineer_smoke_geometry_standoff_layout_n_ne4_b7.md)) · [review](implementation_review_idle_frame_part_count_declare_b1.md) PASS WITH NOTES · suite **2686**  
**Parents:**
- Engineer ★ cola item — [engineer_note_idle_frame_part_count_declare.md](engineer_note_idle_frame_part_count_declare.md)
- Fit attestation **CLOSED** + smoke ACCEPT @ **2679**
- G-N1 parts-only (wizard-only today) — `orchestrator` ~4434 inside `DEFINE_MISSING` + `expected_keys[0]=="frame"`
- [Standoff count gate B4-min](implementation_contract_geometry_standoff_count_gate_b4.md) **CLOSED** @ **2661** — corners only when `frame_standoff.properties.count == 4`
- Feature lock — [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)

**Type:** IDLE deterministic bridge — parts-only `extract_all_frame_part_properties` → `upsert_frame_part` when frame already exists. Same extract + writer as G-N1. Never LLM. Never rewrite root from a part clause.  
**Not** N=6/8 visor layout. **Not** inventing Rooster `standoff_count`. **Not** Conversation Engine. **Not** Continuity `declara standoff_count` grammar. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **2679** → **2686** · UI **83** (Fit/Situar cycle; this Buy untouched `ui/`)

**Output:** `.jes/artifacts/implementation_report_idle_frame_part_count_declare_b1.md`  
**Review:** `.jes/artifacts/implementation_review_idle_frame_part_count_declare_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1 — IDLE frame-part declare** (count / material / arm thickness already parsed by extract) |
| 2 | Trigger | IDLE only. Phrase yields non-empty `extract_all_frame_part_properties(normalized)` |
| 3 | Frame gate | Active project has `components["frame"]` with completeness ≠ `low`. Else return `None` (fall through — do not invent frame) |
| 4 | Root guard | Same as G-N1: if `extract_frame_properties` carries any of `mass_kg` / `size_class_inch` / `configuration` / `wheelbase_mm` → **do not** take this bridge (`None`). Those stay on existing root / wizard / LLM-refused paths |
| 5 | Writer | Reuse `upsert_frame_part` only — merge props onto existing children; create child if missing. **Never** rewrite `frame.material` / root mass from a part clause (`standoffs aluminio` → standoff material only) |
| 6 | Message | Mirror G-N1 tone: `Frame partes: standoff×6.` (label = key without `frame_` prefix; append `×N` when count present) |
| 7 | Mode | Stay **IDLE** — do not open `DEFINE_MISSING`. Do not call `_set_pending_next_block` |
| 8 | Dispatch order | New IDLE check **after** fit-attestation bridge, **before** FN-005 help-choose — same family as pose / envelope / cabe / attest |
| 9 | Extract | **Zero** changes to `aerial.extract_all_frame_part_properties` / `_props_from_part_clause` unless a regression forces a surgical fix (report it) |
| 10 | Visor | No projector / `ui/` change. After `count=4`, existing B4-min corners remain; `count=6` still one box until a later ★ |
| 11 | Version / library | No bump · no seed invent |

**Product sentence:**

```text
En IDLE, “6 standoffs” / “6 separadores” escribe count en frame_standoff
sin LLM y sin abrir el wizard. “standoffs aluminio” solo material del
hijo. Sin count o N≠4 el visor no inventa cuatro pilares.
```

**Not:**

```text
layout N=6/8 · seed Rooster standoff_count · Conversation Engine ·
reabrir G-N1 wizard path · default 4 silencioso
```

---

## 1. You (implementer)

- Add `_try_handle_idle_frame_part_declare(user_input) -> dict | None` (or equivalent name) on the orchestrator.
- Wire it in the IDLE bridge strip after fit attestation, before FN-005.
- Prefer extracting a shared tiny helper with the G-N1 block **only if** it stays byte-faithful for the wizard path; otherwise duplicate the gate logic once with a comment pointing at G-N1 — do **not** refactor the wizard into a risky shared monster.
- Tests + report. Full pytest green. Zero weakened tests.
- **STOP** if the only way to green is inventing catalog `standoff_count` or drawing N≠4 corners.
- **STOP** if `6 standoffs` still reaches the LLM under IDLE + existing frame.

---

## 2. Intent

```text
IDLE + frame completeness ≠ low
        ↓
“6 standoffs” / “6 separadores” / “standoffs aluminio” / “4 brazos …”
        ↓
extract_all_frame_part_properties  (existing)
        ↓
no root mass/size/config/wheelbase in extract_frame_properties
        ↓
upsert_frame_part × each hit
        ↓
save · “Frame partes: …” · stay IDLE
```

Miss / low frame / root update / empty extract → `None` → existing IDLE chain (may still hit LLM for unrelated text — that is OK).

---

## 3. Locked behavior

### 3.1 Match / no-match

| Input (IDLE, frame OK) | Result |
|---|---|
| `6 standoffs` | `frame_standoff.properties.count == 6` · no LLM |
| `6 separadores` | same |
| `standoffs aluminio` | material only on standoff · root material unchanged |
| `4 brazos fibra` | arm count/material upsert · no LLM |
| `wheelbase 230` / `450g` alone | **not** this bridge (`None`) |
| no frame / frame completeness low | `None` |
| DEFINE_MISSING frame wizard | **unchanged** — existing G-N1 path only |

### 3.2 Multi-part

Same as extract: one entry per locked key. `"4 brazos, 6 standoffs"` may upsert both in one turn.

### 3.3 Photos / invent N

Do not add vision, image, or “count from photo” paths. Count only from declared digits in text via existing extract.

---

## 4. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | IDLE + existing non-low frame + `6 standoffs` → count 6 on `frame_standoff` · `_RefuseLLM` |
| T2 | `6 separadores` → same |
| T3 | `standoffs aluminio` → material on child · `frame.material` unchanged · `_RefuseLLM` |
| T4 | no frame → bridge returns / falls through without upsert |
| T5 | G-N1 wizard path still works (regression: open frame wizard + parts-only still upserts) |
| T6 | B4-min: after IDLE `4 standoffs`, projector still emits corners when plate+standoff boxes exist (reuse existing gate helpers / projector test style — optional if heavy; at least assert `count==4` on spec) |

Prefer new `tests/test_idle_frame_part_count_declare_b1.py`. Do not weaken `test_frame_parts_freetext_gn1.py`.

---

## 5. Files

| Path | Action |
|---|---|
| `src/jarvis/core/orchestrator.py` | IDLE bridge + helper |
| `tests/test_idle_frame_part_count_declare_b1.py` | write |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD sync after report |
| `.jes/state/engineering_state.json` | sync after report |
| `.jes/artifacts/implementation_report_idle_frame_part_count_declare_b1.md` | write |
| `domains/aerial.py` / `ui/` / `library/` / version | **no** (unless STOP-reported extract bug) |

---

## 6. Smoke (Engineer, ~3 min)

On `autonomía-de-5min` (or fresh) with frame already declared:

1. IDLE: `6 standoffs` → Continuity/BOM shows standoff count 6 · no LLM waffle.  
2. Board: still **not** four corner pillars (N≠4 omit) — expected.  
3. IDLE: `4 standoffs` → count 4; if Main Plate + standoff boxes exist, corners return (B4-min).  
4. IDLE: `standoffs aluminio` → material only; root frame material untouched.

---

## 7. Out of scope (separate ★)

- N=6/8 station / layout formula  
- Rooster / catalog `standoff_count` seed invent  
- Continuity `declara el count…` grammar  
- LLM pending deactivate map  
- C-114 / version bump  
- Platform Capability Vision packages
