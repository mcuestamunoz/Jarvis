---
id: punto-de-operacion-vs-capacidad-intrinseca
nombre: Punto de operación vs capacidad intrínseca
area: Ingeniería
subarea: Electrónica / propulsión
nivel: intermedio
estado: solid
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — maxon Motor Constants ($k_n$, $k_M$); maxon Motor Data and Simulation; maxon technical PDF
tags: [spine, lote-4]
---

# Punto de operación vs capacidad intrínseca

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Punto de operación vs capacidad intrínseca
Un **punto de operación (OP)** describe el estado concreto en el que un sistema o conjunto está funcionando, definido por las variables relevantes de ese sistema. En un sistema de propulsión eléctrica pueden incluirse, según el modelo, tensión, corriente, velocidad de giro, par, hélice, carga y condiciones ambientales.

Una **especificación o característica intrínseca del componente** describe propiedades o límites propios del componente bajo las condiciones declaradas por el fabricante, como la constante de velocidad $k_n$, la constante de par $k_M$, la corriente continua admisible o determinados límites térmicos.

Por tanto:

**un dato de rendimiento obtenido para un conjunto motor + hélice + alimentación bajo unas condiciones concretas no debe tratarse automáticamente como una propiedad intrínseca del motor aislado.**

Las constantes del motor describen relaciones propias del motor, mientras que el punto de funcionamiento depende también de la carga y de las condiciones de operación. Por ejemplo, maxon define la constante de velocidad en relación con la velocidad y la tensión inducida, y la constante de par en relación con el par y la corriente.

---
## [INTUICION] Punto de operación vs capacidad intrínseca
“Este motor produce `X gf`” es una afirmación incompleta si no se conoce **en qué condiciones se obtuvo ese empuje**.

En una propulsión con hélice, el motor proporciona par y velocidad; la hélice transforma esa operación mecánica en empuje y potencia aerodinámica. El punto resultante depende del conjunto y de sus condiciones de funcionamiento.

Por ello, un valor de thrust obtenido en banco para un determinado motor, hélice, tensión y régimen de funcionamiento debe conservar esas condiciones cuando se almacena o utiliza en Jarvis.

Una constante como $k_n$ tampoco equivale directamente a thrust. maxon define $k_n$ como la relación entre velocidad y tensión inducida y $k_M$ como la relación entre par y corriente.

---
## [FUNDAMENTO] Punto de operación vs capacidad intrínseca
### Especificación / característica del componente

Puede incluir:

- masa del componente;
- constante de velocidad $k_n$;
- constante de par $k_M$;
- resistencia eléctrica;
- corriente continua o límite térmico especificado;
- tensión nominal;
- velocidad nominal;
- otros límites o características definidos por el fabricante.

Estos datos deben conservar sus **condiciones de especificación**. Por ejemplo, los datos de catálogo de un motor pueden distinguir velocidad sin carga, velocidad nominal, par nominal, corriente nominal y corriente de bloqueo.

### Punto de operación

Un OP representa una condición concreta de funcionamiento, por ejemplo:

- tensión aplicada;
- corriente;
- velocidad de giro;
- par;
- hélice;
- carga;
- empuje;
- potencia;
- temperatura;
- condiciones ambientales.

En un sistema motor + hélice, el thrust es una **salida del conjunto bajo unas condiciones determinadas**, no una propiedad que pueda atribuirse al motor únicamente sin especificar el sistema y las condiciones.

### Relación entre ambos

Las características del motor ayudan a determinar qué puntos de operación son posibles, pero **no determinan por sí solas el rendimiento completo del sistema motor + hélice + aire**.

Por ejemplo, la constante de velocidad $k_n$ puede utilizarse para relacionar velocidad y tensión inducida:

$$
k_n = \frac{n}{U_{\mathrm{ind}}}
$$

y la constante de par relaciona par y corriente:

$$
k_M = \frac{M}{I}
$$

Estas relaciones describen características del motor; no son una ecuación de thrust de una hélice.

---
## [EJEMPLO] Punto de operación vs capacidad intrínseca
Supongamos un ensayo de banco de un conjunto:

- motor determinado;
- hélice determinada;
- batería a una tensión determinada;
- ESC determinado;
- régimen de giro determinado;
- condiciones ambientales determinadas.

El ensayo puede producir un valor de thrust y corriente.

Ese resultado puede registrarse como:

**OP verificado → motor + hélice + condiciones → thrust/corriente/RPM medidos.**

No debe transformarse en:

**“este motor tiene X gf de thrust”**

sin conservar las condiciones que dieron lugar al dato.

Del mismo modo, un valor de $k_n$ procedente del fabricante puede almacenarse como característica del motor, pero no debe convertirse directamente en un valor de thrust.

---
## [PROCEDIMIENTO] Punto de operación vs capacidad intrínseca
1. Identificar si el dato procede de una **especificación del componente** o de una **condición de operación/ensayo**.
2. Para un OP, registrar las variables necesarias para reproducir o interpretar el resultado.
3. Declarar motor, hélice, alimentación, RPM y demás condiciones relevantes cuando estén disponibles.
4. Mantener separadas las características del motor de las prestaciones del conjunto.
5. Citar la fuente original o registrar el ensayo que produjo el dato.
6. Marcar como estimado cualquier OP calculado que no proceda de una medición.
7. No completar una curva de rendimiento mediante interpolaciones o valores inventados cuando faltan datos.
8. No utilizar un único OP como si representara toda la capacidad del sistema.

---
## [USO_PROBLEMAS] Punto de operación vs capacidad intrínseca
Selección y emparejamiento motor-hélice, análisis de bancos de ensayo, construcción de curvas de rendimiento, validación de modelos de propulsión y control de calidad de datos de catálogo.

---
## [APLICACIONES] Punto de operación vs capacidad intrínseca
**Jarvis catalog/craft:** establece una separación entre propiedades del componente y prestaciones observadas o estimadas de un conjunto.

**Jarvis physics:** permite que un thrust procedente de un OP se utilice únicamente bajo las condiciones que respaldan ese dato.

**Jarvis honesty:** la ausencia de una curva o de un ensayo no debe resolverse inventando puntos intermedios.

---
## [CONEXIONES] Punto de operación vs capacidad intrínseca
- [[Motores]]
- [[Motor DC]]
- [[Corriente y circuitos]]
- [[C-rate de batería]]
- [[Electrónica de potencia]]
- [[Hélices]]
- [[Empuje]]
- [[Punto de operación]]
- [[Curva de rendimiento]]

---
## [ERRORES] Punto de operación vs capacidad intrínseca
- Publicar thrust sin indicar las condiciones bajo las que se obtuvo.
- Tratar un valor de thrust de un conjunto motor-hélice como propiedad del motor aislado.
- Tratar $k_n$ / Kv como si fuera thrust.
- Utilizar una especificación nominal como si fuera un punto de operación medido.
- Inventar una curva de thrust a partir de un único punto.
- Mezclar resultados de distintos motores, hélices, tensiones o condiciones sin declararlo.
- Utilizar una estimación como si fuera una medición.
- Confundir una característica del motor con el rendimiento del sistema completo.

---
## [NOTAS] Punto de operación vs capacidad intrínseca
Nodo revisado mediante contraste externo (Engineer + GPT cite).

La distinción conceptual es válida, pero se ha corregido la formulación de **“capacidad intrínseca”**: no es una categoría física formal única ni todo dato de catálogo es estrictamente “intrínseco”. Es más preciso hablar de **característica/especificación del componente bajo condiciones declaradas** frente a **punto de operación del sistema**.

También se evita afirmar que un OP requiere necesariamente todas las variables enumeradas; las variables necesarias dependen de qué magnitud se esté caracterizando y del modelo/ensayo.

---
## [REFERENCIAS] Punto de operación vs capacidad intrínseca
- maxon — Motor Constants ($k_n$, $k_M$; velocidad, tensión inducida, par, corriente):
  https://support.maxongroup.com/hc/en-us/articles/360005873794-Motor-constants
- maxon — Motor Data and Simulation (datos de catálogo; velocidad/par; corriente; comportamiento):
  https://support.maxongroup.com/hc/en-us/articles/360013761160-Motor-data-and-simulation
- maxon — Motor Constants, technical reference PDF (relaciones $k_n$, $k_M$):
  https://www.maxongroup.com/assets/public/caas/v1/media/219142/data/4cbfb8e3f8b30686be19b6672f127c4a/maxon-knowlege-support-academy-pdf-en-download.pdf

---
## [ESTADO] Punto de operación vs capacidad intrínseca
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-4
- estado: solid
