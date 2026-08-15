# Implementation Review — SYS-MAP-004 Routing / System Map Audit

**Project:** Jarvis  
**Date:** 2026-08-15  
**Reviewer:** Cursor (JES)  
**Type:** Audit review (no product code in scope)  

**Contract:** `.jes/artifacts/implementation_contract_sys_map_004_routing_audit.md`  
**Report:** `.jes/artifacts/sys_map_004_routing_audit.md`  
**Base:** `checkpoint-g5-dse-component-sync` (+ G3 uncommitted, treated as current)

---

## Veredicto

### **PASS WITH NOTES**

El audit es sólido, evidence-first, y acierta el veredicto primario. Cumple los 8 pass criteria del contrato. Las notes son de higiene de entregable y un matiz de framing — no invalidan B ni la cola R1→R3→R4.

| Criterio contrato §7 | Resultado |
|---|---|
| 1 Path de `"reducir payload"` under DEFINE_MISSING+battery | ✅ Turn path §2 + UX-C `:796-802` verificado |
| 2 Clasificación A/B/C/D | ✅ **B** con exclusión correcta de A y C |
| 3 C-040 reachability IDLE-only vs global | ✅ Confirmado; gate en `:931-936` |
| 4 FN-021 vs mid-arch chain | ✅ Ortogonal; no double-count |
| 5 Continuity “no motor” separado | ✅ G9 / `build_startup_context` `:2743-2794` |
| 6 Drift desde SYS-MAP-003 | ✅ Counts 59/58🟢/1🟡; checkpoint table sin drift top-level |
| 7 Ranked next cuts; zero `src/` | ✅ R1–R5; `src/` intacto |
| 8 G3 probe guidance | ✅ Workaround `cancelar` OK; P6a/P6b documentados |

---

## Qué se re-verificó (revisor)

| Claim | Código | Match |
|---|---|---|
| UX-C unconditional on `MISSING_COMPONENT_DEFINITION` | `orchestrator.py:796-802` | ✅ |
| C-040 gate | `orchestrator.py:931-936` | ✅ |
| C-040 comment already says IDLE-only | `:929-930` *"Runs only in IDLE (this code is only reached when no mode-specific branch above already returned)"* | ✅ — refuerza B (mapa overclaim; código ya es honesto localmente) |
| C-052 iterate preempt exists; DEFINE_MISSING no analogue | `:408-430` + `_ITERATE_PREEMPT_INTENTS` | ✅ |
| `CONNECTIONS.md` C-040 evidence stale `:894-899` | still cites `:894-899` | ✅ |
| `ACQUISITION_MAP` “Known issues: None” | line ~35 area | ✅ |
| Catalog-gap blind to `catalog_ref` | `:2747-2794` recomputa matches; no read de `catalog_ref` | ✅ |
| G8/G9 en `cli_findings_…` | grep → **0 hits** | ⚠ report §10 claims “Added”; closing message says EPERM — **not applied** |

---

## Acuerdo con el veredicto B

Correcto:

- Classifiers OK (`iterate` + `reducir_payload`) → no es F-1 regression.
- Structural: checkpoint 10 returns before checkpoint 18.
- Not **A**: no design/doc asserts DEFINE_MISSING sticky-vs-engineering as intentional product policy.
- Not **C**: FN-021 only post-completion clear/chain.
- **B**: map presents C-040 / authority precedence without mode-gating caveat; ACQUISITION claims no known issues.

Matiz (note, no downgrade): el **código** del gate C-040 ya declara “only in IDLE”. El overclaim es documental (CONNECTIONS / ACQUISITION / AUTHORITY presentation), no un autoengaño del runtime comment. El audit lo dice en sustancia; merece una línea explícita en R1.

---

## Notes (no bloquean PASS)

1. **§10 vs realidad:** G8/G9 **no** están en `cli_findings_post_catalog_bind_v1.md`. El informe dice “Added”; el cierre de Claude dice EPERM. Hay que pegarlos (contenido debería estar en el audit — si no está verbatim en §10, reconstruir desde §1/§6/§8 R2). Hasta entonces el finding register está stale.

2. **C-040 code comment:** incluir en R1 que el runtime ya documenta IDLE-only; el fix de mapa es alinear CONNECTIONS/ACQUISITION con ese hecho, no “descubrir” un hecho nuevo en código.

3. **Ownership nuance ACQUISITION vs Runtime:** UX-C vive en `orchestrator` DEFINE_MISSING branch; `_handle_component_description` es acquisition-shaped. Apuntar G8 como cross-cutting Runtime↔Acquisition es más preciso que “owned solely by Acquisition” — fine for R1 one-liner.

4. **G3 + R1 C-042/C-106:** el audit correctamente aplaza documentar G3 hasta commit. Mantener ese orden.

5. **R3/R4 framing:** excelente advertencia de no portar `_should_preempt_iterate_wizard` verbatim (`collected_params`). Cursor concurre: **no autorizar FN de preempt sin design note R3**.

6. **G9 vs F-5/F-6:** elevación a confirmed-with-repro es correcta; no fusionar con G8; no forzar en C-081.

---

## Cola recomendada (post-review)

```text
1. Pegar G8 + G9 en cli_findings (doc only)     ← inmediato
2. R1 map-only (C-040 caveat + ACQUISITION known issue + line cites)
3. G3 CLI probe con workaround `cancelar` → checkpoint-g3
4. R3 design note — DEFINE_MISSING preempt policy (Engineer)
5. Solo entonces R4 FN closing G8
   (G9 aparte; no Impl C / no Conversation Engine)
```

**G3 PROBE:** concurro — workaround OK; no bloquear checkpoint G3 por G8.

---

## Conclusión

SYS-MAP-004 hace exactamente lo que pedía el contrato: explica el sticky mid-arch con path de código, clasifica B, separa Continuity/catalog honesty, y deja una cola segura sin implementar.

**Listo para Engineer:** aplicar findings register + R1 cuando lo pida; no abrir FN de routing todavía.
