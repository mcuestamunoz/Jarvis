# Implementation Report — Assistant terminal canal (`B1-assistant-terminal-canal`)

**Project:** Jarvis
**Date:** 2026-09-28
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_terminal_canal_b1.md`](implementation_contract_assistant_terminal_canal_b1.md)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.3` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.3` is reserved for Engineer ACCEPT per IC §0 row 11 / §4.

---

## 1. Files changed

**New:**
- `src/jarvis/intelligence/explain.py` — `resolve_explain_query`, `format_explain_cite`, `run_explain_cli`
- `src/jarvis/intelligence/explain_aliases.py` — `EXPLAIN_ALIASES` (frozen seed dict)
- `tests/test_assistant_terminal_canal_b1.py` — T1–T6 (+2 supporting checks)

**Modified:**
- `src/jarvis/adapters/cli/main.py` — added the `explain` subparser (positional `query` arg, same grain as `board`) and dispatch branch (`raise SystemExit(run_explain_cli(args.query))`), local import inside the branch, matching the existing `board` pattern
- `src/jarvis/intelligence/README.md` — added "Terminal canal (A3)" section; updated "what this package is not (yet)" (canal ≠ chat, not "not wired"); updated Buys/Package header, Tip parent, and Tests sections
- `pyproject.toml` — `version = "0.6.2"` → `version = "0.6.3"`
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + A3 row updated to "delivered, awaiting Cursor review + Engineer ACCEPT"
- `docs/ARCHITECTURE.md` §1 — `intelligence/` knowledge-tree row: canal delivered @ package `0.6.3`
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement line updated: canal delivered, pending ACCEPT before tag

**Not touched:** `ontology/` (still read-only, only reached via A2), `library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `jarvis.knowledge.retriever`, `JarvisOrchestrator`/chat path (`run_chat`/`run_demo` in `main.py` untouched).

---

## 2. Shape delivered

```text
src/jarvis/intelligence/
├── __init__.py            # unchanged (SCAFFOLD_STATUS, RETRIEVE_STATUS)
├── README.md
├── ontology_retrieve.py   # unchanged (A2)
├── explain_aliases.py     # EXPLAIN_ALIASES — 4 seed entries
└── explain.py             # resolve_explain_query / format_explain_cite / run_explain_cli
```

```text
$ jarvis explain c-rate-de-bateria
$ jarvis explain c-rate
$ python -m jarvis.main explain c-rate-de-bateria
```

Wired in `src/jarvis/adapters/cli/main.py` beside the existing `board` subparser, same shape: subparser → thin dispatch branch → `raise SystemExit(<exit code>)`.

---

## 3. Resolve order and alias seed (IC §0 row 4, §1.1)

Deterministic, no re-ordering, no fallthrough after a match:

1. `retrieve_by_id(query)` — treat query as frontmatter `id`
2. else `retrieve_by_nombre(query)` — exact `nombre`, casefolded
3. else `EXPLAIN_ALIASES.get(query.casefold())` → `retrieve_by_id(alias_id)`
4. else `None` — CLI prints `No solid ontology note for: …` to stderr, exit 1

**Alias seed** (`explain_aliases.py`, 4 entries, within the IC's ≤8 cap):

| Alias key (casefold) | → `id` | Verified `solid` before seeding |
|---|---|---|
| `c-rate` | `c-rate-de-bateria` | Yes (frontmatter `estado: solid`) |
| `crate` | `c-rate-de-bateria` | Yes |
| `op` | `punto-de-operacion-vs-capacidad-intrinseca` | Yes — checked `ontology/03_Ingenieria/Electrónica/Punto de operación vs capacidad intrínseca/....md` line 7 (`estado: solid`) before adding |
| `operating point` | `punto-de-operacion-vs-capacidad-intrinseca` | Yes, same note |

No alias points at a non-solid or missing note.

---

## 4. Output shape (IC §0 row 5, §1.3)

Manual verification (`jarvis explain c-rate`):

```text
C-rate de batería  (id: c-rate-de-bateria)
Fuente: ontology/03_Ingenieria/Electrónica/C-rate de batería/C-rate de batería.md

[DEFINICION]
... (full section body)

[INTUICION]
... (full section body)

Citas: cited — Battery University BU-402 (C-rate); BU-105 (defs); BU-904 (capacity vs discharge); BU-1101 (glossary / coulomb ≠ C-rate)

Honestidad: esta explicación no inventa mass_g, power_w, thrust_gf, autonomy_min — esos valores deben venir de catálogo/Continuity, nunca de esta nota.
```

Matches IC §0 row 5 exactly: `nombre` · `id` · repo-relative `path` · `[DEFINICION]` · `[INTUICION]` · `formula_citation` line · `never_invents` honesty line (only printed when the list is non-empty).

---

## 5. Tests

`tests/test_assistant_terminal_canal_b1.py` — 8 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | `resolve_explain_query("c-rate-de-bateria")` yields cite with non-empty `definicion` | PASS |
| T2 | Alias `c-rate` (and `op`) resolve to the same note ids as direct `id` lookup | PASS |
| T3 | Unknown query → `resolve_explain_query` returns `None`; `run_explain_cli` returns exit code 1 | PASS |
| T4 | Formatted output contains every `never_invents` token, the honesty sentence, `definicion`, `intuicion`, and `path` | PASS |
| T5 | `explain.py`/`explain_aliases.py` never import `jarvis.core`; no call named `submit_command` or `JarvisOrchestrator` (AST-based) | PASS |
| T6 | Neither module imports anything llm/ollama/openai/anthropic-named (AST-based) | PASS |
| — | Subprocess smoke: `python -m jarvis.main explain c-rate-de-bateria` → exit 0, stdout contains `DEFINICION` + the id; `... explain not-a-real-id-xyz` → exit 1, stderr contains `No solid ontology note` | PASS |
| — | `pyproject.toml` reads `version = "0.6.3"` | PASS |

```text
$ python -m pytest tests/test_assistant_terminal_canal_b1.py -v
...
8 passed in 0.42s
```

Prior suites re-run: `tests/test_intelligence_scaffold_b1.py` (A1, T1–T5) and `tests/test_ontology_retrieve_r2_b1.py` (A2, T1–T7) — **all IC-mandated assertions still green.** Two of my own *additional* (non-IC-required) version-checkpoint tests from the prior two Buys now fail (`test_pyproject_version_is_0_6_1`, `test_pyproject_version_is_0_6_2`) — expected, same class of drift documented in both prior reports (a version string frozen at that Buy's own landing time, not an IC-mandated T1–TN assertion, and not retroactively rewritten per this repo's established convention).

---

## 6. Full suite

```text
$ python -m pytest -q
51 failed, 3731 passed, 9 skipped in 8.33s
```

Before this Buy (parent tip `v0.6.2`), the suite had 50 pre-existing version-pinned checkpoint failures (49 from before A1/A2, plus A1's own `test_pyproject_version_is_0_6_1` that went stale at A2's bump — both prior reports document this class). This Buy adds exactly one more of the same kind (A2's own `test_pyproject_version_is_0_6_2`, now stale at this Buy's `0.6.3` bump). Net: 8 new tests added (all pass), 1 additional stale checkpoint (expected), zero new behavioral failures, zero tests weakened or deleted.

---

## 7. Docs pointers (IC §2)

- `src/jarvis/intelligence/README.md` — new "Terminal canal (A3)" section describing `jarvis explain`, resolve order, alias seed, and honesty locks; "what this package is not (yet)" updated from "canal not wired" to "canal ≠ chat."
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line and A3 cola row now read "delivered, package `0.6.3`, awaiting Cursor review + Engineer ★ ACCEPT."
- `docs/ARCHITECTURE.md` §1 — `intelligence/` row updated: canal delivered @ package `0.6.3`, naming both the library call and the CLI entry.
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement paragraph updated: canal delivered on disk, pending ACCEPT before tag; explicit "still command-first only — no chat/RAG/LLM."

All are pointer-level edits, no rewrite epics.

---

## 8. Acceptance criteria (IC §4) — self-check

- [x] `jarvis explain` works for real solid id (verified manually + subprocess test)
- [x] Alias seed works for `c-rate` → C-rate note (and `op` → operating-point note)
- [x] Miss is honest (`None` / exit 1, no invented note)
- [x] `never_invents` surfaced in printed output
- [x] No LLM · no Continuity mutation · no RAG (AST-enforced, T5/T6)
- [x] Report + docs + `pyproject` `0.6.3`
- [x] Tag `v0.6.3` **not created** — reserved for Engineer ACCEPT

---

## 9. Stop conditions honored (IC §5)

- No free-form chat / "oye Jarvis" loop added — `explain` is one explicit subcommand; `run_chat`/`run_demo` untouched.
- No embeddings — alias resolution is a fixed `dict.get`, not search.
- No claim of a complete Iron Man Assistant — README and module docstring both state this is one command canal over A2 retrieve.
- **No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 10. Non-edits / git-state verification

```text
$ git status --short
 M .jes/state/engineering_state.json
 M docs/ARCHITECTURE.md
 M docs/IMPLEMENTATION_TASKS.md
 M docs/PLATFORM_CAPABILITY_VISION.md
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/adapters/cli/main.py
 M src/jarvis/intelligence/README.md
?? src/jarvis/intelligence/explain.py
?? src/jarvis/intelligence/explain_aliases.py
?? tests/test_assistant_terminal_canal_b1.py
```

`.jes/state/engineering_state.json` and `ontology/.obsidian/workspace.json` were **already modified in the working tree before this Buy started** — same pre-existing local state noted in both prior reports, unrelated to this IC, not written by this implementation.

```text
$ git diff --stat -- ontology/
(only ontology/.obsidian/workspace.json — Obsidian UI state, not a vault note; zero vault-note diff, confirming the canal only reads through A2)
```

```text
$ git diff --stat -- docs/ pyproject.toml src/jarvis/intelligence/ src/jarvis/adapters/cli/main.py
 docs/ARCHITECTURE.md               |  2 +-
 docs/IMPLEMENTATION_TASKS.md       |  4 ++--
 docs/PLATFORM_CAPABILITY_VISION.md |  2 +-
 pyproject.toml                     |  2 +-
 src/jarvis/adapters/cli/main.py    | 11 +++++++++
 src/jarvis/intelligence/README.md  | 49 +++++++++++++++++++++++++++++---------
```

`library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm` — zero diff, confirmed untouched. `src/jarvis/intelligence/ontology_retrieve.py` — zero diff, confirmed unchanged from A2.

```text
$ git tag -l | sort -V | tail -1
v0.6.2

$ grep -m1 '^version' pyproject.toml
version = "0.6.3"
```

Tag remains **`v0.6.2`** — package bumped to `0.6.3` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.3`.
