# Implementation Contract — Intelligence package scaffold (`B1-intelligence-scaffold`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.1`**

**Status:** ★ **AUTHORIZED** — await Claude implementation + report  
**Parents:**
- [`DC-assistant-placement`](design_contract_assistant_placement_b0.md) — **★ ACCEPT CLOSED** (placement lock)  
- Ontology explain **CLOSED @ `v0.6.0`** — [close note](engineer_note_v0_6_0_ontology_epoch_close.md)  
- [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md) §7 branch (a)  
- [`docs/ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md) — explain SoT for **later** R2 (not this Buy)  
- Tip / package base: **`v0.6.0` / `0.6.0`**

**Type:** **Scaffold only** — open `src/jarvis/intelligence/` on disk (same grain as C1 `capabilities/` empty registry).  
**Opens package/tag:** **`0.6.1` / `v0.6.1`** on Engineer ACCEPT (report which commit).  
**Not** ontology retrieve (A2/R2) · not terminal canal (A3) · not voice/world/STT · not Continuity/LLM cite · not Conversation Engine · not `flight_software` calls.

**Outputs (required):**
1. `src/jarvis/intelligence/` package on disk (see §0)  
2. README honesty locks  
3. Tests (see §4)  
4. `.jes/artifacts/implementation_report_intelligence_scaffold_b1.md`  
5. Living-doc pointers: PRIORIDAD A1 · ARCHITECTURE knowledge § · PLATFORM placement line  
6. `pyproject.toml` → **`0.6.1`**; git tag **`v0.6.1`** only after Engineer ★ ACCEPT (may be same closeout or follow-up — report which)

**Checkpoint base:** **`v0.6.0` / `0.6.0`** until this Buy lands **`0.6.1`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-intelligence-scaffold`** — empty Assistant home package |
| 2 | Path | **`src/jarvis/intelligence/`** only. Do **not** create `world/` in this Buy |
| 3 | Placement | Per DC ★: Assistant lives here; **≠** `flight_software/` · **≠** swallow `core/` Continuity · **≠** MCU `native/` |
| 4 | Contents (minimal) | `__init__.py` (package docstring) · `README.md` (honesty) · optional empty placeholder module **only if** needed for clean imports — prefer minimal |
| 5 | No retrieve yet | **No** reading `ontology/` · **no** cite API · **no** RAG · **no** LLM calls |
| 6 | No execution | **No** Intent→actuator · **no** `submit_command` · **no** Safety gate · **no** orchestrator fork |
| 7 | Forbidden imports | Package must **not** import `jarvis.flight_software` or `jarvis.vehicle_profiles` (test-enforced). Do **not** silently reuse empty `knowledge/retriever.py` as the Assistant retrieve surface |
| 8 | Craft untouched | **No** Continuity / Board / `library/` / CLI behavior changes in this Buy |
| 9 | Version | Bump to **`0.6.1`**; tag `v0.6.1` on Engineer ACCEPT |
| 10 | Forbidden | Conversation Engine · voice · house map · inventing available flight · ontology write · R2 scope creep |

**Product sentence:**

```text
Abrir intelligence/ en 0.6.1 como casa vacía del Assistant —
importable, documentada, sin retrieve ni control de vuelo.
```

---

## 1. Package shape (normative)

```text
src/jarvis/intelligence/
├── __init__.py      # docstring: Assistant platform home; scaffold only
└── README.md        # honesty locks (see §2)
```

`__init__.py` may export a single constant e.g. `SCAFFOLD_STATUS = "stub"` or remain docstring-only — either OK if tests pass.

**Do not** add `retrieve.py`, `assistant.py`, `memory.py`, or world schemas in this Buy.

---

## 2. README honesty (must state)

- This package is the **Assistant / intelligence column** home (DC placement ★).  
- **Scaffold ≠ Assistant shipped** · **≠** ontology retrieve · **≠** voice.  
- Does **not** call `flight_software` / ESC / mixer.  
- Does **not** decide Continuity craft steps.  
- Ontology vault EXPLAINS; retrieve is **A2** (`B1-ontology-retrieve-r2`).  
- Tip parent: ontology closed @ `v0.6.0`.

---

## 3. Living docs (pointers only)

Update briefly (no rewrite epics):

- `docs/IMPLEMENTATION_TASKS.md` — A1 state when reporting  
- `docs/ARCHITECTURE.md` knowledge trees — one line: `intelligence/` exists as stub  
- `docs/PLATFORM_CAPABILITY_VISION.md` placement line — scaffold on disk @ `0.6.1`

---

## 4. Tests (required)

New module e.g. `tests/test_intelligence_scaffold_b1.py`:

| ID | Assert |
|---|---|
| T1 | `import jarvis.intelligence` succeeds |
| T2 | Package path exists under `src/jarvis/intelligence/` |
| T3 | Source tree of `intelligence/` does **not** contain imports of `jarvis.flight_software` or `jarvis.vehicle_profiles` (grep/AST) |
| T4 | README exists and mentions scaffold / not retrieve (substring check OK) |
| T5 | No new call into Continuity/orchestrator from `intelligence/` |

Do **not** weaken existing suite.

---

## 5. Acceptance criteria

- [ ] Package on disk + README  
- [ ] Tests T1–T5 green  
- [ ] Implementation report at required path  
- [ ] Docs pointers updated  
- [ ] `pyproject.toml` = `0.6.1`  
- [ ] No ontology retrieve · no `world/` · no CLI Assistant canal  
- [ ] Tag `v0.6.1` only after Engineer ACCEPT  

---

## 6. Stop conditions

- Do not implement R2 retrieve.  
- Do not wire CLI.  
- Do not claim Assistant “works” beyond importable scaffold.  
- Do not claim ACCEPT — Cursor review + Engineer.

---

## 7. Paste for Claude

```text
★ AUTHORIZED implementation — B1-intelligence-scaffold

IC: .jes/artifacts/implementation_contract_intelligence_scaffold_b1.md

Create src/jarvis/intelligence/ (__init__.py + README honesty).
No ontology retrieve, no world/, no flight_software imports,
no Continuity/CLI changes. Tests T1–T5.
Bump pyproject to 0.6.1 (tag v0.6.1 only after Engineer ACCEPT).
Write implementation_report_intelligence_scaffold_b1.md

Parent tip v0.6.0. No ACCEPT claim.
```
