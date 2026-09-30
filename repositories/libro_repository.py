import sqlite3
from typing import List, Optional
from db.database import get_connection, DEFAULT_DB_PATH
from models.libro import Libro


class LibroRepository:
    """
    Repositorio para la entidad Libro (Entidad A).
    Encapsula consultas SQL y mapeo a objetos Libro (RNF-2).
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _map_row(self, row: sqlite3.Row) -> Libro:
        return Libro(
            id=row["id"],
            isbn=row["isbn"],
            titulo=row["titulo"],
            autor=row["autor"],
            categoria=row["categoria"],
            anio=row["anio"],
            stock_total=row["stock_total"],
            stock_disponible=row["stock_disponible"],
            activo=row["activo"]
        )

    def obtener_por_id(self, libro_id: int) -> Optional[Libro]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo 
                   FROM libros WHERE id = ?""",
                (libro_id,)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def obtener_por_isbn(self, isbn: str) -> Optional[Libro]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo 
                   FROM libros WHERE isbn = ?""",
                (isbn.strip(),)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def listar_todos(self, solo_activos: bool = False) -> List[Libro]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query = """SELECT id, isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo 
                       FROM libros"""
            params = []
            if solo_activos:
                query += " WHERE activo = 1"
            query += " ORDER BY titulo ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]

    def buscar(self, criterio: str, solo_activos: bool = False) -> List[Libro]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            pattern = f"%{criterio.strip()}%"
            query = """SELECT id, isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo 
                       FROM libros 
                       WHERE (isbn LIKE ? OR titulo LIKE ? OR autor LIKE ? OR categoria LIKE ?)"""
            params = [pattern, pattern, pattern, pattern]
            if solo_activos:
                query += " AND activo = 1"
            query += " ORDER BY titulo ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]

    def crear(self, libro: Libro) -> int:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO libros 
                   (isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (libro.isbn, libro.titulo, libro.autor, libro.categoria, libro.anio,
                 libro.stock_total, libro.stock_disponible, libro.activo)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, libro: Libro) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE libros 
                   SET isbn = ?, titulo = ?, autor = ?, categoria = ?, anio = ?, 
                       stock_total = ?, stock_disponible = ?, activo = ?
                   WHERE id = ?""",
                (libro.isbn, libro.titulo, libro.autor, libro.categoria, libro.anio,
                 libro.stock_total, libro.stock_disponible, libro.activo, libro.id)
            )
            conn.commit()

    def actualizar_stock_disponible(self, libro_id: int, nuevo_stock_disponible: int) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE libros SET stock_disponible = ? WHERE id = ?",
                (nuevo_stock_disponible, libro_id)
            )
            conn.commit()

    def cambiar_estado(self, libro_id: int, activo: int) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE libros SET activo = ? WHERE id = ?",
                (activo, libro_id)
            )
            conn.commit()

    def tiene_prestamos_activos(self, libro_id: int) -> bool:
        """Verifica si el libro tiene préstamos en curso con estado 'activo'."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM prestamos WHERE libro_id = ? AND estado = 'activo'",
                (libro_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def tiene_prestamos_historicos(self, libro_id: int) -> bool:
        """Verifica si el libro tiene cualquier préstamo registrado en el historial."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM prestamos WHERE libro_id = ?",
                (libro_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def eliminar_fisico(self, libro_id: int) -> None:
        """
        Intento de borrado físico en base de datos.
        Si existen préstamos hijos, SQLite lanzará sqlite3.IntegrityError por la FK ON DELETE RESTRICT.
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
            conn.commit()
