from dataclasses import dataclass
from typing import Optional


@dataclass
class Libro:
    """
    Entidad de dominio A: Libros del acervo bibliotecario.
    Atributos: ISBN, título, autor, categoría, año, stock_total, stock_disponible, activo.
    """
    id: Optional[int]
    isbn: str
    titulo: str
    autor: str
    categoria: str
    anio: int
    stock_total: int
    stock_disponible: int
    activo: int = 1  # 1: Activo, 0: Desactivado / Baja lógica

    @property
    def tiene_stock(self) -> bool:
        return self.stock_disponible > 0

    @property
    def esta_activo(self) -> bool:
        return bool(self.activo)
