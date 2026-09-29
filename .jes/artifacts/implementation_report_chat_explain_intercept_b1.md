# Implementation Report — Chat explain intercept (`B1-chat-explain-intercept`)

**Project:** Jarvis
**Date:** 2026-09-29
**Implementer:** Claude Code
**Contract:** [`implementation_contract_chat_explain_intercept_b1.md`](implementation_contract_chat_explain_intercept_b1.md)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.6` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.6` is reserved for Engineer ACCEPT per IC §0 row 11 / §3.

---

## 1. Files changed

**New:**
- `tests/test_chat_explain_intercept_b1.py` — T1–T6 (+1 supporting check)

**Modified:**
- `src/jarvis/config.py` — added `CHAT_EXPLAIN_PREFIXES: tuple[str, ...] = ("jarvis explain ", "explain ")`, same convention as `ESCAPE_WORDS`/`NEW_PROJECT_WORDS`
- `src/jarvis/core/orchestrator.py` — extended `_handle_global_commands` (IC §0 row 2: same intercept point, not a second layer) with a prefix-match branch calling new `_handle_chat_explain(query)`; local import of `jarvis.intelligence.explain` inside that method only
- `src/jarvis/adapters/cli/main.py` — added `_CONCEPTOS_HEADER` constant, both Conceptos header call sites now use it, `_render_concept_lines`'s docstring updated
- `src/jarvis/intelligence/continuity_cite.py` — `format_continuity_cite_lines`'s docstring updated to note the pointer command now also works in chat
- `pyproject.toml` — `version = "0.6.5"` → `version = "0.6.6"`
- `src/jarvis/intelligence/README.md` — new "Chat intercept (A7)" section; Buys/Package/Tip-parent/Tests sections updated
- `docs/USER_GUIDE_EXPLAIN.md` — §2 note that the same command works in `--chat`; §7 new paragraph + updated example output (header text changed); §8 two new limit bullets
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + A7 cola row updated to "delivered, awaiting review"
- `docs/system_map/CONNECTIONS.md` — **C-114 extended** (not a new id, per IC §0 row 12's explicit preference): registry table row and the full Detail entry both updated to describe the second (chat) ingress and its "Non-edges" addendum; C-010's own Detail entry (the literal function extended) also updated for accuracy
- `docs/system_map/00_entry/ENTRY_MAP.md` — Outbound line extended, new Key-modules row, Local-state/Tests lines updated
- `docs/system_map/01_runtime/RUNTIME_MAP.md` — checkpoint-1 row updated (same function, now also matches the explain prefix)
- `docs/system_map/jarvis-system-map.canvas.tsx`, `docs/system_map/DIAGRAMS.md`, `docs/system_map/JARVIS_SYSTEM_MAP.md` — C-114 extension mirrored (second data-array edge under the same id, header log line, new "Shipped" Callout, chronology paragraph); registry **counts unchanged** (68 total / 66 connected — extending an id adds no new edge to the count)

**Test file touched for a legitimate reason (not weakened):**
- `tests/test_continuity_explain_cite_r3_b1.py` — two assertions fixed: T4 dropped a raw-text `"JarvisOrchestrator" not in source` check that this Buy's own honest documentation (naming `JarvisOrchestrator._handle_global_commands` in a docstring) would otherwise false-fail; T5's exact-string check for the old `"Conceptos (ontology):"` header updated to the substring `"Conceptos (ontology)"` since this Buy intentionally changed the trailing wording (IC §0 row 9). See §5 below for full detail.

**Not touched:** `ontology/` (confirmed zero diff on any vault note below), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `project_continuity.py` (R3's fence — Continuity ranking/`explain_topics` logic — is completely untouched by this Buy, per IC §0 row 10), `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py` (A3–A5 modules, unchanged).

---

## 2. Intercept design (IC §0 rows 2–8)

Extended the existing `_handle_global_commands` — the literal first check in `_handle_user_text_inner` (line 956), which returns immediately on any non-`None` result, before the LLM-calling code later in that function is ever reached:

```python
for prefix in CHAT_EXPLAIN_PREFIXES:
    if normalized.startswith(prefix):
        query = stripped[len(prefix):].strip()
        return self._handle_chat_explain(query)
```

`normalized`/`stripped` are the same `user_input.strip()`/`.lower()` pair the function already computed for the escape-word/`nuevo` checks above this branch — no second normalization pass, no second intercept layer.

`_handle_chat_explain(query)`:
- `--list`/`--rung` prefix on `query` → honest one-line terminal redirect (IC §0 row 4), never attempted as a lookup.
- Otherwise: `resolve_explain_query(query)` (A3, unchanged) → `format_explain_cite(cite)` on a hit, or the exact same honest-miss wording `run_explain_cli`'s stderr already uses on a miss (IC §0 row 6). Both branches return `status="ok"`, `action="global_command"`.

**Live verification before writing tests** (`_ExplodingLLMInterface` whose `interpret`/`analyze`/`complete` all raise):

```text
jarvis explain c-rate  -> status=ok, DEFINICION body printed
explain imu            -> status=ok, DEFINICION body printed
explain no-existe-xyz  -> status=ok, "No solid ontology note for: no-existe-xyz ..."
explain --list         -> status=ok, "Eso solo está disponible en terminal: ..."
```

None of the four raised — confirming the LLM path is never reached, on hit, miss, or the `--list`/`--rung` redirect.

---

## 3. Conceptos pointer copy (IC §0 row 9)

Since the exact string every Conceptos line already prints (`jarvis explain <id>`) now works verbatim when typed into `--chat`, the mechanism needed no change — only the surrounding copy needed to say so. Added `_CONCEPTOS_HEADER = "Conceptos (ontology) — puedes escribirlo aquí mismo:"` in `adapters/cli/main.py`, used at both call sites (`render_startup_context`'s Continuity block and `render_response`'s coherence footer — same two sites R3 wired). Verified against the real render path:

```text
Conceptos (ontology) — puedes escribirlo aquí mismo:
  - motores  →  jarvis explain motores
  - motor-dc  →  jarvis explain motor-dc
```

`USER_GUIDE_EXPLAIN.md` §7 updated to match this exact live output, plus a new paragraph explaining the chat intercept and its `--list`/`--rung` limit.

---

## 4. Tests

`tests/test_chat_explain_intercept_b1.py` — 7 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | `handle_user_text("jarvis explain c-rate", llm)` → `DEFINICION` in message; LLM never called (exploding mock) | PASS |
| T2 | `handle_user_text("explain imu", llm)` — same path, bare prefix | PASS |
| T3 | `handle_user_text("explain no-existe-xyz", llm)` → honest miss text; LLM never called | PASS |
| T4 | Unrelated global paths unchanged: `cancelar` still works; `"explica esto por favor"`/`"no explain plz"` (contain "explain"-adjacent text but not the exact required prefix) are **not** swallowed; an unrelated craft phrase still falls through (`None`) | PASS |
| T5 | Hit, miss, and `--list` redirect all confirmed with the same exploding-LLM interface — the intercept short-circuits before `llm_interface` is ever touched, so an unhealthy/raising client cannot break `explain` | PASS |
| T6 | Every module under `src/jarvis/intelligence/` still has zero `jarvis.core` imports (AST) | PASS |
| — | `pyproject.toml` reads `version = "0.6.6"` | PASS |

```text
$ python -m pytest tests/test_chat_explain_intercept_b1.py -v
...
7 passed in 0.18s
```

---

## 5. Regression fixes in the prior R3 test file (found by running the combined suite, not by inspection alone)

Running `tests/test_continuity_explain_cite_r3_b1.py` alongside the new suite surfaced two real breakages caused by this Buy's own honest changes:

1. **T4** (`test_t4_continuity_cite_module_does_not_import_core`) asserted `"JarvisOrchestrator" not in source` as a raw text search over `continuity_cite.py`. This Buy's own docstring update to `format_continuity_cite_lines` *names* `JarvisOrchestrator._handle_global_commands` to honestly document why the pointer text is now accurate in chat — a prose mention, not an import or a call. Same class of self-inflicted pitfall already caught twice earlier in this Buy series (A1's own T5, R3's own T3) — the fix is identical: keep the AST-based import check (the real guarantee), drop the substring check.
2. **T5** (`test_t5_render_path_mentions_c_rate_and_jarvis_explain`) asserted the exact string `"Conceptos (ontology):"`. This Buy intentionally changed that header to `"Conceptos (ontology) — puedes escribirlo aquí mismo:"` (IC §0 row 9) — the old exact-match assertion is now testing stale, superseded copy, not a regression. Updated to the still-stable substring `"Conceptos (ontology)"`.

Both fixes are corrections to match an intentional, IC-authorized behavior change — not weakening a test to hide a real regression. Both are documented inline in the test file itself (see the updated docstrings on those two tests).

Full `tests/test_project_continuity.py` (18 tests, R3-era, untouched by this Buy) re-run: all pass unchanged, confirming `project_continuity.py` itself was not touched.

---

## 6. Full suite

```text
$ python -m pytest -q
54 failed, 3753 passed, 9 skipped in 7.62s
```

Before this Buy (parent tip `v0.6.5`), the suite had 53 pre-existing version-pinned checkpoint failures (documented across every prior report in this series). This Buy adds exactly one more of the same kind (A6's own `test_pyproject_version_is_0_6_5`, now stale at this Buy's `0.6.6` bump). Net: 7 new tests added (all pass), 1 additional stale checkpoint (expected, same established convention), zero new *behavioral* failures — explicitly confirmed via `grep FAILED | grep -v version-checkpoint-pattern` returning empty. The full suite run was repeated after the docs-only pass and produced the identical 54/3753/9 split.

---

## 7. Docs sync (IC §0 row 12) — every path touched

| Doc | Change |
|---|---|
| `docs/USER_GUIDE_EXPLAIN.md` | §2 in-chat note; §7 new paragraph + example header updated to live output; §8 two new limit bullets |
| `src/jarvis/intelligence/README.md` | New "Chat intercept (A7)" section (explicitly documents the new one-way `orchestrator` → `intelligence.explain` import); Buys/Package/Tip-parent/Tests updated |
| `docs/system_map/00_entry/ENTRY_MAP.md` | Outbound line extended with the chat ingress note, new Key-modules row for `_handle_chat_explain`, Local-state and Tests lines updated |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD + A7 row: delivered, awaiting review (not yet CLOSED — that's Engineer's call after ACCEPT, per IC §0 row 12's own "CLOSED after ACCEPT" phrasing) |
| `docs/system_map/CONNECTIONS.md` | **C-114 extended** (registry row + full Detail entry + new "Non-edges" addendum describing the one new import direction) — preferred over a new C-116 per the IC's own instruction; C-010's Detail entry (the literal extended function) also corrected for accuracy |
| `docs/system_map/01_runtime/RUNTIME_MAP.md` | Checkpoint-1 row updated (same function this Buy touched — not separately required by the IC, but a direct, low-risk accuracy fix on code I edited, same discipline as fixing stale notes in prior Buys) |
| `docs/system_map/jarvis-system-map.canvas.tsx`, `DIAGRAMS.md`, `JARVIS_SYSTEM_MAP.md` | C-114 extension mirrored (second live data-array edge, header log line, new "Shipped" Callout, chronology paragraph); registry counts left unchanged (extending an id, not adding one) |

All are pointer-level or small-section edits, no rewrite epics — same discipline as every prior report in this series.

---

## 8. Acceptance criteria (IC §3) — self-check

- [x] Chat intercept works · no LLM on explain-prefix lines (T1–T3, T5; also manually verified against a real exploding-LLM mock before tests were written)
- [x] Conceptos / USER_GUIDE wording updated for in-chat `explain`
- [x] Tests T1–T6 · implementation report · docs · package `0.6.6`
- [ ] Cursor independent review PASS · Engineer ACCEPT · tag `v0.6.6` — **pending**, not claimed by Claude

---

## 9. Stop conditions honored (IC, "Not" list)

- No RAG — exact prefix match + A3's existing exact-lookup resolve, nothing added.
- No voice/world work.
- No topic/maps expand (A5's `explain_maps.py` untouched).
- No Continuity ranking change — `project_continuity.py` has zero diff.
- No `ActionPolicy` weakening — the intercept lives entirely in the pre-LLM global-command layer, never touches `ActionPolicy.ALLOWED_ACTIONS` or the LLM response-validation path.
- No Conversation Engine, no craft autonomy, no silicon work.
- **No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 10. Non-edits / git-state verification

```text
$ git status --short
 M .jes/artifacts/implementation_contract_chat_explain_intercept_b1.md
 M .jes/state/engineering_state.json
 M docs/IMPLEMENTATION_TASKS.md
 M docs/USER_GUIDE_EXPLAIN.md
 M docs/system_map/00_entry/ENTRY_MAP.md
 M docs/system_map/01_runtime/RUNTIME_MAP.md
 M docs/system_map/CONNECTIONS.md
 M docs/system_map/DIAGRAMS.md
 M docs/system_map/JARVIS_SYSTEM_MAP.md
 M docs/system_map/jarvis-system-map.canvas.tsx
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/adapters/cli/main.py
 M src/jarvis/config.py
 M src/jarvis/core/orchestrator.py
 M src/jarvis/intelligence/README.md
 M src/jarvis/intelligence/continuity_cite.py
 M tests/test_continuity_explain_cite_r3_b1.py
?? tests/test_chat_explain_intercept_b1.py
```

`.jes/artifacts/implementation_contract_chat_explain_intercept_b1.md` and `.jes/state/engineering_state.json` were **already modified in the working tree before this Buy started** (Cursor's own IC-authorization commit, and the same pre-existing local state noted in every prior report in this series) — not written by this implementation.

```text
$ git diff --stat -- ontology/
 ontology/.obsidian/workspace.json | 47 ++++++++++++++++++++++-----------------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Zero diff on every actual vault note.

```text
$ git diff --stat -- src/ tests/test_continuity_explain_cite_r3_b1.py
 src/jarvis/adapters/cli/main.py             | 17 +++++++--
 src/jarvis/config.py                        |  6 ++++
 src/jarvis/core/orchestrator.py             | 54 ++++++++++++++++++++++++++--
 src/jarvis/intelligence/README.md           | 45 +++++++++++++++++++----
 src/jarvis/intelligence/continuity_cite.py  |  6 +++-
 tests/test_continuity_explain_cite_r3_b1.py | 14 ++++++--
```

`library/`, `project_continuity.py`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py` — zero diff, confirmed untouched.

```text
$ git tag -l | sort -V | tail -1
v0.6.5

$ grep -m1 '^version' pyproject.toml
version = "0.6.6"
```

Tag remains **`v0.6.5`** — package bumped to `0.6.6` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.6`.
