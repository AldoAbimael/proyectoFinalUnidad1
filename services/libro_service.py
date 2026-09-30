import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
from models.libro import Libro
from repositories.libro_repository import LibroRepository
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError


class LibroService:
    """
    Servicio de lógica de negocio para la Entidad A: Libros.
    Valida campos, reglas de stock y controla la integridad referencial (RF-4, RF-10, RNF-4).
    """

    def __init__(self, libro_repo: Optional[LibroRepository] = None):
        self.libro_repo = libro_repo or LibroRepository()

    def _validar_datos(
        self,
        isbn: str,
        titulo: str,
        autor: str,
        categoria: str,
        anio: int,
        stock_total: int,
        stock_disponible: int
    ) -> None:
        """Valida tipos, rangos y campos obligatorios."""
        if not isbn or not str(isbn).strip():
            raise ValidationError("El ISBN es obligatorio y no puede estar vacío.")
        if not titulo or not str(titulo).strip():
            raise ValidationError("El título del libro no puede estar vacío.")
        if not autor or not str(autor).strip():
            raise ValidationError("El autor del libro no puede estar vacío.")
        if not categoria or not str(categoria).strip():
            raise ValidationError("La categoría no puede estar vacía.")

        try:
            anio_int = int(anio)
        except (ValueError, TypeError):
            raise ValidationError("El año de publicación debe ser un número entero.")

        anio_actual = datetime.now().year
        if anio_int < 1400 or anio_int > anio_actual + 1:
            raise ValidationError(f"El año de publicación debe estar entre 1400 y {anio_actual + 1}.")

        try:
            st_total = int(stock_total)
            st_disp = int(stock_disponible)
        except (ValueError, TypeError):
            raise ValidationError("Los valores de stock total y disponible deben ser enteros numéricos.")

        if st_total < 0:
            raise ValidationError("El stock total no puede ser negativo.")
        if st_disp < 0:
            raise ValidationError("El stock disponible no puede ser negativo.")
        if st_disp > st_total:
            raise ValidationError("El stock disponible no puede ser mayor al stock total.")

    def listar_libros(self, solo_activos: bool = False) -> List[Libro]:
        return self.libro_repo.listar_todos(solo_activos=solo_activos)

    def buscar_libros(self, criterio: str, solo_activos: bool = False) -> List[Libro]:
        return self.libro_repo.buscar(criterio, solo_activos=solo_activos)

    def obtener_libro(self, libro_id: int) -> Libro:
        libro = self.libro_repo.obtener_por_id(libro_id)
        if not libro:
            raise ValidationError(f"No se encontró el libro con ID {libro_id}.")
        return libro

    def crear_libro(
        self,
        isbn: str,
        titulo: str,
        autor: str,
        categoria: str,
        anio: int,
        stock_total: int,
        stock_disponible: Optional[int] = None,
        activo: int = 1
    ) -> Libro:
        isbn = isbn.strip()
        titulo = titulo.strip()
        autor = autor.strip()
        categoria = categoria.strip()
        
        # Si no se indica stock disponible al crear, por defecto es igual al stock total
        if stock_disponible is None:
            stock_disponible = stock_total

        self._validar_datos(isbn, titulo, autor, categoria, anio, stock_total, stock_disponible)

        existente = self.libro_repo.obtener_por_isbn(isbn)
        if existente:
            raise IntegrityConflictError(f"Ya existe un libro registrado con el ISBN '{isbn}'.")

        nuevo_libro = Libro(
            id=None,
            isbn=isbn,
            titulo=titulo,
            autor=autor,
            categoria=categoria,
            anio=int(anio),
            stock_total=int(stock_total),
            stock_disponible=int(stock_disponible),
            activo=1 if activo else 0
        )

        try:
            nuevo_id = self.libro_repo.crear(nuevo_libro)
            nuevo_libro.id = nuevo_id
            return nuevo_libro
        except sqlite3.IntegrityError as e:
            raise IntegrityConflictError(f"Error de integridad en base de datos: {e}")

    def actualizar_libro(
        self,
        libro_id: int,
        isbn: str,
        titulo: str,
        autor: str,
        categoria: str,
        anio: int,
        stock_total: int,
        stock_disponible: int,
        activo: int = 1
    ) -> Libro:
        libro_actual = self.obtener_libro(libro_id)
        isbn = isbn.strip()
        titulo = titulo.strip()
        autor = autor.strip()
        categoria = categoria.strip()

        self._validar_datos(isbn, titulo, autor, categoria, anio, stock_total, stock_disponible)

        # Si cambió el ISBN, comprobar que el nuevo no pertenezca a otro libro
        if isbn != libro_actual.isbn:
            existente = self.libro_repo.obtener_por_isbn(isbn)
            if existente and existente.id != libro_id:
                raise IntegrityConflictError(f"El ISBN '{isbn}' ya pertenece a otro libro registrado.")

        libro_actual.isbn = isbn
        libro_actual.titulo = titulo
        libro_actual.autor = autor
        libro_actual.categoria = categoria
        libro_actual.anio = int(anio)
        libro_actual.stock_total = int(stock_total)
        libro_actual.stock_disponible = int(stock_disponible)
        libro_actual.activo = 1 if activo else 0

        try:
            self.libro_repo.actualizar(libro_actual)
            return libro_actual
        except sqlite3.IntegrityError as e:
            raise IntegrityConflictError(f"Error de integridad al actualizar libro: {e}")

    def cambiar_estado(self, libro_id: int, nuevo_activo: int) -> None:
        """Activa o desactiva lógicamente un libro."""
        libro = self.obtener_libro(libro_id)
        if nuevo_activo == 0 and self.libro_repo.tiene_prestamos_activos(libro_id):
            raise BusinessError(
                f"No se puede desactivar el libro '{libro.titulo}' porque actualmente tiene préstamos activos sin devolver."
            )
        self.libro_repo.cambiar_estado(libro_id, 1 if nuevo_activo else 0)

    def eliminar_o_desactivar(self, libro_id: int) -> Tuple[str, str]:
        """
        RF-10 y Reglas de la Opción 1:
        - Si tiene préstamos activos: NO se permite eliminar ni desactivar.
        - Si tiene préstamos históricos: Se desactiva (baja lógica) para mantener integridad referencial.
        - Si no tiene préstamos de ningún tipo: Se elimina físicamente de la base de datos.
        Retorna (accion_realizada, mensaje_informativo).
        """
        libro = self.obtener_libro(libro_id)

        if self.libro_repo.tiene_prestamos_activos(libro_id):
            raise BusinessError(
                f"No se puede eliminar ni dar de baja el libro '{libro.titulo}' porque tiene préstamos ACTIVOS en curso. "
                "Debe registrarse primero la devolución de todos sus ejemplares."
            )

        if self.libro_repo.tiene_prestamos_historicos(libro_id):
            # Proteger historial con baja lógica (RF-10)
            self.libro_repo.cambiar_estado(libro_id, 0)
            return (
                "desactivado",
                f"El libro '{libro.titulo}' tiene préstamos registrados en el historial. "
                "Para preservar la integridad referencial, fue desactivado (baja lógica)."
            )

        # Sin historial: eliminación física segura
        try:
            self.libro_repo.eliminar_fisico(libro_id)
            return ("eliminado", f"El libro '{libro.titulo}' fue eliminado correctamente.")
        except sqlite3.IntegrityError:
            # Fallback en caso de restricción en BD
            self.libro_repo.cambiar_estado(libro_id, 0)
            return (
                "desactivado",
                f"Por restricción de clave foránea, el libro '{libro.titulo}' fue desactivado."
            )
