---
id: forma-medicion-banco-empuje
nombre: Forma de medición en banco de empuje
area: Ingeniería
subarea: Electrónica / propulsión
nivel: intermedio
estado: draft
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-5]
---

# Forma de medición en banco de empuje

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Forma de medición en banco de empuje
La **forma de medición en banco de empuje** (*thrust-stand measurement shape*) es el conjunto mínimo de **condiciones + magnitudes + metadatos** que deben acompañar un resultado de ensayo (thrust, corriente, RPM, …) para que el dato sea interpretable y reutilizable.

No es un valor de thrust. Es el **contrato de evidencia** de un OP medido — frente a una especificación de catálogo o a un número suelto.

Relacionado: [[Punto de operación vs capacidad intrínseca]].

---
## [INTUICION] Forma de medición en banco de empuje
“Medí 800 gf” sin decir motor, hélice, tensión, ESC, RPM ni atmósfera **no es un OP usable**.

Forma mínima conceptual:

```text
conjunto: motor + hélice + ESC + alimentación
condiciones: V, I, RPM (si hay), atmósfera / T
resultado: thrust (+ potencias si se miden)
metadatos: fecha, instrumento, método, incertidumbre (si hay)
```

Sin esa forma, el número no debe entrar en `library/` como hecho citado ni cerrar HD-*.

---
## [FUNDAMENTO] Forma de medición en banco de empuje
- Un resultado de banco es un **OP del conjunto**, no una propiedad intrínseca del motor solo.
- HD-004 / HD-005 piden curvas o puntos con **esta disciplina**; la ontología describe la forma, **no inventa la curva**.
- Distinguir:
  - T1 — dato de fabricante para ese conjunto/condiciones;
  - T2 — ensayo propio instrumentado;
  - estimado — método declarado, no fingir medición.
- No mezclar un blob motor+ESC+hélice de stand con η de ESC aislado (ver límites HD-002).

---
## [EJEMPLO] Forma de medición en banco de empuje
HD-005 (conceptual): falta OP del combo XING-E + Gemfan 51466-3 + 4S.  
La nota dice *qué habría que registrar* en un T2; **no** inventa `thrust_gf` ni cierra el HD.

---
## [PROCEDIMIENTO] Forma de medición en banco de empuje
1. Nombrar SKUs / piezas del conjunto.
2. Fijar y registrar condiciones (V, prop, régimen).
3. Medir magnitudes acordadas (thrust, I, …).
4. Conservar forma completa al almacenar o citar.
5. Marcar estimado vs medido.
6. No completar huecos inventando puntos intermedios.

---
## [USO_PROBLEMAS] Forma de medición en banco de empuje
Diseño de campañas T2, revisión de tablas de fabricante, honestidad de catálogo, interpretación de HD-*.

---
## [APLICACIONES] Forma de medición en banco de empuje
**Jarvis catalog/craft:** plantilla conceptual de evidencia para OPs — no escribe `library/`.  
**Jarvis HD-\*:** explain de *qué falta*, sin campaña de lab automática.

---
## [CONEXIONES] Forma de medición en banco de empuje
- [[Punto de operación vs capacidad intrínseca]]
- [[Motores]]
- [[Motor DC]]
- [[Actuadores]]
- [[Corriente y circuitos]]
- [[C-rate de batería]]
- [[Empuje]]
- [[Hélice]]

---
## [ERRORES] Forma de medición en banco de empuje
- Publicar thrust sin condiciones.
- Usar OP de otra hélice/tensión como si fuera el craft.
- Inventar curva “para cerrar” HD-004/HD-005.
- Confundir stand conjunto con η ESC aislada.
- Tratar un único punto como capacidad universal del motor.

---
## [NOTAS] Forma de medición en banco de empuje
Borrador Cursor spine-lote-5 (2026-09-28). Nota **nueva** (vision §8.1 #12). Engineer + GPT cite → Cursor land `solid`.

---
## [REFERENCIAS] Forma de medición en banco de empuje
(pendiente cite pass — candidatos: docs Jarvis HD-004/005; buenas prácticas thrust-stand / motor testing; maxon/TI OP discipline ya citada en lote-4)

---
## [ESTADO] Forma de medición en banco de empuje
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-5
- estado: draft
