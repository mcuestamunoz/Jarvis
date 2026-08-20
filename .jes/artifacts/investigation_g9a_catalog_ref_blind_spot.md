# Investigation — G9-A Catalog-Ref Blind Spot

**Contract:** [`investigation_contract_g9a_catalog_ref_blind_spot.md`](investigation_contract_g9a_catalog_ref_blind_spot.md)
**Checkpoint base:** `checkpoint-r3b` (`4608eed`) — confirmed current HEAD.
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no new tests (investigation only, per contract §2).

---

## 1. Dual call-site audit

### 1.1 Equivalence

The two call sites are **byte-for-byte identical**, and this is not incidental — `engineering_readiness.py`'s own docstring says so directly:

> `resolve_motor_catalog_surface` — "Ported byte-for-byte from `orchestrator.build_startup_context`'s own catalog-gap computation (unchanged there) — same filters, same wording."

| Call site | Location | Consumer |
|---|---|---|
| Inline duplicate | `orchestrator.py:3585–3633` (`build_startup_context`) | `motor_catalog_gap`/`motor_catalog_matches` in the startup-context dict → `build_project_continuity` (via kwarg) → CLI `estado` |
| `resolve_motor_catalog_surface` | `engineering_readiness.py:180–240`, called once at `:1020` inside `build_engineering_readiness` | `_motor_catalog_gaps(req, catalog_gap)` → `GAP-MOTOR-CATALOG-UNRESOLVED` in the Gap Registry rollup |

**No drift found.** Both read the same three inputs, run the same `default_library.find_motors_for_requirements(min_thrust_n, kv, prop_inch)` call, and build the same Spanish message string. `orchestrator.py` does **not** call `resolve_motor_catalog_surface` at all — it keeps its own copy, exactly the debt ERF-1 §6.1 flagged and did not close. This is confirmed by grep: the only caller of `resolve_motor_catalog_surface` in the whole codebase is `engineering_readiness.py:1020` itself.

Both computations run **independently, once per `build_startup_context` call** (orchestrator computes its own copy directly; `build_engineering_readiness` — called a few lines later in the same function — recomputes `req` via `derive_physical_requirements` again and runs `resolve_motor_catalog_surface` a second time). No caching, no shared call — same physics inputs in, same string out, just computed twice per turn. Not a correctness bug, just a minor redundancy dedup would also remove for free.

### 1.2 Field-read matrix

| Field on `motors` component / params | Read by gap computation? | Used for |
|---|---|---|
| `catalog_ref` | **No** | — (the blind spot) |
| `catalog_ref.family` | **No** | — |
| `catalog_ref.sku` | **No** | — |
| `properties["kv_rating"]` | Yes | `kv_hint` → filter param to `find_motors_for_requirements` |
| `properties["thrust_n"]` | **No** | — (the bound SKU's own declared thrust is never read; the "requirement" side comes entirely from `physical_requirements["thrust_per_motor_needed_n"]`, a physics-derived floor, not from what the bound part actually delivers) |
| `properties["power_w"]` | No | — |
| `properties["weight_g"]` | No | — |
| `completeness` | No (in this computation; used elsewhere for BOM tier) | — |
| `current_parameters["propeller_diameter_in"]` | Yes | `prop_inch` → filter param |
| `current_parameters["per_motor_max_thrust_n"]` | No (in this computation; read separately by G9-B's `catalog_gap_covered_by_declared_thrust`) | — |

**Conclusion:** the computation treats "is there a motor in the library that covers this design-space point" as if no motor had ever been chosen — it re-runs a fresh, generic catalog search on every call, discarding the one fact (`catalog_ref`) that Impl B added specifically to remember a durable identity decision.

---

## 2. Bound-SKU scenarios

| # | Scenario | Expected gap? | Expected evidence / CTA |
|---|---|---|---|
| A | No motor / no `catalog_ref` | Yes, if `find_motors_for_requirements` returns empty | Current message, unchanged |
| **B** | `catalog_ref` set, SKU exists in library, SKU's design-space (`min_thrust_n..max_thrust_n`, `kv_min..kv_max`, `compatible_prop_inch`) covers current requirements | **No** `GAP-MOTOR-CATALOG-UNRESOLVED` | `catalog_gap = None`. BOM already shows the SKU (via `component_bom`/`completeness="high"`); no further catalog note needed. |
| **C** | `catalog_ref` set, SKU exists, but current requirements have drifted **past** what the bound SKU's design-space covers | **Yes — but a different, honest message than A/F** | New wording: names the bound SKU and *why* it's now insufficient (e.g. thrust floor moved past `max_thrust_n`), not "no tengo un motor" (false — a motor **is** bound, it's just outgrown). See §8 recommendation. |
| **D** | `catalog_ref` set, but `sku` no longer resolves in the library (row deleted/renamed) | **Yes** | Honest "el motor vinculado ({sku}) ya no está en el catálogo" — a failure mode with **zero** existing coverage today (see §4). |
| E | `catalog_ref` cleared by G5 (`invalidate_diverged_catalog_refs`) after a DSE/iterate divergence | Yes | Falls straight through to today's Scenario-A path — component is now unbound by construction, no new logic needed. |
| F | Generic/unbound motor, declared thrust present, no SKU | Yes | Current behavior, unchanged |

### Recommended default for Scenario C (the open question from the original G9 audit)

**Gap, not silence, and not INCOMPATIBLE.**

- **Not silence:** the whole point of G9-A is honesty. If the bound SKU no longer covers the design space, saying nothing would be a *worse* lie than today's "no tengo un motor" — it would let the user believe an already-stale part is still correct.
- **Not INCOMPATIBLE:** `_INCOMPATIBLE_CLASS_GAP_TYPES` (ERF-2 §8.2) is reserved for deterministic evidence of a real conflict the physics/electrical layer computed (`GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`). A stale catalog binding is a **procurement/identity** fact, not a physics conflict — the design itself may still be perfectly flyable (physics uses `per_motor_max_thrust_n`, a declared/derived number, independent of whether a SKU still backs it). Promoting it to INCOMPATIBLE would conflate "the BOM identity is stale" with "the design doesn't work," which is a category error the ERF-2 severity model deliberately avoids elsewhere.
- **Same gap type, richer evidence — not a new `GAP-` type.** Reuse `GAP-MOTOR-CATALOG-UNRESOLVED` (MEDIUM, `catalog`/`propulsion`/`bom`), but with a distinguishing `GapEvidence.fact` (e.g. `"bound_sku_underspec:{sku}"` vs today's `"catalog_matches.empty"`) and message wording that names the SKU. This keeps the ERF-2 gap-type registry closed (no new type to slot into `_INCOMPATIBLE_CLASS_GAP_TYPES`, `_COMPONENT_SUBSYSTEM_MAP`, etc.) while still being honest and distinguishable in evidence for anyone inspecting the Gap Registry.
- **CTA:** still run `find_motors_for_requirements` against the *current* requirements (not the bound SKU) so the message can offer real alternatives when they exist ("el motor {sku} vinculado ya no cubre el hueco de diseño; alternativas: X, Y") or fall back to today's generic "no tengo un motor" wording appended after naming the stale SKU when no alternative exists either.

---

## 3. ERF-2 / Continuity / G9-B interaction

- **G9-B (`catalog_gap_covered_by_declared_thrust`) is orthogonal, not conflicting.** G9-B only *demotes the ranking* of an already-computed non-`None` `catalog_gap` (PASS + declared thrust ≥ floor → `next_useful_step` no longer leads with it). G9-A changes *whether* `catalog_gap` is `None` in the first place. If G9-A clears the gap for Scenario B, G9-B's demotion logic simply never runs for that project (nothing to demote — consistent, not a double-count). For Scenario C, G9-B still independently decides demotion from `per_motor_max_thrust_n` vs the physics floor, which is correct: a stale-but-not-physically-blocking SKU is exactly the case G9-B's demotion was built for, and it will keep working unchanged because G9-A does not touch `current_parameters` or `sim_status`.
- **`GAP-PROP-MOTOR-MISMATCH`** comes from `electrical_compatibility.evaluate` → `library.match_motor_propeller`, a completely separate compatibility check (declared KV/prop pairing, not catalog-search-for-requirements). No overlap with G9-A's fix; both can independently be true or false on the same project (e.g. bound SKU still covers current thrust requirements — no `GAP-MOTOR-CATALOG-UNRESOLVED` — but its prop pairing is wrong — `GAP-PROP-MOTOR-MISMATCH` fires). No double-count risk since they are different `gap_type`s with independent triggers.
- **`GAP-BOM-INCOMPLETE-COMPONENT:motors`** is driven by `component_presence_tier`/`completeness`, not by catalog-gap computation. A bound SKU is always `completeness="high"` (set by `bind_motor_from_catalog`), so this gap never fires for a bound motor regardless of G9-A. No interaction.
- **No verdict double-count:** `_INCOMPATIBLE_VERDICT_SUBSYSTEMS` only maps the three INCOMPATIBLE-class types above; `GAP-MOTOR-CATALOG-UNRESOLVED` stays MEDIUM/WARNING-class in the subsystem rollup regardless of which scenario produced it, so clearing it in Scenario B or re-wording it in Scenario C changes `ASSEMBLY_READY` eligibility exactly as expected (fewer/more non-PASS subsystems) with no new rollup logic needed.

---

## 4. Dedup / single authority

**Recommended: yes, land the fix in `resolve_motor_catalog_surface` only, and make `orchestrator.build_startup_context` call it instead of inlining.**

- `orchestrator.py` already imports from `engineering_readiness` two lines below the inline block (`from jarvis.core.engineering_readiness import build_engineering_readiness`) — adding `resolve_motor_catalog_surface` to that same import is zero new circular-import risk (the dependency direction orchestrator → engineering_readiness already exists and is one-way; engineering_readiness never imports orchestrator, confirmed by `test_readiness_does_not_import_continuity`'s sibling constraint and a source grep).
- Blast radius of dedup: delete ~48 lines (3585–3632) from `orchestrator.py`, replace with a 6-line call to `resolve_motor_catalog_surface(project_state, physical_requirements)`. Since the two are already proven byte-identical, this is a pure refactor with **zero behavior change** on its own — the risk is entirely in the G9-A logic addition, not the dedup.
- Fix-in-place (patch both copies identically) is strictly worse here: it doubles the diff, re-introduces exactly the "two places to keep in sync" debt ERF-1 already flagged once, and has already drifted zero times only because no one has touched either copy since the port — a second independent edit site increases the chance a future change updates one and not the other.
- **No existing test breaks from the dedup itself** — every test that exercises `motor_catalog_gap`/`motor_catalog_matches` goes through either `build_startup_context` or `build_engineering_readiness`/`resolve_motor_catalog_surface` as a black box; none asserts on the *duplication* itself, and the byte-for-byte equivalence means assertions on output strings/lists are unaffected by which code path produced them.

---

## 5. Design options

### Option A — Minimal, fix in place (no dedup)

Add the bound-SKU check identically to both `orchestrator.py:3585` and `engineering_readiness.py:180`.

- `catalog_gap` is `None` when: (existing "matches found" path) **or** (new: `catalog_ref` set, SKU resolves, SKU's own design-space bounds cover current `thrust_per`/`kv_hint`/`prop_inch`).
- Bound SKU validated via `default_library.get_motor(sku)` / `has_motor(sku)` (already exist, no new library method needed) wrapped in a try/except `KeyError` for Scenario D.
- Requirements drifting past the bound SKU: reuse the same bound/covers check — `False` → Scenario C wording (§2 recommendation).
- Files touched: 2 (`orchestrator.py`, `engineering_readiness.py`), symmetric diffs.
- Tests: extend `tests/test_engineering_readiness_gaps.py`'s existing `catalog_ref` fixture parameter (currently unused — see §7) for B/C/D, plus a small `build_startup_context`-level test mirroring the same three cases in `tests/test_project_continuity.py` or a new orchestrator test.
- Risks: keeps the duplication debt alive (two edit sites forever); otherwise same risk profile as B for the logic itself.

### Option B — Dedup + fix (recommended)

Everything in Option A's *logic*, but landed **once** in `resolve_motor_catalog_surface`; `orchestrator.build_startup_context` deletes its inline copy and calls the shared function (§4).

- Same `catalog_gap`/validation/drift semantics as Option A.
- Files touched: `engineering_readiness.py` (add ~15–20 lines of bound-SKU logic to `resolve_motor_catalog_surface`), `orchestrator.py` (net **negative** diff — delete ~48 lines, add ~6).
- Tests: same as Option A's test list, but only one production code path to exercise per scenario (though still worth a thin orchestrator-level smoke test to confirm the delegation wiring didn't drop a field).
- Risks: same logic risk as A (false silence if the "covers" check is too permissive; stale SKU label if Scenario D's `has_motor` check is skipped) — mitigated by an explicit test per scenario (§7) — plus a one-time refactor risk on the dedup itself, which §4 argues is near-zero given proven byte-equivalence.

### Option C — Full scenario matrix + typed bound-status (most complete, larger scope)

Everything in Option B, plus:

- A new returned field (`bound_sku_status: Literal["sufficient","underspec","unknown","unbound"]`, or similar) alongside `catalog_gap`/`catalog_matches`, so BOM/Continuity/future Impl C can reason about bound-SKU state without string-matching gap text.
- Distinct `GapEvidence.fact` values per scenario (already recommended as part of B/C's message; Option C makes this a first-class typed field instead of just evidence-string flavor).
- Files touched: `engineering_readiness.py`, `orchestrator.py`, likely `project_closure.py` (BOM formatting) and/or `project_continuity.py` if any consumer wants to branch on the new field instead of just displaying the message, possibly schema changes if the field needs to persist.
- Tests: everything in B, plus consumer-side tests for whichever new field gets threaded through.
- Risks: larger diff, more downstream churn for a benefit (typed consumption) nothing in the current codebase actually needs yet — `project_continuity.py`/CLI only ever display the message string today. This is a reasonable **future** direction for Impl C (catalog-aware DSE candidates, which will need to reason about bound-SKU state programmatically), not a requirement for closing G9-A's honesty gap now.

**Recommendation: Option B.** It closes the exact residual the contract names (Scenario B/C/D honesty) and the dedup debt ERF-1 already flagged, without expanding the data contract (Option C) beyond what any current consumer needs. Option C's typed field is worth flagging to Engineer as a candidate for Impl C's own investigation rather than folding it into G9-A.

---

## 6. Test inventory

| File | What it covers today | Needs updating for G9-A? |
|---|---|---|
| `tests/test_engineering_readiness_gaps.py` | `GAP-MOTOR-CATALOG-UNRESOLVED` trigger/absent. `_motor_spec()` fixture **already accepts** a `catalog_ref` kwarg (default `None`) but no existing test passes a non-`None` value — the groundwork is there, unused. | **Yes** — add B/C/D cases using the existing fixture parameter. |
| `tests/test_engineering_readiness_subsystems.py`, `test_engineering_readiness_erf2_gaps.py`, `test_engineering_readiness_continuity.py` | Subsystem verdict/rollup, ERF-2 gap types, readiness→continuity wiring | Only if a B/C/D scenario is added at this layer to confirm rollup still reads `catalog_gap`/`GAP-MOTOR-CATALOG-UNRESOLVED` correctly post-fix — likely one smoke test each, not a rewrite. |
| `tests/test_cli_polish.py` (G9-B) | Passes `motor_catalog_gap` as a **pre-built string literal** directly into `build_project_continuity`/CLI formatters | **No** — insulated from the computation change; these test downstream *consumption* of an already-given gap value. |
| `tests/test_project_continuity.py` | Same pattern — `motor_catalog_gap` passed as a literal string or `None` | **No**, same reason. |
| `tests/test_catalog_bind_v1.py` | `catalog_ref` binding/persistence/divergence (Impl B, G5) — `bind_motor_from_catalog`, `invalidate_diverged_catalog_refs` | **No** — orthogonal (binding mechanics, not gap computation), but this file is the right place to add a round-trip probe: bind → run `resolve_motor_catalog_surface` → confirm `catalog_gap is None` (Scenario B end-to-end), since it already has the fixtures for a bound project. |
| `tests/test_assisted_acquisition.py`, `test_f1_reducir_payload.py`, `test_fn020_completeness_coherence.py`, `test_g5_dse_iterate_dual_truth.py`, `test_electrical_compatibility.py`, `test_catalog_foundation_v1.py` | Reference `motor_catalog_gap`/`catalog_ref` incidentally (fixture setup or unrelated assertions in the same test) | Spot-check only — grep hits are incidental, not scenario-specific; unlikely to need changes but worth a full-suite run after the fix (contract's own "zero weakened tests" bar). |

**Proposed regression probes for the future IC** (bullets, not written here):

1. Scenario B: bound SKU, requirements unchanged since bind → `catalog_gap is None`, `GAP-MOTOR-CATALOG-UNRESOLVED` absent from `readiness.gaps`.
2. Scenario B → C transition: bind, then raise payload/thrust requirement past the bound SKU's `max_thrust_n` (e.g. via DSE apply that stays under G5's divergence epsilon, or a `motor_count` change that raises `thrust_per_motor_needed_n` without touching `per_motor_max_thrust_n` — the actual field G5 watches) → gap reappears with SKU-naming wording, not the generic "no tengo un motor" string.
3. Scenario D: `catalog_ref.sku` set to a value not present in `default_library` (simulate a deleted row) → honest "ya no está en el catálogo" message, not a `KeyError` propagating up through `build_startup_context`/`build_engineering_readiness`.
4. Scenario E regression: existing `test_dse_apply_diverging_thrust_clears_motor_catalog_ref` (already in `test_catalog_bind_v1.py`) must keep passing unchanged — divergence clears `catalog_ref` before G9-A's check ever sees it, so it's Scenario A/F by the time the gap computation runs.
5. G9-B regression: PASS + declared thrust covers floor + **Scenario C** bound SKU → gap still demotes from `next_useful_step` (not swallowed by G9-A, not double-surfaced).
6. Dedup smoke: `build_startup_context`'s `motor_catalog_gap`/`motor_catalog_matches` fields stay present and correctly populated after `orchestrator.py` switches to calling `resolve_motor_catalog_surface` instead of inlining.

---

## 7. Recommendation

**Option B** — land the catalog_ref-aware logic once, inside `resolve_motor_catalog_surface`, and have `orchestrator.build_startup_context` delegate to it instead of keeping its own inline copy.

Reasoning, in priority order:

1. It is the only option that satisfies the contract's own hard constraint "single authority preferred... if dedup is feasible within G9-A scope" — and §4 shows dedup here is close to risk-free (proven byte-equivalence, no circularity, no test asserts on the duplication).
2. It closes exactly the residual named in §0 (Scenario B's false "no tengo un motor") without expanding the data contract the way Option C would — no consumer today needs a typed bound-status field; the message string is all `project_continuity`/CLI actually read.
3. Scenario C's recommended treatment (reuse `GAP-MOTOR-CATALOG-UNRESOLVED`, richer evidence/wording, no new gap type) keeps the ERF-2 gap-type registry closed, consistent with how G9-B was scoped as "a ranking fix, not a new subsystem."
4. Scenario D closes a genuine, previously-uncovered failure mode (a bound SKU silently vanishing from the library) with library methods (`get_motor`/`has_motor`) that already exist — no new library API needed.

---

## 8. Suggested Implementation Contract outline

*(Bullets only, per contract §3 — not a full IC.)*

**Slice 1 — bound-SKU-aware `resolve_motor_catalog_surface`**
- Add `catalog_ref` read + `default_library.get_motor(sku)`/`has_motor(sku)` lookup.
- Add a single-motor "covers requirements" predicate (reuse `find_motors_for_requirements`'s own bound-check logic — `min_thrust_n`/`max_thrust_n`/`kv_min`/`kv_max`/`compatible_prop_inch` — factored so it can run against one `MotorSpec`, not just filter a list).
- Branch: SKU missing from library → Scenario D message. SKU found, covers current requirements → `catalog_gap = None`. SKU found, does not cover → Scenario C message (name the SKU, still run `find_motors_for_requirements` for alternatives).
- Acceptance: `test_engineering_readiness_gaps.py`'s three new cases (B/C/D) pass; existing `test_gap_motor_catalog_unresolved_trigger`/`_absent_when_matches_found` unchanged.

**Slice 2 — dedup orchestrator's inline copy**
- Delete `orchestrator.py:3585–3632`'s inline block; call `resolve_motor_catalog_surface(project_state, physical_requirements)` instead.
- Acceptance: `build_startup_context`'s `motor_catalog_gap`/`motor_catalog_matches` output unchanged for every existing fixture; new B/C/D cases reachable through `build_startup_context` too (one smoke test each).

**Slice 3 — regression coverage for interactions**
- G9-B demotion + Scenario C (probe #5 in §6).
- G5 divergence + Scenario C→A/F transition (probe #4).
- Full suite green, zero weakened tests.

**Out of scope for the IC (flag to Engineer, not implied by this investigation):**
- Option C's typed `bound_sku_status` field — candidate for Impl C's own investigation.
- Battery/propeller `catalog_ref` equivalents — same blind spot likely exists (`bind_battery_from_catalog`/`bind_propeller_from_catalog` both set `catalog_ref`, and nothing in the codebase currently computes a "battery catalog gap" or "propeller catalog gap" the way motors get one — so there is arguably no equivalent gap-computation to fix yet, only the motor one). Worth a one-line note in the IC that this is motor-only by design, not by oversight.
