"""
system_dependency_graph
========================
Construye un DependencyGraph a partir de un vehicle_type y una lista de bloques.

Reglas:
  - Solo se incluyen dependencias entre bloques presentes en la lista recibida.
    Si un bloque custom (modo B) no existe en el catálogo, recibe deps=[].
  - build_dependency_graph normaliza vehicle_type via get_domain_dependencies,
    que a su vez usa VEHICLE_TYPE_ALIASES — misma clave canónica que la arquitectura.
  - No importa nada de jarvis.schemas.
"""
from __future__ import annotations

from dataclasses import dataclass

from jarvis.core.system_dependency_catalog import get_domain_dependencies


@dataclass
class DependencyGraph:
    """Grafo de dependencias de bloques de sistema.

    dependencies: { bloque: [bloques_de_los_que_depende] }
    Solo contiene los bloques del sistema actual (filtrado al construir).

    Inmutable por convención: no modificar dependencies tras la construcción.
    No se usa frozen=True porque el campo dict es inherentemente mutable y
    frozen=True solo impediría reasignación del atributo, no mutación interna.
    """
    dependencies: dict[str, list[str]]

    def get_dependencies(self, block: str) -> list[str]:
        """Devuelve la lista de bloques que deben definirse antes que 'block'."""
        return self.dependencies.get(block, [])

    def get_dependents(self, block: str) -> list[str]:
        """Devuelve los bloques que dependen de 'block' (para propagación futura)."""
        return [b for b, deps in self.dependencies.items() if block in deps]


def build_dependency_graph(vehicle_type: str, blocks: list[str]) -> DependencyGraph:
    """Construye el grafo de dependencias para el conjunto de bloques dado.

    - Usa el catálogo del dominio filtrado a los bloques presentes.
    - Bloques custom sin entrada en el catálogo reciben deps=[].
    - Incluye TODOS los bloques (base + custom) — los custom sin deps no alteran el orden.
    """
    catalog = get_domain_dependencies(vehicle_type)
    block_set = set(blocks)
    filtered = {
        block: [d for d in catalog.get(block, []) if d in block_set]
        for block in blocks
    }
    return DependencyGraph(dependencies=filtered)
