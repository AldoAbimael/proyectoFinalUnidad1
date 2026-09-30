"""
Módulo de repositorios (Capa de persistencia SQL y mapeo a objetos).
Cumple con RNF-1 y RNF-2: La UI nunca llama a SQL, solo a los servicios.
"""
from .usuario_repository import UsuarioRepository
from .libro_repository import LibroRepository
from .lector_repository import LectorRepository
from .prestamo_repository import PrestamoRepository

__all__ = [
    "UsuarioRepository",
    "LibroRepository",
    "LectorRepository",
    "PrestamoRepository"
]
