# Implementation Report — Assistant Task ↔ registry coherence (`B1-assistant-task-registry-coherence`, T3)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_task_registry_coherence_b1.md`](implementation_contract_assistant_task_registry_coherence_b1.md)
**Parents:** T2 `B1-capability-registry-product-fill` — ★ **ACCEPT CLOSED @ `v0.6.10`** (commit `c321842`, tag `v0.6.10` present); [`design_contract_capability_registry_product_fill_b0.md`](design_contract_capability_registry_product_fill_b0.md) §0 row 7 — the deferred "soft id known in registry check" this IC delivers
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.11` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.11` is reserved for Engineer ACCEPT per IC §0 row 9 / §4.

---

## 1. Files changed

**New:**
- `tests/test_assistant_task_registry_coherence_b1.py` — T1–T6, plus one optional test asserting the gate calls only `get_capability` (never `availability`/`providers`/`get_provider`)

**Modified:**
- `src/jarvis/intelligence/assistant_task.py` — added `from jarvis.capabilities.registry import CapabilityRegistry` (new, explicitly authorized one-way edge, IC §0 row 6); added `_capabilities_known_in_default_registry(capability_ids: list[str]) -> bool`; wired the gate into both `try_explain_concept_task` and `try_defer_to_continuity_task` (build `Task` → gate → write `intent.metadata`/return, or refuse with `None` and no metadata write on a miss); module docstring extended to mention T3
- `pyproject.toml` — `version = "0.6.10"` → `version = "0.6.11"`
- `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py` — their own stale version-checkpoint assertions bumped `0.6.10` → `0.6.11` (IC §2: "bump stale `0.6.10` checkpoints forward")
- `tests/test_capability_registry_product_fill_b1.py::test_t6b_assistant_task_and_orchestrator_untouched_by_this_buy` — corrected: this test previously asserted `assistant_task.py` must **not** import `jarvis.capabilities.registry`, a constraint that was T2-scoped and explicitly deferred to a later IC (this one). Removed only that now-superseded sub-assertion (and the now-unused `assistant_task_path` local); kept the still-true half (`registry.py` must not import `jarvis.intelligence`); docstring rewritten to explain the supersession and point at this Buy's own AST fence test (T5) as the new authority on `assistant_task.py`'s import direction. See §4 below for why this is a correction, not a weakening.
- `src/jarvis/intelligence/README.md` — new "Registry coherence gate (T3)" section (placed above the T1 section, newest-first per existing convention); Buys/Package lines updated to `0.6.11`; the T0-section line that said `assistant_task.py` "still does not import `jarvis.capabilities.registry`" corrected to describe the new T3 edge; the T1-section capability-row note extended with a T3 pointer
- `docs/PLATFORM_CAPABILITY_VISION.md` — §12 Placement line updated (T2 now correctly shown ★ ACCEPT CLOSED @ `v0.6.10`, not "awaiting"; new T3 clause added); §13 T2 entry corrected from "awaiting Engineer ★ ACCEPT" to "★ ACCEPT CLOSED @ `v0.6.10`" (true as of this session, confirmed via `git log`/`git tag`) and its stale "`assistant_task.py` does not look up this registry" clause removed; new T3 paragraph added with the requested one-liner ("Assistant soft-checks ids against default registry; still not a dispatcher")
- `docs/system_map/CONNECTIONS.md` — **extended the existing T2 note** (corrected its "awaiting Engineer ★ ACCEPT" status to ACCEPT CLOSED, removed its now-false "`assistant_task.py` does not import `jarvis.capabilities.registry`" clause) and **added a new paragraph directly below it** for T3, explicitly noting it flips that one clause and cross-referencing this report. **No new `C-xxx`**, per IC §0 row 10.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T3 cola row updated from "IC READY FOR ★" to "IMPLEMENTED · package `0.6.11`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link

**Not touched (verified — see §4):** `src/jarvis/core/orchestrator.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/data/default_registry.json`, `src/jarvis/capabilities/schemas.py`, `src/jarvis/capabilities/__init__.py`, `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py`/`continuity_cite.py`, `config.py` (`CHAT_EXPLAIN_PREFIXES`/`CONTINUITY_DEFER_PHRASES` unchanged).

---

## 2. The gate itself (IC §1, §0 rows 3–4)

```python
def _capabilities_known_in_default_registry(capability_ids: list[str]) -> bool:
    registry = CapabilityRegistry.load_default()
    return all(registry.get_capability(cid) is not None for cid in capability_ids)
```

Call-site pattern in both `try_explain_concept_task` and `try_defer_to_continuity_task`, matching the IC's own required ordering exactly (§0 row 4: "build Task, check, then write metadata / return; if check fails, return `None` with no `task_kind` written"):

```python
required_capability_ids = [CAPABILITY_...]
task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
if not _capabilities_known_in_default_registry(required_capability_ids):
    return None
intent.metadata["task_kind"] = ...
return task
```

`Task(...)` is constructed *before* the gate runs (needed to read `required_capability_ids` off it, per the IC's own sketch) but `intent.metadata` is only ever written *after* the gate passes — so a refuse never leaves partial/dangling state on the caller's `Intent`, matching IC §0 row 4 precisely.

**Membership only (IC §0 row 5).** The gate calls exactly one registry method, `get_capability`. It never reads `.availability`, never calls `.providers()`/`.get_provider()`/`.providers_offering()`, and neither `try_*` function's fulfill path (`fulfill_ontology_explain`, `core._handle_project_status()`) was touched. This is asserted directly by a dedicated test (`test_gate_does_not_touch_availability_or_providers`), which subclasses `CapabilityRegistry` to record every method call and asserts the recorded sequence is exactly `["get_capability", "get_capability"]` across one call to each `try_*` function.

---

## 3. Manual verification (before writing tests)

Ran live against the actual `data/default_registry.json` seed (T2's two rows, both `available`):

```text
explain happy: Task(id=..., intent_id=..., required_capability_ids=['ontology.explain'])
  metadata: {'task_kind': 'explain_concept', 'explain_query': 'c-rate'}
defer happy:   Task(id=..., intent_id=..., required_capability_ids=['engineering.continuity'])
  metadata: {'task_kind': 'defer_to_continuity'}
```

Then monkeypatched `CapabilityRegistry.load_default` to return an empty `CapabilityRegistry()` and re-ran the same two lines:

```text
explain refuse: None   metadata: {}
defer refuse:   None   metadata: {}
```

Both the happy path (T2 seed present → same Tasks T0/T1 always emitted, IC §0 row 7) and the refuse path (registry missing the id → `None`, no `task_kind` written, IC §0 row 4) behave exactly as specified. This was re-run a second time after T2 landed and tagged `v0.6.10` mid-session (see §6) to confirm nothing shifted under the new HEAD — identical results.

---

## 4. Correcting `test_t6b` in T2's own suite (not a weakening)

T2's `test_t6b_assistant_task_and_orchestrator_untouched_by_this_buy` asserted, as part of proving T2 made zero changes to `assistant_task.py`, that `assistant_task.py` does not import `jarvis.capabilities.registry` at all. That was true *of T2* and was never meant to be a permanent fence — T2's own IC/DC explicitly named this exact edge as **deferred to a later IC** (T2 IC "Parents": *"the design_contract_capability_registry_product_fill_b0.md §0 row 7 — explicitly deferred 'soft id known in registry check' to a later IC"*). This Buy's IC (§0 row 6) is that later IC, and it explicitly authorizes the edge: *"`assistant_task` **may** import `jarvis.capabilities.registry.CapabilityRegistry`"*.

So the old assertion is not a regression to paper over — it is a T2-scoped snapshot that this IC was always going to supersede. I removed only that one sub-assertion (and its now-unused `assistant_task_path` local), kept the still-true half of the same test (`registry.py` still never imports `jarvis.intelligence` — verified independently below too), and rewrote the docstring to say exactly why, pointing at this Buy's own AST fence (T5) as the new authoritative check on `assistant_task.py`'s import direction. Nothing about the isolation/no-dispatch guarantees the test protects was loosened — the one clause removed encoded a constraint this IC was explicitly authorized to lift.

---

## 5. Tests

`tests/test_assistant_task_registry_coherence_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | Explain-shaped Intent still → `Task(ontology.explain)` with T2 seed present | PASS |
| T2 | `estado` still → `Task(engineering.continuity)` with T2 seed present | PASS |
| T3 | Monkeypatched empty registry → explain-shaped Intent → `None`, no `task_kind`/`explain_query` on metadata | PASS |
| T4 | Same monkeypatch → `estado` → `None`, no `task_kind` | PASS |
| T5 | AST: `assistant_task.py` **may** import `jarvis.capabilities.registry` (asserted present); must **not** import `jarvis.core`/`jarvis.flight_software`/`jarvis.vehicle_profiles`; `registry.py` still does not import `jarvis.intelligence` | PASS |
| T6 | `pyproject.toml` reads `0.6.11` | PASS |
| (extra) | Gate calls only `get_capability` (never `availability`/`providers`/`get_provider`) | PASS |

```text
$ python3 -m pytest tests/test_assistant_task_registry_coherence_b1.py -v
7 passed
```

Regression — T0/T1/T2 suites plus the new T3 suite together:

```text
$ python3 -m pytest tests/test_assistant_task_registry_coherence_b1.py \
    tests/test_assistant_explain_task_b1.py \
    tests/test_assistant_defer_continuity_b1.py \
    tests/test_capability_registry_product_fill_b1.py \
    tests/test_fase_c_capability_registry_scaffold_b1.py -q
46 passed
```

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3793 passed, 9 skipped
```

All 52 failures are pre-existing, older stale version-checkpoint assertions (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`) predating this Buy's scope — the IC named only stale `0.6.10` checkpoints to bump forward (§2), and every `0.6.10` checkpoint found via `grep -rl '0\.6\.10' tests/` (7 files) was bumped (§1). This is the same accepted drift pattern documented in every prior Buy's report this session; none of the 52 failures involve `assistant_task.py`, the registry, or any file this Buy touched.

---

## 6. Git-state note: T2 landed mid-session

At the moment this IC was authorized, T2 was Cursor-reviewed **PASS** with an Engineer-signed review doc but its commit/tag had not yet appeared in `git log`/`git tag` (confirmed via `git log --oneline -5`, `git tag -l | sort -V | tail -3`, and `git status --short | wc -l` = 62 modified files, matching the full T2-era working tree). Partway through this Buy's implementation, `git log` showed a new commit `c321842 Close Assistant T2 capability registry product fill.` and `git tag -l` gained `v0.6.10` — T2 was committed and tagged by the Engineer/Cursor side of this session while T3 work was in progress. `git status --short` dropped from 62 to the 15 files this Buy actually touches (docs, `pyproject.toml`, `assistant_task.py`, the version-checkpoint test bumps, `ontology/.obsidian/workspace.json`). All manual verification and the full suite run in §3/§5 above were re-run against this new HEAD to confirm nothing shifted; results were identical. This report's file-changed list and doc updates (§1) reflect the corrected, now-true state (T2 ★ ACCEPT CLOSED @ `v0.6.10`, not "awaiting").

One transient tooling issue during this same window is worth naming for the record: an early attempt at editing `assistant_task.py` reported success via the edit tool but did not persist to disk (independently confirmed via `grep`/`wc -l`/`git diff --stat`, which all showed the file unchanged from its pre-T3 HEAD state) — most likely a race with the concurrent T2 commit landing at the same moment. The edits were redone from scratch and each one verified independently via `grep`/`git diff --stat` immediately after applying, before proceeding to the next. No functional impact — the final on-disk state matches the IC exactly.

---

## 7. IC acceptance checklist self-check

- [x] Both Task emitters soft-check default registry membership before return
- [x] Unknown id → `None`, no raise, no dangling Task (verified live, §3; tested T3/T4)
- [x] T0/T1 happy path unchanged with T2 seed (verified live, §3; tested T1/T2); fences held (T5); no dispatcher (§2)
- [x] Tests T1–T6 · report (this document) · docs (README, PLATFORM/CONNECTIONS, PRIORIDAD) · package `0.6.11`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.11`** — pending, not claimed here
- [x] Prerequisite: T2 ★ ACCEPT + tag `v0.6.10` landed (confirmed, §6)

**No ACCEPT claim.**
