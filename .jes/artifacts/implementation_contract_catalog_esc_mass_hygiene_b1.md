# Implementation Contract — ESC mass hygiene B1 (`hobbywing_xrotor_40a_6s` 26→15)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY FOR IMPLEMENTATION — Engineer ★ Buy B1 ratified (`procede`)  
**Parents:**
- [investigation_contract_catalog_esc_variant_coherence.md](investigation_contract_catalog_esc_variant_coherence.md)
- [investigation_report_catalog_esc_variant_coherence.md](investigation_report_catalog_esc_variant_coherence.md)
- [investigation_review_catalog_esc_variant_coherence.md](investigation_review_catalog_esc_variant_coherence.md) — **PASS WITH NOTES**
- ESC Geometry B1 CLOSED suite **2327** (N2 left mass untouched — **this IC resolves that debt**)
- Board glyphs B1 CLOSED suite **2344**

**Type:** Single-field catalog data hygiene for **one** ESC row.  
**Not** Geometry rung climb. **Not** glyph. **Not** pose/assembly/fit. **Not** motor thrust. **Not** Here3/Pixhawk.

**Baseline:** package **`0.3.8`** · suite **2344**  
**Catalog reality:** `library/esc/_datos.json` has **1** row — edit that row only.

**Output:** `.jes/artifacts/implementation_report_catalog_esc_mass_hygiene_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — `mass_g` **26 → 15** for `hobbywing_xrotor_40a_6s` |
| 2 | PN / dims | **Unchanged** — `part_number` `30901001`, L/W/H **50.0 / 21.6 / 12.0** |
| 3 | H3 SKU split | **Rejected** — no Version A second row |
| 4 | **N1** `source_note` | Rewrite per §3.2 (cite 15 g; retire debt framing; keep www URL) |
| 5 | **N2** tests | Update **all four** `26.0` pins; **rename** `test_esc_mass_unchanged_by_geometry_addition` |
| 6 | **N4** honesty | Report must note: already-bound projects keep stale `26` until rebind |
| 7 | Glyph / Board code | **No** `ui/` or `spatial_board.py` edits |
| 8 | Motor thrust / FC / sensors | **Out** — cola 2 untouched |
| 9 | Version | **No** bump |

---

## 1. You

- Do **not** change PN, dims, electrical ratings, topology, or channels.
- Do **not** add a second ESC SKU (Version A).
- Do **not** edit `ui/**`, `workspace/spatial_board.py`, motor seeds, FC, sensors, or `thrust_n`.
- Do **not** build Continuity ESC picker / pose / fit / CAD.
- Do **not** bump package version.
- Full suite green. Zero weakened tests (retarget, don’t delete coverage).
- Write `implementation_report_catalog_esc_mass_hygiene_b1.md` when done.

---

## 2. Intent

```text
library/esc/_datos.json
  hobbywing_xrotor_40a_6s.mass_g: 26 → 15
  source_note: rewrite (cite page 15g for PN 30901001; prior 26 undocumented)
        ↓
  EscSpec / bind_esc_from_catalog  (no logic change — seed only)
        ↓
  tests: assert 15.0 everywhere this SKU’s mass was pinned
```

---

## 3. Locked behavior

### 3.1 Seed — `library/esc/_datos.json`

Update **`hobbywing_xrotor_40a_6s` only**:

| Field | Value |
|---|---|
| `mass_g` | **15** |
| `part_number` | **unchanged** `30901001` |
| `length_mm` / `width_mm` / `height_mm` | **unchanged** 50.0 / 21.6 / 12.0 |
| `source_url` | **unchanged** `https://www.hobbywing.com/en/products/xrotor-40a122` |

**`source_note` rewrite (required content, wording may vary):**

1. Keep identity: HOBBYWING XRotor 40A 6S, PN **30901001**, International Version B, no output wires.
2. Size: `"50.0x21.6x12.0mm"` → L/W/H (already seeded; reaffirm).
3. Weight: page states **15g** for this PN — **seeded as `mass_g: 15`**.
4. Explicit: prior seed value **26g** had **no** cited primary provenance; corrected this IC (catalog hygiene). Not Version A’s 18.5g; not an average.
5. Version A (`30901013`, 42.0×21.6×12.0, 18.5g, with wires) **not** seeded.
6. Drop Geometry-B1 “flagged as debt / left unchanged” language.
7. Keep note that `a.hobbywing.com` fails TLS; www mirror is the working URL.

Do **not** invent a provenance story for where 26 came from.

### 3.2 Schema / bind / Board

- **No** `EscSpec` field changes.
- **No** `bind_esc_from_catalog` logic changes (it already projects `mass_g` from the seed).
- **No** glyph / projector / CSS / React changes (`_geometry_from_spec` does not read mass).

### 3.3 Tests — `tests/test_catalog_foundation_v1.py` (exhaustive)

| Site | Action |
|---|---|
| `_assert_esc_hobbywing` (~line 399) | `mass_g == pytest.approx(15.0)` |
| `test_esc_mass_unchanged_by_geometry_addition` (~413–417) | **Rename** (e.g. `test_esc_mass_matches_page_for_part_number` or `test_esc_mass_coherent_with_version_b_envelope`) + rewrite docstring: mass is **15** for PN 30901001; dims still present / independent. Assert `15.0`. |
| `test_bind_esc_from_catalog_projects_continuous_current` (~455) | `properties["mass_g"].value == pytest.approx(15.0)` |
| `test_bind_esc_from_catalog_projects_declared_envelope` (~469) | same → `15.0`; update comment if it still implies “mass unaffected by geometry addition” as an N2 debt lock |

Grep the tree after edits: **zero** remaining `26.0` / `mass_g: 26` for this ESC SKU (seed + tests). Unrelated `26` elsewhere (e.g. watts) must not be touched.

### 3.4 Smoke note (required in implementation report)

- New `get_esc` / `bind_esc_from_catalog` → `mass_g == 15`.
- **N4:** projects that already persisted `mass_g: 26` on the ESC component keep showing 26 on Board until **rebind** (or equivalent refresh). That is expected; not a bug in this IC.

---

## 4. Files expected to change

| File | Change |
|---|---|
| `library/esc/_datos.json` | `mass_g` 26→15 + `source_note` rewrite |
| `tests/test_catalog_foundation_v1.py` | four asserts + rename/docstring N2 test |
| `.jes/artifacts/implementation_report_catalog_esc_mass_hygiene_b1.md` | write |

**Do not change:** `src/**` (unless a docstring uniquely claims mass=26 — only if such text exists; prefer not), `ui/**`, motor/battery/FC/sensor seeds, `aerial.py`, Continuity/orchestrator, calculation engine, package version.

---

## 5. Explicit non-goals

Pose / `mounted_on` / assembly / fit / CAD / FEA · glyph renderer · Version A second SKU · Here3 / Pixhawk · motor `thrust_n` / OP schema · ESC efficiency / Phase 2.6 · Continuity ESC picker · electrical-rating edits · System Optimization · Conversation Engine · version bump · weakened tests · migrating every on-disk project’s persisted mass automatically

---

## 6. Done criteria

- [ ] Seed `hobbywing_xrotor_40a_6s.mass_g == 15`.
- [ ] `source_note` cites page 15g for PN 30901001 and retires debt framing.
- [ ] PN + dims unchanged.
- [ ] All four former `26.0` asserts now `15.0`; N2 test renamed + re-docstringed.
- [ ] Grep: no leftover ESC mass 26 for this SKU.
- [ ] No `ui/` / projector / motor / FC edits.
- [ ] Full suite green; count reported.
- [ ] Implementation report written (include N4 rebind honesty).
- [ ] Cursor review PASS before Engineer close.

---

## 7. Stop conditions

Stop and ask before: changing PN/dims, adding Version A, editing glyphs/pose, touching motor thrust, auto-migrating workspace projects, or bumping version.
