---
id: vectores
nombre: Vectores
area: Matemáticas
subarea: Álgebra lineal
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — OpenStax Calculus Vol. 3 §2.3–2.4; University Physics Vol. 1 §2.4; Algebra and Trigonometry 2e §10.8
tags: [spine, lote-1]
---

# Vectores

---
## [DEFINICION] Vectores
Un **vector** es un objeto matemático que, en un espacio euclídeo, se caracteriza por su **magnitud, dirección y sentido**. Un **escalar** es una cantidad que queda caracterizada por un único valor respecto a una unidad o escala. En física e ingeniería, magnitudes como desplazamiento, velocidad, aceleración y fuerza se representan mediante vectores.

En ℝ²/ℝ³, un vector puede representarse mediante sus componentes respecto a una base determinada. La representación por componentes depende del sistema de coordenadas utilizado.

---
## [INTUICION] Vectores
Piensa en una flecha: lo larga que es representa su **magnitud**, mientras que su orientación y sentido indican hacia dónde apunta. Sumar vectores no consiste necesariamente en sumar sus magnitudes: las componentes deben combinarse respetando sus direcciones.

El **producto escalar** produce un escalar y cuantifica la componente de un vector en la dirección del otro. El **producto vectorial**, definido en ℝ³, produce un vector perpendicular a los dos vectores de entrada; su magnitud depende de la componente perpendicular entre ellos y su sentido sigue la regla de la mano derecha.

---
## [FUNDAMENTO] Vectores
En ℝ²/ℝ³ un vector se representa mediante componentes respecto a una base, por ejemplo:

$$
\mathbf{v}=(v_x,v_y,v_z)
$$

La lista de componentes es una **representación del vector respecto a una base concreta**; cambiar de base puede cambiar sus componentes sin cambiar el vector físico representado.

Operaciones básicas:

- suma
- resta
- producto por escalar
- norma $\|\mathbf v\|$
- producto escalar $\mathbf a\cdot\mathbf b$
- producto vectorial $\mathbf a\times\mathbf b$ en ℝ³

La norma euclídea puede expresarse como:

$$
\|\mathbf v\|=\sqrt{\mathbf v\cdot\mathbf v}
$$

Para dos vectores:

$$
\mathbf a\cdot\mathbf b
=
\|\mathbf a\|\|\mathbf b\|\cos\theta
$$

y, en componentes cartesianas:

$$
\mathbf a\cdot\mathbf b
=
a_xb_x+a_yb_y+a_zb_z
$$

Para el producto vectorial:

$$
\|\mathbf a\times\mathbf b\|
=
\|\mathbf a\|\|\mathbf b\|\sin\theta
$$

y $\mathbf a\times\mathbf b$ es perpendicular a ambos vectores.

En aplicaciones de ingeniería, un vector puede expresarse en distintos marcos de referencia. Por ejemplo, un vector expresado en el marco inercial y el mismo vector expresado en el marco cuerpo pueden tener componentes diferentes. La transformación entre representaciones debe realizarse mediante la transformación geométrica apropiada, como una matriz de rotación o una representación equivalente de actitud.

---
## [EJEMPLO] Vectores
La velocidad angular del vehículo puede representarse como un vector expresado en ejes cuerpo:

$$
\boldsymbol{\omega}
=
(\omega_x,\omega_y,\omega_z)
$$

Las componentes $\omega_x,\omega_y,\omega_z$ representan la velocidad angular respecto a los ejes definidos por el marco cuerpo.

Un error de actitud puede representarse, según la formulación del sistema de control, mediante diferentes representaciones, entre ellas ángulos de Euler, un vector de rotación o un cuaternión de error. No existe un único escalar que represente en general una actitud tridimensional completa.

---
## [PROCEDIMIENTO] Vectores
1. Elegir y declarar el **marco de referencia** en el que están expresados los vectores.
2. Expresar la magnitud de interés mediante sus componentes respecto a ese marco.
3. Operar con los vectores respetando sus componentes y la operación matemática correspondiente.
4. No comparar ni combinar directamente componentes expresadas en marcos diferentes sin aplicar previamente la transformación entre marcos.
5. Si se cambia de marco, utilizar la transformación de coordenadas apropiada, por ejemplo una matriz de rotación o una representación equivalente mediante cuaterniones.
6. Verificar que las magnitudes comparadas representan el mismo tipo de cantidad física y utilizan unidades compatibles.

---
## [USO_PROBLEMAS] Vectores
Los vectores se utilizan como representación matemática de magnitudes con comportamiento direccional en:

- estática y dinámica: fuerzas y momentos;
- cinemática: posición, desplazamiento, velocidad y aceleración;
- robótica: posiciones, orientaciones, velocidades y transformaciones entre marcos;
- control de actitud: velocidad angular y representación del error de orientación;
- navegación y estimación de estado: magnitudes expresadas en diferentes marcos de referencia.

---
## [APLICACIONES] Vectores
**Jarvis:** lenguaje matemático base para explicar el ladder FS:

- IMU: aceleración y velocidad angular;
- attitude (C7): orientación y transformaciones entre marcos;
- PD por ejes (C8): magnitudes y errores expresados en ejes definidos;
- planta 6-DoF (C36): posición, velocidad, aceleración, fuerzas y momentos.

La nota no define valores concretos de masas, ganancias, potencia, empuje ni otros parámetros de componentes.

---
## [CONEXIONES] Vectores
Hojas del hub:

- [[Vector]]
- [[Magnitud]]
- [[Dirección]]
- [[Suma de vectores]]
- [[Producto escalar]]
- [[Producto vectorial]]

Spine:

- [[Espacios vectoriales]]
- [[Dinámica]]
- [[Momento y rotación]]
- [[Control clásico]]
- [[Cinemática y dinámica]]
- [[Marcos de referencia]]
- [[Rotaciones]]
- [[Cuaterniones]]

---
## [ERRORES] Vectores
- Sumar o comparar componentes de vectores expresados en marcos distintos sin realizar previamente la transformación correspondiente.
- Confundir un vector físico con sus componentes respecto a una base concreta.
- Tratar los tres valores de un conjunto de ángulos de Euler como si fueran, en general, las componentes de un vector libre de rotación.
- Ignorar que las representaciones mediante ángulos de Euler dependen de la convención/secuencia de rotación y pueden presentar singularidades.
- Confundir el producto escalar con el producto vectorial.
- Interpretar el producto vectorial simplemente como "un eje de giro": el resultado matemático es un vector perpendicular a los vectores de entrada; puede utilizarse para representar magnitudes relacionadas con rotaciones, como el momento.
- Usar un número de ejemplo de esta nota como si fuera un dato de `library/` o un gain de `flight_software/`.

---
## [NOTAS] Vectores
Nodo revisado contra referencias académicas y técnicas (Engineer + contraste externo).

La representación de un vector mediante componentes depende de la base/marco elegido. Esta distinción es especialmente importante para Jarvis, donde una misma magnitud física puede expresarse en marcos cuerpo e inercial.

Las fórmulas de norma, producto escalar y producto vectorial incluidas en esta nota corresponden a las definiciones estándar para espacios euclídeos y ℝ³.

La representación de actitud y el uso de velocidad angular en marcos cuerpo requieren convenciones explícitas de marcos y transformaciones.

---
## [REFERENCIAS] Vectores
- OpenStax — *Algebra and Trigonometry 2e*, §10.8, "Vectors":
  https://openstax.org/books/algebra-and-trigonometry-2e/pages/10-8-vectors
- OpenStax — *Calculus Volume 3*, §2.3, "The Dot Product":
  https://openstax.org/books/calculus-volume-3/pages/2-3-the-dot-product
- OpenStax — *Calculus Volume 3*, §2.4, "The Cross Product":
  https://openstax.org/books/calculus-volume-3/pages/2-4-the-cross-product
- OpenStax — *University Physics Volume 1*, §2.4, "Products of Vectors":
  https://openstax.org/books/university-physics-volume-1/pages/2-4-products-of-vectors
- NASA Technical Reports Server — *2001 Flight Mechanics Symposium* proceedings (attitude determination / prediction / control papers; multi-paper compilation, not a single quaternion-focused monograph):
  https://ntrs.nasa.gov/api/citations/20010084958/downloads/20010084958.pdf

---
## [ESTADO] Vectores
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R1 (Cursor)
- jarvis_lote: spine-lote-1
- estado: solid
