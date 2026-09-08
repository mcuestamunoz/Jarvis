# Investigation Report — Catalog-bound Property Freshness B1 (ESC stale mass + rebind gap)

**IC:** [investigation_contract_catalog_bound_property_freshness_b1.md](investigation_contract_catalog_bound_property_freshness_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2385 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B1 — Refresh-from-`catalog_ref`, generalized across every `bind_*_from_catalog` family (motor/battery/propeller/ESC/frame), not ESC-only.** The refresh primitive already exists and requires zero new merge logic: every one of the five `bind_*_from_catalog` functions already supports a `base=<existing spec>` parameter whose `model_copy` only overwrites `properties`/`completeness`/`catalog_ref`, leaving every other field — critically `mounted_on`, `name`, `parent_key` — untouched. I proved this empirically on the actual stale demo project: `bind_esc_from_catalog(sku, base=esc_spec)` turns `mass_g` `26.0 → 15.0` while `mounted_on="frame_plate"` and `catalog_ref` survive byte-identical. **The missing 5% is a thin writer (dispatch by `catalog_ref.family`) and one Continuity IDLE phrase — not new binding logic.** B0 (walk-only) is not merely inconvenient — I verified it is actively unsafe today: the only tool a user could currently reach for (re-declaring "ESC 40A" in free text) routes through `set_control_component`, which does a wholesale dict replace and would silently drop `mass_g`, `catalog_ref`, *and* `mounted_on` — a strictly worse outcome than leaving the stale 26g alone. B1+ (a full ESC picker) is unjustified scope: the catalog has exactly one ESC row, so a picker would present a one-item list to solve a problem a plain "refresh" verb already solves with less surface area. B2 (auto-refresh on load) is correctly out — Locked Stance 3 and this IC's own stop condition forbid it, and it would also silently overwrite a user's own subsequent free-text edits to the same fields with no visible cause.

---

## 2. Evidence table

| Surface | Finding | Cite |
|---|---|---|
| ESC seed | `hobbywing_xrotor_40a_6s.mass_g` = **15** (corrected from the prior ESC mass hygiene B1 IC) | `library/esc/_datos.json:16` |
| Demo project `esc` component | `catalog_ref={family:esc, sku:hobbywing_xrotor_40a_6s}`, `properties.mass_g=26.0`, `mounted_on="frame_plate"` — all other properties (`current_a`, dims) match the live seed exactly | `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` (read live) |
| Same project's other 3 catalog-bound families (motors/battery/frame) | **Zero mismatch** — every bound property (`thrust_n`, `weight_g`, stator dims, `battery_capacity_wh`, `mass_g`, battery dims, frame `mass_kg`/`size_class_inch`/`material`) matches the current live seed exactly. Staleness is isolated to ESC in this project. | Cross-checked project JSON against `library/motores`, `library/baterias`, `library/frames` live seeds |
| `bind_esc_from_catalog` | Docstring: *"No CLI/UX entry point calls this yet — no ESC catalog-pick wizard exists in Continuity/orchestrator; exposed as a deterministic, test-callable/script-callable API."* Confirms N4's own claim and explains how the demo project got `catalog_ref` set at all (only reachable via a script/test call, never a real product path). | `src/jarvis/core/catalog_bind.py:214-227` |
| `set_esc_component` writer | **Does not exist** — confirmed via grep, zero hits anywhere in `component_writers.py` or `orchestrator.py`. | grep, zero hits |
| ESC free-text write path (the only path that exists today) | `orchestrator.py:2588-2595`: any ESC declaration (catalog-bound or not) routes through the generic `set_control_component(project_state, spec)` (`component_writers.py:288-300`), which does `{**components, key: spec}` — a **wholesale replace**, no merge, no preservation of `mounted_on`/`catalog_ref` from the prior entry. | `orchestrator.py:2588-2595`, `component_writers.py:288-300` |
| `extract_esc_properties` (what free text actually extracts) | Only `current_a` (regex `\d+\s*a\b`) — **no mass, no dims, no catalog identity.** Re-declaring "ESC 40A" today would not merely fail to fix the stale mass — it would delete it, along with the catalog identity and the mount relation. Verified this is not a viable "walk." | `src/jarvis/domains/aerial.py:136-143` |
| `catalog_rebind_assist.resolve_idle_catalog_rebind` | Families: `frame`, `motors`, `propellers`, `battery` only — **no `esc` entry in `_FAMILY_NOUN_PATTERNS`.** Confirms the IC's own claim; not a bug, an intentional B3 scope line (per that IC's own "explicitly Not ESC/FC/sensors"). | `src/jarvis/core/catalog_rebind_assist.py:26-31` |
| `invalidate_diverged_catalog_refs` | Covers **motor** (`thrust_n` vs `current_parameters`), **battery** (`battery_capacity_wh` vs params), **frame** (mass/size vs the *live* `FrameSpec`, or `structure_mass_override_kg` vs params) — **zero ESC branch.** Called from exactly 2 sites, both **turn-triggered** (`actions/iterate.py:158`, `orchestrator.py:4427` inside DSE-apply) — **never on Board load/read.** | `src/jarvis/core/catalog_bind.py:459-584`; call-site grep |
| Frame's own "seed changed after bind" branch (case 2 of 3) | *"the bound component's own `mass_kg`/`size_class_inch` no longer match what the live `FrameSpec` declares → clear (catches a corrected/removed seed row)."* This is architecturally the **closest existing precedent** to the ESC scenario — but it **disowns** (clears `catalog_ref`, renames to `_DIVERGED_FRAME_NAME`) rather than **refreshes** the stale number, which is a different fix for a different problem (see §4A2). | `src/jarvis/core/catalog_bind.py:499-517,553-580` |
| `bind_*_from_catalog`'s `base=` merge pattern | All 5 binders (motor/battery/propeller/ESC/frame) share the identical shape: `base.model_copy(update={"properties": merged, "completeness": ..., "catalog_ref": ...})` — every other field on `base` (including `mounted_on`) survives untouched. Confirmed by grep (5 `base.model_copy` call sites) and by direct empirical test on the live demo project's ESC spec (below). | `src/jarvis/core/catalog_bind.py:82,149,197,260,329` |
| **Empirical proof** | `bind_esc_from_catalog(esc.catalog_ref.sku, base=esc)` on the actual demo project's live ESC spec: `mass_g` 26.0 → **15.0**; `mounted_on` stays `"frame_plate"`; `catalog_ref` unchanged; `current_a`/dims unchanged (already matched). Ran this session, not hypothetical. | this session's live Python REPL trace |

---

## 3. Answers A–E

### A. Mechanism

**A1 — Why does `catalog_ref` + stale `mass_g` coexist after seed edit?** Confirmed exactly per N4: `bind_esc_from_catalog` (and every `bind_*` function) only runs **at bind time** — it projects the seed's *current* value into the `ComponentSpec` once, then that `PropertyValue` is a plain, static, persisted fact in `state.json` with no ongoing link back to the seed file. Editing the seed JSON later (the ESC mass hygiene B1 IC) has zero effect on any project that already bound before the edit — there is no mechanism anywhere that re-reads the library for an already-bound component outside of an explicit re-bind call.

**A2 — Does divergence invalidation fire for ESC mass? If not, is that a gap or intentional?** It does not fire — ESC has no branch in `invalidate_diverged_catalog_refs` at all. This is **not simply a gap to fill with an ESC branch mirroring frame's**, because frame's "seed changed" branch solves a *different* problem than this IC asks about: it **disowns** the SKU (clears `catalog_ref`, renames the component) rather than **refreshing** the stale value. Applying that same disown-only pattern to ESC would leave the Board still showing `26g`, just now unlabeled as `hobbywing_xrotor_40a_6s` — it would not make the product sentence ("Board numbers match the cited seed") true. The two mechanisms are complementary, not substitutes: disown-on-divergence protects against a *different* SKU's data leaking through (or a future params-bypass mutation), while refresh-from-catalog_ref is the tool this IC actually needs — a component whose identity is still correct, but whose historically-projected numbers predate a seed correction.

### B. Product paths

**B3 — Minimum path to make the demo Board show 15g honestly?** Call `bind_esc_from_catalog("hobbywing_xrotor_40a_6s", base=<existing esc spec>)` and persist the result — proven above to work with zero side effects on `mounted_on`/`catalog_ref`/other properties. The only genuinely missing piece is a caller: a thin writer (so this isn't done ad hoc via a script) plus one Continuity IDLE phrase to trigger it.

**B4 — ESC-only or generic?** **Generic — the marginal cost is effectively zero.** All 5 `bind_*_from_catalog` functions already share the identical `base=` merge shape (§2). A single writer that dispatches on `catalog_ref.family` (`"esc" → bind_esc_from_catalog`, `"motor" → bind_motor_from_catalog`, etc. — the same dispatch-by-family shape DSE-apply code elsewhere in the codebase already uses) covers every catalog-bound family for the price of writing it once. Scoping it to ESC-only would be an artificial restriction with no cost savings, and would leave the exact same staleness class latent for the next motor/battery/frame seed hygiene fix.

### C. Continuity / UX

**C5 — Full picker or no-picker refresh?** **No-picker refresh is enough, and is the more honest choice.** The identity is not in question (that's what a picker is for — choosing *among* SKUs); only the *projected numbers* are stale. A picker would force the user through a redundant "choose 1 of 1" flow for ESC specifically, and for other families would falsely imply the user might want a *different* SKU when the actual need is "make the current one's numbers current." A verb like "actualiza el esc desde catálogo" / "refresca el esc" maps naturally to this and is a smaller Continuity surface than reusing/extending the full `cambiar X` rebind flow.

**C6 — Honest copy after refresh?** Must name what changed and from where, e.g. *"ESC actualizado desde catálogo: mass_g 26 → 15 (hobbywing_xrotor_40a_6s)."* Forbidden: "corregido automáticamente" (implies the system found and fixed an error on its own initiative — it did not; the user asked), "verificado," "ahora es correcto" (the number is *current*, not independently *verified*). The copy should read as "you asked, here is what changed," mirroring the honest, no-overclaim tone already established for `mounted_on`'s own confirmation copy ("Declarado: X montado en Y").

### D. Buy options — reversal criteria

| Option | Verdict | What would change it |
|---|---|---|
| B0 — Walk only | **Rejected — not just weaker, actively unsafe.** Proven: the only reachable "walk" (free-text ESC re-declare) destroys `mass_g`, `catalog_ref`, and `mounted_on` via `set_control_component`'s wholesale replace. | If a safe walk existed (it doesn't) — e.g. if `set_control_component` merged instead of replaced. That would itself be a code change, so "B0 truly no-code" is not realistically available for this specific case. |
| **B1 — Refresh-from-`catalog_ref`, generic** | **Recommended.** Minimal, reuses proven-safe existing merge semantics, generalizes for free. | — |
| B1+ — Full ESC picker | Rejected as over-scoped for a 1-SKU family; revisit only if/when a second ESC SKU is ever seeded (making "which one" a real question again). | A second ESC catalog row being added. |
| B2 — Auto-refresh on load | Rejected per Locked Stance 3 and this IC's own stop condition. | Nothing short of a separate, explicitly-scoped Engineer ★ reopening the "silent state mutation" question generally — out of scope for this investigation to entertain further. |

### E. Out-of-scope checklist

- Fase 2 (geometry-for-all): **untouched** — this investigation never proposes new geometry fields, only re-projecting fields that already exist on already-shipped `bind_*` functions.
- Fase 3 (mount-connect): **untouched** — `mounted_on`/Board edges were only read to confirm they survive a refresh; no change to their behavior is proposed.
- Fit / pose: **untouched** — not referenced anywhere in the recommended Buy.
- Here3/Pixhawk identity freeze: **not implicated.** Flagging only, as instructed: `FLIGHT_CONTROLLER_DIMENSIONS` (the FC identity-linked dims table) has no `bind_*_from_catalog`-style function or `base=` merge parameter at all (FC has no `CatalogRef.family` entry — confirmed in the prior FC Geometry investigation) — so a generic "refresh from `catalog_ref`" writer has **no FC branch to dispatch to** and cannot touch Here3/Pixhawk even by accident. No unfreeze proposed or required.

---

## 4. Risks if we Buy wrong

- **Buying B0** (or Engineer manually "walking" it) risks exactly the destructive outcome proven in §2/§B — a well-meaning free-text re-declare that silently deletes `mounted_on` and the catalog identity while leaving `mass_g` just as wrong (or worse, gone entirely from a fresh freeform spec that never asked about mass at all).
- **Buying B1+ (full picker) prematurely** spends UX/Continuity-parser effort (a bigger surface than B1's single verb) on a problem a 1-item picker cannot meaningfully differ from a no-picker refresh — pure overhead for this catalog's current shape.
- **Buying B2** risks a silent-mutation product regression: a user's own manually-corrected/overridden property (say, they'd already free-text-adjusted `mass_g` for a physically-modified ESC) could be wiped by an unsolicited load-time refresh with no visible trigger — the exact class of trust violation this whole investigation exists to prevent, just moved to a different silent-mutation vector.
- **Scoping B1 to ESC-only** risks under-delivering relative to its near-zero marginal cost, and leaves the identical staleness class dormant for the next motor/battery/frame seed correction — a foreseeable near-term repeat of this exact investigation.

---

## 5. Field / API sketch (contingency — not an IC)

```text
# component_writers.py (new, thin — no new catalog_bind logic needed)
def refresh_component_from_catalog(project_state, key: str) -> ProjectState:
    """Re-project a catalog-bound component's physicals from the CURRENT
    seed, preserving mounted_on/name/parent_key/everything else via the
    existing bind_*_from_catalog(base=...) merge. No-op (or honest error)
    when the component has no catalog_ref — nothing to refresh."""
    spec = project_state.design_properties.components.get(key)
    if spec is None or spec.catalog_ref is None:
        raise ValueError(f"'{key}' no está vinculado a catálogo — nada que actualizar.")
    family = spec.catalog_ref.family
    binder = {"esc": bind_esc_from_catalog, "motor": bind_motor_from_catalog,
              "battery": bind_battery_from_catalog, "frame": bind_frame_from_catalog,
              "propeller": bind_propeller_from_catalog}[family]
    refreshed = binder(spec.catalog_ref.sku, base=spec)
    # ... write into components[key], same shape as every existing writer
```

Continuity: one new IDLE gate phrase family (`actualiza/refresca <componente> desde catálogo`), dispatched the same way `mounted_on_declare_assist` is — deterministic parse, no LLM, calling this writer directly. Confirmation copy per §C6. **This sketch is illustrative only — a Cursor-authored IC would size and lock the exact function name, phrase list, and error copy.**

---

## 6. Explicit note for Engineer

The demo project `autonomía-de-10min-9ada1a1b0cca` will keep showing ESC `mass_g=26` on the Board until either (a) a B1-shaped IC ships and the Engineer runs the new refresh path on that project, or (b) someone with direct script/REPL access calls `bind_esc_from_catalog(sku, base=existing_spec)` manually (exactly the call proven safe in §2) and re-saves the state file outside of any product UX. **No existing product action fixes this today, and the one action that might seem to (re-declaring the ESC in chat) actively makes things worse.** This report recommends against using that free-text workaround even as a stopgap.
