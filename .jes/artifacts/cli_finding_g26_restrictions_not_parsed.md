# G26 — `cambia restrictions a autonomía X min` no actualiza `restrictions` / `parsed_constraints`

**Date:** 2026-08-21  
**Severity:** 🟡 product / routing  
**Status:** OPEN — Engineer CLI full-project walk (post–Impl C)  
**Project:** `autonomia-5540bda0ac16`

## Observed

```text
User > cambia restrictions a autonomia minima 15 min

Jarvis > Parámetros aplicados: autonomia=15.0
```

Disk after turn:

```text
restrictions: "no"              ← unchanged
current_parameters.autonomia: 15.0   ← invented loose key
parsed_constraints: {}          ← still empty
Requirements: INCOMPLETE        ← ERF still sees defined=False
```

## Expected

```text
restrictions: "... autonomia minima 15 min ..." (or equivalent)
parsed_constraints.autonomy_min: 15.0
Requirements.defined: True
```

(Then unmet autonomy vs ~2.5 min sim may surface as requirements gap — honest.)

## Why it matters (system)

Blocks ASSEMBLY READY for an otherwise 4/4 + BOM/Catalog PASS project when the user tries to quantify the objective mid-session. Continuity still pushes “aumentar payload” instead of “aumentar batería / autonomía”.

## Related

- `state_schema._parse_constraints` only reads `restrictions` / `objective` for `\d+ min`
- ERF `_requirements_evidence.defined = bool(parsed_constraints)`

---

**End of finding.**
