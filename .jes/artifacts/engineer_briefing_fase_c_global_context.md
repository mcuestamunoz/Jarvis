# Briefing — Jarvis: estado global + Fase C (para otra IA)

**Fecha:** 2026-09-20 (truth-sync)  
**Audiencia:** agente / modelo que entra en frío  
**Autoridad viva:** `docs/IMPLEMENTATION_TASKS.md` § PRIORIDAD · [truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md) · ICs/reviews en `.jes/artifacts/` · código en `src/`  
**No es:** roadmap inventado · permiso para implementar · Design Contract nuevo  

---

## 0. En una frase

Jarvis es un **sistema de ingeniería determinista** (diseño de craft / BOM / Continuity / Board) al que se está añadiendo, en el **mismo monorepo**, una **arquitectura de plataforma** para operar sistemas físicos (el dron es el primero). Fase C construye contratos y stubs honestos — **aún no vuela nada**.

---

## 1. Principios que no debes romper

1. **LLM ≠ verdad de ingeniería.**  
2. **Un Buy = un IC.** No inventes paquetes/runtime/`available` flight sin ★.  
3. **Roles:** Cursor IC/review · Claude implementa tras ★ · Engineer ACCEPT (+ tag si el IC lo pide).  
4. **Craft SoT intacto** salvo IC que diga lo contrario.  
5. **Honestidad:** scaffold / RejectAll ≠ producto listo.  
6. **Visión ≠ implementación.** Solo un IC crea árboles en disco.  
7. **Docs tip vs tags:** no creas ACCEPT/tag solo porque el report lo diga — verifica `git tag` y tip commit ([truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md)).

---

## 2. Dos dimensiones

| Dimensión | Qué | Path | Estado |
|---|---|---|---|
| **Craft** | Diseño físico | `core/`, `library/`, Board | SoT **`v0.4.3`** |
| **Platform** | Operación (Fase C) | `capabilities/`, `flight_software/`, `vehicle_profiles/` | Tagged tip **`v0.5.1`**; WT ahead |

**Naming:** craft `flight_controller` (BOM) ≠ `flight_software.flight_control` (spine).

---

## 3. Snapshot verificado (truth-sync)

| Ítem | Valor |
|---|---|
| Git tip commit | `fbda5cc` Accept C3 |
| Tags | `v0.5.0`, `v0.5.1` — **no** `v0.5.2`/`v0.5.3` |
| `pyproject` on disk | **`0.5.3`** (ahead of tags) |
| Suite WT | **3236** passed, 1 skipped |
| C1–C3 | ACCEPT CLOSED |
| C4 | Code + Cursor **PASS** — **await ACCEPT + commit + tag v0.5.2** |
| C5 | Code in WT (`radio.py`) — **await Cursor review** (no report on disk) |
| PRIORIDAD | Process gate — ACCEPT C4 then review C5 |

---

## 4. Scaffold en lenguaje llano

Lee **`docs/ARCHITECTURE.md` §1a** — definición de scaffold, craft vs platform, tabla archivo→frase.

---

## 5. Fase C Buys

```text
C0 ★ DC              DONE
C1 registry @ v0.5.0 DONE
C2 Intent+RejectAll  DONE @ 0.5.0 (no tag)
C3 HAL+IMU @ v0.5.1  DONE
C4 autonomy surface  PASS → await ACCEPT / tag v0.5.2
C5 radio dual-role   code in WT → await review / tag v0.5.3
```

---

## 6. Layout

```text
src/jarvis/
├── core/                 # craft
├── capabilities/         # C1+C2 (+ radio.py C5 si presente)
├── flight_software/
│   ├── flight_control/   # C3
│   └── autonomy/         # C4
└── vehicle_profiles/     # C3
```

---

## 7. Prohibido asumir

No vuela · RejectAll · registry vacío · C3 ≠ ladder ESC · Intent C2 ≠ Continuity wired · radio stub ≠ ELRS live · **docs que digan tag v0.5.2 sin `git tag` = drift**.

---

## 8. Enlaces

| Qué | Path |
|---|---|
| **Truth-sync** | `.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md` |
| **Scaffold llano** | `docs/ARCHITECTURE.md` §1a |
| PRIORIDAD | `docs/IMPLEMENTATION_TASKS.md` |
| Visión | `docs/PLATFORM_CAPABILITY_VISION.md` |
| C4 review | `.jes/artifacts/implementation_review_fase_c_autonomy_surface_b1.md` |
| C5 IC | `.jes/artifacts/implementation_contract_fase_c_radio_dual_role_b1.md` |

---

## 9. Mensaje de arranque

```text
Jarvis monorepo: Craft SoT v0.4.3 intacto. Fase C tagged tip v0.5.1 (C3).
Working tree may have C4 (PASS, untagged) + C5 radio stub (unreviewed);
pyproject may say 0.5.3. No flight. Read ARCHITECTURE §1a + PRIORIDAD +
engineer_note_docs_truth_sync_fase_c_2026_09_20.md before claiming ACCEPT/tags.
```
