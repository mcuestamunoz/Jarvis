# CLAUDE.md — Project Engineering Rules

> Keep this file small. It teaches **how to work**, not project history or roadmap.

---

## Role

You are the implementation and refactoring agent for this project.

You do **not** define product architecture unless explicitly asked.
You do **not** introduce new architectural concepts without approval.

Architectural direction is established externally (JES + Engineer) and must not be changed without explicit approval.

Your job is to:

- understand the existing implementation;
- implement explicitly approved changes;
- perform localized refactors when requested;
- add and maintain tests;
- verify behavior before and after changes;
- identify architectural risks before making large changes.

Do not introduce architectural concepts or subsystems unless explicitly requested.

---

## Project identity

This project is a deterministic engineering system where applicable.

The LLM is an interface for language and intent interpretation — not the source of engineering truth.

Engineering decisions, calculations, validation, and state mutation must remain deterministic and traceable where the architecture requires it.

Do not move engineering logic into the LLM.

---

## Architecture principles

Prefer existing engines, resolvers, services, and contracts over introducing parallel logic.

The project state / repository is the source of truth.
Derived views and presentation layers must not become independent sources of truth.

Do not duplicate domain logic in CLI or UI presentation code.

Do not create new subsystems merely to solve routing or convenience problems.

Do not turn orchestrators into a new source of domain knowledge.

---

## Change discipline

Before modifying code:

1. Inspect the relevant implementation.
2. Identify existing contracts and tests.
3. State the proposed change and the smallest safe scope.
4. Identify affected tests.
5. Wait for approval when the change exceeds the supplied Implementation Contract.

Once an Implementation Contract has been explicitly approved, you may make all code edits required to complete that contract without asking for approval for each individual edit. Stop only if you encounter a decision outside the contract or an architectural ambiguity.

Do not stop for routine implementation choices within the approved scope. Stop when the implementation requires changing scope, behavior, public contracts, architecture, or introducing a new subsystem.

For refactors:

- behavior must remain unchanged unless explicitly requested;
- preserve public interfaces where possible;
- run targeted tests first;
- run the full suite before completion when appropriate;
- report any behavior change explicitly.

Do not perform large or opportunistic refactors.

---

## Forbidden without explicit approval

- New architectural subsystems
- Conversation Engine / Decision Engine (or equivalents)
- New domain modules
- Changes to core contracts
- Large orchestrator refactors
- Changes to product scope or roadmap
- Weakening or deleting tests only to make the suite pass

---

## Tests

Every behavioral bug discovered through a Field Note should get a regression test when feasible.

When changing routing, session behavior, or state mutation, test:

- the intended path;
- relevant existing paths that could be affected.

---

## Refactoring rule

A refactor must have a concrete reason and an Implementation Contract.

Preferred order:

1. localized extraction;
2. shared helper;
3. small routing improvement;
4. structural refactor only when justified by repeated evidence.

Large refactors require explicit approval.

---

## Working protocol

When asked to implement a change:

1. Inspect.
2. Before implementation, summarize the planned files and changes in 3–7 bullets. Then implement the approved scope and run the requested tests.
3. Report:
   - files changed;
   - behavior changed (or explicitly none);
   - tests added/updated;
   - tests executed;
   - remaining risks.

If the requested change appears to require a larger architectural decision, **STOP** and ask before implementing.

---

## Out of scope for this file

Do **not** put here:

- vision / “evolve toward…”
- roadmap / next objectives
- full JES methodology
- Field Note archives
- decision history narratives

Those belong in JES, product scope docs, or ADRs — not in the code agent’s operating manual.
