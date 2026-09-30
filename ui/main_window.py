import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from datetime import date
from models.usuario import Usuario
from services.libro_service import LibroService
from services.lector_service import LectorService
from services.prestamo_service import PrestamoService
from services.usuario_service import UsuarioService
from ui.theme import ModernTheme
from ui.libros_view import LibrosView
from ui.lectores_view import LectoresView
from ui.prestamos_view import PrestamosView
from ui.reportes_view import ReportesView
from ui.usuarios_view import UsuariosView
from ui.avatar_widget import AvatarWidget
from ui.dialogs.personalizacion_dialog import PersonalizacionDialog


class MainWindow(tk.Toplevel):
    """
    Ventana Principal del Sistema de Biblioteca (RNF-3, A.4).
    Incluye barra de menú superior, identificación de usuario y rol,
    foto de perfil (avatar interactivo), selector de 5 temas y fuentes accesibles,
    y pestañas de navegación para cada módulo del sistema.
    """

    def __init__(
        self,
        usuario_actual: Usuario,
        libro_service: LibroService,
        lector_service: LectorService,
        prestamo_service: PrestamoService,
        usuario_service: UsuarioService,
        on_logout: Callable[[], None]
    ):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.libro_service = libro_service
        self.lector_service = lector_service
        self.prestamo_service = prestamo_service
        self.usuario_service = usuario_service
        self.on_logout = on_logout

        self.title("Sistema de Gestión Bibliotecaria — Opción 1")
        self.geometry("1100x720")
        self.minsize(980, 620)

        # Aplicar tema y fuentes personalizadas del usuario guardadas en BD
        ModernTheme.apply(
            self,
            theme_name=self.usuario_actual.tema or "estandar",
            font_family=self.usuario_actual.fuente_familia or "Segoe UI",
            font_size=self.usuario_actual.fuente_tamano or 10
        )
        self.configure(bg=ModernTheme.COLOR_BG)

        self._centrar()
        self._crear_menu()
        self._crear_encabezado()
        self._crear_tabs()
        self._crear_barra_estado()

        # Al cerrar con la 'X', cerrar sesión o terminar app
        self.protocol("WM_DELETE_WINDOW", self._confirmar_salida)

    def _centrar(self) -> None:
        self.update_idletasks()
        w = 1100
        h = 720
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_menu(self) -> None:
        """Crea el menú superior requerido por RNF-3 y A.4, incluyendo personalización visual."""
        menubar = tk.Menu(self)

        # Menú Archivo
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Cerrar Sesión", command=self._cerrar_sesion)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir del Sistema", command=self._confirmar_salida)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)

        # Menú Módulos
        menu_modulos = tk.Menu(menubar, tearoff=0)
        menu_modulos.add_command(label="Libros (Acervo)", command=lambda: self.notebook.select(0))
        menu_modulos.add_command(label="Lectores (Padrón)", command=lambda: self.notebook.select(1))
        menu_modulos.add_command(label="Préstamos y Devoluciones", command=lambda: self.notebook.select(2))
        if self.usuario_actual.es_admin:
            menu_modulos.add_separator()
            menu_modulos.add_command(label="Usuarios del Sistema", command=lambda: self.notebook.select(4))
        menubar.add_cascade(label="Módulos", menu=menu_modulos)

        # Menú Reportes
        menu_reportes = tk.Menu(menubar, tearoff=0)
        menu_reportes.add_command(label="Préstamos Atrasados (RF-8)", command=lambda: self.notebook.select(3))
        menubar.add_cascade(label="Reportes", menu=menu_reportes)

        # Menú Apariencia y Accesibilidad (NUEVO: 5 Modos de Color y Fuentes)
        menu_apariencia = tk.Menu(menubar, tearoff=0)
        menu_apariencia.add_command(
            label="⚙ Configuración de Temas y Accesibilidad...",
            command=self._abrir_personalizacion
        )
        menu_apariencia.add_separator()

        # Submenú rápido de los 5 temas
        menu_temas = tk.Menu(menu_apariencia, tearoff=0)
        for clave, nombre in [
            ("estandar", "🏛 Modo Estándar"),
            ("oscuro", "🌙 Modo Oscuro / Nocturno"),
            ("pastel", "🌸 Modo Pastel"),
            ("corporativo", "💼 Modo Vivo / Corporativo"),
            ("bosque", "🌲 Modo Bosque")
        ]:
            menu_temas.add_command(
                label=nombre,
                command=lambda c=clave: self._cambiar_tema_rapido(c)
            )
        menu_apariencia.add_cascade(label="Cambiar Tema (5 Modos)", menu=menu_temas)

        # Submenú rápido de tamaño de fuente
        menu_tamanos = tk.Menu(menu_apariencia, tearoff=0)
        for tam, texto in [
            (9, "Pequeño (9 pt)"),
            (10, "Estándar (10 pt)"),
            (12, "Mediano (12 pt)"),
            (14, "Grande / Accesible (14 pt)")
        ]:
            menu_tamanos.add_command(
                label=texto,
                command=lambda t=tam: self._cambiar_tamano_rapido(t)
            )
        menu_apariencia.add_cascade(label="Tamaño de Fuente (Accesibilidad)", menu=menu_tamanos)
        menu_apariencia.add_separator()
        menu_apariencia.add_command(label="📷 Cambiar Foto de Perfil...", command=self._cambiar_foto_perfil)
        menubar.add_cascade(label="Apariencia y Accesibilidad", menu=menu_apariencia)

        # Menú Ayuda
        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menu_ayuda.add_command(label="Acerca del Sistema", command=self._mostrar_acerca_de)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

        self.config(menu=menubar)

    def _crear_encabezado(self) -> None:
        self.header_frame = ttk.Frame(self, style="Header.TFrame", padding=(15, 10))
        self.header_frame.pack(fill="x")

        # Título a la izquierda
        lbl_app = ttk.Label(
            self.header_frame,
            text="📚 SISTEMA BIBLIOTECARIO",
            font=("Segoe UI", 13, "bold"),
            style="Header.TLabel"
        )
        lbl_app.pack(side="left")

        # Información de sesión y foto de perfil a la derecha
        self.user_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        self.user_frame.pack(side="right")

        # Botón de configuración rápida de apariencia
        btn_tema = ttk.Button(
            self.user_frame,
            text="🎨 Apariencia",
            style="Secondary.TButton",
            command=self._abrir_personalizacion
        )
        btn_tema.pack(side="left", padx=(0, 12))

        # Texto con datos del usuario
        rol_badge = f"[{self.usuario_actual.rol.upper()}]"
        self.lbl_user = ttk.Label(
            self.user_frame,
            text=f"Usuario: {self.usuario_actual.username} {rol_badge}  |  Fecha: {date.today().isoformat()}",
            font=ModernTheme.FONT_NORMAL,
            style="Header.TLabel"
        )
        self.lbl_user.pack(side="left", padx=(0, 10))

        # Foto de Perfil interactiva (Avatar Circular)
        self.avatar_widget = AvatarWidget(
            self.user_frame,
            usuario=self.usuario_actual,
            usuario_service=self.usuario_service,
            size=44,
            bg_color=ModernTheme.COLOR_HEADER_BG,
            on_avatar_updated=self._on_avatar_actualizado
        )
        self.avatar_widget.pack(side="left", padx=(0, 12))

        btn_logout = ttk.Button(
            self.user_frame,
            text="Cerrar Sesión",
            style="Danger.TButton",
            command=self._cerrar_sesion
        )
        btn_logout.pack(side="left")

    def _crear_tabs(self) -> None:
        """Crea el Notebook con pestañas para los módulos de la aplicación."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # 1. Pestaña Libros (Entidad A)
        self.view_libros = LibrosView(self.notebook, self.libro_service)
        self.notebook.add(self.view_libros, text="  📖 Libros (Acervo)  ")

        # 2. Pestaña Lectores (Entidad B)
        self.view_lectores = LectoresView(self.notebook, self.lector_service)
        self.notebook.add(self.view_lectores, text="  👥 Lectores (Padrón)  ")

        # 3. Pestaña Préstamos (Movimiento de Negocio + JOIN)
        self.view_prestamos = PrestamosView(
            self.notebook,
            self.prestamo_service,
            self.lector_service,
            self.libro_service
        )
        self.notebook.add(self.view_prestamos, text="  🔄 Préstamos y Devoluciones (JOIN)  ")

        # 4. Pestaña Reportes (Caso Problemático RF-8)
        self.view_reportes = ReportesView(self.notebook, self.prestamo_service)
        self.notebook.add(self.view_reportes, text="  ⚠ Reporte: Préstamos Atrasados  ")

        # 5. Pestaña Usuarios del Sistema (Solo visible si es Administrador, RF-2)
        if self.usuario_actual.es_admin:
            self.view_usuarios = UsuariosView(self.notebook, self.usuario_service, self.usuario_actual)
            self.notebook.add(self.view_usuarios, text="  ⚙ Usuarios del Sistema  ")

        # Escuchar cambio de pestaña para refrescar datos automáticamente
        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

    def _al_cambiar_pestana(self, event: tk.Event) -> None:
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 0:
            self.view_libros.cargar_datos()
        elif selected_tab == 1:
            self.view_lectores.cargar_datos()
        elif selected_tab == 2:
            self.view_prestamos.cargar_datos()
        elif selected_tab == 3:
            self.view_reportes.cargar_datos()
        elif selected_tab == 4 and self.usuario_actual.es_admin:
            self.view_usuarios.cargar_datos()

    def _crear_barra_estado(self) -> None:
        statusbar = ttk.Frame(self, padding=(10, 4))
        statusbar.pack(fill="x", side="bottom")

        lbl_status = ttk.Label(
            statusbar,
            text="Persistencia: SQLite 3 (PRAGMA foreign_keys = ON) | Arquitectura por Capas: UI ➔ Services ➔ Repositories ➔ DB",
            font=ModernTheme.FONT_SMALL,
            foreground=ModernTheme.COLOR_MUTED
        )
        lbl_status.pack(side="left")

        lbl_version = ttk.Label(
            statusbar,
            text="Tópicos Avanzados de Programación — Proyecto Unidad 1 (Opción 1)",
            font=ModernTheme.FONT_SMALL,
            foreground=ModernTheme.COLOR_MUTED
        )
        lbl_version.pack(side="right")

    def _cerrar_sesion(self) -> None:
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión actual?", parent=self):
            self.destroy()
            self.on_logout()

    def _confirmar_salida(self) -> None:
        if messagebox.askyesno("Salir", "¿Desea cerrar la aplicación por completo?", parent=self):
            self.quit()

    def _abrir_personalizacion(self) -> None:
        """Abre el diálogo modal de configuración de temas y accesibilidad."""
        PersonalizacionDialog(
            parent=self,
            usuario_actual=self.usuario_actual,
            usuario_service=self.usuario_service,
            on_theme_changed=lambda t, f, s: self._aplicar_cambios_tema(t, f, s, guardar=False)
        )

    def _cambiar_tema_rapido(self, tema: str) -> None:
        """Cambio instantáneo de tema desde el menú superior con persistencia."""
        self._aplicar_cambios_tema(
            tema=tema,
            fuente=self.usuario_actual.fuente_familia or "Segoe UI",
            tamano=self.usuario_actual.fuente_tamano or 10,
            guardar=True
        )

    def _cambiar_tamano_rapido(self, tamano: int) -> None:
        """Cambio rápido de tamaño de texto para accesibilidad visual."""
        self._aplicar_cambios_tema(
            tema=self.usuario_actual.tema or "estandar",
            fuente=self.usuario_actual.fuente_familia or "Segoe UI",
            tamano=tamano,
            guardar=True
        )

    def _cambiar_foto_perfil(self) -> None:
        """Invoca el selector de foto de perfil del widget de avatar."""
        if hasattr(self, "avatar_widget"):
            self.avatar_widget.seleccionar_nueva_foto()

    def _on_avatar_actualizado(self, nueva_ruta: str) -> None:
        """Manejador tras actualizar la foto de perfil."""
        pass

    def _aplicar_cambios_tema(self, tema: str, fuente: str, tamano: int, guardar: bool = False) -> None:
        """Aplica la configuración de tema y fuentes a la ventana y refresca los componentes."""
        if guardar:
            try:
                self.usuario_service.guardar_preferencias(self.usuario_actual, tema, fuente, tamano)
            except Exception as e:
                print(f"Error al guardar preferencias: {e}")

        ModernTheme.apply(self, theme_name=tema, font_family=fuente, font_size=tamano)
        self.configure(bg=ModernTheme.COLOR_BG)

        if hasattr(self, "avatar_widget"):
            self.avatar_widget.set_bg(ModernTheme.COLOR_HEADER_BG)

        # Actualizar datos de vistas
        if hasattr(self, "view_libros"):
            self.view_libros.cargar_datos()
        if hasattr(self, "view_lectores"):
            self.view_lectores.cargar_datos()
        if hasattr(self, "view_prestamos"):
            self.view_prestamos.cargar_datos()
        if hasattr(self, "view_reportes"):
            self.view_reportes.cargar_datos()
        if self.usuario_actual.es_admin and hasattr(self, "view_usuarios"):
            self.view_usuarios.cargar_datos()

    def _mostrar_acerca_de(self) -> None:
        messagebox.showinfo(
            "Acerca de",
            "Sistema de Gestión Bibliotecaria\n"
            "Tópicos Avanzados de Programación · Unidad 1\n"
            "Opción 1: Sistema de Biblioteca\n\n"
            "Stack Tecnológico:\n"
            "• Python 3.10+ / Tkinter & ttk\n"
            "• SQLite 3 relacional con llaves foráneas activas\n"
            "• Hash SHA-256 para contraseñas\n"
            "• Arquitectura limpia por capas (RNF-1 / RNF-2)\n\n"
            "Personalización y Accesibilidad:\n"
            "• 5 Modos de Color: Estándar, Oscuro, Pastel, Corporativo y Bosque\n"
            "• Escalador de tipografía para accesibilidad visual\n"
            "• Fotos de perfil con recorte circular interactivo\n\n"
            "Usuarios de prueba:\n"
            "• admin / admin123 (Administrador)\n"
            "• operador / operador123 (Operador)",
            parent=self
        )
