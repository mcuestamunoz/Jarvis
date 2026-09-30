# Implementation Report — Capability registry product fill (`B1-capability-registry-product-fill`, T2)

**Project:** Jarvis
**Date:** 2026-09-29
**Implementer:** Claude Code
**Contract:** [`implementation_contract_capability_registry_product_fill_b1.md`](implementation_contract_capability_registry_product_fill_b1.md)
**Design parent:** [`design_contract_capability_registry_product_fill_b0.md`](design_contract_capability_registry_product_fill_b0.md) — ★ ACCEPT CLOSED (ratified as drafted)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.10` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.10` is reserved for Engineer ACCEPT per IC §0 row 11 / §4.

---

## 1. Files changed

**New:**
- `tests/test_capability_registry_product_fill_b1.py` — T1–T7

**Modified (this Buy's own scope):**
- `src/jarvis/capabilities/schemas.py` — `CapabilityAvailability.AVAILABLE = "available"`, `ProviderKind.SOFTWARE = "software"`; module docstring rewritten
- `src/jarvis/capabilities/registry.py` — `load_default()` docstring rewritten (no longer "always empty"); module docstring rewritten
- `src/jarvis/capabilities/data/default_registry.json` — replaced with the IC §1 normative seed (two capabilities, two software providers, zero skills) verbatim
- `src/jarvis/capabilities/__init__.py` — top docstring paragraph updated (was "empty-by-default")
- `pyproject.toml` — `version = "0.6.9"` → `version = "0.6.10"`
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new T2 paragraph, placement line refreshed
- `docs/system_map/CONNECTIONS.md` — new chronology paragraph extending the existing Fase C `src/jarvis/capabilities/` isolation note — **no new `C-xxx`**, per IC §0 row 12's explicit preference
- `src/jarvis/intelligence/README.md` — both capability-string bullets (T0's `ontology.explain`, T1's `engineering.continuity`) updated to note they're now also named registry rows, with the "id-synced by test, not by import" fence restated
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + T2 cola row + COLA header updated to "delivered, awaiting review"

**Modified (regression fix — found while verifying, not in the IC's own file list, see §3):**
- `tests/test_fase_c_capability_registry_scaffold_b1.py` (C1) — IC-mandated adaptations (§3 below)
- `tests/test_fase_c_intent_safety_stub_b1.py` (C2) — same class of fix, found independently
- 39 `tests/test_fase_c_*.py` files (C6 onward) — each had its own copy of a now-false `registry.capabilities()/providers() == []` assertion bundled inside a larger structural-isolation test; fixed uniformly (see §3)
- `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_defer_continuity_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py` — their own stale `0.6.9` version-checkpoint tests bumped forward to `0.6.10`

**Not touched — confirmed zero diff (IC §0 row 8):**
- `src/jarvis/intelligence/assistant_task.py`
- `src/jarvis/core/orchestrator.py` (Task wire)
- `src/jarvis/core/project_continuity.py` (Continuity ranking)
- `ontology/` (only the pre-existing, unrelated `.obsidian/workspace.json` shows in the raw diff)

---

## 2. Seed content (IC §1) — verified against `load_default()`, not just the JSON

```text
$ python -c "from jarvis.capabilities import CapabilityRegistry; ..."
capabilities: [('ontology.explain', AVAILABLE, 'provider.ontology_explain'),
               ('engineering.continuity', AVAILABLE, 'provider.engineering_continuity')]
providers: [('provider.ontology_explain', SOFTWARE, ['ontology.explain']),
            ('provider.engineering_continuity', SOFTWARE, ['engineering.continuity'])]
skills: []
providers_offering ontology.explain: ['provider.ontology_explain']
providers_offering engineering.continuity: ['provider.engineering_continuity']
enum values: {'not_implemented', 'available', 'stub'}
provider kinds: {'vehicle', 'software', 'device'}
```

Byte-identical to the IC's own §1 JSON, loaded through the real `CapabilityRegistry.load_default()` → `from_dict()` → pydantic validation path (not just a JSON diff) before writing any test.

---

## 3. Regression found and fixed: the "registry stays empty" assumption was load-bearing in 41 files, not 2

The IC's own §3 named exactly one file for adaptation (`tests/test_fase_c_capability_registry_scaffold_b1.py`, C1). Running the C1 suite alone was clean, but running the **combined** suite surfaced a second file with the identical stale assumption — `tests/test_fase_c_intent_safety_stub_b1.py` (C2's own `test_t8_capability_registry_default_still_empty`) — which the IC's file list did not name. Running the **full** suite then surfaced the real scope: **39 additional Fase C test files** (C6 through the C35+/Taller-CSS closeout), each carrying its own copy of

```python
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
```

bundled inside a larger, otherwise-still-valid structural-isolation test (e.g. "no craft/core imports of this rung's module, and registry stays empty"). Every one of these was a real regression this Buy caused, not a pre-existing failure — none were part of the established version-checkpoint-drift pattern documented in every prior report in this series.

**Verification before fixing:** confirmed the exact 3-line block was byte-identical and appeared exactly once in each of the 39 files (scripted check, not assumed) before touching any of them.

**Fix applied uniformly:** replaced the two now-false lines with a comment explaining why, keeping the one still-true assertion (`skills() == []`):

```python
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py for that
    # shape. Skills stay empty; this file's own isolation proof is unaffected.
    assert registry.skills() == []
```

Nothing else in any of the 39 tests was touched — the surrounding "no craft/core imports" assertions in the same test functions are unchanged and still pass. `tests/test_fase_c_capability_registry_scaffold_b1.py` (C1) and `tests/test_fase_c_intent_safety_stub_b1.py` (C2) got individually-tailored fixes instead (see below), since their own tests were dedicated single-purpose registry checks, not bundled isolation proofs.

**C1 adaptations (IC §3, mandatory):**
- `test_t1_load_default_is_empty` → renamed `test_t1_load_default_returns_product_seed`; asserts `capabilities()`/`providers()` are non-empty, `skills() == []`. Full seed-shape assertions live in the new T2 test file, not duplicated here.
- `test_t8_availability_enum_rejects_available` → renamed `test_t8_availability_enum_accepts_available_still_rejects_ready`; `available` no longer raises, `ready` still does, enum set is `{stub, not_implemented, available}`.
- `test_default_seed_file_is_honestly_empty` → renamed `test_default_seed_file_is_honestly_software_only`; asserts no flight-prefixed/hold/land/go_to capability id and every provider `kind == "software"`.
- `test_t9_no_public_method_executes_or_dispatches`, `test_t9b_no_execute_or_dispatch_field_on_records` — left intact, unchanged, still pass.
- `test_t10_pyproject_version_is_0_5_0` → renamed `test_t10_pyproject_version_is_0_6_10`, bumped (was already checking `0.5.44` in its body despite the `0_5_0` name — a pre-existing naming/body mismatch from an earlier Buy, not introduced here, not otherwise touched).

**C2 adaptation (found independently, same treatment):**
- `test_t8_capability_registry_default_still_empty` → renamed `test_t8_capability_registry_default_still_descriptive_only`; keeps the still-true `skills() == []` assertion and the still-true "no dispatcher method" assertion, drops the two now-false ones.
- `test_t9_pyproject_version_stays_0_5_0` → renamed `test_t9_pyproject_version_stays_0_6_10`, bumped.

---

## 4. Tests

`tests/test_capability_registry_product_fill_b1.py` — 8 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | `load_default()` has exactly `{ontology.explain, engineering.continuity}`, both `AVAILABLE`; skills empty | PASS |
| T2 | Both providers exist, `kind == SOFTWARE`; `providers_offering` returns the correct provider for each capability | PASS |
| T3 | Seed capability ids equal `assistant_task.CAPABILITY_ONTOLOGY_EXPLAIN`/`CAPABILITY_ENGINEERING_CONTINUITY` exactly | PASS |
| T4 | Seed JSON has no `flight`-prefixed/`hold`/`land`/`go_to` capability id; no `vehicle`/`device` provider | PASS |
| T5 | `CapabilityAvailability` includes `available`; `ProviderKind` includes `software`; `"ready"` still rejected on `CapabilityRecord` | PASS |
| T6 | No public `CapabilityRegistry` method name contains execute/dispatch/command_esc/actuat/run_skill (same grain as C1 T9) | PASS |
| — | Import-graph check: `registry.py` doesn't import `jarvis.intelligence`; `assistant_task.py` doesn't import `jarvis.capabilities.registry`/bare `jarvis.capabilities` (T0/T1's classify stays authoritative, no registry lookup added) | PASS |
| T7 | `pyproject.toml` reads `version = "0.6.10"` | PASS |

```text
$ python -m pytest tests/test_capability_registry_product_fill_b1.py -v
...
8 passed in 0.07s
```

`tests/test_fase_c_capability_registry_scaffold_b1.py` (C1, now 15 tests) and `tests/test_fase_c_intent_safety_stub_b1.py` (C2) re-run: **all pass.** All 39 Fase C files touched for the registry-assumption fix re-run: **all pass**, combined with `test_capability_registry_product_fill_b1.py`, `test_assistant_explain_task_b1.py`, `test_assistant_defer_continuity_b1.py`, `test_chat_explain_intercept_b1.py`:

```text
$ python -m pytest tests/test_fase_c_capability_registry_scaffold_b1.py tests/test_capability_registry_product_fill_b1.py \
    tests/test_assistant_explain_task_b1.py tests/test_assistant_defer_continuity_b1.py \
    tests/test_chat_explain_intercept_b1.py tests/test_fase_c_intent_safety_stub_b1.py \
    tests/test_continuity_explain_topics_expand_b1.py -q
64 passed in 0.43s
```

---

## 5. Full suite

```text
$ python -m pytest -q
52 failed, 3786 passed, 9 skipped in 7.65s
```

Before this Buy (parent tip `v0.6.9`), the suite had 54 pre-existing version-pinned checkpoint failures. This Buy: fixed the 41-file registry-assumption regression (§3, net zero on the final count — these were failures this Buy itself introduced mid-implementation, caught and fixed before delivery, never part of the delivered state); bumped four Buys' own stale `0.6.9` checkpoints forward to `0.6.10`, plus C1's/C2's own long-stale `0.5.X` checkpoints, for a net **−2** on the pre-existing baseline (54 → 52). +8 new tests (the T2 file). Confirmed zero unexpected failures via `grep FAILED | grep -v <version-checkpoint pattern>` returning empty on the final delivered state.

---

## 6. Docs sync (IC §0 row 12) — every path touched

| Doc | Change |
|---|---|
| `src/jarvis/capabilities/schemas.py`, `registry.py`, `__init__.py` | Module docstrings rewritten to describe the new enum members and the non-empty seed, still emphasizing descriptive-only/no-dispatcher |
| `docs/PLATFORM_CAPABILITY_VISION.md` §13 | New T2 paragraph (scaffold ≠ empty forever; product seed is software-only); Placement line refreshed to include T0/T1/T2 status |
| `docs/system_map/CONNECTIONS.md` | New chronology paragraph extending the existing Fase C `capabilities/` isolation note — **no new `C-xxx`**, per IC's explicit preference |
| `src/jarvis/intelligence/README.md` | One-pointer update on both T0's and T1's capability-string bullets, noting they're now also registry rows (id-synced by test, not import) |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line, T2 cola row, COLA header — all updated to "delivered, awaiting review" |

All are pointer-level or small-section edits, no rewrite epics — same discipline as every prior report in this series.

---

## 7. Acceptance criteria (IC §4) — self-check

- [x] Schema enums extended; seed §1 loads via `load_default` (verified through the real load path, not just JSON diff)
- [x] Id sync with Assistant Task constants (T3)
- [x] No dispatcher / no flight available / T0–T1 code untouched (T6, confirmed zero diff on `assistant_task.py`/`orchestrator.py`/`project_continuity.py`)
- [x] Tests T1–T7 · C1 adapted (+ C2, found independently, + 39 Fase C files) · report · docs · package `0.6.10`
- [ ] Cursor review · Engineer ACCEPT · tag `v0.6.10` — **pending**, not claimed by Claude

---

## 8. DC locks honored (`design_contract_capability_registry_product_fill_b0.md`)

- Registry stays descriptive — no dispatcher, no Safety gate, no FS path; fulfill stays exactly where T0/T1 already put it.
- `available` restricted to the two non-actuation software capabilities named; no flight/vehicle/radio id marked `available`.
- `ProviderKind.SOFTWARE` added for in-process product providers only.
- `assistant_task.py` does not look up the registry before emitting a Task — Task-string classify stays authoritative on its own (confirmed by the import-graph check).
- Skills stay empty.
- No Conversation Engine, no Capability Registry UI, no Continuity ranking change.

**No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 9. Non-edits / git-state verification

```text
$ git diff --stat -- ontology/
 ontology/.obsidian/workspace.json | 47 ++++++++++++++++++++++-----------------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Zero diff on every actual vault note (pre-existing, unrelated Obsidian UI state — same as every prior report in this series).

```text
$ git diff --stat -- src/jarvis/intelligence/assistant_task.py src/jarvis/core/orchestrator.py src/jarvis/core/project_continuity.py
(no output — zero diff on all three)
```

```text
$ git tag -l | sort -V | tail -1
v0.6.9

$ grep -m1 '^version' pyproject.toml
version = "0.6.10"
```

Tag remains **`v0.6.9`** — package bumped to `0.6.10` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.10`.
