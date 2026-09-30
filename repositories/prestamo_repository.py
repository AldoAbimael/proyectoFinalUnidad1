import sqlite3
from typing import List, Optional
from datetime import date
from db.database import get_connection, DEFAULT_DB_PATH
from models.prestamo import Prestamo, PrestamoDetalle


class PrestamoRepository:
    """
    Repositorio para el movimiento de negocio Préstamo.
    Implementa consultas SQL puras con JOIN (RF-7) y consultas de reportes (RF-8).
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _map_row_to_prestamo(self, row: sqlite3.Row) -> Prestamo:
        return Prestamo(
            id=row["id"],
            lector_id=row["lector_id"],
            libro_id=row["libro_id"],
            fecha_prestamo=row["fecha_prestamo"],
            fecha_vencimiento=row["fecha_vencimiento"],
            fecha_devolucion=row["fecha_devolucion"],
            estado=row["estado"]
        )

    def _map_row_to_detalle(self, row: sqlite3.Row) -> PrestamoDetalle:
        return PrestamoDetalle(
            id=row["id"],
            lector_id=row["lector_id"],
            lector_folio=row["lector_folio"],
            lector_nombre=row["lector_nombre"],
            lector_tipo=row["lector_tipo"],
            libro_id=row["libro_id"],
            libro_isbn=row["libro_isbn"],
            libro_titulo=row["libro_titulo"],
            fecha_prestamo=row["fecha_prestamo"],
            fecha_vencimiento=row["fecha_vencimiento"],
            fecha_devolucion=row["fecha_devolucion"],
            estado=row["estado"]
        )

    def obtener_por_id(self, prestamo_id: int) -> Optional[Prestamo]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, lector_id, libro_id, fecha_prestamo, fecha_vencimiento, 
                          fecha_devolucion, estado 
                   FROM prestamos WHERE id = ?""",
                (prestamo_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_prestamo(row) if row else None

    def tiene_prestamo_activo_del_libro(self, lector_id: int, libro_id: int) -> bool:
        """
        Regla de negocio: Un lector no puede tener dos préstamos activos del mismo libro.
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT COUNT(*) FROM prestamos 
                   WHERE lector_id = ? AND libro_id = ? AND estado = 'activo'""",
                (lector_id, libro_id)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def crear(self, prestamo: Prestamo) -> int:
        """Inserta un nuevo préstamo en la base de datos."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO prestamos 
                   (lector_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (prestamo.lector_id, prestamo.libro_id, prestamo.fecha_prestamo,
                 prestamo.fecha_vencimiento, prestamo.fecha_devolucion, prestamo.estado)
            )
            conn.commit()
            return cursor.lastrowid

    def registrar_devolucion(self, prestamo_id: int, fecha_devolucion: str) -> None:
        """Actualiza el estado del préstamo a devuelto y asigna la fecha de entrega."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE prestamos 
                   SET estado = 'devuelto', fecha_devolucion = ? 
                   WHERE id = ?""",
                (fecha_devolucion, prestamo_id)
            )
            conn.commit()

    def listar_con_detalle(
        self,
        filtro_estado: Optional[str] = None,
        busqueda: Optional[str] = None
    ) -> List[PrestamoDetalle]:
        """
        RF-7: Consulta SQL con JOIN obligatorio:
        Préstamo + nombre y folio del lector + título e ISBN del libro.
        Permite filtrado visible en Treeview por estado y búsqueda textual (RF-6).
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.id,
                    p.lector_id,
                    lec.folio AS lector_folio,
                    lec.nombre AS lector_nombre,
                    lec.tipo AS lector_tipo,
                    p.libro_id,
                    lib.isbn AS libro_isbn,
                    lib.titulo AS libro_titulo,
                    p.fecha_prestamo,
                    p.fecha_vencimiento,
                    p.fecha_devolucion,
                    p.estado
                FROM prestamos p
                JOIN lectores lec ON p.lector_id = lec.id
                JOIN libros lib ON p.libro_id = lib.id
                WHERE 1=1
            """
            params = []

            if filtro_estado and filtro_estado in ("activo", "devuelto"):
                query += " AND p.estado = ?"
                params.append(filtro_estado)

            if busqueda and busqueda.strip():
                pattern = f"%{busqueda.strip()}%"
                query += """ AND (lec.nombre LIKE ? OR lec.folio LIKE ? 
                             OR lib.titulo LIKE ? OR lib.isbn LIKE ?)"""
                params.extend([pattern, pattern, pattern, pattern])

            query += " ORDER BY p.id DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row_to_detalle(r) for r in rows]

    def obtener_prestamos_atrasados(self) -> List[PrestamoDetalle]:
        """
        RF-8: Consulta SQL del caso problemático del dominio:
        Préstamos activos con fecha de vencimiento menor al día actual (vencimiento < date('now')).
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.id,
                    p.lector_id,
                    lec.folio AS lector_folio,
                    lec.nombre AS lector_nombre,
                    lec.tipo AS lector_tipo,
                    p.libro_id,
                    lib.isbn AS libro_isbn,
                    lib.titulo AS libro_titulo,
                    p.fecha_prestamo,
                    p.fecha_vencimiento,
                    p.fecha_devolucion,
                    p.estado
                FROM prestamos p
                JOIN lectores lec ON p.lector_id = lec.id
                JOIN libros lib ON p.libro_id = lib.id
                WHERE p.estado = 'activo' AND p.fecha_vencimiento < date('now')
                ORDER BY p.fecha_vencimiento ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._map_row_to_detalle(r) for r in rows]
