# Investigation Report — Propeller Catalog Bind UX (P2-1 unlock)

**Contract:** [`investigation_contract_propeller_catalog_bind_ux.md`](investigation_contract_propeller_catalog_bind_ux.md)
**Checkpoint base:** `checkpoint-phase2-p2-1` (`e82b8a1`)
**Status:** Investigation complete. **No `src/` or test files touched** (verified — see §11 sign-off).

---

## 1. Executive summary

Propellers today can only be acquired as a **freeform component description** (`hélices 5x4.5`) inside the composite `propulsion` wizard (`BLOCK_TO_COMPONENTS["propulsion"] = ["motors", "propellers", "esc"]`) — there is no catalog list, no numbered pick, and `bind_propeller_from_catalog` (which already exists and is correct) has exactly zero live call sites; it's only reachable from tests and the P2-1 CLI probe. This is architecturally the **same gap G21 closed for motors**, one level behind.

The good news: G21's own machinery is almost entirely reusable as-is. `match_suggestion_by_input` (index/name matching) is generic — it never touches motor-specific fields beyond `idx`/`name`, so it works unmodified on a propeller suggestion list. `ComponentLibrary.match_motor_propeller` (already used by ERF-2) is sufficient to build a ranked, filtered propeller suggestion list with **zero new library code** — confirmed directly: querying it for both P2-1 SKUs (`emax_rs2205s_2300`, `sunnysky_r2205_2500`) already surfaces `hq_5045_bn` and `gf_5045x3` via ordinary diameter-tolerance matching, no special-casing required (Option C from the contract is unnecessary — Option A subsumes it for the current seed).

One real, currently-latent bug must be fixed as part of this work, not worked around: `orchestrator._handle_component_description`'s motors help-choose block intercepts `is_help_choose_phrase` **unconditionally** whenever `"motors" in expected_keys` — with no check that motors is still actually incomplete. In the composite `propulsion` wizard, `expected_keys` stays the static `["motors","propellers","esc"]` list for the whole session, so once motors is bound, a propeller help-choose block added *after* it in the same `if` chain would **never be reached** — the motors block would keep re-intercepting every "ayúdame a elegir" turn. This must be fixed by gating both blocks on "is this key still incomplete," not on static list membership.

A second, positive finding: **P2-1's `resolve_operating_point` does not require voltage/battery context to reach `exact_operating_point`** for the ★6 dataset — verified directly: propeller bind alone (no battery, no `battery_cell_count`) already resolves `emax_rs2205s_2300` + `hq_5045_bn` to `exact_operating_point`, 9.7086 N. The investigation contract's own framing ("exact rows need ~16 V... does fallback still win until battery declared?") assumed voltage was a hard prerequisite; it is not, for this dataset. This simplifies the recommended CLI walk and the v1 IC scope: **propeller bind alone is the unlock**, battery bind stays correctly deferred (C3).

Mandatory OP re-resolve question (§5): confirmed `set_propeller_component` does **not** trigger a motor OP refresh — nothing does, today, automatically. The minimal, correct fix (already proven working in the P2-1 CLI probe) is an **explicit re-call of `set_motor_component`** with the already-bound motor spec immediately after a propeller bind, when motors is catalog-bound. No new shared "refresh" helper is needed or recommended.

**Recommended v1 slice: Option A+B** — propeller help-choose inside the composite propulsion component wizard (mirroring G21 Slice 1 exactly) plus the IDLE re-bind branch for a freeform-declared, unbound propeller. Requires one new session field (`propeller_suggestions`, symmetric with `motor_suggestions`), one new small suggestion-builder function, one motors/propellers priority-gating fix, and the explicit OP re-resolve call.

---

## 2. As-is propeller acquisition audit

| Step | File / symbol | Finding |
|---|---|---|
| Component wizard | `orchestrator._handle_component_description` | `expected_keys` for `propulsion` = `["motors","propellers","esc"]` (composite, `system_architecture_catalog.py:158`). Propellers reaches the wizard only via the generic `infer_components`/`infer_component_for_key` freeform path (FN-019's forced-propeller block, `orchestrator.py:2615-2625`). No catalog branch exists for `"propellers"` — the motors catalog branch (`orchestrator.py:2528-2542`) has no propeller sibling. |
| Help-choose | `is_help_choose_phrase` (`motor_catalog_assist.py:68`) | **Not motor-locked despite the module name.** Soft-match rule is `"ayudame" in text and any(tok in text for tok in ("elegir","escoger","motor","opcion"))` — bare "ayúdame a elegir" (no "motor" mentioned) already matches via the "elegir" token alone. It is reusable verbatim for propellers; the module's *name* is motor-specific, its *phrase logic* is not. |
| Freeform | `hélices 5x4.5` / `10x4.5` | Sets `properties["diameter_in"]`/`["pitch_in"]` via `infer_component_for_key` → `set_propeller_component`. **Never sets `catalog_ref`** — confirmed by reading `component_inference.py`'s propeller extractor: it only ever returns a bare `ComponentSpec` with `catalog_ref` left at its default `None`. This is correct/expected: freeform declaration is not supposed to claim catalog identity. |
| Bind | `bind_propeller_from_catalog` (`catalog_bind.py:126`) | Exists, correct (confirmed in the P2-1 investigation), zero production call sites. `grep -rn "bind_propeller_from_catalog" src/` returns only its own definition — every other reference is in `tests/` or `scripts/cli_probe_phase2_lookup_op.py`. |
| Writer | `set_propeller_component` (`component_writers.py:271`) | Bridges `diameter_in`/`pitch_in`/(new) nothing else — confirmed by reading its full body: it does **not** call `resolve_operating_point` or `set_motor_component`. A propeller bind alone never touches `per_motor_max_thrust_n` or `propulsion_resolution` — see §5 for the mandatory fix. |
| Continuity | `acquisition_brief.build_acquisition_brief` | The "decir 'ayúdame a elegir'" bullet is gated `if key == "motors"` only (`acquisition_brief.py:83-89`), with an explicit comment: *"battery/frame/propellers, which have no bind path to point to yet"* — this comment is the exact TODO this IC closes for propellers specifically. |
| Numeric wizard | `ASSISTED_MOTOR_PARAMS` (`motor_catalog_assist.py:47`) | `frozenset({"motor_power_w", "per_motor_max_thrust_n"})` — **motor-only.** `MISSING_PROPELLER_PARAMETERS`'s required params (`propeller_diameter_in`, `propeller_rpm`, `parameter_requirements.py:241`) have no assisted/catalog numeric-wizard sibling at all. **This means propellers only need the component-wizard integration (mirroring G21 Slice 1) — there is no second, numeric-wizard surface to also wire**, unlike how motors originally had two (component-wizard + numeric ASSISTED_MOTOR_PARAMS wizard). This narrows scope meaningfully vs. G21's original two-slice shape. |

**Sequence diagram — motor-done → propeller declare → state, today:**

```text
User: "ayúdame a elegir" (motors pending)
  → _offer_component_motor_catalog → motor_suggestions populated
User: "5"
  → _apply_component_motor_catalog_pick
      → bind_motor_from_catalog(suggestion)
      → set_motor_component(ps, spec, watts)
          → resolve_operating_point(sku, propeller_sku=None, voltage_v=None)
          → resolution_type = fallback_operating_point (or legacy_estimate)
  → wizard advances: still_missing = ["propellers"] (esc handled separately/already satisfied or next)
User: "hélices 5x4.5"                         ← ONLY path available today
  → infer_components → propellers ComponentSpec (catalog_ref=None)
  → set_propeller_component(ps, spec)          ← bridges diameter/pitch only
  → per_motor_max_thrust_n / propulsion_resolution: UNCHANGED, still fallback
  → estado: still "fallback_operating_point · 10.042 N" forever
      (freeform propeller can never produce catalog_ref → never exact)
```

---

## 3. Suggestion authority options + recommendation

| Option | Approach | Verdict |
|---|---|---|
| **A** | Filter `list_propellers()` by bound motor via `match_motor_propeller(motor_sku, prop_sku)` (existing ERF-2 predicate — no new library code) | **Recommended.** Verified directly (see below) — already surfaces both P2-1 seeded props for both new motor SKUs with zero special-casing. |
| **B** | Always show the full propeller catalog (16 rows today, `limit` applied) | Works as a **fallback only**, when no motor is bound yet (Option A has nothing to filter against) — not a substitute for A once a motor exists. |
| **C** | Prefer P2-1 seeded props when motor is one of the two new SKUs, else A | **Rejected as unnecessary** — proven redundant: Option A already returns `hq_5045_bn`/`gf_5045x3` for both new motors via ordinary `compatible_prop_inch` diameter-tolerance matching (no `compatible_prop_ids` was set on either motor row in P2-1, so the match goes through the diameter-tolerance branch, same mechanism `find_motors_for_requirements` already uses elsewhere). Adding SKU-specific special-casing on top would be exactly the kind of parallel/duplicated logic both this contract and CLAUDE.md forbid without proven necessity — and necessity is disproven here. |

**Verified (direct library call, no code changes):**

```text
match_motor_propeller("emax_rs2205s_2300", *)   → gemfan_5030, gemfan_6040, gf_5045x3, hq_5045_bn
match_motor_propeller("sunnysky_r2205_2500", *) → gemfan_5030, gemfan_6040, gf_5045x3, hq_5045_bn
```

(`gemfan_6040` appears too — it's a 6.0" prop within the existing ±1.0" diameter tolerance `match_motor_propeller` already uses for every motor in the library, not a new coarseness introduced by this work.)

**Recommended: Option A, with Option B as the explicit no-motor-bound fallback** — i.e. exactly the same two-tier structure `build_motor_catalog_suggestions` already uses (strict filter first, an honest "nothing matches" gap message when empty — **not** a silent full-catalog dump, per the G22 precedent of "no KV-only fallback that disagrees with the gap").

**Suggestion authority location:** a **new small dedicated function**, `build_propeller_catalog_suggestions(project_state)`, in a **new** module — not inside `motor_catalog_assist.py`. That module is conceptually and literally motor-scoped (`MotorSuggestion`, `ASSISTED_MOTOR_PARAMS`, motor-specific phrase constants); bolting propeller logic onto it would blur a module that Impl C/D/P2-1 already treat as "the motor assist module." A new `propeller_catalog_assist.py` (mirroring the existing file's shape: `PropellerSuggestion` TypedDict, `build_propeller_catalog_suggestions`, `format_propeller_catalog_suggestions`) keeps the reused generic pieces (`match_suggestion_by_input`, `is_help_choose_phrase`) **imported from** `motor_catalog_assist.py` rather than duplicated — no second implementation of either, only a second *call site* built around the same generic functions plus a propeller-specific candidate query.

---

## 4. Session / help-choose wiring plan

**Reuse `is_help_choose_phrase`** as-is (§2) — no new phrase detector needed; it already fires on generic "ayúdame a elegir" regardless of component.

**New session field required:** `propeller_suggestions: list[dict] = Field(default_factory=list)` on `InteractiveSessionState` (`action_schema.py:239`, symmetric with `motor_suggestions`). Reusing the existing `motor_suggestions` field for both would conflate two independent pick contexts that can legitimately coexist mid-session (composite wizard) — a real ambiguity, not a hypothetical one, given the collision finding below.

**The collision the contract's own risk list already flagged is real and currently latent, not new:**

`orchestrator.py:2528` — `if "motors" in expected_keys:` — intercepts `is_help_choose_phrase` **unconditionally**, with no check that motors is still incomplete. Because `expected_keys` is the static composite list `["motors","propellers","esc"]` for the entire wizard session (confirmed: `_apply_component_motor_catalog_pick`'s `still_missing` is recomputed from live component completeness on each call, not from a shrinking `pending_missing_params` — the list itself never narrows), **this check is already unconditionally true for the whole session**, even after motors is bound. Today this is invisible because there's no propeller help-choose block to be starved. The moment one is added after it in the same `if`/`elif` chain, it becomes unreachable in the common composite-wizard path — a user who already picked a motor and says "ayúdame a elegir" wanting a propeller would silently get the motor catalog re-shown instead.

**Required fix (part of this slice, not a separate finding):** gate both blocks on **live incompleteness**, not static membership:

```text
motors_done = components.get("motors") is not None and components["motors"].catalog_ref is not None \
              or (components.get("motors") is not None and components["motors"].completeness != "low")
if "motors" in expected_keys and not motors_done and is_help_choose_phrase(user_input):
    → motor catalog branch
elif "propellers" in expected_keys and not propellers_done and is_help_choose_phrase(user_input):
    → propeller catalog branch
```

This is a **minimal, targeted priority fix**, not a wizard redesign — it reuses the exact "still_missing" completeness check `_apply_component_motor_catalog_pick` already computes after a pick, just evaluated *before* dispatch too. It also naturally implements the "motors-first when both pending" precedent Continuity Hardening ★4 already established for forced inference (§2's `component_inference` ordering) — consistent product behavior, not a new policy.

**IDLE wiring:** mirror `_try_start_assisted_motor_help`'s already-correct gating pattern (`catalog_ref is not None → return None`, no picker noise) — a new `_try_start_assisted_propeller_help`-equivalent branch, reached from the same FN-005 IDLE dispatch (`orchestrator.py:811-818`) only when motors is already resolved (bound or intentionally freeform) and propellers is the next real gap. Given §2's finding that there is no numeric propeller wizard, this IDLE branch only ever needs to open the **component-wizard** propeller picker (same shape as G21's motors IDLE re-bind), not a second numeric-wizard variant.

**Does not conflict with motor IDLE help-choose**, because `_try_start_assisted_motor_help` already returns `None` (falls through) once a motor is bound with `catalog_ref` set — the natural place to add "then check propellers" is right after that existing early return, not a parallel dispatch.

---

## 5. OP re-resolve after bind (mandatory answer)

**Confirmed: `set_propeller_component` does not, and today nothing does, automatically re-resolve the motor's operating point after a propeller bind.** There is no global "recompute all component-derived params" pass in this codebase — `apply_and_recalculate` (`param_definition_session.py:712`) is a per-key mirrored-param dispatcher, not a holistic recompute. `set_motor_component` is the **only** place `resolve_operating_point` is called, and it only runs when `set_motor_component` itself runs.

**Options evaluated:**

1. **Explicit re-call of `set_motor_component`** with the already-bound motor spec, immediately after `set_propeller_component` succeeds, whenever `components["motors"].catalog_ref` is already set. — Reuses the exact writer P2-1 already built; **already proven correct** in `scripts/cli_probe_phase2_lookup_op.py`'s own step 3 (which does exactly this to demonstrate the exact-OP path). No new function.
2. A new shared `refresh_propulsion_resolution(project_state)` helper that re-derives only the OP fields without going through the full `set_motor_component` machinery (motor_count preservation, mass mirroring, etc.). — More code, a second place that could drift from `set_motor_component`'s own logic over time, and no proven need for it to skip any of that machinery (re-running it is cheap and idempotent — it's a pure, deterministic recomputation from already-known inputs).

**Recommendation: Option 1.** Minimal, already-validated, reuses the sole existing writer, adds zero new surface. Practically: the propeller-pick handler needs read access to the current motor `ComponentSpec` and its `power_w` (from `motors_spec.properties.get("power_w")` or `current_parameters.get("motor_power_w")`) to pass to the re-call — both already available at that point in the call site (same pattern `_apply_component_motor_catalog_pick` uses to read `expected_keys`/`components`).

**Hashability re-confirmed (P2-1 lesson, §6 of that report):** the re-call goes through the *same* `set_motor_component` code path that already stores `propulsion_resolution` as a JSON string — no new risk introduced, no design_explorer.py cache-key concern, since nothing about this slice adds a second place that writes to `current_parameters`.

---

## 6. Voltage / walk sequencing notes

**Finding (verified, not assumed):** for the ★6 dataset, propeller bind **alone** — no battery, no `battery_cell_count` — already resolves `exact_operating_point`:

```text
resolve_operating_point("emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=None)
  → resolution_type=exact_operating_point, thrust_n=9.7086, selection_reason=v1_max_thrust
```

This is because `resolve_operating_point`'s own exact-match rule (P2-1, §3.2 rule 1) treats an absent caller-side `voltage_v` as "don't filter on voltage," not as "no match." Since both OP-1 and OP-2 for `emax_rs2205s_2300` are at the same 16.0 V, there is nothing for voltage to disambiguate *in this dataset* — the max-thrust policy alone picks between them.

**This contradicts the contract's own §1.5 framing**, which assumed voltage was a hard prerequisite ("Exact EMAX rows need ~16 V... does fallback still win until battery cells declared?"). It does not, for this dataset. **Voltage only becomes load-bearing once a future motor+prop combo has multiple exact rows at *different* voltages** — not the case for OP-1/OP-2/OP-3 today.

**Recommended honest `estado` sequence for the Engineer CLI walk (v1 slice):**

```text
1. Bind emax_rs2205s_2300 (component wizard pick)
   → estado: fallback_operating_point · manufacturer_test · 10.042 N (sin hélice de catálogo)
2. ayúdame a elegir (propellers pending) → pick hq_5045_bn
   → set_propeller_component + re-call set_motor_component (§5)
   → estado: exact_operating_point · manufacturer_test · 9.7086 N
```

No battery step is required to reach the exact walk milestone — battery bind stays correctly out of scope (C3, deferred), and this investigation found no reason to reconsider that.

---

## 7. Design options (2-3) + trade-offs

| Option | Scope | Pros | Cons |
|---|---|---|---|
| **A** | Propeller help-choose only inside the composite propulsion component wizard (mirror G21 motors exactly) | Smallest change; matches §2's finding that no numeric-wizard sibling is needed; unlocks the exact-OP CLI walk end to end | No IDLE re-bind for a user who already freeform-declared propellers before this ships — they'd need to know to re-declare or the (future) IDLE branch |
| **B** (additive on A) | A + IDLE re-bind when propellers is freeform/unbound (mirrors G21's `_try_start_assisted_motor_help` addendum) | Symmetric with the motor UX; catches the "already declared freeform, wants to upgrade to SKU" case | Slightly more surface (one more IDLE branch, one more completeness check) |
| **C** | A + Continuity CTA only (no numbered pick, just a "consider binding a propeller SKU" message) | Cheapest possible | **Rejected** — does not unlock `exact_operating_point` at all (no bind occurs), fails this contract's entire stated purpose (P2-1 unlock). Consistent with the contract's own instruction to reject C unless proven otherwise — it is not proven sufficient here, it's proven insufficient. |

**Recommend A+B** — same shape the contract sketched, confirmed appropriately scoped by the audit: A alone unlocks the walk; B is a small, low-risk addition that keeps propeller UX symmetric with motors and avoids a known asymmetry (a user who typed `hélices 5x4.5` before this ships has no path back to catalog identity without B).

---

## 8. Test + CLI probe sketch

Future test file (e.g. `tests/test_propeller_catalog_bind_ux.py`), mirroring `test_g21_catalog_bind_ux.py`'s shape:

1. `test_propeller_component_wizard_help_choose_shows_numbered_catalog` — composite `["motors","propellers"]` wizard, motors already bound → `"ayúdame a elegir"` → numbered propeller list (not the motor list, not a Brief re-show) — this is the direct regression test for §4's priority-gating fix.
2. `test_propeller_component_wizard_pick_sets_catalog_ref_and_reresolves_op` — pick → `components["propellers"].catalog_ref.family == "propeller"` AND `current_parameters["propulsion_resolution"]` (JSON, parsed) shows `resolution_type == "exact_operating_point"` when the bound motor+prop combo has a real OP row (§5's re-call, end to end).
3. `test_propeller_idle_help_choose_when_freeform_unbound` — freeform-declared propeller, IDLE `"ayúdame a elegir"` → propeller picker, not `estado`/Continuity block (B).
4. `test_propeller_idle_help_choose_noop_when_catalog_ref_set` — bound propeller → IDLE help-choose → falls through cleanly (regression guard, mirrors G21's own).
5. `test_motors_help_choose_still_wins_when_both_incomplete` — composite wizard, **both** motors and propellers incomplete → "ayúdame a elegir" → motor list (priority-order regression, proves the §4 fix didn't flip the precedent).
6. `test_freeform_propeller_never_produces_false_exact_op` — `hélices 5x4.5` freeform declare → `catalog_ref` stays `None` → `propulsion_resolution` (if any, from a prior motor bind) still shows `fallback_operating_point`/`legacy_estimate`, never `exact_operating_point` — regression guard against ever inferring identity from a freeform size string.
7. Regression: full `tests/test_g21_catalog_bind_ux.py` + `tests/test_phase2_lookup_operating_point.py` unchanged.

CLI probe sketch (`scripts/cli_probe_propeller_catalog_bind_ux.py`), extending `cli_probe_phase2_lookup_op.py`'s already-proven manual steps into real wizard turns:

```text
1. Bind emax_rs2205s_2300 via real wizard pick (as today's probe already does)
2. estado → fallback · 10.042 N
3. "ayúdame a elegir" (propellers pending, real wizard, not a state patch)
   → numbered list includes hq_5045_bn
4. Pick by number → catalog_ref set
5. estado → exact_operating_point · 9.7086 N   (no battery step needed, §6)
6. Regression: motor G21 "ayúdame a elegir" still works on a fresh project
```

---

## 9. Recommended approach

Implement Option A+B (§7) as a single Implementation Contract, structured as G21's own slices were: Slice 1 (component-wizard propeller help-choose + priority-gating fix + OP re-resolve call), Slice 2 (IDLE re-bind for freeform-unbound propellers), Slice 3 (integration + CLI probe + regression). New surface: one session field (`propeller_suggestions`), one new small module (`propeller_catalog_assist.py`, importing — not duplicating — `is_help_choose_phrase`/`match_suggestion_by_input` from `motor_catalog_assist.py`), one Brief-copy bullet extension (`acquisition_brief.py`, `key == "propellers"` alongside the existing `key == "motors"` check), the priority-gating fix in `_handle_component_description`, and the explicit re-call of `set_motor_component` after a propeller bind.

---

## 10. ★ Decisions for Engineer

1. **★1 — Suggestion authority (§3):** Option A (`match_motor_propeller` filter) with Option B (full list) as the no-motor-bound fallback; Option C confirmed unnecessary. Recommend ratify A, drop C from consideration.
2. **★2 — New module vs extending `motor_catalog_assist.py` (§3):** recommend a new `propeller_catalog_assist.py` importing the two generic reusable functions rather than growing the motor-named module. Confirm or redirect.
3. **★3 — New session field `propeller_suggestions` (§4):** confirm adding this field to `InteractiveSessionState` (a `src/` schema change — flagged for the future IC, not made here).
4. **★4 — Priority-gating fix (§4):** confirm this latent motors/propellers collision must be fixed as part of this slice (not deferred as a separate finding) — recommend yes, since a propeller help-choose block is unreachable without it in the common composite-wizard path.
5. **★5 — OP re-resolve mechanism (§5):** confirm Option 1 (explicit re-call of `set_motor_component`, no new helper) over Option 2 (new `refresh_propulsion_resolution` helper). Recommend Option 1.
6. **★6 — Scope: A+B vs A-only (§7):** confirm A+B (component wizard + IDLE re-bind) as the v1 slice. Recommend A+B.
7. **★7 — Voltage/battery sequencing (§6):** confirm the CLI walk does **not** need a battery step to reach `exact_operating_point` for the ★6 dataset — update Engineer's own mental model/any walk script accordingly.

---

## 11. Suggested Implementation Contract outline (slices only)

```text
Prop-1  InteractiveSessionState: add propeller_suggestions field (schema, additive)
Prop-2  propeller_catalog_assist.py: PropellerSuggestion TypedDict,
                 build_propeller_catalog_suggestions (Option A+B filter),
                 format_propeller_catalog_suggestions
                 (imports is_help_choose_phrase / match_suggestion_by_input
                 from motor_catalog_assist.py — no duplication)
Prop-3  orchestrator._handle_component_description: priority-gated propeller
                 help-choose block (motors-done check first, §4) +
                 _offer_component_propeller_catalog / _apply_component_propeller_catalog_pick
                 (mirrors _offer_component_motor_catalog / _apply_component_motor_catalog_pick)
Prop-4  _apply_component_propeller_catalog_pick: explicit re-call of
                 set_motor_component after set_propeller_component when
                 motors already catalog-bound (§5, Option 1)
Prop-5  orchestrator FN-005 IDLE branch: propeller re-bind when freeform/
                 unbound and motors already resolved (§4, Option B)
Prop-6  acquisition_brief.py: extend the "ayúdame a elegir" bullet to
                 key == "propellers" (mirrors G21 ★4, motors-only comment
                 updated)
Prop-7  Tests per §8 (1-7) + CLI probe extending cli_probe_phase2_lookup_op.py
                 into real wizard turns (no more test-only bind_propeller_from_catalog
                 in the probe)
```

---

**Compliance check (this investigation):** `git status --porcelain=v1 -- src/ tests/` returns empty at time of writing — no production or test files were modified in the course of this investigation.

---

**End of report.**
