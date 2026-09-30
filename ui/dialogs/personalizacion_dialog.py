import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from models.usuario import Usuario
from services.usuario_service import UsuarioService
from services.exceptions import BusinessError, ValidationError
from ui.theme import ModernTheme


class PersonalizacionDialog(tk.Toplevel):
    """
    Diálogo de Configuración de Apariencia y Accesibilidad (Temas y Fuentes).
    Permite alternar entre los 5 modos de color, cambiar tipografía y escalar el tamaño
    de letra para usuarios con requerimientos visuales o de accesibilidad.
    """

    def __init__(
        self,
        parent: tk.Widget,
        usuario_actual: Usuario,
        usuario_service: UsuarioService,
        on_theme_changed: Optional[Callable[[str, str, int], None]] = None
    ):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.usuario_service = usuario_service
        self.on_theme_changed = on_theme_changed

        self.title("Personalización Visual y Accesibilidad")
        self.geometry("520x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_widgets()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 520
        h = 480
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        lbl_titulo = ttk.Label(
            main_frame,
            text="🎨 Personalización Visual y Accesibilidad",
            font=ModernTheme.FONT_SUBTITLE,
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_titulo.pack(anchor="w", pady=(0, 15))

        # 1. Sección de Temas (5 Modos de Color)
        frame_temas = ttk.LabelFrame(main_frame, text="Paleta de Colores (5 Modos)", padding=12)
        frame_temas.pack(fill="x", pady=(0, 12))

        self.var_tema = tk.StringVar(value=self.usuario_actual.tema or "estandar")

        temas_opciones = [
            ("estandar", "🏛 Modo Estándar (Azul Institucional original)"),
            ("oscuro", "🌙 Modo Oscuro / Nocturno (Descanso visual y contraste)"),
            ("pastel", "🌸 Modo Pastel (Tonos crema, lavanda y menta suave)"),
            ("corporativo", "💼 Modo Vivo / Corporativo (Azul rey vibrante y blanco)"),
            ("bosque", "🌲 Modo Bosque (Verde oliva, beige y tonos tierra)")
        ]

        for clave, descripcion in temas_opciones:
            rb = ttk.Radiobutton(
                frame_temas,
                text=descripcion,
                value=clave,
                variable=self.var_tema,
                command=self._previsualizar
            )
            rb.pack(anchor="w", pady=2)

        # 2. Sección de Accesibilidad Tipográfica
        frame_fuente = ttk.LabelFrame(main_frame, text="Configuración de Fuente y Tamaño", padding=12)
        frame_fuente.pack(fill="x", pady=(0, 15))

        # Tipografía
        row_font = ttk.Frame(frame_fuente)
        row_font.pack(fill="x", pady=4)
        ttk.Label(row_font, text="Tipo de Letra:", font=ModernTheme.FONT_BOLD, width=16).pack(side="left")
        self.cbo_fuente = ttk.Combobox(
            row_font,
            values=ModernTheme.SUPPORTED_FONTS,
            state="readonly",
            width=22
        )
        self.cbo_fuente.set(self.usuario_actual.fuente_familia or "Segoe UI")
        self.cbo_fuente.pack(side="left")
        self.cbo_fuente.bind("<<ComboboxSelected>>", lambda e: self._previsualizar())

        # Tamaño de Fuente
        row_tam = ttk.Frame(frame_fuente)
        row_tam.pack(fill="x", pady=4)
        ttk.Label(row_tam, text="Tamaño de Texto:", font=ModernTheme.FONT_BOLD, width=16).pack(side="left")
        
        self.tam_map = {
            "Pequeño (9 pt)": 9,
            "Estándar (10 pt)": 10,
            "Mediano / Cómodo (12 pt)": 12,
            "Grande / Accesible (14 pt)": 14
        }
        self.cbo_tamano = ttk.Combobox(
            row_tam,
            values=list(self.tam_map.keys()),
            state="readonly",
            width=22
        )
        # Buscar clave actual
        tam_actual = self.usuario_actual.fuente_tamano or 10
        clave_tam = next((k for k, v in self.tam_map.items() if v == tam_actual), "Estándar (10 pt)")
        self.cbo_tamano.set(clave_tam)
        self.cbo_tamano.pack(side="left")
        self.cbo_tamano.bind("<<ComboboxSelected>>", lambda e: self._previsualizar())

        # Botones de Acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", side="bottom", pady=(10, 0))

        btn_cerrar = ttk.Button(btn_frame, text="Cerrar", style="Secondary.TButton", command=self.destroy)
        btn_cerrar.pack(side="right", padx=(8, 0))

        btn_guardar = ttk.Button(
            btn_frame,
            text="💾 Guardar Preferencias",
            style="Primary.TButton",
            command=self._guardar
        )
        btn_guardar.pack(side="right")

    def _obtener_valores_actuales(self):
        tema = self.var_tema.get()
        fuente = self.cbo_fuente.get()
        tam_texto = self.cbo_tamano.get()
        tamano = self.tam_map.get(tam_texto, 10)
        return tema, fuente, tamano

    def _previsualizar(self) -> None:
        """Aplica el cambio visual en vivo a la ventana principal."""
        tema, fuente, tamano = self._obtener_valores_actuales()
        if self.on_theme_changed:
            self.on_theme_changed(tema, fuente, tamano)

    def _guardar(self) -> None:
        """Persiste las preferencias en la base de datos."""
        tema, fuente, tamano = self._obtener_valores_actuales()
        try:
            self.usuario_service.guardar_preferencias(
                usuario=self.usuario_actual,
                tema=tema,
                fuente_familia=fuente,
                fuente_tamano=tamano
            )
            if self.on_theme_changed:
                self.on_theme_changed(tema, fuente, tamano)

            messagebox.showinfo(
                "Preferencias Guardadas",
                f"Tus preferencias visuales han sido guardadas con éxito:\n\n"
                f"• Tema: {ModernTheme.PALETTES[tema]['name']}\n"
                f"• Fuente: {fuente}\n"
                f"• Tamaño: {tamano} pt\n\n"
                "Se cargarán automáticamente cada vez que inicies sesión.",
                parent=self
            )
            self.destroy()
        except (ValidationError, BusinessError) as e:
            messagebox.showerror("Error", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}", parent=self)
