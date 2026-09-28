# Implementation Contract — Explain maps expand (`B1-explain-maps-expand`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.4`**

**Status:** ★ **AUTHORIZED** — await Claude implementation + report  
**Parents:**
- [`B1-assistant-terminal-canal`](implementation_contract_assistant_terminal_canal_b1.md) — **★ ACCEPT CLOSED @ `v0.6.3`**  
- [`B1-ontology-retrieve-r2`](implementation_contract_ontology_retrieve_r2_b1.md) — ★ @ `v0.6.2`  
- [`docs/ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md) — docs teach map (this Buy code-ifies a **finite** subset)  
- Engineer lock: command / pattern first · RAG/LLM later as interpreter only · ontology `id` ≠ core param namespace  
- Tip / package base: **`v0.6.3` / `0.6.3`**

**Type:** **Table expansion** under `intelligence/` — more aliases + FS/HD explain maps + list/rung CLI. No RAG. No Continuity cite. No voice.  
**Opens package/tag:** **`0.6.4` / `v0.6.4`** on Engineer ACCEPT.  
**Cola id:** **A5** (A4 voz/world stays **Parked**).

**Not:** A4 voice/STT/`world/` · embeddings · Continuity intercept · inventing SKU · rewriting vault notes · Conversation Engine.

**Outputs (required):**
1. Expanded `EXPLAIN_ALIASES` (see §1)  
2. Code maps: FS rungs + HD keys → ontology `id` lists (see §2)  
3. CLI: `jarvis explain --list` · `jarvis explain --rung <KEY>` (see §3)  
4. Tests (see §4)  
5. `.jes/artifacts/implementation_report_explain_maps_expand_b1.md`  
6. Docs pointers: PRIORIDAD A5 · ARCHITECTURE/PLATFORM one-liners · intelligence README · optional header note in `ONTOLOGY_CROSSWALKS.md`  
7. `pyproject.toml` → **`0.6.4`**; tag **`v0.6.4`** only after Engineer ★ ACCEPT

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-explain-maps-expand`** — bridges by tables, not search |
| 2 | Aliases | Expand finite alias dict so **every solid spine `id`** has ≥1 short alias (plus keep existing `c-rate`/`op` seeds). Exact casefold keys only |
| 3 | FS map | Ship `FS_EXPLAIN_MAP: dict[str, list[str]]` — keys like `C7`, `C10`, `C39` (normative seed in §2). Values = ontology ids (solid). Mirror [`ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md) §1 for the seeded keys only — **not** required to encode every row in one Buy |
| 4 | HD map | Ship `HD_EXPLAIN_MAP` for at least **`HD-001`**, **`HD-005`** → id lists from crosswalk §2 |
| 5 | CLI list | `jarvis explain --list` prints solid ids (from vault scan via existing retrieve helpers or a small list API) and known aliases — read-only |
| 6 | CLI rung | `jarvis explain --rung C7` (and HD keys) prints mapped ontology ids (+ nombre if cheap via retrieve). **Does not** dump all DEFINICION bodies by default (noise). Miss → exit 1 |
| 7 | Existing path | `jarvis explain <query>` resolve order **unchanged** (id → nombre → alias) |
| 8 | No RAG / LLM / Continuity | Same locks as A3 |
| 9 | Namespace honesty | README must state: these maps bridge **product keys → ontology ids**; they are **not** `core/` parameter ids |
| 10 | Version | Bump **`0.6.4`**; tag on ACCEPT |

**Product sentence:**

```text
Más puentes explícitos: aliases del spine + mapas FS/HD → ids,
y jarvis explain --list / --rung — sin RAG ni Continuity.
```

---

## 1. Alias expansion (normative seed)

Keep existing four aliases. **Add** at least these short keys → solid ids (adjust spelling only if an id is wrong — verify solid before ship):

| Alias (casefold) | → `id` |
|---|---|
| `imu` | `imu` |
| `gyro` / `giroscopio` | `giroscopio` |
| `accel` / `acelerometro` | `acelerometro` |
| `motor-dc` / `motor dc` | `motor-dc` |
| `motores` | `motores` |
| `actuadores` | `actuadores` |
| `dinamica` / `dynamics` | `dinamica` |
| `vectores` / `vectors` | `vectores` |
| `magnetismo` / `mag` | `magnetismo` |
| `corriente` | `corriente-y-circuitos` |
| `c-rate` … | *(already)* `c-rate-de-bateria` |
| `op` … | *(already)* `punto-de-operacion-vs-capacidad-intrinseca` |
| `banco` / `thrust stand` | `forma-medicion-banco-empuje` |
| `control clasico` / `pid` | `control-clasico` |
| `control robotico` | `control-robotico` |
| `navegacion` / `nav` | `navegacion-y-planificacion` |
| `momento` | `momento-y-rotacion` |
| `sensores movimiento` | `sensores-de-movimiento` |

Every target **must** be `estado: solid` at seed time. Prefer ≤40 alias keys total this Buy.

Also ensure: for each solid spine id, **either** the bare `id` string is already resolvable via `retrieve_by_id` (true today) **or** an alias exists — the table above covers human shorthand.

---

## 2. FS / HD maps (normative minimum seed)

Module e.g. `src/jarvis/intelligence/explain_maps.py`:

```python
FS_EXPLAIN_MAP: dict[str, list[str]] = {
    "C3": ["sensores-de-movimiento", "imu"],
    "C7": ["imu", "giroscopio", "acelerometro", "control-robotico", "vectores"],
    "C10": ["actuadores", "motores", "motor-dc"],
    "C39": ["navegacion-y-planificacion", "control-robotico"],
    "C42": ["imu", "sensores-de-movimiento"],
}
HD_EXPLAIN_MAP: dict[str, list[str]] = {
    "HD-001": ["c-rate-de-bateria", "corriente-y-circuitos", "punto-de-operacion-vs-capacidad-intrinseca"],
    "HD-005": ["forma-medicion-banco-empuje", "punto-de-operacion-vs-capacidad-intrinseca", "motor-dc"],
}
```

Keys case-normalized on lookup (`C7` / `c7` → same; `HD-001` / `hd-001` OK).  
Lookup API: `ids_for_rung(key) -> list[str] | None`.

**Do not** import `flight_software` to discover rungs — static table only.

---

## 3. CLI

Extend `explain` subparser:

| Invocation | Behavior |
|---|---|
| `jarvis explain <query>` | Unchanged (A3) |
| `jarvis explain --list` | Print solid note ids (+ alias → id lines). Exit 0 |
| `jarvis explain --rung KEY` | Print KEY + mapped ids (and nombre via retrieve when found). Exit 0 / 1 |

`--list` and `--rung` are mutually exclusive with positional query (argparse mutually exclusive group OK).

---

## 4. Tests (required)

`tests/test_explain_maps_expand_b1.py`:

| ID | Assert |
|---|---|
| T1 | Alias `imu` (or `gyro`) resolves via `resolve_explain_query` to solid cite |
| T2 | `ids_for_rung("C7")` returns list containing `imu` and `giroscopio` |
| T3 | `ids_for_rung("HD-001")` contains `c-rate-de-bateria` |
| T4 | Unknown rung → `None` / miss path |
| T5 | `--list` path (function or subprocess) mentions at least `c-rate-de-bateria` and one alias |
| T6 | No Continuity/LLM imports in new map modules (AST); no write to ontology |

Keep A2/A3 IC tests green.

---

## 5. Acceptance criteria

- [ ] Alias table expanded + solid-verified  
- [ ] FS/HD maps seeded as in §2  
- [ ] `--list` and `--rung` work  
- [ ] A3 query path unchanged  
- [ ] Tests T1–T6 green  
- [ ] Report + docs + `pyproject` `0.6.4`  
- [ ] Tag only after Engineer ACCEPT  

---

## 6. Stop conditions

- Do not implement A4 voice/world.  
- Do not add RAG/embeddings.  
- Do not wire Continuity auto-cite (future R3).  
- Do not claim ACCEPT.

---

## 7. Paste for Claude

```text
★ AUTHORIZED implementation — B1-explain-maps-expand

IC: .jes/artifacts/implementation_contract_explain_maps_expand_b1.md

Expand EXPLAIN_ALIASES (spine short keys, solid-only).
Add explain_maps.py: FS_EXPLAIN_MAP + HD_EXPLAIN_MAP (seed C3/C7/C10/C39/C42 + HD-001/HD-005).
CLI: jarvis explain --list and --rung KEY (query path unchanged).
No RAG, no Continuity, no voice. Tests T1–T6.
Bump pyproject to 0.6.4 (tag after Engineer ACCEPT).
Write implementation_report_explain_maps_expand_b1.md

Parent tip v0.6.3. No ACCEPT claim.
```
