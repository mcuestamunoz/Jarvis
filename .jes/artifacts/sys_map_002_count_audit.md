# SYS-MAP-002 — Connection count audit

**Date:** 2026-08-10  
**Author:** Cursor (JES)  
**Scope:** Documentation / map hygiene only. No product code. No new connections. No FN on C-042 / C-025 / C-044 / C-043.

## Verdict

**57 unique `C-xxx` is the sole canonical connection count.**

| Claim | Status |
|---|---|
| Canonical registry length = 57 | Confirmed (`CONNECTIONS.md` Canonical registry table) |
| Rollup 52 🟢 / 4 🔴 / 1 🟡 | Confirmed |
| Forbidden = 8, not C-xxx | Confirmed |
| “65 connections” | **Rejected** — counted `| C-xxx |` table cells including 8 derived re-listings |

## How 65 appeared

Duplicate leading-table rows (same IDs, second occurrence in derived summaries):

| ID | Role of second table |
|---|---|
| C-021, C-022, C-023, C-024 | Intent → handler summary |
| C-084, C-085 | Phase / Reasoning summary |
| C-093, C-094 | ProjectState → disk summary |

`57 + 8 = 65` table cells ≠ 65 connections.

Also: early review text in `implementation_review_sys_map_002.md` stated “65 edges” / “65 populated rows” — corrected in the same pass as this audit.

## Files updated this pass

| File | Change |
|---|---|
| `docs/system_map/CONNECTIONS.md` | Canonical vs derived vs forbidden structure; labels on derived summaries |
| `docs/system_map/DIAGRAMS.md` | Count semantics; explicit reject of 65 |
| `docs/system_map/jarvis-system-map.canvas.tsx` | Stats: 57 / 52 / 4 / 1 / +8 forbidden |
| `docs/system_map/README.md` | Registry blurb |
| `.jes/artifacts/implementation_review_sys_map_002.md` | Notes corrected to 57 |

## Grep hygiene

Repo search for connection-count “65” in system_map / SYS-MAP reviews: cleared after this pass. Unrelated “65” (Bug 65, motor factor 0.65) left untouched.

## Known residual risk (not fixed here)

Canvas / DIAGRAMS **manually duplicate** the canonical registry. Future FN that adds a `C-xxx` must update: Canonical registry → Detail → DIAGRAMS → canvas. Optional later: generate canvas data from the markdown table (out of scope).

## Explicit non-goals

- No Implementation Contract for C-042 / C-025 / C-044 / C-043
- No Create→BOM / FN-024
- No `src/` changes
