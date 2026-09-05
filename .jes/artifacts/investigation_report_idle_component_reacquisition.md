# Investigation Report — IDLE component re-acquisition

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_idle_component_reacquisition.md](investigation_contract_idle_component_reacquisition.md)
**Checkpoint:** tag `v0.3.6`; live tree includes Structure block close (suite 2229+, preserved)
**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · awaiting Engineer ★ on Buy  
**Review:** [investigation_review_idle_component_reacquisition.md](investigation_review_idle_component_reacquisition.md)

Not an Implementation Contract. No `src/` edits. All reconstructions run against a `tmp_path` workspace via a real `JarvisOrchestrator` — no Engineer project was touched.

---

## A. Executive answer

**Today, a user cannot swap a bound frame/motor/battery via any assisted (catalog list) path once architecture is 4/4.** Two independent gates, both confirmed by live reconstruction:

1. **`_try_start_acquisition_from_mention` (FN-014)** returns `None` unconditionally once `_next_pending_block(project_state) is None` (`orchestrator.py:1675-1678`) — a syntactically perfect mention like `"definir frame"` is discarded before it can even consider reopening frame's COMPONENT wizard.
2. **The bare IDLE "ayúdame a elegir" chain** (`orchestrator.py:893-909`, motor → propeller → battery, **no frame step exists at all**) only offers a family when `_wants_catalog_help` is true — which is `False` once `catalog_ref` is set (`orchestrator.py:114-121`). So even the three families that *do* have an IDLE fallback chain **cannot re-offer a component that is already bound** — this is not a frame-specific gap, it is a gap in every family's re-bind story. Frame is simply the one Engineer is looking at right now because Structure just closed.

Both `"cambiar frame"` and `"definir frame"` are swallowed by `ITERATE_PATTERNS` (`intent_resolver.py:154`, which lists `cambia|cambiar` and `define|definir` in the *same* pattern) and land in the iterate wizard with a generic *"¿Qué quieres ajustar/definir?"* prompt — confirmed live, not assumed. `"ayúdame a elegir frame"` is **byte-identical** to bare `"ayúdame a elegir"` — the word `"frame"` is not parsed at all by the bare-phrase dispatcher, so it always reopens whichever family the fixed chain (motor→propeller→battery) finds something to offer for, which in a realistic project is frequently the **motor T1-underspec re-offer** (`bound_motor_sku_is_underspec`), confirmed live to fire ahead of anything frame-related in two independent fixtures. Naming the exact bound product string (`"frame Armattan Quads Rooster 5\""`) is swallowed the same way — **no path resolves a name string to a SKU bind outside the DEFINE_MISSING wizard's own free-text inference.**

**Confirmed, not hypothesized, "frankenstein" risk:** a root-only free-text rewrite of an already-bound, parts-graph-enriched frame clears the root's `catalog_ref` (correct) but leaves `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` **untouched**, now declaring materials from the *previous* SKU next to a root that names a different material entirely — reproduced live (§Reconstruction, Fixture B).

**Primary Buy: B2, frame-first** — a named-mention re-bind bridge (`"cambiar frame"`, `"ayúdame a elegir frame"`) that bypasses the `_next_pending_block is None` gate and the bound-only `_wants_catalog_help` restriction for an **explicitly named** component, reusing `_offer_component_frame_catalog`/`_apply_component_frame_catalog_pick` unchanged. Not extended to motor/propeller/battery in this thread (B3) because no existing pattern for "swap when bound" exists anywhere to mirror yet — building and proving it once for frame is the right sequencing, not a frame-specific fix.

---

## B. Know table

| Component | Catalog reopen today? | Free-text overwrite? | Iterate path? | Authority (`file:line`) |
|---|---|---|---|---|
| `frame` | **No**, once bound (`_wants_catalog_help` false) or once architecture complete (FN-014 gate) — offer/apply exist only inside an active `DEFINE_MISSING` wizard | Yes, always legal — clears `catalog_ref` by construction, orphans part children (confirmed, §Reconstruction Fixture B) | Not a registered iterate variable (`_VALID_VARIABLE_DOMAIN`, `iterate_domain.py:72`, has no `"frame"` entry) — `"cambiar frame"`/`"definir frame"` still enter iterate mode (matched by the verb alone) and get a generic, unresolvable prompt | `orchestrator.py:1646-1710` (FN-014 gate), `:2999-3049` (`_offer_component_frame_catalog`/`_apply_component_frame_catalog_pick`, IC-3), `:3255-3273` (frame's help-choose block, gated on `expected_keys`) |
| `motors` | **No**, once bound — same `_wants_catalog_help` gate. **Exception:** the T1 **underspec** re-offer (`bound_motor_sku_is_underspec`) fires even when bound, if the SKU no longer covers the current kv/prop combo — the *one* real "swap when bound" path in the codebase today, and it is need-triggered, not user-triggered | Yes | `motor_count`/`per_motor_max_thrust_n` are registered numeric iterate variables (unlike frame) — but that's a *parametric* thrust knob, not a SKU swap | `orchestrator.py:1465-1563` (`_try_start_assisted_motor_help`, includes the T1 underspec OR), `engineering_readiness.bound_motor_sku_is_underspec` |
| `propellers` | **No**, once bound | Yes | Not registered the way motor thrust is (no direct evidence of a propeller-specific numeric iterate var beyond `propeller_diameter_in`, which is param-level not catalog-level) | `orchestrator.py:1564-1595` (`_try_start_assisted_propeller_help`) |
| `battery` | **No**, once bound | Yes | `battery_capacity_wh` registered | `orchestrator.py:1597-1625` (`_try_start_assisted_battery_help`) |
| `esc`/`flight_controller`/`sensors` | No catalog for FC/sensors (control parity investigation, unchanged); ESC has a catalog+bind function but **zero** production caller of any kind (Catalog Foundation investigation finding, still true) | Yes | N/A | — |

**One universal fact, not a frame-only one:** `_wants_catalog_help(spec) = _is_stub_or_absent(spec) or spec.catalog_ref is None` (`orchestrator.py:119-121`) is the single predicate every family's IDLE/COMPONENT catalog offer is gated on, and it is **false** the instant any family is bound. No family has a "user explicitly wants to swap a bound SKU" predicate today — motor's T1 underspec re-offer is a *system*-triggered exception (the SKU stopped covering requirements), not a *user*-triggered one.

---

## C. Routing matrix (phrases × outcome)

Reconstructed live (§Reconstruction Fixture A, architecture confirmed 4/4 via `_next_pending_block(ps) is None`):

| Phrase | Mode after | Opens numbered catalog? | Honest? | Desired (proposal only) |
|---|---|---|---|---|
| `"cambiar frame"` | `ITERATE_INTERACTIVE` — *"Quieres ajustar frame del sistema actual."* | No | **Misleading** — implies frame is an adjustable parameter; it is not a registered iterate variable, so the wizard has nothing coherent to do with the answer | Should open frame's numbered catalog (same list `_offer_component_frame_catalog` already builds) |
| `"definir frame"` | `ITERATE_INTERACTIVE` — *"Quieres definir una propiedad declarativa del sistema actual."* | No | **Misleading**, same class — FN-014's mention resolution correctly identified this as a `frame` component mention (`_has_declare_verb` passes for `definir`) and was then discarded solely because architecture is complete | Same as above |
| `"ayúdame a elegir"` (bare) | `DEFINE_MISSING_PARAMETERS` — reopens the **motor** list (T1 underspec re-offer, confirmed live in two independent fixtures) | Yes, but for the wrong family | **Honest about motors, silent about frame** — the user gets a real catalog list, just never the one for the component Structure just closed | Unchanged for the bare, unnamed phrase — this is arguably correct triage behavior when something *is* genuinely wrong elsewhere |
| `"ayúdame a elegir frame"` | Identical to the row above, **byte-for-byte** | Yes, same wrong family | **The word "frame" is silently discarded** — confirmed live: the message, mode, and action are identical whether or not `"frame"` is appended | Should route to `_offer_component_frame_catalog` specifically when the phrase names frame |
| `"frame Armattan Quads Rooster 5\""` | `DEFINE_MISSING_PARAMETERS` — reopens the **motor** free-text prompt (*"Vamos a definir los motores..."*) | No | **Misleading** — the exact display name of a real catalog SKU is typed and silently discarded because an unrelated wizard (motors) currently owns `expected_keys` | Should resolve to `bind_frame_from_catalog` when the text matches a known frame SKU/model closely, or explicitly say "no reconozco esa referencia, prueba 'ayúdame a elegir'" |

---

## D. Gate analysis

```text
User types "definir frame" (architecture already 4/4, frame bound)
  │
  ├─ IDLE mode? yes
  │
  ├─ FN-005 bare help-choose phrase? "definir frame" is not in HELP_CHOOSE_PHRASES → no
  │
  ├─ FN-014 _try_start_acquisition_from_mention(user_input):
  │     _next_pending_block(project_state) → None  (architecture complete)
  │     pending_block_key is None → RETURN None IMMEDIATELY
  │     (never even calls resolve_acquisition_mention — the mention
  │      resolver that WOULD have correctly identified "frame" as a
  │      component mention is never reached)
  │
  ├─ falls through orchestrator.py's IDLE dispatch to intent_resolver.resolve_intent(...)
  │
  ├─ ITERATE_PATTERNS matches "definir" (same pattern group as "cambiar")
  │     → intent = "iterate"
  │
  └─ iterate wizard opens with "frame" as an unrecognized/unregistered
     variable → generic, unresolvable prompt (confirmed live)
```

For `"ayúdame a elegir frame"`, the chain is shorter and the gate is different:

```text
FN-005: is_help_choose_phrase("ayúdame a elegir frame") → True
  (HELP_CHOOSE_PHRASES soft-matches "ayudame" + "elegir" — the trailing
   "frame" token is never inspected by this predicate at all)
  → _try_start_assisted_motor_help() called FIRST, unconditionally
    → bound_motor_sku_is_underspec(project_state) → True (in both
      reconstructed fixtures) → returns the motor list, claims the turn
  → _try_start_assisted_propeller_help() / _battery_ never even called
    (short-circuited by "assist is not None")
```

`"frame"` never enters this decision at any point — the function that receives the phrase (`is_help_choose_phrase`, then `_try_start_assisted_motor_help`) has no parameter for "which component," only "is this a help-choose phrase at all."

---

## E. Buy recommendation

**B2, frame-first.**

```text
| Option | Verdict |
|---|---|
| B0 (docs only) | Rejected — leaves a reproduced, confirmed dead-end (both "cambiar frame" and "ayúdame a elegir frame" mislead) undocumented for a fix. |
| B1 (copy-only) | Rejected as primary — the underlying capability gap is real and cheap to close (§H); copy-only would tell the user the truth ("no puedo reabrir el frame") without fixing the actual, small missing bridge. Worth doing anyway as a fallback message for the small residual of names Jarvis still can't resolve (see §H tests). |
| **B2 (frame-first named-mention rebind bridge)** | **Recommended.** Two small, independent additions bypass the two gates found in §D: (a) `_try_start_acquisition_from_mention`'s early return on `pending_block_key is None` needs a narrow exception for an *explicitly named, already-satisfied* component (not blocks in general — never reopens propulsion/energy at random); (b) a frame-specific IDLE dispatch that fires on `"cambiar frame"`/`"definir frame"`/`"ayúdame a elegir frame"`/`"frame <sku or name>"` and calls the **already-shipped** `_offer_component_frame_catalog`/`_apply_component_frame_catalog_pick` (Catalog Foundation IC-3) — no new offer/apply logic, only a new way to reach the existing one. |
| B3 (extend to all 4 families) | Rejected for *this* thread, not forever — §B's Know table shows **no family** has a working "swap when bound" UX today, so there is no proven, battle-tested pattern to generalize yet. Building it once for frame, shipping it, and confirming it in a field walk (per the contract's own success signal) is the right sequencing before touching three more dispatch sites. |
| B4 (teach iterate about "componentes") | Rejected — heavier than B2 for the same outcome; iterate's job is parametric knobs (`motor_count`, `battery_capacity_wh`), not SKU identity swaps, and teaching it to redirect to a catalog list duplicates B2's bridge inside a different subsystem. |
| B5 (soft coherence note, arms↔motors) | **Secondary, not primary — see §Coherence fork below.** |
```

---

## Coherence fork (governing question 5)

**Default lean confirmed: debt / B0.** I could not construct a Continuity-only warning sentence for "DSE set `motor_count=3` while frame declares `└ arm ×4`" that survives the same test the earlier Structure investigations already applied: would a reasonable reader take it as *"Jarvis checked this and something's wrong"* (a validation claim) rather than *"these two independently-declared facts happen to differ"* (a neutral observation)? Any phrasing that names both numbers side-by-side in the same sentence reads as a mismatch **finding**, which is exactly the `arm_count`↔`motor_count` claim-closing cross-check Structure B's own investigation forbade twice already (parts-graph report §5, Structure-A-pass-meaning report). A note that *doesn't* name both numbers together has nothing left to say. This is not a wording problem solvable with more careful copy — it's structural: the moment Jarvis states a relationship between the two counts, it has performed the forbidden check, regardless of how hedged the sentence is. **Stays debt (B0) for this thread; not recommended even as a small parallel addition.**

---

## F. Rebind semantics (Buy = B2)

On a catalog re-pick after a prior bind (either catalog-bound or free-text):

- **Root:** `catalog_ref`/`mass_kg`/`material`/`size_class_inch`/`wheelbase_mm`/`configuration` all **replace** the prior values — this is `_apply_component_frame_catalog_pick`'s existing behavior (Catalog Foundation IC-3), unchanged, already correct (each `set_frame_material` call rebuilds a fresh `ComponentSpec`).
- **`frame_*` children:** on a **catalog re-pick**, `_apply_component_frame_catalog_pick` already calls `frame_part_specs_from_catalog(new_sku)` and `upsert_frame_part` for whatever the *new* SKU declares (Structure B Parts Graph IC) — but `upsert_frame_part` **merges onto an existing child rather than replacing it** (`component_writers.py`, `upsert_frame_part`'s own docstring: "merges onto any existing child spec"). Re-picking Armattan → TBS (which has no part fields) would therefore **not clear** the Armattan-sourced `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` — they would survive, orphaned, exactly like the free-text case in §Reconstruction Fixture B. **This is the same G-N4-class gap, reachable through the *catalog* path too, not just free-text** — a fact this investigation surfaces but does not fix.
- **Recalc/sim:** confirmed unchanged — `_apply_component_frame_catalog_pick` does not recalculate (same posture as battery/propeller picks, per its own docstring); a rebind would leave stale `latest_results` exactly as any other component pick does today, requiring an explicit `"calcular"`/`"simular"` afterward. No new physics implied by rebind.

**In-scope note vs. defer:** the *catalog-repick* half of G-N4 (children not cleared on cross-SKU rebind) is a small, one-line consequence of B2 reusing the existing apply path unchanged — if B2 ships, Cursor's later IC should decide explicitly whether to clear part children when the new SKU's `frame_part_specs_from_catalog` returns a different (or empty) set, rather than silently merging stale ones. This investigation does **not** expand into a standalone orphan-cleanup IC per the contract's own instruction — it is named here as a one-line policy decision the B2 IC must make, not a separate thread.

---

## G. Explicit non-goals confirmed

- No Structure PASS meaning reopened — `_structure_evidence`/`_derive_subsystem_verdict` were not read for any behavioral change, only cited for context already established.
- No `arm_count`↔`motor_count` claim-closing cross-check — explicitly rejected again in the Coherence fork above.
- No MEASURE/CAD/FEA.
- No FC/sensor catalog, no H5, no Conversation Engine.
- No Structure geometry/parts-graph ontology reopen — Fixture B only *exercises* the existing parts graph to prove the orphan risk; no new node/edge type is proposed.
- No DSE scoring rewrite.
- No orphan-cleanup IC proposed standalone — folded into §F as a one-line policy note for the B2 IC.
- No version bump.

---

## H. IC skeleton (Buy = B2, frame-first — not an Implementation Contract)

- **Files (illustrative):** `src/jarvis/core/orchestrator.py` — (a) a narrow exception in `_try_start_acquisition_from_mention` (or a new sibling check called before its early return) that, when `pending_block_key is None` but the mention names a component that already exists and is catalog-family-eligible (frame only, in this slice), still resolves to a **rebind** action instead of returning `None`; (b) a frame-specific check alongside the existing FN-005 bare-phrase block, so `"ayúdame a elegir frame"`/`"cambiar frame"`/`"definir frame"` route to `_offer_component_frame_catalog` (reused unchanged) rather than falling to iterate or being swallowed by another family's underspec re-offer.
- **Behavior change:** three named phrases regain a working frame catalog reopen after 4/4 and after bind; free-text override and iterate's existing (registered) variables are untouched; no other family's dispatch order changes.
- **Tests:** each of the five reconstructed phrases from §Reconstruction Fixture A, asserted against the *fixed* behavior (numbered list opens, correct SKU binds on pick); a regression proving unnamed `"ayúdame a elegir"` still triages motor-underspec first (§D's second chain is a feature, not a bug, and must not regress); a regression proving `"cambiar motor"`/`"cambiar batería"` are **unchanged** (still route to iterate, B3 not silently included).
- **Forbidden:** extending this bridge to motors/propellers/battery (B3, separate future thread); any `arm_count`/`motor_count` cross-check; any Structure PASS/evidence change; any new physics on rebind; silently deciding the §F children-orphan policy without a one-line explicit statement in the IC itself.

---

## Reconstruction (fixtures, run against `tmp_path`, not an Engineer workspace)

**Fixture A** — motors (catalog-bound), propellers (catalog-bound), battery (catalog-bound), frame (`armattan_rooster_5in`, catalog-bound with parts graph), ESC/FC/sensors declared, `system_blocks`/`system_priority` = all four aerial blocks, `motor_count`/`per_motor_max_thrust_n`/`battery_capacity_wh`/`motor_power_w` set so `_next_pending_block(project_state)` returns `None` (confirmed). Exact outputs are quoted verbatim in §C.

**Fixture B** — same bound+parts-graph frame; a root-only free-text rewrite (`set_frame_material(ps, 0.5, "aluminio", 7.0)`, no `catalog_ref`) clears the root's `catalog_ref` (correct) but leaves all four `frame_*` children declaring the *original* Armattan materials (`fibra de carbono`/`titanio`/`aluminio` for arm/plate/cage/standoff respectively) — reproduced and quoted verbatim in §A/§F.

**Fixture C (code-cited, not re-executed):** `_try_start_assisted_battery_help` (`orchestrator.py:1597-1625`) uses the identical `_wants_catalog_help` gate as frame's own offer path — structurally guaranteed to behave the same way (bound → no re-offer) without needing a separate live run; cited directly rather than duplicating the same proof.
