# Implementation Contract — Continuity explain topics expand (`B1-continuity-explain-topics-expand`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.7`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-09-29) — Cursor review PASS; package/tag **`0.6.7` / `v0.6.7`**.  
**Prior:** READY FOR ★ → Claude implemented → Cursor review → Engineer ACCEPT.  
**Parents:**
- A7 ★ ACCEPT CLOSED (2026-09-29) — chat explain intercept · package **`0.6.6`**
- A6/R3 ★ CLOSED @ **`v0.6.5`** — `explain_topics` + Conceptos; map already seeds `"current"` → `corriente-y-circuitos` but Continuity **never tags** it (no distinguished signal at R3 close)
- Tip / package parent: **`0.6.6`** mid-cycle · A0–A7 CLOSED on intelligence path before this Buy

**Type:** **Additive topic tagging expand** — wire one deferred R3 row (`current`) to a **real, already-distinguished** Continuity-visible signal; ranking / vault fences unchanged.  
**Opens:** **`0.6.7` / `v0.6.7`** on Engineer ACCEPT.  
**Cola:** **A8** (topic expand)

**Not:** maps expand (FS/HD keys) · R4 LLM cite · A4 voice/world · inventing a new Continuity ranking branch · Continuity reading `ontology/` · guessing `current` from generic energy/catalog gaps · N1 A7 flag casefold polish · craft autonomy · silicon.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-continuity-explain-topics-expand`** — tag `current` when OP electrical current is present |
| 2 | Signal (normative) | Tag topic **`current`** iff `project_state.current_parameters["motor_op_current_a"]` is **not** `None` (same OP-electrical field already surfaced via `_motor_op_electrical_from_params` / CLI). This is the “distinguished electrical/current” signal R3 deferred |
| 3 | Where | Extend `_explain_topics_for_continuity(...)` with a new bool kwarg e.g. `op_current_present: bool`. Compute that bool at the **existing** post-ranking call site in `build_project_continuity` (after `next_useful_step` / `next_useful_why` are final). Do **not** move the call earlier; do **not** feed topics into ranking |
| 4 | Map | Keep `CONTINUITY_TOPIC_MAP["current"]` → `["corriente-y-circuitos"]`. **Do not** add speculative new topic keys in this Buy unless a second signal is listed in §2 |
| 5 | Fence | `project_continuity.py` still **must not** import `jarvis.intelligence` / read `ontology/`. `intelligence/*` still **must not** import `jarvis.core` |
| 6 | Ranking | Byte-stable on existing R3/A7 fixtures: `next_useful_step` / `next_useful_why` / `situation` unchanged for fixtures that do not intentionally exercise the new tag |
| 7 | Conceptos | No new CLI formatter required — existing Conceptos + A7 chat intercept already consume topics |
| 8 | Version | Bump **`0.6.7`**; tag **`v0.6.7`** only after Engineer ACCEPT |
| 9 | Docs | USER_GUIDE_EXPLAIN §7 (mention `current` / corriente when OP current exists) · intelligence README · CONTINUITY_MAP one-liner · extend **C-115** Detail (new tagging rule) · PRIORIDAD A8 |

**Product sentence:**

```text
Si el craft ya tiene motor_op_current_a (OP eléctrico), Conceptos
puede apuntar a corriente-y-circuitos — sin que Continuity lea el vault
ni cambie el siguiente paso.
```

---

## 1. Tagging table (this Buy only)

| When (existing signal) | Topic to add |
|---|---|
| `motor_op_current_a is not None` in `current_parameters` | `current` |

All prior R3 rules remain:

| When | Topics |
|---|---|
| `motor_catalog_gap` / underspec live | `motor` |
| autonomy target / `energy_model_note` | `c_rate`, `operating_point` |
| watts recovery active | `operating_point`, `thrust_stand` |

Accumulate; de-dupe order = append order (stable). Empty → `[]`.

**Forbidden:** tagging `current` from watts-recovery alone, from generic `energy_model_note`, or from motor catalog gap — those are not current-specific.

---

## 2. Explicitly out (do not sneak in)

- New Continuity ranking branches or new `next_useful_why` codes  
- New ontology notes / vault edits  
- New `CONTINUITY_TOPIC_MAP` keys beyond what’s needed for §1 (map already has `current`)  
- `explain_maps` / `--rung` expansion  
- Bare-id chat steal / A7 behavior changes  

---

## 3. Files (expected)

| Area | Path | Change |
|---|---|---|
| Continuity | `src/jarvis/core/project_continuity.py` | New kwarg + tag rule; call-site passes `op_current_present` |
| Map | `src/jarvis/intelligence/continuity_cite.py` | Docstring only (unless map already missing `current` — it is present; leave map) |
| Tests | `tests/test_continuity_explain_topics_expand_b1.py` (new) and/or extend R3 file | T1–T5 below |
| Version | `pyproject.toml` | `0.6.7` |
| Docs | USER_GUIDE_EXPLAIN · intelligence README · CONTINUITY_MAP · CONNECTIONS C-115 · PRIORIDAD | §0.9 |

---

## 4. Tests

| ID | Assert |
|---|---|
| T1 | Fixture / helper: `op_current_present=True` → `"current"` ∈ `explain_topics`; resolves via `cites_for_topics` to solid id `corriente-y-circuitos` |
| T2 | Same fixture family with `op_current_present=False` and no other signals → `explain_topics == []` **or** unchanged prior topics without `current` |
| T3 | Ranking regression: existing R3 golden `next_useful_step` / `next_useful_why` strings on prior fixtures still match (topics additive only) |
| T4 | AST: `project_continuity.py` does not import `jarvis.intelligence`; `continuity_cite.py` does not import `jarvis.core` |
| T5 | `cites_for_topics(["current"])` still returns cite with DEFINICION (map + vault solid) |

Also bump/fix any stale `0.6.6` version checkpoint in the A7 test file to `0.6.7` (same established pattern).

---

## 5. Acceptance

- [ ] `current` tagged only on `motor_op_current_a` present  
- [ ] Ranking / step-why regression held  
- [ ] Fences AST held  
- [ ] Tests T1–T5 · report · docs · package `0.6.7`  
- [ ] Cursor review PASS · Engineer ACCEPT · tag **`v0.6.7`**

---

## 6. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-continuity-explain-topics-expand (A8)

IC: .jes/artifacts/implementation_contract_continuity_explain_topics_expand_b1.md

Extend _explain_topics_for_continuity with op_current_present: bool.
At the existing post-ranking call site in build_project_continuity, set it
from current_parameters["motor_op_current_a"] is not None. When true, append
topic "current" (map already → corriente-y-circuitos). Do NOT tag current
from watts-recovery or generic energy gaps. Do NOT change ranking / step / why.
No vault I/O in Continuity; no intelligence→core imports.
Tests T1–T5. Bump pyproject to 0.6.7. Docs: USER_GUIDE §7, intelligence
README, CONTINUITY_MAP, extend C-115. Report. Parent package 0.6.6.
No ACCEPT claim.
```

---

## 7. Engineer gate

Reply **★** (or “procede / implementa”) to authorize Claude.  
Until then: **no `src/` edits** for this Buy.
