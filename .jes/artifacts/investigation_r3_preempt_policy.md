# Investigation — R3 Preempt Policy for DEFINE_MISSING

**Type:** Audit + design investigation. Zero `src/` changes, zero new tests.
**Contract:** [`investigation_contract_r3_preempt_policy.md`](investigation_contract_r3_preempt_policy.md)
**Checkpoint base:** `checkpoint-cli-routing-residuals` (`0690895`)
**Findings closed:** G8 (engineering-intent/explore unreachable), G11 (iterate trapped), G7 (related preempt gap) — scoped, not fixed.

---

## 1. DEFINE_MISSING routing audit

`_handle_user_text_inner`'s `mode == DEFINE_MISSING_PARAMETERS` branch (`orchestrator.py:845-962`) is a single ordered if/elif-style chain. The first ten gates apply uniformly to **both** sub-modes (component acquisition and numeric parameter collection); the chain then forks at `orchestrator.py:933` on `pending_missing_reason`/`param_definition_reason == MISSING_COMPONENT_DEFINITION`, and the two sub-modes diverge completely from that point on — this fork is the reason C-052 cannot be copied verbatim (§2).

**Legend:** ✅ intent executes · ⚠ intent is acknowledged (explicit refusal naming the block) but not executed · ❌ intent is neither executed nor acknowledged (silent trap or generic parse error)

| # | Gate | Location | Input pattern | Returns? | Reachable (component sub-mode) | Reachable (numeric sub-mode) |
|---|---|---|---|---|---|---|
| 1 | project_status soft-interrupt | `:849-852` | `"estado"`, `"cómo va"`, … | YES | ✅ wizard stays open | ✅ wizard stays open |
| 2 | list_materials soft-interrupt | `:857-860` | `"qué materiales…"` | YES | ✅ | ✅ |
| 3 | list_motors soft-interrupt | `:866-869` | `"qué motores…"` (incl. trailing `?`) | YES | ✅ | ✅ |
| 4 | FN-013 same-block reprompt | `:874-877` (`_try_reprompt_active_block_declaration`) | `"definir <active block>"` | YES if match, else `None` | ✅ preserves `collected_params` | ✅ preserves `collected_params` |
| 5 | FN-015 pending-help | `:883-887` (`is_help_define_pending_phrase`) | `"ayúdame a definir"` (bare) | YES if match, else `None` | ✅ | ✅ |
| 6 | FN-005 analyze / help-choose | `:890-895` | `analyze` intent, not a catalog help-choose phrase | YES | → LLM ✅ (intended) | → LLM ✅ (intended) |
| 7 | calculate | `:896-899` | `"calcula"` | YES | ✅ | ✅ |
| 8 | simulate | `:900-903` | `"simula"` | YES | ✅ | ✅ |
| 9 | FN-016 navigation-back | `:910-918` | `"atrás"`, `"volver"`, `"vuelve"` | YES, clears session | ✅ full cancel (data-loss profile: §3) | ✅ full cancel (data-loss profile: §3) |
| 10 | `MISSING_COMPONENT_DEFINITION` fork | `:933-939` | everything not caught above | routes to `_handle_component_description` | **see 10a-10e below** | *(not this sub-mode — falls to 11-12)* |
| 10a | ★2 different-block refuse | `_maybe_refuse_different_target`, `:2067-2077` | `"definir <other block>"` | YES | ⚠ named, told to `cancelar` first | — |
| 10b | ★2 engineering-intent/explore refuse | `_maybe_refuse_different_target`, `:2079-2094` | `"reducir payload"`, `"explora opciones"` | YES | ⚠ named, told to `cancelar` first, **never executes** | — |
| 10c | affirmative / real component description / force-motors,propellers,frame | `:2140-2236` | `"sí"`, `"4x 2306 1400kv"`, `"10x4.5"`, `"plástico 400g"`, … | YES | ✅ (this gate's actual purpose) | — |
| 10d | **low-completeness fallback** | `:2237-2246` onward | `"aplica la mejor"`, bare `"itera X"`, dismiss phrases, `"nuevo proyecto"`, unparseable text | YES | ❌ **silently re-shows the Brief, zero acknowledgment** | — |
| 11 | battery component-intent intercept | `:940-954` | battery-shaped text | YES if battery-shaped, else falls through | *(numeric sub-mode only)* | ✅ narrow (battery only) |
| 12 | `ParamDefinitionSession.answer()` | `:955` → `param_definition_session.py:515` | everything else | YES (always returns) | — | **see 12a-12d below** |
| 12a | ESCAPE_WORDS / nav-back defense-in-depth | `:518-537` | `"cancelar"`, `"atrás"` | YES, clears | — | ✅ (already caught upstream at gate 9/global) |
| 12b | assisted-motor help (FN-005/006) | `:548-551` (`_answer_assisted_motor`) | catalog help-choose, `is_list_motors_phrase`, a catalog pick | YES if matched | — | ✅ narrow (only when `pending[0] ∈ ASSISTED_MOTOR_PARAMS`) |
| 12c | affirmative / skip / numeric value | `:571-654` | `"sí"`, skip phrases, a float | YES | — | ✅ (this gate's actual purpose) |
| 12d | **generic parse-error fallback** | `:604-612` | `"explora opciones"`, `"reducir payload"`, `"aplica la mejor"`, bare `"itera X"`, dismiss phrases, `"nuevo proyecto"`, anything non-numeric/non-skip/non-affirmative | YES | — | ❌ **`"No reconozco 'X' como valor."` — not silent, but no acknowledgment of what the user actually asked for, and the intent never executes** |

### 1.1 The asymmetry this table exposes

Continuity Hardening ★2 (`_maybe_refuse_different_target`) already fixed the **worst** form of G8 — but **only for component sub-mode**, and **only for two intent shapes** (declare-different-block, engineering-intent/explore). It is called exclusively from inside `_handle_component_description` (`:2139`), which the numeric sub-mode never reaches. The result:

- **Component sub-mode:** engineering-intent/explore phrases get an honest, named refusal ("Estoy definiendo los motores. Escribe 'cancelar' primero si quieres explorar otras opciones."). Everything else not shaped like a component (`apply_exploration_result`, bare `iterate`, `dismiss_suggestion`, `create_project`) still falls into the **silent** Brief-reshow (10d) — genuinely swallowed, no acknowledgment at all.
- **Numeric sub-mode:** ★2 is never consulted. **Every** unrecognized intent — including the exact two shapes ★2 already solved for component sub-mode — degrades to the generic `"No reconozco 'X' como valor."` (12d). This is not silent, but it is *less* honest than 10a/10b: it never tells the user they're mid-wizard, never offers `cancelar`, and reads as if the system simply didn't understand a word, not as if a real request was recognized and set aside.

So G8/G11/G7 are not one bug with one shape — they are **two different failure depths** (silent trap vs. generic parse-error) split across **two sub-modes** that diverged the moment ★2 was added only where the pain was worst at the time (component wizards, since that's what the Continuity Hardening cycle's own CLI walk exercised). Any R3 fix has to either unify both sub-modes under one mechanism, or explicitly accept treating them differently for a documented reason (§4).

---

## 2. C-052 reference summary (`_should_preempt_iterate_wizard`, `orchestrator.py:486-524`)

Applies only to `ITERATE_INTERACTIVE`. Mechanics:

1. **Soft interrupts first** (`:783-815`, checked *before* C-052 is even consulted): `project_status`, `list_materials`, `list_motors`, `analyze`, and an `information`/`hybrid` semantic-class guard — all answered inline, wizard state is **never touched**, a `wizard_reprompt` field is appended so the caller can re-show the current step's question.
2. **Ownership guard** (`_iterate_owns_component_input`, `:527-553`): true when the wizard is mid-collecting a component/motor pick (`DEFINE` @ step 2, live `motor_suggestions`), or sitting at a strategy-selection step (`variable` named, `operation` not yet resolved). When owned, a `None`/`iterate`-classified input is treated as *this step's own answer*, not a new request.
3. **Strong-intent preempt** (`:515-516`): a fixed intent set — `explore_design_space, apply_exploration_result, calculate, simulate, create_project, define_params, iterate, dismiss_suggestion` — always preempts, **even while owned** (★3 rule 4: "a genuinely different strong action... still preempts even while the wizard owns the current step").
4. **Component-description fallback** (`:521-524`): when not owned and not a strong intent, probe `_should_intercept_component` against an IDLE-shaped copy of the session; if it matches, preempt too.
5. **Execution** (`:820-830`): `self.state_manager.clear_runtime_session()` — **unconditional, no data check** — then a **recursive** `_handle_user_text_inner` call re-dispatches the same input as if the session had always been IDLE, and the result is prefixed with a fixed notice: *"He cerrado la iteración en curso para atender esta instrucción."*

**What makes this safe for ITERATE and why it does not generalize directly:** `iteration_draft` is a **single in-flight variable change** — `operacion`/`variable`/`valor`/`estrategia` for exactly one mutation, never written to `design_properties`/`current_parameters` until the *final* confirmation step (`"¿Confirmas la iteración?"`) is answered `"sí"`. Discarding it mid-way genuinely discards nothing durable — the user was still deciding what to change, not holding already-declared data. This is not true for DEFINE_MISSING (§3).

---

## 3. Danger zones

### 3.1 `collected_params` loss — real, sub-mode-dependent

Traced `ParamDefinitionSession.answer()` (`param_definition_session.py:515-660`) end to end. For the **numeric** sub-mode:

- Each turn's answered param is folded into `session.collected_params` (`:619, :622, :646`) and the session is re-saved with the growing dict — **this is the only place the value lives**.
- `design_properties`/`current_parameters` are **not** touched until `apply_and_recalculate(collected)` runs (`:708`), which only happens once `pending_param_definitions` is fully empty (`:637` guard is the inverse — non-empty `remaining` always re-prompts and returns *before* reaching apply) — or via the explicit skip-to-completion path (`_SKIP_PHRASES`, `:601-603`).
- **Consequence:** if a numeric wizard has collected 2 of 3 params (e.g. `motor_count=4` typed, `per_motor_max_thrust_n` still pending) and something calls `clear_runtime_session()`, `motor_count=4` is gone — not "state reset", the user's actual typed value is lost and would need to be re-typed from scratch on re-entry.

For the **component** sub-mode, this risk **does not exist** the same way:

- `_handle_component_description`'s `processable` branch calls `self._apply_inferred_component_spec(updated_state, spec)` then **`self.workspace_manager.save_state(updated_state)` immediately, per turn** (`orchestrator.py:2344-2348`) — every successfully-matched component is durably written to `design_properties.components` **the instant it's accepted**, not deferred to session state.
- `session.pending_missing_params`/`collected_params` for this sub-mode only ever hold *routing* state (which keys are still outstanding), not undeclared data — a `clear_runtime_session()` here loses nothing that was actually typed and accepted.

**This is the single most important asymmetry for any R3 design**: a blind C-052-style `clear_runtime_session()` is **safe** for component sub-mode and **lossy** for numeric sub-mode. Any option that treats both sub-modes identically is either over-cautious (component) or unsafe (numeric).

### 3.2 Re-entry

Component sub-mode re-entry is **naturally resumable** with no extra mechanism needed: `_next_pending_block`/`_set_pending_next_block` always recompute the current gap **fresh from `design_properties.components`** (never from session state), so any of the existing bridges (FN-011 `"ayúdame a declarar propulsión"`, FN-014 mention-based, FN-015 bare "ayúdame a definir") correctly pick up exactly where the user left off — already-saved components are already reflected on disk.

Numeric sub-mode re-entry is **not** resumable past what was durably applied: re-triggering the same reason (e.g. `missing_propulsion_parameters`) recomputes `missing_params_for_reason(reason, current_parameters)` fresh — since `motor_count` was never applied to `current_parameters`, it is asked again from scratch. There is no "half-collected" state anywhere the system can recover from except `session.collected_params` itself, which is exactly what a clear would destroy.

### 3.3 Practical implication

Any preempt for the **numeric** sub-mode needs one of:
(a) apply whatever's in `collected_params` before clearing (`apply_and_recalculate(session.collected_params)` — already a proven code path via the skip-to-completion flow, `param_definition_session.py:601-603`, so this is not new semantics, just an earlier trigger point), or
(b) explicitly warn the user before discarding non-empty `collected_params`, or
(c) never blind-clear at all — only preempt when `collected_params` is empty (nothing to lose), and fall back to an explicit refuse (mirroring ★2) otherwise.

Component sub-mode needs none of this — a direct C-052-style clear-and-redispatch is safe there because nothing valuable lives only in session state.

---

## 4. Design options

### Option A — Simplest: symmetric soft-interrupt + refuse, no clearing ever

**Fires on:** extend the *existing* soft-interrupt shape (gates 1-3, 7-8 in §1) to also cover `explore_design_space` (genuinely read-only, per its own docstring — "pure in-memory exploration, no state mutation") in **both** sub-modes. Separately, port ★2's `_maybe_refuse_different_target` engineering-intent/explore refuse logic (10a/10b) so it also runs for the **numeric** sub-mode before falling to `ParamDefinitionSession.answer()` — replacing the generic `"No reconozco 'X' como valor."` (12d) with the same honest, named refusal component sub-mode already gets. `apply_exploration_result`, bare `iterate`, `dismiss_suggestion`, `create_project` remain **explicitly out of scope** — left as a documented residual, not solved.

**Wizard state:** never touched. No `clear_runtime_session()` anywhere in this option.

**User sees:** for `explore_design_space` — DSE results shown inline, current wizard question re-appended (mirrors ITERATE's `wizard_reprompt` field). For engineering-intent/explore-adjacent phrases in numeric sub-mode — the same "Estoy definiendo X. Escribe 'cancelar' primero..." message component sub-mode already shows. For everything still out of scope — unchanged (silent Brief-reshow or generic parse error, as today).

**Risks:** none from a data-safety standpoint (§3.1's `collected_params` risk is fully sidestepped — no clearing occurs, so there's nothing to lose). The residual risk is purely UX: `apply_exploration_result`/bare `iterate`/`dismiss_suggestion` remain unsolved, so G7/G11 are only *partially* closed by this option.

**Tests needed:** unit tests for `explore_design_space` as a soft-interrupt in both sub-modes (mirroring the existing `list_motors` soft-interrupt tests); unit tests proving numeric sub-mode now shows the ★2-style refusal for `"reducir payload"`/`"explora opciones"` instead of the generic parse error; regression tests that the existing component-sub-mode ★2 refusal (10a/10b) is unchanged.

---

### Option B — Most correct: sub-mode-aware real preempt (extends C-052's actual semantics)

**Fires on:** the *same* strong-intent set C-052 uses (`explore_design_space, apply_exploration_result, calculate, simulate, create_project, define_params-for-a-different-block, iterate, dismiss_suggestion`), detected via a new `_should_preempt_define_missing_wizard(user_input)` mirroring `_should_preempt_iterate_wizard`'s structure (strong-intent detection, no "ownership" concept needed here since DEFINE_MISSING has no analogous "mid-typing-an-answer" ambiguity the way ITERATE's strategy-selection step does — a numeric param answer is unambiguously either a float or it isn't).

**Wizard state, by sub-mode:**
- **Component sub-mode:** direct `clear_runtime_session()` + recursive re-dispatch, **identical to C-052** — proven safe per §3.1 (nothing durable lives only in session state).
- **Numeric sub-mode:** *before* clearing, if `session.collected_params` is non-empty, call `apply_and_recalculate(session.collected_params)` first (same call the skip-to-completion path already makes) so partially-collected values are saved as a partial update, **then** clear and re-dispatch. If `collected_params` is empty, clear directly — nothing to lose.

**User sees:** the same `"He cerrado la [wizard] en curso para atender esta instrucción."`-style notice C-052 already uses, extended with a note when a partial apply happened ("... — se aplicaron los 2 parámetros que ya habías indicado.") so the user isn't surprised state changed.

**Risks:** partial-apply changes physics/state as a side effect of a preempt the user didn't explicitly ask for (they said "explora opciones", not "aplica motor_count=4") — this is a real, if small, surprise-factor risk; it needs its own message so it doesn't read as silent. Also broader surface than Option A: touches both sub-modes' clearing paths, needs the same care CLI Polish's S4/S5 slices took around force-write ordering and stale-pending guards — this is the kind of change that historically has produced regressions elsewhere in this codebase (FN-021's own lesson) if the "what does clearing actually discard" question isn't re-verified for every entry point that can leave a wizard "open."

**Tests needed:** full mirror of C-052's own test suite shape (regression tests for owned-input suppression are N/A here, but need: strong-intent-preempts-component-submode-with-clear; strong-intent-preempts-numeric-submode-with-partial-apply-when-collected-params-nonempty; strong-intent-preempts-numeric-submode-with-direct-clear-when-collected-params-empty; notice message content for both; re-entry-after-preempt tests confirming the durable component case resumes cleanly and the numeric partial-apply case doesn't re-ask for what was just applied).

---

### Option C — Middle ground: confirm-before-discard (new interaction state, thread-the-needle)

**Fires on:** same strong-intent set as Option B.

**Wizard state:** if `collected_params` is empty (numeric) or we're in component sub-mode (already durable) — preempt immediately, same as Option B, no confirmation needed (nothing at risk). If `collected_params` is non-empty (numeric, real unsaved progress) — **do not clear yet.** Return a one-turn confirmation: *"Tienes progreso sin guardar (motor_count=4). Si continúas con 'explora opciones' se perderá. Escribe 'sí' para continuar de todas formas, o termina/cancela primero."* Only on an explicit affirmative reply does the *next* turn actually clear and re-dispatch the **original** pending instruction (requires holding the original strong-intent input somewhere recoverable across the confirmation turn — the same `resume_user_input` pattern `begin_structural_confirm` already uses for FN-004's structural-change confirmation, `orchestrator.py:2321-2331`).

**User sees:** an explicit choice, never a silent or automatic loss, and never a surprise side-effect (unlike Option B's auto-apply).

**Risks:** genuinely new interaction pattern — a "pending preempt confirmation" state that doesn't exist anywhere in the codebase today (closest precedent is FN-004's `pending_structural_change`, which already proves the `resume_*` pattern works, so this isn't unprecedented, but it is new *surface*). Two-turn resolution for the lossy case adds friction the other two options don't have. Needs its own session field(s) (or reuse of `pending_structural_change`'s shape) and its own escape-word handling (declining the confirmation must not leave the wizard in a broken state).

**Tests needed:** everything Option B needs, plus: confirmation-prompt-shown-when-collected-params-nonempty; affirmative-reply-executes-original-intent; negative-reply-returns-to-wizard-unchanged; declining-then-cancelar-still-works; no-confirmation-needed-when-collected-params-empty (fast path matches Option B).

---

## 5. G9-A scope assessment

Unchanged root cause from the CLI Polish audit (`.jes/artifacts/investigation_cli_polish_audit.md` §4.2, G9-A): `orchestrator.build_startup_context`'s catalog-gap computation (`orchestrator.py:3226-3253`) recomputes `catalog_gap`/`catalog_matches` from `thrust_per_motor_needed_n`/`kv_rating`/`propeller_diameter_in` every call — it never reads a bound `catalog_ref` on `components["motors"]`, so a motor already bound to a specific SKU can still show "no tengo un motor en el catálogo" once requirements drift past that SKU's coverage.

**What's changed since that audit:** ERF-1 added `engineering_readiness.resolve_motor_catalog_surface` (`engineering_readiness.py:180-227`), an explicitly-acknowledged **byte-for-byte port** of this same orchestrator logic (per its own docstring: "Ported byte-for-byte from `orchestrator.build_startup_context`'s own catalog-gap computation"). It has the exact same blind spot, independently. **G9-A's blast radius has grown**: a fix now needs to touch two call sites in lock-step (or, better, extract the shared logic into one authority both consume, which `resolve_motor_catalog_surface` was *supposed* to become per ERF-1's own §6.1 "optional but recommended" dedup note — never actually wired back into `orchestrator.py`, which still keeps its own separate inline copy for the `motor_catalog_matches`/`motor_catalog_gap` startup-context fields).

**Still not trivially fixable in this cut** — it remains gated on the same unresolved data-contract question the original audit flagged: *"bound-but-underspec'd SKU → gap, warning, or silence?"* This is a real design decision (arguably now touching ERF-2's `catalog`/`propulsion` `INCOMPATIBLE`-vs-`WARNING` verdict machinery too, since a `catalog_ref`-aware gap would change what `G9B`'s demotion and ERF-2's `GAP-PROP-MOTOR-MISMATCH` see as "the" catalog gap), not something to fold into an R3 preempt-policy IC as a side effect. **Recommend: continue deferring, revisit alongside a dedicated catalog-authority consolidation pass** (the orchestrator/engineering_readiness duplication is itself now worth its own small IC, independent of the `catalog_ref` question).

---

## 6. Recommendation

**Option A first, Option B as a deliberate follow-up — not Option C.**

Reasoning:

1. **Option A closes the sharpest, most misleading part of the bug for free.** The numeric-sub-mode/component-sub-mode asymmetry documented in §1.1 is a real, demonstrable inconsistency (the exact same phrase gets an honest refusal in one sub-mode and a confusing "I don't understand" in the other) that Option A fixes with **zero data-safety surface** — no `clear_runtime_session()` call is added anywhere, so §3's entire danger-zone analysis is moot for this option. This is the kind of fix this project's own discipline (CLAUDE.md: "preferred order: localized extraction, shared helper, small routing improvement, structural refactor only when justified by repeated evidence") explicitly favors before reaching for the more invasive options.
2. **Option B is the right *eventual* answer** for `apply_exploration_result`/bare `iterate`/`dismiss_suggestion`/`create_project` — G7/G11 aren't *fully* closed without it — but it's real surgery on a clearing path this codebase has been burned by before (FN-021's own "what were we just doing" lesson, and this session's own CLI-Polish S5 slice had to specifically re-verify every entry point that can leave a wizard "open" before trusting a freshness check). It deserves its own IC with its own focused review, not a bundle with Option A's low-risk win.
3. **Option C is not worth its complexity here.** It solves the same problem Option B's partial-apply solves, but with a strictly worse UX (an extra confirmation turn for a case Option B can resolve in one turn with a clear, honest notice) and a genuinely new session-state shape to build and test. The `resume_*`/`begin_structural_confirm` precedent it would reuse exists for a *different* kind of decision (numeric substitution ambiguity, FN-004) — stretching it to cover "should I discard my wizard progress" is a bigger conceptual reuse than it looks. Auto-apply-then-notify (Option B) is simpler and no less honest, since the user is told exactly what happened after the fact rather than asked to predict it beforehand.

**Suggested sequencing for the eventual IC(s):** ship Option A as R3a (small, symmetric, zero-risk). Scope Option B as R3b once R3a's CLI walk confirms the remaining residual (`apply_exploration_result`/`iterate`/`dismiss_suggestion`/`create_project` mid-wizard) is still worth closing — R3a may itself reduce how often users hit that residual in practice, which is useful signal before committing to R3b's larger surface.
