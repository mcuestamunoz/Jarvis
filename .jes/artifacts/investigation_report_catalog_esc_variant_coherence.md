# Investigation Report — ESC XRotor Variant Coherence (PN ↔ dims ↔ mass)

**Project:** Jarvis
**Date:** 2026-09-07
**Investigator:** Claude Code
**Contract:** [investigation_contract_catalog_esc_variant_coherence.md](investigation_contract_catalog_esc_variant_coherence.md)
**Parents:** ESC Geometry B1 CLOSED @ 2327 · Board glyphs B1 CLOSED @ 2344
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · awaiting Engineer ★ Buy B1  
**Review:** [investigation_review_catalog_esc_variant_coherence.md](investigation_review_catalog_esc_variant_coherence.md)

**Not an Implementation Contract. No `src/`/seed edits made.** The manufacturer page was re-fetched live this session (a second, independent confirmation of the same finding the prior ESC Geometry investigation already flagged as debt) — not assumed from that prior investigation's own quote.

---

## A. Executive answer

Confirmed, live, a second time: `hobbywing_xrotor_40a_6s`'s own declared `part_number` (`30901001`) is real and unambiguous — the manufacturer's official page names it explicitly as **"International Version B"** with a stated size of **50.0×21.6×12.0mm and a weight of 15g, no output wires**. The seed's `length_mm`/`width_mm`/`height_mm` (50.0/21.6/12.0, sourced by the prior ESC Geometry B1 IC) match this PN exactly. **The seed's `mass_g: 26` does not match any of the page's four variants** — the two real weight values on the entire page are 15g (Version B, both regional SKUs) and 18.5g (Version A, both regional SKUs, which also has a *different* physical size, 42.0×21.6×12.0mm, and comes with output wires this row's identity doesn't claim). 26 is not an average, rounding, or transcription of either real value, and no cited source states it for this or any sibling PN — its origin is **unknown**, best-effort exhausted within primary-source scope this session. This is a genuine, single-field coherence defect, not a split-identity problem: the PN and dims already correctly point at one real, single physical variant (Version B); only `mass_g` disagrees with that same variant's own page. **Recommend Buy B1: correct `mass_g` from 26 to 15 for the current PN, rewrite `source_note` to state the correction and retire the "flagged as debt" framing, and update the four test assertions that pin `26.0`.** No SKU split is evidenced or needed — H3 is explicitly rejected. No glyph, pose, Here3/Pixhawk, or motor-thrust change is implicated; mass has never been read by the geometry glyph function (`_geometry_from_spec` only reads `length_mm`/`width_mm`/`height_mm`/`diameter_mm`/`diameter_in`).

---

## B. Live variant table (re-fetched this session)

Source: `https://www.hobbywing.com/en/products/xrotor-40a122` (the working `www.` mirror already recorded in the seed's `source_url` — the seed's originally-cited `a.hobbywing.com` URL still fails TLS validation, unchanged from the prior investigation, not re-litigated here).

| Variant | Product Number | Size (mm) | Weight (g) | Output wires |
|---|---|---|---|---|
| International Version A | `30901013` | 42.0×21.6×12.0 | 18.5 | Yes (3×16AWG, 75mm) |
| **International Version B** | **`30901001`** | **50.0×21.6×12.0** | **15** | No |
| Asian Version A | `30901014` | 42.0×21.6×12.0 | 18.5 | Yes (3×16AWG, 75mm) |
| Asian Version B | `30901000` | 50.0×21.6×12.0 | 15 | No |

Electrical ratings (40A continuous / 60A peak, 2-6S LiPo, no BEC) are stated as **identical across all four variants** — confirmed live; this is why electrical ratings cannot distinguish or validate a PN choice here, consistent with locked stance #3 keeping them out of scope for this exercise.

---

## C. Seed vs. page delta for `hobbywing_xrotor_40a_6s`

| Field | Seed (live tree) | Page, for PN `30901001` | Match? |
|---|---|---|---|
| `part_number` | `30901001` | `30901001` (International Version B) | ✅ Exact |
| `length_mm`/`width_mm`/`height_mm` | 50.0 / 21.6 / 12.0 | 50.0×21.6×12.0 | ✅ Exact |
| `mass_g` | **26** | **15** | ❌ **Mismatch — confirmed live, second independent fetch** |
| electrical ratings (40A/60A, 2-6S, no BEC) | matches | identical across all 4 variants | ✅ (uninformative for PN disambiguation, but not contradicted) |

**The row is not a collage of siblings** — every field that *does* match points consistently at the same single variant (Version B). The mass field is the one outlier, isolated and correctable without touching PN or dims (locked stance #2: dims stay unless disproven — they are not).

---

## D. Provenance of `26g`

**Unknown — best-effort exhausted within primary-source scope this session.** 26 does not equal either of the page's two real weight values (15g, 18.5g), nor their average (16.75g), nor either doubled/halved, nor any obvious unit-conversion artifact from either. A supplementary check of a well-known third-party retailer page for this SKU was attempted (to see whether 26g might trace to a retailer's own listing rather than the manufacturer) but returned an HTTP 403 before any content could be read — not pursued further by guessing another URL, per this session's own no-URL-invention discipline. The `source_note` already on this row (written during the ESC Geometry B1 IC) does not claim a citation for 26g either — it only states the manufacturer page's 15g figure and flags the mismatch as debt, exactly matching what this investigation re-confirms. **No fabricated provenance is proposed; the field is corrected on the strength of the two now-independently-fetched manufacturer quotes for this exact PN, not on a guess about where 26 came from.**

---

## E. Options H1–H3 + honesty matrix

| Option | Evidence for | Evidence against | Verdict |
|---|---|---|---|
| **H1** — keep PN + dims, correct `mass_g` → 15 | Two independent live fetches of the manufacturer's own page, for this exact PN, both stating 15g unambiguously; PN and dims already correct and untouched | None found | **Recommended** |
| H2 — keep 26 if a cited primary source defends it for this PN | — | No such source found anywhere this session or the prior ESC investigation; 26 matches nothing on the manufacturer's own variant table | **Rejected** |
| H3 — split into two SKUs (Version A vs B) | The manufacturer genuinely sells both as distinct, purchasable variants | Nothing in Jarvis's current catalog usage, tests, or Continuity flow needs both variants represented; the *existing* row already correctly identifies as Version B end-to-end (PN + dims) — a split would be net-new catalog surface with no evidenced consumer, contradicting the locked default-lean-toward-one-row instruction | **Rejected for this Buy** — naming Version A (`30901013`/`30901014`, 42.0×21.6×12.0mm, 18.5g, with output wires) as a legitimate *future* second row if a real product reason ever needs it, not decided here |

**Exact recommended field set after Buy (H1):**

```json
"mass_g": 15
```

`source_note` rewrite (illustrative, not prescriptive of exact wording — Cursor's eventual IC may phrase differently): replace the existing "differing from this row's existing mass_g=26 — flagged as pre-existing data-quality debt, not resolved in this IC" clause with a statement that the mass was corrected to the page's own stated 15g for PN `30901001`, and that the 26g figure's origin was investigated and found undocumented/unknown (so a future reader doesn't wonder whether it was silently dropped).

### Honesty matrix

| Phrase | True after H1? | Risk today (before H1) | Desired wording |
|---|---|---|---|
| "ESC weighs 26 g" | No — false today, corrected to 15g by H1 | **High — this is the exact defect under investigation**, live on the tree right now | "Peso declarado: 15 g (fuente: Hobbywing, PN 30901001)." |
| "Same as Version A" | No — Version A is a different PN, different size (42.0×21.6×12.0mm), different weight (18.5g), with output wires this row doesn't claim | Medium if ever assumed casually — the two versions share electrical ratings but not physical identity | Never imply cross-PN equivalence; Version A is explicitly a different, unseeded row (§E, H3). |
| "Board glyph proves mass" | No, and never was — confirmed `_geometry_from_spec` (Board glyphs B1) reads only `length_mm`/`width_mm`/`height_mm`/`diameter_mm`/`diameter_in`; `mass_g` is never part of the glyph payload, only the text `fields` list | Low — no glyph claim was ever made about mass | No change needed; cited here only to close the "does this Buy touch glyphs" question explicitly (answer: no). |
| "Fixed without source" | No — H1's correction is backed by two independent live fetches of the manufacturer's own page for this exact PN, both quoted verbatim in this report | Would be high if a future IC skipped re-citing the source — flagging so the eventual IC's own diff/`source_note` carries the citation forward, not just this report | `source_note` must retain the manufacturer URL + quoted "15" figure, not just a bare corrected number. |

**Confirmed out of this Buy, per locked stances:** Here3/Pixhawk identity — untouched, not referenced by any change proposed here. Motor `thrust_n`/operating-point schema — untouched, explicitly queued separately per §8 of the contract; this report does not expand into it.

---

## F. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 | Doc-only (name the discrepancy more prominently in a debt register, no seed edit) | Insufficient — the seed already documents the discrepancy in its own `source_note`; a doc-only pass would leave a *known-wrong* number live in `ComponentSpec.properties`/BOM/Board text for every project that binds this SKU |
| **B1** | **Correct `mass_g` 26→15 for the current PN; rewrite `source_note`; update the 4 test assertions that pin `26.0`** | **Recommended — see below** |
| B2 | Re-match PN entirely, or split into Version A/B SKUs | Not evidenced — PN and dims already correctly identify Version B; nothing forces a second row (§E, H3) |
| Defer | — | Not applicable — the correct value is known, cited twice, and the fix is a single-field, zero-ambiguity change |

### Default lean: **B1 — mass-only correction for the current PN, no split**

Smallest defensible fix: one seed field (`mass_g: 26` → `15`), one `source_note` rewrite recording the correction and the citation, and the four test locations that currently assert `26.0` (`tests/test_catalog_foundation_v1.py`: `_assert_esc_hobbywing` shared helper at line 399, `test_esc_mass_unchanged_by_geometry_addition` at line 413-417 — whose own name and docstring will need updating since its premise, "leave the pre-existing debt untouched," is exactly what this Buy resolves — and the two bind-level assertions in `test_bind_esc_from_catalog_projects_continuous_current`/`test_bind_esc_from_catalog_projects_declared_envelope`). No PN change, no dims change, no glyph change, no Here3/Pixhawk/motor-thrust change.

**Suggested first IC title (for Cursor, not decided here):** *"ESC mass correction (26→15g) for hobbywing_xrotor_40a_6s, PN 30901001 — data hygiene only."*

---

## G. Non-goals / test impact list

**Non-goals:** pose/`mounted_on`/assembly/fit/CAD/FEA · Here3/Pixhawk variant investigation · motor `thrust_n`/operating-point schema (queued separately, §8 of the contract — not expanded here) · ESC efficiency/Phase-2.6 losses · new ESC electrical families or 4-in-1 topology · glyph renderer changes (confirmed unnecessary — mass is not a glyph input) · a Version-A second SKU (named as a possible future row, not this Buy) · Continuity ESC picker/System Optimization/Conversation Engine · version bump · weakening tests.

**Exact test impact list (files/tests asserting the current, incorrect `26.0`):**

| File | Test | What changes under B1 |
|---|---|---|
| `tests/test_catalog_foundation_v1.py:399` | `_assert_esc_hobbywing` (shared helper, used by `test_escs_load_and_get_by_id`) | `assert spec.mass_g == pytest.approx(26.0)` → `15.0` |
| `tests/test_catalog_foundation_v1.py:413-417` | `test_esc_mass_unchanged_by_geometry_addition` | Assertion value → `15.0`; **name/docstring need rewriting** — today's name explicitly says "unchanged... pre-existing... debt," which becomes stale once B1 corrects the value; should become something like "mass corrected, dims still independent of it" |
| `tests/test_catalog_foundation_v1.py:448-455` | `test_bind_esc_from_catalog_projects_continuous_current` | `assert spec.properties["mass_g"].value == pytest.approx(26.0)` → `15.0` |
| `tests/test_catalog_foundation_v1.py:458-469` | `test_bind_esc_from_catalog_projects_declared_envelope` | Same trailing mass assertion → `15.0` |

No other file in the tree references this row's mass value (confirmed by grepping for the literal `26` alongside `hobbywing`/`esc` context; no production code path other than `bind_esc_from_catalog`'s existing `mass_g` projection reads this field, and that function requires no logic change — only the seed value changes).
