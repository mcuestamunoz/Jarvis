# Implementation Contract — Capability registry product fill (`B1-capability-registry-product-fill`)

**Project:** Jarvis  
**Date:** 2026-09-29  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.10`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS · smoke OK; package/tag **`0.6.10` / `v0.6.10`**.
**Parents:**
- [`design_contract_capability_registry_product_fill_b0.md`](design_contract_capability_registry_product_fill_b0.md) — ★ **ACCEPT CLOSED** 2026-09-29 (Engineer: redacta)
- C1 [`B1-fase-c-capability-registry-scaffold`](implementation_contract_fase_c_capability_registry_scaffold_b1.md) — ★ CLOSED @ **`v0.5.0`** — empty seed + schemas without `available` / `software`
- T0 / T1 ★ CLOSED @ **`v0.6.8` / `v0.6.9`** — Task strings `ontology.explain` · `engineering.continuity`
- Tip / package parent: **`v0.6.9` / `0.6.9`**

**Type:** **Product seed + schema honesty extend** — first non-empty default Capability Registry for the two software capabilities Assistant Tasks already require. Registry stays **descriptive** (no dispatcher).  
**Opens:** **`0.6.10` / `v0.6.10`** on Engineer ACCEPT.  
**Cola:** **T2**

**Not:** Task→registry lookup before emit · Safety · FS · vehicle/device actuation · voice/world · R4 · Continuity ranking · Skills catalog · Capability UI · Conversation Engine.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-capability-registry-product-fill`** |
| 2 | Enum extend | `CapabilityAvailability.AVAILABLE = "available"`. Keep `stub` / `not_implemented`. **Do not** add `ready` / `healthy` |
| 3 | Provider kind | `ProviderKind.SOFTWARE = "software"`. Keep `vehicle` / `device` |
| 4 | Seed shape | **Two** software providers (not one combined): `provider.ontology_explain` offers `["ontology.explain"]`; `provider.engineering_continuity` offers `["engineering.continuity"]`. Skills array stays **`[]`** |
| 5 | Capability rows | Exactly these two in product seed (plus no extras this Buy): |
| | | • `id=ontology.explain`, `version="0.6.10"`, `provider_id=provider.ontology_explain`, `availability=available`, `health=unknown`, `requirements=[]` |
| | | • `id=engineering.continuity`, `version="0.6.10"`, `provider_id=provider.engineering_continuity`, `availability=available`, `health=unknown`, `requirements=[]` |
| 6 | Load path | `CapabilityRegistry.load_default()` continues to read `data/default_registry.json` — update that file; do **not** hardcode a second seed in Python |
| 7 | Id sync | Seed capability ids **must** equal `jarvis.intelligence.assistant_task.CAPABILITY_ONTOLOGY_EXPLAIN` and `CAPABILITY_ENGINEERING_CONTINUITY` (test asserts). Do **not** change those constant values |
| 8 | Task / orchestrator | **Zero** changes to `assistant_task.py`, orchestrator Task wire, Continuity ranking, explain cite — this Buy is registry/schema/docs/tests only |
| 9 | Honesty | No flight / HOLD / LAND / GO_TO / radio capability rows. No `vehicle`/`device` providers in product seed. No execute/dispatch methods on `CapabilityRegistry` |
| 10 | C1 tests | Update stale C1 asserts that required empty seed / rejected `available` / enum size — see §3. Do **not** weaken reject-on-load / no-dispatch tests |
| 11 | Version | Bump **`0.6.10`**; tag only after ACCEPT |
| 12 | Docs | `src/jarvis/capabilities/` module docstrings (`schemas.py`, `registry.py`) · capabilities package `__init__` / short README if present · PLATFORM_CAPABILITY_VISION §13 one-liner (scaffold ≠ empty forever; product seed is software-only) · CONNECTIONS: prefer **extend** existing Fase C / capabilities note (**no new C-xxx**) · PRIORIDAD T2 · intelligence README one pointer that Task capability strings now appear in default registry |

**Product sentence:**

```text
load_default() ya no está vacío: ontology.explain y engineering.continuity
están available vía providers software — sin dispatcher ni vuelo fingido.
```

---

## 1. Normative seed (`default_registry.json`)

```json
{
  "capabilities": [
    {
      "id": "ontology.explain",
      "version": "0.6.10",
      "provider_id": "provider.ontology_explain",
      "availability": "available",
      "requirements": [],
      "health": "unknown"
    },
    {
      "id": "engineering.continuity",
      "version": "0.6.10",
      "provider_id": "provider.engineering_continuity",
      "availability": "available",
      "requirements": [],
      "health": "unknown"
    }
  ],
  "providers": [
    {
      "id": "provider.ontology_explain",
      "kind": "software",
      "offered_capability_ids": ["ontology.explain"],
      "health": "unknown"
    },
    {
      "id": "provider.engineering_continuity",
      "kind": "software",
      "offered_capability_ids": ["engineering.continuity"],
      "health": "unknown"
    }
  ],
  "skills": []
}
```

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Schema | `src/jarvis/capabilities/schemas.py` | Add `AVAILABLE`; add `SOFTWARE`; refresh module docstring (C1 “no available” claim is superseded for software-only) |
| Registry | `src/jarvis/capabilities/registry.py` | Docstring: `load_default` is no longer always empty; still descriptive-only |
| Seed | `src/jarvis/capabilities/data/default_registry.json` | §1 contents |
| Tests | `tests/test_capability_registry_product_fill_b1.py` (**new**) | T1–T7 |
| C1 adapt | `tests/test_fase_c_capability_registry_scaffold_b1.py` | Retarget empty/available/seed honesty tests — see §3 |
| Version | `pyproject.toml` | `0.6.10` |
| Docs | capabilities docs · PLATFORM §13 · CONNECTIONS · intelligence README pointer · PRIORIDAD | §0.12 |

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | `load_default()` has exactly the two capability ids; both `availability == available`; skills empty |
| T2 | Both providers exist, `kind == software`, and `providers_offering` returns the expected provider for each capability |
| T3 | Capability ids match `assistant_task.CAPABILITY_ONTOLOGY_EXPLAIN` / `CAPABILITY_ENGINEERING_CONTINUITY` |
| T4 | Product seed JSON contains **no** capability id starting with `flight` / containing `hold`/`land`/`go_to` (casefold); no provider `kind` in `{vehicle, device}` |
| T5 | `CapabilityAvailability` includes `available`; `ProviderKind` includes `software`; `"ready"` still rejected on CapabilityRecord |
| T6 | AST / public API: `CapabilityRegistry` still has no public method name containing execute/dispatch/command_esc/actuat (same grain as C1 T9) |
| T7 | `pyproject` reads `0.6.10` |

**C1 adaptations (mandatory, not weakenings):**

- `test_t1_load_default_is_empty` → rename/replace: default is the §1 seed (or move assert into new T1 and delete empty assert)
- `test_t8_availability_enum_rejects_available` → `available` **accepted**; enum set = `{stub, not_implemented, available}`; `ready` still rejected
- `test_default_seed_file_is_honestly_empty` → replace with honesty: seed matches §1 shape; no flight/`vehicle`/`device` in product seed
- Leave reject-on-load / no-dispatch tests intact
- Bump any stale version-checkpoint in nearby suites forward per established pattern (including leftover `0.5.44` / `0.6.9` asserts when touched)

---

## 4. Acceptance

- [ ] Schema enums extended; seed §1 loads via `load_default`  
- [ ] Id sync with Assistant Task constants  
- [ ] No dispatcher / no flight available / T0–T1 code untouched  
- [ ] Tests T1–T7 · C1 adapted · report · docs · package `0.6.10`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.10`**

---

## 5. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-capability-registry-product-fill (T2)

IC: .jes/artifacts/implementation_contract_capability_registry_product_fill_b1.md
DC: .jes/artifacts/design_contract_capability_registry_product_fill_b0.md (★ CLOSED)

Extend CapabilityAvailability with available; ProviderKind with software.
Fill data/default_registry.json per IC §1 (two capabilities + two software
providers; skills []). load_default() still reads that file.
Do NOT touch assistant_task / orchestrator Task wire / Continuity ranking.
Do NOT add dispatcher methods. No flight/vehicle/device in product seed.
Update C1 tests that assumed empty seed / rejected available.
New tests T1–T7 (include id sync with assistant_task capability constants).
Bump pyproject to 0.6.10. Docs: schemas/registry docstrings, PLATFORM §13,
CONNECTIONS extend (no new C-xxx), intelligence README pointer, PRIORIDAD.
Report. Parent tip v0.6.9. No ACCEPT claim.
```

---

## 6. Engineer gate

Reply **★** (or “procede / implementa”) to authorize Claude.  
Until then: **no `src/` for this Buy.**
