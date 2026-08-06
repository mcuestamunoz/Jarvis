"""
priority_engine
===============
Ordena bloques de sistema según su grafo de dependencias (topological sort DFS).

Garantías:
  - Protección contra ciclos: usa dos conjuntos (visited + visiting).
    Si se detecta un ciclo, el bloque implicado se omite del orden y se lanza
    un warning (no excepción) — el sistema no se rompe ante catálogos malformados.
  - Orden estable: los nodos sin dependencias aparecen primero, respetando
    el orden de iteración original de graph.dependencies (inserción en dict Python 3.7+).
  - No importa nada de jarvis.schemas.
"""
from __future__ import annotations

import warnings

from jarvis.core.system_dependency_graph import DependencyGraph


def compute_priority_order(graph: DependencyGraph) -> list[str]:
    """Devuelve la lista de bloques ordenada de menos a más dependiente.

    Ejemplo:
      dron → ["propulsion", "energy", "structure", "control"]
      El primer elemento es siempre el bloque raíz (sin dependencias).

    Protección ante ciclos:
      Si se detecta un ciclo (bloque ya en `visiting`), se emite un warning
      y ese bloque se salta — evita recursión infinita sin crash.
    """
    visited: set[str] = set()
    visiting: set[str] = set()   # nodos en el stack actual de DFS — detecta ciclos
    result: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            warnings.warn(
                f"priority_engine: ciclo detectado en bloque '{node}', "
                "se omite del orden de prioridad.",
                stacklevel=2,
            )
            return
        visiting.add(node)
        for dep in graph.get_dependencies(node):
            visit(dep)
        visiting.discard(node)
        visited.add(node)
        result.append(node)

    for node in graph.dependencies:
        visit(node)

    return result
