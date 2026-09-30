"""Assistant Task seam — `B1-assistant-explain-task` (T0), extended by
`B1-assistant-defer-continuity` (T1),
`B1-assistant-task-registry-coherence` (T3),
`B1-assistant-software-safety-bridge` (T4),
`B1-assistant-vehicle-hold-task` (T6),
`B1-assistant-vehicle-land-task` (T7),
`B1-assistant-vehicle-go-to-task` (T8),
`B1-assistant-vehicle-takeoff-task` (T9),
`B1-assistant-vehicle-return-home-task` (T10),
`B1-assistant-vehicle-arm-ux` (T11), and
`B1-assistant-vehicle-follow-task` (T12).

T11 adds Safety **policy** Tasks `request_arm_policy` /
`request_disarm_policy` (require `safety.chat_armed_allowlist`,
`available`+`software`) — classified from `VEHICLE_ARM_PHRASES` /
`VEHICLE_DISARM_PHRASES`, through the T4 `SoftwareCapabilitySafetyGate`
path (unlike vehicle verbs). Precedence: explain → Continuity defer →
ARM → DISARM → HOLD → … → RETURN_HOME → FOLLOW. Fulfill (gate.arm/disarm
on the orchestrator's shared chat ArmedAllowlist) lives entirely in
`core/orchestrator.py` — this module still never imports
`jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`.

T12 adds the **sixth** vehicle Task kind, `request_follow` (requires
`flight.follow`) — same membership-only seam as HOLD…RETURN_HOME, own
finite phrase table (`jarvis.config.VEHICLE_FOLLOW_PHRASES`). Precedence:
explain → Continuity defer → ARM → DISARM → HOLD → LAND → GO_TO →
TAKEOFF → RETURN_HOME → **FOLLOW** → fallthrough. No person/target parse
— orchestrator always proposes with empty `params={}`. Allow-list stays
`{HOLD, LAND, GO_TO}` (unwidened) — after ARM, FOLLOW yields
`verb_not_allowed` like TAKEOFF/RETURN_HOME.

T6 adds the first **vehicle** Task kind, `request_hold` (requires
`flight.hold`) — classified from a finite HOLD phrase table
(`jarvis.config.VEHICLE_HOLD_PHRASES`), same membership-only T3 gate as
every other kind, but deliberately **no** `SoftwareCapabilitySafetyGate`
call (T4's gate only ever allows an `available`+`software`-provided
capability; `flight.hold` is intentionally `not_implemented`+`vehicle`,
so that gate would always and correctly refuse it — the real Safety
check for this kind lives entirely in the orchestrator's fulfill step,
via `flight_software.autonomy.submit_command` + the process-scoped chat
`ArmedAllowlistSafetyGate` owned by the orchestrator since T11, not in
this module). This module still never imports
`jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`.

T7 adds the **second** vehicle Task kind, `request_land` (requires
`flight.land`) — same seam as T6, own finite phrase table
(`jarvis.config.VEHICLE_LAND_PHRASES`), same membership-only gate, same
deliberate absence of `SoftwareCapabilitySafetyGate`. Precedence: explain
→ Continuity defer → HOLD → LAND → fallthrough — `try_request_land_task`
refuses explain-, Continuity-, *and* HOLD-shaped input internally (a
direct caller cannot steal HOLD's own phrases), mirroring the same
internal-guard discipline every earlier kind here already uses.

T8 adds the **third** vehicle Task kind, `request_go_to` (requires
`flight.go_to`) — same seam again, own finite phrase table
(`jarvis.config.VEHICLE_GO_TO_PHRASES`). Precedence: explain →
Continuity defer → HOLD → LAND → GO_TO → fallthrough —
`try_request_go_to_task` refuses explain-, Continuity-, HOLD-, *and*
LAND-shaped input internally. No coordinate/waypoint parsing this Buy —
the orchestrator's own fulfill always proposes with empty `params={}`.

T9 adds the **fourth** vehicle Task kind, `request_takeoff` (requires
`flight.takeoff`) — same seam again, own finite phrase table
(`jarvis.config.VEHICLE_TAKEOFF_PHRASES`). Precedence: explain →
Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → fallthrough —
`try_request_takeoff_task` refuses explain-, Continuity-, HOLD-, LAND-,
*and* GO_TO-shaped input internally. No altitude parsing this Buy —
`params` is always empty, same as GO_TO. Note: `ArmedAllowlistSafetyGate`'s
own allow-list is still only `{HOLD, LAND, GO_TO}` (unwidened by this
Buy — DC §0 row 7) — the product chat path never arms anyway, so this
doesn't change TAKEOFF's honest `disarmed` reject, but an armed caller
would still get `verb_not_allowed` for TAKEOFF specifically until a
later, separate allow-list Buy.

T10 adds the **fifth and closing** vehicle Task kind of the basic
command set, `request_return_home` (requires `flight.return_home`) —
same seam again, own finite phrase table
(`jarvis.config.VEHICLE_RETURN_HOME_PHRASES`). Precedence: explain →
Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME →
fallthrough — `try_request_return_home_task` refuses explain-,
Continuity-, HOLD-, LAND-, GO_TO-, *and* TAKEOFF-shaped input
internally. No home-point/GPS parsing this Buy — `params` is always
empty. `VEHICLE_RETURN_HOME_PHRASES` includes several short single
words (`casa`, `home`, `volver`, `vuelve`) — exact-match only, same
discipline as every table here, so a longer craft-chat line merely
*containing* one of those words (e.g. "volver al board") is never
stolen. `ArmedAllowlistSafetyGate`'s own allow-list stays unwidened
(still `{HOLD, LAND, GO_TO}`, RETURN_HOME not included) — same honest-
`disarmed`-regardless reasoning as TAKEOFF. After this kind, the basic
chat vehicle command set is complete: TAKEOFF/HOLD/GO_TO/RETURN_HOME/LAND.

First on-disk `Task` emission per `DC-assistant-first-task`
(`design_contract_assistant_first_task_b0.md`, ★ ACCEPT CLOSED):
`jarvis.intelligence` — the Assistant — classifies an `Intent` into a
`Task` (or refuses honestly), never a second task brain living in the
orchestrator. Reuses `jarvis.capabilities.intent.Task` as-is; no forked
Task type. Two kinds ship here:

- `explain_concept` (T0) — requires `ontology.explain`, fulfilled by
  A3's existing read-only cite path (`jarvis.intelligence.explain`).
- `defer_to_continuity` (T1, `design_contract_assistant_defer_continuity_b0.md`
  ★ ACCEPT CLOSED) — requires `engineering.continuity`, classified from
  a finite, explicit phrase table (`jarvis.config.CONTINUITY_DEFER_PHRASES`,
  a hand-synced copy of `IntentResolver.STATUS_PATTERNS`) and fulfilled
  entirely by `core/`'s existing `_handle_project_status()`. This module
  never formats a Continuity body itself and never imports
  `jarvis.core.intent_resolver`/`jarvis.core.project_continuity` — only
  the finite phrase *strings* are copied into `jarvis.config`, not the
  resolver class. An explain-shaped line always wins over a Continuity-
  shaped one (checked in both directions: the orchestrator's own call
  order, and `try_defer_to_continuity_task`'s own internal guard).

No LLM call anywhere in this module. No Continuity ranking read, no
`jarvis.core` import. See `tests/test_assistant_explain_task_b1.py` T6
and `tests/test_assistant_defer_continuity_b1.py` T6 for the
AST-enforced fence (also: no `jarvis.flight_software` /
`jarvis.vehicle_profiles`).
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from jarvis.capabilities.intent import Intent, Task
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import SafetyRequest, SoftwareCapabilitySafetyGate
from jarvis.config import (
    CHAT_EXPLAIN_PREFIXES,
    CONTINUITY_DEFER_PHRASES,
    VEHICLE_ARM_PHRASES,
    VEHICLE_DISARM_PHRASES,
    VEHICLE_FOLLOW_PHRASES,
    VEHICLE_GO_TO_PHRASES,
    VEHICLE_HOLD_PHRASES,
    VEHICLE_LAND_PHRASES,
    VEHICLE_RETURN_HOME_PHRASES,
    VEHICLE_TAKEOFF_PHRASES,
)

CAPABILITY_ONTOLOGY_EXPLAIN = "ontology.explain"
TASK_KIND_EXPLAIN_CONCEPT = "explain_concept"
CAPABILITY_ENGINEERING_CONTINUITY = "engineering.continuity"
TASK_KIND_DEFER_TO_CONTINUITY = "defer_to_continuity"
CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST = "safety.chat_armed_allowlist"
TASK_KIND_REQUEST_ARM_POLICY = "request_arm_policy"
TASK_KIND_REQUEST_DISARM_POLICY = "request_disarm_policy"
CAPABILITY_FLIGHT_HOLD = "flight.hold"
TASK_KIND_REQUEST_HOLD = "request_hold"
CAPABILITY_FLIGHT_LAND = "flight.land"
TASK_KIND_REQUEST_LAND = "request_land"
CAPABILITY_FLIGHT_GO_TO = "flight.go_to"
TASK_KIND_REQUEST_GO_TO = "request_go_to"
CAPABILITY_FLIGHT_TAKEOFF = "flight.takeoff"
TASK_KIND_REQUEST_TAKEOFF = "request_takeoff"
CAPABILITY_FLIGHT_RETURN_HOME = "flight.return_home"
TASK_KIND_REQUEST_RETURN_HOME = "request_return_home"
CAPABILITY_FLIGHT_FOLLOW = "flight.follow"
TASK_KIND_REQUEST_FOLLOW = "request_follow"

_LIST_RUNG_REDIRECT = (
    "Eso solo está disponible en terminal: "
    "`jarvis explain --list` / `jarvis explain --rung <KEY>` "
    "no funcionan dentro del chat todavía."
)


def _capabilities_known_in_default_registry(capability_ids: list[str]) -> bool:
    """T3 soft coherence gate: membership only — never reads
    `availability`, never calls a provider. Loads the product default
    registry fresh each call (no caching, no alternate seed injection)."""
    registry = CapabilityRegistry.load_default()
    return all(registry.get_capability(cid) is not None for cid in capability_ids)


def _software_safety_allows(intent_id: str, capability_ids: list[str]) -> bool:
    """T4 — the first Safety link for a software Task, run *after* T3's
    membership check passes so refuse reasons stay distinguishable in
    tests (a T3 miss is `capability_unknown` territory the membership
    helper already caught cheaply; this call covers `availability`/
    provider-kind, which `_capabilities_known_in_default_registry`
    deliberately never reads). Constructs `SoftwareCapabilitySafetyGate`
    explicitly — `default_safety_gate()` (still always `RejectAllSafetyGate`)
    is never touched by this seam."""
    action_id = "capability:" + ",".join(capability_ids)
    request = SafetyRequest(intent_id=intent_id, action_id=action_id)
    decision = SoftwareCapabilitySafetyGate().evaluate(request)
    return decision.outcome == "allow"


def _extract_explain_query(raw_text: str) -> str | None:
    """Same A7 grain, same table: exact `jarvis explain `/`explain `
    prefix (casefold, required trailing space) from
    `jarvis.config.CHAT_EXPLAIN_PREFIXES` — a single shared prefix
    table, not a second copy. Returns the stripped remainder, or `None`
    when `raw_text` isn't explain-shaped at all (never a bare-id or
    craft-phrase steal)."""
    stripped = raw_text.strip()
    normalized = stripped.lower()
    for prefix in CHAT_EXPLAIN_PREFIXES:
        if normalized.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _is_list_or_rung_flag(query: str) -> bool:
    return query.startswith("--list") or query.startswith("--rung")


def try_explain_concept_task(intent: Intent) -> Task | None:
    """Classify `intent` as an `explain_concept` Task, or refuse
    (`None`) for anything not explain-shaped — including a
    `--list`/`--rung` flag-only line, which is explain-shaped but
    deliberately does **not** get a Task (IC §0 row 6: no fake
    `ontology.explain` capability claim for a line nothing is actually
    explaining; the caller still handles it honestly via
    `fulfill_ontology_explain`/`handle_explain_intent`).

    Never calls an LLM, never reads Continuity ranking, never reads
    `ontology/` itself — resolving the query is the provider's job
    (`fulfill_ontology_explain`), not this classifier's.

    Side effect: on a real match, records `task_kind`/`explain_query`
    onto `intent.metadata` in place (IC §0 row 4) — the only state this
    function touches, and only the caller's own `Intent` object.

    T3: before writing `intent.metadata`, soft-checks every id in
    `required_capability_ids` exists in `CapabilityRegistry.load_default()`
    (membership only — no availability read, no provider call). Unknown
    id → refuse (`None`), `intent.metadata` left untouched.

    T4: after the T3 membership check passes, also requires
    `SoftwareCapabilitySafetyGate` to `allow` the same capability ids
    (`availability == available` and a `software`-kind bound provider).
    A reject → refuse (`None`), same untouched-metadata grain as T3.
    """
    query = _extract_explain_query(intent.raw_text)
    if query is None or _is_list_or_rung_flag(query):
        return None
    required_capability_ids = [CAPABILITY_ONTOLOGY_EXPLAIN]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    if not _software_safety_allows(intent.id, required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_EXPLAIN_CONCEPT
    intent.metadata["explain_query"] = query
    return task


def fulfill_ontology_explain(query: str, *, ontology_root: Path | None = None) -> str:
    """Provider for `ontology.explain`. A `--list`/`--rung` query gets
    the same honest terminal-redirect A7 already used. A resolved query
    returns the full A3 cite text (`format_explain_cite`); an
    unresolved one returns the same honest-miss wording
    `run_explain_cli`'s own stderr already uses — never a raise, never
    an invented note."""
    if _is_list_or_rung_flag(query):
        return _LIST_RUNG_REDIRECT

    from jarvis.intelligence.explain import format_explain_cite, resolve_explain_query

    cite = resolve_explain_query(query, ontology_root=ontology_root)
    if cite is None:
        return (
            f"No solid ontology note for: {query}"
            " (hint: use the note's id, its exact nombre, or a known alias"
            " such as 'c-rate')"
        )
    return format_explain_cite(cite)


def handle_explain_intent(intent: Intent, *, ontology_root: Path | None = None) -> str | None:
    """`try_explain_concept_task` + fulfill in one call — the seam the
    orchestrator's chat-explain branch calls so it never duplicates the
    resolve logic as a parallel primary brain (IC §0 row 7). Returns
    `None` when `intent.raw_text` isn't explain-shaped at all (caller
    falls through to its normal LLM/craft path unchanged). Otherwise
    always returns a message string — including for `--list`/`--rung`
    lines, which are handled here (honest redirect) without a Task ever
    being emitted for them."""
    query = _extract_explain_query(intent.raw_text)
    if query is None:
        return None
    try_explain_concept_task(intent)
    return fulfill_ontology_explain(query, ontology_root=ontology_root)


def _normalize_for_continuity_match(text: str) -> str:
    """Minimal normalize equivalent to `IntentResolver._normalize_text`'s
    accent-stripping (strip + casefold + NFKD accent-strip) — reimplemented
    locally with only the stdlib, never imported from `jarvis.core.
    intent_resolver` (T1 DC/IC fence: this module must not import that
    module or `jarvis.core.project_continuity`)."""
    lowered = text.strip().lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def try_defer_to_continuity_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `defer_to_continuity` Task, or refuse
    (`None`) when `intent.raw_text` — after a minimal normalize — isn't
    an exact member of `CONTINUITY_DEFER_PHRASES`, **or** when it's
    explain-shaped (explain always wins; a line is never double-tasked).

    Exact-phrase match, deliberately narrower than `IntentResolver`'s
    own word-boundary substring search over a whole sentence (DC §0 row
    6: "no stealing arbitrary craft design chat into this Task") — a
    phrase that doesn't match exactly here still reaches the existing,
    unaffected Continuity/status path through the normal
    `_handle_user_text_inner` chain; this only adds an earlier,
    zero-LLM fast path for a strict subset, it narrows nothing that
    already worked.

    Never calls an LLM, never imports Continuity ranking modules, never
    decides what the fulfilled response looks like — that is entirely
    `core/`'s existing `_handle_project_status()` (DC §0 row 5/§2).

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3: before writing `intent.metadata`, soft-checks every id in
    `required_capability_ids` exists in `CapabilityRegistry.load_default()`
    (membership only — no availability read, no provider call). Unknown
    id → refuse (`None`), `intent.metadata` left untouched.

    T4: after the T3 membership check passes, also requires
    `SoftwareCapabilitySafetyGate` to `allow` the same capability ids
    (`availability == available` and a `software`-kind bound provider).
    A reject → refuse (`None`), same untouched-metadata grain as T3.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized not in CONTINUITY_DEFER_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_ENGINEERING_CONTINUITY]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    if not _software_safety_allows(intent.id, required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_DEFER_TO_CONTINUITY
    return task


def try_request_arm_policy_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_arm_policy` Task (T11) — Safety
    policy latch, **not** an AutonomyVerb — or refuse (`None`).

    Exact match on `VEHICLE_ARM_PHRASES` after normalize. Precedence:
    explain → Continuity defer → **ARM** → DISARM → HOLD → … . Refuses
    explain-, Continuity-, DISARM-, and all five vehicle-shaped inputs.
    Uses T3 membership **and** T4 `SoftwareCapabilitySafetyGate`
    (`safety.chat_armed_allowlist` is `available`+`software`). Never
    imports FS; fulfill (`gate.arm()`) is orchestrator-only.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_GO_TO_PHRASES:
        return None
    if normalized in VEHICLE_TAKEOFF_PHRASES:
        return None
    if normalized in VEHICLE_RETURN_HOME_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_ARM_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    if not _software_safety_allows(intent.id, required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_ARM_POLICY
    return task


def try_request_disarm_policy_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_disarm_policy` Task (T11) — pair
    of `try_request_arm_policy_task`. Exact match on
    `VEHICLE_DISARM_PHRASES`. Refuses explain / Continuity / ARM / five
    vehicle shapes. T3 + T4 software Safety path.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_GO_TO_PHRASES:
        return None
    if normalized in VEHICLE_TAKEOFF_PHRASES:
        return None
    if normalized in VEHICLE_RETURN_HOME_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_DISARM_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    if not _software_safety_allows(intent.id, required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_DISARM_POLICY
    return task


def try_request_hold_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_hold` Task — the first **vehicle**
    Task kind (`DC-assistant-vehicle-hold-task`, ★ CLOSED) — or refuse
    (`None`) when `intent.raw_text` — after the same minimal normalize
    used for Continuity-defer — isn't an exact member of
    `jarvis.config.VEHICLE_HOLD_PHRASES`, **or** when it's explain-shaped
    or Continuity-defer-shaped (precedence: explain → Continuity defer →
    HOLD → fallthrough; DC §0 row 4). This function re-checks both
    ahead-of-it kinds itself — mirroring `try_defer_to_continuity_task`'s
    own internal explain guard — so a direct/test caller gets the same
    precedence without depending on the orchestrator's own call order.

    Exact-phrase match only, same finite-table discipline as every other
    kind here — no fuzzy match, no stealing arbitrary craft design chat.

    Never calls an LLM, never imports `jarvis.flight_software` or
    `jarvis.vehicle_profiles`, never proposes or submits an autonomy
    command itself — fulfilling a matched Task (via `propose_command`/
    `submit_command` + a disarmed `ArmedAllowlistSafetyGate`) is
    entirely the orchestrator's job (DC §0 row 8), same separation T1
    already established for Continuity's own fulfill.

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3-style membership check: before writing `intent.metadata`,
    soft-checks `CAPABILITY_FLIGHT_HOLD` exists in
    `CapabilityRegistry.load_default()` (membership only). Unknown id →
    refuse (`None`), `intent.metadata` left untouched.

    Deliberately **no** T4 `SoftwareCapabilitySafetyGate` call here (IC
    §0 row 6) — that gate only ever `allow`s an `available`, `software`-
    provided capability; `flight.hold` is intentionally seeded
    `not_implemented`/`vehicle`, so calling it here would either always
    (and confusingly) refuse via the wrong gate, or — if the seed ever
    changed — silently imply a software fulfill path for a vehicle verb.
    The real Safety check for this kind happens once, in the
    orchestrator's fulfill step, via the autonomy surface's own
    `submit_command(...)` — not duplicated or pre-empted here.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_HOLD_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_HOLD]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_HOLD
    return task


def try_request_land_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_land` Task — the **second**
    vehicle Task kind (`DC-assistant-vehicle-land-task`, ★ CLOSED,
    same seam as T6's HOLD) — or refuse (`None`) when `intent.raw_text`
    — after the same minimal normalize — isn't an exact member of
    `jarvis.config.VEHICLE_LAND_PHRASES`, **or** when it's explain-shaped,
    Continuity-defer-shaped, **or** HOLD-shaped (precedence: explain →
    Continuity defer → HOLD → LAND → fallthrough; DC §0 row 4). This
    function re-checks all three ahead-of-it kinds itself — mirroring
    `try_request_hold_task`'s own internal explain/Continuity guards —
    so a direct/test caller (not just the orchestrator's own call order)
    cannot have a HOLD phrase stolen by LAND or vice versa.

    Exact-phrase match only, same finite-table discipline as every other
    kind here — no fuzzy match, no stealing arbitrary craft design chat.

    Never calls an LLM, never imports `jarvis.flight_software` or
    `jarvis.vehicle_profiles`, never proposes or submits an autonomy
    command itself — fulfilling a matched Task (via `propose_command`/
    `submit_command` + a disarmed `ArmedAllowlistSafetyGate`) is
    entirely the orchestrator's job (DC §0 row 8), same separation T6
    already established for HOLD's own fulfill.

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3-style membership check: before writing `intent.metadata`,
    soft-checks `CAPABILITY_FLIGHT_LAND` exists in
    `CapabilityRegistry.load_default()` (membership only). Unknown id →
    refuse (`None`), `intent.metadata` left untouched.

    Deliberately **no** T4 `SoftwareCapabilitySafetyGate` call here
    (IC §0 row 6), same reasoning as HOLD's own `try_request_hold_task`:
    `flight.land` is intentionally seeded `not_implemented`/`vehicle`,
    so that gate would either always (and confusingly) refuse via the
    wrong gate, or silently imply a software fulfill path for a vehicle
    verb if the seed ever changed. The real Safety check happens once,
    in the orchestrator's fulfill step.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_LAND_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_LAND]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_LAND
    return task


def try_request_go_to_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_go_to` Task — the **third**
    vehicle Task kind (`DC-assistant-vehicle-go-to-task`, ★ CLOSED,
    same seam as T6's HOLD/T7's LAND) — or refuse (`None`) when
    `intent.raw_text` — after the same minimal normalize — isn't an
    exact member of `jarvis.config.VEHICLE_GO_TO_PHRASES`, **or** when
    it's explain-shaped, Continuity-defer-shaped, HOLD-shaped, **or**
    LAND-shaped (precedence: explain → Continuity defer → HOLD → LAND →
    GO_TO → fallthrough; DC §0 row 4). This function re-checks all four
    ahead-of-it kinds itself — mirroring `try_request_land_task`'s own
    internal guards — so a direct/test caller (not just the
    orchestrator's own call order) cannot have a HOLD or LAND phrase
    stolen by GO_TO or vice versa.

    Exact-phrase match only, same finite-table discipline as every other
    kind here — no fuzzy match, no stealing arbitrary craft design chat.

    Never calls an LLM, never imports `jarvis.flight_software` or
    `jarvis.vehicle_profiles`, never proposes or submits an autonomy
    command itself — fulfilling a matched Task (via `propose_command`/
    `submit_command` + a disarmed `ArmedAllowlistSafetyGate`) is
    entirely the orchestrator's job (DC §0 row 8), same separation T6/T7
    already established. No coordinate/waypoint parsing happens here or
    in the orchestrator this Buy — `params` is always empty (DC §0 row 9).

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3-style membership check: before writing `intent.metadata`,
    soft-checks `CAPABILITY_FLIGHT_GO_TO` exists in
    `CapabilityRegistry.load_default()` (membership only). Unknown id →
    refuse (`None`), `intent.metadata` left untouched.

    Deliberately **no** T4 `SoftwareCapabilitySafetyGate` call here
    (IC §0 row 6), same reasoning as HOLD/LAND: `flight.go_to` is
    intentionally seeded `not_implemented`/`vehicle`, so that gate would
    either always (and confusingly) refuse via the wrong gate, or
    silently imply a software fulfill path for a vehicle verb if the
    seed ever changed. The real Safety check happens once, in the
    orchestrator's fulfill step.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_GO_TO_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_GO_TO]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_GO_TO
    return task


def try_request_takeoff_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_takeoff` Task — the **fourth**
    vehicle Task kind (`DC-assistant-vehicle-takeoff-task`, ★ CLOSED,
    same seam as T6's HOLD/T7's LAND/T8's GO_TO) — or refuse (`None`)
    when `intent.raw_text` — after the same minimal normalize — isn't an
    exact member of `jarvis.config.VEHICLE_TAKEOFF_PHRASES`, **or** when
    it's explain-shaped, Continuity-defer-shaped, HOLD-shaped, LAND-
    shaped, **or** GO_TO-shaped (precedence: explain → Continuity defer
    → HOLD → LAND → GO_TO → TAKEOFF → fallthrough; DC §0 row 4). This
    function re-checks all five ahead-of-it kinds itself — mirroring
    `try_request_go_to_task`'s own internal guards — so a direct/test
    caller (not just the orchestrator's own call order) cannot have a
    HOLD/LAND/GO_TO phrase stolen by TAKEOFF or vice versa.

    Exact-phrase match only, same finite-table discipline as every other
    kind here — no fuzzy match, no stealing arbitrary craft design chat.

    Never calls an LLM, never imports `jarvis.flight_software` or
    `jarvis.vehicle_profiles`, never proposes or submits an autonomy
    command itself — fulfilling a matched Task (via `propose_command`/
    `submit_command` + a disarmed `ArmedAllowlistSafetyGate`) is
    entirely the orchestrator's job (DC §0 row 8), same separation
    T6/T7/T8 already established. No altitude parsing happens here or
    in the orchestrator this Buy — `params` is always empty (DC §0 row 9).

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3-style membership check: before writing `intent.metadata`,
    soft-checks `CAPABILITY_FLIGHT_TAKEOFF` exists in
    `CapabilityRegistry.load_default()` (membership only). Unknown id →
    refuse (`None`), `intent.metadata` left untouched.

    Deliberately **no** T4 `SoftwareCapabilitySafetyGate` call here
    (IC §0 row 6), same reasoning as HOLD/LAND/GO_TO: `flight.takeoff`
    is intentionally seeded `not_implemented`/`vehicle`, so that gate
    would either always (and confusingly) refuse via the wrong gate, or
    silently imply a software fulfill path for a vehicle verb if the
    seed ever changed. The real Safety check happens once, in the
    orchestrator's fulfill step — where a disarmed gate yields
    `"disarmed"` regardless of whether TAKEOFF is even on
    `ArmedAllowlistSafetyGate`'s own allow-list (DC §0 row 7 note: it
    still isn't, this Buy).
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_GO_TO_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_TAKEOFF_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_TAKEOFF]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_TAKEOFF
    return task


def try_request_return_home_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_return_home` Task — the **fifth
    and closing** vehicle Task kind of the basic command set
    (`DC-assistant-vehicle-return-home-task`, ★ CLOSED, same seam as
    T6's HOLD/T7's LAND/T8's GO_TO/T9's TAKEOFF) — or refuse (`None`)
    when `intent.raw_text` — after the same minimal normalize — isn't
    an exact member of `jarvis.config.VEHICLE_RETURN_HOME_PHRASES`,
    **or** when it's explain-shaped, Continuity-defer-shaped, HOLD-
    shaped, LAND-shaped, GO_TO-shaped, **or** TAKEOFF-shaped
    (precedence: explain → Continuity defer → HOLD → LAND → GO_TO →
    TAKEOFF → RETURN_HOME → fallthrough; DC §0 row 4). This function
    re-checks all six ahead-of-it kinds itself — mirroring
    `try_request_takeoff_task`'s own internal guards — so a direct/test
    caller (not just the orchestrator's own call order) cannot have any
    earlier verb's phrase stolen by RETURN_HOME or vice versa.

    Exact-phrase match only, same finite-table discipline as every
    other kind here — no fuzzy match, no stealing arbitrary craft
    design chat. This matters more than usual here: several
    `VEHICLE_RETURN_HOME_PHRASES` entries are short single words
    (`casa`, `home`, `volver`, `vuelve`) — the normalize-then-equality
    check (never a substring/`in` check against the raw line) is what
    keeps a longer craft-chat line like "volver al board" from ever
    matching (IC's own explicit caution).

    Never calls an LLM, never imports `jarvis.flight_software` or
    `jarvis.vehicle_profiles`, never proposes or submits an autonomy
    command itself — fulfilling a matched Task (via `propose_command`/
    `submit_command` + a disarmed `ArmedAllowlistSafetyGate`) is
    entirely the orchestrator's job (DC §0 row 8), same separation
    T6/T7/T8/T9 already established. No home-point/GPS parsing happens
    here or in the orchestrator this Buy — `params` is always empty
    (DC §0 row 9).

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.

    T3-style membership check: before writing `intent.metadata`,
    soft-checks `CAPABILITY_FLIGHT_RETURN_HOME` exists in
    `CapabilityRegistry.load_default()` (membership only). Unknown id →
    refuse (`None`), `intent.metadata` left untouched.

    Deliberately **no** T4 `SoftwareCapabilitySafetyGate` call here
    (IC §0 row 6), same reasoning as every earlier vehicle kind:
    `flight.return_home` is intentionally seeded `not_implemented`/
    `vehicle`, so that gate would either always (and confusingly)
    refuse via the wrong gate, or silently imply a software fulfill
    path for a vehicle verb if the seed ever changed. The real Safety
    check happens once, in the orchestrator's fulfill step — where a
    disarmed gate yields `"disarmed"` regardless of whether
    RETURN_HOME is even on `ArmedAllowlistSafetyGate`'s own allow-list
    (DC §0 row 7 note: it still isn't, this Buy — not widened).
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_GO_TO_PHRASES:
        return None
    if normalized in VEHICLE_TAKEOFF_PHRASES:
        return None
    if normalized in VEHICLE_FOLLOW_PHRASES:
        return None
    if normalized not in VEHICLE_RETURN_HOME_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_RETURN_HOME]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_RETURN_HOME
    return task


def try_request_follow_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `request_follow` Task — the **sixth**
    vehicle Task kind (`DC-assistant-vehicle-follow-task`, ★ CLOSED,
    same seam as HOLD…RETURN_HOME) — or refuse (`None`).

    Exact match on `VEHICLE_FOLLOW_PHRASES` after normalize. Precedence:
    explain → Continuity defer → ARM → DISARM → HOLD → LAND → GO_TO →
    TAKEOFF → RETURN_HOME → **FOLLOW** → fallthrough. Refuses all
    ahead-of-it kinds internally. Membership only — no
    `SoftwareCapabilitySafetyGate`. No person/target parse; fulfill
    always uses empty `params={}`. Never imports FS.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized in CONTINUITY_DEFER_PHRASES:
        return None
    if normalized in VEHICLE_ARM_PHRASES or normalized in VEHICLE_DISARM_PHRASES:
        return None
    if normalized in VEHICLE_HOLD_PHRASES:
        return None
    if normalized in VEHICLE_LAND_PHRASES:
        return None
    if normalized in VEHICLE_GO_TO_PHRASES:
        return None
    if normalized in VEHICLE_TAKEOFF_PHRASES:
        return None
    if normalized in VEHICLE_RETURN_HOME_PHRASES:
        return None
    if normalized not in VEHICLE_FOLLOW_PHRASES:
        return None
    required_capability_ids = [CAPABILITY_FLIGHT_FOLLOW]
    task = Task(intent_id=intent.id, required_capability_ids=required_capability_ids)
    if not _capabilities_known_in_default_registry(required_capability_ids):
        return None
    intent.metadata["task_kind"] = TASK_KIND_REQUEST_FOLLOW
    return task
