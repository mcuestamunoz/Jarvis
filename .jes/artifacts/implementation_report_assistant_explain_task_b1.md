# Implementation Report — Assistant explain Task (`B1-assistant-explain-task`, T0)

**Project:** Jarvis
**Date:** 2026-09-29
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_explain_task_b1.md`](implementation_contract_assistant_explain_task_b1.md)
**Design parent:** [`design_contract_assistant_first_task_b0.md`](design_contract_assistant_first_task_b0.md) — ★ ACCEPT CLOSED (ratified as drafted)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.8` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.8` is reserved for Engineer ACCEPT per IC §0 row 11 / §4.

---

## 1. Files changed

**New:**
- `src/jarvis/intelligence/assistant_task.py` — `CAPABILITY_ONTOLOGY_EXPLAIN`, `TASK_KIND_EXPLAIN_CONCEPT`, `try_explain_concept_task`, `fulfill_ontology_explain`, `handle_explain_intent`
- `tests/test_assistant_explain_task_b1.py` — T1–T7 (+2 supporting checks)

**Modified:**
- `src/jarvis/core/orchestrator.py` — `_handle_global_commands`'s explain branch refactored: it now builds a `TerminalIntentAdapter`-parsed `Intent` and calls `assistant_task.handle_explain_intent`, instead of resolving the query itself. The old A7-only `_handle_chat_explain` method is **removed** (its logic now lives in `assistant_task.py`)
- `src/jarvis/intelligence/__init__.py` — module docstring extended to document `assistant_task.py` (not re-exported through `__all__`, same convention as `explain`/`explain_maps`/`continuity_cite`)
- `pyproject.toml` — `version = "0.6.7"` → `version = "0.6.8"`
- `tests/test_chat_explain_intercept_b1.py` — its own stale version-checkpoint test bumped `0.6.7` → `0.6.8` (IC §3: "bump prior version-checkpoint tests forward per established pattern")
- `tests/test_continuity_explain_topics_expand_b1.py` — same version-checkpoint bump
- `src/jarvis/intelligence/README.md` — new "Assistant Task seam (T0)" section; "Chat intercept (A7)" section rewritten to describe the new mechanism accurately (old text referenced the now-removed `_handle_chat_explain`); Buys/Package/Tip-parent/Tests sections updated
- `docs/USER_GUIDE_EXPLAIN.md` — one internal-architecture note appended after the A7 paragraph (no user-facing instruction changed — behavior is identical)
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + T0 cola row updated to "delivered, awaiting review"
- `docs/system_map/CONNECTIONS.md` — **C-114 extended** (registry row + full Detail entry rewritten for the two-ingress-one-classify shape) and **C-010's Detail entry corrected** (it referenced the removed `_handle_chat_explain` symbol — fixed while touching the same function this Buy modified)
- `docs/system_map/00_entry/ENTRY_MAP.md` — Key-modules row rewritten for the new mechanism, Tests line added for the new test file

**Not touched:** `ontology/` (confirmed zero diff below), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `project_continuity.py` (zero diff — the DC/IC's own Continuity fence, untouched by this Buy entirely), `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py`/`continuity_cite.py` (A2–A6 modules, unchanged — `fulfill_ontology_explain` calls `explain.py`'s existing functions without modifying them), `adapters/cli/main.py`'s `jarvis explain` subcommand (deliberately left calling A3 directly — see §3), `docs/system_map/01_runtime/RUNTIME_MAP.md`/`DIAGRAMS.md`/`JARVIS_SYSTEM_MAP.md`/canvas (not listed in this IC's own §0 row 12 docs list — left untouched this round, unlike A7's IC which explicitly named them).

---

## 2. API delivered (IC §1)

Exactly the normative shape, plus the optional thin helper:

```python
CAPABILITY_ONTOLOGY_EXPLAIN = "ontology.explain"
TASK_KIND_EXPLAIN_CONCEPT = "explain_concept"

def try_explain_concept_task(intent: Intent) -> Task | None: ...
def fulfill_ontology_explain(query: str, *, ontology_root: Path | None = None) -> str: ...
def handle_explain_intent(intent: Intent, *, ontology_root: Path | None = None) -> str | None: ...
```

- `try_explain_concept_task` reuses `jarvis.config.CHAT_EXPLAIN_PREFIXES` (the exact A7 table, not a second copy) to decide if `intent.raw_text` is explain-shaped. On a real query, it records `intent.metadata["task_kind"] = "explain_concept"` and `intent.metadata["explain_query"] = query` (IC §0 row 4's "record kind in Intent.metadata"), then returns `Task(intent_id=intent.id, required_capability_ids=["ontology.explain"])`.
- **`--list`/`--rung` get no Task** (IC §0 row 6's explicit preference): `try_explain_concept_task` treats a flag-only line as explain-shaped-but-refused, returning `None` rather than claiming a capability nothing actually fulfills.
- `fulfill_ontology_explain` is the provider: calls `jarvis.intelligence.explain.resolve_explain_query`/`format_explain_cite` (A3, unmodified) for a real query, or the same `--list`/`--rung` terminal-redirect string A7 always used.
- `handle_explain_intent` is the glue the orchestrator calls: extracts the query once, calls `try_explain_concept_task` for its metadata side-effect, and always fulfills — including the `--list`/`--rung` redirect, which still gets handled (just without a Task).

---

## 3. Orchestrator refactor (IC §0 row 7)

`_handle_global_commands`'s explain branch, before:

```python
for prefix in CHAT_EXPLAIN_PREFIXES:
    if normalized.startswith(prefix):
        query = stripped[len(prefix):].strip()
        return self._handle_chat_explain(query)   # orchestrator's own resolve+format copy
```

After:

```python
if normalized.startswith(CHAT_EXPLAIN_PREFIXES):
    from jarvis.capabilities.intent import TerminalIntentAdapter
    from jarvis.intelligence.assistant_task import handle_explain_intent

    explain_message = handle_explain_intent(TerminalIntentAdapter.parse(stripped))
    if explain_message is not None:
        return {"status": "ok", "action": "global_command", "message": explain_message}
```

`str.startswith` accepts a tuple directly, so the local prefix probe reuses `CHAT_EXPLAIN_PREFIXES` unchanged — it is only a cheap early-out to avoid constructing an `Intent` for every ordinary line; the actual classify/refuse decision lives entirely in `assistant_task.handle_explain_intent`, never duplicated here. The old `_handle_chat_explain` method (the "parallel resolve+format copy" the IC explicitly forbade keeping) is deleted, not left dead.

**`jarvis explain` (CLI, A3) deliberately left unchanged**, per IC §0 row 8's "either OK if cite text stays identical." Both `run_explain_cli` and `fulfill_ontology_explain` already call the identical `resolve_explain_query`/`format_explain_cite`, so cite-text drift between the two paths is structurally impossible regardless of whether the CLI is routed through the new helper. Routing it through `fulfill_ontology_explain` would have required either dropping the CLI's own tested exit-code/stderr contract (miss → stderr + exit 1, a fixed A3-era behavior with its own regression test) or re-deriving hit/miss a second time anyway — a redundant indirection with zero benefit. Documented in the README as a deliberate choice, not an oversight.

---

## 4. Live verification before writing tests

```text
jarvis explain c-rate      -> status=ok, DEFINICION body (unchanged from A7)
explain imu                -> status=ok, DEFINICION body (unchanged from A7)
explain no-existe-xyz      -> status=ok, "No solid ontology note for: ..." (unchanged)
explain --list              -> status=ok, "Eso solo está disponible en terminal: ..." (unchanged)
_handle_global_commands("cancelar")             -> unchanged (escape word)
_handle_global_commands("explica esto por favor") -> None (unchanged — near-miss not swallowed)
_handle_global_commands("quiero diseñar un dron")  -> None (unchanged — falls through)
```

All against an `ExplodingLLM` mock whose `interpret`/`analyze`/`complete` all raise — none raised, confirming zero LLM reach on any branch.

---

## 5. Tests

`tests/test_assistant_explain_task_b1.py` — 9 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | Explain-shaped `Intent` (either A7 prefix) → `Task` with `required_capability_ids == ["ontology.explain"]`; `intent.metadata` records `task_kind`/`explain_query` | PASS |
| T2 | Non-explain `Intent` (incl. near-miss `"explica esto por favor"`/`"no explain plz"`) → `None` Task, no metadata written | PASS |
| T3 | `fulfill_ontology_explain("c-rate")` returns DEFINICION cite body | PASS |
| T4 | Unknown query → honest miss string, no raise; `--list`/`--rung` → terminal redirect via fulfill, **no** Task emitted | PASS |
| T5 | Full `handle_user_text` chat path (hit/miss/`--list`) re-proves zero LLM calls through the new seam | PASS |
| T6 | `assistant_task.py` has zero `jarvis.core`/`jarvis.flight_software`/`jarvis.vehicle_profiles` imports; `project_continuity.py` still has zero `jarvis.intelligence` import (AST, both directions) | PASS |
| T7 | `pyproject.toml` reads `version = "0.6.8"` | PASS |
| — | `handle_explain_intent` result matches `try_explain_concept_task` + `fulfill_ontology_explain` called separately (consistency check) | PASS |
| — | `TerminalIntentAdapter.parse(...)` produces `IntentSource.TERMINAL` | PASS |

```text
$ python -m pytest tests/test_assistant_explain_task_b1.py -v
...
9 passed in 0.19s
```

`tests/test_chat_explain_intercept_b1.py` (A7, 7 tests, unmodified except the version-checkpoint bump) re-run against the refactored orchestrator: **all pass unchanged** — the exploding-LLM regression, the near-miss-phrase guard, and the escape-word/unrelated-phrase fall-through all hold through the new path.

---

## 6. Full suite

```text
$ python -m pytest -q
54 failed, 3769 passed, 9 skipped in 7.59s
```

Before this Buy (parent tip `v0.6.7`), the suite had 54 pre-existing version-pinned checkpoint failures. This Buy fixed A7's and A8's own stale checkpoints forward to `0.6.8` (−2 failures) but that's already netted into the same 54 baseline (both were already counted as failing pre-Buy); net effect: **54 failed, unchanged**, +9 passed (the new test file). Confirmed zero unexpected failures via `grep FAILED | grep -v <version-checkpoint pattern>` returning empty, both before and after the docs-only pass.

---

## 7. Docs sync (IC §0 row 12) — every path touched

| Doc | Change |
|---|---|
| `src/jarvis/intelligence/README.md` | New "Assistant Task seam (T0)" section; "Chat intercept (A7)" section corrected for the new mechanism (old text referenced the removed `_handle_chat_explain`); Buys/Package/Tip-parent/Tests updated |
| `src/jarvis/intelligence/__init__.py` | Module docstring documents `assistant_task.py` (per IC §2's export/document requirement — not re-exported through `__all__`, matching every prior submodule's own precedent) |
| `docs/USER_GUIDE_EXPLAIN.md` | One internal-architecture pointer after the A7 paragraph — no user-facing text changed, since behavior is identical |
| `docs/system_map/CONNECTIONS.md` | **C-114 extended** — registry row + full Detail entry rewritten for the two-ingress shape; **C-010's Detail entry corrected** (found stale while editing the same function, fixed in passing) |
| `docs/system_map/00_entry/ENTRY_MAP.md` | Key-modules row rewritten, Tests line added |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line + T0 cola row updated to "delivered, awaiting review" |

All are pointer-level or small-section edits, no rewrite epics — same discipline as every prior report in this series.

---

## 8. Acceptance criteria (IC §4) — self-check

- [x] `assistant_task.py` emits `explain_concept` Task / refuses honestly (T1/T2/T4)
- [x] A7 chat path routes through Assistant; no LLM; no UX regression on prefixes (T5, plus the unmodified A7 suite re-run green)
- [x] Fences AST held · Continuity untouched for ranking (T6; `project_continuity.py` has zero diff)
- [x] Tests T1–T7 · report · docs · package `0.6.8`
- [ ] Cursor review · Engineer ACCEPT · tag `v0.6.8` — **pending**, not claimed by Claude

---

## 9. DC locks honored (`design_contract_assistant_first_task_b0.md`)

- No forked Task type — `jarvis.capabilities.intent.Task` used as-is.
- `jarvis.intelligence` constructs the Task; orchestrator only calls it — confirmed by the refactor removing the orchestrator's own resolve logic entirely.
- Exactly one kind (`explain_concept`), exactly one capability string (`ontology.explain`) — no others introduced.
- No Conversation Engine, no LLM as SoT, no Continuity ranking/`step()`/craft-decision move into `intelligence/` — `project_continuity.py` diff is zero.
- No vehicle/world/voice work — untouched.
- Safety unaffected — this Task kind is read-only cite, never actuation; no Safety gate touched.

**No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 10. Non-edits / git-state verification

```text
$ git status --short
 M .jes/state/engineering_state.json
 M docs/IMPLEMENTATION_TASKS.md
 M docs/USER_GUIDE_EXPLAIN.md
 M docs/system_map/00_entry/ENTRY_MAP.md
 M docs/system_map/CONNECTIONS.md
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/core/orchestrator.py
 M src/jarvis/intelligence/README.md
 M src/jarvis/intelligence/__init__.py
 M tests/test_chat_explain_intercept_b1.py
 M tests/test_continuity_explain_topics_expand_b1.py
?? .jes/artifacts/design_contract_assistant_first_task_b0.md
?? .jes/artifacts/implementation_contract_assistant_explain_task_b1.md
?? src/jarvis/intelligence/assistant_task.py
?? tests/test_assistant_explain_task_b1.py
```

`.jes/state/engineering_state.json` and `ontology/.obsidian/workspace.json` were **already modified in the working tree before this Buy started** — same pre-existing local state noted in every prior report in this series, unrelated to this IC.

```text
$ git diff --stat -- ontology/
 ontology/.obsidian/workspace.json | 47 ++++++++++++++++++++++-----------------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Zero diff on every actual vault note.

```text
$ git diff --stat -- src/jarvis/core/project_continuity.py src/jarvis/intelligence/explain.py src/jarvis/intelligence/explain_aliases.py src/jarvis/intelligence/explain_maps.py src/jarvis/intelligence/ontology_retrieve.py src/jarvis/intelligence/continuity_cite.py
(no output — zero diff on all six)
```

`library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles` — zero diff, confirmed untouched.

```text
$ git tag -l | sort -V | tail -1
v0.6.7

$ grep -m1 '^version' pyproject.toml
version = "0.6.8"
```

Tag remains **`v0.6.7`** — package bumped to `0.6.8` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.8`.
