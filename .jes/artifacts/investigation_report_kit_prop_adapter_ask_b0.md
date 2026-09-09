# Investigation Report — Prop adapter ask (after hélices; novice; no inferred need)

**IC:** [investigation_contract_kit_prop_adapter_ask_b0.md](investigation_contract_kit_prop_adapter_ask_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint:** package `0.3.8` · suite 2514

**Do not implement — this is a read-only report. No `src/`/library edit made.**

---

## Executive summary

Geometric inference is dishonest on the current catalog: only **1 of 22** motors states `shaft_diameter_mm`, only **1 of 18** propellers states `shaft_bore_mm`, and they are two *different* SKUs — no motor/propeller pair in the library has both sides of a comparable shaft-fit fact. The live-bound pair (EMAX motor + `gf_5045x3`) has a motor shaft (3.0mm) and a propeller **hub outer diameter** (5.0mm, not a bore) — comparing them would compare two unrelated measurements. **B-naive (infer from hub/shaft) is refused.**

I reconstructed the exact Continuity bug the Engineer flagged (empirically, on a synthetic mid-architecture state): once all 7 architecture keys exist as declared components but a composite block's *params* are still missing, `derive_architecture_progress` correctly reports `"1/4"`, yet `build_project_continuity` already says `"Define el componente pendiente: power_connector."` — because BOM's `missing` list is presence-only and kit keys are appended after all architecture keys, so kit keys surface as soon as every architecture *component* exists, regardless of whether the block is actually "complete." This same mechanism, if reused unmodified for `prop_adapter` (Buy **B2**), would **not** surface the ask "right after hélices, before ESC" — it would surface only once ALL 7 architecture keys are non-missing, i.e. essentially at the same late moment power_connector already (prematurely) does. Only Buy **B1** — a narrow, one-off insertion into the propulsion composite wizard's own post-save "still missing" sequencing — actually fires at the Engineer's literal described moment. **Default recommendation: B1**, scoped as a single hardcoded check (not a generic condition engine, consistent with N3).

---

## A. Why Jarvis cannot know (need is not computed)

| Fact | Count | Detail |
|---|---|---|
| Motors with `shaft_diameter_mm` | **1 / 22** | Only `emax_rs2205s_2300` (3.0mm) — every other motor SKU has no shaft figure at all |
| Propellers with `shaft_bore_mm` | **1 / 18** | Only `apc_10x6_ep` (6.35mm) — a 10×6 electric-pusher prop, unrelated to any 5" FPV build |
| Propellers with `hub_diameter_mm` | **3 / 18** | `apc_10x6_ep` (20.3mm), `dal_7040` (5.0mm), `gf_5045x3` (5.0mm) |
| Motor/propeller pair with BOTH a cited shaft AND a cited bore | **0** | The one motor with a shaft figure (EMAX) and the one propeller with a bore figure (APC 10x6EP) are not the same build's pair, not even compatible sizes (5" racing motor vs. 10" pusher prop) |
| Live-bound pair (`emax_rs2205s_2300` + `gf_5045x3`) | shaft 3.0mm vs. **hub** 5.0mm | `hub_diameter_mm` is the plastic boss's own **outer** diameter (a prop-side fact used for the prop's own footprint/mass context, seeded in Propeller B0+B1), not a bore/hole diameter — comparing it to a motor's shaft diameter conflates two different physical measurements. `gf_5045x3.shaft_bore_mm` is `None`. |

**Explicit refusal of the "wrong next step":** comparing `gf_5045x3.hub_diameter_mm` (5mm, an outer boss diameter) against any motor's `shaft_diameter_mm` would be comparing a diameter that isn't a hole to a diameter that is a shaft — never a valid mount-fit check, even before considering that 21 of 22 motors have no shaft figure to compare against at all. **No hub-vs-shaft gate is proposed anywhere in this report.**

---

## B. Candidate Buys (ranked)

| ID | Shape | Assessment |
|---|---|---|
| **B-naive** | Infer adapter need from hub/shaft numbers | **Refused.** Section A proves the data doesn't exist to support it on today's catalog, and even where partial data exists (hub vs. shaft) it's the wrong physical comparison. |
| **B0** | Park — keep only the two existing kit keys; ask about the adapter in a later Buy | Safest, zero new code, but does not address the Engineer's ask at all — a novice with a real hub/collet build still sees nothing about how to mount the propeller until some later, unspecified Buy. |
| **B2** | No wizard insert — `prop_adapter` becomes a new, presence-gated kit-style key (visible only once `motors` AND `propellers` are both present, reusing Board slot / BOM `missing` / IDLE DEFINE / Continuity exactly like `power_connector`/`signal_harness`) | **Smaller hook, but does not hit the described moment** — see §C/§D below: kit-style keys are appended *after* all architecture keys in `bom_and_board_expected_keys`'s ordering, so `prop_adapter` would only surface via Continuity's `missing[0]`/the Board slot list once `esc` (and every other architecture key) is *also* already present — i.e., the same late-in-the-walk moment `power_connector` already (per the reconstructed bug above) surfaces prematurely, not "immediately after hélices, before ESC." |
| **B1** | Insert the Brief directly into the propulsion composite wizard's own sequencing, immediately after `propellers` leaves the wizard's "still missing" list and before `esc` is prompted | **The only candidate that actually fires at the Engineer's literal described moment.** Higher cost than B2 (touches the composite-wizard's own internal sequencing, one specific `orchestrator.py` function, one specific block), but it is a single, narrow, hardcoded conditional — not a new subsystem, not a generic "insert-after-N" engine (see §C for the exact 3-line-shaped hook). |

**Default lean: B1.** The IC invites picking "the smaller hook that still hits that moment" only if both candidates actually hit that moment — I found, empirically and by code inspection, that B2 does **not**: it inherits the exact ordering property that already makes `power_connector` nag too late (per the reconstruction below), which is the opposite of what the Engineer asked for. B1's extra cost is real but narrow: one additional conditional branch inside `_handle_component_description`'s existing post-save "still missing" computation, scoped to the `propulsion` block only, never a new wizard mode.

---

## C. Hook map (exact functions/files — no patches)

**Reconstructed premature-nag bug (empirical proof that B2-style ordering doesn't hit "right after hélices"):**

Built a synthetic `ProjectState` — all 7 architecture components declared (`motors`/`propellers`/`esc`/`battery`/`frame`/`flight_controller`/`sensors`, each with some properties) but `current_parameters` deliberately withholding `motor_power_w`/`battery_capacity_wh` (so `propulsion`/`energy` are genuinely still "in_progress", not "complete") and no `power_connector`/`signal_harness` declared yet:

```
build_component_bom(state)["missing"]        == ["power_connector", "signal_harness"]
derive_architecture_progress(state)["progress"] == "1/4"   # propulsion still in_progress
build_project_continuity(...)["next_useful_step"] == "Define el componente pendiente: power_connector."
```

This proves the current, already-shipped kit-key ordering (`bom_and_board_expected_keys` in `src/jarvis/core/system_architecture_catalog.py`: `blocks_to_component_keys(blocks)` first, kit keys appended after — confirmed by reading the function directly) makes a kit key win Continuity's rank 4 (`elif missing:` in `src/jarvis/core/project_continuity.py`) as soon as every architecture **component** merely *exists*, even while the architecture is provably still only "1/4" by the PASS-relevant definition. **A `prop_adapter` key built the same way would inherit this exact property** — it would not surface until `esc` (and every other architecture key) is *also* non-missing, never "immediately after hélices, before ESC."

**Where B1's insertion point actually is:**

- `src/jarvis/core/orchestrator.py`, `_set_pending_next_block` (composite branch, `elif block_type == "composite":`): on a fresh open of `propulsion`, `missing_component_keys = [k for k in BLOCK_TO_COMPONENTS["propulsion"] if components.get(k) is None or completeness == "low"]` — for a brand-new project this is `["motors", "propellers", "esc"]`, all opened as **one** `pending_missing_params` scope (confirmed by reading the code directly — not three separate wizard opens).
- `src/jarvis/core/orchestrator.py`, `_handle_component_description`: after a save, `still_missing = [k for k in expected_keys if components.get(k) is None or completeness == "low" or (...)]` is recomputed, and `follow_up = self._component_prompt_for_first_missing(still_missing)` asks about `still_missing[0]` — this is the **exact** mechanism that makes the wizard feel sequential (motors → propellers → esc) even though all three share one `expected_keys` scope. **B1's hook is here**: when `expected_keys` is (or reduces to) `["propellers", "esc"]`-shaped for the `propulsion` block specifically, and `motors`+`propellers` are both now present, insert `"prop_adapter"` at the front of `still_missing` (ahead of `"esc"`) — a single conditional, gated on the block being `propulsion` and both `motors`/`propellers` present, never a generic "insert conditionally" framework.
- `_component_prompt_for_first_missing` (same file) already resolves a prompt string generically from whatever key is `keys[0]` — reusing the existing `COMPONENT_PROMPTS`/kit-style Brief machinery (from kit B1-min) for `prop_adapter`'s own prompt ("¿Cómo montas la hélice? Va directa / con adaptador — o dejarlo pendiente.") needs zero new prompt-rendering code, only a new `COMPONENT_PROMPTS["prop_adapter"]` entry (a future IC's concern, not this investigation's).
- The existing kit-key relabel fix (added in the kit B1-min cycle, same file, right after the frame-force block in `_handle_component_description`) — the one that lets a free-text description of a kit key with no `ComponentRule` actually save via `set_control_component` — **already generalizes to any key in `KIT_HOME_BLOCK`**, so `prop_adapter` would only need a `KIT_HOME_BLOCK`-style membership (or an equivalent flat set) to reuse that same relabel path for free-text answers like "va directa" — no new inference code.

**Who must NOT list `prop_adapter` at create:** `SYSTEM_ARCHITECTURES`/`get_domain_architecture` (`system_architecture_catalog.py`) — the project-create block proposal — must never gain a `prop_adapter`-aware block; and `KIT_TO_COMPONENTS` must not simply list `prop_adapter` unconditionally the way `power_connector`/`signal_harness` are listed today, because `kit_component_keys`'s only existing gate (`KIT_HOME_BLOCK.get(key) in blocks`) fires the moment a *block* is declared (at architecture setup, before any component exists) — exactly the "nags before any hélice" failure mode the IC's own "wrong next step" list names. A `prop_adapter` gate needs a **new**, different predicate (component presence, not block declaration) — `kit_component_keys` has no such predicate today; adding one is a small, additive extension (an optional presence-check parameter, or a second small dict alongside `KIT_HOME_BLOCK`), not present in the codebase yet.

---

## D. Twin / non-goals

- **PASS/hover/autonomy byte-identical regardless of which Buy is chosen**: neither B1 nor B2 touches `BLOCK_TO_COMPONENTS`, `_block_progress_status`, or any composite-block param/component list — confirmed by design (B1's hook only reorders which key `_component_prompt_for_first_missing` is shown next within an *already-open* wizard scope; it never adds a new key to any `BLOCK_TO_COMPONENTS` list or to what `_block_progress_status` reads).
- **Connector/harness timing unaffected either way**: `_try_start_kit_component_from_mention` (the kit-key IDLE bridge shipped in kit B1-min) already gates on `_next_pending_block(project_state) is None` — i.e. it structurally cannot fire while the propulsion wizard is open, regardless of whether `prop_adapter` is added via B1 or B2. B1's insertion lives entirely inside the *already-open* composite wizard's own turn-by-turn flow and never touches that gate.
- **B1 does not steal the turn for connector/harness**: the new conditional is scoped to the `propulsion` block's own `still_missing` computation only — it has no interaction with `energy`/`control`'s wizards or with the kit-key IDLE/Continuity paths `power_connector`/`signal_harness` already use.
- **XT60/harness catalog SKUs are out of this investigation** (per lock) — nothing here proposes a `library/*.json` row for any connector/adapter family; `prop_adapter`'s own eventual catalog identity (if any) is explicitly a separate, later ★.
- Stance #7 (an optional future honesty clause comparing a *cited* shaft to a *cited* bore, only once both exist on the SAME bound pair) is **not** proposed as this investigation's default Buy — Section A shows zero such pairs exist today, so there is nothing for that clause to fire on yet; it remains a valid, cheap future addition once/if such a pair is ever seeded, not blocking B1.

---

## Explicitly not this investigation

Implementing `prop_adapter` (no code written — confirmed via `git diff`, empty for all `src/`/`library/` files) · editing `KIT_TO_COMPONENTS`/`BLOCK_TO_COMPONENTS` (untouched) · a catalog adapter/connector family (no library row added) · Conversation Engine · `"cabe"` · plate L×W · XT60/harness SKU rows (a later ★, per lock).
