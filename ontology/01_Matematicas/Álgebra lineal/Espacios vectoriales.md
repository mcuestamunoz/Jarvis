---
title: "Álgebra Lineal"
date: 2026-03-21
estado: "Nuevo"
---

> [!ABSTRACT]
> **Conceptos Fundamentales del Álgebra Lineal**
> Explicación detallada de los conceptos de Espacios Vectoriales, Bases, Dimensión y Transformaciones Lineales. Todo lo que necesitas saber sobre la estructura algebraica y las operaciones en espacios vectoriales.

---

## 1. Espacio Vectorial ([[Espacio vectorial]])

### Definición:
Un **espacio vectorial** es un conjunto de elementos llamados **vectores** que cumple con las siguientes propiedades:
- **Cerradura**: La suma de dos vectores es un vector.
- **Asociatividad**: (u + v) + w = u + (v + w)
- **Elemento neutro**: Existe un vector 0 tal que v + 0 = v
- **Elemento opuesto**: Existe un vector -v tal que v + (-v) = 0
- **Conmutatividad**: u + v = v + u
- **Cerradura bajo producto por escalar**: El producto de un escalar por un vector es un vector.
- **Distribución**: a(u + v) = au + av
- **Leyes de distribución escalares**: (a + b)v = av + bv

### Notación:
Un espacio vectorial se denota como $V$ sobre un **cuerpo** $\mathbb{K}$ (generalmente $\mathbb{R}$ o $\mathbb{C}$).

### Ejemplo:
El conjunto $\mathbb{R}^n$ con las operaciones estándar es un espacio vectorial.

---

## 2. Base ([[Base]])

### Definición:
Una **base** de un espacio vectorial $V$ es un conjunto $\mathcal{B} = \{v_1, v_2, \dots, v_n\}$ que cumple:
1. **Independencia lineal**: Ningún vector de la base puede expresarse como combinación lineal de los demás.
2. **Generación**: Cualquier vector de $V$ puede expresarse como combinación lineal de los vectores de la base.

### Dimensión:
La **dimensión** de $V$ es el número de vectores que componen su base, denotado como $\dim V$.

### Teorema:
Si $V$ es un espacio vectorial de dimensión $n$, entonces:
- Cualquier conjunto de $n+1$ vectores es linealmente dependiente.
- Cualquier conjunto de $n$ vectores linealmente independientes es una base.

### Ejemplo:
En $\mathbb{R}^2$, la base canónica es $\{(1,0), (0,1)\}$.

---

## 3. Transformación Lineal ([[Transformación lineal]])

### Definición:
Una **transformación lineal** $T: V \to W$ entre espacios vectoriales es una función que satisface:
1. **Aditividad**: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + T(\mathbf{v})$
2. **Homogeneidad**: $T(c\mathbf{v}) = cT(\mathbf{v})$

### Matriz asociada:
Si $T: \mathbb{R}^n \to \mathbb{R}^m$ es una transformación lineal, entonces existe una matriz $A \in \mathbb{R}^{m \times n}$ tal que:
$$
T(\mathbf{x}) = A\mathbf{x}
$$

### Núcleo e imagen:
- **Núcleo** ($\ker T$): $\{ \mathbf{v} \in V \mid T(\mathbf{v}) = \mathbf{0} \}$
- **Imagen** ($\operatorname{im} T$): $\{ T(\mathbf{v}) \in W \mid \mathbf{v} \in V \}$

### Teorema del rango:
$\dim \ker T + \dim \operatorname{im} T = \dim V$

---

## 4. Práctica con ejemplos

### Ejercicio 1:
Encuentra la base y dimensión del espacio vectorial $\mathbb{R}^3$.

### Ejercicio 2:
Determina si la siguiente transformación es lineal:
$$
T(x, y) = (2x + y, x - y)
$$

---

## 5. Conclusión

Los conceptos de Espacio Vectorial, Base, Dimensión y Transformación Lineal son fundamentales en el álgebra lineal. Su estudio permite:
- Modelar sistemas de ecuaciones lineales
- Describir fenómenos físicos en mecánica y electromagnetismo
- Aplicar técnicas de aprendizaje automático

Estos conceptos son la base para el análisis matemático en física e ingeniería.

---
