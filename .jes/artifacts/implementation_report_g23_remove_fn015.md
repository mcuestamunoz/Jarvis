# Implementation Report — G23 Eliminate FN-015 ("ayúdame a definir") Feature

**Contract:** [`implementation_contract_g23_remove_fn015.md`](implementation_contract_g23_remove_fn015.md)
**Prerequisite:** G21/G22 review PASS (`implementation_review_g21_g22_catalog_bind_ux.md`), same working tree — commit pending.
**Status:** Implemented, product feature removed in full, hygiene gate preserved, docs purged, 11 new tests, full suite green (1894). **Not committed.**

---

## 1. Files deleted vs changed

### Deleted

| File | Why |
|---|---|
| `tests/test_fn015_pending_help.py` | Asserted the removed feature's behavior (Brief-replay, IDLE wizard auto-open, catalog offer under "definir"); 2 of its 9 tests failed immediately after the removal (proof the old behavior was actually gone). Replaced by `tests/test_g23_fn015_removed.py`. |

### Changed — source

| File | What |
|---|---|
| `src/jarvis/core/orchestrator.py` | IDLE FN-015 bridge (`_try_help_define_pending_idle` call site) replaced with a G23 gate: `is_define_missing_confusion_phrase` → `_handle_project_status()` directly (no wizard opened). `_try_help_define_pending_idle` and `_help_current_pending_acquisition` **deleted**; replaced by one new method `_define_missing_confusion_reask` (component sub-mode → `_component_prompt_for_first_missing`, one line; numeric sub-mode → `_question_for_param(pending[0])`, one line; no catalog offer, no session mutation). DEFINE_MISSING call site updated to call the new method. Import renamed. Stray FN-015 comment references purged or marked explicitly historical/removed. |
| `src/jarvis/core/acquisition_target.py` | `is_help_define_pending_phrase` renamed to `is_define_missing_confusion_phrase`; `_EXACT_HELP_DEFINE_PHRASES`/`_HELP_DEFINE_MARKERS` renamed to `_EXACT_CONFUSION_PHRASES`/`_CONFUSION_MARKERS`. Module docstring rewritten: no longer describes FN-015 as a live feature. |
| `src/jarvis/core/acquisition_brief.py` | Deleted the `"decir 'ayúdame a definir' para repetir esta guía"` bullet from `build_acquisition_brief` — for **all** keys, motors included (the G21 `ayúdame a elegir` bullet stays, motors-only). Module docstring updated. |
| `src/jarvis/core/motor_catalog_assist.py` | No change (audited — the confusion-gate rewrite doesn't touch this module; catalog offer removal happens at the orchestrator call site, not here). |

### Changed — tests (comment/name purge only, logic unaffected)

| File | What |
|---|---|
| `tests/test_fn016_navigation_parse_safety.py` | Renamed `test_ayudame_definir_still_fn015` → `test_ayudame_definir_still_short_reask`; section header purged. |
| `tests/test_fn017_component_acquisition_plumbing.py` | Same rename/header purge. |
| `tests/test_fn018_acquisition_brief.py` | Renamed `test_fn015_help_uses_brief_or_component_prompt` → `test_g23_confusion_reask_names_right_component`; header purged. |
| `tests/test_fn019_bare_propeller_size.py` | Section header purged (test body already behavior-agnostic to the rename). |
| `tests/test_fn023_next_step_help.py` | Renamed `test_fn015_help_define_not_stolen` → `test_define_missing_confusion_reask_not_stolen`; header purged. |

None of these 5 files needed a *logic* change — the pre-existing assertions in the surviving tests already only checked "still interactive, still `define_missing_params`, pending unchanged" (in-wizard) or equivalent, which the new `_define_missing_confusion_reask` still satisfies. Confirmed by running the full suite before renaming (all green) and after (still all green).

### New

| File | What |
|---|---|
| `tests/test_g23_fn015_removed.py` | 11 tests: Brief no longer advertises the phrase (2 keys checked); DEFINE_MISSING short re-ask, 0 LLM, no Brief text, pending unchanged (2 variants); DEFINE_MISSING confusion phrase does not open the catalog even when pending is an assisted motor param; battery/energy never mentioned when pending is propellers; `collected_params` preserved; IDLE confusion phrase → `project_status`, not a wizard (2 variants); regressions — `ayúdame a elegir` (G21) still works, FN-013 named-block reprompt still works, real analyze questions still reach the LLM. |

---

## 2. Doc purge checklist (contract §5)

| Doc | Action taken |
|---|---|
| `docs/PROJECT_CONTINUITY.md` | "Field note FN-015" section rewritten to a short **REMOVED (G23)** block: what was deleted, why, what survives (the confusion gate), pointer to the G23 contract/report. The old "closed feature" narrative (table of symptom→fix, "✅") that taught the verb is gone. |
| `docs/IMPLEMENTATION_TASKS.md` | Top-of-file "PRIORIDAD ACTUAL" and 🟡 REGISTRADOS updated: G23 now ✅ implemented/awaiting review (was "IC READY"). Queue diagram updated. FN-015's "✅ COMPLETADO" historical section marked **⛔ SUPERSEDED / REMOVED by G23**, with the original plan collapsed into a `<details>` block explicitly labeled historical — not left as a current-capability checklist. FN-018's own plan item referencing the now-deleted `_help_current_pending_acquisition` annotated inline. |
| `docs/system_map/CONNECTIONS.md` | C-032 full section rewritten to **⛔ REMOVED** (explains what was deleted, what replaced it, why no new connection number was minted). Summary table row struck through with ⛔. |
| `docs/system_map/01_runtime/RUNTIME_MAP.md` | 25-checkpoint table's #6 (FN-015 bare help-define) replaced with the new G23 confusion-gate checkpoint (routes to `project_status`, no C-xxx — it's not a new acquisition connection, just a Runtime-internal reroute). Nested `DEFINE_MISSING_PARAMETERS` routing block updated to show `_define_missing_confusion_reask` instead of the deleted symbols. Added an honest note that G21/G22/G9-A aren't yet reflected checkpoint-by-checkpoint (out of this IC's scope — flagged, not silently left implying full accuracy). |
| `docs/system_map/03_acquisition/ACQUISITION_MAP.md` | `is_help_define_pending_phrase` replaced with `is_define_missing_confusion_phrase` in the live symbol list, with an inline note that it is now an anti-LLM gate only. |
| `docs/system_map/DIAGRAMS.md` | C-032 row struck through, marked REMOVED (G23), status ⛔. |
| `docs/system_map/jarvis-system-map.canvas.tsx` | C-032 edge entry removed (commented pointer left in its place, not silently deleted with no trace); orphaned `pend_help` node label removed. *(Not explicitly named in the contract's table, but is a live rendering config for the same diagram DIAGRAMS.md documents — updated for consistency.)* |
| `docs/BUGS.md` | Header banner (externally edited before this session to list G21/G22 as "Open") updated to reflect current reality: G21/G22 review PASS/commit-pending, G23 implemented/awaiting review — not left stale. *(Not in the contract's table; touched because it directly contradicted this cycle's actual state.)* |

---

## 3. Historical artifacts (audited, not silently deleted)

| Artifact | Action |
|---|---|
| `.jes/artifacts/implementation_contract_fn015.md` | ⛔ SUPERSEDED banner added at top, pointing to this IC and report. Body left intact as historical record. |
| `.jes/artifacts/cycle_close_fn015.md` | Same SUPERSEDED banner. Body left intact. |
| `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` | The single FN-015 row in G21's "Separate from" table annotated inline — the "working as designed" behavior it described no longer exists; pointer to G23 added. This file is still actively driving the priority queue (source of G21/G22/G23 itself), so it was corrected rather than left to mislead a reader mid-queue. |
| Other historical closed-cycle artifacts matching "FN-015" (fn014/016–023 contracts, various cycle_close/audit/sys_map files, `implementation_contract_r3b_preempt_real.md`) | **Not touched.** These are closed-cycle records mentioning FN-015 only as accurate historical context at the time each was written (e.g. "FN-011/013/014/015 regressions verified green" — a true statement about that day's test run), not living instructions presenting FN-015 as current capability. Rewriting them would be doc churn without correcting anything actually misleading — flagged here rather than silently skipped, per the contract's "where they would mislead implementers" qualifier. |

---

## 4. Design note: IDLE mechanism deviates from the contract's suggested implementation (documented deviation)

The contract's §1 ★3 "Preferred mechanism" suggested adding the confusion phrases to `IntentResolver.GUIDANCE_PATTERNS`. Implementing it that way was tried first and found to cause a real regression: `GUIDANCE_PATTERNS` is read by `_resolve_strong_action_intent`, which `resolve_intent` calls **unconditionally**, including from inside `DEFINE_MISSING_PARAMETERS`'s own pre-existing `_dm_intent == "project_status"` check (Bug 56, checked *before* where ★2's short-re-ask gate needs to run). Adding the phrases there would have made them resolve to `"project_status"` globally — so mid-wizard, the confusion phrase would trigger a **full Continuity dump** (Bug 56's branch) instead of ★2's mandated one-line re-ask, i.e. a worse regression than the one being fixed (bigger LLM-adjacent noise, replacing a small Brief-replay with a full status block).

**Fix:** kept the IDLE routing as its own narrow check (`is_define_missing_confusion_phrase(user_input)` at IDLE only → `_handle_project_status()` directly), not folded into the shared `GUIDANCE_PATTERNS` table. This satisfies ★3's actual requirement — IDLE confusion phrases resolve to `project_status`, same authority as FN-023, zero LLM, no wizard — without the cross-mode collision. Documented inline in the orchestrator comment at the IDLE gate.

No other deviations. All other design decisions (★1, ★2, ★4, ★5) implemented as specified.

---

## 5. Test count / suite result

```
python -m pytest tests/test_g23_fn015_removed.py -v   # 11 passed
python -m pytest -q                                    # 1894 passed
```

1892 baseline (post G21/G22) − 9 (deleted `test_fn015_pending_help.py`) + 11 (new `test_g23_fn015_removed.py`) = 1894. Zero weakened tests — every deleted assertion tested behavior that no longer exists by design; every renamed test's logic is unchanged.

---

## 6. Acceptance criteria — status

1. ✅ No Brief advertises `ayúdame a definir` (`test_g23_brief_does_not_advertise_help_define`).
2. ✅ `_try_help_define_pending_idle` not in tree (grep-confirmed, zero hits in `src/`/`tests/`).
3. ✅ DEFINE_MISSING + old phrases → 0 LLM, short re-ask, no Brief loop, no catalog (`test_g23_define_missing_confusion_no_llm_short_reask`, `test_g23_define_missing_confusion_does_not_open_catalog`).
4. ✅ IDLE + old phrases → `project_status`, no auto wizard open (`test_g23_idle_help_define_is_project_status_not_wizard`).
5. ✅ `ayúdame a elegir` unchanged (`test_g23_help_choose_still_works`).
6. ✅ Living system map: C-032 REMOVED; RUNTIME/ACQUISITION maps cleaned.
7. ✅ Living Continuity/TASKS docs: FN-015 marked removed/superseded.
8. ✅ Historical FN-015 artifacts bannered SUPERSEDED.
9. ✅ Full suite green (1894); no weakened tests.

---

## 7. Deviations

One, documented in §4 above (IDLE mechanism: narrow dedicated check instead of `GUIDANCE_PATTERNS`, to avoid a real regression the contract's suggested mechanism would have caused). No other deviations.
