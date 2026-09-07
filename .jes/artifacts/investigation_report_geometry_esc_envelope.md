# Investigation Report — ESC Declared Envelope (Geometry axis, next family)

**Project:** Jarvis
**Date:** 2026-09-07
**Investigator:** Claude Code
**Contract:** [investigation_contract_geometry_esc_envelope.md](investigation_contract_geometry_esc_envelope.md)
**Parents:** Battery B1 CLOSED suite 2316 · Motor B1 CLOSED suite 2323
**Status:** OPEN — for Cursor review → Engineer ★ on Buy shape

**Not an Implementation Contract. No `src/` edits made.** The seed row's own cited `source_url` (`a.hobbywing.com`) fails TLS validation (cert mismatch, confirmed live this session) — re-fetched via the working `www.hobbywing.com` mirror of the same product, same finding already flagged and worked around in the Battery investigation.

---

## A. Executive answer

`EscSpec` (`library.py:141-160`) has zero geometry fields — confirmed. The catalog has exactly **1** ESC row (`hobbywing_xrotor_40a_6s`), `identity_status: verified`. Re-fetching its source page live surfaced something Battery/Motor didn't: the page describes **4 distinct physical SKU variants** of the same electrical spec (40A/60A, 2-6S) at **2 different sizes** — 42.0×21.6×12.0mm (with pre-attached output wires, 18.5g) or 50.0×21.6×12.0mm (bare pads, no wires, 15g) — and the size difference is real, not noise (it's the wire-exit housing). The seed row **already carries a `part_number` ("30901001")** that disambiguates cleanly to one specific variant — International/Asian "B," 50.0×21.6×12.0mm — so this is seedable honestly with zero guessing, using the identity the catalog already declared rather than inventing a choice. **One data-quality note, flagged not fixed**: that variant's page-stated weight is 15g, but the seed's existing `mass_g` is 26 — a real discrepancy, pre-existing, out of this IC's scope to resolve. Binding path is the easy case: `bind_esc_from_catalog(sku, *, library=None, base=None)` (`catalog_bind.py:214-226`) is already Battery-shaped (SKU-first, no `MotorSuggestion`-style indirection) — extending it is a direct copy of Battery's own pattern. One genuine divergence from Battery/Motor: **no production catalog-pick UX calls `bind_esc_from_catalog` at all** (confirmed by search — zero call sites in `orchestrator.py`), so unlike Battery (whose "no UX yet" docstring turned out to be stale) this one is still accurate — ESC dims would reach a real user's Board only if/when an ESC catalog-pick flow is ever built, not today. Field bag: reuse Battery's box vocabulary verbatim (`length_mm`/`width_mm`/`height_mm`) — the page itself labels the table "Size (mm)," confirming ESC is genuinely box-shaped, no divergence needed. **Recommend Buy: B1**, one SKU, three fields, `representar` only.

---

## B. As-is inventory + bind path

| Surface | Finding | Citation |
|---|---|---|
| `EscSpec` fields | `name, continuous_current_a, burst_current_a, continuous_current_source, voltage_min/max, cells_min/max, esc_topology, channels, mass_g, manufacturer, model, part_number, source_url, identity_status, source_note` — zero geometry fields, confirmed by full read | `library.py:141-160` |
| Seed rows | **1 total.** `hobbywing_xrotor_40a_6s`: `manufacturer=HOBBYWING`, `part_number=30901001`, `esc_topology=individual`, `channels=1`, `continuous_current_a=40`, `mass_g=26`, `source_url=https://a.hobbywing.com/en/products/xrotor-40a122`, `identity_status=verified` | `library/esc/_datos.json` |
| Source URL health | `a.hobbywing.com` TLS cert covers only `hobbywing.com`/`www.hobbywing.com` — fetch fails on the exact cited URL (confirmed live, same as the Battery investigation's earlier finding). The `www.` mirror of the same product page loads fine and is used for the quotes below — a pre-existing seed hygiene issue, not something this IC should silently patch. | live fetch, this session |
| `bind_esc_from_catalog` today | `bind_esc_from_catalog(sku: str, *, library: ComponentLibrary \| None = None, base: ComponentSpec \| None = None)` — projects `current_a` (from `continuous_current_a`) and `mass_g` (when present) only. Already the exact Battery/Propeller shape (SKU-first, library-lookup) — **no** `MotorSuggestion`-style complication, confirmed by direct read. | `catalog_bind.py:214-251` |
| Docstring honesty | *"No CLI/UX entry point calls this yet"* — **confirmed still true**, unlike Battery's equivalent claim (which the Battery investigation found stale). Grepped `orchestrator.py` for `bind_esc_from_catalog`/an ESC catalog-pick flow: zero hits. `"esc"` does appear as a recognized architecture key (`BLOCK_TO_COMPONENTS["propulsion"]`, `project_closure.py:515,554` — BOM/slot handling) and can be freeform-declared like any component, but no assisted catalog-pick wizard exists to reach `bind_esc_from_catalog` in production. | `catalog_bind.py:224-225`, grep confirmed |
| Board | Same generic mechanism as Battery/Motor, re-confirmed live this session: a `ComponentSpec` bound via `bind_esc_from_catalog("hobbywing_xrotor_40a_6s")` today shows exactly `{current_a: 40 A, mass_g: 26 g}` through `_fields()` (`spatial_board.py:181-189`) — adding dims would appear the same way, zero Board code needed. | live check, this session |
| Battery/Motor precedent | **Reused, not diverged**: box vocabulary applies as-is (ESC genuinely is a flat PCB module — the source page's own table header is "Size (mm)," not a cylinder/radial spec). No new field names needed, unlike Motor which had to diverge from Battery's box shape. | — |

---

## C. Minimum ESC geometric bag

| Field | Evidence | Verdict |
|---|---|---|
| `length_mm` | Page states `"50.0"` (first of `"50.0×21.6×12.0mm"`, unlabeled print order) for part `30901001` | **Accept** |
| `width_mm` | `"21.6"` | **Accept** |
| `height_mm` | `"12.0"` | **Accept** |
| A parallel ESC-only field name (e.g. `pcb_length_mm`) | No evidence anywhere that ESC's box needs different vocabulary than Battery's — the page literally uses the same "Size (mm)" framing a box-shaped battery pack page would | **Reject** — reuse Battery's `length_mm`/`width_mm`/`height_mm` verbatim, per locked stance #4 |
| A `mount_pattern_mm`/bolt-spacing field (e.g. FC/ESC "stack" 30.5mm standard) | Not stated anywhere on this page; this is an `esc_topology: "individual"` unit (a standalone ESC), not a 4-in-1 board where a stack-mount pattern would typically apply | **Reject for this SKU** — no source, and topologically the wrong shape of product to test the concept on; named as a real future question for a *4-in-1* ESC row, not decided here |

**Proposed bag: `length_mm`, `width_mm`, `height_mm` only** — identical field names to Battery, zero new vocabulary.

---

## D. Seedable SKUs + live source quotes

Re-fetched live this session (`www.hobbywing.com/en/products/xrotor-40a122`, the working mirror of the seed's cited `a.hobbywing.com` URL):

> "This product line includes four variants, all with identical electrical ratings but different physical configurations... International A (30901013): 42.0×21.6×12.0, 18.5g, 3× output wires. International B (30901001): 50.0×21.6×12.0, 15g, no output wires. Asian A (30901014): 42.0×21.6×12.0, 18.5g. Asian B (30901000): 50.0×21.6×12.0, 15g."

The catalog's `hobbywing_xrotor_40a_6s` row already declares `part_number: "30901001"` — matching **International B** (or equivalently Asian B, same dims) — so the size to seed is unambiguous, **not** a guess between the two physical sizes:

| SKU | `length_mm` | `width_mm` | `height_mm` | Mapping rule |
|---|---|---|---|---|
| `hobbywing_xrotor_40a_6s` | **50.0** | **21.6** | **12.0** | Verbatim print order (page states unlabeled `"50.0×21.6×12.0"` for part `30901001`, which the seed already cites) |

**Flagged, not fixed (out of this IC's scope):** the page states 15g for part `30901001`, but the existing seed's `mass_g` is 26 — a real discrepancy in a field this IC does not touch. Worth a separate, small data-hygiene note for Engineer/Cursor awareness; not blocking the geometry seed (mass and dims are independent facts, and the geometry axis has never re-verified mass for any prior family either).

No other ESC rows exist to seed or omit — this is a 1-row family.

**Binding path:** `bind_esc_from_catalog` needs no signature change (unlike Motor) — it already takes `sku`/`library`. Adding three `if spec.<field> is not None: projected[<field>] = PropertyValue(unit="mm", ...)` lines mirrors Battery's own `bind_battery_from_catalog` body exactly.

---

## E. Honesty / ladder matrix

| Implication | True if we add the proposed fields? | Over-claim risk | Desired wording |
|---|---|---|---|
| "We know the ESC's size" | **Yes, for this one row** — a real, cited, manufacturer-published fact, disambiguated by the catalog's own existing `part_number`. | Low. | "Dimensiones declaradas (fuente: catálogo, part_number 30901001)." |
| "Fits the stack" | **No.** No FC/ESC 30.5mm "stack" comparison is proposed or implied — this ESC's own 12.0mm `height_mm` is its *own* thickness, not a stack-height/clearance fact. Conflating the two would misuse a real number. | **High if ever implied** — this axis's recurring hazard (already named for Motor's excluded overall-height field); flagged explicitly here because "stack" is a real, adjacent FPV term this SKU's height could be mistaken for. | Never pair `height_mm` with any stack/mount sentence; that needs its own future evidence and Buy. |
| "Board = CAD" | **No.** Same as Battery/Motor — text rows on an existing card type. | Medium if marketed loosely. | Keep Board copy scoped to "declared component data." |
| "Same as Battery box" | **Partially true, and that's fine** — same vocabulary, same shape, same provenance discipline. Not the same claim as "this is the same *kind* of object" (an ESC and a battery pack are unrelated components that both happen to be boxes). | Low — reusing field names isn't claiming equivalence of the parts themselves. | No change needed. |
| "Visualization verifies" | **N/A — no visualization proposed.** | Low. | Same non-goal as Battery/Motor. |
| **(new, ESC-specific) "This is now definable/seeable in a real project"** | **Not really, yet.** No catalog-pick UX exists for ESC — this stays test-callable-only until/unless a future, separate IC builds one. Worth stating plainly so the ★ isn't read as "and now users see it." | Medium — the honest scope of *this* Buy is narrower in practical reach than Battery/Motor were, even though the code shape is identical. | Implementation report should say explicitly: dims are wired and tested, but no live user path binds an ESC to a catalog SKU today. |

**Ladder position:** rung 2, **`representar`** only — same rung as Battery/Motor, with the added honesty caveat above about current reachability.

---

## F. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 | Docs/vocab lock only | If Engineer wants to ★ field reuse (vs a new name) before code — low value here since the reuse case is unambiguous |
| **B1** | **Schema (3 fields on `EscSpec`, reusing Battery's names) + seed the 1 sourced row + `bind_esc_from_catalog` projects them + Board shows via existing generic path** | **Recommended — see below** |
| B2 | ESC + FC/stack in the same IC | Rejected — FC/stack introduces the 30.5mm mount-pattern concept, a genuinely different geometric idea (bolt spacing, not a box envelope) that deserves its own sourced investigation, not a bundled afterthought onto a 1-row ESC seed |
| B3 | Glyph/box preview | Not now — `visualizar`, premature |
| Defer | — | Not applicable — the one row is honestly seedable today, and the seemingly-blocking ambiguity (4 physical variants on one page) resolves cleanly via the catalog's own already-declared `part_number` |

### Default lean: **B1, ESC only, three fields, one SKU**

Smallest possible scope: reuses Battery's exact field names (no new vocabulary decision needed), reuses `bind_esc_from_catalog`'s existing SKU-first signature (no parameter change needed, unlike Motor), touches exactly one seed row. The one thing worth Engineer's explicit attention before ★: this Buy's real-world visibility is **narrower** than Battery/Motor's were, because no production ESC catalog-pick flow exists yet — the geometry will be correct and tested, but not reachable by a real user session until a separate UX IC ships. If Engineer wants the pattern to have live user impact immediately, that would be a *different*, larger Buy (build the ESC catalog-pick wizard first) — explicitly not recommended here, as it's a UX/wizard change, not a Geometry-axis schema change, and would reopen scope this axis has kept narrow on purpose.

**Suggested first IC title (for Cursor, not decided here):** *"ESC declared envelope (box, reusing Battery vocabulary) — representar only."*

---

## G. Non-goals for the first ESC IC

Fit/clearance/mount-pattern validation · CAD/FEA · Board glyph/box preview · Battery/Motor/Frame schema edits · FC/stack 30.5mm mount-pattern field (named as a real, separate future question for a 4-in-1-shaped row, not this one) · free-text ESC-dimension extractors · building an ESC catalog-pick UX (a separate, larger, non-Geometry-axis change) · fixing the seed's pre-existing `mass_g` discrepancy (flagged in §D, not this IC's job) · fixing the seed's dead `a.hobbywing.com` URL (same — flag only) · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims beyond the one disambiguated-by-`part_number` variant · weakening tests.
