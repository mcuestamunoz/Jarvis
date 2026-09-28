---
id: corriente-y-circuitos
nombre: Corriente y circuitos
area: Física
subarea: Electromagnetismo
nivel: base
estado: solid
jarvis_relevance: [craft, catalog, fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — OpenStax Physics Ch.19 (I, Ohm, P=VI); OpenStax College Physics §§20.2–20.4; University Physics Vol.2 §9.3
tags: [spine, lote-4]
---

# Corriente y circuitos

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Corriente y circuitos
La **corriente eléctrica** es la tasa de flujo de carga eléctrica a través de una sección. Se define como:

$$
I = \frac{\Delta Q}{\Delta t}
$$

donde $I$ es la corriente, $\Delta Q$ la carga que atraviesa la sección y $\Delta t$ el intervalo de tiempo. Su unidad SI es el amperio (A), equivalente a C/s.

Un **circuito eléctrico** es un conjunto de elementos conectados mediante el que pueden circular corrientes y producirse transferencias de energía. Entre sus elementos pueden existir fuentes, resistencias, cargas y otros componentes eléctricos.

La relación entre tensión, corriente y resistencia en un elemento **óhmico** viene dada por la ley de Ohm:

$$
V = IR
$$

La ley de Ohm es una relación constitutiva que no es universal: existen componentes y materiales no óhmicos para los que la relación entre $V$ e $I$ no es lineal.

La **potencia eléctrica** describe la tasa de transferencia de energía eléctrica. Para una tensión $V$ y una corriente $I$, la potencia eléctrica instantánea puede expresarse como:

$$
P = VI
$$

con la convención de signos adecuada para distinguir potencia suministrada y absorbida.

---
## [INTUICION] Corriente y circuitos
En un sistema eléctrico, una fuente proporciona energía y los elementos conectados reciben, almacenan, convierten o disipan esa energía.

En un craft:

```text
batería
   ↓
distribución / cables
   ↓
ESC / electrónica
   ↓
motor
   ↓
carga mecánica
```

La corriente que circula depende del circuito y de las condiciones de operación. No debe suponerse que un componente consume una corriente fija simplemente porque tenga una corriente máxima especificada.

La tensión tampoco debe confundirse con energía. La tensión es una **diferencia de potencial eléctrico**, mientras que la energía depende además de la cantidad de carga transferida.

La potencia es una tasa:

$$
P = \frac{E}{t}
$$

y, eléctricamente:

$$
P = VI
$$

Por tanto, una batería puede proporcionar distintas potencias instantáneas dependiendo de la tensión y corriente de operación.

---
## [FUNDAMENTO] Corriente y circuitos
### Corriente eléctrica

La definición fundamental es:

$$
I = \frac{\Delta Q}{\Delta t}
$$

Para una corriente variable en el tiempo, la forma instantánea es:

$$
I(t) = \frac{dQ}{dt}
$$

---
### Ley de Ohm

Para un elemento óhmico:

$$
V = IR
$$

y equivalentemente:

$$
I = \frac{V}{R}
$$

La relación no debe aplicarse automáticamente a cualquier componente electrónico. OpenStax señala explícitamente que la relación lineal no es universal y distingue los materiales/componentes óhmicos de los no óhmicos.

---
### Potencia eléctrica

La relación general entre potencia eléctrica, tensión y corriente es:

$$
P = VI
$$

Para una resistencia que cumple la ley de Ohm pueden obtenerse además:

$$
P = I^2R
$$

y:

$$
P = \frac{V^2}{R}
$$

Estas dos últimas expresiones dependen de la relación resistiva $V=IR$ y no deben generalizarse indiscriminadamente a cualquier elemento de un circuito.

---
### Potencia instantánea y potencia media

En sistemas donde tensión y corriente varían con el tiempo:

$$
p(t) = v(t)i(t)
$$

La potencia media durante un intervalo puede expresarse como:

$$
P_{\mathrm{avg}} =
\frac{1}{T}
\int_0^T p(t)\,dt
$$

Esto es importante para distinguir una potencia instantánea, una potencia media y una potencia máxima o nominal.

---
### Energía eléctrica

La energía transferida durante un intervalo se relaciona con la potencia mediante:

$$
E = \int P(t)\,dt
$$

Si la potencia es constante:

$$
E = Pt
$$

En el caso de tensión y corriente constantes:

$$
E = VIt
$$

Por ello, **W y Wh no son la misma magnitud**:

- W → potencia.
- Wh → energía.

OpenStax relaciona explícitamente potencia con tasa de transferencia de energía y energía con la integración de potencia en el tiempo.

---
### Caídas de tensión

En un circuito real, cables, conectores, resistencias internas y otros elementos pueden producir caídas de tensión.

Para un elemento resistivo:

$$
V_{\mathrm{drop}} = IR
$$

Por tanto, la tensión disponible en una carga puede diferir de la tensión nominal de la fuente.

Esto es especialmente relevante en sistemas de alta corriente como baterías, ESC y motores.

---
### Circuitos reales

Un circuito real puede contener:

- resistencia;
- capacitancia;
- inductancia;
- fuentes;
- convertidores;
- motores;
- ESC;
- sensores;
- cargas electrónicas.

Por tanto, **$P=VI$ sigue siendo una relación fundamental de potencia eléctrica**, pero la interpretación de $V$ e $I$ debe corresponder al punto del circuito y al intervalo temporal que se está analizando.

---
### RF frente a alimentación DC

La potencia de una señal de radiofrecuencia y la potencia eléctrica consumida por el circuito que genera esa señal son magnitudes diferentes.

Por ejemplo:

```text
batería
   ↓
regulador
   ↓
electrónica VTX
   ├── potencia eléctrica consumida
   ↓
transmisor RF
   ↓
potencia RF emitida
```

La potencia RF especificada de un transmisor **no determina por sí sola** su consumo eléctrico desde la batería.

Para relacionarlas sería necesario conocer el circuito y su eficiencia:

$$
\eta =
\frac{P_{\mathrm{RF}}}{P_{\mathrm{DC}}}
$$

por lo que:

$$
P_{\mathrm{DC}} =
\frac{P_{\mathrm{RF}}}{\eta}
$$

si la definición de eficiencia y las condiciones de medida son las adecuadas.

Por tanto:

**potencia RF ≠ potencia DC de entrada**.

---
## [EJEMPLO] Corriente y circuitos
En Jarvis Continuity, cuando se declara una potencia o energía, debe quedar claro:

- qué elemento se está midiendo;
- dónde se mide;
- si es entrada o salida;
- si es instantánea, media, nominal o máxima;
- bajo qué condiciones;
- si procede de un datasheet, ensayo o modelo.

Ejemplo conceptual:

```text
batería
   ↓
P_battery
   ↓
ESC
   ↓
P_ESC
   ↓
motor
   ↓
P_mech
```

Estas potencias **no tienen por qué ser iguales** porque existen pérdidas y conversiones de energía.

En un sistema real:

$$
P_{\mathrm{out}} \leq P_{\mathrm{in}}
$$

cuando se consideran únicamente conversiones pasivas/activas con pérdidas y no existen otras fuentes de energía en el intervalo considerado.

Por ello, un dato de potencia de salida de un componente no autoriza a inferir automáticamente su consumo de entrada.

---
## [PROCEDIMIENTO] Corriente y circuitos
1. Identificar el circuito o subsistema.
2. Definir qué magnitud se necesita:
   - tensión;
   - corriente;
   - potencia;
   - energía.
3. Identificar dónde se mide o calcula la magnitud.
4. Declarar si la magnitud es:
   - instantánea;
   - media;
   - nominal;
   - máxima;
   - pico.
5. Identificar fuente, carga y elementos intermedios.
6. Aplicar la ley de Ohm únicamente cuando el modelo y el elemento sean compatibles con ella.
7. Para potencia eléctrica utilizar:

$$
P = VI
$$

8. Si se necesita energía, integrar potencia en el tiempo:

$$
E = \int P(t)\,dt
$$

9. Para componentes reales, incluir pérdidas y eficiencia cuando corresponda.
10. No convertir una especificación de catálogo en una corriente o potencia de operación sin condiciones que la respalden.

---
## [USO_PROBLEMAS] Corriente y circuitos
- análisis de circuitos;
- cálculo de corriente;
- cálculo de tensión;
- análisis de potencia;
- análisis de energía;
- dimensionado de cables;
- dimensionado de alimentación;
- selección de ESC;
- análisis de baterías;
- presupuesto energético;
- análisis de pérdidas;
- diseño de sistemas electrónicos.

---
## [APLICACIONES] Corriente y circuitos
**Jarvis craft/catalog:** proporciona el vocabulario físico necesario para distinguir tensión, corriente, potencia y energía y evitar inferencias no justificadas.

**Jarvis FS:** permite interpretar correctamente la cadena eléctrica:

```text
batería
   ↓
alimentación
   ↓
ESC
   ↓
motor
   ↓
carga
```

Sin embargo, esta nota **no proporciona valores físicos de ningún SKU**.

Los valores de:

- `power_w`;
- `current_a`;
- `voltage_v`;
- capacidad;
- eficiencia;

deben proceder de una fuente o de un modelo/ensayo explícitamente identificado.

---
## [CONEXIONES] Corriente y circuitos
Hojas del hub:

- [[Corriente eléctrica]]
- [[Voltaje]]
- [[Resistencia eléctrica]]
- [[Ley de Ohm]]
- [[Potencia eléctrica]]
- [[Energía eléctrica]]
- [[Circuitos eléctricos]]

Spine:

- [[C-rate de batería]]
- [[Batería]]
- [[Electrónica de potencia]]
- [[Motores]]
- [[Actuadores]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Potencia]]
- [[Energía]]

---
## [ERRORES] Corriente y circuitos
- Confundir corriente con potencia.
- Confundir potencia con energía.
- Confundir tensión nominal con tensión real bajo carga.
- Aplicar la ley de Ohm a cualquier dispositivo sin comprobar que el modelo sea válido.
- Tratar corriente máxima como corriente de operación.
- Tratar potencia nominal como potencia consumida.
- Inventar A/W de un componente sin fuente.
- Confundir potencia eléctrica de entrada con potencia mecánica de salida.
- Igualar potencia RF de un transmisor con potencia DC consumida por el transmisor.
- Confundir potencia instantánea, media, nominal y máxima.
- Ignorar las pérdidas de cables, convertidores, ESC u otros elementos cuando sean relevantes para el balance energético.
- Usar una cifra de catálogo fuera de las condiciones para las que fue especificada.

---
## [NOTAS] Corriente y circuitos
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Se precisa especialmente:

1. La corriente se define como tasa de flujo de carga:

$$
I = \frac{dQ}{dt}
$$

2. $P=VI$ no debe presentarse como una fórmula exclusiva de corriente continua ideal. Es una relación fundamental de potencia eléctrica; en señales variables debe utilizarse la potencia instantánea $p(t)=v(t)i(t)$ y, cuando corresponda, la potencia media.

3. Las expresiones $P=I^2R$ y $P=V^2/R$ requieren la relación resistiva correspondiente y no deben extenderse indiscriminadamente a cualquier componente.

4. La distinción **RF ≠ DC** es correcta: la potencia RF emitida no determina por sí sola la potencia eléctrica de entrada del transmisor.

Las relaciones fundamentales anteriores están respaldadas por OpenStax, que además señala explícitamente que la ley de Ohm no es universal.

---
## [REFERENCIAS] Corriente y circuitos
- OpenStax — *Physics*, Chapter 19: Electric Current, Resistance, and Ohm's Law:
  https://openstax.org/books/physics/pages/19-introduction
- OpenStax — *Physics*, §19.1 Ohm's Law (corriente como tasa de flujo de carga; $V=IR$; aplicabilidad):
  https://openstax.org/books/physics/pages/19-1-ohms-law
- OpenStax — *Physics*, §19.4 Electric Power ($P=VI$; $P=I^2R$; $P=V^2/R$ para resistencias):
  https://openstax.org/books/physics/pages/19-4-electric-power
- OpenStax — *College Physics*, §20.4 Electric Power and Energy:
  https://openstax.org/books/college-physics/pages/20-4-electric-power-and-energy
- OpenStax — *College Physics*, §20.2 Ohm's Law: Resistance and Simple Circuits (relación empírica; no todos los materiales son óhmicos):
  https://openstax.org/books/college-physics/pages/20-2-ohms-law-resistance-and-simple-circuits
- OpenStax — *University Physics Volume 2*, §9.3 Resistivity and Resistance (comportamiento óhmico / no óhmico; contexto de circuitos):
  https://openstax.org/books/university-physics-volume-2/pages/9-3-resistivity-and-resistance

---
## [ESTADO] Corriente y circuitos
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R1/R2 (Cursor)
- jarvis_lote: spine-lote-4
- estado: solid
