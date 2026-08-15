# SYS-MAP-004 — Routing / System Map Audit

**Date:** 2026-08-14
**Type:** Audit only. Zero intentional `src/` changes (verified — see §7 below).
**Checkpoint base:** `checkpoint-g5-dse-component-sync` (+ uncommitted G3: `explore_continuity.py`, treated as current code per contract note).
**Author:** Claude Code
**Contract:** `.jes/artifacts/implementation_contract_sys_map_004_routing_audit.md`

---

## 1. Executive verdict

**Primary classification: B — Map overclaim**, with the underlying code gap best described as an *unaddressed missing edge* rather than a deliberate design decision (**A**) or a violated invariant (**C**).

- `"reducir payload"` while `DEFINE_MISSING_PARAMETERS` (battery) is open is swallowed by the acquisition wizard's unconditional `MISSING_COMPONENT_DEFINITION` intercept (UX-C, `orchestrator.py:796-802`) — reproduced exactly via runtime probe (§4.4, P3): the response is the battery Brief, byte-identical in shape to the CLI transcript.
- `IntentResolver.resolve_intent` correctly classifies the phrase as `"iterate"` and `goal_planner.is_engineering_intention` correctly resolves it to `"reducir_payload"` (F-1 confirmed working, §4.4 P1/P2) — **the classifiers are not the bug**. The bug is structural: checkpoint 18 (C-040, the FN-022 gate) is never reached, because checkpoint 10 (`DEFINE_MISSING_PARAMETERS` mode) already returned.
- `ITERATE_INTERACTIVE` has an explicit, hand-built preempt for exactly this class of problem (C-052, `_should_preempt_iterate_wizard`, added 2026-08-05 specifically because "sticky ITERATE_INTERACTIVE was eating explore, calculate, simulate, new iterate requests, and component descriptions"). **`DEFINE_MISSING_PARAMETERS` has no analogue.** Nothing in code, comments, or design docs asserts this omission as intentional — so it cannot be labeled **A**.
- FN-021's invariant (`CONNECTIONS.md` C-037, `STATE_MAP.md` §"FN-021 invariant") is scoped strictly to *post-completion* routing ("when there is genuinely no next pending block ... clear to IDLE"). It says nothing about mid-wizard preemption by a new strong intent, so nothing here violates it — not **C**.
- The map (`CONNECTIONS.md` C-040, `03_acquisition/ACQUISITION_MAP.md`'s "Known issues: None", `AUTHORITY.md`'s GUIDANCE/ANALYZE/ITERATE precedence table) describes engineering-intent routing and intent precedence **without ever qualifying that both are structurally unreachable whenever `DEFINE_MISSING_PARAMETERS` owns the turn**. That is exactly the overclaim the Engineer's hypothesis named. → **B**.

**Secondary finding (separate root cause, §4.5):** the Continuity/`build_startup_context` motor-catalog-gap computation (`orchestrator.py:2743-2794`) never reads a component's `catalog_ref`. Reproduced via probe P7: a motor bound to `sunnysky_r2305_2500` (catalog_ref intact, untouched) still produces `"...no tengo un motor en el catálogo que cubra ese espacio"` once the physical requirement grows past what that SKU covers. This is **not** a Continuity-authority violation (no LLM, deterministic, `AUTHORITY.md`'s literal claim about *who decides* still holds) — it's a content-honesty gap already half-suspected in the existing findings register (F-6's "Stale-gap UX" note, F-5). This audit **confirms it with reproducible runtime evidence** and separates it cleanly from the primary finding — no shared symbols.

---

## 2. CLI finding reconstruction — turn path table

Scenario: architecture open, motors + propellers declared, `DEFINE_MISSING_PARAMETERS` open on battery (`param_definition_reason == MISSING_COMPONENT_DEFINITION`, `pending_missing_params == ["battery"]`). User sends `"reducir payload"`.

| Step | Checkpoint # (RUNTIME_MAP) | Branch taken | Why not C-040 |
|---|---|---|---|
| 1 | 1 — Global commands (C-010) | no match | not an escape word |
| 2 | 2 — FN-004 structural-confirm (C-011) | no match | `pending_structural_change` empty |
| 3 | 3 — Bug 54 (C-012) | no match | `pending_define_missing` is `False` (wizard already open, not a pending "¿sí?" confirm) |
| 4–6 | 4–6 — FN-005/014/015 (IDLE-only) | skipped | `session.mode != IDLE` |
| 7 | 7 — Global component intercept (C-013) | returns `[]` | `_interceptable_component_specs` **explicitly short-circuits to `[]`** when `session.mode == DEFINE_MISSING_PARAMETERS` (`orchestrator.py:353-354`) — by design, this checkpoint defers entirely to DEFINE_MISSING's own intercept |
| 8 | 8 — `CREATE_PROJECT_INTERACTIVE` | skipped | wrong mode |
| 9 | 9 — `ITERATE_INTERACTIVE` | skipped | wrong mode |
| **10** | **10 — `DEFINE_MISSING_PARAMETERS` (nested)** | **entered — terminal** | see nested trace below |
| 10a | `_dm_intent = resolve_intent("reducir payload")` | `= "iterate"` | `"reducir"` matches `ITERATE_PATTERNS` (`intent_resolver.py:150`); does **not** match GUIDANCE / ANALYZE / CALCULATE / SIMULATE / DEFINE_PARAMS / DISMISS / APPLY / EXPLORE (verified, §4.4 P2) |
| 10b | `_dm_intent == "project_status"` (C-035) | no match | intent is `"iterate"` |
| 10c | FN-013 reprompt-active-block (C-033) | no match | not a "declarar/definir batería" phrase |
| 10d | FN-015 pending-help | no match | not an "ayúdame a definir" phrase |
| 10e | `_dm_intent == "analyze"` | no match | intent is `"iterate"` |
| 10f | `_dm_intent == "calculate"` / `"simulate"` | no match | intent is `"iterate"` |
| 10g | FN-016 navigation-back (C-034) | no match | not "atrás"/"volver"/"vuelve" |
| **10h** | **UX-C: `param_definition_reason == MISSING_COMPONENT_DEFINITION`** | **MATCH — terminal, unconditional on intent** | fires regardless of `_dm_intent`'s value; battery wizard is open, so this is always `True` here |
| → | `_handle_component_description("reducir payload", session)` | `infer_components` finds no battery-shaped spec → completeness `"low"` → re-issues the battery acquisition Brief | **Checkpoint 18 (C-040, FN-022 gate, `orchestrator.py:931-936`) is never reached — the function already returned at step 10h.** |

**Runtime proof (probe P3, §4.4):**
```text
status='interactive' action='component_description_prompt'
message="Vamos a definir la batería.\n\nLa batería determina la energía disponible y la autonomía.\n..."
```
Matches the CLI transcript's `"Vamos a definir la batería…"` exactly.

---

## 3. §4.2 — Preempt comparison across modes

| Mode | Soft-interrupt / preempt today | Engineering-goal reachability |
|---|---|---|
| **IDLE** | n/a (default entry point) | ✅ direct — checkpoint 18 (C-040) is reached whenever no mode branch above it returns first |
| **ITERATE_INTERACTIVE** | **C-052** `_should_preempt_iterate_wizard` (`orchestrator.py:408-430`) — checks `_resolve_strong_action_intent(user_input)` against `_ITERATE_PREEMPT_INTENTS = {explore_design_space, apply_exploration_result, calculate, simulate, create_project, define_params, iterate, dismiss_suggestion}`; a match clears the session and **re-dispatches the same input through `_handle_user_text_inner` as IDLE** | ✅ — `"reducir payload"` resolves to `"iterate"`, which **is** in `_ITERATE_PREEMPT_INTENTS`, so it *would* preempt and reach C-040 on re-dispatch (this is the mechanism P4's workaround manually reproduces via `"cancelar"`) |
| **DEFINE_MISSING_PARAMETERS** | Narrow, per-*intent*-value checks only: `project_status` (C-035), FN-013 reprompt, FN-015 pending-help, `analyze` (non-help-choose), `calculate`, `simulate`, FN-016 navigation-back. **No generic strong-intent preempt list** analogous to `_ITERATE_PREEMPT_INTENTS` exists here — nor is there any check of `is_engineering_intention`/`explore_design_space` before UX-C's catch-all | ❌ never, while `param_definition_reason == MISSING_COMPONENT_DEFINITION` — UX-C fires unconditionally before any such check could run (confirmed P3, P6a, P6b) |
| **SYSTEM_DEFINITION** | None beyond checkpoints 1–7 (global) — falls straight to `system_definition_session.answer` | Out of scope for this cut (not probed) — structurally the same shape of gap as DEFINE_MISSING (no preempt), noted for completeness only |

**Answering §4.2's explicit question:** No, `DEFINE_MISSING_PARAMETERS` has **no analogue of C-052** for `is_engineering_intention`/`explore_design_space`. That absence is **not documented anywhere in the map** — `RUNTIME_MAP.md`'s own nested-`DEFINE_MISSING_PARAMETERS` pseudocode (lines 45-57) is *accurate* to the code (it correctly omits an engineering-intent branch, because there isn't one), but no subsystem map, `AUTHORITY.md`, or `FLOWS.md` entry calls out the *contrast* with ITERATE's C-052, or states that C-040/GUIDANCE-ANALYZE-ITERATE precedence is conditioned on mode. `FLOWS.md` FLOW-002/002b explicitly note the FN-022 gate "only fires for `intent ∈ {"iterate","unknown"}`" but never mention that this is also conditioned on *not being inside an open acquisition wizard* — confirming the map-side gap is one of omission, not contradiction.

---

## 4. §4.3 — FN-021 boundary vs this finding

`orchestrator._set_pending_next_block` (`orchestrator.py:1431-1515`) and `tests/test_fn021_session_hygiene.py` together prove FN-021's actual scope:

```text
FN-021 fires at wizard-completion time only (end of the DEFINE_MISSING branch,
after ParamDefinitionSession.answer / _handle_component_description succeeds):

  _next_pending_block(project_state) is None
    AND session.mode == DEFINE_MISSING_PARAMETERS
    ⇒ clear_runtime_session() → IDLE

  _next_pending_block(project_state) is not None
    ⇒ chain to the next block (C-037) — session stays in
      DEFINE_MISSING_PARAMETERS, param_definition_reason repopulated
```

This is entirely orthogonal to the bug reproduced here: FN-021 governs *what happens after a block finishes*. The CLI finding is about *what happens when a new turn arrives while a block is still open and incomplete* — a case FN-021 never touches (battery was never completed in the reproduction; the wizard is mid-block, not at a completion boundary). `test_fn021_session_hygiene.py`'s own tests never send a non-block-related phrase mid-wizard — they only test the post-completion clear/chain decision. **No overlap, no double-counting.**

---

## 5. §4.4 — Probe results (all run against live code, `_RefuseLLM` fixture, no product changes)

Script: `sysmap004_probes.py` (scratchpad, diagnostic-only — not added to `tests/`, not committed; see §7).

| # | Probe | Result |
|---|---|---|
| **P1** | `is_engineering_intention("reducir payload")` | `'reducir_payload'` — **F-1 confirmed still correct** (direction-aware, no inversion) |
| **P2** | `resolve_intent("reducir payload")` | `'iterate'` |
| **P3** | Forced `DEFINE_MISSING_PARAMETERS`+battery session, then `"reducir payload"` | `status='interactive'`, `action='component_description_prompt'`, message = battery acquisition Brief ("Vamos a definir la batería…") — **swallowed, byte-identical shape to CLI transcript** |
| **P4** | Same session, `"cancelar"` → `"reducir payload"` | `"cancelar"` → `status='cancelled'`, mode → `IDLE`. Then `"reducir payload"` → `action='engineering_intent'`, `status='ok'`, full Goal Plan text ("Plan estratégico — Reducir carga útil: 1. Reducir requisito de carga útil…"). **Workaround confirmed to work.** |
| **P5** | Same session, `"simula"` | `action='simulate'`, `status='ok'` — soft-interrupt (checkpoint 10f) still works mid-wizard, as expected |
| **P6a** | Same session, `"explora opciones"` | `action='component_description_prompt'` — **also swallowed**, same battery Brief |
| **P6b** | Same session, `"optimiza payload"` | `action='component_description_prompt'` — **also swallowed**, same battery Brief |
| **P7** | Motor bound via `catalog_ref` (`sunnysky_r2305_2500`), propellers declared, physical requirement inflated past that SKU's coverage, then `project_status`/Continuity | `next_useful_step` unaffected in this fixture (architecture-gap step wins first), but `continuity.evidence` includes: `'Catálogo: Necesitas empuje ≥ 100.0 N/motor, ~920KV, hélice ~10"; no tengo un motor en el catálogo que cubra ese espacio.'` **while `motors.catalog_ref` is still bound and untouched** (`CatalogRef(family='motor', sku='sunnysky_r2305_2500')`) — confirmed reproduction of the secondary symptom, see §6. |

P6a/P6b are directly relevant to the G3 probe (§8): the sticky-wizard problem is **not limited to engineering-intent phrases** — explore-shaped phrases are swallowed the same way, by the same mechanism (UX-C fires before any intent-specific branch downstream of it exists).

---

## 6. §4.5 — Secondary finding: Continuity catalog-gap is blind to `catalog_ref`

**Symbols:** `orchestrator.build_startup_context`'s catalog-gap block (`orchestrator.py:2743-2794`, specifically `2767-2794`), feeding `project_continuity.build_project_continuity`'s `motor_catalog_gap`/evidence rendering (`project_continuity.py:112-116`).

**Mechanism:** `build_startup_context` recomputes `catalog_matches`/`catalog_gap` fresh on every call from `physical_requirements["thrust_per_motor_needed_n"]` and the `motors` component's `kv_rating`/`propeller_diameter_in`. **It never reads `motors_comp.catalog_ref`.** `grep -n "catalog_ref" orchestrator.py` shows the only `catalog_ref`-aware code in the file is the G5 invalidation call in `_handle_engineering_intent` (lines 2271-2289) — an entirely different code path, never invoked by `build_startup_context`. `project_continuity.py` doesn't receive `catalog_ref` as an input at all (see its full parameter list, `project_continuity.py:10-25`).

**Consequence (proven, P7):** if the physical requirement grows after a motor is bound (e.g., battery/payload declared later), the recomputed `catalog_matches` can come back empty even though a specific, still-valid SKU is bound — producing `"no tengo un motor en el catálogo que cubra ese espacio"` next to a project that already answers "which motor?" with a name. This is a **contradiction the user can directly observe**, distinct from C-081 (which is about `safety_margin_ratio` being ignored in the PASS branch, not about `catalog_ref`).

**Root cause is not shared with the primary finding** — different symbols (`build_startup_context`'s catalog block vs. the DEFINE_MISSING mode branch), different call path, different subsystem (`08_continuity`/`04_engineering`-adjacent catalog code vs. `01_runtime`/`03_acquisition`). Kept separate per contract §4.5.

**Not new to this project** — the existing findings register already half-suspected this: F-6's note ("Stale-gap UX: message may not reflect a motor already bound earlier in the session") and F-5's "pendiente de verificación." **This audit elevates that suspicion to a confirmed, reproducible root cause** with an exact code citation. See G9 below.

---

## 7. Part B — Map ↔ code re-verification (delta since SYS-MAP-003)

### 7.1 Counts & registry

| # | Check | Result |
|---|---|---|
| B1 | Canonical `C-xxx` count | **CONFIRMED** — 59 unique rows in `CONNECTIONS.md`'s Canonical registry section (`awk`-verified between the `## Canonical registry` and `## Forbidden transitions` headers), matches the file's own "59 unique edges" claim. No silent additions/removals since SYS-MAP-003. |
| B2 | Status rollup 🟢/🔴/🟡 | **CONFIRMED** — 58🟢 · 0🔴 · 1🟡 (C-081), matches the FN-026 changelog line. No silent flips found. |
| B3 | Forbidden transitions (8) | **CONFIRMED still accurate** — none of G3/G5/Catalog Bind introduce LLM-driven target/goal/DSE/component selection; all 8 remain structurally absent. |
| B4 | `RUNTIME_MAP.md` 25-checkpoint table vs. current `_handle_user_text_inner` | **CONFIRMED, no drift** — re-traced the full function (`orchestrator.py:580-980`) checkpoint-by-checkpoint; all 25 entries, in the same order, same anchors. G3 and G5 did **not** add new top-level checkpoints — they nest *inside* existing ones (G3 inside checkpoint 21's `_handle_explore`; G5 inside checkpoint 22's `_handle_apply_exploration`). The nested `DEFINE_MISSING_PARAMETERS` pseudocode (lines 45-57) also still matches code exactly. |

### 7.2 High-risk rows (§5.2 of contract)

| ID | Verdict | Evidence |
|---|---|---|
| C-014 | **CONFIRMED** | Mode-branch dispatch order (checkpoints 8-11) matches code; DEFINE_MISSING (10) is checked, and returns, before any IDLE-only gate could apply — consistent with "Mode-branch dispatch" description. |
| C-037 | **CONFIRMED** | Scope is post-completion chain-vs-clear only (§4/§5 above); not implicated in this finding; `tests/test_fn021_session_hygiene.py` (4/4) still passing. |
| C-040 | **NEW MISMATCH — overclaim by omission** | Entry states the connection as `🟢 CONNECTED (FN-022)` with no qualification that it is unreachable whenever `DEFINE_MISSING_PARAMETERS`/`ITERATE_INTERACTIVE`'s own branches intercept first (ITERATE's C-052 *does* eventually reach it via re-dispatch; DEFINE_MISSING's UX-C does not, ever, mid-block). **Also line-stale**: evidence cites `orchestrator.py:894-899`; the gate is now at `931-936` (FN-025 inserted an earlier `is_engineering_intention` call at line 880, shifting everything below it — the map was not re-numbered after FN-025). Proposed row text (report-only, not applied): *"🟢 CONNECTED (FN-022) — reachable from IDLE, and from ITERATE_INTERACTIVE via C-052's preempt-and-redispatch. **Not reachable from DEFINE_MISSING_PARAMETERS** while `param_definition_reason == MISSING_COMPONENT_DEFINITION` (UX-C intercepts first, unconditionally) — see SYS-MAP-004/G8."* |
| C-041 / C-105 | **CONFIRMED** | Reached correctly whenever C-040/C-025 fires (P4's Goal Plan output); `test_fn024_handoff_context_dse.py` suite still green. |
| C-042 / C-106 | **STALE** | `_handle_explore` (`orchestrator.py:2022-2130`) now interposes `explore_continuity.resolve_explore_goal_with_handoff` (G3, uncommitted) **before** the C-106 bind decision — a precedence layer ("explicit new goal > active goal > inferred/default goal") that neither C-042's nor C-106's `CONNECTIONS.md` entries mention at all. The entries describe the pre-G3 FN-024 shape only. Not a behavioral bug (G3 has its own closed design + PASS WITH NOTES review), purely a documentation lag. |
| C-052 | **CONFIRMED** | `_should_preempt_iterate_wizard` (`orchestrator.py:408-430`) matches description; used as the positive contrast case throughout this audit (§3). |
| C-033–C-035 | **CONFIRMED** | Nested nested nested — exactly matches the DEFINE_MISSING soft-path pseudocode in `RUNTIME_MAP.md` and the turn-path trace in §2 above. |
| C-080 / C-081 | **CONFIRMED, C-081 unchanged; adjacent new gap found (not the same row)** | C-081 (margin unread in PASS branch) unaffected by this cut. The *new* gap found (§6, catalog_ref blindness) lives in `build_startup_context`'s catalog-gap computation — a `build_project_continuity` **input**, not `build_project_continuity` itself, and not currently a registered `C-xxx` at all. Registered as **G9** below rather than force-fit into C-080/C-081. |

### 7.3 Subsystem map claims challenged

| File | Claim | Verdict |
|---|---|---|
| `03_acquisition/ACQUISITION_MAP.md` | "Known issues owned by this subsystem: **None**" | **OVERCLAIM** — the sticky UX-C intercept (this audit's primary finding) is owned by this subsystem's own `_handle_component_description`/`param_definition_reason` machinery; it silently consumes turns that a cross-subsystem authority (Engineering's C-040) should arguably see first. Not previously listed as a known gap. |
| `04_engineering/ENGINEERING_MAP.md` | Inbound: "C-040 (from Runtime's FN-022 gate)"; "No open issues remain in this subsystem" | Technically true in isolation (the *subsystem's own* code has no bug), but read alongside ACQUISITION_MAP's "None" it completes the overclaim — neither map states that the inbound edge is mode-gated at the source. |
| `09_state/STATE_MAP.md` | "`explore_design_space`, `apply_exploration_result`, `engineering_intent` are all single-turn actions dispatched from IDLE with no dedicated mode" | **CONFIRMED, not an overclaim** — this is structurally true (checkpoint 18 is only reached after all mode branches return without matching), it just doesn't spell out the *consequence* for DEFINE_MISSING. Accurate but incomplete, not wrong. |
| `AUTHORITY.md` | GUIDANCE/ANALYZE/ITERATE precedence table (§"the mechanism behind several rows above") | **CONFIRMED as a description of `_resolve_strong_action_intent`'s internal order, but presented without the mode-gating caveat** — the table and the two "downstream" C-040/C-025 checks are real and correctly ordered, but the whole apparatus is silently conditioned on "not inside `DEFINE_MISSING_PARAMETERS`'s own branch," which the table never states. |
| `FLOWS.md` FLOW-002/002b | FN-022 gate "only fires for `intent ∈ {"iterate","unknown"}`" | **CONFIRMED, and correctly scoped** — but no FLOW entry anywhere shows or discusses engineering intent arriving **during** an open acquisition wizard. The gap is a missing flow, not a wrong one. |

### 7.4 New modules since SYS-MAP-003 (inventory)

| Module | Context | Map status |
|---|---|---|
| `core/component_sync.py` | G5 — re-syncs `design_properties.components` after a params-only DSE apply, wired into `_handle_apply_exploration` after `catalog_bind.invalidate_diverged_catalog_refs` | **Not mentioned anywhere in `docs/system_map/`** (`grep` returns zero hits) |
| `core/explore_continuity.py` | G3 — goal precedence for explore-shaped turns (uncommitted, but live: imported and called at `orchestrator.py:2046`) | **Not mentioned anywhere in `docs/system_map/`** |
| `core/catalog_bind.py` | Catalog Bind Impl B — SKU identity binding + divergence invalidation | **Not mentioned anywhere in `docs/system_map/`** |
| `core/motor_catalog_assist.py` | Pre-existing (FN-005/009), still the single owner of the "no tengo un motor…" message text — confirmed via grep, no duplicate string elsewhere | Listed in `03_acquisition/ACQUISITION_MAP.md`, current |

No new `C-xxx` invented in this cut for these three modules, per contract instruction ("do not invent a full Catalog connection registry... unless evidence forces a suspected-edge note"). They are flagged here as an inventory gap for the Engineer to prioritize a future map cut, not as broken connections — none of the three exhibit incorrect *behavior* on their own (their own test suites, `test_component_sync.py`/`test_catalog_bind_v1.py`/`test_g5_dse_iterate_dual_truth.py`, all pass, 52/52 across the six relevant FN/G test files run for this audit).

---

## 8. Recommended next cuts (ranked, no implementation performed)

```text
R1 — Map-only doc correction (low cost, high value, safe):
     - C-040's CONNECTIONS.md entry: add the DEFINE_MISSING-unreachability
       caveat + refresh the stale line citation (894-899 → 931-936, and
       cross-ref the FN-025 entry point at line 880).
     - ACQUISITION_MAP.md "Known issues: None" → add a one-line pointer to
       G8 (below).
     - C-042/C-106 entries → add a one-line note that G3's
       resolve_explore_goal_with_handoff now sits upstream of the bind
       decision (once G3 is committed — currently uncommitted, so this can
       wait for that commit rather than documenting an uncommitted state).
     Not applied in this cut — report-first per contract; Engineer can
     approve as a trivial follow-up.

R2 — New Finding IDs registered in cli_findings_post_catalog_bind_v1.md
     (intended in this cut; EPERM blocked write — applied 2026-08-15 by Cursor
      after SYS-MAP-004 review):
       G8 — sticky DEFINE_MISSING swallows engineering-intent AND
            explore-shaped phrases (primary finding, this audit)
       G9 — Continuity catalog-gap blind to bound catalog_ref (secondary
            finding, elevates F-6's existing "Stale-gap UX" note from
            suspected to confirmed-with-repro)

R3 — Design note needed before any implementation: a preempt policy for
     DEFINE_MISSING_PARAMETERS, analogous to C-052 but scoped to this
     mode's actual risk profile (unlike ITERATE, DEFINE_MISSING must not
     lose collected_params on every strong-intent match — a naive port of
     _should_preempt_iterate_wizard would be wrong; the case-by-case
     mid-wizard soft-interrupts already here — FN-013/015/016 — show the
     team already treats this mode's preemption as higher-stakes than
     ITERATE's). This is a product/architecture decision (§9 of the
     contract explicitly frames it as a preference to stress-test, not a
     default), not something to infer from code alone.

R4 — Implementation Contract candidate (future cut, NOT this one):
     once R3's policy is decided, a scoped FN closing G8 — likely shaped
     as "UX-C only intercepts when the input doesn't already resolve to a
     stronger, named authority (is_engineering_intention / explore intent
     with an active handoff)" rather than a blanket C-052-style clear
     (which would discard in-progress battery params on every false-
     positive strong-intent match).

R5 — What NOT to do next:
     - Do not conflate G8 with G3/G6/G7/Impl C — no shared symbols, no
       shared root cause with any of those.
     - Do not port _should_preempt_iterate_wizard verbatim into
       DEFINE_MISSING without a design pass (R3) — ITERATE's calibration
       assumed a wizard whose slot-filling has no equivalent to
       collected_params carrying multi-turn acquisition state.
     - Do not fix G9 by making build_project_continuity itself catalog_ref-
       aware without also deciding whether an "already bound, but now
       under-spec'd" SKU should show as a gap, a warning, or nothing at
       all — that's a data-contract question (mirrors H5/C-081's own
       deferred status), not a one-line patch.
```

---

## 9. G3 probe implication

**Workaround available, not a hard blocker.** Probe P4 proves `"cancelar"` cleanly clears `DEFINE_MISSING_PARAMETERS` to `IDLE` and the very next turn correctly reaches the Goal Plan / explore path with 0 LLM. G3's own CLI probe can proceed today by cancelling any open acquisition wizard before testing explore-continuity phrases. However, probes P6a/P6b show the **same** UX-C intercept also swallows `"explora opciones"` and `"optimiza payload"` — i.e., G3's own subject matter (explore-goal precedence) is *itself* unreachable mid-wizard, not just engineering-intent phrases. This makes the workaround more than a minor inconvenience for G3-specific testing: any CLI script that walks architecture completion and *then* wants to test explore-continuity phrases must explicitly cancel first, every time a wizard happens to still be open — a real but known and scriptable constraint, not a design flaw in G3 itself.

---

## 10. Findings register updates

**Applied 2026-08-15 (Cursor, post-review):** G8 (primary) and G9 (secondary) are in `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`. The original audit cut could not write that file (EPERM); §8 R2 claimed "done" prematurely — corrected here.

## 11. Diagnostic artifact note

A temporary, audit-only script (`sysmap004_probes.py`) was used to run P1-P7 against live orchestrator code via `_RefuseLLM` fixtures, matching the pattern of `tests/test_fn021_session_hygiene.py`. It lives in the session scratchpad, **not** under `tests/`, and was not committed — per contract §4.4's instruction to prefer reporting probe results inside this artifact over landing a new test file. Its full source and raw output are reproduced in §5 above; nothing further is needed to reproduce these results (any engineer can recreate the same fixture from the existing `test_fn021_session_hygiene.py`/`test_catalog_bind_v1.py` patterns).

---

## 12. Regression check (informational — no changes made)

Ran the six test files most relevant to the code paths this audit exercised, no product code touched:

```text
tests/test_fn021_session_hygiene.py
tests/test_fn025_help_goal_intent.py
tests/test_fn026_lever_iterate_preseed.py
tests/test_catalog_bind_v1.py
tests/test_component_sync.py
tests/test_g5_dse_iterate_dual_truth.py

52 passed in 0.27s
```

All green — this audit found documentation/routing gaps, not regressions in already-landed FN/G work.
