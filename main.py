"""
Punto de Entrada Principal — Sistema de Gestión Bibliotecaria
Tópicos Avanzados de Programación · Unidad 1 · Opción 1: Sistema de Biblioteca

Arquitectura por Capas:
  UI (Tkinter/ttk) ➔ Services (Reglas de Negocio) ➔ Repositories (SQL) ➔ DB (SQLite 3)
"""
import sys
import tkinter as tk
from db.database import init_db, DEFAULT_DB_PATH
from repositories import (
    UsuarioRepository,
    LibroRepository,
    LectorRepository,
    PrestamoRepository
)
from services import (
    AuthService,
    UsuarioService,
    LibroService,
    LectorService,
    PrestamoService
)
from ui import LoginWindow, MainWindow
from models.usuario import Usuario


class BibliotecaApp:
    """Controlador principal de la aplicación y ciclo de vida de ventanas."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

        # 1. Inicializar persistencia de datos (RF-1, A.5)
        init_db(self.db_path)

        # 2. Instanciar repositorios (Capa de datos y SQL)
        self.usuario_repo = UsuarioRepository(self.db_path)
        self.libro_repo = LibroRepository(self.db_path)
        self.lector_repo = LectorRepository(self.db_path)
        self.prestamo_repo = PrestamoRepository(self.db_path)

        # 3. Instanciar servicios (Capa de negocio y validación)
        self.auth_service = AuthService(self.usuario_repo)
        self.usuario_service = UsuarioService(self.usuario_repo)
        self.libro_service = LibroService(self.libro_repo)
        self.lector_service = LectorService(self.lector_repo)
        self.prestamo_service = PrestamoService(
            db_path=self.db_path,
            prestamo_repo=self.prestamo_repo,
            libro_repo=self.libro_repo,
            lector_repo=self.lector_repo
        )

        self.login_window: LoginWindow = None
        self.main_window: MainWindow = None

    def start(self) -> None:
        """Inicia la aplicación presentando la ventana de inicio de sesión."""
        self.login_window = LoginWindow(
            auth_service=self.auth_service,
            on_login_success=self._on_login_success
        )
        self.login_window.mainloop()

    def _on_login_success(self, usuario: Usuario) -> None:
        """Manejador tras una autenticación válida."""
        self.main_window = MainWindow(
            usuario_actual=usuario,
            libro_service=self.libro_service,
            lector_service=self.lector_service,
            prestamo_service=self.prestamo_service,
            usuario_service=self.usuario_service,
            on_logout=self._on_logout
        )

    def _on_logout(self) -> None:
        """Restaura la ventana de login al cerrar sesión."""
        if self.login_window:
            self.login_window.deiconify()
            self.login_window.txt_password.delete(0, tk.END)
            self.login_window.txt_username.focus_set()


def main() -> None:
    app = BibliotecaApp()
    app.start()


if __name__ == "__main__":
    main()
