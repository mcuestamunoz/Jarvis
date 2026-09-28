# Implementation Contract — Continuity explain cite R3 (`B1-continuity-explain-cite-r3`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.5`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) @ tag **`v0.6.5`**  
**Review of record:** [`implementation_review_continuity_explain_cite_r3_b1.md`](implementation_review_continuity_explain_cite_r3_b1.md)  
**Parents:**
- Assistant A0–A5 ★ CLOSED @ **`v0.6.4`** (`jarvis explain` + maps)  
- [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md) §7 branch **(b) R3**  
- Engineer locks: Continuity decides craft · ontology EXPLAINS · RAG/LLM later as interpreter only · ontology ids ≠ core params  
- Tip / package base: **`v0.6.4` / `0.6.4`**

**Type:** **Additive Continuity → explain topics → cite** — Continuity emits finite topic tags; `intelligence/` resolves cites; CLI shows optional “Conceptos” lines. Continuity ranking / `next_useful_step` **unchanged**.  
**Opens package/tag:** **`0.6.5` / `v0.6.5`** on Engineer ACCEPT.  
**Cola id:** **A6** (A4 voz/world stays **Parked**).

**Not:** A4 voice · RAG/embeddings · Continuity reading vault to **choose** next step · LLM cite (R4) · inventing SKU · `flight_software` `/step()` coupling · Conversation Engine.

**Outputs (required):**
1. `intelligence` topic→id map + resolve helper (see §1)  
2. Continuity additive `explain_topics` only (see §2) — **no** vault I/O in Continuity  
3. CLI render of optional Conceptos block (see §3)  
4. Tests (see §4)  
5. `.jes/artifacts/implementation_report_continuity_explain_cite_r3_b1.md`  
6. Living docs sync (see §8)  
7. `pyproject.toml` → **`0.6.5`**; tag **`v0.6.5`** only after Engineer ★ ACCEPT

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-continuity-explain-cite-r3`** — first Continuity↔explain bridge |
| 2 | SoT fence | Continuity **still owns** `situation` / `next_useful_step` / `next_useful_why`. Cite is **additive garnish**, never overrides ranking |
| 3 | No vault in Continuity | `project_continuity.py` must **not** import `jarvis.intelligence` and must **not** read `ontology/` |
| 4 | Topics | Continuity may add `explain_topics: list[str]` — finite tags from §2 seed only. Empty list / omit key = no cite UI |
| 5 | Resolve | `intelligence` maps topic → ontology `id`(s) → `retrieve_by_id` (solid only). Miss topic → skip silently (no invented note) |
| 6 | CLI | `render_startup_context` (and coherence footer if it mirrors continuity) shows optional **Conceptos:** lines: `id` + short hint pointing to `jarvis explain <id>` — **do not** dump full DEFINICION/INTUICION bodies in estado (noise). Full body stays `jarvis explain` |
| 7 | Isolation | `intelligence/*` still must not import `jarvis.core` / call `submit_command` (AST keep) |
| 8 | No LLM / RAG | Exact table only |
| 9 | Version | Bump **`0.6.5`**; tag on ACCEPT |
| 10 | Docs | §8 living docs required |

**Product sentence:**

```text
Cuando Continuity diga el siguiente paso craft, opcionalmente
señala conceptos ontology relacionados — sin decidir el paso con el vault.
```

---

## 1. Intelligence API (normative)

New module e.g. `src/jarvis/intelligence/continuity_cite.py`:

```python
CONTINUITY_TOPIC_MAP: dict[str, list[str]] = {
    # topic tag → ontology ids (solid). Seed minimum:
    "c_rate": ["c-rate-de-bateria"],
    "operating_point": ["punto-de-operacion-vs-capacidad-intrinseca"],
    "motor": ["motores", "motor-dc"],
    "current": ["corriente-y-circuitos"],
    "thrust_stand": ["forma-medicion-banco-empuje"],
}

def cites_for_topics(topics: list[str], *, ontology_root: Path | None = None) -> list[OntologyCite]:
    """Resolve known topics to solid cites; unknown topics skipped; de-dupe by id."""
```

Optional thin formatter `format_continuity_cite_lines(cites) -> list[str]` for CLI.

---

## 2. Continuity additive tags (normative)

In `build_project_continuity` return dict, add:

```python
"explain_topics": [...]  # list[str], may be empty
```

**Seed tagging rules (deterministic — first-match / accumulate as listed; keep small):**

| When (existing Continuity signals) | Topics to include |
|---|---|
| `motor_catalog_gap` set / catalog underspec / motor ranking branch | `motor` |
| Autonomy / energy / battery language in next_step or energy_model_note path | `c_rate`, `operating_point` |
| Thrust / hover / OP / nameplate watts recovery path | `operating_point`, `thrust_stand` (if that branch is active) |
| Electrical / current-related gap copy if already distinguished | `current` |

If none match → `explain_topics: []`.

**Forbidden:** changing `next_useful_step` / `next_useful_why` / ranking order because of topics. Topics are computed **after** step/why are chosen, or in parallel without feeding back into ranking.

Prefer a tiny pure helper `_explain_topics_for_continuity(...)` in `project_continuity.py` (or sibling module under `core/` that still does not import intelligence) so unit tests can assert tags without CLI.

---

## 3. CLI render

In `render_startup_context` when continuity present:

```text
Conceptos: c-rate-de-bateria — jarvis explain c-rate-de-bateria
Conceptos: punto-de-operacion-vs-capacidad-intrinseca — jarvis explain op
```

Or one block:

```text
Conceptos (ontology):
  - c-rate-de-bateria  →  jarvis explain c-rate-de-bateria
```

Only if `explain_topics` non-empty **and** resolve yields ≥1 cite.  
CLI may `from jarvis.intelligence.continuity_cite import cites_for_topics` — that is the seam (same grain as `explain` subcommand importing intelligence).

Do **not** route Continuity chat turns through `jarvis explain` subprocess.

---

## 4. Tests (required)

`tests/test_continuity_explain_cite_r3_b1.py`:

| ID | Assert |
|---|---|
| T1 | Topic `c_rate` resolves to cite id `c-rate-de-bateria` with non-empty definicion |
| T2 | Continuity helper / `build_project_continuity` on a fixture that today yields motor-catalog or energy-related next step includes expected topic tag(s) — **and** same `next_useful_step` text as before topics existed (regression: compare golden step string or call without/with topics feature flaglessly — step must be identical to pre-Buy behavior for an existing unit fixture) |
| T3 | Continuity / core modules used for tagging do **not** import `jarvis.intelligence` (AST) |
| T4 | `intelligence/continuity_cite.py` does **not** import `jarvis.core` (AST) |
| T5 | Render path: given continuity dict with `explain_topics=["c_rate"]`, formatted Conceptos lines mention `c-rate-de-bateria` and `jarvis explain` |
| T6 | Unknown topic → no crash, empty cites |

Reuse existing Continuity fixtures where possible; do not weaken Continuity suite.

---

## 5. Acceptance criteria

- [ ] Topic map + `cites_for_topics`  
- [ ] Continuity emits `explain_topics` without vault I/O / without importing intelligence  
- [ ] Ranking / next_useful_step regression held  
- [ ] CLI Conceptos block  
- [ ] Tests T1–T6 green  
- [ ] §8 docs sync  
- [ ] `pyproject` `0.6.5` · tag only after ACCEPT  

---

## 6. Stop conditions

- Do not let Continuity read ontology to pick the next craft step.  
- Do not dump full note bodies into `estado`.  
- Do not implement R4 LLM cite or A4 voice.  
- Do not claim ACCEPT.

---

## 7. Paste for Claude

```text
★ AUTHORIZED implementation — B1-continuity-explain-cite-r3

IC: .jes/artifacts/implementation_contract_continuity_explain_cite_r3_b1.md

Add intelligence/continuity_cite.py (topic→ontology ids + cites_for_topics).
Continuity build_project_continuity adds explain_topics tags ONLY
(no intelligence import, no vault read; next_useful_step unchanged).
CLI render_startup_context shows optional Conceptos → jarvis explain <id>.
No RAG, no LLM, no full DEFINICION dump in estado.
Tests T1–T6. Docs sync IC §8.
Bump pyproject to 0.6.5 (tag after Engineer ACCEPT).
Write implementation_report_continuity_explain_cite_r3_b1.md

Parent tip v0.6.4. No ACCEPT claim.
```

---

## 8. Living docs sync (required)

| Doc | Change |
|---|---|
| `docs/USER_GUIDE_EXPLAIN.md` | Short §: Conceptos en `estado` / Continuity — optional lines; full text still `jarvis explain` |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` | One-line pointer if Continuity chat shows Conceptos |
| `docs/ARCHITECTURE.md` / `PLATFORM` / `IMPLEMENTATION_TASKS` | A6 / R3 state |
| `src/jarvis/intelligence/README.md` | Continuity cite seam + fence |
| `docs/JARVIS_KNOWLEDGE_VISION.md` | Branch (b) R3 status pointer when landed |
| `docs/system_map/CONNECTIONS.md` | New **`C-115`**: Continuity `explain_topics` → CLI → `intelligence.continuity_cite` → retrieve (read-only). Non-edge: Continuity ↛ vault decide |
| `docs/system_map/08_continuity/CONTINUITY_MAP.md` | Note additive `explain_topics` field |
| `docs/system_map/00_entry/ENTRY_MAP.md` | Conceptos render in startup context |
| Canvas / DIAGRAMS / JARVIS_SYSTEM_MAP | Mirror C-115 if registry updated |

Report must list every path.
