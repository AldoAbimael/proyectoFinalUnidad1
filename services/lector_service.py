import re
import sqlite3
from typing import List, Optional, Tuple
from models.lector import Lector
from repositories.lector_repository import LectorRepository
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError


class LectorService:
    """
    Servicio de lógica de negocio para la Entidad B: Lectores.
    Valida formatos de folio, correo y tipo, y gestiona la integridad referencial (RF-4, RF-10, RNF-4).
    """

    def __init__(self, lector_repo: Optional[LectorRepository] = None):
        self.lector_repo = lector_repo or LectorRepository()

    def _validar_datos(
        self,
        folio: str,
        nombre: str,
        correo: str,
        telefono: str,
        tipo: str
    ) -> None:
        """Valida que los campos no estén vacíos y tengan formatos válidos."""
        if not folio or not str(folio).strip():
            raise ValidationError("El folio del lector es obligatorio y no puede estar vacío.")
        if not nombre or not str(nombre).strip():
            raise ValidationError("El nombre del lector no puede estar vacío.")
        if not correo or not str(correo).strip():
            raise ValidationError("El correo electrónico es obligatorio.")
        
        correo_limpio = correo.strip().lower()
        patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(patron_email, correo_limpio):
            raise ValidationError(f"El correo '{correo}' no tiene un formato válido (ejemplo: usuario@correo.com).")

        if not telefono or not str(telefono).strip():
            raise ValidationError("El número de teléfono no puede estar vacío.")

        tipo_limpio = (tipo or "").strip().lower()
        if tipo_limpio not in ("alumno", "docente", "externo"):
            raise ValidationError("El tipo de lector debe ser 'alumno', 'docente' o 'externo'.")

    def listar_lectores(self, solo_activos: bool = False) -> List[Lector]:
        return self.lector_repo.listar_todos(solo_activos=solo_activos)

    def buscar_lectores(self, criterio: str, solo_activos: bool = False) -> List[Lector]:
        return self.lector_repo.buscar(criterio, solo_activos=solo_activos)

    def obtener_lector(self, lector_id: int) -> Lector:
        lector = self.lector_repo.obtener_por_id(lector_id)
        if not lector:
            raise ValidationError(f"No se encontró el lector con ID {lector_id}.")
        return lector

    def crear_lector(
        self,
        folio: str,
        nombre: str,
        correo: str,
        telefono: str,
        tipo: str,
        activo: int = 1
    ) -> Lector:
        folio = folio.strip()
        nombre = nombre.strip()
        correo = correo.strip().lower()
        telefono = telefono.strip()
        tipo = tipo.strip().lower()

        self._validar_datos(folio, nombre, correo, telefono, tipo)

        # Validar unicidad de folio
        if self.lector_repo.obtener_por_folio(folio):
            raise IntegrityConflictError(f"Ya existe un lector registrado con el folio '{folio}'.")

        # Validar unicidad de correo
        if self.lector_repo.obtener_por_correo(correo):
            raise IntegrityConflictError(f"El correo '{correo}' ya se encuentra registrado con otro lector.")

        nuevo_lector = Lector(
            id=None,
            folio=folio,
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            tipo=tipo,
            activo=1 if activo else 0
        )

        try:
            nuevo_id = self.lector_repo.crear(nuevo_lector)
            nuevo_lector.id = nuevo_id
            return nuevo_lector
        except sqlite3.IntegrityError as e:
            raise IntegrityConflictError(f"Error de integridad en base de datos: {e}")

    def actualizar_lector(
        self,
        lector_id: int,
        folio: str,
        nombre: str,
        correo: str,
        telefono: str,
        tipo: str,
        activo: int = 1
    ) -> Lector:
        lector_actual = self.obtener_lector(lector_id)
        folio = folio.strip()
        nombre = nombre.strip()
        correo = correo.strip().lower()
        telefono = telefono.strip()
        tipo = tipo.strip().lower()

        self._validar_datos(folio, nombre, correo, telefono, tipo)

        # Si cambió el folio, validar unicidad
        if folio != lector_actual.folio:
            existente_folio = self.lector_repo.obtener_por_folio(folio)
            if existente_folio and existente_folio.id != lector_id:
                raise IntegrityConflictError(f"El folio '{folio}' ya está en uso por otro lector.")

        # Si cambió el correo, validar unicidad
        if correo != lector_actual.correo:
            existente_correo = self.lector_repo.obtener_por_correo(correo)
            if existente_correo and existente_correo.id != lector_id:
                raise IntegrityConflictError(f"El correo '{correo}' ya está en uso por otro lector.")

        lector_actual.folio = folio
        lector_actual.nombre = nombre
        lector_actual.correo = correo
        lector_actual.telefono = telefono
        lector_actual.tipo = tipo
        lector_actual.activo = 1 if activo else 0

        try:
            self.lector_repo.actualizar(lector_actual)
            return lector_actual
        except sqlite3.IntegrityError as e:
            raise IntegrityConflictError(f"Error de integridad al actualizar lector: {e}")

    def cambiar_estado(self, lector_id: int, nuevo_activo: int) -> None:
        """Activa o desactiva lógicamente a un lector."""
        lector = self.obtener_lector(lector_id)
        if nuevo_activo == 0 and self.lector_repo.tiene_prestamos_activos(lector_id):
            raise BusinessError(
                f"No se puede desactivar al lector '{lector.nombre}' porque tiene préstamos pendientes de devolver."
            )
        self.lector_repo.cambiar_estado(lector_id, 1 if nuevo_activo else 0)

    def eliminar_o_desactivar(self, lector_id: int) -> Tuple[str, str]:
        """
        RF-10 y Reglas de la Opción 1:
        - Si tiene préstamos activos: NO se permite eliminar ni desactivar.
        - Si tiene préstamos históricos: Se desactiva (baja lógica).
        - Si no tiene préstamos registrados: Se elimina físicamente de la base de datos.
        Retorna (accion_realizada, mensaje_informativo).
        """
        lector = self.obtener_lector(lector_id)

        if self.lector_repo.tiene_prestamos_activos(lector_id):
            raise BusinessError(
                f"No se puede eliminar ni dar de baja al lector '{lector.nombre}' porque actualmente tiene "
                "préstamos ACTIVOS sin devolver. Debe registrarse primero la devolución de los libros."
            )

        if self.lector_repo.tiene_prestamos_historicos(lector_id):
            self.lector_repo.cambiar_estado(lector_id, 0)
            return (
                "desactivado",
                f"El lector '{lector.nombre}' tiene historial de préstamos. "
                "Para preservar la integridad de datos, fue desactivado (baja lógica)."
            )

        try:
            self.lector_repo.eliminar_fisico(lector_id)
            return ("eliminado", f"El lector '{lector.nombre}' fue eliminado correctamente.")
        except sqlite3.IntegrityError:
            self.lector_repo.cambiar_estado(lector_id, 0)
            return (
                "desactivado",
                f"Por restricción de clave foránea, el lector '{lector.nombre}' fue desactivado."
            )
