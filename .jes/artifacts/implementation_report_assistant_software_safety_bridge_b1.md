# Implementation Report — Assistant software Safety bridge (`B1-assistant-software-safety-bridge`, T4)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_software_safety_bridge_b1.md`](implementation_contract_assistant_software_safety_bridge_b1.md)
**Parents:** T3 `B1-assistant-task-registry-coherence` — ★ **ACCEPT CLOSED @ `v0.6.11`** (commit `04163d6`, tag `v0.6.11` present, landed mid-session — see §6); T2 registry seed ★ CLOSED @ `v0.6.10`; C2/C17/C41 Safety stack (`SafetyGate`/`SafetyRequest`/`default_safety_gate()` → RejectAll, `ArmedAllowlistSafetyGate`)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.12` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.12` is reserved for Engineer ACCEPT per IC §4/§6.

---

## 1. Files changed

**New:**
- `tests/test_assistant_software_safety_bridge_b1.py` — T1–T7

**Modified:**
- `src/jarvis/capabilities/safety.py` — added `from jarvis.capabilities.registry import CapabilityRegistry` and `from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind` (new intra-`capabilities/` edge; `safety.py` previously imported only `jarvis.capabilities.intent`); added `_parse_capability_action_id(action_id) -> list[str] | None` and `SoftwareCapabilitySafetyGate` (`gate_id="software_capability"`); module docstring extended with a T4 section
- `src/jarvis/capabilities/__init__.py` — exported `SoftwareCapabilitySafetyGate`
- `src/jarvis/intelligence/assistant_task.py` — added `from jarvis.capabilities.safety import SafetyRequest, SoftwareCapabilitySafetyGate`; added `_software_safety_allows(intent_id, capability_ids) -> bool`; wired it into both `try_explain_concept_task` and `try_defer_to_continuity_task`, immediately after the existing T3 membership check and immediately before the `task_kind` write; module docstring extended to mention T4
- `pyproject.toml` — `version = "0.6.11"` → `version = "0.6.12"`
- `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py` — their own stale version-checkpoint assertions bumped `0.6.11` → `0.6.12` (IC §3: "bump stale `0.6.11` checkpoints forward")
- `tests/test_assistant_task_registry_coherence_b1.py::test_gate_does_not_touch_availability_or_providers` — corrected (see §4 below): rescoped from watching the full `try_explain_concept_task`/`try_defer_to_continuity_task` call chain to watching T3's own `_capabilities_known_in_default_registry` helper directly, since T4 legitimately adds a second, downstream registry read (`get_provider`) that the old assertion could not distinguish from a T3 regression
- `src/jarvis/intelligence/README.md` — new "Software Safety bridge (T4)" section (placed above the T3 section, newest-first per existing convention); Buys/Package lines updated to `0.6.12`; T3 section's stale "no Safety gate" clause corrected to point at the new T4 section
- `docs/PLATFORM_CAPABILITY_VISION.md` — §12 Placement line: T3 corrected to ★ ACCEPT CLOSED @ `v0.6.11`, new T4 clause added; §10 ("Safety between Assistant and hardware") gained a short "First concrete instance (T4)" paragraph naming this Buy as the diagram's first real code, still with no `Flight Control`/`Actuators` step; §13 T3 entry corrected to ★ ACCEPT CLOSED, new T4 paragraph added with the requested one-liner shape
- `docs/system_map/CONNECTIONS.md` — **extended the existing T3 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.11`) and **added a new paragraph directly below it** for T4, naming the new `safety.py` → `registry.py`/`schemas.py` edge and cross-referencing this report. **No new `C-xxx`**, per IC §0 row 12.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T4 cola row updated from "★ AUTHORIZED · Claude" to "IMPLEMENTED · package `0.6.12`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link

**Not touched (verified — see §5):** `src/jarvis/core/orchestrator.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/data/default_registry.json`, `src/jarvis/capabilities/schemas.py` (only imported, not modified), `src/jarvis/capabilities/intent.py`, `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py`/`continuity_cite.py`, `config.py`, `ArmedAllowlistSafetyGate`'s class body, `default_safety_gate()`'s function body, `RejectAllSafetyGate`.

---

## 2. The gate itself (IC §0 rows 3–6, §1)

**`_parse_capability_action_id`:**

```python
def _parse_capability_action_id(action_id: str | None) -> list[str] | None:
    if action_id is None:
        return None
    prefix = "capability:"
    if not action_id.startswith(prefix):
        return None
    remainder = action_id[len(prefix):]
    if remainder == "":
        return []
    ids = remainder.split(",")
    if any(not capability_id for capability_id in ids):
        return None
    return ids
```

Returns `None` for anything that isn't `"capability:..."`-shaped at all (including a bare `None` `action_id`, or an unrelated shape like `"autonomy:HOLD:1"`), `[]` for the well-formed-but-empty `"capability:"` case (distinguished so the gate can raise its own `empty_capabilities` reason rather than the more generic `unparseable_action_id`), and a clean id list otherwise. A malformed list (empty segment from a stray/trailing comma) also returns `None`.

**`SoftwareCapabilitySafetyGate.evaluate`:**

```python
def evaluate(self, request: SafetyRequest) -> SafetyDecision:
    capability_ids = _parse_capability_action_id(request.action_id)
    if capability_ids is None:
        return SafetyDecision(outcome="reject", reason="unparseable_action_id", gate_id=self.gate_id)
    if not capability_ids:
        return SafetyDecision(outcome="reject", reason="empty_capabilities", gate_id=self.gate_id)

    registry = CapabilityRegistry.load_default()
    for capability_id in capability_ids:
        capability = registry.get_capability(capability_id)
        if capability is None:
            return SafetyDecision(outcome="reject", reason="capability_unknown", gate_id=self.gate_id)
        if capability.availability != CapabilityAvailability.AVAILABLE:
            return SafetyDecision(outcome="reject", reason="capability_unavailable", gate_id=self.gate_id)
        provider = registry.get_provider(capability.provider_id) if capability.provider_id is not None else None
        if provider is None or provider.kind != ProviderKind.SOFTWARE:
            return SafetyDecision(outcome="reject", reason="provider_not_software", gate_id=self.gate_id)
    return SafetyDecision(outcome="allow", gate_id=self.gate_id)
```

All five reasons from IC §0 row 5 are used and are individually distinguishable — verified live (§3) and by test T3.

**Assistant wire (both `try_*`, matching the IC's own sketch exactly):**

```python
required_capability_ids = [CAPABILITY_...]
task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
if not _capabilities_known_in_default_registry(required_capability_ids):   # T3
    return None
if not _software_safety_allows(intent.id, required_capability_ids):        # T4
    return None
intent.metadata["task_kind"] = ...
return task
```

`_software_safety_allows` builds `action_id = "capability:" + ",".join(capability_ids)`, constructs a `SafetyRequest(intent_id=intent_id, action_id=action_id)`, and returns `decision.outcome == "allow"`. T3's membership helper runs first and stays unchanged (IC's own guidance: "keep T3 helper then Safety, so refuse reasons stay distinguishable in tests") — `_capabilities_known_in_default_registry` still only calls `get_capability`, never `availability`/`get_provider`; the Safety gate is what adds those reads, one step later.

**On reject:** `intent.metadata` is never touched — matching the T3 refuse grain exactly (IC §0 row 8).

---

## 3. Manual verification (before writing tests)

**Gate alone**, live against the actual product seed and hand-built fixtures:

```text
capability:ontology.explain                          -> allow
capability:ontology.explain,engineering.continuity    -> allow
capability:unknown.thing                              -> reject capability_unknown
capability:                                            -> reject empty_capabilities
None                                                    -> reject unparseable_action_id
autonomy:HOLD:1                                         -> reject unparseable_action_id
capability:ontology.explain,                           -> reject unparseable_action_id
```

**`default_safety_gate()` / `ArmedAllowlistSafetyGate` untouched:**

```text
type(default_safety_gate()).__name__ == 'RejectAllSafetyGate'  -> True
ArmedAllowlistSafetyGate._ALLOWED_VERBS == {'GO_TO', 'LAND', 'HOLD'}
```

**Assistant wire, happy path** (T2 seed present):

```text
explain happy: Task(required_capability_ids=['ontology.explain'])
  metadata: {'task_kind': 'explain_concept', 'explain_query': 'c-rate'}
defer happy:   Task(required_capability_ids=['engineering.continuity'])
  metadata: {'task_kind': 'defer_to_continuity'}
```

**Assistant wire, T3-level refuse** (registry empty — caught by T3's own membership check before T4 even runs):

```text
explain refuse (empty registry): None   metadata: {}
```

**Assistant wire, T4-specific refuse** (id present so T3 passes, but `availability=stub` or `provider.kind=vehicle` — proves T4 is doing genuinely different work from T3, not duplicating it):

```text
explain refuse (stub availability): None   metadata: {}
explain refuse (vehicle provider):  None   metadata: {}
```

All re-run a second time after T3 landed and tagged `v0.6.11` mid-session (see §6) to confirm nothing shifted under the new HEAD — identical results both times.

---

## 4. Correcting a T3 test (not a weakening)

T3's own `test_gate_does_not_touch_availability_or_providers` watched every registry call made during a full `try_explain_concept_task`/`try_defer_to_continuity_task` invocation and asserted the recorded sequence was exactly `["get_capability", "get_capability"]` — true at T3 time, when the only registry-touching code in either function was T3's own membership helper. T4 legitimately adds a second, downstream call inside the same functions (`_software_safety_allows` → `SoftwareCapabilitySafetyGate.evaluate` → `registry.get_provider(...)`), which is the entire point of this Buy. Run unmodified against the new code, that test failed with an honest, expected diff (`get_provider` appearing in the recorded call list) — not a bug in the gate, but a T3-era test whose scope implicitly assumed no later Buy would add anything downstream.

I corrected the test rather than deleting or loosening its assertion: it now calls `_capabilities_known_in_default_registry` directly (T3's own helper, unchanged) instead of the full `try_*` functions, so it still proves exactly what it originally set out to prove — that specific helper is membership-only — without being coupled to whatever a later, separately-authorized Buy adds after it. The docstring was rewritten to explain the rescoping and point at this Buy's own test file for the Safety gate's own registry-read coverage. Verified passing after the fix (`tests/test_assistant_task_registry_coherence_b1.py -q` → `7 passed`).

---

## 5. Tests

`tests/test_assistant_software_safety_bridge_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | With product seed: explain Intent → Task (allow); `estado` → Task (allow) | PASS |
| T2 | Gate alone: `action_id="capability:ontology.explain"` (and a multi-id variant) → `allow`, `gate_id="software_capability"` | PASS |
| T3 | Gate alone: unknown id → `capability_unknown`; stub availability → `capability_unavailable`; vehicle-kind provider → `provider_not_software`; empty/`None`/malformed `action_id` → `empty_capabilities`/`unparseable_action_id` | PASS |
| T4 | Monkeypatched empty registry → both `try_*` → `None`, no `task_kind` (extra T4b: id present but stub availability → still `None`, proving T4 ≠ T3) | PASS |
| T5 | `default_safety_gate()` still `RejectAllSafetyGate` (still rejects, reason `not_implemented`); `ArmedAllowlistSafetyGate` allow-list still exactly `{HOLD, LAND, GO_TO}`, still starts disarmed | PASS |
| T6 | AST: `assistant_task.py` imports `jarvis.capabilities.safety`; no `core`/`flight_software`/`vehicle_profiles`; `safety.py` does not import `jarvis.intelligence` | PASS |
| T7 | `pyproject.toml` reads `0.6.12` | PASS |

```text
$ python3 -m pytest tests/test_assistant_software_safety_bridge_b1.py -v
8 passed
```

Regression — T0/T1/T2/T3/C2/C17/C41 suites plus the new T4 suite together:

```text
$ python3 -m pytest tests/test_assistant_software_safety_bridge_b1.py \
    tests/test_assistant_task_registry_coherence_b1.py \
    tests/test_assistant_explain_task_b1.py \
    tests/test_assistant_defer_continuity_b1.py \
    tests/test_capability_registry_product_fill_b1.py \
    tests/test_fase_c_capability_registry_scaffold_b1.py \
    tests/test_fase_c_intent_safety_stub_b1.py \
    tests/test_fase_c_safety_real_policy_b1.py \
    tests/test_fase_c_safety_sim_policy_b1.py -q
86 passed, 2 failed
```

The 2 failures are pre-existing, out-of-scope stale version-checkpoints (`0.5.15`/`0.5.42`, predating `0.6.x` entirely) — not touched by this IC's "bump stale `0.6.11` checkpoints" instruction, same accepted-drift pattern as every prior Buy.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3801 passed, 9 skipped
```

All 52 failures are the same pre-existing stale version-checkpoint set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3801 passed is +8 over the T3 baseline (3793), exactly the new T4 test file's count. No non-version failures anywhere, no test touching `assistant_task.py`, `safety.py`, or the registry fails.

---

## 6. Git-state note: T3 landed mid-session (same pattern as T2 did during the T3 turn)

At authorization time, T3 was Cursor-reviewed and the IC referenced `v0.6.11` as its target tag but `git log`/`git tag` had not yet shown it landed. Partway through this Buy's implementation, `git log` showed two new commits — `04163d6 Close Assistant T3 registry-coherence and open software Safety IC.` and `6a2d597 Fix T3 IC parents header and PRIORIDAD after ACCEPT stamp.` — and `git tag -l` gained `v0.6.11`. `docs/IMPLEMENTATION_TASKS.md` had also already been updated by the Engineer/Cursor side to show T3 as `✅ ★ ACCEPT CLOSED · tip v0.6.11` and T4 as `★ AUTHORIZED · Claude` before I got to my own docs-sync pass — I built on top of that state rather than overwriting it (see §1). `.jes/state/engineering_state.json` and this IC's own file also show independent edits from that same side, unrelated to my work — untouched by me, left as-is. All manual verification and the suite runs in §3/§5 were re-run against the final HEAD to confirm nothing shifted; results were identical both times. No repeat of the transient edit-persistence issue from the T3 turn occurred this time — every edit in this Buy was verified via `grep`/`git diff --stat` immediately after applying, per the practice established then.

---

## 7. IC acceptance checklist self-check

- [x] `SoftwareCapabilitySafetyGate` shipped; Assistant wires it for both Task kinds
- [x] Happy path UX unchanged with T2 seed (verified live, §3; tested T1) · refuse on unknown/unavailable (tested T3/T4/T4b)
- [x] `default_safety_gate`/`ArmedAllowlistSafetyGate`/FS paths untouched (verified live, §3; tested T5; `git diff` confirms zero change to either class body or the factory function)
- [x] Tests T1–T7 · report (this document) · docs (README, PLATFORM §10/§12–13, CONNECTIONS, PRIORIDAD) · package `0.6.12`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.12`** — pending, not claimed here

**No ACCEPT claim.**
