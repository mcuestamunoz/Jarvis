---
id: momento-y-rotacion
nombre: Momento y rotación
area: Física
subarea: Mecánica
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — OpenStax University Physics Vol. 1 §10.6–10.7, §12.1; MIT OCW 8.09 Ch.2 §2.4
tags: [spine, lote-2]
---

# Momento y rotación

---
## [DEFINICION] Momento y rotación
El **momento de una fuerza** (torque) cuantifica la tendencia de una fuerza a producir rotación respecto a un punto o eje. Como vector, respecto a un punto de referencia $O$:

$$
\boldsymbol{\tau}
=
\mathbf r\times\mathbf F
$$

donde $\mathbf r$ es el vector desde $O$ hasta el punto de aplicación de la fuerza.

Su magnitud es:

$$
\|\boldsymbol{\tau}\|
=
rF\sin\theta
=
r_\perp F
$$

donde $r_\perp$ es el brazo de palanca perpendicular a la línea de acción de la fuerza.

La **dinámica rotacional** estudia cómo los momentos externos modifican el movimiento rotacional de un cuerpo. Para un cuerpo rígido, intervienen su momento de inercia o, en el caso general tridimensional, su tensor de inercia y su velocidad angular.

---
## [INTUICION] Momento y rotación
Aplicar una fuerza más lejos del eje de rotación puede producir un mayor efecto rotacional: para una fuerza dada,

$$
\|\boldsymbol{\tau}\|=r_\perp F
$$

En un multicóptero, las fuerzas de empuje aplicadas a cierta distancia del centro de masa pueden generar momentos de **roll** y **pitch**. Los efectos asociados a las fuerzas y pares producidos por los rotores también pueden contribuir al **yaw**, según la configuración y el modelo físico utilizado.

El cuerpo responde a los momentos netos según sus propiedades inerciales. La traslación y la rotación forman conjuntamente la dinámica 6-DoF, pero representan grados de libertad y ecuaciones de movimiento diferentes.

---
## [FUNDAMENTO] Momento y rotación
### Momento de una fuerza

$$
\boldsymbol{\tau}
=
\mathbf r\times\mathbf F
$$

con:

$$
\|\boldsymbol{\tau}\|
=
rF\sin\theta
=
r_\perp F
$$

El vector torque es perpendicular al plano formado por $\mathbf r$ y $\mathbf F$, con sentido determinado por la regla de la mano derecha.

### Rotación alrededor de un eje fijo

Para un cuerpo rígido que rota alrededor de un eje fijo:

$$
\sum \tau
=
I\alpha
$$

donde $I$ es el momento de inercia respecto al eje de rotación y $\alpha$ la aceleración angular. Esta ecuación requiere las hipótesis correspondientes al movimiento alrededor de un eje fijo; no debe utilizarse como ecuación general de cualquier movimiento rotacional tridimensional.

### Dinámica rotacional tridimensional

Para un cuerpo rígido en 3D, la relación general se formula mediante el momento angular y el tensor de inercia. En un marco cuerpo alineado con los ejes principales, las ecuaciones de Euler pueden escribirse como:

$$
I_1\dot{\omega}_1-(I_2-I_3)\omega_2\omega_3=\tau_1
$$

$$
I_2\dot{\omega}_2-(I_3-I_1)\omega_3\omega_1=\tau_2
$$

$$
I_3\dot{\omega}_3-(I_1-I_2)\omega_1\omega_2=\tau_3
$$

De forma compacta:

$$
\boldsymbol{\tau}
=
\mathbf I\dot{\boldsymbol{\omega}}
+
\boldsymbol{\omega}\times
(\mathbf I\boldsymbol{\omega})
$$

cuando $\mathbf I$ y las magnitudes están expresadas de acuerdo con la convención de marco correspondiente.

El **momento lineal**:

$$
\mathbf p=m\mathbf v
$$

es una magnitud distinta del **momento de una fuerza (torque)**:

$$
\boldsymbol{\tau}
=
\mathbf r\times\mathbf F
$$

aunque ambos pertenecen a la formulación de la dinámica y tienen leyes de evolución/conservación relacionadas con las simetrías del sistema.

---
## [EJEMPLO] Momento y rotación
En un multicóptero, el sistema de control puede producir comandos asociados a fuerzas y momentos deseados. El **mixer/control allocation** transforma esos comandos en acciones individuales sobre los actuadores según la geometría y el modelo del vehículo.

La planta dinámica utiliza las fuerzas y momentos resultantes, junto con otras cargas modeladas, para calcular la evolución de la velocidad lineal y angular y, posteriormente, de la actitud.

El `step()` del controlador **no es la ecuación de Euler**: el controlador calcula acciones de control; la planta representa la respuesta dinámica del vehículo a esas acciones.

---
## [PROCEDIMIENTO] Momento y rotación
1. Declarar el **punto o eje de referencia** respecto al cual se calcula el momento.
2. Declarar el **marco de referencia** en el que están expresados las posiciones, fuerzas y momentos.
3. Inventariar las fuerzas externas y sus puntos o líneas de aplicación.
4. Calcular los momentos correspondientes:

$$
\boldsymbol{\tau}_i
=
\mathbf r_i\times\mathbf F_i
$$

5. Obtener el momento neto:

$$
\boldsymbol{\tau}_{net}
=
\sum_i\boldsymbol{\tau}_i
$$

6. Elegir el modelo rotacional apropiado: eje fijo o dinámica tridimensional de cuerpo rígido.
7. Utilizar el momento de inercia o tensor de inercia correspondiente al cuerpo y al eje/marco utilizado.
8. Integrar las ecuaciones de movimiento para una simulación o imponer las condiciones de equilibrio cuando el problema sea estático.
9. Comprobar unidades, signos, marcos y coherencia física de los resultados.

---
## [USO_PROBLEMAS] Momento y rotación
- Estática y equilibrio de momentos.
- Dinámica rotacional.
- Cálculo del efecto de fuerzas aplicadas a distintas distancias.
- Dimensionado y análisis de actuadores.
- Determinación de aceleraciones angulares.
- Interpretación de comandos de roll/pitch/yaw.
- Modelado de cuerpos rígidos 3D.
- Simulación de vehículos y robots.

---
## [APLICACIONES] Momento y rotación
**Jarvis:** puente conceptual entre [[Dinámica]], el sistema de propulsión/mixer y la planta 6-DoF.

En un multicóptero, las fuerzas y pares generados por los actuadores producen fuerzas y momentos sobre el cuerpo. La geometría del vehículo y la distribución de los actuadores determinan cómo esas acciones contribuyen a los grados de libertad de traslación y rotación.

Esta nota no proporciona valores concretos de:

- $I_{xx},I_{yy},I_{zz}$;
- tensor de inercia;
- thrust de un SKU;
- brazos de motor;
- torque de motor;
- ganancias del controlador.

Esos valores requieren datos respaldados por las fuentes correspondientes.

---
## [CONEXIONES] Momento y rotación
Hojas del hub:

- [[Momento lineal]]
- [[Conservación del momento]]
- [[Torque]]
- [[Momento de inercia]]
- [[Movimiento rotacional]]
- [[Momento angular]]

Spine:

- [[Vectores]]
- [[Dinámica]]
- [[Control clásico]]
- [[Dinámica robótica]]
- [[Actuadores]]
- [[Marcos de referencia]]
- [[6-DoF]]

---
## [ERRORES] Momento y rotación
- Usar $\tau=I\alpha$ como ecuación general de cualquier movimiento rotacional tridimensional sin comprobar sus hipótesis.
- Confundir el torque respecto a un punto/eje con una fuerza.
- No declarar el punto o eje respecto al cual se calcula el momento.
- Utilizar una distancia $r$ que no corresponde al brazo de palanca perpendicular cuando se calcula la magnitud mediante $rF$.
- Mezclar fuerzas, posiciones o momentos expresados en marcos diferentes sin realizar la transformación correspondiente.
- Tomar un $I$ de un ejemplo académico como momento de inercia del craft real.
- Confundir momento lineal $\mathbf p$ con momento de una fuerza $\boldsymbol{\tau}$.
- Ignorar el tensor de inercia y los términos de acoplamiento en dinámica rotacional 3D.
- Tratar comandos de momento generados por el controlador como si estuvieran validados experimentalmente.
- Confundir la salida del controlador con la respuesta física de la planta.

---
## [NOTAS] Momento y rotación
Nodo revisado mediante contraste con referencias académicas (Engineer + contraste externo).

La definición vectorial:

$$
\boldsymbol{\tau}
=
\mathbf r\times\mathbf F
$$

y la magnitud:

$$
\|\boldsymbol{\tau}\|
=
r_\perp F
$$

están respaldadas por OpenStax.

La relación:

$$
\sum\tau=I\alpha
$$

es válida para la dinámica rotacional alrededor de un eje fijo bajo las hipótesis correspondientes. No debe generalizarse sin más a un cuerpo rígido libre en 3D.

Para dinámica rotacional 3D, las ecuaciones de Euler incorporan el tensor de inercia y los términos de acoplamiento entre velocidad angular y momento angular.

El torque depende del punto/eje de referencia utilizado. Por tanto, una afirmación sobre un momento debe declarar respecto a qué punto o eje se calcula.

---
## [REFERENCIAS] Momento y rotación
- OpenStax — *University Physics Volume 1*, §10.6, "Torque":
  https://openstax.org/books/university-physics-volume-1/pages/10-6-torque
- OpenStax — *University Physics Volume 1*, §10.7, "Newton's Second Law for Rotation":
  https://openstax.org/books/university-physics-volume-1/pages/10-7-newtons-second-law-for-rotation
- OpenStax — *University Physics Volume 1*, Chapter 10, "Key Equations":
  https://openstax.org/books/university-physics-volume-1/pages/10-key-equations
- OpenStax — *University Physics Volume 1*, §12.1, "Conditions for Static Equilibrium":
  https://openstax.org/books/university-physics-volume-1/pages/12-1-conditions-for-static-equilibrium
- MIT OpenCourseWare — *Classical Mechanics III, Chapter 2: Rigid Body Dynamics*, §2.4 "Euler Equations":
  https://ocw.mit.edu/courses/8-09-classical-mechanics-iii-fall-2014/6fe39e8d5ce4ce746ca256dfea665eda_MIT8_09F14_Chapter_2.pdf

---
## [ESTADO] Momento y rotación
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · math `$`/`$$`
- jarvis_lote: spine-lote-2
- estado: solid
