# Implementation Contract — Fit attestation B1 (Engineer-declared verified)

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** **CLOSED** — smoke **ACCEPT** ([smoke](engineer_smoke_geometry_fit_attestation_b1.md)) · [review](implementation_review_geometry_fit_attestation_b1.md) PASS WITH NOTES · suite **2679** · UI **80**  
**Parents:**
- Engineer ★ **`B1-attest`** (2026-09-10) — first Fit VERIFIED cut
- [investigation_review_geometry_fit_verified_b0.md](investigation_review_geometry_fit_verified_b0.md) **PASS WITH NOTES**
- [investigation_report_geometry_fit_verified_b0.md](investigation_report_geometry_fit_verified_b0.md)
- Screening **CLOSED**: [implementation_contract_geometry_assembly_fit_cabe_b1.md](implementation_contract_geometry_assembly_fit_cabe_b1.md) · `pose_envelope_screening.py`
- Historical stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **do not implement / do not rename into this Buy**
- Board Situar / C-113 **CLOSED** @ `v0.4.1` (pose input; not a fit proof)
- Plate L×W **B0** · LEVEL A frame class — **out**

**Type:** Human attestation on one already-`overlap`-screened posed box–box pair. Board field + IDLE + optional Board button via same writer.  
**Not** automatic “encajada”. **Not** renaming screening → VERIFIED. **Not** CAD/FEA. **Not** `ASSEMBLY_READY` flip.

**Baseline:** package **`0.4.1`** · suite **2669** (known pin: `test_p6_library_and_version_untouched` still asserts `0.4.0` — fix in this Buy) · UI **80**

**Output:** `.jes/artifacts/implementation_report_geometry_fit_attestation_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B1-attest** — Engineer marks a pair as verified by **their** judgment |
| 2 | Gate | Writer accepts **only** if `screen_posed_envelope(child, components).status == "overlap"`. Reject `no_overlap` / incomplete / not-box / no_pose / origin_unusable — never silent grant |
| 3 | Screening copy | **`format_screening` unchanged** — still “screening, no verificado”. Never rename overlap→VERIFIED |
| 4 | Attestation copy | Distinct string only, e.g. `Declarado verificado por el Engineer — no es una comprobación geométrica de Jarvis.` (timestamp optional). Forbidden as bare token alone: `VERIFIED` / `cabe` / `encajado` / `ensamblado` without the human attribution clause |
| 5 | Invalidation | Fingerprint of `(origin_key, x_mm, y_mm, z_mm, child L×W×H, origin L×W×H)` at attest time. Any later `set_component_declared_box_pose` / `set_component_declared_box_envelope` on **child or origin** that changes fingerprinted values **clears** attestation (catalog_bind divergence pattern). Stale fingerprint → treat as absent (no lying seal) |
| 6 | PASS | `engineering_readiness` / `ASSEMBLY_READY` / `_block_progress_status` / Continuity ranks / Structure A — **byte-identical** (no new Gap) |
| 7 | Surfaces | (a) IDLE Continuity phrase set/clear · (b) Board `fields` show seal when valid · (c) **optional but in-scope:** Scene3D/Board control that POSTs the same writer (thin bridge, C-113-shaped) — no second schema |
| 8 | Multiplicity | Singleton subject only (same spirit as Situar): do **not** attest a `solidCopies >= 2` station as if N independent seals |
| 9 | Version | **No** bump (`0.4.1`). Do fix the stale `0.4.0` string assert in `test_geometry_prop_adapter_visor_x_b1.py` |

**Product sentence:**

```text
Cuando los sobres ya se solapan (screening), puedo declarar verificado
ese par. Jarvis no lo inventa. Si muevo la pose o cambio la caja, el
sello se borra. El screening sigue diciendo “no verificado” como hecho
geométrico de Jarvis.
```

**Not:**

```text
aviso automático “encajada” · rename screening→VERIFIED · ASSEMBLY_READY
desde AABB · margin/compose/faces · Rooster L×W · Conversation Engine
· stub fit_compare.md
```

---

## 1. You (Claude)

- **STOP** if you change `format_screening` overlap/no_overlap strings into “verificado”.
- **STOP** if attestation can be set when screening ≠ `overlap`.
- **STOP** if you touch `ASSEMBLY_READY` / new Gap / readiness rollup.
- **STOP** if you implement `implementation_contract_geometry_assembly_fit_compare.md`.
- Reuse `resolve_component_subject_noun` for IDLE subject — no second alias table.
- Full pytest green. Report written.

---

## 2. Intent

```text
screen_posed_envelope == overlap
        ↓
Engineer: “declaro verificado el <sujeto>”  (or Board button → same writer)
        ↓
ComponentSpec.declared_fit_attestation  (+ fingerprint)
        ↓
Board field “verificación” = human copy
        ↓
pose/envelope write that changes fingerprint → attestation cleared
        ↓
ASSEMBLY_READY unchanged
```

---

## 3. Locked behavior

### 3.1 Schema

New optional field on `ComponentSpec` (name may be `declared_fit_attestation`):

```text
DeclaredFitAttestation:
  attested_at: str   # ISO timestamp ok
  fingerprint: str   # stable hash/string of the locked tuple below
```

Fingerprint inputs (order locked in code + tests):

```text
origin_key | x_mm | y_mm | z_mm |
child.length_mm | child.width_mm | child.height_mm |
origin.length_mm | origin.width_mm | origin.height_mm
```

Use geometry from `_geometry_from_spec` at attest time (boxes only — gate already ensures).

### 3.2 Writer

`set_component_declared_fit_attestation(project_state, component_key, attest: bool) -> ProjectState`

- `attest=False` → clear field (idempotent if already None).
- `attest=True` → require component exists; `screen_posed_envelope(...).status == "overlap"`; compute fingerprint; set field. Else `ValueError` with honest Spanish (reuse refuse tone of pose writer).
- Caller saves (same as other component_writers).
- Hook clear into **existing** `set_component_declared_box_pose` and `set_component_declared_box_envelope`: after a successful write on key `K`, clear attestation on `K` if present **and** clear attestation on any component whose pose `origin_key == K` if that write changed fingerprinted geometry/pose inputs. Minimum honest rule that satisfies review:  
  - Any pose write on child → clear that child’s attestation.  
  - Any envelope write on child **or** on the child’s current origin → clear child’s attestation.  
  - Prefer computing “would fingerprint change?” rather than always-clear if easy; always-clear on those writers for touched keys is **acceptable** for B1 (simpler, fail-closed).

### 3.3 IDLE

Near pose / cabe bridges (deterministic, before LLM):

| Phrase (examples) | Effect |
|---|---|
| `declaro verificado el esc` / `declaro verificado el <noun>` | writer attest=True |
| `quito la verificación del esc` / `quita la verificación del <noun>` | writer attest=False |

Subject via `resolve_component_subject_noun`. Bare phrase without subject: if exactly one attest-eligible (`overlap`) component, use it; else ask which — never guess.

### 3.4 Board projector

In `_fields`, **after** `sobres` when a valid (non-stale) attestation exists:

```text
label: "verificación"
value: Declarado verificado por el Engineer — no es una comprobación geométrica de Jarvis.
```

If fingerprint stale vs current pose/geometry: omit field (and clear on next writer touch; projector may treat stale as absent without persisting — prefer persist-clear on write paths so disk stays honest).

**Do not** remove or weaken `sobres`.

### 3.5 Board / Scene3D control (in scope, minimal)

Optional control visible when Situar context or selected singleton has `sobres` = overlap and no valid attestation: **“Declarar verificado”** → POST thin bridge → same writer → refetch nodes (mirror C-113). Clear control or “Quitar verificación” when attestation present.

If POST bridge is disproportionate, IDLE-only write + Board display is acceptable **only if** report § explicitly says Board mutation deferred — prefer shipping the button when C-113 pattern already exists.

### 3.6 Untouched

`pose_envelope_screening.format_screening` strings · `ASSEMBLY_READY` · new Gaps · plate L×W · multi-hop · margin · mating faces · Conversation Engine · version bump to 0.4.2.

---

## 4. Tests (new file)

`tests/test_geometry_fit_attestation_b1.py`

| ID | Behavior |
|---|---|
| T0 | `overlap` pair → attest succeeds; field set; fingerprint stable |
| T1 | `no_overlap` → attest raises; no field |
| T2 | `pose_incomplete` → attest raises |
| T3 | After attest, pose write changing Δmm → attestation cleared |
| T4 | After attest, envelope write on child or origin changing L/W/H → cleared |
| T5 | Board `fields` include `verificación` human copy when attested; `sobres` still screening text (contains `no verificado`) |
| T6 | Readiness / `_block_progress_status` twin unchanged by attestation |
| T7 | IDLE `declaro verificado el esc` + `_RefuseLLM` → ok; LLM not called |
| T8 | `format_screening("overlap")` string **unchanged** vs pre-Buy golden |
| T9 | Pin: `test_geometry_prop_adapter_visor_x_b1.py` expects `0.4.1` (or drop brittle pin — prefer update to `0.4.1`) |

No `workspace/` mutation in tests. No network.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | `DeclaredFitAttestation` + field on `ComponentSpec` |
| `src/jarvis/core/component_writers.py` | new writer + clear hooks on pose/envelope |
| `src/jarvis/core/*_declare_assist` or thin parse next to cabe | IDLE parse |
| `src/jarvis/core/orchestrator.py` | IDLE bridge |
| `src/jarvis/workspace/spatial_board.py` | `verificación` field |
| `src/jarvis/workspace/board_pose_bridge.py` **or** sibling `board_fit_attestation_bridge.py` | optional POST |
| `ui/spatial-board/...` | optional button + POST client |
| `tests/test_geometry_fit_attestation_b1.py` | T0–T8 |
| `tests/test_geometry_prop_adapter_visor_x_b1.py` | T9 pin |
| `.jes/artifacts/implementation_report_geometry_fit_attestation_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Project **`autonomía-de-5min`** or **`10min`** with at least one `overlap` pair (e.g. `esc`→FC).

1. Board `sobres` = solapan — screening, no verificado. No `verificación` yet.  
2. `declaro verificado el esc` → card shows `verificación` human copy; `sobres` still “no verificado”.  
3. Situar-drag the ESC (or re-declare pose) → seal gone.  
4. Try attest on a known `no_overlap` subject → honest refuse.  
5. `estado` / energy / ASSEMBLY_READY unchanged.

Record `engineer_smoke_geometry_fit_attestation_b1.md`.

---

## 7. Done when

- [ ] T0–T9 green; full pytest green  
- [ ] Screening copy golden unchanged  
- [ ] No `ASSEMBLY_READY` / Gap change  
- [ ] No version bump  
- [ ] Report written  
- [ ] Engineer smoke §6  

---

## Explicitly not this IC

Automatic “encajada” alert · rename screening · margin/compose/faces · Rooster box · FEA/STEP · Conversation Engine · `fit_compare.md` stub · version bump
