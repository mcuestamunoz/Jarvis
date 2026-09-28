---
id: dinamica
nombre: Dinámica
area: Física
subarea: Mecánica
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — OpenStax University Physics Vol. 1 §5.3, §10.7; MIT 2.003J Rigid Body Dynamics; NASA Murman 6-DOF
tags: [spine, lote-1]
---

# Dinámica

---
## [DEFINICION] Dinámica
La **dinámica** estudia la relación entre las **fuerzas y momentos externos** y el **movimiento** de los cuerpos, es decir, cómo las interacciones modifican su estado de movimiento.

Para un cuerpo rígido, la dinámica combina el movimiento de traslación de su centro de masa con el movimiento de rotación. Se apoya en la cinemática para describir el movimiento y en las ecuaciones de Newton–Euler para relacionar fuerzas y momentos con aceleraciones lineales y angulares.

---
## [INTUICION] Dinámica
La **cinemática** describe cómo se mueve un sistema; la **dinámica** relaciona ese movimiento con las causas físicas que lo producen, principalmente fuerzas y momentos.

En un multicóptero, las fuerzas de empuje, el peso y otras fuerzas externas producen aceleración lineal. Las diferencias de empuje entre motores y los momentos aerodinámicos o de reacción producen aceleración angular. La planta dinámica representa estas relaciones físicas y permite obtener la evolución temporal del estado del vehículo.

---
## [FUNDAMENTO] Dinámica
Ideas centrales:

- **Segunda ley de Newton:**

$$
\sum \mathbf F_{\mathrm{ext}}
=
\frac{d\mathbf p}{dt}
$$

donde $\mathbf p=m\mathbf v$ es el momento lineal.

Para masa constante:

$$
\sum \mathbf F_{\mathrm{ext}}
=
m\mathbf a
$$

Esta forma se aplica al movimiento traslacional y, expresada para el centro de masa de un sistema, relaciona la fuerza externa neta con la aceleración del centro de masa.

- **Dinámica rotacional:**

Para rotación alrededor de un eje fijo:

$$
\sum \tau = I\alpha
$$

donde $I$ es el momento de inercia respecto al eje y $\alpha$ la aceleración angular.

Para un cuerpo rígido con movimiento rotacional tridimensional, la formulación general requiere el **tensor de inercia** y las ecuaciones de Euler. En un marco cuerpo apropiado, una forma de la ecuación es:

$$
\boldsymbol{\tau}
=
\mathbf I\dot{\boldsymbol{\omega}}
+
\boldsymbol{\omega}
\times
(\mathbf I\boldsymbol{\omega})
$$

donde $\mathbf I$ es el tensor de inercia y $\boldsymbol{\omega}$ la velocidad angular.

- **Diagrama de cuerpo libre:** identificar y representar las fuerzas y momentos externos relevantes antes de formular las ecuaciones de movimiento.

Ejemplo matemático:

$$
\mathbf a
=
\frac{\sum\mathbf F_{\mathrm{ext}}}{m}
$$

Esta expresión solo puede utilizarse cuando la masa del sistema es conocida y constante y se ha definido correctamente el sistema de referencia y las fuerzas externas.

La masa física de un componente concreto no debe obtenerse de esta nota; un valor de `mass_g` de un vehículo o SKU pertenece a la fuente de datos correspondiente.

---
## [EJEMPLO] Dinámica
En una simulación 6-DoF de un multicóptero, las fuerzas y momentos producidos por el sistema de propulsión, junto con la gravedad y otras fuerzas/momentos modelados, entran en las ecuaciones de movimiento.

La dinámica de traslación determina la aceleración del centro de masa a partir de las fuerzas externas.

La dinámica rotacional determina la aceleración angular a partir de los momentos externos y de las propiedades inerciales del cuerpo.

La **planta dinámica no es el `step()` del controlador**: el controlador calcula acciones de control a partir del estado y de sus objetivos; la planta representa la respuesta física del sistema a esas acciones.

---
## [PROCEDIMIENTO] Dinámica
1. Definir el sistema físico y su estado.
2. Elegir y declarar los marcos de referencia utilizados.
3. Identificar las fuerzas y momentos externos relevantes.
4. Dibujar o construir el diagrama de cuerpo libre cuando sea necesario.
5. Separar las ecuaciones de traslación y rotación.
6. Formular las ecuaciones de movimiento utilizando Newton–Euler u otra formulación dinámica apropiada.
7. Incorporar las propiedades físicas necesarias, como masa y tensor de inercia, utilizando valores respaldados por una fuente.
8. Integrar las ecuaciones en el tiempo para una simulación dinámica o resolverlas bajo las condiciones apropiadas para estudiar un estado de equilibrio.
9. Comprobar unidades, marcos de referencia, signos y coherencia física del resultado.

---
## [USO_PROBLEMAS] Dinámica
La dinámica se utiliza en problemas como:

- determinar la aceleración producida por una fuerza neta;
- determinar las fuerzas necesarias para obtener una aceleración o trayectoria determinada;
- determinar aceleraciones angulares producidas por momentos;
- estudiar el movimiento de cuerpos rígidos;
- simular sistemas mecánicos y vehículos;
- formular modelos de planta para sistemas de control;
- determinar la respuesta de un sistema físico ante fuerzas y momentos conocidos.

---
## [APLICACIONES] Dinámica
**Jarvis:** fundamento conceptual de la planta 6-DoF (C36) y de la separación entre **controlador** y **planta física**.

En un multicóptero:

- los actuadores generan fuerzas y momentos;
- el modelo dinámico transforma esas acciones y otras fuerzas externas en aceleraciones;
- la integración temporal de las aceleraciones produce la evolución del estado;
- el controlador utiliza el estado para calcular nuevas acciones de control.

La dinámica explica el papel físico de la masa, el tensor de inercia, las fuerzas y los momentos. No proporciona por sí misma valores concretos de componentes ni parámetros de catálogo.

---
## [CONEXIONES] Dinámica
Hojas del hub:

- [[Fuerza]]
- [[Masa]]
- [[Segunda ley de Newton]]
- [[Equilibrio]]
- [[Fuerzas de contacto]]
- [[Fuerzas a distancia]]
- [[Diagrama de cuerpo libre]]
- [[Momento]]
- [[Momento de inercia]]

Spine:

- [[Cinemática]]
- [[Vectores]]
- [[Momento y rotación]]
- [[Trabajo y energía]]
- [[Control clásico]]
- [[Dinámica robótica]]
- [[Marcos de referencia]]
- [[Planta dinámica]]
- [[6-DoF]]

---
## [ERRORES] Dinámica
- Confundir la **planta física/dinámica** con el `step()` o la ley de control del controlador.
- Confundir fuerza neta con una fuerza individual.
- Usar $F=ma$ sin considerar que la formulación general de la segunda ley es $\mathbf F=d\mathbf p/dt$.
- Aplicar $F=ma$ a un sistema de masa variable sin considerar la formulación apropiada.
- Usar $\tau=I\alpha$ como ecuación general de cualquier movimiento rotacional tridimensional sin comprobar sus hipótesis; para un cuerpo rígido general se requiere la formulación con tensor de inercia y términos giroscópicos.
- Olvidar que en dinámica rotacional tridimensional importa el tensor de inercia y el marco en el que se expresan $\boldsymbol{\omega}$, $\boldsymbol{\tau}$ e $\mathbf I$.
- Mezclar fuerzas o momentos expresados en marcos diferentes sin realizar la transformación correspondiente.
- Tomar un `m` de ejemplo de apuntes como masa del craft real.
- Inventar masa, momento de inercia, empuje u otros parámetros físicos que no estén respaldados por una fuente.

---
## [NOTAS] Dinámica
Nodo revisado mediante contraste con referencias académicas y técnicas (Engineer + contraste externo).

La forma $F=ma$ es una forma particular de la segunda ley de Newton para masa constante. La formulación más general para traslación es:

$$
\mathbf F_{\mathrm{net}}
=
\frac{d\mathbf p}{dt}
$$

La ecuación:

$$
\sum\tau=I\alpha
$$

es válida para la formulación de rotación alrededor de un eje fijo bajo las hipótesis correspondientes. Para la dinámica general de un cuerpo rígido en 3D debe utilizarse la formulación Newton–Euler con tensor de inercia y términos de acoplamiento rotacional.

La NASA describe explícitamente la simulación 6-DoF de un cuerpo rígido como la resolución de las ecuaciones de Newton–Euler, separando la traslación del centro de masa y la rotación respecto a un sistema de ejes ligado al cuerpo.

---
## [REFERENCIAS] Dinámica
- OpenStax — *University Physics Volume 1*, §5.3, "Newton's Second Law":
  https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law
- OpenStax — *University Physics Volume 1*, §10.7, "Newton's Second Law for Rotation":
  https://openstax.org/books/university-physics-volume-1/pages/10-7-newtons-second-law-for-rotation
- OpenStax — *University Physics Volume 1*, Chapter 10, "Key Equations":
  https://openstax.org/books/university-physics-volume-1/pages/10-key-equations
- MIT — *2.003J Dynamics and Control I — Rigid Body Dynamics*:
  https://jasonku.mit.edu/pdf/2011sp-dynamics_notes.pdf
- NASA — *Simulations of 6-DOF Motion with a Cartesian Method*:
  https://www.nas.nasa.gov/assets/nas/pdf/staff/Murman_S_AIAA2003-1246.pdf

---
## [ESTADO] Dinámica
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-1
- estado: solid
