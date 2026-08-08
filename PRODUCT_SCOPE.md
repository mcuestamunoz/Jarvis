# Jarvis — Product scope (v1 usable)

**Target:** leave “prototype” and become a product an engineer can use to **close** an aerial design project — and **reopen it weeks later without losing the thread**.

## When a project is “done” (design slice)

1. Objective + restrictions + architecture blocks are defined.
2. Simulation is **`pass`** with restrictions met — or failure reasons are unambiguous.
3. State / history / views are auditable.
4. **Physical requirements** are explicit (thrust needed, autonomy target, max mass, margin).
5. Component **BOM / gaps**: what is defined, incomplete, declarative-only, or missing.
6. Catalog gaps are honest: “you need X; I have no matching part” — never invent a SKU.

## Project Continuity (always)

Independent of “done”: every status/startup answer must state:

| Question | Field |
|----------|--------|
| Where am I? | `continuity.situation` |
| Why? | `continuity.evidence` |
| What’s the single next useful step? | `continuity.next_useful_step` (+ why) |

Detail: [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md).

## In scope (v1)

- Aerial-first (inspection / photography / light delivery class).
- Deterministic calculate / simulate / iterate / DSE.
- CLI + MCP.
- Small curated motor catalog matched to **design space** (D8), not KV alone.
- Simplified energy model with **visible honesty** when autonomy is a hard constraint.
- Unified Project Continuity surface on status/startup.

## Out of scope (v1)

- CAD / FEM
- Live marketplace / external catalog sync
- Full ground-vehicle parity
- Perception / comms / manipulation blocks ([FUTURO](docs/IMPLEMENTATION_TASKS.md))
- Purchase / assembly / firmware **modules** (may appear later as *kinds of next step*)

## Acceptance checklist (E2E)

- [ ] Create aerial project with objective + restrictions
- [ ] Define propulsion, energy, structure, control (as needed)
- [ ] `calculate` + `simulate` → pass (or clear fail)
- [ ] Status shows requirements + BOM/gaps
- [ ] Motor suggestion matches requirements or declares catalog gap
- [ ] Autonomy restriction shows simplified-model note when relevant
- [ ] Reopen project → Continuity answers situation + evidence + **one** next step (no competing hints)

See also: [VISION.md](VISION.md).
