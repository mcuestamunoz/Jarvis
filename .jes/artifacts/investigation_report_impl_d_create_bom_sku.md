# Investigation Report — Impl D Create → BOM / SKU BOM

**Contract:** [`investigation_contract_impl_d_create_bom_sku.md`](investigation_contract_impl_d_create_bom_sku.md)
**Checkpoint base:** `checkpoint-impl-c` (`c99fec6`) — confirmed current HEAD.
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no new tests (investigation only, per contract §2).

---

## 1. Executive summary

`build_component_bom` classifies components into `defined`/`incomplete`/`missing`/`declarative` buckets purely from `classify_component` (completeness + measurable-property presence) — it never reads `ComponentSpec.catalog_ref`, never derives a quantity, and a bound motor's `.name` field (the SKU string) is indistinguishable from a freeform description that merely happens to look like one. `format_bom_lines`, the CLI `estado` "Componentes / gaps" section, and the file-based `views/sistema.md` all consume this same, unenriched shape — there is exactly one BOM authority today, just not a SKU-aware one. Readiness (`engineering_readiness.py`) already computes a per-component `catalog_bound` boolean (`_catalog_ref_set`) for five subsystems' `SubsystemEvidence`, but that field is **write-only** — nothing reads it back for verdict, display, or gap generation, so "BOM PASS" is fully achievable with zero bound SKUs.

**The Frankenstein risk (Scenario D) is real and already reachable**: `invalidate_diverged_catalog_refs` (G5) clears `catalog_ref` on divergence but never touches `.name`, so a post-divergence motor still displays its old SKU string in every existing BOM/CLI surface as if it were still a resolved part.

There is no Create→BOM handoff (sense B) anywhere today — `actions/create_project.py` has zero BOM/Continuity references, and `project_continuity.py` only ranks BOM `incomplete`/`missing` (stub/absent) into `next_useful_step`, never SKU-unresolved-but-otherwise-complete components.

**A second, independent finding** (not asked for, but load-bearing for any BOM redesign): CLI `estado` **suppresses the entire BOM lines section whenever Continuity has any `evidence` text** (`if bom_lines and not continuity.get("evidence")`). Continuity's evidence block is populated often (physics gaps, catalog gaps, energy notes), so today's BOM section frequently doesn't render at all — independent of what's actually in it.

**Recommendation: Option A** (extend `build_component_bom` entries with `catalog_ref`/quantity/resolved-status fields, upgrade `format_bom_lines`) as v1, explicitly **not** Option C (no parallel BOM authority — nothing in this audit justifies one), and **defer** Option B (Continuity CTA) to a thin, optional slice since it requires touching Continuity's ranking, which is higher-risk than the pure BOM-data upgrade and not needed to satisfy the Design §6 exit criterion's literal wording ("Create/BOM consumes SKU identity").

---

## 2. As-is BOM pipeline audit

### 2.1 Sequence

```text
project_state
   ↓
project_closure.build_component_bom(project_state)
   → classify_component(key, spec, project_state)  [per BLOCK_TO_COMPONENTS-expected key + extras]
   → buckets: defined / incomplete / missing / declarative
   ↓                                              ↓
format_bom_lines(bom)                    engineering_readiness._bom_missing_gaps /
   ↓                                       _bom_incomplete_gaps(bom)
CLI estado "Componentes / gaps:"                 ↓
views/sistema.md "## BOM / gaps"          GAP-BOM-MISSING-COMPONENT (HIGH)
                                           GAP-BOM-INCOMPLETE-COMPONENT (MEDIUM)
                                           — only from missing/incomplete buckets;
                                             defined/declarative never gap
   ↓
orchestrator.build_startup_context
   → component_bom, component_bom_lines  (only call site of build_component_bom
                                            outside render_views.py)
   → passed to project_continuity.build_project_continuity(component_bom=bom, ...)
      → reads only bom["incomplete"] / bom["missing"] for next_useful_step
        ranking (rank 4) — defined/declarative never influence Continuity
```

### 2.2 Consumer table

| Step | File / symbol | Reads `catalog_ref`? | Reads/derives qty? | Notes |
|---|---|---|---|---|
| BOM build | `project_closure.build_component_bom` | **No** | **No** | Only `key`/`name`/`completeness`/`missing_fields`/`component_type` per entry |
| Classification | `project_closure.classify_component` | **No** | — | Completeness + `_MEASURABLE` property presence only; `catalog_ref` is not in `_MEASURABLE` |
| Format | `project_closure.format_bom_lines` | **No** | **No** | `name` field is `spec.name`, which for a bound motor happens to equal the SKU string — a coincidence of how `bind_motor_from_catalog` names the spec, not a read of `catalog_ref` |
| ERF BOM gaps | `engineering_readiness._bom_missing_gaps` / `_bom_incomplete_gaps` | No | No | Only fire for `missing`/`incomplete` buckets — `defined` (bound or not) never gaps |
| ERF subsystem evidence | `engineering_readiness._structure_evidence` / `_propulsion_evidence` / `_energy_evidence` / `_control_evidence` / `_electronics_evidence` / `_bom_evidence` | **Yes** — `_catalog_ref_set(project_state, key)` | No | Sets `SubsystemEvidence.catalog_bound`, but **nothing reads this field elsewhere** — confirmed by grep: every occurrence is a write, `_derive_subsystem_verdict` never references `evidence.catalog_bound` |
| Continuity | `project_continuity.build_project_continuity` | No | No | Reads `bom["incomplete"]`/`bom["missing"]` only, for situation text and `next_useful_step` rank 4 |
| Views (CLI) | `adapters/cli/main.py` | No | No | Renders `ctx["component_bom_lines"]`, **suppressed whenever `continuity["evidence"]` is truthy** (§2.3) |
| Views (file) | `workspace/render_views.render_sistema` | No | No | Same `build_component_bom`/`format_bom_lines` call, always renders (no suppression — file view has no Continuity-evidence gate) |
| Create | `actions/create_project.py` | N/A | N/A | Zero BOM/Continuity references — no Create→BOM handoff exists |

**No drift** across the two BOM call sites (`orchestrator.build_startup_context`, `render_views.render_sistema`) — both call the identical `build_component_bom`/`format_bom_lines` pair, so there is exactly one BOM authority today; the gap is that it isn't SKU-aware, not that it's duplicated.

### 2.3 CLI suppression finding (not asked for, load-bearing)

`adapters/cli/main.py:254-259`:

```python
bom_lines = ctx.get("component_bom_lines") or []
if bom_lines and not continuity.get("evidence"):
    lines.append("")
    lines.append("Componentes / gaps:")
    ...
```

The BOM section only prints when Continuity's `evidence` list is **empty**. Continuity populates `evidence` for physics blocking, non-PASS simulation, catalog gaps, and the energy-model honesty note — all common states. This means: in the exact scenario the contract's CLI walk describes (architecture 4/4, Catalog PASS, BOM PASS, hobbywing bound), if Continuity had *any* evidence line queued (e.g. the energy-model honesty note, which fires whenever autonomy is a constraint — very common), the BOM section — SKU-aware or not — would not render in `estado` at all. **Any future IC must address this rendering gate, or a richer SKU BOM will still be invisible in the exact state it matters most.**

---

## 3. Field-read matrix

| Field on `motors`/other component | Read by `build_component_bom`? | Read by ERF BOM gaps? | Read by ERF subsystem evidence? | Read by Continuity? |
|---|---|---|---|---|
| `catalog_ref` | **No** | No | Yes (`_catalog_ref_set`, write-only downstream) | No |
| `catalog_ref.sku` | No | No | No (only truthiness checked) | No |
| `.name` | Yes (`_entry["name"]`) — displayed as-is, no distinction from a real SKU | No | No | No |
| `completeness` | Yes (bucket routing via `classify_component`) | Indirectly (via bucket) | No | Indirectly (via bucket) |
| `properties.motor_count` | Only for `_is_motor_count_gap` filtering (missing_fields cleanup) | No | No | No |
| `current_parameters.motor_count` | Same as above (fallback) | No | No | No |
| `missing_fields` | Yes | Yes | No | Yes (display in situation text) |
| `component_type` | Yes (`_entry["component_type"]`) — carried but never displayed by `format_bom_lines` | No | No | No |

**No field anywhere in this pipeline carries a quantity number.** `motor_count` is consulted only to *suppress* a missing-fields gap, never surfaced as "qty: 6".

---

## 4. Scenario matrix (A–H) with recommended UX

| # | Scenario | BOM today | Recommended for Impl D |
|---|---|---|---|
| **A** | Motors unbound, freeform name (e.g. `"4x 2306 2400KV 50W"`) | `defined` bucket (if complete), line shows the freeform name, no SKU claim (correctly, since there's nothing to falsely claim) | `sku_resolved: false`, `catalog_ref: null`, line shows the declared description + qty from `motor_count` — unchanged in substance, richer in shape |
| **B** | `catalog_ref` set, SKU in library | `defined` bucket, line shows `.name` (== SKU by construction), **no visible distinction from A** | `sku_resolved: true`, `catalog_ref` populated, qty from `motor_count` — this is the actual "buyable line item" the contract asks for |
| **C** | `catalog_ref` set, SKU missing from library (G9-A Scenario D) | Same as B today — BOM has no idea the SKU is gone, only G9-A's *gap* surface (`resolve_motor_catalog_surface`) knows | `sku_resolved: false` (re-validate via `default_library.has_motor(sku)` at BOM-build time — same check G9-A already performs elsewhere, not a new library reader), keep `catalog_ref` visible but flagged unresolved so the user sees *what was bound* and *that it's now broken*, not silence |
| **D** | Frankenstein: `.name` looks like a SKU, `catalog_ref is None` | **Indistinguishable from B** — this is the honesty bug | `sku_resolved: false`, `catalog_ref: null` — **the BOM entry schema must key `sku_resolved` off `catalog_ref` presence, never off `.name` shape**. This is the one non-negotiable rule from the contract's hard constraints and this is exactly where it must be enforced |
| **E** | Battery freeform Wh only, no `catalog_ref` | `defined`/`declarative` bucket, no SKU claim | Same shape as A — `sku_resolved: false`, qty=1 |
| **F** | Battery `catalog_ref` set (`bind_battery_from_catalog` is test-callable today, no acquisition UX yet — Impl C's own C3 slice, deferred) | Same as B pattern *if* it ever occurs — no live path produces this today | Same shape as B — the BOM schema should be family-agnostic (motors/battery both read the same way) even though only motors has a live bind UX right now; costs nothing extra and avoids a second schema later |
| **G** | Propellers / ESC / FC / sensors — no catalog bind path exists for these families | `defined`/`declarative`, name-only | Declared-only lines, `catalog_ref: null`, `sku_resolved: false` always (no family support) — **not** a gap, just an honest "no catalog for this part yet" |
| **H** | `motor_count=6`, one `ComponentSpec` for motors | One BOM line, no multiplier shown anywhere | `quantity: 6` on the motors line — the single most concrete, low-risk addition this investigation found (§5) |

**Scenario D is the hard constraint this whole investigation turns on.** The fix is structural, not a special case: the line-item schema's `sku_resolved` field must be *computed from* `catalog_ref is not None` (plus, for C, a live `has_motor`/`has_battery` check), never inferred from `.name`. Since `build_component_bom`'s `_entry()` function is the single place that shapes a BOM line, this is a one-function change to get right everywhere at once (§8, Option A).

---

## 5. Line-item schema proposal

Fields only (no code) — extends today's `_entry()` shape additively, does not remove any existing field (`key`, `name`, `completeness`, `missing_fields`, `component_type` all stay):

```text
{
  key:              str            # unchanged
  display_name:     str            # unchanged today's "name" — kept as-is
  component_type:   str | None     # unchanged
  completeness:     str            # unchanged
  missing_fields:   list[str]      # unchanged

  catalog_ref:      {family, sku} | None   # NEW — straight passthrough of spec.catalog_ref
  sku_resolved:      bool                  # NEW — catalog_ref is not None AND (for C) the sku still
                                            #        resolves in the library (has_motor/has_battery)
  quantity:          int | None            # NEW — see below
}
```

**Quantity derivation (v1, minimal, no invention):**

- **Motors:** `current_parameters["motor_count"]` (already the single source of truth this codebase uses everywhere else for fleet size — `set_motor_component`'s own Bug78/FN-007 fallback reads the same field). Falls back to the component's own `properties["motor_count"]` when present and params-side is absent (same precedence `_measurable_and_missing_fields` already uses).
- **Propellers:** same as motors' `motor_count` — the codebase has **no independent propeller-count field anywhere** (confirmed by grep: no `propeller_count` symbol exists); the implicit, everywhere-assumed convention for the aerial domain is 1 propeller per motor. Recommend making this explicit in the BOM line (`quantity = motor_count`) rather than leaving it unstated, but documenting it as a convention, not a measured fact.
- **ESC:** **honest unknown, not invented.** A 4-in-1 ESC vs. one-per-motor is a real design choice this codebase has no data to distinguish (no `esc_count`/`esc_type` field exists). Recommend `quantity: null` for ESC in v1 — an explicit "not tracked" is more honest than guessing 1 or N, matching the hard constraint "LLM/system never invents... quantities."
- **Battery, frame, flight_controller, sensors:** `quantity: 1` — every existing architecture/domain table treats these as singletons (no count field exists or is ever asked for), so 1 is not an invention, it's the only value the rest of the system is already internally consistent with.

---

## 6. Create handoff (sense B) recommendation

1. **No existing "go to BOM" / procurement CTA exists anywhere** — confirmed by grep across `actions/create_project.py` (zero hits) and `project_continuity.py` (BOM only enters via the existing incomplete/missing rank, nothing SKU-specific).
2. **A thin handoff, if built, would be:** a new, narrow Continuity rank (or a qualifier on the existing rank-4 BOM-incomplete text) that fires specifically when architecture is 4/4, all components are `defined`, but one or more `defined` motors/battery entries have `sku_resolved: false` — i.e. "your design is complete and physically valid, but no part in it is a purchasable SKU yet." This is a **new** situation Continuity cannot express today (its incomplete/missing buckets are blind to this state by construction, per §2.2/§4). It would need: (a) a new predicate reading the enriched BOM entries from §5, (b) a place in the existing rank ordering (probably between rank 3 "honest catalog gap" and rank 4 "incomplete/missing BOM", since it's a *milder* signal than either), (c) new copy.
3. **Recommend deferring this for Impl D v1.** The Design §6 exit criterion's literal wording is "Create/BOM **consumes** SKU identity" — satisfied by §5's schema + `format_bom_lines` upgrade alone (sense A). Sense B is a genuine, real UX improvement, but it requires touching `project_continuity.py`'s ranking logic, which the parent Impl C review process has repeatedly treated as higher-risk than pure data/formatting changes (see G21/G22/G23's own pattern of shipping the data-authority fix first, UX polish as a separate, later, explicitly-scoped cut). Also directly avoids reopening the CLI-suppression finding (§2.3) inside this same cut — that bug affects *any* future Continuity-ranked BOM message, sense-B or not, and deserves its own narrow fix rather than being entangled with a first SKU-BOM cut.

---

## 7. ERF / ASSEMBLY READY interaction notes

- **Does a SKU-unresolved motor already affect Catalog/BOM subsystems?** Catalog subsystem: yes, via G9-A's existing `resolve_motor_catalog_surface`/Scenario B/C/D machinery — already correct and untouched by this investigation's proposal. **BOM subsystem: no** — `_bom_evidence`'s `catalog_bound` field (all-defined-entries-bound boolean) is computed but never consumed by verdict derivation (confirmed §2.2) — this is the exact "write-only" gap Impl D's data layer would finally give a real consumer for, *if* a future slice chooses to wire it into `_bom_evidence`'s verdict (not required for v1 — see next point).
- **Should Impl D add a new gap type (`GAP-BOM-SKU-UNRESOLVED`) or reuse existing types?** **Reuse, don't add.** A `defined`-but-unresolved motor is not "incomplete" in the engineering sense the existing `GAP-BOM-INCOMPLETE-COMPONENT` models (missing physical properties) — it's a procurement-identity gap, which is what G9-A's `GAP-MOTOR-CATALOG-UNRESOLVED` already models, on the `catalog` subsystem (not `bom`). Introducing a new BOM-domain gap type would create exactly the "dedupe gaps BOM/ESC" debt the vision doc already flags as deferred technical debt (`docs/ENGINEERING_READINESS_VISION.md` ERF-2 "Out of scope" list) — compounding it, not fixing it. **Recommendation: no new gap type in Impl D v1.** The enriched BOM entry (`sku_resolved: false`) is visible *data*, and G9-A's existing gap already covers the *actionable* signal for motors specifically. If Engineer wants a BOM-side gap later, it should be scoped as a dedup-aware follow-up, not bundled here.
- **"BOM SKU-complete ≠ ASSEMBLY READY while Requirements INCOMPLETE"** — confirmed structurally true and already the case today: `_derive_overall`'s `ASSEMBLY_READY` check requires every subsystem (including `requirements`) to be PASS or an accepted WARNING — a `bom` subsystem improvement in isolation cannot change that. No G26/Requirements design proposed here, per the contract's own boundary.

---

## 8. Design options

### Option A — Extend `build_component_bom` entries (recommended)

Add the §5 fields inside `_entry()` (the single function that shapes every BOM line, for every consumer). Upgrade `format_bom_lines` to show `[sku]` (mirroring the exact `_build_label_components` convention Impl C already established for DSE candidate labels — same visual language, zero new UX vocabulary) and `qty=N` when present.

- **Files touched (estimate):** `project_closure.py` (`_entry`, `format_bom_lines`) — 1 file for the core change. Zero changes needed to `engineering_readiness.py`'s gap functions (they only read `missing`/`incomplete`, both untouched in shape). Zero changes to `orchestrator.py`, `render_views.py`, `adapters/cli/main.py` call sites — they already pass the dict/list through unchanged; new fields ride along for free.
- **Pros:** Minimal, reuses the one existing authority, both consumers (CLI + file view) get it automatically, directly closes Scenario D honestly.
- **Cons:** Does not address the CLI-suppression finding (§2.3) — a future, separate fix. Does not add a Create handoff (sense B, deferred per §6).

### Option B — A + Continuity CTA

Everything in A, plus §6's thin handoff.

- **Files touched:** A's files + `project_continuity.py` (new rank, new predicate, new copy) + likely `adapters/cli/main.py` if the CLI-suppression gate needs adjusting for the new message to actually be visible (§2.3 makes this non-optional if Option B is chosen — a new Continuity message would itself be suppressed by the exact same `evidence`-gate bug unless addressed).
- **Pros:** Closes the full UX loop the contract's CLI-walk symptom describes.
- **Cons:** Larger diff, touches Continuity ranking (real risk of reordering existing rank-4 behavior — needs its own regression suite), and now *also* needs the suppression-gate fix to actually be effective, which was never in this investigation's named scope. Recommend as a **separate, follow-up** IC once A has shipped and been observed in real use, not bundled into Impl D v1.

### Option C — New parallel `build_sku_bom` authority

A second function producing a purchase-order-shaped BOM, independent of `build_component_bom`.

- **Rejected.** Nothing in this audit justifies a second authority: there is exactly one BOM shape today, one set of consumers, and the enrichment needed (§5) is purely additive to the existing entry shape — every field Option A adds is optional/nullable and changes no existing consumer's behavior. A parallel authority would immediately reopen the "two motor lists disagree" class of bug G22 was a whole IC to close (`build_motor_catalog_suggestions` vs `resolve_motor_catalog_surface`) — this time for BOM. The contract's own hard constraint ("prefer extending `build_component_bom` ... unless investigation proves necessity") is not met here; no necessity was found.

**Recommendation: Option A now, Option B's CTA as an explicit, separate future cut** (not blocking, not forgotten — captured in §11/§12).

---

## 9. Test inventory + CLI probe sketch

### Existing tests touching this surface

| File | Coverage | `catalog_ref` assertions today |
|---|---|---|
| `tests/test_project_closure_v1.py` | `build_component_bom`/`classify_component` bucket routing | None |
| `tests/test_fn020_completeness_coherence.py` | `classify_component` tier boundaries (the FN-020 unification) | None |
| `tests/test_project_coherence.py` | BOM + Continuity coherence across turns | None |
| `tests/test_erf2_architecture.py` | ERF-2 architecture/BOM interaction | None |
| `tests/test_engineering_readiness_continuity.py` | Readiness→Continuity wiring | None |

None currently construct a `catalog_ref`-bound fixture and assert on a BOM entry's identity fields — confirmed real, clean gap (not a regression risk for Option A, since no test currently depends on the *absence* of these fields either).

### Proposed CLI probes for a future IC (sketch only, not implemented here)

```text
1) Bind motor SKU (G21 component-wizard path) → estado/BOM entry shows
   catalog_ref.sku + sku_resolved=true + quantity=motor_count
2) Unbound freeform motor → BOM entry has catalog_ref=null, sku_resolved=false,
   same display_name as today (no regression in the no-catalog case)
3) Post-divergence frankenstein (bind, then diverge via params-only DSE apply,
   per G5/test_catalog_bind_v1.py's own existing divergence fixture) →
   BOM entry: catalog_ref=null, sku_resolved=false — .name may still show
   the old SKU string as display_name, but sku_resolved must be false
4) Architecture 4/4 + bound motor → BOM PASS unchanged (no verdict regression);
   SKU line visible in both estado (when Continuity evidence is empty — note
   the §2.3 caveat) and views/sistema.md (always)
5) Regression: GAP-BOM-INCOMPLETE-COMPONENT / GAP-BOM-MISSING-COMPONENT
   unchanged for missing/stub keys — new fields must not perturb existing
   gap generation, which reads shape (missing/incomplete lists), not the
   new per-entry fields
6) Battery bound via bind_battery_from_catalog (test-only path, no live UX)
   → same schema shape as motors, proving family-agnostic design without
   needing new acquisition UX
```

---

## 10. Recommended approach

**Option A**, scoped to motors + battery (family policy per contract §1.7 — propeller/ESC/frame/FC stay declared-only, `catalog_ref` always `null`, `sku_resolved` always `false` for those families in v1, honestly reflecting that no bind path exists for them). No new gap type. Create-handoff (sense B) explicitly deferred to a follow-up IC, not silently dropped — captured as its own slice recommendation.

This is the same shape of recommendation Impl C's own investigation made (generation-first, minimal-diff, defer the UX-polish layer) and it was the right call there — Cursor's Impl C review confirmed the generation-only cut was correct to ship first and the thrust-bridge follow-up closed the *real* gap cleanly once isolated. The same discipline applies here: ship the honest data layer, observe it, then decide if/how much Continuity-copy work sense B actually needs.

---

## 11. ★ Decisions for Engineer

**★1 — v1 scope:** Option A only (BOM entry schema + `format_bom_lines` upgrade). *Recommended.*

**★2 — Families in v1:** motors + battery (schema is family-agnostic; only these two have any bind path — live or test-only). Propeller/ESC/frame/FC/sensors: declared-only lines, `catalog_ref`/`sku_resolved` always null/false. *Recommended.*

**★3 — Create-handoff (sense B):** deferred to a separate, future IC — not implemented in Impl D v1. *Recommended.*

**★4 — New gap type (`GAP-BOM-SKU-UNRESOLVED`):** **do not add.** Reuse G9-A's existing `GAP-MOTOR-CATALOG-UNRESOLVED` (catalog subsystem) as the actionable signal; the enriched BOM entry is visible data, not a new gap. *Recommended.*

**★5 — `_bom_evidence`'s existing `catalog_bound` field:** leave disconnected from verdict derivation in v1 (do not wire it into `_derive_subsystem_verdict`) — that's a subsystem-verdict-semantics change, a bigger and separate decision than "make BOM data honest," and nothing in the contract's exit criterion requires it. *Recommended, flagged for a possible future ★ if Engineer wants BOM verdict itself to reflect SKU resolution.*

**★6 — CLI-suppression finding (§2.3):** real, pre-existing, **not caused by and not required to be fixed by Impl D**. Flagged because any Option A improvement is invisible in `estado` whenever Continuity has evidence text queued (common). Recommend a narrow, separate follow-up (likely: BOM lines should render in their own right, independent of Continuity's evidence state, or Continuity should fold a BOM summary line into its own evidence block instead of relying on a second, conditionally-suppressed section). **Engineer decision needed:** fix now as a tiny adjunct to Option A, or track as separate debt (like G24-G27)?

---

## 12. Suggested Implementation Contract outline

*(Bullets only, per contract §1.9/§3 — not a full IC.)*

**Slice D1 — BOM entry schema (`project_closure.py`)**
- `_entry()` gains `catalog_ref`, `sku_resolved`, `quantity` per §5's derivation rules.
- `sku_resolved` computed from `catalog_ref is not None` (+ live `has_motor`/`has_battery` re-check for Scenario C — reuse `default_library`, no new reader) — never from `.name`.
- Acceptance: Scenario D fixture (bound then diverged) produces `sku_resolved: false` even though `.name` still looks like a SKU.

**Slice D2 — `format_bom_lines` + surfacing**
- Show `[sku]` (Impl C's established label convention) and `qty=N` when present; unchanged formatting when absent (no-catalog case stays byte-identical).
- No `orchestrator.py`/`render_views.py`/`adapters/cli/main.py` call-site changes needed — new fields ride through existing plumbing.
- Acceptance: existing no-catalog BOM tests byte-identical; new bound-SKU fixture shows the new line shape in both CLI and file view.

**Slice D3 — Tests + CLI probe**
- §9's 6 probes as automated tests, mirroring the Impl C precedent (scripted probe + focused test file).
- Regression: `tests/test_project_closure_v1.py`, `tests/test_fn020_completeness_coherence.py`, `tests/test_project_coherence.py`, `tests/test_erf2_architecture.py`, `tests/test_engineering_readiness_continuity.py` all green, unmodified assertions.

**Slice D4 (optional, Engineer's ★6 call) — CLI-suppression fix**
- Either decouple BOM rendering from `continuity["evidence"]` truthiness, or fold a one-line BOM summary into Continuity's own evidence block.
- Acceptance: a bound-SKU project with Continuity evidence present (e.g. energy-model note active) still shows the SKU BOM line somewhere in `estado`.

**Slice D5 — Docs / System Map** (Cursor, later, not Claude's slice)

**Out of scope for the IC (carried forward from this investigation):**
- Create-handoff / Continuity CTA (★3, sense B) — separate future IC.
- New gap type (★4) — rejected.
- `_bom_evidence.catalog_bound` → verdict wiring (★5) — separate future ★ if wanted.
- Battery/propeller catalog **pick UX** (Impl C's own C3) — still deferred, unrelated to BOM *display*.
- G24-G27, Phase 2 physics, H5 ESC catalog, Conversation Engine, Step D.
