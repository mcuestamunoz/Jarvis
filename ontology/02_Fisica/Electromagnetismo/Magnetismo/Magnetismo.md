---
id: magnetismo
nombre: Magnetismo
area: Física
subarea: Electromagnetismo
nivel: base
estado: draft
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-5]
---

# Magnetismo

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Magnetismo
El **magnetismo** describe campos y fuerzas asociados a imanes y a corrientes eléctricas. En robótica aérea, la magnitud práctica más citada es el **campo magnético terrestre** (y campos locales), medido por un **magnetómetro** para aportar información de **rumbo / yaw** relativo al norte magnético.

Un magnetómetro **no** forma parte necesariamente de una IMU de 6 ejes ([[IMU]]). Cuando se usa, aporta una observación de campo — no una actitud verdadera por sí sola.

---
## [INTUICION] Magnetismo
“¿Hacia dónde apunta el vehículo en el plano horizontal?”

```text
campo magnético (tierra + entorno)
        ↓
   magnetómetro
        ↓
  observación B (cuerpo)
        ↓
 estimador / fusión (p. ej. yaw)
        ↓
  heading estimado ≠ verdad absoluta
```

Disturbios (hierro, corriente de motores, cables) y declinación magnética hacen que **B medido ≠ “norte geográfico libre de error”**.

---
## [FUNDAMENTO] Magnetismo
- Campo $\mathbf{B}$ en el marco del sensor; necesita montaje, ejes y calibración.
- Contribuye a **heading / yaw**; no sustituye gyro/accel para dinámica completa.
- En Jarvis FS: C37 usa mag **simulado** + referencia de yaw — **sim mag ≠ cobre / ≠ calibración de vuelo**.
- Relacionado: [[Campo magnético]] · [[Fuerza magnética]] · [[Inducción electromagnética]] · [[Ley de Faraday]] · [[Magnetómetro]] · [[IMU]].

---
## [EJEMPLO] Magnetismo
Jarvis:

```text
C7 attitude (sin mag)
   → C37 mag yaw rung (sim)
   → yaw stick / heading reference
```

Explica el papel del mag en la escalera FS; no valida un magnetómetro concreto del craft.

---
## [PROCEDIMIENTO] Magnetismo
1. Separar IMU 6-DoF vs unidad con mag / AHRS.
2. Declarar marco de ejes y montaje.
3. Tratar mag como observación, no como actitud final.
4. No inventar soft-iron/hard-iron ni declinación sin fuente o ensayo.
5. En FS: etiquetar sim vs hardware.

---
## [USO_PROBLEMAS] Magnetismo
Heading, fusión de actitud, diagnóstico de interferencias, mapear C37 a conceptos físicos.

---
## [APLICACIONES] Magnetismo
**Jarvis FS:** explain map C37 (mag yaw).  
**Jarvis craft:** vocabulario para sensores de rumbo — sin inventar SKU.

---
## [CONEXIONES] Magnetismo
- [[Campo magnético]]
- [[Fuerza magnética]]
- [[Inducción electromagnética]]
- [[Ley de Faraday]]
- [[Magnetómetro]]
- [[IMU]]
- [[Giroscopio]]
- [[Sensores de movimiento]]
- [[Control robótico]]
- [[Navegación y planificación]]

---
## [ERRORES] Magnetismo
- Tratar mag como actitud verdadera.
- Asumir que toda IMU incluye magnetómetro.
- Ignorar interferencias del craft (ESC, motores, acero).
- Confundir norte magnético con norte geográfico sin declinación.
- Inventar calibración o sesgos sin ensayo.
- Confundir mag simulado (C37) con mag en cobre.

---
## [NOTAS] Magnetismo
Borrador Cursor spine-lote-5 (2026-09-28). Sustituye stub de wikilinks. Engineer + GPT cite → Cursor land `solid`.

---
## [REFERENCIAS] Magnetismo
(pendiente cite pass — candidatos: OpenStax electromagnetismo; AD/TDK magnetometer app notes; NASA attitude sensing)

---
## [ESTADO] Magnetismo
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-5
- estado: draft
