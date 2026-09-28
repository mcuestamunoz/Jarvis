# Implementation Contract — Assistant terminal canal (`B1-assistant-terminal-canal`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.3`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) @ tag **`v0.6.3`**  
**Review of record:** [`implementation_review_assistant_terminal_canal_b1.md`](implementation_review_assistant_terminal_canal_b1.md)  
**Parents:**
- [`B1-ontology-retrieve-r2`](implementation_contract_ontology_retrieve_r2_b1.md) — **★ ACCEPT CLOSED @ `v0.6.2`**  
- [`B1-intelligence-scaffold`](implementation_contract_intelligence_scaffold_b1.md) — ★ ACCEPT CLOSED @ `v0.6.1`  
- [`DC-assistant-placement`](design_contract_assistant_placement_b0.md) — ★ ACCEPT CLOSED  
- Engineer lock (2026-09-28): **RAG/LLM = semantic interpreter only**; product stays **command / pattern first**  
- Tip / package base: **`v0.6.2` / `0.6.2`**

**Type:** **Command-first terminal canal** — `jarvis explain …` prints a vault cite via A2 retrieve. No LLM. No Continuity intercept.  
**Opens package/tag:** **`0.6.3` / `v0.6.3`** on Engineer ACCEPT.  
**Not** voice/STT · not `world/` · not RAG/embeddings · not free-chat Conversation Engine · not Continuity/`step()` mutation · not catalog writes.

**Outputs (required):**
1. CLI subcommand wired (see §1)  
2. Thin resolve helper (optional module under `intelligence/` or CLI-local — prefer `intelligence/` if reusable)  
3. Tests (see §4)  
4. `.jes/artifacts/implementation_report_assistant_terminal_canal_b1.md`  
5. Living-doc pointers: PRIORIDAD A3 · ARCHITECTURE / PLATFORM one-liners · intelligence README  
6. `pyproject.toml` → **`0.6.3`**; tag **`v0.6.3`** only after Engineer ★ ACCEPT

**Checkpoint base:** **`v0.6.2` / `0.6.2`** until this Buy lands **`0.6.3`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-assistant-terminal-canal`** — first human-facing Assistant surface |
| 2 | Shape | **Explicit command**, not chat hijack. Subcommand name: **`explain`** (normative) |
| 3 | Invocation | `jarvis explain <query>` via existing argparse entry (`adapters/cli/main.py` subparsers, same grain as `board`) |
| 4 | Resolve order (deterministic) | (1) treat query as frontmatter **`id`** → `retrieve_by_id`; (2) else exact **`nombre`** → `retrieve_by_nombre`; (3) else optional **alias table** (exact casefold key → `id`) — see §1.1; (4) miss → honest failure message, exit non-zero |
| 5 | Output | Print (stdout): `nombre` · `id` · repo-relative `path` · `[DEFINICION]` · `[INTUICION]` · one honesty line listing `never_invents` when non-empty · optional `formula_citation` line. **Spanish** labels OK |
| 6 | No LLM | Zero LLM/Ollama/OpenAI calls on this path |
| 7 | No Continuity | Do **not** route through `JarvisOrchestrator` chat loop; do **not** call `submit_command`; do **not** mutate craft state |
| 8 | No RAG | No embeddings / vector search / fuzzy rank. Alias table is a **finite dict**, not search |
| 9 | Retrieve only | Use A2 API only; do not re-parse vault in CLI ad hoc if avoidable |
| 10 | Forbidden | Voice · world map · inventing SKU numbers · writing ontology · Conversation Engine |
| 11 | Version | Bump to **`0.6.3`**; tag on Engineer ACCEPT |

**Product sentence:**

```text
jarvis explain c-rate-de-bateria  →  DEFINICION + INTUICION + cita + never_invents
sin LLM, sin Continuity, sin inventar watts.
```

---

## 1. Shape (normative)

### 1.1 Alias table (minimal seed — exact keys only)

Ship a small frozen map (module constant), e.g. in `src/jarvis/intelligence/explain_aliases.py` or next to retrieve:

| Alias key (casefold) | → `id` |
|---|---|
| `c-rate` | `c-rate-de-bateria` |
| `crate` | `c-rate-de-bateria` |
| `op` | `punto-de-operacion-vs-capacidad-intrinseca` *(only if that id exists solid — verify before seeding; omit if missing)* |
| `operating point` | same as `op` if seeded |

**Do not** invent aliases for notes that are not `solid`. Prefer ≤8 seed aliases; expanding aliases is a later Buy / docs edit, not fuzzy matching.

If a candidate target id is not solid / missing → omit that alias from the shipped table (tests may assert seed keys that are included).

### 1.2 CLI

```text
jarvis explain <query>
```

- Success → print cite blocks; exit 0  
- Miss → e.g. `No solid ontology note for: …` (+ hint: use id or nombre); exit 1  
- Do not open interactive chat

Wire beside existing `board` subparser in `adapters/cli/main.py` (thin: parse → resolve → format → print). Formatting helper may live under `intelligence/` for testability.

### 1.3 Honesty in printed output

Must include when `never_invents` non-empty a clear line that retrieve/explain does **not** invent those craft quantities (catalog/Continuity remain SoT).

---

## 2. README / living docs

- `src/jarvis/intelligence/README.md` — canal terminal on @ `0.6.3`; still ≠ voice ≠ RAG  
- `docs/IMPLEMENTATION_TASKS.md` — A3 state  
- `docs/ARCHITECTURE.md` / `PLATFORM_CAPABILITY_VISION.md` — one-line pointers  

---

## 3. Tests (required)

New module e.g. `tests/test_assistant_terminal_canal_b1.py`:

| ID | Assert |
|---|---|
| T1 | Resolve/`explain` path for `c-rate-de-bateria` yields cite with non-empty definicion (library or CLI helper) |
| T2 | Alias `c-rate` (or shipped seed) resolves to same note id |
| T3 | Unknown query → miss (None / exit 1 path tested without inventing) |
| T4 | Formatted output includes `never_invents` honesty when present |
| T5 | Explain path does not import/call Continuity `submit_command` / does not construct orchestrator for this command |
| T6 | No LLM client import on the explain module(s) under test (AST or import graph) |

CLI smoke: prefer invoking the resolve+format functions directly; optional subprocess of `python -m jarvis.main explain c-rate-de-bateria` if stable in CI.

Keep A2 tests green. Do not weaken suite.

---

## 4. Acceptance criteria

- [ ] `jarvis explain` works for real solid id  
- [ ] Alias seed works for at least `c-rate` → C-rate note  
- [ ] Miss is honest  
- [ ] never_invents surfaced  
- [ ] No LLM · no Continuity mutation · no RAG  
- [ ] Report + docs + `pyproject` `0.6.3`  
- [ ] Tag `v0.6.3` only after Engineer ACCEPT  

---

## 5. Stop conditions

- Do not add free-form chat / “oye Jarvis” loop.  
- Do not add embeddings.  
- Do not claim Iron Man Assistant complete — this is one command canal.  
- Do not claim ACCEPT.

---

## 6. Paste for Claude

```text
★ AUTHORIZED implementation — B1-assistant-terminal-canal

IC: .jes/artifacts/implementation_contract_assistant_terminal_canal_b1.md

Add CLI: jarvis explain <query>
Resolve: id → nombre → finite alias table (seed c-rate → c-rate-de-bateria).
Print DEFINICION + INTUICION + path + never_invents honesty.
Use A2 retrieve only. No LLM, no Continuity/orchestrator, no RAG.
Tests T1–T6. Bump pyproject to 0.6.3 (tag after Engineer ACCEPT).
Write implementation_report_assistant_terminal_canal_b1.md

Parent tip v0.6.2. No ACCEPT claim.
```
