"""
Módulo de servicios (Capa de lógica de negocio).
Contiene las reglas de negocio, validaciones, transacciones y control de acceso.
Cumple con RNF-1, RNF-2 y RNF-4.
"""
from .exceptions import (
    BusinessError,
    ValidationError,
    AuthenticationError,
    IntegrityConflictError
)
from .auth_service import AuthService
from .usuario_service import UsuarioService
from .libro_service import LibroService
from .lector_service import LectorService
from .prestamo_service import PrestamoService

__all__ = [
    "BusinessError",
    "ValidationError",
    "AuthenticationError",
    "IntegrityConflictError",
    "AuthService",
    "UsuarioService",
    "LibroService",
    "LectorService",
    "PrestamoService"
]
