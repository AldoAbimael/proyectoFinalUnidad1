from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Prestamo:
    """
    Entidad de dominio: Movimiento de préstamo bibliotecario.
    Cruza lector (Entidad B) y libro (Entidad A).
    """
    id: Optional[int]
    lector_id: int
    libro_id: int
    fecha_prestamo: str      # Formato ISO: YYYY-MM-DD
    fecha_vencimiento: str   # Formato ISO: YYYY-MM-DD
    fecha_devolucion: Optional[str] = None  # Formato ISO: YYYY-MM-DD o None
    estado: str = "activo"   # 'activo' | 'devuelto'

    @property
    def esta_devuelto(self) -> bool:
        return self.estado == "devuelto"


@dataclass
class PrestamoDetalle:
    """
    DTO para representar la consulta SQL con JOIN obligatoria (RF-7):
    Cruza préstamo con datos del lector y del libro para presentación en Treeview.
    """
    id: int
    lector_id: int
    lector_folio: str
    lector_nombre: str
    lector_tipo: str
    libro_id: int
    libro_isbn: str
    libro_titulo: str
    fecha_prestamo: str
    fecha_vencimiento: str
    fecha_devolucion: Optional[str]
    estado: str

    @property
    def esta_atrasado(self) -> bool:
        """Determina si el préstamo está atrasado (activo con vencimiento < hoy)."""
        if self.estado != "activo":
            return False
        hoy_str = date.today().isoformat()
        return self.fecha_vencimiento < hoy_str
