import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from models.usuario import Usuario
from services.auth_service import AuthService
from services.exceptions import AuthenticationError, ValidationError
from ui.theme import ModernTheme


class LoginWindow(tk.Tk):
    """
    Ventana de Autenticación de Usuarios del Sistema (RF-2, RF-3, A.4).
    Valida credenciales cifradas con SHA-256 e impide el acceso a cuentas inactivas.
    """

    def __init__(
        self,
        auth_service: AuthService,
        on_login_success: Callable[[Usuario], None]
    ):
        super().__init__()
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        self.title("Inicio de Sesión — Sistema Bibliotecario")
        self.geometry("440x480")
        self.resizable(False, False)

        # Aplicar estilos temáticos
        ModernTheme.apply(self)
        self.configure(bg=ModernTheme.COLOR_BG)

        self._centrar()
        self._crear_interfaz()

        # Atajo de tecla Enter para login
        self.bind("<Return>", lambda e: self._intentar_login())

    def _centrar(self) -> None:
        self.update_idletasks()
        w = 440
        h = 480
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_interfaz(self) -> None:
        # Cabecera institucional
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=20)
        header_frame.pack(fill="x")

        lbl_logo = ttk.Label(
            header_frame,
            text="📚 SISTEMA DE BIBLIOTECA",
            font=("Segoe UI", 14, "bold"),
            style="Header.TLabel"
        )
        lbl_logo.pack()

        lbl_sub = ttk.Label(
            header_frame,
            text="Control de Acervo, Lectores y Préstamos",
            style="HeaderMuted.TLabel"
        )
        lbl_sub.pack(pady=(4, 0))

        # Contenedor central (tarjeta)
        card = ttk.Frame(self, style="Card.TFrame", padding=25)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_ingreso = ttk.Label(
            card,
            text="Acceso al Sistema",
            font=ModernTheme.FONT_SUBTITLE,
            style="Card.TLabel",
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_ingreso.pack(anchor="w", pady=(0, 15))

        # Campo Usuario
        ttk.Label(card, text="Nombre de Usuario:", font=ModernTheme.FONT_BOLD, style="Card.TLabel").pack(anchor="w")
        self.txt_username = ttk.Entry(card, font=ModernTheme.FONT_NORMAL)
        self.txt_username.pack(fill="x", pady=(4, 12))
        self.txt_username.focus_set()

        # Campo Contraseña
        ttk.Label(card, text="Contraseña:", font=ModernTheme.FONT_BOLD, style="Card.TLabel").pack(anchor="w")
        self.txt_password = ttk.Entry(card, show="•", font=ModernTheme.FONT_NORMAL)
        self.txt_password.pack(fill="x", pady=(4, 20))

        # Botón Iniciar Sesión
        btn_login = ttk.Button(
            card,
            text="Iniciar Sesión",
            style="Primary.TButton",
            command=self._intentar_login
        )
        btn_login.pack(fill="x", pady=(0, 15))

        # Mensaje informativo con usuarios de prueba (A.5)
        info_frame = ttk.Frame(card, style="Card.TFrame")
        info_frame.pack(fill="x", side="bottom")

        lbl_credenciales = ttk.Label(
            info_frame,
            text="Credenciales de Prueba:\n• admin / admin123 (Administrador)\n• operador / operador123 (Operador)",
            style="Card.TLabel",
            font=ModernTheme.FONT_SMALL,
            foreground=ModernTheme.COLOR_MUTED,
            justify="center"
        )
        lbl_credenciales.pack(anchor="center")

    def _intentar_login(self) -> None:
        username = self.txt_username.get().strip()
        password = self.txt_password.get().strip()

        try:
            usuario = self.auth_service.login(username, password)
            self.withdraw()  # Ocultar ventana de login
            self.on_login_success(usuario)
        except (AuthenticationError, ValidationError) as e:
            messagebox.showerror("Error de Autenticación", str(e), parent=self)
            self.txt_password.delete(0, tk.END)
            self.txt_password.focus_set()
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al iniciar sesión: {e}", parent=self)
