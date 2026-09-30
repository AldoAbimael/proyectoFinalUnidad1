import sqlite3
from typing import List, Optional
from db.database import get_connection, DEFAULT_DB_PATH
from models.usuario import Usuario


class UsuarioRepository:
    """
    Repositorio de persistencia para la entidad Usuario.
    Maneja consultas SQL puras y mapeo a objetos de dominio.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _map_row(self, row: sqlite3.Row) -> Usuario:
        # Usar .get o acceso seguro por claves para compatibilidad
        keys = row.keys()
        return Usuario(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            rol=row["rol"],
            activo=row["activo"],
            avatar_path=row["avatar_path"] if "avatar_path" in keys else None,
            tema=row["tema"] if "tema" in keys and row["tema"] else "estandar",
            fuente_familia=row["fuente_familia"] if "fuente_familia" in keys and row["fuente_familia"] else "Segoe UI",
            fuente_tamano=row["fuente_tamano"] if "fuente_tamano" in keys and row["fuente_tamano"] else 10
        )

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, username, password_hash, rol, activo, 
                          avatar_path, tema, fuente_familia, fuente_tamano 
                   FROM usuarios_sistema WHERE username = ?""",
                (username,)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def obtener_por_id(self, user_id: int) -> Optional[Usuario]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, username, password_hash, rol, activo, 
                          avatar_path, tema, fuente_familia, fuente_tamano 
                   FROM usuarios_sistema WHERE id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()
            return self._map_row(row) if row else None

    def listar_todos(self) -> List[Usuario]:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, username, password_hash, rol, activo, 
                          avatar_path, tema, fuente_familia, fuente_tamano 
                   FROM usuarios_sistema ORDER BY id ASC"""
            )
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]

    def crear(self, usuario: Usuario) -> int:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO usuarios_sistema 
                   (username, password_hash, rol, activo, avatar_path, tema, fuente_familia, fuente_tamano)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (usuario.username, usuario.password_hash, usuario.rol, usuario.activo,
                 usuario.avatar_path, usuario.tema, usuario.fuente_familia, usuario.fuente_tamano)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, usuario: Usuario) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE usuarios_sistema 
                   SET password_hash = ?, rol = ?, activo = ?, 
                       avatar_path = ?, tema = ?, fuente_familia = ?, fuente_tamano = ?
                   WHERE id = ?""",
                (usuario.password_hash, usuario.rol, usuario.activo,
                 usuario.avatar_path, usuario.tema, usuario.fuente_familia, usuario.fuente_tamano, usuario.id)
            )
            conn.commit()

    def cambiar_estado(self, user_id: int, activo: int) -> None:
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios_sistema SET activo = ? WHERE id = ?",
                (activo, user_id)
            )
            conn.commit()

    def actualizar_preferencias(self, user_id: int, tema: str, fuente_familia: str, fuente_tamano: int) -> None:
        """Actualiza las preferencias visuales y de accesibilidad del usuario."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE usuarios_sistema 
                   SET tema = ?, fuente_familia = ?, fuente_tamano = ?
                   WHERE id = ?""",
                (tema, fuente_familia, fuente_tamano, user_id)
            )
            conn.commit()

    def actualizar_avatar(self, user_id: int, avatar_path: Optional[str]) -> None:
        """Actualiza la ruta de la foto de perfil del usuario."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios_sistema SET avatar_path = ? WHERE id = ?",
                (avatar_path, user_id)
            )
            conn.commit()
