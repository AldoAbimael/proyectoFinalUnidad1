import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List


class ModernTheme:
    """
    Gestor de Temas y Accesibilidad Visual para la aplicación (Tkinter / ttk).
    Soporta 5 modos de color, cambio de tipografía y escalado de fuentes.
    """

    # Definición de las 5 paletas de color
    PALETTES: Dict[str, Dict[str, str]] = {
        "estandar": {
            "name": "Modo Estándar (Azul Institucional)",
            "bg": "#f1f5f9",
            "card": "#ffffff",
            "primary": "#1e3a8a",
            "primary_hover": "#1d4ed8",
            "secondary": "#475569",
            "text": "#0f172a",
            "muted": "#64748b",
            "success": "#16a34a",
            "danger": "#dc2626",
            "warning": "#d97706",
            "header_bg": "#1e293b",
            "header_text": "#ffffff",
            "header_muted": "#cbd5e1",
            "select": "#bfdbfe",
            "tree_bg": "#ffffff",
            "tree_text": "#0f172a",
            "tree_heading_bg": "#e2e8f0",
            "tab_bg": "#e2e8f0",
            "tab_active": "#cbd5e1",
            "entry_bg": "#ffffff",
            "entry_text": "#0f172a"
        },
        "oscuro": {
            "name": "Modo Oscuro / Nocturno (Descanso Visual)",
            "bg": "#0f172a",          # Grafito oscuro
            "card": "#1e293b",        # Slate oscuro
            "primary": "#38bdf8",     # Azul neón
            "primary_hover": "#0284c7",
            "secondary": "#64748b",
            "text": "#f8fafc",        # Texto blanco
            "muted": "#94a3b8",
            "success": "#4ade80",     # Verde neón suave
            "danger": "#f87171",      # Rojo claro
            "warning": "#fbbf24",
            "header_bg": "#020617",   # Negro absoluto
            "header_text": "#38bdf8", # Título neón
            "header_muted": "#94a3b8",
            "select": "#334155",
            "tree_bg": "#1e293b",
            "tree_text": "#f8fafc",
            "tree_heading_bg": "#0f172a",
            "tab_bg": "#1e293b",
            "tab_active": "#334155",
            "entry_bg": "#1e293b",
            "entry_text": "#f8fafc"
        },
        "pastel": {
            "name": "Modo Pastel (Crema, Lavanda y Menta)",
            "bg": "#fcfbf7",          # Crema relajante
            "card": "#ffffff",
            "primary": "#8b5cf6",     # Lavanda suave
            "primary_hover": "#7c3aed",
            "secondary": "#6b7280",
            "text": "#2e1065",        # Violeta oscuro legible
            "muted": "#7c3aed",
            "success": "#10b981",     # Verde menta
            "danger": "#f43f5e",      # Rosa suave
            "warning": "#f59e0b",
            "header_bg": "#581c87",   # Lavanda institucional
            "header_text": "#f3e8ff",
            "header_muted": "#d8b4fe",
            "select": "#e9d5ff",
            "tree_bg": "#ffffff",
            "tree_text": "#2e1065",
            "tree_heading_bg": "#f3e8ff",
            "tab_bg": "#ede9fe",
            "tab_active": "#ddd6fe",
            "entry_bg": "#ffffff",
            "entry_text": "#2e1065"
        },
        "corporativo": {
            "name": "Modo Vivo / Corporativo (Azul Rey y Blanco)",
            "bg": "#f0f4f8",          # Gris claro fresco
            "card": "#ffffff",
            "primary": "#0066cc",     # Azul rey vibrante
            "primary_hover": "#0052a3",
            "secondary": "#475569",
            "text": "#0a2540",        # Marino profundo
            "muted": "#627d98",
            "success": "#00875a",
            "danger": "#de350b",
            "warning": "#ff8b00",
            "header_bg": "#003366",   # Azul corporativo profundo
            "header_text": "#ffffff",
            "header_muted": "#b3d4ff",
            "select": "#cce4ff",
            "tree_bg": "#ffffff",
            "tree_text": "#0a2540",
            "tree_heading_bg": "#e2e8f0",
            "tab_bg": "#e2e8f0",
            "tab_active": "#cce4ff",
            "entry_bg": "#ffffff",
            "entry_text": "#0a2540"
        },
        "bosque": {
            "name": "Modo Bosque (Verde Oliva, Beige y Café)",
            "bg": "#f4f3ee",          # Beige tierra
            "card": "#ffffff",
            "primary": "#4a5d23",     # Verde oliva bosque
            "primary_hover": "#3a4a1b",
            "secondary": "#6c584c",   # Café tierra
            "text": "#1b2d15",        # Verde oscuro
            "muted": "#7f7f6f",
            "success": "#2a9d8f",
            "danger": "#bc4749",
            "warning": "#dd6b20",
            "header_bg": "#283618",   # Verde profundo
            "header_text": "#dda15e", # Beige dorado
            "header_muted": "#ccd5ae",
            "select": "#dde5b6",
            "tree_bg": "#ffffff",
            "tree_text": "#1b2d15",
            "tree_heading_bg": "#e9edc9",
            "tab_bg": "#e9edc9",
            "tab_active": "#ccd5ae",
            "entry_bg": "#ffffff",
            "entry_text": "#1b2d15"
        }
    }

    # Fuentes y tamaños soportados
    SUPPORTED_FONTS = ["Segoe UI", "Arial", "Consolas", "Verdana", "Trebuchet MS"]
    SUPPORTED_SIZES = [9, 10, 12, 14]

    # Estado actual
    current_theme = "estandar"
    current_font_family = "Segoe UI"
    current_font_size = 10

    # Atributos de clase dinámicos para retrocompatibilidad con vistas
    COLOR_BG = PALETTES["estandar"]["bg"]
    COLOR_CARD = PALETTES["estandar"]["card"]
    COLOR_PRIMARY = PALETTES["estandar"]["primary"]
    COLOR_PRIMARY_HOVER = PALETTES["estandar"]["primary_hover"]
    COLOR_SECONDARY = PALETTES["estandar"]["secondary"]
    COLOR_TEXT = PALETTES["estandar"]["text"]
    COLOR_MUTED = PALETTES["estandar"]["muted"]
    COLOR_SUCCESS = PALETTES["estandar"]["success"]
    COLOR_DANGER = PALETTES["estandar"]["danger"]
    COLOR_WARNING = PALETTES["estandar"]["warning"]
    COLOR_HEADER_BG = PALETTES["estandar"]["header_bg"]
    COLOR_SELECT = PALETTES["estandar"]["select"]

    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12, "bold")
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_MONO = ("Consolas", 10)

    @classmethod
    def apply(
        cls,
        root: tk.Widget,
        theme_name: str = "estandar",
        font_family: str = "Segoe UI",
        font_size: int = 10
    ) -> None:
        """
        Aplica y actualiza de forma global el tema de color, tipografía y tamaño de letra.
        """
        if theme_name not in cls.PALETTES:
            theme_name = "estandar"
        if font_family not in cls.SUPPORTED_FONTS:
            font_family = "Segoe UI"
        try:
            font_size = int(font_size)
            if font_size not in cls.SUPPORTED_SIZES:
                font_size = 10
        except Exception:
            font_size = 10

        cls.current_theme = theme_name
        cls.current_font_family = font_family
        cls.current_font_size = font_size

        pal = cls.PALETTES[theme_name]

        # Sincronizar variables de clase
        cls.COLOR_BG = pal["bg"]
        cls.COLOR_CARD = pal["card"]
        cls.COLOR_PRIMARY = pal["primary"]
        cls.COLOR_PRIMARY_HOVER = pal["primary_hover"]
        cls.COLOR_SECONDARY = pal["secondary"]
        cls.COLOR_TEXT = pal["text"]
        cls.COLOR_MUTED = pal["muted"]
        cls.COLOR_SUCCESS = pal["success"]
        cls.COLOR_DANGER = pal["danger"]
        cls.COLOR_WARNING = pal["warning"]
        cls.COLOR_HEADER_BG = pal["header_bg"]
        cls.COLOR_SELECT = pal["select"]

        cls.FONT_FAMILY = font_family
        cls.FONT_TITLE = (font_family, font_size + 6, "bold")
        cls.FONT_SUBTITLE = (font_family, font_size + 2, "bold")
        cls.FONT_NORMAL = (font_family, font_size)
        cls.FONT_BOLD = (font_family, font_size, "bold")
        cls.FONT_SMALL = (font_family, max(8, font_size - 1))
        cls.FONT_MONO = ("Consolas", font_size)

        # Configurar estilos TTK
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # Configurar color de fondo de ventanas nativas de Tk
        try:
            if hasattr(root, "configure"):
                root.configure(bg=pal["bg"])
        except Exception:
            pass

        # Frames
        style.configure("TFrame", background=pal["bg"])
        style.configure("Card.TFrame", background=pal["card"], relief="flat")
        style.configure("Header.TFrame", background=pal["header_bg"])
        style.configure("TLabelframe", background=pal["card"], foreground=pal["text"], font=cls.FONT_BOLD)
        style.configure("TLabelframe.Label", background=pal["card"], foreground=pal["text"], font=cls.FONT_BOLD)

        # Labels
        style.configure("TLabel", background=pal["bg"], foreground=pal["text"], font=cls.FONT_NORMAL)
        style.configure("Card.TLabel", background=pal["card"], foreground=pal["text"], font=cls.FONT_NORMAL)
        style.configure("Title.TLabel", background=pal["bg"], foreground=pal["primary"], font=cls.FONT_TITLE)
        style.configure("Header.TLabel", background=pal["header_bg"], foreground=pal["header_text"], font=cls.FONT_SUBTITLE)
        style.configure("HeaderMuted.TLabel", background=pal["header_bg"], foreground=pal["header_muted"], font=cls.FONT_SMALL)
        style.configure("Muted.TLabel", background=pal["bg"], foreground=pal["muted"], font=cls.FONT_SMALL)

        # Botones
        btn_text_color = "#ffffff" if theme_name != "oscuro" else "#0f172a"
        style.configure(
            "Primary.TButton",
            font=cls.FONT_BOLD,
            foreground=btn_text_color,
            background=pal["primary"],
            borderwidth=0,
            focuscolor="none",
            padding=(12, 6)
        )
        style.map(
            "Primary.TButton",
            background=[("active", pal["primary_hover"]), ("disabled", "#94a3b8")]
        )

        style.configure(
            "Success.TButton",
            font=cls.FONT_BOLD,
            foreground="#ffffff",
            background=pal["success"],
            borderwidth=0,
            focuscolor="none",
            padding=(10, 6)
        )
        style.map(
            "Success.TButton",
            background=[("active", pal["primary_hover"]), ("disabled", "#94a3b8")]
        )

        style.configure(
            "Danger.TButton",
            font=cls.FONT_BOLD,
            foreground="#ffffff",
            background=pal["danger"],
            borderwidth=0,
            focuscolor="none",
            padding=(10, 6)
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#b91c1c"), ("disabled", "#94a3b8")]
        )

        style.configure(
            "Secondary.TButton",
            font=cls.FONT_NORMAL,
            foreground=pal["text"],
            background=pal["tab_bg"],
            borderwidth=0,
            focuscolor="none",
            padding=(10, 6)
        )
        style.map(
            "Secondary.TButton",
            background=[("active", pal["tab_active"])]
        )

        # Treeview (Tablas)
        style.configure(
            "Treeview",
            background=pal["tree_bg"],
            foreground=pal["tree_text"],
            fieldbackground=pal["tree_bg"],
            font=cls.FONT_NORMAL,
            rowheight=int(font_size * 2.8)
        )
        style.map(
            "Treeview",
            background=[("selected", pal["select"])],
            foreground=[("selected", pal["text"])]
        )

        style.configure(
            "Treeview.Heading",
            font=cls.FONT_BOLD,
            background=pal["tree_heading_bg"],
            foreground=pal["text"],
            relief="flat",
            padding=(6, 6)
        )
        style.map(
            "Treeview.Heading",
            background=[("active", pal["tab_active"])]
        )

        # Notebook (Pestañas)
        style.configure(
            "TNotebook",
            background=pal["bg"],
            tabmargins=[2, 5, 2, 0]
        )
        style.configure(
            "TNotebook.Tab",
            font=cls.FONT_BOLD,
            padding=(16, 8),
            background=pal["tab_bg"],
            foreground=pal["muted"]
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", pal["primary"]), ("active", pal["tab_active"])],
            foreground=[("selected", btn_text_color), ("active", pal["text"])]
        )

        # Entradas de texto y combobox
        style.configure("TEntry", font=cls.FONT_NORMAL, padding=4)
        style.configure("TCombobox", font=cls.FONT_NORMAL, padding=4)
        style.configure("TCheckbutton", background=pal["bg"], foreground=pal["text"], font=cls.FONT_NORMAL)
