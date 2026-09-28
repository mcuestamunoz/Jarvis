# Implementation Contract — Ontology retrieve R2 (`B1-ontology-retrieve-r2`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.2`**

**Status:** ★ **AUTHORIZED** — await Claude implementation + report  
**Parents:**
- [`B1-intelligence-scaffold`](implementation_contract_intelligence_scaffold_b1.md) — **★ ACCEPT CLOSED @ `v0.6.1`**  
- [`DC-assistant-placement`](design_contract_assistant_placement_b0.md) — ★ ACCEPT CLOSED  
- Ontology explain **CLOSED @ `v0.6.0`** — [close note](engineer_note_v0_6_0_ontology_epoch_close.md)  
- [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md) §7 branch (a) · R2  
- [`docs/ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md) — explain map (docs teach; retrieve reads vault)  
- Tip / package base: **`v0.6.1` / `0.6.1`**

**Type:** **Read-only retrieve + cite payload** inside `jarvis.intelligence` — no CLI canal (A3), no LLM, no Continuity write.  
**Opens package/tag:** **`0.6.2` / `v0.6.2`** on Engineer ACCEPT.  
**Not** terminal Assistant canal · not voice · not `world/` · not R3 Continuity cite · not R4 LLM cite · not catalog/`library/` writes · not `flight_software` / `step()`.

**Outputs (required):**
1. Retrieve API under `src/jarvis/intelligence/` (see §1)  
2. README honesty update (retrieve exists; canal = A3)  
3. Tests (see §4)  
4. `.jes/artifacts/implementation_report_ontology_retrieve_r2_b1.md`  
5. Living-doc pointers: PRIORIDAD A2 · ARCHITECTURE knowledge row · PLATFORM placement line  
6. `pyproject.toml` → **`0.6.2`**; git tag **`v0.6.2`** only after Engineer ★ ACCEPT

**Checkpoint base:** **`v0.6.1` / `0.6.1`** until this Buy lands **`0.6.2`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-ontology-retrieve-r2`** — first product read of `ontology/` vault |
| 2 | Home | Code lives in **`src/jarvis/intelligence/`** only (not `knowledge/retriever.py`, not `core/`) |
| 3 | Mode | **Read-only.** Never write vault, `library/`, Continuity state, or craft workspace |
| 4 | Lookup | By frontmatter **`id`** (exact). Optional alias: exact `nombre` match (casefold OK). **No** fuzzy RAG, embeddings, or LLM ranking in this Buy |
| 5 | Scope filter | Default: only notes with `estado: solid` (or body `[ESTADO]` solid if that is how a note records it — prefer YAML `estado`). Miss → explicit not-found, do not invent |
| 6 | Cite payload | Return structured fields: `id`, `nombre`, `path` (repo-relative), `estado`, `jarvis_relevance`, `never_invents`, `formula_citation` (if present), plus extracted sections **`[DEFINICION]`** and **`[INTUICION]`** when present (empty string if missing — do not fabricate) |
| 7 | Honesty | Surface `never_invents` to callers. Retrieve **explains**; it does **not** supply SKU watts/thrust/Wh. No number synthesis |
| 8 | Vault root | Resolve `ontology/` from repo root (same grain as other repo-rooted paths). Document how tests locate it. Do not hardcode absolute Engineer machine paths |
| 9 | Forbidden imports | Must **not** import `jarvis.flight_software`, `jarvis.vehicle_profiles`, or mutate via `jarvis.core` Continuity/`submit_command` |
| 10 | No canal | **No** CLI / Board / Continuity prompt wiring — that is **A3** |
| 11 | No LLM | No OpenAI/Anthropic/local LLM calls in this Buy |
| 12 | Version | Bump to **`0.6.2`**; tag `v0.6.2` on Engineer ACCEPT |
| 13 | Forbidden | Conversation Engine · inventing available flight · writing ontology · reusing empty `knowledge/retriever.py` as the public surface (may leave it empty / deprecate-pointer later — do not silently implement there) |

**Product sentence:**

```text
Desde intelligence/, leer una nota solid del vault por id y devolver
definición + intuición + metadatos de cita — sin inventar SKU ni cablear CLI.
```

---

## 1. Package shape (normative)

```text
src/jarvis/intelligence/
├── __init__.py          # may export retrieve entry + bump SCAFFOLD_STATUS or RETRIEVE_STATUS
├── README.md            # honesty: retrieve on; canal = A3; still ≠ voice
└── ontology_retrieve.py # read-only API (name OK if tests/import match)
```

**Public API (normative contract — names may be thin wrappers):**

```python
@dataclass(frozen=True)
class OntologyCite:
    id: str
    nombre: str
    path: str                 # repo-relative, e.g. ontology/.../C-rate de batería.md
    estado: str
    jarvis_relevance: list[str]
    never_invents: list[str]
    formula_citation: str | None
    definicion: str           # body of [DEFINICION] or ""
    intuicion: str            # body of [INTUICION] or ""

def retrieve_by_id(note_id: str, *, ontology_root: Path | None = None) -> OntologyCite | None:
    """Return cite for a solid note with matching YAML id, else None."""
```

Optional helper `retrieve_by_nombre(nombre: str, ...) -> OntologyCite | None` allowed if exact match only.

**Do not** add CLI commands, Board hooks, Continuity intercepts, or `world/` in this Buy.

---

## 2. README honesty (must state)

- Retrieve **read-only** over `ontology/` is available in this package @ `0.6.2`.  
- Vault **EXPLAINS**; catalog / Continuity / `step()` remain their own SoT.  
- Callers must respect `never_invents` — retrieve does not invent craft numbers.  
- **≠** terminal canal (A3) · **≠** voice · **≠** LLM answer synthesis.  
- Tip parent scaffold: **`v0.6.1`**. Ontology epoch: **`v0.6.0`**.

---

## 3. Living docs (pointers only)

- `docs/IMPLEMENTATION_TASKS.md` — A2 state when reporting  
- `docs/ARCHITECTURE.md` — `intelligence/` row: retrieve read-only on  
- `docs/PLATFORM_CAPABILITY_VISION.md` — placement line @ `0.6.2`  
- Optional one-liner in `docs/ONTOLOGY_CROSSWALKS.md` header: runtime read exists under `intelligence/` (still not Continuity SoT)

---

## 4. Tests (required)

New module e.g. `tests/test_ontology_retrieve_r2_b1.py`:

| ID | Assert |
|---|---|
| T1 | `retrieve_by_id("c-rate-de-bateria")` returns non-None against real vault |
| T2 | Cite has non-empty `definicion`, `path` under `ontology/`, `estado` solid |
| T3 | `never_invents` is a non-empty list for C-rate (as in frontmatter) |
| T4 | Unknown id → `None` (no raise, no invented note) |
| T5 | Source of `intelligence/` still has no imports of `jarvis.flight_software` / `jarvis.vehicle_profiles` |
| T6 | Retrieve does not write: after call, target note mtime/content unchanged (or open read-only / no write APIs used) |
| T7 | Does not import/call Continuity `submit_command` / write craft state |

Keep prior scaffold tests green (or update status constant assertions if `SCAFFOLD_STATUS` changes — prefer additive `RETRIEVE_STATUS = "r2"` rather than breaking T1–T5).

Do **not** weaken existing suite.

---

## 5. Acceptance criteria

- [ ] API + README honesty  
- [ ] Tests T1–T7 green against real `ontology/` solid notes  
- [ ] Implementation report at required path  
- [ ] Docs pointers updated  
- [ ] `pyproject.toml` = `0.6.2`  
- [ ] No CLI canal · no LLM · no Continuity/catalog write · no `knowledge/retriever.py` as public surface  
- [ ] Tag `v0.6.2` only after Engineer ACCEPT  

---

## 6. Stop conditions

- Do not wire CLI / Board / Continuity prompts (A3).  
- Do not add embeddings / vector DB / RAG ranking.  
- Do not claim Assistant “answers questions” end-to-end — only that retrieve returns a cite.  
- Do not claim ACCEPT — Cursor review + Engineer.

---

## 7. Paste for Claude

```text
★ AUTHORIZED implementation — B1-ontology-retrieve-r2

IC: .jes/artifacts/implementation_contract_ontology_retrieve_r2_b1.md

Add read-only ontology retrieve under src/jarvis/intelligence/
(ontology_retrieve.py): retrieve_by_id → OntologyCite
(DEFINICION + INTUICION + never_invents + path). Solid notes only.
No CLI, no LLM, no Continuity/catalog writes, no knowledge/retriever.py surface.
Tests T1–T7 against real vault (c-rate-de-bateria).
Bump pyproject to 0.6.2 (tag v0.6.2 only after Engineer ACCEPT).
Write implementation_report_ontology_retrieve_r2_b1.md

Parent tip v0.6.1. No ACCEPT claim.
```
