# Investigation Report — Flight Controller Declared Geometry (Geometry axis)

**Project:** Jarvis
**Date:** 2026-09-07
**Investigator:** Claude Code
**Contract:** [investigation_contract_geometry_fc_envelope.md](investigation_contract_geometry_fc_envelope.md)
**Parents:** ESC B1 CLOSED suite 2327
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Review:** [investigation_review_geometry_fc_envelope.md](investigation_review_geometry_fc_envelope.md)  
**IC:** [implementation_contract_geometry_fc_envelope_b1.md](implementation_contract_geometry_fc_envelope_b1.md)

**Not an Implementation Contract. No `src/` edits made.** Every dimension claim below was re-fetched live this session from official/manufacturer pages, cross-checked across two independent sources where possible.

---

## A. Executive answer

Confirmed: `library/` has no FC family (`baterias, esc, frames, helices, materiales, motores` only — no `fc/`), and grepping `library.py` for "flight_controller" returns zero hits — no `FcSpec`, no loader, no `bind_flight_controller_from_catalog`. FC enters `components` **exclusively** through free-text inference: a `ComponentRule` (`aerial.py:741-749`) matches keywords ("pixhawk," "controladora," etc.) and calls `extract_flight_controller_properties` (`aerial.py:538-564`), which extracts **only** `model` from a closed vocabulary (`FLIGHT_CONTROLLER_MAP`, `aerial.py:523-535`) — confirmed live against the actual `autonomía-de-10min` project's `state.json`: `flight_controller` has `properties: {model: "pixhawk_4"}`, `catalog_ref: null`. Live-fetched Pixhawk 4's own official specs (PX4 docs + Holybro manufacturer page, independently agreeing): **44×84×12mm, ~15.8-49g depending on which sub-assembly/case is weighed** — no mounting-hole pattern stated on either page. Pixhawk 4 Mini's own page could not be located with usable spec content — excluded from this increment on that basis alone. **The minimum honest path does not require a new catalog family.** `extract_flight_controller_properties` already recognizes `"pixhawk_4"` as a canonical identity string; the smallest addition is a tiny **identity-linked dims table** living beside `FLIGHT_CONTROLLER_MAP` (same file, same mechanism, zero new subsystem) that the extractor consults *after* matching a model, attaching `length_mm`/`width_mm`/`height_mm` as ordinary `PropertyValue`s exactly as it already attaches `model`. This is not a free-text mm extractor (no digit is ever parsed from the user's own message) and not a new catalog family (no `library/fc/`, no dataclass, no bind function, no `ComponentLibrary` method). **Recommend Buy B1** directly — skip a separate B0 foundation phase, because the foundation this pattern needs (identity recognition + generic property attachment + generic Board display) already exists and needs no expansion, only one more fact attached to one already-recognized identity.

---

## B. As-is inventory

| Surface | Finding | Citation |
|---|---|---|
| Catalog family | **Absent, confirmed.** `library/` directory listing: `baterias, esc, frames, helices, materiales, motores` — no `fc`/`flight_controller` subdirectory. `library.py` full-text grep for `flight_controller`/`FLIGHT_CONTROLLER`/`fc_`: zero matches. | `ls library/`, grep `library.py` |
| Free-text extraction | `FLIGHT_CONTROLLER_MAP` (closed vocabulary: pixhawk 6x/6c/6/4 mini/4/bare, ardupilot, betaflight, naze32, matek) → `extract_flight_controller_properties` returns `{"model": PropertyValue(value=canonical, confidence=0.7 or 0.9, source="declared")}` **only** — no mass, no dims, nothing else, confirmed by full read of the function body. | `aerial.py:523-564` |
| Completeness | `_flight_controller_completeness` grades `"high"` once `model` confidence ≥ 0.85 (a specific numbered model like "Pixhawk 4") — completeness has never depended on, and will not start depending on, any geometry fact. | `aerial.py:567-579` |
| Registration | Wired into the generic domain-rule engine as one more `ComponentRule` (`keywords`, `property_extractor`, `completeness_evaluator`) — the exact same generic mechanism `frame`/`sensors`/every other free-text-only component type already uses. Adding a fact to what `extract_flight_controller_properties` returns requires **no** change to this registration or to the inference engine itself. | `aerial.py:741-749` |
| Bind | **None exists.** No `bind_flight_controller_from_catalog` anywhere in `catalog_bind.py` — confirmed by the same grep that found none in `library.py`. Consistent: there is nothing to bind *from*, since there is no catalog row. | `catalog_bind.py` (absence) |
| Live Board reality | Read directly from `workspace/autonomía-de-10min-9ada1a1b0cca/state.json`: `components["flight_controller"] = {"name": "Pixhawk 4", "properties": {"model": {"value": "pixhawk_4", "confidence": 0.9, "source": "declared"}}, "catalog_ref": null, "completeness": "high"}` — exactly matching the contract's own "model only" claim, re-verified rather than assumed. | live project state, this session |
| "Stack height" guard | Re-confirmed still present and still about a *different* extractor (the arm-thickness mm pattern), not FC: `"in this slice, never a bare/root mm (wheelbase, stack height, ...)"`. Cited only as a name-check that Jarvis is already aware "stack height" is a distinct, unsourced concept — this investigation does not touch it. | `aerial.py:423` |
| Battery/Motor/ESC pattern applicability | The `*Spec` → `_datos.json` → `ComponentLibrary.get_*` → `bind_*_from_catalog` chain **cannot be reused as-is** — there is no SKU identity for FC to key a JSON row on that the product doesn't already have a cleaner identity for (the free-text `model` string). Reusing that pattern here would mean inventing a whole parallel identity system (a `library/fc/` SKU name) for a fact the system already names correctly (`"pixhawk_4"`). The **Structure free-text scalar pattern** (`wheelbase_mm`/`arm_thickness_mm` — a value attached once a keyword/identity is recognized in text) is the closer honest fit, with one adjustment: those values come from a value the *user* typed; here the value would come from a small sourced table keyed by the *already-recognized* identity, since the user only ever types a model name, never a dimension. | reasoning grounded in `aerial.py` structure |

---

## C. Minimum FC geometric bag

| Field | Evidence for Pixhawk 4 | Verdict |
|---|---|---|
| `length_mm`, `width_mm`, `height_mm` | Two independent official sources agree: PX4 docs ("Dimensions: 44x84x12mm") and Holybro's own product page ("44x84x12mm") | **Accept** — same vocabulary as Battery/ESC, no divergence needed (a flight controller board is a flat box, same shape class) |
| `mount_pattern_mm` (30.5-class) | **Not stated on either page checked.** Neither the PX4 docs nor the Holybro product page for Pixhawk 4 gives a mounting hole spacing. The "30.5mm" figure the ESC investigation named as a *different geometric idea* remains just that — a real, common FPV-stack standard, but **not evidenced for this specific identity** by any source found. | **Reject for this increment** — no invention; naming it as a real, separate future question if a source is ever found that states it for a specific FC identity, exactly the same discipline Motor applied to excluding overall axial height |
| Weight/mass | PX4 docs state 15.8g; Holybro states 33.3g (plastic case) / 49g (aluminum case) for the *same* model name — a real, visible discrepancy (almost certainly FMU-board-alone vs. cased-kit weight), the same "which sub-assembly does this number describe" hazard Motor's height exclusion and ESC's mass_g flag both already surfaced | **Out of scope for this IC** — not asked for by the contract's field-bag question, and the cross-source disagreement here is sharper than any dimension disagreement found; naming as a future, separate, harder question, not attempting it |

**Proposed bag: `length_mm`, `width_mm`, `height_mm` only, for exactly one identity (`"pixhawk_4"`).**

**Where it lives (governing question 6 / identity rule):** a small, sourced, code-level table — not a `_datos.json` file, not a new `ComponentLibrary` family — e.g. a `FLIGHT_CONTROLLER_DIMENSIONS: dict[str, dict]` sitting next to `FLIGHT_CONTROLLER_MAP` in `aerial.py`, keyed by the same canonical model string (`"pixhawk_4"`) `extract_flight_controller_properties` already produces. When the function resolves a canonical model that has an entry in this table, it attaches the three dims as ordinary `PropertyValue(unit="mm", source="declared")` entries **in addition to** `model` — the exact same dict the function already returns, just with more keys when evidence exists. A model with no entry (e.g. `"pixhawk_6x"`, `"betaflight"`) returns `model` only, exactly as today — no regression, no invented coverage. Each table entry carries its own `source_url`/`source_note` values (as dict fields, not code comments) so a future reader can audit provenance without opening a JSON file that doesn't exist. This is honest about **why** it isn't the free-text-mm-extractor pattern the contract forbids: no digit is ever read from the user's own message; the mm values are static facts attached to a static, already-recognized identity, identical in spirit to how `MotorSpec.compatible_prop_inch` is a static fact about a specific motor, never derived from user text.

**Identity claim boundary (governing question 6, second half):** this is a `model` string match, not a catalog SKU. `catalog_ref` stays `None` for FC under this proposal — there is no SKU to bind to, and this report does not propose inventing one. The dims are exactly as trustworthy as `model` itself already is (declared, `source="declared"`, `confidence` inherited from the same match) — no more, no less. A future full catalog foundation (real SKU rows, `catalog_ref`, an eventual pick UX) remains possible later but is not required for this honest increment, and this report does not recommend building toward it preemptively.

---

## D. Source quotes for the concrete identity

**Pixhawk 4** (`model: "pixhawk_4"`, the identity the live Board smoke already surfaced):

| Source | Quote |
|---|---|
| `docs.px4.io/main/en/flight_controller/pixhawk4.html` (PX4 official docs) | "Weight and Dimensions: Weight: 15.8g, Dimensions: 44x84x12mm" |
| `holybro.com/products/pixhawk-4` (manufacturer product page) | "Dimensions: 44x84x12mm" · "Weight: Plastic case: 33.3g, Aluminum case: 49g" |

Both agree on **44×84×12mm** — cross-confirmed, not single-sourced. Neither states a mounting hole pattern.

**Pixhawk 4 Mini** — explicitly checked, explicitly excluded from this increment: the PX4 docs navigation references a Mini page, but its actual specification content could not be retrieved (empty/placeholder content on fetch); Holybro's `/products/pixhawk-4-mini` URL returned HTTP 404. No usable quote exists from either attempted source this session. **Do not seed Mini in the first Buy** — this is itself evidence, not a gap to paper over: disambiguating Mini vs. full Pixhawk 4 (which the free-text extractor already keeps as two separate canonical models, `pixhawk_4` vs `pixhawk_4_mini`) would need its own separate sourcing pass.

---

## E. Honesty / ladder matrix

| Implication | True if we add the proposed table? | Over-claim risk | Desired wording |
|---|---|---|---|
| "We know the FC's size" | **Yes, for `pixhawk_4` only** — a real, cross-confirmed, cited fact, same epistemic status as `model` itself today. Every other recognized FC model (`pixhawk_6x`, `betaflight`, ...) stays dims-less, honestly. | Low, provided the table stays sparse rather than back-filled with guesses for the other models. | "Pixhawk 4: dimensiones declaradas (fuente: PX4/Holybro)." |
| "30.5 stack" | **No relationship implied.** No mount-pattern field is added; nothing pairs the FC's box with any frame/ESC stack concept. | **High if ever implied** — this is the exact idea the ESC investigation already named as a *different* geometric claim and this report keeps that separation. | Never emit a stack/mount sentence from `length_mm`/`width_mm`/`height_mm` alone. |
| "Fits the frame" | **No.** No comparison against `wheelbase_mm`/frame footprint is proposed or computed. | High if ever implied — same `representar → verificar` jump every prior family in this axis has refused. | Never emit a fit sentence; that needs its own future Buy with its own evidence. |
| "Board = CAD" | **No.** Text rows on the existing card type, nothing drawn. | Medium if marketed loosely. | Keep Board copy scoped to "declared component data." |
| "Same as Battery box" | **True of the vocabulary only** (reused field names), not of the object — an FC board and a battery pack are unrelated components that both happen to be boxes, same as the ESC finding. | Low. | No change needed. |
| **(FC-specific) "This came from a catalog"** | **No — and this must stay explicit.** `catalog_ref` remains `None`; the dims live in a code table keyed by a free-text-matched identity string, not a bound SKU. A reader must not confuse this with Battery/Motor/ESC's catalog-bind provenance shape. | Medium — this report's whole recommendation hinges on this distinction being visible, not blurred, to whoever implements it. | Implementation report (if this Buy proceeds) should state plainly: "no catalog, no `catalog_ref`, declared-by-recognized-identity only." |
| "Visualization verifies" | **N/A — no visualization proposed.** | Low. | Same non-goal as every prior family. |

**Ladder position:** rung 2, **`representar`** only — same rung as Battery/Motor/ESC.

---

## F. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 (foundation only) | Build `library/fc/` + `FcSpec` + loader + `bind_flight_controller_from_catalog`, identity fields only, no dims yet | **Not recommended** — this report found a smaller honest path (§C) that delivers real geometry *without* this foundation; building it anyway would be exactly the "side-quest" the contract warns against, since the smaller path isn't blocked by anything a foundation would unblock |
| **B1** | **Identity-linked dims table for `pixhawk_4` only** (`length_mm`/`width_mm`/`height_mm`), attached inside `extract_flight_controller_properties`, no catalog, no bind function, no `catalog_ref` | **Recommended — see below** |
| B2 (box + mount + wizard/multi-SKU) | Add mount pattern, more FC models, and/or a catalog-pick wizard | Rejected for now — mount pattern has zero source evidence for any FC identity checked; more models (Mini, 6-series) would need their own sourcing pass first; a wizard would require the catalog foundation this report just argued against building prematurely |
| B3 | Board glyph | Not now — `visualizar`, premature |
| Defer | — | Not applicable — one clean, cross-confirmed identity exists today (Pixhawk 4, 44×84×12mm) and the smallest mechanism to attach it already exists in the codebase |

### Default lean: **B1 — identity-linked dims table, Pixhawk 4 only, three fields, no catalog foundation**

This is smaller than every prior family's first Buy: no schema dataclass, no seed JSON file, no loader method, no bind function, no `library/` directory. It is a handful of new lines inside `aerial.py`, next to a table (`FLIGHT_CONTROLLER_MAP`) that already exists and already does the "identity string → normalized fact" job this proposal extends by one more fact. The one thing worth Engineer's explicit attention before ★: this is architecturally **not** the same shape as Battery/Motor/ESC (no `catalog_ref`, no bind function) — a deliberate divergence, justified in §B/§C by the absence of any SKU-shaped identity to bind to, not an oversight or a shortcut taken to avoid work.

**Suggested first IC title (for Cursor, not decided here):** *"Flight Controller declared box (Pixhawk 4 only, identity-linked, no catalog) — representar only."*

---

## G. Non-goals for the first FC IC

Fit/clearance vs frame/ESC/stack · CAD/FEA · Board glyph · Battery/Motor/ESC/Frame schema edits · `library/fc/` catalog foundation (explicitly evaluated and rejected as unnecessary for this increment, §F) · `catalog_ref`/bind function for FC · Continuity FC catalog-pick wizard · mount_pattern_mm / 30.5-class stack spacing (no source evidence for this identity) · Pixhawk 4 Mini or any other model's dims (not sourced this session) · FC weight/mass field (out of scope, cross-source disagreement noted but not resolved) · free-text mm parsing from user messages (the proposed table is identity-linked, not text-parsed — explicitly distinguished in §C) · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims for any unsourced model · weakening tests.
