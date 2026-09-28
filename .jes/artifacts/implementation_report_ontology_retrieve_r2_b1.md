# Implementation Report — Ontology retrieve R2 (`B1-ontology-retrieve-r2`)

**Project:** Jarvis
**Date:** 2026-09-28
**Implementer:** Claude Code
**Contract:** [`implementation_contract_ontology_retrieve_r2_b1.md`](implementation_contract_ontology_retrieve_r2_b1.md)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.2` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.2` is reserved for Engineer ACCEPT per IC §0 row 12 / §5.

---

## 1. Files changed

**New:**
- `src/jarvis/intelligence/ontology_retrieve.py` — `OntologyCite`, `retrieve_by_id`, `retrieve_by_nombre`
- `tests/test_ontology_retrieve_r2_b1.py` — T1–T7 (+2 supporting checks)

**Modified:**
- `src/jarvis/intelligence/__init__.py` — added `RETRIEVE_STATUS = "r2"` (additive, `SCAFFOLD_STATUS` unchanged) and re-exports `OntologyCite`/`retrieve_by_id`/`retrieve_by_nombre`
- `src/jarvis/intelligence/README.md` — added "Retrieve (R2, read-only)" section; updated "what this package is not (yet)" to reflect retrieve is now on and the canal (A3) is what remains not-wired; updated "Tip parent" and "Tests" sections
- `pyproject.toml` — `version = "0.6.1"` → `version = "0.6.2"`
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + A2 row updated to "delivered, awaiting Cursor review + Engineer ACCEPT"
- `docs/ARCHITECTURE.md` §1 — `intelligence/` knowledge-tree row updated: retrieve read-only on @ package `0.6.2`
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement line updated: retrieve delivered, pending ACCEPT before tag
- `docs/ONTOLOGY_CROSSWALKS.md` header — one-line epoch note: runtime read-only retrieve now exists under `intelligence/`, still not Continuity SoT (IC §3 optional pointer)

**Not touched:** `ontology/` (read-only), `library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.knowledge.retriever` (left empty, not reused per IC §0 row 13), any CLI/Board/Continuity module.

---

## 2. Package shape delivered

```text
src/jarvis/intelligence/
├── __init__.py          # SCAFFOLD_STATUS="stub" + RETRIEVE_STATUS="r2"; re-exports retrieve API
├── README.md             # honesty: retrieve on; canal = A3; still ≠ voice
└── ontology_retrieve.py  # OntologyCite, retrieve_by_id, retrieve_by_nombre
```

Matches IC §1 normative shape and public API exactly, including field order and types on `OntologyCite`.

---

## 3. Implementation notes

- **Frontmatter parsing:** a small line-based reader (`_parse_frontmatter`), not a general YAML library. The repo has no PyYAML dependency (`pyproject.toml` only lists `pydantic`), and the vault's R1 Plantilla frontmatter is a fixed, simple grammar (`key: value` scalars, `key: [a, b, c]` flow lists) — adding a new dependency for a one-shape read would exceed the smallest-safe-scope principle. If the vault's frontmatter grammar grows more complex in a future Buy, revisiting this choice is reasonable then, not now.
- **Section extraction:** `[DEFINICION]`/`[INTUICION]` are pulled via a regex anchored on `## [SECTIONNAME]` headers, capturing until the next such header or end of file, then stripping a trailing `---` divider. Verified against the real `C-rate de batería.md` note structure before writing the extractor.
- **Scope filter (IC §0 row 5):** `retrieve_by_id`/`retrieve_by_nombre` only match notes where frontmatter `estado == "solid"`. A note that exists with a matching id/nombre but is `draft`/`stub` is treated identically to an unknown id — both return `None`. The IC allows this ("miss → explicit not-found, do not invent"); no separate "found but not solid" signal was added, since the IC's normative `retrieve_by_id` signature returns `OntologyCite | None` only.
- **Path field:** computed repo-relative via `Path.relative_to(REPO_ROOT)`, matching the IC's example (`ontology/.../C-rate de batería.md`). `REPO_ROOT` is derived from `Path(__file__).resolve().parents[3]` (the file lives at `src/jarvis/intelligence/ontology_retrieve.py`), not hardcoded to any machine path, satisfying IC §0 row 8.
- **`knowledge/retriever.py`:** left completely untouched — not read, not imported, not extended (IC §0 row 13).

---

## 4. Tests

`tests/test_ontology_retrieve_r2_b1.py` — 9 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | `retrieve_by_id("c-rate-de-bateria")` returns non-`None` against the real vault | PASS |
| T2 | Cite has non-empty `definicion`/`intuicion`, `path` starts with `ontology/`, `estado == "solid"` | PASS |
| T3 | `never_invents == ["mass_g", "power_w", "thrust_gf", "autonomy_min"]` (matches frontmatter exactly) | PASS |
| T4 | Unknown id → `None`, no raise | PASS |
| T5 | No file under `intelligence/` imports `jarvis.flight_software`/`jarvis.vehicle_profiles` (AST-based) | PASS |
| T6 | Note mtime + content unchanged after retrieve call; module source contains no write API (`write_text`/`open(`/`.write(`/`unlink`/`os.remove`) | PASS |
| T7 | No file under `intelligence/` imports `jarvis.core`; no file calls a `submit_command`-named function | PASS |
| — | `SCAFFOLD_STATUS` unchanged (`"stub"`), `RETRIEVE_STATUS == "r2"` — additive, not breaking | PASS |
| — | `pyproject.toml` reads `version = "0.6.2"` | PASS |

```text
$ python -m pytest tests/test_ontology_retrieve_r2_b1.py -v
...
9 passed in 0.02s
```

Prior scaffold suite (`tests/test_intelligence_scaffold_b1.py`, T1–T5) re-run: **T1–T5 all still green.** One of my own *additional* (non-IC-required) checks from the prior Buy, `test_pyproject_version_is_0_6_1`, now fails — expected, and the same class of drift as the 49 pre-existing checkpoint failures documented below (a version string frozen at a Buy's own landing time, not one of the IC's T1–T5). No IC-mandated assertion from any prior Buy broke.

---

## 5. Full suite

```text
$ python -m pytest -q
50 failed, 3724 passed, 9 skipped in 8.06s
```

Before this Buy (parent tip `v0.6.1`), the same suite had **49** pre-existing, version-pinned checkpoint failures (documented in `implementation_report_intelligence_scaffold_b1.md` §5, and independently re-verified there via `git stash`). This Buy adds exactly **one** more of the same kind: `tests/test_intelligence_scaffold_b1.py::test_pyproject_version_is_0_6_1` — a non-IC-required check I added in the prior Buy that, by this repo's established convention, goes stale at every subsequent version bump rather than being retroactively rewritten. Net: 9 new tests added (all pass), 1 additional stale checkpoint (expected), zero new *behavioral* failures, zero tests weakened or deleted.

---

## 6. Docs pointers (IC §3)

- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line and A2 cola row now read "delivered, package `0.6.2`, awaiting Cursor review + Engineer ★ ACCEPT."
- `docs/ARCHITECTURE.md` §1 — `intelligence/` row updated: retrieve read-only on @ package `0.6.2`, naming the two public functions.
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement paragraph updated: retrieve delivered on disk, pending ACCEPT before tag; explicit "still no CLI/terminal canal — that is A3."
- `docs/ONTOLOGY_CROSSWALKS.md` header (optional per IC §3) — one-line epoch note added.

All are pointer-level edits (1–2 lines each), no rewrite epics.

---

## 7. Acceptance criteria (IC §5) — self-check

- [x] API + README honesty
- [x] Tests T1–T7 green against real `ontology/` solid notes
- [x] Implementation report at required path
- [x] Docs pointers updated
- [x] `pyproject.toml` = `0.6.2`
- [x] No CLI canal · no LLM · no Continuity/catalog write · no `knowledge/retriever.py` as public surface
- [x] Tag `v0.6.2` **not created** — reserved for Engineer ACCEPT

---

## 8. Stop conditions honored (IC §6)

- No CLI/Board/Continuity prompt wiring (A3) added.
- No embeddings/vector DB/RAG ranking — exact `id`/`nombre` match only.
- No claim that the Assistant "answers questions" end-to-end — README and module docstring both state this returns a cite, not an answer.
- **No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 9. Non-edits / git-state verification

```text
$ git status --short
 M .jes/state/engineering_state.json
 M docs/ARCHITECTURE.md
 M docs/IMPLEMENTATION_TASKS.md
 M docs/ONTOLOGY_CROSSWALKS.md
 M docs/PLATFORM_CAPABILITY_VISION.md
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/intelligence/README.md
 M src/jarvis/intelligence/__init__.py
?? src/jarvis/intelligence/ontology_retrieve.py
?? tests/test_ontology_retrieve_r2_b1.py
```

`.jes/state/engineering_state.json` and `ontology/.obsidian/workspace.json` were **already modified in the working tree before this Buy started** (same pre-existing local state noted in the prior Buy's report — unrelated to this IC, not written by this implementation). Every `ontology/` note itself shows zero diff — confirmed read-only:

```text
$ git diff --stat -- ontology/
(only ontology/.obsidian/workspace.json — Obsidian UI state, not a vault note)
```

```text
$ git diff --stat -- docs/ pyproject.toml
 docs/ARCHITECTURE.md               | 2 +-
 docs/IMPLEMENTATION_TASKS.md       | 4 ++--
 docs/ONTOLOGY_CROSSWALKS.md        | 2 +-
 docs/PLATFORM_CAPABILITY_VISION.md | 2 +-
 pyproject.toml                     | 2 +-
```

`library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles` — zero diff, confirmed untouched.

```text
$ git tag -l | sort -V | tail -1
v0.6.1

$ grep -m1 '^version' pyproject.toml
version = "0.6.2"
```

Tag remains **`v0.6.1`** — package bumped to `0.6.2` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.2`.
