---
title: "Matrices"
date: 2026-03-21
estado: "Nuevo"
---

> [!ABSTRACT]
> **Conceptos Básicos de Matrices**
> Explicación detallada de matrices, determinantes, matrices inversas y multiplicación de matrices. Todo lo que necesitas saber para entender las operaciones fundamentales del álgebra lineal.

---

## 1. Matriz ([[Matriz]])

### Definición:
Una **matriz** es un arreglo rectangular de números ordenados por filas y columnas. Se denota como $A = (a_{ij})$, donde $i$ es el número de fila y $j$ el número de columna.

### Notación:
- **Matriz fila**: Una matriz con una fila.
- **Matriz columna**: Una matriz con una columna.
- **Matriz cuadrada**: Número de filas igual al número de columnas.

### Ejemplo:
$$
A = \begin{pmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{pmatrix}
$$

---

## 2. Determinante ([[Determinante]])

### Definición:
El **determinante** es un escalar asociado a una matriz cuadrada. Se denota como $\det(A)$ o $|A|$.

### Propiedades:
- **Cálculo para matrices 2x2**:
  $$
  \det \begin{pmatrix}
  a & b \\
  c & d
  \end{pmatrix} = ad - bc
  $$

- **Cálculo para matrices 3x3** (regla de Sarrus):
  $$
  \det \begin{pmatrix}
  a & b & c \\
  d & e & f \\
  g & h & i
  \end{pmatrix} = a(ei − fh) − b(di − fg) + c(dh − eg)
  $$

### Interpretación:
- El determinante mide el volumen (en 3D) o área (en 2D) transformado por la matriz.

---

## 3. Matriz Inversa ([[Matriz inversa]])

### Definición:
La **matriz inversa** $A^{-1}$ de una matriz cuadrada $A$ es aquella que cumple:
$$
A \cdot A^{-1} = A^{-1} \cdot A = I
$$
donde $I$ es la **matriz identidad**.

### Cálculo:
- **Para matrices 2x2**:
  $$
  A = \begin{pmatrix}
  a & b \\
  c & d
  \end{pmatrix}, \quad \det(A) = ad - bc \neq 0
  $$
  $$
  A^{-1} = \frac{1}{\det(A)} \begin{pmatrix}
  d & -b \\
  -c & a
  \end{pmatrix}
  $$

- **Para matrices 3x3** (usando cofactores o reducción por filas).

### Condición:
- Una matriz tiene inversa si y solo si su determinante es no nulo.

---

## 4. Multiplicación de Matrices ([[Multiplicación de matrices]])

### Definición:
La **multiplicación de matrices** $A$ y $B$ ($C = A \cdot B$) requiere que el número de columnas de $A$ sea igual al número de filas de $B$. El resultado es una matriz $C$ de tamaño $m \times n$, donde $A$ es $m \times p$ y $B$ es $p \times n$.

### Cálculo:
$$
C_{ij} = \sum_{k=1}^{p} A_{ik} \cdot B_{kj}
$$

### Ejemplo:
$$
A = \begin{pmatrix}
1 & 2 \\
3 & 4
\end{pmatrix}, \quad B = \begin{pmatrix}
5 & 6 \\
7 & 8
\end{pmatrix}
$$
$$
C = \begin{pmatrix}
1*5 + 2*7 & 1*6 + 2*8 \\
3*5 + 4*7 & 3*6 + 4*8
\end{pmatrix} = \begin{pmatrix}
19 & 22 \\
43 & 50
\end{pmatrix}
$$

---

## 5. Aplicaciones Prácticas

### Ejemplo 1: Transformaciones Lineales
Las matrices permiten modelar rotaciones, escalados y traslaciones en 2D y 3D.

### Ejemplo 2: Resolución de Sistemas de Ecuaciones
Un sistema de ecuaciones lineales puede representarse como $AX = B$, donde $A$ es la matriz de coeficientes, $X$ el vector de incógnitas y $B$ el vector de términos independientes.

---

## 6. Conclusión

Las matrices son herramientas esenciales en el álgebra lineal, permitiendo:
- Modelar transformaciones geométricas
- Resolver sistemas de ecuaciones simultáneas
- Analizar datos multidimensionales

Estos conceptos son fundamentales en campos como la física, la ingeniería y el aprendizaje automático.

---

