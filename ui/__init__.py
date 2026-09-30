"""
Módulo de interfaz gráfica de usuario basada en Tkinter / ttk (RNF-1, RNF-3).
No contiene consultas SQL directas; se comunica exclusivamente con la capa de servicios (RNF-2).
"""
from .theme import ModernTheme
from .login_window import LoginWindow
from .main_window import MainWindow
from .avatar_widget import AvatarWidget
from .dialogs.personalizacion_dialog import PersonalizacionDialog

__all__ = [
    "ModernTheme",
    "LoginWindow",
    "MainWindow",
    "AvatarWidget",
    "PersonalizacionDialog"
]
