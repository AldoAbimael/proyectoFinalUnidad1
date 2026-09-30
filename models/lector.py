from dataclasses import dataclass
from typing import Optional


@dataclass
class Lector:
    """
    Entidad de dominio B: Lectores registrados en la biblioteca.
    Atributos: folio, nombre, correo, teléfono, tipo (alumno/docente/externo), activo.
    """
    id: Optional[int]
    folio: str
    nombre: str
    correo: str
    telefono: str
    tipo: str  # 'alumno' | 'docente' | 'externo'
    activo: int = 1  # 1: Activo, 0: Desactivado / Baja lógica

    @property
    def esta_activo(self) -> bool:
        return bool(self.activo)
