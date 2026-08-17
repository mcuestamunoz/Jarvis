# Design — Continuity Hardening

**Status: CLOSED — Engineer ★1–★7 locked 2026-08-15**  
**(Cursor review PASS WITH NOTES absorbed into ★4 / ★2 / ★7)**

**Type:** Design only. Zero product `src/` changes. Not an Implementation Contract.  
**Companion:** [investigation_continuity_hardening.md](investigation_continuity_hardening.md) — read first.  
**Review:** [implementation_review_continuity_hardening_investigation.md](implementation_review_continuity_hardening_investigation.md)  
**Impl contract:** [implementation_contract_continuity_hardening.md](implementation_contract_continuity_hardening.md)  
**Checkpoint base:** `checkpoint-g3` (`a3b72b8`)

---

## 0. Locked ★ summary (authoritative)

| ★ | Lock |
|---|---|
| **★1** | One Implementation Contract, **4 slices** in order 1→4. Slice 1 ships first (G14). |
| **★2** | G12/G8: **(b) Refuse** — honest one-liner + keep wizard; `cancelar` remains the only cross-block clear. No retarget (a) in this cut. |
| **★3** | G11: **(a)+(b)** — owns-input **before** strong-intent; extend guard to strategy-selection step. Not (c). |
| **★4** | G14: **Do not force-propellers while `motors` still pending** unless phrase is clearly propeller-shaped; when multiple force candidates apply, **first-declared** member wins. |
| **★5** | G15: deterministic **list-motors** escape inside `ParamDefinitionSession.answer` (mirror G10 ★8 shape). |
| **★6** | G15: `max_available_n` from **same filtered set** as the search (or explicitly labeled if unfiltered kept). |
| **★7** | Thrust under-requirement gate: **OUT of this cut** (messaging-only Continuity). |

Acceptance note (★2): full BOM walk without silent wrong-wizard / wrong write is the Continuity bar; explicit `cancelar` for intentional retarget remains allowed and expected under refuse policy.

---

## 1. Recommended option

**O2 — Acquisition Target Authority helper**, implemented as **4 independent, sequential slices** (per Engineer preference §6.1.5) rather than one large change.

### Why O2 over the alternatives

| Option | Verdict | Reasoning |
|---|---|---|
| **O1 — Force-key respect only (G14-first)** | Adopted as **Slice 1**, not a competing option | O1 is exactly the right *shape* for G14 specifically, but the investigation (§4) shows the same authority gap recurs in three more places (G12/G8, G11-A/B) with different local mechanisms. Treating O1 as the whole fix would leave G12/G8/G11 open. |
| **O2 — Acquisition Target Authority helper** | **Recommended, phased** | Matches the investigation's root-cause synthesis (§4: one tree, four branches) and Engineer preference §6.1.1 ("active acquisition target wins... unless user explicitly retargets") directly. A single, shared, small helper — not a rewrite — that each of the four call sites (two force-* blocks, the component-description fallback, the iterate preempt check) consults instead of independently re-deriving "am I the right target for this phrase." |
| **O3 — Preempt policy pack (R3-lite)** | Folded into **Slice 2 and Slice 4**, not adopted as a separate up-front architecture | A full R3-style policy pack for both wizards is more than G12/G8/G11 need individually — each has a narrow, specific gap (§3.3/§3.4 of the investigation). Building the shared authority helper first (O2) and then writing each wizard's own thin policy on top of it gets the same outcome without inventing a new cross-wizard abstraction before it's justified by more than 2 call sites. |
| **O4 — Messaging-only** | Rejected as primary, **adopted narrowly for G15's incoherent-max half only** | G14 silently writes wrong data (`suggested_key="propellers"` for a motor phrase) — no amount of better copy fixes a wrong write. G12/G8 leave the session permanently stuck with no user-visible path forward except an undocumented `"cancelar"` — a messaging fix alone ("you're stuck, try cancelar") is a band-aid on a missing retarget, not a fix. G15's *other* half (incoherent max) genuinely is messaging-only — see Slice 3. |
| **O5 — Map-only** | Rejected | G14 is a live, reproduced, silent-write bug (investigation §2.1, §3.1) — documenting it without fixing it leaves the exact defect the Engineer's smoking-gun CLI session hit. |

---

## 2. ★ Decisions to lock

**★1 — Slice order and scope confirmation.** Lock the 4-slice plan below as the shape of the eventual Implementation Contract(s), OR split G15 (independent leaf, no shared code with the other three — investigation §4) into its own separate, smaller, faster contract. Both are consistent with the investigation. Recommend: one contract, four slices, in the order below (Slice 1 first — highest severity, smallest blast radius).

**★2 — G12/G8 retarget vs refuse (Slice 2).** When `"definir <X>"` names a *different*, valid, currently-undeclared component/param while a DEFINE_MISSING wizard for `<Y>` is open:
- **(a) Retarget** — honestly clear `Y`'s `collected_params`/`pending_missing_params`, open `X`'s wizard, and say so ("He cambiado a definir `<X>`; lo que tenías capturado de `<Y>` se ha descartado.").
- **(b) Refuse** — keep `Y`'s wizard open, respond with one honest line ("Estoy definiendo `<Y>`. Escribe 'cancelar' primero si quieres pasar a `<X>`."), never silently re-show `Y`'s brief as if the user had said nothing new.

Both close G12/G8 (Engineer preference §6.1.2 lists both as acceptable). (b) is smaller blast radius (no new clear-and-reopen path, reuses the existing `cancelar` mechanism as the only session-clearing writer) — **recommended** unless Engineer wants (a)'s better ergonomics enough to accept the larger surface (a second code path that clears `collected_params`, which is exactly the class of risk FN-021's own lesson (`MISMATCHES.md`) warns about: any new "this replaces what we were doing" writer needs its own hygiene proof).

**★3 — G11 fix shape (Slice 4).** Three ways to close the reproduced bug (investigation §3.4, A18/A19), not mutually exclusive but pick a primary:
- **(a) Reorder** — consult an extended "does the wizard already own this input" guard *before* the strong-intent check in `_should_preempt_iterate_wizard`, not after.
- **(b) Extend guard coverage** — widen `_iterate_owns_component_input` to also recognize the strategy-selection step (`variable` set, `operation` still `None`), not just `DEFINE`+`step==2`.
- **(c) Narrow `_ITERATE_PREEMPT_INTENTS`** — drop `"iterate"` from the preempt set (or gate it on "the phrase doesn't also look like a plausible answer to the current step's question").
Recommended: **(a) + (b) together** — (a) alone doesn't help if the guard still doesn't cover the strategy step (G11-B would persist); (b) alone doesn't help G11-A (the strong-intent check still short-circuits first). (c) alone is the smallest diff but risks under-preempting genuine new iterate requests that happen to arrive mid-wizard — needs the same care FN-021/the original C-052 calibration (2026-08-05) already put into this exact tradeoff.

**★4 — G14 tiebreak rule (Slice 1).** When a composite `expected_keys` set (e.g. `["motors","propellers"]`) has multiple members and every inferred spec is `generic_component`, the force-* mechanism should not blindly try every member's extractor and take the first non-`"low"` result. Proposed rule: only force-key `K` when **either** (i) `K` is the only member of `expected_keys`, **or** (ii) no *other* member's own extractor also produces a non-`"low"` result for the same text (i.e., only force when the ambiguity is already resolved to one candidate). When multiple members' extractors would all succeed (rare, but possible for mixed phrases), prefer the block's **first-declared** member (`system_architecture_catalog.py`'s own key order, e.g. `motors` before `propellers` for `"propulsion"`) over an arbitrary force-order. Needs Engineer confirmation this tiebreak (first-declared-wins) is the right default vs. some other precedence.

**★5 — G15 list-motors escape (Slice 3).** Mirror G10 ★8's shape: a narrow, deterministic pattern set (e.g. `"que motores"`, `"motores disponibles"`, `"catálogo de motores"`) checked inside `ParamDefinitionSession.answer()` (not the orchestrator's `resolve_intent`, since this gap lives in a numeric-param wizard reached by reasons other than `MISSING_COMPONENT_DEFINITION` — see investigation A12) — returns `format_motor_catalog_suggestions`/`build_motor_catalog_suggestions`'s existing output, 0 LLM, no new vocabulary invented.

**★6 — G15 messaging fix (Slice 3).** `format_no_thrust_candidate_message`'s `max_available_n` should be computed from the **same filtered candidate set** the actual search used (kv/prop-constrained), not `lib.list_motors()` unfiltered — so "no candidate found" and "catalog max" always describe the same filter context. If Engineer wants to keep an unfiltered figure for context, it must be explicitly labeled ("máximo del catálogo completo, sin filtrar por KV/hélice") rather than presented as if it contradicts the filtered verdict.

**★7 — G15 thrust gate (A13, optional).** Should accepting a manually-typed thrust value below the computed requirement (e.g. `"15"` vs `≥37.7`) gain a validation warning/gate, or stay messaging-only? Investigation takes no position — Engineer call.

---

## 3. Rejected alternatives

| Option | Rejected because |
|---|---|
| **O1 alone** | Fixes G14 only; leaves G12/G8/G11/G15 open — the Engineer's own hypothesis (contract §0) explicitly frames these as one connected problem, and the investigation confirms it structurally (§4). |
| **O3 as primary architecture** | A full preempt-policy-pack for both wizards, built before the narrower per-finding gaps are understood, risks exactly the FN-021-class stale-state bug the `MISMATCHES.md` lesson warns about — "enumerate every entry point first," which is what Slices 1-4 do incrementally instead of a single big design. |
| **O4 (messaging-only) as primary** | Does not fix G14's silent wrong write or G12/G8's genuine dead-end (no discoverable recovery without already knowing `"cancelar"`). |
| **O5 (map-only)** | Leaves a reproduced, CLI-evidenced data-corruption bug (G14) undocumented as *fixed* while the map would claim awareness of it — worse than not touching the map at all. |

---

## 4. Implementation blast radius (for the future Implementation Contract — not now)

| Slice | File(s) | Change shape |
|---|---|---|
| 1 (G14) | `src/jarvis/core/orchestrator.py` | `_handle_component_description`'s two force-* blocks (propellers, frame) gain the ★4 tiebreak. No new module. |
| 2 (G12/G8) | `src/jarvis/core/orchestrator.py`, possibly a new small helper module (e.g. `core/acquisition_retarget.py`) if Engineer wants it separated from `orchestrator.py`'s size | New retarget-or-refuse check, consulted at the top of `_handle_component_description` and reused by the C-040 engineering-intent gate so both G12 and G8 share one policy (★2) |
| 3 (G15) | `src/jarvis/core/motor_catalog_assist.py` (★6), `src/jarvis/core/param_definition_session.py` (★5) | Messaging fix + new list-motors pattern check, mirrors G10 ★8's shape but lives in this subsystem's own turn handler, not `intent_resolver.py` |
| 4 (G11) | `src/jarvis/core/orchestrator.py` | `_should_preempt_iterate_wizard` reorder + `_iterate_owns_component_input` step-coverage extension (★3) |
| Doc-only (any slice) | `docs/system_map/CONNECTIONS.md`, `03_acquisition/ACQUISITION_MAP.md`, `01_runtime/RUNTIME_MAP.md` | Per investigation §2.3 — proposed text only, not applied by this design |

`library/materiales/_datos.json`, G10's `domains/materials.py`, G9's Continuity catalog-gap code, Catalog Impl C — **not touched by any slice**.

### Test plan sketch (P1–P8 → regression tests)

| Probe | Becomes | Slice |
|---|---|---|
| P1 (motors expected + `"1x 2306 2400KV 50W"`) | Regression: asserts `suggested_key=="motors"` (or an honest re-prompt), never `"propellers"` | 1 |
| P2 (motors expected + bare `"10x4.5"`) | Regression: confirms FN-019's own propeller case is *not* broken by the ★4 tiebreak (single-member expected_keys still forces correctly) | 1 |
| P3 (battery open → `"definir frame"`) | Regression: asserts either honest retarget or honest refuse — never the silent battery-brief re-show | 2 |
| P4 (`pending_*` vs Continuity next block dump) | Regression: confirms Slice 2 doesn't reintroduce an FN-021-class stale-field bug (dump session fields before/after) | 2 |
| P5 (`"ayúdame a elegir"`, motor_count=1, prop 5", req ≥37.7) | Regression: `format_no_thrust_candidate_message`'s max quote matches the filtered set | 3 |
| P6 (list-motors phrasing mid-wizard) | Regression: deterministic list response, 0 LLM | 3 |
| P7 (`"cambiar material"` → `"pvc"` / `"cambiar a pvc"`) | Regression: neither phrasing preempts at step 2; both still function as valid wizard answers | 4 |
| P8 (IDLE `"qué materiales tenemos"` vs DEFINE_MISSING list-motors) | Regression: confirms the two list-* escapes (G10 ★8 materials, this cut's motors) don't cross-collide | 3 |

Each slice also needs: existing FN-011…021, FN-019, `test_propulsion_composite_wizard_flow.py`, `test_iterate_session.py`, `test_g10_materials_frame.py` suites green (no regressions).

---

## 5. Out of scope (restated from contract)

- G9 Continuity `catalog_ref` honesty fix — no shared symbols with any of the four slices.
- G13 opaque `PVC 400g` iterate parse.
- G10 materials/keywords — untouched; investigation §5 confirms G10 did not cause G11, narrowing it would be the wrong fix.
- Catalog Impl C / battery-prop UX / BOM.
- Conversation Engine / Step D / dual-dispatch rewrite — none of the four slices need one; every fix is a bounded, local check inside existing functions.
- R3 formalization as a named, separate architecture — Slices 2 and 4 absorb R3's *substance* for this specific bundle (G8/G12, G11) without declaring a new standalone R3 subsystem. Whether this counts as "R3 absorbed" or "R3 remains a separate future formalization for cases beyond this bundle" is Engineer's call — this design takes no position beyond closing the bundle in front of it.

---

## 6. System Map implications

Per investigation §2.3:

- `CONNECTIONS.md` C-052 → add the caveat text drafted there (report-only).
- `03_acquisition/ACQUISITION_MAP.md` "Known issues: None" (already stale per SYS-MAP-004 for G8) → extend with G11/G12/G14/G15 pointers.
- `01_runtime/RUNTIME_MAP.md`'s nested DEFINE_MISSING pseudocode → refresh for G10's already-landed additions (list_materials check, force-frame) — independent housekeeping, not gated on this design's ★ lock.
- New `C-xxx` candidates once a slice lands: an ID for the Acquisition Target Authority helper itself (Slice 2) would give G12/G8's fix a first-class registry entry the way C-105/C-106 did for the Handoff Context (FN-024) — recommend reusing that precedent's shape (a small typed helper, its own connection ID, referenced from both call sites) rather than inventing a bespoke pattern.
- None of this is applied in this cut — text only, per contract §6.4.

---

## 7. Acceptance scenarios for the later CLI probe

```text
# Slice 1
propulsion wizard open (motors+propellers pending)
"1x 2306 2400KV 50W"  → saved as motors (or honest re-prompt), never "Hélices registradas"

# Slice 2
battery wizard open
"definir frame"  → either retargets honestly or refuses with a one-line "cancelar primero" —
                    never silently re-shows the battery brief

# Slice 3
thrust wizard open, no candidates for the filtered requirement
"ayúdame a elegir"  → message's "máximo cubierto" matches the same filter as "no tengo un motor"
"que motores tenemos"  → deterministic list, 0 LLM

# Slice 4
iterate wizard, step 2, variable=material
"cambiar a pvc"  → applies as the material value, does NOT preempt/clear the wizard
"pvc"            → same

# Overall success criterion (Engineer, contract §6.1.7)
new project → propulsion → battery → frame, declared in full, WITHOUT "cancelar" as a required step
```
