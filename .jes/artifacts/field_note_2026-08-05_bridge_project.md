# Field Notes

## 2026-08-05 — Cerrar proyecto real (inspección puentes)

**Proyecto:** Jarvis / `inspección-de-puentes-…-9656971237a1`

**Problema observado:**
1. Diseño en `fail` por `motor_count=1` y batería 300 Wh (2 kg) incompatible con `max_weight_kg=2`.
2. Al persistir el cierre, `workspace_path` en `state.json` apuntaba a ruta legacy `…/Ingenieria/Ingenieria/06_Proyectos/…` → `PermissionError` / mkdir fallido. Mismo patrón que el test `test_answer_wizard_bidir_no_match_falls_to_positional`.

**Consecuencia:**
- Sin reparación de path, calculate/simulate en memoria funciona pero no se puede guardar historia/vistas.
- Fricción de ~2–5 min para diagnosticar path vs física.

**Idea / evidencia para JES:**
- Al restaurar un ciclo/proyecto, JES (o Jarvis) debería **validar `workspace_path` vs ubicación real del `state.json`** y ofrecer repair, o derivar siempre el path del archivo cargado.
- Field note útil para Phase 3 Engineer Interface: “dónde estoy / path roto” es un dolor real al retomar proyectos migrados.
