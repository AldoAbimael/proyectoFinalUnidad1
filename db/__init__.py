"""
Módulo de acceso a la base de datos SQLite para el Sistema de Biblioteca.
"""
from .database import get_connection, init_db, DEFAULT_DB_PATH

__all__ = ["get_connection", "init_db", "DEFAULT_DB_PATH"]
