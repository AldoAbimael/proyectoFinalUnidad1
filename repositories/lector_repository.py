import sqlite3
from typing import List, Optional
from db.database import get_connection, DEFAULT_DB_PATH
from models.lector import Lector


class LectorRepository:
    """
    Repositorio para la entidad Lector (Entidad B).
    Encapsula consultas SQL y mapeo a objetos Lector (RNF-2).
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _map_row(self, row: sqlite3.Row) -> Lector:
        return Lector(
            id=row["id"],
            folio=row["folio"],
            nombre=row["nombre"],
            correo=row["correo"],
            telefono=row["telefono"],
            tipo=row["tipo"],
            activo=row["activo"]
        )

    def obtener_por_id(self, lector_id: int) -> Optional[Lector]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, folio, nombre, correo, telefono, tipo, activo 
                   FROM lectores WHERE id = ?""",
                (lector_id,)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def obtener_por_folio(self, folio: str) -> Optional[Lector]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, folio, nombre, correo, telefono, tipo, activo 
                   FROM lectores WHERE folio = ?""",
                (folio.strip(),)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def obtener_por_correo(self, correo: str) -> Optional[Lector]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, folio, nombre, correo, telefono, tipo, activo 
                   FROM lectores WHERE correo = ?""",
                (correo.strip().lower(),)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def listar_todos(self, solo_activos: bool = False) -> List[Lector]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT id, folio, nombre, correo, telefono, tipo, activo FROM lectores"
            params = []
            if solo_activos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]

    def buscar(self, criterio: str, solo_activos: bool = False) -> List[Lector]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            pattern = f"%{criterio.strip()}%"
            query = """SELECT id, folio, nombre, correo, telefono, tipo, activo 
                       FROM lectores 
                       WHERE (folio LIKE ? OR nombre LIKE ? OR correo LIKE ? OR telefono LIKE ? OR tipo LIKE ?)"""
            params = [pattern, pattern, pattern, pattern, pattern]
            if solo_activos:
                query += " AND activo = 1"
            query += " ORDER BY nombre ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]

    def crear(self, lector: Lector) -> int:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO lectores (folio, nombre, correo, telefono, tipo, activo)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (lector.folio, lector.nombre, lector.correo, lector.telefono, lector.tipo, lector.activo)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, lector: Lector) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE lectores 
                   SET folio = ?, nombre = ?, correo = ?, telefono = ?, tipo = ?, activo = ?
                   WHERE id = ?""",
                (lector.folio, lector.nombre, lector.correo, lector.telefono, lector.tipo, lector.activo, lector.id)
            )
            conn.commit()

    def cambiar_estado(self, lector_id: int, activo: int) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE lectores SET activo = ? WHERE id = ?",
                (activo, lector_id)
            )
            conn.commit()

    def tiene_prestamos_activos(self, lector_id: int) -> bool:
        """Verifica si el lector tiene préstamos sin devolver (estado = 'activo')."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM prestamos WHERE lector_id = ? AND estado = 'activo'",
                (lector_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def tiene_prestamos_historicos(self, lector_id: int) -> bool:
        """Verifica si el lector tiene algún préstamo en el historial general."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM prestamos WHERE lector_id = ?",
                (lector_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def eliminar_fisico(self, lector_id: int) -> None:
        """
        Intento de eliminación física en la base de datos.
        Lanza sqlite3.IntegrityError si existen préstamos vinculados con ON DELETE RESTRICT.
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lectores WHERE id = ?", (lector_id,))
            conn.commit()
