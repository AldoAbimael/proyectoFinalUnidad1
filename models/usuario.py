from dataclasses import dataclass
from typing import Optional


@dataclass
class Usuario:
    """Entidad de dominio que representa a un usuario del sistema (login/credenciales)."""
    id: Optional[int]
    username: str
    password_hash: str
    rol: str  # 'administrador' | 'operador'
    activo: int = 1  # 1: Activo, 0: Inactivo
    avatar_path: Optional[str] = None
    tema: str = "estandar"
    fuente_familia: str = "Segoe UI"
    fuente_tamano: int = 10

    @property
    def es_admin(self) -> bool:
        return self.rol == "administrador"

    @property
    def esta_activo(self) -> bool:
        return bool(self.activo)
